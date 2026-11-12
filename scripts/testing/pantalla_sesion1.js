// SESION-1 en el navegador local, contra la API de verdad y con datos
// inventados: en el perfil v2, el campo «Contraseña actual» aparece sólo si el
// email cambió (sin distinguir mayúsculas ni espacios). Guardar el nombre con el
// mismo email no la pide; con el email cambiado y sin clave, la pantalla avisa y
// no manda nada; con una clave equivocada el servidor da 400, se ve el error y
// la sesión sigue (un 401 mandaría al login); con la correcta, el email cambia
// y al reabrir el campo vuelve a estar oculto y vacío.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_sesion1.js
// (servidor local con EMAIL_VERIFICATION_REQUIRED=false)
const { chromium } = require('playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const CLAVE = 'Clave-Inventada-123';

(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const page = await (await b.newContext()).newPage();
  const errores = [];
  page.on('pageerror', e => errores.push(String(e)));
  const u = 'ses1_' + Date.now(), mail = u + '@ejemplo.test', otro = 'otro-' + mail;

  let r = await registrarCuenta(page.request, base, { data: { username: u, password: CLAVE, email: mail, name: 'Ses' } });
  r = await page.request.post(base + '/auth/login', { data: { username: u, password: CLAVE } });
  if (!r.ok()) falla('login: ' + r.status() + ' ' + await r.text());

  await page.goto(base + '/dashboard?v=2');
  await page.waitForFunction(() => typeof window.CDI?.openProfileModal === 'function');
  async function abrirPerfil(email) {
    // El cierre esconde el modal un rato después y, ya cargado, el foco salta a «Mi CUIT»:
    // lo que se escriba antes de que pasen las dos cosas se puede perder.
    await page.waitForFunction(() => document.getElementById('profileModal').hidden)
      .catch(() => falla('el perfil no terminó de cerrarse'));
    await page.evaluate(() => CDI.openProfileModal());
    await page.waitForFunction(m => document.getElementById('pfEmail').value === m
      && document.activeElement.id === 'pfCuit', email)
      .catch(() => falla('el perfil no terminó de abrir con el foco en «Mi CUIT»'));
  }
  const campoVisible = () => page.isVisible('#pfEmailPasswordField');
  const put = () => page.waitForResponse(x => x.url().endsWith('/api/user/profile') && x.request().method() === 'PUT');
  let puts = 0;
  page.on('request', q => { if (q.method() === 'PUT' && q.url().endsWith('/api/user/profile')) puts++; });

  await abrirPerfil(mail);
  if (await campoVisible()) falla('el campo de la clave se ve al abrir el perfil');
  await page.fill('#pfEmail', '  ' + mail.toUpperCase() + ' ');
  if (await campoVisible()) falla('el campo de la clave se ve con el mismo email en mayúsculas');

  await page.fill('#pfName', 'Nombre nuevo');
  let resp = put();
  await page.click('#profileSave');
  if ((await resp).status() !== 200) falla('guardar el nombre con el mismo email da ' + (await resp).status());

  await abrirPerfil(mail);
  await page.fill('#pfEmail', otro);
  if (!await campoVisible()) falla('cambiar el email no muestra el campo de la clave');
  const antes = puts;
  await page.click('#profileSave');
  await page.waitForSelector('#pfCuitError', { state: 'visible', timeout: 5000 })
    .catch(() => falla('sin clave no aparece ningún error'));
  const sinClave = await page.textContent('#pfCuitError');
  if (!/contraseña actual/.test(sinClave)) falla('sin clave el error dice: ' + sinClave);
  if (puts !== antes) falla('sin clave la pantalla igual mandó el PUT');

  await page.fill('#pfEmailPassword', 'equivocada-1!');
  resp = put();
  await page.click('#profileSave');
  if ((await resp).status() !== 400) falla('con la clave equivocada el servidor da ' + (await resp).status());
  await page.waitForFunction(() => /incorrecta/.test(document.getElementById('pfCuitError').textContent), null, { timeout: 5000 })
    .catch(() => falla('con la clave equivocada no se ve el error'));
  if (new URL(page.url()).pathname !== '/dashboard') falla('con la clave equivocada la pantalla se fue a ' + page.url());

  await page.fill('#pfEmailPassword', CLAVE);
  resp = put();
  await page.click('#profileSave');
  const ok = await resp;
  if (ok.status() !== 200) falla('con la clave correcta da ' + ok.status());
  if ((await ok.json()).profile.email !== otro) falla('con la clave correcta el email no cambió');

  await abrirPerfil(otro);
  if (await campoVisible()) falla('al reabrir, el campo de la clave sigue visible');
  if (await page.inputValue('#pfEmailPassword') !== '') falla('al reabrir, la clave sigue escrita en el campo');
  if (errores.length) falla('errores de página: ' + errores.join(' | '));

  console.log('OK: el perfil pide la contraseña sólo al cambiar el email y no saca a nadie al login');
  await b.close();
})().catch(e => falla(String(e)));
