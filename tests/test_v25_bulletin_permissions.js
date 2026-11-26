const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=source.lastIndexOf('function canEditBulletinSubject(');
const end=source.indexOf('\nfunction setBulletinComment(',start);
assert(start>=0&&end>start,'term-aware bulletin permission helper must exist');
const helper=source.slice(start,end);

function contextFor({schedule=[],teacherAssignments=[],profileSubjects=['Mathématiques'],classTeacherIds=['teacher-1'],principalTeacherId='teacher-1',teacherId='teacher-1'}={}){
  const period={id:'term-old',start:'2025-09-01',end:'2025-12-20'};
  const context={
    authUser:{role:'teacher'},
    db:{schedule,teacherAssignments},
    currentTeacherProfile:()=>({id:teacherId,subjects:profileSubjects}),
    sameId:(a,b)=>{const x=String(a??'').trim(),y=String(b??'').trim();return !!x&&x===y},
    iso:()=> '2026-11-15',
    term:id=>id===period.id?period:null,
    cls:()=>({teacherIds:classTeacherIds,principalTeacherId}),
    teacherScheduleSuspended:(slot,tid,date)=>{
      const override=(slot.overrides||{})[date];
      if(override?.replacementTeacherId&&override.replacementTeacherId!==tid)return true;
      return teacherAssignments.some(a=>a.type==='replacement'&&a.classId===slot.classId&&a.subject===slot.subject&&a.supersedesTeacherId===tid&&(!a.startDate||a.startDate<=date)&&(!a.endDate||date<=a.endDate));
    }
  };
  vm.createContext(context);
  vm.runInContext(helper,context);
  return context;
}

const historical=contextFor({
  schedule:[{id:'slot-1',classId:'class-1',subject:'Mathématiques',teacherId:'teacher-1'}],
  teacherAssignments:[{id:'replacement-now',classId:'class-1',subject:'Mathématiques',teacherId:'teacher-2',supersedesTeacherId:'teacher-1',type:'replacement',startDate:'2026-01-01',endDate:'2026-12-31'}]
});
assert.strictEqual(historical.canEditBulletinSubject('class-1','Mathematiques','term-old'),true,
  'current replacement must not block the teacher from a past term they taught');

const substitute=contextFor({
  schedule:[{id:'slot-2',classId:'class-1',subject:'Mathématiques',teacherId:'teacher-2',overrides:{'2025-10-14':{replacementTeacherId:'teacher-1'}}}]
});
assert.strictEqual(substitute.canEditBulletinSubject('class-1','Mathématiques','term-old'),true,
  'a one-off replacement during the bulletin term must be allowed');

const unrelated=contextFor({
  schedule:[{id:'slot-3',classId:'class-1',subject:'Mathématiques',teacherId:'teacher-2'}],
  profileSubjects:[],classTeacherIds:[],principalTeacherId:''
});
assert.strictEqual(unrelated.canEditBulletinSubject('class-1','Mathématiques','term-old'),false,
  'an unrelated teacher must not be allowed to edit the subject appreciation');

const mixedPrincipal=contextFor({
  teacherId:123,
  classTeacherIds:[123],
  principalTeacherId:123
});
assert.strictEqual(mixedPrincipal.canEditBulletinSubject('1','Mathématiques','term-old'),true,
  'numeric teacher and class IDs must still authorize a PP/teacher to edit their subject appreciation.');

const mixedSchedule=contextFor({
  teacherId:123,
  classTeacherIds:[],
  principalTeacherId:'',
  schedule:[{id:'slot-mixed',classId:1,subject:'Mathématiques',teacherIds:[123]}]
});
assert.strictEqual(mixedSchedule.canEditBulletinSubject('1','Mathématiques','term-old'),true,
  'numeric class/teacher IDs in the timetable must retain the historical subject permission.');

const mixedAssignment=contextFor({
  teacherId:123,
  classTeacherIds:[],
  principalTeacherId:'',
  teacherAssignments:[{id:'assign-mixed',classId:1,subject:'Mathématiques',teacherId:123,startDate:'2025-09-01',endDate:'2025-12-20'}]
});
assert.strictEqual(mixedAssignment.canEditBulletinSubject('1','Mathématiques','term-old'),true,
  'numeric class/teacher IDs in explicit teacher assignments must retain the permission.');

console.log('OK — droits d’appréciation : période passée, accents, remplacement ponctuel et refus hors affectation.');
