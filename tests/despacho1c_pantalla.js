// Pantallas reales con un DOM falso y sin red: qué avisos quedan a la vista
// cuando el servidor contesta historial_guardado. Uso: node despacho1c_pantalla.js <escenario> <true|false|null>
// null: la respuesta no trae el campo.
const vm = require('node:vm'), fs = require('node:fs'), path = require('node:path');
const V2 = path.join(__dirname, '..', 'proyecto_maria', 'static', 'v2');
const [escenario, flag] = process.argv.slice(2);
const flagJson = JSON.parse(flag);
const conFlag = c => (flagJson === null ? c : Object.assign({ historial_guardado: flagJson }, c));

class Node {
  constructor(id) {
    this.id = id; this.listeners = {}; this.hidden = true; this.value = ''; this.textContent = '';
    this.innerHTML = ''; this.attrs = {}; this.children = {}; this.style = {};
    this.classList = { add() {}, remove() {}, toggle() {}, contains() { return false; } };
    this.firstChild = { nodeValue: '' };
  }
  addEventListener(t, f) { (this.listeners[t] ??= []).push(f); }
  querySelectorAll(sel) { return this.children[sel] || []; }
  querySelector(sel) { return (this.children[sel] || [])[0] || null; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  removeAttribute(k) { delete this.attrs[k]; }
  closest(sel) { return (this.ancestors || {})[sel] || null; }
  appendChild() {} focus() {} select() {}
}

function armar(fuente, extraCDI) {
  const nodes = new Map(), handlers = {}, events = {}, toasts = [], llamadas = [];
  const node = id => { if (!nodes.has(id)) nodes.set(id, new Node(id)); return nodes.get(id); };
  const respuestas = {
    '/generate_maria': { success: true, filename: 'MARIA_SINTETICA.TXT', content: 'x' },
    '/operaciones': conFlag({ success: true, operation_id: 1 }),
    '/api/ncm/guardar-uso': conFlag({ success: true }),
  };
  let cliente = null;
  const CDI = Object.assign({
    state: { items: [], operacion: {} },
    registerScreen: (n, h) => { handlers[n] = h; },
    escapeHtml: v => String(v ?? ''), formatNcm: v => String(v ?? ''), formatMoney: v => String(v),
    track() {}, goTo() {},
    toast: (titulo, detalle, tipo) => toasts.push({ titulo, detalle, tipo }),
    getClienteActivo: () => cliente, setClienteActivo: c => { cliente = c; },
    api: async (url) => {
      llamadas.push(url);
      const clave = Object.keys(respuestas).find(k => url.endsWith(k));
      const cuerpo = clave ? respuestas[clave] : { success: true };
      return { ok: true, status: 200, json: async () => cuerpo };
    },
  }, extraCDI);
  const document = {
    getElementById: node, querySelectorAll: () => [], querySelector: () => null,
    activeElement: { tagName: 'BODY' }, body: node('body'), createElement: () => new Node(),
    addEventListener(t, f) { (events[t] ??= []).push(f); },
  };
  const contexto = vm.createContext({
    window: { CDI, addEventListener() {} }, document, console: { log() {}, warn() {}, error() {} },
    setTimeout: () => 1, clearTimeout() {}, URLSearchParams, location: { search: '' },
    requestAnimationFrame: f => f(), navigator: {},
  });
  for (const archivo of ['montos_ar.js', 'screens/' + fuente]) {
    vm.runInContext(fs.readFileSync(path.join(V2, archivo), 'utf8'), contexto);
  }
  for (const fn of events.DOMContentLoaded || []) fn();
  return { CDI, node, handlers, toasts, llamadas, ponerCliente: c => { cliente = c; } };
}

// Sin red real todo sigue en microtareas, y setImmediate corre recién con esa cola vacía:
// una vuelta después de ver la llamada, la pantalla ya procesó la respuesta.
const vaciar = () => new Promise(r => setImmediate(r));
async function esperarRed(app, url) {
  let i = 0;
  do await vaciar(); while (++i < 50 && !app.llamadas.some(u => u.endsWith(url)));
  if (!app.llamadas.some(u => u.endsWith(url))) throw new Error('la pantalla no llamó a ' + url);
}

const ITEM = { descripcion: 'Mesa de madera sintética', cantidad: 1, pieza: '', origen: 'CN', valor_unitario: 1 };

const escenarios = {
  // Listo con cliente activo: guarda la operación sola después de generar.
  'listo-con-cliente': async () => {
    const app = armar('finalize.js');
    app.ponerCliente({ id: 7, nombre: 'Cliente Sintético' });
    app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
    app.handlers.ready.onEnter();
    await esperarRed(app, '/operaciones');
    return app;
  },
  // Listo sin cliente: el panel asigna uno y vuelve a guardar.
  'asignar-cliente': async () => {
    const app = armar('finalize.js', {
      openClientePicker: ({ onSelect }) => onSelect({ id: 7, nombre: 'Cliente Sintético' }),
    });
    app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
    app.handlers.ready.onEnter();
    await esperarRed(app, '/generate_maria');
    for (const fn of app.node('orphanAssignBtn').listeners.click || []) fn({});
    await esperarRed(app, '/operaciones');
    return app;
  },
  // Paso de NCM: completar la posición SIM y salir del campo la confirma.
  'confirmar-ncm': async () => {
    const app = armar('ncm.js');
    app.ponerCliente({ id: 7, nombre: 'Cliente Sintético' });
    app.CDI.state.items = [Object.assign({}, ITEM)];
    const sim = new Node(), dc = new Node(), fila = new Node(), campos = new Node();
    sim.value = '94036000000'; dc.value = 'A';
    sim.attrs['data-row'] = '0'; dc.attrs['data-row'] = '0';
    campos.children['.ncm-input'] = [sim]; campos.children['.sim-dc-input'] = [dc];
    for (const n of [sim, dc]) n.ancestors = { '.sim-position-fields': campos, tr: fila };
    const tbody = app.node('ncmTbody');
    tbody.children['.ncm-input'] = [sim]; tbody.children['.sim-dc-input'] = [dc];
    app.handlers.ncm.onEnter();
    if (!(sim.listeners.blur || []).length) throw new Error('la tabla no enganchó el blur');
    // render() vuelve a enganchar sobre el mismo nodo falso: se dispara lo que había.
    for (const fn of [...sim.listeners.blur]) fn({ target: sim });
    await esperarRed(app, '/api/ncm/guardar-uso');
    return app;
  },
};

escenarios[escenario]().then(app => {
  process.stdout.write(JSON.stringify({ toasts: app.toasts }));
}, err => { console.error(err && err.stack || err); process.exit(2); });
