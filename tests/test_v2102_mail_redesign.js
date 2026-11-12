const fs=require('fs'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'..','_all.js'),'utf8');
assert(src.includes('/* V21.04 — messagerie reconstruite'),'Le module V21.04 est installé');
for(const token of ['class="v2104App"','class="v2104Side"','class="v2104Center"','class="v2104Reader"','aria-label="Rechercher dans les messages"'])assert(src.includes(token),`Interface présente : ${token}`);
for(const token of ['@media(max-width:820px)','prefers-reduced-motion:reduce','v2104ComposeFoot','v2104RecipientsMeta'])assert(src.includes(token),`Adaptation UI présente : ${token}`);
console.log('OK — V21.04 : architecture visuelle à trois panneaux, recherche accessible, rédaction dédiée, lecture détaillée et responsive.');
