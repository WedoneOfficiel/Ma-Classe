#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
echo
echo "Installation terminée. Tu peux maintenant lancer Lancer-MaClasse.command."
