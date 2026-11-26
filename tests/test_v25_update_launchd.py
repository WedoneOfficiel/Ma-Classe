#!/usr/bin/env python3
"""Regression tests for the independently supervised macOS updater LaunchAgent."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UpdateLaunchdRegressionTests(unittest.TestCase):
    def run_isolated(self, body: str) -> None:
        prelude = r"""
import os, pathlib, subprocess, sys, tempfile
root = pathlib.Path(sys.argv[1])
sandbox = pathlib.Path(tempfile.mkdtemp(prefix="maclasse-update-launchd-unit-"))
home = sandbox / "home"
data = sandbox / "data"
program = sandbox / "program"
(home / "Library" / "LaunchAgents").mkdir(parents=True)
data.mkdir()
program.mkdir()
installer = program / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh"
installer.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
installer.chmod(0o700)
os.environ["HOME"] = str(home)
os.environ["MACLASSE_DATA_DIR"] = str(data)
os.environ["MACLASSE_ROOT"] = str(program)
sys.path.insert(0, str(root))
import server
server.sys.platform = "darwin"
server.ROOT = str(program)
server.DATA_DIR = str(data)

class Launchctl:
    def __init__(self, fail_on=None, missing_stream="stdout"):
        self.fail_on = fail_on
        self.missing_stream = missing_stream
        self.loaded = False
        self.running = False
        self.kickstarted = False
        self.confirm_failure_used = False
        self.calls = []
    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        rc, out, err = 0, "", ""
        if args[:2] == ["/bin/launchctl", "print"]:
            if self.fail_on == "initial_print" and not self.loaded:
                rc, out = 1, "permission denied"
            elif self.fail_on == "confirm" and self.kickstarted and not self.confirm_failure_used:
                self.confirm_failure_used = True
                rc, err = 113, "test confirmation failure"
            elif not self.loaded:
                rc = 113
                if self.missing_stream == "stdout":
                    out = "Could not find service"
                else:
                    err = "Could not find service"
            elif self.running:
                out = "state = running\npid = 4242\n"
            else:
                out = "state = waiting\n"
        elif args[:2] == ["/bin/launchctl", "bootout"]:
            if self.fail_on == "bootout":
                rc, err = 1, "test bootout failure"
            else:
                self.loaded = False
                self.running = False
        elif args[:2] == ["/bin/launchctl", "bootstrap"]:
            if self.fail_on == "bootstrap":
                rc, err = 113, "test bootstrap failure"
            else:
                self.loaded = True
        elif args[:2] == ["/bin/launchctl", "kickstart"]:
            if self.fail_on == "kickstart":
                rc, err = 1, "test kickstart failure"
            else:
                self.kickstarted = True
                self.running = True
        elif args[:2] == ["/usr/bin/plutil", "-lint"]:
            if self.fail_on == "plutil":
                rc, err = 1, "test plist syntax failure"
        result = subprocess.CompletedProcess(args, rc, out, err)
        if kwargs.get("check") and rc:
            raise subprocess.CalledProcessError(rc, args, output=out, stderr=err)
        return result

"""
        code = prelude + "\n" + textwrap.dedent(body)
        with tempfile.TemporaryDirectory(prefix="maclasse-test-home-") as temp:
            env = os.environ.copy()
            env["HOME"] = str(Path(temp) / "home-override")
            env["MACLASSE_DATA_DIR"] = str(Path(temp) / "data-override")
            result = subprocess.run(
                [sys.executable, "-c", code, str(ROOT)],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
            )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)

    def test_launchctl_not_found_is_detected_on_stdout_and_stderr(self):
        self.run_isolated("""
from types import SimpleNamespace
for stream in ("stdout", "stderr"):
    result = SimpleNamespace(returncode=113, stdout="", stderr="")
    setattr(result, stream, "Could not find service")
    assert server._launchctl_service_not_found(result)
assert not server._launchctl_service_not_found(SimpleNamespace(returncode=0, stdout="Could not find service", stderr=""))
assert not server._launchctl_service_not_found(SimpleNamespace(returncode=1, stdout="permission denied", stderr=""))
""")

    def test_launchctl_error_details_include_command_code_and_output(self):
        self.run_isolated("""
error = subprocess.CalledProcessError(113, ["/bin/launchctl", "bootstrap"], output="stdout detail", stderr="stderr detail")
detail = server._update_start_error_detail(error)
assert "launchctl" in detail and "113" in detail
assert "stdout detail" in detail and "stderr detail" in detail
assert "permission denied" in server._update_start_error_detail(RuntimeError("permission denied"))
assert len(server._update_start_error_detail(RuntimeError("x" * 5000))) <= 1200
""")

    def test_start_error_is_logged_with_private_permissions(self):
        self.run_isolated("""
detail = server._record_update_start_error(subprocess.CalledProcessError(
    1, ["/bin/launchctl", "kickstart"], output="launch stdout", stderr="launch stderr"))
log = pathlib.Path(server.DATA_DIR) / "macos-update-error.log"
assert log.is_file()
assert "launch stdout" in log.read_text(encoding="utf-8")
assert "launch stderr" in log.read_text(encoding="utf-8")
assert "kickstart" in detail
assert (log.stat().st_mode & 0o777) == 0o600
""")

    def test_error_logger_keeps_distinct_failures_as_separate_entries(self):
        self.run_isolated("""
server._record_update_start_error(RuntimeError("first failure"))
server._record_update_start_error(RuntimeError("second failure"))
text = (pathlib.Path(server.DATA_DIR) / "macos-update-error.log").read_text(encoding="utf-8")
assert "first failure" in text and "second failure" in text
assert text.count("Échec du démarrage") == 2
""")

    def test_cancel_removes_stale_plist_when_missing_service_is_reported_on_stdout(self):
        self.run_isolated("""
plist = pathlib.Path(server._launchd_update_plist())
plist.write_text("stale", encoding="utf-8")
fake = Launchctl(missing_stream="stdout")
server.subprocess.run = fake
server._cancel_update_timer()
assert not plist.exists()
assert not any(call[:2] == ["/bin/launchctl", "bootout"] for call in fake.calls)
""")

    def test_cancel_removes_stale_plist_when_missing_service_is_reported_on_stderr(self):
        self.run_isolated("""
plist = pathlib.Path(server._launchd_update_plist())
plist.write_text("stale", encoding="utf-8")
fake = Launchctl(missing_stream="stderr")
server.subprocess.run = fake
server._cancel_update_timer()
assert not plist.exists()
""")

    def test_cancel_unloads_an_idle_loaded_agent_and_confirms_absence(self):
        self.run_isolated("""
plist = pathlib.Path(server._launchd_update_plist())
plist.write_text("stale", encoding="utf-8")
fake = Launchctl()
fake.loaded = True
server.subprocess.run = fake
server._cancel_update_timer()
assert not fake.loaded
assert not plist.exists()
assert any(call[:2] == ["/bin/launchctl", "bootout"] for call in fake.calls)
""")

    def test_cancel_refuses_to_unload_an_active_updater(self):
        self.run_isolated("""
plist = pathlib.Path(server._launchd_update_plist())
plist.write_text("active", encoding="utf-8")
fake = Launchctl()
fake.loaded = True
fake.running = True
server.subprocess.run = fake
try:
    server._cancel_update_timer()
except RuntimeError as error:
    assert "déjà en cours" in str(error)
else:
    raise AssertionError("Une tâche active a été déchargée.")
assert plist.exists()
assert not any(call[:2] == ["/bin/launchctl", "bootout"] for call in fake.calls)
""")

    def test_cancel_fails_closed_when_bootout_does_not_unload_agent(self):
        self.run_isolated("""
plist = pathlib.Path(server._launchd_update_plist())
plist.write_text("keep", encoding="utf-8")
fake = Launchctl(fail_on="bootout")
fake.loaded = True
server.subprocess.run = fake
try:
    server._cancel_update_timer()
except RuntimeError as error:
    assert "toujours chargée" in str(error)
else:
    raise AssertionError("Le service encore chargé a été considéré comme déchargé.")
assert plist.exists()
""")

    def test_cancel_does_not_hide_unexpected_launchctl_lookup_errors(self):
        self.run_isolated("""
plist = pathlib.Path(server._launchd_update_plist())
plist.write_text("keep", encoding="utf-8")
fake = Launchctl(fail_on="initial_print")
server.subprocess.run = fake
try:
    server._cancel_update_timer()
except RuntimeError as error:
    assert "Impossible de vérifier" in str(error)
else:
    raise AssertionError("Une erreur launchctl non reconnue a été ignorée.")
assert plist.exists()
""")

    def test_start_replaces_a_stale_on_disk_plist_with_a_fresh_immediate_job(self):
        self.run_isolated("""
plist = pathlib.Path(server._launchd_update_plist())
plist.write_text("obsolete plist", encoding="utf-8")
fake = Launchctl()
server.subprocess.run = fake
server._start_update_apply_service()
import plistlib
with plist.open("rb") as stream:
    definition = plistlib.load(stream)
assert definition["Label"] == "fr.maclasse.update"
assert definition["ProgramArguments"] == ["/bin/bash", str(pathlib.Path(server.ROOT) / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh")]
assert definition["RunAtLoad"] is False
assert "StartCalendarInterval" not in definition
assert definition["EnvironmentVariables"]["MACLASSE_DATA_DIR"] == str(pathlib.Path(server.DATA_DIR).resolve())
commands = [call[:2] for call in fake.calls]
assert commands.index(["/usr/bin/plutil", "-lint"]) < commands.index(["/bin/launchctl", "bootstrap"])
assert commands.index(["/bin/launchctl", "bootstrap"]) < commands.index(["/bin/launchctl", "kickstart"])
assert fake.running
""")

    def test_start_unloads_an_idle_stale_launchd_job_before_bootstrap(self):
        self.run_isolated("""
fake = Launchctl()
fake.loaded = True
server.subprocess.run = fake
server._start_update_apply_service()
bootout = next(i for i, call in enumerate(fake.calls) if call[:2] == ["/bin/launchctl", "bootout"])
bootstrap = next(i for i, call in enumerate(fake.calls) if call[:2] == ["/bin/launchctl", "bootstrap"])
kickstart = next(i for i, call in enumerate(fake.calls) if call[:2] == ["/bin/launchctl", "kickstart"])
assert bootout < bootstrap < kickstart
assert fake.running
""")

    def test_start_refuses_an_already_running_updater_without_mutating_it(self):
        self.run_isolated("""
fake = Launchctl()
fake.loaded = True
fake.running = True
server.subprocess.run = fake
try:
    server._start_update_apply_service()
except RuntimeError as error:
    assert "déjà en cours" in str(error)
else:
    raise AssertionError("Une mise à jour concurrente a été autorisée.")
assert not any(call[:2] in (["/bin/launchctl", "bootout"], ["/bin/launchctl", "bootstrap"], ["/bin/launchctl", "kickstart"]) for call in fake.calls)
""")

    def test_start_reports_missing_installer_script_and_keeps_version_untouched(self):
        self.run_isolated("""
pathlib.Path(server.ROOT, "Appliquer-Mise-A-Jour-MaClasse-macOS.sh").unlink()
fake = Launchctl()
server.subprocess.run = fake
try:
    server._start_update_apply_service()
except FileNotFoundError as error:
    assert "absent" in str(error)
else:
    raise AssertionError("Le script d'installation manquant n'a pas été détecté.")
log = pathlib.Path(server.DATA_DIR) / "macos-update-error.log"
assert "absent" in log.read_text(encoding="utf-8")
assert not fake.loaded
""")

    def test_start_logs_plutil_validation_failure_and_cleans_partial_definition(self):
        self.run_isolated("""
fake = Launchctl(fail_on="plutil")
server.subprocess.run = fake
try:
    server._start_update_apply_service()
except subprocess.CalledProcessError:
    pass
else:
    raise AssertionError("Un plist invalide a été accepté.")
log = pathlib.Path(server.DATA_DIR) / "macos-update-error.log"
assert "plutil" in log.read_text(encoding="utf-8")
assert "test plist syntax failure" in log.read_text(encoding="utf-8")
assert not pathlib.Path(server._launchd_update_plist()).exists()
""")

    def test_start_logs_bootstrap_failure_and_cleans_partial_definition(self):
        self.run_isolated("""
fake = Launchctl(fail_on="bootstrap")
server.subprocess.run = fake
try:
    server._start_update_apply_service()
except subprocess.CalledProcessError:
    pass
else:
    raise AssertionError("Un échec bootstrap n'a pas été remonté.")
log = pathlib.Path(server.DATA_DIR) / "macos-update-error.log"
assert "bootstrap" in log.read_text(encoding="utf-8")
assert "test bootstrap failure" in log.read_text(encoding="utf-8")
assert not pathlib.Path(server._launchd_update_plist()).exists()
""")

    def test_start_logs_kickstart_failure_and_unloads_partial_agent(self):
        self.run_isolated("""
fake = Launchctl(fail_on="kickstart")
server.subprocess.run = fake
try:
    server._start_update_apply_service()
except subprocess.CalledProcessError:
    pass
else:
    raise AssertionError("Un échec kickstart n'a pas été remonté.")
log = pathlib.Path(server.DATA_DIR) / "macos-update-error.log"
assert "kickstart" in log.read_text(encoding="utf-8")
assert "test kickstart failure" in log.read_text(encoding="utf-8")
assert not pathlib.Path(server._launchd_update_plist()).exists()
assert not fake.loaded
""")

    def test_start_keeps_an_agent_loaded_when_confirmed_running_after_uncertain_reply(self):
        self.run_isolated("""
fake = Launchctl(fail_on="confirm")
server.subprocess.run = fake
try:
    server._start_update_apply_service()
except RuntimeError as error:
    assert "confirmation failure" in str(error)
else:
    raise AssertionError("Un démarrage launchd non confirmé a été annoncé comme réussi.")
log = pathlib.Path(server.DATA_DIR) / "macos-update-error.log"
assert "confirmation failure" in log.read_text(encoding="utf-8")
# The fake process has a PID; fail-safe cleanup must not unload an active updater.
assert fake.loaded and fake.running
""")

    def test_start_validates_plist_before_bootstrap_and_kickstart(self):
        self.run_isolated("""
fake = Launchctl()
server.subprocess.run = fake
server._start_update_apply_service()
commands = [call[:2] for call in fake.calls]
assert commands.index(["/usr/bin/plutil", "-lint"]) < commands.index(["/bin/launchctl", "bootstrap"])
assert commands.index(["/bin/launchctl", "bootstrap"]) < commands.index(["/bin/launchctl", "kickstart"])
assert fake.running
""")


if __name__ == "__main__":
    unittest.main()
