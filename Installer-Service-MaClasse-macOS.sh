#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
[[ "$(uname -s)" == "Darwin" ]] || { echo "Cet installateur est réservé à macOS."; exit 1; }
[[ -x "$ROOT/.venv/bin/python" ]] || { echo "Lance d'abord Installer-MaClasse.command."; exit 1; }
[[ -f "$ROOT/data/tls/server.crt" && -f "$ROOT/data/tls/server.key" && -f "$ROOT/data/tls/ca.crt" ]] || { echo "Initialise d'abord le mode réseau MaClasse pour créer les certificats TLS."; exit 1; }
[[ "$(id -u)" -ne 0 ]] || { echo "Ne lance pas ce script avec sudo."; exit 1; }
LABEL="fr.maclasse.server"
UPDATE_LABEL="fr.maclasse.update"
AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$AGENTS" "$ROOT/data/program"
if command -v pgrep >/dev/null 2>&1 && pgrep -f '[p]ython.*server[.]py' >/dev/null 2>&1; then
  RUNNING_PID="$(/bin/launchctl list "$LABEL" 2>/dev/null | /usr/bin/awk 'NR==1 {print $1}')"
  if [[ -z "$RUNNING_PID" || "$RUNNING_PID" == "-" ]]; then
    echo "Un serveur MaClasse lancé manuellement est déjà actif. Arrête-le avec Ctrl+C, puis relance cet installateur."
    exit 1
  fi
fi
chmod 700 "$ROOT/data" "$AGENTS"
CURRENT="$ROOT/data/program/current"
if [[ ! -e "$CURRENT" && ! -L "$CURRENT" ]]; then
  ln -s ../.. "$CURRENT"
fi
[[ -L "$CURRENT" ]] || { echo "Le chemin data/program/current existe mais n'est pas un lien symbolique ; aucune modification effectuée."; exit 1; }
TARGET="$(cd "$(dirname "$CURRENT")" && cd "$(readlink "$CURRENT")" && pwd -P)"
[[ "$TARGET" == "$ROOT" || "$TARGET" == "$ROOT/data/program/versions/"* ]] || { echo "La version active pointe hors du dossier MaClasse."; exit 1; }
ROOT_PATH="$ROOT" AGENTS_PATH="$AGENTS" LABEL="$LABEL" "$ROOT/.venv/bin/python" - <<'PY'
import os, plistlib
root=os.environ["ROOT_PATH"]
agents=os.environ["AGENTS_PATH"]
label=os.environ["LABEL"]
document={
    "Label": label,
    "ProgramArguments": ["/bin/bash", os.path.join(root,"Lancer-MaClasse-Service-macOS.sh")],
    "WorkingDirectory": root,
    "RunAtLoad": True,
    "KeepAlive": True,
    "ThrottleInterval": 5,
    "StandardOutPath": os.path.join(root,"data","macos-service.log"),
    "StandardErrorPath": os.path.join(root,"data","macos-service-error.log"),
    "ProcessType": "Background",
}
path=os.path.join(agents,label+".plist.tmp")
with open(path,"wb") as stream: plistlib.dump(document,stream,fmt=plistlib.FMT_XML,sort_keys=True)
os.chmod(path,0o600)
PY
/usr/bin/plutil -lint "$AGENTS/$LABEL.plist.tmp" >/dev/null
mv "$AGENTS/$LABEL.plist.tmp" "$AGENTS/$LABEL.plist"
chmod 600 "$AGENTS/$LABEL.plist"
printf 'enabled\n' > "$ROOT/data/update-manager.enabled.tmp"
mv "$ROOT/data/update-manager.enabled.tmp" "$ROOT/data/update-manager.enabled"
launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$AGENTS/$LABEL.plist"
launchctl kickstart -k "gui/$(id -u)/$LABEL"
echo "Supervision macOS installée. État : launchctl print gui/$(id -u)/$LABEL"
echo "Données et certificats conservés dans $ROOT/data."
