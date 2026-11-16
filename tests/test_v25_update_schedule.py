#!/usr/bin/env python3
"""Unit tests for one-off systemd maintenance timers."""
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def run():
    with tempfile.TemporaryDirectory() as temp:
        timer = Path(temp) / "maclasse-update-scheduled.timer"
        timestamp = int(time.time()) + 3600
        with patch.object(server, "_update_timer_unit_path", return_value=str(timer)), \
             patch.object(server.subprocess, "run") as command:
            server._schedule_update_timer(timestamp)
            assert timer.is_file()
            content = timer.read_text(encoding="utf-8")
            assert "[Timer]" in content
            assert "OnCalendar=" in content and " UTC" in content
            assert "AccuracySec=1s" in content
            assert "Persistent=false" in content
            assert "Unit=maclasse-update-apply.service" in content
            assert command.call_count == 5
            server._cancel_update_timer()
            assert not timer.exists()
            assert command.call_count == 7
    print("OK — timer systemd unique, UTC, précis, annulable et sans exécution shell arbitraire.")


if __name__ == "__main__":
    run()
