const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=src.lastIndexOf('/* V21.04 — messagerie reconstruite');
assert(start>=0,'Module V21.04 présent');
const ctx={
 db:{mailboxV2:null,conversations:[{id:'legacy'}],messages:[],mailFolders:[],students:[{id:'s1',first:'Camille',last:'Test',classId:'c1'},{id:'s2',first:'Alex',last:'Autre',classId:'c1'}],teachers:[{id:'t1',first:'Prof',last:'Test',active:true},{id:'t2',first:'Autre',last:'Prof',active:true}]},
 window:{},document:{createElement:()=>({}),head:{appendChild(){}}},
 esc:x=>String(x??''),activeStudent:()=> 's1',currentTeacherId:()=> 't1',
 student:id=>ctx.db.students.find(x=>x.id===id)||null,teacherUser:id=>ctx.db.teachers.find(x=>x.id===(id||'t1'))||ctx.db.teachers[0],teacherName:t=>(t.first+' '+t.last).trim(),
 accessibleTeachersForStudent:()=>[{id:'t1',first:'Prof',last:'Test'}],teacherCanReachStudent:()=>true,cls:()=>({name:'Classe'}),
 uid:(()=>{let n=0;return()=>`id${++n}`})(),save(){},toast(){},render(){},closeModal(){},openModal(){},shell:()=>'',notificationFeed:()=>[],page:'messages',authUser:{role:'teacher',teacherId:'t1'},
 messages(){},studentMessages(){},go(){},studentHome(){return ''},upload:async()=>({name:'file.pdf',url:'/file.pdf',size:12}),console
};
vm.createContext(ctx);vm.runInContext("'use strict'; function messages(){}; function studentMessages(){};\n"+src.slice(start),ctx);
const model=ctx.window.mailV2Model;
model.activate();assert.equal(ctx.db.conversations.length,0,'la réinitialisation ne touche que les anciens objets de messagerie');
const original=model.sendOne({role:'student',sid:'s1',to:['teacher:t1'],bcc:['student:s2'],subject:'Question',body:'Bonjour'});
assert.equal(model.folderMessages('teacher','').length,1,'le professeur reçoit le message');
assert.equal(model.folderMessages('student','s1').length,0,'le message envoyé ne revient pas dans la réception de l’élève');
assert.equal(model.folderMessages('student','s1').length,0);
const reply={sender:{key:'teacher:t1',role:'teacher',id:'t1',name:'Prof Test'},to:['student:s1'],cc:[],bcc:[],subject:'Re: Question',body:'Réponse',attachments:[],sentAt:new Date().toISOString()};
const sent=model.copyOriginalForReply(original,reply,{to:reply.to,cc:[]});
assert.equal(model.threadFor(sent,'student','s1').length,2,'la réponse crée un nouvel échange avec copie de l’original et réponse');
assert.equal(model.threadFor(sent,'teacher','').length,2,'les deux messages sont consultables par l’expéditeur de la réponse');
assert.equal(model.threadFor(sent,'student','s1')[0].copiedFrom,original.id,'la copie conserve une référence à l’original');
const copy=model.threadFor(sent,'student','s1')[0];assert.deepEqual(Array.from(copy.bcc),[],'les CCI ne sont jamais copiées dans le nouvel échange');
assert.equal(model.canSee(copy,'student:s2'),false,'un destinataire CCI de l’original ne voit pas la copie s’il ne reçoit pas la réponse');
assert.equal(model.folderMessages('student','s1').length,1,'la réponse arrive dans la réception comme un échange unique');
const replyWithBcc={...reply,id:'',threadId:'',to:['student:s1'],cc:[],bcc:['student:s2'],subject:'Re: Question',body:'Réponse confidentielle',attachments:[],sentAt:new Date().toISOString()};
const sentWithBcc=model.copyOriginalForReply(original,replyWithBcc,{to:replyWithBcc.to,cc:[]});const copiedForBcc=model.threadFor(sentWithBcc,'student','s2')[0];assert(copiedForBcc,'un destinataire CCI de la réponse peut consulter le contexte qui lui a été envoyé');assert.deepEqual(Array.from(copiedForBcc.bcc),[],'la copie visible au destinataire CCI ne révèle aucune liste CCI');
assert.equal(original.bcc[0],'student:s2','le message d’origine reste intact');
model.state(sent,'student:s1').read=true;assert.equal(model.state(sent,'teacher:t1').read,true,'l’état de lecture est indépendant et le professeur a déjà lu son envoi');
model.state(sent,'student:s1').folder='archive';assert.equal(model.state(sent,'teacher:t1').folder,'sent','l’archivage d’un compte ne modifie pas l’autre compte');
const f={dataset:{},elements:{to:{value:'student:s1'},subject:{value:'Brouillon'},body:{value:'À reprendre'}},querySelectorAll:()=>[]};
ctx.window.mailV2104DraftInput({target:{form:f}},'teacher','','','new','');
assert.equal(ctx.db.mailboxV2.drafts.length,1,'le brouillon est enregistré dans le stockage');assert.equal(ctx.db.mailboxV2.drafts[0].body,'À reprendre');
const rendered=ctx.window.messages();assert(rendered.includes('v2104App'),'la page enseignant se rend sans exception');assert(rendered.includes('v2104Reader'),'le panneau de lecture est présent');
console.log('OK — V21.04 : copie originale + réponse, référence source, CCI protégées, accès restreint, dossiers et lecture indépendants, brouillon persistant.');
