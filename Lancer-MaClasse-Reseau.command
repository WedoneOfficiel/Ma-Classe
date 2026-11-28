#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
cd "$ROOT"

public_tls_hostname() {
  "$ROOT/.venv/bin/python" - "$ROOT/data" <<'PYTLS'
import sys
from network_supervisor import load_public_certificate_config
config = load_public_certificate_config(sys.argv[1])
if not config:
    raise SystemExit("Configuration du certificat public absente.")
print(config["hostname"])
PYTLS
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Ce lanceur réseau est réservé à macOS."
  exit 1
fi
if /bin/launchctl print "gui/$(id -u)/fr.maclasse.server" >/dev/null 2>&1; then
  echo "Le service MaClasse est déjà chargé par launchd."
  echo "Ne démarre pas une seconde copie : elle partagerait la même base de données."
  if [[ -f "$ROOT/data/tls/public-certificate.json" ]]; then
    PUBLIC_HOST="$(public_tls_hostname)" || { echo "Configuration TLS publique invalide ; aucun repli non sécurisé n'est effectué."; exit 1; }
    open -a "Firefox" "https://$PUBLIC_HOST:8765" >/dev/null 2>&1 || open "https://$PUBLIC_HOST:8765" >/dev/null 2>&1 || true
  else
    IFACE="$(/sbin/route -n get default 2>/dev/null | /usr/bin/awk '/interface:/{print $2; exit}')"
    HOST=""
    if [[ -n "$IFACE" && -x ".venv/bin/python" ]]; then
      HOST="$(/usr/sbin/ipconfig getifaddr "$IFACE" 2>/dev/null || true)"
      if [[ -z "$HOST" ]] || ! .venv/bin/python -c 'import ipaddress,sys; a=ipaddress.ip_address(sys.argv[1]); assert isinstance(a,ipaddress.IPv4Address) and a.is_private and not a.is_loopback and not a.is_link_local and not a.is_multicast and not a.is_unspecified' "$HOST" >/dev/null 2>&1; then
        HOST=""
      fi
    fi
    if [[ -n "$HOST" ]]; then
      open -a "Firefox" "https://$HOST:8765" >/dev/null 2>&1 || open "https://$HOST:8765" >/dev/null 2>&1 || true
    else
      echo "Adresse IPv4 privée introuvable sur l'interface réseau active ; consulte data/macos-service-error.log."
    fi
  fi
  read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  exit 0
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
admin=next((u for u in users if u.get("role")=="admin" and u.get("active") is not False),None)
if not admin or not str(admin.get("passwordHash","")).startswith("pbkdf2_sha256$") or admin.get("mustChangePassword"):
    sys.exit(1)
PY
then
  echo "Sécurité : initialise d'abord MaClasse en local et crée un compte direction sécurisé."
  echo "Aucun compte enseignant n'est nécessaire pour ouvrir le réseau privé."
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

PUBLIC_MODE=0
if [[ -f "$ROOT/data/tls/public-certificate.json" ]]; then
  PUBLIC_HOST="$(public_tls_hostname)" || { echo "Configuration TLS publique invalide ; aucun repli non sécurisé n'est effectué."; exit 1; }
  PUBLIC_MODE=1
  URL="https://$PUBLIC_HOST:8765"
else
  ./Configurer-MaClasse-Reseau.command "$LAN_IP"
  CA_CERT="data/tls/ca.crt"
  URL="https://$LAN_IP:8765"
fi
echo "============================================================"
echo "MaClasse — MODE RÉSEAU PRIVÉ HTTPS"
echo "Adresse à ouvrir sur le second PC : $URL"
echo
if [[ "$PUBLIC_MODE" == "1" ]]; then
  echo "Certificat DNS public configuré : aucun certificat privé n'est à importer sur les postes."
  echo "Le DNS local du réseau doit résoudre $PUBLIC_HOST vers l'adresse privée de ce Mac."
else
  echo "HTTPS est activé. Installe data/tls/ca.crt dans les autorités racines de confiance de chaque appareil client."
  echo "Sans cette autorité approuvée, le navigateur affichera un avertissement de certificat."
fi
echo "Utilise uniquement un réseau privé maîtrisé ; aucune redirection de port sur la box."
echo "Pour arrêter le serveur : Ctrl+C."
echo "============================================================"
echo

export MACLASSE_ROOT="$ROOT"
export MACLASSE_APP_ROOT="$ROOT"
export MACLASSE_DATA_DIR="$ROOT/data"
export MACLASSE_PYTHON="$ROOT/.venv/bin/python"
export MACLASSE_LAN_MODE=1
export MACLASSE_PORT=8765
unset MACLASSE_HOST MACLASSE_TLS_CERT MACLASSE_TLS_KEY
"$ROOT/.venv/bin/python" "$ROOT/network_supervisor.py" &
SERVER_PID=$!
cleanup() { kill -TERM "$SERVER_PID" >/dev/null 2>&1 || true; wait "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

READY=0
for _ in {1..20}; do
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    wait "$SERVER_PID" || true
    echo "Le serveur n'a pas pu démarrer."
    exit 1
  fi
  if [[ "$PUBLIC_MODE" == "1" ]]; then
    if /usr/bin/curl --noproxy '*' --silent --fail "$URL/api/auth/session" >/dev/null 2>&1; then READY=1; break; fi
  else
    if /usr/bin/curl --noproxy '*' --silent --fail --cacert "$CA_CERT" "$URL/api/auth/session" >/dev/null 2>&1; then READY=1; break; fi
  fi
  sleep 0.5
done
if [[ "$READY" -ne 1 ]]; then echo "Le serveur n'a pas répondu après 10 secondes."; exit 1; fi
open -a "Firefox" "$URL" >/dev/null 2>&1 || open "$URL" >/dev/null 2>&1 || true
wait "$SERVER_PID"
