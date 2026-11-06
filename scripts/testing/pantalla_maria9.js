// MARIA-9 en el navegador local, contra el servidor local (sin terceros).
// Cada error de sufijo de valor sale donde se corrige: el de la operación
// bajo su campo, en la validación; el de un sub-ítem bajo ese sub-ítem, en
// el paso de NCM. Primero con el error real del servidor, después forzado
// con page.route (otro texto, otro ítem). El del renglón no tiene campo en
// la pantalla: sale en el error de la generación, entero.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria9.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const OP = { numero_factura: 'INV-2026/0457', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671',
             fecha_emision: '10/10/2026' };
const LONA = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };
const conSubitems = (...sufijos) => ({ ...LONA, subitems: sufijos.map(s => ({ cantidad: 375, valor_unitario: 1.85, sufijo: s })) });

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'm9_' + id, password: 'Clave-Inventada-123', email: 'm9' + id + '@ejemplo.test' } });

  const campoGeneral = page.locator('#sbtFieldError');
  const errorGeneracion = page.locator('#readyErrorText');
  const bajoElSubitem = (i, k) => page.locator('[data-sub-error="' + i + '"][data-sub-idx="' + k + '"]');

  // Carga la operación, pide el TXT desde la validación y devuelve la respuesta.
  async function generar(items, general) {
    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && CDI.ncmBatch);
    await page.evaluate(([op, items]) => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = op;
      CDI.state.items = items;
      CDI.goTo('validating');
    }, [OP, items]);
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
    await page.fill('#sbtSufijoValor', general);
    const resp = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
    await page.click('#validatingGenerate');
    const r = await resp.catch(() => falla('no se pidió el TXT'));
    if (r.status() !== 400) falla('se esperaba un 400 y vino ' + r.status() + ': ' + (await r.text()).slice(0, 300));
    return JSON.parse(await r.text()).detail;
  }

  async function bajoElCampoGeneral(detail, que) {
    await campoGeneral.waitFor({ state: 'visible', timeout: 5000 })
      .catch(async () => falla(que + ': no sale bajo el campo del sufijo de la operación' +
        (await errorGeneracion.isVisible() ? ' (sale como error de la generación: «' + await errorGeneracion.innerText() + '»)' : '')));
    if (await campoGeneral.innerText() !== detail) falla(que + ': bajo el campo dice otra cosa: ' + await campoGeneral.innerText());
    if (await errorGeneracion.isVisible()) falla(que + ': también sale como error de la generación');
  }

  async function bajoDelSubitem(i, k, detail, que) {
    const lugar = bajoElSubitem(i, k);
    await lugar.waitFor({ state: 'visible', timeout: 5000 })
      .catch(async () => falla(que + ': no sale bajo el sub-ítem ' + (k + 1) + ' del ítem ' + (i + 1) +
        (await errorGeneracion.isVisible() ? ' (sale como error de la generación: «' + await errorGeneracion.innerText() + '»)' : '')));
    if (await lugar.innerText() !== detail) falla(que + ': bajo el sub-ítem dice otra cosa: ' + await lugar.innerText());
    if (await campoGeneral.isVisible()) falla(que + ': también sale bajo el campo del sufijo de la operación');
  }

  // 1. El de la operación, real: un ítem entero lo toma y es texto libre.
  let detail = await generar([{ ...LONA }], 'ROJO');
  if (!detail.startsWith('Sufijo de valor de la operación: «ROJO» no se puede separar')) falla('el servidor dice otra cosa: ' + detail);
  await bajoElCampoGeneral(detail, 'el de la operación');
  console.log('OK «' + detail.slice(0, 60) + '…» sale bajo el campo del sufijo de la operación');

  // 2. El de un sub-ítem, real: el segundo no se puede separar.
  detail = await generar([conSubitems('AA(A)-', 'AA(B')], 'ROJO');
  if (!detail.startsWith('Sufijo de valor del ítem 1, sub-ítem 2: «AA(B» no se puede separar')) falla('el servidor dice otra cosa: ' + detail);
  await bajoDelSubitem(0, 1, detail, 'el del sub-ítem');
  console.log('OK «' + detail.slice(0, 60) + '…» sale bajo el sub-ítem 2');

  // 3. Forzados: el otro texto del de la operación (el largo) y un sub-ítem
  // de otro ítem, para que no se dependa del primero.
  let forzado = null;
  await page.route('**/generate_maria', r => r.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ detail: forzado }) }));
  const dos = [conSubitems('AA(A)-', 'AA(B)-'), { ...conSubitems('AA(C)-', 'AA(D)-'), descripcion: 'Lona de PVC negra' }];

  forzado = 'Sufijo de valor de la operación: separado con guiones queda de 121 caracteres y no puede superar los 120.';
  await bajoElCampoGeneral(await generar(dos, 'AA(X)-'), 'el largo de la operación');
  console.log('OK el error del largo de la operación sale bajo su campo');

  forzado = 'Sufijo de valor del ítem 2, sub-ítem 1: «AA(C» no se puede separar en códigos (forzado).';
  await bajoDelSubitem(1, 0, await generar(dos, ''), 'el del ítem 2');
  if (await bajoElSubitem(0, 0).count() || await bajoElSubitem(0, 1).count()) falla('el error del ítem 2 sale también en el ítem 1');
  console.log('OK el error del sub-ítem 1 del ítem 2 sale bajo ese sub-ítem y no en el ítem 1');

  // 4. Un sub-ítem que no existe en la pantalla no se pierde: sale entero.
  forzado = 'Sufijo de valor del ítem 2, sub-ítem 9: «AA(C» no se puede separar en códigos (forzado).';
  await generar(dos, '');
  await errorGeneracion.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla('el error de un sub-ítem que no existe se pierde'));
  if (await errorGeneracion.innerText() !== forzado) falla('el error de un sub-ítem que no existe dice otra cosa: ' + await errorGeneracion.innerText());
  console.log('OK el de un sub-ítem que no está en la pantalla sale entero como error de la generación');

  // 5. El del renglón: la pantalla no carga sufijos por renglón, así que no
  // hay campo; sale entero como error de la generación.
  forzado = 'Sufijo de valor del renglón 3: «AA(B» no se puede separar en códigos (forzado).';
  await generar(dos, '');
  await errorGeneracion.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla('el error del renglón se pierde'));
  if (await errorGeneracion.innerText() !== forzado) falla('el error del renglón dice otra cosa: ' + await errorGeneracion.innerText());
  if (await campoGeneral.isVisible()) falla('el error del renglón sale bajo el campo del sufijo de la operación');
  console.log('OK el del renglón sale entero como error de la generación');

  await b.close();
  console.log('PANTALLA MARIA-9 OK');
})().catch(e => falla(e && e.stack || e));
