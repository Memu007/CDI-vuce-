// CSRF-3: con el servidor exigiendo el token CSRF (CSRF_ENFORCE=true, como en
// producción), una sesión que abre la página v2 sin la cookie csrf_token la
// recibe sola y escribe sin volver a entrar ni ver el aviso de otro usuario.
// Si otro entra en el mismo navegador antes de que la pestaña sepa quién es,
// la pestaña lo avisa y no escribe. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_csrf3.js
// corredor: servidor CSRF_ENFORCE=true
const { chromium } = require('playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8876';

async function registrar(ctx, prefijo) {
  const nombre = prefijo + Date.now();
  await registrarCuenta(ctx.request, base,
    { data: { username: nombre, password: 'Clave-Inventada-123', email: nombre + '@ejemplo.test' } });
}

const quienEs = p => p.waitForFunction(() => (window.CDI && CDI.currentUser) || document.getElementById('pestanaAjena')?.open,
  null, { timeout: 20000 }).catch(() => falla('la página no supo quién es el usuario'));
const ajena = p => p.evaluate(() => !!document.getElementById('pestanaAjena')?.open);
const escribir = p => p.evaluate(() => CDI.api('/api/backup/localStorage', { method: 'POST', body: JSON.stringify({ x: 1 }) })
  .then(r => r.status, e => e.message));

async function sinTokenEscribe(b) {
  const ctx = await b.newContext();
  await registrar(ctx, 'csrf3_');
  await ctx.clearCookies({ name: 'csrf_token' });
  const p = await ctx.newPage();
  const telemetria = p.waitForResponse(r => new URL(r.url()).pathname === '/api/session/state' && r.ok(), { timeout: 20000 });
  await p.goto(base + '/dashboard');
  await quienEs(p);
  if (await ajena(p)) falla('la página avisó que entró otro usuario');
  if (!(await ctx.cookies()).some(c => c.name === 'csrf_token' && c.value)) falla('la sesión no recibió el token CSRF');
  const escritura = await escribir(p);
  if (escritura !== 200) falla('la escritura dio ' + escritura);
  if (!(await telemetria.catch(() => null))) falla('ninguna telemetría llegó con el token');
  await ctx.close();
}

// La primera consulta de quién es falla y el reintento queda retenido hasta que
// otro usuario entra en el mismo navegador (registrarse abre su sesión).
async function otroEntraAntesDeSaberQuienEs(b) {
  const ctx = await b.newContext();
  await registrar(ctx, 'csrf3a_');
  await ctx.clearCookies({ name: 'csrf_token' });
  const p = await ctx.newPage();
  let consultas = 0, soltar, reintento;
  const suelto = new Promise(r => { soltar = r; });
  const llegoReintento = new Promise(r => { reintento = r; });
  await p.route('**/auth/current_user', async r => {
    if (++consultas === 1) return r.abort();
    reintento(); await suelto; return r.continue();
  });
  await p.goto(base + '/dashboard');
  await llegoReintento;
  await registrar(ctx, 'csrf3b_');
  soltar();
  await quienEs(p);
  if (!(await ajena(p))) falla('entró otro usuario y la pestaña no lo avisó');
  const escritura = await escribir(p);
  if (escritura === 200) falla('la pestaña ajena escribió a nombre del otro usuario');
  await ctx.close();
}

(async () => {
  const b = await chromium.launch();
  await sinTokenEscribe(b);
  await otroEntraAntesDeSaberQuienEs(b);
  await b.close();
  console.log('OK: CSRF-3 en el navegador');
})().catch(e => falla(e.stack || e.message));
