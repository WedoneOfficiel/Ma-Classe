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

const runPlannerUi=sliceBetween(app,'function runPlanner(e)','function plannerCreateDraft(');
assert(runPlannerUi.includes('Choisir cette salle'),'Chaque salle trouvée doit proposer une action de sélection, pas seulement une ligne de texte.');
assert(runPlannerUi.includes('plannerCreateDraft('),'La sélection d’une salle doit ouvrir la préparation du cours.');
let capturedRoomModal=null;
const roomFinderContext={
 FormData:function(){return Object.entries({action:'room',capacity:'20',equipment:'vidéoprojecteur',day:'0',time:'14:00',duration:'60',classId:'6A',teacherId:'t1',subject:'SES'})[Symbol.iterator]()},
 mins(value){const p=String(value||'0:0').split(':').map(Number);return (p[0]||0)*60+(p[1]||0)},
 plannerRoomOptions(){return [{name:'B204',type:'classroom',capacity:30,equipment:['vidéoprojecteur']}]},
 plannerFindSlots(){return []},
 DAYS:['Lundi','Mardi','Mercredi','Jeudi','Vendredi'],
 esc(value){return String(value??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')},
 jsArg(value){return JSON.stringify(String(value??''))},
 openModal(title,body){capturedRoomModal={title,body}}
};
vm.createContext(roomFinderContext);
vm.runInContext(runPlannerUi,roomFinderContext);
roomFinderContext.runPlanner({preventDefault(){},target:{}});
assert(capturedRoomModal.body.includes('B204')&&capturedRoomModal.body.includes('Choisir cette salle'),'Le résultat doit afficher la salle créée et un bouton de sélection.');
assert(capturedRoomModal.body.includes('plannerCreateDraft(&quot;0&quot;,&quot;14:00&quot;,&quot;15:00&quot;,&quot;6A&quot;,&quot;t1&quot;,&quot;SES&quot;,&quot;B204&quot;)'),'Le bouton doit transmettre le créneau, la classe, le professeur, la matière et la salle dans un attribut HTML correctement échappé.');
const draftStart=app.indexOf('function plannerCreateDraft('),draftEnd=app.indexOf('\nfunction ',draftStart);
assert(draftStart>=0&&draftEnd>draftStart,'Le passage du Planner au formulaire de cours doit exister.');
let openedPlannerDraft=null;
const draftWindow={};
const draftContext={window:draftWindow,selectedWeek:new Date('2026-11-23T12:00:00'),iso(){return '2026-11-23'},closeModal(){},openSchedule(){openedPlannerDraft=draftWindow._scheduleDraft}};
vm.createContext(draftContext);
vm.runInContext(app.slice(draftStart,draftEnd),draftContext);
draftContext.plannerCreateDraft(0,'14:00','15:00','6A','t1','SES','B204');
assert.deepStrictEqual(JSON.parse(JSON.stringify(openedPlannerDraft)),{
 day:0,time:'14:00',endTime:'15:00',classId:'6A',classIds:['6A'],teacherId:'t1',teacherIds:['t1'],
 subject:'SES',room:'B204',recurrence:'weekly',startDate:'2026-11-23',endDate:'',exceptions:[]
},'Le formulaire doit recevoir les vrais noms de champs classIds/teacherIds et la salle choisie.');

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
