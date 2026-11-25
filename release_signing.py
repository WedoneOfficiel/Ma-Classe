#!/usr/bin/env python3
"""Ed25519 signing and verification for MaClasse release manifests."""
from __future__ import annotations

import base64
import binascii
import hmac
from pathlib import Path

PUBLIC_KEY_FILE = Path(__file__).with_name("release-signing-public-key.txt")
PUBLIC_KEY_BYTES = 32
SIGNATURE_BYTES = 64


class ReleaseSignatureError(Exception):
    """A MaClasse release signature is missing, malformed, or invalid."""


def _decode_b64(value: str, label: str, expected_bytes: int) -> bytes:
    if not isinstance(value, str):
        raise ReleaseSignatureError(f"{label} absent ou invalide.")
    compact = "".join(value.split())
    try:
        decoded = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ReleaseSignatureError(f"{label} n'est pas un Base64 valide.") from exc
    if len(decoded) != expected_bytes:
        raise ReleaseSignatureError(f"{label} doit contenir exactement {expected_bytes} octets.")
    return decoded


def load_public_key(path: str | Path | None = None) -> bytes:
    """Load the pinned raw Ed25519 public key (Base64) shipped with MaClasse."""
    key_path = Path(path) if path is not None else PUBLIC_KEY_FILE
    try:
        lines = key_path.read_text(encoding="ascii").splitlines()
    except OSError as exc:
        raise ReleaseSignatureError("Clé publique de confiance introuvable.") from exc
    encoded = "".join(line.split("#", 1)[0].strip() for line in lines)
    if not encoded.strip():
        raise ReleaseSignatureError(
            "Clé publique de confiance non configurée. La vérification des mises à jour est bloquée."
        )
    return _decode_b64(encoded, "Clé publique Ed25519", PUBLIC_KEY_BYTES)


def verify_manifest_signature(manifest_payload: bytes, signature_payload: bytes,
                              public_key: bytes | None = None) -> bool:
    """Verify a detached Base64 Ed25519 signature over the exact manifest bytes."""
    if not isinstance(manifest_payload, bytes) or not manifest_payload:
        raise ReleaseSignatureError("Contenu du manifeste absent.")
    if not isinstance(signature_payload, bytes) or len(signature_payload) > 16 * 1024:
        raise ReleaseSignatureError("Fichier de signature absent ou trop volumineux.")
    try:
        signature_text = signature_payload.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ReleaseSignatureError("La signature de release n'est pas un texte Base64.") from exc
    signature = _decode_b64(signature_text, "Signature Ed25519", SIGNATURE_BYTES)
    trusted_key = public_key if public_key is not None else load_public_key()
    if not isinstance(trusted_key, bytes) or len(trusted_key) != PUBLIC_KEY_BYTES:
        raise ReleaseSignatureError("Clé publique Ed25519 invalide.")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise ReleaseSignatureError(
            "La dépendance cryptographique cryptography est absente ; mise à jour refusée."
        ) from exc
    try:
        Ed25519PublicKey.from_public_bytes(trusted_key).verify(signature, manifest_payload)
    except InvalidSignature as exc:
        raise ReleaseSignatureError(
            "La signature du manifeste ne correspond pas à la clé éditeur de confiance."
        ) from exc
    except (TypeError, ValueError) as exc:
        raise ReleaseSignatureError("Clé publique ou signature Ed25519 invalide.") from exc
    return True


def sign_manifest(manifest_payload: bytes, private_key_b64: str) -> str:
    """Sign exact manifest bytes and refuse a private key that differs from the pinned key."""
    if not isinstance(manifest_payload, bytes) or not manifest_payload:
        raise ReleaseSignatureError("Contenu du manifeste absent.")
    private_raw = _decode_b64(private_key_b64, "Clé privée Ed25519", PUBLIC_KEY_BYTES)
    trusted_key = load_public_key()
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:
        raise ReleaseSignatureError(
            "La dépendance cryptographique cryptography est absente."
        ) from exc
    try:
        private_key = Ed25519PrivateKey.from_private_bytes(private_raw)
        derived_public = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    except (TypeError, ValueError) as exc:
        raise ReleaseSignatureError("Clé privée Ed25519 invalide.") from exc
    if not hmac.compare_digest(derived_public, trusted_key):
        raise ReleaseSignatureError(
            "La clé privée GitHub Actions ne correspond pas à la clé publique versionnée."
        )
    return base64.b64encode(private_key.sign(manifest_payload)).decode("ascii")
