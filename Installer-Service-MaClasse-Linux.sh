#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == "Linux" ]] || { echo "Cet installateur de service est réservé à Linux."; exit 1; }
[[ -x .venv/bin/python ]] || { echo "Lance d'abord ./Installer-MaClasse-Linux.sh."; exit 1; }
command -v systemctl >/dev/null 2>&1 || { echo "systemd est requis."; exit 1; }
command -v loginctl >/dev/null 2>&1 || { echo "loginctl est requis pour activer le démarrage au boot."; exit 1; }
ROOT="$(pwd -P)"
[[ "$(id -u)" -ne 0 ]] || { echo "Lance cet installateur depuis le compte utilisateur MaClasse, sans sudo devant le script."; exit 1; }
USER_NAME="$(id -un)"
if [[ ! "$ROOT" =~ ^/[A-Za-z0-9_./-]+$ ]]; then echo "Déplace MaClasse dans un chemin simple (lettres, chiffres, /, ., _ ou -) pour systemd."; exit 1; fi
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_FILE="$UNIT_DIR/maclasse.service"
mkdir -p "$UNIT_DIR"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=MaClasse — serveur scolaire
After=default.target

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=/usr/bin/bash $ROOT/Lancer-MaClasse-Service-Linux.sh
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
KillSignal=SIGINT
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=$ROOT/data

[Install]
WantedBy=default.target
EOF
chmod 600 "$UNIT_FILE"

# Le gestionnaire utilisateur doit rester actif après la fermeture de session et au redémarrage.
LINGER="$(loginctl show-user "$USER_NAME" -p Linger --value 2>/dev/null || true)"
if [[ "$LINGER" != "yes" ]]; then
  if [[ "$(id -u)" -eq 0 ]]; then
    loginctl enable-linger "$USER_NAME"
  else
    sudo loginctl enable-linger "$USER_NAME"
  fi
fi

systemctl --user daemon-reload
systemctl --user enable --now maclasse.service
sleep 2
if ! systemctl --user is-active --quiet maclasse.service; then
  echo "Le service MaClasse n'a pas démarré. Diagnostic :"
  systemctl --user --no-pager --full status maclasse.service || true
  exit 1
fi
echo "Service MaClasse installé et actif pour $USER_NAME."
echo "État : systemctl --user status maclasse.service"
echo "Journaux : journalctl --user -u maclasse.service -f"
echo "Arrêt : systemctl --user stop maclasse.service"
