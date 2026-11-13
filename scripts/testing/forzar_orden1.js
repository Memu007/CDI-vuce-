// Fuerza la carrera de (z22) en pantalla_orden1.js: el login de vuelta tarda
// más que lo que la prueba retiene la consulta de sesión que la pestaña hizo
// entre salir y entrar. Demora el login hasta que esa consulta vuelve; si a
// los 10 s sigue retenida, entra igual (la prueba la suelta recién al entrar).
// Con la pestaña abierta, también demora el registro de otro usuario.
// No cambia la pantalla ni el producto: se carga antes, con
//   NODE_OPTIONS="--require $PWD/scripts/testing/forzar_orden1.js" CASOS=z22
const pw = require('playwright');
const path = require('path');
const TOPE_MS = 10000;

const hasta = (promesa, ms) => Promise.race([promesa, new Promise(r => setTimeout(() => r('tope'), ms))]);

function demorarLogin(ctx) {
  let afuera = false, hueco = null, aparece, conPestana = false, registrando = false, enElRegistro = 0;
  const primero = new Promise(r => { aparece = r; });
  ctx.on('request', r => {
    if (!r.url().includes('/auth/current_user')) return;
    conPestana = true;
    if (registrando) enElRegistro++;
    if (afuera && !hueco) { hueco = r; aparece(r); }
  });
  const api = ctx.request, post = api.post.bind(api);
  api.post = async (url, ...resto) => {
    // Con la pestaña abierta, el registro de otro usuario tarda más que los 3 s
    // que (z20a), (z21), (z23) y (z24) demoran la consulta de sesión.
    if (conPestana && String(url).includes('/auth/register')) {
      registrando = true;
      await new Promise(r => setTimeout(r, 4000));
      const res = await post(url, ...resto);
      registrando = false;
      console.log('forzar_orden1: el registro de B tardó 4 s más; consultas de la pestaña mientras tanto: ' + enElRegistro);
      return res;
    }
    if (String(url).includes('/auth/logout')) {
      const res = await post(url, ...resto);
      afuera = true;
      return res;
    }
    if (afuera && String(url).includes('/auth/login')) {
      const r = await hasta(primero, TOPE_MS);
      afuera = false;
      if (r === 'tope') console.log('forzar_orden1: la pestaña no consultó la sesión entre salir y entrar: no forzado');
      else {
        const res = await hasta(r.response().catch(() => null), TOPE_MS);
        console.log('forzar_orden1: ' + (res === 'tope' ? 'la consulta del hueco seguía retenida a los 10 s'
          : res ? 'la consulta del hueco volvió antes de entrar: ' + res.status()
          : 'la consulta del hueco se cortó sin respuesta antes de entrar'));
      }
    }
    return post(url, ...resto);
  };
}

if (path.basename(process.argv[1] || '', '.js') === 'pantalla_orden1') {
  const launch = pw.chromium.launch.bind(pw.chromium);
  pw.chromium.launch = async (...a) => {
    const b = await launch(...a);
    const newContext = b.newContext.bind(b);
    b.newContext = async (...c) => { const ctx = await newContext(...c); demorarLogin(ctx); return ctx; };
    return b;
  };
  console.log('forzar_orden1: activo');
}
