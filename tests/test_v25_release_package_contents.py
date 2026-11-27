#!/usr/bin/env python3
"""Verify the exact git-archive packaging strategy used for stable releases."""
from __future__ import annotations

import io
from pathlib import Path
import subprocess
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-release.yml"

REQUIRED_RELEASE_FILES = {
    "VERSION.txt",
    "index.html",
    "_all.js",
    "class_tracking.js",
    "release_notes.js",
    "server.py",
    "requirements.txt",
    "update_manager.py",
    "release_signing.py",
    "release-signing-public-key.txt",
    "network_supervisor.py",
    "establishment_import.py",
    "Installer-MaClasse.command",
    "Installer-MaClasse-Linux.sh",
    "Configurer-MaClasse-Reseau.command",
    "Configurer-MaClasse-Reseau.sh",
    "Desinstaller-Service-MaClasse-Linux.sh",
    "Installer-Mise-A-Jour-Directe-MaClasse-macOS.sh",
    "Lancer-MaClasse.command",
    "Lancer-MaClasse-Reseau.command",
    "Mettre-A-Jour-MaClasse-Linux.sh",
    "Mettre-A-Jour-MaClasse.command",
    "Installer-Service-MaClasse-macOS.sh",
    "Installer-Service-MaClasse-Linux.sh",
    "Lancer-MaClasse-Service-macOS.sh",
    "Lancer-MaClasse-Service-Linux.sh",
    "Appliquer-Mise-A-Jour-MaClasse-macOS.sh",
    "Appliquer-Mise-A-Jour-MaClasse-Linux.sh",
    "docs/HISTORIQUE_VERSIONS.md",
    "docs/archives/ETATS_AUDITS_ET_RECETTES_ANTERIEURS.md",
    "docs/archives/README_PRE_REORGANISATION.md",
    "docs/releases/v25.2.0.md",
}


class ReleasePackageContentsTests(unittest.TestCase):
    def test_release_workflow_archives_the_validated_commit(self):
        workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            'git archive --format=zip "$GITHUB_SHA" > dist/maclasse-update.zip',
            workflow,
            "The release must archive the exact validated commit.",
        )

    def test_release_archive_contains_runtime_and_all_release_history_sources(self):
        process = subprocess.run(
            ["git", "archive", "--format=zip", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        with zipfile.ZipFile(io.BytesIO(process.stdout)) as archive:
            names = set(archive.namelist())
            missing = sorted(REQUIRED_RELEASE_FILES - names)
            self.assertFalse(
                missing,
                "The stable update ZIP is missing required runtime/history files: "
                + ", ".join(missing),
            )
            self.assertIsNone(
                archive.testzip(),
                "The generated git archive must not contain a corrupt ZIP member.",
            )

if __name__ == "__main__":
    unittest.main()
