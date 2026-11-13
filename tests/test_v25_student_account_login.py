import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class QuietHandler(server.Handler):
    def log_message(self, *_args):
        pass


class StudentAccountLoginIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_data_file = server.DATA_FILE
        self.old_host, self.old_port = server.HOST, server.PORT
        server.DATA_FILE = os.path.join(self.temp.name, "maclasse.json")
        server.HOST = "127.0.0.1"
        server.SESSIONS.clear()
        server.LOGIN_ATTEMPTS.clear()
        initial = {
            "users": [{
                "id": "teacher-1", "role": "teacher", "username": "teacher",
                "active": True, "passwordHash": server._password_hash("TeacherPass123!")
            }],
            "classes": [{
                "id": "class-1", "name": "CMA", "teacherIds": ["teacher-1"]
            }],
            "students": [{
                "id": "student-1", "first": "Test", "last": "Eleve",
                "classId": "class-1"
            }]
        }
        with open(server.DATA_FILE, "w", encoding="utf-8") as handle:
            json.dump(initial, handle)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        server.PORT = self.httpd.server_port
        self.origin = "http://127.0.0.1:" + str(server.PORT)
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        server.SESSIONS.clear()
        server.LOGIN_ATTEMPTS.clear()
        server.DATA_FILE = self.old_data_file
        server.HOST, server.PORT = self.old_host, self.old_port
        self.temp.cleanup()

    def request(self, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.origin + path, data=data,
            headers={"Origin": self.origin, "Content-Type": "application/json"},
            method="GET" if payload is None else "POST"
        )
        with self.opener.open(request, timeout=5) as response:
            body = response.read()
            return response.status, json.loads(body) if body else {}

    def test_teacher_created_temporary_student_access_can_log_in_and_change_password(self):
        status, teacher = self.request("/api/auth/login", {
            "username": "teacher", "password": "TeacherPass123!"
        })
        self.assertEqual(status, 200)
        self.assertEqual(teacher["user"]["role"], "teacher")

        status, created = self.request("/api/admin/student-account", {
            "studentId": "student-1", "username": "test.eleve"
        })
        self.assertEqual(status, 200)
        temporary = created["user"]["temporaryPassword"]
        self.assertTrue(temporary)

        self.request("/api/auth/logout", {})
        status, student = self.request("/api/auth/login", {
            "username": "test.eleve", "password": temporary
        })
        self.assertEqual(status, 200)
        self.assertEqual(student["user"]["role"], "student")
        self.assertEqual(student["user"]["studentId"], "student-1")
        self.assertTrue(student["user"]["mustChangePassword"])

        status, session = self.request("/api/auth/session")
        self.assertEqual(status, 200)
        self.assertTrue(session["authenticated"])
        self.assertEqual(session["user"]["role"], "student")

        self.request("/api/auth/change-password", {
            "currentPassword": temporary, "newPassword": "StudentPass123!"
        })
        self.request("/api/auth/logout", {})
        status, student = self.request("/api/auth/login", {
            "username": "test.eleve", "password": "StudentPass123!"
        })
        self.assertEqual(status, 200)
        self.assertFalse(student["user"]["mustChangePassword"])

        status, visible = self.request("/api/data")
        self.assertEqual(status, 200)
        self.assertEqual(visible["students"][0]["id"], "student-1")
        self.assertFalse(any("passwordHash" in item for item in visible["students"]))
        self.assertFalse(any("passwordHash" in item for item in visible["users"]))


if __name__ == "__main__":
    unittest.main()
