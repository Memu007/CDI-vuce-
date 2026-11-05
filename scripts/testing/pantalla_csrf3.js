// CSRF-3: con el servidor exigiendo el token CSRF (CSRF_ENFORCE=true, como en
// producción), una sesión que abre la página v2 sin la cookie csrf_token la
// recibe sola y escribe sin volver a entrar ni ver el aviso de otro usuario.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_csrf3.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }

(async () => {
  const base = process.env.BASE_URL || 'http://127.0.0.1:8876';
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
  const id = Date.now();
  const reg = await ctx.request.post(base + '/auth/register',
    { data: { username: 'csrf3_' + id, password: 'Clave-Inventada-123', email: 'csrf3' + id + '@ejemplo.test' } });
  if (!reg.ok()) falla('no se pudo registrar: ' + reg.status());
  await ctx.clearCookies({ name: 'csrf_token' });

  const p = await ctx.newPage();
  const telemetria = p.waitForResponse(r => new URL(r.url()).pathname === '/api/session/state' && r.ok(), { timeout: 20000 });
  await p.goto(base + '/dashboard');
  await p.waitForFunction(() => (window.CDI && CDI.currentUser) || document.getElementById('pestanaAjena')?.open,
    null, { timeout: 20000 }).catch(() => falla('la página no supo quién es el usuario'));
  if (await p.evaluate(() => !!document.getElementById('pestanaAjena')?.open)) falla('la página avisó que entró otro usuario');
  if (!(await ctx.cookies()).some(c => c.name === 'csrf_token' && c.value)) falla('la sesión no recibió el token CSRF');
  const escritura = await p.evaluate(() => CDI.api('/api/backup/localStorage', { method: 'POST', body: JSON.stringify({ x: 1 }) })
    .then(r => r.status, e => e.message));
  if (escritura !== 200) falla('la escritura dio ' + escritura);
  if (!(await telemetria.catch(() => null))) falla('ninguna telemetría llegó con el token');

  await b.close();
  console.log('OK: CSRF-3 en el navegador');
})().catch(e => falla(e.stack || e.message));
