#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "MaClasse n'est pas installé. Lance d'abord ./Installer-MaClasse-Fedora.sh"
  exit 1
fi

echo "Démarrage de MaClasse V25.0.7 — édition sans IA…"
echo "Adresse locale : http://127.0.0.1:8765"
echo "Arrêt : Ctrl+C"
exec .venv/bin/python server.py
