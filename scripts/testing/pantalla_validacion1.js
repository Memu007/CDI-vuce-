// VALIDACION-1 en el navegador local, contra el servidor local (sin terceros).
// Dos cargas distintas, una atrás de la otra en menos de 60 s: el panel de
// totales, el botón «Generar» y lo que se guarda en el historial salen de la
// carga que se ve, no de la anterior, aunque la anterior conteste después o
// el validador falle. La misma carga, sin cambios, reusa su validación sin
// volver a pedirla. Cada caso corre en una página nueva.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_validacion1.js
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
const cargarCuitDelPerfil = require('./_cuit_perfil');
const OP = { moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026' };
const A = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
            valor_unitario: 1.85, peso_unitario: 0.62 };
const B = { pieza: '73181500900A', descripcion: 'Tornillo de acero', origen: 'CN', cantidad: 40,
            valor_unitario: 0.5, peso_unitario: 0.01 };
const SIN_PESO = it => ({ ...it, peso_unitario: 0 });   // error que frena «Generar»
const total = (it, campo) => it.cantidad * it[campo];
const fallas = [];

const PANEL = async page => {
  const nums = await page.$$eval('#validatingStats .validating-stat-num', els => els.map(e => e.textContent));
  const esperado = await page.evaluate(b => {
    const f = n => n.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    return ['1', '$' + f(b.cantidad * b.valor_unitario), f(b.cantidad * b.peso_unitario) + ' kg'];
  }, B);
  const visto = [nums[0], nums[2], nums[3]];
  if (visto.join('|') !== esperado.join('|')) return 'muestra ' + visto.join(', ') + '; la carga que se ve da ' + esperado.join(', ');
};
const HABILITADO = async page => {
  if (await page.$eval('#validatingGenerate', b => b.disabled)) return 'no deja generar por el error de la anterior';
};
// Además del botón, el clic tiene que llegar a generar: onGenerate corta en silencio si queda el error de la anterior.
const GENERA = async page => {
  const mal = await HABILITADO(page);
  if (mal) return mal;
  const pedido = page.waitForRequest(r => r.method() === 'POST' && new URL(r.url()).pathname === '/generate_maria', { timeout: 15000 });
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
  await page.click('#validatingGenerate');
  if (!await pedido.catch(() => null)) return 'el botón está habilitado pero el clic no genera';
};

const CASOS = [
  { que: 'panel', a: A, b: B, mira: PANEL },
  { que: 'panel, la anterior contesta después', a: A, b: B, validador: 'tarda', mira: PANEL },
  { que: 'botón, error sólo en la que se ve', a: A, b: SIN_PESO(B), mira: async page => {
      if (!await page.$eval('#validatingGenerate', b => b.disabled)) return 'deja generar con el peso en cero';
    } },
  { que: 'botón, error sólo en la anterior', a: SIN_PESO(A), b: B, mira: HABILITADO },
  { que: 'botón, falla el validador', a: SIN_PESO(A), b: B, validador: 'falla', mira: GENERA },
  { que: 'botón, falla al volver a validar la misma', a: SIN_PESO(A), validador: 'falla', mira: async page => {
      if (!await page.$eval('#validatingGenerate', b => b.disabled)) return 'deja generar con el peso en cero';
    } },
  { que: 'panel, misma carga sin cambios', a: B, b: B, mira: async (page, _, pidio) =>
      (pidio() ? 'volvió a pedir la validación de la misma carga' : await PANEL(page)) },
  { que: 'cabecera distinta, mismos ítems', a: B, b: B, opB: { ...OP, flete: '120' }, mira: async (page, _, pidio) => {
      if (!pidio()) return 'no volvió a validar con la cabecera cambiada';
    } },
  { que: 'historial', a: A, b: B, cliente: true, mira: async (page, clienteId) => {
      const guardado = page.waitForRequest(r => r.method() === 'POST' &&
        r.url().endsWith('/api/clientes/' + clienteId + '/operaciones'), { timeout: 15000 });
      await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
      await page.click('#validatingGenerate');
      const r = await guardado.catch(() => null);
      if (!r) return 'no guardó en el historial';
      const res = (r.postDataJSON() || {}).resumen || {};
      const bien = (v, campo) => Math.abs(Number(v) - total(B, campo)) < 0.01;
      if (!bien(res.valor_total, 'valor_unitario') || !bien(res.peso_total, 'peso_unitario'))
        return 'guardó valor ' + res.valor_total + ' y peso ' + res.peso_total + '; la carga que se ve da '
          + total(B, 'valor_unitario') + ' y ' + total(B, 'peso_unitario');
    } },
];

// «Nueva operación» y «Carga manual» con clics; los ítems se ponen como los deja la pantalla de NCM.
// Sin «espera», no aguarda la respuesta. Devuelve qué faltó, o nada.
async function validar(page, item, espera = true, op = OP) {
  await page.click('[data-action="go-upload"]');
  await page.click('#uploadManualBtn');
  await page.evaluate(([op, it]) => { CDI.state.operacion = { ...op }; CDI.state.items = [it]; CDI.goTo('validating'); }, [op, item]);
  if (espera && !await page.waitForFunction(() => !document.getElementById('validatingResults').hidden, null, { timeout: 15000 }).catch(() => null))
    return 'no mostró la validación de la que se ve';
}

// «Volver a validar» sobre la carga que se ve. Devuelve qué faltó, o nada.
async function revalidar(page) {
  const pidio = page.waitForRequest('**/api/validate/smart', { timeout: 15000 });
  await page.click('#validatingRerun');
  if (!await pidio.catch(() => null)) return 'volver a validar no pidió validación';
  if (!await page.waitForFunction(() => !document.getElementById('validatingResults').hidden, null, { timeout: 15000 }).catch(() => null))
    return 'no mostró la validación al volver a validar';
}

// El validador simulado, sólo en su caso: el primer pedido es el de la anterior. «tarda» lo retiene
// hasta que lo suelta el caso; «falla» contesta 500 a los que siguen. Cuenta las respuestas que la página leyó.
async function simular(page, modo) {
  const sim = {};
  let pedidos = 0;
  sim.retenida = new Promise(ok => { sim.soltarla = ok; });
  await page.evaluate(() => {
    const pedir = window.fetch;
    window.__leidas = 0;
    window.fetch = async (...args) => {
      const res = await pedir(...args);
      if (String(args[0]).endsWith('/api/validate/smart')) {
        const leer = res.json.bind(res);
        res.json = async () => { const d = await leer(); window.__leidas++; return d; };
      }
      return res;
    };
  });
  await page.route('**/api/validate/smart', async route => {
    const deLaAnterior = ++pedidos === 1;
    if (modo === 'tarda' && deLaAnterior) { await sim.retenida; return route.fulfill({ response: await route.fetch() }); }
    if (modo === 'falla' && !deLaAnterior) return route.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"validador caído"}' });
    return route.continue();
  });
  return sim;
}

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await registrarCuenta(ctx.request, base, { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: 'val1_' + id, password: 'Clave-Inventada-123', email: 'val1' + id + '@ejemplo.test' } });
  await cargarCuitDelPerfil(ctx.request, base);
  const cli = await ctx.request.post(base + '/api/clientes', { data: { nombre: 'Cliente de prueba', cuit: '30999999995' } });
  const cliente = (await cli.json()).cliente;
  if (!cliente) throw new Error('no se creó el cliente: ' + cli.status());

  for (const c of CASOS) {
    const page = await ctx.newPage();
    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && document.querySelector('.screen.is-active'));
    const sim = c.validador ? await simular(page, c.validador) : null;
    const tarda = c.validador === 'tarda';
    const pidioA = tarda && page.waitForRequest('**/api/validate/smart');
    // La anterior tiene que haberse validado, y con su error si lo trae: si no, el caso no prueba nada.
    let mal = await validar(page, c.a, !tarda) && 'la anterior no mostró su validación';
    if (!mal && !tarda && c.a.peso_unitario === 0 && !await page.$eval('#validatingGenerate', b => b.disabled))
      mal = 'la anterior, con el peso en cero, deja generar';
    const pedidoA = tarda && await pidioA;
    const desde = Date.now();
    const pidioB = tarda && page.waitForRequest(r => r.url().endsWith('/api/validate/smart') && r !== pedidoA, { timeout: 15000 });
    let pidioDespues = 0;
    page.on('request', r => { if (r.method() === 'POST' && r.url().endsWith('/api/validate/smart')) pidioDespues++; });
    mal = mal || (c.b ? await validar(page, c.b, true, c.opB) : await revalidar(page));
    if (tarda) {
      if (!await pidioB.catch(() => null)) mal = mal || 'la que se ve no pidió validación mientras la anterior esperaba';
      sim.soltarla();
      // La página ya leyó las dos respuestas: la de la anterior se procesó antes de mirar.
      await page.waitForFunction(() => window.__leidas === 2, null, { timeout: 15000 });
    }
    if (c.cliente) await page.evaluate(cl => CDI.setClienteActivo(cl), cliente);
    if (Date.now() - desde > 50000) throw new Error(c.que + ': entre las dos cargas pasaron más de 50 s');
    mal = mal || await c.mira(page, String(cliente.id), () => pidioDespues);
    if (mal) fallas.push(c.que + ': ' + mal); else console.log('OK | ' + c.que);
    await page.close();
  }
  await b.close();
  if (fallas.length) { fallas.forEach(f => console.error('FALLA: ' + f)); process.exit(1); }
  console.log('pantalla VALIDACION-1: OK');
})().catch(e => { console.error('FALLA: ' + String(e && e.stack || e)); process.exit(1); });
