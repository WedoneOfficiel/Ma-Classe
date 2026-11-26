import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import establishment_import as importer


def lesson(key, *, classes=(), teachers=(), room="", group="", day=0, start=480, end=540):
    return {
        "key": key,
        "classes": list(classes),
        "teachers": list(teachers),
        "room": room,
        "group": group,
        "day": day,
        "startMinutes": start,
        "endMinutes": end,
    }


class EstablishmentImportScalabilityTests(unittest.TestCase):
    def test_only_shared_resources_produce_candidate_pairs(self):
        lessons = [
            lesson("a", classes=("6A",), teachers=("t1",), room="R1", group="A", start=480, end=540),
            lesson("b", classes=("6A",), teachers=("t2",), room="R2", group="B", start=480, end=540),
            lesson("c", classes=("6A",), teachers=("t3",), room="R3", start=510, end=570),
            lesson("d", classes=("6B",), teachers=("t1",), room="R4", start=490, end=530),
            lesson("e", classes=("6C",), teachers=("t4",), room="R1", start=500, end=530),
            lesson("f", classes=("6D",), teachers=("t5",), room="R5", day=1, start=500, end=530),
        ]

        pairs = list(importer._iter_resource_overlap_pairs(lessons))

        self.assertEqual(
            {tuple(pair) for pair in pairs},
            {(0, 2), (1, 2), (0, 3), (0, 4)},
        )
        self.assertEqual(len(pairs), len({tuple(pair) for pair in pairs}))

    def test_separate_groups_do_not_conflict_without_shared_teacher_or_room(self):
        lessons = [
            lesson("group-a", classes=("6A",), teachers=("t1",), room="R1", group="A"),
            lesson("group-b", classes=("6A",), teachers=("t2",), room="R2", group="B"),
        ]
        self.assertEqual(list(importer._iter_resource_overlap_pairs(lessons)), [])

    def test_many_parallel_groups_of_one_class_do_not_form_cross_group_pairs(self):
        count = 5000
        lessons = [
            lesson(
                f"group-slot-{index}",
                classes=("6A",),
                teachers=(f"teacher-{index}",),
                room=f"room-{index}",
                group=f"group-{index}",
            )
            for index in range(count)
        ]

        # Les groupes distincts d'une même classe peuvent travailler en parallèle.
        # Le validateur ne doit pas comparer toutes les paires entre ces groupes.
        self.assertEqual(list(importer._iter_resource_overlap_pairs(lessons)), [])

    def test_many_parallel_lessons_with_distinct_resources_do_not_form_cartesian_pairs(self):
        count = 5000
        lessons = [
            lesson(
                f"slot-{index}",
                classes=(f"class-{index}",),
                teachers=(f"teacher-{index}",),
                room=f"room-{index}",
            )
            for index in range(count)
        ]

        # 5,000 simultaneous lessons would produce 12,497,500 pairs in a
        # global all-against-all scan, but no resource-indexed pair exists.
        self.assertEqual(list(importer._iter_resource_overlap_pairs(lessons)), [])


if __name__ == "__main__":
    unittest.main()
