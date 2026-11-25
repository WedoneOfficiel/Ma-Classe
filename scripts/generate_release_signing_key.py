#!/usr/bin/env python3
"""Generate a local Ed25519 release-signing key pair for MaClasse."""
from __future__ import annotations

import base64
import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE = Path.home() / ".config" / "maclasse" / "release-signing-private-key.b64"
DEFAULT_PUBLIC = ROOT / "release-signing-public-key.txt"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Générer une clé Ed25519. La clé privée ne doit jamais entrer dans Git."
    )
    parser.add_argument("--private-out", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument("--public-out", type=Path, default=DEFAULT_PUBLIC)
    parser.add_argument("--force", action="store_true", help="Remplacer les fichiers de clé existants.")
    args = parser.parse_args()

    private_out = args.private_out.expanduser().resolve()
    public_out = args.public_out.expanduser().resolve()
    if ROOT == private_out or ROOT in private_out.parents:
        parser.error("La clé privée doit être enregistrée hors du dépôt Git.")
    if not args.force and (private_out.exists() or public_out.exists()):
        parser.error("Un fichier de clé existe déjà ; choisir d'autres chemins ou utiliser --force.")

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        print("Dépendance manquante : exécuter python -m pip install -r requirements.txt", file=sys.stderr)
        return 2

    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    private_out.parent.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "posix":
            private_out.parent.chmod(0o700)
        private_out.write_text(base64.b64encode(private_raw).decode("ascii") + "\n", encoding="ascii")
        if os.name == "posix":
            private_out.chmod(0o600)
        public_out.parent.mkdir(parents=True, exist_ok=True)
        public_out.write_text(base64.b64encode(public_raw).decode("ascii") + "\n", encoding="ascii")
        if os.name == "posix":
            public_out.chmod(0o644)
    except OSError as exc:
        print(f"Impossible d'écrire les fichiers de clé : {exc}", file=sys.stderr)
        try:
            private_out.unlink(missing_ok=True)
        except OSError:
            pass
        return 1

    print("Clé Ed25519 générée.")
    print(f"Clé privée (à conserver hors du dépôt) : {private_out}")
    print(f"Clé publique (à committer) : {public_out}")
    print("Créer le secret GitHub Actions MACLASSE_RELEASE_SIGNING_KEY_B64 avec le contenu du fichier privé.")
    print("Ne jamais committer, envoyer ou joindre le fichier de clé privée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
