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
for (const key of ['classStructures','subjectPlans','teacherPlans','componentSchedules']) {
  assert(generatorSource.includes(key+',' ) || generatorSource.includes(key+':'),
    'Le dossier sauvegardé doit contenir '+key+'.');
}
for (const kind of ['class','subject','teacher','schedule']) {
  assert(generatorSource.includes("kind==='")+kind+"'"),
    'Le formulaire doit permettre d’ajouter des lignes '+kind+'.');
}
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
  '\\nresult=establishmentBriefPrompt({schoolTypes:["Collège","Lycée professionnel"],schoolOrganization:"Cité scolaire",schoolSiteMode:"Plusieurs sites / antennes",schoolStructureDetails:"Section européenne",schoolOrganizationDetails:"Bâtiments séparés",schoolYear:"2026-2027",periodMode:"variable",classStructures:[{component:"Collège",level:"6e",classCount:2,studentsPerClass:28,classNames:"6A, 6B"}],subjectPlans:[{component:"Collège",level:"6e",subject:"Français",hoursPerWeek:4,group:""}],teacherPlans:[{component:"Collège",pseudonym:"Professeur 01",subjects:"Français",classes:"6A, 6B",hoursPerWeek:18}],componentSchedules:[{component:"Collège",days:["Lundi","Mardi"],start:"08:00",end:"17:00",lunchStart:"12:00",lunchEnd:"13:30",breakNotes:"Récréation : 10:15–10:30",notes:""}],schoolBreaks:"Pause 12h-13h30",teacherCount:1,roomCount:30,createTeacherAccounts:false,createStudents:false,createSchedule:true,subjectPlan:"Collège | 6e | Français | 4 h/semaine",classPlan:"Collège | 6e | 2 classe(s)",teacherPlan:"Professeur 01 | Collège",schoolDays:"Collège : Lundi, Mardi",schoolHours:"Collège : 08:00–17:00",constraints:""});',
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
assert(promptSandbox.result.includes('classStructures')&&promptSandbox.result.includes('subjectPlans')&&promptSandbox.result.includes('teacherPlans')&&promptSandbox.result.includes('componentSchedules'),
  'Les lignes de classes, matières, professeurs et calendriers doivent être intégrées au prompt.');
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
assert(promptSandbox.result.includes('"teacherCount": 20')&&promptSandbox.result.includes('"roomCount": 30'),'Les quantités explicites du formulaire doivent être injectées dans le dossier transmis à ChatGPT.');
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
