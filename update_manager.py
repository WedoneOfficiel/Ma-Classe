#!/usr/bin/env python3
"""Safe, non-installing GitHub Release checker and updater archive preparer.

This module deliberately does not stop/restart MaClasse or activate code.
Installation is reserved for the independent supervisor, which is implemented
in a later AMEL-01 phase.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

OWNER = "WedoneOfficiel"
REPOSITORY = "Ma-Classe"
API_LATEST = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"
MANIFEST_ASSET = "maclasse-update.json"
USER_AGENT = "MaClasse-Updater/1"
MAX_MANIFEST_BYTES = 256 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_EXTRACTED_BYTES = 1024 * 1024 * 1024
ALLOWED_DOWNLOAD_HOSTS = {"api.github.com", "github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}
VERSION_RE = re.compile(r"^V?(\d+)\.(\d+)\.(\d+)$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class UpdateError(Exception):
    """An update release is invalid, unavailable, or unsafe."""


def _request(url: str, limit: int) -> bytes:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
        raise UpdateError("La ressource de mise à jour doit provenir de GitHub en HTTPS.")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            final = urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname not in ALLOWED_DOWNLOAD_HOSTS:
                raise UpdateError("Redirection hors des serveurs GitHub refusée.")
            data = response.read(limit + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError(f"Impossible de contacter le serveur des versions : {exc}") from exc
    if len(data) > limit:
        raise UpdateError("La ressource téléchargée dépasse la taille autorisée.")
    return data


def _version_tuple(value: str) -> tuple[int, int, int]:
    value = str(value or "")
    if len(value) > 32:
        raise UpdateError("Numéro de version trop long.")
    match = VERSION_RE.fullmatch(value)
    if not match:
        raise UpdateError("Numéro de version invalide.")
    return tuple(int(part) for part in match.groups())


def check_latest_release(current_version: str) -> dict:
    """Return validated stable release metadata; never trusts a draft/prerelease."""
    current = _version_tuple(current_version)
    try:
        release = json.loads(_request(API_LATEST, MAX_MANIFEST_BYTES).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError("Réponse GitHub invalide.") from exc

    if not isinstance(release, dict):
        raise UpdateError("Réponse de publication invalide.")
    if release.get("draft") or release.get("prerelease"):
        raise UpdateError("La version proposée n'est pas une publication stable.")
    tag = release.get("tag_name", "")
    published = _version_tuple(tag)
    if published <= current:
        return {"available": False, "current_version": current_version, "version": tag}

    assets = release.get("assets")
    if not isinstance(assets, list):
        raise UpdateError("La publication ne contient pas de liste de fichiers.")
    manifest_assets = [a for a in assets if isinstance(a, dict) and a.get("name") == MANIFEST_ASSET]
    if len(manifest_assets) != 1:
        raise UpdateError("Le manifeste de mise à jour est absent ou ambigu.")
    manifest_url = manifest_assets[0].get("browser_download_url", "")
    try:
        manifest = json.loads(_request(manifest_url, MAX_MANIFEST_BYTES).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError("Le manifeste de mise à jour est illisible.") from exc

    required = {"schema_version", "version", "tag_name", "min_data_schema",
                "archive_asset", "sha256", "release_notes"}
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise UpdateError("Le manifeste ne contient pas tous les champs requis.")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1 or manifest["tag_name"] != tag:
        raise UpdateError("Version de manifeste ou tag incohérent.")
    if _version_tuple(manifest["version"]) != published:
        raise UpdateError("La version du manifeste ne correspond pas à la release.")
    if type(manifest["min_data_schema"]) is not int or manifest["min_data_schema"] < 1:
        raise UpdateError("Version minimale du schéma de données invalide.")
    if not isinstance(manifest["release_notes"], str) or len(manifest["release_notes"]) > 20000:
        raise UpdateError("Notes de version invalides.")
    archive_name = manifest["archive_asset"]
    if not isinstance(archive_name, str) or not re.fullmatch(r"[A-Za-z0-9._-]+\.zip", archive_name):
        raise UpdateError("Nom d'archive invalide.")
    if not isinstance(manifest["sha256"], str) or not SHA256_RE.fullmatch(manifest["sha256"]):
        raise UpdateError("Empreinte SHA-256 invalide.")
    archive_assets = [a for a in assets if isinstance(a, dict) and a.get("name") == archive_name]
    if len(archive_assets) != 1:
        raise UpdateError("Archive de la version absente ou ambiguë.")
    archive_url = archive_assets[0].get("browser_download_url", "")
    if not isinstance(archive_url, str) or not archive_url.startswith("https://"):
        raise UpdateError("URL de téléchargement invalide.")

    return {
        "available": True,
        "current_version": current_version,
        "version": tag,
        "html_url": release.get("html_url", ""),
        "published_at": release.get("published_at", ""),
        "release_notes": manifest["release_notes"],
        "min_data_schema": manifest["min_data_schema"],
        "archive_name": archive_name,
        "archive_url": archive_url,
        "sha256": manifest["sha256"],
    }


def _safe_member_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or not name or "\\" in name or any(part in ("", ".", "..") for part in path.parts):
        raise UpdateError("L'archive contient un chemin dangereux.")
    if path.parts and re.match(r"^[A-Za-z]:", path.parts[0]):
        raise UpdateError("L'archive contient un chemin Windows interdit.")
    return path


def prepare_release(release: dict, staging_root: str | Path) -> Path:
    """Download, hash-check and safely extract an archive into an isolated staging dir."""
    staging_root = Path(staging_root).resolve()
    staging_root.mkdir(parents=True, exist_ok=True)
    raw = _request(release["archive_url"], MAX_ARCHIVE_BYTES)
    if hashlib.sha256(raw).hexdigest() != release["sha256"]:
        raise UpdateError("L'empreinte de l'archive ne correspond pas au manifeste.")
    target = Path(tempfile.mkdtemp(prefix="prepared-", dir=staging_root))
    total = 0
    try:
        with zipfile.ZipFile(__import__("io").BytesIO(raw)) as archive:
            for info in archive.infolist():
                member = _safe_member_path(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise UpdateError("Les liens symboliques sont interdits dans l'archive.")
                total += info.file_size
                if total > MAX_EXTRACTED_BYTES:
                    raise UpdateError("L'archive décompressée dépasse la taille autorisée.")
                destination = (target / Path(*member.parts)).resolve()
                if os.path.commonpath((str(destination), str(target))) != str(target):
                    raise UpdateError("Chemin d'extraction hors du dossier temporaire.")
                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, destination.open("xb") as output:
                    shutil.copyfileobj(source, output)
                destination.chmod(0o755 if mode == 0o100755 else 0o644)
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        shutil.rmtree(target, ignore_errors=True)
        if isinstance(exc, UpdateError):
            raise
        raise UpdateError(f"Archive ZIP invalide : {exc}") from exc
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise
    try:
        metadata = {key: release.get(key) for key in ("version", "min_data_schema", "sha256")}
        metadata.update({"prepared_at": int(time.time()), "status": "prepared"})
        (target / "maclasse-prepared.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        shutil.rmtree(target, ignore_errors=True)
        raise UpdateError(f"Impossible d'enregistrer les métadonnées de préparation : {exc}") from exc
    return target


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Vérifier et préparer une release MaClasse (sans l'installer).")
    parser.add_argument("--current", default="25.0.22", help="Version installée")
    parser.add_argument("--staging", default="data/update-staging", help="Dossier temporaire de préparation")
    args = parser.parse_args()
    try:
        release = check_latest_release(args.current)
        if not release["available"]:
            print(f"MaClasse est à jour ({args.current}).")
            raise SystemExit(0)
        print(f"Version disponible : {release['version']}")
        prepared = prepare_release(release, args.staging)
        print(f"Archive vérifiée et préparée : {prepared}")
        print("Aucune installation ni interruption du serveur n'a été effectuée.")
    except UpdateError as exc:
        print(f"Vérification interrompue : {exc}", file=sys.stderr)
        raise SystemExit(1)
