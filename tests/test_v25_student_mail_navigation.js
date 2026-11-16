const fs=require('fs'),assert=require('assert');
const source=fs.readFileSync('_all.js','utf8');
const nav=source.match(/const groups=\[\['Mon espace',\['studentHome','activity'\]\].*?\];/);
assert(nav,'student navigation groups must be declared');
assert(nav[0].includes("['Communication',['studentMessages']]"),'student navigation must expose the mailbox');
assert(source.includes("window.studentMessages=function(){const currentStudent=student(activeStudent());return currentStudent?renderBox('student',currentStudent.id):studentHome()}"),'student mailbox must use the isolated student mailbox projection');
assert(source.includes("window.messages=function(){return renderBox('teacher','')};"),'teacher mailbox must remain available');
console.log('OK — la navigation élève expose la messagerie et ouvre sa boîte personnelle cloisonnée.');
