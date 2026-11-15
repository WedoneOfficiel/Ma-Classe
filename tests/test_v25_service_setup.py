#!/usr/bin/env python3
"""Static regression checks for the experimental Linux service supervisor."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "Lancer-MaClasse-Service-Linux.sh",
    "Installer-Service-MaClasse-Linux.sh",
    "Desinstaller-Service-MaClasse-Linux.sh",
)
for name in SCRIPTS:
    result = subprocess.run(["bash", "-n", str(ROOT / name)], capture_output=True, text=True)
    assert result.returncode == 0, f"{name}: {result.stderr}"

launcher = (ROOT / "Lancer-MaClasse-Service-Linux.sh").read_text()
installer = (ROOT / "Installer-Service-MaClasse-Linux.sh").read_text()
uninstaller = (ROOT / "Desinstaller-Service-MaClasse-Linux.sh").read_text()

assert 'MACLASSE_LAN_MODE=1' in launcher
assert 'MACLASSE_TLS_CERT="data/tls/server.crt"' in launcher
assert 'MACLASSE_TLS_KEY="data/tls/server.key"' in launcher
assert 'exec .venv/bin/python server.py' in launcher
assert 'ExecStart=/usr/bin/bash $ROOT/Lancer-MaClasse-Service-Linux.sh' in installer
assert 'loginctl enable-linger "$USER_NAME"' in installer
assert 'NoNewPrivileges=true' in installer
assert 'ProtectSystem=full' in installer
assert 'ReadWritePaths=$ROOT/data' in installer
assert 'rm -f "$UNIT_FILE"' in uninstaller
assert 'rm -rf' not in uninstaller
assert 'data/' not in uninstaller
print("OK — supervision Linux : scripts valides, service isolé et désinstallation sans suppression des données.")
