// ESTUDIO-1b (D23 b) en el navegador local, contra la API de verdad (sin
// terceros: el TXT se genera en modo fake). Generar con el CUIT del perfil
// también cuenta como «último usado»: en la operación siguiente, sin tocar el
// selector, viene elegido el perfil y no el estudio de antes. Un estudio único
// recién cargado, sin uso del perfil antes, viene elegido.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_estudio1b.js
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const CUIT_PERFIL = '20111111112';
const CUIT_UNO = '30222222229';

(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  const usuario = 'e1b_' + id;
  let r = await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: usuario, password: 'Clave-Inventada-123', email: 'e1b' + id + '@ejemplo.test' } });
  r = await page.request.put(base + '/api/user/profile', { data: { cuit: CUIT_PERFIL } });
  if (!r.ok()) falla('CUIT del perfil: ' + r.status() + ' ' + await r.text());
  r = await page.request.post(base + '/api/estudios', { data: { nombre: 'Estudio Inventado Uno', cuit: CUIT_UNO } });
  if (!r.ok()) falla('alta del estudio: ' + r.status() + ' ' + await r.text());
  const uno = (await r.json()).estudio;

  // Una operación nueva en la misma sesión (como en ESTUDIO-1, paso 6b): se
  // espera a que el selector termine de leer la lista que trae esta operación.
  let numero = 0;
  async function nuevaOperacion() {
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.estudios && CDI.currentUser);
    numero += 1;
    const lista = page.waitForResponse(x => x.url().endsWith('/api/estudios') && x.request().method() === 'GET', { timeout: 10000 })
      .catch(() => falla('la operación ' + numero + ' no pidió la lista de estudios'));
    await page.evaluate(n => {
      CDI.state = CDI.state || {};
      CDI.state.uploadedAt = new Date().toISOString() + '#' + n;
      CDI.state.operacion = { numero_factura: 'INV-2026/05' + n, moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026', sbt_sufijo_valor: 'AA(1)-CA00-' };
      CDI.state.items = [{ pieza: '39219019900Z', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62 }];
      CDI.goTo('validating');
    }, numero);
    await lista;
    await page.evaluate(() => CDI.estudios.listo());
    await page.waitForFunction(() => !document.getElementById('estudioSelect').hidden, null, { timeout: 10000 })
      .catch(() => falla('operación ' + numero + ': el selector no aparece'));
    return page.$eval('#estudioSelect', s => s.value);
  }
  async function generar() {
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
    await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
    const respuesta = page.waitForResponse(x => x.url().endsWith('/generate_maria') && x.request().method() === 'POST', { timeout: 15000 })
      .catch(() => falla('no se pidió el TXT'));
    await page.click('#validatingGenerate');
    const resp = await respuesta;
    const cuerpo = await resp.json();
    if (resp.status() !== 200) falla('el TXT no salió: ' + resp.status() + ' ' + JSON.stringify(cuerpo).slice(0, 400));
    return {
      estudio_id: JSON.parse(resp.request().postData()).estudio_id,
      cddtagr: [...cuerpo.content.matchAll(/^CDDTAGR=([^\r\n]*)/mg)].map(m => m[1]),
    };
  }

  await page.goto(base + '/dashboard');

  // 1. Un estudio único recién cargado, sin uso del perfil antes: viene elegido.
  let elegido = await nuevaOperacion();
  if (elegido !== uno.id) falla('el estudio único sin uso del perfil no viene elegido: ' + JSON.stringify(elegido));
  let txt = await generar();
  if (txt.estudio_id !== uno.id || JSON.stringify(txt.cddtagr) !== JSON.stringify([CUIT_UNO])) falla('con el estudio: ' + JSON.stringify(txt));
  console.log('OK el estudio único sin uso del perfil viene elegido y su CUIT va al CDDTAGR');

  // 2. En la operación siguiente la persona elige a mano el CUIT del perfil.
  elegido = await nuevaOperacion();
  if (elegido !== uno.id) falla('después de usar el estudio, viene elegido: ' + JSON.stringify(elegido));
  await page.selectOption('#estudioSelect', '');
  txt = await generar();
  if (txt.estudio_id !== '' || JSON.stringify(txt.cddtagr) !== JSON.stringify([CUIT_PERFIL])) falla('con el perfil elegido a mano: ' + JSON.stringify(txt));
  console.log('OK elegido a mano, el TXT sale con el CUIT del perfil');

  // 3. La operación siguiente, sin tocar el selector: viene el perfil.
  elegido = await nuevaOperacion();
  if (elegido !== '') falla('después de generar con el perfil, en la operación siguiente viene elegido ' + JSON.stringify(elegido) + ' y no el perfil');
  txt = await generar();
  if (txt.estudio_id !== '' || JSON.stringify(txt.cddtagr) !== JSON.stringify([CUIT_PERFIL])) falla('sin tocar el selector: ' + JSON.stringify(txt));
  console.log('OK sin tocar el selector, la operación siguiente viene con el perfil y el TXT sale con su CUIT');

  // 4. También al volver a entrar (otra carga de la página).
  await page.reload();
  elegido = await nuevaOperacion();
  if (elegido !== '') falla('al volver a entrar viene elegido ' + JSON.stringify(elegido) + ' y no el perfil');
  console.log('OK al volver a entrar sigue el perfil');

  await b.close();
  console.log('PANTALLA ESTUDIO-1b OK');
})().catch(e => falla(e && e.stack || e));
