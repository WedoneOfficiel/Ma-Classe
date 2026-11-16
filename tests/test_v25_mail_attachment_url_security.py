import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class MailAttachmentUrlSecurityTests(unittest.TestCase):
    def test_only_canonical_relative_upload_urls_are_accepted(self):
        prefix = "mail-v2/teacher:teacher_1/"
        good = "/data/uploads/mail-v2/teacher:teacher_1/report.pdf"
        self.assertEqual(server._mail_attachment_relative_path(good), good[len("/data/uploads/"):])
        self.assertTrue(server._mail_attachment_relative_path(good).startswith(prefix))

    def test_rejects_script_external_and_protocol_relative_urls(self):
        prefix = "mail-v2/teacher:teacher_1/report.pdf"
        for url in (
            "javascript:alert(1)//data/uploads/" + prefix,
            "https://evil.example/data/uploads/" + prefix,
            "//evil.example/data/uploads/" + prefix,
            "file:///data/uploads/" + prefix,
            "data:text/html,<script>alert(1)</script>",
        ):
            with self.subTest(url=url):
                self.assertIsNone(server._mail_attachment_relative_path(url))

    def test_rejects_traversal_encoded_separators_and_query_fragments(self):
        base = "/data/uploads/mail-v2/teacher:teacher_1/"
        for suffix in ("../student:other/secret.pdf", "%2e%2e/secret.pdf",
                       "folder/%2F..%2Fsecret.pdf", "report.pdf?download=1",
                       "report.pdf#preview", "folder//report.pdf", "folder/./report.pdf"):
            with self.subTest(suffix=suffix):
                self.assertIsNone(server._mail_attachment_relative_path(base + suffix))

    def test_mailbox_projection_drops_invalid_attachment_urls(self):
        message = {
            "id": "m1",
            "attachments": [
                {"name": "safe.pdf", "url": "/data/uploads/mail-v2/teacher:teacher_1/safe.pdf"},
                {"name": "bad.pdf", "url": "javascript:alert(1)//data/uploads/mail-v2/teacher:teacher_1/bad.pdf"},
            ],
        }
        safe = server._mailbox_message_safe_attachments(message, ("mail-v2/teacher:teacher_1/",))
        self.assertEqual([x["name"] for x in safe["attachments"]], ["safe.pdf"])


if __name__ == "__main__":
    unittest.main()
