#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
[[ "$(uname -s)" == "Linux" ]] || { echo "Ce lanceur est réservé à Linux."; exit 1; }
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet maclasse.service; then
  echo "MaClasse est déjà lancé par systemd. Ouvre https://$(openssl x509 -in "$ROOT/data/tls/server.crt" -noout -ext subjectAltName 2>/dev/null | grep -oE 'IP Address:[0-9.]+' | head -n1 | cut -d: -f2):8765"
  exit 0
fi
exec /usr/bin/bash "$ROOT/Lancer-MaClasse-Service-Linux.sh"
