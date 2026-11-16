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
            data, {"id": "account-s1", "role": "student", "studentId": "s1"},
            now=datetime.datetime.fromisoformat(today + "T12:00:00+00:00")
        )
        self.assertEqual([e["id"] for e in visible["evaluations"]], ["today"])

    def test_same_day_publication_time_is_not_exposed_before_its_time(self):
        today = datetime.date.today().isoformat()
        data = {
            "users": [], "students": [{"id": "s1", "classId": "c1"}],
            "classes": [{"id": "c1", "name": "6e"}], "settings": {"terms": []},
            "schedule": [], "lessons": [], "attendance": [], "bulletins": [],
            "attachments": [], "submissions": [], "notifications": [],
            "evaluations": [{
                "id": "later", "classId": "c1", "published": True,
                "publishAt": today + "T08:00:00Z",
                "grades": [{"studentId": "s1", "value": "12"}],
            }],
        }
        visible = server._student_visible_data(
            data, {"id": "account-s1", "role": "student", "studentId": "s1"},
            now=datetime.datetime.fromisoformat(today + "T07:00:00+00:00")
        )
        self.assertEqual(visible["evaluations"], [])

    def test_assigned_teacher_can_publish_and_only_valid_student_grades_are_saved(self):
        today = datetime.date.today().isoformat()
        current = {
            "users": [{"id": "t1", "role": "teacher"}],
            "classes": [{"id": "c1", "teacherIds": ["t1"], "principalTeacherId": "pp"}],
            "students": [{"id": "s1", "classId": "c1"}],
            "schedule": [{
                "id": "slot", "classId": "c1", "subject": "Maths",
                "teacherId": "t1", "teacherIds": [],
                "startDate": "2020-01-01", "endDate": "2999-12-31",
            }],
            "evaluations": [{
                "id": "e1", "classId": "c1", "subject": "Maths",
                "date": today, "published": False,
                "grades": [{"studentId": "s1", "value": ""}],
            }],
            "teacherAssignments": [], "lessons": [], "attendance": [],
            "bulletins": [], "attachments": [], "submissions": [],
            "conversations": [], "cloudItems": [], "notifications": [],
            "mailFolders": [],
        }
        import copy
        incoming = copy.deepcopy(current)
        incoming["evaluations"][0]["published"] = True
        incoming["evaluations"][0]["grades"] = [
            {"studentId": "s1", "value": "15"},
            {"studentId": "intruder", "value": "20"},
        ]
        merged = server._merge_teacher_data(
            current, incoming, {"id": "t1", "role": "teacher"}
        )
        saved = next(e for e in merged["evaluations"] if e["id"] == "e1")
        self.assertIs(saved["published"], True)
        self.assertEqual(saved["grades"], [{"studentId": "s1", "value": "15"}])

    def test_teacher_without_subject_assignment_cannot_publish_or_overwrite_grades(self):
        today = datetime.date.today().isoformat()
        current = {
            "users": [{"id": "t1", "role": "teacher"}],
            "classes": [{"id": "c1", "teacherIds": ["t1"]}],
            "students": [{"id": "s1", "classId": "c1"}],
            "schedule": [{
                "id": "slot", "classId": "c1", "subject": "Histoire",
                "teacherId": "t1", "teacherIds": [],
                "startDate": "2020-01-01", "endDate": "2999-12-31",
            }],
            "evaluations": [{
                "id": "e1", "classId": "c1", "subject": "Maths",
                "date": today, "published": False,
                "grades": [{"studentId": "s1", "value": "12"}],
            }],
            "teacherAssignments": [], "lessons": [], "attendance": [],
            "bulletins": [], "attachments": [], "submissions": [],
            "conversations": [], "cloudItems": [], "notifications": [],
            "mailFolders": [],
        }
        import copy
        incoming = copy.deepcopy(current)
        incoming["evaluations"][0]["published"] = True
        incoming["evaluations"][0]["grades"] = [
            {"studentId": "s1", "value": "20"}
        ]
        merged = server._merge_teacher_data(
            current, incoming, {"id": "t1", "role": "teacher"}
        )
        saved = next(e for e in merged["evaluations"] if e["id"] == "e1")
        self.assertIs(saved["published"], False)
        self.assertEqual(saved["grades"], [{"studentId": "s1", "value": "12"}])


if __name__ == "__main__":
    unittest.main()
