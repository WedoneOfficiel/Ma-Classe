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
    {id:1,name:'6A',level:'6e',levels:['6e'],teacherIds:['123'],principalTeacherId:'123',attendanceMode:'hour',groups:[]},
    {id:'2',name:'6B',level:'6e',levels:['6e'],teacherIds:['other'],principalTeacherId:'other',attendanceMode:'halfday',groups:[]}
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
  schedule:[{id:'slot-1',classId:'1',time:'09:00'}],
  teacherAssignments:[],
  evaluations:[{id:'e1',classId:1,subject:'Français',grades:[{studentId:'11',value:14}]}],
  attendance:[{id:'a1',classId:'1',rows:[{studentId:'11',status:'absent'}]}],
  lessons:[],
  bulletins:[],
  submissions:[],
  settings:{}
};
const context={
  db,
  authUser:{id:'123',role:'teacher'},
  CLASS_LEVELS:['6e','5e','4e'],
  sameId:(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
  iso:()=> '2026-11-26',
  teacherScheduleSuspended:()=>false,
  student:id=>db.students.find(s=>context.sameId(s.id,id)),
  cls:id=>db.classes.find(c=>context.sameId(c.id,id)),
  weightedAverageForEvaluations:(evaluations,ids)=>{
    assert.strictEqual(evaluations.length,1,'Le calcul doit inclure les évaluations avec un identifiant de classe mixte.');
    assert(ids.some(id=>context.sameId(id,'11')),'Les élèves ciblés doivent utiliser la même normalisation.');
    return '14.00';
  },
  v103MissingWorkList:()=>[
    {lesson:{id:'l1',classId:'1'},student:{id:'11'}},
    {lesson:{id:'l2',classId:'2'},student:{id:'22'}}
  ],
  esc:v=>String(v??''),
  jsArg:v=>JSON.stringify(v),
  shell:(section,title,description,actions='')=>section+' '+title+' '+description+' '+actions,
  countLabel:(n,s,p)=>String(n)+' '+(n===1?s:(p||s+'s')),
  teacherName:t=>[t.first,t.last].filter(Boolean).join(' '),
  classLevelLabel:c=>c.level||'Niveau non renseigné',
  openModal:(title,html)=>{context.lastModal={title,html}},
  toast:message=>{context.lastToast=message},
  closeModal:()=>{},
  render:()=>{},
  auditEvent:()=>{},
  reconcileStudentGroupsForClass:()=>{},
  save:()=>{context.saveCount++},
  flushPendingSave:async()=>{},
  api:async()=>db,
  normalize:()=>{},
  uid:()=>'new-class',
  saveCount:0,
  lastToast:''
};
context.formEntries=[];
context.FormData=class{constructor(){this.entries=context.formEntries}[Symbol.iterator](){return this.entries[Symbol.iterator]()}};
vm.createContext(context);
for(const name of [
  'currentTeacherProfile','teacherClassIds','teacherPPClasses','teacherClasses',
  'classTeachers','teacherAccount','teacherUser','teacherCanReachStudent',
  'ppClassStats','openUserEditor','openClass','saveClass','syncTeacherClassLinks','classes'
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
assert.strictEqual(stats.missing,1,'Le suivi PP ne doit compter que les rendus manquants de sa classe.');

const page=context.classes();
assert(page.includes('Mes classes principales')&&page.includes('Alice Martin'),
  'L’écran Classes doit afficher la classe PP même si le compte et la classe utilisent des types d’identifiants différents.');
assert(page.includes('1 élève'),
  'L’effectif de la classe doit être correct dans la liste générale.');
assert(page.includes('<small>EDT</small><b>1</b>')&&page.includes('<small>Évals</small><b>1</b>'),
  'Les compteurs EDT et évaluations de la classe doivent utiliser des identifiants normalisés.');

context.openClass('1');
assert(context.lastModal?.title==='Modifier la classe',
  'La fiche de classe doit se rouvrir avec l’identifiant texte équivalent.');
assert(context.lastModal.html.includes('value="123" selected'),
  'Le professeur principal doit rester sélectionné dans le formulaire.');
assert(context.lastModal.html.includes('name="teacherIds" value="123" checked'),
  'Les enseignants affectés doivent rester cochés dans le formulaire.');

const form={
  querySelectorAll(selector){
    if(selector==='input[name="levels"]:checked')return [{value:'6e'}];
    if(selector==='input[name="teacherIds"]:checked')return [{value:'123'}];
    if(selector==='input[name="ppIds"]:checked')return [];
    return [];
  }
};
context.formEntries=[
  ['name','6A'],
  ['attendanceMode','hour'],
  ['periodMode','trimestres'],
  ['principalTeacherId','123'],
  ['extraGroups','']
];
(async()=>{
  await context.saveClass({preventDefault(){},target:form},'1');
  assert.strictEqual(context.lastToast,'Classe modifiée et sauvegardée.',
    'La classe doit pouvoir être modifiée sans être confondue avec un doublon de son identifiant texte.');
  assert.strictEqual(db.classes[0].teacherIds.length,1,
    'Un professeur choisi et PP ne doit pas être ajouté deux fois à cause d’un identifiant numérique/texte.');
  assert.strictEqual(String(db.classes[0].teacherIds[0]),'123',
    'L’affectation du professeur doit rester enregistrée.');
  assert(db.teachers[0].classIds.some(id=>context.sameId(id,1)),
    'La synchronisation des affectations doit retrouver la classe avec un identifiant mixte.');
  console.log('OK — administration des classes : affichage PP, effectifs, EDT, évaluations, sélection et sauvegarde des affectations mixtes.');
})().catch(error=>{console.error(error);process.exitCode=1;});
