#!/usr/bin/env python3
"""Linux integration simulation for atomic update, health-check and rollback."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform.startswith("linux"), "Le moteur d'installation cible systemd/Linux.")
class UpdateApplyIntegrationTests(unittest.TestCase):
    def make_version(self, directory, version, sha=None):
        directory.mkdir(parents=True)
        (directory / "VERSION.txt").write_text("V" + version + "\n", encoding="utf-8")
        (directory / "server.py").write_text("APP_VERSION='" + version + "'\n", encoding="utf-8")
        (directory / "_all.js").write_text("const MC_VERSION='V" + version + "';\n", encoding="utf-8")
        (directory / ".venv" / "bin").mkdir(parents=True)
        (directory / ".venv" / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
        (directory / ".venv" / "bin" / "python").chmod(0o755)
        (directory / "maclasse-runtime-ready.json").write_text('{"ready":true}', encoding="utf-8")
        if sha:
            (directory / "maclasse-prepared.json").write_text(json.dumps({
                "version": version, "sha256": sha, "status": "prepared"
            }), encoding="utf-8")

    def run_update(self, fail_version=None):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            program = base / "program"
            data = program / "data"
            versions = data / "program" / "versions"
            versions.mkdir(parents=True)
            previous = versions / "V25.0.22"
            self.make_version(previous, "25.0.22")
            current = data / "program" / "current"
            current.symlink_to("versions/V25.0.22")
            target = versions / "V25.0.23"
            sha = "a" * 64
            self.make_version(target, "25.0.23", sha)
            (data / "tls").mkdir()
            (data / "tls" / "server.crt").write_text("test cert", encoding="utf-8")
            (data / "tls" / "ca.crt").write_text("test CA", encoding="utf-8")
            (data / "maclasse.json").write_text('{"settings":{"school":"Test"}}', encoding="utf-8")
            (data / "update-state.json").write_text(json.dumps({
                "status": "prepared", "version": "v25.0.23", "sha256": sha
            }), encoding="utf-8")

            fakebin = base / "bin"
            fakebin.mkdir()
            systemctl_log = base / "systemctl.log"
            stubs = {
                "systemctl": '#!/bin/sh\necho "$*" >> "$SYSTEMCTL_LOG"\nexit 0\n',
                "openssl": '#!/bin/sh\necho "X509v3 Subject Alternative Name: IP Address:192.168.1.10"\n',
                "curl": '#!/bin/sh\nversion="$(cat "$CURRENT_LINK/VERSION.txt" | sed "s/^V//")"\nif [ "$version" = "$FAIL_VERSION" ]; then echo \'{"ok":false,"version":"$version","database":"error"}\'; else printf \'{"ok":true,"version":"%s","database":"ok"}\' "$version"; fi\n',
                "sleep": '#!/bin/sh\nexit 0\n',
            }
            for name, source in stubs.items():
                path = fakebin / name
                path.write_text(source, encoding="utf-8")
                path.chmod(0o755)

            env = os.environ.copy()
            env.update({
                "PATH": str(fakebin) + os.pathsep + env.get("PATH", ""),
                "MACLASSE_ROOT": str(program),
                "CURRENT_LINK": str(current),
                "SYSTEMCTL_LOG": str(systemctl_log),
                "FAIL_VERSION": fail_version or "",
            })
            result = subprocess.run(
                ["/usr/bin/bash", str(ROOT / "Appliquer-Mise-A-Jour-MaClasse-Linux.sh")],
                cwd=program, env=env, capture_output=True, text=True, timeout=30
            )
            state = json.loads((data / "update-state.json").read_text(encoding="utf-8"))
            return result, current.resolve(), previous.resolve(), target.resolve(), state, data

    def test_success_switches_atomically_and_preserves_persistent_data(self):
        result, active, previous, target, state, data = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(active, target)
        self.assertEqual(state["status"], "installed")
        self.assertEqual(json.loads((data / "maclasse.json").read_text())["settings"]["school"], "Test")
        self.assertEqual(len(list((data / "backups").glob("maclasse-avant-maj-*.json"))), 1)

    def test_failed_health_check_restores_previous_release(self):
        result, active, previous, target, state, data = self.run_update(fail_version="25.0.23")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(active, previous)
        self.assertEqual(state["status"], "failed")
        self.assertIn("version précédente restaurée", state["last_error"])
        self.assertEqual(json.loads((data / "maclasse.json").read_text())["settings"]["school"], "Test")


if __name__ == "__main__":
    unittest.main()
