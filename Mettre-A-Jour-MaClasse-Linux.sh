#!/usr/bin/env bash
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
    echo "Sauvegarde des données conservée : $BACKUP"
  fi
}
fail() { echo "Mise à jour interrompue : $1"; rollback; exit 1; }
[[ -d .git ]] || fail "Cette installation n'est pas un clone Git."
[[ -x .venv/bin/python ]] || fail "Environnement Python absent ; lance Installer-MaClasse-Linux.sh."
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" =~ WedoneOfficiel/Ma-Classe(\.git)?$ ]] || fail "Le dépôt distant origin n'est pas le dépôt officiel MaClasse."
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "main" ]] || fail "La branche active doit être main (branche actuelle : $BRANCH)."
[[ -z "$(git status --porcelain)" ]] || fail "Modifications locales détectées ; aucune donnée ne sera écrasée."
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="../MaClasse-sauvegarde-avant-maj-$STAMP"
mkdir -p "$BACKUP"
if [[ -d data ]]; then cp -a data "$BACKUP/data"; fi
PREVIOUS="$(git rev-parse HEAD)"
PREVIOUS_VERSION="$(cat VERSION.txt)"
printf "Version précédente : %s\nCommit précédent : %s\nDate : %s\n" "$PREVIOUS_VERSION" "$PREVIOUS" "$STAMP" > "$BACKUP/INFORMATIONS.txt"
echo "Sauvegarde créée : $BACKUP (base, pièces jointes et fichiers de data/)."
git fetch origin main || fail "Impossible de récupérer la version officielle."
git merge-base --is-ancestor "$PREVIOUS" origin/main || fail "Branche locale divergente ; aucune réinitialisation automatique."
git merge --ff-only origin/main || fail "Mise à jour Git impossible."
UPDATED=1
.venv/bin/python -m pip install -r requirements.txt || fail "Échec de mise à jour des dépendances."
.venv/bin/python -m py_compile server.py || fail "Échec compilation serveur."
VERSION="$(cat VERSION.txt)" || fail "Fichier VERSION.txt illisible."
VERSION_NUMBER="$(printf '%s' "$VERSION" | sed 's/^V//')"
grep -Fq "APP_VERSION='$VERSION_NUMBER'" server.py || fail "La version du serveur ne correspond pas à VERSION.txt."
grep -Fq "const MC_VERSION='V$VERSION_NUMBER'" _all.js || fail "La version de l'interface ne correspond pas à VERSION.txt."
if command -v node >/dev/null 2>&1; then node --check _all.js || fail "La vérification JavaScript a échoué."; else echo "Node.js absent : vérification JavaScript reportée aux tests de publication."; fi
UPDATED=0
echo "MaClasse $VERSION mise à jour. Sauvegarde : $BACKUP"