#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
UPDATED=0
PREVIOUS=""
BACKUP=""
rollback() {
  if [[ "$UPDATED" == "1" ]]; then
    echo "La validation a échoué : retour à la version précédente…"
    git reset --hard "$PREVIOUS" || echo "Attention : restauration Git à terminer manuellement."
    .venv/bin/python -m pip install -r requirements.txt || echo "Attention : dépendances précédentes à réinstaller."
    UPDATED=0
    echo "Le dossier de sauvegarde des données reste disponible : $BACKUP"
  fi
}
fail() {
  echo
  echo "Mise à jour interrompue : $1"
  rollback
  read -r -p "Appuie sur Entrée pour fermer… " _ || true
  exit 1
}
if [[ ! -d .git ]] || ! command -v git >/dev/null 2>&1; then fail "Cette installation n'est pas un clone Git. N'utilise pas ce script pour cette installation."; fi
if [[ ! -x .venv/bin/python ]]; then fail "L'environnement Python est absent. Lance d'abord Installer-MaClasse.command."; fi
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" =~ WedoneOfficiel/Ma-Classe(\.git)?$ ]] || fail "Le dépôt distant origin n'est pas le dépôt officiel MaClasse."
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "main" ]] || fail "La branche active doit être main (branche actuelle : $BRANCH)."
if [[ -n "$(git status --porcelain)" ]]; then fail "Des fichiers locaux ont été modifiés. La mise à jour s'arrête pour ne rien écraser."; fi
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="../MaClasse-sauvegarde-avant-maj-$STAMP"
mkdir -p "$BACKUP"
if [[ -d data ]]; then /usr/bin/ditto data "$BACKUP/data"; fi
PREVIOUS="$(git rev-parse HEAD)"
PREVIOUS_VERSION="$(cat VERSION.txt)"
printf "Version précédente : %s\nCommit précédent : %s\nDate : %s\n" "$PREVIOUS_VERSION" "$PREVIOUS" "$STAMP" > "$BACKUP/INFORMATIONS.txt"
echo "Sauvegarde créée : $BACKUP (base, pièces jointes et fichiers de data/)."
echo "Récupération de la version officielle…"
git fetch origin main || fail "Impossible de récupérer la version officielle."
git merge-base --is-ancestor "$PREVIOUS" origin/main || fail "La branche locale diverge de main. Aucune réinitialisation automatique n'est effectuée."
git merge --ff-only origin/main || fail "La mise à jour Git n'a pas pu être appliquée en avance rapide."
UPDATED=1
echo "Mise à jour des dépendances…"
.venv/bin/python -m pip install -r requirements.txt || fail "Échec de mise à jour des dépendances."
.venv/bin/python -m py_compile server.py || fail "La vérification Python a échoué."
VERSION="$(cat VERSION.txt)" || fail "Fichier VERSION.txt illisible."
VERSION_NUMBER="$(printf '%s' "$VERSION" | sed 's/^V//')"
grep -Fq "APP_VERSION='$VERSION_NUMBER'" server.py || fail "La version du serveur ne correspond pas à VERSION.txt."
grep -Fq "const MC_VERSION='V$VERSION_NUMBER'" _all.js || fail "La version de l'interface ne correspond pas à VERSION.txt."
if command -v node >/dev/null 2>&1; then node --check _all.js || fail "La vérification JavaScript a échoué."; else echo "Node.js absent : vérification JavaScript reportée aux tests de publication."; fi
UPDATED=0
echo
echo "Mise à jour terminée — version $VERSION."
echo "Données locales conservées dans data/."
echo "Sauvegarde préalable : $BACKUP"
echo "Tu peux maintenant lancer Lancer-MaClasse.command."