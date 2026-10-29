'use strict';
// Graba el recorrido real de CDI (Excel → revisión → NCM → validación → MARIA.TXT)
// con Playwright: video 1440x900, capturas 2x y marcas de tiempo por paso.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.BASE_URL;
const fixture = process.env.FIXTURE;
const clientesCsv = process.env.CLIENTES_CSV;
const out = process.env.OUT;
if (!base || !fixture || !out) throw new Error('Faltan BASE_URL, FIXTURE u OUT');
fs.mkdirSync(path.join(out, 'shots'), { recursive: true });
fs.mkdirSync(path.join(out, 'video'), { recursive: true });

const marks = [];
let t0 = 0;
const mark = (name) => { marks.push({ name, t: +((Date.now() - t0) / 1000).toFixed(3) }); console.log('mark', name, marks[marks.length - 1].t); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function api(page, endpoint, method = 'GET', payload) {
  return page.evaluate(async ({ endpoint, method, payload }) => {
    const options = { method };
    if (payload !== undefined) options.body = JSON.stringify(payload);
    const r = await window.CDI.api(endpoint, options);
    return { status: r.status, body: await r.json().catch(() => ({})) };
  }, { endpoint, method, payload });
}

async function humanFill(page, selector, value, delay = 70) {
  const el = page.locator(selector).first();
  await el.scrollIntoViewIfNeeded();
  await el.click();
  await el.fill('');
  await el.pressSequentially(value, { delay });
  await el.dispatchEvent('change');
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    locale: 'es-AR',
    timezoneId: 'America/Argentina/Buenos_Aires',
    recordVideo: { dir: path.join(out, 'video'), size: { width: 1440, height: 900 } },
  });
  // Factura ficticia en PDF (sólo para mostrar la carga: sin clave de Gemini no se lee).
  const pdfPath = path.join(out, 'factura_SBE-2026-0417.pdf');
  {
    const aux = await browser.newPage();
    await aux.goto('file://' + path.join(__dirname, 'factura.html'));
    await aux.pdf({ path: pdfPath, format: 'A4', printBackground: true });
    await aux.close();
  }
  const page = await ctx.newPage();
  t0 = Date.now();
  page.setDefaultTimeout(20000);
  // Igual que el E2E: ni feed de ARCA ni cotizaciones (externos, no son el flujo).
  await page.route((url) => url.origin === base && ['/api/arca/novedades', '/api/financials'].includes(url.pathname), (route) => route.abort('blockedbyclient'));
  const shot = (name) => page.screenshot({ path: path.join(out, 'shots', `${name}.png`) });

  // 1. Landing
  await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#btnOpenAuth');
  await page.click('#betaBannerClose').catch(() => {});
  await sleep(1200);
  mark('landing');
  await shot('landing');
  await sleep(800);

  // 2. Alta (no se muestra en el video)
  await page.click('#btnOpenAuth');
  await page.waitForSelector('#authPopover:not([hidden])');
  await page.click('#loginForm [data-tab="register"]');
  await page.waitForSelector('#registerForm.is-active');
  await page.fill('#registerForm input[name="name"]', 'Estudio Aduanero Demo');
  await page.fill('#registerForm input[name="email"]', `estudio.demo.${Date.now()}@cdi.test`);
  await page.fill('#registerForm input[name="password"]', 'Demo-video-2026');
  await Promise.all([page.waitForNavigation({ waitUntil: 'domcontentloaded' }), page.click('#registerForm button[type="submit"]')]);
  await page.waitForSelector('#uploadPickBtn');
  await page.waitForFunction(() => Boolean(window.CDI && window.CDI.api));
  await page.waitForSelector('#tourWelcomeModal:not([hidden])');
  await page.click('#tourWelcomeSkip');
  await page.waitForSelector('#tourWelcomeModal[hidden]', { state: 'attached' });

  // Clientes de demostración (CUIT con dígito verificador válido, obviamente ficticio)
  for (const c of [
    { nombre: 'Importadora del Sur S.A.', cuit: '30000000007', direccion: 'Av. Córdoba 1234, CABA', fecha_inic_activ: '2015-03-01', preferred_currency: 'DOL' },
    { nombre: 'Textil Andina S.R.L.', cuit: '30000000015', direccion: 'Ruta 9 km 12, Córdoba', fecha_inic_activ: '2018-07-15', preferred_currency: 'DOL' },
  ]) {
    const r = await api(page, '/api/clientes', 'POST', c);
    if (r.status !== 200) throw new Error('cliente: ' + JSON.stringify(r.body));
  }

  // 3. Upload (sin avisos de beta ni de prueba: los cierra el usuario)
  await page.click('#betaBannerClose').catch(() => {});
  await page.click('#billingBannerClose', { force: true }).catch(() => {});
  await page.evaluate(() => { const b = document.getElementById('billingBanner'); if (b) b.hidden = true; });
  await page.click('[data-action="go-upload"]');
  await page.waitForSelector('[data-screen="upload"].is-active');
  await sleep(1200);
  mark('upload');
  await shot('upload');
  await sleep(600);
  // PDF: se ve el arrastre y «Procesando PDF…». La respuesta se demora para que
  // el estado quede en pantalla; después la lectura falla (sin Gemini) y se corta ahí.
  await page.route((url) => url.pathname === '/upload_pdf/public', async (route) => { await sleep(3500); await route.continue(); });
  await page.setInputFiles('#uploadFileInput', pdfPath);
  await page.waitForSelector('#uploadProgress:not([hidden])');
  mark('pdf');
  await sleep(2400);
  mark('pdf_fin');
  await page.waitForSelector('#uploadProgress[hidden]', { state: 'attached' });
  await sleep(400);
  await page.click('#uploadFormatExcel');
  mark('upload_excel');
  await sleep(900);
  await page.setInputFiles('#uploadFileInput', fixture);
  mark('upload_file');
  await page.waitForSelector('[data-testid="client-picker-row"]');
  mark('picker');
  await sleep(1500);
  await shot('picker');
  await page.locator('[data-testid="client-picker-row"]', { hasText: 'Importadora del Sur' }).first().click();
  await page.waitForSelector('[data-screen="review"].is-active');
  mark('review');
  await sleep(1800);
  await shot('review');

  // 4. Revisión: proveedor, incoterm y fecha tipeados a mano
  await humanFill(page, '#f_vendedor_nombre', 'Shenzhen Bright Electronics Co.', 45);
  await sleep(300);
  await humanFill(page, '#f_incoterm', 'FOB');
  await sleep(400);
  await humanFill(page, '#f_fecha_emision', '20/10/2026');
  await page.waitForFunction(() => !document.getElementById('reviewContinueBtn').disabled);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(1300);
  mark('review_done');
  await shot('review_done');
  await page.click('#reviewContinueBtn');
  await page.waitForSelector('[data-screen="ncm"].is-active');
  mark('ncm');
  await page.waitForFunction(() => document.querySelectorAll('[data-testid="ncm-sim-input"]').length === 3);
  await sleep(1500);
  await shot('ncm');

  // 5. NCM: posición SIM completa por fila (pegada: 11 dígitos + letra)
  const sims = page.locator('[data-testid="ncm-sim-input"]');
  for (let i = 0; i < 3; i++) {
    const el = sims.nth(i);
    await el.scrollIntoViewIfNeeded();
    await el.click();
    await el.evaluate((input, v) => {
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(input, v);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }, '84713012100R');
    await sleep(650);
  }
  const origins = await page.$$eval('[data-testid="ncm-origin-input"]', (els) => els.map((e) => e.value));
  console.log('origins', origins);
  if (!origins.every((v) => /^310/.test(v))) {
    for (let i = 0; i < origins.length; i++) {
      await page.locator('[data-testid="ncm-origin-input"]').nth(i).evaluate((input) => {
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(input, '310');
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }
  }
  await page.waitForFunction(() => !document.getElementById('ncmContinueBtn').disabled);
  await sleep(900);
  mark('ncm_done');
  await shot('ncm_done');
  await page.click('#ncmContinueBtn');

  // 6. Validación
  await page.waitForSelector('#validatingResults:not([hidden])');
  mark('validating');
  await sleep(1800);
  await shot('validating');
  await humanFill(page, '#sbtSufijoValor', 'AA(GENERICA)-AB(NB14)-CA00-', 35);
  await sleep(600);
  mark('validating_done');
  await shot('validating_done');
  await page.click('#validatingGenerate');

  // 7. Listo
  await page.waitForSelector('#readyDone:not([hidden])');
  mark('ready');
  await sleep(2200);
  await shot('ready');
  const preview = await page.$eval('#readyPreview', (el) => el.textContent.slice(0, 300));
  console.log('preview', preview);

  // 8. Tablero de operaciones: estado y canal editables
  await page.click('[data-action="go-cockpit"]');
  await page.waitForSelector('#ckTableBody tr');
  mark('cockpit');
  await sleep(1500);
  await shot('cockpit');
  await page.selectOption('#ckTableBody .ck-estado-select', 'oficializada');
  await sleep(1200);
  await page.selectOption('#ckTableBody .ck-estado-select', 'canal');
  await sleep(900);
  const canal = page.locator('#ckTableBody .ck-canal-select').first();
  if (await canal.count()) { await canal.selectOption('verde'); await sleep(1200); }
  mark('cockpit_done');
  await shot('cockpit_done');

  // 9. Ficha del cliente: historial, CSV, plantilla Excel y catálogo
  await page.click('[data-action="go-clientes"]');
  await page.waitForSelector('.cx-card');
  mark('clientes');
  await sleep(1300);
  await shot('clientes');
  await page.locator('.cx-card', { hasText: 'Importadora del Sur' }).first().click();
  await page.waitForSelector('#cxKebabBtn');
  await page.waitForSelector('.cx-ops-item');
  mark('cliente');
  await sleep(1600);
  await shot('cliente');
  await page.click('#cxKebabBtn');
  await page.waitForSelector('#cxKebabMenu.is-open');
  mark('cliente_menu');
  await sleep(1500);
  await shot('cliente_menu');
  const descarga = page.waitForEvent('download');
  await page.click('#cxKebabMenu [data-kaction="csv"]');
  const archivoCsv = await descarga;
  console.log('descarga', archivoCsv.suggestedFilename());
  await sleep(1200);
  await page.click('#cxTabCatalogo');
  await page.waitForSelector('[data-panel="catalogo"]:not([hidden])');
  mark('cliente_catalogo');
  await sleep(2200);
  await shot('cliente_catalogo');

  // 10. Mi catálogo aprendido: corregir la NCM de un producto y guardar
  await page.click('#goCatalogoBtn');
  await page.waitForSelector('#catalogoDrawer:not([hidden])');
  await page.waitForSelector('.catalogo-vendor-card');
  mark('catalogo');
  await sleep(1300);
  await page.locator('.catalogo-vendor-card').first().click();
  await page.waitForSelector('.catalogo-product-row');
  await sleep(1300);
  await shot('catalogo');
  const ncmInput = page.locator('.catalogo-product-row').nth(2).locator('input[data-field="ncm"]');
  await ncmInput.click();
  await ncmInput.fill('');
  await ncmInput.pressSequentially('84713019', { delay: 60 });
  await sleep(500);
  await page.locator('.catalogo-product-row').nth(2).locator('[data-action="save-product"]').click();
  await sleep(1400);
  mark('catalogo_done');
  await shot('catalogo_done');
  // El ícono de borrar proveedor queda sobre el botón de cerrar: click directo.
  await page.evaluate(() => document.getElementById('catalogoDrawerClose').click());
  await page.waitForSelector('#catalogoDrawer[hidden]', { state: 'attached' });
  await sleep(500);

  // 11. Traer mis clientes desde la planilla que ya usa el estudio
  if (clientesCsv) {
    await page.click('#cxImportBtn');
    await page.waitForSelector('#importClientesModal:not([hidden])');
    mark('import');
    await sleep(1000);
    await page.setInputFiles('#importFileInput', clientesCsv);
    await page.waitForSelector('#importPreviewStep:not([hidden])');
    mark('import_preview');
    await sleep(2000);
    await shot('import_preview');
    await page.click('#importConfirm');
    await page.waitForSelector('#importDoneStep:not([hidden])');
    mark('import_done');
    await sleep(2000);
    await shot('import_done');
  }
  mark('end');

  fs.writeFileSync(path.join(out, 'marks.json'), JSON.stringify(marks, null, 2));
  const videoPath = await page.video().path();
  await ctx.close();
  await browser.close();
  fs.writeFileSync(path.join(out, 'video.txt'), videoPath);
  console.log('video', videoPath);
})().catch(async (e) => { console.error(e); process.exit(1); });
