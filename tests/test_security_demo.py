import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/security-demo/src"))

from security_demo import healthcheck
from security_demo.review import review_skill_manifest


class SecurityDemoTests(unittest.TestCase):
    def test_healthcheck(self):
        h = healthcheck()
        self.assertEqual(h["status"], "ok")

    def test_refuses_exec_tools(self):
        out = review_skill_manifest({"name": "x", "tools": ["exec:rm"]})
        self.assertEqual(out["decision"], "refuse")

    def test_summarizes_safe(self):
        out = review_skill_manifest({"name": "x", "tools": ["search"]})
        self.assertEqual(out["decision"], "summarize")


if __name__ == "__main__":
    unittest.main()
