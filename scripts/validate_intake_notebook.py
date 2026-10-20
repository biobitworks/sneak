#!/usr/bin/env python3
"""Validate/source-audit notebook preparation. Run with nbformat, nbclient, ipykernel, pymupdf."""
from pathlib import Path
import json, hashlib, subprocess, sys, importlib.metadata, datetime
import nbformat, fitz
ROOT=Path(__file__).resolve().parents[1]
pdf=ROOT/"sources/challenge.pdf"
pages=[{"page_1based":i+1,"text":p.get_text("text",sort=True)} for i,p in enumerate(fitz.open(pdf))]
p=ROOT/"sources/independent_extraction_pages.jsonl"
p.write_text("".join(json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(",",":"))+"\n" for x in pages))
old=[json.loads(x) for x in (ROOT/"sources/predecessor/source_pages.jsonl").read_text().splitlines()]
comparison={"page_count":len(pages),"all_page_texts_equal":all(a["text"]==b["text"] for a,b in zip(pages,old)),
"independent_extractor_version":importlib.metadata.version("pymupdf"),"source_pdf_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),
"visual_layout_review":"NOT_TESTED","status":"PASS_SOURCE_EXTRACTION_COMPLETE"}
(ROOT/"receipts/INDEPENDENT_EXTRACTION.json").write_text(json.dumps(comparison,indent=2)+"\n")
nb=nbformat.v4.new_notebook()
nb.metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
"language_info":{"name":"python"}}
nb.cells=[
nbformat.v4.new_markdown_cell("# Intake custody replication\n\nVerifies original PDF identity, source atom pointers, candidate Merkle leaves/proofs/root and independent Node recomputation. "
"Does not execute untrusted skills, call models, scan vulnerabilities or admit canonical state. "
"Run from the repository root. Outputs are saved separately under receipts/ so the source notebook remains immutable."),
nbformat.v4.new_code_cell("from pathlib import Path\nimport json, hashlib, subprocess, sys\nROOT=Path.cwd()\nif not (ROOT/'sources/challenge.pdf').exists(): ROOT=ROOT.parent\nassert (ROOT/'sources/challenge.pdf').exists()\nexpected='f9c730d4c6464cdfeedb540e0d4b6080b7bfcde9fab496a1eac0dbc15b0aa1cc'\nassert hashlib.sha256((ROOT/'sources/challenge.pdf').read_bytes()).hexdigest()==expected\natoms=[json.loads(x) for x in (ROOT/'data/rules/atoms.jsonl').read_text().splitlines()]\ncontent=json.loads((ROOT/'data/rules/deduplicated_content.json').read_text())\nassert all(content[a['content_sha256']]==a['text'] for a in atoms)\nprint(json.dumps({'source_identity':True,'atoms':len(atoms),'occurrence_reconstruction_exact':True}))"),
nbformat.v4.new_markdown_cell("## Recompute candidate custody\n\nSHA-256, domain-separated leaves/internal nodes, UTF-8 path ordering and odd-node promotion are declared in the receipt. Expected adversarial acceptance results are FALSE."),
nbformat.v4.new_code_cell("r=subprocess.run([sys.executable,str(ROOT/'scripts/recompute_intake.py')],cwd=ROOT,text=True,capture_output=True,check=True)\nprint(r.stdout)\nreceipt=json.loads((ROOT/'receipts/INTAKE_MERKLE.json').read_text())\nassert receipt['checks']['all_inclusion_proofs_valid'] is True\nassert receipt['checks']['tampered_leaf_accepted'] is False"),
nbformat.v4.new_code_cell("r=subprocess.run(['node',str(ROOT/'scripts/verify_intake.mjs')],cwd=ROOT,text=True,capture_output=True,check=True)\nprint(r.stdout)\nresult=json.loads(r.stdout)\nassert result['root']==receipt['root'] and result['result']=='PASS'"),
nbformat.v4.new_markdown_cell("## Limits\n\nPASS applies to the declared intake snapshot only. Model/VM/BAND/Cognee/Snyk/Flexprice experiments remain NOT_EXECUTED. "
"Project MMR NOT_COMMITTED; SIGNED=NO; Anticube and DeltaG* NOT_COMPUTED. "
"Four synthetic fixtures are development data, not a validated adversarial benchmark.")
]
(ROOT/"notebooks").mkdir(exist_ok=True)
nbformat.validate(nb)
nbformat.write(nb,ROOT/"notebooks/01_intake_recompute.ipynb")
versions={x:importlib.metadata.version(x) for x in ["nbformat","nbclient","ipykernel","pymupdf"]}
(ROOT/"requirements-intake.txt").write_text("".join(f"{k}=={v}\n" for k,v in versions.items()))
source_review=json.loads((ROOT/"receipts/SOURCE_REVIEW.json").read_text())
source_review["requirements_successor_count"]=len((ROOT/".planning/requirements.jsonl").read_text().splitlines())
source_review["independent_extraction"]=comparison
(ROOT/"receipts/SOURCE_REVIEW_SUCCESSOR.json").write_text(json.dumps(source_review,indent=2)+"\n")
# The first immutable leaf snapshot is computed after source notebook and environment pins exist.
r=subprocess.run([sys.executable,str(ROOT/"scripts/recompute_intake.py")],cwd=ROOT,capture_output=True,text=True,check=True)
print(r.stdout,flush=True)
from nbclient import NotebookClient
nbformat.validate(nb)
NotebookClient(nb,timeout=120,kernel_name="python3",resources={"metadata":{"path":str(ROOT)}}).execute()
nbformat.validate(nb)
dest=ROOT/"receipts/01_intake_recompute.executed.ipynb"
nbformat.write(nb,dest)
assert all(c.execution_count is not None for c in nb.cells if c.cell_type=="code")
assert not any(o.output_type=="error" for c in nb.cells if c.cell_type=="code" for o in c.outputs)
(ROOT/"receipts/NOTEBOOK_EXECUTION.json").write_text(json.dumps({
"source":"notebooks/01_intake_recompute.ipynb","source_sha256":hashlib.sha256((ROOT/"notebooks/01_intake_recompute.ipynb").read_bytes()).hexdigest(),
"executed":str(dest.relative_to(ROOT)),"executed_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
"code_cells":sum(c.cell_type=="code" for c in nb.cells),"execution":"PASS","nbformat_validation":"PASS",
"saved_output_inspection":"programmatic inspection passed; visual UI inspection NOT_TESTED","versions":versions},indent=2)+"\n")
print(json.dumps({"notebook":"PASS","source_review":comparison,"versions":versions}),flush=True)
