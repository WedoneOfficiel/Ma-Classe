const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=source.indexOf('async function uploadWorkFiles(');
const end=source.indexOf('\nasync function uploadLessonFiles(',start);
assert(start>=0&&end>start,'homework attachment upload handler must exist');
const handler=source.slice(start,end);
async function scenario({fail=false}={}){
 const messages=[],refresh=[];
 const context={
  lessonDraft:{sid:'slot-1',date:'2026-11-16',files:[],workFiles:[]},
  captureLessonDraft(){},
  upload:async(file,folder)=>{assert.strictEqual(folder,'submissions/slot-1');if(fail&&file.name==='refuse.pdf')throw Error('Accès refusé (403)');return {name:'submissions/slot-1/'+file.name,url:'/data/uploads/submissions/slot-1/'+file.name,size:file.size}},
  refreshDraftFileList:kind=>refresh.push(kind),
  toast:message=>messages.push(message)
 };
 vm.createContext(context);vm.runInContext(handler,context);
 await context.uploadWorkFiles('slot-1','2026-11-16',[{name:'consigne.pdf',size:1200},{name:fail?'refuse.pdf':'annexe.pdf',size:800}]);
 return {context,messages,refresh};
}
(async()=>{
 const ok=await scenario();
 assert.strictEqual(ok.context.lessonDraft.workFiles.length,2,'uploaded homework files must be retained in the lesson draft');
 assert(ok.messages.some(x=>x.includes('2 pièce(s) jointe(s) ajoutée(s)')),'success feedback must be explicit');
 assert.strictEqual(ok.refresh.length,2,'file list must refresh after each uploaded file');
 const failed=await scenario({fail:true});
 assert.strictEqual(failed.context.lessonDraft.workFiles.length,1,'a failed upload must not create a phantom attachment');
 assert(failed.messages.some(x=>x.includes('Accès refusé (403)')),'the server error must be surfaced instead of a generic failure');
 const repeated=await scenario();
 await repeated.context.uploadWorkFiles('slot-1','2026-11-16',[{name:'consigne.pdf',size:1200}]);
 assert.strictEqual(repeated.context.lessonDraft.workFiles.filter(x=>x.name.endsWith('consigne.pdf')).length,1,'reselecting an already attached file must not duplicate it');
 console.log('OK — pièces jointes des devoirs : dépôt, erreurs détaillées, absence de doublon et conservation dans le brouillon.');
})().catch(error=>{console.error(error);process.exitCode=1;});
