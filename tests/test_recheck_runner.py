import contextlib,io,json,pathlib,subprocess,tempfile,unittest
from unittest.mock import patch
from scripts import recheck_ship_gate as runner
from apps.sneak_mvp import snyk_adapter
class RecheckRunnerTests(unittest.TestCase):
 def test_two_immediate_blocked_modes_append_distinct_receipts(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td)
   subprocess.run(['git','init','-q',td],check=True)
   subprocess.run(['git','-C',td,'-c','user.name=Test','-c','user.email=test@example.com','commit','--allow-empty','-qm','fixture'],check=True)
   with patch.object(snyk_adapter,'PERSIST_DIR',root/'receipts/ship_gate'),patch.object(runner,'REPO_ROOT',root),patch('sys.argv',['recheck']),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(runner.main(),1)
   records=list((root/'receipts/ship_gate').glob('*.json'))
   self.assertEqual(len(records),2)
   self.assertEqual({json.loads(p.read_text())['mode'] for p in records},{'oss','code'})
   self.assertTrue(all(json.loads(p.read_text())['gate']=='BLOCKED' for p in records))
