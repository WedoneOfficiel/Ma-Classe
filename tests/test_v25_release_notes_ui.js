const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const helper=fs.readFileSync(path.join(__dirname,'..','release_notes.js'),'utf8');
const ctx={window:{},console};
vm.runInNewContext(helper,ctx);
const api=ctx.window.MCReleaseNotes;
assert(api,'The release notes helper must be registered before application startup.');
const docs=[
 {path:'docs/HISTORIQUE_VERSIONS.md',label:'Historique',markdown:fs.readFileSync(path.join(__dirname,'..','docs/HISTORIQUE_VERSIONS.md'),'utf8')},
 {path:'docs/archives/ETATS_AUDITS_ET_RECETTES_ANTERIEURS.md',label:'Audits et recettes',markdown:fs.readFileSync(path.join(__dirname,'..','docs/archives/ETATS_AUDITS_ET_RECETTES_ANTERIEURS.md'),'utf8')},
 {path:'docs/archives/README_PRE_REORGANISATION.md',label:'Ancien README',markdown:fs.readFileSync(path.join(__dirname,'..','docs/archives/README_PRE_REORGANISATION.md'),'utf8')}
];
const entries=api.parseHistory(docs);
const versions=entries.map(x=>x.version).filter(Boolean);
const expected=['25.1.1','25.1.0','25.0.25','25.0.24','25.0.23','25.0.18','25.0.17','25.0.15','25.0.13','25.0.12','25.0.10','25.0.9','25.0.7','25.0.6','25.0.5','25.0.4','25.0.3','25.0.2','25.0.1','21.22','21.21','21.20','21.19','21.18','21.17.1','21.17','21.16.1','21.16','21.15','21.14','21.13','21.12','21.11.3','21.09','21.04','21.05','21.06','20.10','20.9','20.8','20.7','20.6','20.5','20.4','20.3','20.2','20.1','20.0.0','19.9','19.8','19.7'];
for(const version of expected)assert(versions.includes(version),'Missing source-backed history entry: '+version);
assert(!versions.includes('25.2.1')&&!versions.includes('25.2.0')&&!versions.includes('25.0.20'),'Candidate, future and undocumented versions must not be presented as archived releases.');
assert(entries.some(x=>x.sourceFile.includes('ETATS_AUDITS')),'Archived audits must keep their source attribution.');
assert(entries.some(x=>x.sourceFile.includes('README_PRE')),'The legacy README must keep its source attribution.');
assert(entries.some(x=>!x.version&&x.title.includes('12/11/2026')),'Dated records without a version number must stay dated records.');
const recent=entries.find(x=>x.version==='25.1.1');
assert(recent&&recent.content.includes('Ed25519'),'Preserve the documented detail of recent releases.');
const old=entries.find(x=>x.version==='21.22');
assert(old&&old.content.includes('7 jours'),'Retain archived feature notes.');
const rendered=api.renderMarkdown('<script>alert(1)</script>\n\n- **Correction** réelle avec \x60code\x60');
assert(!rendered.includes('<script>')&&rendered.includes('&lt;script&gt;'),'Escape source HTML.');
assert(rendered.includes('<strong>Correction</strong>')&&rendered.includes('<code>code</code>'),'Support basic Markdown formatting.');
const current=api.cleanCurrentRelease('# V25.2.0\n\n> Candidat\n\n## Classes\n\n- Fonctionnalité\n\n## Validation et limites\n\nContenu interne de validation');
assert(current.includes('## Classes')&&!current.includes('Candidat')&&!current.includes('Contenu interne'));
console.log('OK — journal : historique extrait des archives présentes, lacunes préservées, source et rendu sûrs.');

assert(helper.includes('function closeJournal()'),'Closing the full journal from the automatic announcement must preserve the pending announcement.');

(async function testAutomaticAnnouncementInStrictMode(){
  const modal={classList:{added:[],add(name){this.added.push(name)}}};
  const calls=[];
  const automaticContext={
    window:{},
    console,
    document:{
      getElementById(id){return id==='modal'?modal:null},
      querySelector(){return null}
    },
    fetch:async url=>{
      calls.push(url);
      if(url==='/api/release-notes/state')return {
        ok:true,
        json:async()=>({version:'25.2.0',seen_version:''})
      };
      if(url==='/api/release-notes/history')return {
        ok:true,
        json:async()=>({
          current_version:'25.2.0',
          history_documents:docs,
          current_release_markdown:'# V25.2.0\\n\\n## Nouveautés\\n\\n- Écran des nouveautés par compte'
        })
      };
      throw new Error('Unexpected release-notes request: '+url);
    }
  };
  vm.runInNewContext(helper,automaticContext);
  let opened=null;
  automaticContext.window.openModal=(title,body)=>{opened={title,body}};
  automaticContext.window.MCReleaseNotes.maybeShow('V25.2.0','admin-test');
  await new Promise(resolve=>setTimeout(resolve,0));
  assert(opened,'A new account must receive the automatic release announcement.');
  assert(opened.title.includes('25.2.0'),'The automatic announcement must identify the installed version.');
  assert(opened.body.includes('Nouveautés de MaClasse'),'The automatic announcement must render its heading.');
  assert(modal.classList.added.includes('releaseNotesModal'),'The modal must receive its dedicated styling class.');
  assert.deepStrictEqual(calls,['/api/release-notes/state','/api/release-notes/history']);
  console.log('OK — ouverture automatique des nouveautés par compte en mode strict.');
})().catch(error=>{console.error(error);process.exitCode=1});

