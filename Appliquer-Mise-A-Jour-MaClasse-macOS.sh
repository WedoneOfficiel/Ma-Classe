#!/usr/bin/env bash
set -euo pipefail
umask 077
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
if [[ -n "${MACLASSE_ROOT:-}" ]]; then
  ROOT="$MACLASSE_ROOT"
elif [[ -d "$SCRIPT_DIR/data" ]]; then
  ROOT="$SCRIPT_DIR"
else
  ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
fi
ROOT_INPUT="$ROOT"
if [[ "$ROOT_INPUT" != /* ]]; then ROOT_INPUT="$(cd "$ROOT_INPUT" && pwd -L)"; fi
ROOT="$(cd "$ROOT" && pwd -P)"
cd "$ROOT"
DATA="${MACLASSE_DATA_DIR:-$ROOT/data}"
DATA="$(cd "$DATA" && pwd -P)"
PROGRAM_ROOT="$DATA/program"
VERSIONS="$PROGRAM_ROOT/versions"
CURRENT="$PROGRAM_ROOT/current"
STATE="$DATA/update-state.json"
SERVICE_LABEL="fr.maclasse.server"
UPDATE_PLIST="$HOME/Library/LaunchAgents/fr.maclasse.update.plist"
SERVICE_PLIST="$HOME/Library/LaunchAgents/fr.maclasse.server.plist"
UID_NOW="$(id -u)"
SERVICE_DISABLED=0
restore_service_enabled() {
  if [[ "$SERVICE_DISABLED" == "1" ]]; then
    /bin/launchctl enable "gui/$UID_NOW/$SERVICE_LABEL" >/dev/null 2>&1 || true
    SERVICE_DISABLED=0
  fi
}
trap restore_service_enabled EXIT
exec 9>"$DATA/update-apply.lock"
if ! "$ROOT/.venv/bin/python" -c 'import fcntl; fcntl.flock(9, fcntl.LOCK_EX | fcntl.LOCK_NB)' 2>/dev/null; then
  echo "Une autre mise à jour est en cours ou un serveur manuel utilise encore le verrou partagé ; arrête-le avant de continuer." >&2
  exit 1
fi
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
write_maintenance_state() {
  local status="$1"
  "$ROOT/.venv/bin/python" - "$DATA/update-maintenance.json" "$status" <<'PY'
import json,os,sys,time
path,status=sys.argv[1],sys.argv[2]
try:
    with open(path,encoding="utf-8") as stream: data=json.load(stream)
    if isinstance(data,dict) and data.get("status") in ("scheduled","installing"):
        data.update(status=status,updated_at=int(time.time()))
        tmp=path+".tmp"
        with open(tmp,"w",encoding="utf-8") as stream: json.dump(data,stream,ensure_ascii=False,indent=2)
        os.replace(tmp,path)
except (OSError,ValueError):
    pass
PY
}
health_ok() {
  local expected="$1" host response http_status body_file
  # Parse the certificate SAN with Python rather than OpenSSL/LibreSSL display text.
  host="$("$ROOT/.venv/bin/python" - "$DATA/tls/server.crt" <<'PYSAN' 2>/dev/null || true
import ipaddress, ssl, sys
certificate = ssl._ssl._test_decode_cert(sys.argv[1])
for kind, value in certificate.get("subjectAltName", ()):
    if kind == "IP Address":
        try:
            print(ipaddress.ip_address(value))
            break
        except ValueError:
            pass
PYSAN
)"
  if [[ -z "$host" ]]; then
    echo "DEBUG health: aucun SAN IP exploitable dans $DATA/tls/server.crt." >&2
    /usr/bin/openssl x509 -in "$DATA/tls/server.crt" -noout -ext subjectAltName >&2 2>/dev/null || true
    return 2
  fi
  # Distinguish an unreachable service (retry) from an explicit unhealthy
  # HTTP response (fail immediately instead of wasting the full retry window).
  body_file="$(/usr/bin/mktemp "$DATA/.health-check.XXXXXX")" || return 2
  if ! http_status="$(/usr/bin/curl --noproxy '*' --silent --connect-timeout 2 --max-time 4 --cacert "$DATA/tls/ca.crt" --output "$body_file" --write-out '%{http_code}' "https://$host:8765/api/health" 2>/dev/null)"; then
    echo "DEBUG health: aucune réponse HTTPS pour $expected." >&2
    /bin/rm -f "$body_file"
    return 2
  fi
  if [[ "$http_status" != "200" ]]; then
    echo "DEBUG health: HTTP $http_status pour $expected." >&2
    /bin/rm -f "$body_file"
    return 1
  fi
  if ! EXPECTED_VERSION="$expected" "$ROOT/.venv/bin/python" -c 'import json,os,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); sys.exit(0 if d.get("ok") is True and d.get("version")==os.environ["EXPECTED_VERSION"] and d.get("database")=="ok" else 1)' "$body_file"; then
    echo "DEBUG health: réponse JSON invalide pour $expected : $(/bin/cat "$body_file" 2>/dev/null)." >&2
    /bin/rm -f "$body_file"
    return 1
  fi
  echo "DEBUG health: version $expected validée." >&2
  /bin/rm -f "$body_file"
  return 0
}
start_service() {
  /bin/launchctl enable "gui/$UID_NOW/$SERVICE_LABEL"
  SERVICE_DISABLED=0
  /bin/launchctl bootstrap "gui/$UID_NOW" "$SERVICE_PLIST" 2>/dev/null || true
  /bin/launchctl kickstart "gui/$UID_NOW/$SERVICE_LABEL"
}
owned_service_pids() {
  local root_input="${ROOT_INPUT:-$ROOT}"
  /bin/ps -axo pid=,command= | /usr/bin/awk -v root="$ROOT" -v root_input="$root_input" '
    $1 ~ /^[0-9]+$/ && NF >= 2 {
      command = substr($0, index($0, $2))
      if ((index(command, root "/") > 0 || index(command, root_input "/") > 0) &&
          command ~ /[pP]ython/ && command ~ /(network_supervisor|server)[.]py/) print $1
    }'
}
pid_is_in_list() {
  local candidate="$1" process_list="$2"
  [[ "$candidate" =~ ^[0-9]+$ ]] || return 1
  /usr/bin/grep -Fxq -- "$candidate" <<< "$process_list"
}
stop_owned_service_processes() {
  local owned_pids pid
  owned_pids="$(owned_service_pids)" || return 1
  [[ -n "$owned_pids" ]] || return 0
  echo "DEBUG updater: processus du dossier courant détectés sans PID launchd : $owned_pids." >&2

  while IFS= read -r pid; do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    /bin/kill -TERM "$pid" >/dev/null 2>&1 || true
  done <<< "$owned_pids"
  for _ in {1..5}; do
    owned_pids="$(owned_service_pids)" || return 1
    [[ -z "$owned_pids" ]] && return 0
    /bin/sleep 1
  done

  echo "DEBUG updater: arrêt gracieux du processus orphelin incomplet ; arrêt forcé ciblé." >&2
  while IFS= read -r pid; do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    /bin/kill -KILL "$pid" >/dev/null 2>&1 || true
  done <<< "$owned_pids"
  for _ in {1..5}; do
    owned_pids="$(owned_service_pids)" || return 1
    [[ -z "$owned_pids" ]] && return 0
    /bin/sleep 1
  done
  echo "Impossible d'arrêter tous les processus MaClasse appartenant à $ROOT : $owned_pids" >&2
  return 1
}
stop_service_and_confirm() {
  local service_pid probe loaded=0 bootout_pid pgrep_status server_pids
  # A launchd job can remain loaded in the waiting/throttled state after its
  # process has already exited. A missing PID is therefore not, by itself,
  # proof that shutdown failed.
  if probe="$(/bin/launchctl print "gui/$UID_NOW/$SERVICE_LABEL" 2>&1)"; then
    loaded=1
  else
    case "$probe" in
      *"Could not find service"*) loaded=0 ;;
      *)
        echo "Impossible de déterminer l'état launchd : $probe" >&2
        return 1
        ;;
    esac
  fi
  service_pid="$(printf '%s\n' "$probe" | /usr/bin/awk '$1 == "pid" && $2 == "=" && $3 ~ /^[0-9]+$/ && $3 > 0 {print $3; exit}' || true)"
  if [[ "$service_pid" =~ ^[0-9]+$ ]]; then
    echo "DEBUG updater: PID du serveur identifié ($service_pid)." >&2
  elif [[ "$loaded" == "1" ]]; then
    echo "DEBUG updater: job launchd chargé mais aucun PID actif ; arrêt idempotent." >&2
  fi

  # If launchd has already unloaded the job, still prove that no Python
  # supervisor/server process remains before allowing a database restore.
  if [[ "$loaded" == "0" ]]; then
    if ! stop_owned_service_processes; then return 1; fi
    if server_pids="$(/usr/bin/pgrep -f '[p]ython.*(network_supervisor|server)[.]py' 2>/dev/null)"; then
      echo "Un processus MaClasse subsiste alors que le job launchd est absent : $server_pids" >&2
      return 1
    else
      pgrep_status=$?
      [[ "$pgrep_status" == "1" ]] || return 1
    fi
    echo "DEBUG updater: job launchd absent et aucun processus serveur actif." >&2
    return 0
  fi

  # Désactiver d'abord KeepAlive : sinon launchd peut relancer le processus
  # après SIGKILL pendant que bootout attend encore sa terminaison.
  /bin/launchctl disable "gui/$UID_NOW/$SERVICE_LABEL" || return 1
  SERVICE_DISABLED=1
  echo "DEBUG updater: launchctl disable terminé." >&2

  # bootout peut attendre indéfiniment server_close() si un client TLS inactif
  # conserve un thread de requête. Le lancer en arrière-plan borne l'arrêt.
  /bin/launchctl bootout "gui/$UID_NOW/$SERVICE_LABEL" >/dev/null 2>&1 &
  bootout_pid=$!
  echo "DEBUG updater: bootout lancé en arrière-plan (PID $bootout_pid)." >&2

  # Laisser au serveur 25 s pour son arrêt gracieux (timeout HTTP : 20 s).
  if [[ "$service_pid" =~ ^[0-9]+$ ]]; then
    for _ in {1..25}; do
      if ! /bin/kill -0 "$service_pid" >/dev/null 2>&1; then break; fi
      /bin/sleep 1
    done

    echo "DEBUG updater: délai gracieux terminé." >&2

    # Sécurité : un arrêt gracieux bloqué ne doit pas figer la mise à jour.
    # La sauvegarde attendra toujours la confirmation de la mort du PID.
    if /bin/kill -0 "$service_pid" >/dev/null 2>&1; then
      echo "Arrêt gracieux bloqué ; arrêt forcé du serveur PID $service_pid." >&2
      /bin/kill -KILL "$service_pid" >/dev/null 2>&1 || true
    fi
    echo "DEBUG updater: vérification après arrêt forcé." >&2
    for _ in {1..10}; do
      if ! /bin/kill -0 "$service_pid" >/dev/null 2>&1; then break; fi
      /bin/sleep 1
    done
    /bin/kill -0 "$service_pid" >/dev/null 2>&1 && return 1
  fi

  # Confirm both sides of the shutdown: launchd no longer owns the job and
  # no Python server/supervisor process remains. A waiting job with no PID is
  # not accepted until bootout has removed it from the GUI domain.
  for _ in {1..10}; do
    if probe="$(/bin/launchctl print "gui/$UID_NOW/$SERVICE_LABEL" 2>&1)"; then
      loaded=1
    else
      case "$probe" in
        *"Could not find service"*) loaded=0 ;;
        *) echo "DEBUG updater: état launchd indéterminé après bootout : $probe" >&2; return 1 ;;
      esac
    fi
    if [[ "$loaded" == "0" ]]; then
      if ! stop_owned_service_processes; then
        echo "DEBUG updater: impossible de confirmer l'arrêt des processus du dossier courant." >&2
        return 1
      fi
      if server_pids="$(/usr/bin/pgrep -f '[p]ython.*(network_supervisor|server)[.]py' 2>/dev/null)"; then
        echo "DEBUG updater: processus serveur encore actif après bootout : $server_pids" >&2
        return 1
      else
        pgrep_status=$?
        [[ "$pgrep_status" == "1" ]] || return 1
      fi
      echo "DEBUG updater: service launchd déchargé et aucun processus MaClasse actif." >&2
      /bin/kill "$bootout_pid" >/dev/null 2>&1 || true
      return 0
    fi
    /bin/sleep 1
  done
  /bin/kill "$bootout_pid" >/dev/null 2>&1 || true
  return 1
}
fail_restore() {
  local message="$1"
  echo "Échec : $message" >&2
  if ! stop_service_and_confirm; then
    write_state rollback_failed "$message — arrêt du nouveau serveur non confirmé ; restauration de la base interdite pour protéger les données."
    write_maintenance_state failed
    echo "ATTENTION : le nouveau serveur semble toujours actif. Le code et la base ne seront pas restaurés tant que son arrêt n'est pas confirmé." >&2
    exit 1
  fi
  if [[ -z "${PREVIOUS_LINK:-}" || -z "${PREVIOUS_REAL:-}" || ! -d "$PREVIOUS_REAL" ]]; then
    write_state rollback_failed "$message — version précédente absente ou invalide ; base non restaurée et serveur laissé arrêté."
    write_maintenance_state failed
    echo "ATTENTION : version précédente introuvable. Le serveur reste arrêté et la base n'est pas remplacée." >&2
    exit 1
  fi
  /bin/rm -f "$CURRENT.rollback"
  if ! /bin/ln -s "$PREVIOUS_LINK" "$CURRENT.rollback" ||
     ! "$ROOT/.venv/bin/python" - "$CURRENT.rollback" "$CURRENT" <<'PYLINK'
import os,sys
os.replace(sys.argv[1],sys.argv[2])
PYLINK
  then
    /bin/rm -f "$CURRENT.rollback"
    write_state rollback_failed "$message — impossible de réactiver le lien de la version précédente ; base non restaurée."
    write_maintenance_state failed
    exit 1
  fi
  if [[ -n "${BACKUP_FILE:-}" && -f "$BACKUP_FILE" ]]; then
    RESTORE_TMP="$DATA/maclasse.json.rollback.$RANDOM-$PPID.tmp"
    /bin/rm -f "$RESTORE_TMP"
    if ! /bin/cp -p "$BACKUP_FILE" "$RESTORE_TMP"; then
      write_state rollback_failed "$message — copie temporaire de la base impossible ; serveur laissé arrêté."
      write_maintenance_state failed
      exit 1
    fi
    if ! "$ROOT/.venv/bin/python" - "$RESTORE_TMP" "$DATA/maclasse.json" <<'PYRESTORE'
import os,sys
source,destination=sys.argv[1],sys.argv[2]
with open(source,"rb") as stream: os.fsync(stream.fileno())
os.replace(source,destination)
directory=os.open(os.path.dirname(destination),os.O_RDONLY)
try:
    os.fsync(directory)
except OSError:
    pass
finally:
    os.close(directory)
PYRESTORE
    then
      /bin/rm -f "$RESTORE_TMP"
      write_state rollback_failed "$message — restauration atomique de la base impossible ; serveur laissé arrêté."
      write_maintenance_state failed
      exit 1
    fi
  else
    write_state rollback_failed "$message — sauvegarde de base absente ; serveur laissé arrêté."
    write_maintenance_state failed
    exit 1
  fi
  if ! start_service; then
    write_state rollback_failed "$message — impossible de redémarrer la version précédente."
    write_maintenance_state failed
    exit 1
  fi
  for _ in {1..20}; do
    if health_ok "$PREVIOUS_VERSION"; then
      write_state failed "$message — version précédente restaurée."
      write_maintenance_state failed
      exit 1
    fi
    /bin/sleep 2
  done
  write_state rollback_failed "$message — restauration appliquée mais contrôle de santé de l'ancienne version en échec."
  write_maintenance_state failed
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
[[ -d "$TARGET" && ! -L "$TARGET" && -x "$TARGET/.venv/bin/python" && -f "$TARGET/maclasse-runtime-ready.json" && -f "$TARGET/server.py" && -f "$TARGET/_all.js" ]] || { echo "Version préparée incomplète." >&2; exit 1; }
TARGET_REAL="$(cd "$TARGET" && pwd -P)"
VERSIONS_REAL="$(cd "$VERSIONS" && pwd -P)"
[[ "$TARGET_REAL" == "$VERSIONS_REAL/"* ]] || { echo "Dossier de version hors du stockage autorisé." >&2; exit 1; }
grep -Fq "APP_VERSION='$VERSION'" "$TARGET/server.py" || { echo "Version du serveur incohérente." >&2; exit 1; }
grep -Fq "const MC_VERSION='V$VERSION'" "$TARGET/_all.js" || { echo "Version de l'interface incohérente." >&2; exit 1; }
grep -Fxq "V$VERSION" "$TARGET/VERSION.txt" || { echo "VERSION.txt incohérent." >&2; exit 1; }
EXPECTED="$("$ROOT/.venv/bin/python" - "$TARGET/maclasse-prepared.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8")); print(d.get("sha256",""))
PY
)"
[[ "$EXPECTED" == "$SHA" ]] || { echo "Manifeste préparé incohérent." >&2; exit 1; }
PREVIOUS_LINK="$(/usr/bin/readlink "$CURRENT")"
PREVIOUS_REAL="$(cd "$(dirname "$CURRENT")" && cd "$(readlink "$CURRENT")" && pwd -P)"
case "$PREVIOUS_REAL" in "$ROOT"|"$VERSIONS_REAL"/*) ;; *) echo "Version précédente hors du stockage autorisé." >&2; exit 1;; esac
PREVIOUS_VERSION="$("$ROOT/.venv/bin/python" - "$PREVIOUS_REAL/VERSION.txt" <<'PY'
import re,sys
from pathlib import Path
v=Path(sys.argv[1]).read_text(encoding="utf-8").strip().lstrip("vV")
if not re.fullmatch(r"\d+\.\d+\.\d+",v): raise SystemExit("Version précédente invalide.")
print(v)
PY
)"
umask 077
BACKUP_DIR="$DATA/backups"
mkdir -p "$BACKUP_DIR"
command -v pgrep >/dev/null 2>&1 || { write_state failed "pgrep est requis pour vérifier l'absence de serveur manuel."; write_maintenance_state failed; exit 1; }
SERVICE_PID="$(/bin/launchctl print "gui/$UID_NOW/$SERVICE_LABEL" 2>/dev/null | /usr/bin/awk '$1 == "pid" && $2 == "=" && $3 ~ /^[0-9]+$/ && $3 > 0 {print $3; exit}' || true)"
[[ "$SERVICE_PID" =~ ^[0-9]+$ ]] || { write_state failed "Impossible d'identifier le processus launchd MaClasse ; mise à jour refusée."; write_maintenance_state failed; exit 1; }
OWNED_SERVICE_PIDS="$(owned_service_pids)" || { write_state failed "Impossible d'identifier les processus de cette installation ; mise à jour refusée."; write_maintenance_state failed; exit 1; }
pid_is_in_list "$SERVICE_PID" "$OWNED_SERVICE_PIDS" || { write_state failed "Le PID launchd ne correspond pas à un processus de cette installation ; mise à jour refusée."; write_maintenance_state failed; exit 1; }
if SERVER_PIDS="$(/usr/bin/pgrep -f '[p]ython.*(network_supervisor|server)[.]py' 2>/dev/null)"; then PGREP_STATUS=0; else PGREP_STATUS=$?; fi
[[ "$PGREP_STATUS" -le 1 ]] || { write_state failed "Impossible de vérifier les processus Python ; mise à jour refusée par sécurité."; write_maintenance_state failed; exit 1; }
while IFS= read -r pid; do
  [[ -z "$pid" ]] && continue
  pid_is_in_list "$pid" "$OWNED_SERVICE_PIDS" || { write_state failed "Un autre serveur MaClasse non supervisé est actif (PID $pid) ; arrête-le avant la mise à jour."; write_maintenance_state failed; exit 1; }
done <<< "$SERVER_PIDS"
write_state installing
if ! stop_service_and_confirm; then
  write_state failed "Impossible de confirmer l'arrêt complet du serveur launchd ; aucune sauvegarde ni bascule n'a été effectuée."
  write_maintenance_state failed
  exit 1
fi
# Snapshot after confirmed stop: no concurrent writes can be lost on rollback.
STAMP="$(/bin/date +%Y%m%d-%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/maclasse-avant-maj-$STAMP-$RANDOM-$PPID.json"
if [[ ! -f "$DATA/maclasse.json" || -L "$DATA/maclasse.json" ]] || ! /bin/cp -p "$DATA/maclasse.json" "$BACKUP_FILE"; then
  if start_service; then
    write_state failed "Impossible de sauvegarder la base après l'arrêt ; ancienne version relancée."
    write_maintenance_state failed
  else
    write_state rollback_failed "Impossible de sauvegarder la base et de relancer l'ancienne version."
    write_maintenance_state failed
  fi
  exit 1
fi
if ! "$ROOT/.venv/bin/python" -c 'import json,sys; json.load(open(sys.argv[1],encoding="utf-8"))' "$BACKUP_FILE"; then
  /bin/rm -f "$BACKUP_FILE"
  if start_service; then
    write_state failed "La sauvegarde JSON est invalide ; ancienne version relancée."
    write_maintenance_state failed
  else
    write_state rollback_failed "La sauvegarde JSON est invalide et l'ancienne version n'a pas redémarré."
    write_maintenance_state failed
  fi
  exit 1
fi
if ! "$ROOT/.venv/bin/python" - "$BACKUP_FILE" "$BACKUP_DIR" <<'PYSYNC'
import os,sys
backup,directory=sys.argv[1],sys.argv[2]
with open(backup,"rb") as stream: os.fsync(stream.fileno())
fd=os.open(directory,os.O_RDONLY)
try:
    os.fsync(fd)
except OSError:
    pass
finally:
    os.close(fd)
PYSYNC
then
  /bin/rm -f "$BACKUP_FILE"
  if start_service; then
    write_state failed "La sauvegarde de la base n'a pas pu être synchronisée ; ancienne version relancée."
    write_maintenance_state failed
  else
    write_state rollback_failed "La sauvegarde de la base n'a pas pu être synchronisée et l'ancienne version n'a pas redémarré."
    write_maintenance_state failed
  fi
  exit 1
fi
/bin/rm -f "$CURRENT.next"
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
write_maintenance_state completed
# Keep the three newest releases, plus the active and immediate rollback versions.
if ! "$ROOT/.venv/bin/python" - "$VERSIONS" "$TARGET_REAL" "$PREVIOUS_REAL" <<'PY'
import re, shutil, sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
active=Path(sys.argv[2]).resolve()
previous=Path(sys.argv[3]).resolve()
versions=[]
for path in root.iterdir():
    if path.is_symlink() or not path.is_dir():
        continue
    match=re.fullmatch(r"V(\d+)\.(\d+)\.(\d+)",path.name)
    if match:
        versions.append((tuple(map(int,match.groups())),path.resolve()))
keep={active,previous}
keep.update(path for _,path in sorted(versions,reverse=True)[:3])
for _,path in versions:
    if path in keep:
        continue
    if path.parent==root and path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
PY
then
  echo "Avertissement : nettoyage des anciennes versions ignoré ; la mise à jour reste installée."
fi
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
