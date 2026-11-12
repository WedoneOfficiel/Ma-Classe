const fs = require('fs');
const vm = require('vm');
const path = require('path');
const assert = require('assert');
const source = fs.readFileSync(process.argv[2] || path.join(__dirname, '..', '_all.js'), 'utf8');
function getFunction(name, nextName) {
  const start = source.indexOf(`function ${name}(`);
  assert(start >= 0, `function ${name} found`);
  const end = nextName ? source.indexOf(`function ${nextName}(`, start) : source.indexOf('function deleteEvaluation(', start);
  assert(end > start, `end of function ${name} found`);
  return source.slice(start, end).trim();
}
function getLine(name) { const line = source.split(/\r?\n/).find(x => x.startsWith(`function ${name}(`)); assert(line, `function ${name} found`); return line; }
const db = { evaluations: [{ id:'e1', classId:'c1', competencies:['Comprendre un texte'], grades:[{studentId:'s1', value:'15', comment:'Bien'}] }] };
const ctx = { db, save(){}, targetStudents(e){return [{id:'s1',first:'Alice',last:'Test',group:''}]}, esc:x=>String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'), evalAverage:()=> '15.00', gradeExtremes:()=>({min:'15.00',max:'15.00'}), JSON, String, Array, Object, Number, Math };
vm.createContext(ctx);
vm.runInContext([getFunction('setCompetencyRating','deleteEvaluation'), getLine('gradeTable')].join('\n'), ctx);
ctx.setCompetencyRating('e1','s1','Comprendre un texte','3');
assert.strictEqual(db.evaluations[0].grades[0].competencyRatings['Comprendre un texte'], '3');
assert.strictEqual(db.evaluations[0].grades[0].value, '15');
ctx.setCompetencyRating('e1','s1','Comprendre un texte','');
assert.ok(!('Comprendre un texte' in db.evaluations[0].grades[0].competencyRatings));
db.evaluations[0].grades[0].competencyRatings['Comprendre un texte']='4';
const html = ctx.gradeTable(db.evaluations[0]);
assert.ok(html.includes('Comprendre un texte'));
assert.ok(html.includes('Très bien maîtrisé'));
assert.ok(html.includes("setCompetencyRating('e1','s1'"));
console.log('OK — niveaux de compétence enregistrés, effaçables et affichés sans écraser les notes.');
