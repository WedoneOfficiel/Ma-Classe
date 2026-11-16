#!/usr/bin/env bash
set -euo pipefail
ROOT="${MACLASSE_ROOT:-$(cd "$(dirname "$0")" && pwd -P)}"
ROOT="$(cd "$ROOT" && pwd -P)"
DATA_ROOT="$ROOT/data"
PROGRAM_ROOT="$DATA_ROOT/program"
VERSIONS_ROOT="$PROGRAM_ROOT/versions"
CURRENT_LINK="$PROGRAM_ROOT/current"
STATE_FILE="$DATA_ROOT/update-state.json"
BACKUP_ROOT="$DATA_ROOT/backups"

write_state() {
  local status="$1"
  local error="${2:-}"
  UPDATE_STATUS="$status" UPDATE_ERROR="$error" STATE_FILE="$STATE_FILE" /usr/bin/python3 - <<'PY'
import json, os, tempfile, time
path=os.environ["STATE_FILE"]
try:
    with open(path, encoding="utf-8") as f: state=json.load(f)
except Exception:
    state={}
if not isinstance(state,dict): state={}
state.update({"status":os.environ["UPDATE_STATUS"],"updated_at":int(time.time())})
if os.environ.get("UPDATE_ERROR"):
    state["last_error"]=os.environ["UPDATE_ERROR"]
else:
    state.pop("last_error",None)
tmp=path+".tmp"
with open(tmp,"w",encoding="utf-8") as f: json.dump(state,f,ensure_ascii=False,indent=2)
os.replace(tmp,path)
PY
}

write_maintenance_state() {
  local status="$1"
  MAINTENANCE_FILE="$DATA_ROOT/update-maintenance.json" MAINTENANCE_STATUS="$status" /usr/bin/python3 - <<'PY'
import json, os, time
path=os.environ["MAINTENANCE_FILE"]
if not os.path.isfile(path): raise SystemExit(0)
with open(path,encoding="utf-8") as f: state=json.load(f)
if not isinstance(state,dict): raise SystemExit(0)
if state.get("status") in ("scheduled","installing"):
    state["status"]=os.environ["MAINTENANCE_STATUS"]
    state["updated_at"]=int(time.time())
    tmp=path+".tmp"
    with open(tmp,"w",encoding="utf-8") as f: json.dump(state,f,ensure_ascii=False,indent=2)
    os.replace(tmp,path)
PY
}

fail_and_restore() {
  local message="$1"
  echo "Échec de la mise à jour : $message" >&2
  systemctl --user stop maclasse.service >/dev/null 2>&1 || true
  set +e
  systemctl --user is-active --quiet maclasse.service >/dev/null 2>&1
  local service_state=$?
  set -e
  if [[ "$service_state" != "3" ]]; then
    write_state "rollback_failed" "$message — impossible de confirmer l'arrêt du serveur ; aucune restauration de données n'a été tentée."
    write_maintenance_state "failed"
    echo "ATTENTION : le serveur semble toujours actif ou son état est inconnu. Aucune bascule ni restauration de base n'est tentée pour éviter une corruption." >&2
    exit 1
  fi
  rm -f "$CURRENT_LINK.rollback"
  ln -s "$PREVIOUS_LINK_TARGET" "$CURRENT_LINK.rollback"
  mv -Tf "$CURRENT_LINK.rollback" "$CURRENT_LINK"
  if [[ -n "${BACKUP_FILE:-}" && -f "$BACKUP_FILE" ]]; then
    if ! cp -a "$BACKUP_FILE" "$DATA_ROOT/maclasse.json"; then
      write_state "rollback_failed" "$message — code précédent restauré, mais la base n'a pas pu être restaurée depuis sa sauvegarde."
      write_maintenance_state "failed"
      echo "ATTENTION : le code précédent est réactivé, mais la restauration de la base a échoué. Le serveur reste arrêté pour protéger les données." >&2
      exit 1
    fi
  fi
  systemctl --user start maclasse.service || true
  local restored=0
  for _ in {1..15}; do
    if health_ok "$PREVIOUS_VERSION"; then restored=1; break; fi
    sleep 2
  done
  if [[ "$restored" == "1" ]]; then
    write_state "failed" "$message — version précédente restaurée."
    write_maintenance_state "failed"
    echo "Retour à la version $PREVIOUS_VERSION effectué."
  else
    write_state "rollback_failed" "$message — le redémarrage de la version précédente a également échoué."
    write_maintenance_state "failed"
    echo "ATTENTION : restauration automatique du code effectuée, mais le serveur ne répond pas. Consulter journalctl." >&2
  fi
  exit 1
}

health_ok() {
  local expected="$1"
  local host
  host="$(openssl x509 -in "$DATA_ROOT/tls/server.crt" -noout -ext subjectAltName 2>/dev/null | grep -oE 'IP Address:[0-9.]+' | head -n1 | cut -d: -f2 || true)"
  [[ -n "$host" ]] || return 1
  curl --silent --show-error --fail --connect-timeout 2 --max-time 4 \
    --cacert "$DATA_ROOT/tls/ca.crt" "https://$host:8765/api/health" 2>/dev/null |
    EXPECTED_VERSION="$expected" /usr/bin/python3 -c 'import json,os,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("ok") is True and d.get("version")==os.environ["EXPECTED_VERSION"] and d.get("database")=="ok" else 1)'
}

[[ -f "$STATE_FILE" ]] || { echo "Aucune mise à jour préparée."; exit 1; }
[[ -L "$CURRENT_LINK" ]] || { echo "Le lien vers la version active est absent."; exit 1; }
command -v systemctl >/dev/null 2>&1
command -v curl >/dev/null 2>&1
command -v openssl >/dev/null 2>&1

read -r VERSION_NUMBER EXPECTED_SHA STATUS < <(/usr/bin/python3 - "$STATE_FILE" <<'PY'
import json, re, sys
with open(sys.argv[1],encoding="utf-8") as f: state=json.load(f)
version=str(state.get("version","")).lstrip("vV")
if not re.fullmatch(r"\d+\.\d+\.\d+",version): raise SystemExit("Version invalide.")
sha=str(state.get("sha256",""))
if not re.fullmatch(r"[a-f0-9]{64}",sha): raise SystemExit("Empreinte invalide.")
if state.get("status")!="prepared": raise SystemExit("Aucune version prête à installer.")
print(version,sha,state["status"])
PY
)
TARGET="$VERSIONS_ROOT/V$VERSION_NUMBER"
[[ ! -L "$TARGET" ]] || { echo "Le dossier de version ne peut pas être un lien symbolique."; exit 1; }
[[ -d "$TARGET" ]] || { echo "Dossier de version préparée absent."; exit 1; }
[[ -x "$TARGET/.venv/bin/python" && -f "$TARGET/maclasse-runtime-ready.json" && -f "$TARGET/server.py" && -f "$TARGET/_all.js" ]] || { echo "Version préparée incomplète."; exit 1; }
EXPECTED_VERSION="$VERSION_NUMBER"
grep -Fq "APP_VERSION='$EXPECTED_VERSION'" "$TARGET/server.py" || { echo "Version du serveur incohérente."; exit 1; }
grep -Fq "const MC_VERSION='V$EXPECTED_VERSION'" "$TARGET/_all.js" || { echo "Version de l'interface incohérente."; exit 1; }
grep -Fxq "V$EXPECTED_VERSION" "$TARGET/VERSION.txt" || { echo "VERSION.txt ne correspond pas au code téléchargé."; exit 1; }
TARGET_REAL="$(realpath "$TARGET")"
VERSIONS_REAL="$(realpath "$VERSIONS_ROOT")"
[[ "$TARGET_REAL" == "$VERSIONS_REAL/"* ]] || { echo "Chemin de version hors du stockage autorisé."; exit 1; }
META="$TARGET/maclasse-prepared.json"
META_SHA="$(/usr/bin/python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["sha256"])' "$META")"
META_VERSION="$(/usr/bin/python3 -c 'import json,sys; print(str(json.load(open(sys.argv[1]))["version"]).lstrip("vV"))' "$META")"
[[ "$META_SHA" == "$EXPECTED_SHA" && "$META_VERSION" == "$VERSION_NUMBER" ]] || { echo "Le manifeste de la version préparée ne correspond plus."; exit 1; }
PREVIOUS_TARGET="$(readlink -f "$CURRENT_LINK")"
case "$PREVIOUS_TARGET" in "$ROOT"|"$VERSIONS_REAL"/*) ;; *) echo "Cible active précédente non reconnue."; exit 1;; esac
PREVIOUS_LINK_TARGET="$(realpath --relative-to="$PROGRAM_ROOT" "$PREVIOUS_TARGET")"
PREVIOUS_VERSION="$(/usr/bin/python3 - "$PREVIOUS_TARGET" <<'PY'
import re,sys
from pathlib import Path
p=Path(sys.argv[1])/"VERSION.txt"
try: value=p.read_text(encoding="utf-8").strip().lstrip("vV")
except OSError: value=""
print(value if re.fullmatch(r"\d+\.\d+\.\d+",value) else "")
PY
)"
[[ -n "$PREVIOUS_VERSION" ]] || { echo "Impossible d'identifier la version précédente."; exit 1; }

mkdir -p "$BACKUP_ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="$BACKUP_ROOT/maclasse-avant-maj-$STAMP.json"
if [[ -f "$DATA_ROOT/maclasse.json" ]]; then
  cp -a "$DATA_ROOT/maclasse.json" "$BACKUP_FILE"
else
  echo "Base de données absente : mise à jour annulée avant arrêt du serveur." >&2
  exit 1
fi
systemctl --user disable --now maclasse-update-scheduled.timer >/dev/null 2>&1 || true
write_state "installing"
write_maintenance_state "installing"
echo "Arrêt temporaire de MaClasse…"
if ! systemctl --user stop maclasse.service; then
  fail_and_restore "L’arrêt propre du serveur a échoué."
fi
rm -f "$CURRENT_LINK.next"
if ! ln -s "versions/V$VERSION_NUMBER" "$CURRENT_LINK.next" || ! mv -Tf "$CURRENT_LINK.next" "$CURRENT_LINK"; then
  fail_and_restore "La bascule atomique vers la nouvelle version a échoué."
fi
echo "Redémarrage de MaClasse $VERSION_NUMBER…"
if ! systemctl --user start maclasse.service; then
  fail_and_restore "Le service n'a pas redémarré."
fi
healthy=0
for _ in {1..15}; do
  if health_ok "$EXPECTED_VERSION"; then healthy=1; break; fi
  sleep 2
done
if [[ "$healthy" != "1" ]]; then
  fail_and_restore "Le contrôle de santé n'a pas confirmé la version $EXPECTED_VERSION."
fi
write_state "installed"
write_maintenance_state "completed"
# Garder les trois dernières versions et toujours le code actif + son prédécesseur.
if ! /usr/bin/python3 - "$VERSIONS_ROOT" "$TARGET_REAL" "$PREVIOUS_TARGET" <<'PY'
import re, shutil, sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
active=Path(sys.argv[2]).resolve()
previous=Path(sys.argv[3]).resolve()
versions=[]
for path in root.iterdir():
    if path.is_symlink() or not path.is_dir():
        continue
    match=re.fullmatch(r"V(\d+)\.(\d+)\.(\d+)",path.name)
    if match:
        versions.append((tuple(map(int,match.groups())),path.resolve()))
keep={active,previous}
keep.update(path for _,path in sorted(versions,reverse=True)[:3])
for _,path in versions:
    if path in keep:
        continue
    if path.parent==root and path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
PY
then
  echo "Avertissement : nettoyage des anciennes versions ignoré ; la mise à jour reste installée."
fi
echo "Mise à jour MaClasse $VERSION_NUMBER installée et contrôlée avec succès."
