import ast, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
server = (ROOT / 'server.py').read_text(encoding='utf-8')
js = (ROOT / '_all.js').read_text(encoding='utf-8')
html = (ROOT / 'index.html').read_text(encoding='utf-8')

ast.parse(server)
assert "Access-Control-Allow-Origin" not in server
assert "if not self._require_local_origin(): return" in server
assert "if not parts: return self._json({'error':'Chemin invalide'},400)" in server
assert "BACKUP_RETENTION_DAYS=30" in server
assert "BACKUP_INTERVAL_SECONDS=6*60*60" in server
assert "for pattern in ('maclasse-*.json','maclasse-*.zip')" in server
assert "with open_snapshot_source(DATA_FILE,database_stat) as source, archive.open('data/maclasse.json','w') as target:" in server
assert "archive.open(archive_name,'w')" in server
assert "followlinks=False" in server
assert "getattr(os,'O_NOFOLLOW',0)" in server
assert "MAX_BACKUP_ARCHIVE_BYTES=512*1024*1024" in server
assert "MAX_BACKUP_UNCOMPRESSED_BYTES=500*1024*1024" in server
assert 'DATA_LOCK=threading.RLock()' in server
assert 'bulletinSetView(\'overview\')' in js
assert 'bulletinSetView(\'subject\')' in js
assert 'data-bulletin-subject="${esc(sub)}"' in js
assert 'JSON.stringify(sub).replace' not in js
assert 'MaClasse V21.22' in html
print('V25 security/persistence regression checks: OK')
