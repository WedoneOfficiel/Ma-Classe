#!/usr/bin/env python3
"""Offline security and regression tests for the release checker."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import update_manager as updater


class ReleaseCheckerTests(unittest.TestCase):
    def setUp(self):
        self.archive = self.make_zip({"server.py": "print('ok')", "VERSION.txt": "V25.1.0", "requirements.txt": ""})
        self.manifest = {
            "schema_version": 1,
            "version": "25.1.0",
            "tag_name": "v25.1.0",
            "min_data_schema": 1,
            "archive_asset": "maclasse-v25.1.0.zip",
            "sha256": hashlib.sha256(self.archive).hexdigest(),
            "release_notes": "Corrections et améliorations."
        }
        self.release = {
            "draft": False,
            "prerelease": False,
            "tag_name": "v25.1.0",
            "html_url": "https://github.com/WedoneOfficiel/Ma-Classe/releases/tag/v25.1.0",
            "assets": [
                {"name": updater.MANIFEST_ASSET, "browser_download_url": "https://example.test/manifest"},
                {"name": self.manifest["archive_asset"], "browser_download_url": "https://example.test/archive"}
            ]
        }

    @staticmethod
    def make_zip(files):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return buffer.getvalue()

    def fake_request(self, url, limit):
        if url == updater.API_LATEST:
            return json.dumps(self.release).encode()
        if url == "https://example.test/manifest":
            return json.dumps(self.manifest).encode()
        if url == "https://example.test/archive":
            return self.archive
        raise AssertionError("URL inattendue : " + url)

    def test_release_is_found_and_archive_prepared_without_install(self):
        with patch.object(updater, "_request", side_effect=self.fake_request):
            info = updater.check_latest_release("25.0.22")
            self.assertTrue(info["available"])
            self.assertEqual(info["version"], "v25.1.0")
            with tempfile.TemporaryDirectory() as temp:
                prepared = updater.prepare_release(info, temp)
                self.assertEqual((prepared / "VERSION.txt").read_text(), "V25.1.0")
                self.assertTrue(prepared.is_relative_to(Path(temp).resolve()))
                self.assertEqual(json.loads((prepared / "maclasse-prepared.json").read_text())["status"], "prepared")

    def test_no_update_when_same_or_newer_version_installed(self):
        with patch.object(updater, "_request", side_effect=self.fake_request):
            self.assertFalse(updater.check_latest_release("25.1.0")["available"])
            self.assertFalse(updater.check_latest_release("25.2.0")["available"])

    def test_rejects_invalid_tag(self):
        self.release["tag_name"] = "latest"
        with patch.object(updater, "_request", side_effect=self.fake_request):
            with self.assertRaises(updater.UpdateError):
                updater.check_latest_release("25.0.22")

    def test_rejects_prerelease(self):
        self.release["prerelease"] = True
        with patch.object(updater, "_request", side_effect=self.fake_request):
            with self.assertRaises(updater.UpdateError):
                updater.check_latest_release("25.0.22")

    def test_rejects_archive_hash_mismatch(self):
        info = {
            "archive_url": "https://example.test/archive",
            "sha256": "0" * 64,
        }
        with patch.object(updater, "_request", side_effect=self.fake_request):
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(updater.UpdateError):
                    updater.prepare_release(info, temp)
                self.assertEqual(list(Path(temp).iterdir()), [])

    def test_rejects_path_traversal(self):
        bad_zip = self.make_zip({"../outside.txt": "no"})
        info = {"archive_url": "https://example.test/archive", "sha256": hashlib.sha256(bad_zip).hexdigest()}
        with patch.object(updater, "_request", return_value=bad_zip):
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(updater.UpdateError):
                    updater.prepare_release(info, temp)
                self.assertEqual(list(Path(temp).iterdir()), [])

    def test_prepares_isolated_runtime_and_reuses_matching_requirements(self):
        with tempfile.TemporaryDirectory() as temp:
            program = Path(temp)
            (program / "requirements.txt").write_text("", encoding="utf-8")
            (program / "server.py").write_text("print('ok')", encoding="utf-8")
            (program / "_all.js").write_text("const ok=true;", encoding="utf-8")
            calls = []
            def fake_run(command, **kwargs):
                calls.append(command)
                if command[1:3] == ["-m", "venv"]:
                    python = Path(command[-1]) / "bin" / "python"
                    python.parent.mkdir(parents=True, exist_ok=True)
                    python.write_text("", encoding="utf-8")
                return None
            with patch.object(updater.subprocess, "run", side_effect=fake_run), patch.object(updater.shutil, "which", return_value=None):
                python = updater.prepare_runtime(program)
                self.assertTrue(python.is_file())
                self.assertEqual(len(calls), 3)
                updater.prepare_runtime(program)
                self.assertEqual(len(calls), 3)

    def test_runtime_failure_removes_partial_virtual_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            program = Path(temp)
            (program / "requirements.txt").write_text("", encoding="utf-8")
            with patch.object(updater.subprocess, "run", side_effect=updater.subprocess.CalledProcessError(1, ["python"])):
                with self.assertRaises(updater.UpdateError):
                    updater.prepare_runtime(program)
            self.assertFalse((program / ".venv").exists())
            self.assertFalse((program / "maclasse-runtime-ready.json").exists())

    def test_rejects_http_asset_url(self):
        with self.assertRaises(updater.UpdateError):
            updater._request("http://example.test/archive", 100)

    def test_rejects_untrusted_https_host(self):
        with self.assertRaises(updater.UpdateError):
            updater._request("https://example.test/archive", 100)

    def test_rejects_reserved_data_and_runtime_paths(self):
        for name in ("data/maclasse.json", ".venv/bin/python", "maclasse-runtime-ready.json"):
            with self.assertRaises(updater.UpdateError):
                updater._safe_member_path(name)

    def test_rejects_windows_path_and_backslash(self):
        for name in ("C:/outside.txt", "folder\\\\..\\\\outside.txt"):
            with self.assertRaises(updater.UpdateError):
                updater._safe_member_path(name)

    def test_rejects_boolean_data_schema(self):
        self.manifest["min_data_schema"] = True
        with patch.object(updater, "_request", side_effect=self.fake_request):
            with self.assertRaises(updater.UpdateError):
                updater.check_latest_release("25.0.22")

    def test_manifest_must_match_release_tag(self):
        self.manifest["tag_name"] = "v99.0.0"
        with patch.object(updater, "_request", side_effect=self.fake_request):
            with self.assertRaises(updater.UpdateError):
                updater.check_latest_release("25.0.22")


if __name__ == "__main__":
    unittest.main()
