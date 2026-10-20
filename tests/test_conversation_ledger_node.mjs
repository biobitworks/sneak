import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const src=path.join(repo,'deploy/vercel-preview/data/conversation-lineage.json');
const H=b=>createHash('sha256').update(b).digest();
const u64=n=>{let b=Buffer.alloc(8);b.writeBigUInt64BE(BigInt(n));return b};
const norm=x=>Array.isArray(x)?'['+x.map(norm).join(',')+']':x&&typeof x==='object'?'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+norm(x[k])).join(',')+'}':JSON.stringify(x);
function mmr(objects){let peaks=[],pos=0;for(let o of objects){let d=Buffer.from(norm(o),'ascii');let node={h:0,b:H(Buffer.concat([Buffer.from([0]),u64(pos++),d]))};while(peaks.length&&peaks.at(-1).h===node.h){let prev=peaks.pop();node={h:node.h+1,b:H(Buffer.concat([Buffer.from([1]),u64(pos++),prev.b,node.b]))}}peaks.push(node)}if(!peaks.length)return "NOT_COMPUTED";let acc=peaks.at(-1).b;for(let j=peaks.length-2;j>=0;j--)acc=H(Buffer.concat([Buffer.from([2]),u64(pos),peaks[j].b,acc]));return acc.toString('hex')}
function merkle(objects){let row=objects.map(x=>H(Buffer.concat([Buffer.from([0]),Buffer.from(norm(x),'ascii')])));if(!row.length)throw Error('empty');while(row.length>1){let next=[];for(let i=0;i<row.length;i+=2)next.push(i+1<row.length?H(Buffer.concat([Buffer.from([1]),row[i],row[i+1]])):row[i]);row=next}return row[0].toString('hex')}
test('independent root question, actor and global MMR replay including every breakpoint',()=>{
 const d=JSON.parse(fs.readFileSync(src,'utf8'));
 assert.equal(d.source.message_count,3);
 assert.equal(d.events.length,3);
 assert.equal(d.breakpoints.length,3);
 assert.equal(mmr(d.events),d.global_mmr.root);
 assert.equal(mmr([d.question.question_record,...d.events]),d.question_mmr.root);
 for(const [id,a]of Object.entries(d.actor_mmr)){
  const xs=d.events.filter(x=>x.actor_identity_sha256===id);
  assert.equal(mmr(xs),a.mmr.root);
 }
 for(let i=0;i<d.breakpoints.length;i++){
  const bp=d.breakpoints[i],subset=d.events.slice(0,i+1), q=[d.question.question_record,...subset];
  assert.equal(bp.global_mmr.root,mmr(subset));
  assert.equal(bp.question_mmr.root,mmr(q));
  assert.equal(bp.question_merkle_tree_root,merkle(q));
  assert.equal(bp.actor_mmr.root,mmr(subset.filter(x=>x.actor_identity_sha256===bp.actor_identity_sha256)));
  assert.equal(bp.custody_replay_bool,true);
  assert.equal(bp.semantic_verdict,"UNKNOWN");
  assert.equal(bp.root_question_true_false,null);
 }
});
test('mutated FCO changes question MMR and fails prior root',()=>{
 const d=JSON.parse(fs.readFileSync(src,'utf8'));
 let baseline=mmr([d.question.question_record,...d.events]);
 let changed=JSON.parse(JSON.stringify(d.events));changed[1].output_sha256='0'.repeat(64);
 assert.notEqual(mmr([d.question.question_record,...changed]),baseline);
});
test('no claimed model lineage or full conversation coverage without provenance',()=>{
 const d=JSON.parse(fs.readFileSync(src,'utf8'));
 assert.deepEqual(d.model_mmr,{});
 assert.equal(d.missing_model_identity,3);
 assert.equal(d.all_conversations_imported,false);
 assert.equal(d.cognee_graph_commit,"NOT_EXECUTED");
});
