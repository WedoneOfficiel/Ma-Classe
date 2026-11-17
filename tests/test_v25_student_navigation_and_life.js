const fs=require('fs'),assert=require('assert');
const source=fs.readFileSync('_all.js','utf8');
const nav=source.match(/const groups=\[\['Mon espace',\['studentHome','activity'\]\].*?\];/);
assert(nav&&nav[0].includes("['Communication',['studentMessages']]"),'student navigation must expose the mailbox');
assert(source.includes("window.studentMessages=function(){const currentStudent=student(activeStudent());return currentStudent?renderBox('student',currentStudent.id):studentHome()}"),'student mailbox must use its isolated mailbox');
const life=source.slice(source.indexOf('function studentLife(){'),source.indexOf('\nfunction dashboardLegacy',source.indexOf('function studentLife(){')));
assert(life.includes("filter(x=>x.status==='absent')"),'student life must show absences only');
assert(!life.includes('Retards')&&!life.includes('Bulletins')&&!life.includes("status==='retard'"),'student life must not mix other categories into the absences page');
console.log('OK — navigation messagerie élève et Vie scolaire limitée aux absences.');
