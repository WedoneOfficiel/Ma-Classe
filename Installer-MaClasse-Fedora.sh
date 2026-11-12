#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 est introuvable. Installe-le avec : sudo dnf install python3 python3-pip"
  exit 1
fi

echo "Installation de MaClasse V25.0.7 pour Fedora…"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv || {
    echo "Impossible de créer l'environnement virtuel."
    echo "Sur Fedora, vérifie l'installation de python3 et python3-pip."
    exit 1
  }
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
chmod +x Lancer-MaClasse-Fedora.sh

echo
echo "Installation terminée."
echo "Lance ./Lancer-MaClasse-Fedora.sh pour démarrer MaClasse."
