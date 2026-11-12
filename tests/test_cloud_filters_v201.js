const fs = require('fs');
const vm = require('vm');
const path = require('path');
const assert = require('assert');
const source = fs.readFileSync(process.argv[2] || path.join(__dirname, '..', '_all.js'), 'utf8');
const start = source.indexOf('function cloudCurrentItems(');
const end = source.indexOf('function cloudSelect(', start);
assert(start >= 0 && end > start, 'cloudCurrentItems function found');
const db = { cloudItems: [
  {id:'f1',type:'folder',name:'Leçons',parentId:'',space:'personal',ownerId:'teacher-local'},
  {id:'p1',type:'file',name:'bilan.pdf',mime:'application/pdf',size:1024,parentId:'',space:'personal',ownerId:'teacher-local'},
  {id:'i1',type:'file',name:'photo.png',mime:'image/png',size:2048,parentId:'',space:'personal',ownerId:'teacher-local'},
  {id:'d1',type:'file',name:'fiche.docx',size:2048,parentId:'',space:'personal',ownerId:'teacher-local'}
]};
const window = {cloudSpace:'personal',cloudSort:'name'};
const ctx = {db,window,cloudAccessible:()=>db.cloudItems,cloudContext:()=>({space:'personal'}),cloudPathContextValid:()=>true,getCloudPath:()=>[],String,Array};
vm.createContext(ctx);
vm.runInContext(source.slice(start,end),ctx);
window.cloudTypeFilter='pdf';
assert.deepStrictEqual(Array.from(ctx.cloudCurrentItems('teacher','')).map(x=>x.id),['p1']);
window.cloudTypeFilter='image';
assert.deepStrictEqual(Array.from(ctx.cloudCurrentItems('teacher','')).map(x=>x.id),['i1']);
window.cloudTypeFilter='folder';
assert.deepStrictEqual(Array.from(ctx.cloudCurrentItems('teacher','')).map(x=>x.id),['f1']);
window.cloudTypeFilter='document';
assert.deepStrictEqual(Array.from(ctx.cloudCurrentItems('teacher','')).map(x=>x.id),['d1']);
console.log('OK — filtres Cloud PDF, images, documents et dossiers.');
