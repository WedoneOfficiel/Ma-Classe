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


    def test_launchd_schedule_and_immediate_job_plists(self):
        code = r"""
import os, pathlib, plistlib, subprocess, sys, tempfile, time
root = pathlib.Path(sys.argv[1])
tmp = pathlib.Path(tempfile.mkdtemp(prefix="maclasse-launchd-test-"))
os.environ["MACLASSE_DATA_DIR"] = str(tmp / "data")
os.environ["MACLASSE_SUPERVISED"] = "launchd"
os.environ["HOME"] = str(tmp / "home")
(tmp / "home" / "Library" / "LaunchAgents").mkdir(parents=True)
sys.path.insert(0, str(root))
import server
server.sys.platform = "darwin"
calls = []
def fake_run(args, **kwargs):
    calls.append(args)
    if args[:3] == ["/bin/launchctl", "list", "fr.maclasse.update"]:
        return subprocess.CompletedProcess(args, 1, "", "")
    return subprocess.CompletedProcess(args, 0, "", "")
server.subprocess.run = fake_run
server._schedule_update_timer(time.time() + 3600)
scheduled = pathlib.Path(server._launchd_update_plist())
with scheduled.open("rb") as stream:
    data = plistlib.load(stream)
assert data["Label"] == "fr.maclasse.update"
assert data["StartCalendarInterval"]["Minute"] >= 0
assert data["ProgramArguments"][0:2] == ["/bin/bash", str(root / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh")]
server._cancel_update_timer()
assert not scheduled.exists()
server._start_update_apply_service()
with scheduled.open("rb") as stream:
    immediate = plistlib.load(stream)
assert immediate["RunAtLoad"] is False
assert "StartCalendarInterval" not in immediate
assert any(call[:2] == ["/bin/launchctl", "kickstart"] for call in calls)
"""
        subprocess.run(["python", "-c", code, str(ROOT)], check=True, cwd=ROOT)

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
