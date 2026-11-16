#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

URL="http://127.0.0.1:8765"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "MaClasse V25 est configurée pour macOS."
  exit 1
fi

if /bin/launchctl print "gui/$(id -u)/fr.maclasse.server" >/dev/null 2>&1; then
  echo "Le service MaClasse est déjà chargé par launchd."
  echo "Ne démarre pas une seconde copie : elle partagerait la même base de données."
  HOST="$(/usr/bin/openssl x509 -in "data/tls/server.crt" -noout -ext subjectAltName 2>/dev/null | /usr/bin/grep -oE 'IP Address:[0-9.]+' | /usr/bin/head -n1 | /usr/bin/cut -d: -f2 || true)"
  if [[ -n "$HOST" ]]; then
    open -a "Firefox" "https://$HOST:8765" >/dev/null 2>&1 || open "https://$HOST:8765" >/dev/null 2>&1 || true
  else
    echo "Certificat HTTPS introuvable ; consulte data/macos-service-error.log."
  fi
  read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  exit 0
fi

if [[ ! -x ".venv/bin/python" ]]; then
  echo "L'environnement MaClasse n'est pas installé."
  echo "Double-clique d'abord sur Installer-MaClasse.command."
  read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  exit 1
fi

if ! .venv/bin/python -c "import reportlab" >/dev/null 2>&1; then
  echo "Les dépendances semblent incomplètes."
  echo "Relance Installer-MaClasse.command."
  read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  exit 1
fi

if /usr/bin/curl --silent --fail "$URL/api/auth/session" >/dev/null 2>&1; then
  echo "Un service répond déjà sur le port 8765."
  echo "Vérifie qu'il s'agit bien de MaClasse avant de continuer."
  open -a "Firefox" "$URL" >/dev/null 2>&1 || open "$URL" >/dev/null 2>&1 || true
  read -r -p "Appuie sur Entrée pour fermer cette fenêtre… " _ || true
  exit 0
fi

echo "MaClasse V$(cat VERSION.txt) démarre sur ce Mac."
echo "Adresse locale : $URL"
echo "Le serveur n'est pas accessible depuis le Wi-Fi ou Internet."
echo "Laisse cette fenêtre ouverte. Pour arrêter MaClasse : Ctrl+C."
echo

.venv/bin/python server.py &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

READY=0
for _ in {1..20}; do
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    wait "$SERVER_PID" || true
    echo "Le serveur n'a pas pu démarrer. Vérifie que le port 8765 est libre."
    exit 1
  fi
  if /usr/bin/curl --silent --fail "$URL/api/auth/session" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.5
done

if [[ "$READY" -ne 1 ]]; then
  echo "Le serveur n'a pas répondu après 10 secondes."
  exit 1
fi

if ! open -a "Firefox" "$URL" >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
fi

wait "$SERVER_PID"
