#!/usr/bin/env python3
"""Static safety checks for the macOS launchd update supervisor."""
import json
import os
import plistlib
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "Installer-Service-MaClasse-macOS.sh",
    "Lancer-MaClasse-Service-macOS.sh",
    "Appliquer-Mise-A-Jour-MaClasse-macOS.sh",
    "Lancer-MaClasse.command",
    "Lancer-MaClasse-Reseau.command",
)

class MacOSSupervisorTests(unittest.TestCase):
    def test_launchd_scripts_have_valid_bash_syntax(self):
        for name in SCRIPTS:
            with self.subTest(script=name):
                subprocess.run(["bash", "-n", str(ROOT / name)], check=True)

    def test_manual_launchers_never_start_a_second_server_when_launchd_is_loaded(self):
        for name in SCRIPTS[3:]:
            with self.subTest(script=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                guard = source.index('launchctl print "gui/$(id -u)/fr.maclasse.server"')
                starts = [
                    source.find(".venv/bin/python server.py"),
                    source.find("network_supervisor.py"),
                ]
                start = min(position for position in starts if position >= 0)
                self.assertLess(guard, start)
                self.assertIn("partagerait la même base de données", source)

    def test_service_is_user_scoped_and_keeps_data_outside_versions(self):
        installer = (ROOT / SCRIPTS[0]).read_text(encoding="utf-8")
        runner = (ROOT / SCRIPTS[1]).read_text(encoding="utf-8")
        self.assertIn("gui/$(id -u)", installer)
        self.assertIn("fr.maclasse.server", installer)
        self.assertIn("KeepAlive", installer)
        self.assertIn('MACLASSE_ROOT="$ROOT"', runner)
        self.assertIn('MACLASSE_DATA_DIR="$DATA"', runner)
        self.assertIn('SCRIPT_DIR/../../../..', runner)
        self.assertIn('MACLASSE_APP_ROOT="$PROGRAM"', runner)
        self.assertIn('MACLASSE_SUPERVISED=launchd', runner)
        self.assertIn("network_supervisor.py", runner)



    @unittest.skipUnless(__import__("sys").platform == "darwin", "L'installateur launchd ne peut être exécuté que sur macOS.")
    def test_service_installer_builds_and_loads_user_agent(self):
        import os
        import shutil
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="maclasse-launchd-installer-"))
        root = tmp / "MaClasse"
        (root / ".venv" / "bin").mkdir(parents=True)
        (root / "data" / "tls").mkdir(parents=True)
        (root / ".venv" / "bin" / "python").symlink_to(__import__("sys").executable)
        for name in SCRIPTS:
            shutil.copy2(ROOT / name, root / name)
        for name in ("server.crt", "server.key", "ca.crt"):
            (root / "data" / "tls" / name).write_text("test-only placeholder", encoding="utf-8")
        home = tmp / "home"
        fakebin = tmp / "bin"
        home.mkdir()
        fakebin.mkdir()
        log = tmp / "launchctl.log"
        launchctl = fakebin / "launchctl"
        launchctl.write_text("#!/bin/sh\necho \"$*\" >> \"$LAUNCHCTL_LOG\"\nexit 0\n", encoding="utf-8")
        launchctl.chmod(0o755)
        pgrep = fakebin / "pgrep"
        pgrep.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        pgrep.chmod(0o755)
        env = os.environ.copy()
        env.update({"HOME": str(home), "PATH": str(fakebin) + os.pathsep + env.get("PATH", ""),
                    "LAUNCHCTL_LOG": str(log)})
        subprocess.run(["bash", str(root / SCRIPTS[0])], check=True, cwd=root, env=env,
                       capture_output=True, text=True, timeout=20)
        plist = home / "Library" / "LaunchAgents" / "fr.maclasse.server.plist"
        with plist.open("rb") as stream:
            data = plistlib.load(stream)
        self.assertEqual(data["Label"], "fr.maclasse.server")
        self.assertTrue(data["KeepAlive"])
        self.assertTrue(data["RunAtLoad"])
        self.assertEqual(data["ProgramArguments"][1], str(root.resolve() / "data" / "program" / "current" / SCRIPTS[1]))
        self.assertEqual(data["EnvironmentVariables"]["MACLASSE_ROOT"], str(root.resolve()))
        self.assertEqual(data["EnvironmentVariables"]["MACLASSE_DATA_DIR"], str(root.resolve() / "data"))
        self.assertEqual(os.readlink(root / "data" / "program" / "current"), "../..")
        marker = root / "data" / "update-manager.enabled"
        self.assertTrue(marker.is_file())
        self.assertEqual(stat.S_IMODE(marker.stat().st_mode), 0o600)
        self.assertIn("$1 ~ /^[0-9]+$/", (root / SCRIPTS[0]).read_text(encoding="utf-8"))
        calls = log.read_text(encoding="utf-8")
        self.assertIn("bootstrap", calls)
        self.assertIn("kickstart", calls)


    @unittest.skipUnless(sys.platform == "darwin", "Le vrai serveur launchd nécessite macOS.")
    def test_launchd_starts_real_maclasse_server_over_local_https(self):
        uid = os.getuid()
        label = "fr.maclasse.server"
        domain = f"gui/{uid}/{label}"
        existing = subprocess.run(
            ["/bin/launchctl", "print", domain],
            capture_output=True, text=True, timeout=10
        )
        self.assertNotEqual(existing.returncode, 0, "Un agent MaClasse existe déjà ; test refusé.")
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        with tempfile.TemporaryDirectory(prefix="maclasse-real-server-launchd-") as temp:
            tmp = Path(temp)
            root = tmp / "MaClasse"
            data = root / "data"
            tls = data / "tls"
            agents = tmp / "home" / "Library" / "LaunchAgents"
            (root / ".venv" / "bin").mkdir(parents=True)
            tls.mkdir(parents=True)
            agents.mkdir(parents=True)
            (root / ".venv" / "bin" / "python").symlink_to(sys.executable)
            shutil.copy2(ROOT / "server.py", root / "server.py")
            shutil.copy2(ROOT / "update_manager.py", root / "update_manager.py")
            shutil.copy2(ROOT / "release_signing.py", root / "release_signing.py")
            self.assertTrue((root / "release_signing.py").is_file())
            (data / "maclasse.json").write_text(
                json.dumps({"schemaVersion": 25011, "users": [], "classes": [], "students": []}),
                encoding="utf-8"
            )
            cert = tls / "server.crt"
            key = tls / "server.key"
            subprocess.run([
                "/usr/bin/openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(key), "-out", str(cert), "-days", "2",
                "-subj", "/CN=127.0.0.1",
                "-addext", "subjectAltName=IP:127.0.0.1",
                "-addext", "basicConstraints=critical,CA:TRUE",
                "-addext", "keyUsage=critical,digitalSignature,keyCertSign,keyEncipherment"
            ], check=True, capture_output=True, timeout=30)
            key.chmod(0o600)
            runner = root / "launch-server.sh"
            runner.write_text(
                "#!/bin/bash\nset -euo pipefail\n"
                "exec \"$MACLASSE_ROOT/.venv/bin/python\" -u \"$MACLASSE_ROOT/server.py\"\n",
                encoding="utf-8"
            )
            runner.chmod(0o700)
            plist = agents / (label + ".plist")
            with plist.open("wb") as stream:
                plistlib.dump({
                    "Label": label,
                    "ProgramArguments": ["/bin/bash", str(runner)],
                    "WorkingDirectory": str(root),
                    "EnvironmentVariables": {
                        "MACLASSE_SUPERVISED": "launchd",
                        "MACLASSE_ROOT": str(root),
                        "MACLASSE_DATA_DIR": str(data),
                        "MACLASSE_HOST": "127.0.0.1",
                        "MACLASSE_PORT": str(port),
                        "MACLASSE_TLS_CERT": str(cert),
                        "MACLASSE_TLS_KEY": str(key)
                    },
                    "RunAtLoad": True,
                    "KeepAlive": True,
                    "StandardOutPath": str(data / "launchd-real-server.log"),
                    "StandardErrorPath": str(data / "launchd-real-server-error.log")
                }, stream, fmt=plistlib.FMT_XML)
            plist.chmod(0o600)
            context = ssl.create_default_context(cafile=str(cert))
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context)
            )
            url = f"https://127.0.0.1:{port}/api/health"
            try:
                subprocess.run(
                    ["/bin/launchctl", "bootstrap", f"gui/{uid}", str(plist)],
                    check=True, capture_output=True, text=True, timeout=15
                )
                subprocess.run(
                    ["/bin/launchctl", "kickstart", domain],
                    check=True, capture_output=True, text=True, timeout=15
                )
                deadline = time.time() + 20
                last_error = None
                while time.time() < deadline:
                    try:
                        with opener.open(url, timeout=2) as response:
                            payload = json.loads(response.read().decode("utf-8"))
                        self.assertTrue(payload.get("ok"), payload)
                        self.assertEqual(payload.get("database"), "ok")
                        version_source = (ROOT / "server.py").read_text(encoding="utf-8")
                        expected_version = next(line.split("\'")[1] for line in version_source.splitlines() if line.startswith("APP_VERSION="))
                        self.assertEqual(payload.get("version"), expected_version)
                        break
                    except (OSError, urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
                        last_error = error
                        time.sleep(0.25)
                else:
                    logs = (data / "launchd-real-server.log").read_text(encoding="utf-8", errors="replace") if (data / "launchd-real-server.log").exists() else ""
                    errors = (data / "launchd-real-server-error.log").read_text(encoding="utf-8", errors="replace") if (data / "launchd-real-server-error.log").exists() else ""
                    raise AssertionError(f"Le vrai serveur MaClasse ne répond pas sous launchd : {last_error}\nstdout:\n{logs}\nstderr:\n{errors}")
            finally:
                subprocess.run(
                    ["/bin/launchctl", "bootout", domain],
                    capture_output=True, text=True, timeout=15
                )
                deadline = time.time() + 10
                while time.time() < deadline:
                    probe = subprocess.run(
                        ["/bin/launchctl", "print", domain],
                        capture_output=True, text=True, timeout=5
                    )
                    if probe.returncode != 0 and "Could not find service" in (probe.stderr or ""):
                        break
                    time.sleep(0.2)
                else:
                    self.fail("Le LaunchAgent du vrai serveur MaClasse n'a pas été déchargé après le test.")

    @unittest.skipUnless(__import__("sys").platform == "darwin", "launchd réel uniquement sur macOS.")
    def test_real_launchd_bootstrap_starts_and_unloads_isolated_agent(self):
        import os
        import tempfile
        import time
        import shutil
        uid = os.getuid()
        label = "fr.maclasse.server"
        domain = f"gui/{uid}/{label}"
        existing = subprocess.run(["/bin/launchctl", "print", domain], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(existing.returncode, 0, "Le runner possède déjà un agent MaClasse ; test refusé pour ne rien perturber.")
        with tempfile.TemporaryDirectory(prefix="maclasse-launchd-live-") as temp:
            tmp = Path(temp)
            root = tmp / "MaClasse"
            (root / ".venv" / "bin").mkdir(parents=True)
            (root / "data" / "tls").mkdir(parents=True)
            (root / ".venv" / "bin" / "python").symlink_to(__import__("sys").executable)
            shutil.copy2(ROOT / "Installer-Service-MaClasse-macOS.sh", root / "Installer-Service-MaClasse-macOS.sh")
            runner = root / "Lancer-MaClasse-Service-macOS.sh"
            runner.write_text(
                '#!/bin/bash\nprintf "%s" "$BASHPID" > "$MACLASSE_DATA_DIR/launchd-live.pid"\nexec /bin/sleep 60\n',
                encoding="utf-8",
            )
            runner.chmod(0o700)
            for name in ("server.crt", "server.key", "ca.crt"):
                (root / "data" / "tls" / name).write_text("test-only placeholder", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(tmp / "home")
            try:
                result = subprocess.run(
                    ["bash", str(root / "Installer-Service-MaClasse-macOS.sh")],
                    cwd=root, env=env, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
                marker_file = root / "data" / "launchd-live.pid"
                deadline = time.time() + 10
                while time.time() < deadline and not marker_file.exists():
                    time.sleep(0.2)
                self.assertTrue(marker_file.is_file(), "launchd n'a pas démarré le lanceur isolé.")
                loaded = subprocess.run(["/bin/launchctl", "print", domain], capture_output=True, text=True, timeout=10)
                self.assertEqual(loaded.returncode, 0, loaded.stderr)
                self.assertIn(label, loaded.stdout)
            finally:
                subprocess.run(["/bin/launchctl", "bootout", domain], capture_output=True, text=True, timeout=10)
                pid_file = root / "data" / "launchd-live.pid"
                if pid_file.exists():
                    try:
                        os.kill(int(pid_file.read_text(encoding="utf-8")), 15)
                    except (OSError, ValueError):
                        pass



    def test_macos_health_check_extracts_ip_san_portably(self):
        with tempfile.TemporaryDirectory(prefix="maclasse-health-san-") as temp:
            certificate = Path(temp) / "server.crt"
            key = Path(temp) / "server.key"
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(key), "-out", str(certificate), "-days", "1",
                "-subj", "/CN=127.0.0.1",
                "-addext", "subjectAltName=IP:127.0.0.1"
            ], check=True, capture_output=True, timeout=30)
            parser = (
                "import ipaddress,ssl,sys\n"
                "certificate=ssl._ssl._test_decode_cert(sys.argv[1])\n"
                "for kind,value in certificate.get('subjectAltName',()):\n"
                " if kind=='IP Address':\n"
                "  print(ipaddress.ip_address(value)); break\n"
            )
            result = subprocess.run(
                [sys.executable, "-c", parser, str(certificate)],
                check=True, capture_output=True, text=True, timeout=10
            )
            self.assertEqual(result.stdout.strip(), "127.0.0.1")

    def test_macos_updater_retains_active_previous_and_three_newest_versions(self):
        script = (ROOT / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh").read_text(encoding="utf-8")
        start_marker = 'if ! "$ROOT/.venv/bin/python" - "$VERSIONS" "$TARGET_REAL" "$PREVIOUS_REAL" <<\'PY\'\n'
        self.assertIn(start_marker, script)
        start = script.index(start_marker) + len(start_marker)
        end = script.index("\nPY\nthen", start)
        pruning_code = script[start:end]
        with tempfile.TemporaryDirectory(prefix="maclasse-version-retention-") as temp:
            versions = Path(temp) / "versions"
            versions.mkdir()
            paths = {}
            for version in range(1, 7):
                path = versions / f"V1.0.{version}"
                path.mkdir()
                paths[version] = path
            outside = Path(temp) / "outside"
            outside.mkdir()
            (versions / "V1.0.7").symlink_to(outside, target_is_directory=True)
            subprocess.run(
                [sys.executable, "-c", pruning_code, str(versions), str(paths[6]), str(paths[2])],
                check=True,
            )
            self.assertTrue(paths[6].is_dir(), "La version active doit être conservée.")
            self.assertTrue(paths[2].is_dir(), "La version de rollback doit être conservée.")
            self.assertTrue(paths[4].is_dir() and paths[5].is_dir(), "Les trois versions les plus récentes doivent être conservées.")
            self.assertFalse(paths[1].exists())
            self.assertFalse(paths[3].exists())
            self.assertTrue(outside.is_dir(), "Le nettoyage ne doit jamais suivre un lien symbolique.")



    @unittest.skipUnless(__import__("sys").platform == "darwin", "Le test launchd réel nécessite macOS.")
    def test_launchd_waiting_service_without_pid_can_be_unloaded_for_rollback(self):
        import os
        import plistlib
        import tempfile
        import time

        uid = os.getuid()
        label = "fr.maclasse.server"
        domain = f"gui/{uid}/{label}"
        existing = subprocess.run(
            ["/bin/launchctl", "print", domain],
            capture_output=True, text=True, timeout=10
        )
        self.assertNotEqual(existing.returncode, 0, "Un agent MaClasse existe déjà ; test refusé.")

        script = (ROOT / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh").read_text(encoding="utf-8")
        helper_start = script.index("server_processes() {")
        helper_end = script.index("\nstart_service() {", helper_start)
        helper_functions = script[helper_start:helper_end]
        stop_start = script.index("stop_service_and_confirm() {")
        stop_end = script.index("\nfail_restore() {", stop_start)
        stop_function = script[stop_start:stop_end]

        with tempfile.TemporaryDirectory(prefix="maclasse-launchd-no-pid-") as temp:
            base = Path(temp)
            root = base / "MaClasse"
            python = root / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.symlink_to(sys.executable)
            agents = base / "home" / "Library" / "LaunchAgents"
            agents.mkdir(parents=True)
            plist = agents / (label + ".plist")
            with plist.open("wb") as stream:
                plistlib.dump({
                    "Label": label,
                    "ProgramArguments": ["/usr/bin/true"],
                    "RunAtLoad": True,
                    "KeepAlive": False,
                    "StandardOutPath": str(base / "service.log"),
                    "StandardErrorPath": str(base / "service-error.log"),
                }, stream, fmt=plistlib.FMT_XML)
            plist.chmod(0o600)
            try:
                subprocess.run(
                    ["/bin/launchctl", "bootstrap", f"gui/{uid}", str(plist)],
                    check=True, capture_output=True, text=True, timeout=15
                )
                subprocess.run(
                    ["/bin/launchctl", "kickstart", domain],
                    check=True, capture_output=True, text=True, timeout=15
                )
                deadline = time.time() + 10
                waiting_without_pid = False
                while time.time() < deadline:
                    current = subprocess.run(
                        ["/bin/launchctl", "print", domain],
                        capture_output=True, text=True, timeout=5
                    )
                    has_live_pid = any(
                        line.strip().startswith("pid = ")
                        and line.strip() != "pid = 0"
                        and line.strip().split("=", 1)[1].strip().isdigit()
                        for line in current.stdout.splitlines()
                    )
                    if current.returncode == 0 and not has_live_pid:
                        waiting_without_pid = True
                        break
                    time.sleep(0.1)
                self.assertTrue(waiting_without_pid, "Le service test n'a pas atteint l'état chargé sans PID.")

                command = (
                    "set -euo pipefail\n"
                    f"ROOT={str(root)!r}\n"
                    f"UID_NOW={uid}\n"
                    f"SERVICE_LABEL={label!r}\n"
                    "SERVICE_DISABLED=0\n"
                    + helper_functions + "\n" + stop_function + "\n"
                    "stop_service_and_confirm\n"
                    "printf 'SERVICE_DISABLED=%s\\n' \"$SERVICE_DISABLED\"\n"
                )
                result = subprocess.run(
                    ["/bin/bash"], input=command,
                    capture_output=True, text=True, timeout=40
                )
                self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
                self.assertIn("SERVICE_DISABLED=1", result.stdout)
                self.assertIn("service déchargé", result.stderr)
            finally:
                subprocess.run(
                    ["/bin/launchctl", "bootout", domain],
                    capture_output=True, text=True, timeout=10
                )
                subprocess.run(
                    ["/bin/launchctl", "enable", domain],
                    capture_output=True, text=True, timeout=10
                )

    @unittest.skipUnless(__import__("sys").platform == "darwin", "L'installation macOS réelle nécessite launchd.")
    def test_macos_update_install_and_rollback_end_to_end_with_launchd_and_https(self):
        import json
        import os
        import ssl
        import socket
        import tempfile
        import time
        import urllib.error
        import urllib.request

        uid = os.getuid()
        label = "fr.maclasse.server"
        domain = f"gui/{uid}/{label}"
        existing = subprocess.run(
            ["/bin/launchctl", "print", domain],
            capture_output=True, text=True, timeout=10
        )
        self.assertNotEqual(existing.returncode, 0, "Un agent MaClasse existe déjà ; test refusé pour ne rien perturber.")
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", 8765))
            except OSError:
                self.skipTest("Le port HTTPS 8765 est déjà utilisé.")

        with tempfile.TemporaryDirectory(prefix="maclasse-update-e2e-") as temp:
            tmp = Path(temp)
            root = tmp / "MaClasse"
            data = root / "data"
            tls = data / "tls"
            versions = data / "program" / "versions"
            agents = tmp / "home" / "Library" / "LaunchAgents"
            for directory in (root / ".venv" / "bin", tls, versions, agents):
                directory.mkdir(parents=True, exist_ok=True)
            (root / ".venv" / "bin" / "python").symlink_to(sys.executable)

            ca_key = tls / "ca.key"
            ca_cert = tls / "ca.crt"
            server_key = tls / "server.key"
            server_csr = tls / "server.csr"
            server_cert = tls / "server.crt"
            extensions = tls / "server.ext"
            subprocess.run(["/usr/bin/openssl", "genrsa", "-out", str(ca_key), "2048"],
                           check=True, capture_output=True, timeout=20)
            ca_config = tls / "ca.cnf"
            ca_config.write_text(
                """[req]
distinguished_name=dn
x509_extensions=v3_ca
prompt=no
[dn]
CN=MaClasse updater test CA
[v3_ca]
basicConstraints=critical,CA:TRUE
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
""",
                encoding="utf-8"
            )
            ca_result = subprocess.run([
                "/usr/bin/openssl", "req", "-x509", "-new", "-sha256", "-days", "2",
                "-key", str(ca_key), "-out", str(ca_cert), "-config", str(ca_config),
                "-extensions", "v3_ca", "-subj", "/CN=MaClasse updater test CA"
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(ca_result.returncode, 0, ca_result.stdout + "\n" + ca_result.stderr)
            subprocess.run([
                "/usr/bin/openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(server_key), "-out", str(server_csr),
                "-subj", "/CN=127.0.0.1"
            ], check=True, capture_output=True, timeout=20)
            extensions.write_text(
                "subjectAltName=IP:127.0.0.1\nextendedKeyUsage=serverAuth\nkeyUsage=digitalSignature,keyEncipherment\n",
                encoding="utf-8"
            )
            subprocess.run([
                "/usr/bin/openssl", "x509", "-req", "-in", str(server_csr),
                "-CA", str(ca_cert), "-CAkey", str(ca_key), "-CAcreateserial",
                "-out", str(server_cert), "-days", "2", "-sha256", "-extfile", str(extensions)
            ], check=True, capture_output=True, timeout=20)
            ca_key.chmod(0o600)
            server_key.chmod(0o600)

            def make_version(version, sha, healthy=True, prepared=False):
                program = versions / ("V" + version)
                (program / ".venv" / "bin").mkdir(parents=True)
                (program / ".venv" / "bin" / "python").symlink_to(sys.executable)
                (program / "VERSION.txt").write_text("V" + version + "\n", encoding="utf-8")
                (program / "_all.js").write_text("const MC_VERSION='V" + version + "';\n", encoding="utf-8")
                (program / "server.py").write_text(
                    "APP_VERSION='" + version + "'\n"
                    "HEALTHY=" + ("True" if healthy else "False") + "\n"
                    "import json,os,ssl,socketserver,signal\n"
                    "from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer\n"
                    "class TestHTTPServer(ThreadingHTTPServer):\n"
                    " daemon_threads=False\n"
                    " block_on_close=True\n"
                    " def server_bind(self):\n"
                    "  socketserver.TCPServer.server_bind(self)\n"
                    "  self.server_name=str(self.server_address[0])\n"
                    "  self.server_port=int(self.server_address[1])\n"
                    "class Handler(BaseHTTPRequestHandler):\n"
                    " timeout=20\n"
                    " def do_GET(self):\n"
                    "  body=json.dumps({'ok':HEALTHY,'version':APP_VERSION,'database':'ok'}).encode()\n"
                    "  self.send_response(200 if HEALTHY else 503)\n"
                    "  self.send_header('Content-Type','application/json')\n"
                    "  self.send_header('Content-Length',str(len(body)))\n"
                    "  self.end_headers();self.wfile.write(body)\n"
                    " def log_message(self,*args): pass\n"
                    "server=TestHTTPServer(('127.0.0.1',8765),Handler)\n"

                    "context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)\n"
                    "context.load_cert_chain(os.environ['MACLASSE_TLS_CERT'],os.environ['MACLASSE_TLS_KEY'])\n"

                    "server.socket=context.wrap_socket(server.socket,server_side=True)\n"
                    "def stop(signum,frame): raise KeyboardInterrupt\n"
                    "signal.signal(signal.SIGTERM,stop)\n"
                    "try: server.serve_forever()\n"
                    "except KeyboardInterrupt: pass\n"
                    "finally: server.server_close()\n",
                    encoding="utf-8"
                )
                supervisor_source = (ROOT / "network_supervisor.py").read_text(encoding="utf-8")
                marker = "    detect_ip = detect_ip or detect_lan_ipv4"
                if marker not in supervisor_source:
                    raise AssertionError("Le point d'injection de l'IP de test a changé.")
                supervisor_source = supervisor_source.replace(
                    marker, "    detect_ip = detect_ip or (lambda: '127.0.0.1')"
                )
                (program / "network_supervisor.py").write_text(supervisor_source, encoding="utf-8")
                (program / "maclasse-runtime-ready.json").write_text("{}", encoding="utf-8")
                if prepared:
                    (program / "maclasse-prepared.json").write_text(
                        json.dumps({"sha256": sha, "status": "prepared"}), encoding="utf-8"
                    )
                return program

            make_version("25.0.22", "0" * 64)
            good_sha = "a" * 64
            make_version("25.0.23", good_sha, healthy=True, prepared=True)
            bad_sha = "b" * 64
            make_version("25.0.24", bad_sha, healthy=False, prepared=True)
            current = data / "program" / "current"
            current.symlink_to("versions/V25.0.22")
            (data / "maclasse.json").write_text('{"preserve":"original"}', encoding="utf-8")
            runner = root / "Lancer-MaClasse-Service-macOS.sh"
            shutil.copy2(ROOT / "Lancer-MaClasse-Service-macOS.sh", runner)
            runner.chmod(0o700)
            service_plist = agents / (label + ".plist")
            with service_plist.open("wb") as stream:
                plistlib.dump({
                    "Label": label,
                    "ProgramArguments": ["/bin/bash", str(runner)],
                    "WorkingDirectory": str(root),
                    "EnvironmentVariables": {
                        "MACLASSE_ROOT": str(root),
                        "MACLASSE_DATA_DIR": str(data),
                        "MACLASSE_TLS_CERT": str(server_cert),
                        "MACLASSE_TLS_KEY": str(server_key)
                    },
                    "RunAtLoad": True,
                    "KeepAlive": True,
                    "StandardOutPath": str(data / "service.log"),
                    "StandardErrorPath": str(data / "service-error.log")
                }, stream, fmt=plistlib.FMT_XML)
            service_plist.chmod(0o600)

            env = os.environ.copy()
            env.update({
                "HOME": str(tmp / "home"),
                "MACLASSE_ROOT": str(root),
                "MACLASSE_DATA_DIR": str(data)
            })
            base_url = "https://127.0.0.1:8765/api/health"
            context = ssl.create_default_context(cafile=str(ca_cert))
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(context=context)
            )
            env["NO_PROXY"] = "127.0.0.1,localhost"
            env["no_proxy"] = "127.0.0.1,localhost"

            def wait_for_version(version, timeout=15):
                deadline = time.time() + timeout
                last_error = None
                while time.time() < deadline:
                    try:
                        with opener.open(base_url, timeout=2) as response:
                            payload = json.loads(response.read().decode("utf-8"))
                        if payload.get("ok") is True and payload.get("version") == version and payload.get("database") == "ok":
                            return payload
                        last_error = payload
                    except (OSError, urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
                        last_error = error
                    time.sleep(0.25)
                launchd_list = subprocess.run(
                    ["/bin/launchctl", "list", label], capture_output=True, text=True, timeout=10
                )
                launchd_print = subprocess.run(
                    ["/bin/launchctl", "print", domain], capture_output=True, text=True, timeout=10
                )
                service_log = (data / "service.log").read_text(encoding="utf-8", errors="replace") if (data / "service.log").exists() else ""
                service_error = (data / "service-error.log").read_text(encoding="utf-8", errors="replace") if (data / "service-error.log").exists() else ""
                runner_log = (data / "runner.log").read_text(encoding="utf-8", errors="replace") if (data / "runner.log").exists() else ""
                process_info = subprocess.run(["/bin/ps", "-axo", "pid,ppid,stat,command"], capture_output=True, text=True, timeout=10).stdout
                listener_info = subprocess.run(["/usr/sbin/lsof", "-nP", "-iTCP:8765", "-sTCP:LISTEN"], capture_output=True, text=True, timeout=10).stdout
                raise AssertionError(
                    "Le serveur de test n'est pas sain pour " + version + " : " + repr(last_error)
                    + "\nlaunchctl list:\n" + launchd_list.stdout + launchd_list.stderr
                    + "\nlaunchctl print:\n" + launchd_print.stdout + launchd_print.stderr
                    + "\nstdout:\n" + service_log + "\nstderr:\n" + service_error + "\nrunner:\n" + runner_log + "\nlisteners:\n" + listener_info + "\nprocesses:\n" + process_info[-8000:]
                )

            idle_connection = None
            try:
                subprocess.run(["/bin/launchctl", "bootstrap", f"gui/{uid}", str(service_plist)],
                               check=True, capture_output=True, text=True, timeout=15)
                subprocess.run(["/bin/launchctl", "kickstart", domain],
                               check=True, capture_output=True, text=True, timeout=15)
                wait_for_version("25.0.22")
                # A connected client that never sends an HTTP request must not
                # hold launchd bootout and the complete update cycle forever.
                idle_connection = context.wrap_socket(
                    socket.create_connection(("127.0.0.1", 8765), timeout=5),
                    server_hostname="127.0.0.1"
                )

                updater = ROOT / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh"
                state_file = data / "update-state.json"
                state_file.write_text(json.dumps({
                    "status": "prepared", "version": "25.0.23", "sha256": good_sha
                }), encoding="utf-8")
                try:
                    success = subprocess.run(
                        ["/bin/bash", str(updater)], cwd=root, env=env,
                        capture_output=True, text=True, timeout=140
                    )
                except subprocess.TimeoutExpired as timeout_error:
                    timeout_diagnostics = {
                        "update_state": state_file.read_text(encoding="utf-8", errors="replace") if state_file.exists() else "<absent>",
                        "current_link": os.readlink(current) if current.is_symlink() else "<not a symlink>",
                        "launchd_service": subprocess.run(
                            ["/bin/launchctl", "print", f"gui/{uid}/fr.maclasse.server"],
                            capture_output=True, text=True, timeout=10
                        ).stdout,
                        "processes": subprocess.run(
                            ["/usr/bin/pgrep", "-alf", "server[.]py"],
                            capture_output=True, text=True, timeout=10
                        ).stdout,
                        "updater_stdout": timeout_error.stdout,
                        "updater_stderr": timeout_error.stderr,
                        "service_stdout": (data / "service.log").read_text(encoding="utf-8", errors="replace") if (data / "service.log").exists() else "",
                        "service_stderr": (data / "service-error.log").read_text(encoding="utf-8", errors="replace") if (data / "service-error.log").exists() else "",
                        "runner_log": (data / "runner.log").read_text(encoding="utf-8", errors="replace") if (data / "runner.log").exists() else "",
                        "process_table": subprocess.run(
                            ["/bin/ps", "-axo", "pid,ppid,stat,command"],
                            capture_output=True, text=True, timeout=10
                        ).stdout[-6000:],
                        "listener": subprocess.run(
                            ["/usr/sbin/lsof", "-nP", "-iTCP:8765"],
                            capture_output=True, text=True, timeout=10
                        ).stdout,
                        "health_probe": subprocess.run(
                            ["/usr/bin/curl", "--noproxy", "*", "--insecure", "--silent", "--show-error",
                             "--connect-timeout", "2", "--max-time", "4", "--write-out", "\nHTTP=%{http_code}",
                             "https://127.0.0.1:8765/api/health"],
                            capture_output=True, text=True, timeout=10
                        ).stdout
                    }
                    self.fail(f"Mise à jour macOS bloquée après 140 s : {timeout_error}\n" + json.dumps(timeout_diagnostics, ensure_ascii=False, indent=2, default=lambda value: value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)))
                if success.returncode != 0:
                    diagnostics = {}
                    for name in ("macos-update.log", "macos-update-error.log", "service.log", "service-error.log"):
                        path = data / name
                        diagnostics[name] = path.read_text(encoding="utf-8", errors="replace") if path.exists() else "<absent>"
                    diagnostics["update_state"] = state_file.read_text(encoding="utf-8", errors="replace") if state_file.exists() else "<absent>"
                    diagnostics["current_link"] = os.readlink(current) if current.is_symlink() else "<not a symlink>"
                    diagnostics["launchd_service"] = subprocess.run(
                        ["/bin/launchctl", "print", f"gui/{uid}/fr.maclasse.server"],
                        capture_output=True, text=True, timeout=10
                    ).stdout
                    diagnostics["launchd_update"] = subprocess.run(
                        ["/bin/launchctl", "print", f"gui/{uid}/fr.maclasse.update"],
                        capture_output=True, text=True, timeout=10
                    ).stdout
                    diagnostics["processes"] = subprocess.run(
                        ["/usr/bin/pgrep", "-alf", "server[.]py"],
                        capture_output=True, text=True, timeout=10
                    ).stdout
                    self.fail(success.stdout + "\n" + success.stderr + "\n" + json.dumps(diagnostics, ensure_ascii=False, indent=2))
                self.assertEqual((current.resolve()).name, "V25.0.23")
                self.assertEqual(json.loads((data / "maclasse.json").read_text(encoding="utf-8")),
                                 {"preserve": "original"})
                self.assertEqual(json.loads(state_file.read_text(encoding="utf-8"))["status"], "installed")
                self.assertTrue(list((data / "backups").glob("maclasse-avant-maj-*.json")))
                wait_for_version("25.0.23")

                # A bad next version must fail health validation, restore the previous
                # symlink and database atomically, then restart the previous service.
                (data / "maclasse.json").write_text('{"preserve":"before-rollback"}', encoding="utf-8")
                state_file.write_text(json.dumps({
                    "status": "prepared", "version": "25.0.24", "sha256": bad_sha
                }), encoding="utf-8")
                failed = subprocess.run(
                    ["/bin/bash", str(updater)], cwd=root, env=env,
                    capture_output=True, text=True, timeout=140
                )
                self.assertNotEqual(failed.returncode, 0, failed.stdout + "\n" + failed.stderr)
                self.assertEqual(current.resolve().name, "V25.0.23")
                self.assertEqual(json.loads((data / "maclasse.json").read_text(encoding="utf-8")),
                                 {"preserve": "before-rollback"})
                self.assertEqual(json.loads(state_file.read_text(encoding="utf-8"))["status"], "failed")
                wait_for_version("25.0.23")
            finally:
                if idle_connection is not None:
                    idle_connection.close()
                subprocess.run(["/bin/launchctl", "bootout", domain],
                               capture_output=True, text=True, timeout=10)
                listed = subprocess.run(["/bin/launchctl", "print", domain],
                                        capture_output=True, text=True, timeout=10)
                for line in (listed.stdout or "").splitlines():
                    fields = line.strip().split()
                    if len(fields) == 3 and fields[0] == "pid" and fields[1] == "=" and fields[2].isdigit() and int(fields[2]) > 0:
                        try:
                            os.kill(int(fields[2]), 15)
                        except OSError:
                            pass

    def test_launchd_schedule_and_immediate_job_plists(self):
        code = r"""
import os, pathlib, plistlib, subprocess, sys, tempfile, time
root = pathlib.Path(sys.argv[1])
tmp = pathlib.Path(tempfile.mkdtemp(prefix="maclasse-launchd-test-"))
os.environ["MACLASSE_DATA_DIR"] = str(tmp / "data")
os.environ["MACLASSE_SUPERVISED"] = "launchd"
os.environ["HOME"] = str(tmp / "home")
(tmp / "home" / "Library" / "LaunchAgents").mkdir(parents=True)
sys.path.insert(0, str(root))
import server
server.sys.platform = "darwin"
calls = []
def fake_run(args, **kwargs):
    calls.append(args)
    if args[:2] == ["/bin/launchctl", "print"]:
        return subprocess.CompletedProcess(args, 1, "", "Could not find service")
    return subprocess.CompletedProcess(args, 0, "", "")
server.subprocess.run = fake_run
server._schedule_update_timer(time.time() + 3600)
scheduled = pathlib.Path(server._launchd_update_plist())
with scheduled.open("rb") as stream:
    data = plistlib.load(stream)
assert data["Label"] == "fr.maclasse.update"
assert data["EnvironmentVariables"]["MACLASSE_ROOT"] == str(tmp)
assert data["EnvironmentVariables"]["MACLASSE_DATA_DIR"] == str(tmp / "data")
assert data["StartCalendarInterval"]["Minute"] >= 0
assert data["ProgramArguments"][0:2] == ["/bin/bash", str(root / "Appliquer-Mise-A-Jour-MaClasse-macOS.sh")]
server._cancel_update_timer()
assert not scheduled.exists()
server._start_update_apply_service()
with scheduled.open("rb") as stream:
    immediate = plistlib.load(stream)
assert immediate["RunAtLoad"] is False
assert immediate["EnvironmentVariables"]["MACLASSE_ROOT"] == str(tmp)
assert immediate["EnvironmentVariables"]["MACLASSE_DATA_DIR"] == str(tmp / "data")
assert "StartCalendarInterval" not in immediate
assert any(call[:2] == ["/bin/launchctl", "kickstart"] for call in calls)

# Never unload an updater process that has already started installing.
active_calls = []
def active_run(args, **kwargs):
    active_calls.append(args)
    if args[:2] == ["/bin/launchctl", "print"]:
        return subprocess.CompletedProcess(args, 0, "state = running\npid = 4321\n", "")
    return subprocess.CompletedProcess(args, 0, "", "")
server.subprocess.run = active_run
try:
    server._start_update_apply_service()
except RuntimeError:
    pass
else:
    raise AssertionError("immediate launch was allowed while a scheduled updater was running")
assert not any(call[:2] in (["/bin/launchctl", "bootout"], ["/bin/launchctl", "kickstart"]) for call in active_calls)
try:
    server._cancel_update_timer()
except RuntimeError:
    pass
else:
    raise AssertionError("running launchd updater was allowed to be unloaded")
assert not any(call[:2] == ["/bin/launchctl", "bootout"] for call in active_calls)

# A failed bootout must not be reported as a successful cancellation.
def stuck_run(args, **kwargs):
    if args[:2] == ["/bin/launchctl", "print"]:
        return subprocess.CompletedProcess(args, 0, "loaded", "")
    return subprocess.CompletedProcess(args, 0, "", "")
server.subprocess.run = stuck_run
try:
    server._cancel_update_timer()
except RuntimeError:
    pass
else:
    raise AssertionError("launchd still loaded the task but cancellation was accepted")
assert scheduled.exists()
"""
        subprocess.run(["python", "-c", code, str(ROOT)], check=True, cwd=ROOT)

    def test_launchd_activity_parser_uses_print_pid_and_idle_state(self):
        code = r"""
import subprocess, sys
sys.path.insert(0, str(sys.argv[1]))
import server
server.sys.platform = "darwin"
server.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "state = waiting\n", "")
assert server._update_apply_service_active() is False
server.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "state = running\npid = 4321\n", "")
assert server._update_apply_service_active() is True
server.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 113, "", "Could not find service")
assert server._update_apply_service_active() is False
"""
        subprocess.run(["python", "-c", code, str(ROOT)], check=True, cwd=ROOT)

    def test_database_backup_happens_after_launchd_service_shutdown(self):
        script = (ROOT / SCRIPTS[2]).read_text(encoding="utf-8")
        self.assertIn("fcntl.LOCK_EX | fcntl.LOCK_NB", script)
        self.assertIn("update-apply.lock", script)
        stop = script.index('launchctl bootout "gui/$UID_NOW/$SERVICE_LABEL"')
        backup = script.index('/bin/cp -p "$DATA/maclasse.json" "$BACKUP_FILE"')
        self.assertLess(stop, backup)
        self.assertLess(script.index("if ! stop_service_and_confirm; then"), backup)
        self.assertIn("write_maintenance_state completed", script)


    def test_launchd_shutdown_is_bounded_and_confirms_process_exit_before_backup(self):
        script = (ROOT / SCRIPTS[2]).read_text(encoding="utf-8")
        start = script.index("stop_service_and_confirm() {")
        end = script.index("\n}\nfail_restore()", start) + 2
        function = script[start:end]
        self.assertIn("launchctl bootout", function)
        self.assertIn("for _ in {1..125}", function)
        self.assertIn("server_processes remaining 0", function)
        self.assertIn("/bin/kill -KILL", function)
        self.assertIn("/bin/kill -0", function)
        self.assertIn("Could not find service", function)
        self.assertLess(function.index("/bin/launchctl disable"), function.index("/bin/launchctl bootout"))
        self.assertLess(function.index("/bin/launchctl bootout"), function.index("/bin/kill -KILL"))
        self.assertGreater(function.rindex("server_processes remaining 0"), function.index("/bin/launchctl bootout"))
        trap = script[script.index("restore_service_enabled() {"):script.index("trap restore_service_enabled EXIT")]
        failure = script[script.index("fail_restore() {"):script.index("\n}\nabort_before_switch()")]
        self.assertIn('if [[ "$KEEP_SERVICE_DISABLED" == "1" ]]', trap)
        self.assertIn("KEEP_SERVICE_DISABLED=1", failure)
        backup = script.index('/bin/cp -p "$DATA/maclasse.json" "$BACKUP_FILE"')
        self.assertLess(script.index("if ! stop_service_and_confirm; then"), backup)

    def test_installer_checks_health_and_has_rollback_path(self):
        script = (ROOT / SCRIPTS[2]).read_text(encoding="utf-8")
        self.assertIn("health_ok", script)
        self.assertIn("stop_service_and_confirm", script)
        self.assertIn('server_processes unmanaged "$SERVICE_PID"', script)
        self.assertIn("server_processes remaining 0", script)
        self.assertIn("version précédente absente ou invalide", script)
        self.assertIn("base non restaurée", script)
        self.assertIn('MACLASSE_ROOT:-', script)
        self.assertIn('MACLASSE_DATA_DIR:-', script)
        self.assertIn("fail_restore", script)
        self.assertIn("os.replace(sys.argv[1],sys.argv[2])", script)
        self.assertIn("maclasse-avant-maj-", script)
        self.assertIn("rollback_failed", script)
        self.assertIn("launchctl bootout", script)
        self.assertIn("os.replace(source,destination)", script)
        self.assertIn("os.fsync(stream.fileno())", script)

    @unittest.skipUnless(sys.platform == "darwin", "La migration d'installation nécessite macOS.")
    def test_v25_0_19_existing_install_migrates_to_managed_launchd_without_touching_data(self):
        """Reproduces the pre-supervisor V25.0.19 layout before enabling the updater."""
        import os
        import tempfile
        import shutil
        import json
        import plistlib

        with tempfile.TemporaryDirectory(prefix="maclasse-v2519-migration-") as temp:
            base = Path(temp)
            root = base / "MaClasse"
            data = root / "data"
            (root / ".venv" / "bin").mkdir(parents=True)
            (data / "tls").mkdir(parents=True)
            (data / "uploads" / "travaux").mkdir(parents=True)
            (root / "VERSION.txt").write_text("V25.0.19" + chr(10), encoding="utf-8")
            (data / "uploads" / "travaux" / "échantillon.txt").write_text("rendu conservé", encoding="utf-8")
            (root / ".venv" / "bin" / "python").symlink_to(sys.executable)
            for name in SCRIPTS:
                shutil.copy2(ROOT / name, root / name)
            # Representative persistent V25.0.19 installation data.
            database = {"schemaVersion": 25011, "school": "École de test",
                        "users": [{"username": "admin"}], "classes": [{"name": "6e A"}],
                        "students": [{"name": "Élève témoin"}]}
            (data / "maclasse.json").write_text(json.dumps(database, ensure_ascii=False), encoding="utf-8")
            for name in ("server.crt", "server.key", "ca.crt"):
                (data / "tls" / name).write_text("fixture-" + name, encoding="utf-8")
            home = base / "home"
            fakebin = base / "bin"
            home.mkdir()
            fakebin.mkdir()
            log = base / "launchctl.log"
            launchctl = fakebin / "launchctl"
            launchctl.write_text('#!/bin/sh\necho "$*" >> "$LAUNCHCTL_LOG"\nexit 0\n', encoding="utf-8")
            launchctl.chmod(0o755)
            pgrep = fakebin / "pgrep"
            pgrep.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            pgrep.chmod(0o755)
            env = os.environ.copy()
            env.update({"HOME": str(home), "PATH": str(fakebin) + os.pathsep + env.get("PATH", ""),
                        "LAUNCHCTL_LOG": str(log)})
            result = subprocess.run(["bash", str(root / SCRIPTS[0])], cwd=root, env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
            self.assertEqual(json.loads((data / "maclasse.json").read_text(encoding="utf-8")), database)
            for name in ("server.crt", "server.key", "ca.crt"):
                self.assertEqual((data / "tls" / name).read_text(encoding="utf-8"), "fixture-" + name)
            self.assertEqual((data / "uploads" / "travaux" / "échantillon.txt").read_text(encoding="utf-8"), "rendu conservé")
            self.assertEqual((root / "VERSION.txt").read_text(encoding="utf-8"), "V25.0.19" + chr(10))
            current = data / "program" / "current"
            self.assertTrue(current.is_symlink())
            self.assertEqual(current.resolve(), root.resolve())
            plist = home / "Library" / "LaunchAgents" / "fr.maclasse.server.plist"
            with plist.open("rb") as stream:
                service = plistlib.load(stream)
            self.assertEqual(service["EnvironmentVariables"]["MACLASSE_ROOT"], str(root.resolve()))
            self.assertEqual(service["EnvironmentVariables"]["MACLASSE_DATA_DIR"], str(data.resolve()))
            # macOS may canonicalize /var through its /private/var symlink.
            # Compare resolved paths rather than their textual spelling.
            self.assertEqual(
                Path(service["ProgramArguments"][1]).resolve(),
                (current / "Lancer-MaClasse-Service-macOS.sh").resolve(),
            )
            self.assertTrue((data / "update-manager.enabled").is_file())
            self.assertIn("bootstrap", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
