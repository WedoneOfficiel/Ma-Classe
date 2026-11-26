const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=source.lastIndexOf('function notificationFeed(');
const end=source.indexOf('\nfunction ',start+10);
assert(start>=0&&end>start,'La fonction active notificationFeed doit exister.');
const handler=source.slice(start,end);
const db={
  students:[{id:'7',first:'Alice',last:'Martin',classId:'1'}],
  lessons:[{id:101,classId:1,subject:'Français',homework:{title:'Rédaction',requiresSubmission:true,due:'2026-11-25'}}],
  submissions:[
    {id:'sent-1',lessonId:'101',studentId:7,status:'submitted',submittedAt:'2026-11-25T10:00:00Z'},
    {id:'draft-1',lessonId:101,studentId:'7',status:'draft',createdAt:'2026-11-25T09:00:00Z'},
    {id:'corrected-1',lessonId:101,studentId:'7',status:'submitted',submittedAt:'2026-11-24T10:00:00Z',corrected:true}
  ],
  evaluations:[],
  bulletins:[{id:'b1',studentId:7,published:true,publishedAt:'2026-11-25T12:00:00Z',termId:'T1',classId:1}],
  notifications:[{type:'bulletin',studentId:7,id:'b1:2026-11-25T12:00:00Z',read:false}],
  cloudItems:[{id:'f1',name:'Document partagé',createdAt:'2026-11-25T08:00:00Z',shares:[
    {type:'student',id:7},{type:'teacher',id:'123'}
  ]}]
};
const context={
  db,
  sameId:(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
  student:id=>db.students.find(s=>context.sameId(s.id,id)),
  currentTeacherProfile:()=>({id:123}),
  studentLessonsFor:()=>[],
  studentSubmitted:()=>null,
  iso:()=> '2026-11-26',
  term:()=>({name:'Trimestre 1'}),
  cls:()=>({name:'6A'}),
  notificationReadKey:n=>String(n.id),
};
vm.createContext(context);
vm.runInContext(handler,context);

const teacherFeed=context.notificationFeed('teacher');
const sent=teacherFeed.filter(x=>x.type==='submission');
assert.strictEqual(sent.length,1,
  'Le centre professeur doit proposer uniquement le vrai rendu non corrigé, pas le brouillon ni le rendu corrigé.');
assert.strictEqual(sent[0].id,'sent-1',
  'Le rendu doit être retrouvé malgré des identifiants de séance et d’élève de types différents.');
assert(sent[0].action?.type==='openWorkTracking',
  'La notification de rendu doit ouvrir le suivi du bon travail.');
assert(teacherFeed.some(x=>x.type==='cloud-share'&&x.id==='f1'),
  'Un partage destiné au compte professeur doit être visible malgré un identifiant mixte.');

const studentFeed=context.notificationFeed('student','7');
assert(studentFeed.some(x=>x.type==='bulletin'&&x.id==='b1:2026-11-25T12:00:00Z'),
  'La notification de bulletin doit retrouver le bon élève malgré les types d’identifiants différents.');
assert(studentFeed.some(x=>x.type==='cloud-share'&&x.id==='f1'),
  'Un document partagé avec un élève doit être visible malgré un identifiant mixte.');
console.log('OK — centre de notifications : rendus envoyés, bulletins et partages filtrés avec identifiants historiques mixtes.');
