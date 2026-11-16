#!/usr/bin/env python3
"""Unit tests for one-off systemd maintenance timers."""
import tempfile
import time
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def run():
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
            assert "[Timer]" in content
            assert "OnCalendar=" in content and " UTC" in content
            assert "AccuracySec=1s" in content
            assert "Persistent=false" in content
            assert "Unit=maclasse-update-apply.service" in content
            assert command.call_count == 8
            second_timestamp = timestamp + 3600
            server._schedule_update_timer(second_timestamp)
            rescheduled = timer.read_text(encoding="utf-8")
            expected = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(second_timestamp))
            assert f"OnCalendar={expected}" in rescheduled
            assert rescheduled.count("OnCalendar=") == 1
            assert command.call_count == 16
            server._cancel_update_timer()
            assert not timer.exists()
            assert command.call_count == 20
    with tempfile.TemporaryDirectory() as temp:
        timer = Path(temp) / "maclasse-update-scheduled.timer"
        timer.write_text("[Timer]", encoding="utf-8")
        def stuck_run(command, **kwargs):
            if "is-active" in command:
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

    print("OK — timer systemd unique, UTC, précis, reprogrammable, annulable et sans exécution shell arbitraire.")


if __name__ == "__main__":
    run()
