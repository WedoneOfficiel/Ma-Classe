#!/usr/bin/env python3
"""Concurrency regressions: attachment mutations must not race backup/restore."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import threading
import time
import zipfile
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("maclasse_server_upload_locks", ROOT / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class BackupHarness:
    def _backup_dir(self):
        path = Path(server.DATA_DIR) / "backups"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    _create_backup = server.Handler._create_backup
    _create_backup_locked = server.Handler._create_backup_locked


def make_archive(database, uploads):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("data/maclasse.json", json.dumps(database))
        for name, payload in uploads.items():
            archive.writestr("data/uploads/" + name, payload)
    return buffer.getvalue()


def test_backup_waits_for_upload_mutations():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        database = data_dir / "maclasse.json"
        database.write_text(json.dumps({"classes": [{"id": "6A"}], "students": []}), encoding="utf-8")
        (uploads / "piece.txt").write_text("contenu complet", encoding="utf-8")
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database)
        server.UPLOADS = str(uploads)

        started = threading.Event()
        finished = threading.Event()
        result = {}
        errors = []

        def create_backup():
            started.set()
            try:
                result["name"] = BackupHarness()._create_backup(force=True)
            except Exception as error:  # pragma: no cover - diagnostic path
                errors.append(error)
            finally:
                finished.set()

        server.UPLOADS_LOCK.acquire()
        worker = threading.Thread(target=create_backup, daemon=True)
        try:
            worker.start()
            assert started.wait(2), "Le thread de sauvegarde n'a pas démarré."
            assert not finished.wait(0.2), "La sauvegarde doit attendre la fin d'une mutation de fichier en cours."
        finally:
            server.UPLOADS_LOCK.release()
        worker.join(timeout=5)
        assert not worker.is_alive(), "La sauvegarde n'a pas terminé après libération du verrou."
        assert not errors, f"Erreur de sauvegarde : {errors!r}"
        backup_path = data_dir / "backups" / result["name"]
        assert backup_path.is_file()
        with zipfile.ZipFile(backup_path) as archive:
            assert archive.read("data/uploads/piece.txt") == b"contenu complet"
            saved = json.loads(archive.read("data/maclasse.json"))
            assert saved["classes"][0]["id"] == "6A"


def test_restore_waits_for_upload_mutations():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        database = data_dir / "maclasse.json"
        database.write_text(json.dumps({"classes": [{"id": "before"}], "students": []}), encoding="utf-8")
        (uploads / "keep.txt").write_text("avant", encoding="utf-8")
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database)
        server.UPLOADS = str(uploads)

        raw = make_archive(
            {"classes": [{"id": "after"}], "students": [{"id": "s1"}], "users": []},
            {"restored.txt": "après"},
        )
        started = threading.Event()
        finished = threading.Event()
        errors = []

        def restore():
            started.set()
            try:
                server._restore_backup_archive(raw)
            except Exception as error:  # pragma: no cover - diagnostic path
                errors.append(error)
            finally:
                finished.set()

        server.UPLOADS_LOCK.acquire()
        worker = threading.Thread(target=restore, daemon=True)
        try:
            worker.start()
            assert started.wait(2), "Le thread de restauration n'a pas démarré."
            assert not finished.wait(0.2), "La restauration doit attendre avant de basculer le dossier uploads."
            assert (uploads / "keep.txt").read_text(encoding="utf-8") == "avant"
            assert json.loads(database.read_text(encoding="utf-8"))["classes"][0]["id"] == "before"
        finally:
            server.UPLOADS_LOCK.release()
        worker.join(timeout=5)
        assert not worker.is_alive(), "La restauration n'a pas repris après libération du verrou."
        assert not errors, f"Erreur de restauration : {errors!r}"
        assert not (uploads / "keep.txt").exists()
        assert (uploads / "restored.txt").read_text(encoding="utf-8") == "après"
        assert json.loads(database.read_text(encoding="utf-8"))["classes"][0]["id"] == "after"


def test_every_upload_mutation_route_uses_the_shared_lock():
    source = (ROOT / "server.py").read_text(encoding="utf-8")
    route_markers = [
        ("if path=='/api/cloud-mkdir':", "if path=='/api/cloud-rename':"),
        ("if path=='/api/cloud-rename':", "if path=='/api/cloud-move':"),
        ("if path=='/api/cloud-move':", "if path=='/api/cloud-copy':"),
        ("if path=='/api/cloud-copy':", "if path=='/api/cloud-delete':"),
        ("if path=='/api/cloud-delete':", "if path=='/api/delete-upload':"),
        ("if path=='/api/delete-upload':", "if path=='/api/reset':"),
        ("if path=='/api/upload':", "self.send_error(404)"),
    ]
    for start_marker, end_marker in route_markers:
        start = source.index(start_marker)
        end = source.index(end_marker, start + len(start_marker))
        route = source[start:end]
        assert "with UPLOADS_LOCK:" in route, f"Route non verrouillée : {start_marker}"


if __name__ == "__main__":
    test_backup_waits_for_upload_mutations()
    test_restore_waits_for_upload_mutations()
    test_every_upload_mutation_route_uses_the_shared_lock()
    print("OK — sauvegarde, restauration et mutations de pièces jointes partagent un verrou de cohérence.")
