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


    def test_repeated_messaging_rules_are_consolidated(self):
        self.assertEqual(HTML.count(".v15ThreadDot{flex:0 0 30px}"), 1)
        self.assertEqual(HTML.count(".v15ChatMessages{overflow:auto}"), 1)
        self.assertEqual(HTML.count(".v15ChatHead .actions{display:flex;gap:6px}"), 1)

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

    def test_legacy_today_route_uses_role_aware_activity_renderer(self):
        self.assertIn("today:authUser?.role==='student'?studentActivityCenter:activity", JS)
        self.assertIn("if(p==='today'||p==='notifications')p='activity'", JS)
        self.assertNotIn("today:today,activity:", JS)

    def test_dashboard_uses_natural_french_count_labels(self):
        start = JS.index("function dashboard(){")
        end = JS.index("\nfunction ", start + 20)
        dashboard = JS[start:end]
        self.assertIn("slotsLabel=", dashboard)
        self.assertIn("workLabel=", dashboard)
        self.assertNotIn("créneau(x)", dashboard)
        self.assertNotIn("travail(aux)", dashboard)
        self.assertIn("</b> <small class=\"muted\">", dashboard)

    def test_appearance_is_a_visual_three_way_choice(self):
        self.assertIn('class="themeChoices"', JS)
        for theme in ("light", "dark", "system"):
            self.assertIn(f"setAppearanceTheme('{theme}')", JS)
        self.assertIn(".themePreviewSystem{", HTML)


    def test_dark_cards_do_not_keep_the_light_glass_highlight(self):
        self.assertIn('html[data-mc-theme="dark"] .card::before,', HTML)
        self.assertIn('html[data-mc-theme="dark"] .bulletin::before{', HTML)
        self.assertIn('background:none!important;', HTML)
        self.assertIn('opacity:0!important;', HTML)

    def test_visible_screens_use_french_singular_and_plural_counts(self):
        self.assertIn("function countLabel(value,singular,plural)", JS)
        start = JS.index("function studentLessons(){")
        end = JS.index("\nfunction ", start + 20)
        student_lessons = JS[start:end]
        self.assertIn("countLabel(occ(d).length,'créneau','créneaux')", student_lessons)
        self.assertIn("countLabel(items.filter(l=>l.date===lessonDay).length,'séance','séances')", student_lessons)
        self.assertNotIn("créneau(x)", student_lessons)
        self.assertNotIn("séance(s)", student_lessons)

        start = JS.index("function lessons(){")
        end = JS.index("\nfunction ", start + 20)
        teacher_lessons = JS[start:end]
        self.assertIn("countLabel(occ.length,'créneau','créneaux')", teacher_lessons)
        self.assertNotIn("créneau(x)", teacher_lessons)

        start = JS.index("function settings(){")
        end = JS.index("\nasync function restoreZipBackup", start + 20)
        settings = JS[start:end]
        self.assertIn("countLabel(db.students.length,'élève','élèves')", settings)
        self.assertIn("countLabel((db.auditLog||[]).length,'événement','événements')", settings)
        self.assertNotIn("événement(s)", settings)

    def test_french_counts_are_consistent_in_product_modules(self):
        for fragment in (
            "countLabel(cs.length,'classe','classes')",
            "countLabel(taught.length,'classe','classes')",
            "countLabel(pp.length,'classe','classes')",
            "countLabel(stats.classes||0,'classe','classes')",
            "countLabel(stats.students||0,'élève','élèves')",
            "countLabel(stats.files||0,'fichier','fichiers')",
            "countLabel(ok,'fichier','fichiers')",
            "countLabel(items.length,'fichier','fichiers')",
            "countLabel(w.files.length+w.studentFiles.length,'fichier','fichiers')",
            "countLabel(sub.works.length,'travail','travaux')",
            "countLabel(c.subjects.length,'matière','matières')",
            "countLabel(missing.length,'travail','travaux')",
            "countLabel(low.length,'élève','élèves')",
            "countLabel(a.rows.filter(r=>r.status==='absent').length,'absence','absences')",
        ):
            self.assertIn(fragment, JS)

    def test_french_date_headings_keep_month_names_lowercase(self):
        self.assertIn("function formatFrenchDate(date,options)", JS)
        self.assertIn("formatFrenchDate(d,{weekday:'long',day:'numeric',month:'long',year:'numeric'})", JS)
        self.assertIn("formatFrenchDate(sel,{weekday:'long',day:'numeric',month:'long',year:'numeric'})", JS)
        self.assertIn(".scheduleCurrentRange strong,", HTML)
        self.assertIn(".scheduleMonthAgendaDay b{", HTML)
        self.assertIn("text-transform:none!important;", HTML)

    def test_teacher_and_student_lesson_headings_are_consistent(self):
        self.assertIn("shell('Cahier de cours','Séances & leçons'", JS)
        start = JS.index("function studentLessons(){")
        end = JS.index("\nfunction ", start + 20)
        self.assertIn("Séances & leçons", JS[start:end])

    def test_student_cloud_is_reachable_from_the_sidebar(self):
        start = JS.index("function nav(){")
        end = JS.index("\nfunction v12AttentionCount", start + 10)
        student_nav = JS[start:end]
        self.assertIn("['Ressources',['studentDocuments']]", student_nav)
        self.assertIn("studentDocuments:['☁','Cloud']", student_nav)

    def test_mobile_navigation_and_main_content_use_full_width(self):
        self.assertIn("@media(max-width:800px){", HTML)
        self.assertIn(".app{display:block!important;min-height:100vh}", HTML)
        self.assertIn("body.sidebar-collapsed .side{", HTML)
        self.assertIn("width:100%!important;", HTML)
        self.assertIn(".navSection,", HTML)
        self.assertIn("display:contents!important;", HTML)
        self.assertIn(".nav{", HTML)
        self.assertIn("overflow-x:auto!important;", HTML)
        self.assertIn("body.sidebar-collapsed .main{", HTML)
        self.assertIn("margin:0!important;", HTML)

    def test_dark_timetable_grid_overrides_the_light_repeating_surface(self):
        self.assertIn('html[data-mc-theme="dark"] .daycol{background:repeating-linear-gradient(to bottom,#29292c 0,#29292c 71px,#3c3c40 72px)!important}', HTML)
        self.assertIn('html[data-mc-theme="dark"] .scheduleCalendarSurface{', HTML)
        self.assertIn('background:var(--paper)!important;', HTML)

    def test_dark_theme_does_not_add_extra_background_effects(self):
        self.assertIn('html[data-mc-theme="dark"] body{background:var(--bg)!important}', HTML)
        self.assertIn('html[data-mc-theme="dark"] .card,html[data-mc-theme="dark"] .bulletin{background:var(--paper)!important', HTML)


if __name__ == "__main__":
    unittest.main()
