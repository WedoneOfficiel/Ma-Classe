const fs=require('fs');
const vm=require('vm');
const assert=require('assert');

const source=fs.readFileSync('_all.js','utf8');
function sliceBetween(startText,endText){
  const start=source.indexOf(startText);
  const end=source.indexOf(endText,start+startText.length);
  assert(start>=0&&end>start,'Missing source block: '+startText);
  return source.slice(start,end);
}

const sameId=sliceBetween('function sameId(','\nfunction cls(');
const studentAttendance=sliceBetween('function studentAttendance(','\nfunction openStudentBulletinNotification');
const studentScheduleOcc=sliceBetween('function studentScheduleOcc(','\nfunction studentLessonItems(');
const studentSubmitted=sliceBetween('function studentSubmitted(','\nfunction evaluationGradeLabel(');
const studentDraftSubmission=sliceBetween('function studentDraftSubmission(','\nfunction studentWorkEligible(');
const studentRows=sliceBetween('function studentRows(','\nfunction filterStudents');
const attendanceCounts=sliceBetween('function studentAbsenceCount(','\nfunction studentEvaluations');
const activeFollowupStart=source.lastIndexOf('function attendanceFollowup()');
const activeFollowupEnd=source.indexOf('\n\n/* MaClasse V20.8',activeFollowupStart);
assert(activeFollowupStart>=0&&activeFollowupEnd>activeFollowupStart,
  'The active attendance follow-up module must exist');
const attendanceFollowup=source.slice(activeFollowupStart,activeFollowupEnd);

const db={
  classes:[{id:42,name:'6e A'}],
  students:[{id:7,classId:42,group:'A',first:'Alice',last:'Martin',birth:'2014-04-03',email:'alice@example.test'}],
  attendance:[{
    id:'call-1',classId:42,date:'2026-11-25',mode:'hour',slotId:'slot-1',time:'09:00',
    rows:[
      {studentId:7,status:'absent',justified:false,reason:'Non justifiée'},
      {studentId:7,status:'retard',justified:false,reason:'Retard de 5 minutes'}
    ]
  }],
  submissions:[
    {lessonId:'lesson-submitted',studentId:7,status:'submitted',submittedAt:'2026-11-20T10:00:00Z'},
    {lessonId:'lesson-draft',studentId:7,status:'draft'}
  ]
};
const context={
  db,
  window:{classGroupContext:''},
  location:{search:'?class=42&student=7&status=all'},
  URLSearchParams,
  dayOcc:()=>[{id:'slot-1',classId:'42',group:'A',subject:'Mathématiques'}],
  $:selector=>selector==='#studentSearch'?{value:''}:selector==='#studentClass'?{value:'42'}:null,
  initials:s=>(s.first[0]+s.last[0]).toUpperCase(),
  esc:value=>String(value??''),
  fmtDate:value=>String(value??''),
  weightedAvg:()=> '14.00',
  jsArg:value=>JSON.stringify(value),
  shell:(section,title,description,actions='')=>
    '<header>'+section+' '+title+' '+description+'</header>'+actions,
  countLabel:(n,singular,plural)=>n+' '+(n===1?singular:(plural||singular+'s')),
  attendanceSlotLabel:()=> '09:00 · Français',
  openAttendanceFollowup:()=>{},
  v205FollowupFilter:()=>{}
};
vm.createContext(context);
vm.runInContext(
  sameId+'\n'+studentAttendance+'\n'+studentScheduleOcc+'\n'+studentSubmitted+'\n'+studentDraftSubmission+'\n'+studentRows+'\n'+attendanceCounts+'\n'+attendanceFollowup+
  "\nfunction student(id){return db.students.find(s=>sameId(s.id,id))}"+
  "\nfunction cls(id){return db.classes.find(c=>sameId(c.id,id))}",
  context
);

assert.strictEqual(vm.runInContext("sameId(7,'7')",context),true,
  'Numeric and textual forms of the same stable ID must match.');
assert.deepStrictEqual(
  Array.from(vm.runInContext("studentAttendance('7').map(x=>x.status)",context)),
  ['absent','retard'],
  'The student attendance history must find numeric IDs when the account supplies text IDs.'
);
assert.strictEqual(
  vm.runInContext("studentScheduleOcc(null,new Date('2026-11-26T12:00:00')).length",context),
  1,
  'The student timetable must match a string class ID to the numeric class ID on the student record.'
);
assert.strictEqual(
  vm.runInContext("studentSubmitted({id:'lesson-submitted'},'7').status",context),
  'submitted',
  'The student work list must detect an existing submission when the student ID type differs.'
);
assert.strictEqual(
  vm.runInContext("studentDraftSubmission('lesson-draft','7').status",context),
  'draft',
  'The student must be able to resume a draft submission with a normalized student ID.'
);
assert.strictEqual(vm.runInContext("studentAbsenceCount('7')",context),1,
  'The student absence count must use the same normalized identifier.');
assert.strictEqual(vm.runInContext("studentLateCount('7')",context),1,
  'The student late count must use the same normalized identifier.');

const directory=vm.runInContext('studentRows()',context);
assert(directory.includes('MARTIN Alice'),
  'The student directory must retain a class when its ID is stored as a number and selected as text.');

const followup=vm.runInContext('attendanceFollowup()',context);
assert(followup.includes('MARTIN Alice'),
  'The follow-up must retain a student selected with the textual form of a numeric ID.');
assert(followup.includes('Absence')&&followup.includes('Retard'),
  'Both events for the student must remain visible after applying class and student filters.');
assert(followup.includes('value="42" selected'),
  'The numeric class must remain selected in the class filter.');
assert(followup.includes('value="7" selected'),
  'The numeric student must remain selected in the student filter.');

console.log('OK — identifiants mixtes : historique élève, compteurs absences/retards, annuaire et suivi des justifications.');
