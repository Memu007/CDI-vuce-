// CSRF-1: con el servidor exigiendo el token CSRF (CSRF_ENFORCE=true, como en
// producción), la telemetría que manda la página v2 llega y el botón «Salir»
// cierra la sesión, o avisa si el servidor no lo acepta o el pedido no sale. Lo que se rechaza sin token lo cubre tests/test_csrf.py.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_csrf1.js
const { chromium } = require('playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }

(async () => {
  const base = process.env.BASE_URL || 'http://127.0.0.1:8876';
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
  const id = Date.now();
  const cuenta = { username: 'csrf1_' + id, password: 'Clave-Inventada-123' };
  await registrarCuenta(ctx.request, base, { data: { ...cuenta, email: 'csrf1' + id + '@ejemplo.test' } });

  // Sin el header CSRF el servidor rechaza el cierre: «Salir» tiene que decirlo y no llevar al inicio.
  const p0 = await ctx.newPage();
  await p0.route('**/auth/logout', r => {
    const headers = { ...r.request().headers() };
    delete headers['x-csrf-token'];
    r.continue({ headers });
  });
  await p0.goto(base + '/dashboard');
  await p0.waitForFunction(() => window.CDI && CDI.currentUser);
  await p0.click('#logoutBtn');
  await p0.waitForFunction(() => /No se pudo cerrar la sesión/.test(document.querySelector('#toastHost .toast-title')?.textContent),
    null, { timeout: 20000 }).catch(() => falla('«Salir» rechazado no avisó y la página fue a ' + new URL(p0.url()).pathname));
  await p0.close();

  const p = await ctx.newPage();
  const telemetria = p.waitForResponse(r => new URL(r.url()).pathname === '/api/session/state', { timeout: 20000 });
  await p.goto(base + '/dashboard');
  const r = await telemetria.catch(() => null);
  if (!r) falla('la página no mandó telemetría');
  if (!r.ok()) falla('la telemetría de la página dio ' + r.status());

  await p.waitForFunction(() => window.CDI && CDI.currentUser);
  // Con el pedido cortado, «Salir» tampoco puede llevar al inicio con la sesión abierta.
  await p.route('**/auth/logout', r => r.abort());
  await p.click('#logoutBtn');
  await p.waitForFunction(() => /No se pudo cerrar la sesión/.test(document.querySelector('#toastHost .toast-title')?.textContent),
    null, { timeout: 20000 }).catch(() => falla('«Salir» sin red no avisó y la página fue a ' + new URL(p.url()).pathname));
  await p.unroute('**/auth/logout');
  await Promise.all([p.waitForURL(u => u.pathname === '/', { timeout: 20000 }), p.click('#logoutBtn')])
    .catch(() => falla('«Salir» no llevó al inicio'));
  const sesion = await ctx.request.get(base + '/auth/current_user');
  if (sesion.status() !== 401) falla('«Salir» llevó al inicio con la sesión abierta (' + sesion.status() + ')');

  await b.close();
  console.log('OK: CSRF-1 en el navegador');
})().catch(e => falla(e.stack || e.message));
