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
assert 'export MACLASSE_TLS_CERT="$DATA_ROOT/tls/server.crt"' in launcher
assert 'export MACLASSE_TLS_KEY="$DATA_ROOT/tls/server.key"' in launcher
assert 'exec "$PYTHON" "$APP_ROOT/server.py"' in launcher
assert 'ExecStart=/usr/bin/bash $ROOT/Lancer-MaClasse-Service-Linux.sh' in installer
assert 'loginctl enable-linger "$USER_NAME"' in installer
assert 'NoNewPrivileges=true' in installer
assert 'ProtectSystem=full' in installer
assert 'ReadWritePaths=$ROOT/data' in installer
assert 'maclasse-update-apply.service' in installer
assert 'Appliquer-Mise-A-Jour-MaClasse-Linux.sh' in installer
assert 'rm -f "$UNIT_FILE"' in uninstaller
assert 'rm -rf' not in uninstaller
assert 'data/' not in uninstaller
apply_script = (ROOT / "Appliquer-Mise-A-Jour-MaClasse-Linux.sh").read_text()
assert 'systemctl --user stop maclasse.service' in apply_script
assert 'mv -Tf "$CURRENT_LINK.next" "$CURRENT_LINK"' in apply_script
assert 'rollback_failed' in apply_script
print("OK — supervision Linux : scripts valides, service isolé et désinstallation sans suppression des données.")
