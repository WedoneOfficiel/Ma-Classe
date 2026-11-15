#!/usr/bin/env bash
set -euo pipefail
[[ "$(uname -s)" == "Linux" ]] || { echo "Cet outil est réservé à Linux."; exit 1; }
command -v systemctl >/dev/null 2>&1 || exit 1
UNIT_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/maclasse.service"
systemctl --user disable --now maclasse.service 2>/dev/null || true
rm -f "$UNIT_FILE" "$UNIT_DIR/maclasse-update-apply.service"
systemctl --user daemon-reload
echo "Service MaClasse désinstallé. Le dossier du programme et les données n'ont pas été supprimés."
echo "Le maintien de session (linger) n'a pas été modifié."
