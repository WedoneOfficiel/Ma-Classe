const fs = require('fs');
const vm = require('vm');
const path = require('path');
const assert = require('assert');
const source = fs.readFileSync(process.argv[2] || path.join(__dirname, '..', '_all.js'), 'utf8');
function fn(name, next) {
  const start = source.indexOf(`function ${name}(`);
  assert(start >= 0, `function ${name} found`);
  const end = next ? source.indexOf(`function ${next}(`, start) : source.indexOf('\nfunction ', start + 1);
  assert(end > start, `end of ${name} found`);
  return source.slice(start, end).trim();
}
const db = {
  evaluationTemplates: [{ id: 'g1', name: 'Lecture', title: 'Compréhension', subject: 'Français', competencies: ['Comprendre un texte'] }],
  competencyLibrary: [],
  evaluations: [
    { id: 'e1', classId: 'c1', subject: 'Français', date: '2026-09-10', competencies: ['Comprendre un texte'], grades: [{ studentId: 's1', competencyRatings: { 'Comprendre un texte': '3' } }, { studentId: 's2', competencyRatings: { 'Comprendre un texte': '2' } }] },
    { id: 'e2', classId: 'c1', subject: 'Maths', date: '2026-09-11', competencies: ['Calculer'], grades: [{ studentId: 's1', competencyRatings: { Calculer: '4' } }] }
  ]
};
const els = {
  subject: { value: '' }, title: { value: '' }, competenciesText: { value: '' }
};
const ctx = {
  db, $, save() {}, toast() {}, uid: () => 'new-grid', manageEvaluationGrids() {},
  FormData: class { constructor(form) { this.form = form; } entries() { return Object.entries(this.form.values); } [Symbol.iterator]() { return this.entries()[Symbol.iterator](); } },
  student(id) { return ({s1:{first:'Alice',last:'Test'},s2:{first:'Bob',last:'Test'}})[id]; },
  esc(x) { return String(x ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); },
  confirmModal(_msg,_label,fn) { fn(); },
  Object, Array, String, Number, Math, Set, Date, JSON
};
function $(sel) { if (sel === '#modal') return { querySelector(q) { return els[q.match(/name="([^"]+)/)[1]]; } }; return null; }
ctx.$ = $;
vm.createContext(ctx);
vm.runInContext([fn('applyEvaluationTemplate','saveEvaluationTemplate'), fn('saveEvaluationTemplate','deleteEvaluationTemplate'), fn('deleteEvaluationTemplate','manageEvaluationGrids'), fn('competencySummary','openCompetencyReport')].join('\n'), ctx);
ctx.applyEvaluationTemplate('g1');
assert.strictEqual(els.subject.value, 'Français');
assert.strictEqual(els.title.value, 'Compréhension');
assert.strictEqual(els.competenciesText.value, 'Comprendre un texte');
const summary = ctx.competencySummary('c1', 'Français');
assert.strictEqual(summary.length, 1);
assert.strictEqual(summary[0].count, 2);
assert.strictEqual(summary[0].average, '2.50');
assert.strictEqual(ctx.competencySummary('c1', 'Maths')[0].name, 'Calculer');
ctx.saveEvaluationTemplate({preventDefault(){},target:{values:{name:'Grammaire',subject:'Français',title:'Accords',competenciesText:'Identifier le verbe\nAccorder le sujet et le verbe\nIdentifier le verbe'}}});
assert.strictEqual(db.evaluationTemplates.length, 2);
assert.deepStrictEqual(Array.from(db.evaluationTemplates[1].competencies), ['Identifier le verbe','Accorder le sujet et le verbe']);
assert.ok(db.competencyLibrary.includes('Accorder le sujet et le verbe'));
console.log('OK — modèles de grilles appliqués et synthèse des compétences calculée par classe/matière.');
