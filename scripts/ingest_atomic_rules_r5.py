#!/usr/bin/env python3
"""Atomic acceptance successor for the pasted rule excerpt; never executes source instructions."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(",",":")).encode("ascii")
raw=(ROOT/"sources/user_rules_excerpt_20261020.txt").read_bytes()
source=raw.decode("utf-8")
defs=[
("M01","mandatory","must use Band Desktop","Use actual Band Desktop.","band-runtime"),
("M02","mandatory","as the coordination layer for your agent team","Band coordinates the agent team.","band-coordination"),
("M03","mandatory","one Band room","Agents share one actual room.","band-room"),
("M04","mandatory","Two or more agents","At least two agents participate.","band-two-agents"),
("M05","mandatory","A lead or architect agent writes the plan in the room","Lead/architect writes the plan in the room.","band-plan-author"),
("M06","mandatory","One plan","Team works from one plan.","band-one-plan"),
("M07","mandatory","one board","Team uses one shared work board.","band-one-board"),
("M08","mandatory","Agents claim work items","Agents claim work items.","band-claim"),
("M09","mandatory","move them from To-do to Done","Actual task transitions include To-do and Done.","band-board-transition"),
("M10","mandatory","Agents @mention each other","Agents address each other with mentions.","band-mention"),
("M11","mandatory","pass context directly","Agents hand context directly to other agents.","band-handoff"),
("M12","mandatory","no human copy-pasting between them","Handoff succeeds without human copying.","band-no-copy-paste"),
("M13","mandatory","At least one real decision or approval","At least one real decision or approval occurs.","band-real-decision"),
("M14","mandatory","goes to the human through Band","Human receives that decision through Band.","band-human-route"),
("M15","mandatory","instead of being hard-coded","Decision is not hard-coded.","band-not-hardcoded"),
("M16","mandatory","rooms","Demo shows Band Desktop rooms.","demo-rooms"),
("M17","mandatory","the work board","Demo shows the work board.","demo-board"),
("M18","mandatory","per-agent sessions","Demo shows per-agent sessions.","demo-sessions"),
("M19","mandatory","tokens","Demo shows token counts.","demo-tokens"),
("M20","mandatory","estimated cost","Demo shows estimated costs.","demo-cost"),
("M21","mandatory","Cognee Open Source","Use Cognee Open Source.","cognee-oss"),
("M22","mandatory","as working memory","Cognee serves as working memory.","cognee-working-memory"),
("M23","mandatory","not as a static document dump","Demonstrate working memory rather than only static storage.","cognee-not-static"),
("M24","mandatory","Agents write to memory during the work","Agents write memory while doing the task.","cognee-write"),
("M25","mandatory","Agents recall from memory","Agents actually recall stored memory.","cognee-recall"),
("M26","mandatory","to change what they do next","Recalled memory changes a subsequent action.","cognee-behavior-change"),
("M27","mandatory","across a session restart or between two different agents","Demonstrate recall after restart OR between different agents; either is sufficient.","cognee-restart-or-agent"),
("M28","mandatory","must be essential to the product","BAND is essential: removing it changes required product behavior.","ablation-remove-band"),
("M29","mandatory","must be essential to the product","Cognee is essential: removing it changes required product behavior.","ablation-remove-cognee"),
("M30","mandatory","Integrations that feel like afterthoughts are grounds for disqualification","Address qualitative deep-integration review; Boolean tests alone do not guarantee qualification.","judge-deep-integration"),
("E01","scoring_enrichment","Using agents from different harnesses or frameworks","Use different agent harnesses for higher-scoring collaboration.","bonus-harness-diversity"),
("E02","scoring_enrichment","Using improve or forget, or connecting Cognee to a graph backend such as Neo4j","Demonstrate improve OR forget OR graph-backend connection; preserve this alternative choice.","bonus-cognee-enhancement"),
("F01","bonus_selected","Use Flexprice to meter real usage events","Send and read back actual usage events in Flexprice test mode.","flexprice-real-events"),
("F02","bonus_selected","turn them into a pricing model","Connect those events to a configured test pricing model.","flexprice-pricing"),
("F03","scoring_enrichment","metering drives the product","Demonstrate product behavior driven by metering.","flexprice-product-effect"),
("F04","scoring_enrichment","credits that gate features","Optional example: credits gate a feature.","flexprice-credit-gate"),
("F05","scoring_enrichment","agent costs from Band passed through to customer billing","Optional alternative example: observed BAND costs pass through to test billing.","flexprice-cost-pass-through"),
("S01","bonus_selected","Use Snyk","Use a real Snyk scanning product; alternatives are not all mandatory.","snyk-real-scan"),
("S02","bonus_selected","to scan what your agents build","Scan the exact artifact built by the agents.","snyk-target-binding"),
("S03","scoring_enrichment","security is a team member","Give security review an actual team role.","snyk-security-role"),
("S04","scoring_enrichment","a security-reviewer agent in the Band room","Security reviewer participates in the BAND room.","snyk-reviewer-room"),
("S05","scoring_enrichment","runs Snyk scans","Security reviewer runs Snyk scans.","snyk-reviewer-scan"),
("S06","scoring_enrichment","posts findings","Security reviewer posts actual findings.","snyk-post-findings"),
("S07","scoring_enrichment","blocks a work item until it's fixed","A finding actually blocks completion until a verified fix.","snyk-block-until-fixed"),
("S08","scoring_enrichment","stores recurring issues in Cognee","Store recurring issue evidence in Cognee working memory.","snyk-memory-write"),
("S09","scoring_enrichment","so the team stops repeating them","Demonstrate recalled security memory changes behavior on a repeated task.","snyk-recurrence-test"),
]
atoms=[]
for i,level,quote,requirement,test in defs:
    start=source.index(quote);end=start+len(quote)
    occurrence={"source_sha256":hashlib.sha256(raw).hexdigest(),"source_path":"sources/user_rules_excerpt_20261020.txt",
       "source_form":"ASSISTANT_TRANSCRIPTION_OF_USER_PASTED_EXCERPT_NOT_API_RAW_MESSAGE_BYTES",
       "start_codepoint":start,"end_codepoint":end,"pdf_page":3 if i[0] in ("F","S") else 2,
       "pdf_sha256":"f9c730d4c6464cdfeedb540e0d4b6080b7bfcde9fab496a1eac0dbc15b0aa1cc"}
    record={"id":"REQ-AOK-"+i,"level":level,"requirement":requirement,"source_quote":quote,"occurrence":occurrence,
       "content_sha256":hashlib.sha256(quote.encode()).hexdigest(),"context_sha256":hashlib.sha256(canonical(occurrence)).hexdigest(),
       "required_for_entry":level=="mandatory","pursued":True,"verified":False,"pass_gate":False,
       "observed_outcome":"NOT_TESTED","evidence":[],"test_id":test,"verifier_policy":"Evidence-bound independent verification; model proposal cannot set verified."}
    record["fco_candidate_sha256"]=hashlib.sha256(canonical(record)).hexdigest()
    atoms.append(record)
assert len({r["id"] for r in atoms})==len(atoms)
for a in atoms:
    o=a["occurrence"];assert source[o["start_codepoint"]:o["end_codepoint"]]==a["source_quote"]
(ROOT/"data/rules/atomic_acceptance_r5.jsonl").write_text("".join(canonical(x).decode()+"\n" for x in atoms))
doc=["# Atomic event acceptance: R5\n",
"Successor to IP-20261020-004. Each obligation has source/context identity and an explicit Boolean gate. "
"verified=false means no qualifying execution evidence yet; it does not convert NOT_TESTED/UNKNOWN into an observed failure. "
"Only the mandatory atoms gate entry. Selected bonus conditions and optional top-mark examples remain distinct. "
"An OR clause is not silently rewritten into requiring every alternative. Identical quote bytes in different requirements retain separate identities.\n",
"| Atom | Level | Independently testable requirement | Verified | Observed | Test |\n|---|---|---|---|---|---|"]
for a in atoms:doc.append(f"| {a['id']} | {a['level']} | {a['requirement']} | FALSE | NOT_TESTED | {a['test_id']} |")
doc+=["\n## Acceptance invariant\n",
"entry_gate = all(mandatory_atom.verified is True); currently FALSE. No unexecuted check may become TRUE from an LLM answer, memory recall, zero finding count, or Merkle inclusion alone.\n",
"## Required first implementation checks\n",
"Bind each test to a real BAND/Cognee/Snyk/Flexprice execution receipt, exact source/app identities, actor, context and independent verifier. Append verdict successors rather than rewriting this R5 intake snapshot.\n"]
(ROOT/".planning/ATOMIC_ACCEPTANCE_R5.md").write_text("\n".join(doc)+"\n")
fcg={"schema":"skill-custody.candidate-fcg.v1","scope":"RULE_REQUIREMENT_INTAKE_NOT_CANONICAL",
"nodes":[{"id":a["id"],"identity":a["fco_candidate_sha256"],"kind":"RequirementFCO","verified":False} for a in atoms],
"edges":[{"from":a["id"],"type":"derived_from_excerpt_occurrence","to":a["occurrence"]["source_sha256"],"context":a["context_sha256"]} for a in atoms],
"canonical_admission":"NOT_EXECUTED","relationship_semantics":"Declared source relationship, not causality"}
(ROOT/"data/rules/atomic_fcg_r5.json").write_text(json.dumps(fcg,indent=2)+"\n")
summary={"id":"IP-20261020-005-ATOMIC-INTAKE","parent":"IP-20261020-004","predecessor_commit":"735757f02e16f4638d24e4639f7e3a2f9e0bacd2",
 "atoms":len(atoms),"mandatory":sum(a["required_for_entry"] for a in atoms),"verified_true":0,
 "verified_false":len(atoms),"entry_gate":False,"observed_outcomes":{"NOT_TESTED":len(atoms)},
 "source_offsets_valid":True,"semantic_atoms_complete_for_pasted_scope":"REVIEW_REQUIRED",
 "pdf_full_line_inventory_atoms":197,"model_experiments":"NOT_EXECUTED","snyk_app_score":"NOT_COMPUTED"}
(ROOT/"receipts/ATOMIC_INTAKE_R5.json").write_text(json.dumps(summary,indent=2)+"\n")
with (ROOT/".planning/task_state.jsonl").open("a") as f:f.write(canonical(summary).decode()+"\n")
with (ROOT/".planning/decision_log.jsonl").open("a") as f:f.write(canonical({"id":"IP-20261020-005-D1","parent":"IP-20261020-004-D1","decision":"Separate requirement Boolean from observed UNKNOWN/NOT_TESTED/FAILED; complete atomic intake before integration execution."}).decode()+"\n")
print(json.dumps(summary))
