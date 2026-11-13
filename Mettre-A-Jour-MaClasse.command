#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

fail() { echo; echo "Mise à jour interrompue : $1"; read -r -p "Appuie sur Entrée pour fermer… " _ || true; exit 1; }

if [[ ! -d .git ]] || ! command -v git >/dev/null 2>&1; then
  fail "Cette installation n'est pas un clone Git. N'utilise pas ce script pour cette installation."
fi
if [[ ! -x .venv/bin/python ]]; then
  fail "L'environnement Python est absent. Lance d'abord Installer-MaClasse.command."
fi
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" =~ WedoneOfficiel/Ma-Classe(\.git)?$ ]] || fail "Le dépôt distant origin n'est pas le dépôt officiel MaClasse."
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "main" ]] || fail "La branche active doit être main (branche actuelle : $BRANCH)."
if [[ -n "$(git status --porcelain)" ]]; then
  fail "Des fichiers locaux ont été modifiés. La mise à jour s'arrête pour ne rien écraser."
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="../MaClasse-sauvegarde-avant-maj-$STAMP"
mkdir -p "$BACKUP"
if [[ -d data ]]; then /usr/bin/ditto data "$BACKUP/data"; fi
echo "Sauvegarde locale créée : $BACKUP"
PREVIOUS="$(git rev-parse HEAD)"
echo "Récupération de la version officielle…"
git fetch origin main
git merge-base --is-ancestor "$PREVIOUS" origin/main || fail "La branche locale diverge de main. Aucune réinitialisation automatique n'est effectuée."
git merge --ff-only origin/main || fail "La mise à jour Git n'a pas pu être appliquée en avance rapide."
echo "Mise à jour des dépendances…"
.venv/bin/python -m pip install -r requirements.txt || fail "Échec de mise à jour des dépendances. Les données restent sauvegardées."
.venv/bin/python -m py_compile server.py || fail "La vérification Python a échoué."
echo
echo "Mise à jour terminée — version $(cat VERSION.txt)."
echo "Données locales conservées dans data/."
echo "Sauvegarde préalable : $BACKUP"
echo "Tu peux maintenant lancer Lancer-MaClasse.command."
