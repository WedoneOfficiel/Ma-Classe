#!/usr/bin/env python3
"""Real Firefox regression test for teacher timetable navigation and persistence.

The app is copied into a temporary directory so this test never touches the
checkout's data/ directory or any developer installation.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


SOURCE_ROOT = Path(__file__).resolve().parents[2]



def capture_product_screenshots(page, role: str, modules: list[str], output_dir: Path) -> None:
    """Capture real module states and check layout in light/dark and narrow viewports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    original_viewport = page.viewport_size or {"width": 1280, "height": 720}

    def render_state(module: str, theme: str) -> dict:
        return page.evaluate(
            """({role,module,theme}) => {
              const isStudentState = role === 'student' &&
                ['studentHomework','studentTodo'].includes(module);
              const actualPage = isStudentState ? 'studentLessons' : module;
              if(role === 'student') {
                if(module === 'studentLessons') lessonTab = 'done';
                if(module === 'studentHomework') lessonTab = 'work';
                if(module === 'studentTodo') lessonTab = 'upcoming';
              }
              setAppearanceTheme(theme);
              appSpace=role;
              page=actualPage;
              render();
              const toast=document.getElementById('toast');
              if(toast){toast.classList.remove('show');toast.textContent='';}
              const card=document.querySelector('#main .card');
              const main=document.querySelector('main.main');
              const side=document.querySelector('.side');
              const workRow=actualPage==='studentWork'
                ?main?.querySelector('.studentWorkTable tbody tr:not(.studentWorkEmpty)'):null;
              const workCells=workRow?[...workRow.querySelectorAll(':scope > td')]:[];
              const workButton=workRow?.querySelector('button');
              const studentWorkLayout=workRow?{
                rowDisplay:getComputedStyle(workRow).display,
                columns:getComputedStyle(workRow).gridTemplateColumns.split(' ').length,
                cellLabels:workCells.map(cell=>cell.getAttribute('data-label')||''),
                cellWidths:workCells.map(cell=>Math.round(cell.getBoundingClientRect().width)),
                buttonWidth:Math.round(workButton?.getBoundingClientRect().width||0),
                tableWidth:Math.round(workRow.getBoundingClientRect().width)
              }:null;
              const mainRect=main?.getBoundingClientRect();
              const sideRect=side?.getBoundingClientRect();
              // Inspect visible content surfaces throughout the page subtree.
              // Some modules wrap their data area in nested layout containers rather
              // than placing it directly beside the header.
              const contentSurfaces=[...(main?.querySelectorAll('*')||[])]
                .filter(el=>!el.classList.contains('top')&&!el.classList.contains('actions'))
                .map(el=>({el,rect:el.getBoundingClientRect(),style:getComputedStyle(el)}))
                .filter(x=>x.rect.width>=120&&x.rect.height>=24&&x.style.display!=='none'&&x.style.visibility!=='hidden');
              const contentRight=contentSurfaces.length
                ?Math.max(...contentSurfaces.map(x=>x.rect.right)):0;
              const contentLeft=contentSurfaces.length
                ?Math.min(...contentSurfaces.map(x=>x.rect.left)):0;
              return {
                actualPage,
                theme:document.documentElement.dataset.mcTheme,
                heading:document.querySelector('#main h1')?.textContent?.trim()||'',
                horizontalOverflow:Math.max(
                  document.documentElement.scrollWidth,
                  document.body.scrollWidth
                )-window.innerWidth,
                layout:{
                  viewport:window.innerWidth,
                  mainLeft:Math.round(mainRect?.left||0),
                  mainRight:Math.round(mainRect?.right||0),
                  mainWidth:Math.round(mainRect?.width||0),
                  sideRight:Math.round(sideRect?.right||0),
                  contentLeft:Math.round(contentLeft),
                  contentRight:Math.round(contentRight),
                  contentWidth:Math.round(contentRight-contentLeft)
                },
                cardBefore:card?getComputedStyle(card,'::before').backgroundImage:'none',
                studentWorkLayout
              };
            }""",
            {"role": role, "module": module, "theme": theme},
        )

    def assert_state(module: str, theme: str, state: dict, viewport: int) -> None:
        if state["theme"] != theme or not state["heading"]:
            raise AssertionError(
                f"Écran {role}/{module} : thème ou en-tête absent à {viewport}px ({state!r})"
            )
        if state["horizontalOverflow"] > 2:
            raise AssertionError(
                f"Débordement horizontal sur {role}/{module} à {viewport}px : {state!r}"
            )
        if viewport <= 650 and state["layout"]["contentRight"] < viewport - 24:
            raise AssertionError(
                f"Zone principale trop étroite ou partiellement masquée sur {role}/{module} "
                f"à {viewport}px : {state['layout']!r}"
            )
        if theme == "dark" and state["cardBefore"] != "none":
            raise AssertionError(
                f"Reflet clair indésirable sur les cartes sombres ({role}/{module}) : {state!r}"
            )

        if role == "student" and module == "studentWork" and viewport <= 650:
            layout = state.get("studentWorkLayout")
            if (
                not layout
                or layout["rowDisplay"] != "grid"
                or layout["columns"] != 2
                or layout["buttonWidth"] < 70
                or not all(layout["cellLabels"])
                or len(layout["cellWidths"]) != 5
            ):
                raise AssertionError(
                    "Le module Travail à faire doit s'empiler en carte mobile avec des actions lisibles : "
                    + repr(layout)
                )

    if role == "student":
        responsive_modules = [
            "studentHome","studentSchedule","studentLessons","studentWork","studentHomework",
            "studentMessages","studentDocuments","studentSettings"
        ]
        mobile_visual_modules = {
            "studentHome","studentSchedule","studentLessons","studentWork","studentMessages",
            "studentDocuments","studentSettings"
        }
    elif role == "admin":
        responsive_modules = ["adminUsers","teachers","ppDashboard","settings"]
        mobile_visual_modules = set(responsive_modules)
    else:
        responsive_modules = ["dashboard","schedule","lessons","students","messages","documents","settings"]
        mobile_visual_modules = {"dashboard","schedule","lessons","messages","documents","settings"}

    for theme in ("light", "dark"):
        system_theme = "dark" if theme == "light" else "light"
        page.emulate_media(color_scheme=system_theme)
        page.set_viewport_size(original_viewport)
        for module in modules:
            state = render_state(module, theme)
            assert_state(module, theme, state, original_viewport["width"])
            page.wait_for_timeout(140)
            destination = output_dir / f"{role}-{theme}-{module}.png"
            page.screenshot(path=str(destination), full_page=True, animations="disabled")

        if role == "student":
            cloud_nav = page.locator("#nav button[onclick*='studentDocuments']")
            if cloud_nav.count() != 1:
                raise AssertionError("Le Cloud élève doit être accessible dans la navigation latérale.")
            cloud_nav.click()
            expect(page.locator("#main h1")).to_contain_text("documents")

        for width in (900, 390):
            page.set_viewport_size({"width": width, "height": 900})
            for module in responsive_modules:
                state = render_state(module, theme)
                assert_state(module, theme, state, width)
                if width == 390 and module in mobile_visual_modules:
                    page.wait_for_timeout(80)
                    destination = output_dir / f"{role}-{theme}-{module}-390px.png"
                    page.screenshot(path=str(destination), full_page=True, animations="disabled")

        page.set_viewport_size(original_viewport)

    # Automatic appearance must follow the operating-system preference too.
    page.emulate_media(color_scheme="light")
    page.evaluate("setAppearanceTheme('system')")
    page.wait_for_function("document.documentElement.dataset.mcTheme === 'light'", timeout=1500)
    automatic_light = page.evaluate("""() => ({
        theme:document.documentElement.dataset.mcTheme,
        preference:document.documentElement.dataset.mcThemePreference,
        mediaDark:window.matchMedia('(prefers-color-scheme: dark)').matches,
        listenerInstalled:document.documentElement.dataset.mcThemeListener === '1'
    })""")
    if automatic_light["theme"] != "light" or automatic_light["mediaDark"]:
        raise AssertionError(f"Le thème automatique devrait être clair ici : {automatic_light!r}")
    page.emulate_media(color_scheme="dark")
    try:
        page.wait_for_function("document.documentElement.dataset.mcTheme === 'dark'", timeout=1500)
    except Exception as error:
        automatic_dark = page.evaluate("""() => ({
            theme:document.documentElement.dataset.mcTheme,
            preference:document.documentElement.dataset.mcThemePreference,
            mediaDark:window.matchMedia('(prefers-color-scheme: dark)').matches,
            listenerInstalled:document.documentElement.dataset.mcThemeListener === '1'
        })""")
        raise AssertionError(f"Le thème automatique ne suit pas le mode sombre : {automatic_dark!r}") from error
    page.evaluate("setAppearanceTheme('light')")

def acknowledge_release_notes(page, role: str) -> None:
    """Verify and acknowledge the real first-login release screen for an account."""
    modal = page.locator("#modal.releaseNotesModal")
    expect(modal).to_be_visible(timeout=10000)
    expect(modal).to_contain_text("Nouveautés de MaClasse")
    expect(modal).to_contain_text("V25.2.0")
    expect(modal).to_contain_text("une fois par compte")
    page.get_by_role("button", name="Voir le journal complet").click()
    expect(modal).to_be_visible()
    page.locator("#modal .modalhead .close").click()
    expect(modal).to_contain_text("Nouveautés de MaClasse")
    page.get_by_role("button", name="J’ai compris").click()
    expect(modal).not_to_be_visible(timeout=5000)
    state = page.evaluate("""async () => {
      const response = await fetch('/api/release-notes/state', {cache:'no-store'});
      if (!response.ok) throw new Error('Release notes state failed: '+response.status);
      return response.json();
    }""")
    if state.get("seen_version") != "25.2.0":
        raise AssertionError(f"Accusé de lecture non persisté pour {role}: {state!r}")


def verify_release_journal(page, role: str, output_dir: Path) -> None:
    """Exercise the journal as a user would, including theme and mobile layouts."""
    if role == "student":
        page.evaluate("page='studentSettings';appSpace='student';render()")
        expect(page.locator(".settingsStudentGrid")).to_be_visible()
        page.get_by_role("button", name="Journal des versions").click()
    else:
        page.locator("#nav button").filter(has_text="Paramètres").click()
        expect(page.locator("#main h1")).to_have_text("Paramètres")
        page.get_by_role("button", name="Consulter le journal des versions").click()

    modal = page.locator("#modal.releaseNotesModal")
    expect(modal).to_be_visible()
    nav = page.locator("#releaseNotesNav")
    expect(nav).to_contain_text("V25.1.1")
    expect(nav).to_contain_text("V25.0.6")
    expect(nav).to_contain_text("V21.22")
    expect(nav).to_contain_text("V20.10")
    expect(nav).to_contain_text("V19.7")
    if "V25.2.1" in nav.inner_text():
        raise AssertionError("Le journal ne doit pas inventer une version absente des archives.")

    output_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        page.evaluate("(theme) => setAppearanceTheme(theme)", theme)
        expect(page.locator("html")).to_have_attribute("data-mc-theme", theme)
        page.screenshot(path=str(output_dir / f"release-journal-{role}-{theme}.png"),
                        full_page=True, animations="disabled")

    # Automatic must follow the operating-system preference, independent of the last manual choice.
    page.emulate_media(color_scheme="dark")
    page.evaluate("setAppearanceTheme('system')")
    expect(page.locator("html")).to_have_attribute("data-mc-theme", "dark")
    page.emulate_media(color_scheme="light")
    page.evaluate("setAppearanceTheme('system')")
    expect(page.locator("html")).to_have_attribute("data-mc-theme", "light")

    # Verify a genuinely narrow modal, not only a CSS string.
    page.set_viewport_size({"width":390,"height":844})
    page.screenshot(path=str(output_dir / f"release-journal-{role}-mobile.png"),
                    full_page=True, animations="disabled")
    layout = page.evaluate("""() => ({
      viewport:window.innerWidth,
      documentWidth:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth),
      modalWidth:Math.round(document.getElementById('modal').getBoundingClientRect().width),
      navHeight:Math.round(document.getElementById('releaseNotesNav').getBoundingClientRect().height),
      articleHeight:Math.round(document.getElementById('releaseNotesArticle').getBoundingClientRect().height)
    })""")
    if layout["documentWidth"] > layout["viewport"] + 2 or layout["modalWidth"] > layout["viewport"] + 2:
        raise AssertionError(f"Journal mobile overflow for {role}: {layout!r}")
    page.set_viewport_size({"width":1280,"height":800})
    page.locator("#modal .modalhead .close").click()
    expect(modal).not_to_be_visible()


def verify_establishment_generator(page, output_dir: Path) -> None:
    """Open the real Direction generator and verify its privacy-first workflow."""
    page.evaluate("page='adminUsers';appSpace='teacher';render()")
    expect(page.get_by_role("heading",name="Générateur de configuration d’établissement")).to_be_visible()
    page.get_by_role("button",name="Ouvrir le générateur").click()
    modal=page.locator("#modal")
    expect(modal).to_contain_text("Générateur de configuration d’établissement")
    expect(modal).to_contain_text("1. Décrire l’établissement")
    expect(modal).to_contain_text("2. Générer le JSON dans ChatGPT")
    expect(modal).to_contain_text("3. Vérifier et importer")
    expect(modal).to_contain_text("ne transmets aucune identité réelle")
    expect(modal).to_contain_text("aucun fichier à un service externe")
    expect(modal.get_by_role("button",name="Télécharger le modèle JSON")).to_be_visible()
    expect(modal.get_by_role("button",name="Télécharger le schéma JSON")).to_be_visible()
    expect(modal.get_by_role("button",name="Télécharger les instructions")).to_be_visible()
    expect(modal.get_by_role("button",name="Exporter le contexte anonymisé")).to_be_visible()
    output_dir.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output_dir/"establishment-generator-admin-light.png"),full_page=True,animations="disabled")
    page.evaluate("setAppearanceTheme('dark')")
    expect(page.locator("html")).to_have_attribute("data-mc-theme","dark")
    page.screenshot(path=str(output_dir/"establishment-generator-admin-dark.png"),full_page=True,animations="disabled")
    page.locator("#modal .modalhead .close").click()
    expect(modal).not_to_be_visible()


def verify_settings_grid_geometry(page, role: str, output_dir: Path) -> None:
    """Check actual Settings card placement for each role at desktop and mobile widths."""
    is_student = role == "student"
    desktop_page = "studentSettings" if is_student else "settings"
    desktop_space = "student" if is_student else "teacher"
    page.set_viewport_size({"width":1280,"height":800})
    page.evaluate("(p,s) => { page=p; appSpace=s; render(); }", desktop_page, desktop_space)
    selector = "#main .settingsStudentGrid" if is_student else "#main .settingsGrid"
    grid = page.locator(selector)
    expect(grid).to_be_visible()
    state = grid.evaluate("""el => {
      const css=getComputedStyle(el);
      const rect=sel=>{
        const node=el.querySelector(sel);
        if(!node)return null;
        const r=node.getBoundingClientRect();
        return {left:Math.round(r.left),top:Math.round(r.top),width:Math.round(r.width)};
      };
      return {
        className:el.className,
        display:css.display,
        columns:css.gridTemplateColumns.split(/\\s+/).filter(Boolean).length,
        appearance:rect('.settingsAppearanceCard'),
        periods:rect('.settingsPeriodsCard'),
        rooms:rect('.settingsRoomsCard'),
        version:rect('.settingsVersionCard'),
        updates:rect('.settingsUpdateCard'),
        data:rect('.settingsDataCard')
      };
    }""")
    expected_columns = 2 if is_student else 3
    if state["display"] != "grid" or state["columns"] != expected_columns:
        raise AssertionError(f"Grille Paramètres desktop incorrecte pour {role}: {state!r}")
    if not is_student:
        if not (state["appearance"]["left"] < state["periods"]["left"] < state["version"]["left"]):
            raise AssertionError(f"Colonnes sémantiques Paramètres incohérentes pour {role}: {state!r}")
        if abs(state["rooms"]["left"]-state["appearance"]["left"]) > 3:
            raise AssertionError(f"Salles doit rester sous Apparence pour {role}: {state!r}")
        if abs(state["data"]["left"]-state["version"]["left"]) > 3:
            raise AssertionError(f"Données doit rester sous Version pour {role}: {state!r}")
        if role == "admin":
            if "settingsAdminLayout" not in state["className"] or not state["updates"]:
                raise AssertionError(f"La Direction doit recevoir la carte Mises à jour: {state!r}")
            if abs(state["updates"]["left"]-state["version"]["left"]) > 3:
                raise AssertionError(f"Mises à jour doit rester dans la colonne de droite: {state!r}")
        elif "settingsAdminLayout" in state["className"] or state["updates"] is not None:
            raise AssertionError(f"Le professeur ne doit pas recevoir le layout Direction: {state!r}")
    else:
        if "settingsStudentGrid" not in state["className"]:
            raise AssertionError(f"L'élève doit utiliser sa grille Paramètres dédiée: {state!r}")

    output_dir.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output_dir/f"settings-{role}-desktop.png"),full_page=True,animations="disabled")
    page.set_viewport_size({"width":390,"height":844})
    page.evaluate("(p,s) => { page=p; appSpace=s; render(); }", desktop_page, desktop_space)
    mobile = page.locator(selector)
    mobile_state = mobile.evaluate("""el => ({
      display:getComputedStyle(el).display,
      columns:getComputedStyle(el).gridTemplateColumns.split(/\\s+/).filter(Boolean).length,
      width:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth),
      viewport:window.innerWidth
    })""")
    if mobile_state["display"] != "grid" or mobile_state["columns"] != 1 or mobile_state["width"] > mobile_state["viewport"]+2:
        raise AssertionError(f"Paramètres mobile incohérents pour {role}: {mobile_state!r}")
    page.screenshot(path=str(output_dir/f"settings-{role}-mobile.png"),full_page=True,animations="disabled")
    page.set_viewport_size({"width":1280,"height":800})


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="maclasse-firefox-edt-") as temp:
        app_root = Path(temp) / "app"
        shutil.copytree(
            SOURCE_ROOT,
            app_root,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", "venv", "data", "__pycache__", "*.pyc",
                "backups", "backup", "node_modules",
            ),
        )
        port = free_port()
        env = os.environ.copy()
        env.update({"MACLASSE_HOST": "127.0.0.1", "MACLASSE_PORT": str(port)})
        server = subprocess.Popen(
            [sys.executable, str(app_root / "server.py")],
            cwd=app_root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        browser = None
        try:
            url = f"http://127.0.0.1:{port}/"
            deadline = time.time() + 20
            while time.time() < deadline:
                if server.poll() is not None:
                    stderr = server.stderr.read() if server.stderr else ""
                    raise AssertionError(f"MaClasse server stopped: {stderr}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                        break
                except OSError:
                    time.sleep(0.2)
            else:
                raise AssertionError("MaClasse server did not start in time")

            with sync_playwright() as playwright:
                browser = playwright.firefox.launch()
                page = browser.new_page(locale='fr-FR', timezone_id='Europe/Paris')
                page_errors: list[str] = []
                browser_errors: list[str] = []
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on("console", lambda message: browser_errors.append(message.text) if message.type == "error" else None)
                page.goto(url, wait_until="networkidle")
                browser_locale = page.evaluate("""() => ({
                  language:navigator.language,
                  timezone:Intl.DateTimeFormat().resolvedOptions().timeZone
                })""")
                if browser_locale.get("language") != "fr-FR" or browser_locale.get("timezone") != "Europe/Paris":
                    raise AssertionError("Le navigateur de recette doit utiliser fr-FR / Europe-Paris : "
                                         +repr(browser_locale))

                # Create a disposable administrator in the temporary app.
                expect(page.locator('input[name="first"]')).to_be_visible()
                page.locator('input[name="first"]').fill("Test")
                page.locator('input[name="last"]').fill("Firefox")
                page.locator('input[name="username"]').fill("firefox-test")
                page.locator('input[name="password"]').fill("Temporary-Test-Password-2026!")
                page.locator('input[name="confirm"]').fill("Temporary-Test-Password-2026!")
                page.get_by_role("button", name="Créer l’accès direction").click()
                expect(page.locator("#nav")).not_to_be_empty()
                acknowledge_release_notes(page, "direction")
                verify_release_journal(page, "admin", Path("artifacts/browser-v25"))
                verify_settings_grid_geometry(page, "admin", Path("artifacts/browser-v25"))
                page.evaluate("page='adminUsers';appSpace='teacher';render()")
                verify_establishment_generator(page, Path("artifacts/browser-v25"))
                page.evaluate("setAppearanceTheme('light')")

                # Seed one recurring course through the real authenticated API.
                page.evaluate(
                    """async () => {
                      const response = await fetch('/api/data', {cache:'no-store'});
                      if (!response.ok) throw new Error('GET /api/data: '+response.status);
                      const revision = response.headers.get('X-MaClasse-Revision');
                      const data = await response.json();
                      data.settings = data.settings || {};
                      data.settings.subjectColors = {...(data.settings.subjectColors || {}), francais:'#123456'};
                      data.classes = [{
                        id:'firefox-class', name:'6e A', level:'6e',
                        levels:['6e'], teacherIds:[], groups:['A','B'],
                        attendanceMode:'hour', periodMode:'trimestres'
                      }];
                      data.students = [{id:'firefox-student',first:'Élève',last:'Test',classId:'firefox-class',group:'A'}];
                      const reportTerm = data.settings.terms?.[0]?.id || 'firefox-term';
                      if (!data.settings.terms?.length) {
                        data.settings.terms = [{
                          id:reportTerm,name:'Trimestre 1',start:'2026-09-01',end:'2026-12-31'
                        }];
                      }
                      data.evaluations = [{
                        id:'firefox-evaluation',title:'Contrôle de français',
                        classId:'firefox-class',group:'A',subject:'Français',
                        date:'2026-11-12',maxScore:20,coefficient:1,published:true,
                        grades:[{studentId:'firefox-student',value:'16'}]
                      }];
                      data.attendance = [{
                        id:'firefox-attendance',classId:'firefox-class',
                        date:'2026-11-12',mode:'hour',slotId:'firefox-existing-course',
                        time:'09:00',rows:[{
                          studentId:'firefox-student',status:'absent',
                          justified:false,reason:''
                        }]
                      }];
                      data.bulletins = [{
                        id:'firefox-bulletin',studentId:'firefox-student',
                        classId:'firefox-class',termId:reportTerm,
                        subjectData:{'Français':{comment:'Participation régulière.'}},
                        overall:'Ensemble sérieux.',published:false,validated:false
                      }];
                      data.schedule = [{
                        id:'firefox-existing-course', classId:'firefox-class',
                        day:4, time:'09:00', endTime:'10:00',
                        subject:'Français', recurrence:'weekly',
                        startDate:'2026-11-09', endDate:'',
                        exceptions:[], overrides:{}, teacherId:'',
                        room:'', group:'A'
                      }];
                      const saved = await fetch('/api/save', {
                        method:'POST',
                        headers:{'Content-Type':'application/json','If-Match':revision},
                        body:JSON.stringify(data)
                      });
                      if (!saved.ok) throw new Error('POST /api/save: '+saved.status+' '+await saved.text());
                      db = await api('/api/data');
                      normalize();
                      scheduleView='week';
                      selectedWeek=scheduleLocalDate('2026-11-09');
                      page='schedule';
                      render();
                    }"""
                )

                existing = page.locator('[data-schedule-id="firefox-existing-course"]')
                try:
                    expect(existing).to_be_visible(timeout=5_000)
                except AssertionError as failure:
                    initial_state=page.evaluate("""({pageErrors,browserErrors}) => {
                      const target=(db.schedule||[]).find(x=>x.id==='firefox-existing-course');
                      const dates=weekDates();
                      const main=document.getElementById('main');
                      const surface=main?.querySelector('.scheduleCalendarSurface');
                      return {
                        page,appSpace,authUser,authReady,scheduleView,
                        selectedWeek:iso(selectedWeek),
                        weekDates:dates.map(iso),
                        target,
                        targetRecurring:target?recurring(target,dates[4]):null,
                        fridayOccurrences:dayOcc(dates[4]).map(x=>({id:x.id,subject:x.subject,time:x.time})),
                        computedMarkup:scheduleWeek(dates,d=>dayOcc(d),false).includes('Français'),
                        lastRenderError:lastRenderError?String(lastRenderError.stack||lastRenderError):null,
                        mainExists:!!main,
                        mainHtml:main?.innerHTML.slice(0,12000)||'',
                        calendarExists:!!surface,
                        calendarText:surface?.innerText||'',
                        calendarHtml:surface?.innerHTML.slice(0,8000)||'',
                        revision:{dataRevision,lastRenderedRevision},
                        pageErrors,browserErrors
                      };
                    }""", {"pageErrors":page_errors,"browserErrors":browser_errors})
                    raise AssertionError(
                        "Le premier créneau EDT ne s'affiche pas : "
                        +json.dumps(initial_state,ensure_ascii=False)+" | "+str(failure)
                    )
                if "#123456" not in (existing.get_attribute("style") or ""):
                    raise AssertionError("La couleur personnalisée de matière n'est pas appliquée à l'EDT professeur.")

                # Today, month, week navigation in both directions, then back.
                page.locator("button.scheduleToday").click()
                if not existing.is_visible():
                    state = page.evaluate("""() => ({
                      now: new Date().toString(),
                      page, scheduleView,
                      selectedWeek: selectedWeek.toString(),
                      selectedIso: iso(selectedWeek),
                      schedule: (db.schedule || []).map(x => ({
                        id:x.id, day:x.day, startDate:x.startDate,
                        endDate:x.endDate, recurrence:x.recurrence,
                        exceptions:x.exceptions
                      })),
                      calendar: document.querySelector('.scheduleCalendarSurface')?.innerHTML.slice(0,3000) || null
                    })""")
                    raise AssertionError("Le cours disparaît après « Aujourd’hui » : "
                                         + json.dumps(state, ensure_ascii=False)
                                         + " | page errors=" + repr(page_errors)
                                         + " | console errors=" + repr(browser_errors))
                expect(existing).to_be_visible()

                page.locator(".scheduleViewSwitch").get_by_role("button", name="Mois").click()
                expect(page.locator(".scheduleMonthView")).to_be_visible()
                month_counts = page.locator(".scheduleMonthCount")
                expect(month_counts).to_have_count(3)
                expect(month_counts.first).to_contain_text("cours")

                page.locator(".scheduleViewSwitch").get_by_role("button", name="Semaine").click()
                expect(existing).to_be_visible()
                nav_buttons = page.locator(".scheduleDateNav .scheduleIconBtn")
                nav_buttons.nth(1).click()
                expect(existing).to_be_visible()
                nav_buttons.nth(0).click()
                expect(existing).to_be_visible()

                # Create a second course through the actual modal and form.
                page.evaluate("openSchedule()")
                form = page.locator("#modalback form")
                expect(form).to_be_visible()
                form.locator('[name="day"]').select_option("2")
                form.locator('[name="classIds"]').select_option("firefox-class")
                form.locator('[name="time"]').fill("11:00")
                form.locator('[name="endTime"]').fill("12:00")
                form.locator('[name="subject"]').fill("Histoire")
                form.locator('[name="recurrence"]').select_option("weekly")
                form.locator('[name="startDate"]').fill("2026-11-09")
                page.evaluate("window.__scheduleScrollBefore=window.scrollY")
                form.locator("button.primary").last.click()
                expect(page.locator("#toast")).to_contain_text(
                    "Emploi du temps enregistré.", timeout=10_000
                )
                expect(page.locator('[data-schedule-id="firefox-existing-course"]')).to_be_visible()
                expect(page.locator('[data-schedule-id]').filter(has_text="Histoire")).to_be_visible()
                scroll_state = page.evaluate("() => ({before:window.__scheduleScrollBefore,after:window.scrollY})")
                if abs(scroll_state["before"]-scroll_state["after"]) > 2:
                    raise AssertionError("L'enregistrement du créneau a déplacé la page : "+repr(scroll_state))

                # Open the same timetable as a real student account in a separate
                # browser context, then change the timetable from the administrator.
                teacher_id = page.evaluate("""async () => {
                  const created = await fetch('/api/admin/teacher', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({
                      username:'firefox-teacher',first:'Prof',last:'Test',
                      subjects:['Français'],classIds:['firefox-class'],ppIds:[],
                      password:'Teacher-Temporary-Password-2026!'
                    })
                  });
                  const teacherResult = await created.json();
                  if (!created.ok) throw new Error('Teacher creation failed: '+JSON.stringify(teacherResult));
                  const id = teacherResult.user.teacherId;
                  const response = await fetch('/api/data', {cache:'no-store'});
                  const revision = response.headers.get('X-MaClasse-Revision');
                  const data = await response.json();
                  data.schedule.find(x=>x.id==='firefox-existing-course').teacherId=id;
                  data.mailboxV2 = {
                    schemaVersion:2,resetPending:false,
                    messages:[{
                      id:'firefox-student-message',threadId:'firefox-student-thread',
                      sender:{key:'teacher:'+id,role:'teacher',id,name:'Prof Test'},
                      to:['student:firefox-student'],cc:[],bcc:[],
                      subject:'Message de test élève',body:'La messagerie élève fonctionne.',
                      sentAt:'2026-11-15T10:00:00Z',attachments:[]
                    }],
                    states:{['student:firefox-student']:{'firefox-student-message':{folder:'inbox',read:false}}},
                    folders:[],drafts:[]
                  };
                  const saved = await fetch('/api/save', {
                    method:'POST',
                    headers:{'Content-Type':'application/json','If-Match':revision},
                    body:JSON.stringify(data)
                  });
                  if (!saved.ok) throw new Error('Teacher-linked mailbox seed failed: '+saved.status+' '+await saved.text());
                  return id;
                }""")
                teacher_context = browser.new_context(locale='fr-FR', timezone_id='Europe/Paris')
                teacher_page = teacher_context.new_page()
                teacher_page_errors: list[str] = []
                teacher_page.on("pageerror", lambda error: teacher_page_errors.append(str(error)))
                teacher_page.goto(url, wait_until="networkidle")
                teacher_state = teacher_page.evaluate("""async () => {
                  const response = await fetch('/api/auth/login', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({username:'firefox-teacher',password:'Teacher-Temporary-Password-2026!'})
                  });
                  const result = await response.json();
                  if (!response.ok) throw new Error('Teacher login failed: '+JSON.stringify(result));
                  const changed = await fetch('/api/auth/change-password', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({currentPassword:'Teacher-Temporary-Password-2026!',newPassword:'Teacher-Test-Password-2026!'})
                  });
                  if (!changed.ok) throw new Error('Teacher password change failed: '+await changed.text());
                  await load();
                  return {role:authUser?.role,id:authUser?.id};
                }""")
                if teacher_state.get("role") != "teacher" or teacher_state.get("id") != teacher_id:
                    raise AssertionError("Teacher session not initialized: "+repr(teacher_state))
                acknowledge_release_notes(teacher_page, "professeur")
                verify_release_journal(teacher_page, "teacher", Path("artifacts/browser-v25"))
                verify_settings_grid_geometry(teacher_page, "teacher", Path("artifacts/browser-v25"))
                teacher_page.evaluate("page='schedule';appSpace='teacher';render()")
                shared_cloud = teacher_page.evaluate("""async () => {
                  const folder='cloud/personal/users/'+authUser.id;
                  const shared=await upload(new File(
                    ['Fichier de révision partagé avec un élève.'],
                    'Fiche partagée.txt',{type:'text/plain'}
                  ),folder);
                  const privateFile=await upload(new File(
                    ['Document strictement privé.'],
                    'Document privé.txt',{type:'text/plain'}
                  ),folder);
                  const data=await api('/api/data');
                  data.cloudItems??=[];
                  data.cloudItems.push(
                    {
                      id:'firefox-student-shared-cloud-file',type:'file',
                      name:'Fiche partagée.txt',size:shared.size,mime:'text/plain',
                      url:shared.url,serverName:shared.name,space:'personal',
                      ownerId:authUser.id,parentId:'',
                      shares:[{type:'student',id:'firefox-student',role:'edit'}],
                      createdAt:new Date().toISOString()
                    },
                    {
                      id:'firefox-student-private-cloud-file',type:'file',
                      name:'Document privé.txt',size:privateFile.size,mime:'text/plain',
                      url:privateFile.url,serverName:privateFile.name,space:'personal',
                      ownerId:authUser.id,parentId:'',shares:[],
                      createdAt:new Date().toISOString()
                    }
                  );
                  await api('/api/save',{
                    method:'POST',
                    headers:{'Content-Type':'application/json','If-Match':dataRevision||''},
                    body:JSON.stringify(data)
                  });
                  // Keep the live teacher model aligned with the newly committed Cloud metadata.
                  db=await api('/api/data');normalize();
                  return {sharedUrl:shared.url,privateUrl:privateFile.url};
                }""")
                # The active evaluation page must agree with the selected class immediately.
                teacher_page.evaluate("""() => {
                  window.classContext='deleted-class';
                  page='evaluations';appSpace='teacher';render();
                }""")
                expect(teacher_page.locator('#evalClassFilter')).to_have_value('firefox-class')
                expect(teacher_page.locator('#evalStats')).not_to_contain_text(
                    "Sélectionne une classe pour afficher les évaluations."
                )
                teacher_page.evaluate("window.classContext='';page='schedule';appSpace='teacher';render();")
                # Product smoke pass: render each visible teacher module in the real browser.
                module_smoke = teacher_page.evaluate("""() => {
                  const modules=[
                    'dashboard','today','activity','notifications','schedule',
                    'lessons','students','evaluations','attendance',
                    'attendanceFollowup','bulletins','messages','documents',
                    'teachers','classes','ppDashboard','settings'
                  ];
                  const results=[];
                  for(const id of modules){
                    page=id;appSpace='teacher';render();
                    const main=document.getElementById('main');
                    const text=main?.innerText||'';
                    results.push({
                      id,
                      hasTitle:!!main?.querySelector('.top h1'),
                      hasError:text.includes('Une erreur a empêché l’affichage de cette page.'),
                      title:main?.querySelector('.top h1')?.innerText||'',
                      width:main?.scrollWidth||0,
                      viewport:window.innerWidth,
                      lessonWeekHasSelectedDate:!['lessons','studentLessons'].includes(id)||!!main?.querySelector('.lessonWeek .dayBtn.active')
                    });
                  }
                  return results;
                }""")
                broken_modules = [item for item in module_smoke if item["hasError"] or not item["hasTitle"]]
                if broken_modules:
                    raise AssertionError("Des modules professeur ne se rendent pas correctement : "
                                         + json.dumps(broken_modules,ensure_ascii=False))
                misaligned_teacher_lessons = [
                    item for item in module_smoke
                    if item["id"] == "lessons" and not item["lessonWeekHasSelectedDate"]
                ]
                if misaligned_teacher_lessons:
                    raise AssertionError(
                        "La semaine affichée dans Leçons & séances ne contient pas la date sélectionnée : "
                        + json.dumps(misaligned_teacher_lessons,ensure_ascii=False)
                    )

                tracking_state = teacher_page.evaluate("""() => {
                  window.classContext='';
                  page='classes';appSpace='teacher';render();
                  const card=[...document.querySelectorAll('.classHubCard')].find(x=>(x.innerText||'').includes('6e A'));
                  if(!card)throw new Error('La classe accessible doit apparaître dans le module Classes unifié.');
                  const action=[...card.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Voir le suivi');
                  if(!action)throw new Error('La fiche de suivi doit rester accessible depuis la carte de classe.');
                  action.click();
                  const main=document.getElementById('main');
                  return {
                    title:main?.querySelector('.top h1')?.innerText||'',
                    hasClass:(main?.innerText||'').includes('6e A'),
                    hasStudents:(main?.innerText||'').includes('Élèves'),
                    hasAttendance:(main?.innerText||'').includes('Assiduité récente'),
                    hasUpcoming:(main?.innerText||'').includes('Prochaines échéances'),
                    hasError:(main?.innerText||'').includes('Une erreur a empêché l’affichage de cette page.')
                  };
                }""")
                if tracking_state["title"] != "Classes" or not tracking_state["hasClass"] or tracking_state["hasError"] or not tracking_state["hasStudents"] or not tracking_state["hasAttendance"] or not tracking_state["hasUpcoming"]:
                    raise AssertionError("Le module Classes unifié ne s'affiche pas correctement dans Firefox : "+repr(tracking_state))

                # Manual theme choices must override the operating-system preference.
                teacher_page.emulate_media(color_scheme="light")
                dark_theme = teacher_page.evaluate("""() => {
                  setAppearanceTheme('dark');
                  const style=getComputedStyle(document.documentElement);
                  return {
                    preference:document.documentElement.dataset.mcThemePreference,
                    theme:document.documentElement.dataset.mcTheme,
                    colorScheme:style.colorScheme,
                    background:style.getPropertyValue('--ui-bg').trim(),
                    text:style.getPropertyValue('--ui-text').trim()
                  };
                }""")
                if dark_theme["theme"] != "dark" or dark_theme["colorScheme"] != "dark":
                    raise AssertionError("Le thème sombre manuel ne s'impose pas au thème système clair : "
                                         + repr(dark_theme))
                teacher_page.emulate_media(color_scheme="dark")
                light_theme = teacher_page.evaluate("""() => {
                  setAppearanceTheme('light');
                  const style=getComputedStyle(document.documentElement);
                  return {
                    preference:document.documentElement.dataset.mcThemePreference,
                    theme:document.documentElement.dataset.mcTheme,
                    colorScheme:style.colorScheme,
                    background:style.getPropertyValue('--ui-bg').trim(),
                    text:style.getPropertyValue('--ui-text').trim()
                  };
                }""")
                if light_theme["theme"] != "light" or light_theme["colorScheme"] != "light":
                    raise AssertionError("Le thème clair manuel ne s'impose pas au thème système sombre : "
                                         + repr(light_theme))
                teacher_page.evaluate("setAppearanceTheme('light');page='schedule';appSpace='teacher';render();")
                cloud_layout = teacher_page.evaluate("""() => {
                  const inspect = space => {
                    page='documents';appSpace='teacher';setCloudSpace(space);
                    const layout=document.querySelector('.cloudLayout');
                    const side=layout?.querySelector(':scope > aside');
                    return {
                      space,
                      actualSpace:window.cloudSpace,
                      classContext:window.classContext||'',
                      hasSidebar:!!side,
                      columns:getComputedStyle(layout).gridTemplateColumns,
                      sectionWidth:Math.round(layout?.querySelector(':scope > section')?.getBoundingClientRect().width||0),
                      mainWidth:Math.round(layout?.getBoundingClientRect().width||0)
                    };
                  };
                  return {
                    personal:inspect('personal'),
                    shared:inspect('shared'),
                    class:inspect('class')
                  };
                }""")
                for space in ("personal","shared"):
                    state=cloud_layout[space]
                    if state["actualSpace"] != space or (space != "class" and state["classContext"]) or state["hasSidebar"] or len(state["columns"].split()) != 1:
                        raise AssertionError(
                            "Cloud "+space+" doit utiliser toute la largeur sans colonne latérale vide : "
                            + repr(state)
                        )
                class_state=cloud_layout["class"]
                if class_state["actualSpace"] != "class" or not class_state["hasSidebar"] or len(class_state["columns"].split()) != 2:
                    raise AssertionError(
                        "Cloud Classe doit conserver sa navigation latérale : "+repr(class_state)
                    )
                teacher_page.evaluate("window.cloudSpace='personal';page='schedule';appSpace='teacher';render();")
                uploaded_homework = teacher_page.evaluate("""async () => {
                  db=await api('/api/data');
                  normalize();
                  lessonDraft={
                    sid:'firefox-existing-course',date:'2026-11-13',
                    title:'Séance test',content:'',makeWork:true,workType:'normal',
                    workTitle:'Devoir avec pièce jointe',workDue:'2026-11-20',
                    workDueTime:'09:00',workContent:'Consigne de test',
                    workSubmit:true,workEvalLink:false,files:[],workFiles:[]
                  };
                  const file=new File(['Fichier de devoir de test'],'devoir-test.txt',{type:'text/plain'});
                  await uploadWorkFiles('firefox-existing-course','2026-11-13',[file]);
                  const slot=db.schedule.find(x=>x.id==='firefox-existing-course');
                  const lesson={
                    id:'firefox-homework-lesson',scheduleId:slot.id,date:'2026-11-13',
                    classId:slot.classId,subject:slot.subject,title:'Séance test',content:'',
                    files:[],homework:{
                      title:'Devoir avec pièce jointe',type:'normal',due:'2026-11-20',
                      dueTime:'09:00',instructions:'Consigne de test',
                      files:[...lessonDraft.workFiles],requiresSubmission:true,
                      submissionFolder:{id:'firefox-homework-folder',name:'Rendus — Devoir avec pièce jointe'}
                    }
                  };
                  db.lessons.push(lesson);
                  const localCloud=JSON.parse(JSON.stringify(db.cloudItems||[]));
                  const serverResponse=await fetch('/api/data',{cache:'no-store'});
                  const serverData=await serverResponse.json();
                  const serverCloud=serverData.cloudItems||[];
                  try {
                    save(true);
                    await flushPendingSave();
                  } catch(error) {
                    return {
                      saveError:String(error?.message||error),
                      teacherId:authUser?.id,
                      localCloud,
                      serverCloud,
                      localRevision:dataRevision,
                      serverRevision:serverResponse.headers.get('X-MaClasse-Revision')
                    };
                  }
                  return {file:lesson.homework.files[0],localCloud,serverCloud};
                }""")
                if uploaded_homework and uploaded_homework.get("saveError"):
                    raise AssertionError("Sauvegarde après partage Cloud refusée : "+json.dumps(uploaded_homework,ensure_ascii=False))
                uploaded_homework_file=(uploaded_homework or {}).get("file")
                if not uploaded_homework_file or not uploaded_homework_file.get("url"):
                    raise AssertionError("Teacher homework attachment was not uploaded: "+repr(uploaded_homework))
                if teacher_page_errors:
                    raise AssertionError("Teacher Firefox page errors: "+" | ".join(teacher_page_errors))
                account = page.evaluate("""async () => {
                  const response = await fetch('/api/admin/student-account', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({studentId:'firefox-student',username:'firefox-student'})
                  });
                  const result = await response.json();
                  if (!response.ok) throw new Error('Student account creation failed: '+JSON.stringify(result));
                  return result.user.temporaryPassword;
                }""")
                # Exercise the actual Direction interface, not only the administration API.
                page.evaluate("""async () => {
                  db=await api('/api/data');
                  normalize();
                  page='adminUsers';
                  appSpace='teacher';
                  render();
                }""")
                expect(page.locator('#main h1')).to_contain_text("Utilisateurs")
                expect(page.locator('#main')).to_contain_text("firefox-student")

                page.get_by_role("button",name="+ Nouveau professeur").click()
                admin_teacher_form=page.locator("#modal form")
                expect(admin_teacher_form).to_be_visible()
                admin_teacher_form.locator('input[name="first"]').fill("Camille")
                admin_teacher_form.locator('input[name="last"]').fill("Interface")
                admin_teacher_form.locator('input[name="username"]').fill("ui-test-prof")
                admin_teacher_form.locator('input[name="subjectsText"]').fill("Sciences")
                admin_teacher_form.get_by_role("button",name="Enregistrer le professeur").click()
                expect(page.locator("#modal")).to_contain_text("Compte professeur créé",timeout=10_000)
                page.locator("#modal .modalfoot button").click()
                ui_teacher_row=page.locator("#main .message").filter(has_text="ui-test-prof")
                expect(ui_teacher_row).to_contain_text("Actif",timeout=10_000)
                ui_teacher_row.get_by_role("button",name="Désactiver").click()
                expect(ui_teacher_row).to_contain_text("Désactivé",timeout=10_000)
                ui_teacher_row.get_by_role("button",name="Activer").click()
                expect(ui_teacher_row).to_contain_text("Actif",timeout=10_000)

                capture_product_screenshots(
                    page,
                    "admin",
                    ["adminUsers","teachers","ppDashboard","settings"],
                    Path("artifacts/browser-v25"),
                )
                page.evaluate("""() => {
                  page='adminUsers';
                  appSpace='teacher';
                  render();
                }""")

                student_context = browser.new_context(locale='fr-FR', timezone_id='Europe/Paris')
                student_page = student_context.new_page()
                student_page_errors: list[str] = []
                student_console_errors: list[str] = []
                student_page.on("pageerror", lambda error: student_page_errors.append(str(error)))
                student_page.on("console", lambda message: student_console_errors.append(message.text) if message.type == "error" else None)
                student_page.goto(url, wait_until="networkidle")
                student_state = student_page.evaluate("""async (password) => {
                  const response = await fetch('/api/auth/login', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({username:'firefox-student',password})
                  });
                  const result = await response.json();
                  if (!response.ok) throw new Error('Student login failed: '+JSON.stringify(result));
                  const changed = await fetch('/api/auth/change-password', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({currentPassword:password,newPassword:'Student-Test-Password-2026!'})
                  });
                  if (!changed.ok) throw new Error('Student password change failed: '+await changed.text());
                  await load();
                  page='studentSchedule';
                  appSpace='student';
                  selectedWeek=scheduleLocalDate('2026-11-09');
                  scheduleView='week';
                  render();
                  return {role:authUser?.role,studentId:authUser?.studentId,page};
                }""", account)
                if student_state.get("role") != "student" or student_state.get("studentId") != "firefox-student":
                    raise AssertionError("Student session not initialized: "+repr(student_state))
                acknowledge_release_notes(student_page, "élève")
                verify_release_journal(student_page, "student", Path("artifacts/browser-v25"))
                verify_settings_grid_geometry(student_page, "student", Path("artifacts/browser-v25"))
                student_page.evaluate("page='studentSchedule';appSpace='student';render()")
                student_module_smoke = student_page.evaluate("""() => {
                  const modules=[
                    'studentHome','studentSchedule','studentLessons','studentWork',
                    'studentResults','studentLife','studentMessages','studentDocuments',
                    'studentSettings','today','activity'
                  ];
                  const results=[];
                  for(const id of modules){
                    page=id;appSpace='student';render();
                    const main=document.getElementById('main');
                    const text=main?.innerText||'';
                    results.push({
                      id,
                      hasTitle:!!main?.querySelector('.top h1'),
                      hasError:text.includes('Une erreur a empêché l’affichage de cette page.'),
                      title:main?.querySelector('.top h1')?.innerText||'',
                      width:main?.scrollWidth||0,
                      viewport:window.innerWidth,
                      lessonWeekHasSelectedDate:!['lessons','studentLessons'].includes(id)||!!main?.querySelector('.lessonWeek .dayBtn.active')
                    });
                  }
                  return results;
                }""")
                broken_student_modules = [
                    item for item in student_module_smoke
                    if item["hasError"] or not item["hasTitle"]
                ]
                if broken_student_modules:
                    raise AssertionError(
                        "Des modules de l'espace élève ne se rendent pas correctement : "
                        + json.dumps(broken_student_modules,ensure_ascii=False)
                    )
                misaligned_student_lessons = [
                    item for item in student_module_smoke
                    if item["id"] == "studentLessons" and not item["lessonWeekHasSelectedDate"]
                ]
                if misaligned_student_lessons:
                    raise AssertionError(
                        "La semaine affichée dans Séances & leçons élève ne contient pas la date sélectionnée : "
                        + json.dumps(misaligned_student_lessons,ensure_ascii=False)
                    )

                # The dedicated student work module must expose overdue, unsubmitted work.
                student_page.evaluate("""() => {
                  page='studentHome';
                  appSpace='student';
                  render();
                }""")
                student_page.get_by_role("button",name="Voir mon travail").click()
                expect(student_page.locator("#main h1")).to_contain_text("Travail à faire")
                expect(student_page.locator("#nav button[onclick*='studentWork']")).to_contain_text("1")
                overdue_row=student_page.locator("#main .table tbody tr").filter(
                    has_text="Devoir avec pièce jointe"
                )
                expect(overdue_row).to_contain_text("En retard")
                expect(overdue_row.get_by_role("button",name="Ouvrir")).to_be_visible()

                student_tracking_state = student_page.evaluate("""() => {
                  page='ppDashboard';appSpace='teacher';render();
                  const main=document.getElementById('main');
                  return {
                    title:main?.querySelector('.top h1')?.innerText||'',
                    hasClassCards:!!main?.querySelector('.ppQuick'),
                    hasError:(main?.innerText||'').includes('Une erreur a empêché l’affichage de cette page.')
                  };
                }""")
                if student_tracking_state["title"] == "Suivi de classe" or student_tracking_state["hasClassCards"] or student_tracking_state["hasError"]:
                    raise AssertionError("Un compte élève ne doit pas accéder au Suivi de classe : "+repr(student_tracking_state))
                # The student can read an explicitly shared Cloud file, but cannot
                # see the teacher's private sibling or write to the Cloud.
                student_page.evaluate("""() => {
                  page='studentDocuments';appSpace='student';
                  window.cloudSpace='shared';window.cloudPath=[];window.cloudSelected='';
                  render();
                }""")
                expect(student_page.locator('.top')).to_contain_text("Mes documents")
                expect(student_page.locator('.cloudName')).to_contain_text("Fiche partagée.txt")
                if "Document privé.txt" in student_page.locator('#main').inner_text():
                    raise AssertionError("Un document Cloud privé de l'enseignant apparaît chez l'élève.")
                cloud_access = student_page.evaluate("""async ({sharedUrl,privateUrl}) => {
                  const sharedItem=db.cloudItems.find(x=>x.id==='firefox-student-shared-cloud-file');
                  const privateItem=db.cloudItems.find(x=>x.id==='firefox-student-private-cloud-file');
                  const [sharedResponse,privateResponse,writeResponse]=await Promise.all([
                    fetch(sharedUrl,{cache:'no-store'}),
                    fetch(privateUrl,{cache:'no-store'}),
                    fetch('/api/upload',{
                      method:'POST',
                      headers:{'X-Filename':'utf8:tentative.txt','X-Upload-Folder':'cloud/class/classes/firefox-class'},
                      body:new Blob(['tentative'],{type:'text/plain'})
                    })
                  ]);
                  return {
                    sharedStatus:sharedResponse.status,
                    sharedContent:await sharedResponse.text(),
                    privateStatus:privateResponse.status,
                    visibleShared:!!sharedItem,
                    visiblePrivate:!!privateItem,
                    sharedRole:sharedItem?.shares?.[0]?.role||null,
                    canWrite:cloudCanWrite('student',activeStudent(),sharedItem),
                    uploadStatus:writeResponse.status
                  };
                }""", shared_cloud)
                if cloud_access["sharedStatus"] != 200 or cloud_access["sharedContent"] != "Fichier de révision partagé avec un élève.":
                    raise AssertionError("Le fichier Cloud partagé n'est pas lisible par l'élève : "+repr(cloud_access))
                if cloud_access["privateStatus"] != 403 or cloud_access["visiblePrivate"]:
                    raise AssertionError("Un fichier Cloud privé n'est pas correctement cloisonné : "+repr(cloud_access))
                if not cloud_access["visibleShared"] or cloud_access["sharedRole"] != "view" or cloud_access["canWrite"] or cloud_access["uploadStatus"] != 403:
                    raise AssertionError("Le Cloud élève doit être strictement en lecture seule : "+repr(cloud_access))
                student_page.evaluate("page='studentHome';appSpace='student';render();")
                student_page.evaluate("page='studentHome';appSpace='student';setAppearanceTheme('light');render();")
                student_page.evaluate("""() => {
                  page='studentMessages';
                  appSpace='student';
                  render();
                }""")
                # The student account must have its own settings page and shared lesson header.
                student_page.evaluate("""() => { page='studentSettings'; appSpace='student'; render(); }""")
                expect(student_page.locator(".top")).to_contain_text("Paramètres")
                expect(student_page.locator("#main")).to_contain_text("Mon profil")
                expect(student_page.locator("#main")).to_contain_text("Sécurité")
                expect(student_page.get_by_role("button", name="Changer mon mot de passe")).to_be_visible()
                expect(student_page.locator(".themeChoices button")).to_have_count(3)
                student_page.evaluate("""() => { page='studentLessons'; appSpace='student'; render(); }""")
                expect(student_page.locator(".top")).to_contain_text("Séances & leçons")
                expect(student_page.locator(".lessonTopBar")).to_be_visible()

                # The student must see and be able to open the teacher's saved homework attachment.
                student_page.evaluate("""async () => {
                  db=await api('/api/data');
                  normalize();
                  openStudentWork('firefox-homework-lesson');
                }""")
                expect(student_page.locator('#modal')).to_contain_text("Pièces jointes du professeur")
                attachment_link = student_page.locator('#modal a[href*="/data/uploads/submissions/"]')
                expect(attachment_link).to_have_count(1)
                attachment_url = attachment_link.get_attribute("href")
                attachment_content = student_page.evaluate(
                    "async url => await (await fetch(url)).text()", attachment_url
                )
                if attachment_content != "Fichier de devoir de test":
                    raise AssertionError("Student cannot read teacher homework attachment: "+repr(attachment_content))
                student_page.evaluate("""() => { closeModal(); page='studentMessages'; appSpace='student'; render(); }""")
                mailbox = student_page.locator('.v2104App')
                expect(mailbox).to_be_visible()
                mailbox_state = student_page.evaluate("""() => ({
                  user:authUser,
                  page,
                  studentCount:db.students?.length,
                  classTeacherIds:db.classes?.[0]?.teacherIds,
                  teachers:db.teachers?.map(t=>t.id),
                  mailbox:db.mailboxV2,
                  body:document.body.innerText.slice(0,1200)
                })""")
                if mailbox.locator('.v2104Row').count() == 0:
                    raise AssertionError("Student mailbox has no message row: "+json.dumps(mailbox_state,ensure_ascii=False))
                expect(mailbox.locator('.v2104Row')).to_contain_text("Message de test élève")
                # End-to-end Mail V2: compose, save a draft, reload, resume, send and receive.
                teacher_page.evaluate("""() => {
                  page='messages';appSpace='teacher';window.mailV2Folder='inbox';
                  window.mailV2Selected='';render();window.mailV2104Compose('teacher','');
                }""")
                composer = teacher_page.locator('#modal .v2104Compose')
                expect(composer).to_be_visible()
                composer_layout = teacher_page.evaluate("""() => {
                  const modal=document.getElementById('modal');
                  const form=modal?.querySelector('.v2104Compose');
                  const rect=form?.getBoundingClientRect();
                  return {
                    viewportWidth:window.innerWidth,
                    modalClientWidth:modal?.clientWidth||0,
                    modalScrollWidth:modal?.scrollWidth||0,
                    formLeft:rect?.left||0,
                    formRight:rect?.right||0,
                    formWidth:rect?.width||0,
                    recipientPickerCount:form?.querySelectorAll('.v2104Recipients').length||0
                  };
                }""")
                if (
                    composer_layout["formWidth"] <= 0
                    or composer_layout["formLeft"] < 0
                    or composer_layout["formRight"] > composer_layout["viewportWidth"]
                    or composer_layout["modalScrollWidth"] > composer_layout["modalClientWidth"] + 1
                ):
                    raise AssertionError(
                        "La fenêtre de rédaction Mail déborde horizontalement : "+repr(composer_layout)
                    )
                screenshot_dir = Path("artifacts/browser-v25")
                screenshot_dir.mkdir(parents=True,exist_ok=True)
                for theme in ("light","dark"):
                    teacher_page.emulate_media(color_scheme="dark" if theme=="light" else "light")
                    teacher_page.evaluate("""theme => {
                      setAppearanceTheme(theme);
                      const toast=document.getElementById('toast');
                      if(toast){toast.classList.remove('show');toast.textContent='';}
                    }""",theme)
                    teacher_page.wait_for_timeout(140)
                    teacher_page.screenshot(
                        path=str(screenshot_dir/f"teacher-{theme}-mail-compose.png"),
                        full_page=True,animations="disabled"
                    )
                teacher_page.evaluate("""() => {
                  setAppearanceTheme('light');
                  const toast=document.getElementById('toast');
                  if(toast){toast.classList.remove('show');toast.textContent='';}
                }""")
                recipient = composer.locator('input[name="to"][value="student:firefox-student"]')
                if recipient.count() != 1:
                    people = teacher_page.evaluate("peopleOptions('teacher','')")
                    raise AssertionError(
                        "Le professeur ne peut pas sélectionner son élève dans la messagerie : "
                        + json.dumps(people,ensure_ascii=False)
                    )
                recipient.check()
                composer.locator('#v2104Subject').fill("Test de rédaction persistante")
                composer.locator('#v2104BodyEditor').fill("Message conservé après réouverture du brouillon.")
                composer.get_by_role("button",name="Enregistrer le brouillon").click()
                teacher_page.evaluate("""async () => {
                  await flushPendingSave();
                  await load();
                  page='messages';appSpace='teacher';window.mailV2Folder='drafts';
                  window.mailV2Selected='';render();
                }""")
                drafts = teacher_page.locator('.v2104Row')
                expect(drafts).to_have_count(1)
                expect(drafts.first).to_contain_text("Test de rédaction persistante")
                drafts.first.click()
                resumed = teacher_page.locator('#modal .v2104Compose')
                expect(resumed).to_be_visible()
                expect(resumed.locator('#v2104Subject')).to_have_value("Test de rédaction persistante")
                expect(resumed.locator('#v2104BodyEditor')).to_contain_text(
                    "Message conservé après réouverture du brouillon."
                )
                resumed.locator('#v2104BodyEditor').fill(
                    "Message envoyé depuis le brouillon repris."
                )
                teacher_page.evaluate("flushPendingSave()")
                mail_save_attempts = {"count": 0}
                def fail_first_mail_save(route):
                    if route.request.url.endswith("/api/save") and mail_save_attempts["count"] == 0:
                        mail_save_attempts["count"] += 1
                        route.fulfill(
                            status=503,
                            content_type="application/json",
                            body=json.dumps({"error":"Panne réseau simulée pendant l'envoi."})
                        )
                    else:
                        route.continue_()
                teacher_page.route("**/api/save",fail_first_mail_save)
                resumed.get_by_role("button",name="Envoyer").click()
                retry_send = resumed.locator('button[type="submit"]')
                expect(retry_send).to_have_text("Réessayer l’envoi",timeout=10_000)
                if mail_save_attempts["count"] != 1:
                    raise AssertionError("La panne réseau simulée n'a pas intercepté une seule sauvegarde.")
                # Retry the same pending message after removing the simulated outage.
                teacher_page.unroute("**/api/save",fail_first_mail_save)
                retry_send.click()
                expect(teacher_page.locator('#modalback')).not_to_have_class("open",timeout=10_000)
                teacher_page.evaluate("""async () => {
                  await flushPendingSave();
                  await load();
                  page='messages';appSpace='teacher';window.mailV2Folder='sent';
                  render();
                }""")
                sent_rows = teacher_page.locator('.v2104Row').filter(
                    has_text="Test de rédaction persistante"
                )
                expect(sent_rows).to_have_count(1)
                sent_rows.click()
                expect(teacher_page.locator('.v2104Thread')).to_contain_text(
                    "Message envoyé depuis le brouillon repris."
                )
                mail_delivery = teacher_page.evaluate("""() => ({
                  draftCount:db.mailboxV2.drafts.filter(d=>d.owner==='teacher:'+currentTeacherId()).length,
                  sent:db.mailboxV2.messages.filter(m=>
                    m.subject==='Test de rédaction persistante' &&
                    m.to.includes('student:firefox-student')
                  ).length
                })""")
                if mail_delivery["draftCount"] != 0 or mail_delivery["sent"] != 1:
                    raise AssertionError("État final du brouillon/envoi incorrect : "+repr(mail_delivery))
                student_page.evaluate("""async () => {
                  await load();
                  page='studentMessages';appSpace='student';window.mailV2Folder='inbox';
                  render();
                }""")
                student_mail_row = student_page.locator('.v2104Row').filter(
                    has_text="Test de rédaction persistante"
                )
                expect(student_mail_row).to_have_count(1)
                student_mail_row.click()
                expect(student_page.locator('.v2104Thread')).to_contain_text(
                    "Message envoyé depuis le brouillon repris."
                )
                student_page.evaluate("""() => {
                  closeModal();
                  page='studentSchedule';
                  appSpace='student';
                  selectedWeek=scheduleLocalDate('2026-11-09');
                  scheduleView='week';
                  render();
                }""")
                student_calendar = student_page.locator('.scheduleCalendarSurface')
                expect(student_calendar).to_contain_text("Français")
                student_course = student_page.locator('[data-schedule-id="firefox-existing-course"]')
                if "#123456" not in (student_course.get_attribute("style") or ""):
                    raise AssertionError("La couleur personnalisée de matière n'est pas transmise à l'EDT élève.")
                # Trace every student-side render while the other account changes the timetable.
                student_page.evaluate("""() => {
                  window.__studentRenderTrace=[];
                  window.__studentSyncTrace=[];
                  window.__studentTraceStartRevision=lastRenderedRevision;
                  window.__studentTraceStartDataRevision=dataRevision;
                  const originalRender=render;
                  render=function(){
                    window.__studentRenderTrace.push({
                      page,revision:dataRevision,
                      targetInDomBefore:!!document.querySelector('[data-schedule-id="firefox-live-student-course"]'),
                      targetInModel:(db.schedule||[]).some(x=>x.id==='firefox-live-student-course')
                    });
                    const result=originalRender.apply(this,arguments);
                    window.__studentRenderTrace[window.__studentRenderTrace.length-1].targetInDomAfter=
                      !!document.querySelector('[data-schedule-id="firefox-live-student-course"]');
                    return result;
                  };
                  const originalSync=refreshLiveScheduleData;
                  refreshLiveScheduleData=async function(force=false){
                    window.__studentSyncTrace.push({
                      stage:'start',force,revision:dataRevision,lastRenderedRevision,page,localWork:syncHasLocalWork(),
                      hidden:document.hidden
                    });
                    try{return await originalSync.call(this,force)}
                    finally{window.__studentSyncTrace.push({
                      stage:'end',revision:dataRevision,lastRenderedRevision,page,localWork:syncHasLocalWork(),
                      targetInModel:(db.schedule||[]).some(x=>x.id==='firefox-live-student-course'),
                      targetInDom:!!document.querySelector('[data-schedule-id="firefox-live-student-course"]')
                    })}
                  };
                }""")
                # A teacher-side write must be picked up by the student's 5-second sync.
                page.evaluate("""async () => {
                  const response = await fetch('/api/data', {cache:'no-store'});
                  const revision = response.headers.get('X-MaClasse-Revision');
                  const data = await response.json();
                  data.schedule.push({
                    id:'firefox-live-student-course',classId:'firefox-class',
                    day:4,time:'13:00',endTime:'14:00',subject:'Sciences',
                    recurrence:'weekly',startDate:'2026-11-09',endDate:'',
                    exceptions:[],overrides:{},teacherId:''
                  });
                  const saved = await fetch('/api/save', {
                    method:'POST',
                    headers:{'Content-Type':'application/json','If-Match':revision},
                    body:JSON.stringify(data)
                  });
                  if (!saved.ok) throw new Error('Teacher timetable update failed: '+saved.status+' '+await saved.text());
                }""")
                try:
                    expect(student_calendar).to_contain_text("Sciences", timeout=15_000)
                except AssertionError as failure:
                    state = student_page.evaluate("""async () => {
                      const [statusResponse,dataResponse] = await Promise.all([
                        fetch('/api/sync-status',{cache:'no-store'}),
                        fetch('/api/data',{cache:'no-store'})
                      ]);
                      const status = await statusResponse.json();
                      const latest = await dataResponse.json();
                      return {
                        documentHidden:document.hidden,
                        activeElement:document.activeElement?.outerHTML?.slice(0,500)||document.activeElement?.tagName,
                        page,authUser,
                        dataRevision,lastRenderedRevision,traceStartRevision:window.__studentTraceStartRevision,traceStartDataRevision:window.__studentTraceStartDataRevision,latestRevision:dataResponse.headers.get('X-MaClasse-Revision'),
                        statusRevision:status.revision,
                        liveSyncBusy,syncOnline,syncLastError,remoteChangePending,
                        savePending,saveTimer:!!saveTimer,saveError:saveError?.message||null,
                        hasLocalWork:syncHasLocalWork(),
                        localSchedule:(db.schedule||[]).map(x=>({id:x.id,subject:x.subject,day:x.day})),
                        serverSchedule:(latest.schedule||[]).map(x=>({id:x.id,subject:x.subject,day:x.day})),
                        selectedWeek:iso(selectedWeek),
                        student:student(activeStudent()),
                        targetSlot:(db.schedule||[]).find(x=>x.id==='firefox-live-student-course')||null,
                        targetDates:weekDates().map(d=>({
                          date:iso(d),
                          recurring:recurring((db.schedule||[]).find(x=>x.id==='firefox-live-student-course'),d),
                          dayOcc:dayOcc(d).filter(x=>x.id==='firefox-live-student-course').map(x=>({id:x.id,group:x.group,day:x.day})),
                          studentOcc:studentScheduleOcc(student(activeStudent()),d).filter(x=>x.id==='firefox-live-student-course').map(x=>({id:x.id,group:x.group,day:x.day}))
                        })),
                        scheduleView,
                        weekDates:weekDates().map(iso),
                        occFriday:studentScheduleOcc(student(activeStudent()),new Date('2026-11-13T12:00:00')).map(x=>({id:x.id,subject:x.subject})),
                        weekMarkup:studentSchedule().includes('Sciences'),
                        weekRendererMarkup:scheduleWeek(weekDates(),d=>studentScheduleOcc(student(activeStudent()),d),true).includes('Sciences'),
                        eventMarkup:eventCard((db.schedule||[]).find(x=>x.id==='firefox-live-student-course'),new Date('2026-11-13T12:00:00'),true),
                        targetDomCount:document.querySelectorAll('[data-schedule-id="firefox-live-student-course"]').length,
                        renderTrace:window.__studentRenderTrace||[],
                        syncTrace:window.__studentSyncTrace||[],
                        calendarHtml:document.querySelector('.scheduleCalendarSurface')?.innerHTML.slice(0,15000)||'',
                        calendar:document.querySelector('.scheduleCalendarSurface')?.innerText||''
                      };
                    }""")
                    raise AssertionError(
                        "Synchronisation élève : le créneau Sciences n'est pas apparu. "
                        + json.dumps(state,ensure_ascii=False)
                        + " | page errors=" + repr(student_page_errors)
                        + " | console errors=" + repr(student_console_errors)
                        + " | " + str(failure)
                    )
                teacher_page.evaluate("""() => {
                  page='schedule';
                  appSpace='teacher';
                  selectedWeek=scheduleLocalDate('2026-11-09');
                  scheduleView='week';
                  render();
                }""")
                teacher_calendar = teacher_page.locator('.scheduleCalendarSurface')
                expect(teacher_calendar).to_contain_text("Sciences")
                def layout_signature(target):
                    return target.evaluate("""root => {
                      const selectors=['.scheduleControlPanel','.scheduleCalendarSurface','.scheduleGrid','.scheduleDays','.daycol','.daycolHeader','.eventCard'];
                      return Object.fromEntries(selectors.map(selector=>{
                        const nodes=[...root.querySelectorAll(selector)];
                        const styles=nodes[0]?getComputedStyle(nodes[0]):null;
                        return [selector,{
                          count:nodes.length,
                          display:styles?.display||'',
                          columnCount:styles?.gridTemplateColumns&&styles.gridTemplateColumns!=='none'?styles.gridTemplateColumns.split(' ').length:0,
                          gap:styles?.gap||'',
                          borderRadius:styles?.borderRadius||'',
                          padding:styles?.padding||''
                        }];
                      }));
                    }""")
                teacher_layout=layout_signature(teacher_page.locator('body'))
                student_layout=layout_signature(student_page.locator('body'))
                for selector in teacher_layout:
                    left,right=teacher_layout[selector],student_layout[selector]
                    if left['count']!=right['count'] or left['display']!=right['display'] or left['columnCount']!=right['columnCount'] or left['gap']!=right['gap'] or left['borderRadius']!=right['borderRadius'] or left['padding']!=right['padding']:
                        raise AssertionError("EDT teacher/student visual structure differs at "+selector+": "+repr((left,right)))
                if student_page.locator('.schedulePage .eventEdit').count()!=0:
                    raise AssertionError("Student timetable unexpectedly exposes teacher edit controls")
                if student_page.locator('.schedulePage .eventEdit').count()!=0:
                    raise AssertionError("Student timetable unexpectedly exposes teacher edit controls")

                # Capture product screens only after representative module data and
                # the homework/Mail V2 end-to-end journeys have been exercised.
                capture_product_screenshots(
                    teacher_page,
                    "teacher",
                    ["dashboard","activity","schedule","lessons","students","evaluations","attendance","attendanceFollowup","bulletins","messages","documents","teachers","classes","ppDashboard","settings"],
                    Path("artifacts/browser-v25"),
                )
                capture_product_screenshots(
                    student_page,
                    "student",
                    ["studentHome","studentSchedule","studentLessons","studentWork","studentHomework","studentTodo","studentResults","studentMessages","studentLife","studentDocuments","studentSettings"],
                    Path("artifacts/browser-v25"),
                )
                if teacher_page_errors:
                    raise AssertionError("Teacher Firefox page errors after the individual-module visual pass: "+" | ".join(teacher_page_errors))
                if student_page_errors:
                    raise AssertionError("Student Firefox page errors after the individual-module visual pass: "+" | ".join(student_page_errors))
                teacher_context.close()
                student_context.close()

                # Return to the timetable after the Direction capture pass.
                # The final synchronization assertion below deliberately targets this page.
                page.evaluate("""() => {
                  page='schedule';
                  appSpace='teacher';
                  selectedWeek=scheduleLocalDate('2026-11-09');
                  scheduleView='week';
                  render();
                }""")
                expect(page.locator('[data-schedule-id="firefox-existing-course"]')).to_be_visible()

                # Force an unrelated server-side revision so the real-time refresh
                # runs while the timetable is open; this must not erase its courses.
                page.evaluate("""async () => {
                  const response = await fetch('/api/data', {cache:'no-store'});
                  const revision = response.headers.get('X-MaClasse-Revision');
                  const data = await response.json();
                  data.notifications = [...(data.notifications || []), {
                    id:'firefox-unrelated-update', type:'test', date:'2026-11-15'
                  }];
                  const saved = await fetch('/api/save', {
                    method:'POST',
                    headers:{'Content-Type':'application/json','If-Match':revision},
                    body:JSON.stringify(data)
                  });
                  if (!saved.ok) throw new Error('Unrelated revision update failed: '+saved.status);
                }""")
                page.wait_for_timeout(5500)
                expect(page.locator('[data-schedule-id="firefox-existing-course"]')).to_be_visible()
                expect(page.locator('[data-schedule-id]').filter(has_text="Histoire")).to_be_visible()

                # Exercise the actual Today action once more after a persisted write.
                page.locator("button.scheduleToday").click()
                expect(page.locator('[data-schedule-id="firefox-existing-course"]')).to_be_visible()
                expect(page.locator('[data-schedule-id]').filter(has_text="Histoire")).to_be_visible()

                if page_errors:
                    raise AssertionError("Firefox page errors: " + " | ".join(page_errors))
                print("OK — Firefox réel : Aujourd’hui, mois, navigation semaine, création, sauvegarde et persistance EDT.")

        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


if __name__ == "__main__":
    main()
