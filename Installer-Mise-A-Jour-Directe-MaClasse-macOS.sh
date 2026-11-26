#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
if [[ -n "\${MACLASSE_ROOT:-}" ]]; then
  ROOT="$MACLASSE_ROOT"
elif [[ -d "$SCRIPT_DIR/data" ]]; then
  ROOT="$SCRIPT_DIR"
else
  ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
fi
ROOT="$(cd "$ROOT" && pwd -P)"
DATA="\${MACLASSE_DATA_DIR:-$ROOT/data}"
DATA="$(cd "$DATA" && pwd -P)"
STATE="$DATA/update-state.json"
VERSIONS="$DATA/program/versions"
CURRENT="$DATA/program/current"
SERVICE_PLIST="$HOME/Library/LaunchAgents/fr.maclasse.server.plist"
PYTHON="$ROOT/.venv/bin/python"

[[ "$(uname -s)" == "Darwin" ]] || {
  echo "Ce lanceur direct est réservé à macOS." >&2
  exit 1
}
[[ "$(id -u)" -ne 0 ]] || {
  echo "Ne lance pas cette installation avec sudo." >&2
  exit 1
}
[[ -x "$PYTHON" ]] || {
  echo "Python MaClasse est introuvable : $PYTHON" >&2
  exit 1
}
[[ -f "$DATA/maclasse.json" && -f "$STATE" ]] || {
  echo "Base de données ou état de mise à jour absent. Aucune modification effectuée." >&2
  exit 1
}
[[ -L "$CURRENT" ]] || {
  echo "Le lien de version active est absent. Aucune modification effectuée." >&2
  exit 1
}
[[ -f "$SERVICE_PLIST" ]] || {
  echo "Le service launchd MaClasse n'est pas installé. Aucune modification effectuée." >&2
  exit 1
}

read -r VERSION SHA MIN_SCHEMA < <("$PYTHON" - "$STATE" "$DATA/maclasse.json" <<'PY'
import json,re,sys
try:
    with open(sys.argv[1],encoding="utf-8") as stream:
        state=json.load(stream)
    with open(sys.argv[2],encoding="utf-8") as stream:
        database=json.load(stream)
except (OSError,ValueError) as error:
    raise SystemExit("État de mise à jour ou base de données illisible : "+str(error))
if not isinstance(state,dict) or state.get("status")!="prepared":
    raise SystemExit("Aucune version n'est marquée comme préparée. Télécharge d'abord la mise à jour depuis Paramètres.")
version=str(state.get("version") or "").lstrip("vV")
sha=str(state.get("sha256") or "")
minimum=state.get("min_data_schema")
if not re.fullmatch(r"\d+\.\d+\.\d+",version):
    raise SystemExit("Numéro de version préparée invalide.")
if not re.fullmatch(r"[a-f0-9]{64}",sha):
    raise SystemExit("Empreinte de version préparée invalide.")
if type(minimum) is not int or minimum < 1:
    raise SystemExit("Schéma minimal de la mise à jour invalide.")
current=database.get("schemaVersion",0) if isinstance(database,dict) else 0
if type(current) is not int or minimum > current:
    raise SystemExit("Cette mise à jour n'est pas compatible avec le schéma actuel des données.")
print(version,sha,minimum)
PY
)

VERSIONS_REAL="$(cd "$VERSIONS" && pwd -P)"
TARGET="$VERSIONS/V$VERSION"
[[ -d "$TARGET" && ! -L "$TARGET" ]] || {
  echo "Le dossier de la version préparée est absent ou invalide : $TARGET" >&2
  exit 1
}
TARGET_REAL="$(cd "$TARGET" && pwd -P)"
case "$TARGET_REAL" in
  "$VERSIONS_REAL/"*) ;;
  *) echo "Le dossier préparé sort du stockage autorisé." >&2; exit 1 ;;
esac
[[ -x "$TARGET_REAL/.venv/bin/python" &&
   -f "$TARGET_REAL/maclasse-runtime-ready.json" &&
   -f "$TARGET_REAL/server.py" &&
   -f "$TARGET_REAL/_all.js" &&
   -f "$TARGET_REAL/VERSION.txt" &&
   -f "$TARGET_REAL/maclasse-prepared.json" &&
   -f "$TARGET_REAL/Appliquer-Mise-A-Jour-MaClasse-macOS.sh" ]] || {
  echo "La version préparée est incomplète. Aucune modification effectuée." >&2
  exit 1
}

EXPECTED="$("$PYTHON" - "$TARGET_REAL/maclasse-prepared.json" "$VERSION" "$MIN_SCHEMA" <<'PY'
import json,sys
try:
    with open(sys.argv[1],encoding="utf-8") as stream:
        metadata=json.load(stream)
except (OSError,ValueError) as error:
    raise SystemExit("Métadonnées de préparation illisibles : "+str(error))
if not isinstance(metadata,dict) or metadata.get("status")!="prepared":
    raise SystemExit("La version n'est pas marquée comme préparée.")
if metadata.get("version") not in (sys.argv[2],"V"+sys.argv[2]):
    raise SystemExit("Le numéro de version des métadonnées est incohérent.")
if metadata.get("min_data_schema") != int(sys.argv[3]):
    raise SystemExit("Le schéma minimal des métadonnées est incohérent.")
print(metadata.get("sha256",""))
PY
)"
[[ "$EXPECTED" == "$SHA" ]] || {
  echo "L'empreinte du dossier ne correspond pas à l'état préparé. Aucune modification effectuée." >&2
  exit 1
}
grep -Fxq "V$VERSION" "$TARGET_REAL/VERSION.txt" || {
  echo "Le numéro de version du dossier est incohérent." >&2
  exit 1
}
grep -Fq "APP_VERSION='$VERSION'" "$TARGET_REAL/server.py" || {
  echo "La version du serveur est incohérente." >&2
  exit 1
}

CURRENT_REAL="$(cd "$(dirname "$CURRENT")" && cd "$(readlink "$CURRENT")" && pwd -P)"
case "$CURRENT_REAL" in
  "$ROOT"|"$VERSIONS_REAL"/*) ;;
  *) echo "La version active pointe hors du stockage autorisé." >&2; exit 1 ;;
esac

echo "Version préparée et contrôlée : V$VERSION"
echo "Le lancement direct contourne uniquement l'ancien déclencheur launchd."
echo "L'installateur conserve les sauvegardes, le contrôle HTTPS et le rollback."
echo "MaClasse sera temporairement inaccessible pendant la bascule."
export MACLASSE_ROOT="$ROOT"
export MACLASSE_DATA_DIR="$DATA"
exec /bin/bash "$TARGET_REAL/Appliquer-Mise-A-Jour-MaClasse-macOS.sh"
