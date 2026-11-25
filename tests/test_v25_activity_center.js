const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('_all.js','utf8');
const start=source.indexOf('function activity(){');
const end=source.indexOf('\nfunction auditEvent',start);
assert(start>=0&&end>start,'Le Centre d’activité doit être présent');
const context={
  appSpace:'teacher',
  activityData:()=>({missingGrades:[],submissions:[],missing:[],unjust:[],upcoming:[]}),
  db:{evaluations:[],auditLog:[{id:'audit-1',at:'2026-11-25T10:00:00Z',actor:'Prof Test',action:'Évaluation créée',detail:'Mathématiques'}]},
  iso:()=> '2026-11-25',
  dayOcc:()=>[],
  notificationFeed:()=>[],
  cls:()=>null,
  isActivityRead:()=>false,
  activityFilter:'all',
  jsArg:value=>JSON.stringify(String(value??'')),
  jsObjectArg:value=>JSON.stringify(value??null),
  esc:value=>String(value??''),
  fmtDate:value=>String(value??''),
  shell:(section,title,description,actions='')=>'<div class="shell">'+String(actions||'')+'</div>',
  time:value=>String(value??'').slice(0,5),
  unreadConversationCount:()=>0
};
vm.createContext(context);
vm.runInContext(source.slice(start,end),context);
const html=context.activity();
const headings=html.match(/<h2>Aujourd’hui<\/h2>/g)||[];
assert.strictEqual(headings.length,1,
  'Le Centre d’activité ne doit présenter qu’un seul bloc « Aujourd’hui ».');
assert(html.includes('id="activityToday"'),
  'Le bouton « Voir la journée » doit garder sa cible principale.');
assert(html.includes("getElementById('activityToday')"),
  'Le bouton « Voir la journée » doit continuer à pointer vers le bloc conservé.');
assert(html.includes('Cours, notes, rendus et messages au même endroit'),
  'Le bloc principal doit conserver son rôle de synthèse.');
assert(html.includes('À traiter')&&html.includes('Activité récente'),
  'Les deux autres panneaux du Centre d’activité doivent rester visibles.');
assert(html.includes('Historique des actions')&&html.includes('Évaluation créée'),
  'Le Centre d’activité doit préserver l’historique des actions de l’ancienne vue quotidienne.');
assert(html.includes('onclick="downloadAuditLog()"'),
  'L’export de l’historique doit rester accessible depuis le Centre d’activité.');
assert(!source.includes('function today(){'),
  'L’ancienne vue quotidienne non routable ne doit pas subsister comme fonction morte.');
assert(source.includes("if(p==='today'||p==='notifications')p='activity'"),
  'Les anciennes entrées aujourd’hui/notifications doivent rester compatibles avec le Centre d’activité.');
assert(!html.includes('Votre planning et les accès rapides du jour'),
  'L’ancien second bloc dupliqué doit être retiré.');
console.log('OK — Centre d’activité : bloc Aujourd’hui, actions, activité récente et historique consolidés ; ancienne vue quotidienne morte retirée.');
