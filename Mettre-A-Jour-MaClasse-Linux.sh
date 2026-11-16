#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd -P)"
DATA_ROOT="$ROOT/data"
# Sur une installation supervisée, le secours CLI utilise le même moteur de release
# que l'interface : aucune modification Git du code actif.
if [[ -f "$DATA_ROOT/update-manager.enabled" ]]; then
  command -v systemctl >/dev/null 2>&1 || { echo "systemctl est requis pour cette installation supervisée."; exit 1; }
  APP_ROOT="$DATA_ROOT/program/current"
  [[ -x "$APP_ROOT/.venv/bin/python" ]] || { echo "Version active ou environnement Python introuvable."; exit 1; }
  if systemctl --user is-active --quiet maclasse-update-apply.service; then
    echo "Une installation MaClasse est déjà en cours."
    exit 1
  fi
  command -v pgrep >/dev/null 2>&1 || { echo "pgrep est requis pour vérifier qu'aucun serveur manuel ne tourne."; exit 1; }
  SERVICE_PID="$(systemctl --user show --property=MainPID --value maclasse.service 2>/dev/null || echo 0)"
  while IFS= read -r pid; do
    [[ -z "$pid" || "$pid" == "$SERVICE_PID" ]] || { echo "Un serveur MaClasse manuel non supervisé est actif (PID $pid) ; arrêt requis avant la mise à jour." >&2; exit 1; }
  done < <(pgrep -f '[p]ython.*server\.py' || true)
  set +e
  "$APP_ROOT/.venv/bin/python" - "$ROOT" <<'PY'
import json, os, sys, time
from pathlib import Path
root=Path(sys.argv[1]).resolve()
data=root/"data"
active=data/"program"/"current"
sys.path.insert(0,str(active))
import update_manager
version=(active/"VERSION.txt").read_text(encoding="utf-8").strip().lstrip("vV")
database=json.loads((data/"maclasse.json").read_text(encoding="utf-8"))
if not isinstance(database,dict):
    raise SystemExit("La base MaClasse est invalide.")
release=update_manager.check_latest_release(version)
if not release.get("available"):
    print(f"MaClasse est déjà à jour ({version}).")
    raise SystemExit(10)
if release.get("min_data_schema",1)>int(database.get("schemaVersion",0) or 0):
    raise SystemExit("Cette version est incompatible avec la structure actuelle des données.")
versions=data/"program"/"versions"
prepared=update_manager.prepare_release(release,versions)
update_manager.prepare_runtime(prepared)
state={
    "status":"prepared",
    "version":release["version"],
    "sha256":release["sha256"],
    "min_data_schema":release["min_data_schema"],
    "prepared_at":int(time.time()),
}
path=data/"update-state.json"
tmp=path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
os.replace(tmp,path)
print(f"Version {release['version']} téléchargée, vérifiée et prête.")
PY
  PY_STATUS=$?
  set -e
  if [[ "$PY_STATUS" == "10" ]]; then exit 0; fi
  if [[ "$PY_STATUS" != "0" ]]; then exit "$PY_STATUS"; fi
  if ! systemctl --user start --no-block maclasse-update-apply.service; then
    echo "Impossible de lancer le gestionnaire indépendant. La version active n'a pas été remplacée." >&2
    exit 1
  fi
  echo "Installation déclenchée. Le serveur va redémarrer et contrôler la nouvelle version."
  exit 0
fi
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet maclasse.service; then
  echo "Le serveur est actif mais le gestionnaire de mise à jour n'est pas installé. Arrête le service ou installe le gestionnaire avant toute mise à jour." >&2
  exit 1
fi
if command -v pgrep >/dev/null 2>&1 && pgrep -f '[p]ython.*server\.py' >/dev/null; then
  echo "Le serveur MaClasse semble actif en lancement manuel. Arrête-le avant toute mise à jour Git." >&2
  exit 1
fi
UPDATED=0
PREVIOUS=""
BACKUP=""
rollback() {
  if [[ "$UPDATED" == "1" ]]; then
    echo "La validation a échoué : retour à la version précédente…"
    git reset --hard "$PREVIOUS" || echo "Attention : restauration Git à terminer manuellement."
    .venv/bin/python -m pip install -r requirements.txt || echo "Attention : dépendances précédentes à réinstaller."
    UPDATED=0
    echo "Sauvegarde des données conservée : $BACKUP"
  fi
}
fail() { echo "Mise à jour interrompue : $1"; rollback; exit 1; }
[[ -d .git ]] || fail "Cette installation n'est pas un clone Git."
[[ -x .venv/bin/python ]] || fail "Environnement Python absent ; lance Installer-MaClasse-Linux.sh."
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" =~ WedoneOfficiel/Ma-Classe(\.git)?$ ]] || fail "Le dépôt distant origin n'est pas le dépôt officiel MaClasse."
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "main" ]] || fail "La branche active doit être main (branche actuelle : $BRANCH)."
[[ -z "$(git status --porcelain)" ]] || fail "Modifications locales détectées ; aucune donnée ne sera écrasée."
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="../MaClasse-sauvegarde-avant-maj-$STAMP"
mkdir -p "$BACKUP"
if [[ -d data ]]; then
  mkdir -p "$BACKUP/data"
  tar -C data --exclude=./tls -cf - . | tar -C "$BACKUP/data" -xf -
fi
PREVIOUS="$(git rev-parse HEAD)"
PREVIOUS_VERSION="$(cat VERSION.txt)"
printf "Version précédente : %s\nCommit précédent : %s\nDate : %s\n" "$PREVIOUS_VERSION" "$PREVIOUS" "$STAMP" > "$BACKUP/INFORMATIONS.txt"
echo "Sauvegarde créée : $BACKUP (base, pièces jointes et fichiers de data/, hors certificats et clés TLS)."
git fetch origin main || fail "Impossible de récupérer la version officielle."
git merge-base --is-ancestor "$PREVIOUS" origin/main || fail "Branche locale divergente ; aucune réinitialisation automatique."
git merge --ff-only origin/main || fail "Mise à jour Git impossible."
UPDATED=1
.venv/bin/python -m pip install -r requirements.txt || fail "Échec de mise à jour des dépendances."
.venv/bin/python -m py_compile server.py || fail "Échec compilation serveur."
VERSION="$(cat VERSION.txt)" || fail "Fichier VERSION.txt illisible."
VERSION_NUMBER="$(printf '%s' "$VERSION" | sed 's/^V//')"
grep -Fq "APP_VERSION='$VERSION_NUMBER'" server.py || fail "La version du serveur ne correspond pas à VERSION.txt."
grep -Fq "const MC_VERSION='V$VERSION_NUMBER'" _all.js || fail "La version de l'interface ne correspond pas à VERSION.txt."
if command -v node >/dev/null 2>&1; then node --check _all.js || fail "La vérification JavaScript a échoué."; else echo "Node.js absent : vérification JavaScript reportée aux tests de publication."; fi
UPDATED=0
echo "MaClasse $VERSION mise à jour. Sauvegarde : $BACKUP"