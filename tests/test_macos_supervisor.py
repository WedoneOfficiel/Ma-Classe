#!/usr/bin/env python3
"""Static safety checks for the macOS launchd update supervisor."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "Installer-Service-MaClasse-macOS.sh",
    "Lancer-MaClasse-Service-macOS.sh",
    "Appliquer-Mise-A-Jour-MaClasse-macOS.sh",
)

class MacOSSupervisorTests(unittest.TestCase):
    def test_launchd_scripts_have_valid_bash_syntax(self):
        for name in SCRIPTS:
            with self.subTest(script=name):
                subprocess.run(["bash", "-n", str(ROOT / name)], check=True)

    def test_service_is_user_scoped_and_keeps_data_outside_versions(self):
        installer = (ROOT / SCRIPTS[0]).read_text(encoding="utf-8")
        runner = (ROOT / SCRIPTS[1]).read_text(encoding="utf-8")
        self.assertIn("gui/$(id -u)", installer)
        self.assertIn("fr.maclasse.server", installer)
        self.assertIn("KeepAlive", installer)
        self.assertIn('MACLASSE_DATA_DIR="$DATA"', runner)
        self.assertIn('MACLASSE_SUPERVISED=launchd', runner)
        self.assertIn('MACLASSE_TLS_KEY="$KEY"', runner)

    def test_installer_checks_health_and_has_rollback_path(self):
        script = (ROOT / SCRIPTS[2]).read_text(encoding="utf-8")
        self.assertIn("health_ok", script)
        self.assertIn("fail_restore", script)
        self.assertIn("os.replace(sys.argv[1],sys.argv[2])", script)
        self.assertIn("maclasse-avant-maj-", script)
        self.assertIn("rollback_failed", script)
        self.assertIn("launchctl bootout", script)

if __name__ == "__main__":
    unittest.main()
