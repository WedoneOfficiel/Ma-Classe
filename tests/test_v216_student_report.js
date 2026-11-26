const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const js=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=js.indexOf('function studentReportToday');
const end=js.indexOf('function studentReportDetail',start);
assert(start>=0&&end>start,'V21.17 engine not found');
const engine=js.slice(start,end);
const ctx={
  console,
  Date,
  window:{},
  iso:d=>d instanceof Date?d.toISOString().slice(0,10):String(d),
  gradeNumber:v=>{if(v===''||v===null||v===undefined)return null;const n=typeof v==='string'?Number(v.trim().replace(',','.')):Number(v);return Number.isFinite(n)?n:null},
  v207EvaluationMax:e=>{const n=Number(e?.maxScore);return Number.isFinite(n)&&n>0?n:20}
};
vm.createContext(ctx);vm.runInContext(engine,ctx);
const db={settings:{terms:[
  {id:'t1',name:'Trimestre 1',start:'2026-09-01',end:'2026-12-31'},
  {id:'t2',name:'Trimestre 2',start:'2027-01-01',end:'2027-03-31'}
]},evaluations:[
  {id:'e1',title:'Contrôle fractions',subject:'Maths',date:'2026-10-10',published:true,maxScore:20,coefficient:1,grades:[{studentId:'s1',value:'14,5'}]},
  {id:'e2',title:'Interro vocabulaire',subject:'Français',date:'2026-11-05',published:true,maxScore:10,coefficient:2,grades:[{studentId:'s1',value:'8'}]},
  {id:'e3',title:'Brouillon',subject:'Maths',date:'2026-11-12',published:false,maxScore:20,grades:[{studentId:'s1',value:'20'}]},
  {id:'e4',title:'Future',subject:'Maths',date:'2026-12-01',published:true,publishAt:'2026-12-10',maxScore:20,grades:[{studentId:'s1',value:'20'}]},
  {id:'e5',title:'Projet oral',subject:'Français',date:'2026-10-20',published:true,maxScore:20,coefficient:1,criteria:[{id:'c1',name:'Expression',maxPoints:4,levels:[4,2,0],levelDetails:[]}],grades:[{studentId:'s1',value:'',criterionScores:{c1:4}}]},
  {id:'e6',title:'Autre élève',subject:'Maths',date:'2026-10-25',published:true,maxScore:20,grades:[{studentId:'s2',value:'20'}]},
  {id:'e7',title:'T2',subject:'Maths',date:'2027-01-10',published:true,maxScore:20,grades:[{studentId:'s1',value:'12'}]}
]};
let r=ctx.buildStudentReport(db,'s1','t1','2026-11-30');
assert.strictEqual(r.termId,'t1');
assert.strictEqual(r.subjects.length,2);
assert.strictEqual(r.counts.numeric,2);
assert.strictEqual(r.counts.qualitative,1);
const maths=r.subjects.find(x=>x.name==='Maths'),fr=r.subjects.find(x=>x.name==='Français');
assert.strictEqual(maths.items.length,1);
assert.strictEqual(maths.items[0].raw,14.5);
assert.strictEqual(maths.items[0].on20,14.5);
assert.strictEqual(fr.items.find(x=>x.evaluationId==='e2').on20,16);
assert.strictEqual(fr.average,16);
assert.strictEqual(r.overall,15.5);
assert.strictEqual(r.items.some(x=>x.evaluationId==='e3'),false,'unpublished evaluation must stay hidden');
assert.strictEqual(r.items.some(x=>x.evaluationId==='e4'),false,'future publication must stay hidden');
assert.strictEqual(r.items.some(x=>x.evaluationId==='e7'),false,'other term must stay out');
r=ctx.buildStudentReport(db,'s1','t1','2026-12-11');
assert.strictEqual(r.items.some(x=>x.evaluationId==='e4'),true,'publishedAt reached must be visible');
r=ctx.buildStudentReport(db,'s1','','2026-11-30');
assert.strictEqual(r.items.some(x=>x.evaluationId==='e7'),true,'all-period report includes all evaluations published by the requested date');
r=ctx.buildStudentReport(db,'s1','','2027-02-01');
assert.strictEqual(r.items.some(x=>x.evaluationId==='e7'),true);
assert.strictEqual(ctx.studentReportFormatAverage(null),'—');
assert.strictEqual(ctx.studentReportFormatAverage(14.5),'14.50');
console.log('OK — V21.17 moteur Student Report : périodes, publication, barèmes, coefficients, décimales FR et qualitatif.');

// Régression UI : les handlers inline doivent rester valides dans un attribut HTML.
const source=js;
assert(source.includes('studentReportDetail(${jsArg(item.evaluationId)},${jsArg(sid)})'),'detail handler must use HTML-safe serialized JS args');
assert(source.includes('setStudentResultsTerm(${jsArg(sid)},this.value)'),'term handler must use HTML-safe serialized JS args');
assert(source.includes('function studentReportDetail(evaluationId,sid)'), 'detail handler must receive evaluationId, not a report item');
console.log('OK — V21.17 handlers Résultats : détail des évaluations et changement de période.');

/* Cross-module consistency: timestamp precision and student class/group scope. */
const scopedDb = {
  students: [{id:'s1',classId:'c1',group:'A'}],
  settings:{terms:[{id:'t1',name:'T1',start:'2026-09-01',end:'2026-12-31'}]},
  evaluations:[
    {id:'before',classId:'c1',group:'A',subject:'Maths',date:'2026-11-20',published:true,publishAt:'2026-11-30T11:59:59Z',maxScore:20,grades:[{studentId:'s1',value:'12'}]},
    {id:'after',classId:'c1',group:'A',subject:'Maths',date:'2026-11-20',published:true,publishAt:'2026-11-30T12:00:01Z',maxScore:20,grades:[{studentId:'s1',value:'18'}]},
    {id:'other-group',classId:'c1',group:'B',subject:'Maths',date:'2026-11-20',published:true,maxScore:20,grades:[{studentId:'s1',value:'20'}]},
    {id:'other-class',classId:'c2',group:'A',subject:'Maths',date:'2026-11-20',published:true,maxScore:20,grades:[{studentId:'s1',value:'20'}]},
    {id:'missing-published',classId:'c1',group:'A',subject:'Maths',date:'2026-11-20',maxScore:20,grades:[{studentId:'s1',value:'20'}]},
    {id:'negative',classId:'c1',group:'A',subject:'Maths',date:'2026-11-20',published:true,maxScore:20,grades:[{studentId:'s1',value:'-1'}]},
    {id:'over-max',classId:'c1',group:'A',subject:'Maths',date:'2026-11-20',published:true,maxScore:20,grades:[{studentId:'s1',value:'21'}]}
  ]
};
let scoped=ctx.buildStudentReport(scopedDb,'s1','t1','2026-11-30T12:00:00Z');
assert.deepStrictEqual(Array.from(scoped.items, x=>x.evaluationId),['before'],
  'Exact as-of timestamp must include due grades and exclude future, other class/group, unpublished and invalid-score records');
const exactDate=vm.runInContext("new Date('2026-11-30T12:00:00Z')",ctx);
scoped=ctx.buildStudentReport(scopedDb,'s1','t1',exactDate);
assert.deepStrictEqual(Array.from(scoped.items, x=>x.evaluationId),['before'],
  'Date object as-of must preserve its exact instant');
assert.strictEqual(scoped.asOf,'2026-11-30T12:00:00.000Z',
  'Date object metadata must preserve the exact ISO instant');
scoped=ctx.buildStudentReport(scopedDb,'s1','t1','2026-11-30');
assert.deepStrictEqual(Array.from(scoped.items, x=>x.evaluationId),['before','after'],
  'Date-only as-of remains an end-of-day historical cutoff');
assert.strictEqual(scoped.asOf,'2026-11-30',
  'Explicit date-only as-of value remains stable for report metadata');
console.log('OK — Student Report : précision horaire, fuseaux, compatibilité dates seules et périmètre classe/groupe.');

