#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Ce lanceur réseau est réservé à macOS."
  exit 1
fi
if [[ ! -x ".venv/bin/python" ]]; then
  echo "Installe d'abord MaClasse avec Installer-MaClasse.command."
  read -r -p "Appuie sur Entrée pour fermer… " _ || true
  exit 1
fi
if [[ ! -f "data/maclasse.json" ]] || ! .venv/bin/python - <<'PY'
import hashlib, json, sys
from pathlib import Path
try:
    users=json.loads(Path("data/maclasse.json").read_text(encoding="utf-8")).get("users", [])
except Exception:
    sys.exit(1)
def matches(password, stored):
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt, digest=stored.split("$",3)
            actual=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),int(rounds)).hex()
            return actual==digest
        except Exception:
            return False
    return stored==hashlib.sha256(password.encode()).hexdigest()
for username, default in (("admin","admin"),("enseignant","enseignant")):
    account=next((u for u in users if u.get("username")==username and u.get("active") is not False),None)
    if not account or matches(default,str(account.get("passwordHash",""))):
        sys.exit(1)
PY
then
  echo "Sécurité : change d'abord les deux mots de passe initiaux depuis le lanceur local."
  echo "Les identifiants admin/admin et enseignant/enseignant ne doivent jamais être utilisés sur le réseau."
  exit 1
fi
if /usr/bin/curl --silent --fail "http://127.0.0.1:8765/api/auth/session" >/dev/null 2>&1; then
  echo "Un serveur MaClasse répond déjà sur ce Mac."
  echo "Arrête-le avec Ctrl+C avant de lancer le mode réseau."
  read -r -p "Appuie sur Entrée pour fermer… " _ || true
  exit 1
fi

IFACE="$(/sbin/route -n get default 2>/dev/null | /usr/bin/awk '/interface:/{print $2; exit}')"
if [[ -z "$IFACE" ]]; then
  echo "Impossible de détecter l'interface réseau active."
  exit 1
fi
LAN_IP="$(/usr/sbin/ipconfig getifaddr "$IFACE" 2>/dev/null || true)"
if [[ -z "$LAN_IP" ]]; then
  echo "Aucune adresse IPv4 sur l'interface $IFACE."
  echo "Connecte ce Mac à la box privée du bureau puis réessaie."
  exit 1
fi
if ! .venv/bin/python -c 'import ipaddress,sys; a=ipaddress.ip_address(sys.argv[1]); assert isinstance(a,ipaddress.IPv4Address) and a.is_private and not a.is_loopback and not a.is_link_local and not a.is_multicast and not a.is_unspecified' "$LAN_IP" >/dev/null 2>&1; then
  echo "Adresse refusée : $LAN_IP n'est pas une IPv4 privée utilisable."
  exit 1
fi

URL="http://$LAN_IP:8765"
echo "============================================================"
echo "MaClasse — MODE TEST SUR RÉSEAU PRIVÉ"
echo "Adresse à ouvrir sur le second PC : $URL"
echo
echo "IMPORTANT : HTTP n'est pas chiffré sur le réseau local."
echo "Utilise uniquement ta box privée isolée et des données fictives."
echo "N'utilise pas ce mode sur le réseau de l'établissement."
echo "Ne configure aucune redirection de port sur la box."
echo "Pour arrêter le serveur : Ctrl+C."
echo "============================================================"
echo

MACLASSE_LAN_MODE=1 MACLASSE_HOST="$LAN_IP" MACLASSE_PORT=8765 .venv/bin/python server.py &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" >/dev/null 2>&1 || true; wait "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

READY=0
for _ in {1..20}; do
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    wait "$SERVER_PID" || true
    echo "Le serveur n'a pas pu démarrer."
    exit 1
  fi
  if /usr/bin/curl --silent --fail "$URL/api/auth/session" >/dev/null 2>&1; then READY=1; break; fi
  sleep 0.5
done
if [[ "$READY" -ne 1 ]]; then echo "Le serveur n'a pas répondu après 10 secondes."; exit 1; fi
open -a "Firefox" "$URL" >/dev/null 2>&1 || open "$URL" >/dev/null 2>&1 || true
wait "$SERVER_PID"
