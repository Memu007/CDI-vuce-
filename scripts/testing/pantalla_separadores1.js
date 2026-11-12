// SEPARADORES-1 en el navegador local, contra el servidor local (sin terceros).
// En la revisión se escribe el flete «2.750» y el seguro «1.234,50» a mano:
// la revisión los guarda como 2750 y 1234.5, y el TXT sale con
// MDDTFLE=2750.00 y MDDTASS=1234.50. Un flete «1,500» (¿mil quinientos o uno
// con cinco?) muestra la pregunta bajo el campo y no deja continuar.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_separadores1.js [captura.png]
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const OP = { numero_factura: 'INV-2026/0458', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671',
             comprador_nombre: 'Importadora Inventada SA', vendedor_nombre: 'Proveedor Inventado Ltd',
             fecha_emision: '10/10/2026', flete: 0, seguro: 0, cuit_agr: '20123456786' };
const LONA = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };
const CLIENTE = { id: 1, cuit: '30712345671', razon_social: 'Importadora Inventada SA' };
const PREGUNTA = '¿1.500 o 1,5? Escribilo con punto de miles (1.500) o como 1,5.';

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: 's1_' + id, password: 'Clave-Inventada-123', email: 's1' + id + '@ejemplo.test' } });
  const pantalla = () => page.$eval('.screen.is-active', el => el.dataset.screen);

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante);
  await page.evaluate(([op, items, cliente]) => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = op;
    CDI.state.items = items;
    CDI.state.clienteActivo = cliente;
    CDI.goTo('review');
  }, [OP, [{ ...LONA }], CLIENTE]);
  await page.waitForSelector('#f_flete', { state: 'visible' });

  // 1. «1,500»: la pregunta bajo el campo, y continuar no avanza.
  await page.fill('#f_flete', '1,500');
  await page.press('#f_flete', 'Tab');
  const error = page.locator('[data-error-for="flete"]');
  await error.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla('«1,500» no muestra nada bajo el flete'));
  if (await error.innerText() !== PREGUNTA) falla('bajo el flete dice otra cosa: ' + await error.innerText());
  if (process.argv[2]) await page.locator('#f_flete').locator('xpath=ancestor::fieldset[1]').screenshot({ path: process.argv[2] });
  if (await page.isDisabled('#reviewContinueBtn')) {
    falla('continuar está deshabilitado por otra cosa: ' + await page.locator('#reviewMissingCount').innerText());
  }
  await page.click('#reviewContinueBtn');
  if (await pantalla() !== 'review') falla('con «1,500» continuar pasó a ' + await pantalla());
  console.log('OK «1,500» muestra «' + PREGUNTA + '» y no deja continuar');

  // 2. «2.750» y «1.234,50»: se guardan enteros y continuar avanza.
  await page.fill('#f_flete', '2.750');
  await page.fill('#f_seguro', '1.234,50');
  await page.press('#f_seguro', 'Tab');
  if (await error.isVisible()) falla('con «2.750» sigue el error: ' + await error.innerText());
  const guardado = await page.evaluate(() => [CDI.state.operacion.flete, CDI.state.operacion.seguro]);
  if (guardado[0] !== 2750 || guardado[1] !== 1234.5) falla('la revisión guardó ' + JSON.stringify(guardado) + ' y no [2750,1234.5]');
  console.log('OK la revisión guarda flete 2750 y seguro 1234.5');
  await page.click('#reviewContinueBtn');
  await page.waitForFunction(() => document.querySelector('.screen.is-active').dataset.screen !== 'review', null, { timeout: 5000 })
    .catch(() => falla('con «2.750» continuar no avanza'));
  console.log('OK continuar avanza a ' + await pantalla());

  // 3. El TXT, con la operación que dejó la revisión.
  await page.evaluate(() => CDI.goTo('validating'));
  await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
    .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');
  const resp = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
  await page.click('#validatingGenerate');
  const r = await resp.catch(() => falla('no se pidió el TXT'));
  const pedido = JSON.parse(r.request().postData());
  if (pedido.flete !== 2750 || pedido.seguro !== 1234.5) {
    falla('el pedido lleva flete ' + pedido.flete + ' y seguro ' + pedido.seguro);
  }
  if (r.status() !== 200) falla('el TXT no salió: ' + r.status() + ' ' + (await r.text()).slice(0, 300));
  const txt = (await r.json()).content || '';
  for (const linea of ['MDDTFLE=2750.00', 'MDDTASS=1234.50']) {
    if (!txt.split(/\r?\n/).includes(linea)) falla('el TXT no tiene ' + linea + ': ' + (txt.match(/^MDDT(FLE|ASS)=.*$/gm) || []).join(' '));
  }
  console.log('OK el TXT sale con MDDTFLE=2750.00 y MDDTASS=1234.50');

  await b.close();
  console.log('PANTALLA SEPARADORES-1 OK');
})().catch(e => falla(e && e.stack || e));
