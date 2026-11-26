/* MaClasse V25.1.0 — Vue transversale de suivi de classe.
 * Les données affichées sont limitées aux classes déjà accessibles au rôle connecté.
 * Aucun score de risque ni classement automatique n'est calculé.
 */
(function(){
'use strict';
function classTrackingClasses(){
 if(typeof db==='undefined'||!db||!Array.isArray(db.classes)||authUser?.role==='student')return [];
 if(authUser?.role==='admin')return db.classes.slice().sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'fr',{sensitivity:'base'}));
 if(authUser?.role!=='teacher')return [];
 const tid=String(currentTeacherProfile()?.id||authUser.teacherId||authUser.id||'');
 if(!tid)return [];
 const allowed=new Set([...teacherClasses(tid),...teacherPPClasses(tid)].map(c=>String(c.id)));
 return db.classes.filter(c=>allowed.has(String(c.id))).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'fr',{sensitivity:'base'}));
}
function classTrackingCanSeeAllSubjects(c){
 if(authUser?.role==='admin')return true;
 const tid=String(currentTeacherProfile()?.id||authUser?.id||authUser?.teacherId||'');
 return authUser?.role==='teacher'&&!!tid&&String(c?.principalTeacherId||'')===tid;
}
function classTrackingSubjectAllowed(c,record){
 if(classTrackingCanSeeAllSubjects(c))return true;
 if(authUser?.role!=='teacher'||typeof canEditEvaluation!=='function')return false;
 const schedule=(db.schedule||[]).find(s=>String(s.id)===String(record?.scheduleId||''));
 const subject=String(record?.subject||schedule?.subject||'');
 return canEditEvaluation({classId:c.id,subject,date:String(record?.date||record?.homework?.due||iso(new Date()))});
}
function classTrackingData(classId,referenceDate=new Date()){
 const c=classTrackingClasses().find(x=>String(x.id)===String(classId));
 if(!c)return null;
 const today=iso(referenceDate),sinceDate=new Date(referenceDate);
 sinceDate.setDate(sinceDate.getDate()-29);
 const since=iso(sinceDate);
 const students=db.students.filter(s=>String(s.classId)===String(c.id)).slice().sort((a,b)=>String(a.last||'').localeCompare(String(b.last||''),'fr',{sensitivity:'base'})||String(a.first||'').localeCompare(String(b.first||''),'fr',{sensitivity:'base'}));
 const studentIds=new Set(students.map(s=>String(s.id)));
 const attendance=(db.attendance||[]).filter(a=>String(a.classId)===String(c.id)&&String(a.date||'')>=since&&String(a.date||'')<=today).slice().sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))).map(a=>({record:a,absent:(a.rows||[]).filter(r=>r.status==='absent'&&studentIds.has(String(r.studentId))).length,late:(a.rows||[]).filter(r=>r.status==='retard'&&studentIds.has(String(r.studentId))).length}));
 const attendanceRows=attendance.flatMap(x=>(x.record.rows||[]).filter(r=>studentIds.has(String(r.studentId))).map(r=>({...r,date:x.record.date})));
 const lessons=(db.lessons||[]).filter(l=>String(l.classId)===String(c.id)&&classTrackingSubjectAllowed(c,l)&&l.homework?.requiresSubmission&&l.homework?.due&&(!l.group||students.some(s=>String(s.group||'')===String(l.group))));
 const missingWorks=[];
 lessons.filter(l=>String(l.homework.due)<today).forEach(l=>students.filter(s=>!l.group||String(s.group||'')===String(l.group)).forEach(s=>{if(!studentSubmitted(l,s.id))missingWorks.push({lesson:l,student:s})}));
 const upcoming=(db.lessons||[]).filter(l=>String(l.classId)===String(c.id)&&classTrackingSubjectAllowed(c,l)&&l.homework?.due&&String(l.homework.due)>=today&&(!l.group||students.some(s=>String(s.group||'')===String(l.group)))).slice().sort((a,b)=>String(a.homework.due).localeCompare(String(b.homework.due))).slice(0,8);
 const recentEvaluations=(db.evaluations||[]).filter(e=>String(e.classId)===String(c.id)&&e.published===true&&classTrackingSubjectAllowed(c,e)&&String(e.date||'')<=today&&evaluationModelPublished(e,today)&&(!e.group||students.some(s=>String(s.group||'')===String(e.group)))).slice().sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))).slice(0,6).map(e=>{const targetIds=new Set(students.filter(s=>!e.group||String(s.group||'')===String(e.group)).map(s=>String(s.id)));return {evaluation:e,gradedCount:(e.grades||[]).filter(g=>targetIds.has(String(g.studentId))&&g.value!==''&&g.value!==null&&g.value!==undefined).length}});
 const studentRows=students.map(s=>{const rows=attendanceRows.filter(r=>String(r.studentId)===String(s.id));return {student:s,absent:rows.filter(r=>r.status==='absent').length,late:rows.filter(r=>r.status==='retard').length,missing:missingWorks.filter(x=>String(x.student.id)===String(s.id)).length}});
 return {classroom:c,students:studentRows,attendance,missingWorks,upcoming,recentEvaluations,stats:{students:students.length,absent:attendance.reduce((n,x)=>n+x.absent,0),late:attendance.reduce((n,x)=>n+x.late,0),missing:missingWorks.length,upcoming:upcoming.length,since}};
}
function openClassTracking(classId){
 const available=classTrackingClasses(),target=available.find(c=>String(c.id)===String(classId||window.classContext||''));
 if(classId&&!target)return toast('Cette classe ne fait pas partie de vos classes accessibles.');
 window.classContext=target?.id||'';
 window.classGroupContext='';
 appSpace='teacher';page='classes';render();
}
function showClassTrackingList(){
 window.classContext='';window.classGroupContext='';window.classTrackingSearch='';window.classTrackingLevel='';
 appSpace='teacher';page='classes';render();
}
function classTrackingExportCsv(classId){
 const data=classTrackingData(classId);
 if(!data)return toast('Cette classe n’est pas accessible.');
 const rows=[['Élève','Classe','Niveau','Groupe','Absences · 30 jours','Retards · 30 jours','Travaux non rendus']];
 data.students.forEach(row=>rows.push([
  (row.student.last||'').toLocaleUpperCase('fr')+' '+(row.student.first||''),
  data.classroom.name||'',
  Array.isArray(data.classroom.levels)?data.classroom.levels.join(' / '):(data.classroom.level||''),
  row.student.group||'',
  row.absent,row.late,row.missing
 ]));
 const csv='\uFEFF'+rows.map(row=>row.map(value=>'"'+String(value??'').replaceAll('"','""')+'"').join(';')).join('\r\n');
 downloadText('bilan-classe-'+String(data.classroom.name||'classe').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')+'.csv',csv,'text/csv;charset=utf-8');
}
function filterClassTrackingCards(){
 const search=String(document.getElementById('classTrackingSearch')?.value||'').trim().toLocaleLowerCase('fr');
 const level=String(document.getElementById('classTrackingLevel')?.value||'');
 window.classTrackingSearch=search;window.classTrackingLevel=level;
 let visible=0;
 document.querySelectorAll('.classHubCard[data-class-search]').forEach(card=>{
  const haystack=String(card.dataset.classSearch||'').toLocaleLowerCase('fr');
  const levels=String(card.dataset.classLevels||'').split('|').filter(Boolean);
  const match=(!search||haystack.includes(search))&&(!level||levels.includes(level));
  card.hidden=!match;
  if(match)visible++;
 });
 const total=document.querySelectorAll('.classHubCard[data-class-search]').length;
 const counter=document.getElementById('classTrackingCount');
 if(counter)counter.textContent=visible+' classe(s) affichée(s) sur '+total+' accessible(s)';
 const empty=document.getElementById('classTrackingNoResults');
 if(empty)empty.hidden=visible!==0;
}
function classTracking(){
 if(authUser?.role!=='admin'&&authUser?.role!=='teacher')return studentHome();
 const available=classTrackingClasses();
 if(!available.length)return shell('Scolarité','Classes','Les classes auxquelles vous avez accès apparaîtront ici.','<button class="btn primary" onclick="openClass()">+ Nouvelle classe</button>')+'<div class="card section"><div class="empty">Aucune classe accessible pour le moment.<div class="actions section"><button class="btn primary" onclick="openClass()">Créer une classe</button></div></div></div>';
 const selected=available.find(c=>String(c.id)===String(window.classContext||''));
 if(!selected){
  const search=String(window.classTrackingSearch||'').trim().toLocaleLowerCase('fr');
  const level=String(window.classTrackingLevel||'');
  const levels=[...new Set(available.flatMap(c=>Array.isArray(c.levels)&&c.levels.length?c.levels:String(c.level||'').split('/').map(x=>x.trim()).filter(Boolean)))].sort((a,b)=>a.localeCompare(b,'fr',{sensitivity:'base'}));
  const filtered=available.filter(c=>{
   const name=String(c.name||'').toLocaleLowerCase('fr');
   const levelNames=Array.isArray(c.levels)&&c.levels.length?c.levels:String(c.level||'').split('/').map(x=>x.trim()).filter(Boolean);
   return (!search||name.includes(search)||levelNames.join(' ').toLocaleLowerCase('fr').includes(search))&&(!level||levelNames.includes(level));
  });
  const visibleIds=new Set(filtered.map(c=>String(c.id)));
  const cards=available.map(c=>{
   const d=classTrackingData(c.id),teacherNames=classTeachers(c).map(t=>teacherName(t)).filter(Boolean);
   const levelNames=Array.isArray(c.levels)&&c.levels.length?c.levels:String(c.level||'').split('/').filter(Boolean);
   const pp=c.principalTeacherId?teacherName(db.teachers.find(t=>sameId(t.id,c.principalTeacherId))||{}):'';
   const stats='<div class="gradeStats section"><div class="metric"><small>Effectif</small><b>'+d.stats.students+'</b></div><div class="metric"><small>Abs. · 30 j</small><b>'+d.stats.absent+'</b></div><div class="metric"><small>Ret. · 30 j</small><b>'+d.stats.late+'</b></div><div class="metric"><small>Non rendus</small><b>'+d.stats.missing+'</b></div></div>';
   const groups=(c.groups||[]).length?'<div class="groupPills">'+c.groups.map(g=>'<span class="pill purple">'+esc(g)+'</span>').join('')+'</div>':'';
   return '<article class="card classHubCard" '+(visibleIds.has(String(c.id))?'':'hidden ')+'data-class-search="'+esc((c.name+' '+levelNames.join(' ')).toLocaleLowerCase('fr'))+'" data-class-levels="'+esc(levelNames.join('|'))+'"><div class="sectionhead"><div><h2>'+esc(c.name)+'</h2><div class="muted">'+esc(levelNames.join(' / ')||'Niveau non renseigné')+'</div><small class="muted">'+(c.principalTeacherId?'PP : '+esc(pp||'Enseignant non renseigné'):'Aucun PP désigné')+'</small></div><span class="pill blue">'+countLabel(d.stats.students,'élève','élèves')+'</span></div>'+groups+'<div class="muted section">'+(teacherNames.length?'Enseignants : '+esc(teacherNames.join(' · ')):'Aucun enseignant renseigné')+'</div>'+stats+'<div class="actions"><button class="btn primary small" onclick="openClassTracking('+jsArg(c.id)+')">Voir le suivi</button><button class="btn small" onclick="openClass('+jsArg(c.id)+')">Modifier</button><button class="btn small" onclick="manageClassGroups('+jsArg(c.id)+')">Groupes</button></div></article>';
  }).join('');
  const toolbar='<div class="card section classHubFilters"><div class="searchRow"><input id="classTrackingSearch" class="input" type="search" placeholder="Rechercher une classe ou un niveau…" value="'+esc(window.classTrackingSearch||'')+'" oninput="filterClassTrackingCards()"><select id="classTrackingLevel" class="select" aria-label="Filtrer par niveau" onchange="filterClassTrackingCards()"><option value="">Tous les niveaux</option>'+levels.map(x=>'<option value="'+esc(x)+'" '+(level===x?'selected':'')+'>'+esc(x)+'</option>').join('')+'</select></div><div id="classTrackingCount" class="muted">'+countLabel(filtered.length,'classe affichée','classes affichées')+' sur '+countLabel(available.length,'classe accessible','classes accessibles')+'</div></div>';
  return shell('Scolarité','Classes','Organisation, gestion et suivi de toutes les classes accessibles.', '<button class="btn primary" onclick="openClass()">+ Nouvelle classe</button>')+toolbar+'<div class="grid g3 section classHubGrid">'+cards+'</div><div id="classTrackingNoResults" class="card empty section"'+(filtered.length?' hidden':'')+'>Aucune classe ne correspond à ces critères.</div>';
 }
 const d=classTrackingData(selected.id);
 if(!d)return shell('Scolarité','Classes','Cette classe n’est plus accessible.');
 const levelNames=Array.isArray(selected.levels)&&selected.levels.length?selected.levels:String(selected.level||'').split('/').filter(Boolean);
 const options=available.map(c=>'<option value="'+esc(c.id)+'" '+(String(c.id)===String(selected.id)?'selected':'')+'>'+esc(c.name)+'</option>').join('');
 const scopeNotice=authUser?.role==='teacher'&&!classTrackingCanSeeAllSubjects(selected)?'<div class="notice section">Les travaux et évaluations affichés sont limités aux matières accessibles via vos affectations. Le reste des informations de la classe demeure visible selon vos droits.</div>':'';
 const teacherNames=classTeachers(selected).map(t=>teacherName(t)).filter(Boolean);
 const pp=selected.principalTeacherId?teacherName(db.teachers.find(t=>sameId(t.id,selected.principalTeacherId))||{}):'';
 const attendanceRows=d.attendance.slice(0,8).map(x=>'<tr><td>'+fmtDate(x.record.date)+'</td><td>'+esc(attendanceSlotLabel(x.record))+'</td><td>'+x.absent+'</td><td>'+x.late+'</td></tr>').join('');
 const evalRows=d.recentEvaluations.map(x=>'<tr><td><b>'+esc(x.evaluation.title||'Évaluation')+'</b><small>'+esc(x.evaluation.subject||'')+'</small></td><td>'+fmtDate(x.evaluation.date)+'</td><td>'+countLabel(x.gradedCount,'note publiée','notes publiées')+'</td></tr>').join('');
 const workRows=d.missingWorks.slice(0,12).map(x=>'<tr><td><b>'+esc((x.student.last||'').toLocaleUpperCase('fr'))+' '+esc(x.student.first||'')+'</b></td><td>'+esc(x.lesson.homework.title||'Travail')+'</td><td>'+fmtDate(x.lesson.homework.due)+'</td></tr>').join('');
 const upcomingRows=d.upcoming.map(l=>'<tr><td><b>'+esc(l.homework.title||'Travail à faire')+'</b><small>'+esc(l.subject||'')+'</small></td><td>'+fmtDate(l.homework.due)+'</td><td>'+(l.homework.requiresSubmission?'Dépôt attendu':'À consulter')+'</td></tr>').join('');
 const students=d.students.map(x=>'<tr><td><div class="person"><div class="avatar">'+esc(initials(x.student))+'</div><div><b>'+esc((x.student.last||'').toLocaleUpperCase('fr'))+' '+esc(x.student.first||'')+'</b><small>'+esc(x.student.group||'Classe entière')+'</small></div></div></td><td>'+x.absent+'</td><td>'+x.late+'</td><td>'+x.missing+'</td><td><button class="btn small" onclick="openStudentProfile('+jsArg(x.student.id)+')">Fiche élève</button><button class="btn small" onclick="openStudentActivity('+jsArg(x.student.id)+')">Suivi</button></td></tr>').join('');
 const actionBar='<div class="actions section"><button class="btn" onclick="showClassTrackingList()">Toutes les classes</button><button class="btn" onclick="openClass('+jsArg(selected.id)+')">Modifier la classe</button><button class="btn" onclick="manageClassGroups('+jsArg(selected.id)+')">Gérer les groupes</button><button class="btn" onclick="classTrackingExportCsv('+jsArg(selected.id)+')">Exporter le bilan CSV</button><button class="btn" onclick="goClassModule(\'schedule\','+jsArg(selected.id)+')">Emploi du temps</button><button class="btn" onclick="goClassModule(\'attendance\','+jsArg(selected.id)+')">Appels</button><button class="btn" onclick="goClassModule(\'evaluations\','+jsArg(selected.id)+')">Évaluations</button><button class="btn" onclick="goClassModule(\'lessons\','+jsArg(selected.id)+')">Séances & leçons</button></div>';
 return shell('Scolarité','Classes',esc(selected.name)+' · '+esc(levelNames.join(' / ')), '<select class="select" style="max-width:220px" aria-label="Choisir une classe" onchange="openClassTracking(this.value)">'+options+'</select>')+
 '<div class="card section classHubIntro"><div class="sectionhead"><div><h2>'+esc(selected.name)+'</h2><div class="muted">'+(selected.principalTeacherId?'Professeur principal : '+esc(pp||'Non renseigné'):'Aucun PP désigné')+'</div><div class="muted">'+(teacherNames.length?'Enseignants : '+esc(teacherNames.join(' · ')):'Aucun enseignant renseigné')+'</div></div><div class="actions"><span class="pill blue">'+countLabel(d.stats.students,'élève','élèves')+'</span>'+((selected.groups||[]).length?'<span class="pill purple">'+countLabel(selected.groups.length,'groupe','groupes')+'</span>':'')+'</div></div></div>'+
 scopeNotice+'<div class="gradeStats section"><div class="metric"><small>Effectif</small><b>'+d.stats.students+'</b></div><div class="metric"><small>Absences · 30 jours</small><b>'+d.stats.absent+'</b></div><div class="metric"><small>Retards · 30 jours</small><b>'+d.stats.late+'</b></div><div class="metric"><small>Travaux non rendus</small><b>'+d.stats.missing+'</b></div></div>'+actionBar+
 '<div class="grid g2 section"><section class="card"><div class="sectionhead"><div><h2>Assiduité récente</h2><div class="muted">Appels des 30 derniers jours</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Date</th><th>Créneau</th><th>Abs.</th><th>Ret.</th></tr></thead><tbody>'+(attendanceRows||'<tr><td colspan="4"><div class="empty">Aucun appel récent.</div></td></tr>')+'</tbody></table></div></section>'+
 '<section class="card"><div class="sectionhead"><div><h2>Évaluations publiées</h2><div class="muted">Dernières évaluations visibles par les élèves</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Évaluation</th><th>Date</th><th>Notes</th></tr></thead><tbody>'+(evalRows||'<tr><td colspan="3"><div class="empty">Aucune évaluation publiée récemment.</div></td></tr>')+'</tbody></table></div></section></div>'+
 '<div class="grid g2 section"><section class="card"><div class="sectionhead"><div><h2>Travaux non rendus</h2><div class="muted">Échéance dépassée et aucun dépôt reçu</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Élève</th><th>Travail</th><th>Échéance</th></tr></thead><tbody>'+(workRows||'<tr><td colspan="3"><div class="empty">Aucun travail non rendu.</div></td></tr>')+'</tbody></table></div>'+(d.missingWorks.length>12?'<div class="hint">12 situations affichées. Consultez le module Séances & leçons pour la liste complète.</div>':'')+'</section>'+
 '<section class="card"><div class="sectionhead"><div><h2>Prochaines échéances</h2><div class="muted">Travaux et activités à venir</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Travail</th><th>Date</th><th>Type</th></tr></thead><tbody>'+(upcomingRows||'<tr><td colspan="3"><div class="empty">Aucune échéance à venir.</div></td></tr>')+'</tbody></table></div></section></div>'+
 '<section class="card section"><div class="sectionhead"><div><h2>Élèves</h2><div class="muted">Indicateurs factuels sur les 30 derniers jours · sans classement ni score automatique</div></div><button class="btn small" onclick="goClassModule(\'students\','+jsArg(selected.id)+')">Ouvrir les élèves</button></div><div class="tablewrap"><table class="table"><thead><tr><th>Élève</th><th>Abs.</th><th>Ret.</th><th>Non rendus</th><th></th></tr></thead><tbody>'+(students||'<tr><td colspan="5"><div class="empty">Aucun élève dans cette classe.</div></td></tr>')+'</tbody></table></div></section>';
}
window.classTrackingClasses=classTrackingClasses;
window.classTracking=classTracking;
window.classTrackingExportCsv=classTrackingExportCsv;
window.classTrackingData=classTrackingData;
window.openClassTracking=openClassTracking;
window.showClassTrackingList=showClassTrackingList;
window.ppDashboard=classTracking;
window.openPPDashboard=function(classId){
 const c=cls(classId),tid=String(currentTeacherProfile()?.id||'');
 if(!c||!sameId(c.principalTeacherId,tid))return toast('Cette classe ne vous est pas attribuée comme PP.');
 openClassTracking(c.id);
};
})();