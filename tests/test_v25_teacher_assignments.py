#!/usr/bin/env python3
"""Tests for timetable-derived teacher permissions and temporary assignments."""
import copy
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class TeacherAssignmentTests(unittest.TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.today = today.isoformat()
        self.tomorrow = (today + datetime.timedelta(days=1)).isoformat()
        self.yesterday = (today - datetime.timedelta(days=1)).isoformat()
        self.data = {
            "users": [
                {"id": "t1", "role": "teacher", "subjects": []},
                {"id": "t2", "role": "teacher", "subjects": []},
                {"id": "t3", "role": "teacher", "subjects": []},
                {"id": "t4", "role": "teacher", "subjects": []},
                {"id": "t5", "role": "teacher", "subjects": []},
                {"id": "t6", "role": "teacher", "subjects": ["Legacy subject"]},
            ],
            "classes": [{"id": "c1", "name": "6e A", "teacherIds": ["t6"], "principalTeacherId": "pp"}],
            "students": [{"id": "s1", "classId": "c1", "first": "Alice", "last": "Test"}],
            "schedule": [
                {
                    "id": "slot1", "classId": "c1", "subject": "Mathématiques",
                    "teacherId": "t1", "teacherIds": ["t2"],
                    "startDate": self.yesterday, "endDate": self.tomorrow,
                    "recurrence": "weekly", "day": today.weekday(),
                    "exceptions": [], "overrides": {},
                },
                {
                    "id": "slot2", "classId": "c1", "subject": "Histoire",
                    "teacherId": "pp", "teacherIds": [],
                    "startDate": self.yesterday, "endDate": self.tomorrow,
                    "recurrence": "weekly", "day": today.weekday(),
                    "exceptions": [],
                    "overrides": {
                        self.today: {"status": "changed", "replacementTeacherId": "t4", "replacementOfTeacherId": "pp"}
                    },
                },
            ],
            "teacherAssignments": [
                {
                    "id": "a1", "scheduleId": "slot1", "classId": "c1",
                    "subject": "Français", "teacherId": "t3",
                    "startDate": self.yesterday, "endDate": self.tomorrow,
                    "type": "replacement",
                },
                {
                    "id": "a2", "scheduleId": "slot1", "classId": "c1",
                    "subject": "Sciences", "teacherId": "t5",
                    "startDate": "2020-01-01", "endDate": self.yesterday,
                    "type": "replacement",
                },
            ],
            "settings": {"terms": []},
            "lessons": [], "evaluations": [], "attendance": [],
            "bulletins": [], "attachments": [], "submissions": [],
            "conversations": [], "cloudItems": [], "notifications": [],
            "mailFolders": [],
        }

    def test_regular_and_multiple_teachers_get_subject_rights(self):
        self.assertTrue(server._teacher_can_teach_subject(
            self.data, {"id": "t1", "role": "teacher"}, "c1", "Mathématiques", self.today
        ))
        self.assertTrue(server._teacher_can_teach_subject(
            self.data, {"id": "t2", "role": "teacher"}, "c1", "Mathématiques", self.today
        ))

    def test_long_term_replacement_is_limited_to_its_dates_and_subject(self):
        user = {"id": "t3", "role": "teacher"}
        self.assertTrue(server._teacher_can_teach_subject(self.data, user, "c1", "Français", self.today))
        self.assertFalse(server._teacher_can_teach_subject(self.data, user, "c1", "Français", "2028-01-01"))
        self.assertFalse(server._teacher_can_teach_subject(self.data, user, "c1", "Mathématiques", self.today))

    def test_one_off_replacement_only_grants_rights_on_the_exception_date(self):
        user = {"id": "t4", "role": "teacher"}
        self.assertTrue(server._teacher_can_teach_subject(self.data, user, "c1", "Histoire", self.today))
        self.assertFalse(server._teacher_can_teach_subject(self.data, user, "c1", "Histoire", self.tomorrow))
        self.assertFalse(server._teacher_can_teach_subject(self.data, {"id": "pp", "role": "teacher"}, "c1", "Histoire", self.today))
        self.assertTrue(server._teacher_can_teach_subject(self.data, {"id": "pp", "role": "teacher"}, "c1", "Histoire", self.tomorrow))

    def test_long_term_replacement_suspends_only_the_selected_co_teacher(self):
        data = copy.deepcopy(self.data)
        data["schedule"][0]["endDate"] = "2028-12-31"
        data["teacherAssignments"].append({
            "id": "a3", "scheduleId": "slot1", "classId": "c1",
            "subject": "Mathématiques", "teacherId": "t3",
            "supersedesTeacherId": "t1",
            "startDate": self.yesterday, "endDate": self.tomorrow,
            "type": "replacement",
        })
        self.assertFalse(server._teacher_can_teach_subject(data, {"id": "t1"}, "c1", "Mathématiques", self.today))
        self.assertTrue(server._teacher_can_teach_subject(data, {"id": "t2"}, "c1", "Mathématiques", self.today))
        self.assertTrue(server._teacher_can_teach_subject(data, {"id": "t3"}, "c1", "Mathématiques", self.today))
        self.assertTrue(server._teacher_can_teach_subject(data, {"id": "t1"}, "c1", "Mathématiques", "2028-01-01"))

    def test_expired_replacement_does_not_keep_access(self):
        user = {"id": "t5", "role": "teacher"}
        self.assertFalse(server._teacher_can_teach_subject(self.data, user, "c1", "Sciences", self.today))
        self.assertNotIn("c1", server._teacher_class_ids(self.data, user))

    def test_timetable_assignment_grants_class_projection_without_profile_duplication(self):
        view = server._teacher_visible_data(self.data, {"id": "t3", "role": "teacher"})
        self.assertEqual([x["id"] for x in view["classes"]], ["c1"])
        self.assertEqual([x["id"] for x in view["students"]], ["s1"])
        self.assertTrue(any(x["id"] == "a1" for x in view["teacherAssignments"]))

    def test_teacher_cannot_self_assign_or_assign_a_substitute(self):
        data = copy.deepcopy(self.data)
        data["classes"][0]["teacherIds"] = ["t1"]
        data["schedule"][0]["teacherId"] = "t2"
        data["schedule"][0]["teacherIds"] = []
        user = {"id": "t1", "role": "teacher"}
        view = copy.deepcopy(server._teacher_visible_data(data, user))
        view["schedule"][0]["teacherId"] = "t1"
        view["schedule"][0]["teacherIds"] = ["t1"]
        view["schedule"][0].setdefault("overrides", {})[self.tomorrow] = {
            "status": "changed", "replacementTeacherId": "t3"
        }
        view["teacherAssignments"] = [{
            "id": "forged", "scheduleId": "slot1", "classId": "c1",
            "subject": "Sciences", "teacherId": "t1",
            "startDate": self.today, "endDate": self.tomorrow,
            "type": "replacement",
        }]
        merged = server._merge_teacher_data(data, view, user)
        saved = next(x for x in merged["schedule"] if x["id"] == "slot1")
        self.assertEqual(saved["teacherId"], "t2")
        self.assertEqual(saved["teacherIds"], [])
        self.assertNotEqual(saved["overrides"][self.tomorrow].get("replacementTeacherId"), "t3")
        self.assertFalse(any(x.get("id") == "forged" for x in merged.get("teacherAssignments", [])))

    def test_legacy_profile_subject_is_only_a_fallback_without_explicit_assignment(self):
        user = {"id": "t6", "role": "teacher"}
        self.assertTrue(server._teacher_can_teach_subject(self.data, user, "c1", "Legacy subject", self.today))
        self.assertFalse(server._teacher_can_teach_subject(self.data, user, "c1", "Other subject", self.today))


if __name__ == "__main__":
    unittest.main()
