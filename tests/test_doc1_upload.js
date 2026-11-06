// Synthetic uploads only; node tests/test_doc1_upload.js [upload.js path].
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[2] || 'proyecto_maria/static/v2/screens/upload.js', 'utf8');
const deferred = () => { let resolve, reject; const promise = new Promise((a,b) => { resolve=a; reject=b; }); return {promise,resolve,reject}; };
const flush = async () => { for(let i=0;i<20;i++) await Promise.resolve(); };
const response = (data, ok=true) => ({ok,status:ok?200:422,json:async()=>data});
const invoice = (name, op={}) => ({filename:name,documento:{tipo:'factura_comercial',operacion:'importacion'},operacion:op,items:[{descripcion:name,pieza:'',origen:'XX'}]});
const rejected = () => response({code:'documento_no_admitido',detail:'Este documento no es una factura comercial admitida.'},false);
function harness() {
    const nodes = new Map();
    class Node {
        constructor(id) { this.id=id; this.listeners={}; this.hidden=true; this.textContent=''; this.isConnected=true; this.classList={add(){},remove(){},toggle(){}}; }
        addEventListener(type,fn) { this.listeners[type]=fn; }
        appendChild() {} setAttribute() {} getAttribute() { return this.id; } click() { return this.listeners.click?.({preventDefault(){}}); }
    }
    const node = id => {if(!nodes.has(id))nodes.set(id,new Node(id));return nodes.get(id);};
    const storage = new Map([['cdi_v2_state:esta-pestana','old-draft'],['cdi_v2_state:otra-pestana','other-tab-draft'],['history-must-stay','saved-operation']]);
    const session = new Map([['cdi.pending_create_client','old-client']]);
    const calls=[], routes=[], toasts=[], clients=[];
    const CDI={state:{filename:'A.pdf',operacion:{numero_factura:'A'},items:[{pieza:'OLD-NCM'}],catalogAutofillBanner:{old:true},clienteActivo:{id:'persistent-client'}},
        borrador:{borrar(){storage.delete('cdi_v2_state:esta-pestana');}},
        track(){},toast:Object.assign((...args)=>toasts.push(args),{error:(...args)=>toasts.push(args)}),
        registerScreen(name,screen){this.screen=screen;},goTo(name){routes.push(name);},normalizeCuit:s=>s,
        getClienteActivo(){return this.state.clienteActivo;},setClienteActivo(c){this.state.clienteActivo=c;clients.push(c);},
        api(url,opts){const d=deferred();calls.push({url,opts,...d});return d.promise;}};
    const document={getElementById:node,querySelectorAll:()=>[node('pdf'),node('excel')],addEventListener(type,fn){if(type==='DOMContentLoaded')this.init=fn;},createElement:()=>new Node(),createTextNode:()=>({})};
    const context={window:{CDI,addEventListener(){}},document,sessionStorage:{removeItem:k=>session.delete(k),setItem:(k,v)=>session.set(k,v)},localStorage:{removeItem:k=>storage.delete(k),clear:()=>storage.clear(),key:i=>[...storage.keys()][i]??null,get length(){return storage.size;}},
        FormData:class{append(){}},console:{log(){},warn(){},error(){}},setTimeout:()=>1,clearTimeout(){},Date};
    vm.runInNewContext(source,context);document.init();
    return {CDI,calls,routes,toasts,clients,storage,session,node,upload(name='B.pdf',size=10){return node('uploadFileInput').listeners.change({target:{files:[{name,size,type:'application/pdf'}]}});}};
}
(async()=>{
    {
        const h=harness();h.upload();
        assert.equal(h.CDI.state.items.length,0,'B must invalidate A immediately');
        assert.equal(h.CDI.state.operacion.numero_factura,undefined);
        assert.equal(h.CDI.state.catalogAutofillBanner,null);
        assert.equal(h.CDI.state.clienteActivo.id,'persistent-client','keep selected client until valid PDF');
        assert.equal(h.storage.has('cdi_v2_state:esta-pestana'),false,'reload cannot restore A draft');
        assert.equal(h.storage.get('history-must-stay'),'saved-operation');
        assert.equal(h.storage.get('cdi_v2_state:otra-pestana'),'other-tab-draft','another tab keeps its draft');
        h.calls[0].resolve(rejected());await flush();
        assert.equal(h.CDI.state.items.length,0);assert.deepEqual(h.routes,[]);
        assert.equal(h.storage.has('cdi_v2_state:esta-pestana'),false,'failed B cannot restore the old draft');
        assert.equal(h.storage.get('history-must-stay'),'saved-operation','failed B keeps saved history');
        assert.match(h.node('uploadError').textContent,/no es una factura.*empezar de nuevo/);
        h.upload('C.pdf');h.calls[1].resolve(response(invoice('C.pdf')));await flush();
        assert.equal(h.CDI.state.filename,'C.pdf');assert.deepEqual(h.routes,['review']);
        assert.equal(h.CDI.state.documento.tipo,'factura_comercial');
    }
    {
        const h=harness();h.upload('wrong.pdf',0);
        assert.equal(h.CDI.state.items.length,0,'local rejection also invalidates A');
        assert.equal(h.calls.length,0);
    }
    {
        const h=harness();h.upload('A.pdf');h.upload('B.pdf');
        h.calls[1].resolve(rejected());await flush();
        h.calls[0].resolve(response(invoice('A.pdf')));await flush();
        assert.equal(h.CDI.state.items.length,0,'late upload cannot revive A');assert.deepEqual(h.routes,[]);
    }
    {
        const h=harness();h.upload();h.calls[0].reject(new Error('synthetic network failure'));await flush();
        assert.equal(h.CDI.state.items.length,0);assert.deepEqual(h.routes,[]);
    }
    {
        const h=harness();h.upload('A.pdf');h.upload('B.pdf');
        h.calls[1].resolve(response(invoice('B.pdf')));await flush();
        h.calls[0].reject(new Error('late synthetic A failure'));await flush();
        assert.equal(h.CDI.state.filename,'B.pdf');assert.equal(h.CDI.state.items.length,1);
        assert.deepEqual(h.routes,['review']);assert.equal(h.node('uploadError').hidden,true);
    }
    // Both auto-match branches ignore old A, including late JSON parsing.
    for(const op of [{comprador_cuit:'30111111111',comprador_nombre:'Synthetic A'},{comprador_nombre:'Synthetic A'}]) {
        const h=harness();h.upload('A.pdf');h.calls[0].resolve(response(invoice('A.pdf',op)));await flush();
        const json=deferred();h.calls[1].resolve({ok:true,json:()=>json.promise});await flush();
        h.upload('B.pdf');h.calls[2].resolve(rejected());await flush();
        const client={id:'stale-A',nombre:'Synthetic A'};
        json.resolve(op.comprador_cuit?{match:'exact',cliente:client}:{clientes:[client]});await flush();
        assert.equal(h.CDI.state.items.length,0);assert.equal(h.CDI.state.clienteActivo,null);
        assert.equal(h.session.has('cdi.pending_create_client'),false);assert.deepEqual(h.routes,[]);
        assert.equal(h.clients.some(c=>c?.id==='stale-A'),false);
    }
    {
        const h=harness();h.upload('A.pdf');h.calls[0].resolve(response(invoice('A.pdf',{vendedor_nombre:'Synthetic Vendor'})));await flush();
        assert.equal(h.calls[1].url,'/api/catalog/lookup');
        const json=deferred();h.calls[1].resolve({ok:true,json:()=>json.promise});await flush();
        h.upload('B.pdf');h.calls[2].resolve(response(invoice('B.pdf')));await flush();
        json.resolve({items:[{idx:0,ncm:'STALE-NCM',source:'cliente'}],aplicados_cliente:1});await flush();
        assert.equal(h.CDI.state.filename,'B.pdf');assert.equal(h.CDI.state.items[0].pieza,'');
        assert.equal(h.CDI.state.catalogAutofillBanner,null);assert.deepEqual(h.routes,['review']);
    }
    {
        const h=harness();h.upload('A.pdf');
        const json=deferred();h.calls[0].resolve({ok:true,json:()=>json.promise});await flush();
        h.upload('B.pdf');h.calls[1].resolve(rejected());await flush();
        json.resolve(invoice('A.pdf'));await flush();
        assert.equal(h.CDI.state.items.length,0);assert.deepEqual(h.routes,[]);
    }
    {
        const h=harness();let picker;
        h.CDI.openClientePicker=opts=>{picker=opts;};
        h.node('excel').click();h.upload('A.xlsx');
        h.node('pdf').click();h.upload('B.pdf');
        h.calls[0].resolve(rejected());await flush();
        picker.onSelect({id:'stale-excel-client'});await flush();
        assert.equal(h.calls.length,1,'old Excel picker cannot upload or select A client');
        assert.equal(h.CDI.state.clienteActivo.id,'persistent-client');
        assert.equal(h.CDI.state.items.length,0);
    }
    {
        const h=harness();const confirm=deferred();
        h.CDI.confirm=()=>confirm.promise;
        h.node('excel').click();h.upload('A.xlsx');await flush();
        h.node('pdf').click();h.upload('B.pdf');h.calls[0].resolve(rejected());await flush();
        confirm.resolve(true);await flush();
        assert.equal(h.calls.length,1,'old Excel confirmation cannot start another upload');
        assert.equal(h.CDI.state.items.length,0);
    }
    console.log('DOC-1 upload: 11 synthetic scenarios OK (state, rejection, races, client, catalog, draft, Excel).');
})().catch(e=>{console.error(e);process.exitCode=1;});
