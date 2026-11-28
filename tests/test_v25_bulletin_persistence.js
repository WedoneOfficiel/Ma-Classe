const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('_all.js','utf8');
const sameIdStart=source.indexOf('function sameId('),sameIdEnd=source.indexOf('\nfunction ',sameIdStart+10);
const start=source.indexOf('async function createAllBulletins('),end=source.indexOf('\nfunction bulletinSetView',start);
assert(start>=0&&end>start,'async persistent bulletin generation function must exist');
let saved=null,sequence=0,fail=false;
const context={
 db:{students:[{id:'s1',classId:'c1'},{id:'s2',classId:'c1'},{id:'s3',classId:'c2'}],bulletins:[]},
 bulletinFor:(sid,cid,tid)=>context.db.bulletins.find(b=>b.studentId===sid&&b.classId===cid&&b.termId===tid),
 uid:()=> 'bulletin-'+(++sequence),
 save:()=>{saved=JSON.stringify(context.db)},
 flushPendingSave:async()=>{if(fail)throw new Error('offline')},
 api:async()=>JSON.parse(saved),normalize:()=>{},render:()=>{},toast:()=>{}
};
vm.createContext(context);vm.runInContext(source.slice(sameIdStart,sameIdEnd)+'\n'+source.slice(start,end),context);
(async()=>{
 await context.createAllBulletins('c1','t1');
 assert.strictEqual(context.db.bulletins.length,2,'two students in the class must receive a bulletin');
 assert.strictEqual(JSON.parse(saved).bulletins.length,2,'the created bulletins must be persisted before the action completes');
 await context.createAllBulletins('c1','t1');
 assert.strictEqual(context.db.bulletins.length,2,'reopening/generating again must not duplicate existing bulletins');
 fail=true;
 await context.createAllBulletins('c2','t1');
 assert.strictEqual(context.db.bulletins.length,2,'a failed save must roll back the local additions');
 console.log('OK — bulletins persist before completion, generation is idempotent and failed saves roll back.');
})().catch(e=>{console.error(e);process.exitCode=1});
