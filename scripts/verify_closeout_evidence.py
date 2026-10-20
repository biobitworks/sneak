#!/usr/bin/env python3
"""Offline source, successor and acceptance consistency verifier. Fail closed."""
from __future__ import annotations
import json,pathlib,hashlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from scripts.verify_sponsor_evidence import enc,digest,identity,merkle_root
ROOT=pathlib.Path(__file__).resolve().parents[1]
def checked(path):
 p=ROOT/path;d=json.loads(p.read_bytes())
 claim=d.pop('receipt_sha256')
 if digest(enc(d))!=claim:raise ValueError('record content hash mismatch '+str(path))
 d['receipt_sha256']=claim
 return d
def verify():
 v1_path=pathlib.Path('receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json')
 v1=checked(v1_path)
 v2=checked(pathlib.Path('receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V2_20261020.json'))
 usage=checked(pathlib.Path('receipts/flexprice/SNEAK_BAND_REAL_USAGE_UNATTRIBUTED_20261020.json'))
 ledger=checked(pathlib.Path('receipts/requirements/SNEAK_AOK_M01_M30_CLOSEOUT_20261020.json'))
 x,a=identity(v1['identity']['source_commit'])
 if a!=v1['evidence_sha256'] or x!=v1['identity']:raise ValueError('identity mismatch')
 if v2['predecessor_receipt_sha256']!=digest((ROOT/v1_path).read_bytes()):raise ValueError('predecessor byte mismatch')
 if v2['predecessor_record_sha256']!=v1['receipt_sha256']:raise ValueError('predecessor record mismatch')
 if a!=v2['evidence_sha256'] or a!=ledger['evidence_sha256']:raise ValueError('address not shared')
 if ledger['sponsor_successor_sha256']!=v2['receipt_sha256'] or ledger['real_band_usage_sha256']!=usage['receipt_sha256']:raise ValueError('successor links mismatch')
 if ledger['predecessor_baseline_sha256']!=digest((ROOT/'receipts/sneak_mvp/ATOM_STATUS_20261020.json').read_bytes()):raise ValueError('baseline mismatch')
 leaves=[{'service':n,'result':v1[n],'evidence_sha256':a} for n in ('band','cognee','snyk')]
 if v1['local_attempt_merkle']['root']!=merkle_root(leaves):raise ValueError('local attempt merkle mismatch')
 if len(ledger['records'])!=30 or any(r['acceptance_verified'] for r in ledger['records']):raise ValueError('unadmitted acceptance')
 if not v1['band']['exact_hash_found'] or not v2['cognee_exact_hash_found']:raise ValueError('partial provider hash evidence missing')
 if v1['snyk']['scan']['exit_code']==0:raise ValueError('Snyk auth successor must be reviewed')
 return {'result':'PASS_OFFLINE_CUSTODY_ONLY','shared_sha256':a,'attempt_merkle_root':v1['local_attempt_merkle']['root'],
         'band_message_id':v1['band']['message_id'],'cognee_hash_exact':v2['cognee_exact_hash_found'],
         'snyk':'FAILED_AUTHENTICATION','mandatory_accepted':0}
if __name__=='__main__':
 print(json.dumps(verify(),sort_keys=True))
