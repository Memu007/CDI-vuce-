// CSRF-1: con el servidor exigiendo el token CSRF (CSRF_ENFORCE=true, como en
// producción), la telemetría que manda la página v2 llega y el botón «Salir»
// cierra la sesión. Lo que se rechaza sin token lo cubre tests/test_csrf.py.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_csrf1.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }

(async () => {
  const base = process.env.BASE_URL || 'http://127.0.0.1:8876';
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
  const id = Date.now();
  const reg = await ctx.request.post(base + '/auth/register',
    { data: { username: 'csrf1_' + id, password: 'Clave-Inventada-123', email: 'csrf1' + id + '@ejemplo.test' } });
  if (!reg.ok()) falla('no se pudo registrar: ' + reg.status());

  const p = await ctx.newPage();
  const telemetria = p.waitForResponse(r => new URL(r.url()).pathname === '/api/session/state', { timeout: 20000 });
  await p.goto(base + '/dashboard');
  const r = await telemetria.catch(() => null);
  if (!r) falla('la página no mandó telemetría');
  if (!r.ok()) falla('la telemetría de la página dio ' + r.status());

  await p.waitForFunction(() => window.CDI && CDI.currentUser);
  await Promise.all([p.waitForURL(u => u.pathname === '/', { timeout: 20000 }), p.click('#logoutBtn')])
    .catch(() => falla('«Salir» no llevó al inicio'));
  const sesion = await ctx.request.get(base + '/auth/current_user');
  if (sesion.status() !== 401) falla('«Salir» llevó al inicio con la sesión abierta (' + sesion.status() + ')');

  await b.close();
  console.log('OK: CSRF-1 en el navegador');
})().catch(e => falla(e.stack || e.message));
