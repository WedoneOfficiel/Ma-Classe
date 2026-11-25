/* MaClasse V25.1.0 — Vue transversale de suivi de classe.
 * Les données affichées sont limitées aux classes déjà accessibles au rôle connecté.
 * Aucun score de risque ni classement automatique n'est calculé.
 */
(function(){
'use strict';
function classTrackingClasses(){
 if(typeof db==='undefined'||!Array.isArray(db.classes)||authUser?.role==='student')return [];
 if(authUser?.role==='admin')return db.classes.slice().sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'fr',{sensitivity:'base'}));
 if(authUser?.role!=='teacher')return [];
 const tid=String(currentTeacherProfile()?.id||authUser.teacherId||authUser.id||'');
 if(!tid)return [];
 const allowed=new Set([...teacherClasses(tid),...teacherPPClasses(tid)].map(c=>String(c.id)));
 return db.classes.filter(c=>allowed.has(String(c.id))).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'fr',{sensitivity:'base'}));
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
 const lessons=(db.lessons||[]).filter(l=>String(l.classId)===String(c.id)&&l.homework?.requiresSubmission&&l.homework?.due&&(!l.group||students.some(s=>String(s.group||'')===String(l.group))));
 const missingWorks=[];
 lessons.filter(l=>String(l.homework.due)<today).forEach(l=>students.filter(s=>!l.group||String(s.group||'')===String(l.group)).forEach(s=>{if(!studentSubmitted(l,s.id))missingWorks.push({lesson:l,student:s})}));
 const upcoming=(db.lessons||[]).filter(l=>String(l.classId)===String(c.id)&&l.homework?.due&&String(l.homework.due)>=today&&(!l.group||students.some(s=>String(s.group||'')===String(l.group)))).slice().sort((a,b)=>String(a.homework.due).localeCompare(String(b.homework.due))).slice(0,8);
 const recentEvaluations=(db.evaluations||[]).filter(e=>String(e.classId)===String(c.id)&&e.published===true&&String(e.date||'')<=today&&evaluationModelPublished(e,today)&&(!e.group||students.some(s=>String(s.group||'')===String(e.group)))).slice().sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))).slice(0,6).map(e=>{const targetIds=new Set(students.filter(s=>!e.group||String(s.group||'')===String(e.group)).map(s=>String(s.id)));return {evaluation:e,gradedCount:(e.grades||[]).filter(g=>targetIds.has(String(g.studentId))&&g.value!==''&&g.value!==null&&g.value!==undefined).length}});
 const studentRows=students.map(s=>{const rows=attendanceRows.filter(r=>String(r.studentId)===String(s.id));return {student:s,absent:rows.filter(r=>r.status==='absent').length,late:rows.filter(r=>r.status==='retard').length,missing:missingWorks.filter(x=>String(x.student.id)===String(s.id)).length}});
 return {classroom:c,students:studentRows,attendance,missingWorks,upcoming,recentEvaluations,stats:{students:students.length,absent:attendance.reduce((n,x)=>n+x.absent,0),late:attendance.reduce((n,x)=>n+x.late,0),missing:missingWorks.length,upcoming:upcoming.length,since}};
}
function openClassTracking(classId){
 const available=classTrackingClasses(),target=available.find(c=>String(c.id)===String(classId||window.classContext||''));
 if(classId&&!target)return toast('Cette classe ne fait pas partie de vos classes accessibles.');
 window.classContext=target?.id||'';
 window.classGroupContext='';
 appSpace='teacher';page='ppDashboard';render();
}
function classTracking(){
 if(authUser?.role!=='admin'&&authUser?.role!=='teacher')return studentHome();
 const available=classTrackingClasses();
 if(!available.length)return shell('Pilotage','Suivi de classe','Les classes auxquelles vous avez accès apparaîtront ici.')+'<div class="card section"><div class="empty">Aucune classe accessible pour le moment.</div></div>';
 const selected=available.find(c=>String(c.id)===String(window.classContext||''));
 if(!selected){
  const cards=available.map(c=>{const d=classTrackingData(c.id);return '<button class="card ppQuick" style="text-align:left" onclick="openClassTracking('+jsArg(c.id)+')"><span><b>'+esc(c.name)+'</b><small>'+esc(classLevelLabel(c))+' · '+countLabel(d.stats.students,'élève','élèves')+'</small><small>'+countLabel(d.stats.absent,'absence','absences')+' · '+countLabel(d.stats.missing,'travail non rendu','travaux non rendus')+'</small></span><span>›</span></button>'}).join('');
  return shell('Pilotage','Suivi de classe','Retrouvez les informations essentielles de vos classes.')+'<div class="grid g3 section">'+cards+'</div>';
 }
 const d=classTrackingData(selected.id);
 if(!d)return shell('Pilotage','Suivi de classe','Cette classe n’est plus accessible.');
 const options=available.map(c=>'<option value="'+esc(c.id)+'" '+(c.id===selected.id?'selected':'')+'>'+esc(c.name)+'</option>').join('');
 const attendanceRows=d.attendance.slice(0,8).map(x=>'<tr><td>'+fmtDate(x.record.date)+'</td><td>'+esc(attendanceSlotLabel(x.record))+'</td><td>'+x.absent+'</td><td>'+x.late+'</td></tr>').join('');
 const evalRows=d.recentEvaluations.map(x=>'<tr><td><b>'+esc(x.evaluation.title||'Évaluation')+'</b><small>'+esc(x.evaluation.subject||'')+'</small></td><td>'+fmtDate(x.evaluation.date)+'</td><td>'+countLabel(x.gradedCount,'note publiée','notes publiées')+'</td></tr>').join('');
 const workRows=d.missingWorks.slice(0,12).map(x=>'<tr><td><b>'+esc((x.student.last||'').toUpperCase())+' '+esc(x.student.first||'')+'</b></td><td>'+esc(x.lesson.homework.title||'Travail')+'</td><td>'+fmtDate(x.lesson.homework.due)+'</td></tr>').join('');
 const upcomingRows=d.upcoming.map(l=>'<tr><td><b>'+esc(l.homework.title||'Travail à faire')+'</b><small>'+esc(l.subject||'')+'</small></td><td>'+fmtDate(l.homework.due)+'</td><td>'+(l.homework.requiresSubmission?'Dépôt attendu':'À consulter')+'</td></tr>').join('');
 const students=d.students.map(x=>'<tr><td><div class="person"><div class="avatar">'+initials(x.student)+'</div><div><b>'+esc((x.student.last||'').toUpperCase())+' '+esc(x.student.first||'')+'</b><small>'+esc(x.student.group||'Classe entière')+'</small></div></div></td><td>'+x.absent+'</td><td>'+x.late+'</td><td>'+x.missing+'</td><td><button class="btn small" onclick="openStudentProfile('+jsArg(x.student.id)+')">Fiche élève</button><button class="btn small" onclick="openStudentActivity('+jsArg(x.student.id)+')">Suivi</button></td></tr>').join('');
 return shell('Pilotage','Suivi de classe',esc(selected.name)+' · '+esc(classLevelLabel(selected)),'<select class="select" style="max-width:220px" aria-label="Choisir une classe" onchange="openClassTracking(this.value)">'+options+'</select>')+
 '<div class="gradeStats section"><div class="metric"><small>Effectif</small><b>'+d.stats.students+'</b></div><div class="metric"><small>Absences · 30 jours</small><b>'+d.stats.absent+'</b></div><div class="metric"><small>Retards · 30 jours</small><b>'+d.stats.late+'</b></div><div class="metric"><small>Travaux non rendus</small><b>'+d.stats.missing+'</b></div></div>'+
 '<div class="actions section"><button class="btn" onclick="goClassModule(\'schedule\','+jsArg(selected.id)+')">Emploi du temps</button><button class="btn" onclick="goClassModule(\'attendance\','+jsArg(selected.id)+')">Appels</button><button class="btn" onclick="goClassModule(\'evaluations\','+jsArg(selected.id)+')">Évaluations</button><button class="btn" onclick="goClassModule(\'lessons\','+jsArg(selected.id)+')">Séances & leçons</button></div>'+
 '<div class="grid g2 section"><section class="card"><div class="sectionhead"><div><h2>Assiduité récente</h2><div class="muted">Appels des 30 derniers jours</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Date</th><th>Créneau</th><th>Abs.</th><th>Ret.</th></tr></thead><tbody>'+(attendanceRows||'<tr><td colspan="4"><div class="empty">Aucun appel récent.</div></td></tr>')+'</tbody></table></div></section>'+
 '<section class="card"><div class="sectionhead"><div><h2>Évaluations publiées</h2><div class="muted">Dernières évaluations visibles par les élèves</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Évaluation</th><th>Date</th><th>Notes</th></tr></thead><tbody>'+(evalRows||'<tr><td colspan="3"><div class="empty">Aucune évaluation publiée récemment.</div></td></tr>')+'</tbody></table></div></section></div>'+
 '<div class="grid g2 section"><section class="card"><div class="sectionhead"><div><h2>Travaux non rendus</h2><div class="muted">Échéance dépassée et aucun dépôt reçu</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Élève</th><th>Travail</th><th>Échéance</th></tr></thead><tbody>'+(workRows||'<tr><td colspan="3"><div class="empty">Aucun travail non rendu.</div></td></tr>')+'</tbody></table></div>'+(d.missingWorks.length>12?'<div class="hint">12 situations affichées. Consultez le module Séances & leçons pour la liste complète.</div>':'')+'</section>'+
 '<section class="card"><div class="sectionhead"><div><h2>Prochaines échéances</h2><div class="muted">Travaux et activités à venir</div></div></div><div class="tablewrap"><table class="table"><thead><tr><th>Travail</th><th>Date</th><th>Type</th></tr></thead><tbody>'+(upcomingRows||'<tr><td colspan="3"><div class="empty">Aucune échéance à venir.</div></td></tr>')+'</tbody></table></div></section></div>'+
 '<section class="card section"><div class="sectionhead"><div><h2>Élèves</h2><div class="muted">Indicateurs factuels sur les 30 derniers jours · sans classement ni score automatique</div></div><button class="btn small" onclick="goClassModule(\'students\','+jsArg(selected.id)+')">Ouvrir le module Élèves</button></div><div class="tablewrap"><table class="table"><thead><tr><th>Élève</th><th>Abs.</th><th>Ret.</th><th>Non rendus</th><th></th></tr></thead><tbody>'+(students||'<tr><td colspan="5"><div class="empty">Aucun élève dans cette classe.</div></td></tr>')+'</tbody></table></div></section>';
}
window.classTrackingClasses=classTrackingClasses;
window.classTrackingData=classTrackingData;
window.openClassTracking=openClassTracking;
window.ppDashboard=classTracking;
window.openPPDashboard=function(classId){
 const c=cls(classId),tid=String(currentTeacherProfile()?.id||'');
 if(!c||c.principalTeacherId!==tid)return toast('Cette classe ne vous est pas attribuée comme PP.');
 openClassTracking(c.id);
};
})();