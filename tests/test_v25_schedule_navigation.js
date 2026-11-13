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
  {id:'class-a',classId:'class-1',group:'A',day:4,startDate:'2026-11-09',recurrence:'biweekly'},
  {id:'class-b',classId:'class-1',group:'B',day:4,startDate:'2026-11-09',recurrence:'biweekly'}
];
context.db.schedule = groupSlots;
assert.strictEqual(vm.runInContext("dayOcc(new Date('2026-11-13T12:00:00')).length", context), 2, 'Les groupes A et B doivent garder leur occurrence du premier vendredi.');
assert.strictEqual(vm.runInContext("dayOcc(new Date('2026-11-20T12:00:00')).length", context), 0, 'Les cours bimensuels ne doivent pas apparaître la semaine intermédiaire.');
assert.strictEqual(vm.runInContext("dayOcc(new Date('2026-11-27T12:00:00')).length", context), 2, 'Les cours bimensuels doivent réapparaître après deux semaines.');

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
context.eventCard = (item, date) => item.id+'@'+context.iso(date);
context.scheduleDay = (date, getOccurrences) => String(getOccurrences(date).length);
context.scheduleMonth = (date, getOccurrences) => String(getOccurrences(date).length);
vm.runInContext(source.slice(scheduleStart, scheduleEnd), context);
const weekRendererStart = source.indexOf('function scheduleWeek(');
const weekRendererEnd = source.indexOf('function scheduleDay(', weekRendererStart);
assert(weekRendererStart >= 0 && weekRendererEnd > weekRendererStart, 'Le vrai rendu hebdomadaire doit être présent.');
vm.runInContext(source.slice(weekRendererStart, weekRendererEnd), context);
vm.runInContext("scheduleView='week';selectedWeek=startWeek(new Date(2026,10,13,19,30))", context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-13'), 'Le cours doit apparaître le vendredi de la semaine initiale.');
vm.runInContext('changeWeek(7)', context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-20'), 'Le cours récurrent doit apparaître la semaine suivante.');
vm.runInContext('changeWeek(-7)', context);
assert(vm.runInContext('schedule()', context).includes('slot-1@2026-11-13'), 'Le cours doit réapparaître après le retour à la semaine initiale.');

const overlapStart = source.indexOf('function scheduleOverlap(');
const overlapEnd = source.indexOf('function scheduleConflicts(', overlapStart);
assert(overlapStart >= 0 && overlapEnd > overlapStart, 'Le contrôle des chevauchements doit être présent.');
vm.runInContext(source.slice(overlapStart, overlapEnd), context);
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:6,startDate:'2026-11-09',recurrence:'weekly'},{day:6,startDate:'2026-11-09',recurrence:'weekly'})", context), true, 'Les conflits du dimanche doivent être détectés.');
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:4,startDate:'2026-11-09',recurrence:'biweekly'},{day:4,startDate:'2026-11-16',recurrence:'biweekly'})", context), false, 'Deux récurrences bimensuelles décalées d’une semaine ne se chevauchent jamais.');
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:4,startDate:'2026-11-09',recurrence:'biweekly',exceptions:['2026-11-13']},{day:4,startDate:'2026-11-09',recurrence:'biweekly'})", context), true, 'Une exception ponctuelle ne doit pas masquer le chevauchement des occurrences suivantes.');
assert.strictEqual(vm.runInContext("scheduleDatesOverlap({day:4,startDate:'1900-01-01',recurrence:'biweekly'},{day:4,startDate:'1900-01-08',recurrence:'biweekly',endDate:'2999-12-31'})", context), false, 'Une longue période sans intersection doit être résolue par cycle, pas jour après jour.');

console.log('OK — navigation semaine aller/retour, bouton Aujourd’hui, dates locales, occurrences récurrentes et rendu du planning.');
