// «Mi perfil» no guarda un CUIT con el verificador equivocado: el error queda a la vista junto al campo
// y la ventana sigue abierta. Uno malo que ya estaba guardado (se siembra directo en la base local del
// servidor, CDI_DB) se muestra, y al guardar se pide corregirlo sin tocar lo guardado.
// Navegador local, servidor local. Datos inventados. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> CDI_DB=<base sqlite del servidor> node scripts/testing/pantalla_cuit_perfil1.js
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8822';
const baseLocal = process.env.CDI_DB || falla('falta CDI_DB: la base sqlite local del servidor, para sembrar un CUIT guardado');
const MALO = '20-99999999-8', BUENO = '20-11111111-2';
const sinGuiones = c => c.replace(/-/g, '');

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext()).newPage();
  const usuario = 'cp1_' + Date.now();
  await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() },
    data: { username: usuario, password: 'Clave-Inventada-123', email: usuario + '@ejemplo.test', name: 'Nombre Inventado' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.openProfileModal && CDI.currentUser);

  const guardado = async () => (await (await page.request.get(base + '/api/user/profile')).json()).profile;
  const abrir = async () => {
    await page.evaluate(() => CDI.openProfileModal());
    await page.waitForSelector('#profileModal.is-open');
  };
  // Escribe el perfil, toca Guardar y devuelve cómo terminó: «guardado» o el error que quedó a la vista.
  const guardar = async (cuit, nombre) => {
    await page.fill('#pfCuit', cuit);
    if (nombre) await page.fill('#pfName', nombre);
    await page.click('#profileSave');
    return (await page.waitForFunction(() => {
      const error = document.getElementById('pfCuitError');
      if (!error.hidden && error.textContent) return 'error: ' + error.textContent;
      return document.getElementById('profileModal').classList.contains('is-open') ? false : 'guardado';
    }, null, { timeout: 15000 })).jsonValue();
  };
  const pideCorregir = (fin, cuando) => {
    if (!/^error: .*CUIT.*verificador/.test(fin)) falla(cuando + ' terminó en «' + fin + '» y no en el error del CUIT');
    console.log('OK ' + cuando + ': ' + fin);
  };

  await abrir();
  let fin = await guardar(MALO);
  let p = await guardado();
  if (p.cuit) falla('«Mi perfil» guardó ' + MALO + ', que tiene el verificador equivocado: el perfil quedó con «' + p.cuit + '» (' + fin + ')');
  pideCorregir(fin, 'con ' + MALO + ' escrito');
  if (!await page.$eval('#pfCuit', el => el.classList.contains('is-error'))) falla('el campo del CUIT no queda marcado');

  fin = await guardar(BUENO);
  p = await guardado();
  if (fin !== 'guardado' || p.cuit !== sinGuiones(BUENO)) falla('con ' + BUENO + ' terminó en «' + fin + '» y el perfil quedó con «' + p.cuit + '»');
  console.log('OK ' + BUENO + ' se guarda como ' + p.cuit);

  execFileSync('python3', ['-c',
    'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute("UPDATE users SET cuit=? WHERE username=?", (sys.argv[3], sys.argv[2])).rowcount; c.commit(); sys.exit(0 if n == 1 else 1)',
    baseLocal, usuario, sinGuiones(MALO)]);
  await abrir();
  const visto = await page.inputValue('#pfCuit');
  if (visto !== MALO) falla('con ' + MALO + ' ya guardado, el campo muestra «' + visto + '»');
  fin = await guardar(visto, 'Otro Nombre');
  p = await guardado();
  if (p.cuit !== sinGuiones(MALO) || p.name !== 'Nombre Inventado') falla('con el CUIT malo ya guardado, el perfil quedó con «' + p.cuit + '» y «' + p.name + '» (' + fin + ')');
  pideCorregir(fin, 'con ' + MALO + ' ya guardado, al cambiar el nombre');

  fin = await guardar(BUENO);
  p = await guardado();
  if (fin !== 'guardado' || p.cuit !== sinGuiones(BUENO) || p.name !== 'Otro Nombre') falla('al corregirlo terminó en «' + fin + '» y el perfil quedó con «' + p.cuit + '» y «' + p.name + '»');
  console.log('OK corregido, se guarda con el nombre nuevo');
  await b.close();
  console.log('PANTALLA CUIT-PERFIL-1 OK');
})().catch(e => falla(e && e.stack || e));
