"""Non-regression tests for the explicit appearance selector."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ThemeControlsTests(unittest.TestCase):
    def test_three_theme_choices_are_available(self):
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        self.assertIn('value="system"', js)
        self.assertIn('value="light"', js)
        self.assertIn('value="dark"', js)
        self.assertIn('id="appearanceTheme"', js)

    def test_theme_preference_is_applied_and_persisted_locally(self):
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        self.assertIn("localStorage.getItem(MC_THEME_KEY)", js)
        self.assertIn("localStorage.setItem(MC_THEME_KEY,value)", js)
        self.assertIn("applyAppearanceTheme()", js)

    def test_explicit_theme_styles_exist(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"]', html)
        self.assertIn('html[data-mc-theme="light"]', html)


    def test_system_dark_mode_has_complete_cross_platform_surface_rules(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="system"]{', html)
        self.assertIn('color-scheme:dark;', html)
        self.assertIn('html[data-mc-theme="system"] .mc-select-trigger', html)
        self.assertIn('html[data-mc-theme="system"] .lessonModeBlue.active', html)

    def test_dark_theme_covers_document_profile_and_assessment_modules(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .docRoot', html)
        self.assertIn('html[data-mc-theme="dark"] .finderItem', html)
        self.assertIn('html[data-mc-theme="dark"] .v206CriterionRow', html)

    def test_dark_theme_covers_secondary_navigation_and_document_controls(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in ('.nav button.active', '.gradebookMatrix th:first-child',
                         '.miniKpi', '.mc-select-menu', '.folderBox'):
            self.assertIn('html[data-mc-theme="dark"] ' + selector, html)
        self.assertIn('html[data-mc-theme="system"] .gradebookMatrix th:first-child', html)

    def test_dark_theme_hover_and_focus_states_never_flash_light(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .eventEdit:hover', html)
        self.assertIn('html[data-mc-theme="dark"] .input:focus', html)
        self.assertIn('html[data-mc-theme="system"] .searchResult:hover', html)

    def test_dark_theme_native_checkboxes_and_assessment_levels(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] input[type="checkbox"]', html)
        self.assertIn('html[data-mc-theme="dark"] input[type="radio"]:checked', html)
        self.assertIn('html[data-mc-theme="dark"] .v205Level.lv1', html)

    def test_dark_theme_custom_select_and_navigation_states(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .mcSelectMenu', html)
        self.assertIn('html[data-mc-theme="dark"] .mcSelectOption.selected', html)
        self.assertIn('html[data-mc-theme="dark"] .btn.dark', html)
        self.assertIn('html[data-mc-theme="system"] .mcSelectMenu', html)

    def test_dark_theme_calendar_attendance_and_messaging_states(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in ('.statusBtn.on.present', '.eventEdit', '.dayBtn .count',
                         '.v15Bubble', '.v15Thread.active'):
            self.assertIn('html[data-mc-theme="dark"] ' + selector, html)
        self.assertIn('html[data-mc-theme="system"] .v15Bubble', html)

    def test_dark_theme_student_space_mail_and_translucent_surfaces(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in ('.v14WeekDay', '.mailList', '.mailReply',
                         '.v12Workspace', '.v12StatStrip .v12Stat'):
            self.assertIn('html[data-mc-theme="dark"] ' + selector, html)
        self.assertIn('html[data-mc-theme="system"] .mailList', html)

    def test_theme_layer_covers_reported_and_interactive_components(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .statMini', html)
        self.assertIn('html[data-mc-theme="light"] .statMini', html)
        self.assertIn('html[data-mc-theme="dark"] .lessonModeGreen.active', html)
        self.assertIn('--mc-card-padding', html)

if __name__ == "__main__":
    unittest.main()
