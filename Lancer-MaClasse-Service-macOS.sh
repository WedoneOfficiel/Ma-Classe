#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
DATA="$ROOT/data"
CURRENT="$DATA/program/current"
[[ -L "$CURRENT" ]] || { echo "Version active absente : $CURRENT" >&2; exit 1; }
PROGRAM="$(cd "$(dirname "$CURRENT")" && cd "$(readlink "$CURRENT")" && pwd -P)"
case "$PROGRAM" in "$ROOT"|"$DATA/program/versions/"*) ;; *) echo "Cible active hors du stockage autorisé." >&2; exit 1;; esac
PYTHON="$PROGRAM/.venv/bin/python"
[[ -x "$PYTHON" && -f "$PROGRAM/server.py" ]] || { echo "Environnement Python ou serveur absent dans $PROGRAM." >&2; exit 1; }
CERT="$DATA/tls/server.crt"
KEY="$DATA/tls/server.key"
CA="$DATA/tls/ca.crt"
[[ -f "$CERT" && -f "$KEY" && -f "$CA" ]] || { echo "Certificats TLS absents ; relance la configuration réseau MaClasse." >&2; exit 1; }
HOST="$(/usr/bin/openssl x509 -in "$CERT" -noout -ext subjectAltName 2>/dev/null | /usr/bin/grep -oE 'IP Address:[0-9.]+' | /usr/bin/head -n1 | /usr/bin/cut -d: -f2 || true)"
[[ -n "$HOST" ]] || { echo "Impossible de lire l'adresse IP du certificat TLS." >&2; exit 1; }
export MACLASSE_SUPERVISED=launchd
export MACLASSE_DATA_DIR="$DATA"
export MACLASSE_LAN_MODE=1
export MACLASSE_HOST="$HOST"
export MACLASSE_PORT=8765
export MACLASSE_TLS_CERT="$CERT"
export MACLASSE_TLS_KEY="$KEY"
cd "$PROGRAM"
exec "$PYTHON" server.py
