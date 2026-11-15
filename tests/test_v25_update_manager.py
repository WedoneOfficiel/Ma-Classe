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

import update_manager as updater


class ReleaseCheckerTests(unittest.TestCase):
    def setUp(self):
        self.archive = self.make_zip({"MaClasse/server.py": "print('ok')", "MaClasse/VERSION.txt": "V25.1.0"})
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
                self.assertEqual((prepared / "MaClasse" / "VERSION.txt").read_text(), "V25.1.0")
                self.assertTrue(prepared.is_relative_to(Path(temp)))

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

    def test_rejects_http_asset_url(self):
        with self.assertRaises(updater.UpdateError):
            updater._request("http://example.test/archive", 100)

    def test_manifest_must_match_release_tag(self):
        self.manifest["tag_name"] = "v99.0.0"
        with patch.object(updater, "_request", side_effect=self.fake_request):
            with self.assertRaises(updater.UpdateError):
                updater.check_latest_release("25.0.22")


if __name__ == "__main__":
    unittest.main()
