// Fuerza en (z22) de pantalla_orden1.js que un pedido de avisos de la pestaña
// llegue al servidor con la sesión cerrada: cada pedido de avisos tarda 1 s más
// en salir y el login de vuelta tarda 2 s más. Las dos demoras quedan por debajo
// de los topes del producto y de la prueba.
// No cambia la pantalla ni el producto: se carga antes, con
//   NODE_OPTIONS="--require $PWD/scripts/testing/forzar_avisos_orden1.js" CASOS=z22
const pw = require('playwright');
const path = require('path');
const AVISOS_MS = 1000, LOGIN_MS = 2000;
const demora = ms => new Promise(r => setTimeout(r, ms));

async function demorar(ctx) {
  // Acá y no al cargar: si este playwright no es el de la pantalla, no se demora nada y no tiene que decir que sí.
  console.log('forzar_avisos_orden1: activo');
  let salio = 0;
  await ctx.route('**/generate_maria/avisos', async ruta => {
    await demora(AVISOS_MS);
    console.log('forzar_avisos_orden1: un pedido de avisos sale ' + (salio ? (Date.now() - salio) + ' ms después de salir' : 'antes de salir'));
    return ruta.continue().catch(() => {});
  });
  const api = ctx.request, post = api.post.bind(api);
  api.post = async (url, ...resto) => {
    if (salio && String(url).includes('/auth/login')) await demora(LOGIN_MS - (Date.now() - salio));
    const res = await post(url, ...resto);
    if (String(url).includes('/auth/logout')) salio = Date.now();
    return res;
  };
}

if (path.basename(process.argv[1] || '', '.js') === 'pantalla_orden1') {
  const launch = pw.chromium.launch.bind(pw.chromium);
  pw.chromium.launch = async (...a) => {
    const b = await launch(...a);
    const newContext = b.newContext.bind(b);
    b.newContext = async (...c) => { const ctx = await newContext(...c); await demorar(ctx); return ctx; };
    return b;
  };
}
