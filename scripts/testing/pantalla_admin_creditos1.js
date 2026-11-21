// Carga de créditos extra desde el panel de admin, con el servidor exigiendo CSRF.
// Un doble clic manda un solo pedido; si la respuesta se pierde, el reintento
// manda el mismo pedido y no carga dos veces; lo que no entra en el tope se ve
// con el texto del servidor; la respuesta de una carga anterior no se escribe
// en el diálogo de otra. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> CDI_DB=<base sqlite del servidor> node scripts/testing/pantalla_admin_creditos1.js
// corredor: servidor CSRF_ENFORCE=true
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8876';
const baseLocal = process.env.CDI_DB || falla('falta CDI_DB: la base sqlite del servidor, para dar admin');

async function registrar(ctx, nombre) {
  await registrarCuenta(ctx.request, base,
    { data: { username: nombre, password: 'Clave-Inventada-123', email: nombre + '@ejemplo.test' } });
}

function hacerAdmin(nombre) {
  execFileSync('python3', ['-c',
    'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute("UPDATE users SET roles=? WHERE username=?", (\'["admin"]\', sys.argv[2])).rowcount; c.commit(); sys.exit(0 if n == 1 else 1)',
    baseLocal, nombre]);
}

const estado = p => p.locator('#carga-estado');
async function esperarEstado(p, texto, que) {
  await p.waitForFunction(t => document.getElementById('carga-estado').textContent === t, texto, { timeout: 15000 })
    .catch(async () => falla(que + ': el diálogo dice «' + await estado(p).textContent() + '», no «' + texto + '»'));
}

async function abrir(p, usuario) {
  await p.fill('#usuarios-buscar', usuario);
  await p.click('#usuarios-buscar ~ button');
  const boton = p.locator('#usuarios-body tr', { hasText: usuario }).getByRole('button', { name: 'Cargar créditos' });
  await boton.click({ timeout: 15000 });
  if (await p.locator('#carga-enviar').isDisabled()) falla('el diálogo de ' + usuario + ' abrió sin poder cargar');
}

(async () => {
  const sufijo = String(Date.now()).slice(-8);
  const admin = 'adcr_adm' + sufijo, uno = 'adcr_uno' + sufijo, otro = 'adcr_otro' + sufijo;
  const b = await chromium.launch();
  for (const nombre of [uno, otro]) { const c = await b.newContext(); await registrar(c, nombre); await c.close(); }
  const ctx = await b.newContext();
  await registrar(ctx, admin);
  hacerAdmin(admin);
  const p = await ctx.newPage();
  const enviados = [];
  p.on('request', r => { if (r.method() === 'POST' && r.url().endsWith('/creditos')) enviados.push(r.postDataJSON()); });
  await p.goto(base + '/dev/dashboard');

  // Doble clic: un pedido, y la fila se refresca con lo cargado.
  await abrir(p, uno);
  await p.fill('#carga-cantidad', '5');
  // Los dos clics van al botón dentro de la página: con dblclick el segundo cae
  // en el formulario, porque «Cargando…» corre el botón.
  await p.evaluate(() => { const b = document.getElementById('carga-enviar'); b.click(); b.click(); });
  await p.waitForFunction(() => !['', 'Cargando…'].includes(document.getElementById('carga-estado').textContent));
  if (enviados.length !== 1) falla('el doble clic mandó ' + enviados.length + ' pedidos');
  await esperarEstado(p, 'Cargada. Ahora tiene 5 vigentes.', 'doble clic');
  await p.locator('#usuarios-body tr', { hasText: uno }).locator('td').nth(7).filter({ hasText: /^5$/ })
    .waitFor({ timeout: 15000 }).catch(() => falla('la fila no muestra los 5 cargados'));
  await p.click('#carga-cerrar');

  // La carga llega al servidor pero la respuesta se pierde: el reintento no carga otra vez.
  await abrir(p, uno);
  await p.fill('#carga-cantidad', '3');
  await p.route('**/creditos', async r => { await r.fetch(); await r.abort(); }, { times: 1 });
  await p.click('#carga-enviar');
  await esperarEstado(p, 'No se pudo cargar: sin conexión. Si la reintentás, no se carga dos veces.', 'sin red');
  if (await p.locator('#carga-enviar').isDisabled()) falla('después de perder la respuesta no se puede reintentar');
  await p.click('#carga-enviar');
  await esperarEstado(p, 'Ya estaba cargada. Ahora tiene 8 vigentes.', 'reintento');
  if (enviados[1].pedido !== enviados[2].pedido) falla('el reintento mandó otro pedido');
  if (enviados[0].pedido === enviados[1].pedido) falla('dos diálogos usaron el mismo pedido');
  await p.click('#carga-cerrar');

  // Lo que no entra en el tope se ve con el texto del servidor.
  await abrir(p, uno);
  await p.fill('#carga-cantidad', '93');
  await p.click('#carga-enviar');
  await esperarEstado(p, 'Ya tiene 8 operaciones extra y el tope es 100: entran como mucho 92.', 'tope');
  if (await p.locator('#carga-enviar').isDisabled()) falla('después del 409 no se puede corregir la cantidad');
  await p.click('#carga-cerrar');

  // La respuesta de la carga de «uno» llega con el diálogo de «otro» abierto.
  let soltar;
  const suelto = new Promise(r => { soltar = r; });
  await p.route('**/creditos', async r => { await suelto; await r.continue(); }, { times: 1 });
  await abrir(p, uno);
  await p.fill('#carga-cantidad', '1');
  await p.click('#carga-enviar');
  await p.click('#carga-cerrar');
  await abrir(p, otro);
  // El refresco de la tabla sale en la misma vuelta que escribiría en el diálogo.
  const refresco = p.waitForRequest(r => r.method() === 'GET' && r.url().includes('/api/admin/usuarios?'));
  soltar();
  await refresco;
  const ajeno = await estado(p).textContent();
  if (ajeno !== '') falla('el diálogo de otra cuenta muestra «' + ajeno + '»');

  await b.close();
  console.log('OK: ADMIN-CREDITOS-1 en el navegador');
})().catch(e => falla(e.stack || e.message));
