const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync('_all.js', 'utf8');
assert(!source.includes('$'+'{pat}'), 'Aucune interpolation de motif non définie ne doit subsister.');
assert(source.includes('function studentScheduleWeek(ds,occ){return scheduleWeek(ds,occ,true)}'));
assert(source.includes('function studentScheduleDay(d,occ){return scheduleDay(d,occ,true)}'));
assert(source.includes('window.setInterval(refreshLiveScheduleData,5000)'));
assert(source.includes('Le serveur n’a pas confirmé l’enregistrement'));
assert(source.includes('Le serveur n’a pas confirmé l’envoi du travail'));
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
  studentScheduleWeek: () => '<div id="student-week"></div>',
  studentScheduleDay: () => '<div id="student-day"></div>',
  studentScheduleMonth: () => '<div id="student-month"></div>',
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
assert(scheduleHtml.indexOf('</header>') < scheduleHtml.indexOf('<div class="toolbar">'));
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