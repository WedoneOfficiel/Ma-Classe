const fs=require('fs'),assert=require('assert'),path=require('path'),vm=require('vm');
const root=path.join(__dirname,'..');
const app=fs.readFileSync(path.join(root,'_all.js'),'utf8');
const server=fs.readFileSync(path.join(root,'server.py'),'utf8');
const helper=fs.readFileSync(path.join(root,'establishment_import.py'),'utf8');
const schema=JSON.parse(fs.readFileSync(path.join(root,'docs/templates/establishment-import.v1.schema.json'),'utf8'));
const example=JSON.parse(fs.readFileSync(path.join(root,'docs/templates/establishment-import.v1.example.json'),'utf8'));
const guide=fs.readFileSync(path.join(root,'docs/CONFIGURATION_ETABLISSEMENT_CHATGPT.md'),'utf8');
new vm.Script(app,{filename:'_all.js'});
assert.strictEqual((app.match(/function openStudentAccountEditor\(/g)||[]).length,1,'Le point d’entrée de création du compte élève ne doit exister qu’une seule fois.');
assert.strictEqual(example.format,'maclasse-establishment');
assert.strictEqual(example.version,1);
assert(schema.properties.classes&&schema.properties.students&&schema.properties.teachers&&schema.properties.rooms&&schema.properties.schedule);
assert(!JSON.stringify(schema).toLowerCase().includes('"password"'),'Le JSON ne doit jamais pouvoir fournir un mot de passe.');
assert(app.includes("format:'maclasse-establishment',version:1"),'Le modèle exporté doit être versionné.');
assert(app.includes("api('/api/admin/establishment-import/validate'"),'L’aperçu doit utiliser le validateur serveur.');
assert(app.includes("api('/api/admin/establishment-import/apply'"),'La confirmation doit passer par la route dédiée.');
assert(app.includes("if(authUser?.role!=='admin')"),'L’outil doit vérifier le rôle Direction côté interface.');
assert(app.includes('file.size>25*1024*1024'),'Le fichier JSON doit accepter les imports volumineux jusqu’à 25 Mo.');
assert(server.includes("elif path in ('/api/admin/establishment-import/validate','/api/admin/establishment-import/apply'):\n            max_length=25*1024*1024"),'Les deux routes d’import doivent avoir une limite HTTP dédiée de 25 Mo.');
assert(app.includes('previewEstablishmentImport(this.files&&this.files[0]);this.value=String()'),'Le sélecteur de fichier doit se réinitialiser sans casser la chaîne HTML/JavaScript.');
assert(app.includes("window.establishmentImportCredentials=[]"),'Les secrets doivent être effacés à la fermeture de la fenêtre.');
assert(app.includes('downloadEstablishmentCredentials'),'La Direction doit pouvoir enregistrer les identifiants générés.');
assert(app.includes('downloadEstablishmentSchema'),'Le schéma JSON doit être téléchargeable depuis l’outil.');
assert(app.includes('downloadEstablishmentContext'),'Le contexte existant anonymisé doit être exportable.');
assert(server.includes('import establishment_import'),'Le module de validation doit être chargé par le serveur.');
assert(server.includes("'/api/admin/establishment-import/validate'")&&server.includes("'/api/admin/establishment-import/apply'"));
assert(server.includes("if user.get('role')!='admin':"),'L’accès doit être contrôlé côté serveur.');
assert(server.includes('self._create_backup(force=True)'),'Une sauvegarde doit précéder chaque import.');
assert(server.includes('password_hasher=_password_hash'),'Les mots de passe doivent être hachés localement.');
assert(server.includes('token_factory=secrets.token_urlsafe'),'Les identifiants/mots de passe doivent être créés localement.');
assert(server.includes('os.fsync(output.fileno())')&&server.includes('os.replace(temporary_path,DATA_FILE)'),'La nouvelle base doit être écrite atomiquement.');
assert(helper.includes('def validate_bundle(')&&helper.includes('def build_data('));
assert(helper.includes('mustChangePassword')&&helper.includes('passwordHash'));
assert(!app.includes('api.openai.com')&&!server.includes('api.openai.com'),'Aucune API OpenAI/ChatGPT n’est intégrée.');
assert(guide.includes('Ma Classe ne se connecte jamais à ChatGPT'));

const generatorSource = fs.readFileSync('_all.js','utf8');
const generatorGuide = fs.readFileSync('docs/CONFIGURATION_ETABLISSEMENT_CHATGPT.md','utf8');
const generatorServer = fs.readFileSync('server.py','utf8');
assert(generatorSource.includes("Configurateur de l’établissement avec ChatGPT"),'Le configurateur doit être présenté comme un outil guidé.');
for (const field of ['schoolYear','periodMode','schoolBreaksNotes','schoolStructureDetails','schoolOrganization','schoolSiteMode','schoolOrganizationDetails','classPlanNotes','teacherPlanNotes','subjectPlanNotes']) {
  assert(generatorSource.includes('name="'+field+'"'), 'Le formulaire doit proposer le champ '+field+'.');
}
assert(generatorSource.includes("schoolBreaks:joinNotes(schoolBreaksStructured,schoolBreaksNotes)"),
  'Les horaires et pauses structurés doivent continuer à être réunis dans les données transmises.');

assert(generatorSource.includes('name="schoolTypes"')&&generatorSource.includes('input[name="schoolTypes"]:checked'),
  'Les composantes pédagogiques doivent être collectées sous forme de choix multiples.');
assert(generatorSource.includes('getSavedEstablishmentComponents(saved)'),
  'Les anciens formulaires doivent être repris avec une conversion de compatibilité.');
assert(generatorSource.includes("['trimestres','semestres','variable']"),
  'Le formulaire doit accepter une organisation des périodes variable selon les composantes.');

assert(generatorSource.includes('Plusieurs sites / antennes')&&generatorSource.includes('Cité scolaire'),
  'L’organisation physique doit être distinguée des composantes pédagogiques.');

assert(generatorSource.includes('function collectEstablishmentPlanRows(form,kind)')&&generatorSource.includes('function validateEstablishmentBrief(brief)'),
  'Le configurateur doit collecter et valider les lignes structurées.');
for (const key of ['classStructures','subjectPlans','teacherPlans','componentSchedules','roomStructures']) {
  assert(generatorSource.includes(key+',' ) || generatorSource.includes(key+':'),
    'Le dossier sauvegardé doit contenir '+key+'.');
}
assert(generatorSource.includes("if(kind==='class')")&&generatorSource.includes("else if(kind==='subject')")&&generatorSource.includes("else if(kind==='teacher')")&&generatorSource.includes("else if(kind==='schedule')")&&generatorSource.includes("else if(kind==='room')"),
  'Le formulaire doit permettre d’ajouter des lignes de classes, matières, professeurs, calendriers et salles.');
assert(generatorSource.includes('establishmentRoomRows')&&generatorSource.includes("const roomStructures=collectEstablishmentPlanRows(form,'room')"),
  'Les salles doivent être décrites ligne par ligne et intégrées aux réponses sauvegardées.');
assert(generatorSource.includes('SALLES STRUCTURÉES : roomStructures')&&generatorSource.includes('Utilise roomStructures comme liste prioritaire'),
  'Le prompt doit transmettre les salles connues comme source prioritaire.');
assert(generatorSource.includes('function addEstablishmentPlanRow(kind)')&&generatorSource.includes('function removeEstablishmentPlanRow(button)'),
  'La Direction doit pouvoir ajouter et retirer les lignes structurées.');
assert(generatorSource.includes('classPlanStructured')&&generatorSource.includes('subjectPlanStructured')&&generatorSource.includes('teacherPlanStructured')&&generatorSource.includes('schoolDaysStructured'),
  'Les données structurées doivent également être converties en consignes lisibles et compatibles.');
assert(generatorSource.includes('STRUCTURE DES CLASSES : classStructures')&&generatorSource.includes('MATIÈRES STRUCTURÉES : subjectPlans')&&generatorSource.includes('AFFECTATIONS STRUCTURÉES : teacherPlans')&&generatorSource.includes('CALENDRIERS PAR COMPOSANTE : componentSchedules'),
  'Les consignes ChatGPT doivent traiter les quatre catégories structurées comme sources prioritaires.');

const legacyStart=generatorSource.indexOf('function getSavedEstablishmentComponents(');
const legacyEnd=generatorSource.indexOf('function collectEstablishmentBrief(',legacyStart);
assert(legacyStart>=0&&legacyEnd>legacyStart,'Les fonctions de compatibilité des anciens choix doivent exister.');
const migrationSandbox={};
vm.runInNewContext(generatorSource.slice(legacyStart,legacyEnd)+
  '\nresult={components:getSavedEstablishmentComponents({schoolType:"École maternelle et élémentaire"}),organization:getSavedEstablishmentOrganization({schoolType:"Cité scolaire ou établissement polyvalent"}),details:getSavedEstablishmentOrganizationDetails({schoolType:"Cité scolaire ou établissement polyvalent"})};',
  migrationSandbox);
assert.deepStrictEqual(Array.from(migrationSandbox.result.components),['Maternelle','Élémentaire'],
  'L’ancien choix école maternelle et élémentaire doit devenir deux composantes.');
assert.strictEqual(migrationSandbox.result.organization,'',
  'L’ancienne catégorie ambiguë ne doit pas être convertie arbitrairement en une organisation.');
assert(migrationSandbox.result.details.includes('cité scolaire ou établissement polyvalent'),
  'L’ancienne précision ambiguë doit être conservée pour confirmation.');

assert(generatorSource.includes('function updateEstablishmentBriefSummary()')&&generatorSource.includes('establishmentBriefStatusReady'),
  'Le récapitulatif du formulaire doit être calculé et actualisé côté interface.');
assert(generatorSource.includes('form.reportValidity()'),
  'La sauvegarde et la copie doivent respecter les contrôles natifs du formulaire.');
const promptFunctionStart=generatorSource.indexOf('function establishmentBriefPrompt(brief){');
const promptFunctionEnd=generatorSource.indexOf('async function copyEstablishmentBrief()',promptFunctionStart);
assert(promptFunctionStart>=0&&promptFunctionEnd>promptFunctionStart,'La fonction de génération des consignes doit rester isolable.');
const promptSandbox={};
vm.runInNewContext(generatorSource.slice(promptFunctionStart,promptFunctionEnd)+
  '\nresult=establishmentBriefPrompt({schoolTypes:["Collège","Lycée professionnel"],schoolOrganization:"Cité scolaire",schoolSiteMode:"Plusieurs sites / antennes",schoolStructureDetails:"Section européenne",schoolOrganizationDetails:"Bâtiments séparés",schoolYear:"2026-2027",periodMode:"variable",classStructures:[{component:"Collège",level:"6e",classCount:2,studentsPerClass:28,classNames:"6A, 6B"}],subjectPlans:[{component:"Collège",level:"6e",subject:"Français",hoursPerWeek:4,group:""}],teacherPlans:[{component:"Collège",pseudonym:"Professeur 01",subjects:"Français",classes:"6A, 6B",hoursPerWeek:18}],componentSchedules:[{component:"Collège",days:["Lundi","Mardi"],start:"08:00",end:"17:00",lunchStart:"12:00",lunchEnd:"13:30",breakNotes:"Récréation : 10:15–10:30",notes:""}],roomStructures:[{id:"room-1",site:"Site A",name:"Salle 101",type:"Salle ordinaire",capacity:30,equipment:"vidéoprojecteur",unavailableNotes:""}],schoolBreaks:"Pause 12h-13h30",teacherCount:1,roomCount:30,createTeacherAccounts:false,createStudents:false,createSchedule:true,subjectPlan:"Collège | 6e | Français | 4 h/semaine",classPlan:"Collège | 6e | 2 classe(s)",teacherPlan:"Professeur 01 | Collège",schoolDays:"Collège : Lundi, Mardi",schoolHours:"Collège : 08:00–17:00",constraints:""});',
  promptSandbox);
assert(promptSandbox.result.includes('composantes pédagogiques sélectionnées=Collège ; Lycée professionnel')&&promptSandbox.result.includes('structure de regroupement=Cité scolaire')&&promptSandbox.result.includes('implantation=Plusieurs sites / antennes'),
  'Les composantes multiples et l’organisation de l’établissement doivent être injectées séparément.');
assert(promptSandbox.result.includes('Section européenne')&&promptSandbox.result.includes('Bâtiments séparés'),
  'Les précisions de structure et de sites doivent parvenir à ChatGPT.');
assert(promptSandbox.result.includes('Si schoolSiteMode=Plusieurs sites / antennes')&&promptSandbox.result.includes('siteId dédié'),
  'Les consignes doivent prévenir que le format V1 ne possède pas de champ site dédié.');
assert(promptSandbox.result.includes('Si periodMode=variable'),
  'Les consignes doivent préserver les régimes de périodes différents selon les classes.');
assert(promptSandbox.result.includes('année scolaire=2026-2027'),
  'L’année scolaire doit rester injectée dans les consignes.');
assert(promptSandbox.result.includes('SchoolBreaks=Pause 12h-13h30'),
  'Les pauses déclarées doivent être transmises aux consignes.');
assert.strictEqual((promptSandbox.result.match(/NOMBRE DE PROFESSEURS : teacherCount=/g)||[]).length,1,
  'Le nombre de professeurs ne doit être indiqué qu’une seule fois.');
assert.strictEqual((promptSandbox.result.match(/NOMBRE DE SALLES : roomCount=/g)||[]).length,1,
  'Le nombre de salles ne doit être indiqué qu’une seule fois.');
assert(promptSandbox.result.includes('classStructures')&&promptSandbox.result.includes('subjectPlans')&&promptSandbox.result.includes('teacherPlans')&&promptSandbox.result.includes('componentSchedules')&&promptSandbox.result.includes('roomStructures'),
  'Les lignes de classes, matières, professeurs, salles et calendriers doivent être intégrées au prompt.');
assert(promptSandbox.result.includes('Site A')&&promptSandbox.result.includes('Salle 101')&&promptSandbox.result.includes('Salle ordinaire')&&promptSandbox.result.includes('vidéoprojecteur'),
  'Le site, le nom, le type, la capacité et les équipements des salles doivent parvenir au prompt.');
assert(promptSandbox.result.includes('Professeur 01')&&promptSandbox.result.includes('Récréation : 10:15–10:30'),
  'Les affectations et horaires particuliers des composantes doivent être conservés.');
assert(promptSandbox.result.includes('même pseudonyme apparaît dans plusieurs composantes'),
  'Un enseignant intervenant dans plusieurs composantes doit être dédupliqué en un seul profil.');
const adminUsersStart=generatorSource.indexOf('function adminUsers(){');
const adminUsersEnd=generatorSource.indexOf('\nfunction ',adminUsersStart);
const adminUsersSource=generatorSource.slice(adminUsersStart,adminUsersEnd);
assert(!adminUsersSource.includes('openEstablishmentImport')&&!adminUsersSource.includes('Générateur de configuration d’établissement'),'Le configurateur ne doit plus figurer dans Administration → Utilisateurs.');
const settingsStart=generatorSource.indexOf('function settings(){');
const settingsEnd=generatorSource.indexOf('\nfunction ',settingsStart);
assert(generatorSource.slice(settingsStart,settingsEnd).includes('settingsEstablishmentCard'),'Le configurateur doit être accessible dans Paramètres.');
assert(generatorSource.includes('Enregistrer le formulaire dans Ma Classe')&&generatorSource.includes('Copier les consignes et les données pour ChatGPT'),'Le formulaire doit être enregistré puis copié en un seul bloc.');
assert(generatorSource.includes('await flushPendingSave()')&&generatorSource.includes('db.settings.establishmentBrief'),'Le configurateur doit conserver les réponses dans les données enregistrées.');
assert(generatorSource.includes('Enregistre le formulaire avant de copier la demande'),'La copie doit être bloquée tant que le formulaire n’est pas enregistré.');
assert(generatorSource.includes('createTeacherAccounts:values.createTeacherAccounts')&&generatorSource.includes('createStudentProfiles')&&generatorSource.includes('PROFILS ET COMPTES PROFESSEURS')&&generatorSource.includes('La Direction pourra ouvrir ultérieurement un compte'),'Les options de création des comptes professeurs et des fiches élèves doivent être transmises à ChatGPT.');
assert(generatorSource.includes('Non, conserver les fiches sans compte'),'Le choix sans compte doit expliquer que les fiches pédagogiques restent conservées.');
assert(generatorSource.includes('const profile=id?(db.teachers||[]).find')&&generatorSource.includes('Créer un compte de connexion pour ce professeur')&&generatorSource.includes('Sans compte de connexion'),'La Direction doit pouvoir différer puis créer un compte depuis une fiche professeur existante.');
assert(generatorSource.includes('Élève 6A-001')&&generatorSource.includes('createTeacherAccounts=')&&generatorSource.includes('createStudentProfiles=')&&generatorSource.includes('Créer les comptes de connexion des professeurs ?')&&generatorSource.includes('15 emplois du temps')&&generatorSource.includes('20 000 fiches élèves'),'Les consignes doivent couvrir les pseudonymes, les choix de création et les grands établissements.');
assert(generatorSource.includes("const teacherCount=values.teacherCount===''?null:Number(values.teacherCount)")&&generatorSource.includes("const roomCount=values.roomCount===''?null:Number(values.roomCount)")&&generatorSource.includes("teacherCount:teacherCount===null?null")&&generatorSource.includes("roomCount:roomCount===null?null"),'Un champ de quantité vide doit rester non renseigné, sans être converti en zéro.');
assert(promptSandbox.result.includes('"teacherCount": 1')&&promptSandbox.result.includes('"roomCount": 30'),'Les quantités explicites du formulaire doivent être injectées dans le dossier transmis à ChatGPT.');
const wizardStart=generatorSource.indexOf('function openEstablishmentImport(){');
const wizardEnd=generatorSource.indexOf('\nfunction establishmentImportList',wizardStart);
const wizardSource=generatorSource.slice(wizardStart,wizardEnd);
assert(!wizardSource.includes('downloadEstablishmentTemplate()')&&!wizardSource.includes('downloadEstablishmentSchema()')&&!wizardSource.includes('downloadEstablishmentPrompt()')&&!wizardSource.includes('downloadEstablishmentContext()'),'Aucun document annexe ne doit être demandé à l’utilisateur pour ChatGPT.');
assert(wizardSource.includes('accept=".json,application/json"')&&wizardSource.includes('Un seul fichier JSON'),'Un seul JSON final doit être importé dans Ma Classe.');
assert(!generatorSource.includes("api.openai.com")&&!generatorServer.includes("api.openai.com"),'Aucune intégration API ChatGPT ne doit être ajoutée.');
assert(generatorGuide.toLowerCase().includes("aucun fichier à joindre à chatgpt")&&generatorGuide.includes("Confidentialité"),'Le guide doit expliquer le copier-coller unique et la pseudonymisation.');


assert(generatorSource.includes("function openTeacherProfileEditor(")&&generatorSource.includes("function saveTeacherProfileOnly("),'Une fiche professeur sans compte doit pouvoir être modifiée sans créer de compte.');
assert(generatorSource.includes("Créer un compte de connexion")&&generatorSource.includes("Modifier la fiche"),'Le module Professeurs doit distinguer modification de fiche et création de compte.');
assert(generatorSource.includes("t.hasAccount!==false"),'Les élèves doivent voir les profils des professeurs sans compte sans les traiter comme des destinataires joignables.');
assert(generatorServer.includes("def _teacher_profiles_for_save(")&&generatorServer.includes("data['teachers']=_teacher_profiles_for_save(current or {},data,user)"),'La sauvegarde doit conserver le répertoire des profils professeurs et le protéger pour les rôles non Direction.');
assert(generatorServer.includes("stored_profile=next((x for x in data.get('teachers',[])"),'La projection professeur doit combiner fiche pédagogique et compte de connexion.');
assert(generatorServer.includes("hasAccount':ident in account_teacher_ids"),'La projection élève doit distinguer un professeur avec compte et sans compte.');
console.log('OK — Import établissement : schéma, exemple, documentation, échange manuel, Direction, sauvegarde, comptes locaux et import atomique.');


{
  const start=generatorSource.lastIndexOf('function downloadEstablishmentContext(');
  const end=generatorSource.indexOf('\nfunction ',start+10);
  assert(start>=0&&end>start,'La fonction d’export du contexte doit exister.');
  const sample={
    classes:[{id:'CLASS_ID_A',name:'6e A',level:'6e',levels:['6e'],groups:['Groupe A'],teacherIds:['TEACHER_ID_A'],principalTeacherId:'TEACHER_ID_A',subjectRequirements:[]}],
    teachers:[{id:'TEACHER_ID_A',first:'NAME_A',last:'SURNAME_A',email:'EMAIL_A',phone:'PHONE_A',subjects:['Français']}],
    users:[{id:'TEACHER_ID_A',role:'teacher',username:'USERNAME_A',first:'NAME_A',last:'SURNAME_A',email:'EMAIL_A',phone:'PHONE_A',scheduleUnavailable:[]}],
    students:[{id:'STUDENT_ID_A',first:'STUDENT_NAME_A',last:'STUDENT_SURNAME_A',email:'STUDENT_EMAIL_A',phone:'STUDENT_PHONE_A',classId:'CLASS_ID_A',group:'Groupe A'}],
    settings:{rooms:[{id:'ROOM_ID_A',name:'Salle 101',type:'classroom',capacity:30,equipment:[],unavailable:[]}]},
    schedule:[{id:'SCHEDULE_ID_A',classId:'CLASS_ID_A',teacherId:'TEACHER_ID_A',roomId:'ROOM_ID_A',room:'Salle 101',day:1,time:'08:00',endTime:'09:00',subject:'Français',group:'Groupe A',recurrence:'weekly',startDate:'2026-09-01',exceptions:[]}]
  };
  const exportState={db:sample,authUser:{role:'admin'},establishmentImportAdminOnly:()=>true,
    sameId:(a,b)=>String(a??'')===String(b??''),
    downloadText:(filename,content,mime)=>{exportState.download={filename,content,mime};}
  };
  vm.createContext(exportState);
  vm.runInContext(generatorSource.slice(start,end),exportState);
  vm.runInContext('downloadEstablishmentContext()',exportState);
  assert(exportState.download,'L’export du contexte doit être déclenché.');
  const exported=JSON.parse(exportState.download.content);
  const serialized=JSON.stringify(exported);
  for(const secret of ['NAME_A','SURNAME_A','EMAIL_A','PHONE_A','USERNAME_A','STUDENT_NAME_A','STUDENT_SURNAME_A','STUDENT_EMAIL_A','STUDENT_PHONE_A','TEACHER_ID_A','STUDENT_ID_A','CLASS_ID_A','ROOM_ID_A','SCHEDULE_ID_A']) {
    assert(!serialized.includes(secret),'Le contexte ne doit pas exporter : '+secret);
  }
  assert.strictEqual(exported.classes[0].studentCount,1,'Seul l’effectif agrégé doit être exporté.');
  assert.strictEqual(exported.teachers[0].label,'Enseignant 1','Le professeur doit être pseudonymisé.');
  assert.strictEqual(exported.schedule[0].teachers[0],'professeur_1','Les références professeur doivent être pseudonymisées.');
  console.log('OK — export réel du contexte établissement sans identité ni coordonnée.');
}


// Validation des lignes de salles, des doublons et de la cohérence des quantités.
const validationStart=generatorSource.indexOf('function validateEstablishmentBrief(brief){');
const validationEnd=generatorSource.indexOf('\nfunction collectEstablishmentBrief(',validationStart);
assert(validationStart>=0&&validationEnd>validationStart,'Le validateur du formulaire doit rester isolable.');
const validationSandbox={};
vm.runInNewContext(generatorSource.slice(validationStart,validationEnd)+
  '\nconst base={name:"Établissement test",schoolTypes:["Collège"],classStructures:[{component:"Collège",level:"6e",classCount:1,studentsPerClass:25}],classPlanNotes:"",subjectPlans:[],teacherPlans:[],componentSchedules:[],roomStructures:[{site:"Site A",name:"Salle 101",capacity:30}],teacherCount:null,roomCount:1,createSchedule:false,schoolDaysNotes:"",schoolHoursNotes:"",schoolBreaksNotes:"",subjectPlanNotes:""};'+
  '\nresult={valid:validateEstablishmentBrief(base),missingRoom:validateEstablishmentBrief({...base,roomStructures:[{site:"Site A",name:"",capacity:30}]}),duplicateRoom:validateEstablishmentBrief({...base,roomStructures:[{site:"Site A",name:"Salle 101",capacity:30},{site:"Site A",name:"Salle 101",capacity:20}],roomCount:2}),tooManyRooms:validateEstablishmentBrief({...base,roomStructures:[{site:"Site A",name:"101",capacity:30},{site:"Site A",name:"102",capacity:30}],roomCount:1}),fractionalCount:validateEstablishmentBrief({...base,teacherCount:1.5}),staleComponent:validateEstablishmentBrief({...base,classStructures:[{component:"Lycée général",level:"2nde",classCount:1,studentsPerClass:25}]})};',
  validationSandbox);
assert.strictEqual(validationSandbox.result.valid,'','Une fiche de salle complète doit être acceptée.');
assert(validationSandbox.result.missingRoom.includes('salle détaillée'),'Une salle sans nom doit être refusée.');
assert(validationSandbox.result.duplicateRoom.includes('plusieurs fois'),'Une salle dupliquée sur le même site doit être refusée.');
assert(validationSandbox.result.tooManyRooms.includes('dépasse'),'Le nombre de salles détaillées ne doit pas dépasser le total annoncé.');
assert(validationSandbox.result.fractionalCount.includes('nombre de professeurs'),'Un nombre de professeurs fractionnaire doit être refusé.');
assert(validationSandbox.result.staleComponent.includes('n’est plus cochée'),'Une ligne attachée à une composante désélectionnée doit être signalée.');


// Référentiel national préchargé par niveau : volumes, sous-domaines et statuts distincts.
const curriculumStart=generatorSource.indexOf('function mcNationalCurriculumCatalog(');
const curriculumEnd=generatorSource.indexOf('\nfunction prefillNationalCurriculum()',curriculumStart);
assert(curriculumStart>=0&&curriculumEnd>curriculumStart,'Le catalogue national doit être isolable.');
const curriculumSandbox={};
vm.runInNewContext(generatorSource.slice(curriculumStart,curriculumEnd)+
  '\nresult=mcNationalCurriculumCatalog(["Maternelle","Élémentaire","Collège","Lycée général","Lycée technologique"],["STMG"],["Mathématiques","Sciences économiques et sociales"]);',
  curriculumSandbox);
const curriculum=Array.from(curriculumSandbox.result);
const pick=(component,level,subject)=>curriculum.find(x=>x.component===component&&x.level===level&&x.subject===subject);
assert(pick('Maternelle','Petite section','Développement et structuration du langage oral et écrit'),'La maternelle doit distinguer le domaine du langage.');
assert.strictEqual(pick('Maternelle','Petite section','Développement et structuration du langage oral et écrit').hoursPerWeek,null,'Aucun quota artificiel ne doit être attribué au domaine du langage en maternelle.');
assert.strictEqual(pick('Maternelle','Petite section','Ensemble des enseignements du cycle 1').hoursPerWeek,24,'Les 24 h doivent rester un volume global de cycle.');
assert.strictEqual(pick('Élémentaire','CP','Français').hoursPerWeek,10,'Le français CP doit être prérempli avec la moyenne du cycle 2.');
assert.strictEqual(pick('Élémentaire','CP','Sciences et technologie').hoursPerWeek,1.11,'Le CP doit utiliser la nouvelle grille applicable à la rentrée 2026.');
assert.strictEqual(pick('Élémentaire','CP','Histoire-géographie et enseignement moral et civique').hoursPerWeek,1.39,'Le volume histoire-géographie/EMC du CP doit suivre le tableau 2026.');
assert.strictEqual(pick('Élémentaire','CE1','Questionner le monde et enseignement moral et civique').hoursPerWeek,2.5,'En 2026-2027, la grille précédente reste applicable au CE1.');
assert(pick('Élémentaire','CP','Français').details.includes('vocabulaire')&&pick('Élémentaire','CP','Français').details.includes('lecture'),'Les sous-domaines du français doivent être préremplis.');
assert.strictEqual(pick('Élémentaire','CM1','Français').hoursPerWeek,8,'Le français CM1 doit utiliser la moyenne du cycle 3.');
assert.strictEqual(pick('Collège','6e','Français').hoursPerWeek,4.5,'L’horaire de français en 6e doit suivre la grille 2026.');
assert.strictEqual(pick('Collège','3e','Histoire-géographie et EMC').hoursPerWeek,3.5,'Le volume histoire-géographie/EMC de 3e doit être exact.');
assert.strictEqual(pick('Lycée général','Terminale générale','Philosophie').hoursPerWeek,4,'La philosophie de terminale doit être préremplie.');
assert.strictEqual(pick('Lycée technologique','Première STMG','Sciences de gestion et numérique').hoursPerWeek,7,'La série STMG doit être préremplie si sélectionnée.');
assert(pick('Lycée général','Première générale','Mathématiques spécifiques (élèves ne suivant pas la spécialité mathématiques)').hoursBasis==='specialty_choice','Les mathématiques spécifiques de première doivent rester conditionnelles.');
const sthrSandbox={};
vm.runInNewContext(generatorSource.slice(curriculumStart,curriculumEnd)+'\nresult=mcNationalCurriculumCatalog(["Lycée technologique"],["STHR"],[],"2026-2027");',sthrSandbox);
const sthr=Array.from(sthrSandbox.result);
assert(sthr.some(x=>x.level==='Seconde STHR'&&x.subject==='Sciences et technologies culinaires'&&x.hoursPerWeek===4),'La seconde STHR doit avoir son programme spécifique.');
assert(!sthr.some(x=>x.level==='Seconde générale et technologique'),'La seconde STHR ne doit pas recevoir à tort la grille générale de seconde.');

assert(pick('Lycée professionnel','Seconde professionnelle','Enseignements professionnels de la spécialité').details.includes('450 h annuelles'),'Les horaires professionnels doivent rester reliés à leurs volumes annuels.');
const curriculum2027={};
vm.runInNewContext(generatorSource.slice(curriculumStart,curriculumEnd)+'\nresult=mcNationalCurriculumCatalog(["Élémentaire"],[],[],"2027-2028");',curriculum2027);
const elementary2027=Array.from(curriculum2027.result);
assert.strictEqual(elementary2027.find(x=>x.level==='CE1'&&x.subject==='Sciences et technologie').hoursPerWeek,1.11,'La nouvelle grille doit entrer en vigueur au CE1 à la rentrée 2027.');
assert(!elementary2027.some(x=>x.level==='CE1'&&x.subject==='Questionner le monde et enseignement moral et civique'),'La grille précédente ne doit plus être utilisée au CE1 à partir de 2027.');
assert(generatorSource.includes('function prefillNationalCurriculum()')&&generatorSource.includes('Préremplir les programmes nationaux'),'Le formulaire doit disposer d’une commande de préremplissage.');
assert(generatorSource.includes('name="extraSubjects"'),'L’établissement doit pouvoir ajouter des matières complémentaires.');
assert(generatorSource.includes('curriculumMode')&&generatorSource.includes('techSeries')&&generatorSource.includes('generalSpecialties'),'Le régime et les séries/spécialités doivent être mémorisés.');

const nullHoursValidationStart=generatorSource.indexOf('function validateEstablishmentBrief(brief){');
const nullHoursValidationEnd=generatorSource.indexOf('\nfunction collectEstablishmentBrief(',nullHoursValidationStart);
const nullHoursSandbox={};
vm.runInNewContext(generatorSource.slice(nullHoursValidationStart,nullHoursValidationEnd)+
  '\nconst b={name:"École test",schoolTypes:["Maternelle"],classStructures:[{component:"Maternelle",level:"Petite section",classCount:1,studentsPerClass:20}],classPlanNotes:"",subjectPlans:[{component:"Maternelle",level:"Petite section",subject:"Langage",hoursPerWeek:null,details:"Oral et vocabulaire",source:"national",hoursBasis:"not_allocated"}],teacherPlans:[],componentSchedules:[],roomStructures:[],teacherCount:null,roomCount:null,createSchedule:false,schoolDaysNotes:"",schoolHoursNotes:"",schoolBreaksNotes:"",subjectPlanNotes:""};result={national:validateEstablishmentBrief(b),manual:validateEstablishmentBrief({...b,subjectPlans:[{component:"Maternelle",level:"Petite section",subject:"Langage",hoursPerWeek:null,details:"Oral et vocabulaire"}]})};',
  nullHoursSandbox);
assert.strictEqual(nullHoursSandbox.result.national,'','Un domaine national sans quota horaire doit être accepté si le détail pédagogique est fourni.');
assert(nullHoursSandbox.result.manual.includes('Indique les heures'),'Une matière manuelle sans horaire ne doit pas être acceptée implicitement.');

