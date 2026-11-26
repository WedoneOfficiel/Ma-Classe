const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
function section(startMarker,endMarker){
  const start=source.indexOf(startMarker),end=source.indexOf(endMarker,start);
  assert(start>=0&&end>start,'Section introuvable : '+startMarker);
  return source.slice(start,end);
}
const db={
  evaluations:[],
  attendance:[],
  classes:[{id:'1',name:'6A'}],
  students:[
    {id:'s1',first:'Alice',last:'Martin',classId:1,group:'A'},
    {id:2,first:'Bilal',last:'Durand',classId:'1',group:'A'},
    {id:'s3',first:'Chloé',last:'Petit',classId:'1',group:'B'},
    {id:'4',first:'Dina',last:'Moreau',classId:1,group:'B'},
    {id:'s5',first:'Emma',last:'Robert',classId:'1',group:'B'}
  ],
  lessons:[
    {id:101,classId:'1',group:'A',date:'2026-11-13',subject:'Français',homework:{title:'Rédaction',requiresSubmission:true,due:'2026-11-20'}},
    {id:'102',classId:1,group:'B',date:'2026-11-13',subject:'Maths',homework:{title:'Exercices',requiresSubmission:true,due:'2026-11-20'}},
    {id:'103',classId:'1',group:'A',date:'2026-11-20',subject:'Histoire',homework:{title:'Exposé',requiresSubmission:true,due:'2026-11-26'}},
    {id:'104',classId:'1',group:'A',date:'2026-11-25',subject:'Sciences',homework:{title:'Recherche',requiresSubmission:true,due:'2026-12-01'}}
  ],
  schedule:[{id:7,classId:'1',group:'A'}],
  submissions:[
    {id:'sub-1',lessonId:'101',studentId:'s1',status:'submitted',submittedAt:'2026-11-19T10:00:00Z',files:[{name:'alice.pdf',url:'/data/uploads/alice.pdf'}]},
    {id:'sub-2',lessonId:101,studentId:'2',status:'draft',files:[{name:'brouillon.pdf',url:'/data/uploads/brouillon.pdf'}]},
    {id:'sub-3',lessonId:102,studentId:'s3',status:'submitted',submittedAt:'2026-11-19T11:00:00Z',corrected:true,files:[{name:'chloe.pdf',url:'/data/uploads/chloe.pdf'}]},
    {id:'sub-4',lessonId:'102',studentId:4,status:'submitted',corrected:false,files:[{name:'dina.pdf',url:'/data/uploads/dina.pdf'}]}
  ]
};
const context={
  db,
  sameId:(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
  iso:d=>{const x=new Date(d);return x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0')},
  student:id=>db.students.find(s=>context.sameId(s.id,id)),
  activeStudent:()=> 's1',
  v10MissingGrades:()=>[],
  v10Upcoming:()=>[],
  esc:v=>String(v??''),
  fmtDate:v=>String(v??'—'),
  countLabel:(n,s,p)=>String(n)+' '+(n===1?s:(p||s+'s')),
  jsArg:v=>JSON.stringify(String(v??'')),
  safeUploadUrl:v=>v,
  submissionFiles:sub=>Array.isArray(sub?.files)?sub.files:(sub?.file?[sub.file]:[]),
  openModal:(title,html)=>{context.lastModal={title,html}},
  lessonFor:()=>db.lessons.find(l=>context.sameId(l.id,101))
};
vm.createContext(context);
vm.runInContext(section('function submissionIsSubmitted(','function evaluationGradeLabel('),context);
vm.runInContext(section('function submissionFiles(','function studentWorkEligible('),context);
vm.runInContext(section('function studentWorkEligible(','async function deleteUploadedFile('),context);
vm.runInContext(section('function v103MissingWorkList(','function v103ActionCenter('),context);
vm.runInContext(section('function activityData(){','function activity(){'),context);
vm.runInContext(section('function openWorkTracking(','function renderCommand('),context);
vm.runInContext(section('function showSubmissions(','function lessons(){'),context);

(async()=>{
  const missing=context.v103MissingWorkList(new Date('2026-11-26T12:00:00'));
  const keys=missing.map(x=>String(x.lesson.id)+':'+String(x.student.id)).sort();
  assert.deepStrictEqual(keys,['101:2','102:s5'],
    'Seuls les devoirs dont la date est passée et sans véritable envoi doivent être manquants ; les brouillons, échéances du jour et échéances futures doivent être traités correctement.');

  assert.strictEqual(context.studentSubmitted(db.lessons[1],4)?.id,'sub-4',
    'Un statut submitted suffit même si submittedAt est absent, et les identifiants texte/nombre doivent être équivalents.');
  assert.strictEqual(context.studentDraftSubmission('102','4'),undefined,
    'Un rendu déjà marqué submitted ne doit jamais redevenir un brouillon faute de submittedAt.');
  assert.strictEqual(context.studentDraftSubmission('101',2)?.id,'sub-2',
    'Un vrai brouillon doit rester modifiable malgré les identifiants mixtes.');

  const activity=context.activityData();
  assert.deepStrictEqual(activity.submissions.map(x=>x.id).sort(),['sub-1','sub-4'],
    'Le centre d’activité ne doit envoyer à corriger que les rendus effectivement transmis, non les brouillons ni les copies déjà corrigées.');
  assert.deepStrictEqual(activity.missing.map(x=>String(x.lessonId)+':'+String(x.student.id)).sort(),['101:2','102:s5'],
    'Les actions « travail non rendu » doivent réutiliser la même règle que la liste dédiée.');

  context.openWorkTracking('101');
  assert(context.lastModal.html.includes('<small>À rendre</small><b>2</b>'),
    'Le suivi professeur doit inclure tous les élèves du groupe, malgré les identifiants historiques mixtes.');
  assert(context.lastModal.html.includes('<small>Reçus</small><b>1</b>'),
    'Le compteur Reçus doit compter les élèves ayant réellement envoyé un travail, pas les brouillons.');
  assert(context.lastModal.html.includes('<small>À corriger</small><b>1</b>'),
    'Le compteur À corriger doit refléter les rendus transmis non corrigés.');

  context.showSubmissions(7,'2026-11-13');
  assert(context.lastModal.html.includes('ALICE')&&context.lastModal.html.includes('alice.pdf'),
    'La liste des rendus doit retrouver un devoir envoyé avec des identifiants de types différents.');
  assert(context.lastModal.html.includes('BILAL')&&context.lastModal.html.includes('Aucun fichier rendu'),
    'Un brouillon ne doit pas être présenté comme un rendu transmis au professeur.');

  const studentWork=source.slice(source.indexOf('function openStudentWork('),source.indexOf('\nasync function studentAddSubmissionFiles(',source.indexOf('function openStudentWork(')));
  assert(studentWork.includes('${safeRichHtml(sub.correctionComment||\'Correction disponible.\')}'),
    'Le retour mis en forme par le professeur doit être rendu comme contenu riche dans l’espace élève.');
  console.log('OK — cycle des devoirs : échéances, brouillons, rendus, identifiants mixtes, suivi professeur et restitution des corrections.');
})().catch(error=>{console.error(error);process.exitCode=1;});
