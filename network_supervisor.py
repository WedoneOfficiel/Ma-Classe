#!/usr/bin/env python3
"""Supervise MaClasse's LAN listener and rebind it safely after DHCP changes.

The trusted local CA and server private key remain in the persistent data
folder. Only the leaf certificate and HTTPS listener are renewed/restarted
when the selected private IPv4 address changes.
"""
from __future__ import annotations

import ipaddress
from cryptography.hazmat.primitives import serialization
import ssl
import stat
import json
import hmac
import hashlib
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from cryptography import x509


def _command_output(command: list[str], runner: Callable = subprocess.run) -> str:
    try:
        result = runner(
            command, check=False, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if getattr(result, "returncode", 1) != 0:
        return ""
    return (getattr(result, "stdout", "") or "").strip()


def _usable_private_ipv4(value: str) -> str | None:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return None
    if not (
        isinstance(address, ipaddress.IPv4Address)
        and address.is_private
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_unspecified
    ):
        return None
    return str(address)


def detect_lan_ipv4(
    platform_name: str | None = None, runner: Callable = subprocess.run
) -> str | None:
    """Return the IPv4 on the default-route interface, or None while offline."""
    platform_name = platform_name or sys.platform
    if platform_name == "darwin":
        route = _command_output(
            ["/sbin/route", "-n", "get", "default"], runner
        )
        match = re.search(r"(?m)^\s*interface:\s*(\S+)\s*$", route)
        if not match:
            return None
        address = _command_output(
            ["/usr/sbin/ipconfig", "getifaddr", match.group(1)], runner
        )
        return _usable_private_ipv4(address)

    if platform_name.startswith("linux"):
        route = _command_output(
            ["ip", "-4", "route", "show", "default"], runner
        )
        match = re.search(r"(?:^|\s)dev\s+(\S+)", route)
        if not match:
            return None
        addresses = _command_output(
            [
                "ip", "-4", "-o", "addr", "show", "dev",
                match.group(1), "scope", "global",
            ],
            runner,
        )
        for address in re.findall(r"\binet\s+([0-9.]+)/\d+", addresses):
            valid = _usable_private_ipv4(address)
            if valid:
                return valid
    return None


def _normalise_dns_hostname(value: str) -> str | None:
    """Normalise an exact DNS hostname; IP literals are deliberately rejected."""
    if not isinstance(value, str):
        return None
    try:
        hostname = value.strip().rstrip(".").encode("idna").decode("ascii").lower()
        ipaddress.ip_address(hostname)
        return None
    except ValueError:
        pass
    except UnicodeError:
        return None
    if not hostname or len(hostname) > 253:
        return None
    labels = hostname.split(".")
    if len(labels) < 2:
        return None
    if any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in labels
    ):
        return None
    return hostname


def certificate_matches_host(certificate: Path | str, host: str) -> bool:
    """Validate an IPv4 or DNS SAN and more than 24 hours of certificate validity."""
    certificate = Path(certificate)
    try:
        parsed = x509.load_pem_x509_certificate(certificate.read_bytes())
        san = parsed.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value
        try:
            expected_ip = ipaddress.ip_address(host)
        except ValueError:
            expected_dns = _normalise_dns_hostname(host)
            if not expected_dns:
                return False
            matches = False
            for candidate in san.get_values_for_type(x509.DNSName):
                if candidate.startswith("*."):
                    suffix = _normalise_dns_hostname(candidate[2:])
                    labels = expected_dns.split(".")
                    if (
                        suffix
                        and len(labels) == len(suffix.split(".")) + 1
                        and ".".join(labels[1:]) == suffix
                    ):
                        matches = True
                        break
                    continue
                name = _normalise_dns_hostname(candidate)
                if name == expected_dns:
                    matches = True
                    break
            if not matches:
                return False
        else:
            if not isinstance(expected_ip, ipaddress.IPv4Address):
                return False
            if expected_ip not in san.get_values_for_type(x509.IPAddress):
                return False

        now = datetime.now(timezone.utc)
        return (
            parsed.not_valid_before_utc <= now
            and parsed.not_valid_after_utc > now + timedelta(hours=24)
        )
    except (OSError, ValueError, TypeError, UnicodeError, x509.ExtensionNotFound):
        return False


def load_public_certificate_config(data_dir: Path | str) -> dict | None:
    """Load an optional public-CA certificate configuration from persistent data.

    data/tls/public-certificate.json contains only a DNS name and absolute
    certificate/key paths. ACME credentials are not read or stored by MaClasse.
    """
    config_path = Path(data_dir) / "tls" / "public-certificate.json"
    if config_path.is_symlink():
        raise RuntimeError("La configuration TLS publique ne peut pas être un lien symbolique.")
    if not config_path.exists():
        return None
    try:
        config_stat = config_path.stat()
        if not config_path.is_file():
            raise RuntimeError("La configuration TLS publique doit être un fichier normal.")
        if os.name == "posix" and config_stat.st_mode & 0o077:
            raise RuntimeError("La configuration TLS publique doit être protégée (chmod 600).")
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("La configuration TLS publique est illisible.") from error
    if not isinstance(payload, dict) or set(payload) != {"hostname", "certificate", "private_key"}:
        raise RuntimeError("La configuration doit contenir exactement hostname, certificate et private_key.")

    hostname = _normalise_dns_hostname(payload.get("hostname"))
    if not hostname:
        raise RuntimeError("Le nom DNS du certificat public n'est pas un FQDN valide.")

    paths = {}
    for field in ("certificate", "private_key"):
        raw = payload.get(field)
        if not isinstance(raw, str) or not raw.strip():
            raise RuntimeError(f"Chemin {field} absent dans la configuration TLS publique.")
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            raise RuntimeError(f"Le chemin {field} doit être absolu.")
        try:
            resolved = candidate.resolve(strict=True)
            file_stat = resolved.stat()
        except OSError as error:
            raise RuntimeError(f"Le fichier TLS {field} est introuvable ou inaccessible.") from error
        if not resolved.is_file():
            raise RuntimeError(f"Le fichier TLS {field} doit être un fichier normal.")
        if field == "private_key" and os.name == "posix" and file_stat.st_mode & 0o077:
            raise RuntimeError("La clé privée TLS doit être lisible uniquement par le compte de service.")
        paths[field] = resolved

    if not certificate_matches_host(paths["certificate"], hostname):
        raise RuntimeError("Le certificat public ne couvre pas le nom DNS ou expire dans moins de 24 heures.")
    try:
        certificate = x509.load_pem_x509_certificate(paths["certificate"].read_bytes())
        private_key = serialization.load_pem_private_key(
            paths["private_key"].read_bytes(), password=None
        )
        cert_public = certificate.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_public = private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    except (OSError, ValueError, TypeError) as error:
        raise RuntimeError("Le certificat ou la clé privée TLS ne peut pas être lu.") from error
    if not hmac.compare_digest(cert_public, key_public):
        raise RuntimeError("Le certificat public et la clé privée TLS ne correspondent pas.")

    fingerprint = hashlib.sha256(
        str(paths["certificate"]).encode("utf-8")
        + b"\0"
        + paths["certificate"].read_bytes()
        + b"\0"
        + str(paths["private_key"]).encode("utf-8")
        + b"\0"
        + paths["private_key"].read_bytes()
    ).hexdigest()
    return {
        "hostname": hostname,
        "certificate": paths["certificate"],
        "private_key": paths["private_key"],
        "fingerprint": fingerprint,
    }


def ensure_certificate(
    root: Path | str,
    data_dir: Path | str,
    python: Path | str,
    host: str,
    runner: Callable = subprocess.run,
) -> None:
    """Create/renew only the server certificate, preserving the local CA."""
    root = Path(root).resolve()
    data_dir = Path(data_dir).resolve()
    certificate = data_dir / "tls" / "server.crt"
    if certificate_matches_host(certificate, host):
        return
    configurer = root / "Configurer-MaClasse-Reseau.sh"
    if not configurer.is_file():
        raise RuntimeError(f"Script de configuration HTTPS introuvable : {configurer}")
    environment = os.environ.copy()
    environment["PYTHON"] = str(python)
    environment["MACLASSE_DATA_DIR"] = str(data_dir)
    try:
        runner(
            ["/bin/bash", str(configurer), host],
            cwd=str(root), env=environment, check=True, timeout=120,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(
            f"Impossible de renouveler le certificat HTTPS pour {host}."
        ) from error
    if not certificate_matches_host(certificate, host):
        raise RuntimeError(
            f"Le certificat HTTPS généré ne couvre pas la nouvelle adresse {host}."
        )


def _stop_server(process: subprocess.Popen, timeout: int = 105) -> None:
    """Ask the HTTP server to drain in-flight requests before closing its socket."""
    if process.poll() is not None:
        return
    try:
        process.send_signal(signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def run_supervisor(
    root: Path | str,
    app_root: Path | str,
    data_dir: Path | str,
    python: Path | str,
    *,
    port: int = 8765,
    poll_seconds: float = 5,
    stop_event: threading.Event | None = None,
    detect_ip: Callable[[], str | None] | None = None,
    ensure_cert: Callable[[str], None] | None = None,
    cert_valid: Callable[[Path, str], bool] | None = None,
    spawn: Callable = subprocess.Popen,
) -> int:
    """Keep the HTTPS server attached to its LAN address and selected TLS identity.

    The default private-CA mode is unchanged. An optional
    data/tls/public-certificate.json switches to an externally renewed,
    publicly trusted DNS certificate. The ACME client is managed separately;
    this supervisor only validates and reloads the issued files.
    """
    root = Path(root).resolve()
    app_root = Path(app_root).resolve()
    data_dir = Path(data_dir).resolve()
    python = str(python)
    stop_event = stop_event or threading.Event()
    detect_ip = detect_ip or detect_lan_ipv4
    local_cert_path = data_dir / "tls" / "server.crt"
    local_key_path = data_dir / "tls" / "server.key"
    # The helper script must come from the active application version, not
    # the immutable installation root. This matters after atomic version swaps.
    ensure_cert = ensure_cert or (
        lambda host: ensure_certificate(app_root, data_dir, python, host)
    )
    cert_valid = cert_valid or certificate_matches_host

    process = None
    active_host = None
    active_tls_hostname = None
    active_tls_fingerprint = None
    last_offline_log = 0.0
    last_tls_config_error_log = 0.0
    try:
        while not stop_event.is_set():
            if process is not None and process.poll() is not None:
                code = process.returncode
                print(
                    f"Le serveur MaClasse s'est arrêté inopinément "
                    f"(code {code}) ; le superviseur transmet l'échec au service.",
                    file=sys.stderr, flush=True,
                )
                return code if isinstance(code, int) and code != 0 else 1

            try:
                public_config = load_public_certificate_config(data_dir)
            except RuntimeError as error:
                if process is None:
                    raise
                # During ACME deployment, fullchain and private key may be
                # atomically replaced one after the other. Keep the last
                # already-running TLS listener and retry on the next poll;
                # never stop it or start with a mismatched pair.
                now = time.monotonic()
                if now - last_tls_config_error_log >= 60:
                    print(
                        f"Configuration TLS publique temporairement invalide ; "
                        f"le listener courant est conservé et un nouvel essai sera effectué : {error}",
                        file=sys.stderr, flush=True,
                    )
                    last_tls_config_error_log = now
                if stop_event.wait(poll_seconds):
                    break
                continue
            if public_config:
                cert_path = public_config["certificate"]
                key_path = public_config["private_key"]
                certificate_identity = public_config["hostname"]
                tls_hostname = public_config["hostname"]
                tls_fingerprint = public_config["fingerprint"]
            else:
                cert_path = local_cert_path
                key_path = local_key_path
                certificate_identity = None
                tls_hostname = ""
                tls_fingerprint = None

            host = detect_ip()
            if host is None:
                if process is not None:
                    print(
                        "Réseau privé indisponible : arrêt propre du listener HTTPS "
                        "jusqu'au retour d'une adresse IPv4.",
                        flush=True,
                    )
                    _stop_server(process)
                    process = None
                    active_host = None
                    active_tls_hostname = None
                    active_tls_fingerprint = None
                now = time.monotonic()
                if now - last_offline_log >= 60:
                    print(
                        "En attente d'une adresse IPv4 privée sur l'interface par défaut…",
                        flush=True,
                    )
                    last_offline_log = now
            else:
                identity = certificate_identity or host
                valid_certificate = (
                    cert_valid(cert_path, identity) if process is not None else False
                )
                tls_configuration_changed = (
                    tls_hostname != active_tls_hostname
                    or tls_fingerprint != active_tls_fingerprint
                )
                if (
                    process is None
                    or host != active_host
                    or not valid_certificate
                    or tls_configuration_changed
                ):
                    if process is not None:
                        if tls_configuration_changed:
                            reason = "changement de configuration/certificat TLS"
                        elif host != active_host:
                            reason = "changement d'adresse IP"
                        else:
                            reason = "renouvellement du certificat"
                        print(f"{reason.capitalize()} : arrêt propre du serveur…", flush=True)
                        _stop_server(process)
                        process = None
                    if public_config:
                        if not cert_valid(cert_path, certificate_identity):
                            raise RuntimeError("Le certificat TLS public n'est pas valide pour le nom DNS configuré.")
                    else:
                        ensure_cert(host)
                    child_env = os.environ.copy()
                    child_env.update({
                        "MACLASSE_ROOT": str(root),
                        "MACLASSE_APP_ROOT": str(app_root),
                        "MACLASSE_DATA_DIR": str(data_dir),
                        "MACLASSE_LAN_MODE": "1",
                        "MACLASSE_HOST": host,
                        "MACLASSE_PORT": str(port),
                        "MACLASSE_TLS_CERT": str(cert_path),
                        "MACLASSE_TLS_KEY": str(key_path),
                        "MACLASSE_TLS_HOSTNAME": tls_hostname,
                    })
                    process = spawn(
                        [python, "-u", str(app_root / "server.py")],
                        cwd=str(app_root),
                        env=child_env,
                    )
                    active_host = host
                    active_tls_hostname = tls_hostname
                    active_tls_fingerprint = tls_fingerprint
                    advertised_host = tls_hostname or host
                    print(
                        f"MaClasse HTTPS actif sur https://{advertised_host}:{port} "
                        f"(bind privé {host}, surveillance réseau toutes les {poll_seconds:g} s).",
                        flush=True,
                    )

            if stop_event.wait(poll_seconds):
                break
    finally:
        if process is not None:
            print("Arrêt du superviseur : fermeture propre du serveur MaClasse…", flush=True)
            _stop_server(process)
    return 0


def main() -> int:
    root = Path(os.environ.get("MACLASSE_ROOT") or Path(__file__).resolve().parent)
    app_root = Path(os.environ.get("MACLASSE_APP_ROOT") or Path(__file__).resolve().parent)
    data_dir = Path(os.environ.get("MACLASSE_DATA_DIR") or root / "data")
    python = Path(os.environ.get("MACLASSE_PYTHON") or app_root / ".venv" / "bin" / "python")
    try:
        port = int(os.environ.get("MACLASSE_PORT", "8765"))
        poll_seconds = float(os.environ.get("MACLASSE_NETWORK_POLL_SECONDS", "5"))
    except ValueError:
        raise SystemExit("Port ou intervalle de surveillance réseau invalide.")
    if not 1 <= port <= 65535 or not 2 <= poll_seconds <= 60:
        raise SystemExit("Port ou intervalle de surveillance réseau hors limites.")

    stop_event = threading.Event()

    def request_stop(_signum, _frame):
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    return run_supervisor(
        root, app_root, data_dir, python,
        port=port, poll_seconds=poll_seconds, stop_event=stop_event,
    )


if __name__ == "__main__":
    raise SystemExit(main())
