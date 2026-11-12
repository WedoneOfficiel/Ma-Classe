const fs=require('fs'),assert=require('assert'),path=require('path');
const js=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const p=js.lastIndexOf('/* V21.17 DEEP UX');
assert(p>=0,'Deep UX block missing');
const ui=js.slice(p);
for(const needle of [
 'v217DeepOpenEvaluation','v217DeepSaveMeta','v217DeepEntry','v217DeepGradeKey',
 'inputmode="decimal"','v217DeepManageGrids','v217DeepApplyTemplate',
 'Gérer les grilles','Saisie rapide','Nouvelle évaluation'
]) assert(ui.includes(needle),`Missing deep UX element: ${needle}`);
assert(ui.includes('window.openEvaluation=window.v217DeepOpenEvaluation'),'openEvaluation not switched to deep UX');
assert(ui.includes('window.manageEvaluationGrids=window.v217DeepManageGrids'),'grid manager not switched to deep UX');
assert(ui.includes('Entrée</kbd> élève suivant'),'keyboard help missing');
console.log('OK — V21.17 deep UX: creation flow, compact grid, keyboard-first grade entry and simplified grid library.');
