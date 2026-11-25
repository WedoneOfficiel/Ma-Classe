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
                browser_errors: list[str] = []
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on("console", lambda message: browser_errors.append(message.text) if message.type == "error" else None)
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
                        levels:['6e'], teacherIds:[], groups:[],
                        attendanceMode:'hour', periodMode:'trimestres'
                      }];
                      data.students = [{id:'firefox-student',first:'Élève',last:'Test',classId:'firefox-class',group:''}];
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
                teacher_context = browser.new_context()
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
                # Product smoke pass: render each visible teacher module in the real browser.
                module_smoke = teacher_page.evaluate("""() => {
                  const modules=[
                    'dashboard','today','activity','notifications','schedule',
                    'lessons','students','evaluations','attendance',
                    'attendanceFollowup','bulletins','messages','documents',
                    'teachers','classes','settings'
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
                      viewport:window.innerWidth
                    });
                  }
                  return results;
                }""")
                broken_modules = [item for item in module_smoke if item["hasError"] or not item["hasTitle"]]
                if broken_modules:
                    raise AssertionError("Des modules professeur ne se rendent pas correctement : "
                                         + json.dumps(broken_modules,ensure_ascii=False))

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
                  save(true);
                  await flushPendingSave();
                  return lesson.homework.files[0];
                }""")
                if not uploaded_homework or not uploaded_homework.get("url"):
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
                student_context = browser.new_context()
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
                student_module_smoke = student_page.evaluate("""() => {
                  const modules=[
                    'studentHome','studentSchedule','studentLessons','studentWork',
                    'studentResults','studentLife','studentMessages','studentDocuments',
                    'studentSettings','activity'
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
                      viewport:window.innerWidth
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
                student_page.evaluate("page='studentHome';appSpace='student';render();")
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
                      stage:'start',force,revision:dataRevision,page,localWork:syncHasLocalWork(),
                      hidden:document.hidden
                    });
                    try{return await originalSync.call(this,force)}
                    finally{window.__studentSyncTrace.push({
                      stage:'end',revision:dataRevision,page,localWork:syncHasLocalWork(),
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
                        dataRevision,latestRevision:dataResponse.headers.get('X-MaClasse-Revision'),
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
                if student_page_errors:
                    raise AssertionError("Student Firefox page errors: "+" | ".join(student_page_errors))
                teacher_context.close()
                student_context.close()

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
