#!/usr/bin/env python3
"""Network rebinding and certificate lifecycle tests for MaClasse V25."""
import os
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import network_supervisor as supervisor


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
        def runner(command, **kwargs):
            if "-ext" in command:
                return SimpleNamespace(returncode=0, stdout="X509v3 Subject Alternative Name: IP Address:192.168.1.42\n")
            if "-checkend" in command:
                return SimpleNamespace(returncode=0, stdout="")
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as temp:
            cert = Path(temp) / "server.crt"
            cert.write_text("fixture", encoding="utf-8")
            self.assertTrue(supervisor.certificate_matches_host(cert, "192.168.1.42", runner, "/usr/bin/openssl"))
            self.assertFalse(supervisor.certificate_matches_host(cert, "192.168.1.43", runner, "/usr/bin/openssl"))

            def expiring(command, **kwargs):
                if "-ext" in command:
                    return SimpleNamespace(returncode=0, stdout="X509v3 Subject Alternative Name: IP Address:192.168.1.42\n")
                return SimpleNamespace(returncode=1, stdout="")
            self.assertFalse(supervisor.certificate_matches_host(cert, "192.168.1.42", expiring, "/usr/bin/openssl"))

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
                    (cert_dir / "server.crt").write_text("configured", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
