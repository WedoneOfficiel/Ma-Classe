#!/usr/bin/env python3
"""Static safety checks for the macOS launchd update supervisor."""
import plistlib
import stat
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "Installer-Service-MaClasse-macOS.sh",
    "Lancer-MaClasse-Service-macOS.sh",
    "Appliquer-Mise-A-Jour-MaClasse-macOS.sh",
    "Lancer-MaClasse.command",
    "Lancer-MaClasse-Reseau.command",
)

class MacOSSupervisorTests(unittest.TestCase):
    def test_launchd_scripts_have_valid_bash_syntax(self):
        for name in SCRIPTS:
            with self.subTest(script=name):
                subprocess.run(["bash", "-n", str(ROOT / name)], check=True)

    def test_manual_launchers_never_start_a_second_server_when_launchd_is_loaded(self):
        for name in SCRIPTS[3:]:
            with self.subTest(script=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                guard = source.index('launchctl print "gui/$(id -u)/fr.maclasse.server"')
                start = source.index(".venv/bin/python server.py")
                self.assertLess(guard, start)
                self.assertIn("partagerait la même base de données", source)

    def test_service_is_user_scoped_and_keeps_data_outside_versions(self):
        installer = (ROOT / SCRIPTS[0]).read_text(encoding="utf-8")
        runner = (ROOT / SCRIPTS[1]).read_text(encoding="utf-8")
        self.assertIn("gui/$(id -u)", installer)
        self.assertIn("fr.maclasse.server", installer)
        self.assertIn("KeepAlive", installer)
        self.assertIn('MACLASSE_ROOT="$ROOT"', runner)
        self.assertIn('MACLASSE_DATA_DIR="$DATA"', runner)
        self.assertIn('SCRIPT_DIR/../../../..', runner)
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
        self.assertEqual(data["ProgramArguments"][1], str(root.resolve() / "data" / "program" / "current" / SCRIPTS[1]))
        self.assertEqual(data["EnvironmentVariables"]["MACLASSE_ROOT"], str(root.resolve()))
        self.assertEqual(data["EnvironmentVariables"]["MACLASSE_DATA_DIR"], str(root.resolve() / "data"))
        self.assertEqual(os.readlink(root / "data" / "program" / "current"), "../..")
        marker = root / "data" / "update-manager.enabled"
        self.assertTrue(marker.is_file())
        self.assertEqual(stat.S_IMODE(marker.stat().st_mode), 0o600)
        self.assertIn("$1 ~ /^[0-9]+$/", (root / SCRIPTS[0]).read_text(encoding="utf-8"))
        calls = log.read_text(encoding="utf-8")
        self.assertIn("bootstrap", calls)
        self.assertIn("kickstart", calls)


    @unittest.skipUnless(__import__("sys").platform == "darwin", "launchd réel uniquement sur macOS.")
    def test_real_launchd_bootstrap_starts_and_unloads_isolated_agent(self):
        import os
        import tempfile
        import time
        import shutil
        uid = os.getuid()
        label = "fr.maclasse.server"
        domain = f"gui/{uid}/{label}"
        existing = subprocess.run(["/bin/launchctl", "print", domain], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(existing.returncode, 0, "Le runner possède déjà un agent MaClasse ; test refusé pour ne rien perturber.")
        with tempfile.TemporaryDirectory(prefix="maclasse-launchd-live-") as temp:
            tmp = Path(temp)
            root = tmp / "MaClasse"
            (root / ".venv" / "bin").mkdir(parents=True)
            (root / "data" / "tls").mkdir(parents=True)
            (root / ".venv" / "bin" / "python").symlink_to(__import__("sys").executable)
            shutil.copy2(ROOT / "Installer-Service-MaClasse-macOS.sh", root / "Installer-Service-MaClasse-macOS.sh")
            runner = root / "Lancer-MaClasse-Service-macOS.sh"
            runner.write_text(
                '#!/bin/bash\nprintf "%s" "$BASHPID" > "$MACLASSE_DATA_DIR/launchd-live.pid"\nexec /bin/sleep 60\n',
                encoding="utf-8",
            )
            runner.chmod(0o700)
            for name in ("server.crt", "server.key", "ca.crt"):
                (root / "data" / "tls" / name).write_text("test-only placeholder", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(tmp / "home")
            try:
                result = subprocess.run(
                    ["bash", str(root / "Installer-Service-MaClasse-macOS.sh")],
                    cwd=root, env=env, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + "\\n" + result.stderr)
                marker_file = root / "data" / "launchd-live.pid"
                deadline = time.time() + 10
                while time.time() < deadline and not marker_file.exists():
                    time.sleep(0.2)
                self.assertTrue(marker_file.is_file(), "launchd n'a pas démarré le lanceur isolé.")
                loaded = subprocess.run(["/bin/launchctl", "print", domain], capture_output=True, text=True)
                self.assertEqual(loaded.returncode, 0, loaded.stderr)
                self.assertIn(label, loaded.stdout)
            finally:
                subprocess.run(["/bin/launchctl", "bootout", domain], capture_output=True, text=True, timeout=10)
                pid_file = root / "data" / "launchd-live.pid"
                if pid_file.exists():
                    try:
                        os.kill(int(pid_file.read_text(encoding="utf-8")), 15)
                    except (OSError, ValueError):
                        pass

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
    if args[:2] == ["/bin/launchctl", "print"]:
        return subprocess.CompletedProcess(args, 1, "", "Could not find service")
    if args[:3] == ["/bin/launchctl", "list", "fr.maclasse.update"]:
        return subprocess.CompletedProcess(args, 1, "", "Could not find service")
    return subprocess.CompletedProcess(args, 0, "", "")
server.subprocess.run = fake_run
server._schedule_update_timer(time.time() + 3600)
scheduled = pathlib.Path(server._launchd_update_plist())
with scheduled.open("rb") as stream:
    data = plistlib.load(stream)
assert data["Label"] == "fr.maclasse.update"
assert data["EnvironmentVariables"]["MACLASSE_ROOT"] == str(tmp)
assert data["EnvironmentVariables"]["MACLASSE_DATA_DIR"] == str(tmp / "data")
assert data["StartCalendarInterval"]["Minute"] >= 0
assert data["ProgramArguments"][0:2] == ["/bin/bash", str(root / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh")]
server._cancel_update_timer()
assert not scheduled.exists()
server._start_update_apply_service()
with scheduled.open("rb") as stream:
    immediate = plistlib.load(stream)
assert immediate["RunAtLoad"] is False
assert immediate["EnvironmentVariables"]["MACLASSE_ROOT"] == str(tmp)
assert immediate["EnvironmentVariables"]["MACLASSE_DATA_DIR"] == str(tmp / "data")
assert "StartCalendarInterval" not in immediate
assert any(call[:2] == ["/bin/launchctl", "kickstart"] for call in calls)

# Never unload an updater process that has already started installing.
active_calls = []
def active_run(args, **kwargs):
    active_calls.append(args)
    if args[:3] == ["/bin/launchctl", "list", "fr.maclasse.update"]:
        return subprocess.CompletedProcess(args, 0, "4321 0 fr.maclasse.update", "")
    return subprocess.CompletedProcess(args, 0, "", "")
server.subprocess.run = active_run
try:
    server._start_update_apply_service()
except RuntimeError:
    pass
else:
    raise AssertionError("immediate launch was allowed while a scheduled updater was running")
assert not any(call[:2] in (["/bin/launchctl", "bootout"], ["/bin/launchctl", "kickstart"]) for call in active_calls)
try:
    server._cancel_update_timer()
except RuntimeError:
    pass
else:
    raise AssertionError("running launchd updater was allowed to be unloaded")
assert not any(call[:2] == ["/bin/launchctl", "bootout"] for call in active_calls)

# A failed bootout must not be reported as a successful cancellation.
def stuck_run(args, **kwargs):
    if args[:2] == ["/bin/launchctl", "print"]:
        return subprocess.CompletedProcess(args, 0, "loaded", "")
    return subprocess.CompletedProcess(args, 0, "", "")
server.subprocess.run = stuck_run
try:
    server._cancel_update_timer()
except RuntimeError:
    pass
else:
    raise AssertionError("launchd still loaded the task but cancellation was accepted")
assert scheduled.exists()
"""
        subprocess.run(["python", "-c", code, str(ROOT)], check=True, cwd=ROOT)

    def test_launchd_activity_parser_ignores_header_and_idle_job(self):
        code = r"""
import subprocess, sys
sys.path.insert(0, str(sys.argv[1]))
import server
server.sys.platform = "darwin"
server.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "PID Status Label\n- 0 fr.maclasse.update\n", "")
assert server._update_apply_service_active() is False
server.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "PID Status Label\n4321 0 fr.maclasse.update\n", "")
assert server._update_apply_service_active() is True
"""
        subprocess.run(["python", "-c", code, str(ROOT)], check=True, cwd=ROOT)

    def test_database_backup_happens_after_launchd_service_shutdown(self):
        script = (ROOT / SCRIPTS[2]).read_text(encoding="utf-8")
        self.assertIn("fcntl.LOCK_EX | fcntl.LOCK_NB", script)
        self.assertIn("update-apply.lock", script)
        stop = script.index('launchctl bootout "gui/$UID_NOW/$SERVICE_LABEL"')
        backup = script.index('/bin/cp -p "$DATA/maclasse.json" "$BACKUP_FILE"')
        self.assertLess(stop, backup)
        self.assertLess(script.index('if [[ "$STOPPED" != "1" ]]'), backup)
        self.assertIn("write_maintenance_state completed", script)


    def test_rollback_waits_for_launchd_job_to_be_unloaded(self):
        import os
        import tempfile
        script = (ROOT / SCRIPTS[2]).read_text(encoding="utf-8")
        start = script.index("stop_service_and_confirm() {")
        end = script.index("\n}\nfail_restore()", start) + 2
        function = script[start:end]
        function = function.replace("/bin/launchctl", '"$FAKE_LAUNCHCTL"')
        function = function.replace("/usr/bin/awk", "awk")
        function = function.replace("/bin/kill", "kill")
        function = function.replace("/bin/sleep 1", ":")
        with tempfile.TemporaryDirectory(prefix="maclasse-launchd-stop-") as temp:
            root = Path(temp)
            fake = root / "launchctl"
            fake.write_text(
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  list) printf 'PID Status Label\\n- 0 fr.maclasse.server\\n' ;;\n"
                "  bootout) touch \"$BOOTED\" ;;\n"
                "  print) if [ ! -f \"$BOOTED\" ]; then echo loaded; exit 0; fi; "
                "n=0; [ ! -f \"$COUNT\" ] || n=$(cat \"$COUNT\"); n=$((n+1)); "
                "echo \"$n\" > \"$COUNT\"; if [ \"$n\" -lt 3 ]; then echo loaded; exit 0; "
                "else echo 'Could not find service' >&2; exit 113; fi ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            env = os.environ.copy()
            env.update({"FAKE_LAUNCHCTL": str(fake), "BOOTED": str(root / "booted"),
                        "COUNT": str(root / "count")})
            command = "UID_NOW=501; SERVICE_LABEL=fr.maclasse.server; " + function + "; stop_service_and_confirm"
            subprocess.run(["bash", "-c", command], check=True, env=env, timeout=5)
            self.assertEqual((root / "count").read_text(encoding="utf-8").strip(), "3")

            fake.write_text(
                "#!/bin/sh\n"
                "case \"$1\" in list) printf 'PID Status Label\\n- 0 fr.maclasse.server\\n' ;; "
                "bootout) : ;; print) echo 'Operation not permitted' >&2; exit 1 ;; esac\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            result = subprocess.run(["bash", "-c", command], env=env, capture_output=True, text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0, "unknown launchctl state must fail closed")

    def test_installer_checks_health_and_has_rollback_path(self):
        script = (ROOT / SCRIPTS[2]).read_text(encoding="utf-8")
        self.assertIn("health_ok", script)
        self.assertIn("stop_service_and_confirm", script)
        self.assertIn("pgrep -f '[p]ython.*server[.]py'", script)
        self.assertIn('"$pid" == "$SERVICE_PID"', script)
        self.assertIn("version précédente absente ou invalide", script)
        self.assertIn("base non restaurée", script)
        self.assertIn('MACLASSE_ROOT:-', script)
        self.assertIn('MACLASSE_DATA_DIR:-', script)
        self.assertIn("fail_restore", script)
        self.assertIn("os.replace(sys.argv[1],sys.argv[2])", script)
        self.assertIn("maclasse-avant-maj-", script)
        self.assertIn("rollback_failed", script)
        self.assertIn("launchctl bootout", script)
        self.assertIn("os.replace(source,destination)", script)
        self.assertIn("os.fsync(stream.fileno())", script)

if __name__ == "__main__":
    unittest.main()
