const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.join(__dirname,'..');
const app=fs.readFileSync(path.join(root,'_all.js'),'utf8');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
assert(!app.includes(String.fromCharCode(92)+'`'),'Aucun accent grave ne doit être échappé hors d’un littéral template.');
assert(!app.includes(String.fromCharCode(92)+'${'),'Aucune interpolation de template ne doit rester échappée dans les nouveaux formulaires.');
function sliceBetween(source,startMarker,endMarker){
 const start=source.indexOf(startMarker),end=source.indexOf(endMarker,start+startMarker.length);
 assert(start>=0&&end>start,'Bloc introuvable : '+startMarker);
 return source.slice(start,end);
}
const scheduling=sliceBetween(app,'function scheduleGroupsOverlap(','function duplicateSchedule(');
const availability=sliceBetween(app,'function scheduleAvailabilityConflicts(','function scheduleConflicts(');
const planner=sliceBetween(app,'function plannerConflicts(','function plannerFindSlots(');
const context={
 db:{
  users:[{id:'t1',role:'teacher',first:'Élodie',last:'Martin',scheduleUnavailable:[{day:0,startMinutes:480,endMinutes:540}]}],
  teachers:[],
  settings:{rooms:[
   {id:'r1',name:'B204',type:'classroom',capacity:30,equipment:['vidéoprojecteur'],unavailable:[{day:0,startMinutes:480,endMinutes:600}]},
   {id:'r2',name:'Info',type:'computer',capacity:25,equipment:['ordinateurs'],unavailable:[]},
   {id:'r3',name:'Labo',type:'science',capacity:35,equipment:['vidéoprojecteur','paillasses'],unavailable:[]},
   {id:'r4',name:'Petite',type:'classroom',capacity:12,equipment:['vidéoprojecteur'],unavailable:[]}
  ]},
  schedule:[{id:'s1',classId:'5A',day:1,time:'08:00',endTime:'09:00',room:'Info',teacherId:'t2',teacherIds:['t2'],subject:'Maths'}]
 },
 mins(value){const p=String(value||'0:0').split(':').map(Number);return (p[0]||0)*60+(p[1]||0)},
 addHour(value){const n=this.mins(value)+60;return String(Math.floor(n/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0')},
 sameId(a,b){const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
 teacherName(t){return String(t?.first||'')+' '+String(t?.last||'')||'Enseignant'},
 scheduleOverlap(a,b){return this.mins(a.time)<this.mins(b.endTime||this.addHour(b.time))&&this.mins(b.time)<this.mins(a.endTime||this.addHour(a.time))},
 scheduleGroupsOverlap(a,b){const x=String(a?.group||''),y=String(b?.group||'');return !x||!y||x===y}
};
vm.createContext(context);
vm.runInContext(scheduling+availability+planner,context);
const availabilityConflicts=Array.from(context.scheduleAvailabilityConflicts({
 classId:'6A',day:0,time:'08:30',endTime:'09:30',teacherIds:['t1'],room:'B204'
}));
assert(availabilityConflicts.some(x=>x.includes('Professeur Élodie Martin')));
assert(availabilityConflicts.some(x=>x.includes('Salle B204')));
const parallel=Array.from(context.plannerConflicts({
 classId:'6A',group:'Groupe B',day:0,time:'08:00',endTime:'09:00',
 teacherId:'t2',teacherIds:['t2'],room:'Labo'
}));
assert.strictEqual(parallel.length,0,'Deux sous-groupes distincts peuvent travailler en parallèle.');
const monday=Array.from(context.plannerRoomOptions(20,['vidéoprojecteur'],0,'08:30','09:30')).map(x=>x.name);
assert.deepStrictEqual(monday,['Labo'],'Le Planner exclut les salles indisponibles, trop petites, mal équipées ou déjà prises.');
const tuesday=Array.from(context.plannerRoomOptions(20,['vidéoprojecteur'],1,'08:30','09:30')).map(x=>x.name);
assert.deepStrictEqual(tuesday,['B204','Labo'],'Le Planner vérifie le créneau exact et les réservations déjà planifiées.');
const tooLarge=Array.from(context.plannerRoomOptions(40,[],1,'08:30','09:30'));
assert.strictEqual(tooLarge.length,0,'Une salle de capacité insuffisante ne doit pas être recommandée.');
const saveRoomFn=sliceBetween(app,'function savePlannerRoom(','function deletePlannerRoom(');
const newRoomForm={name:'Nouvelle salle de test',type:'classroom',capacity:'40',equipment:'ordinateurs, vidéoprojecteur',unavailable:''};
context.FormData=function(){return Object.entries(newRoomForm)[Symbol.iterator]()};
context.uid=()=> 'room-test-id';
context.save=()=>{};
context.closeModal=()=>{};
context.render=()=>{};
context.toast=()=>{};
vm.runInContext(saveRoomFn,context);
context.savePlannerRoom({preventDefault(){},target:{}});
const savedRoom=context.db.settings.rooms.find(r=>r.id==='room-test-id');
assert(savedRoom&&savedRoom.name==='Nouvelle salle de test','Une salle enregistrée dans Paramètres doit rester dans settings.rooms.');
const savedRoomOptions=Array.from(context.plannerRoomOptions(30,['vidéoprojecteur'],1,'08:30','09:30')).map(x=>x.name);
assert(savedRoomOptions.includes('Nouvelle salle de test'),'Une salle créée dans Paramètres doit être disponible dans la recherche Planner si elle satisfait les critères.');

const openPlannerUi=sliceBetween(app,'function openPlanner(){','function runPlanner(e)');
const plannerUiContext={
 db:{classes:[{id:'6A',name:'6e A'}],teachers:[{id:'t1',first:'Élodie',last:'Martin'}],schedule:[]},
 DAYS:['Lundi','Mardi','Mercredi','Jeudi','Vendredi'],
 esc:roomTestEsc,teacherName:t=>t.first+' '+t.last,
 plannerCourseOptions(){return [{slot:{id:'s1'},label:'Mardi · 09:00–10:00 · 6e A · SES · Sans salle'}]},
 plannerToggleAction(){},openModal(title,body){capturedRoomModal={title,body}}
};
vm.createContext(plannerUiContext);
vm.runInContext(openPlannerUi,plannerUiContext);
plannerUiContext.openPlanner();
assert(capturedRoomModal.body.includes('Trouver un créneau pour un nouveau cours'),'Le premier parcours doit clairement créer un nouveau cours.');
assert(capturedRoomModal.body.includes('Trouver ou changer la salle d’un cours existant'),'Le second parcours doit clairement concerner un cours déjà inscrit.');
assert(capturedRoomModal.body.includes('name="scheduleId"'),'Le choix de salle doit demander de sélectionner un cours existant.');
assert(!capturedRoomModal.body.includes('Préparer un cours'),'L’action redondante Préparer un cours doit disparaître.');

const runPlannerUi=sliceBetween(app,'function runPlanner(e)','function plannerCreateDraft(');
assert(runPlannerUi.includes('plannerSetExistingRoom('),'Le remplacement de salle doit ouvrir le créneau existant.');
assert(runPlannerUi.includes('plannerCreateDraft('),'Le parcours de création doit ouvrir un nouveau cours avec la salle choisie.');
let capturedPlannerCall=null,openedScheduleEdit=null;
const roomActionContext={
 db:{
  classes:[{id:'6A',name:'6e A'},{id:'6B',name:'6e B'}],
  students:Array.from({length:26},(_,i)=>({id:'stu'+i,classId:'6A'})),
  schedule:[
   {id:'s1',sharedSlotId:'shared-1',classId:'6A',day:1,time:'09:00',endTime:'10:00',subject:'SES',teacherId:'t1',teacherIds:['t1'],room:'A101'},
   {id:'s2',sharedSlotId:'shared-1',classId:'6B',day:1,time:'09:00',endTime:'10:00',subject:'SES',teacherId:'t1',teacherIds:['t1'],room:'A101'},
   {id:'other',classId:'5A',day:1,time:'09:00',endTime:'10:00',subject:'Histoire',teacherId:'t2',room:'B204'}
  ]
 },
 FormData:function(){return Object.entries({action:'room',scheduleId:'s1',capacity:'0',equipment:'vidéoprojecteur'})[Symbol.iterator]()},
 sameId:(a,b)=>String(a??'').trim()===String(b??'').trim(),
 cls(id){return this.db.classes.find(x=>x.id===id)},
 DAYS:['Lundi','Mardi','Mercredi','Jeudi','Vendredi'],
 plannerClassStudentCount(ids){return this.db.students.filter(s=>ids.includes(s.classId)).length},
 plannerRoomOptions(...args){capturedPlannerCall=args;return [{name:'Salle 301',type:'classroom',capacity:30,equipment:['vidéoprojecteur']}]},
 esc:roomTestEsc,
 jsArg(value){return roomTestEsc(JSON.stringify(String(value??'')))},
 openSchedule(...args){openedScheduleEdit=args},
 openModal(title,body){capturedRoomModal={title,body}},
 toast(message){throw Error(message)}
};
vm.createContext(roomActionContext);
vm.runInContext(runPlannerUi,roomActionContext);
roomActionContext.runPlanner({preventDefault(){},target:{}});
assert.strictEqual(capturedPlannerCall[0],26,'La recherche de remplacement doit reprendre l’effectif réel du ou des cours.');
assert.strictEqual(capturedPlannerCall[2],1,'La recherche de remplacement doit conserver le jour du cours.');
assert.strictEqual(capturedPlannerCall[3],'09:00','La recherche de remplacement doit conserver l’heure de début.');
assert.strictEqual(capturedPlannerCall[4],'10:00','La recherche de remplacement doit conserver l’heure de fin.');
assert.deepStrictEqual(Array.from(capturedPlannerCall[5]),['s1','s2'],'Les créneaux existants du cours partagé doivent être ignorés, pas considérés comme des conflits.');
assert(capturedRoomModal.title.includes('Salles disponibles pour ce cours')&&capturedRoomModal.body.includes('SES'),'La recherche doit présenter les informations du cours sélectionné, sans demander un nouvel intitulé.');
assert(capturedRoomModal.body.includes('plannerSetExistingRoom(&quot;s1&quot;,&quot;Salle 301&quot;)'),'Le résultat doit proposer le remplacement de salle sur le cours sélectionné.');
roomActionContext.plannerSetExistingRoom('s1','Salle 301');
assert.deepStrictEqual(openedScheduleEdit,['s1',null,'Salle 301'],'Choisir une salle doit ouvrir le formulaire de modification du cours existant avec sa nouvelle salle.');

let newCourseModal=null,newCourseRoomArgs=null;
const newCourseContext={
 db:{classes:[{id:'6A',name:'6e A'}],students:Array.from({length:26},(_,i)=>({id:'stu'+i,classId:'6A'})),schedule:[]},
 FormData:function(){return Object.entries({action:'find',classId:'6A',subject:'SES',teacherId:'t1',day:'0',time:'14:00',duration:'60',capacity:'0',equipment:'vidéoprojecteur'})[Symbol.iterator]()},
 mins(value){const p=String(value||'0:0').split(':').map(Number);return (p[0]||0)*60+(p[1]||0)},
 plannerClassStudentCount(){return 26},
 plannerFindSlots(){return [{day:1,time:'09:00',endTime:'10:00'}]},
 plannerRoomOptions(...args){newCourseRoomArgs=args;return [{name:'Labo',type:'science',capacity:30,equipment:['vidéoprojecteur']}]},
 DAYS:['Lundi','Mardi','Mercredi','Jeudi','Vendredi'],
 esc:roomTestEsc,
 jsArg(value){return roomTestEsc(JSON.stringify(String(value??'')))},
 openModal(title,body){newCourseModal={title,body}},
 toast(message){throw Error(message)}
};
vm.createContext(newCourseContext);
vm.runInContext(runPlannerUi,newCourseContext);
newCourseContext.runPlanner({preventDefault(){},target:{}});
assert.strictEqual(newCourseRoomArgs[0],26,'Le nouveau cours doit utiliser l’effectif de sa classe pour filtrer les salles.');
assert.strictEqual(newCourseRoomArgs[2],1,'Le moteur doit chercher les salles sur chacun des créneaux proposés.');
assert(newCourseModal.title.includes('Créneaux et salles compatibles'),'La recherche d’un nouveau créneau doit aussi présenter les salles.');
assert(newCourseModal.body.includes('Choisir Labo'),'Chaque créneau proposé doit offrir un choix de salle.');
assert(newCourseModal.body.includes('plannerCreateDraft(&quot;1&quot;,&quot;09:00&quot;,&quot;10:00&quot;,&quot;6A&quot;,&quot;t1&quot;,&quot;SES&quot;,&quot;Labo&quot;)'),'La création doit transmettre le créneau, la classe, le professeur, la matière et la salle au nouveau formulaire.');
assert(app.includes('scheduleAvailabilityConflicts(c)'),'La validation du formulaire de cours doit aussi vérifier les indisponibilités.');
assert(app.includes('slot.room=name;slot.roomId=roomId'),'Renommer une salle doit préserver les liens de ses créneaux.');
assert(app.includes("confirmModal(message,'Supprimer la salle'"),'La suppression d’une salle liée doit demander confirmation.');
const cssStart=html.indexOf('<style id="v2520-settings-and-release-notes">');
assert(cssStart>=0,'La grille Paramètres doit être définie dans une feuille de style active.');
const cssEnd=html.indexOf('</style>',cssStart);
const css=html.slice(cssStart,cssEnd);
assert(css.includes('grid-template-columns:minmax(220px,.95fr) minmax(300px,1.15fr) minmax(250px,1fr)'),'La grille Paramètres desktop doit comporter trois colonnes.');
assert(css.includes('@media(max-width:900px)')&&css.includes('grid-template-columns:repeat(2,minmax(0,1fr))'),'La grille Paramètres doit passer à deux colonnes sur largeur intermédiaire.');
assert(css.includes('@media(max-width:650px)')&&css.includes('grid-template-columns:minmax(0,1fr)'),'La grille Paramètres doit passer à une colonne sur mobile.');
assert(css.includes('.settingsAppearanceCard{grid-area:appearance')&&css.includes('.settingsPeriodsCard{grid-area:periods')&&css.includes('.settingsRoomsCard{grid-area:rooms'),'Les cartes doivent utiliser des zones sémantiques.');
assert(css.includes('.settingsUpdateCard{grid-area:updates'),'La carte des mises à jour Direction doit avoir sa propre zone.');
assert(html.trimEnd().endsWith('</html>'),'Aucun bloc CSS ne doit apparaître après la fermeture du document.');
console.log('OK — Planner et salles : groupes parallèles, professeurs, indisponibilités, capacité, équipements, réservations, liens et grille Paramètres.');
