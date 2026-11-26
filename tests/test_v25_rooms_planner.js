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
