#!/usr/bin/env python3
"""Concurrency regressions: attachment mutations must not race backup/restore."""
from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path
import tempfile
import threading
import time
import zipfile
import importlib.util
from unittest.mock import patch

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
        ("\n        if path=='/api/upload':", "\n        self.send_error(404)"),
    ]
    for start_marker, end_marker in route_markers:
        start = source.index(start_marker)
        end = source.index(end_marker, start + len(start_marker))
        route = source[start:end]
        assert "with UPLOADS_LOCK:" in route, f"Route non verrouillée : {start_marker}"

    restore_start = source.index("if path=='/api/backup/restore':")
    restore_end = source.index("if path=='/api/bulletin-pdf':", restore_start)
    restore_route = source[restore_start:restore_end]
    assert "with DATA_LOCK, UPLOADS_LOCK:" in restore_route, (
        "La restauration doit exclure les écritures concurrentes pendant tout le staging."
    )


def test_restore_rolls_back_both_stores_if_database_swap_fails():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        database = data_dir / "maclasse.json"
        original_json = json.dumps({"classes": [{"id": "before"}], "students": []}).encode()
        database.write_bytes(original_json)
        (uploads / "keep.txt").write_text("ancienne pièce jointe", encoding="utf-8")
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database)
        server.UPLOADS = str(uploads)

        raw = make_archive(
            {"classes": [{"id": "after"}], "students": [{"id": "s1"}], "users": []},
            {"new.txt": "nouvelle pièce jointe"},
        )
        real_replace = server.os.replace
        failed = {"value": False}

        def fail_new_database_once(source, destination):
            if (
                not failed["value"]
                and Path(destination) == database
                and Path(source).name == "maclasse.json"
                and "maclasse-restore-" in str(source)
            ):
                failed["value"] = True
                raise OSError("échec simulé du remplacement de la base")
            return real_replace(source, destination)

        with patch.object(server.os, "replace", side_effect=fail_new_database_once):
            try:
                server._restore_backup_archive(raw)
                raise AssertionError("Une erreur de bascule simulée aurait dû échouer.")
            except OSError as error:
                assert "échec simulé" in str(error)

        assert failed["value"], "Le test doit échouer précisément au remplacement final de la base."
        assert database.read_bytes() == original_json
        assert (uploads / "keep.txt").read_text(encoding="utf-8") == "ancienne pièce jointe"
        assert not list(data_dir.glob("maclasse-restore-*")), "Un rollback réussi doit nettoyer son staging."


def test_restore_preserves_recovery_copy_if_rollback_itself_fails():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        database = data_dir / "maclasse.json"
        original_json = json.dumps({"classes": [{"id": "before"}], "students": []}).encode()
        database.write_bytes(original_json)
        (uploads / "keep.txt").write_text("ancienne pièce jointe", encoding="utf-8")
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database)
        server.UPLOADS = str(uploads)

        raw = make_archive(
            {"classes": [{"id": "after"}], "students": [{"id": "s1"}], "users": []},
            {"new.txt": "nouvelle pièce jointe"},
        )
        real_replace = server.os.replace

        def fail_swap_and_upload_rollback(source, destination):
            source_name = Path(source).name
            if (
                Path(destination) == database
                and source_name == "maclasse.json"
                and "maclasse-restore-" in str(source)
            ):
                raise OSError("échec simulé de la bascule")
            if source_name == "uploads-before-restore" and Path(destination) == uploads:
                raise OSError("échec simulé du retour des pièces jointes")
            return real_replace(source, destination)

        with patch.object(server.os, "replace", side_effect=fail_swap_and_upload_rollback):
            try:
                server._restore_backup_archive(raw)
                raise AssertionError("Le retour arrière incomplet aurait dû être signalé.")
            except RuntimeError as error:
                message = str(error).lower()
                assert "retour arrière est incomplet" in message
                assert "dossier de récupération" in message

        recovery_dirs = list(data_dir.glob("maclasse-restore-*"))
        assert len(recovery_dirs) == 1, "Le staging doit être conservé après échec du rollback."
        saved_upload = recovery_dirs[0] / "uploads-before-restore" / "keep.txt"
        assert saved_upload.read_text(encoding="utf-8") == "ancienne pièce jointe"
        assert database.read_bytes() == original_json
        assert not uploads.exists(), "Le dossier de récupération doit rester distinct du dossier actif manquant."


def test_backup_rejects_symlinked_upload_files_and_directories():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        database = data_dir / "maclasse.json"
        database.write_text(json.dumps({"classes": [], "students": []}), encoding="utf-8")
        outside = root / "secret-outside-uploads.txt"
        outside.write_text("ne doit jamais entrer dans l'archive", encoding="utf-8")
        try:
            (uploads / "leak.txt").symlink_to(outside)
            (uploads / "linked-directory").symlink_to(root, target_is_directory=True)
        except (OSError, NotImplementedError):
            return
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database)
        server.UPLOADS = str(uploads)
        try:
            BackupHarness()._create_backup(force=True)
            raise AssertionError("Une sauvegarde contenant des liens symboliques aurait dû être refusée.")
        except ValueError as error:
            assert "liens symboliques" in str(error) or "lien symbolique" in str(error)
        backup_dir = data_dir / "backups"
        assert not list(backup_dir.glob("maclasse-*.zip")), "Aucune archive ne doit être publiée."
        assert not list(backup_dir.glob("*.tmp")), "Aucun fichier temporaire ne doit subsister."


def test_backup_refuses_symlinked_database_and_backup_directory_paths():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        outside = root / "outside.json"
        outside.write_text(json.dumps({"classes": [], "students": []}), encoding="utf-8")
        database_link = data_dir / "maclasse.json"
        try:
            database_link.symlink_to(outside)
        except (OSError, NotImplementedError):
            return
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database_link)
        server.UPLOADS = str(uploads)
        try:
            BackupHarness()._create_backup(force=True)
            raise AssertionError("Une base symbolique aurait dû être refusée.")
        except ValueError as error:
            assert "base doit être un fichier normal" in str(error)
        assert outside.read_text(encoding="utf-8") == json.dumps({"classes": [], "students": []})
        database_link.unlink()

        server.DATA_FILE = str(outside)
        server.DATA_DIR = str(data_dir)
        server.UPLOADS = str(uploads)
        external_backups = root / "external-backups"
        external_backups.mkdir()
        (external_backups / "keep.txt").write_text("ne pas toucher", encoding="utf-8")
        backup_link = data_dir / "backups"
        try:
            backup_link.symlink_to(external_backups, target_is_directory=True)
        except (OSError, NotImplementedError):
            return
        try:
            BackupHarness()._create_backup(force=True)
            raise AssertionError("Un dossier backups symbolique aurait dû être refusé.")
        except ValueError as error:
            assert "dossier backups" in str(error)
        assert (external_backups / "keep.txt").read_text(encoding="utf-8") == "ne pas toucher"
        assert not list(external_backups.glob("maclasse-*"))


def test_backup_refuses_a_snapshot_larger_than_the_restore_limit():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        database = data_dir / "maclasse.json"
        database.write_text(json.dumps({"classes": [{"id": "large"}], "students": []}), encoding="utf-8")
        (uploads / "piece.txt").write_text("contenu", encoding="utf-8")
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database)
        server.UPLOADS = str(uploads)
        with patch.object(server, "MAX_BACKUP_UNCOMPRESSED_BYTES", 8):
            try:
                BackupHarness()._create_backup(force=True)
                raise AssertionError("Une sauvegarde au-delà du plafond de restauration aurait dû être refusée.")
            except ValueError as error:
                assert "limite de restauration" in str(error)
        backup_dir = data_dir / "backups"
        assert not list(backup_dir.glob("maclasse-*.json"))
        assert not list(backup_dir.glob("maclasse-*.zip"))


def test_backup_publishes_zip_atomically_and_incomplete_attempt_does_not_throttle():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data_dir = root / "data"
        uploads = data_dir / "uploads"
        uploads.mkdir(parents=True)
        database = data_dir / "maclasse.json"
        database.write_text(json.dumps({"classes": [{"id": "6A"}], "students": []}), encoding="utf-8")
        (uploads / "piece.txt").write_text("pièce complète", encoding="utf-8")
        server.DATA_DIR = str(data_dir)
        server.DATA_FILE = str(database)
        server.UPLOADS = str(uploads)
        server.BACKUP_INTERVAL_SECONDS = 86400
        backup_dir = data_dir / "backups"
        original_open = server.zipfile.ZipFile.open

        def fail_while_archiving_uploads(archive, name, mode="r", *args, **kwargs):
            if isinstance(name, str) and name.startswith("data/uploads/"):
                raise OSError("échec simulé pendant l'archivage des pièces jointes")
            return original_open(archive, name, mode, *args, **kwargs)

        with patch.object(server.zipfile.ZipFile, "open", new=fail_while_archiving_uploads):
            try:
                BackupHarness()._create_backup(force=True)
                raise AssertionError("La panne d'archivage simulée aurait dû échouer.")
            except OSError as error:
                assert "échec simulé" in str(error)

        assert len(list(backup_dir.glob("maclasse-*.json"))) == 1, "La copie JSON complète reste disponible."
        assert not list(backup_dir.glob("maclasse-*.zip")), "Un ZIP incomplet ne doit jamais être publié."
        assert not list(backup_dir.glob("*.tmp")), "Les fichiers temporaires doivent être nettoyés."

        time.sleep(0.002)
        name = BackupHarness()._create_backup(force=False)
        assert name and (backup_dir / name).is_file(), "Un JSON orphelin ne doit pas retarder la prochaine sauvegarde complète."
        with zipfile.ZipFile(backup_dir / name) as archive:
            assert archive.read("data/uploads/piece.txt") == "pièce complète".encode()
            assert archive.testzip() is None
        json_backup = backup_dir / (Path(name).stem + ".json")
        assert stat.S_IMODE(os.stat(backup_dir).st_mode) == 0o700
        assert stat.S_IMODE(os.stat(json_backup).st_mode) == 0o600
        assert stat.S_IMODE(os.stat(backup_dir / name).st_mode) == 0o600



if __name__ == "__main__":
    test_backup_waits_for_upload_mutations()
    test_restore_waits_for_upload_mutations()
    test_every_upload_mutation_route_uses_the_shared_lock()
    test_restore_rolls_back_both_stores_if_database_swap_fails()
    test_restore_preserves_recovery_copy_if_rollback_itself_fails()
    test_backup_publishes_zip_atomically_and_incomplete_attempt_does_not_throttle()
    test_backup_rejects_symlinked_upload_files_and_directories()
    test_backup_refuses_a_snapshot_larger_than_the_restore_limit()
    test_backup_refuses_symlinked_database_and_backup_directory_paths()
    print("OK — verrouillage, snapshots atomiques privés, refus des liens symboliques et tailles non restaurables, rollback et conservation du dossier de récupération.")
