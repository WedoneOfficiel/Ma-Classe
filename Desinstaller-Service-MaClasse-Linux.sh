#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == "Linux" ]] || { echo "Cet outil est réservé à Linux."; exit 1; }
command -v systemctl >/dev/null 2>&1 || exit 1
ROOT="$(pwd -P)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_FILE="$UNIT_DIR/maclasse.service"
UPDATE_UNIT_FILE="$UNIT_DIR/maclasse-update-apply.service"
systemctl --user disable --now maclasse.service 2>/dev/null || true
systemctl --user stop maclasse-update-apply.service 2>/dev/null || true
rm -f "$UNIT_FILE" "$UPDATE_UNIT_FILE"
rm -f "$ROOT/data/update-manager.enabled"
systemctl --user daemon-reload
echo "Service MaClasse désinstallé. Le dossier du programme et les données n'ont pas été supprimés."
echo "Le maintien de session (linger) n'a pas été modifié."
