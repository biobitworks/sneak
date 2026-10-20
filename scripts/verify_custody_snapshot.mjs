// Independently recomputes declared snapshot and checks actual Git and working bytes.
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
import {execFileSync} from "node:child_process";
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const argument=process.argv[2]||"";
if(!/^receipts\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_.-]+\.json$/.test(argument))throw Error("receipt argument must be under receipts/");
const receiptPath=path.resolve(base,argument);
if(!receiptPath.startsWith(path.join(base,"receipts")+path.sep))throw Error("receipt traversal");
const r=JSON.parse(fs.readFileSync(receiptPath,"utf8"));
const h=b=>createHash("sha256").update(b).digest();
const hash=b=>h(b).toString("hex");
const par=(a,b)=>h(Buffer.concat([Buffer.from([1]),a,b]));
const git=(...a)=>execFileSync("git",["-C",base,...a],{maxBuffer:32*1024*1024});
const all=git("ls-tree","-rz","--full-tree",r.snapshot_commit).toString("utf8").split("\0").filter(Boolean);
const expectedPaths=all.map(x=>x.split("\t")[1]).sort();
const paths=r.leaves.map(x=>x.record.path);
if(JSON.stringify(paths)!==JSON.stringify(expectedPaths))throw Error("manifest coverage/order");
if(r.leaf_count!==r.leaves.length)throw Error("leaf count");
let xs=r.leaves.map(item=>{
 const rec=item.record;
 if(!/^[\x20-\x7e]+$/.test(rec.path))throw Error("non-ASCII path");
 const data=git("show",r.snapshot_commit+":"+rec.path);
 if(data.length!==rec.size_bytes||hash(data)!==rec.sha256)throw Error("committed bytes "+rec.path);
 const work=path.resolve(base,rec.path);
 if(!work.startsWith(base+path.sep))throw Error("working path traversal");
 if(fs.lstatSync(work).isSymbolicLink())throw Error("symlink");
 if(!fs.realpathSync(work).startsWith(base+path.sep))throw Error("working realpath traversal");
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
