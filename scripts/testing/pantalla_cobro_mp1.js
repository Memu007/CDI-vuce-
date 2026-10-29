// COBRO-MP-1 C y D en el perfil, contra el servidor local (sin terceros).
// C: con el plan vencido (past_due) se ve «Cancelar plan» y la confirmación
// no promete el «período ya pagado»; con el plan activo, sí.
// D: dos clics en «Activar plan» piden un solo checkout. «Activar plan»,
// «Reactivar plan» y «Activar plan ahora» (el aviso de arriba) quedan
// deshabilitados mientras el navegador va a Mercado Pago, y volver de ahí
// con «Atrás» recarga la página.
// El estado de cobro y las respuestas de cancelar y del checkout se fuerzan
// con page.route: las pruebas del servidor cubren cuándo salen de verdad.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_cobro_mp1.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const reg = await page.request.post(base + '/auth/register', { data: { username: 'cmp1_' + id, password: 'Clave-Inventada-123', email: 'cmp1' + id + '@ejemplo.test' } });
  if (!reg.ok()) falla('no se pudo registrar: ' + reg.status());

  const cancelar = page.locator('#pfBillingCancel');
  const activar = page.locator('#pfBillingActivate');
  const texto = page.locator('#cdiConfirmText');
  const aceptar = page.locator('#cdiConfirmAccept');

  // Abre el perfil con el estado de cobro forzado.
  async function perfilCon(estado, extra) {
    await page.unroute('**/api/billing/me');
    await page.route('**/api/billing/me', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ billing_status: estado, plan: 'premium', trial_ends_at: '2026-10-20T00:00:00Z',
                             ops_used_this_period: 3, ops_limit: 50, extra_ops_remaining: 0, ...(extra || {}) }) }));
    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.openProfileModal);
    await page.evaluate(() => CDI.openProfileModal());
    await page.waitForFunction(() => {
      const el = document.getElementById('pfBillingStatus');
      return el && el.textContent.trim() !== '—';
    }, null, { timeout: 10000 }).catch(() => falla(estado + ': el perfil no cargó el cobro'));
    // «Plan y facturación» es un <details> cerrado: se abre como lo abre la persona.
    await page.click('#pfBillingBlock > summary');
    await page.waitForFunction(() => document.getElementById('pfBillingBlock').open);
  }

  // Abre la confirmación de cancelar, devuelve su texto y la cierra.
  async function confirmacionDeCancelar(estado) {
    if (!await cancelar.isVisible()) falla(estado + ': no se ve «Cancelar plan»');
    await cancelar.click();
    await texto.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla(estado + ': no sale la confirmación'));
    const t = (await texto.innerText()).trim();
    const a = (await aceptar.innerText()).trim();
    await page.click('#cdiConfirmCancel');
    return { t, a };
  }

  // C. past_due: se ve el botón y la confirmación dice que no hay período pagado.
  await perfilCon('past_due');
  const pd = await confirmacionDeCancelar('past_due');
  if (pd.t.includes('ya pagado')) falla('past_due: la confirmación promete el período ya pagado: «' + pd.t + '»');
  if (!pd.t.includes('pago pendiente')) falla('past_due: la confirmación no habla del pago pendiente: «' + pd.t + '»');
  if (pd.a !== 'Sí, cancelar') falla('past_due: el botón de aceptar dice «' + pd.a + '»');
  console.log('OK | past_due: se ve «Cancelar plan» y la confirmación dice «' + pd.t + '»');

  // Cancelar de verdad desde past_due llama al servidor y vuelve a cargar el cobro.
  let cancelados = 0;
  await page.route('**/api/billing/cancel', route => {
    cancelados++;
    route.fulfill({ status: 200, contentType: 'application/json',
                    body: JSON.stringify({ success: true, billing_status: 'canceled', service_until: null }) });
  });
  await cancelar.click();
  await aceptar.waitFor({ state: 'visible', timeout: 5000 });
  await aceptar.click();
  await page.waitForFunction(() => document.getElementById('pfBillingCancel').textContent.trim() === 'Cancelar plan'
                                   && !document.getElementById('pfBillingCancel').disabled, null, { timeout: 5000 })
    .catch(() => falla('past_due: cancelar no termina'));
  if (cancelados !== 1) falla('past_due: cancelar pidió ' + cancelados + ' veces');
  await page.unroute('**/api/billing/cancel');
  console.log('OK | past_due: cancelar llama una vez al servidor');

  // El plan activo sigue diciendo el período ya pagado.
  await perfilCon('active');
  const ac = await confirmacionDeCancelar('active');
  if (!ac.t.includes('ya pagado')) falla('active: la confirmación no dice el período ya pagado: «' + ac.t + '»');
  console.log('OK | active: la confirmación dice el período ya pagado');

  // Cancelada que reactivó y abrió el checkout: tiene una suscripción que
  // cancelar, y se ve «Cancelar plan». Sin suscripción, no.
  await perfilCon('canceled', { suscripcion_abierta: true });
  const ca = await confirmacionDeCancelar('canceled con suscripción abierta');
  if (!ca.t.includes('ya pagado')) falla('canceled con suscripción abierta: la confirmación no dice el período ya pagado: «' + ca.t + '»');
  console.log('OK | canceled con suscripción abierta: se ve «Cancelar plan»');
  await perfilCon('canceled', { suscripcion_abierta: false });
  if (await cancelar.isVisible()) falla('canceled sin suscripción: se ve «Cancelar plan»');
  console.log('OK | canceled sin suscripción: no se ve «Cancelar plan»');

  // D. Dos clics en «Activar plan»: un solo checkout, y el botón deshabilitado mientras espera.
  await perfilCon('past_due');
  if (!await activar.isVisible()) falla('past_due: no se ve «Activar plan»');
  const pedidos = [];
  let soltar;
  const suelto = new Promise(r => { soltar = r; });
  await page.route('**/api/billing/checkout', async route => {
    pedidos.push(1);
    await suelto;
    route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'checkout de prueba' }) });
  });
  const textoAntes = (await activar.innerText()).trim();
  await activar.dblclick();
  await page.waitForFunction(() => document.getElementById('pfBillingActivate').disabled, null, { timeout: 5000 })
    .catch(() => falla('el botón «Activar plan» no se deshabilita mientras pide el checkout'));
  // Un tercer clic sobre el botón deshabilitado tampoco pide otro.
  await activar.click({ force: true }).catch(() => {});
  soltar();
  await page.waitForFunction(t => !document.getElementById('pfBillingActivate').disabled
                                  && document.getElementById('pfBillingActivate').textContent.trim() === t,
                             textoAntes, { timeout: 5000 })
    .catch(() => falla('el botón «Activar plan» no vuelve a su estado después del error'));
  if (pedidos.length !== 1) falla('dos clics en «Activar plan» pidieron ' + pedidos.length + ' checkouts');
  console.log('OK | dos clics en «Activar plan»: un checkout, botón deshabilitado mientras espera');

  // Después del error, sin recargar la página, otro clic vuelve a pedir el
  // checkout: el que falló no deja trabados a los demás botones.
  await Promise.all([
    page.waitForRequest('**/api/billing/checkout', { timeout: 5000 })
      .catch(() => falla('después de un checkout fallido, «Activar plan» no vuelve a pedirlo')),
    activar.click(),
  ]);
  console.log('OK | después de un checkout fallido, «Activar plan» vuelve a pedirlo');

  // Con el checkout creado, el botón queda deshabilitado mientras el navegador
  // va a Mercado Pago: otro clic pediría un segundo checkout, que cancela la
  // suscripción adonde está yendo. Vale para los tres botones que lo piden.
  await page.unroute('**/api/billing/checkout');
  const mercadoPago = base + '/mercado-pago-de-prueba-' + id;
  // Mercado Pago de prueba contesta 204: el navegador intenta ir y se queda en
  // la página, como si la navegación no hubiera terminado todavía.
  let llego = () => {};
  await page.route(mercadoPago, route => { llego(); route.fulfill({ status: 204 }); });
  await page.route('**/api/billing/checkout', route => route.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, init_point: mercadoPago }) }));

  // Pide el checkout con `pedir` y comprueba que el botón siga deshabilitado
  // cuando el navegador ya va a Mercado Pago.
  async function sigueDeshabilitado(nombre, selector, pedir) {
    const yendo = new Promise(r => { llego = r; });
    await pedir();
    let reloj;
    const tope = new Promise(r => { reloj = setTimeout(r, 10000); })
      .then(() => falla('«' + nombre + '»: el navegador no va a Mercado Pago'));
    await Promise.race([yendo, tope]);
    clearTimeout(reloj);
    if (!await page.evaluate(s => document.querySelector(s).disabled, selector))
      falla('«' + nombre + '» se vuelve a habilitar mientras el navegador va a Mercado Pago');
    console.log('OK | con el checkout creado, «' + nombre + '» sigue deshabilitado mientras va a Mercado Pago');
  }

  await perfilCon('past_due');
  await sigueDeshabilitado('Activar plan', '#pfBillingActivate', () => activar.click());

  // Si vuelve con «Atrás» y el navegador restaura la página de su caché, se
  // recarga: el botón y el estado de cobro que mostraba quedaron viejos. La
  // restauración se simula con el evento, porque Chromium automatizado no la
  // hace de forma confiable.
  await Promise.all([
    page.waitForEvent('load', { timeout: 5000 })
      .catch(() => falla('volver de Mercado Pago con «Atrás» no recarga la página')),
    page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))).catch(() => {}),
  ]);
  console.log('OK | volver de Mercado Pago con «Atrás» recarga la página');

  await page.route('**/api/billing/reactivate', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ success: true, needs_checkout: true, message: 'Tu período pagado terminó.' }) }));
  await perfilCon('canceled', { suscripcion_abierta: false });
  await sigueDeshabilitado('Reactivar plan', '#pfBillingReactivate', async () => {
    await page.click('#pfBillingReactivate');
    await aceptar.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla('reactivar: no sale la confirmación'));
    await aceptar.click();
  });
  await page.unroute('**/api/billing/reactivate');

  // El aviso de arriba sale con el estado de /auth/current_user.
  await page.route('**/auth/current_user', async route => {
    const res = await route.fetch();
    route.fulfill({ response: res, json: { ...(await res.json()), billing_status: 'past_due' } });
  });
  await page.goto(base + '/dashboard');
  await page.locator('#billingBannerCta').waitFor({ state: 'visible', timeout: 10000 })
    .catch(() => falla('past_due: no sale el aviso con «Activar plan ahora»'));
  await sigueDeshabilitado('Activar plan ahora', '#billingBannerCta', () => page.click('#billingBannerCta'));

  // Con el aviso y el perfil a la vista hay dos botones que piden el checkout:
  // mientras uno lo pide, el otro no pide un segundo.
  await page.unroute('**/api/billing/checkout');
  const cruzados = [];
  let soltarCruce;
  const sueltoCruce = new Promise(r => { soltarCruce = r; });
  await page.route('**/api/billing/checkout', async route => {
    cruzados.push(1);
    await sueltoCruce;
    route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'checkout de prueba' }) });
  });
  await perfilCon('past_due');
  await page.locator('#billingBannerCta').waitFor({ state: 'visible', timeout: 10000 })
    .catch(() => falla('past_due: no sale el aviso con «Activar plan ahora»'));
  await page.evaluate(() => document.getElementById('billingBannerCta').click());
  await page.waitForFunction(() => document.getElementById('billingBannerCta').disabled, null, { timeout: 5000 })
    .catch(() => falla('«Activar plan ahora» no se deshabilita mientras pide el checkout'));
  await page.evaluate(() => document.getElementById('pfBillingActivate').click());
  soltarCruce();
  await page.waitForFunction(() => !document.getElementById('billingBannerCta').disabled, null, { timeout: 5000 })
    .catch(() => falla('«Activar plan ahora» no vuelve a su estado después del error'));
  if (cruzados.length !== 1) falla('«Activar plan ahora» y después «Activar plan» pidieron ' + cruzados.length + ' checkouts');
  console.log('OK | «Activar plan ahora» y «Activar plan» a la vez: un checkout');

  await b.close();
  console.log('pantalla COBRO-MP-1: OK');
})().catch(e => falla(String(e && e.stack || e)));
