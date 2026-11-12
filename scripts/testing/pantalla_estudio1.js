// ESTUDIO-1 en el navegador local, contra la API de verdad (sin terceros: el
// TXT se genera en modo fake). Los estudios se cargan en «Mi perfil», «Mis
// estudios»; en la operación se elige uno y su CUIT va al CDDTAGR. Sin
// estudios se usa el CUIT del perfil; se preselecciona el último usado o el
// único; el nombre se muestra como texto, nunca como HTML.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_estudio1.js [captura-telefono.png]
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const CUIT_PERFIL = '20111111112';
const CUIT_UNO = '30222222229';
const CUIT_DOS = '27333333339';
const NOMBRE_HTML = '<img src=x onerror="window.__xss=1">Estudio Inventado Uno';

(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  const usuario = 'e1_' + id;
  let r = await page.request.post(base + '/auth/register', { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: usuario, password: 'Clave-Inventada-123', email: 'e1' + id + '@ejemplo.test' } });
  if (!r.ok()) falla('registro: ' + r.status() + ' ' + await r.text());
  r = await page.request.put(base + '/api/user/profile', { data: { cuit: CUIT_PERFIL } });
  if (!r.ok()) falla('CUIT del perfil: ' + r.status() + ' ' + await r.text());

  async function aValidar() {
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.estudios && CDI.currentUser);
    await page.evaluate(() => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = { numero_factura: 'INV-2026/0457', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026', sbt_sufijo_valor: 'AA(1)-CA00-' };
      CDI.state.items = [{ pieza: '39219019900Z', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62 }];
      CDI.goTo('validating');
    });
  }
  async function hint() { return (await page.textContent('#estudioHint')).trim(); }
  // El perfil pone el foco en «Mi CUIT» después de cargar: si cae durante un fill,
  // el texto va ahí. Se escribe recién cuando ya cayó.
  async function abrirMisEstudios(p = page) {
    await p.evaluate(() => CDI.openProfileModal());
    await p.waitForFunction(() => document.activeElement && document.activeElement.id === 'pfCuit', null, { timeout: 10000 })
      .catch(() => falla('el perfil no puso el foco en «Mi CUIT»'));
    await p.waitForSelector('#pfEstudiosBlock', { state: 'visible' });
    if (!await p.$eval('#pfEstudiosBlock', d => d.open)) await p.click('#pfEstudiosBlock summary');
  }
  async function filas() {
    return page.$$eval('#pfEstudiosList > div > span', s => s.map(x => x.textContent));
  }
  async function cerrarPerfil() {
    await page.evaluate(() => CDI.closeProfileModal());
    await page.waitForSelector('#pfEstudiosBlock', { state: 'hidden' });
  }

  // 1. Sin estudios: no hay selector y se dice que va el CUIT del perfil.
  await page.goto(base + '/dashboard');
  await aValidar();
  await page.waitForFunction(() => document.getElementById('estudioHint').textContent.trim() !== '', null, { timeout: 10000 })
    .catch(() => falla('sin estudios, el hint no aparece'));
  if (!await page.$eval('#estudioSelect', s => s.hidden)) falla('sin estudios, el selector se ve');
  if (!(await hint()).includes('Se usa el CUIT de tu perfil')) falla('hint sin estudios: ' + await hint());
  console.log('OK sin estudios no hay selector: se usa el CUIT del perfil y se dice dónde cargarlos');

  // 2. «Mis estudios»: un CUIT que no sirve no se guarda y el error se ve.
  await abrirMisEstudios();
  await page.waitForFunction(() => document.getElementById('pfEstudiosList').textContent.includes('Todavía no cargaste'), null, { timeout: 10000 })
    .catch(() => falla('la lista vacía no lo dice'));
  await page.fill('#pfEstudioNombre', 'Estudio Inventado');
  await page.fill('#pfEstudioCuit', '30-2222');
  await page.click('#pfEstudioAlta');
  await page.waitForSelector('#pfEstudiosError:not([hidden])', { timeout: 10000 }).catch(() => falla('el CUIT corto no muestra error'));
  const err = await page.textContent('#pfEstudiosError');
  if (!err.includes('11 dígitos')) falla('error del CUIT corto: ' + err);
  if ((await filas()).length) falla('el CUIT corto se guardó');
  console.log('OK un CUIT corto no se guarda: «' + err + '»');

  // 3. Dos estudios; el nombre con HTML se muestra como texto.
  await page.fill('#pfEstudioNombre', NOMBRE_HTML);
  await page.fill('#pfEstudioCuit', '30-22222222-9');
  await page.click('#pfEstudioAlta');
  await page.waitForFunction(() => document.querySelectorAll('#pfEstudiosList > div').length === 1, null, { timeout: 10000 })
    .catch(() => falla('el primer estudio no aparece en la lista'));
  if (!await page.$eval('#pfEstudiosError', e => e.hidden)) falla('queda el error viejo después del alta');
  await page.fill('#pfEstudioNombre', 'Estudio Inventado Dos');
  await page.fill('#pfEstudioCuit', CUIT_DOS);
  await page.press('#pfEstudioCuit', 'Enter');
  await page.waitForFunction(() => document.querySelectorAll('#pfEstudiosList > div').length === 2, null, { timeout: 10000 })
    .catch(() => falla('el segundo estudio (con Enter) no aparece en la lista'));
  const lista = await filas();
  if (await page.$('#pfEstudiosList img') || await page.evaluate(() => window.__xss)) falla('el nombre del estudio se interpretó como HTML');
  if (!lista.includes(NOMBRE_HTML + ' · 30-22222222-9')) falla('lista: ' + JSON.stringify(lista));
  console.log('OK dos estudios en la lista, con el CUIT con guiones y el nombre como texto');
  await cerrarPerfil();

  // 4. En la operación: el CUIT del perfil primero y nada elegido (dos, ninguno usado).
  const { estudios } = await (await page.request.get(base + '/api/estudios')).json();
  const uno = estudios.find(e => e.cuit === CUIT_UNO), dos = estudios.find(e => e.cuit === CUIT_DOS);
  await page.waitForFunction(() => !document.getElementById('estudioSelect').hidden, null, { timeout: 10000 })
    .catch(() => falla('con estudios, el selector no aparece'));
  const opciones = await page.$$eval('#estudioSelect option', os => os.map(o => [o.value, o.textContent]));
  const esperadas = [['', 'CUIT de mi perfil (20-11111111-2)'], [uno.id, NOMBRE_HTML + ' — 30-22222222-9'], [dos.id, 'Estudio Inventado Dos — 27-33333333-9']];
  if (JSON.stringify(opciones) !== JSON.stringify(esperadas)) falla('opciones: ' + JSON.stringify(opciones));
  if (await page.$eval('#estudioSelect', s => s.value) !== '') falla('con dos sin usar, ya viene uno elegido');
  console.log('OK el selector ofrece el perfil y los dos estudios, sin elegir por la persona');

  // 5. Se elige uno y se genera de verdad: su CUIT va al CDDTAGR.
  await page.selectOption('#estudioSelect', dos.id);
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });
  // La página entera ya se pasaba de 390 px antes de ESTUDIO-1 (barra de
  // arriba, pasos y tabla): se mide la tarjeta del estudio.
  const anchoPagina = await page.evaluate(() => document.documentElement.scrollWidth);
  const bordes = await page.$$eval('#estudioWrap, #estudioSelect, #estudioHint', els => els.map(e => Math.round(e.getBoundingClientRect().right)));
  console.log('ancho de la página a 390 px: ' + anchoPagina + '; borde derecho de la tarjeta, el selector y el hint: ' + bordes.join(', '));
  if (Math.max(...bordes) > 390) falla('la tarjeta del estudio se sale del teléfono: ' + bordes.join(', '));
  await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
    .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
  const respuesta = page.waitForResponse(x => x.url().endsWith('/generate_maria') && x.request().method() === 'POST', { timeout: 15000 })
    .catch(() => falla('no se pidió el TXT'));
  await page.click('#validatingGenerate');
  const resp = await respuesta;
  const pedido = JSON.parse(resp.request().postData());
  if (pedido.estudio_id !== dos.id) falla('estudio_id del pedido: ' + pedido.estudio_id);
  const cuerpo = await resp.json();
  if (resp.status() !== 200) falla('el TXT no salió: ' + resp.status() + ' ' + JSON.stringify(cuerpo).slice(0, 400));
  const cddtagr = [...cuerpo.content.matchAll(/^CDDTAGR=([^\r\n]*)/mg)].map(m => m[1]);
  if (JSON.stringify(cddtagr) !== JSON.stringify([CUIT_DOS])) falla('CDDTAGR: ' + JSON.stringify(cddtagr));
  console.log('OK el pedido lleva el estudio elegido y el TXT sale con su CUIT en el CDDTAGR');

  // 6. Al volver, viene elegido el último usado.
  await page.reload();
  await aValidar();
  await page.waitForFunction(() => !document.getElementById('estudioSelect').hidden, null, { timeout: 10000 })
    .catch(() => falla('después de recargar, el selector no aparece'));
  const preseleccionado = await page.$eval('#estudioSelect', s => s.value);
  if (preseleccionado !== dos.id) falla('después de usarlo, viene elegido: ' + JSON.stringify(preseleccionado));
  console.log('OK al volver viene elegido el último estudio usado');

  // 6b. Lo que la persona eligió en una operación no pasa a la siguiente.
  await page.selectOption('#estudioSelect', uno.id);
  await page.evaluate(() => { CDI.state.uploadedAt = new Date().toISOString(); CDI.goTo('validating'); });
  await page.waitForFunction(id => document.getElementById('estudioSelect').value === id, dos.id, { timeout: 10000 })
    .catch(async () => falla('en la operación siguiente queda lo elegido en la anterior: ' + JSON.stringify(await page.$eval('#estudioSelect', s => s.value))));
  console.log('OK en la operación siguiente vuelve la preselección, no lo elegido en la anterior');

  // 7. La persona lo elige y después lo borra: el que queda es el único y
  // viene elegido (lo elegido que se borró no queda pegado).
  await page.selectOption('#estudioSelect', uno.id);
  await page.selectOption('#estudioSelect', dos.id);
  await abrirMisEstudios();
  await page.waitForFunction(() => document.querySelectorAll('#pfEstudiosList > div').length === 2, null, { timeout: 10000 });
  await page.locator('#pfEstudiosList > div', { hasText: 'Estudio Inventado Dos' }).locator('button').click();
  await page.waitForSelector('#cdiConfirmAccept', { state: 'visible', timeout: 10000 }).catch(() => falla('borrar no pide confirmación'));
  await page.click('#cdiConfirmAccept');
  await page.waitForFunction(() => document.querySelectorAll('#pfEstudiosList > div').length === 1, null, { timeout: 10000 })
    .catch(() => falla('el estudio borrado sigue en la lista'));
  if ((await filas())[0] !== NOMBRE_HTML + ' · 30-22222222-9') falla('quedó otro: ' + JSON.stringify(await filas()));
  await cerrarPerfil();
  await page.waitForFunction(id => document.getElementById('estudioSelect').value === id, uno.id, { timeout: 10000 })
    .catch(async () => falla('después de borrar, viene elegido: ' + JSON.stringify(await page.$eval('#estudioSelect', s => s.value))));
  const quedan = await page.$$eval('#estudioSelect option', os => os.map(o => o.value));
  if (JSON.stringify(quedan) !== JSON.stringify(['', uno.id])) falla('opciones después de borrar: ' + JSON.stringify(quedan));
  console.log('OK borrar pide confirmación; el que queda es el único y viene elegido');

  // 8. Generar antes de que lleguen los estudios: se espera la lista y va el
  // preseleccionado, no el CUIT del perfil. La lista se retiene hasta el clic.
  await page.reload();
  const retenidas = [];
  await page.route('**/api/estudios', route => { retenidas.push(route); });
  await aValidar();
  await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
    .catch(() => falla('con la lista retenida, no deja generar'));
  if (!retenidas.length) falla('la lista de estudios no se pidió');
  if (!await page.$eval('#estudioSelect', s => s.hidden)) falla('el selector ya se ve con la lista retenida');
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
  const respuesta2 = page.waitForResponse(x => x.url().endsWith('/generate_maria') && x.request().method() === 'POST', { timeout: 15000 })
    .catch(() => falla('no se pidió el TXT con la lista retenida'));
  await page.click('#validatingGenerate');
  for (const r of retenidas) await r.continue();
  await page.unroute('**/api/estudios');
  const pedido2 = JSON.parse((await respuesta2).request().postData());
  if (pedido2.estudio_id !== uno.id) falla('generar antes de la lista manda estudio_id ' + JSON.stringify(pedido2.estudio_id));
  console.log('OK generar antes de que llegue la lista espera y manda el preseleccionado');

  // 9. Sin CUIT en el perfil: si la lista no se lee, el hint no promete el
  // perfil; al cargar el estudio, los avisos dejan de pedir el CDDTAGR.
  const ctx2 = await b.newContext({ viewport: { width: 390, height: 844 } });
  const p2 = await ctx2.newPage();
  const usuario2 = 'e1b_' + id;
  r = await p2.request.post(base + '/auth/register', { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: usuario2, password: 'Clave-Inventada-123', email: 'e1b' + id + '@ejemplo.test' } });
  if (!r.ok()) falla('registro sin perfil: ' + r.status());
  await p2.route('**/api/estudios', route => route.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"x"}' }));
  await p2.goto(base + '/dashboard');
  await p2.waitForFunction(() => window.CDI && CDI.goTo && CDI.estudios && CDI.currentUser);
  await p2.evaluate(() => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = { numero_factura: 'INV-2026/0458', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026', sbt_sufijo_valor: 'AA(1)-CA00-' };
    CDI.state.items = [{ pieza: '39219019900Z', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62 }];
    CDI.goTo('validating');
  });
  await p2.waitForFunction(() => document.getElementById('estudioHint').textContent.includes('No se pudieron leer'), null, { timeout: 10000 })
    .catch(() => falla('la lista que falla no lo dice'));
  const hint2 = (await p2.textContent('#estudioHint')).trim();
  if (hint2.includes('se usa el CUIT de tu perfil') || !hint2.includes('tu perfil no tiene CUIT')) falla('hint sin perfil y sin lista: ' + hint2);
  console.log('OK sin perfil y sin lista, el hint dice que no se genera: «' + hint2 + '»');
  await p2.unroute('**/api/estudios');
  const avisos2 = () => p2.$eval('#validatingAvisosList', l => l.textContent);
  await p2.waitForFunction(() => document.getElementById('validatingAvisosList').textContent.includes('CDDTAGR'), null, { timeout: 10000 })
    .catch(async () => falla('sin estudio ni perfil, los avisos no piden el CDDTAGR: ' + await avisos2()));
  await abrirMisEstudios(p2);
  await p2.fill('#pfEstudioNombre', 'Estudio Inventado Tres');
  await p2.fill('#pfEstudioCuit', CUIT_UNO);
  await p2.click('#pfEstudioAlta');
  await p2.waitForFunction(() => document.querySelectorAll('#pfEstudiosList > div').length === 1, null, { timeout: 10000 })
    .catch(() => falla('sin perfil, el estudio no aparece en la lista'));
  await p2.evaluate(() => CDI.closeProfileModal());
  await p2.waitForFunction(() => !document.getElementById('validatingAvisosList').textContent.includes('CDDTAGR'), null, { timeout: 10000 })
    .catch(async () => falla('después del alta, los avisos siguen pidiendo el CDDTAGR: ' + await avisos2()));
  console.log('OK al cargar el estudio, los avisos dejan de pedir el CDDTAGR');

  await b.close();
  console.log('PANTALLA ESTUDIO-1 OK');
})().catch(e => falla(e && e.stack || e));
