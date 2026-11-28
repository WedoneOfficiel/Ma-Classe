import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import establishment_import as importer
import server


def sample_bundle():
    return {
        "format": "maclasse-establishment",
        "version": 1,
        "establishment": {"name": "Collège des Tilleuls"},
        "classes": [
            {
                "key": "6A", "name": "6e A", "levels": ["6e"],
                "teachers": ["t1"], "principalTeacher": "t1",
                "expectedStudentCount": 2,
                "subjectRequirements": [{"subject": "Français", "hoursPerWeek": 2}],
            },
            {
                "key": "5A", "name": "5e A", "levels": ["5e", "4e"],
                "teachers": ["t1", "t2"], "principalTeacher": "t2",
            },
        ],
        "teachers": [
            {
                "key": "t1", "first": "Élodie", "last": "Martin",
                "subjects": ["Français"], "classes": ["6A", "5A"],
                "unavailable": [{"day": "wednesday", "start": "13:00", "end": "14:00"}],
            },
            {
                "key": "t2", "first": "Marc", "last": "Durand",
                "subjects": ["Mathématiques"], "classes": ["5A"],
            },
        ],
        "students": [
            {"key": "s1", "first": "Alice", "last": "Test", "class": "6A"},
            {"key": "s2", "first": "Bilal", "last": "Test", "class": "6A"},
            {"key": "s3", "first": "Chloé", "last": "Test", "class": "5A", "level": "5e"},
        ],
        "rooms": [
            {"key": "R1", "name": "B204", "capacity": 35, "equipment": ["vidéoprojecteur"]},
            {"key": "R2", "name": "Info", "type": "informatique", "capacity": 20, "equipment": ["ordinateurs"]},
        ],
        "schedule": [
            {"key": "L1", "day": "monday", "start": "08:00", "end": "09:00", "subject": "Français", "class": "6A", "teacher": "t1", "room": "R1", "startDate": "2026-09-07"},
            {"key": "L2", "day": "wednesday", "start": "08:00", "end": "09:00", "subject": "Mathématiques", "class": "5A", "teacher": "t2", "room": "R2", "startDate": "2026-09-09"},
            {"key": "L3", "day": "monday", "start": "09:00", "end": "10:00", "subject": "Français", "class": "6A", "teacher": "t1", "room": "R1", "startDate": "2026-09-07"},
        ],
    }


class EstablishmentImportTests(unittest.TestCase):
    def validate(self, bundle=None, existing=None):
        return importer.validate_bundle(bundle or sample_bundle(), existing)

    def test_distributed_example_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        example_path = root / "docs" / "templates" / "establishment-import.v1.example.json"
        with example_path.open(encoding="utf-8") as handle:
            bundle = json.load(handle)
        result = importer.validate_bundle(bundle)
        self.assertEqual(result["errors"], [])

    def test_valid_bundle_builds_local_accounts_and_all_school_records(self):
        bundle = sample_bundle()
        result = importer.validate_bundle(bundle)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["summary"], {
            "establishment": "Collège des Tilleuls",
            "classes": 2, "students": 3, "teachers": 2, "teacherAccounts": 2,
            "rooms": 2, "scheduleSlots": 3,
        })
        counter = {"n": 0}
        def token_factory(size):
            counter["n"] += 1
            return f"generated-{counter['n']}"
        original = {"users": [{"id": "admin", "role": "admin", "username": "direction"}]}
        data, credentials, summary = importer.build_data(
            bundle, original,
            password_hasher=lambda value: "HASH:" + value,
            token_factory=token_factory,
        )
        self.assertEqual(len(data["classes"]), 2)
        self.assertEqual(len(data["students"]), 3)
        self.assertEqual(len(data["settings"]["rooms"]), 2)
        self.assertEqual(len(data["schedule"]), 3)
        self.assertEqual(len(credentials), 2)
        self.assertTrue(all(u["mustChangePassword"] for u in data["users"] if u["role"] == "teacher"))
        self.assertTrue(all(u["passwordHash"].startswith("HASH:") for u in data["users"] if u["role"] == "teacher"))
        self.assertEqual(len(data["teachers"]), 2)
        multi = next(x for x in data["classes"] if x["name"] == "5e A")
        self.assertEqual(multi["groups"], ["5e A/5e", "5e A/4e"])
        student = next(x for x in data["students"] if x["first"] == "Chloé")
        self.assertEqual((student["level"], student["group"]), ("5e", "5e A/5e"))
        teacher = next(x for x in data["users"] if x["role"] == "teacher" and x["first"] == "Élodie")
        self.assertEqual(teacher["scheduleUnavailable"], [{"day": 2, "startMinutes": 780, "endMinutes": 840}])
        room = next(x for x in data["settings"]["rooms"] if x["name"] == "B204")
        self.assertEqual(room["type"], "classroom")
        slot = next(x for x in data["schedule"] if x["subject"] == "Français")
        self.assertEqual(slot["roomId"], room["id"])
        self.assertTrue(slot["sharedSlotId"])
        self.assertEqual(summary["teachers"], 2)
        self.assertEqual(summary["teacherAccounts"], 2)
        self.assertTrue(all(profile["id"] in {account["id"] for account in data["users"] if account.get("role") == "teacher"} for profile in data["teachers"]))
        self.assertEqual(original, {"users": [{"id": "admin", "role": "admin", "username": "direction"}]})

    def test_teacher_profiles_are_preserved_without_login_accounts(self):
        bundle = sample_bundle()
        bundle["createTeacherAccounts"] = False
        bundle["createStudentProfiles"] = False
        bundle["students"] = []

        result = importer.validate_bundle(bundle)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["summary"]["students"], 0)
        self.assertEqual(result["summary"]["teachers"], 2)
        self.assertEqual(result["summary"]["teacherAccounts"], 0)

        counter = {"n": 0}
        def token_factory(size):
            counter["n"] += 1
            return f"generated-{counter['n']}"

        data, credentials, summary = importer.build_data(
            bundle,
            {"users": [{"id": "admin", "role": "admin", "username": "direction"}]},
            password_hasher=lambda value: "HASH:" + value,
            token_factory=token_factory,
        )
        self.assertEqual(credentials, [])
        self.assertEqual(summary["teachers"], 2)
        self.assertEqual(summary["teacherAccounts"], 0)
        self.assertEqual(len([u for u in data["users"] if u["role"] == "teacher"]), 0)
        self.assertEqual(len(data["teachers"]), 2)
        self.assertEqual(data["students"], [])

        teacher_ids = {teacher["id"] for teacher in data["teachers"]}
        self.assertEqual(
            {ident for classroom in data["classes"] for ident in classroom["teacherIds"]},
            teacher_ids,
        )
        self.assertTrue(all(slot["teacherIds"] for slot in data["schedule"]))
        self.assertTrue(all(set(slot["teacherIds"]).issubset(teacher_ids) for slot in data["schedule"]))
        self.assertTrue(all(teacher["role"] == "teacher" for teacher in data["teachers"]))
        self.assertTrue(all("username" not in teacher and "passwordHash" not in teacher for teacher in data["teachers"]))


    def test_expected_student_count_still_protects_room_capacity_without_student_profiles(self):
        bundle = sample_bundle()
        bundle["createStudentProfiles"] = False
        bundle["students"] = []
        bundle["classes"][0]["expectedStudentCount"] = 40
        errors = "\n".join(importer.validate_bundle(bundle)["errors"])
        self.assertIn("B204", errors)
        self.assertIn("40 élèves", errors)
        self.assertIn("trop petite", errors)

    def test_rejects_non_boolean_profile_creation_options(self):
        bundle = sample_bundle()
        bundle["createTeacherAccounts"] = "non"
        bundle["createStudentProfiles"] = 0
        errors = "\n".join(importer.validate_bundle(bundle)["errors"])
        self.assertIn("createTeacherAccounts doit être un booléen", errors)
        self.assertIn("createStudentProfiles doit être un booléen", errors)

    def test_rejects_bad_format_version_unknown_fields_and_missing_root_fields(self):
        self.assertTrue(importer.validate_bundle({"format": "wrong", "version": 99})["errors"])
        bundle = sample_bundle()
        bundle["students"][0]["unexpected"] = True
        self.assertTrue(any("propriété inconnue" in x for x in self.validate(bundle)["errors"]))
        bundle = sample_bundle()
        bundle["version"] = True
        self.assertTrue(any("Version de format non prise en charge" in x for x in self.validate(bundle)["errors"]))
        bundle = sample_bundle()
        del bundle["rooms"]
        self.assertTrue(any("Propriété obligatoire manquante : rooms" in x for x in self.validate(bundle)["errors"]))

    def test_rejects_duplicate_keys_and_unresolved_references(self):
        bundle = sample_bundle()
        bundle["students"][0]["class"] = "missing"
        bundle["classes"].append(dict(bundle["classes"][0]))
        errors = "\n".join(self.validate(bundle)["errors"])
        self.assertIn("utilisée plusieurs fois", errors)
        self.assertIn("introuvable", errors)

    def test_rejects_duplicate_class_room_names_and_existing_records(self):
        bundle = sample_bundle()
        bundle["classes"].append(dict(bundle["classes"][0], key="6A-copy"))
        bundle["rooms"].append(dict(bundle["rooms"][0], key="R1-copy"))
        errors = "\n".join(self.validate(bundle)["errors"])
        self.assertIn("nom de classe", errors)
        self.assertIn("nom de salle", errors)
        existing = {
            "classes": [{"id": "c1", "name": "6e A"}],
            "settings": {"rooms": [{"id": "r1", "name": "B204"}]},
        }
        errors = "\n".join(self.validate(sample_bundle(), existing)["errors"])
        self.assertIn("existe déjà", errors)

    def test_rejects_missing_levels_for_multi_level_classes(self):
        bundle = sample_bundle()
        bundle["students"][2].pop("level")
        self.assertTrue(any("le niveau doit être indiqué" in x for x in self.validate(bundle)["errors"]))

    def test_rejects_invalid_student_count_and_group(self):
        bundle = sample_bundle()
        bundle["classes"][0]["expectedStudentCount"] = 4
        bundle["students"][0]["group"] = "Groupe qui n'existe pas"
        errors = "\n".join(self.validate(bundle)["errors"])
        self.assertIn("élèves attendus", errors)
        self.assertIn("groupe", errors)

    def test_rejects_teacher_subject_and_class_assignment_mismatches(self):
        bundle = sample_bundle()
        bundle["schedule"][0]["subject"] = "Histoire"
        self.assertTrue(any("n'a pas 'Histoire'" in x for x in self.validate(bundle)["errors"]))
        bundle = sample_bundle()
        bundle["schedule"][0]["teacher"] = "t2"
        self.assertTrue(any("n'est pas affecté" in x for x in self.validate(bundle)["errors"]))

    def test_rejects_invalid_room_capacity_and_missing_equipment(self):
        bundle = sample_bundle()
        bundle["rooms"][0]["capacity"] = 1
        bundle["schedule"][0]["equipment"] = ["ordinateurs"]
        errors = "\n".join(self.validate(bundle)["errors"])
        self.assertIn("trop petite", errors)
        self.assertIn("ne possède pas", errors)

    def test_room_capacity_counts_all_classes_in_a_shared_lesson(self):
        bundle = sample_bundle()
        bundle["teachers"][0]["subjects"].append("Arts")
        bundle["rooms"][0]["capacity"] = 2
        bundle["schedule"].append({
            "key": "SHARED-CLASSES",
            "day": "thursday", "start": "08:00", "end": "09:00",
            "subject": "Arts", "classes": ["6A", "5A"],
            "teacher": "t1", "room": "R1",
            "startDate": "2026-09-10",
        })
        errors = "\\n".join(self.validate(bundle)["errors"])
        self.assertIn("3 élèves", errors)
        self.assertIn("trop petite", errors)

    def test_room_capacity_counts_implicit_multi_level_student_groups(self):
        bundle = sample_bundle()
        # build_data() assigns students without an explicit group to
        # "<class name>/<level>" for multi-level classes.
        bundle["students"].append({
            "key": "s4", "first": "Dina", "last": "Test",
            "class": "5A", "level": "5e",
        })
        bundle["rooms"][1]["capacity"] = 1
        bundle["schedule"].append({
            "key": "MULTI-LEVEL-GROUP",
            "day": "friday", "start": "10:00", "end": "11:00",
            "subject": "Mathématiques", "class": "5A",
            "group": "5e A/5e", "teacher": "t2", "room": "R2",
            "startDate": "2026-09-11",
        })
        errors = "\\n".join(self.validate(bundle)["errors"])
        self.assertIn("Info", errors)
        self.assertIn("2 élèves", errors)
        self.assertIn("trop petite", errors)

    def test_rejects_room_and_teacher_unavailability(self):
        bundle = sample_bundle()
        bundle["rooms"][0]["unavailable"] = [{"day": "monday", "start": "08:00", "end": "10:00"}]
        self.assertTrue(any("est indisponible sur ce créneau" in x for x in self.validate(bundle)["errors"]))
        bundle = sample_bundle()
        bundle["teachers"][0]["unavailable"] = [{"day": "monday", "start": "08:00", "end": "09:00"}]
        self.assertTrue(any("est indisponible à cet horaire" in x for x in self.validate(bundle)["errors"]))

    def test_blocks_class_teacher_and_room_overlaps_but_allows_separate_groups(self):
        bundle = sample_bundle()
        bundle["schedule"].append({
            "key": "OVERLAP", "day": "monday", "start": "08:30", "end": "09:30",
            "subject": "Mathématiques", "class": "6A", "teacher": "t2", "room": "R1",
            "startDate": "2026-09-07",
        })
        self.assertTrue(any("Conflit entre les créneaux" in x for x in self.validate(bundle)["errors"]))
        bundle = sample_bundle()
        classroom = bundle["classes"][1]
        classroom["groups"] = ["Groupe A", "Groupe B"]
        bundle["schedule"] = [
            {"key": "A", "day": "monday", "start": "08:00", "end": "09:00", "subject": "Français", "class": "5A", "group": "Groupe A", "teacher": "t1", "room": "R1", "startDate": "2026-09-07"},
            {"key": "B", "day": "monday", "start": "08:00", "end": "09:00", "subject": "Mathématiques", "class": "5A", "group": "Groupe B", "teacher": "t2", "room": "R2", "startDate": "2026-09-07"},
        ]
        self.assertFalse(any("Conflit entre les créneaux" in x for x in self.validate(bundle)["errors"]))
        bundle["schedule"][1]["teacher"] = "t1"
        self.assertTrue(any("professeur" in x for x in self.validate(bundle)["errors"]))
        bundle["schedule"][1]["teacher"] = "t2"
        bundle["schedule"][1]["room"] = "R1"
        self.assertTrue(any("salle" in x for x in self.validate(bundle)["errors"]))

    def test_detects_alternating_recurrence_conflicts_and_exceptions(self):
        bundle = sample_bundle()
        first = dict(bundle["schedule"][0], recurrence="biweekly")
        second = dict(first, key="ALT", start="08:30", end="09:30", startDate="2026-09-14")
        bundle["schedule"] = [first, second]
        self.assertFalse(any("Conflit entre les créneaux" in x for x in self.validate(bundle)["errors"]))
        second["startDate"] = "2026-09-21"
        second["endDate"] = "2026-09-21"
        self.assertTrue(any("Conflit entre les créneaux" in x for x in self.validate(bundle)["errors"]))
        second["exceptions"] = ["2026-09-21"]
        self.assertFalse(any("Conflit entre les créneaux" in x for x in self.validate(bundle)["errors"]))

    def test_weekly_hours_are_validated_per_group_including_common_lessons(self):
        bundle = sample_bundle()
        classroom = bundle["classes"][0]
        classroom["groups"] = ["Groupe A", "Groupe B"]
        classroom["teachers"] = ["t1", "t3"]
        classroom["subjectRequirements"] = [{"subject": "Français", "hoursPerWeek": 2, "group": "Groupe A"}]
        bundle["students"][0]["group"] = "Groupe A"
        bundle["students"][1]["group"] = "Groupe B"
        bundle["teachers"].append({"key": "t3", "first": "Lina", "last": "Bernard", "subjects": ["Français"], "classes": ["6A"]})
        bundle["schedule"] = [
            {"key": "COMMON", "day": "monday", "start": "08:00", "end": "09:00", "subject": "Français", "class": "6A", "teacher": "t1", "room": "R1", "startDate": "2026-09-07"},
            {"key": "GROUP-A", "day": "monday", "start": "09:00", "end": "10:00", "subject": "Français", "class": "6A", "group": "Groupe A", "teacher": "t3", "room": "R2", "startDate": "2026-09-07"},
            {"key": "GROUP-B", "day": "monday", "start": "09:00", "end": "10:00", "subject": "Français", "class": "6A", "group": "Groupe B", "teacher": "t1", "room": "R1", "startDate": "2026-09-07"},
        ]
        errors = self.validate(bundle)["errors"]
        self.assertFalse(any("heures/semaine" in x for x in errors))

    def test_gap_quality_is_calculated_per_group_and_teacher(self):
        bundle = sample_bundle()
        bundle["classes"][1]["groups"] = ["Groupe A", "Groupe B"]
        bundle["teachers"].append({"key": "t3", "first": "Lina", "last": "Bernard", "subjects": ["Français"], "classes": ["5A"]})
        bundle["classes"][1]["teachers"] = ["t1", "t3"]
        bundle["schedule"] = [
            {"key": "A", "day": "monday", "start": "08:00", "end": "09:00", "subject": "Français", "class": "5A", "group": "Groupe A", "teacher": "t1", "room": "R1", "startDate": "2026-09-07"},
            {"key": "B", "day": "monday", "start": "10:00", "end": "11:00", "subject": "Français", "class": "5A", "group": "Groupe B", "teacher": "t3", "room": "R2", "startDate": "2026-09-07"},
        ]
        result = self.validate(bundle)
        self.assertEqual(result["quality"]["classDaysWithGaps"], 0)
        self.assertEqual(result["quality"]["weeklyGapHours"], 0)
        self.assertIn("teacherWeeklyGapHours", result["quality"])

    def test_subject_hours_reject_invalid_types_and_values(self):
        for bad in (True, "2", 0, 41):
            bundle = sample_bundle()
            bundle["classes"][0]["subjectRequirements"][0]["hoursPerWeek"] = bad
            self.assertTrue(self.validate(bundle)["errors"], f"hoursPerWeek={bad!r} must be rejected")

    def test_protects_existing_usernames_and_generates_unique_local_usernames(self):
        existing = {"users": [{"id": "existing", "role": "teacher", "username": "elodie.martin"}]}
        bundle = sample_bundle()
        bundle["teachers"][0]["username"] = "elodie.martin"
        self.assertTrue(any("Identifiant professeur" in x for x in self.validate(bundle, existing)["errors"]))
        bundle = sample_bundle()
        bundle["teachers"][1]["first"] = "Élodie"
        bundle["teachers"][1]["last"] = "Martin"
        result = self.validate(bundle)
        self.assertFalse(result["errors"])
        bundle_without_accounts = sample_bundle()
        bundle_without_accounts["createTeacherAccounts"] = False
        bundle_without_accounts["teachers"][0]["username"] = "elodie.martin"
        no_account_result = self.validate(bundle_without_accounts, existing)
        self.assertFalse(no_account_result["errors"])
        self.assertEqual(no_account_result["summary"]["teacherAccounts"], 0)
        counter = {"n": 0}
        def tokens(size):
            counter["n"] += 1
            return f"token-{counter['n']}"
        data, credentials, _ = importer.build_data(bundle, {}, password_hasher=lambda p: p, token_factory=tokens)
        names = [x["username"] for x in credentials]
        self.assertEqual(len(set(names)), len(names))

    def test_import_database_loader_rejects_non_object_root_without_mutation(self):
        for raw in ("[]", '"database"', "null", "{invalid json"):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as temp:
                database = Path(temp) / "maclasse.json"
                database.write_text(raw, encoding="utf-8")
                with patch.object(server, "DATA_FILE", str(database)):
                    with self.assertRaisesRegex(ValueError, "base de données existante|racine"):
                        server._load_database_for_establishment_import()
                self.assertEqual(database.read_text(encoding="utf-8"), raw)

    def test_import_database_loader_rejects_malformed_collections_before_preview(self):
        malformed = [
            {"classes": {"legacy": {"name": "Classe conservée"}}},
            {"students": "not-a-list"},
            {"teachers": {"legacy": {"id": "teacher-without-account"}}},
            {"settings": ["paramètres historiques"]},
            {"settings": {"rooms": {"legacy": {"name": "Salle conservée"}}}},
        ]
        for saved in malformed:
            with self.subTest(saved=saved), tempfile.TemporaryDirectory() as temp:
                database = Path(temp) / "maclasse.json"
                raw = json.dumps(saved, ensure_ascii=False)
                database.write_text(raw, encoding="utf-8")
                with patch.object(server, "DATA_FILE", str(database)):
                    with self.assertRaisesRegex(ValueError, "Données existantes incompatibles"):
                        server._load_database_for_establishment_import()
                self.assertEqual(database.read_text(encoding="utf-8"), raw)

    def test_import_database_loader_accepts_absent_database_as_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "missing.json"
            with patch.object(server, "DATA_FILE", str(database)):
                self.assertEqual(server._load_database_for_establishment_import(), {})

    def test_build_data_rejects_non_object_existing_database(self):
        for malformed in ([], "not-an-object", 42, False):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(ValueError, "racine de la base"):
                    importer.build_data(
                        sample_bundle(), malformed,
                        password_hasher=lambda value: "HASH:" + value,
                        token_factory=lambda size: "generated-token",
                    )

    def test_refuses_to_replace_malformed_existing_data_during_import(self):
        malformed_records = [
            {"classes": {"legacy-record": {"name": "Classe conservée"}}},
            {"settings": ["paramètre historique"]},
            {"settings": {"rooms": {"legacy-room": {"name": "Salle conservée"}}}},
            {"users": {"legacy-user": {"username": "ancien.compte"}}},
        ]
        for existing in malformed_records:
            with self.subTest(existing=existing):
                before = copy.deepcopy(existing)
                with self.assertRaisesRegex(ValueError, "Données existantes incompatibles"):
                    importer.build_data(
                        sample_bundle(), existing,
                        password_hasher=lambda value: "HASH:" + value,
                        token_factory=lambda size: "generated-token",
                    )
                self.assertEqual(existing, before)

    def test_never_mutates_input_and_strips_internal_normalized_data(self):
        bundle = sample_bundle()
        before = copy.deepcopy(bundle)
        validation = importer.validate_bundle(bundle)
        self.assertEqual(bundle, before)
        public = importer.public_validation(validation)
        self.assertNotIn("_normalized", public)
        self.assertTrue(public["valid"])

    def test_curriculum_domain_without_fixed_hourly_allocation_is_preserved(self):
        bundle = sample_bundle()
        bundle["classes"][0]["subjectRequirements"] = [{
            "subject": "Développement et structuration du langage oral et écrit",
            "hoursPerWeek": None,
            "group": "",
            "details": "Oral, vocabulaire, phonologie, lecture et entrée dans l'écrit.",
            "hoursBasis": "not_allocated",
            "reference": "BO n° 19 du 7 mai 2026",
        }, {
            "subject": "Ensemble des enseignements du cycle 1",
            "hoursPerWeek": 24,
            "group": "",
            "details": "24 heures hebdomadaires pour l'ensemble du cycle.",
            "hoursBasis": "global_cycle",
            "reference": "Code de l'éducation ; Éduscol cycle 1",
        }]
        validation = importer.validate_bundle(bundle)
        self.assertEqual(validation["errors"], [])
        data, _, _ = importer.build_data(
            bundle,
            {},
            password_hasher=lambda value: "HASH:" + value,
            token_factory=lambda size: "generated-token",
        )
        requirement = data["classes"][0]["subjectRequirements"][0]
        self.assertIsNone(requirement["hoursPerWeek"])
        self.assertEqual(requirement["hoursBasis"], "not_allocated")
        self.assertIn("vocabulaire", requirement["details"])
        self.assertEqual(requirement["reference"], "BO n° 19 du 7 mai 2026")

    def test_null_subject_hours_require_explicit_non_allocated_basis(self):
        bundle = sample_bundle()
        bundle["classes"][0]["subjectRequirements"] = [{
            "subject": "Français",
            "hoursPerWeek": None,
            "details": "Lecture et écriture",
        }]
        errors = "\\n".join(importer.validate_bundle(bundle)["errors"])
        self.assertIn("hoursBasis='not_allocated'", errors)

    def test_empty_schedule_and_students_are_warnings_not_fatal(self):
        bundle = sample_bundle()
        bundle["students"] = []
        bundle["schedule"] = []
        bundle["classes"][0].pop("expectedStudentCount", None)
        bundle["classes"][0]["subjectRequirements"] = []
        result = self.validate(bundle)
        self.assertFalse(result["errors"])
        self.assertTrue(result["warnings"])


if __name__ == "__main__":
    unittest.main()
