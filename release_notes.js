(function(global){
'use strict';
var currentVersion='',historyPromise=null,attemptedAccounts=Object.create(null),showingAutomatic=false;
function escapeHtml(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
function markerFromLine(line){
 var value=String(line||'').trim();if(!value)return null;
 var heading=value.match(/^(#{1,6})\s+/),level=heading?heading[1].length:0,body=value.replace(/^#{1,6}\s+/,'').replace(/^\d+(?:\.\d+)*\.\s*/,'');
 if(/^(?:candidat\b|pistes proposées\b|pistes pour\b|propositions\b|backlog\b|future\b)/i.test(body))return null;
 var table=body.match(/^\|\s*(V\d+(?:\.\d+){1,2})\s*\|\s*([^|]+)\|/i);
 if(table)return {version:table[1].replace(/^v/i,''),title:table[1]+' — '+table[2].trim(),level:0,tableSummary:true,summary:table[2].trim()};
 var dated=body.match(/^(\d{2}\/\d{2}\/\d{4})\s*[—–-]\s*(.+)$/),date=dated?dated[1]:'';
 if(dated)body=dated[2];
 var lead=/^(?:MaClasse|Correctif|AUDIT|LIVRAISON|MISE À JOUR|MISE A JOUR|ÉTAT DE CONSTRUCTION|ETAT DE CONSTRUCTION)\b/i.test(body),starts=/^V\d/i.test(body);
 var m=body.match(/(?:^|\s)(V\d+(?:\.\d+){1,2})(?=$|[\s—–:.)])/i);
 return m&&(heading||date||lead||starts)?{version:m[1].replace(/^v/i,''),title:(date?date+' — ':'')+body,level:level}:null;
}
function parseDocument(markdown,source,sourceLabel){
 var lines=String(markdown||'').split(/\r?\n/),entries=[],cur=null,archive='';
 function flush(){if(!cur)return;entries.push({version:cur.version||'',title:cur.title,content:cur.tableSummary?'- '+cur.summary:cur.lines.join('\n').trim(),source:sourceLabel||'Archive du dépôt',sourceFile:cur.archive||source||''});cur=null}
 lines.forEach(function(line){
  var t=line.trim(),a=t.match(/^#{1,6}\s+Archive source\s*:\s*[\x60]?([^\x60]+)[\x60]?/i),o=t.match(/^#{1,6}\s+Source originale?\s*:\s*[\x60]?([^\x60]+)[\x60]?/i);
  if(a){archive=a[1].trim();return}if(o){archive=o[1].trim();return}
  if(/^#{1,6}\s+(?:Journal V25|Notes historiques V21 complémentaires)\b/i.test(t))return;
  var m=markerFromLine(t);
  if(m){flush();cur={version:m.version,title:m.title,level:m.level,tableSummary:!!m.tableSummary,summary:m.summary||'',archive:archive,lines:[]};archive='';return}
  var dated=t.match(/^#{2,6}\s+(\d{2}\/\d{2}\/\d{4}\s*[—–-]\s*.+)$/);
  if(dated){flush();cur={version:'',title:dated[1],level:t.match(/^#+/)[0].length,archive:archive,lines:[]};archive='';return}
  if(/^#{1,6}\s+/.test(t)&&cur){var level=t.match(/^#+/)[0].length;if(!cur.level||level<=cur.level)flush()}
  if(cur)cur.lines.push(line);
 });
 flush();return entries;
}
function parseHistory(docs){
 var all=[];
 (docs||[]).forEach(function(d){parseDocument(d.markdown,d.path,d.label).forEach(function(e){
  if(e.version){var old=all.find(function(x){return x.version===e.version});if(old){if(e.content&&old.content.indexOf(e.content)<0)old.content+='\n\n#### Autre trace conservée : '+e.sourceFile+'\n\n'+e.content;if(e.sourceFile&&old.sourceFile.indexOf(e.sourceFile)<0)old.sourceFile+=' · '+e.sourceFile}else all.push(e)}
  else if(e.content)all.push(e);
 })});
 return all;
}
function inlineMarkdown(v){return escapeHtml(v).replace(/\x60([^\x60]+)\x60/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>')}
function renderMarkdown(md){
 var lines=String(md||'').split(/\r?\n/),out=[],list=false;
 function endList(){if(list){out.push('</ul>');list=false}}
 lines.forEach(function(line){var v=line.trim();if(!v){endList();return}
  if(/^#{1,6}\s+/.test(v)){endList();var n=Math.min(4,Math.max(3,v.match(/^#+/)[0].length+1));out.push('<h'+n+'>'+inlineMarkdown(v.replace(/^#{1,6}\s+/,''))+'</h'+n+'>')}
  else if(/^>\s?/.test(v)){endList();out.push('<blockquote>'+inlineMarkdown(v.replace(/^>\s?/,'') )+'</blockquote>')}
  else if(/^[-*]\s+/.test(v)){if(!list){out.push('<ul>');list=true}out.push('<li>'+inlineMarkdown(v.replace(/^[-*]\s+/,''))+'</li>')}
  else{endList();out.push('<p>'+inlineMarkdown(v)+'</p>')}
 });endList();return out.join('');
}
function cleanCurrentRelease(md){var v=String(md||'').replace(/^#\s+[^\n]+\n/,'').replace(/^\s*>[^\n]*\n/gm,'');return v.replace(/^##\s+Validation et limites[\s\S]*$/mi,'').trim()}
function loadHistory(){
 if(historyPromise)return historyPromise;
 historyPromise=fetch('/api/release-notes/history',{credentials:'same-origin',cache:'no-store'}).then(function(r){if(!r.ok)throw Error('Journal indisponible ('+r.status+').');return r.json()}).then(function(p){currentVersion=String(p.current_version||currentVersion||'');return p}).catch(function(e){historyPromise=null;throw e});
 return historyPromise;
}
function currentEntry(p){var v=String(p.current_version||currentVersion||'');return {version:v,title:'V'+v+' · Version actuelle',content:cleanCurrentRelease(p.current_release_markdown||''),sourceFile:'docs/releases/v'+v+'.md'}}
function journalEntries(p){var c=currentEntry(p);return (c.content?[c]:[]).concat(parseHistory(p.history_documents||[]))}
function selectEntry(i){
 var e=(global.__mcReleaseEntries||[])[i];if(!e)return;var nav=document.getElementById('releaseNotesNav');
 if(nav)Array.prototype.forEach.call(nav.querySelectorAll('button'),function(b,n){b.classList.toggle('active',n===i);b.setAttribute('aria-current',n===i?'true':'false')});
 var article=document.getElementById('releaseNotesArticle');if(article)article.innerHTML='<h3>'+escapeHtml(e.title)+'</h3>'+(e.content?renderMarkdown(e.content):'<p>Aucune note détaillée n’est conservée pour cette entrée.</p>')+'<p class="releaseNotesSource">Source : '+escapeHtml(e.sourceFile||e.source||'documents historiques du dépôt')+'</p>';
}
function navMarkup(entries){return entries.map(function(e,i){var l=e.version?'Trace historique documentée':'Trace datée';if(i===0&&e.version)l='Version actuelle';return '<button type="button" class="'+(i===0?'active':'')+'" aria-current="'+(i===0?'true':'false')+'" onclick="window.MCReleaseNotes.selectEntry('+i+')">'+escapeHtml(e.title)+'<small>'+escapeHtml(l)+'</small></button>'}).join('')}
function styleModal(){var m=document.getElementById('modal');if(m)m.classList.add('releaseNotesModal')}
function openJournal(){return loadHistory().then(function(p){
 var entries=journalEntries(p);global.__mcReleaseEntries=entries;
 var body='<p class="releaseNotesLead">Les informations anciennes proviennent des notes, audits, recettes et archives effectivement présents dans le dépôt. Un numéro trouvé dans un audit ne prouve pas, à lui seul, qu’une release a été publiée. Les lacunes ne sont pas reconstituées.</p><div class="releaseNotesLayout"><nav id="releaseNotesNav" class="releaseNotesNav" aria-label="Historique documenté">'+(entries.length?navMarkup(entries):'<p>Aucune entrée historique documentée.</p>')+'</nav><article id="releaseNotesArticle" class="releaseNotesArticle" aria-live="polite"></article></div><div class="releaseNotesActions"><span class="releaseNotesSource">Sources : historique consolidé, archives des audits et ancien README.</span><button type="button" class="btn primary" onclick="window.MCReleaseNotes.acknowledge()">J’ai pris connaissance de la version actuelle</button></div>';
 if(typeof global.openModal!=='function')throw Error('Fenêtre MaClasse indisponible.');global.openModal('Journal des versions',body);styleModal();if(entries.length)selectEntry(0);
 }).catch(function(e){if(typeof global.toast==='function')global.toast(e.message||'Journal indisponible.')})}
function acknowledge(){
 if(!currentVersion)return Promise.resolve(false);
 return fetch('/api/release-notes/ack',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({version:currentVersion})}).then(function(r){return r.json().catch(function(){return {}}).then(function(p){if(!r.ok)throw Error(p.error||'Consultation non enregistrée.');showingAutomatic=false;if(typeof global.closeModal==='function')global.closeModal();return true})}).catch(function(e){if(typeof global.toast==='function')global.toast(e.message||'Consultation non enregistrée.');return false});
}
function openAutomatic(v,p){
 currentVersion=String(v||p.current_version||'');var e=currentEntry(p);
 var body='<p class="releaseNotesLead">Voici les nouveautés de la version installée. Cet écran est présenté une fois par compte et par version.</p><div class="releaseNotesLayout"><div class="releaseNotesNav"><button type="button" class="active" aria-current="true">V'+escapeHtml(currentVersion)+'<small>Nouveautés de cette installation</small></button></div><article class="releaseNotesArticle">'+(e.content?renderMarkdown(e.content):'<p>Aucune note détaillée n’est conservée pour cette version.</p>')+'</article></div><div class="releaseNotesActions"><button type="button" class="btn" onclick="window.MCReleaseNotes.openJournal()">Voir le journal complet</button><button type="button" class="btn primary" onclick="window.MCReleaseNotes.acknowledge()">J’ai compris</button></div>';
 if(typeof global.openModal!=='function')return;global.openModal('Nouveautés de MaClasse · V'+currentVersion,body);styleModal();
 var close=document.querySelector('#modal .modalhead .close');if(close)close.setAttribute('onclick','window.MCReleaseNotes.acknowledge()');showingAutomatic=true;
}
function maybeShow(v,id){
 var version=String(v||'').replace(/^v/i,''),account=String(id||'').trim();if(!version||!account||showingAutomatic)return;
 var key=account+':'+version;if(attemptedAccounts[key])return;attemptedAccounts[key]=true;currentVersion=version;
 fetch('/api/release-notes/state',{credentials:'same-origin',cache:'no-store'}).then(function(r){if(!r.ok)throw Error('État des nouveautés indisponible.');return r.json()}).then(function(state){
  if(String(state.seen_version||'').replace(/^v/i,'')===version)return null;
  return loadHistory().then(function(p){if(String(p.current_version||'').replace(/^v/i,'')!==version)throw Error('Version du journal différente de la version installée.');openAutomatic(version,p);return p});
 }).catch(function(e){delete attemptedAccounts[key];console.warn('MaClasse nouveautés :',e)});
}
global.MCReleaseNotes={parseHistory:parseHistory,parseDocument:parseDocument,renderMarkdown:renderMarkdown,cleanCurrentRelease:cleanCurrentRelease,openJournal:openJournal,maybeShow:maybeShow,acknowledge:acknowledge,selectEntry:selectEntry};
})(window);
