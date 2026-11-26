#!/usr/bin/env python3
"""Tests for the one-time direct macOS update launcher used to bootstrap older installations."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAME = "Installer-Mise-A-Jour-Directe-MaClasse-macOS.sh"
UPDATER_NAME = "Appliquer-Mise-A-Jour-MaClasse-macOS.sh"
VERSION = "25.1.1"
SHA = "a" * 64


class DirectMacUpdateBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="maclasse-direct-bootstrap-")
        self.base = Path(self.temp.name)
        self.root = self.base / "MaClasse"
        self.data = self.root / "data"
        self.versions = self.data / "program" / "versions"
        self.target = self.versions / ("V" + VERSION)
        self.current_version = self.versions / "V25.0.23"
        self.home = self.base / "home"
        self.fakebin = self.base / "fakebin"
        self.script = self.target / SCRIPT_NAME
        self.launcher_source = ROOT / SCRIPT_NAME
        self.fakebin.mkdir()
        (self.home / "Library" / "LaunchAgents").mkdir(parents=True)
        (self.root / ".venv" / "bin").mkdir(parents=True)
        (self.data / "backups").mkdir(parents=True)
        self.versions.mkdir(parents=True)
        self.target.mkdir()
        self.current_version.mkdir()
        self.data_file = self.data / "maclasse.json"
        self.data_file.write_text(json.dumps({"schemaVersion": 25011, "keep": "original"}), encoding="utf-8")
        (self.root / ".venv" / "bin" / "python").symlink_to(sys.executable)
        (self.data / "program" / "current").symlink_to(Path("versions") / "V25.0.23")
        (self.home / "Library" / "LaunchAgents" / "fr.maclasse.server.plist").write_text("installed", encoding="utf-8")
        (self.fakebin / "uname").write_text("#!/bin/sh\nprintf 'Darwin\\n'\n", encoding="utf-8")
        (self.fakebin / "uname").chmod(0o755)
        (self.target / ".venv" / "bin").mkdir(parents=True)
        (self.target / ".venv" / "bin" / "python").symlink_to(sys.executable)
        (self.target / "maclasse-runtime-ready.json").write_text("{}", encoding="utf-8")
        (self.target / "server.py").write_text("APP_VERSION='25.1.1'\n", encoding="utf-8")
        (self.target / "_all.js").write_text("const MC_VERSION='V25.1.1';\n", encoding="utf-8")
        (self.target / "VERSION.txt").write_text("V25.1.1\n", encoding="utf-8")
        metadata = {
            "status": "prepared", "version": "v" + VERSION,
            "sha256": SHA, "min_data_schema": 25011
        }
        (self.target / "maclasse-prepared.json").write_text(json.dumps(metadata), encoding="utf-8")
        state = {
            "status": "prepared", "version": "v" + VERSION,
            "sha256": SHA, "min_data_schema": 25011
        }
        (self.data / "update-state.json").write_text(json.dumps(state), encoding="utf-8")
        updater = self.target / UPDATER_NAME
        updater.write_text(
            '#!/bin/bash\nprintf "%s\\n%s\\n" "$MACLASSE_ROOT" "$MACLASSE_DATA_DIR" > "$MACLASSE_DATA_DIR/direct-installer-ran"\n',
            encoding="utf-8",
        )
        updater.chmod(0o700)
        self.script.write_text(self.launcher_source.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_launcher(self, *, uname="Darwin", root_uid=False):
        uname_script = self.fakebin / "uname"
        uname_script.write_text("#!/bin/sh\nprintf '" + uname + "\\n'\n", encoding="utf-8")
        uname_script.chmod(0o755)
        if root_uid:
            (self.fakebin / "id").write_text("#!/bin/sh\nprintf '0\\n'\n", encoding="utf-8")
            (self.fakebin / "id").chmod(0o755)
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["PATH"] = str(self.fakebin) + os.pathsep + env.get("PATH", "/usr/bin:/bin")
        env.pop("MACLASSE_ROOT", None)
        env.pop("MACLASSE_DATA_DIR", None)
        return subprocess.run(
            ["/bin/bash", str(self.script)],
            cwd=self.root, env=env, capture_output=True, text=True, timeout=30
        )

    def test_valid_prepared_release_runs_direct_installer_and_preserves_database(self):
        original = self.data_file.read_text(encoding="utf-8")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        marker = self.data / "direct-installer-ran"
        self.assertTrue(marker.is_file())
        self.assertEqual(marker.read_text(encoding="utf-8").splitlines(), [str(self.root), str(self.data)])
        self.assertEqual(self.data_file.read_text(encoding="utf-8"), original)
        self.assertIn("V25.1.1", result.stdout)

    def test_rejects_update_state_that_is_not_prepared(self):
        state = json.loads((self.data / "update-state.json").read_text(encoding="utf-8"))
        state["status"] = "downloading"
        (self.data / "update-state.json").write_text(json.dumps(state), encoding="utf-8")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Aucune version", result.stderr)
        self.assertFalse((self.data / "direct-installer-ran").exists())

    def test_rejects_malformed_or_traversal_version(self):
        state = json.loads((self.data / "update-state.json").read_text(encoding="utf-8"))
        state["version"] = "../../outside"
        (self.data / "update-state.json").write_text(json.dumps(state), encoding="utf-8")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Numéro de version", result.stderr)

    def test_rejects_invalid_sha256_in_update_state(self):
        state = json.loads((self.data / "update-state.json").read_text(encoding="utf-8"))
        state["sha256"] = "not-a-sha"
        (self.data / "update-state.json").write_text(json.dumps(state), encoding="utf-8")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Empreinte", result.stderr)

    def test_rejects_prepared_metadata_hash_mismatch(self):
        metadata = json.loads((self.target / "maclasse-prepared.json").read_text(encoding="utf-8"))
        metadata["sha256"] = "b" * 64
        (self.target / "maclasse-prepared.json").write_text(json.dumps(metadata), encoding="utf-8")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empreinte", result.stderr.lower())
        self.assertFalse((self.data / "direct-installer-ran").exists())

    def test_rejects_prepared_metadata_version_mismatch(self):
        metadata = json.loads((self.target / "maclasse-prepared.json").read_text(encoding="utf-8"))
        metadata["version"] = "v25.1.0"
        (self.target / "maclasse-prepared.json").write_text(json.dumps(metadata), encoding="utf-8")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("numéro de version", result.stderr.lower())

    def test_rejects_data_schema_newer_than_installed_database(self):
        state = json.loads((self.data / "update-state.json").read_text(encoding="utf-8"))
        state["min_data_schema"] = 99999
        (self.data / "update-state.json").write_text(json.dumps(state), encoding="utf-8")
        metadata = json.loads((self.target / "maclasse-prepared.json").read_text(encoding="utf-8"))
        metadata["min_data_schema"] = 99999
        (self.target / "maclasse-prepared.json").write_text(json.dumps(metadata), encoding="utf-8")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pas compatible", result.stderr)
        self.assertFalse((self.data / "direct-installer-ran").exists())

    def test_rejects_symlink_as_prepared_version_directory(self):
        outside = self.base / "outside"
        outside.mkdir()
        original = self.target
        original.rename(self.versions / "V25.1.1.real")
        self.script = self.versions / "V25.1.1.real" / SCRIPT_NAME
        self.target.symlink_to(outside, target_is_directory=True)
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("absent ou invalide", result.stderr)
        self.assertFalse((self.data / "direct-installer-ran").exists())

    def test_rejects_missing_launchd_service_installation(self):
        (self.home / "Library" / "LaunchAgents" / "fr.maclasse.server.plist").unlink()
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("service launchd", result.stderr)
        self.assertFalse((self.data / "direct-installer-ran").exists())

    def test_rejects_missing_active_version_symlink(self):
        (self.data / "program" / "current").unlink()
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lien de version active", result.stderr)

    def test_rejects_missing_root_python_environment(self):
        (self.root / ".venv" / "bin" / "python").unlink()
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python MaClasse est introuvable", result.stderr)

    def test_rejects_missing_runtime_ready_marker(self):
        (self.target / "maclasse-runtime-ready.json").unlink()
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("incomplète", result.stderr)

    def test_rejects_server_version_mismatch(self):
        (self.target / "server.py").write_text("APP_VERSION='25.1.0'\n", encoding="utf-8")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("version du serveur", result.stderr.lower())

    def test_rejects_windows_or_linux_host_before_preflight(self):
        result = self.run_launcher(uname="Linux")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("réservé à macOS", result.stderr)

    def test_refuses_root_execution(self):
        result = self.run_launcher(root_uid=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sudo", result.stderr)
        self.assertFalse((self.data / "direct-installer-ran").exists())


if __name__ == "__main__":
    unittest.main()
