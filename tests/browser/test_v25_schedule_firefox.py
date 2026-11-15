#!/usr/bin/env python3
"""Real Firefox regression test for teacher timetable navigation and persistence.

The app is copied into a temporary directory so this test never touches the
checkout's data/ directory or any developer installation.
"""
from __future__ import annotations

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
                page = browser.new_page()
                page_errors: list[str] = []
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.goto(url, wait_until="networkidle")

                # Create a disposable administrator in the temporary app.
                expect(page.locator('input[name="first"]')).to_be_visible()
                page.locator('input[name="first"]').fill("Test")
                page.locator('input[name="last"]').fill("Firefox")
                page.locator('input[name="username"]').fill("firefox-test")
                page.locator('input[name="password"]').fill("Temporary-Test-Password-2026!")
                page.locator('input[name="confirm"]').fill("Temporary-Test-Password-2026!")
                page.get_by_role("button", name="Créer l’accès direction").click()
                expect(page.locator("#nav")).not_to_be_empty()

                # Seed one recurring course through the real authenticated API.
                await page.evaluate(
                    """async () => {
                      const response = await fetch('/api/data', {cache:'no-store'});
                      if (!response.ok) throw new Error('GET /api/data: '+response.status);
                      const revision = response.headers.get('X-MaClasse-Revision');
                      const data = await response.json();
                      data.classes = [{
                        id:'firefox-class', name:'6e A', level:'6e',
                        levels:['6e'], teacherIds:[], groups:[],
                        attendanceMode:'hour', periodMode:'trimestres'
                      }];
                      data.schedule = [{
                        id:'firefox-existing-course', classId:'firefox-class',
                        day:4, time:'09:00', endTime:'10:00',
                        subject:'Français', recurrence:'weekly',
                        startDate:'2026-11-09', endDate:'',
                        exceptions:[], overrides:{}, teacherId:'',
                        room:'', group:''
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
                expect(existing).to_be_visible()

                # Today, month, week navigation in both directions, then back.
                page.locator("button.scheduleToday").click()
                expect(existing).to_be_visible()

                page.locator(".scheduleViewSwitch").get_by_role("button", name="Mois").click()
                expect(page.locator(".scheduleMonthView")).to_be_visible()
                expect(page.locator(".scheduleMonthCount")).to_contain_text("cours")

                page.locator(".scheduleViewSwitch").get_by_role("button", name="Semaine").click()
                expect(existing).to_be_visible()
                nav_buttons = page.locator(".scheduleDateNav .scheduleIconBtn")
                nav_buttons.nth(1).click()
                expect(existing).to_be_visible()
                nav_buttons.nth(0).click()
                expect(existing).to_be_visible()

                # Create a second course through the actual modal and form.
                await page.evaluate("openSchedule()")
                form = page.locator("#modalback form")
                expect(form).to_be_visible()
                form.locator('[name="day"]').select_option("2")
                form.locator('[name="classIds"]').select_option("firefox-class")
                form.locator('[name="time"]').fill("11:00")
                form.locator('[name="endTime"]').fill("12:00")
                form.locator('[name="subject"]').fill("Histoire")
                form.locator('[name="recurrence"]').select_option("weekly")
                form.locator('[name="startDate"]').fill("2026-11-09")
                form.locator("button.primary").last.click()
                expect(page.locator("#toast")).to_contain_text(
                    "Emploi du temps enregistré.", timeout=10_000
                )
                expect(page.locator('[data-schedule-id="firefox-existing-course"]')).to_be_visible()
                expect(page.locator('[data-schedule-id]').filter(has=page.get_by_text("Histoire"))).to_be_visible()

                # Exercise the actual Today action once more after a persisted write.
                page.locator("button.scheduleToday").click()
                expect(page.locator('[data-schedule-id="firefox-existing-course"]')).to_be_visible()
                expect(page.locator('[data-schedule-id]').filter(has=page.get_by_text("Histoire"))).to_be_visible()

                if page_errors:
                    raise AssertionError("Firefox page errors: " + " | ".join(page_errors))
                print("OK — Firefox réel : Aujourd’hui, mois, navigation semaine, création, sauvegarde et persistance EDT.")

        finally:
            if browser:
                browser.close()
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


if __name__ == "__main__":
    main()
