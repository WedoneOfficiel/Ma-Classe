#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
fail(){ echo "Mise à jour interrompue : $1"; exit 1; }
[[ -d .git ]] || fail "Cette installation n'est pas un clone Git."
[[ -x .venv/bin/python ]] || fail "Environnement Python absent ; lance Installer-MaClasse-Linux.sh."
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" =~ WedoneOfficiel/Ma-Classe(\.git)?$ ]] || fail "Le dépôt distant origin n'est pas le dépôt officiel MaClasse."
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "main" ]] || fail "La branche active doit être main (branche actuelle : $BRANCH)."
[[ -z "$(git status --porcelain)" ]] || fail "Modifications locales détectées ; aucune donnée ne sera écrasée."
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="../MaClasse-sauvegarde-avant-maj-$STAMP"; mkdir -p "$BACKUP"
if [[ -d data ]]; then cp -a data "$BACKUP/data"; fi
PREVIOUS="$(git rev-parse HEAD)"; git fetch origin main
git merge-base --is-ancestor "$PREVIOUS" origin/main || fail "Branche locale divergente ; aucune réinitialisation automatique."
git merge --ff-only origin/main || fail "Mise à jour Git impossible."
.venv/bin/python -m pip install -r requirements.txt || fail "Échec dépendances ; sauvegarde conservée."
.venv/bin/python -m py_compile server.py || fail "Échec compilation serveur."
echo "MaClasse $(cat VERSION.txt) mise à jour. Sauvegarde : $BACKUP"
