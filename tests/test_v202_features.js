const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync(path.join(__dirname, '..', '_all.js'), 'utf8');
function fn(name) {
  const start = source.lastIndexOf(`function ${name}(`);
  assert(start >= 0, `function ${name} exists`);
  const end = source.indexOf('\nfunction ', start + 1);
  return source.slice(start, end < 0 ? source.length : end).trim();
}
const db = {
  cloudItems: [{id:'hidden-parent',type:'folder',parentId:'',space:'personal'},{id:'shared-file',type:'file',name:'shared.pdf',parentId:'hidden-parent',space:'personal',shares:[{type:'teacher',id:'teacher-2'}]}],
  schedule: [
    {id:'a', classId:'c1', subject:'Français', teacherId:'t1', group:'', courseId:'c1|Français|t1|', color:'#112233'},
    {id:'b', classId:'c1', subject:'Français', teacherId:'t1', group:'', courseId:'c1|Français|t1|', color:'#112233'},
    {id:'c', classId:'c1', subject:'Français', teacherId:'t2', group:'', courseId:'c1|Français|t2|', color:'#445566'}
  ],
  evaluations: [
    {id:'e1',classId:'c1',subject:'Français',date:'2026-10-10',competencies:['Lire'],grades:[{studentId:'s1',competencyRatings:{Lire:4}}]},
    {id:'e2',classId:'c1',subject:'Français',date:'2027-02-10',competencies:['Lire'],grades:[{studentId:'s1',competencyRatings:{Lire:2}}]}
  ],
  settings:{terms:[{id:'t1',name:'T1',start:'2026-09-01',end:'2026-12-31'},{id:'t2',name:'T2',start:'2027-01-01',end:'2027-03-31'}]}
};
const window = {cloudSpace:'shared',cloudPath:[],cloudSearch:'',cloudSort:'name',cloudTypeFilter:'all'};
const ctx = {db, window, term:id=>db.settings.terms.find(t=>t.id===id), cls:id=>({name:id}), subjectColor:()=>['','','#123456'], cloudPathContextValid:()=>true, getCloudPath:()=>window.cloudPath, cloudAccessible:()=>db.cloudItems.filter(x=>x.id==='shared-file'), Object, Array, String, Number, Math, Set, Date, JSON};
vm.createContext(ctx);
vm.runInContext([fn('courseIdentity'),fn('competencySummaryForPeriod'),fn('cloudCurrentItems')].join('\n'),ctx);
assert.strictEqual(ctx.courseIdentity(db.schedule[0]),'c1|Français|t1|');
assert.notStrictEqual(ctx.courseIdentity(db.schedule[0]),ctx.courseIdentity(db.schedule[2]),'different regular teachers define different courses');
const t1 = ctx.competencySummaryForPeriod('c1','Français','t1');
assert.strictEqual(t1.length,1);
assert.strictEqual(t1[0].count,1);
assert.strictEqual(t1[0].average,'4.00');
const t2 = ctx.competencySummaryForPeriod('c1','Français','t2');
assert.strictEqual(t2[0].average,'2.00');
assert.ok(source.includes('Grilles & compétences'));
const sharedItems = ctx.cloudCurrentItems('teacher','teacher-2');
assert.strictEqual(sharedItems.length,1,'a directly shared file remains visible at the shared-space root even when its parent folder is not shared');
assert.strictEqual(sharedItems[0].id,'shared-file');
assert.ok(source.includes('function cloudSelectAll()'));
assert.ok(source.includes('function cloudMoveSelected()'));
assert.ok(source.includes('function notifications()'));
assert.ok(source.includes('function saveScheduleException('));
console.log('OK — cours distingués par professeur habituel, bilan filtré par période, notifications et actions Drive V20.2 présentes.');
