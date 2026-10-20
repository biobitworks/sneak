#!/usr/bin/env python3
"""Append verified successor for one address and 30-atom evidence acceptance ledger."""
from __future__ import annotations
import hashlib,json,os,pathlib,subprocess,urllib.request,urllib.error,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from scripts.verify_sponsor_evidence import enc,digest
ROOT=pathlib.Path(__file__).resolve().parents[1]
V1=ROOT/'receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json'
V2=ROOT/'receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V2_20261020.json'
LEDGER=ROOT/'receipts/requirements/SNEAK_AOK_M01_M30_CLOSEOUT_20261020.json'
USAGE=ROOT/'receipts/flexprice/SNEAK_BAND_REAL_USAGE_UNATTRIBUTED_20261020.json'
SOURCE=ROOT/'receipts/sneak_mvp/ATOM_STATUS_20261020.json'
def add_once(path,obj):
 if path.exists():raise RuntimeError('refuse to overwrite '+str(path))
 path.parent.mkdir(parents=True,exist_ok=True)
 obj['receipt_sha256']=digest(enc(obj))
 path.write_bytes(enc(obj)+b'\n')
def followup():
 p=json.loads(V1.read_text());address=p['evidence_sha256']
 headers={'X-Api-Key':os.environ['COGNEE_API_KEY'],'Content-Type':'application/json'}
 responses=[]
 for typ in ('CHUNKS_LEXICAL','CHUNKS'):
  obj={'query':address,'searchType':typ,'datasets':['sneak_working_memory']}
  req=urllib.request.Request('https://tenant-4ee605b3-4511-4496-bc8a-d9ee322fd30e.aws.cognee.ai/api/v1/search',
         headers=headers,data=enc(obj),method='POST')
  try:
   with urllib.request.urlopen(req,timeout=20) as r:
    raw=r.read()
    responses.append({'search_type':typ,'http_code':r.status,'response_sha256':digest(raw),
                     'exact_hash_found':address.encode() in raw})
  except urllib.error.HTTPError as e:
   raw=e.read();responses.append({'search_type':typ,'http_code':e.code,'response_sha256':digest(raw),'exact_hash_found':False})
 result={'schema':'sneak.sponsor-traversal.successor.v2','predecessor_receipt_sha256':digest(V1.read_bytes()),
     'predecessor_record_sha256':p['receipt_sha256'],'evidence_sha256':address,
     'band_message_id':p['band'].get('message_id'),'band_exact_hash_found':p['band'].get('exact_hash_found',False),
     'cognee_separate_query':responses,'cognee_exact_hash_found':any(r['exact_hash_found'] for r in responses),
     'snyk_exact_target_scan':'FAILED_AUTHENTICATION','snyk_sca':'NOT_TESTED',
     'same_hash_traversal_to_snyk':'NOT_VERIFIED',
     'agent_ack':'NOT_OBSERVED','human_approval':'NOT_OBSERVED','global_mmr':'NOT_COMPUTED',
     'verdict':'PARTIAL_VERIFIED_BAND_AND_COGNEE_ONLY' if p['band'].get('exact_hash_found') and any(r['exact_hash_found'] for r in responses) else 'FAILED'}
 add_once(V2,result)
 return result
def usage():
 cp=subprocess.run(['band','usage','rooms','--since','2026-10-20','--until','2026-10-20','--json'],
                    capture_output=True,timeout=25)
 if cp.returncode: raise RuntimeError('Band usage capture FAILED')
 src=json.loads(cp.stdout)
 summary={'schema':'sneak.band-usage-observed-unattributed.v1','source':'band CLI 0.4.16 usage rooms',
          'captured_stdout_sha256':digest(cp.stdout),'date':'2026-10-20',
          'metrics':[],'attribution':'UNATTRIBUTED_NOT_SNEAK_ROI','pricing':'CATALOG_ESTIMATE_NOT_INVOICE',
          'baseline_comparison':'NOT_COMPUTED'}
 for x in src:
  summary['metrics'].append({'room_known':bool(x.get('room')),'tokens':x.get('tokens'),
       'sessions':x.get('sessions'),'estimated_usd':x.get('totalCost')})
 add_once(USAGE,summary)
 return summary
def ledger(v2,us):
 raw=json.loads(SOURCE.read_text())
 source_id=digest(SOURCE.read_bytes())
 attempts={'REQ-AOK-M01':('FAILED','Band CLI account unavailable; human API distinct'),
 'REQ-AOK-M03':('OBSERVED','Band live room and participant registry (agent activity not observed)'),
 'REQ-AOK-M04':('NOT_OBSERVED','Room contains agents but participation is inactive/unverified'),
 'REQ-AOK-M10':('PARTIAL','Human API mention payload succeeded; agent-owned mentions not attested'),
 'REQ-AOK-M11':('PARTIAL','Human API handoff delivered; no agent to agent handoff observed'),
 'REQ-AOK-M12':('NOT_OBSERVED','Automated agent-owned independent handoff not proven'),
 'REQ-AOK-M19':('PARTIAL','Band historical real token usage exists, not native judge demo per-agent sessions'),
 'REQ-AOK-M20':('PARTIAL','Band estimates exist but are unattributed, not demonstrated per agent'),
 'REQ-AOK-M21':('PARTIAL','Earlier local Cognee OSS receipt; current live probe is hosted Cognee, not OSS'),
 'REQ-AOK-M22':('PARTIAL','Hosted add+cognify+separate hash search; agent use unproven'),
 'REQ-AOK-M23':('NOT_VERIFIED','Memory retrieval observed; behavior change under live multi-agent conditions not proven'),
 'REQ-AOK-M24':('NOT_OBSERVED','Human probe writes memory, not agent task execution'),
 'REQ-AOK-M25':('NOT_OBSERVED','Independent script queries; not agent-initiated recall'),
 'REQ-AOK-M26':('NOT_OBSERVED','No observed agent behavior change'),
 'REQ-AOK-M27':('PARTIAL','Separate-process historical OSS recall exists; does not establish agent execution in same room')}
 records=[]
 for row in raw['atoms']:
  if row['level']!='mandatory':continue
  id=row['id']; st,note=attempts.get(id,('NOT_TESTED','No new acceptance-bound execution receipt inspected'))
  records.append({'id':id,'requirement':row['requirement'],'predecessor_verified':row['verified'],
      'predecessor_outcome':row.get('observed_outcome'),'attempt_evidence_status':st,
      'acceptance_verified':False,'note':note,'evidence':['SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json','SNEAK_SPONSOR_TRAVERSAL_V2_20261020.json'] if id in attempts else []})
 v={'schema':'sneak.requirement-attempt-snapshot.v1','predecessor_baseline_sha256':source_id,
    'evidence_sha256':v2['evidence_sha256'],'sponsor_successor_sha256':v2['receipt_sha256'],
    'real_band_usage_sha256':us['receipt_sha256'],'acceptance_policy':'NEVER_INFER_FROM_GRAPH_EDGES',
    'mandatory_count':len(records),'acceptance_verified_count':sum(x['acceptance_verified'] for x in records),
    'review_status':'HUMAN_SIGNOFF_PENDING','records':records}
 add_once(LEDGER,v)
 return v
if __name__=='__main__':
 v=followup();u=usage();r=ledger(v,u)
 print(json.dumps({'evidence_sha256':v['evidence_sha256'],'band_hash_verified':v['band_exact_hash_found'],
    'cognee_hash_verified':v['cognee_exact_hash_found'],'snyk':'FAILED_AUTHENTICATION',
    'accepted_mandatory':r['acceptance_verified_count'],'atoms':r['mandatory_count'],
    'successor_sha256':v['receipt_sha256'],'ledger_sha256':r['receipt_sha256'],
    'usage':u['metrics']}))
