#!/usr/bin/env python3
"""Static safety checks for the macOS launchd update supervisor."""
import plistlib
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
        self.assertIn("/sbin/route -n get default", runner)
        self.assertIn("/usr/sbin/ipconfig getifaddr", runner)
        self.assertIn("Configurer-MaClasse-Reseau.sh", runner)



    @unittest.skipUnless(__import__("sys").platform == "darwin", "L'installateur launchd ne peut être exécuté que sur macOS.")
    def test_service_installer_builds_and_loads_user_agent(self):
        import os
        import shutil
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="maclasse-launchd-installer-"))
        root = tmp / "MaClasse"
        (root / ".venv" / "bin").mkdir(parents=True)
        (root / "data" / "tls").mkdir(parents=True)
        (root / ".venv" / "bin" / "python").symlink_to(__import__("sys").executable)
        for name in SCRIPTS:
            shutil.copy2(ROOT / name, root / name)
        for name in ("server.crt", "server.key", "ca.crt"):
            (root / "data" / "tls" / name).write_text("test-only placeholder", encoding="utf-8")
        home = tmp / "home"
        fakebin = tmp / "bin"
        home.mkdir()
        fakebin.mkdir()
        log = tmp / "launchctl.log"
        launchctl = fakebin / "launchctl"
        launchctl.write_text("#!/bin/sh\necho \"$*\" >> \"$LAUNCHCTL_LOG\"\nexit 0\n", encoding="utf-8")
        launchctl.chmod(0o755)
        pgrep = fakebin / "pgrep"
        pgrep.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        pgrep.chmod(0o755)
        env = os.environ.copy()
        env.update({"HOME": str(home), "PATH": str(fakebin) + os.pathsep + env.get("PATH", ""),
                    "LAUNCHCTL_LOG": str(log)})
        subprocess.run(["bash", str(root / SCRIPTS[0])], check=True, cwd=root, env=env,
                       capture_output=True, text=True, timeout=20)
        plist = home / "Library" / "LaunchAgents" / "fr.maclasse.server.plist"
        with plist.open("rb") as stream:
            data = plistlib.load(stream)
        self.assertEqual(data["Label"], "fr.maclasse.server")
        self.assertTrue(data["KeepAlive"])
        self.assertTrue(data["RunAtLoad"])
        self.assertEqual(data["ProgramArguments"][1], str(root / SCRIPTS[1]))
        self.assertEqual(os.readlink(root / "data" / "program" / "current"), "../..")
        self.assertTrue((root / "data" / "update-manager.enabled").is_file())
        calls = log.read_text(encoding="utf-8")
        self.assertIn("bootstrap", calls)
        self.assertIn("kickstart", calls)

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
