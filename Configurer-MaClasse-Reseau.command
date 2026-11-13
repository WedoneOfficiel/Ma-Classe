#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
exec bash ./Configurer-MaClasse-Reseau.sh "$@"
