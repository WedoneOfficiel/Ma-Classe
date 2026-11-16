#!/usr/bin/env python3
"""Concurrency tests for manually launched MaClasse server processes."""
import fcntl
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class ManualUpdateLockTests(unittest.TestCase):
    def test_manual_server_holds_shared_lock_until_exit(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(server, "DATA_DIR", temp), \
             patch.dict(os.environ, {"MACLASSE_SUPERVISED": ""}, clear=False):
            lock_fd = server._acquire_manual_server_lock()
            self.assertIsInstance(lock_fd, int)
            path = Path(temp) / "update-apply.lock"
            probe = (
                "import fcntl,os,sys; fd=os.open(sys.argv[1],os.O_RDWR); "
                "fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)"
            )
            blocked = subprocess.run([sys.executable, "-c", probe, str(path)], capture_output=True)
            self.assertNotEqual(blocked.returncode, 0, "updater must not acquire an exclusive lock beside a manual server")
            os.close(lock_fd)
            allowed = subprocess.run([sys.executable, "-c", probe, str(path)], capture_output=True)
            self.assertEqual(allowed.returncode, 0, allowed.stderr.decode(errors="replace"))

    def test_manual_server_refuses_to_start_while_updater_holds_exclusive_lock(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(server, "DATA_DIR", temp), \
             patch.dict(os.environ, {"MACLASSE_SUPERVISED": ""}, clear=False):
            path = Path(temp) / "update-apply.lock"
            fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                with self.assertRaises(RuntimeError):
                    server._acquire_manual_server_lock()
            finally:
                os.close(fd)

    def test_supervised_service_does_not_take_a_shared_lock(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(server, "DATA_DIR", temp), \
             patch.dict(os.environ, {"MACLASSE_SUPERVISED": "systemd"}, clear=False):
            self.assertIsNone(server._acquire_manual_server_lock())
            self.assertFalse((Path(temp) / "update-apply.lock").exists())


if __name__ == "__main__":
    unittest.main()
