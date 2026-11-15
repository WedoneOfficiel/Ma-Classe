#!/usr/bin/env python3
"""Student grade publication must be enforced by the server projection."""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class StudentGradePublicationTests(unittest.TestCase):
    def test_student_receives_only_published_current_group_grades_for_self(self):
        today = datetime.date.today().isoformat()
        data = {
            "users": [],
            "students": [
                {"id": "s1", "classId": "c1", "group": "A", "first": "Alice"},
                {"id": "s2", "classId": "c1", "group": "A", "first": "Bob"},
                {"id": "s3", "classId": "c1", "group": "B", "first": "Chloé"},
            ],
            "classes": [{"id": "c1", "name": "6e A", "teacherIds": []}],
            "settings": {"terms": []},
            "schedule": [], "lessons": [], "attendance": [], "bulletins": [],
            "attachments": [], "submissions": [], "notifications": [],
            "evaluations": [
                {"id": "visible", "classId": "c1", "group": "A", "published": True,
                 "publishAt": today, "grades": [
                     {"studentId": "s1", "value": "14"},
                     {"studentId": "s2", "value": "18"}]},
                {"id": "unpublished", "classId": "c1", "group": "A", "published": False,
                 "grades": [{"studentId": "s1", "value": "19"}]},
                {"id": "scheduled", "classId": "c1", "group": "A", "published": True,
                 "publishAt": "2999-01-01", "grades": [{"studentId": "s1", "value": "20"}]},
                {"id": "other-group", "classId": "c1", "group": "B", "published": True,
                 "grades": [{"studentId": "s1", "value": "17"}]},
                {"id": "other-class", "classId": "c2", "published": True,
                 "grades": [{"studentId": "s1", "value": "16"}]},
            ],
        }
        visible = server._student_visible_data(
            data, {"id": "account-s1", "role": "student", "studentId": "s1"}
        )
        self.assertEqual([e["id"] for e in visible["evaluations"]], ["visible"])
        self.assertEqual(visible["evaluations"][0]["grades"], [
            {"studentId": "s1", "value": "14"}
        ])

    def test_publication_date_is_compared_as_a_calendar_date(self):
        today = datetime.date.today().isoformat()
        data = {
            "users": [], "students": [{"id": "s1", "classId": "c1", "group": ""}],
            "classes": [{"id": "c1", "name": "6e"}], "settings": {"terms": []},
            "schedule": [], "lessons": [], "attendance": [], "bulletins": [],
            "attachments": [], "submissions": [], "notifications": [],
            "evaluations": [{
                "id": "today", "classId": "c1", "published": True,
                "publishAt": today + "T08:00:00Z",
                "grades": [{"studentId": "s1", "value": "12"}],
            }],
        }
        visible = server._student_visible_data(
            data, {"id": "account-s1", "role": "student", "studentId": "s1"}
        )
        self.assertEqual([e["id"] for e in visible["evaluations"]], ["today"])


if __name__ == "__main__":
    unittest.main()
