import unittest, importlib.util, pathlib, tempfile, subprocess, shutil, sys, json, hashlib
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
def fixture_repo(t):
    """Temp repo carrying a copy of the CLI so the CLI's repo root is the fixture."""
    p=pathlib.Path(t)/"repo";(p/"scripts").mkdir(parents=True)
    shutil.copy(ROOT/"scripts/custody_snapshot.py",p/"scripts/custody_snapshot.py")
    def git(*args):return subprocess.check_output(["git","-C",str(p),*args],stderr=subprocess.DEVNULL)
    git("init","-q");git("config","user.name","Test");git("config","user.email","test@example.invalid")
    (p/"d").mkdir();(p/"d/a.txt").write_text("baseline");git("add","-A");git("commit","-qm","fixture")
    (pathlib.Path(t)/"outside.txt").write_text("OUTSIDE")
    return p
def cli(repo,*args):
    return subprocess.run([sys.executable,"-I",str(repo/"scripts/custody_snapshot.py"),*args],cwd=repo,capture_output=True,text=True)
class PathContainmentTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(module,"custody snapshot verifier not implemented");self.m=module
    def test_safe_relpath_rejects(self):
        for bad in ["/etc/passwd","../x","a/../../x","a//b","./a","a/.","","a\\..\\b","caf\u00e9","a\x00b","a\nb",None,7]:
            with self.assertRaises(ValueError,msg=repr(bad)):self.m.safe_relpath(bad)
    def test_safe_relpath_accepts_tracked_paths(self):
        for rel in subprocess.check_output(["git","-C",str(ROOT),"ls-files","-z"]).decode("ascii").split("\0"):
            if rel:self.assertEqual(self.m.safe_relpath(rel),rel)
    def test_tampered_leaf_traversal_not_read(self):
        with tempfile.TemporaryDirectory() as t:
            repo=fixture_repo(t);receipt=self.m.snapshot(repo,"HEAD")
            self.assertTrue(self.m.check(repo,receipt)["pass"])
            data=b"OUTSIDE"
            for bad in ["../outside.txt",str(pathlib.Path(t)/"outside.txt"),"d/../../outside.txt"]:
                r=json.loads(json.dumps(receipt))
                r["leaves"][0]["record"]={"path":bad,"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
                out=self.m.check(repo,r)
                self.assertFalse(out["pass"]);self.assertIn("unsafe path rejected",out["errors"])
                self.assertFalse(any(bad in e for e in out["errors"]),out["errors"])
    def test_symlinked_leaf_component_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            repo=fixture_repo(t);receipt=self.m.snapshot(repo,"HEAD")
            outdir=pathlib.Path(t)/"outdir";outdir.mkdir();(outdir/"a.txt").write_text("baseline")
            shutil.rmtree(repo/"d");(repo/"d").symlink_to(outdir,target_is_directory=True)
            out=self.m.check(repo,receipt)
            self.assertFalse(out["pass"]);self.assertIn("missing/nonregular: d/a.txt",out["errors"])
    def test_snapshot_commit_option_injection_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            repo=fixture_repo(t);r=self.m.snapshot(repo,"HEAD");r["snapshot_commit"]="--output=x"
            self.assertEqual(self.m.check(repo,r)["errors"],["invalid snapshot_commit"])
    def test_cli_receipt_paths(self):
        with tempfile.TemporaryDirectory() as t:
            repo=fixture_repo(t);outside=pathlib.Path(t)
            ok=cli(repo,"create","receipts/R.json");self.assertEqual(ok.returncode,0,ok.stderr)
            ok=cli(repo,"verify","receipts/R.json");self.assertEqual(ok.returncode,0,ok.stdout+ok.stderr)
            self.assertTrue(json.loads(ok.stdout)["pass"])
            shutil.copy(repo/"receipts/R.json",outside/"evil.json")
            (outside/"linkdir").mkdir();(repo/"ln").symlink_to(outside/"linkdir",target_is_directory=True)
            for args in [("verify","../evil.json"),("verify",str(outside/"evil.json")),("verify","receipts/../../evil.json"),
                         ("create","../written.json"),("create",str(outside/"written2.json")),("create","ln/written3.json"),
                         ("verify","receipts\\R.json"),("verify","receipts/R\u00e9.json"),("create","x.json","--ref","--output=y")]:
                res=cli(repo,*args)
                self.assertEqual(res.returncode,2,(args,res.stdout,res.stderr))
            for name in ["written.json","written2.json","linkdir/written3.json"]:self.assertFalse((outside/name).exists(),name)
if __name__=="__main__":unittest.main()
