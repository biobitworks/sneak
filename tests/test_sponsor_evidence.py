import hashlib,unittest
from scripts import verify_sponsor_evidence as V
class SponsorProof(unittest.TestCase):
 def test_hash_determinism(self):
  i,a=V.identity('ab'*20)
  self.assertEqual(a,V.digest(V.enc(i)))
  self.assertEqual(a,V.identity('ab'*20)[1])
 def test_source_commit_changes_address(self):
  self.assertNotEqual(V.identity('ab'*20)[1],V.identity('cd'*20)[1])
 def test_proof_is_exact(self):
  a=V.identity('ab'*20)[1]
  self.assertTrue(V.find_exact_hash({'data':a},a))
  self.assertFalse(V.find_exact_hash({'data':a[:-1]+'0'},a) if a[-1]!='0' else V.find_exact_hash({'data':a[:-1]+'1'},a))
 def test_merkle_differs_on_tamper(self):
  x=[{'kind':'band','status':'ok'},{'kind':'cognee','status':'error'},{'kind':'snyk','status':'noauth'}]
  y=[*x];y[1]={'kind':'cognee','status':'ok'}
  self.assertNotEqual(V.merkle_root(x),V.merkle_root(y))
