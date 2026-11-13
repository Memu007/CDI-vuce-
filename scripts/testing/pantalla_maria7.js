// MARIA-7 en el navegador local (sin terceros: la subida y /generate_maria se
// interceptan). Al subir, la fecha ambigua se pregunta con el título de la
// factura.
// En «Lo que decide el despachante»: la unidad de la factura y la estadística
// por operación, con cambio por producto. El pedido lleva la unidad de cada
// producto, la estadística sólo si es kilos, y el número real de la factura.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria7.js [captura-telefono.png]
const { chromium } = require('playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  await registrarCuenta(page.request, base, { data: { username: 'm7_' + id, password: 'Clave-Inventada-123', email: 'm7' + id + '@ejemplo.test' } });

  await page.route('**/generate_maria', async r => { await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, filename: 'MARIA_X.TXT', download_url: '#', content: '', supuestos: [] }) }); });
  // La subida se simula: la fecha ambigua llega como pregunta, con el título de la factura.
  const PREGUNTA = 'Fecha de emisión: «07/08/2026» puede ser el 7 de agosto o el 8 de julio; no se adivina. Cargala en la revisión (DD/MM/AAAA).';
  await page.route('**/upload_pdf/public', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
    message: 'ok', filename: 'factura.pdf', items_count: 1, avisos: [], avisos_fecha: [PREGUNTA],
    operacion: { numero_factura: 'INV-2026/0457', fecha_emision: '' },
    items: [{ descripcion: 'Lona de PVC gris', cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62, origen: 'CN', pieza: '' }] }) }));
  await page.goto(base + '/dashboard');
  // Una subida anterior a la primera pantalla del tablero se descarta o no prende el semáforo.
  await page.waitForSelector('[data-screen="upload"].is-active', { state: 'attached' });
  await page.setInputFiles('#uploadFileInput', { name: 'factura.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4\n%%EOF\n') });
  const aviso = page.locator('#toastHost .toast', { hasText: PREGUNTA });
  await aviso.waitFor({ timeout: 10000 }).catch(() => falla('la pregunta por la fecha no aparece al subir'));
  const titulo = await aviso.locator('.toast-title').textContent();
  if (titulo !== 'Revisá la factura') falla('título del aviso de la fecha: ' + titulo);
  console.log('OK la fecha ambigua se pregunta al subir, con el título «Revisá la factura»');

  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante && CDI.despachante.unidadesDe);
  await page.evaluate(() => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = { numero_factura: 'INV-2026/0457', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026', sbt_sufijo_valor: 'AA(1)-CA00-' };
    CDI.state.items = [
      { pieza: '39219019900Z', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62 },
      { pieza: '39219019900Z', descripcion: 'Lona de PVC negra', origen: 'CN', cantidad: 10, valor_unitario: 5, peso_unitario: 1, unidad: 'ROLLS' },
    ];
    CDI.goTo('validating');
  });
  await page.waitForFunction(() => document.querySelectorAll('.despachante-unidad').length === 2, null, { timeout: 10000 }).catch(() => falla('no aparecen las unidades por producto'));
  const propias = await page.$$eval('.despachante-unidad', s => s.map(x => x.value));
  if (propias[0] !== '' || propias[1] !== 'ROLLS') falla('unidad por producto al entrar: ' + JSON.stringify(propias));
  console.log('OK la unidad que trae el producto se muestra tal cual; el otro, igual que la operación');

  await page.selectOption('#despachanteUnidad', '03');
  await page.selectOption('#despachanteUnidadEst', '01');
  await page.selectOption('.despachante-unidad[data-row="1"]', '07');
  await page.selectOption('.despachante-unidad-est[data-row="1"]', 'DCL');
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });
  const anchoPagina = await page.evaluate(() => document.documentElement.scrollWidth);
  console.log('ancho de la página a 390 px: ' + anchoPagina);

  await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
    .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
  const pedida = page.waitForRequest('**/generate_maria', { timeout: 5000 }).catch(() => falla('no se pidió el TXT'));
  await page.click('#validatingGenerate');
  const pedido = JSON.parse((await pedida).postData());
  const u = pedido.items.map(i => [i.unidad, i.unidad_estadistica]);
  if (JSON.stringify(u) !== JSON.stringify([['03', '01'], ['07', null]])) falla('unidades del pedido: ' + JSON.stringify(u));
  if (pedido.numero_factura !== 'INV-2026/0457') falla('número de factura: ' + pedido.numero_factura);
  console.log('OK el pedido lleva m² y kilos de la operación, la unidad y la estadística elegidas en el producto y el número real de la factura');
  await b.close();
  console.log('PANTALLA MARIA-7 OK');
})().catch(e => falla(e && e.stack || e));
