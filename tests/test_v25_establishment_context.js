const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.join(__dirname,'..'),app=fs.readFileSync(path.join(root,'_all.js'),'utf8');
const start=app.indexOf('function downloadEstablishmentContext(){');
const end=app.indexOf('function downloadEstablishmentTemplate(){',start);
assert(start>=0&&end>start,'L’export de contexte anonymisé doit être disponible.');
const captured={};
const context={
 db:{
  classes:[{id:'class-id-1',name:'6e A',levels:['6e'],level:'6e',groups:['Groupe A','Groupe B'],teacherIds:['teacher-id-1'],principalTeacherId:'teacher-id-1',subjectRequirements:[{subject:'Français',hoursPerWeek:4}]}],
  students:[
   {id:'student-id-1',classId:'class-id-1',first:'PRENOM_CONFIDENTIEL',last:'NOM_CONFIDENTIEL',group:'Groupe A',email:'private@example.invalid'},
   {id:'student-id-2',classId:'class-id-1',first:'AUTRE_PRENOM',last:'AUTRE_NOM',group:'Groupe B'}
  ],
  teachers:[{id:'teacher-id-1',first:'IDENTITE_PROF_CONFIDENTIELLE',last:'NOM_PROF',subjects:['Français']}],
  users:[{id:'teacher-id-1',role:'teacher',first:'IDENTITE_PROF_CONFIDENTIELLE',last:'NOM_PROF',email:'prof@example.invalid',scheduleUnavailable:[{day:2,startMinutes:780,endMinutes:840}]}],
  settings:{rooms:[{id:'room-id-1',name:'B204',type:'classroom',capacity:30,equipment:['vidéoprojecteur'],unavailable:[]}]},
  schedule:[{id:'slot-id-1',classId:'class-id-1',day:0,time:'08:00',endTime:'09:00',subject:'Français',group:'Groupe A',teacherId:'teacher-id-1',teacherIds:['teacher-id-1'],room:'B204',roomId:'room-id-1',recurrence:'weekly',startDate:'2026-09-07',endDate:'2027-07-02'}]
 },
 establishmentImportAdminOnly:()=>true,
 sameId:(a,b)=>String(a??'').trim()===String(b??'').trim(),
 downloadText:(name,content,type)=>{captured.name=name;captured.content=content;captured.type=type}
};
vm.createContext(context);
vm.runInContext(app.slice(start,end),context);
context.downloadEstablishmentContext();
assert.strictEqual(captured.name,'contexte-etablissement-maclasse-anonymise.json');
assert.strictEqual(captured.type,'application/json;charset=utf-8');
const data=JSON.parse(captured.content);
assert.strictEqual(data.format,'maclasse-establishment-context');
assert.strictEqual(data.classes[0].studentCount,2);
assert.deepStrictEqual(data.classes[0].groupCounts,{'Groupe A':1,'Groupe B':1});
assert.strictEqual(data.teachers[0].label,'Enseignant 1');
assert.deepStrictEqual(data.teachers[0].unavailable,[{day:2,start:'13:00',end:'14:00'}]);
assert.strictEqual(data.schedule[0].class,'classe_1');
assert.deepStrictEqual(data.schedule[0].teachers,['professeur_1']);
assert.strictEqual(data.schedule[0].room,'salle_1');
const serialized=JSON.stringify(data);
for(const secret of ['PRENOM_CONFIDENTIEL','NOM_CONFIDENTIEL','AUTRE_PRENOM','private@example.invalid','IDENTITE_PROF_CONFIDENTIELLE','prof@example.invalid','student-id-1','teacher-id-1','room-id-1','slot-id-1']){
 assert(!serialized.includes(secret),'Le contexte ne doit pas exporter '+secret);
}
assert(data.note.includes('aucun nom d’élève'));
assert(data.constraints.includes('ne modifie pas les classes'));
console.log('OK — Contexte existant : classes et effectifs agrégés, affectations pseudonymisées, salles/EDT et absence de données personnelles.');
