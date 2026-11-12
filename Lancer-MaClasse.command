#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

URL="http://127.0.0.1:8765"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "MaClasse V25 est configurée pour macOS."
  exit 1
fi

if [[ ! -x ".venv/bin/python" ]]; then
  echo "L'environnement MaClasse n'est pas installé."
  echo "Double-clique d'abord sur Installer-MaClasse.command."
  read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  exit 1
fi

if ! .venv/bin/python -c "import reportlab" >/dev/null 2>&1; then
  echo "Les dépendances semblent incomplètes."
  echo "Relance Installer-MaClasse.command."
  read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  exit 1
fi

echo "MaClasse V25.0.7 démarre sur ce Mac."
echo "Adresse locale : $URL"
echo "Le serveur n'est pas accessible depuis le Wi-Fi ou Internet."
echo "Laisse cette fenêtre ouverte. Pour arrêter MaClasse : Ctrl+C."
echo

if ! open -a "Firefox" "$URL" >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
fi

exec .venv/bin/python server.py
