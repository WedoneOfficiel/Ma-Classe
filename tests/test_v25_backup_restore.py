import importlib.util, io, json, pathlib, tempfile, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('maclasse_server_v25_restore', ROOT / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    data_dir = root / 'data'
    uploads = data_dir / 'uploads'
    uploads.mkdir(parents=True)
    data_file = data_dir / 'maclasse.json'
    data_file.write_text(json.dumps({'classes': [{'id': 'old'}], 'students': []}), encoding='utf-8')
    (uploads / 'old.txt').write_text('old file', encoding='utf-8')
    server.DATA_DIR = str(data_dir)
    server.DATA_FILE = str(data_file)
    server.UPLOADS = str(uploads)

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('data/maclasse.json', json.dumps({'classes': [{'id': 'new'}], 'students': [{'id': 's1'}], 'users': []}))
        z.writestr('data/uploads/new.txt', 'new file')
    stats = server._restore_backup_archive(archive.getvalue())
    restored = json.loads(data_file.read_text(encoding='utf-8'))
    assert restored['classes'][0]['id'] == 'new'
    assert restored['students'][0]['id'] == 's1'
    assert not (uploads / 'old.txt').exists()
    assert (uploads / 'new.txt').read_text(encoding='utf-8') == 'new file'
    assert stats == {'classes': 1, 'students': 1, 'files': 1}

    malicious = io.BytesIO()
    with zipfile.ZipFile(malicious, 'w') as z:
        z.writestr('data/maclasse.json', '{}')
        z.writestr('data/uploads/../../outside.txt', 'bad')
    before = data_file.read_bytes()
    try:
        server._restore_backup_archive(malicious.getvalue())
        raise AssertionError('Une archive traversant les chemins aurait dû être refusée.')
    except ValueError:
        pass
    assert data_file.read_bytes() == before
    assert (uploads / 'new.txt').exists()

    invalid = io.BytesIO(b'not a zip')
    try:
        server._restore_backup_archive(invalid.getvalue())
        raise AssertionError('Un fichier non ZIP aurait dû être refusé.')
    except ValueError:
        pass
print('OK — restauration complète, remplacement des fichiers et refus des archives malveillantes.')
