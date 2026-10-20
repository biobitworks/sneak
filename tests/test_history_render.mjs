import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const graph=JSON.parse(fs.readFileSync('deploy/vercel-preview/data/graph.json'));
class Element {
 constructor(){this.children=[];this.textContent='';this.classList={remove(){},add(){}};this.namespaceURI='svg';}
 append(...x){this.children.push(...x)}
 replaceChildren(...x){this.children=x}
 setAttribute(){} addEventListener(){} querySelectorAll(){return []}
}
const nodes=new Map();
const document={querySelector(s){if(!nodes.has(s))nodes.set(s,new Element());return nodes.get(s)},createElement(){return new Element()},createElementNS(){return new Element()}};
vm.runInNewContext(fs.readFileSync('apps/sneak_mvp/web/app.js','utf8'),{document,fetch:async()=>({ok:true,json:async()=>graph})});
await new Promise(resolve=>setImmediate(resolve));
function text(n){return typeof n==='string'?n:n.textContent+n.children.map(text).join(' ')}
const history=text(nodes.get('#actions'));
assert(!history.includes('undefined'), 'redacted snapshot must never render undefined actor');
assert(history.includes('EV-001-R5-ATOMS'), 'all predecessor history must remain visible');
assert(history.includes('aok'), 'redacted history must label actual source');
console.log('PASS history: no undefined, all predecessors, source provenance');
