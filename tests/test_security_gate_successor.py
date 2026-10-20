import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sneak.security_gate import gate, summarize_sast

class SecurityGateTest(unittest.TestCase):
    def test_scan_error_deny(self):
        self.assertEqual(gate(2,0)["decision"],"DENY")
        self.assertEqual(gate(0,3)["reason"],"SCAN_ERROR_OR_UNSUPPORTED")
    def test_no_scan_report_denied(self):
        self.assertEqual(gate(0,0)["reason"],"SAST_REPORT_MISSING")
    def test_positive_result_denied(self):
        sarif={"runs":[{"results":[{"ruleId":"python/PT","level":"note"}]}]}
        self.assertEqual(summarize_sast(sarif)["finding_count"],1)
        self.assertEqual(gate(1,0,sarif)["decision"],"DENY")
    def test_no_findings_not_automatic_admission(self):
        sarif={"runs":[{"results":[]}]}
        self.assertEqual(gate(0,0,sarif)["decision"],"PENDING")
    def test_invalid_sarif_rejected(self):
        with self.assertRaises(ValueError):
            summarize_sast({})
if __name__=="__main__": unittest.main()
