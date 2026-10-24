// Fake DOM triggers actual NCM selection, batch button and Ctrl-Z handlers. No network.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2] || 'proyecto_maria/static/v2/screens/ncm.js','utf8');
function scenario(kind) {
const handlers={},events={},nodes=new Map();let screen='ncm';
class Node{
 constructor(id){this.id=id;this.firstChild={};this.listeners={};this.hidden=true;this.value='';this.classList={add(){},remove(){},toggle(){},contains(){return false;}};}
 addEventListener(t,f){(this.listeners[t]??=[]).push(f);} querySelectorAll(){return [];}querySelector(){return null;}
 setAttribute(){}removeAttribute(){}getAttribute(k){return k==='data-screen'?screen:null;}
}
const node=id=>{if(!nodes.has(id))nodes.set(id,new Node(id));return nodes.get(id);};
const document={getElementById:node,querySelectorAll:()=>[],querySelector:s=>s==='.screen.is-active'?node('active'):null,activeElement:{tagName:'BODY'},
 addEventListener(t,f){(events[t]??=[]).push(f);},body:node('body'),createElement:()=>new Node()};
const CDI={state:{items:[{descripcion:'Synthetic operation A',cantidad:4,pieza:'9031.80.99.990G',valor_unitario:1}]},registerScreen:(n,h)=>handlers[n]=h,
 escapeHtml:v=>String(v??''),track(){},toast(){},formatNcm:v=>v,formatMoney:v=>String(v)};
vm.runInNewContext(source,{window:{CDI},document,console,setTimeout:()=>1,clearTimeout(){},URLSearchParams,location:{search:''},requestAnimationFrame:f=>f()});
function fire(id,t,event={}){for(const fn of node(id).listeners[t]||[])fn(event);}
for(const fn of events.DOMContentLoaded||[])fn();
handlers.ncm.onEnter();
fire('ncmSelectAll','change',{target:{checked:true}});
node('ncmBatchFactor').value='2';fire('ncmBatchApplyQty','click');
assert.equal(CDI.state.items[0].cantidad,8);
if(kind !== 'same-screen') { handlers.ncm.onLeave(); screen='review'; }
if(kind === 'rejected-B' || kind === 'valid-C') {
 screen='upload';
 // upload.js starts a new operation by replacing CDI.state and clearing items.
 CDI.state=Object.assign({},CDI.state,{operacion:{},items:[]});
 if(kind === 'valid-C') {
  CDI.state.operacion={numero_factura:'C'};
  CDI.state.items=[{descripcion:'Synthetic operation C',cantidad:1,pieza:'9031.80.99.990G',valor_unitario:2}];
 }
}
screen='ncm';handlers.ncm.onEnter();
for(const fn of events.keydown||[])fn({ctrlKey:true,key:'z',preventDefault(){}});
if(kind === 'rejected-B') {
 assert.equal(CDI.state.items.length,0,'undo must not revive A after rejected B');
} else if(kind === 'valid-C') {
 assert.equal(CDI.state.items[0].descripcion,'Synthetic operation C','undo must not replace valid C with A');
 assert.equal(CDI.state.items[0].cantidad,1);
} else {
 assert.equal(CDI.state.items[0].descripcion,'Synthetic operation A');
 assert.equal(CDI.state.items[0].cantidad,4,'same operation keeps working undo');
}
}
for(const kind of ['same-screen','same-operation-return','rejected-B','valid-C']) scenario(kind);
console.log('DOC-1 NCM undo: 4 synthetic scenarios OK.');
