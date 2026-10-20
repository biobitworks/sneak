// Independent Node implementation. Does not import Python construction code.
import {createHash} from "node:crypto";
import fs from "node:fs";
const r=JSON.parse(fs.readFileSync(new URL("../receipts/INTAKE_MERKLE.json",import.meta.url),"utf8"));
const h=b=>createHash("sha256").update(b).digest();
const parent=(a,b)=>h(Buffer.concat([Buffer.from([1]),a,b]));
let xs=r.leaves.map(l=>{
 const b=Buffer.from(l.canonical_hex,"hex");
 const parsed=JSON.parse(b.toString("ascii"));
 if(JSON.stringify(parsed)!==JSON.stringify(l.record))throw Error("record mismatch");
 const leaf=h(Buffer.concat([Buffer.from([0]),b]));
 if(leaf.toString("hex")!==l.leaf)throw Error("leaf mismatch");
 let v=leaf;
 for(const step of l.proof){const s=Buffer.from(step.hash,"hex");v=step.side==="left"?parent(s,v):parent(v,s);}
 if(v.toString("hex")!==r.root)throw Error("proof mismatch");
 return leaf;
});
while(xs.length>1){
 const next=[];for(let i=0;i<xs.length;i+=2)next.push(i+1<xs.length?parent(xs[i],xs[i+1]):xs[i]);
 xs=next;
}
if(xs[0].toString("hex")!==r.root)throw Error("root mismatch");
console.log(JSON.stringify({implementation:"node:crypto independently implemented",root:r.root,leaves:r.leaf_count,result:"PASS"}));
