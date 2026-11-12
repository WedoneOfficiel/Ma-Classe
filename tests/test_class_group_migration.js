const fs = require('fs');
const vm = require('vm');
const path = require('path');
const assert = require('assert');
const sourcePath = process.argv[2] || path.join(__dirname, '..', '_all.js');
const source = fs.readFileSync(sourcePath, 'utf8');
const helper = source.split(/\r?\n/).find(line => line.startsWith('function reconcileStudentGroupsForClass('));
assert(helper, 'reconcileStudentGroupsForClass exists');
const ctx = { Set, String };
vm.runInNewContext(helper, ctx);
const reconcile = vm.runInNewContext('reconcileStudentGroupsForClass', ctx);

const oldClass = {id:'c1', name:'CM1-CM2', doubleLevel:true, levels:['CM1','CM2'], groups:['CM1-CM2/CM1','CM1-CM2/CM2']};
const renamed = {id:'c1', name:'Cycle 3', doubleLevel:true, levels:['CM1','CM2'], groups:['Cycle 3/CM1','Cycle 3/CM2']};
const students = [
  {id:'s1', classId:'c1', group:'CM1-CM2/CM1'},
  {id:'s2', classId:'c1', group:'CM1-CM2/CM2'},
  {id:'s3', classId:'c1', group:'CM1-CM2/CM3'},
  {id:'s4', classId:'c2', group:'CM1-CM2/CM1'}
];
reconcile(oldClass, renamed, students);
assert.strictEqual(students[0].group, 'Cycle 3/CM1');
assert.strictEqual(students[1].group, 'Cycle 3/CM2');
assert.strictEqual(students[2].group, '');
assert.strictEqual(students[3].group, 'CM1-CM2/CM1');

const oldNormal = {id:'c3', name:'CE2', doubleLevel:false, levels:[], groups:['Groupe A']};
const newNormal = {id:'c3', name:'CE2', doubleLevel:false, levels:[], groups:['Groupe B']};
const students2 = [{id:'s5', classId:'c3', group:'Groupe A'}, {id:'s6', classId:'c3', group:'Groupe B'}];
reconcile(oldNormal, newNormal, students2);
assert.strictEqual(students2[0].group, '');
assert.strictEqual(students2[1].group, 'Groupe B');

const toSingle = {id:'c1', name:'Cycle 3', doubleLevel:false, levels:[], groups:[]};
reconcile(renamed, toSingle, students);
assert.strictEqual(students[0].group, '');
assert.strictEqual(students[1].group, '');
console.log('OK — renommage de classe à double niveau, suppression des groupes invalides et absence de modification des élèves d’une autre classe.');
