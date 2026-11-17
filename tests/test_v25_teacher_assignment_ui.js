const fs=require('fs'),assert=require('assert');
const js=fs.readFileSync('_all.js','utf8');
assert(js.includes("function canManageScheduleAssignments(s){if(authUser?.role==='admin')return true;"),'Direction must retain full access');
assert(js.includes("String(s.teacherId||'')===tid||(s.teacherIds||[]).map(String).includes(tid)"),'a teacher may manage only a slot they teach');
assert(js.includes("if(!s||!canManageScheduleAssignments(s))return;"),'the assignment editor must enforce the same scope');
assert(js.includes("...(authUser?.role==='teacher'?{createdBy:String(currentTeacherProfile()?.id||authUser.id||'')}: {})"),'teacher-created assignments must be attributed to their creator');
assert(js.includes("String(a.createdBy||'')!==String(currentTeacherProfile()?.id||'')? 'disabled" )||js.includes('Seul le créateur ou la Direction peut retirer cette affectation'),'the UI must not offer removal of another user\'s assignment');
console.log('OK — interface affectations : Direction et professeur titulaire, suppression attribuée au créateur.');
