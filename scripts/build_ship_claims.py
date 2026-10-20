#!/usr/bin/env python3
"""Append-only claim audit and static review page. Does not contact providers."""
import hashlib,html,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
PARENT='517f630866834ddbe2e4dcee74f1213271055bbc'
ID='SNEAK-SHIP-GATE-R1-20261020'
def build(source_commit):
 from scripts.verify_closeout_evidence import verify
 result=verify()
 trace=json.loads((ROOT/'deploy/vercel-preview/data/sponsor-trace.json').read_text())
 original=json.loads((ROOT/'receipts/sneak_mvp/AOK_MVP_20261020.json').read_text())
 claims=[
  {'claim':'Snyk clean scan / score zero','status':'FAILED','where':'receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json → snyk.scan','evidence':'Exit 2 authentication failure; findings UNKNOWN; security app score NOT_COMPUTED. SCA and Code coverage of successor NOT_TESTED.'},
  {'claim':'History actor','status':'IMPLEMENTED','where':'apps/sneak_mvp/web/app.js; scripts/build_vercel_preview.py','evidence':'Export intentionally removes actor; UI now displays source or UNKNOWN. Regression test executed. All predecessor actions shown.'},
  {'claim':'Band exact digest','status':'SUPPORTED','where':'receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json → band','evidence':'Stored receipt digest and linkage verified offline; live provider recheck NOT_TESTED this turn. Human API readback does not establish autonomous participation.'},
  {'claim':'Cognee exact digest','status':'SUPPORTED','where':'receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V2_20261020.json','evidence':'Separate hosted search recorded; custody reverified offline. Agent-owned OSS recall and behavior change NOT_VERIFIED.'},
  {'claim':'Human decision','status':'NOT_TESTED','where':'EV-020-HUMAN-DECISION','evidence':'No actual decision receipt verified. Original event retained.'},
  {'claim':'EV-030 / EV-040 proposal status','status':'PROPOSED','where':'receipts/sneak_mvp/AOK_MVP_20261020.json','evidence':'Historical proposal leaves unchanged. Later hosted Cognee receipt and Snyk failure are separate attempt evidence on /trace.'},
  {'claim':'Mandatory acceptance','status':'NEGATIVE','where':'receipts/requirements/SNEAK_AOK_M01_M30_CLOSEOUT_20261020.json','evidence':'0 of 30 accepted. Every source requirement and blocker is listed below.'},
  {'claim':'Measured savings / Flexprice','status':'NOT_TESTED','where':'receipts/flexprice/SNEAK_BAND_REAL_USAGE_UNATTRIBUTED_20261020.json','evidence':'Historical token usage is UNATTRIBUTED_NOT_SNEAK_ROI; economics fixture simulated. Live Flexprice billing NOT_TESTED.'},
  {'claim':'Merkle / MMR','status':'SUPPORTED','where':'scripts/verify_closeout_evidence.py; data/export-custody.json','evidence':'Local attempt custody replay passes. Export roots apply only to declared static file bytes. Project/model global MMR, Anticube and delta G*: NOT_COMPUTED.'},
  {'claim':'Live application / production release','status':'DEFERRED','where':'Vercel project sneak-evidence-preview','evidence':'Protected static projection; target preview. Live APIs false. Production release remains BLOCKED.'},
  {'claim':'Public judge repository','status':'NEGATIVE','where':'GitHub repository metadata','evidence':'biobitworks/sneak is private; no visibility change authorized or executed.'},
 ]
 data={'schema':'sneak.ship-claims.v1','id':ID,'parent_commit':PARENT,'source_commit':source_commit,
       'scope':'OFFLINE_RECEIPT_AUDIT_AND_STATIC_UI_FIX','live_provider_recheck':'NOT_TESTED',
       'gate':'BLOCKED','security_app_score':'NOT_COMPUTED','claims':claims,
       'custody_replay':result,'requirements':trace['requirements'],
       'historical_events':[{'id':x['record']['id'],'status':x['record']['status']} for x in original['leaves']]}
 out=ROOT/'receipts/ship_gate'/f'{ID}.json'
 encoded=(json.dumps(data,sort_keys=True,indent=2)+'\n').encode()
 if out.exists() and out.read_bytes()!=encoded:raise ValueError('refusing predecessor overwrite')
 out.parent.mkdir(exist_ok=True);out.write_bytes(encoded)
 md=['# SNEAK ship gate audit',f'ID: {ID}; parent: `{PARENT}`; source: `{source_commit}`.',
     'Gate: **BLOCKED**. Custody replay executed; live providers NOT_TESTED this turn.',
     '| Claim | Status | Failure/evidence location | Interpretation |','|---|---|---|---|']
 for c in claims:md.append('| '+' | '.join(c[k] for k in ('claim','status','where','evidence'))+' |')
 md+=['','Run on a clean authenticated checkout:','```bash','snyk auth','python scripts/recheck_ship_gate.py --allow-code-upload','python scripts/verify_closeout_evidence.py','```',
      'The scan runner appends new receipts after both scans; it never promotes a deployment. Scan PASS does not establish score zero or sponsor acceptance. The historical verifier audits the preserved attempt, not a later live rescan.',
      '','| Requirement | Attempt | Blocker |','|---|---|---|']
 for r in trace['requirements']:md.append(f"| {r['id']} — {r['requirement']} | {r['attempt_evidence_status']} | {r['note']} |")
 report=ROOT/'docs'/f'{ID}.md';report.write_text('\n'.join(md)+'\n')
 esc=lambda x:html.escape(str(x))
 page=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SNEAK | Ship gate claims</title><link rel="stylesheet" href="/static/style.css"><main><nav><a href="/">SNEAK</a> | <a href="/trace">Sponsor trace</a> | <a href="/audit">Audit</a></nav><h1>Ship gate: BLOCKED</h1><p>Offline receipts checked; live providers NOT_TESTED this turn. Security app score NOT_COMPUTED.</p>',f'<p>Successor {ID}; parent {PARENT}; source {esc(source_commit)}</p>','<h2>Claims and failure locations</h2>']
 for c in claims:page.append('<section><h3>'+esc(c['claim'])+' · '+esc(c['status'])+'</h3><p>'+esc(c['where'])+'</p><p>'+esc(c['evidence'])+'</p></section>')
 page+=['<h2>Run the authentication remediation in the scan runner</h2><pre>snyk auth\npython scripts/recheck_ship_gate.py --allow-code-upload</pre><p>The script requires a clean checkout, appends receipts, and never releases production.</p><h2>Mandatory requirements: 0 / 30 accepted</h2>']
 for r in trace['requirements']:page.append('<section><h3>'+esc(r['id']+' · '+r['attempt_evidence_status'])+'</h3><p>'+esc(r['requirement'])+'</p><p>'+esc(r['note'])+'</p></section>')
 page.append('</main></html>')
 (ROOT/'deploy/vercel-preview/claims.html').write_text('\n'.join(page))
 (ROOT/'deploy/vercel-preview/data/ship-claims.json').write_bytes(encoded)
 return {'id':ID,'receipt_sha256':hashlib.sha256(encoded).hexdigest(),'claims':len(claims),'requirements':len(trace['requirements'])}
