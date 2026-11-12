const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
assert.strictEqual((src.match(/function cloudCanWrite\(/g)||[]).length,1,'cloudCanWrite must have a single active definition');
assert(src.includes("let saveQueue=Promise.resolve()"),'save queue must serialize writes');
assert(src.includes("let dataRevision=null"),'client must retain the server data revision');
assert(src.includes("'If-Match':dataRevision||''"),'every full database save must send its loaded revision');
assert(src.includes('REVISION_CONFLICT'),'client must explain stale-save conflicts');
assert(src.includes('function cloudSearchInput(input)'), 'Cloud search must preserve focus after rendering');
assert(src.includes('function openInitialPasswordModal()'), 'temporary account passwords must be changed before use');
assert(src.includes("/api/auth/login"), 'login must be verified by the server');
assert(src.includes('function openAuthStudent()'), 'students must have an individual username/password login');
assert(src.includes('function saveStudentAccount(e)'), 'direction must be able to create individual student accounts');
assert(src.includes("/api/admin/student-account"), 'student credentials must be created and hashed server-side');
assert(src.includes("upload(file,'submissions/'+sid)"), 'student homework uploads must use the student-specific submission folder');
assert(src.includes("scheduleView==='week'?studentScheduleWeek(ds,occ):scheduleView==='day'?studentScheduleDay(sel,occ):studentScheduleMonth(sel,occ)"), 'student timetable must use read-only student event cards');
assert(src.includes('La messagerie élève arrive dans une prochaine étape'), 'unreviewed student messaging must remain unavailable');
assert(src.includes("for(const k of ['schedule','bulletins','attachments','conversations','teachers','subjects','cloudItems','mailFolders','users','notifications','auditLog','messages'])"),'all collections normalized defensively');
assert(src.includes("cls(defaultClass)?.attendanceMode==='hour'"),'attendance mode must use the stored hour value');
const singleDeleteStart=src.indexOf('function cloudDelete(){'),singleDeleteEnd=src.indexOf('function ',singleDeleteStart+10);
assert(singleDeleteStart>=0&&singleDeleteEnd>singleDeleteStart,'single Cloud delete handler exists');
const singleDelete=src.slice(singleDeleteStart,singleDeleteEnd);
assert(singleDelete.indexOf("await api('/api/cloud-delete'")<singleDelete.indexOf('db.cloudItems=db.cloudItems.filter'), 'physical Cloud deletion must succeed before metadata removal');
const start=src.lastIndexOf('function subjectAverage('),end=src.indexOf('\nfunction bulletinAttendance',start);
assert(start>=0&&end>start,'active bulletin subjectAverage found');
const modelStart=src.indexOf('function gradeNumber('),modelEnd=src.indexOf('function evaluationModelAverage',modelStart);
const context={db:{students:[{id:'s1',classId:'c1',group:'A'}],evaluations:[
 {id:'e1',classId:'c1',subject:'Maths',date:'2026-10-01',published:true,maxScore:10,coefficient:2,grades:[{studentId:'s1',value:'8'}]},
 {id:'e2',classId:'c1',subject:'Maths',date:'2026-10-02',published:false,maxScore:20,coefficient:1,grades:[{studentId:'s1',value:'20'}]},
 {id:'e3',classId:'c1',subject:'Maths',group:'B',date:'2026-10-03',published:true,maxScore:20,coefficient:1,grades:[{studentId:'s1',value:'20'}]},
 {id:'e4',classId:'c1',subject:'Maths',date:'2026-10-04',published:true,publishAt:'2999-01-01',maxScore:20,coefficient:1,grades:[{studentId:'s1',value:'20'}]}
 ]},term:()=>({start:'2026-09-01',end:'2026-12-31'}),student:id=>({id:'s1',classId:'c1',group:'A'}),iso:()=> '2026-11-12'};
vm.createContext(context);
vm.runInContext(src.slice(modelStart,modelEnd)+'\n'+src.slice(start,end),context);
assert.strictEqual(context.subjectAverage('s1','c1','Maths','t1'),'16.00','8/10 must become 16/20; unpublished, future and other-group grades excluded');
console.log('OK — V25 regressions: normalized bulletin average, publication/group filtering, save serialization and defensive collections.');
