// Con el servidor exigiendo el token CSRF (CSRF_ENFORCE=true, como en producción),
// las escrituras de la landing y de la pantalla (v2) llegan con sesión abierta y
// su «Salir» cierra la sesión; csrf.js, que carga la landing, no manda el token a
// otro origen ni tira antes de devolver la promesa. Hasta el 2026-11-05 la parte
// de la pantalla se medía en la v1, que se retiró. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_csrf2.js
const { chromium } = require('playwright');
const registrarCuenta = require('./_registrar');
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
  await registrarCuenta(ctx.request, base, { data: { ...cuenta, email: 'csrf2' + id + '@ejemplo.test' } });

  const landing = await ctx.newPage();
  // La CSP corta en el navegador los pedidos a otro origen: se mira lo que csrf.js le pasa a fetch nativo.
  await landing.addInitScript(() => {
    const nativo = window.fetch;
    window.__pedidos = [];
    window.fetch = function (input, init) {
      window.__pedidos.push({ url: String(input), headers: [...new Headers((init || {}).headers).keys()] });
      return nativo.apply(this, arguments);
    };
  });
  await landing.goto(base + '/');
  await escribe(landing, '/api/ui/event', () => landing.click('#btnHeroCta'), 'la telemetría de la landing');
  // El token no sale de su sitio: un pedido a otro origen va sin él.
  const ajenos = await landing.evaluate(async () => {
    await fetch('http://otro.ejemplo.test/x', { method: 'POST', body: 'x' }).catch(() => {});
    return window.__pedidos.filter(q => q.url.startsWith('http://otro.ejemplo.test/'));
  });
  if (!ajenos.length) falla('csrf.js no le pasó a fetch el pedido a otro origen');
  if (ajenos.some(q => q.headers.includes('x-csrf-token'))) falla('el token CSRF salió hacia otro origen');
  // Un pedido mal armado tiene que fallar como en fetch nativo: con la promesa, no antes.
  const rompe = await landing.evaluate(() => { try { fetch('http://[', { method: 'POST' }).catch(() => {}); return ''; } catch (e) { return String(e); } });
  if (rompe) falla('con una URL inválida fetch tiró antes de devolver la promesa: ' + rompe);
  await landing.close();

  // La pantalla: una escritura con la sesión abierta llega, y «Salir» cierra la sesión.
  const p = await ctx.newPage();
  await p.goto(base + '/dashboard');
  await p.waitForFunction(() => window.CDI && CDI.api && CDI.currentUser);
  await escribe(p, '/api/clientes',
    () => p.evaluate(() => CDI.api('/api/clientes', { method: 'POST', body: JSON.stringify({ nombre: 'Cliente CSRF-2', cuit: '30999999995' }) }).catch(() => {})),
    'la escritura de la pantalla');
  await Promise.all([p.waitForURL(u => u.pathname === '/', { timeout: 20000 }), p.click('#logoutBtn')])
    .catch(() => falla('«Salir» de la pantalla no llevó al inicio'));
  const sesion = await ctx.request.get(base + '/auth/current_user');
  if (sesion.status() !== 401) falla('«Salir» de la pantalla dejó la sesión abierta (' + sesion.status() + ')');

  await b.close();
  console.log('OK: CSRF-2 en el navegador');
})().catch(e => falla(e.stack || e.message));
