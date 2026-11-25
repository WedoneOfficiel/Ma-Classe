const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('_all.js','utf8');
const pageStart=source.indexOf('window.evaluations=function()');
const pageEnd=source.indexOf('\n  window.openEvaluation',pageStart);
assert(pageStart>=0&&pageEnd>pageStart,
  'Le point d’entrée Évaluations réellement utilisé doit être présent.');

const dashboardCalls=[];
const context={
  window:{classContext:''},
  db:{
    classes:[{id:'class-1',name:'6e A'},{id:'class-2',name:'5e B'}],
    evaluations:[
      {id:'e1',classId:'class-1',subject:'Français'},
      {id:'e2',classId:'class-2',subject:'Mathématiques'}
    ]
  },
  shell:(section,title,description,actions='')=>'<header>'+String(actions||'')+'</header>',
  esc:value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char])),
  jsArg:value=>JSON.stringify(String(value??'')),
  v217EvaluationDashboard:(classId,subject)=>{
    dashboardCalls.push([String(classId||''),String(subject||'')]);
    return classId?'Statistiques de '+classId:'Sélectionne une classe pour afficher les évaluations.';
  }
};
vm.createContext(context);
vm.runInContext(source.slice(pageStart,pageEnd),context);

let html=context.window.evaluations();
assert(html.includes('<option value="class-1" selected>6e A</option>'),
  'La première classe doit être sélectionnée dès la création du filtre.');
assert(html.includes('Statistiques de class-1'),
  'Le tableau de bord doit recevoir explicitement la classe initiale, sans lire un select qui n’existe pas encore.');
assert(!html.includes('Sélectionne une classe pour afficher les évaluations.'),
  'La page ne doit pas afficher un message contradictoire quand une classe est déjà sélectionnée.');
assert.deepStrictEqual(dashboardCalls.pop(),['class-1','']);

context.window.classContext='class-2';
html=context.window.evaluations();
assert(html.includes('<option value="class-2" selected>5e B</option>'),
  'Le contexte de classe valide doit être conservé à l’ouverture.');
assert(html.includes('Statistiques de class-2'));
assert.deepStrictEqual(dashboardCalls.pop(),['class-2','']);

context.window.classContext='deleted-class';
html=context.window.evaluations();
assert(html.includes('<option value="class-1" selected>6e A</option>'),
  'Un ancien contexte devenu invalide doit retomber sur la première classe disponible.');
assert(html.includes('Statistiques de class-1'));
assert.deepStrictEqual(dashboardCalls.pop(),['class-1','']);

context.db.classes=[];
context.window.classContext='';
html=context.window.evaluations();
assert(html.includes('Choisir une classe'));
assert(html.includes('Sélectionne une classe pour afficher les évaluations.'),
  'Le message doit rester lorsque l’établissement ne contient aucune classe.');
assert.deepStrictEqual(dashboardCalls.pop(),['','']);
console.log('OK — Évaluations actives : classe initiale et statistiques cohérentes, contexte invalide et établissement sans classe.');
