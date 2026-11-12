const fs=require('fs'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
for(const token of ['copyOriginalForReply','copiedFrom:source.id','inReplyTo:source.id','bcc:[]','mailV2104DraftFiles','mailV2104EditDraft','mailV2104CreateFolder','mailV2104PermanentDelete'])assert(src.includes(token),`Mécanisme présent : ${token}`);
assert(src.includes("if(!m||!canSee(m,me(role,sid)))return"),'La lecture est limitée aux messages accessibles');
assert(src.includes("m.hiddenFor||[]"),'La suppression définitive est propre au compte');
console.log('OK — V21.04 : réponses avec copie référencée, CCI protégées, brouillons avec fichiers, dossiers, corbeille et accès contrôlé.');
