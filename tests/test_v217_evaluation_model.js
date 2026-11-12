const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const js=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=js.indexOf('function evaluationModelMaxScore');
const end=js.indexOf('function weightedAverageForEvaluations',start);
assert(start>=0&&end>start,'V21.17 evaluation model not found');
const ctx={console,Number,gradeNumber:v=>{if(v===''||v===null||v===undefined)return null;const n=typeof v==='string'?Number(v.trim().replace(',','.')):Number(v);return Number.isFinite(n)?n:null}};
vm.createContext(ctx);vm.runInContext(js.slice(start,end),ctx);
const db={
 settings:{terms:[{id:'t1',name:'T1',start:'2026-09-01',end:'2026-12-31'},{id:'t2',name:'T2',start:'2027-01-01',end:'2027-03-31'}]},
 students:[{id:'s1',classId:'c1',group:'A'},{id:'s2',classId:'c1',group:'B'}],
 evaluations:[
  {id:'e1',classId:'c1',group:'A',subject:'Maths',title:'Contrôle',date:'2026-10-01',coefficient:2,maxScore:20,published:true,grades:[{studentId:'s1',value:'14,5'}]},
  {id:'e2',classId:'c1',subject:'Français',title:'Barème 10',date:'2026-10-10',coefficient:1,maxScore:10,published:true,grades:[{studentId:'s1',value:'8'}]},
  {id:'e3',classId:'c1',subject:'Maths',title:'Brouillon',date:'2026-10-15',published:false,grades:[{studentId:'s1',value:'20'}]},
  {id:'e4',classId:'c1',subject:'Maths',title:'Plus tard',date:'2026-11-01',published:true,publishAt:'2026-12-01',grades:[{studentId:'s1',value:'20'}]},
  {id:'e5',classId:'c1',subject:'Maths',title:'T2',date:'2027-01-05',published:true,grades:[{studentId:'s1',value:'10'}]},
  {id:'e6',classId:'c1',subject:'Maths',title:'Quali',date:'2026-10-20',published:true,competencies:['Lire'],criteria:[{id:'c',name:'Soin',levels:[2,1,0]}],grades:[{studentId:'s1',value:'',competencyRatings:{Lire:'3'},criterionScores:{c:2}}]}
 ]
};
let r=ctx.evaluationModelStudentReport(db,'s1','t1','2026-11-30');
assert.strictEqual(r.items.length,3);
assert.strictEqual(r.counts.numeric,2);
assert.strictEqual(r.counts.qualitative,1);
assert.strictEqual(r.subjects.find(x=>x.name==='Maths').items.find(x=>x.evaluationId==='e1').on20,14.5);
assert.strictEqual(r.subjects.find(x=>x.name==='Français').items[0].on20,16);
assert.strictEqual(r.items.some(x=>x.evaluationId==='e3'),false);
assert.strictEqual(r.items.some(x=>x.evaluationId==='e4'),false);
r=ctx.evaluationModelStudentReport(db,'s1','t1','2026-12-01');
assert.strictEqual(r.items.some(x=>x.evaluationId==='e4'),true);
r=ctx.evaluationModelStudentReport(db,'s1','t2','2027-02-01');
assert.strictEqual(r.items.length,1);
assert.strictEqual(r.items[0].evaluationId,'e5');
let out=ctx.evaluationModelSetGrade(db,'e1','s1','15,5');
assert.strictEqual(out.ok,true);assert.strictEqual(db.evaluations[0].grades[0].value,'15,5');
out=ctx.evaluationModelSetGrade(db,'e1','s1','99');assert.strictEqual(out.ok,false);assert.strictEqual(out.error,'invalid_grade');
out=ctx.evaluationModelSetCriterion(db,'e6','s1','c','2');assert.strictEqual(out.ok,true);
out=ctx.evaluationModelSetCompetency(db,'e6','s1','Lire','4');assert.strictEqual(out.ok,true);
out=ctx.evaluationModelSetCompetency(db,'e6','s1','Lire','5');assert.strictEqual(out.ok,false);
const stats=ctx.evaluationModelClassStats(db,'c1','','2026-11-30');assert.strictEqual(stats.evaluations,4);assert.strictEqual(stats.graded,3);
console.log('OK — V21.17 moteur Évaluations : périodes, publication, barèmes, coefficients, saisie notes, critères, compétences et statistiques.');

const ui=js.slice(js.lastIndexOf('/* V21.17 — interface Évaluations'));
assert(ui.includes('function evaluations(){'),'V21.17 evaluations UI missing');
assert(ui.includes('function openEvaluation(id=null){'),'V21.17 evaluation editor missing');
assert(ui.includes('function setGrade(eid,sid,v){'),'V21.17 grade setter missing');
assert(ui.includes('function setCriterionScore(eid,sid,cid,v){'),'V21.17 criterion setter missing');
assert(ui.includes('function setCompetencyRating(eid,sid,c,v){'),'V21.17 competency setter missing');
console.log('OK — V21.17 interface Évaluations branchée sur le moteur central.');
