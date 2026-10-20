"use strict";
const node=(tag,text,klass)=>{const el=document.createElement(tag);if(klass)el.className=klass;el.textContent=String(text);return el};
const put=(parent,tag,text,klass)=>parent.append(node(tag,text,klass));
(async()=>{
try{
 const resp=await fetch("/data/sponsor-trace.json",{cache:"no-store"});if(!resp.ok)throw Error("Evidence snapshot unavailable");
 const x=await resp.json();
 document.querySelector("#identity").textContent="SHA-256: "+x.evidence_sha256;
 const hops=document.querySelector("#hops");
 for(const [name,statement,detail] of [
 ["Band",x.band.exact_hash_found?"OBSERVED — exact digest readback":"FAILED", "Message "+x.band.message_id+"; human API, not agent acknowledgment"],
 ["Cognee",x.cognee.exact_hash_found?"OBSERVED — separate exact digest recall":"FAILED", "Hosted Cognee retrieval; agent-owned Cognee OSS flow NOT_VERIFIED"],
 ["Snyk","FAILED — authentication", "Exact commit scan and clean-coverage score NOT_VERIFIED"],
 ["GitHub","OBSERVED — versioned candidate", "Versioned source and successor receipts; not merged to main"]
 ]){const box=node("section","","hop");put(box,"strong",name);put(box,"p",statement);put(box,"p",detail);hops.append(box)}
 document.querySelector("#custody").textContent="Local attempt Merkle root: "+x.attempt_merkle_root+"\nProject global MMR: NOT_COMPUTED\nHuman approval: NOT_OBSERVED\nSnyk: FAILED_AUTHENTICATION";
 const u=x.usage.metrics[0];document.querySelector("#usage").textContent=
 "Observed Band archive, 2026-10-20: "+Number(u.tokens).toLocaleString()+" tokens, "+u.sessions+
 " sessions; $"+Number(u.estimated_usd).toFixed(2)+" catalog equivalent. Room/agent UNATTRIBUTED; not observed SNEAK ROI. Flexprice live test: NOT_TESTED. The economics fixture remains simulated.";
 const table=document.querySelector("#requirements");
 for(const item of x.requirements){
  const tr=document.createElement("tr");
  for(const value of [item.id,item.requirement,item.attempt_evidence_status,"NO — NOT_VERIFIED",item.note])put(tr,"td",value);
  table.append(tr);
 }
}catch(e){document.querySelector("#identity").textContent="Readback FAILED: "+String(e.message)}
})();
