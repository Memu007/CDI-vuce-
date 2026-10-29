'use strict';
// Graba el recorrido real de CDI (Excel → revisión → NCM → validación → MARIA.TXT)
// con Playwright: video 1440x900, capturas 2x y marcas de tiempo por paso.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.BASE_URL;
const fixture = process.env.FIXTURE;
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

  // 4. Revisión: incoterm y fecha tipeados a mano
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
  mark('end');

  fs.writeFileSync(path.join(out, 'marks.json'), JSON.stringify(marks, null, 2));
  const videoPath = await page.video().path();
  await ctx.close();
  await browser.close();
  fs.writeFileSync(path.join(out, 'video.txt'), videoPath);
  console.log('video', videoPath);
})().catch(async (e) => { console.error(e); process.exit(1); });
