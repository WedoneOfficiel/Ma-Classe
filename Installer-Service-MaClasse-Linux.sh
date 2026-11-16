#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == "Linux" ]] || { echo "Cet installateur de service est réservé à Linux."; exit 1; }
[[ -x .venv/bin/python ]] || { echo "Lance d'abord ./Installer-MaClasse-Linux.sh."; exit 1; }
command -v systemctl >/dev/null 2>&1 || { echo "systemd est requis."; exit 1; }
command -v loginctl >/dev/null 2>&1 || { echo "loginctl est requis pour activer le démarrage au boot."; exit 1; }
for dependency in systemd-analyze curl openssl realpath python3; do
  command -v "$dependency" >/dev/null 2>&1 || { echo "Dépendance manquante : $dependency."; exit 1; }
done
ROOT="$(pwd -P)"
[[ "$(id -u)" -ne 0 ]] || { echo "Lance cet installateur depuis le compte utilisateur MaClasse, sans sudo devant le script."; exit 1; }
USER_NAME="$(id -un)"
if [[ ! "$ROOT" =~ ^/[A-Za-z0-9_./-]+$ ]]; then echo "Déplace MaClasse dans un chemin simple (lettres, chiffres, /, ., _ ou -) pour systemd."; exit 1; fi
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_FILE="$UNIT_DIR/maclasse.service"
mkdir -p "$UNIT_DIR"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=MaClasse — serveur scolaire
After=default.target

[Service]
Type=simple
Environment=MACLASSE_SUPERVISED=systemd
WorkingDirectory=$ROOT
ExecStart=/usr/bin/bash $ROOT/Lancer-MaClasse-Service-Linux.sh
Restart=on-failure
RestartSec=5
TimeoutStopSec=120
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

UPDATE_UNIT_FILE="$UNIT_DIR/maclasse-update-apply.service"
cat > "$UPDATE_UNIT_FILE" <<EOF
[Unit]
Description=MaClasse — installation indépendante d'une mise à jour
After=default.target

[Service]
Type=oneshot
WorkingDirectory=$ROOT
Environment=MACLASSE_ROOT=$ROOT
ExecStart=/usr/bin/bash $ROOT/data/program/current/Appliquer-Mise-A-Jour-MaClasse-Linux.sh
TimeoutStartSec=900
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=$ROOT/data
EOF
chmod 600 "$UPDATE_UNIT_FILE"
touch "$ROOT/data/update-manager.enabled"
chmod 600 "$ROOT/data/update-manager.enabled"

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
echo "Le service d’application des mises à jour est installé mais ne démarre qu’à la demande de MaClasse."
