import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class NeverRead:
    def read(self, length):
        raise AssertionError("request body must not be read before authentication")


class StubHandler:
    path = "/api/save"
    headers = {"Content-Length": str(100 * 1024 * 1024)}
    rfile = NeverRead()

    def __init__(self):
        self.auth_called = False
        self.response = None

    def _require_local_origin(self):
        return True

    def _require_auth(self, roles):
        self.auth_called = True
        self.roles = roles
        return None

    def _json(self, payload, status=200, headers=None):
        self.response = (status, payload)
        return self.response


class PostBodyAuthenticationTests(unittest.TestCase):
    def test_unauthenticated_large_post_is_rejected_before_body_read(self):
        handler = StubHandler()
        server.Handler.do_POST(handler)
        self.assertTrue(handler.auth_called)
        self.assertEqual(handler.roles, ("admin", "teacher", "student"))
        self.assertIsNone(handler.response)

    def test_large_backup_restore_is_admin_authorized_before_body_read(self):
        handler = StubHandler()
        handler.path = "/api/backup/restore"
        server.Handler.do_POST(handler)
        self.assertTrue(handler.auth_called)
        self.assertEqual(handler.roles, ("admin",))

    def test_change_password_requires_a_session_before_body_read(self):
        handler = StubHandler()
        handler.path = "/api/auth/change-password"
        handler._session_user = lambda: None
        server.Handler.do_POST(handler)
        self.assertEqual(handler.response[0], 401)

    def test_auth_endpoints_have_a_small_body_limit(self):
        source = (Path(__file__).resolve().parents[1] / "server.py").read_text(encoding="utf-8")
        self.assertIn("max_length=1*1024*1024", source)
        self.assertIn("max_length=50*1024*1024", source)
        self.assertIn("max_length=100*1024*1024", source)
        self.assertIn("max_length=20*1024*1024", source)


if __name__ == "__main__":
    unittest.main()
