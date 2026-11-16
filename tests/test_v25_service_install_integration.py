#!/usr/bin/env python3
"""Exercise the Linux service installer/uninstaller with isolated command stubs."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform.startswith("linux") and os.geteuid() != 0,
                     "Simulation du service utilisateur Linux hors compte root.")
class ServiceInstallIntegrationTests(unittest.TestCase):
    def test_install_and_uninstall_keep_application_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            program = base / "MaClasse"
            home = base / "home"
            fakebin = base / "bin"
            (program / ".venv" / "bin").mkdir(parents=True)
            (program / "data").mkdir(parents=True)
            home.mkdir()
            fakebin.mkdir()
            (program / ".venv" / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
            (program / ".venv" / "bin" / "python").chmod(0o755)
            (program / "data" / "maclasse.json").write_text('{"settings":{"school":"Test"}}', encoding="utf-8")
            for name in ("Installer-Service-MaClasse-Linux.sh", "Desinstaller-Service-MaClasse-Linux.sh"):
                shutil.copy2(ROOT / name, program / name)

            stubs = {
                "systemctl": '#!/bin/sh\necho "$*" >> "$SYSTEMCTL_LOG"\ncase "$*" in *"is-active --quiet maclasse-update-apply.service"*) exit 3;; esac\nexit 0\n',
                "loginctl": '#!/bin/sh\necho "$*" >> "$LOGINCTL_LOG"\nif [ "$1" = "show-user" ]; then echo no; fi\nexit 0\n',
                "sudo": '#!/bin/sh\nexec "$@"\n',
                "sleep": '#!/bin/sh\nexit 0\n',
            }
            for name, source in stubs.items():
                path = fakebin / name
                path.write_text(source, encoding="utf-8")
                path.chmod(0o755)

            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "PATH": str(fakebin) + os.pathsep + env.get("PATH", ""),
                "SYSTEMCTL_LOG": str(base / "systemctl.log"),
                "LOGINCTL_LOG": str(base / "loginctl.log"),
            })
            install = subprocess.run(
                ["/usr/bin/bash", str(program / "Installer-Service-MaClasse-Linux.sh")],
                cwd=program, env=env, capture_output=True, text=True, timeout=20
            )
            self.assertEqual(install.returncode, 0, install.stderr + install.stdout)
            unit_dir = home / ".config" / "systemd" / "user"
            service = (unit_dir / "maclasse.service").read_text(encoding="utf-8")
            updater = (unit_dir / "maclasse-update-apply.service").read_text(encoding="utf-8")
            self.assertIn("MACLASSE_SUPERVISED=systemd", service)
            self.assertIn("data/program/current/Appliquer-Mise-A-Jour-MaClasse-Linux.sh", updater)
            self.assertTrue((program / "data" / "update-manager.enabled").is_file())

            uninstall = subprocess.run(
                ["/usr/bin/bash", str(program / "Desinstaller-Service-MaClasse-Linux.sh")],
                cwd=program, env=env, capture_output=True, text=True, timeout=20
            )
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr + uninstall.stdout)
            self.assertFalse((unit_dir / "maclasse.service").exists())
            self.assertFalse((unit_dir / "maclasse-update-apply.service").exists())
            self.assertFalse((program / "data" / "update-manager.enabled").exists())
            self.assertTrue((program / "data" / "maclasse.json").is_file())
            self.assertIn("enable-linger", (base / "loginctl.log").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
