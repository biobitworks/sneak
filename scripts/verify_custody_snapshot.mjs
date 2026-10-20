// Independently recomputes declared snapshot and checks actual Git and working bytes.
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
import {execFileSync} from "node:child_process";
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const baseReal=fs.realpathSync(base);
// Rejects absolute, parent/empty/dot segments, backslash and non-printable-ASCII paths.
const safeRel=rel=>{
 if(typeof rel!=="string"||!/^[\x20-\x7e]+$/.test(rel)||rel.includes("\\")||rel.startsWith("/"))throw Error("unsafe path encoding");
 if(rel.split("/").some(p=>p===""||p==="."||p===".."))throw Error("unsafe path segment");
 return rel;
};
// Resolves rel under the repository with no symlink in any component and no escape.
const contained=rel=>{
 let cur=baseReal;
 for(const part of safeRel(rel).split("/")){cur=path.join(cur,part);if(fs.lstatSync(cur).isSymbolicLink())throw Error("symlink");}
 const real=fs.realpathSync(cur);
 if(real!==path.join(baseReal,rel)||!real.startsWith(baseReal+path.sep))throw Error("path escapes repository");
 return real;
};
const argument=process.argv[2]||"";
if(!/^receipts\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_.-]+\.json$/.test(argument))throw Error("receipt argument must be under receipts/");
const r=JSON.parse(fs.readFileSync(contained(process.argv[2]),"utf8"));
if(typeof r.snapshot_commit!=="string"||!/^(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(r.snapshot_commit))throw Error("snapshot_commit encoding");
const h=b=>createHash("sha256").update(b).digest();
const hash=b=>h(b).toString("hex");
const par=(a,b)=>h(Buffer.concat([Buffer.from([1]),a,b]));
const git=(...a)=>execFileSync("git",["-C",base,...a],{maxBuffer:32*1024*1024});
const all=git("ls-tree","-rz","--full-tree",r.snapshot_commit).toString("utf8").split("\0").filter(Boolean);
const expectedPaths=all.map(x=>x.split("\t")[1]).sort();
const paths=r.leaves.map(x=>x.record.path);
if(JSON.stringify(paths)!==JSON.stringify(expectedPaths))throw Error("manifest coverage/order");
const legacy="48e72e9b1a62371fc25f79180196b7fb87ae8da1";
const expectedMetadata={
 schema:"sneak.git-snapshot.v1",
 scope:"ALL_REGULAR_TRACKED_FILES_AT_DECLARED_COMMIT",
 parent_breakpoint:r.snapshot_commit===legacy?"SNEAK-011-MERGE":"SNEAK-010",
 exclusions:"Untracked/ignored assets and commits after snapshot_commit; this generated receipt is subsequent to its snapshot",
 meaning:"Integrity only; not source truth, rights, security, signatures or canonical admission",
 mmr:"NOT_COMMITTED",
 signed:false,
 construction:{
  hash:"SHA-256",canonical:"ASCII JSON sorted keys ensure_ascii=true compact separators no newline",
  ordering:"UTF-8 path ascending; ASCII paths required",
  leaf:"SHA256(0x00 || canonical(record))",internal:"SHA256(0x01 || left || right)",odd:"promote unchanged"
 }
};
const canonical=o=>JSON.stringify(o,Object.keys(o).sort());
for(const [k,v] of Object.entries(expectedMetadata)){
 const a=r[k];
 if(k==="construction"){
  if(!a||Object.keys(a).length!==Object.keys(v).length||Object.keys(v).some(z=>a[z]!==v[z]))throw Error("metadata mismatch: "+k);
 } else if(a!==v)throw Error("metadata mismatch: "+k);
}
if(r.snapshot_commit===legacy){
 expectedMetadata.parent_root="dcabcb5db384588b701b70014546d0afada1dd35e3a8b1b844c75c0bcf53e403";
 expectedMetadata.parent_snapshot_receipt="receipts/repository_bootstrap/SNAPSHOT.json";
 if(r.parent_root!==expectedMetadata.parent_root||r.parent_snapshot_receipt!==expectedMetadata.parent_snapshot_receipt)throw Error("legacy parent metadata mismatch");
}
const expectedKeys=[...Object.keys(expectedMetadata),"snapshot_commit","leaf_count","root","leaves"].sort();
if(JSON.stringify(Object.keys(r).sort())!==JSON.stringify(expectedKeys))throw Error("metadata unexpected fields");
if(r.leaf_count!==r.leaves.length)throw Error("leaf count");
let xs=r.leaves.map(item=>{
 const rec=item.record;
 if(!/^[\x20-\x7e]+$/.test(rec.path))throw Error("non-ASCII path");
 safeRel(rec.path);
 const data=git("show",r.snapshot_commit+":"+rec.path);
 if(data.length!==rec.size_bytes||hash(data)!==rec.sha256)throw Error("committed bytes "+rec.path);
 const work=contained(rec.path);
 if(!fs.lstatSync(work).isFile())throw Error("nonregular");
 const wb=fs.readFileSync(work);
 if(wb.length!==rec.size_bytes||hash(wb)!==rec.sha256)throw Error("working bytes "+rec.path);
 const c=Buffer.from(JSON.stringify({path:rec.path,sha256:rec.sha256,size_bytes:rec.size_bytes}),"ascii");
 if(c.toString("hex")!==item.canonical_hex)throw Error("canonical bytes");
 const x=h(Buffer.concat([Buffer.from([0]),c]));
 if(x.toString("hex")!==item.leaf)throw Error("leaf");
 let v=x;
 for(const s of item.proof){
  if(!["left","right"].includes(s.side)||!/^[0-9a-f]{64}$/.test(s.hash))throw Error("proof encoding");
  const b=Buffer.from(s.hash,"hex");v=s.side==="left"?par(b,v):par(v,b);
 }
 if(v.toString("hex")!==r.root)throw Error("proof");
 return x;
});
if(!xs.length)throw Error("empty");
while(xs.length>1){const n=[];for(let i=0;i<xs.length;i+=2)n.push(i+1<xs.length?par(xs[i],xs[i+1]):xs[i]);xs=n;}
if(xs[0].toString("hex")!==r.root)throw Error("root");
console.log(JSON.stringify({result:"PASS",implementation:"independent Node",root:r.root,leaves:r.leaf_count,snapshot_commit:r.snapshot_commit}));
