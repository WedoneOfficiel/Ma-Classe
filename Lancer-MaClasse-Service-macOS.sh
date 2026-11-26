#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
if [[ -n "${MACLASSE_ROOT:-}" ]]; then
  ROOT="$MACLASSE_ROOT"
elif [[ -d "$SCRIPT_DIR/data" ]]; then
  ROOT="$SCRIPT_DIR"
else
  ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
fi
ROOT="$(cd "$ROOT" && pwd -P)"
DATA="${MACLASSE_DATA_DIR:-$ROOT/data}"
DATA="$(cd "$DATA" && pwd -P)"
CURRENT="$DATA/program/current"
[[ -L "$CURRENT" ]] || { echo "Version active absente : $CURRENT" >&2; exit 1; }
PROGRAM="$(cd "$(dirname "$CURRENT")" && cd "$(readlink "$CURRENT")" && pwd -P)"
case "$PROGRAM" in "$ROOT"|"$DATA/program/versions/"*) ;; *) echo "Cible active hors du stockage autorisé." >&2; exit 1;; esac
# Keep the stable launcher in the installation root aligned with the active
# version. Existing installations otherwise keep opening the original launcher
# forever, because updates are extracted into data/program/versions/.
if [[ "$PROGRAM" != "$ROOT" ]]; then
  VERSION_LAUNCHER="$PROGRAM/Lancer-MaClasse-Reseau.command"
  ROOT_LAUNCHER="$ROOT/Lancer-MaClasse-Reseau.command"
  if [[ -f "$VERSION_LAUNCHER" && ! -L "$VERSION_LAUNCHER" ]] &&
     { [[ ! -f "$ROOT_LAUNCHER" ]] || ! /usr/bin/cmp -s "$VERSION_LAUNCHER" "$ROOT_LAUNCHER"; }; then
    TEMP_LAUNCHER="$ROOT/.Lancer-MaClasse-Reseau.command.$"
    if ! /bin/cp -p "$VERSION_LAUNCHER" "$TEMP_LAUNCHER" ||
       ! /bin/mv -f "$TEMP_LAUNCHER" "$ROOT_LAUNCHER"; then
      /bin/rm -f "$TEMP_LAUNCHER"
      echo "Avertissement : impossible de synchroniser le lanceur réseau dans $ROOT." >&2
    fi
  fi
fi
PYTHON="$PROGRAM/.venv/bin/python"
[[ -x "$PYTHON" && -f "$PROGRAM/server.py" ]] || { echo "Environnement Python ou serveur absent dans $PROGRAM." >&2; exit 1; }
# The shared supervisor follows DHCP changes, renews the leaf certificate and
# restarts only the listener. The root CA and private server key stay in data/.
export MACLASSE_SUPERVISED=launchd
export MACLASSE_ROOT="$ROOT"
export MACLASSE_APP_ROOT="$PROGRAM"
export MACLASSE_DATA_DIR="$DATA"
export MACLASSE_PYTHON="$PYTHON"
export MACLASSE_LAN_MODE=1
export MACLASSE_PORT=8765
unset MACLASSE_HOST MACLASSE_TLS_CERT MACLASSE_TLS_KEY
cd "$PROGRAM"
exec "$PYTHON" "$PROGRAM/network_supervisor.py"
