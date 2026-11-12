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


    def test_theme_layer_covers_reported_and_interactive_components(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .statMini', html)
        self.assertIn('html[data-mc-theme="light"] .statMini', html)
        self.assertIn('html[data-mc-theme="dark"] .lessonModeGreen.active', html)
        self.assertIn('--mc-card-padding', html)

if __name__ == "__main__":
    unittest.main()
