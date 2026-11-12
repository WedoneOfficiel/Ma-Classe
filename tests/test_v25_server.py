import importlib.util, json, pathlib, tempfile, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('maclasse_server_v25', ROOT / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    data_dir = root / 'data'
    uploads = data_dir / 'uploads'
    uploads.mkdir(parents=True)
    data_file = data_dir / 'maclasse.json'
    data_file.write_text(json.dumps({'classes': []}), encoding='utf-8')
    (uploads / 'piece-test.txt').write_text('document de test', encoding='utf-8')
    server.ROOT = str(root)
    server.DATA_DIR = str(data_dir)
    server.DATA_FILE = str(data_file)
    server.UPLOADS = str(uploads)
    handler = object.__new__(server.Handler)
    name = handler._create_backup(force=True)
    archive_path = data_dir / 'backups' / name
    assert archive_path.suffix == '.zip'
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert 'data/maclasse.json' in names
        assert 'data/uploads/piece-test.txt' in names
        assert archive.read('data/uploads/piece-test.txt') == b'document de test'
print('OK — sauvegarde V25 : données JSON et fichiers téléversés réunis dans une archive ZIP.')
