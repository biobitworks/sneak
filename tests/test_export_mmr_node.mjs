import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(repo,'deploy','vercel-preview');
const H=b=>createHash('sha256').update(b).digest();
const u64=n=>{const b=Buffer.alloc(8);b.writeBigUInt64BE(BigInt(n));return b};
function canonical(x){
 if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
 if(x&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
 return JSON.stringify(x);
}
function merkle(leaves){
 if(!leaves.length)throw Error('empty Merkle');
 let row=leaves;
 while(row.length>1){const next=[];for(let i=0;i<row.length;i+=2)next.push(i+1<row.length?H(Buffer.concat([Buffer.from([1]),row[i],row[i+1]])):row[i]);row=next}
 return row[0].toString('hex');
}
function mmr(records){
 let pos=0,peaks=[];
 for(const bytes of records){
  let item={height:0,hash:H(Buffer.concat([Buffer.from([0]),u64(pos++),bytes]))};
  while(peaks.length&&peaks.at(-1).height===item.height){
   const left=peaks.pop();
   item={height:item.height+1,hash:H(Buffer.concat([Buffer.from([1]),u64(pos++),left.hash,item.hash]))}
  }
  peaks.push(item);
 }
 let acc=peaks.at(-1).hash;
 for(let i=peaks.length-2;i>=0;i--)acc=H(Buffer.concat([Buffer.from([2]),u64(pos),peaks[i].hash,acc]));
 return {root:acc.toString('hex'),size:pos,peaks:peaks.map(x=>x.hash.toString('hex'))};
}
test('independent Node verifies actual exported file bytes, Merkle, MMR and peaks',()=>{
 const c=JSON.parse(fs.readFileSync(path.join(out,'data/export-custody.json')));
 const data=c.files.map(r=>{const raw=fs.readFileSync(path.join(out,r.path));assert.equal(raw.length,r.size_bytes);assert.equal(H(raw).toString('hex'),r.sha256);return Buffer.from(canonical(r),'ascii')});
 assert.deepEqual(c.files.map(r=>r.path),[...c.files.map(r=>r.path)].sort());
 assert.equal(merkle(data.map(d=>H(Buffer.concat([Buffer.from([0]),d])))),c.tree.root);
 const x=mmr(data);assert.equal(x.root,c.mmr.root_hash);assert.equal(x.size,c.mmr.size);
 assert.deepEqual(x.peaks,c.mmr.peaks.map(p=>p.hash));
 const manifest=JSON.parse(fs.readFileSync(path.join(out,'EXPORT_MANIFEST.json')));
 assert.equal(manifest.export_merkle_root,c.tree.root);
 assert.equal(manifest.export_mmr_root,c.mmr.root_hash);
});
test('independent Node checks 80 ablations, exact-one deletion, roots and MMR identities',()=>{
 const m=JSON.parse(fs.readFileSync(path.join(out,'data/evidence-matrix.json')));
 assert.equal(m.trial_count,80);
 for(const row of m.rows){
  const bindings=Object.fromEntries(m.components.map(c=>[c,{source:'SNEAK-FIXTURE',applicable:true,binding:row.actor+'/'+c}]));
  const baseline={schema:'sneak.synthetic-binding.v1',actor:row.actor,bindings,real_agent_observation:false};
  const ablated={schema:'sneak.synthetic-binding.v1',actor:row.actor,bindings:Object.fromEntries(Object.entries(bindings).filter(([key])=>key!==row.component)),real_agent_observation:false};
  const b=Buffer.from(canonical(baseline),'ascii'),a=Buffer.from(canonical(ablated),'ascii');
  assert.equal(H(Buffer.concat([Buffer.from([0]),b])).toString('hex'),row.baseline_merkle_root);
  assert.equal(H(Buffer.concat([Buffer.from([0]),a])).toString('hex'),row.ablation_merkle_root);
  assert.equal(mmr([b]).root,row.baseline_mmr_root);
  assert.equal(mmr([a]).root,row.ablation_mmr_root);
  assert.equal(row.structural_gate,'DENY_MISSING_REQUIRED_BINDING');
  assert.equal(row.agent_behavior,'NOT_TESTED');
 }
});
test('tampered bytes change independent export root',()=>{
 const c=JSON.parse(fs.readFileSync(path.join(out,'data/export-custody.json')));
 const dat=c.files.map(r=>Buffer.from(canonical(r),'ascii'));
 const before=merkle(dat.map(d=>H(Buffer.concat([Buffer.from([0]),d]))));
 dat[0]=Buffer.from('tampered');
 assert.notEqual(merkle(dat.map(d=>H(Buffer.concat([Buffer.from([0]),d])))),before);
 assert.notEqual(mmr(dat).root,c.mmr.root_hash);
});
