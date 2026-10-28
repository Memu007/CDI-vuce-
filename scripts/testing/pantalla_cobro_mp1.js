// COBRO-MP-1 C y D en el perfil, contra el servidor local (sin terceros).
// C: con el plan vencido (past_due) se ve «Cancelar plan» y la confirmación
// no promete el «período ya pagado»; con el plan activo, sí.
// D: dos clics en «Activar plan» piden un solo checkout, y el botón queda
// deshabilitado mientras espera.
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
  async function perfilCon(estado) {
    await page.unroute('**/api/billing/me');
    await page.route('**/api/billing/me', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ billing_status: estado, plan: 'premium', trial_ends_at: '2026-10-20T00:00:00Z',
                             ops_used_this_period: 3, ops_limit: 50, extra_ops_remaining: 0 }) }));
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

  await b.close();
  console.log('pantalla COBRO-MP-1: OK');
})().catch(e => falla(String(e && e.stack || e)));
