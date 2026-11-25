#!/usr/bin/env python3
"""Offline tests for Ed25519 release signing and key pinning."""
import base64
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import release_signing


class ReleaseSigningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.public_path = Path(self.temp.name) / "release-signing-public-key.txt"
        self.key = Ed25519PrivateKey.generate()
        self.private_raw = self.key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self.public_raw = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.private_b64 = base64.b64encode(self.private_raw).decode("ascii")
        self.public_path.write_text(base64.b64encode(self.public_raw).decode("ascii") + "\n", encoding="ascii")
        self.key_path_patch = patch.object(release_signing, "PUBLIC_KEY_FILE", self.public_path)
        self.key_path_patch.start()
        self.addCleanup(self.key_path_patch.stop)

    def test_signing_and_verification_use_exact_manifest_bytes(self):
        payload = b'{"version":"25.1.0","tag_name":"v25.1.0"}\n'
        signature = release_signing.sign_manifest(payload, self.private_b64)
        self.assertTrue(release_signing.verify_manifest_signature(payload, signature.encode("ascii")))
        with self.assertRaises(release_signing.ReleaseSignatureError):
            release_signing.verify_manifest_signature(payload + b" ", signature.encode("ascii"))

    def test_wrong_private_key_cannot_sign_for_the_pinned_public_key(self):
        other = Ed25519PrivateKey.generate().private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with self.assertRaisesRegex(release_signing.ReleaseSignatureError, "ne correspond pas"):
            release_signing.sign_manifest(b"manifest", base64.b64encode(other).decode("ascii"))

    def test_invalid_or_missing_public_key_fails_closed(self):
        self.public_path.write_text("# public key is not configured\n", encoding="ascii")
        with self.assertRaisesRegex(release_signing.ReleaseSignatureError, "non configurée"):
            release_signing.load_public_key()
        self.public_path.write_text("not-base64!!!\n", encoding="ascii")
        with self.assertRaises(release_signing.ReleaseSignatureError):
            release_signing.load_public_key()

    def test_key_generator_cli_writes_private_key_outside_repository_with_restricted_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            private_path = Path(temp) / "secrets" / "release-private.b64"
            public_path = Path(temp) / "public" / "release-signing-public-key.txt"
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "generate_release_signing_key.py"),
                "--private-out", str(private_path), "--public-out", str(public_path)
            ], check=True, capture_output=True, text=True, timeout=20)
            private_raw = base64.b64decode(private_path.read_text(encoding="ascii").strip(), validate=True)
            public_raw = base64.b64decode(public_path.read_text(encoding="ascii").strip(), validate=True)
            self.assertEqual(len(private_raw), 32)
            self.assertEqual(len(public_raw), 32)
            self.assertNotEqual(private_path.resolve(), ROOT)
            self.assertNotIn(ROOT, private_path.resolve().parents)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(private_path.stat().st_mode), 0o600)

    def test_sign_release_cli_signs_manifest_and_fails_closed_without_secret(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "release-tool"
            scripts = root / "scripts"
            scripts.mkdir(parents=True)
            shutil.copy2(ROOT / "release_signing.py", root / "release_signing.py")
            shutil.copy2(ROOT / "scripts" / "sign_release.py", scripts / "sign_release.py")
            (root / "release-signing-public-key.txt").write_text(
                base64.b64encode(self.public_raw).decode("ascii") + "\n", encoding="ascii"
            )
            manifest = root / "maclasse-update.json"
            payload = b'{"version":"25.1.0","tag_name":"v25.1.0"}\n'
            manifest.write_bytes(payload)
            signature = root / "maclasse-update.sig"
            env = os.environ.copy()
            env["MACLASSE_RELEASE_SIGNING_KEY_B64"] = self.private_b64
            subprocess.run([
                sys.executable, str(scripts / "sign_release.py"),
                "--manifest", str(manifest), "--signature", str(signature)
            ], check=True, env=env, capture_output=True, text=True, timeout=20)
            self.assertTrue(release_signing.verify_manifest_signature(
                payload, signature.read_bytes(), public_key=self.public_raw
            ))
            absent_secret_env = dict(env)
            absent_secret_env.pop("MACLASSE_RELEASE_SIGNING_KEY_B64", None)
            missing_signature = root / "missing-secret.sig"
            result = subprocess.run([
                sys.executable, str(scripts / "sign_release.py"),
                "--manifest", str(manifest), "--signature", str(missing_signature)
            ], env=absent_secret_env, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertIn("secret GitHub Actions absent", result.stderr)
            self.assertFalse(missing_signature.exists())

    def test_malformed_and_invalid_signatures_are_rejected(self):
        payload = b"manifest"
        with self.assertRaises(release_signing.ReleaseSignatureError):
            release_signing.verify_manifest_signature(payload, b"not base64")
        signature = base64.b64encode(b"0" * release_signing.SIGNATURE_BYTES)
        with self.assertRaises(release_signing.ReleaseSignatureError):
            release_signing.verify_manifest_signature(payload, signature)


if __name__ == "__main__":
    unittest.main()
