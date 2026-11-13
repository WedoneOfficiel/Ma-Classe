#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "$(uname -s)" != "Linux" ]]; then echo "Cet installateur est réservé à Linux."; exit 1; fi
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || { echo "Python 3 est introuvable."; exit 1; }
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10 minimum requis"; print("Python",sys.version.split()[0])'
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m py_compile server.py
chmod +x ./*.sh
echo "Installation terminée. Les données restent dans data/."
echo "Pour un usage local : .venv/bin/python server.py"
echo "Pour le réseau privé HTTPS : ./Lancer-MaClasse-Reseau.sh"
