const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
function declaration(name){
  const start=source.lastIndexOf('function '+name+'(');
  assert(start>=0,'Fonction active absente : '+name);
  const end=source.indexOf('\nfunction ',start+10);
  return source.slice(start,end>=0?end:source.length);
}
const db={
  classes:[
    {id:1,name:'6A',teacherIds:[123],principalTeacherId:123},
    {id:'2',name:'6B',teacherIds:['other'],principalTeacherId:'other'}
  ],
  teachers:[
    {id:123,first:'Alice',last:'Martin',classIds:[1],subjects:['Français']},
    {id:'other',first:'Bilal',last:'Durand',classIds:['2'],subjects:['Mathématiques']}
  ],
  users:[{id:123,role:'teacher',username:'alice',teacherId:123}],
  students:[
    {id:11,first:'Élève',last:'Test',classId:'1',group:'A'},
    {id:'22',first:'Autre',last:'Classe',classId:2,group:'B'}
  ],
  schedule:[],
  teacherAssignments:[],
  evaluations:[{id:'e1',classId:1,subject:'Français',grades:[{studentId:'11',value:14}]}],
  attendance:[{id:'a1',classId:'1',rows:[
    {studentId:'11',status:'absent'},
    {studentId:11,status:'retard'},
    {studentId:'22',status:'absent'}
  ]}],
  lessons:[],
  bulletins:[],
  submissions:[]
};
const context={
  db,
  authUser:{id:'123',role:'teacher'},
  sameId:(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
  iso:()=> '2026-11-26',
  teacherScheduleSuspended:()=>false,
  student:id=>db.students.find(s=>context.sameId(s.id,id)),
  weightedAverageForEvaluations:(evaluations,ids)=>{
    assert.strictEqual(evaluations.length,1,'Le calcul doit inclure les évaluations de la classe malgré les identifiants mixtes.');
    assert(ids.some(id=>context.sameId(id,'11')),'La liste d’élèves doit comprendre le bon identifiant.');
    return '14.00';
  },
  v103MissingWorkList:()=>[
    {lesson:{id:'l1',classId:'1'},student:{id:'11'}},
    {lesson:{id:'l2',classId:'2'},student:{id:'22'}}
  ],
  esc:v=>String(v??''),
  jsArg:v=>JSON.stringify(v),
  openModal:(title,html)=>{context.lastModal={title,html}}
};
vm.createContext(context);
for(const name of [
  'currentTeacherProfile','teacherClassIds','teacherPPClasses','teacherClasses',
  'classTeachers','teacherAccount','teacherUser','teacherCanReachStudent','ppClassStats','openUserEditor'
])vm.runInContext(declaration(name),context);

assert.strictEqual(context.currentTeacherProfile().first,'Alice',
  'Le compte canonique doit retrouver la fiche prof quand les identifiants sont de types différents.');
assert.deepStrictEqual(Array.from(context.teacherClassIds('123')),['1'],
  'Les classes affectées via teacherIds doivent être visibles avec une clé historique numérique.');
assert.deepStrictEqual(Array.from(context.teacherClasses('123'),x=>String(x.id)),['1'],
  'Le tableau des classes enseignées doit faire correspondre les classes numériques et textuelles.');
assert.deepStrictEqual(Array.from(context.teacherPPClasses('123'),x=>String(x.id)),['1'],
  'La classe de professeur principal doit rester accessible avec un identifiant mixte.');
assert.strictEqual(context.classTeachers({teacherIds:['123']})[0].first,'Alice',
  'Le nom du professeur doit être retrouvé dans la liste des co-enseignants.');
assert.strictEqual(context.teacherAccount('123').username,'alice',
  'La fiche compte doit retrouver le compte enseignant canonique.');
assert.strictEqual(context.teacherCanReachStudent('123','11'),true,
  'Le contrôle d’accès d’un élève doit normaliser les identifiants de classe.');
context.openUserEditor('123');
assert(context.lastModal?.title==='Modifier le compte et la fiche professeur',
  'Le formulaire de modification du compte doit être accessible.');
assert(context.lastModal.html.includes('name="classIds" value="1" checked'),
  'Ouvrir un compte professeur ne doit pas décocher ses classes si les identifiants sont mixtes.');
assert(context.lastModal.html.includes('name="ppIds" value="1" checked'),
  'Ouvrir un compte professeur ne doit pas décocher ses classes PP si les identifiants sont mixtes.');
const stats=context.ppClassStats({id:'1'});
assert.strictEqual(stats.students,1,'L’effectif PP doit compter les élèves de la classe.');
assert.strictEqual(stats.avg,'14.00','La moyenne PP doit inclure les évaluations de la classe.');
assert.strictEqual(stats.abs,1,'Le suivi PP doit compter l’absence malgré les identifiants mixtes.');
assert.strictEqual(stats.late,1,'Le suivi PP doit compter le retard sans le confondre avec l’absence.');
assert.strictEqual(stats.missing,1,'Le suivi PP ne doit compter que les rendus manquants de sa classe.');
console.log('OK — comptes enseignants, classes enseignées, PP et statistiques de classe avec identifiants historiques mixtes.');
