"""Regression tests for formerly tainted path/executable sources."""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.scanner import resolve_snyk_cli
from sneak.secrets import load_secret_file


class SecurityHardeningTests(unittest.TestCase):
    def test_env_scanner_executable_override_does_not_apply(self):
        with tempfile.TemporaryDirectory() as td:
            rogue = pathlib.Path(td) / "rogue-executable"
            rogue.write_text("#!/bin/sh\n")
            with patch.dict(os.environ, {"SNYK_CLI": str(rogue)}):
                self.assertNotEqual(resolve_snyk_cli(), str(rogue))

    def test_env_secret_file_override_does_not_apply(self):
        with tempfile.TemporaryDirectory() as td:
            rogue = pathlib.Path(td) / "providers.env"
            rogue.write_text("EXAMPLE_SHOULD_NOT_LOAD=not-a-real-key\n")
            with patch.dict(os.environ, {"SNEAK_SECRETS_FILE": str(rogue)}):
                self.assertNotIn("EXAMPLE_SHOULD_NOT_LOAD", load_secret_file())

    def test_python_snapshot_traversal_argument_rejected(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "custody_snapshot.py"),
                                 "verify", "../../etc/passwd"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt must be", result.stderr)

    def test_node_snapshot_traversal_argument_rejected(self):
        if not __import__("shutil").which("node"):
            self.skipTest("node not installed")
        result = subprocess.run(["node", str(ROOT / "scripts" / "verify_custody_snapshot.mjs"),
                                 "../../etc/passwd"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt argument", result.stderr)


if __name__ == "__main__":
    unittest.main()
