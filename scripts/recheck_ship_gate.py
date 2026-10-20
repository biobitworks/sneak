#!/usr/bin/env python3
"""Run both authenticated scan modes on a clean checkout; append evidence, never release.

First authenticate in this runner using `snyk auth` or a protected SNYK_TOKEN.
Run: python scripts/recheck_ship_gate.py --allow-code-upload
Exit 0 means both scan gates passed, NOT sponsor acceptance or app-score zero.
"""
import argparse
import json
import pathlib
import sys
import threading
import uuid
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from apps.sneak_mvp import REPO_ROOT
from apps.sneak_mvp.snyk_adapter import bind_target, run_scan

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--allow-code-upload', action='store_true')
 args=ap.parse_args()
 binding=bind_target(REPO_ROOT)
 if binding['dirty']:
  print('FAIL: dirty checkout; commit scoped work before scanning. No scan executed.')
  return 1
 print('START: OSS and Code scans; credentials are never printed.', flush=True)
 receipts=[]
 for mode in ('oss','code'):
  print('RUNNING: '+mode, flush=True)
  stop=threading.Event()
  def heartbeat():
   while not stop.wait(20):
    print("RUNNING: "+mode+" scan pending",flush=True)
  worker=threading.Thread(target=heartbeat,daemon=True);worker.start()
  try:
   receipt=run_scan(REPO_ROOT,mode=mode,allow_code_upload=args.allow_code_upload)
  finally:
   stop.set();worker.join()
  receipts.append(receipt)
  print(json.dumps({'mode':mode,'gate':receipt['gate'],'outcome':receipt['outcome'],
                    'reason':receipt.get('reason'),'exit_code':receipt.get('exit_code')}),flush=True)
 # Persist after BOTH scans, so receipt writes cannot dirty the second scan target.
 for receipt in receipts:
  out=REPO_ROOT/'receipts/ship_gate'
  out.mkdir(parents=True,exist_ok=True)
  path=out/('SNYK_'+receipt['mode']+'_'+uuid.uuid4().hex+'.json')
  with path.open('x') as f:
   f.write(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
  print('Receipt: '+str(path.relative_to(REPO_ROOT)))
 passed=all(r['gate']=='PASS' for r in receipts)
 print(json.dumps({'result':'PASS_SCANS_ONLY' if passed else 'FAIL_BLOCKED',
   'commit':binding['commit'],'security_app_score':'NOT_COMPUTED',
   'mandatory_acceptance':'NOT_VERIFIED','release':'NOT_EXECUTED'}))
 return 0 if passed else 1

if __name__=='__main__':
 sys.exit(main())
