"""Tests for scripts/contribution_fco.py, run inside a throwaway Git repository."""
import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/contribution_fco.py"


class ContributionFcoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fco-test-"))
        (self.tmp / "scripts").mkdir()
        shutil.copy(SCRIPT, self.tmp / "scripts/contribution_fco.py")
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "tester")
        (self.tmp / "work.py").write_text("print('hello')\n")
        self.git("add", "-A"); self.git("commit", "-qm", "seed")
        self.ledger = self.tmp / "data/contributions/fco_ledger.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.tmp), *a], check=True, capture_output=True)

    def run_tool(self, *a):
        return subprocess.run([sys.executable, str(self.tmp / "scripts/contribution_fco.py"), *a],
                              capture_output=True, text=True)

    def mint(self, *extra):
        return self.run_tool("mint", "--contributor", "jane-doe", "--kind", "code",
                             "--title", "Hello", "--path", "work.py", *extra)

    def test_mint_verify_and_stable_id(self):
        r = self.mint(); self.assertEqual(r.returncode, 0, r.stderr)
        fid = json.loads(r.stdout)["fco_id"]
        self.assertRegex(fid, r"^FCO-[0-9a-f]{16}$")
        self.assertEqual(self.run_tool("verify").returncode, 0)
        # Adding a verdict must not change the identity (RT-07).
        ev = self.tmp / "receipt.json"; ev.write_text("{}")
        s = self.run_tool("status", "--fco", fid, "--state", "SUPPORTED", "--actor", "byron", "--evidence", "receipt.json")
        self.assertEqual(s.returncode, 0, s.stderr)
        v = json.loads(self.run_tool("verify").stdout)
        self.assertTrue(v["pass"]); self.assertEqual(v["latest_state"][fid], "SUPPORTED")

    def test_duplicate_rejected(self):
        self.assertEqual(self.mint().returncode, 0)
        self.assertNotEqual(self.mint().returncode, 0)

    def test_uncommitted_path_rejected(self):
        (self.tmp / "new.py").write_text("x=1\n")
        r = self.run_tool("mint", "--contributor", "jane-doe", "--kind", "code", "--title", "x", "--path", "new.py")
        self.assertNotEqual(r.returncode, 0)

    def test_secret_rejected(self):
        fake_key = "band" + "_u_" + "123_abcdefabcdef"  # assembled so this file itself is not flagged
        (self.tmp / "leak.txt").write_text(f"key={fake_key}\n")
        self.git("add", "-A"); self.git("commit", "-qm", "leak")
        r = self.run_tool("mint", "--contributor", "jane-doe", "--kind", "doc", "--title", "x", "--path", "leak.txt")
        self.assertNotEqual(r.returncode, 0)

    def test_supported_requires_evidence(self):
        fid = json.loads(self.mint().stdout)["fco_id"]
        self.assertNotEqual(self.run_tool("status", "--fco", fid, "--state", "SUPPORTED", "--actor", "byron").returncode, 0)

    def test_parent_must_exist(self):
        self.assertNotEqual(self.mint("--parent", "FCO-0000000000000000").returncode, 0)

    def test_tampered_ledger_fails_verify(self):
        self.mint()
        lines = self.ledger.read_text().splitlines()
        rec = json.loads(lines[0]); rec["title"] = "Changed"
        lines[0] = json.dumps(rec); self.ledger.write_text("\n".join(lines) + "\n")
        self.assertNotEqual(self.run_tool("verify").returncode, 0)

    def test_changed_artifact_fails_verify(self):
        self.mint()
        lines = self.ledger.read_text().splitlines()
        rec = json.loads(lines[0]); rec["artifacts"][0]["sha256"] = "0" * 64
        lines[0] = json.dumps(rec); self.ledger.write_text("\n".join(lines) + "\n")
        self.assertNotEqual(self.run_tool("verify").returncode, 0)


if __name__ == "__main__":
    unittest.main()
