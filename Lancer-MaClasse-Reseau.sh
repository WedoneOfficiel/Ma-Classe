#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
[[ "$(uname -s)" == "Linux" ]] || { echo "Ce lanceur est réservé à Linux."; exit 1; }
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet maclasse.service; then
  if [[ -f "$ROOT/data/tls/public-certificate.json" ]]; then
    PUBLIC_HOST="$("$ROOT/.venv/bin/python" - "$ROOT/data" <<'PYTLS'
import sys
from network_supervisor import load_public_certificate_config
config = load_public_certificate_config(sys.argv[1])
if not config:
    raise SystemExit("Configuration du certificat public absente.")
print(config["hostname"])
PYTLS
)" || { echo "Configuration TLS publique invalide ; aucun repli non sécurisé n'est effectué."; exit 1; }
    echo "MaClasse est déjà lancé par systemd. Ouvre https://$PUBLIC_HOST:8765"
  else
    echo "MaClasse est déjà lancé par systemd. Ouvre https://$(openssl x509 -in "$ROOT/data/tls/server.crt" -noout -ext subjectAltName 2>/dev/null | grep -oE 'IP Address:[0-9.]+' | head -n1 | cut -d: -f2):8765"
  fi
  exit 0
fi
exec /usr/bin/bash "$ROOT/Lancer-MaClasse-Service-Linux.sh"
