import unittest, importlib.util, pathlib, tempfile, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("custody",ROOT/"scripts/custody_snapshot.py")
module=None
if spec and spec.loader and pathlib.Path(spec.origin).exists():
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class CustodyTests(unittest.TestCase):
    def require(self):
        self.assertIsNotNone(module,"custody snapshot verifier not implemented")
        return module
    def test_canonical_bytes(self):
        m=self.require();self.assertEqual(m.canonical({"size_bytes":1,"path":"a","sha256":"b"}),b'{"path":"a","sha256":"b","size_bytes":1}')
    def test_all_proofs(self):
        m=self.require();xs=[m.leaf({"id":i}) for i in range(5)]
        for i in range(5):self.assertTrue(m.verify(xs[i],m.proof(xs,i),m.root(xs)))
    def test_tamper_rejected(self):
        m=self.require();xs=[m.leaf({"id":i}) for i in range(3)]
        self.assertFalse(m.verify(m.leaf({"id":9}),m.proof(xs,0),m.root(xs)))
    def test_invalid_side_rejected(self):
        m=self.require();x=m.leaf({"id":1})
        self.assertFalse(m.verify(x,[{"side":"unknown","hash":"00"*32}],x))
    def test_single_leaf(self):
        m=self.require();x=m.leaf({"id":1});self.assertEqual(m.root([x]),x)
    def test_leaf_removal_changes_root(self):
        m=self.require();xs=[m.leaf({"id":i}) for i in range(3)]
        self.assertNotEqual(m.root(xs),m.root(xs[:-1]))
    def test_empty_rejected(self):
        m=self.require()
        with self.assertRaises(ValueError):m.root([])
    def test_committed_and_working_bytes_checked(self):
        m=self.require()
        with tempfile.TemporaryDirectory() as t:
            p=pathlib.Path(t)
            def git(*args):return subprocess.check_output(["git","-C",t,*args],stderr=subprocess.DEVNULL)
            git("init","-q");git("config","user.name","Test");git("config","user.email","test@example.invalid")
            (p/"a.txt").write_text("baseline");git("add","a.txt");git("commit","-qm","fixture")
            receipt=m.snapshot(p,"HEAD")
            self.assertTrue(m.check(p,receipt)["pass"])
            (p/"a.txt").write_text("tampered")
            self.assertFalse(m.check(p,receipt)["pass"])
if __name__=="__main__":unittest.main()
