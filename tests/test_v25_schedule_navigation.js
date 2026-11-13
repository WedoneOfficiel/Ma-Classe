const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const source = fs.readFileSync('_all.js', 'utf8');
assert(source.includes("scheduleView='day';setScheduleDate('${iso(x)}')"), 'Les clics du calendrier mensuel doivent passer par le normalisateur local.');
assert(!source.includes("selectedWeek=new Date('${iso(x)}');scheduleView='day';render()"));
assert(source.includes("selectedWeek=startWeek(scheduleLocalDate('${iso(x)}'))"), 'Le mini-calendrier doit aussi utiliser la date locale.');
const start = source.indexOf('function monday(d)');
const end = source.indexOf('function lessonFor(', start);
assert(start >= 0 && end > start, 'Les helpers de calendrier doivent être présents.');

const context = {
  DAYS: ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
  selectedWeek: null,
  scheduleView: 'week',
  renderCount: 0,
  render() { this.renderCount += 1; },
  db: { schedule: [], classes: [] },
  iso(date) { const d = new Date(date); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); },
};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
const navStart = source.indexOf('function changeLessonMonth(', end);
const navEnd = source.indexOf('function openScheduleOccurrence(', navStart);
assert(navStart >= 0 && navEnd > navStart, 'Les commandes de navigation doivent être présentes.');
vm.runInContext(source.slice(navStart, navEnd), context);

const asISO = (date) => vm.runInContext('iso(selectedWeek)', context);
vm.runInContext("selectedWeek=startWeek(new Date(2026,10,13,19,30))", context);
assert.strictEqual(asISO(), '2026-11-09', 'La semaine doit commencer le lundi local.');
assert.deepStrictEqual(
  Array.from(vm.runInContext('weekDates().map(iso)', context)),
  ['2026-11-09','2026-11-10','2026-11-11','2026-11-12','2026-11-13','2026-11-14','2026-11-15']
);

vm.runInContext('changeWeek(7)', context);
assert.strictEqual(asISO(), '2026-11-16');
vm.runInContext('changeWeek(-7)', context);
assert.strictEqual(asISO(), '2026-11-09', 'Aller une semaine plus loin puis revenir doit restaurer la semaine initiale.');

vm.runInContext("setScheduleDate(new Date(2026,10,13,19,45))", context);
assert.strictEqual(asISO(), '2026-11-09', '« Aujourd’hui » doit conserver la bonne semaine, même avec une heure tardive.');

vm.runInContext("scheduleView='day';setScheduleDate('2026-11-13')", context);
assert.strictEqual(asISO(), '2026-11-13', 'Une date ISO doit être interprétée en date locale, pas en UTC.');

vm.runInContext("scheduleView='week';setScheduleDate('2026-11-13')", context);
assert.strictEqual(asISO(), '2026-11-09');

const weekdayStarts = ['2026-11-09','2026-11-10','2026-11-11','2026-11-12','2026-11-13','2026-11-14','2026-11-15'];
for (let day = 0; day < 7; day++) {
  const once = {id:'once-'+day,day,startDate:'2026-11-09',recurrence:'once'};
  assert.strictEqual(vm.runInContext('recurring('+JSON.stringify(once)+', new Date('+JSON.stringify(weekdayStarts[day]+'T12:00:00')+'))', context), true, 'Un cours ponctuel doit apparaître le '+weekdayStarts[day]);
  const fortnight = {id:'fortnight-'+day,day,startDate:'2026-11-09',recurrence:'biweekly'};
  assert.strictEqual(vm.runInContext('recurring('+JSON.stringify(fortnight)+', new Date('+JSON.stringify(weekdayStarts[day]+'T12:00:00')+'))', context), true, 'Un cours bimensuel doit apparaître dès sa première occurrence, jour '+day);
  const nextWeek = new Date(weekdayStarts[day]+'T12:00:00'); nextWeek.setDate(nextWeek.getDate()+7);
  assert.strictEqual(vm.runInContext('recurring('+JSON.stringify(fortnight)+', new Date('+JSON.stringify(nextWeek.toISOString().slice(0,10)+'T12:00:00')+'))', context), false, 'Un cours bimensuel ne doit pas apparaître la semaine intermédiaire, jour '+day);
  const secondOccurrence = new Date(weekdayStarts[day]+'T12:00:00'); secondOccurrence.setDate(secondOccurrence.getDate()+14);
  assert.strictEqual(vm.runInContext('recurring('+JSON.stringify(fortnight)+', new Date('+JSON.stringify(secondOccurrence.toISOString().slice(0,10)+'T12:00:00')+'))', context), true, 'Un cours bimensuel doit réapparaître après 14 jours, jour '+day);
}
const recurrenceCases = [
  { recurrence:'once', day:4, startDate:'2026-11-09', dates:['2026-11-13'] },
  { recurrence:'weekly', day:4, startDate:'2026-11-09', dates:['2026-11-13','2026-11-20','2026-11-27','2026-12-04','2026-12-11'] },
  { recurrence:'biweekly', day:4, startDate:'2026-11-09', dates:['2026-11-13','2026-11-27','2026-12-11'] },
  { recurrence:'triweekly', day:4, startDate:'2026-11-09', dates:['2026-11-13','2026-12-04'] },
  { recurrence:'custom', intervalWeeks:4, day:4, startDate:'2026-11-09', dates:['2026-11-13','2026-12-11'] },
  { recurrence:'once', day:2, startDate:'2026-11-13', dates:['2026-11-18'] },
];
for (const testCase of recurrenceCases) {
  const candidate = { id:'recurrence-'+testCase.recurrence, ...testCase };
  for (const date of ['2026-11-09','2026-11-13','2026-11-18','2026-11-20','2026-11-27','2026-12-04','2026-12-11']) {
    const expected = testCase.dates.includes(date);
    const actual = vm.runInContext('recurring('+JSON.stringify(candidate)+', new Date('+JSON.stringify(date+'T12:00:00')+'))', context);
    assert.strictEqual(actual, expected, testCase.recurrence+' / '+testCase.day+' / '+date);
  }
}
const groupSlots = [
  {id:'class-wide',classId:'class-1',group:'',day:4,startDate:'2026-11-09',recurrence:'biweekly',time:'09:00'},
  {id:'class-a',classId:'class-1',group:'A',day:4,startDate:'2026-11-09',recurrence:'biweekly',time:'10:00'},
  {id:'class-b',classId:'class-1',group:'B',day:4,startDate:'2026-11-09',recurrence:'biweekly',time:'11:00'}
];
context.db.schedule = groupSlots;
assert.strictEqual(vm.runInContext("dayOcc(new Date('2026-11-13T12:00:00')).length", context), 3, 'Les cours de classe et de groupes doivent garder leur première occurrence.');
const studentOccStart = source.indexOf('function studentScheduleOcc(');
const studentOccEnd = source.indexOf('function studentLessonItems(', studentOccStart);
assert(studentOccStart >= 0 && studentOccEnd > studentOccStart);
context.activeStudent = () => 'student-1';
context.student = id => ({id,classId:'class-1',group:'A'});
vm.runInContext(source.slice(studentOccStart, studentOccEnd), context);
assert.strictEqual(vm.runInContext("studentScheduleOcc(null,new Date('2026-11-13T12:00:00')).length", context), 2, 'L’élève du groupe A voit les cours de classe et de son groupe, pas ceux du groupe B.');
assert.strictEqual(vm.runInContext("dayOcc(new Date('2026-11-20T12:00:00')).length", context), 0, 'Les cours bimensuels ne doivent pas apparaître la semaine intermédiaire.');
assert.strictEqual(vm.runInContext("dayOcc(new Date('2026-11-27T12:00:00')).length", context), 3, 'Les cours bimensuels doivent réapparaître après deux semaines.');

const slot = { id:'slot-1', day:4, startDate:'2026-11-09', recurrence:'weekly', time:'09:00', endTime:'10:00' };
context.db.schedule = [slot];
assert.strictEqual(vm.runInContext("dayOcc(new Date(2026,10,13,12)).length", context), 1);
vm.runInContext('changeWeek(7)', context);
assert.strictEqual(vm.runInContext("dayOcc(new Date(2026,10,20,12)).length", context), 1);
vm.runInContext('changeWeek(-7)', context);
assert.strictEqual(vm.runInContext("dayOcc(new Date(2026,10,13,12)).length", context), 1);


const scheduleStart = source.indexOf('function schedule(){');
const scheduleEnd = source.indexOf('function scheduleWeek(', scheduleStart);
assert(scheduleStart >= 0 && scheduleEnd > scheduleStart, 'Le rendu du planning doit être présent.');
context.window = {};
context.shell = () => '';
context.esc = value => String(value ?? '');
context.subjectColor = () => ['#fff','#ddd','#000'];
context.time = value => String(value||'').slice(0,5);
context.cls = id => context.db.classes.find(x => x.id === id);
vm.runInContext(source.slice(scheduleStart, scheduleEnd), context);
const weekRendererStart = source.indexOf('function scheduleWeek(');
const dayRendererStart = source.indexOf('function scheduleDay(', weekRendererStart);
const monthRendererStart = source.indexOf('function scheduleMonth(', dayRendererStart);
const timeHelpersStart = source.indexOf('function mins(', monthRendererStart);
assert(weekRendererStart >= 0 && dayRendererStart > weekRendererStart && monthRendererStart > dayRendererStart && timeHelpersStart > monthRendererStart, 'Les trois rendus de calendrier doivent être présents.');
const subjectColorsStart = source.indexOf('const SUBJECT_COLORS', dayRendererStart);
assert(subjectColorsStart > dayRendererStart, 'Le rendu jour doit être isolé des helpers de cartes.');
vm.runInContext(source.slice(weekRendererStart, dayRendererStart), context);
vm.runInContext(source.slice(dayRendererStart, subjectColorsStart), context);
vm.runInContext(source.slice(monthRendererStart, timeHelpersStart), context);
const colorHelpersStart = source.indexOf('const SUBJECT_COLORS', dayRendererStart);
const dragHelpersStart = source.indexOf('function startScheduleDrag(', colorHelpersStart);
const minuteHelpersStart = timeHelpersStart;
const miniCalendarStart = source.indexOf('function miniCalendar(', minuteHelpersStart);
assert(colorHelpersStart > dayRendererStart && dragHelpersStart > colorHelpersStart && minuteHelpersStart === timeHelpersStart && miniCalendarStart > minuteHelpersStart, 'Les fonctions réelles des cartes de cours doivent être présentes.');
vm.runInContext(source.slice(colorHelpersStart, dragHelpersStart), context);
vm.runInContext(source.slice(minuteHelpersStart, miniCalendarStart), context);
vm.runInContext("scheduleView='week';selectedWeek=startWeek(new Date(2026,10,13,19,30))", context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-13'), 'Le cours doit apparaître le vendredi de la semaine initiale.');
vm.runInContext('changeWeek(7)', context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-20'), 'Le cours récurrent doit apparaître la semaine suivante.');
vm.runInContext('changeWeek(-7)', context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-13'), 'Le cours doit réapparaître après le retour à la semaine initiale.');

vm.runInContext("scheduleView='day';setScheduleDate('2026-11-13')", context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-13'), 'Le cours doit rester visible en passant à la vue jour.');
vm.runInContext("scheduleView='month';setScheduleDate('2026-11-13')", context);
assert(vm.runInContext('schedule()', context).includes('1 cours'), 'Le cours doit rester comptabilisé dans la vue mois.');
vm.runInContext("scheduleView='week';setScheduleDate('2026-11-13')", context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-13'), 'Le cours doit rester visible après le retour à la vue semaine.');
assert.strictEqual(vm.runInContext('db.schedule.length', context), 1, 'Changer de vue ou de période ne doit jamais vider les créneaux enregistrés.');

const studentScheduleStart = source.indexOf('function studentSchedule(){');
const studentScheduleEnd = source.indexOf('function openStudentLesson(', studentScheduleStart);
assert(studentScheduleStart >= 0 && studentScheduleEnd > studentScheduleStart, 'La page EDT élève doit être présente.');
context.studentClass = () => ({name:'Classe 1'});
context.subjectColor = () => ['#fff','#ddd','#000'];
context.esc = value => String(value ?? '');
context.shell = () => '';
vm.runInContext(source.slice(studentScheduleStart, studentScheduleEnd), context);
vm.runInContext("scheduleView='week';selectedWeek=startWeek(new Date(2026,10,13,19,30))", context);
assert(vm.runInContext('studentSchedule()', context).includes('2'), 'Les cours visibles par l’élève doivent être rendus en semaine.');
vm.runInContext("scheduleView='day';setScheduleDate('2026-11-13')", context);
assert(vm.runInContext('studentSchedule()', context).includes('2'), 'Les cours visibles par l’élève doivent rester rendus en jour.');
vm.runInContext("scheduleView='month';setScheduleDate('2026-11-13')", context);

assert(vm.runInContext('studentSchedule()', context).includes('2026-11-13'), 'La vue mois élève doit conserver les dates et les occurrences.');
const renderStart=source.indexOf('function render(){');
const shellStart=source.indexOf('function shell(',renderStart);
assert(renderStart>=0&&shellStart>renderStart,'Le routeur principal doit être présent.');
context.authGuard=()=>true;
context.nav=()=>{};
context.main={innerHTML:''};
context.document={getElementById:()=>context.main};
context.console={error:()=>{}};
context.shell=()=>'<div class="top"></div>';
context.window.messages=()=>'<div></div>';
context.window.studentMessages=()=>'<div></div>';
for(const name of ['dashboard','today','activity','notifications','teachersModule','lessons','studentsModule','evaluations','attendance','attendanceFollowup','bulletins','documents','classes','ppDashboard','settings','adminUsers','studentHome','studentResults','studentLife','studentDocuments'])context[name]=()=>'<div></div>';
vm.runInContext(source.slice(renderStart,shellStart),context);
context.page='schedule';
context.scheduleView='week';
context.render();
assert(context.main.innerHTML.includes('schedulePage')&&context.main.innerHTML.includes('data-schedule-id="slot-1"'),'Le routeur doit afficher le véritable EDT enseignant et ses créneaux.');
context.scheduleView='day';context.render();
assert(context.main.innerHTML.includes('data-schedule-id="slot-1"'),'Le routeur doit afficher le créneau en vue jour.');
context.scheduleView='month';context.render();
assert(context.main.innerHTML.includes('1 cours'),'Le routeur doit afficher le calendrier mensuel avec son cours.');
context.page='studentSchedule';
context.scheduleView='week';context.render();
assert(context.main.innerHTML.includes('data-schedule-id="slot-1"'),'Le routeur doit afficher les cours autorisés dans l’espace élève.');


const overlapStart = source.indexOf('function scheduleOverlap(');
const overlapEnd = source.indexOf('function scheduleConflicts(', overlapStart);
assert(overlapStart >= 0 && overlapEnd > overlapStart, 'Le contrôle des chevauchements doit être présent.');
vm.runInContext(source.slice(overlapStart, overlapEnd), context);
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:6,startDate:'2026-11-09',recurrence:'weekly'},{day:6,startDate:'2026-11-09',recurrence:'weekly'})", context), true, 'Les conflits du dimanche doivent être détectés.');
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:4,startDate:'2026-11-09',recurrence:'biweekly'},{day:4,startDate:'2026-11-16',recurrence:'biweekly'})", context), false, 'Deux récurrences bimensuelles décalées d’une semaine ne se chevauchent jamais.');
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:4,startDate:'2026-11-09',recurrence:'biweekly',exceptions:['2026-11-13']},{day:4,startDate:'2026-11-09',recurrence:'biweekly'})", context), true, 'Une exception ponctuelle ne doit pas masquer le chevauchement des occurrences suivantes.');
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:4,startDate:'1900-01-01',recurrence:'biweekly'},{day:4,startDate:'1900-01-08',recurrence:'biweekly',endDate:'2999-12-31'})", context), false, 'Une longue période sans intersection doit être résolue par cycle, pas jour après jour.');


(async()=>{
  const saveStart=source.indexOf('async function saveSchedule(e,id)');
  const saveEnd=source.indexOf('async function deleteSchedule(',saveStart);
  assert(saveStart>=0&&saveEnd>saveStart,'La sauvegarde du créneau doit être présente.');
  class FakeFormData{
    constructor(form){this.values=form.values}
    getAll(key){const v=this.values[key];return Array.isArray(v)?v:(v===undefined?[]:[v])}
    *[Symbol.iterator](){for(const [key,value] of Object.entries(this.values)){if(Array.isArray(value)){for(const item of value)yield [key,item]}else yield [key,value]}}
  }
  context.FormData=FakeFormData;
  context.uid=()=> 'created-slot';
  context.subjectColor=()=>['#fff','#ddd','#000'];
  context.time=value=>String(value||'').slice(0,5);
  context.addHour=value=>'10:00';
  context.save=()=>{};
  context.persistedSchedule=null;
  context.flushPendingSave=async()=>{context.persistedSchedule=JSON.parse(JSON.stringify(context.db))};
  context.api=async()=>JSON.parse(JSON.stringify(context.persistedSchedule));
  context.normalize=()=>{};
  context.closeModal=()=>{};
  context.toast=message=>{context.lastToast=message};
  context.render=()=>{context.renderCount++};
  context.db={schedule:[],classes:[{id:'class-1',name:'Classe 1'}],teachers:[],settings:{rooms:[]}};
  context.persistedSchedule=JSON.parse(JSON.stringify(context.db));
  vm.runInContext(source.slice(saveStart,saveEnd),context);
  const form={values:{day:'4',classIds:['class-1'],teacherId:'',time:'09:00',endTime:'10:00',subject:'Français',group:'',room:'',recurrence:'weekly',intervalWeeks:'1',startDate:'2026-11-09',endDate:'',exceptions:''}};
  context.form=form;
  await vm.runInContext("saveSchedule({preventDefault(){},target:form},'')",context);
  assert.strictEqual(context.db.schedule.length,1,'Un nouveau créneau doit rester présent après la sauvegarde et le rechargement serveur.');
  assert.strictEqual(context.db.schedule[0].subject,'Français');
  assert.strictEqual(context.lastToast,'Emploi du temps enregistré.');
})().catch(error=>{console.error(error);process.exitCode=1});

console.log('OK — navigation semaine aller/retour, bouton Aujourd’hui, dates locales, occurrences récurrentes et rendu du planning.');
