// Si la usuaria va a otra pantalla (Clientes) mientras la página arranca, el
// arranque no la saca de ahí: ni al no llegar el usuario a tiempo, ni al
// encontrar la operación que dejó antes, que queda guardada y se avisa.
// Si no fue a ninguna, o el tour la llevó a la carga, la operación se recupera.
// Datos inventados. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_borrador1.js
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8771';
const FACTURA = 'F0001-demo-borrador';

let mal = 0;
const mala = m => { console.error('FALLA: ' + m); mal++; };
// ir: la pantalla a la que va antes de que llegue el usuario (upload es lo que hace el tour);
// tecla: además toca la página; recupera: la operación de antes se carga en la pestaña.
const CASOS = [
  { nombre: 'el usuario no llega a tiempo', borrador: false, ir: 'clientes', soltar: 'tarde', aviso: 'No se pudo comprobar la sesión', pantalla: 'clientes' },
  { nombre: 'hay una operación de antes', borrador: true, ir: 'clientes', soltar: 'enseguida', aviso: 'Quedó guardada la operación', pantalla: 'clientes' },
  { nombre: 'sin ir a ninguna pantalla', borrador: true, ir: null, soltar: 'enseguida', pantalla: 'review', recupera: true },
  { nombre: 'el tour la lleva a la carga', borrador: true, ir: 'upload', tecla: true, soltar: 'enseguida', pantalla: 'review', recupera: true },
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
  const cerrada = new Promise(r => p.once('close', () => r(true)));
  await p.close({ runBeforeUnload: true });
  if (!await Promise.race([cerrada, new Promise(r => setTimeout(() => r(false), 10000))]))
    falla('la pestaña que deja la operación no se cerró');
}

(async () => {
  const browser = await chromium.launch();
  try {
    for (const caso of CASOS) {
      const ctx = await browser.newContext();
      const id = Date.now() + '_' + Math.floor(Math.random() * 1e6);
      await registrarCuenta(ctx.request, base,
        { data: { username: 'borrador_' + id, password: 'Clave-Inventada-123', email: 'borrador' + id + '@ejemplo.test' } });
      if (caso.borrador) await dejarOperacion(ctx);

      // El usuario espera hasta que la prueba lo suelta: el arranque no puede terminar antes.
      let soltar;
      const suelto = new Promise(res => { soltar = res; });
      const p = await ctx.newPage();
      await p.route('**/auth/current_user', async ruta => { await suelto; return ruta.continue().catch(() => {}); });
      await p.goto(base + '/dashboard');
      await p.waitForFunction(() => window.CDI && CDI.goTo && !document.querySelector('.screen.is-active'));
      if (caso.ir) await p.evaluate(s => CDI.goTo(s), caso.ir);
      if (caso.tecla) await p.keyboard.press('Shift');
      if (caso.soltar === 'enseguida') soltar();
      const visto = !caso.aviso || await p.waitForFunction(t => {
        const el = document.getElementById('avisoBorrador');
        return el && !el.hidden && el.textContent.includes(t);
      }, caso.aviso, { timeout: 15000 }).then(() => true, () => false);
      soltar();
      // Que termine lo que el arranque hace al llegar el usuario antes de mirar la pantalla.
      await p.waitForFunction(() => CDI.currentUser && document.querySelector('.screen.is-active')
        && !(document.getElementById('avisoBorrador').textContent || '').includes('No se pudo comprobar'));
      if (caso.recupera) await p.waitForFunction(s => document.querySelector('.screen.is-active').dataset.screen === s,
        caso.pantalla, { timeout: 5000 }).catch(() => {});
      const pantalla = await p.evaluate(() => (document.querySelector('.screen.is-active') || {}).dataset.screen || null);
      if (pantalla !== caso.pantalla) mala(caso.nombre + ': el arranque tenía que dejarla en ' + caso.pantalla + ' y la llevó a ' + pantalla);
      if (!visto) mala(caso.nombre + ': no apareció el aviso «' + caso.aviso + '»');
      if (caso.recupera) {
        if (!await p.evaluate(f => JSON.stringify(CDI.state || {}).includes(f), FACTURA))
          mala(caso.nombre + ': la operación de antes no se recuperó');
      } else if (caso.borrador) {
        // Adoptarla la copia a la clave de esta pestaña y borra la otra: tiene que seguir en la otra.
        const { enOtra, enEsta } = await p.evaluate(f => {
          const propia = 'cdi_v2_state:' + sessionStorage.getItem('cdi_v2_tab');
          return { enEsta: JSON.stringify(CDI.state || {}).includes(f),
            enOtra: Object.keys(localStorage).some(k => k.startsWith('cdi_v2_state') && k !== propia && (localStorage.getItem(k) || '').includes(f)) };
        }, FACTURA);
        if (enEsta) mala(caso.nombre + ': la operación de antes se cargó en la pestaña');
        if (!enOtra) mala(caso.nombre + ': la operación de antes ya no está guardada');
      }
      await ctx.close();
    }
  } finally {
    await browser.close();
  }
  if (mal) process.exit(1);
  console.log('ok: el arranque no saca de Clientes y recupera si no fue a ninguna pantalla');
})().catch(e => falla(e && e.stack || String(e)));
