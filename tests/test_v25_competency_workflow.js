const fs=require('fs');
const assert=require('assert');
const path=require('path');
const vm=require('vm');

const root=path.join(__dirname,'..');
const app=fs.readFileSync(path.join(root,'_all.js'),'utf8');
new vm.Script(app,{filename:'_all.js'});

assert(app.includes("function v217OpenCompetencyManager("),
  'Un référentiel de compétences accessible doit exister.');
assert(app.includes('Référentiel de compétences')&&app.includes('onclick="v217OpenCompetencyManager()"'),
  'La page Évaluations doit donner un accès direct au référentiel.');
assert(app.includes('onclick="v217OpenCompetencyManager(true,null,this)"'),
  'La création d’une compétence doit être accessible depuis une évaluation.');
assert(app.includes('Créer ou gérer les compétences'),
  'Le formulaire d’évaluation doit proposer une action claire pour créer une compétence.');
assert(app.includes('Aucune compétence n’est encore disponible')&&app.includes('+ Créer une compétence'),
  'Une liste vide doit proposer immédiatement la création au lieu de renvoyer vers une bibliothèque introuvable.');
assert(app.includes('data-v217-meta="1"')&&app.includes('window.v217CompetencyReturnDraft'),
  'Le formulaire d’évaluation doit être sauvegardé puis restauré après la création d’une compétence.');
assert(app.includes("level=explicitLevel||cls(classId)?.level||''"),
  'La liste doit utiliser le niveau de la classe sélectionnée même si aucun champ niveau séparé n’existe.');
assert(app.includes("v217EnsureCompetencyEntry(c,o.level,o.subject"),
  'Les compétences sélectionnées dans une évaluation doivent être ajoutées sans doublons au référentiel.');
assert(app.includes("v217EnsureCompetencyEntry(c,level,subject"),
  'Les compétences d’une grille doivent être ajoutées sans doublons au référentiel.');

const coreStart=app.indexOf('function v217CompetencyLibraryItems(){');
const coreEnd=app.indexOf('function evaluationModelCriterionMax(c)',coreStart);
assert(coreStart>=0&&coreEnd>coreStart,'Le moteur du référentiel doit pouvoir être isolé pour test.');
let counter=0;
const sandbox={
  window:{},
  db:{competencyLibrary:[],evaluationTemplates:[],evaluations:[],classes:[],settings:{competencyLevels:{}}},
  uid:()=> 'competency-test-'+(++counter),
  competencyLevels:()=>sandbox.db.settings.competencyLevels,
  esc:value=>String(value??''),
  cls:()=>null,
  jsArg:value=>JSON.stringify(value),
  document:{querySelectorAll:()=>[],querySelector:()=>null,getElementById:()=>null},
  openModal:()=>{},
  setWide:()=>{},
  FormData:class{}
};
vm.createContext(sandbox);
vm.runInContext(app.slice(coreStart,coreEnd),sandbox);

sandbox.db.evaluationTemplates=[{competencies:['Compétence historique de grille']}];
sandbox.db.evaluations=[{competencies:['Compétence historique d’évaluation']}];
vm.runInContext('v217EnsureLegacyCompetencies()',sandbox);
assert(sandbox.db.competencyLibrary.includes('Compétence historique de grille'),
  'Les compétences présentes dans les anciennes grilles doivent être rapatriées au référentiel.');
assert(sandbox.db.competencyLibrary.includes('Compétence historique d’évaluation'),
  'Les compétences déjà utilisées dans les anciennes évaluations doivent être rapatriées.');

const created=vm.runInContext("v217EnsureCompetencyEntry('Argumenter une réponse','6e|5e','Français','Justifier avec un élément du cours.')",sandbox);
assert.strictEqual(created.name,'Argumenter une réponse');
assert.strictEqual(created.level,'6e|5e');
assert.strictEqual(created.subject,'Français');
assert.strictEqual(created.description,'Justifier avec un élément du cours.');
assert(sandbox.db.competencyLibrary.includes('Argumenter une réponse'),
  'Le référentiel conserve les intitulés en chaînes compatibles avec la normalisation existante.');
assert.deepStrictEqual(Array.from(sandbox.db.settings.competencyLevels['Argumenter une réponse']),['6e','5e']);
assert.strictEqual(sandbox.db.settings.competencySubjects['Argumenter une réponse'],'Français');
assert.strictEqual(sandbox.db.settings.competencyDescriptions['Argumenter une réponse'],'Justifier avec un élément du cours.');

assert(vm.runInNewContext("v217CompetencyMatches(c,'5e','Français')",{
  v217CompetencyMatches:sandbox.v217CompetencyMatches,
  c:created
}));
assert(!vm.runInNewContext("v217CompetencyMatches(c,'3e','Français')",{
  v217CompetencyMatches:sandbox.v217CompetencyMatches,
  c:created
}));
assert(!vm.runInNewContext("v217CompetencyMatches(c,'5e','Mathématiques')",{
  v217CompetencyMatches:sandbox.v217CompetencyMatches,
  c:created
}));

sandbox.db.competencyLibrary.push('Compétence à dédoublonner');
sandbox.db.competencyLibrary.push({id:'duplicate-id',name:'Compétence à dédoublonner',level:'6e',subject:'Histoire'});
vm.runInNewContext("v217EnsureCompetencyEntry('Compétence à dédoublonner','6e','Français')",sandbox);
const duplicates=sandbox.db.competencyLibrary.filter(x=>String(typeof x==='string'?x:x.name).toLowerCase()==='compétence à dédoublonner');
assert.strictEqual(duplicates.length,1,'Le référentiel ne doit pas créer plusieurs entrées pour un même intitulé.');
assert(sandbox.db.competencyLibrary.some(x=>(typeof x==='string'?x:x.name)==='Argumenter une réponse'),
  'La compétence doit rester disponible dans la bibliothèque.');

const ratingStart=app.indexOf('function evaluationModelSetCompetency(');
const ratingEnd=app.indexOf('\n',ratingStart);
assert(ratingStart>=0&&ratingEnd>ratingStart,'Le moteur de saisie du niveau de maîtrise doit rester présent.');
const ratingSandbox={db:{evaluations:[{
  id:'evaluation-1',competencies:['Argumenter une réponse'],
  grades:[{studentId:'student-1',value:'14',competencyRatings:{'Autre compétence':'2'}}]
}]}};
vm.createContext(ratingSandbox);
vm.runInContext(app.slice(ratingStart,ratingEnd),ratingSandbox);
vm.runInContext("evaluationModelSetCompetency(db,'evaluation-1','student-1','Argumenter une réponse','3')",ratingSandbox);
let grade=ratingSandbox.db.evaluations[0].grades[0];
assert.strictEqual(grade.value,'14','La note chiffrée existante ne doit pas être modifiée par la compétence.');
assert.strictEqual(grade.competencyRatings['Argumenter une réponse'],'3','Le niveau de maîtrise doit être enregistré.');
assert.strictEqual(grade.competencyRatings['Autre compétence'],'2','Les autres compétences déjà évaluées doivent être conservées.');
vm.runInContext("evaluationModelSetCompetency(db,'evaluation-1','student-1','Argumenter une réponse','')",ratingSandbox);
grade=ratingSandbox.db.evaluations[0].grades[0];
assert(!Object.prototype.hasOwnProperty.call(grade.competencyRatings,'Argumenter une réponse'),
  'Effacer une maîtrise doit supprimer uniquement cette valeur.');
assert.strictEqual(grade.competencyRatings['Autre compétence'],'2');

console.log('OK — Référentiel accessible, migration/dédoublonnage, filtrage niveau/matière et notes de maîtrise conservées.');
