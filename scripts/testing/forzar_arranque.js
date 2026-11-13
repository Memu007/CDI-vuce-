// Fuerza que la subida le gane al arranque del tablero, para reproducir a
// voluntad la carrera de pantalla_maria1c.js y pantalla_maria7.js. Retiene la
// consulta de sesión (que decide la primera pantalla) hasta que la subida:
//   maria1c: ya terminó y la pantalla pasó a revisión;
//   maria7:  ya salió y sigue sin respuesta; la respuesta llega recién cuando
//            el tablero eligió su primera pantalla.
// No cambia la pantalla ni el producto: se carga antes, con
//   NODE_OPTIONS="--require $PWD/scripts/testing/forzar_arranque.js"
// Desde esta carpeta, el mismo playwright que cargan las pantallas.
const pw = require('playwright');
const path = require('path');
const modo = { pantalla_maria1c: 'terminada', pantalla_maria7: 'en_vuelo' }[path.basename(process.argv[1] || '', '.js')];

function retener(page) {
  let soltar;
  const suelta = new Promise(r => { soltar = r; });
  page.route('**/auth/current_user', async r => { await suelta; await r.continue().catch(() => {}); });
  const route = page.route.bind(page);
  page.route = (url, handler, ...resto) => {
    if (!String(url).includes('upload_pdf')) return route(url, handler, ...resto);
    return route(url, async (r, ...a) => {
      if (modo === 'en_vuelo') {
        soltar();
        await page.waitForSelector('.screen.is-active', { state: 'attached', timeout: 0 });
        return handler(r, ...a);
      }
      await handler(r, ...a);
      await page.waitForSelector('[data-screen="review"].is-active', { state: 'attached', timeout: 0 });
      soltar();
    }, ...resto);
  };
}

if (modo) {
  const launch = pw.chromium.launch.bind(pw.chromium);
  pw.chromium.launch = async (...a) => {
    const b = await launch(...a);
    const newContext = b.newContext.bind(b);
    b.newContext = async (...c) => {
      const ctx = await newContext(...c);
      const newPage = ctx.newPage.bind(ctx);
      ctx.newPage = async () => { const p = await newPage(); retener(p); return p; };
      return ctx;
    };
    return b;
  };
  console.log('forzar_arranque: ' + modo);
}
