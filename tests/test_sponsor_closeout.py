import unittest
from scripts import verify_closeout_evidence as V
class CloseoutTests(unittest.TestCase):
 def test_replay(self):
  self.assertEqual(V.verify()['result'],'PASS_OFFLINE_CUSTODY_ONLY')
 def test_readonly_source(self):
  x=V.verify()
  self.assertEqual(len(x['shared_sha256']),64)
  self.assertEqual(x['mandatory_accepted'],0)
