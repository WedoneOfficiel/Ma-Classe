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
assert(generatorSource.includes('createTeacherAccounts:values.createTeacherAccounts')&&generatorSource.includes('createStudentProfiles')&&generatorSource.includes('teachers:[]'),'Les options de création des comptes professeurs et des fiches élèves doivent être transmises à ChatGPT.');
assert(generatorSource.includes('Élève 6A-001')&&generatorSource.includes('createTeacherAccounts=')&&generatorSource.includes('createStudentProfiles=')&&generatorSource.includes('15 emplois du temps')&&generatorSource.includes('20 000 fiches élèves'),'Les consignes doivent couvrir les pseudonymes, les choix de création et les grands établissements.');
const wizardStart=generatorSource.indexOf('function openEstablishmentImport(){');
const wizardEnd=generatorSource.indexOf('\nfunction establishmentImportList',wizardStart);
const wizardSource=generatorSource.slice(wizardStart,wizardEnd);
assert(!wizardSource.includes('downloadEstablishmentTemplate()')&&!wizardSource.includes('downloadEstablishmentSchema()')&&!wizardSource.includes('downloadEstablishmentPrompt()')&&!wizardSource.includes('downloadEstablishmentContext()'),'Aucun document annexe ne doit être demandé à l’utilisateur pour ChatGPT.');
assert(wizardSource.includes('accept=".json,application/json"')&&wizardSource.includes('Un seul fichier JSON'),'Un seul JSON final doit être importé dans Ma Classe.');
assert(!generatorSource.includes("api.openai.com")&&!generatorServer.includes("api.openai.com"),'Aucune intégration API ChatGPT ne doit être ajoutée.');
assert(generatorGuide.includes("Aucun fichier à joindre à ChatGPT")&&generatorGuide.includes("Confidentialité"),'Le guide doit expliquer le copier-coller unique et la pseudonymisation.');

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
