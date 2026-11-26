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
    {id:'sub-2',lessonId:101,studentId:'2',files:[{name:'brouillon.pdf',url:'/data/uploads/brouillon.pdf'}]},
    {id:'sub-3',lessonId:102,studentId:'s3',status:'submitted',submittedAt:'2026-11-19T11:00:00Z',corrected:true,files:[{name:'chloe.pdf',url:'/data/uploads/chloe.pdf'}]},
    {id:'sub-4',lessonId:'102',studentId:4,status:'submitted',corrected:false,files:[{name:'dina.pdf',url:'/data/uploads/dina.pdf'}]}
  ]
};
const context={
  db,
  sameId:(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
  iso:()=> '2026-11-26',
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
  const missing=context.v103MissingWorkList();
  const keys=Array.from(missing,x=>String(x.lesson.id)+':'+String(x.student.id)).sort();
  assert.deepStrictEqual(keys,['101:2','102:s5','103:2','103:s1','104:2','104:s1'],
    'La liste globale des rendus manquants conserve les devoirs à venir, mais ne doit jamais confondre un brouillon avec un rendu transmis ; le retard est calculé séparément dans le suivi de classe.');

  assert.strictEqual(context.studentSubmitted(db.lessons[1],4)?.id,'sub-4',
    'Un statut submitted suffit même si submittedAt est absent, et les identifiants texte/nombre doivent être équivalents.');
  assert.strictEqual(context.studentSubmitted(db.lessons[0],2),undefined,
    'Une entrée historique sans status ni submittedAt doit rester un brouillon, jamais un rendu transmis.');
  assert.strictEqual(context.studentDraftSubmission('102','4'),undefined,
    'Un rendu déjà marqué submitted ne doit jamais redevenir un brouillon faute de submittedAt.');
  assert.strictEqual(context.studentDraftSubmission('101',2)?.id,'sub-2',
    'Un vrai brouillon doit rester modifiable malgré les identifiants mixtes.');

  const activity=context.activityData();
  assert.deepStrictEqual(Array.from(activity.submissions,x=>x.id).sort(),['sub-1','sub-4'],
    'Le centre d’activité ne doit envoyer à corriger que les rendus effectivement transmis, non les brouillons ni les copies déjà corrigées.');
  assert.deepStrictEqual(Array.from(activity.missing,x=>String(x.lessonId)+':'+String(x.student.id)).sort(),['101:2','102:s5','103:2','103:s1','104:2','104:s1'],
    'Les actions « travail non rendu » doivent réutiliser la même règle que la liste dédiée.');

  // Les synthèses élève et les statistiques générales ne doivent pas considérer
  // le brouillon de Bilal comme un rendu transmis.
  context.v101StudentAverage=()=> '12.00';
  vm.runInContext(section('function v101SubmissionStats(){','function v101StudentAverage('),context);
  vm.runInContext(section('function studentActivitySummary(','function openStudentActivity('),context);
  assert.strictEqual(context.v101SubmissionStats().expected,9,
    'Les statistiques globales doivent compter tous les élèves ciblés, y compris les groupes.');
  assert.strictEqual(context.v101SubmissionStats().received,3,
    'Les statistiques globales ne doivent compter que les rendus transmis, et normaliser les identifiants.');
  assert.strictEqual(context.v101SubmissionStats().missing,6,
    'Un brouillon ne doit pas réduire le nombre global de travaux manquants.');
  const quickSummary=context.studentActivitySummary('2');
  assert.strictEqual(quickSummary.submissions,0,
    'La fiche rapide de Bilal ne doit compter aucun rendu transmis lorsqu’il ne possède qu’un brouillon.');
  assert.strictEqual(quickSummary.missing,3,
    'La fiche rapide doit compter comme manquants les devoirs dont Bilal n’a pas réellement envoyé le travail.');

  context.evaluationModelTargetStudents=()=>db.students;
  context.evaluationGradeLabel=()=> '—';
  vm.runInContext(section('function openStudentActivity(','function v103MissingWorkList('),context);
  context.openStudentActivity('2');
  assert(context.lastModal.html.includes('<small>Rendus</small><b>0</b>'),
    'Le KPI Rendus du suivi rapide doit exclure le brouillon.');
  const draftRow=context.lastModal.html.indexOf('<span class="pill orange">À FAIRE</span><div class="grow"><b>Rédaction</b>');
  assert(draftRow>=0,
    'Le devoir pour lequel Bilal a un brouillon doit rester affiché comme À FAIRE dans le suivi rapide.');

  const profile360=declaration('profile360Tab');
  assert(profile360.includes("sameId(z.lessonId,x.l.id)&&sameId(z.studentId,id)&&(z.status==='submitted'||!!z.submittedAt)"),
    'Le profil 360 doit réserver le statut Rendu aux soumissions réellement envoyées.');
  assert(profile360.includes("sameId(x.studentId,id)&&(x.status==='submitted'||!!x.submittedAt)"),
    'Le KPI Rendus du profil 360 doit exclure les brouillons.');

  context.openWorkTracking('101');
  assert(context.lastModal.html.includes('<small>À rendre</small><b>2</b>'),
    'Le suivi professeur doit inclure tous les élèves du groupe, malgré les identifiants historiques mixtes.');
  assert(context.lastModal.html.includes('<small>Reçus</small><b>1</b>'),
    'Le compteur Reçus doit compter les élèves ayant réellement envoyé un travail, pas les brouillons.');
  assert(context.lastModal.html.includes('<small>À corriger</small><b>1</b>'),
    'Le compteur À corriger doit refléter les rendus transmis non corrigés.');

  context.showSubmissions(7,'2026-11-13');
  assert(context.lastModal?.title==='Rendus des élèves'&&context.lastModal.html.includes('MARTIN')&&context.lastModal.html.includes('Alice')&&context.lastModal.html.includes('1 fichier')&&context.lastModal.html.includes('Parcourir / corriger'),
    'La liste des rendus doit retrouver le travail envoyé malgré les identifiants de types différents.');
  assert(context.lastModal.html.includes('DURAND')&&context.lastModal.html.includes('Bilal')&&context.lastModal.html.includes('Aucun fichier rendu'),
    'Un brouillon ne doit pas être présenté comme un rendu transmis au professeur.');

  const studentWork=source.slice(source.indexOf('function openStudentWork('),source.indexOf('\nasync function studentAddSubmissionFiles(',source.indexOf('function openStudentWork(')));
  assert(studentWork.includes('${safeRichHtml(sub.correctionComment||\'Correction disponible.\')}'),
    'Le retour mis en forme par le professeur doit être rendu comme contenu riche dans l’espace élève.');
  console.log('OK — cycle des devoirs : échéances, brouillons, rendus, identifiants mixtes, suivi professeur et restitution des corrections.');
})().catch(error=>{console.error(error);process.exitCode=1;});
