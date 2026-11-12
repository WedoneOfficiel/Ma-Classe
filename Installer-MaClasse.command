#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

pause_on_error() {
  status=$?
  if [[ $status -ne 0 ]]; then
    echo
    echo "L'installation a échoué (code $status)."
    echo "Lis le message ci-dessus, corrige le problème puis relance ce fichier."
    read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  fi
}
trap pause_on_error EXIT

echo "MaClasse — installation macOS (Apple Silicon)"
echo "-----------------------------------------------"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Erreur : cet installateur est réservé à macOS."
  exit 1
fi

ARCH="$(/usr/bin/arch)"
if [[ "$ARCH" != "arm64" ]]; then
  echo "Erreur : lance cet installateur dans un Terminal natif Apple Silicon."
  echo "Architecture détectée : $ARCH"
  echo "Si Terminal utilise Rosetta, désactive Rosetta puis relance."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 est introuvable."
  echo "Installe Python 3.12 depuis https://www.python.org/downloads/macos/"
  exit 1
fi

python3 -c 'import platform,sys; assert platform.system()=="Darwin" and platform.machine()=="arm64", "Python doit fonctionner nativement sur Apple Silicon"; assert sys.version_info >= (3,10), "Python 3.10 minimum requis (3.12 recommandé)"; print("Python",platform.python_version(),platform.machine())'

echo
echo "Création de l'environnement Python isolé…"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m py_compile server.py

echo
echo "Installation terminée."
echo "Les données seront conservées dans data/."
echo "Pour démarrer MaClasse, double-clique sur Lancer-MaClasse.command."
echo "Le serveur restera limité à ce Mac (127.0.0.1)."
