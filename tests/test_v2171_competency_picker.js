const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const js=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=js.indexOf('function v217CompetencyLibraryItems');
const end=js.indexOf('function evaluationModelCriterionMax',start);
assert(start>=0&&end>start,'V21.17.1 competency picker helpers missing');
const ctx={window:{},document:{querySelectorAll:()=>[]},competencyLevels:()=>({}),db:{competencyLibrary:[
 {id:'1',name:'Calculer avec les fractions',level:'5e',subject:'Mathématiques'},
 {id:'2',name:'Résoudre un problème',level:'5e',subject:'Mathématiques'},
 {id:'3',name:'Lire un texte',level:'5e',subject:'Français'},
 {id:'4',name:'Compétence historique',level:'4e',subject:'Histoire'},
 'Ancienne compétence'
]}};
vm.createContext(ctx);vm.runInContext(js.slice(start,end),ctx);
let items=ctx.v217CompetencyLibraryItems().filter(c=>ctx.v217CompetencyMatches(c,'5e','Mathématiques'));
assert.deepStrictEqual(items.map(x=>x.name),['Calculer avec les fractions','Résoudre un problème','Ancienne compétence']);
items=ctx.v217CompetencyLibraryItems().filter(c=>ctx.v217CompetencyMatches(c,'5e','Français'));
assert.deepStrictEqual(items.map(x=>x.name),['Lire un texte','Ancienne compétence']);
assert.strictEqual(ctx.v217CompetencyMatches({name:'x',level:'5e',subject:'Mathématiques'},'4e','Mathématiques'),false);
const deep=js.slice(start, js.lastIndexOf('window.evaluations=function'));
for(const needle of ['v217RenderCompetencyPicker','Tout sélectionner','Tout désélectionner','Rechercher une compétence','niveau et la matière','v217DeepEditTemplate']) assert(deep.includes(needle),`missing picker UX: ${needle}`);
console.log('OK — V21.17.1 sélection compétences : filtrage niveau/matière, compatibilité anciennes compétences et sélection simple.');
