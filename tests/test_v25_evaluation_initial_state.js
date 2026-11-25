const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('_all.js','utf8');
const dashboardStart=source.indexOf('function v217EvaluationDashboard(');
const pageStart=source.indexOf('function evaluations()',dashboardStart);
const pageEnd=source.indexOf('\nfunction renderEvalList()',pageStart);
assert(dashboardStart>=0&&pageStart>dashboardStart&&pageEnd>pageStart,
  'Le moteur Évaluations et sa page doivent être présents');

const context={
  window:{classContext:''},
  db:{classes:[{id:'class-1',name:'6e A'}],evaluations:[]},
  $:()=>null, // The page is rendered before its select elements exist in the DOM.
  shell:(section,title,description,actions='')=>'<header>'+String(actions||'')+'</header>',
  esc:value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char])),
  jsArg:value=>JSON.stringify(String(value??'')),
  evaluationModelDashboardStats:()=>({all:0,entered:0,average:null,students:1}),
  evaluationModelMaxScore:()=>20,
  evalAverage:()=>0,
  fmtDate:value=>String(value??'')
};
vm.createContext(context);
vm.runInContext(source.slice(dashboardStart,pageEnd),context);

let html=context.evaluations();
assert(html.includes('<option value="class-1" selected>6e A</option>'),
  'La classe par défaut doit être sélectionnée dans le filtre visible.');
assert(html.includes('Aucune évaluation.'),
  'Une classe sélectionnée sans évaluation doit afficher son véritable état vide.');
assert(!html.includes('Sélectionne une classe pour afficher les évaluations.'),
  'La page ne doit pas afficher le message de sélection quand la classe est déjà sélectionnée.');

context.window.classContext='class-1';
html=context.evaluations();
assert(html.includes('<option value="class-1" selected>6e A</option>'),
  'Le contexte de classe courant doit être respecté à l’ouverture.');
assert(!html.includes('Sélectionne une classe pour afficher les évaluations.'));

context.window.classContext='deleted-class';
html=context.evaluations();
assert(html.includes('<option value="class-1" selected>6e A</option>'),
  'Un ancien contexte devenu invalide doit retomber sur la première classe disponible.');
assert(html.includes('Aucune évaluation.'));

context.db.classes=[];
html=context.evaluations();
assert(html.includes('Sélectionne une classe pour afficher les évaluations.'),
  'Le message de sélection doit rester lorsque l’établissement ne contient aucune classe.');
console.log('OK — Évaluations : classe initiale cohérente avec le tableau de bord, filtre invalide et établissement sans classe.');
