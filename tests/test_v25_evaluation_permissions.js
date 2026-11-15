const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
const start=source.lastIndexOf('function canEditEvaluation(');
const end=source.indexOf('\nfunction syncTeacherClassLinks(',start);
assert(start>=0&&end>start,'evaluation permission helper must exist');
const helper=source.slice(start,end);
function contextFor({schedule=[],teacherAssignments=[],profileSubjects=['Maths'],classTeacherIds=['teacher-1']}={}){
 const context={
  authUser:{id:'teacher-1',role:'teacher'},
  db:{schedule,teacherAssignments},
  currentTeacherProfile:()=>({id:'teacher-1',subjects:profileSubjects}),
  cls:()=>({teacherIds:classTeacherIds}),
  iso:()=> '2026-11-15',
  teacherScheduleSuspended:()=>false
 };
 vm.createContext(context);vm.runInContext(helper,context);return context;
}
const assigned=contextFor({schedule:[{id:'maths',classId:'class-1',subject:'Mathématiques',teacherId:'teacher-1'},{id:'french',classId:'class-1',subject:'Français',teacherId:'teacher-2'}]});
assert.strictEqual(assigned.canEditEvaluation({classId:'class-1',subject:'Mathematiques',date:'2026-11-10'}),true,'teacher may edit the subject they teach, accents ignored');
assert.strictEqual(assigned.canEditEvaluation({classId:'class-1',subject:'Français',date:'2026-11-10'}),false,'class access must not grant rights over another subject');
const replacement=contextFor({schedule:[{id:'slot',classId:'class-1',subject:'Maths',teacherId:'teacher-2',overrides:{'2026-11-10':{replacementTeacherId:'teacher-1'}}}]});
assert.strictEqual(replacement.canEditEvaluation({classId:'class-1',subject:'Maths',date:'2026-11-10'}),true,'one-off replacement grants access for its date');
const unrelated=contextFor({schedule:[{id:'slot',classId:'class-1',subject:'Français',teacherId:'teacher-2'}],profileSubjects:[],classTeacherIds:[]});
assert.strictEqual(unrelated.canEditEvaluation({classId:'class-1',subject:'Maths',date:'2026-11-10'}),false,'unrelated teacher must be denied');
console.log('OK — droits des évaluations : matière enseignée, accents, remplacement ponctuel et refus hors affectation.');
