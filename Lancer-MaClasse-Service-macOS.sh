#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
if [[ -n "${MACLASSE_ROOT:-}" ]]; then
  ROOT="$MACLASSE_ROOT"
elif [[ -d "$SCRIPT_DIR/data" ]]; then
  ROOT="$SCRIPT_DIR"
else
  ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
fi
ROOT="$(cd "$ROOT" && pwd -P)"
DATA="${MACLASSE_DATA_DIR:-$ROOT/data}"
DATA="$(cd "$DATA" && pwd -P)"
CURRENT="$DATA/program/current"
[[ -L "$CURRENT" ]] || { echo "Version active absente : $CURRENT" >&2; exit 1; }
PROGRAM="$(cd "$(dirname "$CURRENT")" && cd "$(readlink "$CURRENT")" && pwd -P)"
case "$PROGRAM" in "$ROOT"|"$DATA/program/versions/"*) ;; *) echo "Cible active hors du stockage autorisé." >&2; exit 1;; esac
PYTHON="$PROGRAM/.venv/bin/python"
[[ -x "$PYTHON" && -f "$PROGRAM/server.py" ]] || { echo "Environnement Python ou serveur absent dans $PROGRAM." >&2; exit 1; }
IFACE="$(/sbin/route -n get default 2>/dev/null | /usr/bin/awk '/interface:/{print $2; exit}')"
[[ -n "$IFACE" ]] || { echo "Aucune interface réseau par défaut." >&2; exit 1; }
HOST="$(/usr/sbin/ipconfig getifaddr "$IFACE" 2>/dev/null || true)"
[[ -n "$HOST" ]] || { echo "Aucune adresse IPv4 sur l'interface $IFACE." >&2; exit 1; }
"$ROOT/.venv/bin/python" -c 'import ipaddress,sys; a=ipaddress.ip_address(sys.argv[1]); assert isinstance(a,ipaddress.IPv4Address) and a.is_private and not a.is_loopback and not a.is_link_local and not a.is_multicast and not a.is_unspecified' "$HOST" || { echo "Adresse LAN refusée : $HOST." >&2; exit 1; }
CERT="$DATA/tls/server.crt"
KEY="$DATA/tls/server.key"
CA="$DATA/tls/ca.crt"
[[ -f "$CERT" && -f "$KEY" && -f "$CA" ]] || { echo "Certificats TLS absents ; relance la configuration réseau MaClasse." >&2; exit 1; }
CERT_HOST="$(/usr/bin/openssl x509 -in "$CERT" -noout -ext subjectAltName 2>/dev/null | /usr/bin/grep -oE 'IP Address:[0-9.]+' | /usr/bin/head -n1 | /usr/bin/cut -d: -f2 || true)"
if [[ "$CERT_HOST" != "$HOST" ]] || ! /usr/bin/openssl x509 -in "$CERT" -checkend 86400 -noout >/dev/null 2>&1; then
  echo "Mise à jour du certificat HTTPS pour la nouvelle adresse LAN $HOST…"
  (cd "$ROOT" && PYTHON="$ROOT/.venv/bin/python" /bin/bash ./Configurer-MaClasse-Reseau.sh "$HOST")
fi
export MACLASSE_SUPERVISED=launchd
export MACLASSE_ROOT="$ROOT"
export MACLASSE_DATA_DIR="$DATA"
export MACLASSE_LAN_MODE=1
export MACLASSE_HOST="$HOST"
export MACLASSE_PORT=8765
export MACLASSE_TLS_CERT="$CERT"
export MACLASSE_TLS_KEY="$KEY"
cd "$PROGRAM"
exec "$PYTHON" server.py
