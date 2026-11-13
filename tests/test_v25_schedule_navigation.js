const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const source = fs.readFileSync('_all.js', 'utf8');
const start = source.indexOf('function monday(d)');
const end = source.indexOf('function lessonFor(', start);
assert(start >= 0 && end > start, 'Les helpers de calendrier doivent être présents.');

const context = {
  DAYS: ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
  selectedWeek: null,
  scheduleView: 'week',
  renderCount: 0,
  render() { this.renderCount += 1; },
  db: { schedule: [] },
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

const slot = { id:'slot-1', day:4, startDate:'2026-11-09', recurrence:'weekly', time:'09:00', endTime:'10:00' };
context.db.schedule = [slot];
assert.strictEqual(vm.runInContext("dayOcc(new Date(2026,10,13,12)).length", context), 1);
vm.runInContext('changeWeek(7)', context);
assert.strictEqual(vm.runInContext("dayOcc(new Date(2026,10,20,12)).length", context), 1);
vm.runInContext('changeWeek(-7)', context);
assert.strictEqual(vm.runInContext("dayOcc(new Date(2026,10,13,12)).length", context), 1);

assert(context.renderCount >= 6, 'Chaque navigation doit déclencher un rendu.');
console.log('OK — navigation semaine aller/retour, bouton Aujourd’hui, dates locales et occurrences récurrentes.');
