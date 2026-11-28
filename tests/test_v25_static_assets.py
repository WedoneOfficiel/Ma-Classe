import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class StaticAssetAllowlistTests(unittest.TestCase):
    def test_application_javascript_assets_are_explicitly_allowed(self):
        for path in ("/", "/index.html", "/_all.js", "/class_tracking.js", "/release_notes.js"):
            with self.subTest(path=path):
                self.assertTrue(server.Handler._safe_static_path(None, path))

    def test_server_sources_and_unknown_scripts_are_not_public_static_assets(self):
        for path in ("/server.py", "/update_manager.py", "/release-signing-private-key.txt", "/unknown.js"):
            with self.subTest(path=path):
                self.assertFalse(server.Handler._safe_static_path(None, path))


if __name__ == "__main__":
    unittest.main()
