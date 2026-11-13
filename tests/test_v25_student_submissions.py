import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPCookieProcessor
from urllib.parse import quote
from http.cookiejar import CookieJar

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class QuietHandler(server.Handler):
    def log_message(self, *_args):
        pass


class StudentSubmissionUploadIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        self.old = {key: getattr(server, key) for key in ("ROOT", "DATA_DIR", "DATA_FILE", "UPLOADS", "HOST", "PORT")}
        server.ROOT = self.temp.name
        server.DATA_DIR = os.path.join(self.temp.name, "data")
        server.DATA_FILE = os.path.join(server.DATA_DIR, "maclasse.json")
        server.UPLOADS = os.path.join(server.DATA_DIR, "uploads")
        os.makedirs(server.UPLOADS, exist_ok=True)
        os.chdir(self.temp.name)
        server.HOST = "127.0.0.1"
        server.SESSIONS.clear()
        server.LOGIN_ATTEMPTS.clear()
        initial = {
            "users": [],
            "classes": [{"id": "class-1", "name": "6A", "teacherIds": []}],
            "students": [{"id": "student-1", "first": "Alice", "last": "Test", "classId": "class-1",
                          "username": "student", "role": "student", "active": True, "mustChangePassword": False,
                          "passwordHash": server._password_hash("StudentPass123!") }],
            "schedule": [],
            "lessons": [{
                "id": "lesson-1", "classId": "class-1", "date": "2026-11-13",
                "subject": "Français", "files": [],
                "homework": {"title": "Exercice", "due": "2026-11-20",
                             "instructions": "Rendre le fichier.", "files": [],
                             "requiresSubmission": True}
            }],
            "submissions": []
        }
        with open(server.DATA_FILE, "w", encoding="utf-8") as handle:
            json.dump(initial, handle)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        server.PORT = self.httpd.server_port
        self.origin = "http://127.0.0.1:" + str(server.PORT)
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        status, login, _ = self.request("/api/auth/login", "POST", {
            "username": "student", "password": "StudentPass123!"
        })
        self.assertEqual(status, 200, login)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        server.SESSIONS.clear()
        server.LOGIN_ATTEMPTS.clear()
        for key, value in self.old.items():
            setattr(server, key, value)
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def request(self, path, method="GET", payload=None, raw=None, extra_headers=None):
        data = raw
        headers = {"Origin": self.origin}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if extra_headers:
            headers.update(extra_headers)
        request = Request(self.origin + path, data=data, headers=headers, method=method)
        try:
            response = self.opener.open(request, timeout=5)
        except HTTPError as error:
            response = error
        body = response.read()
        if response.headers.get_content_type() == "application/json":
            try:
                body = json.loads(body.decode("utf-8"))
            except Exception:
                pass
        return response.status, body, response.headers

    def test_student_can_upload_persist_submit_and_read_own_attachment(self):
        status, visible, headers = self.request("/api/data")
        self.assertEqual(status, 200)
        revision = headers.get("X-MaClasse-Revision")
        self.assertTrue(revision)
        content = b"piece jointe de devoir"
        original_name = "Capture d’écran 2026-10-11 à 15.32.16.png"
        status, uploaded, _ = self.request(
            "/api/upload", "POST", raw=content,
            extra_headers={"X-Filename": "utf8:" + quote(original_name, safe=""), "X-Upload-Folder": "submissions/student-1"}
        )
        self.assertEqual(status, 200, uploaded)
        self.assertEqual(uploaded["name"], "submissions/student-1/" + original_name)
        visible["submissions"].append({
            "id": "submission-1", "lessonId": "lesson-1", "studentId": "student-1",
            "status": "draft", "files": [uploaded], "correctionFiles": [],
            "createdAt": "2026-11-13T12:00:00"
        })
        status, saved, _ = self.request("/api/save", "POST", visible, extra_headers={"If-Match": revision})
        self.assertEqual(status, 200, saved)
        status, fresh, headers = self.request("/api/data")
        self.assertEqual(status, 200)
        self.assertEqual(fresh["submissions"][0]["files"][0]["name"], uploaded["name"])
        revision = headers.get("X-MaClasse-Revision")
        status, file_body, _ = self.request("/data/uploads/" + quote(uploaded["name"], safe="/"))
        self.assertEqual(status, 200)
        self.assertEqual(file_body, content)
        fresh["submissions"][0]["status"] = "submitted"
        fresh["submissions"][0]["submittedAt"] = "2026-11-13T12:05:00"
        status, submitted, _ = self.request("/api/save", "POST", fresh, extra_headers={"If-Match": revision})
        self.assertEqual(status, 200, submitted)
        status, final_data, _ = self.request("/api/data")
        self.assertEqual(status, 200)
        self.assertEqual(final_data["submissions"][0]["status"], "submitted")
        self.assertTrue(final_data["submissions"][0]["submittedAt"])

    def test_student_cannot_upload_into_another_students_folder(self):
        status, result, _ = self.request(
            "/api/upload", "POST", raw=b"not allowed",
            extra_headers={"X-Filename": "intrus.txt", "X-Upload-Folder": "submissions/student-2"}
        )
        self.assertEqual(status, 403)
        self.assertIn("propre espace", result["error"])


if __name__ == "__main__":
    unittest.main()