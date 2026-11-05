// Con el servidor exigiendo el token CSRF (CSRF_ENFORCE=true, como en producción),
// las escrituras de la landing y de la pantalla vieja llegan con sesión abierta
// y su «Salir» cierra la sesión. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_csrf2.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }

async function escribe(p, ruta, accion, nombre) {
  const resp = p.waitForResponse(r => new URL(r.url()).pathname === ruta && r.request().method() === 'POST', { timeout: 20000 });
  await accion();
  const r = await resp.catch(() => null);
  if (!r) falla(nombre + ' no mandó ' + ruta);
  if (!r.ok()) falla(nombre + ' dio ' + r.status() + ' en ' + ruta + ': ' + await r.text());
}

(async () => {
  const base = process.env.BASE_URL || 'http://127.0.0.1:8877';
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
  const id = Date.now();
  const cuenta = { username: 'csrf2_' + id, password: 'Clave-Inventada-123' };
  const reg = await ctx.request.post(base + '/auth/register', { data: { ...cuenta, email: 'csrf2' + id + '@ejemplo.test' } });
  if (!reg.ok()) falla('no se pudo registrar: ' + reg.status());

  const landing = await ctx.newPage();
  await landing.goto(base + '/');
  await escribe(landing, '/api/ui/event', () => landing.click('#btnHeroCta'), 'la telemetría de la landing');
  await landing.close();

  const p = await ctx.newPage();
  // La v1 manda a la portada si no encuentra el token en localStorage.
  const token = (await reg.json()).access_token;
  if (!token) falla('el registro no devolvió access_token');
  await p.addInitScript(t => localStorage.setItem('access_token', t), token);
  await p.goto(base + '/dashboard?v=1');
  await p.waitForFunction(() => typeof autoBackupLocalStorage === 'function' && typeof logout === 'function');
  await escribe(p, '/api/backup/localStorage', () => p.evaluate(() => autoBackupLocalStorage()), 'la copia de la pantalla vieja');
  // El token no sale de su sitio: un pedido a otro origen va sin él.
  const ajenos = [];
  await p.route('http://otro.ejemplo.test/**', r => { ajenos.push(r.request().headers()); r.fulfill({ status: 200, body: 'ok' }); });
  await p.evaluate(() => fetch('http://otro.ejemplo.test/x', { method: 'POST', body: 'x' }).catch(() => {}));
  if (!ajenos.length) falla('el pedido a otro origen no salió');
  if (ajenos.some(h => JSON.stringify(h).toLowerCase().includes('x-csrf-token'))) falla('el token CSRF salió hacia otro origen');
  await p.unroute('http://otro.ejemplo.test/**');
  // Un pedido mal armado tiene que fallar como en fetch nativo: con la promesa, no antes.
  const rompe = await p.evaluate(() => { try { fetch('http://[', { method: 'POST' }).catch(() => {}); return ''; } catch (e) { return String(e); } });
  if (rompe) falla('con una URL inválida fetch tiró antes de devolver la promesa: ' + rompe);

  await p.evaluate(() => { window.showConfirmation = async () => true; });
  await Promise.all([p.waitForURL(u => u.pathname === '/', { timeout: 20000 }), p.evaluate(() => { logout(); })])
    .catch(() => falla('«Salir» de la pantalla vieja no llevó al inicio'));
  const sesion = await ctx.request.get(base + '/auth/current_user');
  if (sesion.status() !== 401) falla('«Salir» de la pantalla vieja dejó la sesión abierta (' + sesion.status() + ')');

  await b.close();
  console.log('OK: CSRF-2 en el navegador');
})().catch(e => falla(e.stack || e.message));
