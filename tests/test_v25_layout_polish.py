"""Regression checks for the V25.2 layout polish."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "_all.js").read_text(encoding="utf-8")


class LayoutPolishTests(unittest.TestCase):
    def test_home_focus_card_keeps_blue_gradient(self):
        self.assertIn(".focusCard{background:linear-gradient(135deg,#102a43,#1b4777)", HTML)
        self.assertIn(".focusCard .metric b{color:#fff!important}", HTML)

    def test_settings_cards_have_intentional_placement(self):
        self.assertIn(".settingsGrid>.settingsCard:nth-child(1){grid-column:1;grid-row:1}", HTML)
        self.assertIn(".settingsGrid>.settingsCard:nth-child(2){grid-column:2;grid-row:1 / span 2}", HTML)
        self.assertIn(".settingsGrid>.settingsCard:nth-child(3){grid-column:1;grid-row:2}", HTML)

    def test_activity_and_bulletin_metrics_have_spacing_hooks(self):
        self.assertIn("activityMainGrid", JS)
        self.assertIn("bulletinMetrics", JS)
        self.assertIn(".activityMainGrid{margin-top:18px;gap:18px", HTML)
        self.assertIn(".bulletinMetrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px", HTML)

    def test_settings_layout_overrides_legacy_full_width_and_positions(self):
        self.assertIn('.settingsGrid>.settingsCard{grid-column:auto!important;grid-row:auto!important', HTML)
        self.assertIn('.settingsGrid>.settingsCard:nth-child(5){grid-area:data!important}', HTML)
        self.assertIn('grid-template-areas:"appearance periods version" "rooms periods data"!important', HTML)

    def test_student_search_and_class_filter_have_horizontal_spacing(self):
        self.assertIn('.studentDirectory>.searchRow{display:grid!important', HTML)
        self.assertIn('column-gap:16px!important', HTML)

    def test_bulletin_tabs_are_horizontally_centered_with_optical_offset(self):
        self.assertIn('.bulletinPreparation>.bulletinTabs{display:flex!important;justify-content:center!important', HTML)
        self.assertIn('left:4px;top:-2px', HTML)

    def test_settings_no_longer_advertise_v19_compatibility(self):
        self.assertNotIn('compatible V19.x', JS)

    def test_schedule_uses_available_width(self):
        self.assertIn(".scheduleGrid{width:100%;min-width:0;grid-template-columns:64px minmax(0,1fr)", HTML)
        self.assertIn(".scheduleDays{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));width:100%;min-width:0}", HTML)

    def test_module_headers_share_one_hierarchy(self):
        self.assertIn(".pageContext>.eyebrow{color:var(--mc-blue,var(--blue))!important", HTML)
        self.assertIn(".pageTitleRow{display:flex;flex-direction:column", HTML)
        self.assertIn(".pageTitleRow h1{font-size:22px!important", HTML)


if __name__ == "__main__":
    unittest.main()
