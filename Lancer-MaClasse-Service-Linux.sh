#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
[[ "$(uname -s)" == "Linux" ]] || { echo "Ce service est réservé à Linux."; exit 1; }
command -v ip >/dev/null 2>&1 || { echo "Commande ip absente."; exit 1; }
command -v awk >/dev/null 2>&1 || { echo "Commande awk absente."; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "Commande openssl absente."; exit 1; }

DATA_ROOT="$ROOT/data"
PROGRAM_ROOT="$DATA_ROOT/program"
VERSIONS_ROOT="$PROGRAM_ROOT/versions"
APP_ROOT="$PROGRAM_ROOT/current"
mkdir -p "$VERSIONS_ROOT"
if [[ ! -e "$APP_ROOT" && ! -L "$APP_ROOT" ]]; then
  ln -s "$ROOT" "$APP_ROOT"
fi
[[ -d "$APP_ROOT" ]] || { echo "La version active MaClasse est introuvable."; exit 1; }
PYTHON="$APP_ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "Environnement Python absent pour la version active : lance Installer-MaClasse-Linux.sh."; exit 1; }

# Le certificat et les données restent dans data/, hors du répertoire de programme versionné.
cd "$ROOT"
"$PYTHON" - <<'PY'
import json, sys
from pathlib import Path
try:
    users=json.loads(Path("data/maclasse.json").read_text(encoding="utf-8")).get("users", [])
except Exception:
    sys.exit("Initialise d'abord MaClasse en local et crée un compte direction.")
def valid(user):
    password=str(user.get("passwordHash", ""))
    return password.startswith("pbkdf2_sha256$") and not user.get("mustChangePassword") and user.get("active") is not False
if not any(isinstance(u,dict) and u.get("role")=="admin" and valid(u) for u in users):
    sys.exit("Aucun compte direction sécurisé : initialise MaClasse avant d'activer le service réseau.")
PY

IFACE="$(ip -4 route show default 2>/dev/null | awk 'NR==1 {for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')"
[[ -n "$IFACE" ]] || { echo "Interface réseau par défaut introuvable."; exit 1; }
LAN_IP="$(ip -4 -o addr show dev "$IFACE" scope global | awk 'NR==1 {split($4,a,"/"); print a[1]}')"
[[ -n "$LAN_IP" ]] || { echo "Adresse IPv4 introuvable sur $IFACE."; exit 1; }
"$APP_ROOT/.venv/bin/python" -c 'import ipaddress,sys; a=ipaddress.ip_address(sys.argv[1]); assert a.is_private and not a.is_loopback and not a.is_link_local' "$LAN_IP" || { echo "Adresse réseau refusée : $LAN_IP"; exit 1; }

./Configurer-MaClasse-Reseau.sh "$LAN_IP"
export MACLASSE_LAN_MODE=1
export MACLASSE_HOST="$LAN_IP"
export MACLASSE_PORT=8765
export MACLASSE_DATA_DIR="$DATA_ROOT"
export MACLASSE_TLS_CERT="$DATA_ROOT/tls/server.crt"
export MACLASSE_TLS_KEY="$DATA_ROOT/tls/server.key"
cd "$APP_ROOT"
echo "MaClasse HTTPS démarre sur https://$LAN_IP:8765"
if [[ "${MACLASSE_SUPERVISED:-}" != "systemd" ]] && command -v xdg-open >/dev/null 2>&1; then (sleep 2; xdg-open "https://$LAN_IP:8765") >/dev/null 2>&1 & fi
exec "$PYTHON" "$APP_ROOT/server.py"
