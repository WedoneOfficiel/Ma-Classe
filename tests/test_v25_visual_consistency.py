"""Regression checks for the V25.3 visual consistency pass."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "_all.js").read_text(encoding="utf-8")


class VisualConsistencyTests(unittest.TestCase):
    def test_home_focus_card_keeps_dark_base_and_legacy_light_blue_gradient(self):
        self.assertIn(".focusCard{background:linear-gradient(135deg,#102a43,#1b4777)", HTML)
        self.assertIn('html[data-mc-theme="light"] .focusCard{', HTML)
        self.assertIn("linear-gradient(135deg,#0a5ecb,#0a84ff 58%,#4aa3ff)", HTML)
        self.assertNotIn("#075db8 0%", HTML)


    def test_legacy_stylesheet_has_no_malformed_double_class_selector(self):
        self.assertNotIn("..lessonLayout{", HTML)

    def test_bulletin_filters_and_tabs_have_spacing_hooks(self):
        self.assertIn('class="toolbar bulletinFilters"', JS)
        self.assertIn('class="tabs bulletinTabs"', JS)
        self.assertIn('class="card bulletinPreparation"', JS)
        self.assertIn(".bulletinFilters{", HTML)
        self.assertIn(".bulletinTabs{margin-top:14px", HTML)

    def test_schedule_is_wrapped_and_full_width(self):
        p = JS.index("function schedule(){")
        q = JS.index("\nfunction ", p + 20)
        schedule = JS[p:q]
        self.assertIn('class="schedulePage"', schedule)
        self.assertIn(".schedulePage .scheduleDays{", HTML)
        self.assertIn("grid-template-columns:repeat(7,minmax(0,1fr))", HTML)

    def test_every_module_gets_a_header_fallback(self):
        self.assertIn("const headerMeta={dashboard:", JS)
        self.assertIn("content.includes('class=\"top\"')?content:shell(meta[0],meta[1],meta[2])+content", JS)

    def test_appearance_is_a_visual_three_way_choice(self):
        self.assertIn('class="themeChoices"', JS)
        for theme in ("light", "dark", "system"):
            self.assertIn(f"setAppearanceTheme('{theme}')", JS)
        self.assertIn(".themePreviewSystem{", HTML)

    def test_dark_theme_does_not_add_extra_background_effects(self):
        self.assertIn('html[data-mc-theme="dark"] body{background:var(--bg)!important}', HTML)
        self.assertIn('html[data-mc-theme="dark"] .card,html[data-mc-theme="dark"] .bulletin{background:var(--paper)!important', HTML)


if __name__ == "__main__":
    unittest.main()
