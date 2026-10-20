"use strict";
const target=id=>document.getElementById(id);
const elem=(tag,value)=>{const e=document.createElement(tag);if(value!==undefined)e.textContent=String(value);return e};
function table(container,headers,rows){
  const t=elem("table"),head=elem("thead"),h=elem("tr");
  headers.forEach(x=>h.appendChild(elem("th",x)));head.appendChild(h);t.appendChild(head);
  const b=elem("tbody");rows.forEach(row=>{const tr=elem("tr");row.forEach(x=>tr.appendChild(elem("td",x)));b.appendChild(tr)});t.appendChild(b);container.appendChild(t)
}
async function load(){
  const response=await fetch("/data/roi-demo.json",{cache:"no-store"});
  if(!response.ok)throw Error("ROI trial snapshot unavailable");
  const x=await response.json();
  if(x.status!=="SIMULATED_NOT_OBSERVED"||x.live_flexprice_metering!=="NOT_TESTED")throw Error("Unexpected evidence classification; refusing to display ROI");
  const m=x.metrics;
  const f=v=>Number(v).toFixed(4);
  const metrics=target("metrics");
  table(metrics,["Scenario","Tokens","Human minutes (assumed)","Token cost USD (assumed)","Human cost USD (assumed)","Total cost USD (assumed)"],[
    ...["baseline","sneak"].map(k=>[k,m[k].tokens,m[k].human_minutes,f(m[k].token_usd),f(m[k].human_usd),f(m[k].total_usd)])
  ]);
  metrics.appendChild(elem("p","SIMULATED token reduction: "+(Number(x.token_reduction_fraction)*100).toFixed(2)+"%; simulated cost reduction: "+(Number(x.estimated_cost_reduction_fraction)*100).toFixed(2)+"%. Neither figure is an observed product result."));
  for(const [key,name] of [["agents","Agent"],["models","Model"],["humans","Human pseudonym"]]){
    const c=target("groups");c.appendChild(elem("h3",name));
    const rows=[];
    for(const scenario of ["baseline","sneak"]){
      for(const [id,val] of Object.entries(m[scenario][key]))rows.push([scenario,id,val.tokens,val.human_minutes,f(val.estimated_total_usd)]);
    }
    table(c,["Scenario",name,"Tokens","Human minutes","Total estimated USD"],rows)
  }
  target("status").textContent="Trial="+x.status+"; live Flexprice="+x.live_flexprice_metering+"; real-world ROI="+x.claim_not_supported+"; ledger MMR="+x.global_merkle_root+"; receipt SHA-256="+x.receipt_sha256;
}
load().catch(e=>{target("status").textContent="FAILED: "+e.message});
