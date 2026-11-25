const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('class_tracking.js','utf8');
const start=source.indexOf('function classTrackingClasses(){');
const end=source.indexOf('function openClassTracking',start);
assert(start>=0&&end>start,'Les fonctions de données du suivi de classe doivent exister');
const fixed=new Date('2026-11-25T12:00:00');
const db={
 classes:[{id:'c1',name:'6e A'},{id:'c2',name:'5e B'},{id:'c3',name:'4e C'}],
 students:[{id:'s1',classId:'c1',first:'Alice',last:'Martin',group:'A'},{id:'s2',classId:'c1',first:'Bilal',last:'Durand',group:'B'},{id:'s3',classId:'c2',first:'Chloé',last:'Petit'}],
 attendance:[
  {id:'a1',classId:'c1',date:'2026-11-24',rows:[{studentId:'s1',status:'absent'},{studentId:'s2',status:'retard'}]},
  {id:'a2',classId:'c1',date:'2026-10-20',rows:[{studentId:'s1',status:'absent'}]},
  {id:'a3',classId:'c1',date:'2026-11-26',rows:[{studentId:'s1',status:'absent'}]},
  {id:'a4',classId:'c2',date:'2026-11-24',rows:[{studentId:'s3',status:'absent'}]}
 ],
 lessons:[
  {id:'l1',classId:'c1',group:'A',subject:'Français',homework:{requiresSubmission:true,due:'2026-11-20',title:'Rédaction'}},
  {id:'l2',classId:'c1',group:'B',subject:'Maths',homework:{requiresSubmission:true,due:'2026-11-20',title:'Exercices'}},
  {id:'l3',classId:'c1',subject:'Histoire',homework:{requiresSubmission:true,due:'2026-12-01',title:'Exposé'}},
  {id:'l4',classId:'c2',subject:'Sciences',homework:{requiresSubmission:true,due:'2026-11-20',title:'Compte rendu'}}
 ],
 submissions:[{lessonId:'l1',studentId:'s1',status:'submitted'}],
 evaluations:[
  {id:'e1',classId:'c1',date:'2026-11-18',published:true,grades:[{studentId:'s1',value:'15'},{studentId:'s2',value:'12'}]},
  {id:'e2',classId:'c1',date:'2026-11-19',published:false,grades:[{studentId:'s1',value:'18'}]},
  {id:'e3',classId:'c1',date:'2026-12-01',published:true,grades:[{studentId:'s1',value:'19'}]},
  {id:'e4',classId:'c2',date:'2026-11-18',published:true,grades:[{studentId:'s3',value:'14'}]},
  {id:'e5',classId:'c1',group:'A',date:'2026-11-17',published:true,grades:[{studentId:'s1',value:'16'},{studentId:'s2',value:'11'}]}
 ]
};
const context={db,authUser:{role:'admin'},window:{},currentTeacherProfile:()=>({id:'t1'}),teacherClasses:()=>[db.classes[0]],teacherPPClasses:()=>[db.classes[1]],iso:d=>{const x=new Date(d);return x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0')},studentSubmitted:(l,id)=>db.submissions.some(x=>x.lessonId===l.id&&x.studentId===id&&(x.status==='submitted'||!!x.submittedAt)),evaluationModelPublished:(e,today)=>!e.publishAt||e.publishAt<=today};
vm.createContext(context);
vm.runInContext(source.slice(start,end),context);
assert.deepStrictEqual(Array.from(context.classTrackingClasses(),x=>x.id),['c3','c2','c1'],'La Direction doit voir toutes les classes.');
context.authUser={role:'teacher',id:'t1'};
assert.deepStrictEqual(Array.from(context.classTrackingClasses(),x=>x.id),['c2','c1'],'Un professeur ne voit que ses classes enseignées ou dont il est PP.');
assert.strictEqual(context.classTrackingData('c3',fixed),null,'Un professeur ne doit pas pouvoir ouvrir une classe non attribuée.');
context.authUser={role:'student',id:'s1'};
assert.strictEqual(context.classTrackingClasses().length,0,'Un élève ne doit pas accéder au suivi de classe.');
assert.strictEqual(context.classTrackingData('c1',fixed),null,'Un élève ne doit pas pouvoir lire les données du suivi de classe.');
context.authUser={role:'admin'};
const data=context.classTrackingData('c1',fixed);
assert.strictEqual(data.stats.students,2);
assert.strictEqual(data.stats.absent,1,'Les absences doivent être limitées aux 30 derniers jours.');
assert.strictEqual(data.stats.late,1);
assert.strictEqual(data.stats.missing,1,'Le devoir de groupe A est rendu et celui du groupe B reste manquant.');
assert.strictEqual(data.missingWorks[0].student.id,'s2');
assert.strictEqual(data.stats.upcoming,1,'Seules les échéances futures doivent être retenues.');
assert.strictEqual(data.recentEvaluations.length,2,'Les évaluations non publiées et futures doivent être exclues.');
assert.strictEqual(data.recentEvaluations[0].gradedCount,2);
assert.strictEqual(data.recentEvaluations[1].gradedCount,1,'Une évaluation de groupe ne doit compter que les élèves de ce groupe.');
assert.strictEqual(data.students.find(x=>x.student.id==='s1').absent,1);
assert.strictEqual(data.students.find(x=>x.student.id==='s2').missing,1);
assert.strictEqual(context.classTrackingData('c3',fixed).students.length,0);
console.log('OK — suivi de classe : permissions, fenêtre de 30 jours, groupes, travaux rendus, échéances et publication des évaluations.');
