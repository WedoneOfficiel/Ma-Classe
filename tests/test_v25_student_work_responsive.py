from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "_all.js").read_text(encoding="utf-8")


class StudentWorkResponsiveTests(unittest.TestCase):
    def test_mobile_card_layout_is_present(self):
        self.assertIn('<style id="v2512-student-work-responsive">', HTML)
        self.assertIn("@media(max-width:650px)", HTML)
        self.assertIn(".studentWorkTable tbody tr:not(.studentWorkEmpty)", HTML)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))!important", HTML)
        self.assertIn(".studentWorkTable tbody tr:not(.studentWorkEmpty) td::before", HTML)
        self.assertIn("content:attr(data-label)", HTML)

    def test_student_work_table_exposes_mobile_cell_labels(self):
        start = JS.index("function studentWork(){")
        end = JS.index("\nfunction ", start + 20)
        module = JS[start:end]
        self.assertIn('class="table studentWorkTable"', module)
        for label in ("Travail", "Matière", "À rendre", "État", "Action"):
            self.assertIn(f'data-label="{label}"', module)
        self.assertIn('class="studentWorkEmpty"', module)

    def test_desktop_table_and_dedicated_route_are_preserved(self):
        self.assertIn("studentWork:studentWork", JS)
        self.assertNotIn("if(p==='studentWork')p='studentLessons';", JS)
        self.assertIn("function studentWork(){", JS)
        self.assertIn("studentWorkFilter==='overdue'", JS)


if __name__ == "__main__":
    unittest.main()
