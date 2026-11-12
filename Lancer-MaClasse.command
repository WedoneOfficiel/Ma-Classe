#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

echo "Démarrage de MaClasse V25.0.7 — édition sans IA…"

# Stop only the legacy MaClasse ArIA processes recorded by previous versions.
STATE="$HOME/.maclasse/aria"
stop_owned(){
  local file="$1" label="$2"
  [[ -f "$file" ]] || return 0
  local pid cmd
  pid="$(cat "$file" 2>/dev/null || true)"
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    if { [[ "$file" == *router.pid && "$cmd" == *router_server.py* ]]; } || { [[ "$file" == *runtime.pid && "$cmd" == *llama* && ( "$cmd" == *aria-core-* || "$cmd" == *Qwen3.5-4B* ) ]]; }; then
      echo "Arrêt de l’ancien moteur IA MaClasse ($label)…"
      kill "$pid" 2>/dev/null || true
      for _ in {1..20}; do kill -0 "$pid" 2>/dev/null || break; sleep 0.25; done
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$file"
}
stop_owned "$STATE/runtime.pid" "conversation"
stop_owned "$STATE/router.pid" "routeur"

if [[ -x ".venv/bin/python" ]]; then
  exec .venv/bin/python server.py
else
  exec python3 server.py
fi
