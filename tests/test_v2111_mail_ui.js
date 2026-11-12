const fs=require('fs'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
assert(src.includes("window.messages=function(){return renderBox('teacher','')}"),'la boîte enseignant utilise la nouvelle interface via une référence globale explicite');
assert(src.includes("window.studentMessages=function(){const currentStudent=student(activeStudent());return currentStudent?renderBox('student',currentStudent.id):studentHome()}"),'la boîte élève utilise la nouvelle interface via une référence globale explicite');
assert(src.includes("window.mailV2104Star('${m.id}','${role}','${sid}')"),'les favoris utilisent explicitement le compte actif');
assert(src.includes("window.mailV2Search=this.value;const p=this.selectionStart;render();const n=document.querySelector('.v2104Search input')"),'la recherche restaure le focus et la position du curseur');
assert(!src.includes("toggleMailStar('${c.id}','teacher','${s.id}')"),'l’ancien défaut de variable élève dans la boîte enseignant a disparu');
console.log('OK — V21.04 : vues actives remplacées, favoris isolés, ancienne référence s éliminée et recherche avec focus conservé.');
