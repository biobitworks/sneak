#!/usr/bin/env python3
"""Create source-bound human review sheets. Does NOT change acceptance verdicts.

Existing canonical status remains 0/30 unless a new independently verified
acceptance successor is admitted. This creates a human-only annotation template.
"""
from __future__ import annotations
import hashlib, json, pathlib, re, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATUS=ROOT/"receipts/sneak_mvp/ATOM_STATUS_20261020.json"
OFFICIAL=ROOT/"docs/requirements/HACKATHON_REQUIREMENTS.md"
OUT_MD=ROOT/"docs/HUMAN_JUDGE_REQUIREMENTS_20261020.md"
OUT_JSON=ROOT/"deploy/vercel-preview/data/human-acceptance.json"
CATEGORIES=("mandatory","bonus_selected","scoring_enrichment")

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(text):return " ".join(str(text).split()).replace("|","/")
def build():
    data=json.loads(STATUS.read_text())
    atoms=data["atoms"]
    if len(atoms)!=46 or sum(x["level"]=="mandatory" for x in atoms)!=30:
        raise ValueError("acceptance baseline changed; review before generating")
    ids=[x["id"] for x in atoms]
    if len(ids)!=len(set(ids)):raise ValueError("duplicate ID")
    official=[]
    for line in OFFICIAL.read_text().splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| ID "):
            continue
        fields=[x.strip() for x in line.split("|")[1:-1]]
        if len(fields)==6 and re.fullmatch("[A-Za-z][A-Za-z0-9-]+",fields[0]):
            official.append(dict(zip(("id","classification","topic","page","evidence","source_status"),fields)))
    if len(official)!=56: raise ValueError(f"expected 56 official source rows, got {len(official)}")
    m=sum(x["level"]=="mandatory" and x["verified"] is True for x in atoms)
    # Source-anchored claims are not equivalent to actual on-device acceptance.
    review={
      "schema":"sneak.human-review-template.v1",
      "source_git_worktree":"deploy/sneak-vercel-preview-20261020",
      "baseline_status_sha256":sha(STATUS),
      "official_requirements_sha256":sha(OFFICIAL),
      "mandatory_total":30,"mandatory_verified":m,
      "total_atoms":len(atoms),"official_source_rows":len(official),
      "source_official_not_equivalent_to_46_atoms":True,
      "reference_site_status":"STATIC_SSO_PROTECTED",
      "owner_approval_does_not_equal_judge_acceptance":True,
      "requirements":[{
        "id":a["id"],"level":a["level"],
        "text":a["requirement"],"machine_observed":a.get("observed_outcome","NOT_TESTED"),
        "machine_verified":a.get("verified") is True,
        "human_review":"UNREVIEWED","reviewer":"","evidence_url":"",
        "evidence_record_id":"","human_notes":"","human_next_action":""
      } for a in atoms],
      "official_source":[{
         **x,"human_review":"UNREVIEWED","reviewer":"","evidence_url":"",
         "human_notes":""} for x in official],
      "release_gate":"BLOCKED",
      "band_planner_auth":"NOT_VERIFIED",
      "snyk_code_latest":"AUTH_ERROR",
      "snyk_open_source_latest":"DEPENDENCY_RESOLUTION_ERROR",
      "snyk_container":"NOT_TESTED",
      "optional_bonus":"NOT_VERIFIED",
      "demo_video_2_to_3_minutes":"NOT_OBSERVED",
      "production_promotion":"NOT_AUTHORIZED",
      "external_hackathon_acceptance":"NOT_OBSERVED",
      "note":"This is a review template, not a verified status receipt. Review exports require separate evidence-bound human signoff."
    }
    OUT_JSON.parent.mkdir(parents=True,exist_ok=True)
    OUT_JSON.write_text(json.dumps(review,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n")
    out=[
      "# SNEAK — human acceptance and judge readiness review",
      "",
      "**Date:** 20 October 2026. **Source:** official SF Startup Challenge problem statement intake and machine acceptance registry.",
      f"**Machine acceptance:** **{m}/30 mandatory verified**. Extra atoms: 4 selected bonus + 12 scoring enrichment, all unverified in baseline. Official source extraction: **56 separate requirement/option statements**; the inventories overlap but are **not deduplicated into 56+46 distinct obligations**.",
      "",
      "**Human instructions:** For every row, fill decision YES/NO/NEEDS_WORK/UNREVIEWED, name, dated proof link or receipt ID, and notes. Never mark a machine atom verified solely because you checked YES: a new appended, independently validated acceptance receipt is required. The deployed Vercel reviewer can export your annotations as JSON for that next step.",
      "",
      "## Evidence-to-judging translation",
      "",
      "| Judging claim | Source-bound reality | What the human must inspect |",
      "|---|---|---|",
      "| Real multi-agent collaboration in BAND | Historical Tom/Jerry room messages captured, current CLI account not authenticated | Live room, agent IDs, board actions, native mentions, message readback |",
      "| Agent memory that changes action | Cognee OSS local write and separate-process recall executed and changed deterministic gate proposal | Planner/second agent recalls memory and performs changed real task in BAND |",
      "| Merkle/MMR trust layer | Export and historical FCO/actor and question roots independently replayed | Exact receipt, algorithm, inclusion proof and tamper test |",
      "| Secure shipping | Prior Snyk Code findings remain; current CLI auth error and OSS dependency resolution failure | Exact target-commit Code/OSS report, triage, verified rescans and zero/score conditions |",
      "| Live product | Protected Vercel snapshot showing graph, heatmap and conversation lineage | Confirm rendered UI; distinguish read-only snapshot from live relay |",
      "| Flexprice bonus | Test billing API events/pricing not fully verified | Real test-mode event receipt and pricing/entitlement effect |",
      "| Submission | 2–3 minute video required by brief | Recording link, current submission URL/deadline and judge access |",
      "",
      "## Machine acceptance checklist (46 atomic rows)",
      "",
      "| ID | Level | Requirement | Machine outcome | Human decision | Reviewer | Evidence / receipt | Follow-up |",
      "|---|---|---|---|---|---|---|---|",
    ]
    for a in atoms:
        out.append("| "+ " | ".join([a["id"],a["level"],normalize(a["requirement"]),str(a.get("observed_outcome","NOT_TESTED")), "⬜ UNREVIEWED","—","—","—"])+" |")
    out+=["","## Official source extraction (56 statements — including optional, judging, bonus, setup)","",
      "| ID | Source classification | Requirement or topic | Page | Proposed evidence | Human review |",
      "|---|---|---|---|---|---|"]
    for x in official:
        out.append("| "+ " | ".join([x["id"],x["classification"],normalize(x["topic"]),x["page"],normalize(x["evidence"]),"⬜ UNREVIEWED"])+" |")
    out+=["","## Human submission signoff — fill after reviewing live evidence","",
       "Reviewer: ____________________    Reviewed at (timezone): ____________________",
       "",
       "BAND room ID: ____________________     Planner agent ID: ____________________",
       "",
       "Cognee memory dataset and readback receipt: ____________________",
       "",
       "Snyk Code/OSS exact commit and complete scan evidence: ____________________",
       "",
       "Video URL and length: ____________________    Submission/organizer confirmation: ____________________",
       "",
       "Human recommendation (not a machine PASS): ☐ HOLD  ☐ READY_FOR_JUDGES  ☐ NEEDS_REVIEW",
       "",
       "Known NOT_TESTED/UNKNOWN/ERROR evidence stays preserved. No Anticube/ΔG* or additional canonical global MMR claimed for this review sheet.",
    ]
    OUT_MD.write_text("\n".join(out)+"\n")
    return {"atoms":len(atoms),"mandatory":30,"official":len(official),"status_sha256":sha(STATUS),"source_sha256":sha(OFFICIAL),
            "markdown_sha256":sha(OUT_MD),"json_sha256":sha(OUT_JSON)}
if __name__=="__main__":print(json.dumps(build(),sort_keys=True))
