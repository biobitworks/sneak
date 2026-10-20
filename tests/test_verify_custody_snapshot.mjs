// Path-containment tests for scripts/verify_custody_snapshot.mjs. Run: node --test tests/
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {execFileSync, spawnSync} from "node:child_process";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
// Fixture repo carrying copies of both scripts so the verifier's repo root is the fixture.
const fixture=()=>{
 const t=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),"sneak-node-")));
 const repo=path.join(t,"repo");fs.mkdirSync(path.join(repo,"scripts"),{recursive:true});fs.mkdirSync(path.join(repo,"d"));
 for(const f of ["custody_snapshot.py","verify_custody_snapshot.mjs"])fs.copyFileSync(path.join(ROOT,"scripts",f),path.join(repo,"scripts",f));
 fs.writeFileSync(path.join(repo,"d","a.txt"),"baseline");
 const git=(...a)=>execFileSync("git",["-C",repo,...a],{stdio:["ignore","pipe","ignore"]});
 git("init","-q");git("config","user.name","Test");git("config","user.email","test@example.invalid");git("add","-A");git("commit","-qm","fixture");
 execFileSync("python3",["-I",path.join(repo,"scripts","custody_snapshot.py"),"create","receipts/R.json"],{cwd:repo});
 fs.writeFileSync(path.join(t,"outside.txt"),"OUTSIDE");
 return {t,repo};
};
const verify=(repo,arg)=>spawnSync(process.execPath,[path.join(repo,"scripts","verify_custody_snapshot.mjs"),arg],{cwd:repo,encoding:"utf8"});
test("valid relative receipt path passes",()=>{
 const {repo}=fixture();const res=verify(repo,"receipts/R.json");
 assert.equal(res.status,0,res.stderr);assert.equal(JSON.parse(res.stdout).result,"PASS");
});
test("CLI receipt traversal, absolute, symlink and encoding rejected",()=>{
 const {t,repo}=fixture();fs.copyFileSync(path.join(repo,"receipts","R.json"),path.join(t,"evil.json"));
 fs.mkdirSync(path.join(t,"linkdir"));fs.copyFileSync(path.join(repo,"receipts","R.json"),path.join(t,"linkdir","R.json"));
 fs.symlinkSync(path.join(t,"linkdir"),path.join(repo,"ln"));
 for(const bad of ["../evil.json",path.join(t,"evil.json"),"receipts/../../evil.json","ln/R.json","receipts\\R.json","receipts/Ré.json","./receipts/R.json",""]){
  const res=verify(repo,bad);
  assert.notEqual(res.status,0,bad);assert.doesNotMatch(res.stdout,/PASS/,bad);
 }
});
test("tampered receipt leaf path traversal rejected before any read",()=>{
 const {t,repo}=fixture();const r=JSON.parse(fs.readFileSync(path.join(repo,"receipts","R.json"),"utf8"));
 for(const bad of ["../outside.txt",path.join(t,"outside.txt"),"d/../../outside.txt"]){
  const x=structuredClone(r);x.leaves[0].record.path=bad;fs.writeFileSync(path.join(repo,"receipts","T.json"),JSON.stringify(x));
  const res=verify(repo,"receipts/T.json");assert.notEqual(res.status,0,bad);assert.doesNotMatch(res.stdout,/PASS/,bad);
 }
});
test("symlinked leaf directory and option-like snapshot_commit rejected",()=>{
 const {t,repo}=fixture();const r=JSON.parse(fs.readFileSync(path.join(repo,"receipts","R.json"),"utf8"));
 const x=structuredClone(r);x.snapshot_commit="--output=y";fs.writeFileSync(path.join(repo,"receipts","C.json"),JSON.stringify(x));
 let res=verify(repo,"receipts/C.json");assert.notEqual(res.status,0);assert.match(res.stderr,/snapshot_commit encoding/);
 fs.mkdirSync(path.join(t,"outdir"));fs.writeFileSync(path.join(t,"outdir","a.txt"),"baseline");
 fs.rmSync(path.join(repo,"d"),{recursive:true});fs.symlinkSync(path.join(t,"outdir"),path.join(repo,"d"));
 res=verify(repo,"receipts/R.json");assert.notEqual(res.status,0);assert.match(res.stderr,/symlink/);
});

test("unbound metadata is rejected, including signature and MMR claims",()=>{
 const {repo}=fixture();const orig=JSON.parse(fs.readFileSync(path.join(repo,"receipts","R.json"),"utf8"));
 for(const [key,value] of [["signed",true],["mmr","COMMITTED"],["meaning","verified by authority"],["parent_breakpoint","FORGED"]]){
  const x=structuredClone(orig);x[key]=value;fs.writeFileSync(path.join(repo,"receipts","T.json"),JSON.stringify(x));
  const res=verify(repo,"receipts/T.json");assert.notEqual(res.status,0,key);assert.match(res.stderr,/metadata mismatch/,key);
 }
});
