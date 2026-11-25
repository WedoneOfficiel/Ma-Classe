const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('_all.js','utf8');
const start=source.indexOf('function documentInventory()');
const end=source.indexOf('\nfunction docDate',start);
assert(start>=0&&end>start,'Le catalogue documentaire doit être présent.');
const context={
  db:{
    lessons:[{id:'lesson-1',classId:'class-1',subject:'Français',homework:{title:'Réponse'}}],
    conversations:[],
    submissions:[{
      id:'sub-1',lessonId:'lesson-1',studentId:'student-1',
      files:[
        {name:'reponse.pdf',url:'/data/uploads/submissions/student-1/reponse.pdf'},
        {name:'annexe.txt',url:'/data/uploads/submissions/student-1/annexe.txt'}
      ]
    }]
  },
  student:id=>({id,first:'Alice',last:'Test'}),
  submissionFiles:sub=>Array.isArray(sub.files)?sub.files:(sub.file?[sub.file]:[])
};
vm.createContext(context);
vm.runInContext(source.slice(start,end),context);
const result=context.documentInventory();
assert.strictEqual(result.length,2,'Tous les fichiers d’un rendu doivent être ajoutés au catalogue, pas seulement sub.file.');
assert.strictEqual(JSON.stringify(Array.from(result,x=>x.file.name).sort()),JSON.stringify(['annexe.txt','reponse.pdf']));
assert.ok(result.every(x=>x.kind==='Rendu élève'&&x.classId==='class-1'));
assert.notStrictEqual(result[0].key,result[1].key,'Chaque pièce jointe doit garder une identité distincte dans l’arborescence.');
console.log('OK — Documents : toutes les pièces jointes de chaque rendu sont inventoriées séparément.');
