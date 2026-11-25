#!/usr/bin/env python3
"""Create the detached Ed25519 signature asset for a MaClasse GitHub Release."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import release_signing


def main() -> int:
    parser = argparse.ArgumentParser(description="Signer le manifeste de release MaClasse.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    args = parser.parse_args()
    secret = os.environ.get("MACLASSE_RELEASE_SIGNING_KEY_B64", "")
    if not secret.strip():
        print(
            "Secret GitHub Actions absent : configurer MACLASSE_RELEASE_SIGNING_KEY_B64.",
            file=sys.stderr,
        )
        return 2
    try:
        payload = args.manifest.read_bytes()
        encoded_signature = release_signing.sign_manifest(payload, secret)
        args.signature.parent.mkdir(parents=True, exist_ok=True)
        args.signature.write_text(encoded_signature, encoding="ascii")
        if os.name == "posix":
            args.signature.chmod(0o644)
    except (OSError, release_signing.ReleaseSignatureError) as exc:
        print(f"Signature de release impossible : {exc}", file=sys.stderr)
        return 1
    print("Manifeste signé Ed25519 ; clé privée non affichée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
