const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=source.indexOf('async function studentAddSubmissionFiles(');
const end=source.indexOf('\nasync function studentRemoveSubmissionFile',start);
assert(start>=0&&end>start,'student submission upload handler must exist');
const handler=source.slice(start,end);

async function runScenario({uploadFails=false}={}){
  const db={lessons:[{id:'lesson-1',classId:'class-1',homework:{requiresSubmission:true}}],submissions:[]};
  const messages=[];
  const input={files:[{name:'devoir.pdf',size:2048}],click(){this.pending=this.onchange()}};
  const context={
    db,
    student:id=>({id,classId:'class-1'}),
    studentWorkEligible:()=>true,
    document:{createElement:tag=>{assert.strictEqual(tag,'input');return input;}},
    upload:async(file,directory)=>{assert.strictEqual(directory,'submissions/student-1');if(uploadFails)throw new Error('Upload refusé');return {name:file.name,size:file.size,url:'/uploads/devoir.pdf'};},
    uid:()=>'draft-1',
    studentDraftSubmission:(lessonId,studentId)=>db.submissions.find(x=>x.lessonId===lessonId&&x.studentId===studentId&&x.status==='draft'),
    save:()=>{},
    flushPendingSave:async()=>{},
    api:async()=>db,
    normalize:()=>{},
    openStudentWork:()=>{},
    toast:message=>messages.push(message)
  };
  vm.createContext(context);
  vm.runInContext(handler,context);
  await context.studentAddSubmissionFiles('lesson-1','student-1');
  await input.pending;
  return {db,messages,input};
}
(async()=>{
  const success=await runScenario();
  assert.strictEqual(success.db.submissions.length,1,'successful upload must create a student draft');
  assert.strictEqual(success.db.submissions[0].files[0].name,'devoir.pdf','uploaded file must be attached to the draft');
  assert(success.messages.some(x=>x.includes('ajouté')||x.includes('enregistré')),'successful upload must report confirmation');
  const failure=await runScenario({uploadFails:true});
  assert.strictEqual(failure.db.submissions.length,0,'failed upload must not create an empty draft');
  assert(failure.messages.some(x=>x.includes('Upload refusé')),'upload error must be shown to the student');
  console.log('OK — ajout de pièce jointe à un devoir : succès, sauvegarde du brouillon et erreur téléversement.');
})().catch(error=>{console.error(error);process.exitCode=1;});
