#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
cd "$ROOT"
DATA="$ROOT/data"
PROGRAM_ROOT="$DATA/program"
VERSIONS="$PROGRAM_ROOT/versions"
CURRENT="$PROGRAM_ROOT/current"
STATE="$DATA/update-state.json"
SERVICE_LABEL="fr.maclasse.server"
UPDATE_PLIST="$HOME/Library/LaunchAgents/fr.maclasse.update.plist"
SERVICE_PLIST="$HOME/Library/LaunchAgents/fr.maclasse.server.plist"
UID_NOW="$(id -u)"
write_state() {
  UPDATE_STATUS="$1" UPDATE_ERROR="${2:-}" STATE_FILE="$STATE" "$ROOT/.venv/bin/python" - <<'PY'
import json,os,time
p=os.environ["STATE_FILE"]
try:
 with open(p,encoding="utf-8") as f: d=json.load(f)
except Exception: d={}
if not isinstance(d,dict): d={}
d.update(status=os.environ["UPDATE_STATUS"],updated_at=int(time.time()))
if os.environ.get("UPDATE_ERROR"): d["last_error"]=os.environ["UPDATE_ERROR"]
else: d.pop("last_error",None)
tmp=p+".tmp"
with open(tmp,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
os.replace(tmp,p)
PY
}
health_ok() {
  local expected="$1" host
  host="$(/usr/bin/openssl x509 -in "$DATA/tls/server.crt" -noout -ext subjectAltName 2>/dev/null | /usr/bin/grep -oE 'IP Address:[0-9.]+' | /usr/bin/head -n1 | /usr/bin/cut -d: -f2 || true)"
  [[ -n "$host" ]] || return 1
  /usr/bin/curl --silent --fail --connect-timeout 2 --max-time 4 --cacert "$DATA/tls/ca.crt" "https://$host:8765/api/health" 2>/dev/null | EXPECTED_VERSION="$expected" "$ROOT/.venv/bin/python" -c 'import json,os,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("ok") is True and d.get("version")==os.environ["EXPECTED_VERSION"] and d.get("database")=="ok" else 1)'
}
start_service() {
  /bin/launchctl bootstrap "gui/$UID_NOW" "$SERVICE_PLIST" 2>/dev/null || true
  /bin/launchctl kickstart -k "gui/$UID_NOW/$SERVICE_LABEL"
}
fail_restore() {
  local message="$1"
  echo "Échec : $message" >&2
  /bin/launchctl bootout "gui/$UID_NOW/$SERVICE_LABEL" >/dev/null 2>&1 || true
  if [[ -n "${PREVIOUS_LINK:-}" && -e "${PREVIOUS_REAL:-}" ]]; then
    /bin/ln -s "$PREVIOUS_LINK" "$CURRENT.rollback"
    "$ROOT/.venv/bin/python" - "$CURRENT.rollback" "$CURRENT" <<'PYLINK'
import os,sys
os.replace(sys.argv[1],sys.argv[2])
PYLINK
  fi
  if [[ -n "${BACKUP_FILE:-}" && -f "$BACKUP_FILE" ]]; then
    /bin/cp -p "$BACKUP_FILE" "$DATA/maclasse.json"
  else
    write_state rollback_failed "$message — sauvegarde de base absente ; serveur laissé arrêté."
    exit 1
  fi
  start_service
  for _ in {1..20}; do
    if health_ok "$PREVIOUS_VERSION"; then write_state failed "$message — version précédente restaurée."; exit 1; fi
    /bin/sleep 2
  done
  write_state rollback_failed "$message — restauration appliquée mais contrôle de santé de l'ancienne version en échec."
  exit 1
}
[[ "$(uname -s)" == "Darwin" ]] || { echo "Réservé à macOS." >&2; exit 1; }
[[ -f "$STATE" && -L "$CURRENT" && -f "$SERVICE_PLIST" ]] || { echo "Gestionnaire ou service launchd absent." >&2; exit 1; }
read -r VERSION SHA STATUS < <("$ROOT/.venv/bin/python" - "$STATE" <<'PY'
import json,re,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
v=str(d.get("version","")).lstrip("vV")
if not re.fullmatch(r"\d+\.\d+\.\d+",v): raise SystemExit("Version invalide.")
if not re.fullmatch(r"[a-f0-9]{64}",str(d.get("sha256",""))): raise SystemExit("SHA-256 invalide.")
if d.get("status")!="prepared": raise SystemExit("Aucune version prête.")
print(v,d["sha256"],d["status"])
PY
)
TARGET="$VERSIONS/V$VERSION"
[[ -d "$TARGET" && ! -L "$TARGET" && -x "$TARGET/.venv/bin/python" && -f "$TARGET/maclasse-runtime-ready.json" ]] || { echo "Version préparée incomplète." >&2; exit 1; }
EXPECTED="$("$ROOT/.venv/bin/python" - "$TARGET/maclasse-prepared.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8")); print(d.get("sha256",""))
PY
)"
[[ "$EXPECTED" == "$SHA" ]] || { echo "Manifeste préparé incohérent." >&2; exit 1; }
PREVIOUS_LINK="$(/usr/bin/readlink "$CURRENT")"
PREVIOUS_REAL="$(cd "$(dirname "$CURRENT")" && cd "$(readlink "$CURRENT")" && pwd -P)"
PREVIOUS_VERSION="$("$ROOT/.venv/bin/python" - "$PREVIOUS_REAL/VERSION.txt" <<'PY'
import re,sys
from pathlib import Path
v=Path(sys.argv[1]).read_text(encoding="utf-8").strip().lstrip("vV")
if not re.fullmatch(r"\d+\.\d+\.\d+",v): raise SystemExit("Version précédente invalide.")
print(v)
PY
)"
STAMP="$(/bin/date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$DATA/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/maclasse-avant-maj-$STAMP.json"
[[ -f "$DATA/maclasse.json" ]] || { echo "Base de données absente." >&2; exit 1; }
/bin/cp -p "$DATA/maclasse.json" "$BACKUP_FILE"
"$ROOT/.venv/bin/python" -c 'import json,sys; json.load(open(sys.argv[1],encoding="utf-8"))' "$BACKUP_FILE" || { echo "Sauvegarde JSON invalide." >&2; exit 1; }
write_state installing
SERVICE_PID="$(/bin/launchctl list "$SERVICE_LABEL" 2>/dev/null | /usr/bin/awk 'NR==1 {print $1}' || true)"
/bin/launchctl bootout "gui/$UID_NOW/$SERVICE_LABEL" || { write_state failed "Impossible d'arrêter proprement launchd."; exit 1; }
if [[ "$SERVICE_PID" =~ ^[0-9]+$ ]]; then
  STOPPED=0
  for _ in {1..120}; do
    if ! /bin/kill -0 "$SERVICE_PID" >/dev/null 2>&1; then STOPPED=1; break; fi
    /bin/sleep 1
  done
  if [[ "$STOPPED" != "1" ]]; then
    write_state failed "Le serveur n'a pas terminé son arrêt gracieux en 120 secondes ; aucune bascule n'a été effectuée."
    exit 1
  fi
fi
/bin/ln -s "versions/V$VERSION" "$CURRENT.next"
"$ROOT/.venv/bin/python" - "$CURRENT.next" "$CURRENT" <<'PYLINK' || fail_restore "Bascule atomique impossible."
import os,sys
os.replace(sys.argv[1],sys.argv[2])
PYLINK
start_service || fail_restore "Redémarrage launchd impossible."
healthy=0
for _ in {1..20}; do
  if health_ok "$VERSION"; then healthy=1; break; fi
  /bin/sleep 2
done
[[ "$healthy" == "1" ]] || fail_restore "Le contrôle de santé n'a pas confirmé la nouvelle version."
write_state installed
if [[ -f "$DATA/update-maintenance.json" ]]; then
  "$ROOT/.venv/bin/python" - "$DATA/update-maintenance.json" <<'PY'
import json,os,sys,time
p=sys.argv[1]
try:
 d=json.load(open(p,encoding="utf-8"))
 if isinstance(d,dict) and d.get("status") in ("scheduled","installing"):
  d.update(status="completed",updated_at=int(time.time()))
  t=p+".tmp"; json.dump(d,open(t,"w",encoding="utf-8"),ensure_ascii=False,indent=2); os.replace(t,p)
except (OSError,ValueError): pass
PY
fi
echo "MaClasse $VERSION installée et contrôlée."
