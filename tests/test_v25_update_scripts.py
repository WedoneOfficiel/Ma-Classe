import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UpdateScriptSafetyTests(unittest.TestCase):
    def test_both_update_scripts_are_valid_shell(self):
        for name in ("Mettre-A-Jour-MaClasse.command", "Mettre-A-Jour-MaClasse-Linux.sh"):
            with self.subTest(script=name):
                subprocess.run(["bash", "-n", str(ROOT / name)], check=True)

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