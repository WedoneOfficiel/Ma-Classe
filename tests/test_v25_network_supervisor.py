#!/usr/bin/env python3
"""Network rebinding and certificate lifecycle tests for MaClasse V25."""
import os
import signal
import subprocess
import sys
import tempfile
import unittest
import ipaddress
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509.oid import NameOID
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import network_supervisor as supervisor


def write_test_certificate(
    path: Path,
    san_ips: list[str] | None = None,
    *,
    san_dns: list[str] | None = None,
    private_key_path: Path | None = None,
    not_valid_before: datetime | None = None,
    not_valid_after: datetime | None = None,
) -> None:
    """Write a real PEM certificate to exercise X.509 parsing end to end."""
    now = datetime.now(timezone.utc)
    before = (not_valid_before or now - timedelta(days=1)).replace(tzinfo=None)
    after = (not_valid_after or now + timedelta(days=30)).replace(tzinfo=None)
    key = ed25519.Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "MaClasse test")])
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(before)
        .not_valid_after(after)
    )
    names = []
    if san_ips is not None:
        names.extend(x509.IPAddress(ipaddress.ip_address(value)) for value in san_ips)
    if san_dns is not None:
        names.extend(x509.DNSName(value) for value in san_dns)
    if names:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(names),
            critical=False,
        )
    certificate = builder.sign(key, algorithm=None)
    path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    if private_key_path is not None:
        private_key_path.write_bytes(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
        private_key_path.chmod(0o600)


class FakeProcess:
    def __init__(self, command, **kwargs):
        self.command = command
        self.kwargs = kwargs
        self.returncode = None
        self.signals = []

    def poll(self):
        return self.returncode

    def send_signal(self, value):
        self.signals.append(value)

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def kill(self):
        self.returncode = -9


class StopAfter:
    def __init__(self, count):
        self.count = count
        self.calls = 0

    def is_set(self):
        return self.calls >= self.count

    def wait(self, seconds):
        self.calls += 1
        return self.is_set()


class NetworkSupervisorTests(unittest.TestCase):
    def test_linux_detects_address_on_default_route_interface(self):
        def runner(command, **kwargs):
            if command == ["ip", "-4", "route", "show", "default"]:
                return SimpleNamespace(returncode=0, stdout="default via 192.168.1.1 dev wlp2s0 proto dhcp\n")
            if command[0:7] == ["ip", "-4", "-o", "addr", "show", "dev", "wlp2s0"]:
                return SimpleNamespace(returncode=0, stdout="3: wlp2s0 inet 192.168.1.42/24 brd 192.168.1.255 scope global dynamic\n")
            raise AssertionError(command)

        self.assertEqual(supervisor.detect_lan_ipv4("linux", runner), "192.168.1.42")

    def test_macos_detects_address_on_default_route_interface(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            if command == ["/sbin/route", "-n", "get", "default"]:
                return SimpleNamespace(returncode=0, stdout="route to: default\ngateway: 192.168.1.1\ninterface: en0\n")
            if command == ["/usr/sbin/ipconfig", "getifaddr", "en0"]:
                return SimpleNamespace(returncode=0, stdout="192.168.1.50\n")
            raise AssertionError(command)

        self.assertEqual(supervisor.detect_lan_ipv4("darwin", runner), "192.168.1.50")
        self.assertEqual(len(calls), 2)

    def test_public_or_missing_addresses_are_rejected(self):
        self.assertIsNone(supervisor._usable_private_ipv4("8.8.8.8"))
        self.assertIsNone(supervisor._usable_private_ipv4("169.254.2.3"))
        self.assertIsNone(supervisor._usable_private_ipv4("0.0.0.0"))
        self.assertIsNone(supervisor._usable_private_ipv4("not-an-ip"))
        self.assertEqual(supervisor._usable_private_ipv4("10.1.2.3"), "10.1.2.3")

    def test_certificate_requires_matching_ip_san_and_more_than_24h_validity(self):
        with tempfile.TemporaryDirectory() as temp:
            cert = Path(temp) / "server.crt"
            write_test_certificate(cert, ["192.168.1.42"])
            self.assertTrue(supervisor.certificate_matches_host(cert, "192.168.1.42"))
            self.assertFalse(supervisor.certificate_matches_host(cert, "192.168.1.43"))

            write_test_certificate(
                cert,
                ["192.168.1.42"],
                not_valid_after=datetime.now(timezone.utc) + timedelta(hours=12),
            )
            self.assertFalse(supervisor.certificate_matches_host(cert, "192.168.1.42"))

            write_test_certificate(
                cert,
                ["192.168.1.42"],
                not_valid_before=datetime.now(timezone.utc) + timedelta(days=1),
            )
            self.assertFalse(supervisor.certificate_matches_host(cert, "192.168.1.42"))

            write_test_certificate(cert, None)
            self.assertFalse(supervisor.certificate_matches_host(cert, "192.168.1.42"))


    def test_public_dns_certificate_requires_matching_dns_san(self):
        with tempfile.TemporaryDirectory() as temp:
            cert = Path(temp) / "fullchain.pem"
            key = Path(temp) / "privkey.pem"
            write_test_certificate(
                cert, san_dns=["maclasse.example.test"], private_key_path=key
            )
            self.assertTrue(supervisor.certificate_matches_host(
                cert, "maclasse.example.test"
            ))
            self.assertFalse(supervisor.certificate_matches_host(
                cert, "other.example.test"
            ))
            self.assertFalse(supervisor.certificate_matches_host(
                cert, "192.168.1.42"
            ))

    def test_public_certificate_config_checks_permissions_hostname_and_key_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            tls = data / "tls"
            tls.mkdir()
            cert = tls / "fullchain.pem"
            key = tls / "privkey.pem"
            write_test_certificate(
                cert, san_dns=["maclasse.example.test"], private_key_path=key
            )
            config = tls / "public-certificate.json"
            config.write_text(json.dumps({
                "hostname": "maclasse.example.test",
                "certificate": str(cert),
                "private_key": str(key),
            }), encoding="utf-8")
            config.chmod(0o600)
            loaded = supervisor.load_public_certificate_config(data)
            self.assertEqual(loaded["hostname"], "maclasse.example.test")
            self.assertEqual(loaded["certificate"], cert.resolve())
            self.assertEqual(loaded["private_key"], key.resolve())
            self.assertEqual(len(loaded["fingerprint"]), 64)

            config.chmod(0o644)
            with self.assertRaises(RuntimeError):
                supervisor.load_public_certificate_config(data)

    def test_public_certificate_config_rejects_mismatched_private_key(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            tls = data / "tls"
            tls.mkdir()
            cert = tls / "fullchain.pem"
            key = tls / "privkey.pem"
            wrong_key = tls / "wrong-key.pem"
            write_test_certificate(
                cert, san_dns=["maclasse.example.test"], private_key_path=key
            )
            other_cert = tls / "other.pem"
            write_test_certificate(
                other_cert, san_dns=["other.example.test"], private_key_path=wrong_key
            )
            config = tls / "public-certificate.json"
            config.write_text(json.dumps({
                "hostname": "maclasse.example.test",
                "certificate": str(cert),
                "private_key": str(wrong_key),
            }), encoding="utf-8")
            config.chmod(0o600)
            with self.assertRaisesRegex(RuntimeError, "ne correspondent pas"):
                supervisor.load_public_certificate_config(data)

    def test_public_certificate_mode_passes_dns_identity_without_generating_local_ca(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "root"
            app = Path(temp) / "app"
            data = Path(temp) / "data"
            root.mkdir()
            app.mkdir()
            tls = data / "tls"
            tls.mkdir(parents=True)
            cert = tls / "fullchain.pem"
            key = tls / "privkey.pem"
            write_test_certificate(
                cert, san_dns=["maclasse.example.test"], private_key_path=key
            )
            config = tls / "public-certificate.json"
            config.write_text(json.dumps({
                "hostname": "maclasse.example.test",
                "certificate": str(cert),
                "private_key": str(key),
            }), encoding="utf-8")
            config.chmod(0o600)
            processes = []

            def spawn(command, **kwargs):
                process = FakeProcess(command, **kwargs)
                processes.append(process)
                return process

            def unexpected_local_ca(_host):
                raise AssertionError("Le mode TLS public ne doit pas générer d'AC privée.")

            result = supervisor.run_supervisor(
                root, app, data, "/usr/bin/python3",
                stop_event=StopAfter(1),
                detect_ip=lambda: "192.168.1.24",
                ensure_cert=unexpected_local_ca,
                spawn=spawn,
            )
            self.assertEqual(result, 0)
            self.assertEqual(len(processes), 1)
            child_env = processes[0].kwargs["env"]
            self.assertEqual(child_env["MACLASSE_TLS_HOSTNAME"], "maclasse.example.test")
            self.assertEqual(child_env["MACLASSE_TLS_CERT"], str(cert.resolve()))
            self.assertEqual(child_env["MACLASSE_TLS_KEY"], str(key.resolve()))
            self.assertEqual(child_env["MACLASSE_HOST"], "192.168.1.24")
            self.assertEqual(processes[0].signals, [signal.SIGTERM])

    def test_rebind_stops_old_listener_before_starting_new_address(self):
        processes = []
        ensured = []
        hosts = iter(["192.168.1.10", "192.168.1.10", "192.168.1.20"])
        def spawn(command, **kwargs):
            process = FakeProcess(command, **kwargs)
            processes.append(process)
            return process

        event = StopAfter(3)
        result = supervisor.run_supervisor(
            "/tmp/maclasse-root", "/tmp/maclasse-app", "/tmp/maclasse-data", "/usr/bin/python3",
            stop_event=event,
            detect_ip=lambda: next(hosts),
            ensure_cert=ensured.append,
            cert_valid=lambda cert, host: True,
            spawn=spawn,
        )
        self.assertEqual(result, 0)
        self.assertEqual(ensured, ["192.168.1.10", "192.168.1.20"])
        self.assertEqual(len(processes), 2)
        self.assertIn("192.168.1.10", processes[0].kwargs["env"]["MACLASSE_HOST"])
        self.assertIn("192.168.1.20", processes[1].kwargs["env"]["MACLASSE_HOST"])
        self.assertEqual(processes[0].signals, [signal.SIGTERM])
        self.assertEqual(processes[1].signals, [signal.SIGTERM])

    def test_network_loss_stops_listener_and_network_return_restarts_it(self):
        processes = []
        hosts = iter(["192.168.1.10", None, "192.168.1.20"])
        def spawn(command, **kwargs):
            process = FakeProcess(command, **kwargs)
            processes.append(process)
            return process

        result = supervisor.run_supervisor(
            "/tmp/maclasse-root", "/tmp/maclasse-app", "/tmp/maclasse-data", "/usr/bin/python3",
            stop_event=StopAfter(3),
            detect_ip=lambda: next(hosts),
            ensure_cert=lambda host: None,
            cert_valid=lambda cert, host: True,
            spawn=spawn,
        )
        self.assertEqual(result, 0)
        self.assertEqual(len(processes), 2)
        self.assertEqual(processes[0].signals, [signal.SIGTERM])
        self.assertEqual(processes[1].signals, [signal.SIGTERM])

    def test_certificate_configuration_uses_persistent_data_directory(self):
        calls = []
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "persistent-data"
            data.mkdir()
            (root / "Configurer-MaClasse-Reseau.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            cert_dir = data / "tls"
            cert_dir.mkdir()
            def runner(command, **kwargs):
                calls.append((command, kwargs))
                if command[0] == "/bin/bash":
                    write_test_certificate(cert_dir / "server.crt", ["10.0.0.5"])
                    return SimpleNamespace(returncode=0, stdout="")
                if "-ext" in command:
                    return SimpleNamespace(returncode=0, stdout="X509v3 Subject Alternative Name: IP Address:10.0.0.5\n")
                if "-checkend" in command:
                    return SimpleNamespace(returncode=0, stdout="")
                raise AssertionError(command)
            supervisor.ensure_certificate(root, data, "/usr/bin/python3", "10.0.0.5", runner)
            config_call = calls[0]
            self.assertEqual(config_call[0][-1], "10.0.0.5")
            self.assertEqual(config_call[1]["env"]["MACLASSE_DATA_DIR"], str(data.resolve()))
            self.assertEqual(config_call[1]["cwd"], str(root.resolve()))

    def test_unexpected_server_exit_is_reported_to_service_manager(self):
        class DeadProcess(FakeProcess):
            def __init__(self, command, **kwargs):
                super().__init__(command, **kwargs)
                self.returncode = 7

        result = supervisor.run_supervisor(
            "/tmp/root", "/tmp/app", "/tmp/data", "/usr/bin/python3",
            stop_event=StopAfter(2),
            detect_ip=lambda: "192.168.1.10",
            ensure_cert=lambda host: None,
            spawn=lambda command, **kwargs: DeadProcess(command, **kwargs),
        )
        self.assertEqual(result, 7)


    def test_certificate_script_is_loaded_from_active_version_not_install_root(self):
        processes = []
        def spawn(command, **kwargs):
            process = FakeProcess(command, **kwargs)
            processes.append(process)
            return process

        with patch.object(supervisor, "ensure_certificate") as ensure:
            result = supervisor.run_supervisor(
                "/installation-root",
                "/installation-root/data/program/versions/V25.1.0",
                "/installation-root/data",
                "/installation-root/data/program/versions/V25.1.0/.venv/bin/python",
                stop_event=StopAfter(2),
                detect_ip=lambda: "192.168.1.60",
                cert_valid=lambda cert, host: True,
                spawn=spawn,
            )
        self.assertEqual(result, 0)
        ensure.assert_called_once_with(
            Path("/installation-root/data/program/versions/V25.1.0"),
            Path("/installation-root/data"),
            "/installation-root/data/program/versions/V25.1.0/.venv/bin/python",
            "192.168.1.60",
        )


if __name__ == "__main__":
    unittest.main()
