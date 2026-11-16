import subprocess
import unittest
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UpdateScriptSafetyTests(unittest.TestCase):

    def test_stable_release_workflow_is_gated_by_the_full_test_matrix(self):
        tests = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        release = (ROOT / ".github" / "workflows" / "publish-release.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", tests)
        self.assertIn("uses: ./.github/workflows/tests.yml", release)
        self.assertIn("needs: validate", release)
        self.assertIn("macos-validation:", tests)
        self.assertIn("firefox-schedule-regression:", tests)

    def test_both_update_scripts_are_valid_shell(self):
        for name in ("Mettre-A-Jour-MaClasse.command", "Mettre-A-Jour-MaClasse-Linux.sh"):
            with self.subTest(script=name):
                subprocess.run(["bash", "-n", str(ROOT / name)], check=True)

    def test_supervised_linux_cli_uses_the_same_stable_release_engine(self):
        source = (ROOT / "Mettre-A-Jour-MaClasse-Linux.sh").read_text(encoding="utf-8")
        self.assertIn('if [[ -f "$DATA_ROOT/update-manager.enabled" ]]', source)
        self.assertIn("update_manager.check_latest_release(version)", source)
        self.assertIn("update_manager.prepare_runtime(prepared)", source)
        self.assertIn("maclasse-update-apply.service", source)
        self.assertIn("Le serveur est actif mais le gestionnaire", source)
        self.assertIn("pgrep -f '[p]ython.*server\\.py'", source)
        self.assertIn("raise SystemExit(10)", source)

    @unittest.skipUnless(__import__("sys").platform.startswith("linux"), "Le secours CLI supervisé cible Linux.")
    def test_supervised_cli_does_not_start_installer_when_no_release_exists(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "MaClasse"
            data = root / "data"
            version = data / "program" / "versions" / "V25.0.22"
            python = version / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.write_text("#!/bin/sh\nexit 10\n", encoding="utf-8")
            python.chmod(0o755)
            current = data / "program" / "current"
            current.parent.mkdir(parents=True, exist_ok=True)
            current.symlink_to("versions/V25.0.22")
            (data / "update-manager.enabled").parent.mkdir(parents=True, exist_ok=True)
            (data / "update-manager.enabled").write_text("enabled", encoding="utf-8")
            shutil.copy2(ROOT / "Mettre-A-Jour-MaClasse-Linux.sh", root / "Mettre-A-Jour-MaClasse-Linux.sh")
            fakebin = Path(tmp) / "bin"
            fakebin.mkdir()
            log = Path(tmp) / "systemctl.log"
            systemctl = fakebin / "systemctl"
            systemctl.write_text(
                '#!/bin/sh\n'
                'echo "$*" >> "$SYSTEMCTL_LOG"\n'
                'case "$*" in *"is-active --quiet maclasse-update-apply.service"*) exit 3;; '
                '*"show --property=MainPID --value maclasse.service"*) echo 0; exit 0;; '
                'esac\nexit 0\n', encoding="utf-8"
            )
            systemctl.chmod(0o755)
            pgrep = fakebin / "pgrep"
            pgrep.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            pgrep.chmod(0o755)
            env = os.environ.copy()
            env.update({"PATH": str(fakebin) + os.pathsep + env.get("PATH", ""), "SYSTEMCTL_LOG": str(log)})
            result = subprocess.run(
                ["bash", str(root / "Mettre-A-Jour-MaClasse-Linux.sh")],
                cwd=root, env=env, capture_output=True, text=True, timeout=10
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertNotIn("start --no-block maclasse-update-apply.service", log.read_text(encoding="utf-8"))


    def test_macos_legacy_updater_refuses_to_mutate_a_supervised_installation(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "MaClasse"
            (root / ".git").mkdir(parents=True)
            python = root / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
            python.chmod(0o755)
            marker = root / "data" / "update-manager.enabled"
            marker.parent.mkdir(parents=True)
            marker.write_text("enabled", encoding="utf-8")
            script = root / "Mettre-A-Jour-MaClasse.command"
            shutil.copy2(ROOT / "Mettre-A-Jour-MaClasse.command", script)
            result = subprocess.run(["bash", str(script)], cwd=root, input="\\n",
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("gestionnaire de mises à jour supervisé", result.stdout)
            self.assertFalse((root / ".git" / "FETCH_HEAD").exists())

    def test_macos_legacy_updater_refuses_to_run_while_server_is_active(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "MaClasse"
            (root / ".git").mkdir(parents=True)
            python = root / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
            python.chmod(0o755)
            script = root / "Mettre-A-Jour-MaClasse.command"
            shutil.copy2(ROOT / "Mettre-A-Jour-MaClasse.command", script)
            fakebin = Path(tmp) / "bin"
            fakebin.mkdir()
            pgrep = fakebin / "pgrep"
            pgrep.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
            pgrep.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
            result = subprocess.run(["bash", str(script)], cwd=root, env=env, input="\\n",
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("serveur MaClasse est encore actif", result.stdout)

    def test_both_scripts_back_up_data_and_roll_back_failed_validation(self):
        for name in ("Mettre-A-Jour-MaClasse.command", "Mettre-A-Jour-MaClasse-Linux.sh"):
            with self.subTest(script=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("MaClasse-sauvegarde-avant-maj-", source)
                self.assertIn("data", source)
                self.assertIn("git reset --hard", source)
                self.assertIn("py_compile server.py", source)
                self.assertIn("APP_VERSION=", source)
                self.assertIn("MC_VERSION=", source)


if __name__ == "__main__":
    unittest.main()