#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == "Linux" ]] || { echo "Ce service est réservé à Linux."; exit 1; }
[[ -x .venv/bin/python ]] || { echo "Environnement Python absent : lance Installer-MaClasse-Linux.sh."; exit 1; }
for cmd in ip awk curl openssl; do command -v "$cmd" >/dev/null 2>&1 || { echo "Commande requise absente : $cmd"; exit 1; }; done

# Le mode réseau n'est activé qu'après initialisation locale et création d'un compte direction sécurisé.
.venv/bin/python - <<'PY'
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
.venv/bin/python -c 'import ipaddress,sys; a=ipaddress.ip_address(sys.argv[1]); assert a.is_private and not a.is_loopback and not a.is_link_local' "$LAN_IP" || { echo "Adresse réseau refusée : $LAN_IP"; exit 1; }

./Configurer-MaClasse-Reseau.sh "$LAN_IP"
export MACLASSE_LAN_MODE=1
export MACLASSE_HOST="$LAN_IP"
export MACLASSE_PORT=8765
export MACLASSE_TLS_CERT="data/tls/server.crt"
export MACLASSE_TLS_KEY="data/tls/server.key"
echo "MaClasse HTTPS démarre sur https://$LAN_IP:8765"
exec .venv/bin/python server.py
