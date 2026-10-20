#!/usr/bin/env python3
"""Refresh source-bound PR inventory, preserving all unmerged lanes for human review."""
import datetime,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
PRJSON=ROOT/"local-runs/gh_pr_registry_20261020.json"
OUT=ROOT/"docs/PR_LANES_REVIEW_20261020.md"
RC=ROOT/"receipts/pr_status/SNEAK_PR_LANES_20261020.json"

def canon(obj):return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(["git","-C",str(ROOT),*args],text=True).strip()
def run():
  prs=sorted(json.loads(PRJSON.read_text()),key=lambda p:p["number"])
  if len(prs)<14:raise ValueError("PR inventory unexpectedly incomplete")
  remote={}
  for row in git("for-each-ref","--format=%(refname:short) %(objectname)","refs/remotes/origin").splitlines():
    name,commit=row.split(" ",1)
    remote[name[7:]]=commit
  if not remote.get("main"):raise ValueError("missing tracked origin/main")
  rows=[]
  for p in prs:
    head=p["headRefName"]
    sha_head=remote.get(head,"UNKNOWN")
    if sha_head=="UNKNOWN":raise ValueError(f"PR head untracked: {head}")
    rows.append({
      "number":p["number"],"title":p["title"],"state":p["state"],
      "draft":bool(p["isDraft"]),"head":head,"base":p["baseRefName"],
      "head_sha":sha_head,"url":p["url"],
      "human_review":"UNREVIEWED","human_reviewer":"","human_evidence":"",
      "decision":"KEEP_DRAFT_FOR_REVIEW" if p["state"]=="OPEN" else "MERGED_HISTORICAL",
      "merge_authorized":False if p["state"]=="OPEN" else None,
    })
  merged=[r for r in rows if r["state"]=="MERGED"]
  active=[r for r in rows if r["state"]=="OPEN"]
  if any(not x["draft"] for x in active):
    raise ValueError("non-draft PR present: human gate not satisfied")
  record={
    "schema":"sneak.pr-lanes-human-review.v1",
    "snapshot_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_gh_snapshot_sha256":sha(PRJSON.read_bytes()),
    "main_git_sha":remote["main"],"count_total":len(rows),
    "count_merged":len(merged),"count_draft":len(active),
    "local_worktrees_checked":["magicPRObox", "magicSTUDIObox"],
    "source_branch_heads":remote,
    "pull_requests":rows,
    "closure_decision":"NO_CLOSURES_WITHOUT_DUPLICATE_OR_SUPERSEDED_EVIDENCE",
    "unmerged_merge_permission":"NOT_GRANTED",
    "external_acceptance":"NOT_VERIFIED",
    "whole_project_mmr":"NOT_COMPUTED"
  }
  RC.parent.mkdir(parents=True,exist_ok=True)
  if RC.exists():
    raise ValueError("Existing source snapshot receipt; use a new successor instead")
  RC.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
  d=[
    "# SNEAK — GitHub branch/PR review for humans",
    "",
    f"**Snapshot:** {record['snapshot_at_utc']} · **Repository:** private biobitworks/sneak",
    f"**PRs:** {len(rows)} observed, {len(active)} open draft, {len(merged)} merged. No unauthorized merges/closures. All branch heads below are observed origin refs, not claims that integration tests passed.",
    "",
    "## Review queue and evidence gates",
    "",
    "| PR | Lane | Base | State | Head SHA | Human decision | Reviewer / source-proof URL |",
    "|---|---|---|---|---|---|---|",
  ]
  for r in rows:
    status=("MERGED" if r["state"]=="MERGED" else "DRAFT")
    d.append(f"| [#{r['number']}]({r['url']}) | `{r['head']}` | `{r['base']}` | {status} | `{r['head_sha'][:12]}` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |")
  d+=["","## Owner review before any merge or close","",
       "1. Check the PR diff, exact HEAD, tests, provenance and security scan for that HEAD; list any merge-base conflicts.",
       "2. Preserve FAILED, NEGATIVE, NULL, NOT_TESTED and NOT_COMPUTED predecessor artifacts; a branch's root is not a universal global root.",
       "3. For merge: independently verify matching acceptance atoms, source rights, Snyk Code/OSS coverage and owner approval. Do not merge stacked dependencies out of order.",
       "4. For close: cite exact duplicate/superseding PR and retained commits/receipts. No PR has been closed by this snapshot.",
       "5. Reconcile private devices separately. Local magicPRObox main remains diverged; do not force-push origin/main. Custody change is preserved on its own branch.",
       "",
       "## Status that is not PR readiness",
       "",
       "The 30 mandatory hackathon atoms remain unverified in the existing registry. BAND live planner room authorization and board transitions remain unverified. Cognee OSS local write/read and read-only Vercel rendering passed in bounded receipts. Snyk Code and OSS are blocked by authentication/dependency errors; Flexprice billing evidence remains incomplete. The user authorized development, not an organizer award.",
       "",
       "## Source identity",
       "",
       f"GitHub PR listing bytes SHA-256: `{record['source_gh_snapshot_sha256']}`.",
       f"GitHub main tracked commit: `{record['main_git_sha']}`.",
       "PR states may have changed after the snapshot; use a new dated audit before relying on it.",
  ]
  OUT.write_text("\n".join(d)+"\n")
  print(canon({"prs":len(rows),"draft":len(active),"merged":len(merged),"markdown":str(OUT),"receipt":str(RC)}))
if __name__=="__main__":run()
