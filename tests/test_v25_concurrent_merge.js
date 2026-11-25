#!/usr/bin/env node
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=source.indexOf('function copyData('),end=source.indexOf('\nfunction syncHasLocalWork()',start);
assert(start>=0&&end>start,'generic application merge helper must exist');
const context={JSON,Set,Map,Symbol};
vm.createContext(context);
vm.runInContext(source.slice(start,end),context);
const base={
  evaluations:[{id:'e1',title:'Contrôle',grades:[{studentId:'s1',value:10},{studentId:'s2',value:12}]}],
  mailboxV2:{messages:[{id:'m1',body:'Message initial'}],states:{}},
  bulletins:[{id:'b1',overall:'Avis initial'}]
};
const local=JSON.parse(JSON.stringify(base));
local.evaluations[0].grades[0].value=15;
local.evaluations[0].title='Contrôle de calcul';
local.mailboxV2.messages.push({id:'m2',body:'Message créé sur le poste A'});
const remote=JSON.parse(JSON.stringify(base));
remote.evaluations[0].grades[1].value=14;
remote.mailboxV2.messages.push({id:'m3',body:'Message créé sur le poste B'});
remote.bulletins[0].overall='Avis modifié à distance';
const merged=context.mergeConcurrentData(base,local,remote);
assert.strictEqual(JSON.stringify(merged.conflicts),'[]','independent records and fields must merge');
assert.strictEqual(merged.value.evaluations[0].title,'Contrôle de calcul');
assert.strictEqual(merged.value.evaluations[0].grades.find(x=>x.studentId==='s1').value,15);
assert.strictEqual(merged.value.evaluations[0].grades.find(x=>x.studentId==='s2').value,14);
assert.strictEqual(JSON.stringify([...merged.value.mailboxV2.messages.map(x=>x.id)].sort()),JSON.stringify(['m1','m2','m3']));
assert.strictEqual(merged.value.bulletins[0].overall,'Avis modifié à distance');
const sameFieldRemote=JSON.parse(JSON.stringify(base));
sameFieldRemote.evaluations[0].grades[0].value=13;
const conflict=context.mergeConcurrentData(base,local,sameFieldRemote);
assert.ok(conflict.conflicts.some(x=>x.includes('studentId=s1')),'same grade changed on two posts must be flagged');
assert.strictEqual(conflict.value.evaluations[0].grades.find(x=>x.studentId==='s1').value,15,
 'local work remains in memory when a same-field conflict is detected');
const bothInsert=JSON.parse(JSON.stringify(base));
const localInsert=JSON.parse(JSON.stringify(base)),remoteInsert=JSON.parse(JSON.stringify(base));
localInsert.mailboxV2.messages.push({id:'m-local',body:'local'});
remoteInsert.mailboxV2.messages.push({id:'m-remote',body:'remote'});
const inserted=context.mergeConcurrentData(bothInsert,localInsert,remoteInsert);
assert.strictEqual(JSON.stringify(inserted.conflicts),'[]');
assert.strictEqual(JSON.stringify([...inserted.value.mailboxV2.messages.map(x=>x.id)].sort()),JSON.stringify(['m-local','m-remote','m1']));
console.log('OK — fusion inter-postes : modifications indépendantes combinées, même champ signalé, ajouts conservés.');
