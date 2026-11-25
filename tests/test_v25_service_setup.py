#!/usr/bin/env python3
"""Static regression checks for the experimental Linux service supervisor."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "Lancer-MaClasse-Service-Linux.sh",
    "Installer-Service-MaClasse-Linux.sh",
    "Desinstaller-Service-MaClasse-Linux.sh",
    "Appliquer-Mise-A-Jour-MaClasse-Linux.sh",
)
for name in SCRIPTS:
    result = subprocess.run(["bash", "-n", str(ROOT / name)], capture_output=True, text=True)
    assert result.returncode == 0, f"{name}: {result.stderr}"

launcher = (ROOT / "Lancer-MaClasse-Service-Linux.sh").read_text()
installer = (ROOT / "Installer-Service-MaClasse-Linux.sh").read_text()
uninstaller = (ROOT / "Desinstaller-Service-MaClasse-Linux.sh").read_text()

assert 'MACLASSE_LAN_MODE=1' in launcher
assert 'export MACLASSE_APP_ROOT="$APP_ROOT"' in launcher
assert 'export MACLASSE_DATA_DIR="$DATA_ROOT"' in launcher
assert 'exec "$PYTHON" "$APP_ROOT/network_supervisor.py"' in launcher
assert 'DATA_REAL="$(cd "$DATA_ROOT" && pwd -P)"' in launcher
assert 'PROGRAM_REAL="$(cd "$PROGRAM_ROOT" && pwd -P)"' in launcher
assert '[[ "$PROGRAM_REAL" == "$DATA_REAL/program" && "$VERSIONS_REAL" == "$PROGRAM_REAL/versions" ]]' in launcher
assert 'APP_REAL="$(cd "$APP_ROOT" && pwd -P)"' in launcher
assert 'case "$APP_REAL" in "$ROOT"|"$VERSIONS_REAL"/*)' in launcher
assert 'ln -s ../.. "$APP_ROOT"' in launcher
assert 'ExecStart=/usr/bin/bash $ROOT/data/program/current/Lancer-MaClasse-Service-Linux.sh' in installer
assert 'Environment=MACLASSE_ROOT=$ROOT' in installer
assert 'Environment=MACLASSE_DATA_DIR=$ROOT/data' in installer
assert 'SCRIPT_DIR/../../../..' in launcher
assert 'Environment=MACLASSE_SUPERVISED=systemd' in installer
assert 'loginctl enable-linger "$USER_NAME"' in installer
assert 'for dependency in systemd-analyze curl openssl realpath python3 pgrep; do' in installer
assert "pgrep -f '[p]ython.*server[.]py'" in installer
assert 'show --property=MainPID --value maclasse.service' in installer
assert 'NoNewPrivileges=true' in installer
assert 'TimeoutStopSec=120' in installer
server_source = (ROOT / 'server.py').read_text(encoding='utf-8')
assert 'class MaClasseHTTPServer(ThreadingHTTPServer):' in server_source
assert 'daemon_threads=False' in server_source
assert 'block_on_close=True' in server_source
server_source = (ROOT / 'server.py').read_text()
assert 'daemon_threads=False' in server_source
assert 'httpd.server_close()' in server_source
assert 'ProtectSystem=full' in installer
assert 'ReadWritePaths=$ROOT/data' in installer
assert 'maclasse-update-apply.service' in installer
assert 'touch "$ROOT/data/update-manager.enabled"' in installer
assert 'Environment=MACLASSE_ROOT=$ROOT' in installer
assert 'ExecStart=/usr/bin/bash $ROOT/data/program/current/Appliquer-Mise-A-Jour-MaClasse-Linux.sh' in installer
assert 'rm -f "$UNIT_FILE"' in uninstaller
assert 'rm -rf' not in uninstaller
assert 'if systemctl --user is-active --quiet maclasse-update-apply.service' in uninstaller
assert 'La maintenance programmée a été annulée.' in uninstaller
assert 'UPDATE_UNIT_FILE="$UNIT_DIR/maclasse-update-apply.service"' in uninstaller
assert 'rm -f "$ROOT/data/update-manager.enabled"' in uninstaller
apply_script = (ROOT / "Appliquer-Mise-A-Jour-MaClasse-Linux.sh").read_text()
assert 'systemctl --user stop maclasse.service' in apply_script
assert "pgrep -f '[p]ython.*server[.]py'" in apply_script
assert 'Un autre serveur MaClasse non supervisé est actif' in apply_script
assert 'mv -Tf "$CURRENT_LINK.next" "$CURRENT_LINK"' in apply_script
assert 'ln -s "versions/V$VERSION_NUMBER" "$CURRENT_LINK.next"' in apply_script
assert 'PREVIOUS_LINK_TARGET' in apply_script
assert 'rollback_failed' in apply_script
assert 'systemctl --user is-active --quiet maclasse.service' in apply_script
assert 'Aucune bascule ni restauration de base' in apply_script
assert 'sauvegarde de base absente ou invalide' in apply_script
assert 'VERSION.txt' in apply_script
assert 'maclasse-runtime-ready.json' in apply_script
print("OK — supervision Linux : scripts valides, service isolé et désinstallation sans suppression des données.")
