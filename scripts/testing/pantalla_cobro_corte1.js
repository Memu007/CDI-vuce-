// COBRO-CORTE-1 en el navegador local, contra el servidor local (sin terceros).
// Sin factura, generar dos veces la misma operación manda el mismo id (el de
// cuándo se cargó) y el servidor la cuenta una vez. Un 402 dice su razón en
// el modal y en el error de la generación; el 409 de regeneraciones, su
// mensaje. Los 402 y el 409 se fuerzan con page.route: las pruebas del
// servidor cubren cuándo salen de verdad.
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
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'cc1_' + id, password: 'Clave-Inventada-123', email: 'cc1' + id + '@ejemplo.test' } });

  // Sin el CUIT del despachante no se genera el TXT (ESTUDIO-1); inventado.
  const perfil = await page.request.put(base + '/api/user/profile', { data: { cuit: '20999999998' } });
  if (!perfil.ok()) falla('no se pudo cargar el CUIT del perfil: ' + perfil.status());

  const errorGeneracion = page.locator('#readyErrorText');
  const titulo = page.locator('#cdiConfirmTitle');
  const lead = page.locator('#cdiConfirmLead');

  // Carga la operación (sin factura, cargada en CARGADA), pide el TXT y
  // devuelve el status y el operation_id que mandó la pantalla.
  async function generar() {
    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api);
    await page.evaluate(([op, item, cargada]) => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = op;
      CDI.state.items = [item];
      CDI.state.uploadedAt = cargada;
      CDI.goTo('validating');
    }, [OP, LONA, CARGADA]);
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
    await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
    const resp = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
    await page.click('#validatingGenerate');
    const r = await resp.catch(() => falla('no se pidió el TXT'));
    return { status: r.status(), texto: (await r.text()).slice(0, 300),
             operation_id: JSON.parse(r.request().postData() || '{}').operation_id };
  }

  async function usadas() {
    const r = await page.request.get(base + '/api/billing/me');
    if (!r.ok()) falla('/api/billing/me dio ' + r.status());
    return (await r.json()).ops_used_this_period;
  }

  // 1. Regenerar sin factura manda el mismo id y no cuenta otra vez.
  const antes = await usadas();
  const g1 = await generar();
  if (g1.status !== 200) falla('la primera generación dio ' + g1.status + ': ' + g1.texto);
  const g2 = await generar();
  if (g2.status !== 200) falla('la segunda generación dio ' + g2.status + ': ' + g2.texto);
  if (g1.operation_id !== ID) falla('el id sin factura no sale de cuándo se cargó: ' + g1.operation_id);
  if (g2.operation_id !== g1.operation_id) falla('regenerar mandó otro id: ' + g1.operation_id + ' y ' + g2.operation_id);
  const despues = await usadas();
  if (despues - antes !== 1) falla('dos generaciones del mismo id contaron ' + (despues - antes));
  console.log('OK | regenerar sin factura: mismo id (' + ID + ') y cuenta 1');

  // 2. Un 402 dice su razón.
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

  // 3. El 409 de regeneraciones muestra su mensaje.
  const msg409 = 'Esta operación ya se generó 10 veces con datos distintos, el máximo. Si es otra operación, cargala como nueva.';
  await page.route('**/generate_maria', route => route.fulfill({
    status: 409, contentType: 'application/json',
    body: JSON.stringify({ detail: { code: 'MARIA_REGENERACIONES_AGOTADAS', message: msg409 } }) }));
  await generar();
  await errorGeneracion.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla('409: no sale el error de la generación'));
  if ((await errorGeneracion.innerText()).trim() !== msg409) falla('409: el error de la generación dice «' + (await errorGeneracion.innerText()).trim() + '»');
  console.log('OK | 409: su mensaje');

  await b.close();
  console.log('pantalla COBRO-CORTE-1: OK');
})().catch(e => falla(String(e && e.stack || e)));
