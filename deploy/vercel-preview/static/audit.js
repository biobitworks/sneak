"use strict";
const $ = (selector) => document.querySelector(selector);

function textElement(tag, cls, value) {
  const element = document.createElement(tag);
  if (cls) element.className = cls;
  element.textContent = String(value ?? "");
  return element;
}

async function loadAudit() {
  const target = $("#atoms");
  try {
    const response = await fetch("/api/audit", {cache:"no-store"});
    const data = await response.json();
    if (!response.ok || data.error) throw new Error("Audit unavailable");
    const summary = $("#audit-summary");
    summary.appendChild(textElement("div","pill",data.mandatory_verified+" / "+data.mandatory_total+" mandatory verified"));
    summary.appendChild(textElement("div","pill","Entry gate: "+(data.entry_gate?"OPEN":"CLOSED")));
    summary.appendChild(textElement("div","pill","Scan: "+(data.scan?.outcome ?? "NOT_RUN")));
    for (const atom of data.atoms ?? []) {
      const row = document.createElement("div");
      row.className = "atom";
      for (const value of [atom.id, atom.requirement, atom.verified?"VERIFIED":atom.observed_outcome]) {
        row.appendChild(textElement("span",null,value));
      }
      target.appendChild(row);
    }
  } catch (error) {
    target.textContent = "Audit unavailable; read-only service check failed.";
  }
}

async function liveCheck() {
  const output = $("#check-result");
  output.textContent = "Checking read-only providers…";
  try {
    const response = await fetch("/api/check", {cache:"no-store"});
    const state = await response.json();
    if (!response.ok) throw new Error("Check failed");
    const safe = {
      local_import:state.source_import?.status,
      files:state.source_import?.file_count,
      band_account:state.band?.runtime_account,
      band_receipt:state.band?.status,
      cognee_oss:state.cognee?.status,
      cognee_band_action:state.cognee?.band_action_dispatch,
      snyk:state.snyk?.status,
      snyk_current:state.snyk?.target_current_and_clean,
      security_gate:state.snyk?.gate,
      flexprice:state.flexprice?.status,
      release_gate:state.release_gate
    };
    output.textContent = JSON.stringify(safe,null,2);
  } catch (error) {
    output.textContent = "Read-only check unavailable.";
  }
}

const control = $("#run-check");
if (control) control.addEventListener("click",liveCheck);
loadAudit();
