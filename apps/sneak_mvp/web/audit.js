const $=s=>document.querySelector(s);function box(t){let n=document.createElement('div');n.className='pill';n.textContent=t;return n}async function main(){try{let r=await fetch('/api/audit'),d=await r.json();if(d.error)throw Error(d.error);$('#audit-summary').append(box(`${d.mandatory_verified} / ${d.mandatory_total} mandatory verified`),box(`Entry gate: ${d.entry_gate?'OPEN':'CLOSED'}`),box(`Scan: ${d.scan.outcome}`));for(let a of d.atoms){let n=document.createElement('div');n.className='atom';for(let v of [a.id,a.requirement,a.verified?'VERIFIED':a.observed_outcome]){let c=document.createElement('span');c.textContent=v;n.append(c)}$('#atoms').append(n)}}catch(e){$('#atoms').textContent='Audit unavailable: '+e.message}}main();

const control=document.querySelector("#run-check");if(control)control.addEventListener("click",async()=>{
 const output=document.querySelector("#check-result");output.textContent="Checking read-only providers…";
 try{
  const response=await fetch("/api/check",{cache:"no-store"});const x=await response.json();
  if(!response.ok)throw Error("Check failed");
  output.textContent=JSON.stringify({
    local_import:x.source_import?.status,files:x.source_import?.file_count,
    band_account:x.band?.runtime_account,band_receipt:x.band?.status,
    cognee_oss:x.cognee?.status,cognee_band_action:x.cognee?.band_action_dispatch,
    snyk:x.snyk?.status,snyk_current:x.snyk?.target_current_and_clean,
    security_gate:x.snyk?.gate,flexprice:x.flexprice?.status,release_gate:x.release_gate},null,2);
 }catch(e){output.textContent="Check failed: "+e.message}
});
