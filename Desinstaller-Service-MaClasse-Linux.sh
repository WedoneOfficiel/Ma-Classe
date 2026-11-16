#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == "Linux" ]] || { echo "Cet outil est réservé à Linux."; exit 1; }
command -v systemctl >/dev/null 2>&1 || exit 1
ROOT="$(pwd -P)"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_FILE="$UNIT_DIR/maclasse.service"
UPDATE_UNIT_FILE="$UNIT_DIR/maclasse-update-apply.service"
TIMER_FILE="$UNIT_DIR/maclasse-update-scheduled.timer"

if systemctl --user is-active --quiet maclasse-update-apply.service; then
  echo "Une mise à jour est en cours. Attends sa fin avant de désinstaller le service."
  exit 1
fi
systemctl --user disable --now maclasse-update-scheduled.timer 2>/dev/null || true
if systemctl --user is-active --quiet maclasse-update-apply.service; then
  echo "Une mise à jour vient de démarrer. Attends sa fin avant de désinstaller le service."
  exit 1
fi
rm -f "$TIMER_FILE"
if [[ -f "$ROOT/data/update-maintenance.json" ]]; then
  /usr/bin/python3 - "$ROOT/data/update-maintenance.json" <<'PY'
import json, os, sys, time
path=sys.argv[1]
try:
    with open(path,encoding="utf-8") as f: state=json.load(f)
    if isinstance(state,dict) and state.get("status")=="scheduled":
        state["status"]="cancelled"
        state["cancelled_at"]=int(time.time())
        tmp=path+".tmp"
        with open(tmp,"w",encoding="utf-8") as f: json.dump(state,f,ensure_ascii=False,indent=2)
        os.replace(tmp,path)
except (OSError,ValueError):
    pass
PY
fi
systemctl --user disable --now maclasse.service 2>/dev/null || true
rm -f "$UNIT_FILE" "$UPDATE_UNIT_FILE"
rm -f "$ROOT/data/update-manager.enabled"
systemctl --user daemon-reload
echo "Service MaClasse désinstallé. Le dossier du programme et les données n'ont pas été supprimés."
echo "La maintenance programmée a été annulée. Le maintien de session (linger) n'a pas été modifié."
