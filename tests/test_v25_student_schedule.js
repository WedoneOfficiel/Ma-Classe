const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync('_all.js', 'utf8');
assert(!source.includes('$'+'{pat}'), 'Aucune interpolation de motif non définie ne doit subsister.');
const eventContext={eventCard:(slot,date,isStudent)=>({slot,date,isStudent})};
vm.createContext(eventContext);
const studentCardStart=source.indexOf('function studentEventCard(');
const studentCardEnd=source.indexOf('\n',studentCardStart);
assert(studentCardStart>=0&&studentCardEnd>studentCardStart,'Le rendu d’un événement élève doit exister.');
vm.runInContext(source.slice(studentCardStart,studentCardEnd),eventContext);
const renderedStudentCard=vm.runInContext("studentEventCard({id:'slot-1'},'2026-11-16')",eventContext);
assert.strictEqual(renderedStudentCard.isStudent,true,'Le composant élève doit déléguer au rendu partagé en mode élève.');
assert(source.includes('function studentScheduleWeek(ds,occ){return scheduleWeek(ds,occ,true)}'));
assert(source.includes('function studentScheduleDay(d,occ){return scheduleDay(d,occ,true)}'));
assert(source.includes('window.setInterval(refreshLiveScheduleData,5000)'));
assert(source.includes('Le serveur n’a pas confirmé l’enregistrement'));
assert(source.includes('Le serveur n’a pas confirmé l’envoi du travail'));

assert(source.includes("${studentMode?'':`<button class=\"eventEdit\""), 'Le bouton de modification du créneau doit être absent du DOM élève.');
assert(source.includes("${studentMode?'':'ondragover=\"allowScheduleDrop(event)\""), 'Les zones de dépôt doivent être désactivées dans l’EDT élève.');
assert(source.includes('name="color" value="${esc(subjectColor(s.subject)[2])}"'), 'Le formulaire EDT doit proposer la couleur globale de la matière.');
assert(source.includes('db.settings.subjectColors??={}'), 'Les couleurs personnalisées doivent être stockées dans les paramètres.');
assert(source.includes("const c=subjectColor(o.subject), pattern=o.pattern||'none';"), 'Les créneaux doivent lire la couleur depuis la matière.');
assert(source.includes('db.schedule.filter(x=>subjectColorKey(x.subject)===subjectColorKey(o.subject)).forEach(x=>delete x.color)'), 'La sauvegarde doit supprimer les anciennes couleurs locales de la matière.');
assert(source.includes('La couleur est commune à une matière dans tout l’établissement'), 'Le gestionnaire doit expliquer la portée globale de la couleur.');

const colorStart = source.indexOf('const SUBJECT_COLORS=');
const colorEnd = source.indexOf('\nfunction eventCard', colorStart);
assert(colorStart >= 0 && colorEnd > colorStart);
const colorContext = { db: { settings: { subjectColors: { francais: '#123456' } } } };
vm.createContext(colorContext);
vm.runInContext(source.slice(colorStart, colorEnd), colorContext);
assert.strictEqual(vm.runInContext("subjectColor('Français')[2]", colorContext), '#123456');
assert.strictEqual(vm.runInContext("subjectColor(' francais  ')[2]", colorContext), '#123456',
  'La couleur doit être commune malgré les accents, la casse et les espaces.');
assert(source.includes('function refreshSchedulePage(){'), 'La sauvegarde doit disposer d’un rafraîchissement ciblé du calendrier.');
assert(source.includes("typeof document==='undefined'||typeof document.getElementById!=='function'"), 'Le rafraîchissement ciblé doit conserver un fallback dans les contextes sans DOM.');
assert(source.includes('current.replaceWith(next)'), 'La sauvegarde doit remplacer uniquement le calendrier, pas toute la page.');
assert(source.includes('closeModal();refreshSchedulePage();window.scrollTo(0,scrollTop)'), 'Après sauvegarde, le calendrier doit être actualisé sans recharger toute la vue.');
assert(source.includes("catch(err){db=JSON.parse(before);normalize();toast('Échec de sauvegarde : '+(err.message||'réessaie.'))}"), 'En cas d’échec, le formulaire reste ouvert pour permettre une correction ou une nouvelle tentative.');

const context = {
  activeStudent: () => 'student-1',
  student: id => ({id, first:'Alice', classId:'class-1'}),
  studentClass: () => ({name:'6A'}),
  studentScheduleOcc: () => [],
  weekDates: () => Array.from({length:7}, (_,i) => new Date(2026,10,9+i,12)),
  selectedWeek: new Date(2026,10,9,12),
  scheduleView: 'week',
  db: {schedule:[{classId:'class-1',subject:'Français'}]},
  subjectColor: () => ['#eee','#ddd','#333'],
  esc: value => String(value ?? ''),
  shell: (ey,title,sub,actions='') => '<header class="top"><div class="actions">'+actions+'</div></header>',
  scheduleWeek: () => '<div id="student-week"></div>',
  scheduleDay: () => '<div id="student-day"></div>',
  scheduleMonth: () => '<div id="student-month"></div>',
  studentLessonItems: () => [],
  lessonDay: '2026-11-13',
  lessonTab: 'done',
  miniCalendar: () => '<div id="calendar"></div>',
  studentLessonDayList: () => '<div id="lesson-list"></div>',
  studentLessonWorkList: () => '<div id="work-list"></div>',
  studentLessonUpcomingList: () => '<div id="upcoming-list"></div>',
  iso: d => { const x=new Date(d); return x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0'); }
};
vm.createContext(context);
let start = source.indexOf('function studentSchedule(){');
let end = source.indexOf('function studentScheduleWeek(', start);
assert(start >= 0 && end > start);
vm.runInContext(source.slice(start,end), context);
const scheduleHtml = vm.runInContext('studentSchedule()', context);
assert(scheduleHtml.indexOf('</header>') < scheduleHtml.indexOf('<section class="schedulePage"'));
assert(scheduleHtml.includes('scheduleControlPanel'));
assert(scheduleHtml.includes('scheduleCalendarSurface'));
assert(scheduleHtml.includes('student-week'));
start = source.indexOf('function studentLessons(){');
end = source.indexOf('function studentDocuments(', start);
assert(start >= 0 && end > start);
vm.runInContext(source.slice(start,end), context);
const lessonsHtml = vm.runInContext('studentLessons()', context);
assert(lessonsHtml.indexOf('</header>') < lessonsHtml.indexOf('<div class="lessonTopBar">'));
assert(lessonsHtml.includes('lessonTopBar'));
assert(lessonsHtml.includes('lessonWorkspace'));
start = source.indexOf('function studentScheduleShift(');
end = source.indexOf('function studentSchedule(){', start);
assert(start >= 0 && end > start);
let moved = [];
context.changeWeek = n => moved.push(['week',n]);
context.changeMonth = n => moved.push(['month',n]);
vm.runInContext(source.slice(start,end), context);
vm.runInContext("scheduleView='day';studentScheduleShift(1)", context);
vm.runInContext("scheduleView='week';studentScheduleShift(-1)", context);
vm.runInContext("scheduleView='month';studentScheduleShift(1)", context);
assert.deepStrictEqual(moved, [['week',1],['week',-7],['month',1]]);
console.log('OK — rendu élève, sept jours, navigation jour/semaine/mois, en-têtes et synchronisation.');+'{pat}'), 'Aucune interpolation de motif non définie ne doit subsister.');
const eventContext={eventCard:(slot,date,isStudent)=>({slot,date,isStudent})};
vm.createContext(eventContext);
const studentCardStart=source.indexOf('function studentEventCard(');
const studentCardEnd=source.indexOf('\\n',studentCardStart);
assert(studentCardStart>=0&&studentCardEnd>studentCardStart,'Le rendu d’un événement élève doit exister.');
vm.runInContext(source.slice(studentCardStart,studentCardEnd),eventContext);
const renderedStudentCard=vm.runInContext("studentEventCard({id:'slot-1'},'2026-11-16')",eventContext);
assert.strictEqual(renderedStudentCard.isStudent,true,'Le composant élève doit déléguer au rendu partagé en mode élève.');
assert(source.includes('function studentScheduleWeek(ds,occ){return scheduleWeek(ds,occ,true)}'));
assert(source.includes('function studentScheduleDay(d,occ){return scheduleDay(d,occ,true)}'));
assert(source.includes('window.setInterval(refreshLiveScheduleData,5000)'));
assert(source.includes('Le serveur n’a pas confirmé l’enregistrement'));
assert(source.includes('Le serveur n’a pas confirmé l’envoi du travail'));

assert(source.includes("${studentMode?'':`<button class=\"eventEdit\""), 'Le bouton de modification du créneau doit être absent du DOM élève.');
assert(source.includes("${studentMode?'':'ondragover=\"allowScheduleDrop(event)\""), 'Les zones de dépôt doivent être désactivées dans l’EDT élève.');
assert(source.includes('name="color" value="${esc(subjectColor(s.subject)[2])}"'), 'Le formulaire EDT doit proposer la couleur globale de la matière.');
assert(source.includes('db.settings.subjectColors??={}'), 'Les couleurs personnalisées doivent être stockées dans les paramètres.');
assert(source.includes("const c=subjectColor(o.subject), pattern=o.pattern||'none';"), 'Les créneaux doivent lire la couleur depuis la matière.');
assert(source.includes('db.schedule.filter(x=>subjectColorKey(x.subject)===subjectColorKey(o.subject)).forEach(x=>delete x.color)'), 'La sauvegarde doit supprimer les anciennes couleurs locales de la matière.');
assert(source.includes('La couleur est commune à une matière dans tout l’établissement'), 'Le gestionnaire doit expliquer la portée globale de la couleur.');

const colorStart = source.indexOf('const SUBJECT_COLORS=');
const colorEnd = source.indexOf('\nfunction eventCard', colorStart);
assert(colorStart >= 0 && colorEnd > colorStart);
const colorContext = { db: { settings: { subjectColors: { francais: '#123456' } } } };
vm.createContext(colorContext);
vm.runInContext(source.slice(colorStart, colorEnd), colorContext);
assert.strictEqual(vm.runInContext("subjectColor('Français')[2]", colorContext), '#123456');
assert.strictEqual(vm.runInContext("subjectColor(' francais  ')[2]", colorContext), '#123456',
  'La couleur doit être commune malgré les accents, la casse et les espaces.');
assert(source.includes('function refreshSchedulePage(){'), 'La sauvegarde doit disposer d’un rafraîchissement ciblé du calendrier.');
assert(source.includes("typeof document==='undefined'||typeof document.getElementById!=='function'"), 'Le rafraîchissement ciblé doit conserver un fallback dans les contextes sans DOM.');
assert(source.includes('current.replaceWith(next)'), 'La sauvegarde doit remplacer uniquement le calendrier, pas toute la page.');
assert(source.includes('closeModal();refreshSchedulePage();window.scrollTo(0,scrollTop)'), 'Après sauvegarde, le calendrier doit être actualisé sans recharger toute la vue.');
assert(source.includes("catch(err){db=JSON.parse(before);normalize();toast('Échec de sauvegarde : '+(err.message||'réessaie.'))}"), 'En cas d’échec, le formulaire reste ouvert pour permettre une correction ou une nouvelle tentative.');

const context = {
  activeStudent: () => 'student-1',
  student: id => ({id, first:'Alice', classId:'class-1'}),
  studentClass: () => ({name:'6A'}),
  studentScheduleOcc: () => [],
  weekDates: () => Array.from({length:7}, (_,i) => new Date(2026,10,9+i,12)),
  selectedWeek: new Date(2026,10,9,12),
  scheduleView: 'week',
  db: {schedule:[{classId:'class-1',subject:'Français'}]},
  subjectColor: () => ['#eee','#ddd','#333'],
  esc: value => String(value ?? ''),
  shell: (ey,title,sub,actions='') => '<header class="top"><div class="actions">'+actions+'</div></header>',
  scheduleWeek: () => '<div id="student-week"></div>',
  scheduleDay: () => '<div id="student-day"></div>',
  scheduleMonth: () => '<div id="student-month"></div>',
  studentLessonItems: () => [],
  lessonDay: '2026-11-13',
  lessonTab: 'done',
  miniCalendar: () => '<div id="calendar"></div>',
  studentLessonDayList: () => '<div id="lesson-list"></div>',
  studentLessonWorkList: () => '<div id="work-list"></div>',
  studentLessonUpcomingList: () => '<div id="upcoming-list"></div>',
  iso: d => { const x=new Date(d); return x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0'); }
};
vm.createContext(context);
let start = source.indexOf('function studentSchedule(){');
let end = source.indexOf('function studentScheduleWeek(', start);
assert(start >= 0 && end > start);
vm.runInContext(source.slice(start,end), context);
const scheduleHtml = vm.runInContext('studentSchedule()', context);
assert(scheduleHtml.indexOf('</header>') < scheduleHtml.indexOf('<section class="schedulePage"'));
assert(scheduleHtml.includes('scheduleControlPanel'));
assert(scheduleHtml.includes('scheduleCalendarSurface'));
assert(scheduleHtml.includes('student-week'));
start = source.indexOf('function studentLessons(){');
end = source.indexOf('function studentDocuments(', start);
assert(start >= 0 && end > start);
vm.runInContext(source.slice(start,end), context);
const lessonsHtml = vm.runInContext('studentLessons()', context);
assert(lessonsHtml.indexOf('</header>') < lessonsHtml.indexOf('<div class="lessonTopBar">'));
assert(lessonsHtml.includes('lessonTopBar'));
assert(lessonsHtml.includes('lessonWorkspace'));
start = source.indexOf('function studentScheduleShift(');
end = source.indexOf('function studentSchedule(){', start);
assert(start >= 0 && end > start);
let moved = [];
context.changeWeek = n => moved.push(['week',n]);
context.changeMonth = n => moved.push(['month',n]);
vm.runInContext(source.slice(start,end), context);
vm.runInContext("scheduleView='day';studentScheduleShift(1)", context);
vm.runInContext("scheduleView='week';studentScheduleShift(-1)", context);
vm.runInContext("scheduleView='month';studentScheduleShift(1)", context);
assert.deepStrictEqual(moved, [['week',1],['week',-7],['month',1]]);
console.log('OK — rendu élève, sept jours, navigation jour/semaine/mois, en-têtes et synchronisation.');