#!/usr/bin/env python3
"""Offline tests for Ed25519 release signing and key pinning."""
import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

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

    def test_malformed_and_invalid_signatures_are_rejected(self):
        payload = b"manifest"
        with self.assertRaises(release_signing.ReleaseSignatureError):
            release_signing.verify_manifest_signature(payload, b"not base64")
        signature = base64.b64encode(b"0" * release_signing.SIGNATURE_BYTES)
        with self.assertRaises(release_signing.ReleaseSignatureError):
            release_signing.verify_manifest_signature(payload, signature)


if __name__ == "__main__":
    unittest.main()
