// Pantallas reales con un DOM falso y sin red: qué queda a la vista según lo que
// contesta el servidor al guardar. Uso: node despacho1c_pantalla.js <escenario> <respuesta> [opciones]
// respuesta: true|false|null es historial_guardado (null: sin el campo); {"status": N}
// contesta ese error; "red" es la red caída, 402 el plan vencido (CDI.api lanza) y
// "colgado" no vuelve nunca. opciones: {"catalogo": respuesta del catálogo, "vendedor": nombre}.
const vm = require('node:vm'), fs = require('node:fs'), path = require('node:path');
const V2 = path.join(__dirname, '..', 'proyecto_maria', 'static', 'v2');
const [escenario, flag] = process.argv.slice(2);
const flagJson = JSON.parse(flag);
const opciones = JSON.parse(process.argv[4] || '{}');
// lo que lanza CDI.api ante un 402: el motivo del servidor como mensaje y el código aparte
const MOTIVO_402 = 'Motivo sintético del plan';
const esFalla = flagJson !== null && typeof flagJson !== 'boolean';
const conFlag = c => (flagJson === null ? c : esFalla ? flagJson : Object.assign({ historial_guardado: flagJson }, c));
// qué guardados contestan la respuesta pedida; los demás contestan bien
const DESTINOS = {
  'confirmar-ncm': ['/api/ncm/guardar-uso'], 'asignar-ncm': ['/api/ncm/guardar-uso'], aprender: ['/productos'],
  'listo-con-vendedor': 'catalogo' in opciones ? ['/operaciones'] : ['/operaciones', '/productos'],
  'listo-y-cambia': [], 'crear-asignar-crear': ['/operaciones'], 'crear-y-otra': [],
}[escenario] || ['/operaciones'];

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
  const nodes = new Map(), handlers = {}, events = {}, toasts = [], llamadas = [], operaciones = [], hints = [];
  let enCurso = 0;
  const node = id => { if (!nodes.has(id)) nodes.set(id, new Node(id)); return nodes.get(id); };
  const respuestas = {
    '/generate_maria': { success: true, filename: 'MARIA_SINTETICA.TXT', content: 'x' },
    '/operaciones': { success: true, operation_id: 1 },
    '/api/ncm/guardar-uso': { success: true },
    '/productos': { success: true, productos_nuevos: 1 },
    '/api/clientes': { success: true, cliente: { id: 8, nombre: 'Cliente Nuevo Sintético' } },
  };
  for (const d of DESTINOS) respuestas[d] = conFlag(respuestas[d]);
  if ('catalogo' in opciones) respuestas['/productos'] = opciones.catalogo;
  let clientesNuevos = 0;
  const CDI = Object.assign({
    state: { items: [], operacion: {} },
    registerScreen: (n, h) => { handlers[n] = h; },
    escapeHtml: v => String(v ?? ''), formatNcm: v => String(v ?? ''), formatMoney: v => String(v),
    track() {}, goTo() {}, hint: clave => hints.push(clave),
    toast: (titulo, detalle, tipo) => toasts.push({ titulo, detalle, tipo }),
    getClienteActivo: () => (CDI.state && CDI.state.clienteActivo) || null, setClienteActivo: c => { CDI.state.clienteActivo = c || null; },
    api: async (url, opciones) => {
      llamadas.push(url); enCurso++;
      if (url.endsWith('/operaciones')) operaciones.push({ url, resumen: JSON.parse(opciones.body).resumen });
      // el peor caso de guardar y aprender a la vez: el catálogo contesta último
      if (escenario.startsWith('listo-') && url.endsWith('/productos')) {
        if (CDI.mientrasAprende) CDI.mientrasAprende();
        for (let i = 0; i < 5; i++) await vaciar();
      }
      enCurso--;
      const clave = Object.keys(respuestas).find(k => url.endsWith(k));
      let cuerpo = clave ? respuestas[clave] : { success: true };
      if (clave === '/api/clientes') {
        const id = 8 + clientesNuevos++;
        cuerpo = { success: true, cliente: { id, nombre: 'Cliente Nuevo Sintético' } };
      }
      if (cuerpo === 'colgado') return new Promise(() => {});
      if (cuerpo === 'red') throw new TypeError('Failed to fetch');
      if (cuerpo === 402) throw Object.assign(new Error(MOTIVO_402), { code: 'payment_required' });
      if (cuerpo.status) return { ok: false, status: cuerpo.status, json: async () => ({ detail: cuerpo.detail || 'falla sintética' }) };
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
  // errores.js cuelga textoDeError de window; en la página window es el global.
  vm.runInContext(fs.readFileSync(path.join(V2, '..', 'errores.js'), 'utf8'), contexto);
  contexto.textoDeError = contexto.window.textoDeError;
  for (const archivo of ['montos_ar.js', 'screens/' + fuente]) {
    vm.runInContext(fs.readFileSync(path.join(V2, archivo), 'utf8'), contexto);
  }
  const caja = node('readyClientSuccess');
  caja.children['[data-client-success-title]'] = [new Node()];
  caja.children['[data-client-success-text]'] = [new Node()];
  for (const fn of events.DOMContentLoaded || []) fn();
  return { CDI, node, handlers, toasts, llamadas, operaciones, hints, enCurso: () => enCurso, ponerCliente: c => { CDI.state.clienteActivo = c || null; } };
}

// Sin red real todo sigue en microtareas, y setImmediate corre recién con esa cola vacía:
// una vuelta después de ver la llamada, la pantalla ya procesó la respuesta.
const vaciar = () => new Promise(r => setImmediate(r));
async function esperarRed(app, url, veces = 1) {
  const hechas = () => app.llamadas.filter(u => u.endsWith(url)).length;
  let i = 0;
  do await vaciar(); while (++i < 50 && (hechas() < veces || app.enCurso() > 0));
  if (hechas() < veces) throw new Error('la pantalla no llamó ' + veces + ' veces a ' + url);
}

const ITEM = { descripcion: 'Mesa de madera sintética', cantidad: 1, pieza: '', origen: 'CN', valor_unitario: 1 };
const click = (app, id) => { for (const fn of app.node(id).listeners.click || []) fn({}); };
const enter = n => { for (const fn of [...(n.listeners.keydown || [])]) fn({ key: 'Enter', target: n, preventDefault() {} }); };

// Listo sin cliente: el panel de la operación sin cliente ya está a la vista.
async function listoSinCliente(extraCDI) {
  const app = armar('finalize.js', extraCDI);
  app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
  app.handlers.ready.onEnter();
  await esperarRed(app, '/generate_maria');
  app.node('orphanCreateNombre').value = 'Cliente Nuevo Sintético';
  return app;
}

// Paso de NCM con la posición SIM completa en la fila 0.
function pasoNcm() {
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
  return { app, sim };
}

const escenarios = {
  // Listo con cliente activo: guarda la operación sola después de generar. La caja
  // de éxito de una operación anterior sigue abierta.
  'listo-con-cliente': async () => {
    const app = armar('finalize.js');
    app.ponerCliente({ id: 7, nombre: 'Cliente Sintético' });
    app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
    app.node('readyClientSuccess').hidden = false;
    app.handlers.ready.onEnter();
    await esperarRed(app, '/operaciones');
    return app;
  },
  // Listo con cliente: generar el TXT anda y armar la operación lanza antes de mandarla.
  'listo-no-arma': async () => {
    // Los valores se leen antes de pedir; la foto que usa la operación lanza al copiarse.
    let lecturas = 0;
    const app = armar('finalize.js', { despachante: { valores() {
      if (++lecturas > 1) return {};
      return { get banco_bcra() { throw new Error('falla sintética'); } };
    } } });
    app.ponerCliente({ id: 7, nombre: 'Cliente Sintético' });
    app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
    app.handlers.ready.onEnter();
    await esperarRed(app, '/generate_maria');
    return app;
  },
  // Listo con vendedor: aprende los productos en el catálogo del proveedor.
  aprender: async () => {
    const app = armar('finalize.js');
    app.ponerCliente({ id: 7, nombre: 'Cliente Sintético' });
    app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
    app.CDI.state.operacion = { vendedor_nombre: opciones.vendedor || 'Proveedor Sintético' };
    app.handlers.ready.onEnter();
    await esperarRed(app, '/productos');
    return app;
  },
  // Listo con cliente y vendedor: guarda la operación y aprende el catálogo a la vez.
  'listo-con-vendedor': async () => {
    const app = armar('finalize.js');
    app.ponerCliente({ id: 7, nombre: 'Cliente Sintético' });
    app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
    app.CDI.state.operacion = { vendedor_nombre: 'Proveedor Sintético' };
    app.handlers.ready.onEnter();
    await esperarRed(app, '/operaciones');
    await esperarRed(app, '/productos');
    return app;
  },
  // Listo con vendedor: mientras aprende, la persona cambia de cliente o de operación
  // (respuesta: el cliente nuevo, o null si sale de Listo con «Nueva operación»).
  'listo-y-cambia': async () => {
    const app = armar('finalize.js');
    app.ponerCliente({ id: 7, nombre: 'Cliente Sintético' });
    app.CDI.state.items = [Object.assign({}, ITEM, { pieza: '9403.60.00.000 A' })];
    app.CDI.state.operacion = { vendedor_nombre: 'Proveedor Sintético', numero_factura: 'FA-1' };
    app.CDI.mientrasAprende = () => {
      app.ponerCliente(flagJson);
      app.CDI.state.operacion = { numero_factura: 'OTRA' };
    };
    app.handlers.ready.onEnter();
    await esperarRed(app, '/productos');
    return app;
  },
  // Listo sin cliente: el panel crea uno sin CUIT y, si el guardado falla, se reintenta.
  'crear-reintento': async () => {
    const app = await listoSinCliente();
    for (let vez = 1; vez <= 2 && !app.node('readyOrphanPanel').hidden; vez++) {
      click(app, 'orphanCreateSaveBtn');
      await esperarRed(app, '/operaciones', vez);
    }
    return app;
  },
  // Crear A y asignar B fallan al guardar; después se vuelve a tocar crear.
  'crear-asignar-crear': async () => {
    const app = await listoSinCliente({
      openClientePicker: ({ onSelect }) => onSelect({ id: 7, nombre: 'Cliente Sintético' }),
    });
    for (const [vez, boton] of [[1, 'orphanCreateSaveBtn'], [2, 'orphanAssignBtn'], [3, 'orphanCreateSaveBtn']]) {
      click(app, boton);
      await esperarRed(app, '/operaciones', vez);
    }
    return app;
  },
  // Crear guarda bien; la operación siguiente, otra vez sin cliente, crea otro.
  'crear-y-otra': async () => {
    const app = await listoSinCliente();
    click(app, 'orphanCreateSaveBtn');
    await esperarRed(app, '/operaciones');
    app.ponerCliente(null);
    app.CDI.state.operationSavedFor = null;
    app.handlers.ready.onEnter();
    await esperarRed(app, '/generate_maria', 2);
    click(app, 'orphanCreateSaveBtn');
    await esperarRed(app, '/operaciones', 2);
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
    const { app, sim } = pasoNcm();
    // render() vuelve a enganchar sobre el mismo nodo falso: se dispara lo que había.
    for (const fn of [...sim.listeners.blur]) fn({ target: sim });
    await esperarRed(app, '/api/ncm/guardar-uso');
    return app;
  },
  // Paso de NCM: Enter abre el buscador y Enter con la posición escrita la asigna.
  'asignar-ncm': async () => {
    const { app, sim } = pasoNcm();
    enter(sim);
    app.node('spotSearch').value = '94036000000A';
    enter(app.node('spotSearch'));
    await esperarRed(app, '/api/ncm/guardar-uso');
    return app;
  },
};

escenarios[escenario]().then(app => {
  const caja = app.node('readyClientSuccess'), [titulo] = caja.querySelectorAll('[data-client-success-title]');
  const [texto] = caja.querySelectorAll('[data-client-success-text]');
  process.stdout.write(JSON.stringify({
    toasts: app.toasts, panelAbierto: !app.node('readyOrphanPanel').hidden,
    clientesCreados: app.llamadas.filter(u => u.endsWith('/api/clientes')).length,
    operaciones: app.operaciones.map(o => ({ url: o.url, factura: o.resumen.numero_factura })),
    catalogo: app.llamadas.filter(u => u.includes('/api/catalog/')), hints: app.hints,
    caja: caja.hidden ? null : { titulo: titulo.textContent, texto: texto.textContent },
  }));
}, err => { console.error(err && err.stack || err); process.exit(2); });
