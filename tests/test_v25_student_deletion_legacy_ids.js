const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=source.lastIndexOf('function deleteStudent(');
const end=source.indexOf('\nfunction openImportStudents(',start);
assert(start>=0&&end>start,'La fonction active de suppression élève doit exister.');
const handler=source.slice(start,end);

const db={
  students:[{id:7,first:'Alice',last:'Martin'},{id:'8',first:'Bilal',last:'Durand'}],
  evaluations:[{id:'eval-1',grades:[
    {studentId:'7',value:'14'},
    {studentId:8,value:'12'}
  ]}],
  attendance:[{id:'call-1',rows:[
    {studentId:7,status:'absent'},
    {studentId:'8',status:'retard'}
  ]}],
  submissions:[
    {id:'sub-1',studentId:'7',status:'submitted'},
    {id:'sub-2',studentId:8,status:'draft'}
  ]
};
const context={
  db,
  sameId:(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
  confirmModal:(title,label,callback)=>{context.confirmation={title,label,callback}},
  save:()=>{context.saveCount++},
  closeModal:()=>{context.closed++},
  render:()=>{context.rendered++},
  saveCount:0,
  closed:0,
  rendered:0
};
vm.createContext(context);
vm.runInContext(handler,context);
context.deleteStudent(7);
assert(context.confirmation?.title.includes('Supprimer définitivement'),
  'La suppression doit demander une confirmation explicite.');
assert.strictEqual(db.students.length,2,
  'Aucune donnée ne doit être effacée avant la confirmation.');
context.confirmation.callback();
assert.strictEqual(db.students.length,1,
  'La fiche élève doit être supprimée même si son identifiant est stocké sous forme numérique.');
assert.strictEqual(String(db.students[0].id),'8',
  'Les autres élèves doivent être conservés.');
assert.strictEqual(db.evaluations[0].grades.length,1,
  'Les notes liées à l’identifiant texte équivalent doivent être supprimées.');
assert.strictEqual(String(db.evaluations[0].grades[0].studentId),'8',
  'Les notes des autres élèves doivent être conservées.');
assert.strictEqual(db.attendance[0].rows.length,1,
  'Les lignes d’appel liées à l’identifiant texte équivalent doivent être supprimées.');
assert.strictEqual(String(db.attendance[0].rows[0].studentId),'8',
  'Les autres lignes d’appel doivent être conservées.');
assert.strictEqual(db.submissions.length,1,
  'Les rendus et brouillons liés à l’identifiant texte équivalent doivent être supprimés.');
assert.strictEqual(String(db.submissions[0].studentId),'8',
  'Les soumissions des autres élèves doivent être conservées.');
assert.strictEqual(context.saveCount,1,'La suppression confirmée doit persister une seule fois.');
assert.strictEqual(context.closed,1,'La fenêtre de confirmation doit être fermée après suppression.');
assert.strictEqual(context.rendered,1,'La liste doit être rafraîchie après suppression.');
console.log('OK — suppression élève : nettoyage des notes, appels et rendus avec identifiants numériques/texte mixtes.');
