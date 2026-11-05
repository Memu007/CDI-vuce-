// COBRO-CORTE-1 en el navegador local, contra el servidor local (sin terceros).
// La pantalla manda la operación del servidor: regenerar manda la que devolvió
// la primera generación y cuenta una vez; una carga nueva manda un id vacío y
// cuenta otra; guardar antes de generar anota la operación y generar la
// completa. Un 402 dice su razón en el modal y en el error de la generación;
// los 402 se fuerzan con page.route: las pruebas del servidor cubren cuándo salen.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_cobro_corte1.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const OP = { moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026' };
const LONA = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };
const CARGADA = '2026-10-28T05:00:00.123Z';
const ID = 'OP_20261028050000123';

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
  const page = await ctx.newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const reg = await page.request.post(base + '/auth/register', { data: { username: 'cc1_' + id, password: 'Clave-Inventada-123', email: 'cc1' + id + '@ejemplo.test' } });
  if (!reg.ok()) falla('no se pudo registrar: ' + reg.status());

  // Sin el CUIT del despachante no se genera el TXT (ESTUDIO-1); inventado.
  const perfil = await page.request.put(base + '/api/user/profile', { data: { cuit: '20999999998' } });
  if (!perfil.ok()) falla('no se pudo cargar el CUIT del perfil: ' + perfil.status());

  const errorGeneracion = page.locator('#readyErrorText');
  const titulo = page.locator('#cdiConfirmTitle');
  const lead = page.locator('#cdiConfirmLead');

  // Pone la operación en la pantalla sin tocar su operacionId.
  async function cargar(cargada) {
    await page.evaluate(([op, item, cargada]) => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = op;
      CDI.state.items = [item];
      if (cargada) CDI.state.uploadedAt = cargada;
    }, [OP, LONA, cargada]);
  }

  // Pide el TXT desde «validating», sin recargar: recargar fuera del flujo pierde la operación.
  async function pedirTxt() {
    await page.evaluate(() => CDI.goTo('validating'));
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
    await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
    await page.click('#validatingGenerate');
  }
  async function generar() {
    const resp = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
    await pedirTxt();
    const r = await resp.catch(() => falla('no se pidió el TXT'));
    const texto = await r.text();
    const pedido = JSON.parse(r.request().postData() || '{}');
    let devuelta = '';
    try { devuelta = JSON.parse(texto).operacion_id || ''; } catch (_) {}
    return { status: r.status(), texto: texto.slice(0, 300), operation_id: pedido.operation_id,
             mandada: pedido.operacion_id, devuelta };
  }

  async function usadas() {
    const r = await page.request.get(base + '/api/billing/me');
    if (!r.ok()) falla('/api/billing/me dio ' + r.status());
    return (await r.json()).ops_used_this_period;
  }

  await page.goto(base + '/dashboard');
  // El arranque elige su pantalla sin esperar: hasta que lo hace, pisaría la de la prueba.
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && document.querySelector('.screen.is-active'));

  // 1. Regenerar manda la operación que devolvió la primera y no cuenta otra vez.
  let antes = await usadas();
  await cargar(CARGADA);
  const g1 = await generar();
  if (g1.status !== 200) falla('la primera generación dio ' + g1.status + ': ' + g1.texto);
  if (g1.mandada !== '') falla('la primera generación mandó operacion_id «' + g1.mandada + '»');
  if (!g1.devuelta) falla('la primera generación no devolvió operacion_id: ' + g1.texto);
  if (g1.operation_id !== ID) falla('el id sin factura no sale de cuándo se cargó: ' + g1.operation_id);
  const g2 = await generar();
  if (g2.status !== 200) falla('la segunda generación dio ' + g2.status + ': ' + g2.texto);
  if (g2.mandada !== g1.devuelta) falla('regenerar manda la operación que devolvió la primera: mandó «' + g2.mandada + '», no «' + g1.devuelta + '»');
  if (g2.operation_id !== g1.operation_id) falla('el id sin factura no sale de cuándo se cargó: ' + g1.operation_id + ' y ' + g2.operation_id);
  if (await usadas() - antes !== 1) falla('dos generaciones de la misma operación contaron ' + (await usadas() - antes));
  console.log('OK | regenerar: manda la operación de la primera y cuenta 1');

  // 2. Una carga nueva es otra operación: manda un id vacío y cuenta.
  antes = await usadas();
  await page.evaluate(() => CDI.goTo('upload'));
  await page.click('#uploadManualBtn');
  await cargar(null);
  const g3 = await generar();
  if (g3.status !== 200) falla('la generación de la carga nueva dio ' + g3.status + ': ' + g3.texto);
  if (g3.mandada !== '') falla('una operación nueva manda un operacion_id vacío: mandó «' + g3.mandada + '»');
  if (g3.devuelta === g1.devuelta) falla('la carga nueva quedó en la operación anterior');
  if (await usadas() - antes !== 1) falla('la carga nueva contó ' + (await usadas() - antes));
  console.log('OK | carga nueva: operacion_id vacío y cuenta 1');

  // 3. Un 402 dice su razón.
  async function con402(detail, tituloEsperado, que) {
    await page.route('**/generate_maria', route => route.fulfill({
      status: 402, contentType: 'application/json', body: JSON.stringify({ detail }) }));
    await generar();
    await titulo.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla(que + ': no sale el modal'));
    if ((await titulo.innerText()).trim() !== tituloEsperado) falla(que + ': el modal se titula «' + (await titulo.innerText()).trim() + '»');
    if ((await lead.innerText()).trim() !== detail.message) falla(que + ': el modal dice «' + (await lead.innerText()).trim() + '»');
    await page.click('#cdiConfirmCancel');
    await errorGeneracion.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla(que + ': no sale el error de la generación'));
    if ((await errorGeneracion.innerText()).trim() !== detail.message) falla(que + ': el error de la generación dice «' + (await errorGeneracion.innerText()).trim() + '»');
    await page.unroute('**/generate_maria');
    console.log('OK | 402 ' + que + ': «' + tituloEsperado + '» y su mensaje');
  }
  await con402({ code: 'PLAN_LIMIT_EXCEEDED', billing_status: 'active',
                 message: 'Alcanzaste el límite de 15 operaciones del plan Básico. Comprá un top-up o actualizá a Premium.' },
               'Llegaste al tope de tu plan', 'tope');
  await con402({ code: 'SUBSCRIPTION_PAST_DUE', billing_status: 'past_due',
                 message: 'Tenés un pago pendiente de tu suscripción. Regularizalo para seguir usando CDI.' },
               'Tenés un pago pendiente', 'impago');
  await con402({ code: 'TRIAL_EXPIRED', billing_status: 'canceled',
                 message: 'Cancelaste tu suscripción. Reactivala para seguir usando CDI.' },
               'Cancelaste tu suscripción', 'cancelada');
  await con402({ code: 'PLAN_LIMIT_EXCEEDED', billing_status: 'canceled',
                 message: 'Alcanzaste el límite de 15 operaciones del plan Básico. Comprá un top-up o actualizá a Premium.' },
               'Llegaste al tope de tu plan', 'cancelada con el tope');

  // 4. Guardar antes de generar crea la operación; generar después la completa y no cuenta otra.
  const que = 'guardar antes de generar';
  antes = await usadas();
  await page.evaluate(() => CDI.goTo('upload'));
  await page.click('#uploadManualBtn');
  await cargar(null);
  const guardada = await page.evaluate(async () => {
    const r = await CDI.api('/api/clientes', { method: 'POST', body: JSON.stringify({ nombre: 'Cliente de prueba', cuit: '30999999995' }) });
    const d = await r.json();
    if (!d.cliente) return { error: JSON.stringify(d).slice(0, 200) };
    CDI.setClienteActivo(d.cliente);
    const out = await CDI.saveOperationToHistory(CDI.state.items, {});
    return { out, operacionId: CDI.state.operacionId, clienteId: String(d.cliente.id) };
  });
  if (guardada.error) falla(que + ': no se creó el cliente: ' + guardada.error);
  if (!guardada.out || !guardada.out.ok) falla(que + ': el guardado falló: ' + JSON.stringify(guardada.out));
  if (!guardada.operacionId) falla(que + ': la pantalla no anotó la operación que devolvió el guardado');
  const g4 = await generar();
  if (g4.status !== 200) falla(que + ': la generación dio ' + g4.status + ': ' + g4.texto);
  if (g4.mandada !== guardada.operacionId) falla(que + ': generar mandó «' + g4.mandada + '», no la guardada «' + guardada.operacionId + '»');
  if (await usadas() - antes !== 1) falla(que + ': guardar y generar contaron ' + (await usadas() - antes));
  console.log('OK | ' + que + ': generar completa la guardada y cuenta 1');

  // 5. Una respuesta que llega cuando ya empezó otra carga no le anota su operación a ésa.
  await respuestaTardia();
  async function respuestaTardia() {
    const v1 = await ctx.newPage();
    // La v1 manda a la portada si no encuentra el token en localStorage.
    await v1.addInitScript(t => localStorage.setItem('access_token', t), (await reg.json()).access_token);
    v1.on('dialog', d => d.accept());
    await v1.goto(base + '/dashboard?v=1');
    await v1.waitForFunction(id => typeof generateMariaTxt === 'function' &&
      [...document.querySelectorAll('#clientSelectorGrouping option')].some(o => o.value === id), guardada.clienteId, { timeout: 15000 })
      .catch(() => falla('la v1 no muestra el cliente en el selector'));
    const VIEJA = 'la-operacion-de-la-carga-anterior';
    const bien = { success: true, operacion_id: VIEJA, operation_id: VIEJA, filename: 'MARIA_TARDE.TXT', content: 'X', warnings: [], supuestos: [] };
    async function cargaNuevaV2() {
      await page.evaluate(() => CDI.goTo('upload'));
      await page.click('#uploadManualBtn');
      await cargar(null);
    }
    async function armarV1() {
      await v1.evaluate(id => {
        document.getElementById('groupingSection').classList.remove('hidden');
        document.getElementById('clientSelectorGrouping').value = id;
        window.currentItems = [{ pieza: '39219019900Z', codigo_parte: 'L1', descripcion: 'Lona de PVC gris',
                                 cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62, origen: 'CN' }];
        displayItemsForGrouping(window.currentItems, { '3921': window.currentItems });
        document.getElementById('op_numero_factura').value = 'FAC_TARDE';
      }, guardada.clienteId);
    }
    const RESPUESTA_TARDIA = [
      { que: 'v2, generar', p: page, retenida: '**/generate_maria',
        pedir: async () => { await cargaNuevaV2();
          await page.evaluate(id => CDI.setClienteActivo({ id, nombre: 'Cliente de prueba' }), guardada.clienteId);
          await pedirTxt(); },
        // La carga nueva sin cliente: la respuesta tardía se guarda igual en el de la suya.
        otraCarga: async () => { await cargaNuevaV2(); await page.evaluate(() => CDI.setClienteActivo(null)); },
        guardado: () => page.waitForRequest(r => r.method() === 'POST' &&
          r.url().endsWith('/api/clientes/' + guardada.clienteId + '/operaciones'), { timeout: 15000 }),
        terminada: () => page.waitForFunction(() => !document.getElementById('readyDone').hidden, null, { timeout: 15000 }),
        anotada: () => page.evaluate(() => CDI.state.operacionId) },
      { que: 'v2, guardar', p: page, retenida: '**/api/clientes/*/operaciones',
        pedir: async () => { await cargaNuevaV2();
          await page.evaluate(id => {
            CDI.setClienteActivo({ id, nombre: 'Cliente de prueba' });
            window.guardado = CDI.saveOperationToHistory(CDI.state.items, { filename: 'MARIA_TARDE.TXT' });
          }, guardada.clienteId); },
        otraCarga: cargaNuevaV2,
        terminada: () => page.evaluate(() => window.guardado),
        anotada: () => page.evaluate(() => CDI.state.operacionId) },
      { que: 'v1, generar', p: v1, retenida: '**/generate_maria',
        pedir: async () => { await armarV1(); v1.generada = v1.evaluate(() => generateMariaTxt()); },
        otraCarga: () => v1.evaluate(() => cancelGrouping()),
        terminada: () => v1.generada,
        anotada: () => v1.evaluate(() => operacionIdActual) },
      { que: 'v1, guardar', p: v1, retenida: '**/api/clientes/*/operaciones', inmediata: '**/generate_maria',
        pedir: async () => { await armarV1(); v1.generada = v1.evaluate(() => generateMariaTxt()); },
        otraCarga: () => v1.evaluate(() => cancelGrouping()),
        terminada: () => v1.generada,
        anotada: () => v1.evaluate(() => operacionIdActual) },
    ];
    for (const c of RESPUESTA_TARDIA) {
      let soltar, pedida;
      const suelta = new Promise(r => { soltar = r; });
      const llego = new Promise(r => { pedida = r; });
      await c.p.route(c.retenida, async route => {
        if (route.request().method() !== 'POST') return route.continue();
        pedida();
        await suelta;
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(bien) });
      });
      if (c.inmediata) await c.p.route(c.inmediata, route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(bien) }));
      const aTiempo = (p, que) => Promise.race([p, new Promise((_, no) => setTimeout(() => no(new Error(que)), 15000))]);
      await c.pedir();
      await aTiempo(llego, c.que + ': el pedido no salió').catch(e => falla(e.message));
      await c.otraCarga();
      const guardado = c.guardado && c.guardado().catch(() => null);
      soltar();
      await aTiempo(c.terminada(), c.que + ': no terminó').catch(e => falla(e.message));
      if (guardado) {
        const r = await guardado;
        const mandada = r && (r.postDataJSON() || {}).operacion_id;
        if (mandada !== VIEJA) falla(c.que + ': la respuesta tardía no se guardó en el cliente de su carga con su operación (mandó «' + mandada + '»)');
      }
      const anotada = await c.anotada();
      if (anotada) falla(c.que + ': la respuesta tardía le anotó a la carga nueva la operación «' + anotada + '»');
      await c.p.unroute(c.retenida);
      if (c.inmediata) await c.p.unroute(c.inmediata);
      console.log('OK | ' + c.que + ': la respuesta tardía no toca la carga nueva');
    }
  }

  await b.close();
  console.log('pantalla COBRO-CORTE-1: OK');
})().catch(e => falla(String(e && e.stack || e)));
