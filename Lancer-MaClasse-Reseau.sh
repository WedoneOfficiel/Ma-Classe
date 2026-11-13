#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == "Linux" ]] || { echo "Ce lanceur est réservé à Linux."; exit 1; }
[[ -x .venv/bin/python ]] || { echo "Lance d'abord Installer-MaClasse-Linux.sh."; exit 1; }
.venv/bin/python - <<'PY'
import hashlib,json,sys
from pathlib import Path
try: users=json.loads(Path("data/maclasse.json").read_text(encoding="utf-8")).get("users",[])
except Exception: sys.exit(1)
def valid(u):
 p=str(u.get("passwordHash",""))
 return p.startswith("pbkdf2_sha256$") and not u.get("mustChangePassword") and u.get("active") is not False
if not any(u.get("role")=="admin" and valid(u) for u in users if isinstance(u,dict)): sys.exit(1)
PY
IFACE="$(ip -4 route show default 2>/dev/null | awk 'NR==1 {for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')"
[[ -n "$IFACE" ]] || { echo "Interface réseau introuvable."; exit 1; }
LAN_IP="$(ip -4 -o addr show dev "$IFACE" scope global | awk 'NR==1 {split($4,a,"/"); print a[1]}')"
[[ -n "$LAN_IP" ]] || { echo "Adresse IPv4 privée introuvable."; exit 1; }
./Configurer-MaClasse-Reseau.sh "$LAN_IP"
CA_CERT="data/tls/ca.crt"; TLS_CERT="data/tls/server.crt"; TLS_KEY="data/tls/server.key"
URL="https://$LAN_IP:8765"
if curl --silent --fail "http://127.0.0.1:8765/api/auth/session" >/dev/null 2>&1; then echo "Arrête d'abord le serveur local sur le port 8765."; exit 1; fi
echo "MaClasse HTTPS : $URL"
echo "Installe $CA_CERT dans les autorités racines de confiance des appareils clients."
echo "Ne configure aucune redirection de port sur le routeur."
MACLASSE_LAN_MODE=1 MACLASSE_HOST="$LAN_IP" MACLASSE_PORT=8765 MACLASSE_TLS_CERT="$TLS_CERT" MACLASSE_TLS_KEY="$TLS_KEY" .venv/bin/python server.py &
PID=$!
trap 'kill "$PID" >/dev/null 2>&1 || true; wait "$PID" 2>/dev/null || true' EXIT INT TERM
READY=0
for _ in {1..30}; do
  kill -0 "$PID" >/dev/null 2>&1 || { echo "Le serveur n'a pas démarré."; exit 1; }
  if curl --silent --fail --cacert "$CA_CERT" "$URL/api/auth/session" >/dev/null 2>&1; then READY=1; break; fi
  sleep .5
done
[[ "$READY" == 1 ]] || { echo "Le serveur HTTPS ne répond pas."; exit 1; }
if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true; fi
wait "$PID"
