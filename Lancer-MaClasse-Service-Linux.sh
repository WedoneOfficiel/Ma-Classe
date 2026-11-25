#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
if [[ -n "${MACLASSE_ROOT:-}" ]]; then
  ROOT="$MACLASSE_ROOT"
elif [[ -d "$SCRIPT_DIR/data" ]]; then
  ROOT="$SCRIPT_DIR"
else
  ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
fi
ROOT="$(cd "$ROOT" && pwd -P)"
[[ "$(uname -s)" == "Linux" ]] || { echo "Ce service est réservé à Linux."; exit 1; }
command -v ip >/dev/null 2>&1 || { echo "Commande ip absente."; exit 1; }
command -v awk >/dev/null 2>&1 || { echo "Commande awk absente."; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "Commande openssl absente."; exit 1; }

DATA_ROOT="${MACLASSE_DATA_DIR:-$ROOT/data}"
DATA_ROOT="$(cd "$DATA_ROOT" && pwd -P)"
PROGRAM_ROOT="$DATA_ROOT/program"
VERSIONS_ROOT="$PROGRAM_ROOT/versions"
APP_ROOT="$PROGRAM_ROOT/current"
mkdir -p "$VERSIONS_ROOT"
if [[ ! -e "$APP_ROOT" && ! -L "$APP_ROOT" ]]; then
  ln -s ../.. "$APP_ROOT"
fi
[[ -d "$APP_ROOT" ]] || { echo "La version active MaClasse est introuvable."; exit 1; }
DATA_REAL="$(cd "$DATA_ROOT" && pwd -P)"
PROGRAM_REAL="$(cd "$PROGRAM_ROOT" && pwd -P)"
VERSIONS_REAL="$(cd "$VERSIONS_ROOT" && pwd -P)"
[[ "$PROGRAM_REAL" == "$DATA_REAL/program" && "$VERSIONS_REAL" == "$PROGRAM_REAL/versions" ]] || { echo "Le dossier de versions MaClasse pointe hors du stockage autorisé."; exit 1; }
APP_REAL="$(cd "$APP_ROOT" && pwd -P)"
case "$APP_REAL" in "$ROOT"|"$VERSIONS_REAL"/*) ;; *) echo "La version active pointe hors du stockage MaClasse autorisé."; exit 1;; esac
PYTHON="$APP_ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "Environnement Python absent pour la version active : lance Installer-MaClasse-Linux.sh."; exit 1; }

# Le certificat et les données restent dans data/, hors du répertoire de programme versionné.
cd "$ROOT"
"$PYTHON" - <<'PY'
import json, os, sys
from pathlib import Path
try:
    database=Path(os.environ.get("MACLASSE_DATA_DIR", "data")) / "maclasse.json"
    users=json.loads(database.read_text(encoding="utf-8")).get("users", [])
except Exception:
    sys.exit("Initialise d'abord MaClasse en local et crée un compte direction.")
def valid(user):
    password=str(user.get("passwordHash", ""))
    return password.startswith("pbkdf2_sha256$") and not user.get("mustChangePassword") and user.get("active") is not False
if not any(isinstance(u,dict) and u.get("role")=="admin" and valid(u) for u in users):
    sys.exit("Aucun compte direction sécurisé : initialise MaClasse avant d'activer le service réseau.")
PY

# The Python supervisor follows DHCP changes and keeps the HTTPS listener bound
# only to the current private address. If the interface disappears, it closes
# the listener and waits for a usable address before serving again.
export MACLASSE_LAN_MODE=1
export MACLASSE_PORT=8765
export MACLASSE_ROOT="$ROOT"
export MACLASSE_APP_ROOT="$APP_ROOT"
export MACLASSE_DATA_DIR="$DATA_ROOT"
export MACLASSE_PYTHON="$PYTHON"
unset MACLASSE_HOST MACLASSE_TLS_CERT MACLASSE_TLS_KEY
cd "$APP_ROOT"
echo "MaClasse HTTPS — surveillance automatique de l'adresse réseau."
exec "$PYTHON" "$APP_ROOT/network_supervisor.py"
