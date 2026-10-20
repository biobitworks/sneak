import unittest
from scripts import build_vercel_preview as preview

class ShipProjectionTests(unittest.TestCase):
 def test_error_never_looks_like_zero_findings(self):
  graph,_=preview.snapshot()
  self.assertEqual(graph['scan']['outcome'],'ERROR')
  self.assertIsNone(graph['scan']['finding_count'])
  self.assertIsNone(graph['scan']['severity_counts'])
  self.assertEqual(graph['scan']['security_app_score'],'NOT_COMPUTED')
