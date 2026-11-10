// Si la usuaria va a otra pantalla (Clientes) mientras la página arranca, el
// arranque no la saca de ahí: ni al no llegar el usuario a tiempo, ni al
// encontrar la operación que dejó antes, que queda guardada y se avisa.
// Datos inventados. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_borrador1.js
const { chromium } = require('/opt/node-tools/node_modules/playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8771';
const FACTURA = 'F0001-demo-borrador';

let mal = 0;
const mala = m => { console.error('FALLA: ' + m); mal++; };
const CASOS = [
  { nombre: 'el usuario no llega a tiempo', borrador: false, soltar: 'tarde', aviso: 'No se pudo comprobar la sesión' },
  { nombre: 'hay una operación de antes', borrador: true, soltar: 'enseguida', aviso: 'Quedó guardada la operación' },
];

async function dejarOperacion(ctx) {
  const p = await ctx.newPage();
  await p.goto(base + '/dashboard');
  await p.waitForFunction(() => window.CDI && CDI.goTo && CDI.currentUser);
  await p.evaluate(f => {
    CDI.state = { operacion: { numero_factura: f, moneda: 'DOL', incoterm: 'EXW' },
      items: [{ pieza: '84714900100D', descripcion: 'Equipo demo', origen: 'CN', cantidad: 2, valor_unitario: 10, peso_unitario: 1.5, estado: '2' }] };
    CDI.goTo('ncm');
  }, FACTURA);
  await p.waitForFunction(f => Object.keys(localStorage).some(k => k.startsWith('cdi_v2_state') && (localStorage.getItem(k) || '').includes(f)), FACTURA);
  const cerrada = new Promise(r => p.once('close', r));
  await p.close({ runBeforeUnload: true });
  await cerrada;
}

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  try {
    for (const caso of CASOS) {
      const ctx = await browser.newContext();
      const id = Date.now() + '_' + Math.floor(Math.random() * 1e6);
      const r = await ctx.request.post(base + '/auth/register',
        { data: { username: 'borrador_' + id, password: 'Clave-Inventada-123', email: 'borrador' + id + '@ejemplo.test' } });
      if (!r.ok()) falla('no se pudo registrar el usuario de prueba: ' + r.status());
      if (caso.borrador) await dejarOperacion(ctx);

      // El usuario espera hasta que la prueba lo suelta: el arranque no puede terminar antes.
      let soltar;
      const suelto = new Promise(res => { soltar = res; });
      const p = await ctx.newPage();
      await p.route('**/auth/current_user', async ruta => { await suelto; return ruta.continue().catch(() => {}); });
      await p.goto(base + '/dashboard');
      await p.waitForFunction(() => window.CDI && CDI.goTo && !document.querySelector('.screen.is-active'));
      await p.evaluate(() => CDI.goTo('clientes'));
      if (caso.soltar === 'enseguida') soltar();
      const visto = await p.waitForFunction(t => {
        const el = document.getElementById('avisoBorrador');
        return el && !el.hidden && el.textContent.includes(t);
      }, caso.aviso, { timeout: 15000 }).then(() => true, () => false);
      soltar();
      const pantalla = await p.evaluate(() => (document.querySelector('.screen.is-active') || {}).dataset.screen || null);
      if (pantalla !== 'clientes') mala(caso.nombre + ': el arranque la sacó de Clientes y la llevó a ' + pantalla);
      if (!visto) mala(caso.nombre + ': no apareció el aviso «' + caso.aviso + '»');
      if (caso.borrador) {
        const guardada = await p.evaluate(f => Object.keys(localStorage).some(k => k.startsWith('cdi_v2_state') && (localStorage.getItem(k) || '').includes(f)), FACTURA);
        if (!guardada) mala(caso.nombre + ': la operación de antes ya no está guardada');
      }
      await ctx.close();
    }
  } finally {
    await browser.close();
  }
  if (mal) process.exit(1);
  console.log('ok: el arranque no saca de Clientes');
})().catch(e => falla(e && e.stack || String(e)));
