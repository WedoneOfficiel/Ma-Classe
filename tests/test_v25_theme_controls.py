"""Non-regression tests for the explicit appearance selector."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ThemeControlsTests(unittest.TestCase):
    def test_three_theme_choices_are_available(self):
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        self.assertIn("setAppearanceTheme('system')", js)
        self.assertIn("setAppearanceTheme('light')", js)
        self.assertIn("setAppearanceTheme('dark')", js)
        self.assertIn('class="themeChoices"', js)

    def test_theme_preference_is_applied_and_persisted_locally(self):
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        self.assertIn("localStorage.getItem(MC_THEME_KEY)", js)
        self.assertIn("localStorage.setItem(MC_THEME_KEY,value)", js)
        self.assertIn("applyAppearanceTheme()", js)

    def test_appearance_bootstrap_runs_in_head_before_stylesheet(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertLess(html.index('id="mc-appearance-bootstrap"'), html.index('<style id="v218-ui">'))
        self.assertIn("localStorage.getItem('maclasse_appearance_theme')", html)
        self.assertIn("r.dataset.mcThemePreference=v", html)
        self.assertIn("r.dataset.mcTheme=v==='system'&&!dark?'light':v", html)
        self.assertIn("r.dataset.mcTheme=v==='system'&&!dark?'light':v", html)

    def test_appearance_is_applied_before_async_server_boot(self):
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        self.assertIn("applyAppearanceTheme();load();", js)

    def test_theme_application_sets_document_theme_and_native_control_scheme(self):
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        self.assertIn("root.dataset.mcThemePreference=value", js)
        self.assertIn("root.dataset.mcTheme=value==='system'&&!dark?'light':value", js)
        self.assertIn("root.style.colorScheme=value==='system'?(dark?'dark':'light'):value", js)
        self.assertIn("media.addEventListener?.('change',sync)", js)

    def test_explicit_theme_styles_exist(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"]', html)
        self.assertIn('html[data-mc-theme="light"]', html)


    def test_dark_mode_has_complete_cross_platform_surface_rules(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"]{', html)
        self.assertIn('color-scheme:dark;', html)
        self.assertIn('html[data-mc-theme="dark"] .mc-select-trigger', html)
        self.assertIn('html[data-mc-theme="dark"] .lessonModeBlue.active', html)

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
        self.assertIn('html[data-mc-theme="dark"] .gradebookMatrix th:first-child', html)

    def test_dark_theme_hover_and_focus_states_never_flash_light(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .eventEdit:hover', html)
        self.assertIn('html[data-mc-theme="dark"] .input:focus', html)
        self.assertIn('html[data-mc-theme="dark"] .searchResult:hover', html)

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
        self.assertIn('html[data-mc-theme="dark"] .mcSelectMenu', html)

    def test_dark_theme_calendar_attendance_and_messaging_states(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in ('.statusBtn.on.present', '.eventEdit', '.dayBtn .count',
                         '.v15Bubble', '.v15Thread.active'):
            self.assertIn('html[data-mc-theme="dark"] ' + selector, html)
        self.assertIn('html[data-mc-theme="dark"] .v15Bubble', html)

    def test_dark_theme_student_space_mail_and_translucent_surfaces(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in ('.v14WeekDay', '.mailList', '.mailReply',
                         '.v12Workspace', '.v12StatStrip .v12Stat'):
            self.assertIn('html[data-mc-theme="dark"] ' + selector, html)
        self.assertIn('html[data-mc-theme="dark"] .mailList', html)

    def test_dark_theme_overlays_student_hero_and_mail_rows(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in ('.v12CommandPanel', '.v125SearchResults', '.v14StudentHero',
                         '.mailRow.active', '.mailMessageHead', '.mailQuoted'):
            self.assertIn('html[data-mc-theme="dark"] ' + selector, html)
        self.assertIn('html[data-mc-theme="dark"] .v14StudentHero', html)

    def test_legacy_system_dark_media_rules_are_consolidated(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('@media(prefers-color-scheme:dark){:root{', html)
        self.assertNotIn('@media(prefers-color-scheme:dark){html[data-mc-theme="dark"]{', html)
        self.assertIn('html[data-mc-theme="light"]{color-scheme:light}', html)

    def test_explicit_dark_theme_defines_all_shared_surface_tokens(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for token in ('--ui-bg:#171719', '--ui-surface-solid:#2c2c2e',
                      '--glass-bg:rgba(52,52,55,.58)', '--mc-bg:#171719',
                      '--ui-text-3:#98989f'):
            self.assertIn(token, html[html.index('variables de thème explicites'):])

    def test_explicit_dark_theme_uses_dark_focus_and_shadow_tokens(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('--mc-focus-ring:0 0 0 3px rgba(10,132,255,.24)', html)
        self.assertIn('--mc-shadow:0 1px 2px rgba(0,0,0,.24)', html)

    def test_dark_theme_focus_visibility_and_reduced_motion_accessibility(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] button:focus-visible', html)
        self.assertIn('html[data-mc-theme="dark"] button:focus-visible', html)
        self.assertIn('@media(prefers-reduced-motion:reduce)', html)

    def test_reduced_transparency_keeps_toast_text_contrast(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('@media(prefers-reduced-transparency:reduce)', html)
        self.assertIn('.toast{background:#242426!important;color:#fff!important', html)

    def test_explicit_and_automatic_dark_share_one_effective_dark_stylesheet(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('@media(prefers-color-scheme:dark){html[data-mc-theme="dark"]', html)
        self.assertIn('html[data-mc-theme="dark"] .mcSelectTrigger', html)
        self.assertIn('html[data-mc-theme="dark"] .v12Workspace', html)

    def test_automatic_light_inherits_the_explicit_light_appearance(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('@media(prefers-color-scheme:light){html[data-mc-theme="dark"] .side', html)
        self.assertNotIn('@media(prefers-color-scheme:light){html[data-mc-theme="dark"] .focusCard', html)
        self.assertIn('html[data-mc-theme="light"] body', html)


    def test_explicit_light_restores_the_legacy_automatic_light_materials(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        light = html[html.rfind("V25.6 — thème clair"):]
        for selector in (
            'html[data-mc-theme="light"] .side',
            'html[data-mc-theme="light"] .top',
            'html[data-mc-theme="light"] .card',
            'html[data-mc-theme="light"] .btn.primary',
            'html[data-mc-theme="light"] .stat:after',
            'html[data-mc-theme="light"] .focusCard',
            'html[data-mc-theme="light"] .focusCard .muted',
        ):
            self.assertIn(selector, light)
        self.assertIn("rgba(10,40,80,.08)", light)
        self.assertIn("linear-gradient(135deg,#0a5ecb,#0a84ff 58%,#4aa3ff)", light)
        self.assertIn("rgba(10,80,150,.16)", light)

    def test_timetable_uses_a_dedicated_full_width_page_architecture(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        for selector in ('.scheduleControlPanel', '.scheduleDateControls',
                         '.scheduleActionControls', '.scheduleFilters',
                         '.scheduleCalendarSurface', '.scheduleMonthGrid'):
            self.assertIn(selector, html)
        self.assertIn('class="scheduleControlPanel"', js)
        self.assertIn('class="scheduleCalendarSurface"', js)
        self.assertIn('class="scheduleMonthGrid"', js)

    def test_date_and_time_controls_follow_selected_color_scheme(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] input[type="date"]', html)
        self.assertIn('html[data-mc-theme="dark"] input[type="time"]', html)
        self.assertIn('html[data-mc-theme="dark"] input[type="date"]', html)

    def test_dark_theme_overrides_glass_borders_and_focus_tokens(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('--mc-glass-border:rgba(255,255,255,.12)', html)
        self.assertIn('--ui-focus:0 0 0 3px rgba(10,132,255,.24)', html)

    def test_dark_theme_placeholder_contrast(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] input::placeholder', html)
        self.assertIn('html[data-mc-theme="dark"] input::placeholder', html)

    def test_dark_theme_modal_close_control(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .close', html)

    def test_dark_theme_avatar_and_activity_icon_contrast(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .avatar', html)
        self.assertIn('html[data-mc-theme="dark"] .profile360Avatar', html)
        self.assertIn('html[data-mc-theme="dark"] .activityIcon', html)
        self.assertIn(':root{--soft:rgba(118,118,128,.10)}', html)

    def test_legacy_component_tokens_resolve_to_shared_design_tokens(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for alias in ('--text:var(--ui-text)', '--accent:var(--ui-blue)',
                      '--ui-blue2:var(--ui-blue-soft)', '--card:var(--ui-surface)',
                      '--border:var(--ui-line)', '--page-bg:var(--ui-bg)'):
            self.assertIn(alias, html)

    def test_all_css_custom_properties_used_by_the_interface_are_defined(self):
        import re
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        referenced = set(re.findall(r'var\(\s*(--[\w-]+)', html))
        declared = set(re.findall(r'(--[\w-]+)\s*:', html))
        self.assertEqual(referenced - declared, set())

    def test_dynamic_modules_have_complete_theme_token_aliases(self):
        import re
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        declared = set(re.findall(r'(--[\w-]+)\s*:', html))
        referenced = set(re.findall(r'var\(\s*(--[\w-]+)', js))
        self.assertEqual(referenced - declared, set())
        self.assertIn('--surface:var(--ui-surface-solid)', html)
        self.assertIn('--primary:var(--ui-blue)', html)

    def test_dark_primary_actions_use_readable_white_text_backgrounds(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .btn.primary', html)
        self.assertIn('background:#0066cc!important;border-color:#0066cc!important;color:#fff!important', html)
        self.assertIn('html[data-mc-theme="dark"] .btn.primary', html)

    def test_theme_layer_covers_reported_and_interactive_components(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('html[data-mc-theme="dark"] .statMini', html)
        self.assertIn('html[data-mc-theme="light"] .statMini', html)
        self.assertIn('html[data-mc-theme="dark"] .lessonModeGreen.active', html)
        self.assertIn('--mc-card-padding', html)

    def test_timetable_today_and_month_navigation_keep_the_selected_period(self):
        js = (ROOT / "_all.js").read_text(encoding="utf-8")
        schedule = js[js.index("function schedule(){"):js.index("function scheduleWeek", js.index("function schedule(){"))]
        self.assertIn("onclick=\"selectedWeek=scheduleView==='week'?startWeek(new Date()):new Date();render()\"", schedule)
        self.assertIn("function changeMonth(n){selectedWeek=new Date(selectedWeek.getFullYear(),selectedWeek.getMonth()+n,1);render()}", js)


    def test_bulletin_preparation_filters_tabs_and_metrics_have_consistent_spacing(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in (".bulletinPreparation{display:flex", ".bulletinPreparation>.bulletinFilters",
                         ".bulletinPreparation>.bulletinTabs", ".bulletinMetrics{margin-top:14px",
                         ".bulletinMetrics>.card.stat{margin:0"):
            self.assertIn(selector, html)

    def test_settings_cards_use_a_consistent_responsive_grid(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(".settingsGrid{gap:14px!important", html)
        self.assertIn(".settingsGrid>.settingsCard{min-width:0", html)
        self.assertIn(".settingsGrid>.settingsDataCard{grid-column:1/-1!important}", html)

if __name__ == "__main__":
    unittest.main()
