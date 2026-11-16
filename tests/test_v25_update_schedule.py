#!/usr/bin/env python3
"""Unit tests for one-off systemd maintenance timers."""
import os
import tempfile
import time
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server



def test_public_maintenance_projection_keeps_installing_notice_and_hides_private_fields():
    scheduled = server._public_update_maintenance({
        "status": "scheduled", "version": "25.0.23", "scheduled_at": 1800000000,
        "timezone": "Europe/Paris", "scheduled_by": "secret-admin-id", "created_at": 1
    })
    assert scheduled["scheduled"] is True
    assert scheduled["in_progress"] is False
    assert scheduled["maintenance"] == {
        "status": "scheduled", "version": "25.0.23",
        "scheduled_at": 1800000000, "timezone": "Europe/Paris"
    }
    installing = server._public_update_maintenance({
        "status": "installing", "version": "25.0.23", "scheduled_at": 1800000000,
        "timezone": "Europe/Paris", "scheduled_by": "secret-admin-id"
    })
    assert installing["scheduled"] is False
    assert installing["in_progress"] is True
    assert installing["maintenance"]["status"] == "installing"
    assert "scheduled_by" not in installing["maintenance"]
    for terminal in ("completed", "failed", "cancelled", "unknown"):
        hidden = server._public_update_maintenance({"status": terminal, "version": "25.0.23"})
        assert hidden == {"scheduled": False, "in_progress": False, "maintenance": None}
    assert server._public_update_maintenance(None)["maintenance"] is None

def test_linux_updater_support_requires_a_loaded_systemd_unit():
    with tempfile.TemporaryDirectory() as temp:
        data = Path(temp)
        (data / "update-manager.enabled").write_text("enabled", encoding="utf-8")
        env = {"MACLASSE_SUPERVISED": "systemd"}
        with patch.object(server.sys, "platform", "linux"), \
             patch.object(server, "DATA_DIR", str(data)), \
             patch.dict(os.environ, env, clear=False), \
             patch.object(server.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="not-found\n", stderr="")) as command:
            assert server._update_apply_service_installed() is False
            assert command.call_args.args[0][-1] == "maclasse-update-apply.service"
        with patch.object(server.sys, "platform", "linux"), \
             patch.object(server, "DATA_DIR", str(data)), \
             patch.dict(os.environ, env, clear=False), \
             patch.object(server.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="loaded\n", stderr="")):
            assert server._update_apply_service_installed() is True


def run():
    test_public_maintenance_projection_keeps_installing_notice_and_hides_private_fields()
    test_linux_updater_support_requires_a_loaded_systemd_unit()
    with tempfile.TemporaryDirectory() as temp:
        timer = Path(temp) / "maclasse-update-scheduled.timer"
        timestamp = int(time.time()) + 3600

        def fake_run(command, **kwargs):
            if "is-active" in command:
                return SimpleNamespace(returncode=3)
            if "is-enabled" in command:
                return SimpleNamespace(returncode=1)
            return SimpleNamespace(returncode=0)

        with patch.object(server.sys, "platform", "linux"), \
             patch.object(server, "_update_timer_unit_path", return_value=str(timer)), \
             patch.object(server.subprocess, "run", side_effect=fake_run) as command:
            server._schedule_update_timer(timestamp)
            assert timer.is_file()
            content = timer.read_text(encoding="utf-8")
            assert content.splitlines()[0] == "[Unit]"
            assert content.splitlines()[1].startswith("Description=MaClasse")
            assert content.count("[Unit]") == 1 and content.count("[Timer]") == 1 and content.count("[Install]") == 1
            assert "\\n" not in content, "timer file must contain real newlines, not literal backslash-n sequences"
            assert "[Timer]" in content
            assert "OnCalendar=" in content and " UTC" in content
            assert "AccuracySec=1s" in content
            assert "Persistent=false" in content
            assert "Unit=maclasse-update-apply.service" in content
            assert command.call_count == 9
            second_timestamp = timestamp + 3600
            server._schedule_update_timer(second_timestamp)
            rescheduled = timer.read_text(encoding="utf-8")
            expected = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(second_timestamp))
            assert f"OnCalendar={expected}" in rescheduled
            assert rescheduled.count("OnCalendar=") == 1
            assert command.call_count == 18
            server._cancel_update_timer()
            assert not timer.exists()
            assert command.call_count == 23
    with tempfile.TemporaryDirectory() as temp:
        timer = Path(temp) / "maclasse-update-scheduled.timer"
        timer.write_text("[Timer]", encoding="utf-8")
        def stuck_run(command, **kwargs):
            if "is-active" in command and "maclasse-update-apply.service" in command:
                return SimpleNamespace(returncode=3)
            if "is-active" in command and "maclasse-update-scheduled.timer" in command:
                return SimpleNamespace(returncode=0)
            if "is-enabled" in command:
                return SimpleNamespace(returncode=0)
            return SimpleNamespace(returncode=0)
        with patch.object(server.sys, "platform", "linux"), \
             patch.object(server, "_update_timer_unit_path", return_value=str(timer)), \
             patch.object(server.subprocess, "run", side_effect=stuck_run):
            try:
                server._cancel_update_timer()
            except RuntimeError:
                pass
            else:
                raise AssertionError("systemd timer still active but cancellation was accepted")
            assert timer.exists(), "active timer unit must not be deleted"

    calls = []
    def active_apply(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0)
    with patch.object(server.sys, "platform", "linux"), \
         patch.object(server.subprocess, "run", side_effect=active_apply):
        try:
            server._start_update_apply_service()
        except RuntimeError:
            pass
        else:
            raise AssertionError("immediate systemd start was allowed while an updater was active")
        assert len(calls) == 1
        assert "is-active" in calls[0]
        assert "start" not in calls[0]

    print("OK — timer systemd unique, UTC, précis, reprogrammable, annulable et sans exécution shell arbitraire.")


if __name__ == "__main__":
    run()
