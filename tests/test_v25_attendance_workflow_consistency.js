const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
function section(startMarker,endMarker){
  const start=source.indexOf(startMarker),end=source.indexOf(endMarker,start);
  assert(start>=0&&end>start,'Section introuvable : '+startMarker);
  return source.slice(start,end);
}
function declaration(name){
  const start=source.lastIndexOf('function '+name+'(');
  assert(start>=0,'Fonction active absente : '+name);
  const end=source.indexOf('\nfunction ',start+10);
  return source.slice(start,end>=0?end:source.length);
}

const db={
  classes:[{id:1,name:'6A',attendanceMode:'hour'},{id:2,name:'6B',attendanceMode:'halfday'}],
  students:[
    {id:100,first:'Alice',last:'Martin',classId:1,group:'2'},
    {id:'200',first:'Bilal',last:'Durand',classId:'2',group:'A'}
  ],
  schedule:[{id:5,classId:'1',group:2,subject:'Mathématiques',time:'09:00',endTime:'10:00'}],
  attendance:[{
    id:9,classId:1,date:'2026-11-25',mode:'hour',slotId:'5',time:'09:00',
    rows:[{studentId:'100',status:'absent',justified:false,reason:'En attente'}]
  }]
};
const context={
  db,
  location:{search:'?class=1&student=100&status=all'},
  URLSearchParams,
  iso:()=> '2026-11-26',
  dayOcc:()=>[{id:5,classId:'1',group:2,subject:'Mathématiques',time:'09:00',endTime:'10:00'}],
  cls:id=>db.classes.find(c=>context.sameId(c.id,id)),
  student:id=>db.students.find(s=>context.sameId(s.id,id)),
  $:()=>null,
  esc:v=>String(v??''),
  fmtDate:v=>String(v??''),
  jsArg:v=>JSON.stringify(String(v??'')),
  time:v=>String(v??''),
  addHour:v=>v,
  openModal:(title,html)=>{context.lastModal={title,html}},
  shell:(section,title,description,actions='')=>'<header>'+section+' '+title+' '+description+'</header>'+actions,
  countLabel:(n,s,p)=>String(n)+' '+(n===1?s:(p||s+'s')),
  auditEvent:()=>{},
  save:()=>{context.saveCount++},
  closeModal:()=>{},
  render:()=>{},
  toast:message=>context.messages.push(message),
  uid:()=>'new-call',
  saveCount:0,
  messages:[],
  formDataEntries:[]
};
context.sameId=(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y};
context.FormData=class{constructor(){this.entries=context.formDataEntries}get(name){return this.entries.find(([key])=>key===name)?.[1]??null}[Symbol.iterator](){return this.entries[Symbol.iterator]()}};
vm.createContext(context);

vm.runInContext(
  section('function openAttendance(','function attendanceSetup(')+
  section('function attendanceSetup(','function bulletins(){')+
  declaration('attendanceSlotLabel')+
  declaration('attendanceSummaryForClass')+
  declaration('attendanceFollowup')+
  declaration('openAttendanceFollowup')+
  declaration('saveAttendanceFollowup'),
  context
);

assert.strictEqual(context.attendanceSlotLabel(db.attendance[0]),'09:00–10:00 · Mathématiques',
  'Le libellé de cours doit retrouver un créneau avec un identifiant numérique/texte équivalent.');

context.openAttendance('9');
assert(context.lastModal?.title==='Modifier l’appel'&&context.lastModal.html.includes('Alice'),
  'La réouverture d’un appel doit accepter un identifiant d’appel de type différent.');
assert(context.lastModal.html.includes('value="1" selected'),
  'La classe numérique doit rester sélectionnée dans le formulaire.');
assert(context.lastModal.html.includes('value="5" selected'),
  'Le créneau numérique doit rester sélectionné.');

const table=context.attendanceTable({classId:'1',date:'2026-11-25',mode:'hour',slotId:'5',rows:[{studentId:'100',status:'absent',justified:true,reason:'Certificat'}]});
assert(table.includes('MARTIN Alice')&&table.includes('on absent')&&table.includes('checked'),
  'La grille d’appel doit retrouver l’élève et son statut malgré les identifiants historiques mixtes.');

const summary=context.attendanceSummaryForClass('1');
assert.strictEqual(summary['100'].abs,1,'Le résumé doit compter l’absence malgré un ID élève stocké en texte.');
assert.strictEqual(summary['100'].late,0,'Aucun retard ne doit être compté avant sa saisie.');
assert.strictEqual(summary['100'].just,0,'Une absence non justifiée ne doit pas être comptée comme justifiée.');
db.attendance[0].rows.push({studentId:100,status:'retard',justified:false,reason:'5 minutes'});
const summaryWithLate=context.attendanceSummaryForClass('1');
assert.strictEqual(summaryWithLate['100'].abs,1,'Le nombre d’absences doit rester stable après ajout d’un retard.');
assert.strictEqual(summaryWithLate['100'].late,1,'Le résumé doit compter le retard sans dupliquer l’élève.');
assert.strictEqual(summaryWithLate['100'].just,0,'Le retard ne doit pas modifier le total des absences justifiées.');

context.openAttendanceFollowup('9','100');
assert(context.lastModal?.title==='Traiter une absence ou un retard'&&context.lastModal.html.includes('Alice Martin'),
  'L’ouverture du traitement doit retrouver l’appel et l’élève malgré les types d’identifiants différents.');

context.formDataEntries=[['status','absent'],['justified','true'],['reason','Certificat médical']];
context.saveAttendanceFollowup({preventDefault(){}},'9','100');
assert.strictEqual(db.attendance[0].rows[0].justified,true,
  'La justification doit être enregistrée sur la bonne ligne.');
assert.strictEqual(db.attendance[0].rows[0].reason,'Certificat médical',
  'Le motif doit être conservé.');
assert(db.attendance[0].rows[0].processedAt,
  'Le traitement doit être horodaté.');

context.formDataEntries=[['classId','1'],['date','2026-11-25'],['slotId','5'],['partOfDay','']];
context.getAttDraft()['100']={status:'retard',justified:false,reason:'Arrivée à 9h05'};
context.saveAttendance({preventDefault(){}},'9');
assert.strictEqual(db.attendance.length,1,'Modifier un appel existant ne doit pas créer un doublon.');
assert.strictEqual(db.attendance[0].rows.length,1,'Le filtrage doit conserver uniquement les élèves du cours et du groupe ciblé.');
assert.strictEqual(db.attendance[0].rows[0].studentId,100,
  'L’enregistrement doit mettre à jour l’élève correspondant même si son ancien identifiant était du texte.');
assert.strictEqual(db.attendance[0].rows[0].status,'retard',
  'Le statut choisi doit être sauvegardé.');
assert.strictEqual(db.attendance[0].rows[0].reason,'Arrivée à 9h05',
  'Le motif saisi dans la grille doit remplacer l’ancien motif.');
context.formDataEntries=[['status','retard'],['justified','true'],['reason','Retard traité']];
context.saveAttendanceFollowup({preventDefault(){}},'9','100');
const processedAt=db.attendance[0].rows[0].processedAt;
assert(processedAt,'Le traitement d’un retard doit aussi être horodaté.');
assert.strictEqual(db.attendance[0].rows[0].justified,false,
  'Un retard ne doit pas être marqué comme une absence justifiée.');

context.formDataEntries=[['classId','1'],['date','2026-11-25'],['slotId','5'],['partOfDay','']];
context.getAttDraft()['100']={status:'retard',justified:false,reason:'Retard traité'};
context.saveAttendance({preventDefault(){}},'9');
assert.strictEqual(db.attendance[0].rows[0].processedAt,processedAt,
  'Réenregistrer un appel sans changer le statut doit conserver l’horodatage de traitement.');
assert.strictEqual(context.saveCount,4,'Chaque enregistrement du cycle doit persister les changements.');

context.location.search='?class=1&student=100&status=pending';
const pending=context.attendanceFollowup();
assert(!pending.includes('<td><b>MARTIN Alice</b></td>'),
  'Un retard déjà traité doit sortir de la file « À traiter ».');
context.location.search='?class=1&student=100&status=late';
const late=context.attendanceFollowup();
assert(late.includes('<td><b>MARTIN Alice</b></td>')&&late.includes('Retard'),
  'Le filtre Retards doit conserver les événements déjà traités pour consultation.');

console.log('OK — cycle vie scolaire : appel, réouverture, ciblage classe/groupe, compteurs, justification et suivi avec identifiants mixtes.');
