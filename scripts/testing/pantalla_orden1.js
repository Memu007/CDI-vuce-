// ORDEN-1 en el navegador local, contra el servidor local (sin terceros).
// En la tabla de productos del paso de NCM:
//  (a) dos pestañas con operaciones distintas, cerradas las dos: al abrir
//      otras dos se recuperan las dos operaciones, sin perder ninguna;
//  (a2) una pestaña que quedó en la carga de archivos no borra el borrador de
//      otra que se cerró a mitad de la revisión;
//  (b) arrastrar un producto con el mouse cambia el orden de la pantalla, del
//      pedido y del TXT; los dos renglones de la misma posición (MARIA-8)
//      siguen saliendo como un ítem con sus dos subítems;
//  (c) un grupo se arrastra entero, y un producto se puede soltar sobre él;
//  (d) recargar enseguida de arrastrar conserva el orden;
//  (e) arrastrar después de una acción masiva: Ctrl+Z no vuelve el orden, y
//      la selección sigue a los productos;
//  (f) la operación es de quien la dejó: otro usuario en la misma computadora
//      no la ve, y la clave vieja sin pestaña o el sobre de hoy sin dueño no
//      se muestran a nadie y se borran;
//  (g) un borrador de más de 7 días no se recupera y se borra; uno de casi 7
//      días, sí;
//  (h) la operación de una pestaña que murió sin avisar (sin pagehide) hace 4
//      minutos se recupera;
//  (i) una pestaña duplicada no toma la operación de la original, que sigue
//      abierta; la misma pestaña restaurada después de un cierre sin pagehide
//      recupera la suya;
//  (j) si la consulta del usuario falla (500) al abrir, la pestaña lo vuelve a
//      pedir y la operación se guarda con su dueño.
//  (k) si otro usuario entra en el mismo navegador mientras la pestaña
//      reintenta, la operación cargada no se guarda a su nombre ni él la
//      recupera, y la pestaña lo avisa.
//  (l) a (n) si otro usuario entra después (con o sin salir el primero), lo
//      que se carga no se guarda y la pestaña lo avisa; si sale y vuelve a
//      entrar el mismo, sigue guardando;
//  (o) al volver de la caché del navegador queda en uso, salvo que haya
//      entrado otro;
//  (p) al recargar con la consulta del usuario lenta o caída, la operación
//      vuelve cuando llega el usuario, sin pisar otra cargada mientras;
//  (q) sin lugar en el navegador, avisa;
//  (r) a (t) los reintentos de la consulta del usuario: no con 401, sí con un
//      corte de red, de 1 a 30 segundos;
//  (u) al recargar toma su borrador aunque haya otro cerrado más nuevo;
//  (v) la operación terminada se borra; (w) se barren el vencido de otro
//      usuario y el sobre de otra versión;
//  (y) con otro usuario adentro, la pestaña del dueño no borra lo suyo.
//  (m2) se cierra la sesión: avisa; vuelve a entrar el mismo: deja de avisar;
//  (z) y (z2) al recargar con el usuario lento, si la pestaña ya está en otra
//      pantalla o subiendo un archivo, la operación de antes no la pisa;
//  (z3) al recargar sin lugar en el navegador, avisa; (z4) si la consulta
//      del usuario no contesta, avisa.
//  (z5) a (z8) al recargar con el usuario lento: lo que se hace mientras
//      (otra carga, elegir un archivo) no lo pisa la operación de antes; con
//      la consulta caída avisa; si entra otro usuario no guarda a su nombre;
//  (z9) a (z12) si cambia la sesión (entra otro, se cierra, vuelve a
//      entrar el mismo) mientras una pestaña duplicada mira si la
//      original vive, no adopta la operación de otro ni deja sobres sin dueño;
//  (z13) a (z16) tocar la pestaña de cualquier forma (clic sin puntero,
//      tecla, soltar un archivo, apretar el mouse) antes de que llegue el
//      usuario frena la recuperación tardía;
//  (z17) y (z18) con la sesión cerrada o la red cortada, pregunta quién es
//      una vez y no en cada guardado; (z19) el aviso de otro usuario no lo
//      pisa el de la red.
//  (z20) a (z24) ORDEN-1b: si entra otro usuario en el mismo navegador, la
//      pestaña de A no genera, no guarda un cliente ni cierra la sesión del
//      otro, aunque el servidor no exija CSRF, y se tapa; si A sale y vuelve
//      a entrar, sigue trabajando. (z25) con la sesión cerrada, una escritura
//      va al login; (z26) «Salir» sin poder comprobar quién es no va al
//      inicio como si hubiera salido; (z27) no manda telemetría a nombre
//      del otro. (z12) avisa
//      mientras comprueba la sesión y recupera la operación al confirmarla.
//  (z29) la respuesta de «quién es» que llega cuando ya entró otro no
//      autoriza la escritura; (z30) la pestaña tapada al abrir no escribe;
//  (z31) PUT, DELETE y PATCH con otro adentro no salen; (z32) Escape no
//      destapa la pestaña y «Recargar» recarga; (z34) al volver del pago no
//      toma los datos del otro; (z35) ni escribe con la respuesta de A que
//      llega cuando ya entró B.
// Datos inventados. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_orden1.js
// corredor: servidor CSRF_ENFORCE=true
// El servidor corre con CSRF_ENFORCE=true, como en producción.
const { chromium, request } = require('/opt/node-tools/node_modules/playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
const cargarCuitDelPerfil = require('./_cuit_perfil');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8771';
const INTERVALO_MS = 2500;  // el guardado periódico de app_v2.js
// CASOS=a,b corre sólo esos casos (los usa el script de sabotajes).
const CASOS = (process.env.CASOS || '').split(',').filter(Boolean);
const corre = c => CASOS.length === 0 || CASOS.includes(c);

const OPERACION = { moneda: 'DOL', incoterm: 'EXW', fecha_emision: '22/06/2026', flete: 120, seguro: 3.5,
                    comprador_cuit: '30999999995', comprador_nombre: 'IMPORTADORA DEMO S.A.',
                    vendedor_nombre: 'PROVEEDOR DEMO', aduana_codigo: '073' };
const prod = (descripcion, pieza, cantidad, valor_unitario, extra) => Object.assign(
  { pieza, descripcion, origen: 'CN', cantidad, valor_unitario, peso_unitario: 1.5, estado: '2' }, extra || {});
const GRIS = prod('Lona demo gris', '39219019900Z', 11, 2.5);
const AZUL = prod('Lona demo azul', '39219019900Z', 13, 2.75);
const EQUIPO = prod('Equipo demo', '84714900100D', 3, 411.11);
const CABLE = prod('Cable demo', '85444200900E', 40, 0.73);
const TEL_1 = prod('Telefono demo uno', '85171300100F', 7, 99.97, { grupo_id: 7 });
const TEL_2 = prod('Telefono demo dos', '85171300100F', 2, 55.51, { grupo_id: 7 });

const CLAVE = 'Clave-Inventada-123';
// La cookie CSRF de la sesión del contexto: el servidor de la prueba la exige.
const csrf = async ctx => ((await ctx.cookies(base)).find(c => c.name === 'csrf_token') || {}).value || '';
const salir = async ctx => ctx.request.post(base + '/auth/logout', { headers: { 'X-CSRF-Token': await csrf(ctx) } });
// Registra un usuario y deja abierta su sesión en el contexto; devuelve el nombre.
async function nuevoUsuario(ctx, nombre) {
  const p = await ctx.newPage();
  const id = Date.now() + '_' + Math.floor(Math.random() * 1e6);
  const usuario = nombre + '_' + id;
  await registrarCuenta(p.request, base,
    { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: usuario, password: CLAVE, email: nombre + id + '@ejemplo.test' } });
  // Sin el CUIT del despachante no se genera el TXT (ESTUDIO-1); inventado.
  await cargarCuitDelPerfil(p.request, base);
  await p.close();
  return usuario;
}

async function entrar(ctx, usuario) {
  const r = await ctx.request.post(base + '/auth/login', { data: { username: usuario, password: CLAVE } });
  if (!r.ok()) falla('no se pudo volver a entrar como ' + usuario + ': ' + r.status());
}

// Cada consulta de usuario de la pestaña vuelve a los 3 s, y ninguna antes de que llegue la
// de Generar: así Generar comprueba la sesión, lenta pero bajo el tope. Devuelve si llegó.
async function demorarHastaGenerar(p) {
  let abrirPuerta, llego = false;
  const puerta = new Promise(r => { abrirPuerta = r; });
  await p.route('**/auth/current_user', async ruta => {
    const demora = new Promise(r => setTimeout(r, 3000));
    if (ruta.request().headers()['x-arnes-generar']) { llego = true; abrirPuerta(); }
    await Promise.all([demora, puerta]);
    return ruta.continue().catch(() => {});
  });
  await p.evaluate(() => {
    const original = window.fetch;
    window.fetch = function (url, opciones) {
      if (String(url).endsWith('/auth/current_user') && new Error().stack.includes('generateMaria'))
        opciones = { ...opciones, headers: { ...(opciones && opciones.headers), 'x-arnes-generar': '1' } };
      return original.call(this, url, opciones);
    };
  });
  return () => llego;
}

// Lo que la pestaña pide por su cuenta al entrar a «Validación», y cuántas veces: los avisos, al entrar y
// cuando llegan las tarjetas; la validación, la de la pantalla y la del semáforo.
const AL_ENTRAR_A_VALIDACION = [['/generate_maria/avisos', 2], ['/api/validate/smart', 2]];
// Sigue los pedidos de la pestaña. Lo que devuelve espera a que no quede ninguno en vuelo y a que haya
// terminado, de cada ruta, la cantidad dada: «ninguno en vuelo» solo no alcanza, porque la pantalla saca
// pedidos nuevos cuando vuelven otros y desde temporizadores.
function seguirPedidos(p) {
  const enVuelo = new Set(), terminados = {};
  let mirar = () => {};
  const ruta = r => new URL(r.url()).pathname;
  p.on('request', r => enVuelo.add(r));
  p.on('requestfailed', r => { enVuelo.delete(r); mirar(); });
  p.on('requestfinished', r => { enVuelo.delete(r); terminados[ruta(r)] = (terminados[ruta(r)] || 0) + 1; mirar(); });
  return esperados => new Promise((bien, mal) => {
    const faltan = () => esperados.filter(([cual, n]) => (terminados[cual] || 0) < n).map(([cual, n]) => cual + ' (' + (terminados[cual] || 0) + ' de ' + n + ')');
    const tope = setTimeout(() => mal(new Error('la pestaña no terminó sus pedidos: faltan ' + (faltan().join(', ') || 'ninguno') +
      '; en vuelo: ' + ([...enVuelo].map(ruta).join(', ') || 'ninguno'))), 15000);
    mirar = () => { if (!enVuelo.size && !faltan().length) { clearTimeout(tope); mirar = () => {}; bien(); } };
    mirar();
  });
}

// Con `pestana`, la página arranca con ese id de pestaña en sessionStorage,
// como la duplica o la restaura el navegador; sólo en la primera carga.
async function abrir(ctx, pestana) {
  const p = await ctx.newPage();
  if (pestana) await p.addInitScript(id => {
    if (window.name !== 'cdi-prueba-pestana') { window.name = 'cdi-prueba-pestana'; sessionStorage.setItem('cdi_v2_tab', id); }
  }, pestana);
  p.on('dialog', d => d.accept().catch(() => {}));
  await p.goto(base + '/dashboard');
  await p.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && document.querySelector('.screen.is-active'));
  // El banner de la prueba gratis aparece con el usuario y corre la tabla
  // hacia abajo: sin esperarlo, el mouse aprieta sobre la fila de arriba.
  await p.waitForFunction(() => CDI.currentUser);
  return p;
}

// Duplica la pestaña `id` y la frena justo antes de mirar por primera vez si la
// original sigue viva (el lock que pide pestanaViva con signal): marca window.__esperando y
// sigue cuando la prueba llama a window.__seguir(). Con `lenta`, el usuario
// llega a los 10 s, después de la espera del arranque. No espera la pantalla:
// aparece recién después de mirar. Devuelve también cuándo llegan los
// conectores del tablero, que se piden con api() y un 401 manda al login.
async function duplicar(ctx, id, lenta) {
  const p = await ctx.newPage();
  await p.addInitScript(id => {
    if (window.name !== 'cdi-prueba-pestana') { window.name = 'cdi-prueba-pestana'; sessionStorage.setItem('cdi_v2_tab', id); }
    const pedir = navigator.locks.request.bind(navigator.locks);
    navigator.locks.request = (...args) => {
      if (!(args[1] && args[1].signal) || window.__esperando) return pedir(...args);
      window.__esperando = true;
      return new Promise(r => { window.__seguir = r; }).then(() => pedir(...args));
    };
  }, id);
  if (lenta) {
    const hasta = Date.now() + 10000;
    await p.route('**/auth/current_user', async ruta => {
      await new Promise(r => setTimeout(r, Math.max(0, hasta - Date.now())));
      return ruta.continue().catch(() => {});
    });
  }
  p.on('dialog', d => d.accept().catch(() => {}));
  const conectores = p.waitForResponse(r => r.url().includes('/api/system/connectors'), { timeout: 20000 }).then(() => true, () => false);
  await p.goto(base + '/dashboard');
  return { p, conectores };
}

async function cargar(p, factura, items) {
  await p.evaluate(([op, its]) => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = op;
    CDI.state.items = its;
    CDI.goTo('ncm');
  }, [Object.assign({ numero_factura: factura }, OPERACION), items]);
  await p.locator('#ncmTbody tr').first().waitFor({ timeout: 5000 });
}

// Lo que hay guardado en el navegador, sea cual sea la forma de la clave.
const borradores = p => p.evaluate(() => Object.keys(localStorage)
  .filter(k => k.startsWith('cdi_v2_state')).map(k => ({ clave: k, texto: localStorage.getItem(k) })));

async function esperarBorradores(p, facturas, que) {
  const ok = await p.waitForFunction(fs => {
    const textos = Object.keys(localStorage).filter(k => k.startsWith('cdi_v2_state')).map(k => localStorage.getItem(k) || '');
    return fs.every(f => textos.some(t => t.includes('"' + f + '"')));
  }, facturas, { timeout: 4 * INTERVALO_MS }).then(() => true, () => false);
  if (!ok) falla(que + ': ' + JSON.stringify((await borradores(p)).map(b => b.clave + ' → ' +
    ((b.texto || '').match(/"numero_factura":"([^"]*)"/) || [])[1])));
}

async function cerrar(p) {
  const cerrada = new Promise(r => (p.isClosed() ? r() : p.once('close', r)));
  await p.close({ runBeforeUnload: true });
  await cerrada;
}

// La pestaña puede hacer otra consulta mientras se cierra: una ruta que la
// atendiera se quedaría sin contexto a mitad de camino.
async function cerrarConRutas(ctx, p) {
  await p.unrouteAll({ behavior: 'ignoreErrors' });
  await ctx.close();
}

// Abre, carga la operación, espera a que se guarde y cierra la pestaña.
async function dejarAMedias(ctx, factura) {
  const p = await abrir(ctx);
  await cargar(p, factura, [prod('Producto de ' + factura, '84714900100D', 2, 10)]);
  await esperarBorradores(p, [factura], 'la operación ' + factura + ' no se guarda');
  await cerrar(p);
}

// Toca localStorage desde una página del mismo sitio que no corre la app, así
// nadie adopta nada al abrirla.
async function enElSitio(ctx, f, arg) {
  const p = await ctx.newPage();
  await p.goto(base + '/health');
  const r = await p.evaluate(f, arg);
  await p.close();
  return r;
}
// Corre la fecha de guardado (edadMs atrás) o la marca de cerrada del borrador
// de la factura, sin tocar el resto del sobre. Devuelve su clave.
async function cambiarBorrador(ctx, factura, cambios) {
  const clave = await enElSitio(ctx, ([f, c]) => {
    const k = Object.keys(localStorage).find(k => k.startsWith('cdi_v2_state') && (localStorage.getItem(k) || '').includes('"' + f + '"'));
    if (!k) return null;
    const sobre = JSON.parse(localStorage.getItem(k));
    if (c.edadMs !== undefined) sobre.savedAt = Date.now() - c.edadMs;
    if (c.closed !== undefined) sobre.closed = c.closed;
    localStorage.setItem(k, JSON.stringify(sobre));
    return k;
  }, [factura, cambios]);
  if (!clave) falla('no está el borrador de ' + factura);
  return clave;
}
const guardadas = async ctx => (await enElSitio(ctx, () => Object.keys(localStorage)
  .filter(k => k.startsWith('cdi_v2_state')).map(k => ((localStorage.getItem(k) || '').match(/"numero_factura":"([^"]*)"/) || [])[1])));
const MIN = 60 * 1000;
const DIA = 24 * 60 * MIN;

async function recuperada(p) {
  const hay = await p.waitForFunction(() => CDI.state && CDI.state.items && CDI.state.items.length > 0,
    null, { timeout: 5000 }).then(() => true, () => false);
  return hay ? p.evaluate(() => (CDI.state.operacion || {}).numero_factura || '(sin factura)') : null;
}

const pantalla = p => p.evaluate(() => document.querySelector('.screen.is-active').dataset.screen);
const orden = p => p.evaluate(() => CDI.state.items.map(it => it.descripcion));
const filas = p => p.$$eval('#ncmTbody tr:not(.row-sub) td.col-desc', tds => tds.map(td => td.textContent.trim()));

// Arrastre real: botón apretado sobre el agarre de la fila y soltado sobre otra.
// Da false si no hay agarre o si el navegador no llegó a empezar el arrastre
// (dragstart que la pantalla no canceló).
async function arrastrar(p, desde, hacia) {
  const agarre = await p.locator(desde + ' .drag-grip').boundingBox({ timeout: 3000 }).catch(() => null);
  if (!agarre) return false;
  const destino = await p.locator(hacia).boundingBox({ timeout: 3000 });
  await p.evaluate(() => {
    if (!window.__arrastresContados) {
      window.__arrastresContados = true;
      window.addEventListener('dragstart', e => { if (!e.defaultPrevented) window.__arrastres++; });
    }
    window.__arrastres = 0;
  });
  await p.mouse.move(agarre.x + agarre.width / 2, agarre.y + agarre.height / 2);
  await p.mouse.down();
  await p.mouse.move(destino.x + destino.width / 2, destino.y + destino.height / 2, { steps: 10 });
  await p.mouse.up();
  return (await p.evaluate(() => window.__arrastres)) > 0;
}
const fila = i => '#ncmTbody tr[data-index="' + i + '"]';
const grupo = g => '#ncmTbody tr.row-grouped[data-grupo-id="' + g + '"]';
const igual = (a, b) => JSON.stringify(a) === JSON.stringify(b);

async function generar(p) {
  await p.evaluate(() => CDI.goTo('validating'));
  await p.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 });
  await p.fill('#sbtSufijoValor', 'AA(DemoPouchs)-CA00-');
  const resp = p.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
  await p.click('#validatingGenerate');
  const r = await resp;
  const cuerpo = await r.json();
  if (!r.ok() || !cuerpo.content) falla('no se generó el TXT: ' + r.status() + ' ' + JSON.stringify(cuerpo).slice(0, 300));
  return { pedido: JSON.parse(r.request().postData()), txt: cuerpo.content };
}
const campo = (bloque, c) => (bloque.match(new RegExp('^' + c + '=(.*?)\\r?$', 'm')) || [])[1];
const bloques = (txt, tipo) => txt.split('\r\n\r\n').filter(b => b.startsWith('[' + tipo + ']'));

(async () => {
  const b = await chromium.launch();  // el Chromium que trae el Playwright instalado
  const nuevoContexto = async nombre => {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    await nuevoUsuario(ctx, nombre);
    return ctx;
  };

  // (a) Dos pestañas a la vez, cerradas las dos.
  if (corre('a')) {
    const ctx = await nuevoContexto('ord1a');
    const p1 = await abrir(ctx);
    await cargar(p1, 'ORD-A', [prod('Producto de la pestaña A', '84714900100D', 2, 10)]);
    // Sin esto la segunda se abre antes de que la primera guarde y no hay qué tomar.
    await esperarBorradores(p1, ['ORD-A'], 'la primera pestaña no guardó su operación');
    const p2 = await abrir(ctx);
    if (await recuperada(p2)) falla('la segunda pestaña tomó la operación de la primera, que sigue abierta');
    await cargar(p2, 'ORD-B', [prod('Producto de la pestaña B', '84714900100D', 3, 20)]);
    await esperarBorradores(p2, ['ORD-A', 'ORD-B'], 'con dos pestañas abiertas no quedan guardadas las dos operaciones');
    await cerrar(p1);
    await cerrar(p2);
    const p3 = await abrir(ctx);
    const r3 = await recuperada(p3);
    const p4 = await abrir(ctx);
    const r4 = await recuperada(p4);
    if (!igual([r3, r4].sort(), ['ORD-A', 'ORD-B'])) falla('al volver a abrir dos pestañas se recupera ' + JSON.stringify([r3, r4]) + ' y no ORD-A y ORD-B');
    console.log('OK dos pestañas cerradas: al abrir otras dos se recuperan ' + r3 + ' y ' + r4);
    await ctx.close();
  }

  // (a2) Una pestaña en la carga de archivos no borra el borrador de otra.
  if (corre('a2')) {
    const ctx = await nuevoContexto('ord1b');
    const p1 = await abrir(ctx);
    const p2 = await abrir(ctx);  // queda en la carga de archivos
    if ((await pantalla(p2)) !== 'upload') falla('la segunda pestaña no quedó en la carga de archivos');
    await cargar(p1, 'ORD-C', [prod('Producto de la pestaña C', '84714900100D', 2, 10)]);
    await esperarBorradores(p1, ['ORD-C'], 'la operación de la pestaña C no se guarda');
    await cerrar(p1);
    // Lo que se comprueba es que algo NO pasa: se deja correr el guardado
    // periódico de la pestaña en la carga tres veces (espera fija, declarada).
    await p2.waitForTimeout(3 * INTERVALO_MS + 500);
    const p3 = await abrir(ctx);
    const r3 = await recuperada(p3);
    if (r3 !== 'ORD-C') falla('la pestaña que quedó en la carga de archivos borró la operación cerrada: se recupera ' + r3);
    console.log('OK una pestaña en la carga de archivos no borra la operación que otra dejó a medias');
    await ctx.close();
  }

  // (b) Arrastre con el mouse; el pedido y el TXT siguen el orden nuevo.
  if (corre('b')) {
    const ctx = await nuevoContexto('ord1c');
    const p = await abrir(ctx);
    await cargar(p, 'ORD-D', [GRIS, EQUIPO, AZUL, CABLE]);
    if (!(await arrastrar(p, fila(3), fila(0)))) falla('el producto no tiene de dónde arrastrarlo');
    const esperado = ['Cable demo', 'Lona demo gris', 'Equipo demo', 'Lona demo azul'];
    if (!igual(await orden(p), esperado)) falla('arrastrar el cable arriba de todo deja ' + JSON.stringify(await orden(p)));
    if (!igual(await filas(p), esperado)) falla('la tabla no muestra el orden nuevo: ' + JSON.stringify(await filas(p)));
    const { pedido, txt } = await generar(p);
    if (!igual(pedido.items.map(it => it.descripcion), esperado)) falla('el pedido no va en el orden nuevo: ' + JSON.stringify(pedido.items.map(it => it.descripcion)));
    const arts = bloques(txt, 'ART');
    const posiciones = arts.map(a => campo(a, 'IESPNCE'));
    if (!igual(posiciones, ['8544.42.00.900E', '3921.90.19.900Z', '8471.49.00.100D'])) falla('los ítems del TXT no siguen el orden nuevo: ' + JSON.stringify(posiciones));
    if (!igual(arts.map(a => campo(a, 'NARTEXT')), ['0001', '0002', '0003'])) falla('los ítems no quedan numerados corridos');
    // Un ítem sin subítems lleva un [SBT] 0000 sólo con el sufijo; las dos
    // lonas, el 0001 y el 0002 con su cantidad, gris primero.
    const sbts = bloques(txt, 'SBT').map(s => [campo(s, 'NART'), campo(s, 'ISBT'), campo(s, 'QSBTUNTDCL') || '']);
    if (!igual(sbts, [['0001', '0000', ''], ['0002', '0001', '11.00'], ['0002', '0002', '13.00'], ['0003', '0000', '']]))
      falla('los subítems no quedan bajo su ítem, en orden: ' + JSON.stringify(sbts));
    console.log('OK arrastrar con el mouse cambia la tabla, el pedido y el TXT: ' + posiciones.join(' · ') + '; las dos lonas, un ítem con dos subítems');
    await ctx.close();
  }

  // (c) El grupo se arrastra entero; un producto se suelta sobre el grupo.
  if (corre('c')) {
    const ctx = await nuevoContexto('ord1d');
    const p = await abrir(ctx);
    await cargar(p, 'ORD-E', [TEL_1, EQUIPO, TEL_2, CABLE]);
    if (!(await arrastrar(p, grupo(7), fila(3)))) falla('el grupo no tiene de dónde arrastrarlo');
    let esperado = ['Equipo demo', 'Cable demo', 'Telefono demo uno', 'Telefono demo dos'];
    if (!igual(await orden(p), esperado)) falla('arrastrar el grupo sobre el cable deja ' + JSON.stringify(await orden(p)));
    if (!(await arrastrar(p, fila(0), grupo(7)))) falla('el equipo no tiene de dónde arrastrarlo');
    esperado = ['Cable demo', 'Telefono demo uno', 'Telefono demo dos', 'Equipo demo'];
    if (!igual(await orden(p), esperado)) falla('soltar el equipo sobre el grupo deja ' + JSON.stringify(await orden(p)));
    // Con el grupo abierto, soltar sobre uno de sus renglones es soltar sobre el grupo.
    await p.click('[data-expand-grupo="7"]');
    await p.locator('#ncmTbody tr.row-sub').first().waitFor({ timeout: 3000 });
    if (!(await arrastrar(p, fila(0), '#ncmTbody tr.row-sub >> nth=1'))) falla('el cable no tiene de dónde arrastrarlo');
    esperado = ['Telefono demo uno', 'Telefono demo dos', 'Cable demo', 'Equipo demo'];
    if (!igual(await orden(p), esperado)) falla('soltar el cable sobre un renglón del grupo abierto deja ' + JSON.stringify(await orden(p)));
    console.log('OK el grupo se arrastra entero y se puede soltar sobre él, abierto o cerrado');
    await ctx.close();
  }

  // (d) Recargar enseguida de arrastrar conserva el orden.
  if (corre('d')) {
    const ctx = await nuevoContexto('ord1e');
    const p = await abrir(ctx);
    await cargar(p, 'ORD-F', [GRIS, EQUIPO, AZUL, CABLE]);
    await esperarBorradores(p, ['ORD-F'], 'la operación no se guarda');
    // Justo después de un guardado periódico, así el que guarda el orden
    // nuevo es la página al irse y no el reloj (si el borrador dice cuándo
    // se guardó).
    const guardadoEn = () => p.evaluate(() => {
      const k = Object.keys(localStorage).find(c => c.startsWith('cdi_v2_state'));
      try { return JSON.parse(localStorage.getItem(k)).savedAt || null; } catch (_) { return null; }
    });
    const antes = await guardadoEn();
    if (antes) await p.waitForFunction(a => Object.keys(localStorage).filter(c => c.startsWith('cdi_v2_state'))
      .some(c => { try { return JSON.parse(localStorage.getItem(c)).savedAt !== a; } catch (_) { return false; } }),
      antes, { timeout: 3 * INTERVALO_MS });
    if (!(await arrastrar(p, fila(2), fila(0)))) falla('el producto no tiene de dónde arrastrarlo');
    const esperado = ['Lona demo azul', 'Lona demo gris', 'Equipo demo', 'Cable demo'];
    if (!igual(await orden(p), esperado)) falla('arrastrar la lona azul arriba deja ' + JSON.stringify(await orden(p)));
    await p.reload();
    await p.waitForFunction(() => window.CDI && CDI.goTo && document.querySelector('.screen.is-active'));
    if ((await recuperada(p)) !== 'ORD-F') falla('al recargar no se recupera la operación');
    if (!igual(await orden(p), esperado)) falla('al recargar enseguida vuelve el orden de antes: ' + JSON.stringify(await orden(p)));
    // Al recuperar se vuelve al paso 2; la tabla de productos es la del paso de NCM.
    await p.evaluate(() => CDI.goTo('ncm'));
    await p.locator('#ncmTbody tr').first().waitFor({ timeout: 5000 });
    if (!igual(await filas(p), esperado)) falla('la tabla recargada no muestra el orden nuevo: ' + JSON.stringify(await filas(p)));
    console.log('OK recargar enseguida de arrastrar conserva el orden');
    await ctx.close();
  }

  // (e) Acción masiva, arrastre y Ctrl+Z: el orden no vuelve atrás.
  if (corre('e')) {
    const ctx = await nuevoContexto('ord1f');
    const p = await abrir(ctx);
    await cargar(p, 'ORD-G', [EQUIPO, CABLE, prod('Mouse demo', '84716053000H', 5, 7.5)]);
    await p.check('[data-row-check="0"]');
    await p.check('[data-row-check="1"]');
    await p.fill('#ncmBatchOrigin', 'BR');
    await p.click('#ncmBatchApplyOrigin');
    await p.waitForFunction(() => CDI.state.items[0].origen !== 'CN', null, { timeout: 3000 })
      .catch(() => falla('la acción masiva de origen no se aplicó'));
    if (!(await arrastrar(p, fila(2), fila(0)))) falla('el producto no tiene de dónde arrastrarlo');
    const esperado = ['Mouse demo', 'Equipo demo', 'Cable demo'];
    if (!igual(await orden(p), esperado)) falla('arrastrar el mouse arriba deja ' + JSON.stringify(await orden(p)));
    // Estaban elegidos el equipo y el cable: siguen elegidos en su lugar nuevo.
    const marcados = await p.$$eval('#ncmTbody [data-row-check]', cbs => cbs.filter(c => c.checked).map(c => c.getAttribute('data-row-check')));
    if (!igual(marcados, ['1', '2'])) falla('al arrastrar, la selección no sigue a los productos: quedan elegidas las filas ' + JSON.stringify(marcados));
    await p.locator('body').click({ position: { x: 5, y: 300 } });
    await p.keyboard.press('Control+z');
    // El deshacer es sincrónico: si iba a cambiar algo, ya cambió.
    if (!igual(await orden(p), esperado)) falla('Ctrl+Z después de arrastrar vuelve el orden de antes: ' + JSON.stringify(await orden(p)));
    console.log('OK Ctrl+Z después de arrastrar no deshace el orden');
    await ctx.close();
  }

  // (f) La operación es de quien la dejó.
  if (corre('f')) {
    const ctx = await nuevoContexto('ord1g');
    const a = await (async () => (await (await abrir(ctx)).evaluate(() => CDI.currentUser.username)))();
    await dejarAMedias(ctx, 'DUE-A');
    // La clave de antes de ORDEN-1: la operación sola, sin pestaña ni dueño.
    await enElSitio(ctx, it => localStorage.setItem('cdi_v2_state', JSON.stringify(
      { operacion: { numero_factura: 'VIEJA-SIN-PESTANA' }, items: [it] })), prod('Producto viejo', '84714900100D', 1, 1));
    // Un sobre de hoy, cerrado y con pestaña, pero sin dueño: se descarta por
    // no tener dueño, no por la edad.
    await enElSitio(ctx, it => localStorage.setItem('cdi_v2_state:sin-dueno', JSON.stringify(
      { v: 1, savedAt: Date.now(), closed: true, state: { operacion: { numero_factura: 'SIN-DUENO' }, items: [it] } })),
      prod('Producto sin dueño', '84714900100D', 1, 1));
    const usuarioB = await nuevoUsuario(ctx, 'ord1h');
    const pb = await abrir(ctx);
    if ((await pb.evaluate(() => CDI.currentUser.username)) !== usuarioB) falla('la sesión no pasó al segundo usuario');
    const rb = await recuperada(pb);
    if (rb) falla('otro usuario en la misma computadora recupera la operación ' + rb);
    const pb2 = await abrir(ctx);
    const rb2 = await recuperada(pb2);
    if (rb2) falla('otro usuario en la misma computadora recupera la operación ' + rb2 + ' en su segunda pestaña');
    await cerrar(pb);
    await cerrar(pb2);
    if ((await guardadas(ctx)).includes('VIEJA-SIN-PESTANA')) falla('la clave vieja sin pestaña no se descarta');
    if ((await guardadas(ctx)).includes('SIN-DUENO')) falla('el borrador de hoy sin dueño no se descarta');
    await entrar(ctx, a);
    const pa = await abrir(ctx);
    const ra = await recuperada(pa);
    if (ra !== 'DUE-A') falla('quien dejó la operación no la recupera: se recupera ' + ra);
    console.log('OK la operación sólo la recupera quien la dejó; la clave vieja sin pestaña no se muestra');
    await ctx.close();
  }

  // (g) La edad: 7 días.
  if (corre('g')) {
    const ctx = await nuevoContexto('ord1i');
    await dejarAMedias(ctx, 'EDAD-FUERA');
    await cambiarBorrador(ctx, 'EDAD-FUERA', { edadMs: 7 * DIA + MIN });
    const p1 = await abrir(ctx);
    const r1 = await recuperada(p1);
    if (r1) falla('se recupera un borrador de hace más de 7 días: ' + r1);
    if ((await guardadas(ctx)).includes('EDAD-FUERA')) falla('el borrador de hace más de 7 días no se borra al barrer');
    await cerrar(p1);
    await dejarAMedias(ctx, 'EDAD-DENTRO');
    await cambiarBorrador(ctx, 'EDAD-DENTRO', { edadMs: 7 * DIA - MIN });
    const p2 = await abrir(ctx);
    const r2 = await recuperada(p2);
    if (r2 !== 'EDAD-DENTRO') falla('un borrador de hace casi 7 días no se recupera: se recupera ' + r2);
    console.log('OK un borrador de más de 7 días no vuelve y se borra; uno de casi 7, sí');
    await ctx.close();
  }

  // (h) Una pestaña que murió sin pagehide hace 4 minutos.
  if (corre('h')) {
    const ctx = await nuevoContexto('ord1j');
    await dejarAMedias(ctx, 'HUERFANA');
    await cambiarBorrador(ctx, 'HUERFANA', { closed: false, edadMs: 4 * MIN });
    const p = await abrir(ctx);
    const r = await recuperada(p);
    if (r !== 'HUERFANA') falla('no se recupera la operación de una pestaña que murió sin avisar hace 4 minutos: se recupera ' + r);
    console.log('OK la operación de una pestaña muerta sin pagehide vuelve a los 3 minutos');
    await ctx.close();
  }

  // (i) Duplicada y restaurada.
  if (corre('i')) {
    const ctx = await nuevoContexto('ord1k');
    const p1 = await abrir(ctx);
    await cargar(p1, 'DUP-A', [prod('Producto de la original', '84714900100D', 2, 10)]);
    await esperarBorradores(p1, ['DUP-A'], 'la operación de la original no se guarda');
    const id1 = await p1.evaluate(() => sessionStorage.getItem('cdi_v2_tab'));
    if (!id1) falla('la pestaña no tiene id en sessionStorage');
    const p2 = await abrir(ctx, id1);
    const r2 = await recuperada(p2);
    if (r2) falla('la pestaña duplicada tomó la operación de la original, que sigue abierta: ' + r2);
    await esperarBorradores(p1, ['DUP-A'], 'con la duplicada abierta, la original perdió su operación');
    await cerrar(p2);
    // La original se va sin pagehide (el navegador se cerró de golpe) y el
    // navegador la restaura con su id.
    await cerrar(p1);
    await cambiarBorrador(ctx, 'DUP-A', { closed: false, edadMs: 0 });
    const p3 = await abrir(ctx, id1);
    const r3 = await recuperada(p3);
    if (r3 !== 'DUP-A') falla('la pestaña restaurada no recupera su operación: se recupera ' + r3);
    console.log('OK la duplicada no toma la operación de la original viva; la restaurada recupera la suya');
    await ctx.close();
  }

  // (j) La consulta del usuario da 500 (todas: la del tour también la pide)
  // desde que abre hasta 3 segundos después de cargar la operación, así la
  // primera de la app falla seguro, y después anda.
  if (corre('j')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1j');
    let caida = true, fallidas = 0;
    await ctx.route('**/auth/current_user', ruta => {
      if (caida) { fallidas++; return ruta.fulfill({ status: 500, body: 'error de prueba' }); }
      return ruta.continue();
    });
    const p = await ctx.newPage();
    p.on('dialog', d => d.accept().catch(() => {}));
    await p.goto(base + '/dashboard');
    await p.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && document.querySelector('.screen.is-active'));
    await cargar(p, 'SIN-USUARIO-1', [prod('Producto con el usuario caído', '84714900100D', 2, 10)]);
    await p.waitForTimeout(3000);
    caida = false;
    // Esperando 1, 2, 4… segundos, en unos 3 s son la de la app, dos
    // reintentos y la del tour; un reintento sin espera serían cientos.
    if (fallidas > 8) falla('la pestaña martilla la consulta del usuario: ' + fallidas + ' pedidos en la caída');
    const llego = await p.waitForFunction(() => CDI.currentUser, null, { timeout: 40000 }).then(() => true, () => false);
    if (!llego) falla('con la consulta del usuario caída al abrir, la pestaña no la vuelve a pedir');
    await esperarBorradores(p, ['SIN-USUARIO-1'], 'con la consulta del usuario caída al abrir, la operación no se guarda');
    const dueno = await p.evaluate(() => {
      const k = Object.keys(localStorage).find(k => k.startsWith('cdi_v2_state') && (localStorage.getItem(k) || '').includes('"SIN-USUARIO-1"'));
      return JSON.parse(localStorage.getItem(k)).user;
    });
    if (dueno !== usuario) falla('la operación se guardó con otro dueño: ' + dueno);
    console.log('OK con la consulta del usuario caída al abrir, la operación se guarda con su dueño (' + fallidas + ' pedidos en la caída)');
    await ctx.close();
  }

  // (k) La consulta del usuario da 500 hasta que otro usuario entra en el
  // mismo navegador (otra pestaña); la operación ya estaba cargada.
  if (corre('k')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    await nuevoUsuario(ctx, 'ord1ka');
    let caida = true;
    await ctx.route('**/auth/current_user', ruta => (caida
      ? ruta.fulfill({ status: 500, body: 'error de prueba' }) : ruta.continue()));
    const p = await ctx.newPage();
    p.on('dialog', d => d.accept().catch(() => {}));
    await p.goto(base + '/dashboard');
    await p.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && document.querySelector('.screen.is-active'));
    await cargar(p, 'DE-A-SIN-USUARIO', [prod('Producto de A con el usuario caído', '84714900100D', 2, 10)]);
    const otro = await nuevoUsuario(ctx, 'ord1kb');
    caida = false;
    const tapada = await p.waitForFunction(() => document.getElementById('pestanaAjena').open, null, { timeout: 40000 }).then(() => true, () => false);
    await p.waitForTimeout(2 * INTERVALO_MS);
    const ajenos = (await borradores(p)).filter(x => (x.texto || '').includes('"DE-A-SIN-USUARIO"'))
      .map(x => { try { return JSON.parse(x.texto).user; } catch (_) { return '?'; } });
    if (ajenos.length) falla('la operación cargada antes de saber el usuario se guardó a nombre de quien entró después: ' + ajenos.join(', ') + ' (' + otro + ')');
    const q = await abrir(ctx);
    const r = await recuperada(q);
    if (r) falla('quien entró después recupera la operación cargada antes de saber el usuario: ' + r);
    const aviso = await p.locator('#avisoBorrador').isVisible() ? await p.locator('#avisoBorrador').textContent() : '';
    if (!/Entró otro usuario/.test(aviso)) falla('entró otro usuario mientras la pestaña reintentaba y la pestaña no avisa que no guarda: «' + aviso + '»');
    if (!tapada) falla('entró otro usuario mientras la pestaña reintentaba y la pestaña no se tapa');
    console.log('OK si otro usuario entra mientras la pestaña reintenta, la operación no queda a su nombre');
    await ctx.close();
  }

  // Lo que la pestaña guardó de una factura: [{ user, closed, savedAt }].
  const sobresDe = (p, factura) => p.evaluate(f => Object.keys(localStorage)
    .filter(k => k.startsWith('cdi_v2_state') && (localStorage.getItem(k) || '').includes('"' + f + '"'))
    .map(k => { try { const s = JSON.parse(localStorage.getItem(k)); return { user: s.user, closed: s.closed, savedAt: s.savedAt }; } catch (_) { return { user: '?' }; } }), factura);
  const avisa = p => p.locator('#avisoBorrador').isVisible();
  // Espera a que el guardado periódico acabe de pasar (cambia savedAt), así lo
  // que sigue tiene casi 2,5 s antes del próximo.
  async function trasUnGuardado(p, factura) {
    const antes = ((await sobresDe(p, factura))[0] || {}).savedAt;
    const ok = await p.waitForFunction(([f, a]) => Object.keys(localStorage).some(k => {
      const t = localStorage.getItem(k) || '';
      if (!k.startsWith('cdi_v2_state') || !t.includes('"' + f + '"')) return false;
      try { return JSON.parse(t).savedAt !== a; } catch (_) { return false; }
    }), [factura, antes], { timeout: 2 * INTERVALO_MS }).then(() => true, () => false);
    if (!ok) falla('el guardado periódico no vuelve a guardar ' + factura);
  }
  const transicion = (p, tipo) => p.evaluate(t => window.dispatchEvent(new PageTransitionEvent(t, { persisted: true })), tipo);
  // Un sobre armado a mano, del usuario y de la edad que se pida.
  const sembrar = (ctx, sobre, factura) => enElSitio(ctx, ([s, f]) => {
    s.state = { operacion: { numero_factura: f }, items: [{ descripcion: 'Producto de ' + f, cantidad: 1 }] };
    localStorage.setItem('cdi_v2_state:sembrado-' + f, JSON.stringify(s));
  }, [sobre, factura]);

  // (l) Otro usuario entra en el mismo navegador después de que la pestaña ya
  // conoce a su dueño; lo que se carga después no es del dueño.
  if (corre('l')) {
    const ctx = await nuevoContexto('ord1la');
    const t = await abrir(ctx);
    const otro = await nuevoUsuario(ctx, 'ord1lb');
    await cargar(t, 'DE-B', [prod('Producto cargado por B en la pestaña de A', '84714900100D', 2, 10)]);
    await t.waitForTimeout(2 * INTERVALO_MS);
    const sobres = await sobresDe(t, 'DE-B');
    if (sobres.length) falla('lo que cargó B en la pestaña de A se guardó a nombre de ' + sobres.map(s => s.user).join(', '));
    if (!(await avisa(t))) falla('la pestaña dejó de guardar y no lo avisa');
    const rb = await recuperada(await abrir(ctx));
    if (rb) falla('B recupera lo cargado en la pestaña de A: ' + rb);
    console.log('OK si entra otro usuario, la pestaña no guarda lo que se carga y lo avisa (' + otro + ')');
    await ctx.close();
  }

  // (m) El mismo usuario sale y vuelve a entrar: la pestaña sigue guardando.
  if (corre('m')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1m');
    const t = await abrir(ctx);
    // Sin esperar, el pedido de conectores del arranque cae entre la salida y
    // la entrada, da 401 y la pantalla se va al login (eso ya era así).
    await t.waitForLoadState('networkidle');
    const salida = await salir(ctx);
    if (!salida.ok()) falla('no se pudo salir: ' + salida.status());
    await entrar(ctx, usuario);
    await cargar(t, 'MISMO-A', [prod('Producto del mismo usuario', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['MISMO-A'], 'el mismo usuario volvió a entrar y la pestaña dejó de guardar');
    const sobres = await sobresDe(t, 'MISMO-A');
    if (sobres.some(s => s.user !== usuario)) falla('la operación se guardó con otro dueño: ' + JSON.stringify(sobres));
    if (await avisa(t)) falla('el mismo usuario volvió a entrar y la pestaña avisa que no guarda');
    console.log('OK si el mismo usuario sale y vuelve a entrar, la pestaña sigue guardando sin aviso');
    await ctx.close();
  }

  // (n) Sale uno y entra otro.
  if (corre('n')) {
    const ctx = await nuevoContexto('ord1na');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');  // como en (m)
    await salir(ctx);
    await nuevoUsuario(ctx, 'ord1nb');
    await cargar(t, 'DE-B-TRAS-SALIR', [prod('Producto cargado por B', '84714900100D', 2, 10)]);
    await t.waitForTimeout(2 * INTERVALO_MS);
    const sobres = await sobresDe(t, 'DE-B-TRAS-SALIR');
    if (sobres.length) falla('salió A, entró B y lo cargado se guardó a nombre de ' + sobres.map(s => s.user).join(', '));
    if (!(await avisa(t))) falla('salió A, entró B, la pestaña dejó de guardar y no lo avisa');
    console.log('OK si sale uno y entra otro, la pestaña no guarda y lo avisa');
    await ctx.close();
  }

  // (o) Vuelve desde la caché del navegador (pageshow con persisted). El
  // bfcache de verdad no se puede pedir en esta prueba (Playwright lo apaga y
  // el Web Lock de la pestaña lo impide), así que se mandan los eventos.
  if (corre('o')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1oa');
    const t = await abrir(ctx);
    await cargar(t, 'VUELVE', [prod('Producto de la que vuelve', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['VUELVE'], 'la operación no se guarda');
    await trasUnGuardado(t, 'VUELVE');
    await transicion(t, 'pagehide');
    if (!(await sobresDe(t, 'VUELVE')).every(s => s.closed === true)) falla('pagehide no la marca cerrada');
    await transicion(t, 'pageshow');
    await t.waitForTimeout(300);
    const vuelta = await sobresDe(t, 'VUELVE');
    if (!vuelta.length || vuelta.some(s => s.closed !== false || s.user !== usuario)) falla('al volver de la caché no queda en uso: ' + JSON.stringify(vuelta));
    // Se va a la caché, entra otro y vuelve: queda cerrada a nombre del dueño.
    await trasUnGuardado(t, 'VUELVE');
    await transicion(t, 'pagehide');
    await nuevoUsuario(ctx, 'ord1ob');
    await transicion(t, 'pageshow');
    await t.waitForTimeout(2 * INTERVALO_MS);
    const ajena = await sobresDe(t, 'VUELVE');
    if (ajena.length !== 1 || ajena[0].closed !== true || ajena[0].user !== usuario) falla('volvió de la caché con otro usuario y la marcó en uso: ' + JSON.stringify(ajena));
    if (!(await avisa(t))) falla('volvió de la caché con otro usuario y no avisa que dejó de guardar');
    console.log('OK al volver de la caché queda en uso; con otro usuario queda cerrada a nombre del dueño y avisa');
    await ctx.close();
  }

  // (p) Recargar con la consulta del usuario lenta (6 s) o caída (500 durante
  // 5 s): la operación vuelve cuando llega el usuario. Si mientras tanto se
  // cargó otra, no se pisa: la de antes queda guardada y se avisa.
  if (corre('p')) {
    const ctx = await nuevoContexto('ord1p');
    const recargarCon = async (t, factura, demora) => {
      await cargar(t, factura, [prod('Producto de ' + factura, '84714900100D', 2, 10)]);
      await esperarBorradores(t, [factura], 'la operación ' + factura + ' no se guarda');
      const hasta = Date.now() + demora.ms;
      await ctx.route('**/auth/current_user', async ruta => {
        if (Date.now() >= hasta) return ruta.continue().catch(() => {});
        if (demora.caida) return ruta.fulfill({ status: 500, body: 'error de prueba' });
        await new Promise(r => setTimeout(r, hasta - Date.now()));
        return ruta.continue().catch(() => {});
      });
      await t.reload();
      await t.waitForFunction(() => window.CDI && CDI.goTo && document.querySelector('.screen.is-active'));
    };
    for (const demora of [{ ms: 6000 }, { ms: 5000, caida: true }]) {
      const que = demora.caida ? 'con la consulta del usuario caída' : 'con la consulta del usuario lenta';
      const factura = demora.caida ? 'CAIDA-AL-RECARGAR' : 'LENTA-AL-RECARGAR';
      const t = await abrir(ctx);
      await recargarCon(t, factura, demora);
      const volvio = await t.waitForFunction(() => CDI.state && CDI.state.items && CDI.state.items.length > 0,
        null, { timeout: demora.ms + 15000 }).then(() => true, () => false);
      await ctx.unroute('**/auth/current_user');
      if (!volvio) falla(que + ', la operación no vuelve a la pestaña que recargó (pantalla ' + await pantalla(t) + ')');
      const f = await t.evaluate(() => (CDI.state.operacion || {}).numero_factura);
      if (f !== factura) falla(que + ', vuelve otra operación: ' + f);
      await t.waitForFunction(() => document.querySelector('.screen.is-active').dataset.screen === 'review', null, { timeout: 3000 }).catch(() => {});
      if (await pantalla(t) !== 'review') falla(que + ', la operación vuelve pero la pantalla queda en ' + await pantalla(t));
      await cerrar(t);
      console.log('OK ' + que + ' al recargar, la operación vuelve cuando llega el usuario');
    }
    // Mientras espera al usuario, se carga otra: no se pisa.
    const t = await abrir(ctx);
    await recargarCon(t, 'ANTES-DE-RECARGAR', { ms: 6000 });
    await cargar(t, 'CARGADA-MIENTRAS', [prod('Producto cargado mientras', '84714900100D', 2, 10)]);
    await t.waitForFunction(() => CDI.currentUser, null, { timeout: 20000 });
    await ctx.unroute('**/auth/current_user');
    await t.waitForTimeout(INTERVALO_MS + 500);
    const f = await t.evaluate(() => (CDI.state.operacion || {}).numero_factura);
    if (f !== 'CARGADA-MIENTRAS') falla('la operación de antes de recargar pisó la que se cargó mientras: ' + f);
    const hay = await guardadas(ctx);
    if (!hay.includes('ANTES-DE-RECARGAR')) falla('la operación de antes de recargar se perdió: ' + JSON.stringify(hay));
    if (!(await avisa(t))) falla('la operación de antes de recargar quedó guardada y la pestaña no lo avisa');
    console.log('OK si mientras espera al usuario se carga otra, la de antes queda guardada y se avisa');
    await ctx.close();
  }

  // (q) El navegador no tiene lugar para el borrador: se avisa.
  if (corre('q')) {
    const ctx = await nuevoContexto('ord1q');
    await ctx.addInitScript(() => {
      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = function (k, v) {
        if (String(k).startsWith('cdi_v2_state')) throw new DOMException('lleno', 'QuotaExceededError');
        return original.call(this, k, v);
      };
    });
    const t = await abrir(ctx);
    await cargar(t, 'SIN-LUGAR', [prod('Producto sin lugar', '84714900100D', 2, 10)]);
    const ok = await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 2 * INTERVALO_MS }).then(() => true, () => false);
    if (!ok) falla('el navegador no tiene lugar para guardar la operación y la pestaña no avisa');
    console.log('OK sin lugar en el navegador, la pestaña avisa que no guarda');
    await ctx.close();
  }

  // (r) Con la sesión vencida (401) la consulta del usuario no se reintenta:
  // la app ya manda al login. Se corta esa navegación para contar.
  if (corre('r')) {
    const ctx = await nuevoContexto('ord1r');
    let pedidos = 0;
    await ctx.route('**/auth/current_user', ruta => { pedidos++; return ruta.fulfill({ status: 401, body: '{}' }); });
    // Un 204 cancela la ida al login y deja viva la página: si se aborta,
    // Chromium la descarga igual y el reintento muere con ella.
    await ctx.route(u => u.pathname === '/' && u.searchParams.has('next'), ruta => ruta.fulfill({ status: 204, body: '' }));
    const p = await ctx.newPage();
    p.on('dialog', d => d.accept().catch(() => {}));
    await p.goto(base + '/dashboard');
    await p.waitForTimeout(8000);
    // La de la app y la del tour; un reintento con 401 haría 4 o más.
    if (pedidos > 3) falla('con la sesión vencida la pestaña reintenta la consulta del usuario: ' + pedidos + ' pedidos en 8 s');
    console.log('OK con la sesión vencida no se reintenta (' + pedidos + ' pedidos)');
    await ctx.close();
  }

  // (s) Como (j), pero la consulta se corta (error de red) en vez de dar 500.
  if (corre('s')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1s');
    let caida = true;
    await ctx.route('**/auth/current_user', ruta => (caida ? ruta.abort() : ruta.continue()));
    const p = await ctx.newPage();
    p.on('dialog', d => d.accept().catch(() => {}));
    await p.goto(base + '/dashboard');
    await p.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && document.querySelector('.screen.is-active'));
    await cargar(p, 'SIN-RED', [prod('Producto con la red cortada', '84714900100D', 2, 10)]);
    await p.waitForTimeout(3000);
    caida = false;
    const llego = await p.waitForFunction(() => CDI.currentUser, null, { timeout: 40000 }).then(() => true, () => false);
    if (!llego) falla('con la consulta del usuario cortada al abrir, la pestaña no la vuelve a pedir');
    await esperarBorradores(p, ['SIN-RED'], 'con la consulta del usuario cortada al abrir, la operación no se guarda');
    const sobres = await sobresDe(p, 'SIN-RED');
    if (sobres.some(s => s.user !== usuario)) falla('la operación se guardó con otro dueño: ' + JSON.stringify(sobres));
    console.log('OK con la consulta del usuario cortada al abrir, la pestaña la vuelve a pedir');
    await ctx.close();
  }

  // (t) Los reintentos esperan 1, 2, 4… segundos, hasta 30: en 200 segundos
  // de reloj son 1 + 10. Con el reloj de la página adelantado a mano.
  if (corre('t')) {
    const ctx = await nuevoContexto('ord1t');
    let pedidos = 0;
    await ctx.route('**/auth/current_user', ruta => { pedidos++; return ruta.abort(); });
    const p = await ctx.newPage();
    await p.clock.install();
    p.on('dialog', d => d.accept().catch(() => {}));
    await p.goto(base + '/dashboard');
    await p.waitForFunction(() => window.CDI && CDI.goTo && document.querySelector('.screen.is-active'));
    for (let s = 0; s < 200; s++) {
      await p.clock.runFor(1000);
      await p.waitForTimeout(20);
    }
    // Con el tour son 12; sin tope de 30 s, 9; sin crecer, cientos.
    if (pedidos < 11 || pedidos > 13) falla('en 200 s de reloj la consulta del usuario se pidió ' + pedidos + ' veces; se esperan 12 (1 + 10 reintentos + el tour)');
    console.log('OK los reintentos crecen hasta 30 s (' + pedidos + ' pedidos en 200 s)');
    await ctx.close();
  }

  // (u) Al recargar, la pestaña toma su propio borrador aunque haya otro
  // cerrado más nuevo: espera a que se libere el lock de la pestaña anterior.
  if (corre('u')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1u');
    const t = await abrir(ctx);
    await cargar(t, 'PROPIA', [prod('Producto de la que recarga', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['PROPIA'], 'la operación no se guarda');
    await sembrar(ctx, { v: 1, user: usuario, savedAt: Date.now() + MIN, closed: true }, 'OTRA-MAS-NUEVA');
    await t.reload();
    const r = await recuperada(t);
    if (r !== 'PROPIA') falla('al recargar, la pestaña no toma su propio borrador: toma ' + r);
    console.log('OK al recargar, la pestaña toma el suyo y no el cerrado más nuevo');
    await ctx.close();
  }

  // (v) Una operación terminada (la pestaña volvió a la carga) se borra: al
  // cerrar antes del próximo guardado y con la pestaña abierta.
  if (corre('v')) {
    const ctx = await nuevoContexto('ord1v');
    const t1 = await abrir(ctx);
    await cargar(t1, 'TERMINADA-1', [prod('Producto terminado', '84714900100D', 2, 10)]);
    await esperarBorradores(t1, ['TERMINADA-1'], 'la operación no se guarda');
    await trasUnGuardado(t1, 'TERMINADA-1');
    await t1.evaluate(() => CDI.goTo('upload'));
    await cerrar(t1);
    if ((await guardadas(ctx)).includes('TERMINADA-1')) falla('la operación terminada queda guardada al cerrar la pestaña');
    const t2 = await abrir(ctx);
    await cargar(t2, 'TERMINADA-2', [prod('Producto terminado', '84714900100D', 2, 10)]);
    await esperarBorradores(t2, ['TERMINADA-2'], 'la operación no se guarda');
    await t2.evaluate(() => CDI.goTo('upload'));
    await t2.waitForTimeout(2 * INTERVALO_MS);
    if ((await guardadas(ctx)).includes('TERMINADA-2')) falla('la operación terminada queda guardada con la pestaña abierta');
    console.log('OK una operación terminada se borra, al cerrar y con la pestaña abierta');
    await ctx.close();
  }

  // (w) El borrador vencido de otro usuario se barre igual. (x) Un sobre de
  // otra versión no se recupera y se borra.
  if (corre('w')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1w');
    await sembrar(ctx, { v: 1, user: 'otro_usuario_inventado', savedAt: Date.now() - 8 * DIA, closed: true }, 'VENCIDA-DE-OTRO');
    await sembrar(ctx, { v: 2, user: usuario, savedAt: Date.now(), closed: true }, 'OTRA-VERSION');
    const t = await abrir(ctx);
    const r = await recuperada(t);
    if (r) falla('se recupera un sobre de otra versión: ' + r);
    const hay = await guardadas(ctx);
    if (hay.includes('VENCIDA-DE-OTRO')) falla('el borrador vencido de otro usuario no se borra al barrer');
    if (hay.includes('OTRA-VERSION')) falla('el sobre de otra versión no se borra al barrer');
    console.log('OK el vencido de otro usuario y el sobre de otra versión se borran');
    await ctx.close();
  }

  // (y) Entra otro usuario y en la pestaña del dueño se vuelve a la carga de
  // archivos: la operación que el dueño dejó guardada no se borra.
  if (corre('y')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1ya');
    const t = await abrir(ctx);
    await cargar(t, 'DEL-DUENO', [prod('Producto del dueño', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['DEL-DUENO'], 'la operación del dueño no se guarda');
    await nuevoUsuario(ctx, 'ord1yb');
    await t.evaluate(() => CDI.goTo('upload'));
    await t.waitForTimeout(2 * INTERVALO_MS);
    const quedan = await sobresDe(t, 'DEL-DUENO');
    if (quedan.length !== 1 || quedan[0].user !== usuario) falla('entró otro usuario y la pestaña del dueño borró su operación: ' + JSON.stringify(quedan));
    console.log('OK con otro usuario adentro, la pestaña del dueño no borra lo que él dejó guardado');
    await ctx.close();
  }

  // (m2) Se cierra la sesión: la pestaña avisa que no guarda. El mismo
  // usuario vuelve a entrar: deja de avisar y sigue guardando.
  if (corre('m2')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1m2');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');  // como en (m)
    await cargar(t, 'ANTES-DE-SALIR', [prod('Producto antes de salir', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['ANTES-DE-SALIR'], 'la operación no se guarda');
    await ctx.clearCookies();
    const aviso = await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 2 * INTERVALO_MS }).then(() => true, () => false);
    if (!aviso) falla('se cerró la sesión y la pestaña no avisa que no guarda');
    await entrar(ctx, usuario);
    await cargar(t, 'TRAS-VOLVER', [prod('Producto tras volver a entrar', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['TRAS-VOLVER'], 'el mismo usuario volvió a entrar y la pestaña no guarda');
    if (await avisa(t)) falla('el mismo usuario volvió a entrar y la pestaña sigue avisando que no guarda');
    console.log('OK se cierra la sesión: avisa; vuelve a entrar el mismo: deja de avisar y guarda');
    await ctx.close();
  }

  // (z) a (z2) Al recargar, el usuario llega tarde (10 s) y la pestaña ya
  // empezó otra cosa: la operación de antes no la pisa y queda guardada.
  const recargarLento = async (ctx, t, factura) => {
    await cargar(t, factura, [prod('Producto de ' + factura, '84714900100D', 2, 10)]);
    await esperarBorradores(t, [factura], 'la operación ' + factura + ' no se guarda');
    const hasta = Date.now() + 10000;
    await t.route('**/auth/current_user', async ruta => {
      await new Promise(r => setTimeout(r, Math.max(0, hasta - Date.now())));
      return ruta.continue().catch(() => {});
    });
    await t.reload();
    // Sin usuario, la pantalla aparece recién al vencer la espera del arranque.
    await t.waitForFunction(() => window.CDI && CDI.goTo && document.querySelector('.screen.is-active'));
    if (await t.evaluate(() => !!CDI.currentUser)) falla('el usuario llegó antes de lo que demora la prueba');
  };
  // (z) Se fue a otra pantalla con una operación sin productos.
  if (corre('z')) {
    const ctx = await nuevoContexto('ord1z');
    const t = await abrir(ctx);
    await recargarLento(ctx, t, 'ANTES-DE-RECARGAR');
    await t.evaluate(() => { CDI.state = { operacion: { numero_factura: 'PROPIA-SIN-PRODUCTOS' } }; CDI.goTo('cockpit'); });
    await t.waitForFunction(() => CDI.currentUser, null, { timeout: 20000 });
    await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});
    if (await pantalla(t) !== 'cockpit') falla('el usuario llegó tarde y la pestaña se fue de la pantalla en que estaba a ' + await pantalla(t));
    const f = await t.evaluate(() => (CDI.state.operacion || {}).numero_factura);
    if (f !== 'PROPIA-SIN-PRODUCTOS') falla('el usuario llegó tarde y la operación de antes pisó la que se estaba armando: ' + f);
    if (!(await guardadas(ctx)).includes('ANTES-DE-RECARGAR')) falla('la operación de antes de recargar se perdió');
    if (!/Quedó guardada la operación/.test(await t.locator('#avisoBorrador').textContent())) falla('la operación de antes de recargar quedó guardada y la pestaña no lo avisa');
    console.log('OK si el usuario llega tarde y la pestaña está en otra pantalla, no la pisa y avisa');
    await ctx.close();
  }
  // (z2) Hay una subida en curso cuando llega el usuario.
  if (corre('z2')) {
    const ctx = await nuevoContexto('ord1z2');
    const t = await abrir(ctx);
    let soltar, pedida;
    const suelta = new Promise(r => { soltar = r; });
    const llego = new Promise(r => { pedida = r; });
    await t.route('**/upload_pdf/public', async ruta => {
      pedida();
      await suelta;
      return ruta.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        filename: 'demo.pdf', operacion: Object.assign({ numero_factura: 'DEL-PDF' }, OPERACION),
        items: [prod('Producto del PDF', '84714900100D', 2, 10)] }) }).catch(() => {});
    });
    await recargarLento(ctx, t, 'ANTES-DE-SUBIR');
    if (await pantalla(t) !== 'upload') falla('sin usuario, la pestaña no queda en la carga de archivos: ' + await pantalla(t));
    await t.setInputFiles('#uploadFileInput', { name: 'demo.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4\n%demo\n') });
    await Promise.race([llego, new Promise((_, no) => setTimeout(() => no(new Error('la subida no llegó al servidor')), 5000))]);
    await t.waitForFunction(() => CDI.currentUser, null, { timeout: 20000 });
    await t.waitForTimeout(500);
    soltar();
    await t.waitForFunction(() => ((CDI.state || {}).operacion || {}).numero_factura === 'DEL-PDF', null, { timeout: 10000 })
      .catch(async () => falla('la subida no termina: queda ' + await t.evaluate(() => ((CDI.state || {}).operacion || {}).numero_factura)));
    await esperarBorradores(t, ['DEL-PDF'], 'la operación del PDF no se guarda');
    await t.waitForTimeout(INTERVALO_MS);
    if (!(await guardadas(ctx)).includes('ANTES-DE-SUBIR')) falla('el usuario llegó con una subida en curso y la operación de antes de recargar se perdió: ' + JSON.stringify(await guardadas(ctx)));
    const aviso = await avisa(t) ? await t.locator('#avisoBorrador').textContent() : '';
    if (!/Quedó guardada la operación/.test(aviso)) falla('el usuario llegó con una subida en curso y la pestaña no avisa que quedó guardada la de antes: «' + aviso + '»');
    console.log('OK si el usuario llega tarde con una subida en curso, la de antes queda guardada y se avisa (' + JSON.stringify(await guardadas(ctx)) + ')');
    await ctx.close();
  }

  // (z3) Al recargar, el navegador no tiene lugar para tomar el borrador: avisa
  // y el borrador queda.
  if (corre('z3')) {
    const ctx = await nuevoContexto('ord1z3');
    const t = await abrir(ctx);
    await cargar(t, 'SIN-LUGAR-AL-RECARGAR', [prod('Producto sin lugar al recargar', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['SIN-LUGAR-AL-RECARGAR'], 'la operación no se guarda');
    await t.addInitScript(() => {
      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = function (k, v) {
        if (String(k).startsWith('cdi_v2_state')) throw new DOMException('lleno', 'QuotaExceededError');
        return original.call(this, k, v);
      };
    });
    await t.reload();
    await t.waitForFunction(() => window.CDI && CDI.currentUser && document.querySelector('.screen.is-active'));
    const ok = await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 5000 }).then(() => true, () => false);
    if (!ok) falla('al recargar sin lugar en el navegador la operación no vuelve y la pestaña no avisa');
    const texto = await t.locator('#avisoBorrador').textContent();
    if (!/no tiene lugar/.test(texto)) falla('al recargar sin lugar en el navegador avisa otra cosa: ' + texto);
    if (!(await guardadas(ctx)).includes('SIN-LUGAR-AL-RECARGAR')) falla('al recargar sin lugar en el navegador el borrador se borró');
    console.log('OK al recargar sin lugar en el navegador, avisa y el borrador queda');
    await ctx.close();
  }

  // (z4) Cambia la sesión y la consulta del usuario no contesta nunca: la
  // pestaña no se queda callada.
  if (corre('z4')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1z4');
    const t = await abrir(ctx);
    await cargar(t, 'SIN-RESPUESTA', [prod('Producto sin respuesta', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['SIN-RESPUESTA'], 'la operación no se guarda');
    await ctx.route('**/auth/current_user', () => {});  // no contesta nunca
    await entrar(ctx, usuario);
    const ok = await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 20000 }).then(() => true, () => false);
    if (!ok) falla('cambió la sesión, la consulta del usuario no contesta y en 20 s la pestaña no avisa que no guarda');
    const texto = await t.locator('#avisoBorrador').textContent();
    if (!/No se pudo comprobar la sesión/.test(texto)) falla('la consulta del usuario no contesta y la pestaña avisa otra cosa: ' + texto);
    console.log('OK si la consulta del usuario no contesta, la pestaña avisa');
    await ctx.close();
  }

  // (z5) Mientras espera al usuario se carga otra y se vuelve a la carga de
  // archivos (como «Subir una factura» de Clientes): la pantalla es la de
  // carga, pero la pestaña no está vacía y no se pisa.
  if (corre('z5')) {
    const ctx = await nuevoContexto('ord1z5');
    const t = await abrir(ctx);
    await recargarLento(ctx, t, 'ANTES-DE-RECARGAR');
    await cargar(t, 'CARGADA-Y-EN-LA-CARGA', [prod('Producto cargado mientras', '84714900100D', 2, 10)]);
    await t.evaluate(() => CDI.goTo('upload'));
    await t.waitForFunction(() => CDI.currentUser, null, { timeout: 20000 });
    await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});
    const f = await t.evaluate(() => (CDI.state.operacion || {}).numero_factura);
    if (f !== 'CARGADA-Y-EN-LA-CARGA') falla('el usuario llegó tarde a la carga de archivos y la operación de antes pisó la cargada: ' + f);
    if (!(await guardadas(ctx)).includes('ANTES-DE-RECARGAR')) falla('la operación de antes de recargar se perdió');
    if (!/Quedó guardada la operación/.test(await t.locator('#avisoBorrador').textContent())) falla('la operación de antes de recargar quedó guardada y la pestaña no lo avisa');
    console.log('OK si el usuario llega tarde y la carga de archivos tiene una operación, no la pisa y avisa');
    await ctx.close();
  }

  // (z6) Mientras espera al usuario se abre el diálogo de archivos y se elige
  // uno después de que llegó: la operación de antes de recargar no se pierde.
  if (corre('z6')) {
    const ctx = await nuevoContexto('ord1z6');
    const t = await abrir(ctx);
    await t.route('**/upload_pdf/public', ruta => ruta.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ filename: 'demo.pdf', operacion: Object.assign({ numero_factura: 'DEL-PDF' }, OPERACION),
        items: [prod('Producto del PDF', '84714900100D', 2, 10)] }) }).catch(() => {}));
    await recargarLento(ctx, t, 'ANTES-DE-ELEGIR');
    const [dialogo] = await Promise.all([t.waitForEvent('filechooser', { timeout: 5000 }), t.locator('#uploadDropzone').click()]);
    await t.waitForFunction(() => CDI.currentUser, null, { timeout: 20000 });
    await t.waitForTimeout(500);
    await dialogo.setFiles({ name: 'demo.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4\n%demo\n') });
    await t.waitForFunction(() => ((CDI.state || {}).operacion || {}).numero_factura === 'DEL-PDF', null, { timeout: 10000 })
      .catch(async () => falla('la subida no termina: queda ' + await t.evaluate(() => ((CDI.state || {}).operacion || {}).numero_factura)));
    await esperarBorradores(t, ['DEL-PDF'], 'la operación del PDF no se guarda');
    if (!(await guardadas(ctx)).includes('ANTES-DE-ELEGIR')) falla('se abrió el diálogo de archivos antes de que llegara el usuario y la operación de antes de recargar se perdió: ' + JSON.stringify(await guardadas(ctx)));
    const aviso = await avisa(t) ? await t.locator('#avisoBorrador').textContent() : '';
    if (!/Quedó guardada la operación/.test(aviso)) falla('se abrió el diálogo de archivos antes de que llegara el usuario y la pestaña no avisa que quedó guardada la de antes: «' + aviso + '»');
    console.log('OK si se abre el diálogo de archivos antes de que llegue el usuario, la de antes queda guardada y se avisa');
    await ctx.close();
  }

  // (z7) Al recargar, la consulta del usuario da error o no contesta: la
  // pestaña avisa que no guarda y, cuando la consulta vuelve, recupera.
  if (corre('z7')) {
    const ctx = await nuevoContexto('ord1z7');
    for (const caida of [true, false]) {
      const que = caida ? 'la consulta del usuario da error' : 'la consulta del usuario no contesta';
      const factura = caida ? 'CON-ERROR' : 'SIN-RESPUESTA';
      const t = await abrir(ctx);
      await cargar(t, factura, [prod('Producto de ' + factura, '84714900100D', 2, 10)]);
      await esperarBorradores(t, [factura], 'la operación ' + factura + ' no se guarda');
      // Las consultas que salen antes de que vuelva quedan colgadas hasta
      // después de mirar si la pestaña se enteró; las de después contestan.
      let soltar, vuelve = false;
      const suelta = new Promise(r => { soltar = r; });
      await t.route('**/auth/current_user', async ruta => {
        if (vuelve) return ruta.continue().catch(() => {});
        if (caida) return ruta.fulfill({ status: 500, body: 'error de prueba' });
        await suelta;
        return ruta.continue().catch(() => {});
      });
      await t.reload();
      await t.waitForFunction(() => window.CDI && CDI.goTo && document.querySelector('.screen.is-active'));
      const avisó = await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 8000 }).then(() => true, () => false);
      if (!avisó) falla('al recargar ' + que + ' y en 8 s la pestaña no avisa que no guarda');
      const texto = await t.locator('#avisoBorrador').textContent();
      if (!/no guarda/.test(texto)) falla('al recargar ' + que + ' y la pestaña avisa otra cosa: ' + texto);
      vuelve = true;
      const llegó = await t.waitForFunction(() => CDI.currentUser, null, { timeout: 30000 }).then(() => true, () => false);
      soltar();
      await t.unroute('**/auth/current_user');
      if (!llegó) falla('al recargar ' + que + ' y cuando vuelve a contestar la pestaña no se entera en 30 s');
      const volvió = await t.waitForFunction(f => ((CDI.state || {}).operacion || {}).numero_factura === f, factura, { timeout: 5000 }).then(() => true, () => false);
      if (!volvió) falla('al recargar ' + que + ', cuando vuelve a contestar la operación no vuelve');
      if (await avisa(t)) falla('al recargar ' + que + ', cuando vuelve a contestar sigue el aviso: ' + await t.locator('#avisoBorrador').textContent());
      await cerrar(t);
      console.log('OK al recargar si ' + que + ', la pestaña avisa y después recupera');
    }
    await ctx.close();
  }

  // (z8) Entra otro usuario mientras la primera consulta del usuario está en
  // camino y la consulta sale con la sesión nueva (las cookies se leen al
  // salir, no al pedirla): lo cargado no se guarda a nombre del que entró.
  if (corre('z8')) {
    const ctx = await nuevoContexto('ord1z8');
    // Se retienen todas las consultas del usuario que salgan antes de soltar:
    // la pestaña hace más de una al abrir.
    let soltar, pedida;
    const suelta = new Promise(r => { soltar = r; });
    const llego = new Promise(r => { pedida = r; });
    const t = await ctx.newPage();
    t.on('dialog', d => d.accept().catch(() => {}));
    await t.route('**/auth/current_user', async ruta => {
      pedida();
      await suelta;
      const cookie = (await ctx.cookies()).map(c => c.name + '=' + c.value).join('; ');
      const resp = await ruta.fetch({ headers: Object.assign({}, ruta.request().headers(), { cookie }) });
      return ruta.fulfill({ response: resp }).catch(() => {});
    });
    await t.goto(base + '/dashboard');
    await llego;
    await t.waitForFunction(() => window.CDI && CDI.goTo && document.querySelector('.screen.is-active'));
    await cargar(t, 'DE-A', [prod('Producto de A', '84714900100D', 2, 10)]);
    const otro = await nuevoUsuario(ctx, 'ord1z8b');
    soltar();
    const tapada = await t.waitForFunction(() => document.getElementById('pestanaAjena').open, null, { timeout: 10000 }).then(() => true, () => false);
    // Hasta que avise o guarde a nombre del otro: guardar puede llevar un
    // guardado periódico más la consulta de la sesión nueva.
    for (const hasta = Date.now() + 4 * INTERVALO_MS; Date.now() < hasta;) {
      if (/Entró otro usuario/.test(await t.locator('#avisoBorrador').textContent())
        || (await sobresDe(t, 'DE-A')).some(s => s.user === otro)) break;
      await t.waitForTimeout(200);
    }
    const sobres = await sobresDe(t, 'DE-A');
    if (sobres.some(s => s.user === otro)) falla('entró otro usuario con la primera consulta del usuario en camino y lo cargado se guardó a nombre de él: ' + JSON.stringify(sobres));
    const aviso = await avisa(t) ? await t.locator('#avisoBorrador').textContent() : '';
    if (!/Entró otro usuario/.test(aviso)) falla('entró otro usuario con la primera consulta del usuario en camino y la pestaña no avisa: «' + aviso + '»');
    if (!tapada) falla('entró otro usuario con la primera consulta del usuario en camino y la pestaña no se tapa');
    console.log('OK si entra otro usuario con la primera consulta en camino, no guarda a su nombre y avisa');
    await cerrarConRutas(ctx, t);
  }

  // Lo guardado en el navegador, mirado desde una página que no corre la app.
  const sobresEn = (ctx, factura) => enElSitio(ctx, f => Object.keys(localStorage)
    .filter(k => k.startsWith('cdi_v2_state') && (localStorage.getItem(k) || '').includes('"' + f + '"'))
    .map(k => { try { return JSON.parse(localStorage.getItem(k)).user; } catch (_) { return '?'; } }), factura);
  const sinDueno = ctx => enElSitio(ctx, () => Object.keys(localStorage).filter(k => k.startsWith('cdi_v2_state'))
    .filter(k => { try { const u = JSON.parse(localStorage.getItem(k)).user; return typeof u !== 'string' || !u; } catch (_) { return true; } }));

  // (z9) a (z12) La duplicada de una pestaña abierta (con OP-P1) espera a ver
  // si la original sigue viva y, mientras, cambia la sesión. Después busca
  // otra operación y encuentra OP-DE-A, que A dejó cerrada: no la adopta con
  // otro usuario, no la borra y no deja nada guardado sin dueño.
  // `alSeguir(p2)`, si está, corre antes de que la duplicada siga y devuelve
  // lo que corre apenas sigue.
  async function cambiaEnLaEspera(nombre, lenta, cambiar, alSeguir) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, nombre);
    // Primero la abierta: si OP-DE-A ya estuviera cerrada, la tomaría ella.
    const p1 = await abrir(ctx);
    await cargar(p1, 'OP-P1', [prod('Producto de la pestaña abierta', '84714900100D', 2, 10)]);
    await esperarBorradores(p1, ['OP-P1'], 'la operación de la pestaña abierta no se guarda');
    await dejarAMedias(ctx, 'OP-DE-A');
    if (JSON.stringify(await sobresEn(ctx, 'OP-DE-A')) !== JSON.stringify([usuario])) falla('OP-DE-A no quedó guardada a nombre de A antes de duplicar');
    const id1 = await p1.evaluate(() => sessionStorage.getItem('cdi_v2_tab'));
    const { p: p2, conectores } = await duplicar(ctx, id1, lenta);
    const mira = await p2.waitForFunction(() => window.__esperando, null, { timeout: 20000 }).then(() => true, () => false);
    if (!mira) falla('la pestaña duplicada no llega a mirar si la original sigue viva');
    const retiene = await p2.evaluate(async () => (await navigator.locks.query()).held
      .some(l => l.name === 'cdi_v2_tab:' + sessionStorage.getItem('cdi_v2_tab')));
    if (!retiene) falla('la pestaña duplicada no retiene el lock de su propio id');
    // Si la sesión cambia antes, ese pedido con 401 la manda a entrar antes
    // de terminar de mirar y el caso no prueba nada.
    if (!(await conectores)) falla('la pestaña duplicada no pide los conectores del tablero en 20 s');
    await cambiar(ctx, usuario);
    const siguio = alSeguir ? await alSeguir(p2) : null;
    await p2.evaluate(() => window.__seguir());
    if (siguio) await siguio();
    // Sin sesión, un pedido de la app con 401 la manda a entrar: se va del
    // tablero y no hay nada que recuperar.
    let enTablero = null;
    for (const hasta = Date.now() + 30000; enTablero === null && Date.now() < hasta;) {
      enTablero = await p2.evaluate(() => !location.pathname.startsWith('/dashboard') ? false
        : (window.CDI && document.querySelector('.screen.is-active') ? true : null)).catch(() => null);
      if (enTablero === null) await p2.waitForTimeout(200);
    }
    if (enTablero === null) falla('la pestaña duplicada no muestra ninguna pantalla en 30 s');
    return { ctx, usuario, p2, r: enTablero ? await recuperada(p2).catch(() => null) : null };
  }
  async function nadaSePerdio(ctx, usuario, que) {
    const duenos = await sobresEn(ctx, 'OP-DE-A');
    if (!duenos.length || duenos.some(u => u !== usuario)) falla(que + ' y la operación que A dejó guardada quedó con otro dueño o se borró: ' + JSON.stringify(duenos));
    const sin = await sinDueno(ctx);
    if (sin.length) falla(que + ' y quedó guardado un sobre sin dueño: ' + sin.join(', '));
  }
  const entraOtro = (nombre, lenta, que) => async () => {
    let otro;
    const { ctx, usuario, r } = await cambiaEnLaEspera(nombre, lenta, async ctx => { otro = await nuevoUsuario(ctx, nombre + 'b'); });
    if (r) falla(que + ' y la pestaña le muestra a ' + otro + ' la operación de A: ' + r);
    await nadaSePerdio(ctx, usuario, que);
    console.log('OK ' + que + ': no adopta la operación de A ni la deja sin dueño');
    await ctx.close();
  };
  if (corre('z9')) await entraOtro('ord1z9', false, 'entró otro usuario mientras la duplicada miraba si la original vive, al abrir')();
  if (corre('z10')) await entraOtro('ord1z10', true, 'entró otro usuario mientras la duplicada miraba si la original vive, con el usuario tarde')();
  if (corre('z11')) {
    const que = 'se cerró la sesión mientras la duplicada miraba si la original vive';
    const { ctx, usuario } = await cambiaEnLaEspera('ord1z11', false, ctx => ctx.clearCookies());
    await nadaSePerdio(ctx, usuario, que);
    console.log('OK ' + que + ': la operación de A queda guardada con su dueño');
    await ctx.close();
  }
  // (z12) D11 de ORDEN-1b: la duplicada no puede adoptar hasta confirmar la
  // sesión nueva; mientras, lo avisa, y al confirmarla la recupera.
  if (corre('z12')) {
    const que = 'A volvió a entrar (otra sesión) mientras la duplicada miraba si la original vive';
    let aviso = null;
    const { ctx, usuario, p2, r } = await cambiaEnLaEspera('ord1z12', false, (ctx, usuario) => entrar(ctx, usuario), async p2 => {
      const soltar = await retenerUsuario(p2);
      return async () => {
        aviso = await p2.waitForFunction(() => /Comprobando la sesión/.test(document.getElementById('avisoBorrador').textContent), null, { timeout: 15000 })
          .then(() => true, () => false);
        soltar();
      };
    });
    if (!aviso) falla(que + ' y la duplicada no avisa que está comprobando la sesión');
    if (r !== 'OP-DE-A') falla(que + ' y la duplicada no recupera la operación al confirmar la sesión: recupera ' + r);
    if (/Comprobando/.test(await p2.locator('#avisoBorrador').textContent())) falla(que + ' y, ya recuperada, sigue diciendo que comprueba la sesión');
    await esperarBorradores(p2, ['OP-DE-A'], que + ' y la duplicada no guarda la operación que tomó');
    await nadaSePerdio(ctx, usuario, que);
    console.log('OK ' + que + ': avisa que comprueba la sesión y, al confirmarla, recupera la operación');
    await ctx.close();
  }

  // (z13) a (z16) Mientras espera al usuario, la pestaña se toca de cualquier
  // forma: la recuperación tardía no la cambia y avisa que quedó guardada.
  const tocadaAntesDelUsuario = (nombre, como, tocar) => async () => {
    const ctx = await nuevoContexto(nombre);
    const t = await abrir(ctx);
    await recargarLento(ctx, t, 'ANTES-DE-TOCAR');
    await tocar(t);
    await t.waitForFunction(() => CDI.currentUser, null, { timeout: 20000 });
    await t.locator('#avisoBorrador').waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});
    if (await pantalla(t) !== 'upload') falla('se tocó la pestaña (' + como + ') antes de que llegara el usuario y la recuperación tardía la cambió a ' + await pantalla(t));
    if (!(await guardadas(ctx)).includes('ANTES-DE-TOCAR')) falla('se tocó la pestaña (' + como + ') y la operación de antes de recargar se perdió');
    const aviso = await avisa(t) ? await t.locator('#avisoBorrador').textContent() : '';
    if (!/Quedó guardada la operación/.test(aviso)) falla('se tocó la pestaña (' + como + ') y no avisa que quedó guardada la de antes: «' + aviso + '»');
    console.log('OK si se toca la pestaña (' + como + ') antes de que llegue el usuario, no la cambia y avisa');
    await ctx.close();
  };
  if (corre('z13')) await tocadaAntesDelUsuario('ord1z13', 'un clic sin puntero', t =>
    t.evaluate(() => document.getElementById('uploadDropzone').click()))();
  if (corre('z14')) await tocadaAntesDelUsuario('ord1z14', 'una tecla', t => t.keyboard.press('Tab'))();
  if (corre('z15')) await tocadaAntesDelUsuario('ord1z15', 'soltar un archivo que no es factura', t => t.evaluate(() => {
    const dt = new DataTransfer();
    dt.items.add(new File(['no es una factura'], 'notas.txt', { type: 'text/plain' }));
    document.getElementById('uploadDropzone').dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: dt }));
  }))();
  if (corre('z16')) await tocadaAntesDelUsuario('ord1z16', 'apretar el mouse sin soltar', async t => {
    const caja = await t.locator('#uploadDropzone').boundingBox();
    await t.mouse.move(caja.x + caja.width / 2, caja.y + caja.height / 2);
    await t.mouse.down();
  })();

  // (z17) Se cierra la sesión: la pestaña pregunta quién es una vez, no en
  // cada guardado.
  if (corre('z17')) {
    const ctx = await nuevoContexto('ord1z17');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');  // como en (m)
    await cargar(t, 'SESION-CERRADA', [prod('Producto con la sesión cerrada', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['SESION-CERRADA'], 'la operación no se guarda');
    let consultas = 0;
    t.on('request', r => { if (r.url().endsWith('/auth/current_user')) consultas++; });
    await ctx.clearCookies();
    await t.waitForTimeout(4 * INTERVALO_MS);
    if (consultas > 2) falla('con la sesión cerrada la pestaña pregunta quién es en cada guardado: ' + consultas + ' consultas en 10 s');
    if (!(await avisa(t))) falla('se cerró la sesión y la pestaña no avisa que no guarda');
    console.log('OK con la sesión cerrada la pestaña pregunta una vez (' + consultas + ' consultas en 10 s)');
    await ctx.close();
  }

  // (z18) Cambia la sesión con la red cortada: pregunta una vez cada 10 s y,
  // cuando la red vuelve, confirma la sesión, guarda y saca el aviso.
  if (corre('z18')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const usuario = await nuevoUsuario(ctx, 'ord1z18');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');  // como en (m)
    await cargar(t, 'RED-CORTADA', [prod('Producto con la red cortada', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['RED-CORTADA'], 'la operación no se guarda');
    let consultas = 0;
    await t.route('**/auth/current_user', ruta => { consultas++; return ruta.abort(); });
    await entrar(ctx, usuario);  // otra sesión del mismo: la pestaña pregunta quién es
    await t.waitForTimeout(9000);
    if (consultas > 2) falla('con la red cortada la pestaña pregunta quién es en cada guardado: ' + consultas + ' consultas en 9 s');
    const aviso = await avisa(t) ? await t.locator('#avisoBorrador').textContent() : '';
    if (!/No se pudo comprobar la sesión/.test(aviso)) falla('con la red cortada la pestaña no avisa que no guarda: «' + aviso + '»');
    const antes = (await sobresDe(t, 'RED-CORTADA'))[0].savedAt;
    await t.unroute('**/auth/current_user');
    const guarda = await t.waitForFunction(([a]) => Object.keys(localStorage).some(k => {
      const s = localStorage.getItem(k) || '';
      return k.startsWith('cdi_v2_state') && s.includes('"RED-CORTADA"') && JSON.parse(s).savedAt !== a;
    }), [antes], { timeout: 15000 }).then(() => true, () => false);
    if (!guarda) falla('la red volvió y en 15 s la pestaña no vuelve a guardar');
    if (await avisa(t)) falla('la red volvió, la pestaña guarda y sigue el aviso: ' + await t.locator('#avisoBorrador').textContent());
    console.log('OK con la red cortada pregunta cada 10 s (' + consultas + ' en 9 s) y, cuando vuelve, guarda y saca el aviso');
    await ctx.close();
  }

  // (z19) Entra otro usuario antes de que llegue la primera consulta y antes
  // de los 4 s del arranque: el aviso de otro usuario no lo pisa el de la red.
  if (corre('z19')) {
    const ctx = await nuevoContexto('ord1z19');
    let soltar, pedida;
    const suelta = new Promise(r => { soltar = r; });
    const llego = new Promise(r => { pedida = r; });
    const t = await ctx.newPage();
    t.on('dialog', d => d.accept().catch(() => {}));
    await t.route('**/auth/current_user', async ruta => {
      pedida();
      await suelta;
      return ruta.continue().catch(() => {});
    });
    const desde = Date.now();
    await t.goto(base + '/dashboard');
    await llego;
    await nuevoUsuario(ctx, 'ord1z19b');
    soltar();
    if (Date.now() - desde > 3000) falla('el otro usuario tardó ' + (Date.now() - desde) + ' ms en entrar: la prueba no llega antes de los 4 s del arranque');
    await t.waitForFunction(() => window.CDI && document.querySelector('.screen.is-active'), null, { timeout: 10000 });
    const aviso = await avisa(t) ? await t.locator('#avisoBorrador').textContent() : '';
    if (!/Entró otro usuario/.test(aviso)) falla('entró otro usuario antes de la primera consulta y la pestaña avisa otra cosa: «' + aviso + '»');
    console.log('OK si entra otro usuario antes de los 4 s del arranque, el aviso dice que entró otro');
    await ctx.close();
  }

  // (z20) a (z24) ORDEN-1b: lo que la pestaña manda al servidor. La pestaña
  // es de A; entra B en el mismo navegador y la pestaña de A intenta escribir.
  // Lo que A y B tienen en el servidor, mirado con una sesión aparte. Cada
  // mirada entra con otra IP inventada, para no gastar el límite de 5
  // entradas por minuto que usan los casos.
  let miradas = 0;
  async function enElServidor(usuario) {
    const r = await request.newContext({ baseURL: base, extraHTTPHeaders: { 'X-Forwarded-For': '192.0.2.' + (++miradas % 250 + 1) } });
    const login = await r.post('/auth/login', { data: { username: usuario, password: CLAVE } });
    if (!login.ok()) falla('no se pudo entrar como ' + usuario + ' para mirar el servidor: ' + login.status());
    const ops = await (await r.get('/api/operations')).json();
    const cobro = await (await r.get('/api/billing/me')).json();
    const clientes = await (await r.get('/api/clientes')).text();
    await r.dispose();
    return { operaciones: ops.total, cobradas: cobro.ops_used_this_period, clientes };
  }
  const tapada = p => p.evaluate(() => { const d = document.getElementById('pestanaAjena'); return !!(d && d.open); });
  // Los pedidos que escriben y salen de la pestaña, por ruta.
  const contarEscrituras = p => {
    const salen = [];
    p.on('request', r => { if (!['GET', 'HEAD', 'OPTIONS'].includes(r.method())) salen.push(new URL(r.url()).pathname); });
    return salen;
  };
  // Deja la operación en «Validación», lista para generar, mientras la sesión
  // todavía es de A.
  async function listaParaGenerar(p, factura) {
    await cargar(p, factura, [prod('Producto de ' + factura, '84714900100D', 2, 10)]);
    await p.evaluate(() => CDI.goTo('validating'));
    await p.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 });
    await p.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 });
    await p.fill('#sbtSufijoValor', 'AA(DemoPouchs)-CA00-');
  }
  // Aprieta «Generar» por programa (un diálogo modal no lo frena) y espera
  // cómo termina: 'generado', 'error: <texto>', 'tapada' o null.
  async function apretarGenerar(p) {
    await p.evaluate(() => document.getElementById('validatingGenerate').click());
    for (const hasta = Date.now() + 25000; Date.now() < hasta;) {
      const fin = await p.evaluate(() => {
        const visible = id => { const el = document.getElementById(id); return !!(el && !el.hidden && el.offsetParent); };
        if (visible('readyDone')) return 'generado';
        if (visible('readyError')) return 'error: ' + document.getElementById('readyErrorText').textContent.trim();
        return null;
      });
      if (fin) return (await tapada(p)) ? 'tapada, ' + fin : fin;
      if (await tapada(p)) return 'tapada';
      await p.waitForTimeout(200);
    }
    return null;
  }
  // Retiene /auth/current_user de la pestaña hasta soltar(); con `ms`, sólo
  // lo demora.
  async function retenerUsuario(p, ms) {
    let soltar;
    const suelta = ms ? null : new Promise(r => { soltar = r; });
    await p.route('**/auth/current_user', async ruta => {
      await (suelta || new Promise(r => setTimeout(r, ms)));
      return ruta.continue().catch(() => {});
    });
    return () => soltar && soltar();
  }
  async function nadaEnElServidor(a, otro, que, cliente) {
    for (const u of [a, otro]) {
      const s = await enElServidor(u);
      if (s.operaciones || s.cobradas) falla(que + ' y quedó una operación en la cuenta de ' + (u === a ? 'A' : 'B') + ': ' + s.operaciones + ' creadas, ' + s.cobradas + ' cobradas');
      if (cliente && s.clientes.includes(cliente)) falla(que + ' y el cliente quedó en la cuenta de ' + (u === a ? 'A' : 'B'));
    }
  }
  // Como un servidor que no exige CSRF: cada escritura llega con el token de
  // la cookie de ahora, sea cual sea el que mandó la pestaña.
  async function sinCsrf(ctx, p) {
    await p.route(r => !/^\/(static|health)/.test(new URL(r).pathname), async ruta => {
      const pedido = ruta.request();
      if (['GET', 'HEAD', 'OPTIONS'].includes(pedido.method())) return ruta.fallback();
      const token = ((await ctx.cookies()).find(c => c.name === 'csrf_token') || {}).value;
      return ruta.fallback({ headers: Object.assign({}, pedido.headers(), { 'x-csrf-token': token || '' }) });
    });
  }
  const generarConOtro = (nombre, que, antes, espera) => async () => {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const a = await nuevoUsuario(ctx, nombre);
    const t = await abrir(ctx);
    await listaParaGenerar(t, 'GEN-' + nombre);
    const soltar = antes ? await antes(t) : () => {};
    const otro = await nuevoUsuario(ctx, nombre + 'b');
    if (espera) await espera(t);
    const salen = contarEscrituras(t);
    const fin = await apretarGenerar(t);
    soltar();
    await nadaEnElServidor(a, otro, que, null);
    const generados = salen.filter(x => x === '/generate_maria').length;
    await ctx.close();
    return { fin, generados };
  };
  // (z20) Generar con B adentro: (i) enseguida, antes de que la pestaña se
  // entere (pregunta quién es, no sale y se tapa); (ii) con el aviso ya en
  // pantalla (no sale); (iii) sin poder comprobar quién es (error).
  if (corre('z20')) {
    let que = 'entró otro usuario y la pestaña de A generó enseguida';
    let r = await generarConOtro('ord1z20a', que, t => retenerUsuario(t, 3000))();
    if (r.generados) falla(que + ' y el pedido de generar salió de la pestaña ' + r.generados + ' vez/veces');
    if (!/^tapada/.test(r.fin || '')) falla(que + ' y la pestaña no se tapa: ' + r.fin);
    console.log('OK ' + que + ': el pedido no sale y la pestaña se tapa');

    que = 'entró otro usuario, la pestaña de A ya lo avisa y genera';
    r = await generarConOtro('ord1z20b', que, null, t => t.waitForFunction(() =>
      /Entró otro usuario/.test(document.getElementById('avisoBorrador').textContent), null, { timeout: 4 * INTERVALO_MS }))();
    if (r.generados) falla(que + ' y el pedido de generar salió de la pestaña ' + r.generados + ' vez/veces');
    if (!/^tapada/.test(r.fin || '')) falla(que + ' y la pestaña no está tapada: ' + r.fin);
    console.log('OK ' + que + ': el pedido no sale y la pestaña está tapada');

    que = 'entró otro usuario y la pestaña de A genera sin poder comprobar quién es';
    r = await generarConOtro('ord1z20c', que, t => retenerUsuario(t))();
    if (!/^error: .*No se pudo comprobar la sesión/.test(r.fin || '')) falla(que + ' y no muestra el error: ' + r.fin);
    console.log('OK ' + que + ': no se crea ni se cobra nada y avisa el error');
  }

  // (z21) Otra familia de escritura: guardar un cliente con B adentro, con
  // un servidor que no exige CSRF.
  if (corre('z21')) {
    const que = 'entró otro usuario y la pestaña de A guardó un cliente';
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const a = await nuevoUsuario(ctx, 'ord1z21');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');
    await sinCsrf(ctx, t);
    const soltar = await retenerUsuario(t, 3000);
    const otro = await nuevoUsuario(ctx, 'ord1z21b');
    const cliente = 'Cliente demo ' + otro;
    const res = await t.evaluate(n => CDI.api('/api/clientes', { method: 'POST', body: JSON.stringify({ nombre: n }) })
      .then(r => 'status ' + r.status, e => 'error: ' + e.message), cliente);
    soltar();
    await nadaEnElServidor(a, otro, que, cliente);
    if (!(await tapada(t))) falla(que + ' (' + res + ') y la pestaña no se tapa');
    console.log('OK ' + que + ': no queda en ninguna cuenta y la pestaña se tapa');
    await ctx.close();
  }

  // (z22) A sale y vuelve a entrar y genera enseguida: la pestaña confirma
  // que sigue siendo A y genera, sin taparse.
  if (corre('z22')) {
    const que = 'A salió, volvió a entrar y generó enseguida';
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const a = await nuevoUsuario(ctx, 'ord1z22');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');  // como en (m)
    const terminaron = seguirPedidos(t);
    // En un solo paso: si la pestaña se queda en otra pantalla, el semáforo valida una vez más o una menos.
    await t.evaluate(([op, items]) => {
      CDI.state = { operacion: op, items };
      CDI.goTo('validating');
    }, [Object.assign({ numero_factura: 'GEN-Z22' }, OPERACION), [prod('Producto de GEN-Z22', '84714900100D', 2, 10)]]);
    await t.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 });
    // Un pedido de A que el servidor atiende después de la salida da 401 y manda la pestaña al login.
    await terminaron(AL_ENTRAR_A_VALIDACION).catch(e => falla(que + ': antes de salir, ' + e.message));
    const comprobo = await demorarHastaGenerar(t);
    const salida = await salir(ctx);
    if (!salida.ok()) falla('no se pudo salir: ' + salida.status());
    // Con la sesión ya cerrada: lo que dispara escribir sale después de la consulta de sesión, que está demorada.
    await t.fill('#sbtSufijoValor', 'AA(DemoPouchs)-CA00-');
    await entrar(ctx, a);
    const fin = await apretarGenerar(t);
    if (fin !== 'generado') falla(que + ' y no generó: ' + fin);
    if (!comprobo()) falla(que + ' y Generar no comprobó la sesión');
    const s = await enElServidor(a);
    if (s.operaciones !== 1) falla(que + ' y A tiene ' + s.operaciones + ' operaciones en el servidor');
    console.log('OK ' + que + ': genera sin falsos bloqueos');
    await ctx.close();
  }

  // (z23) Lo mismo que (z20) con un servidor que no exige CSRF (desarrollo,
  // o producción si se apaga): el freno es de la pestaña, no del servidor.
  if (corre('z23')) {
    const que = 'con un servidor que no exige CSRF, entró otro usuario y la pestaña de A generó enseguida';
    const r = await generarConOtro('ord1z23', que, async t => {
      await sinCsrf(t.context(), t);
      return retenerUsuario(t, 3000);
    })();
    if (r.generados) falla(que + ' y el pedido de generar salió de la pestaña ' + r.generados + ' vez/veces');
    if (!/^tapada/.test(r.fin || '')) falla(que + ' y la pestaña no se tapa: ' + r.fin);
    console.log('OK ' + que + ': el pedido no sale y la pestaña se tapa');
  }

  // (z24) Salir desde la pestaña de A con B adentro, antes de que se entere:
  // la sesión de B sigue abierta.
  if (corre('z24')) {
    const que = 'entró otro usuario y A apretó «Salir» en su pestaña';
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    await nuevoUsuario(ctx, 'ord1z24');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');
    const soltar = await retenerUsuario(t, 3000);
    await nuevoUsuario(ctx, 'ord1z24b');
    const salidas = contarEscrituras(t);
    await t.evaluate(() => { CDI.logout(); });
    await t.waitForFunction(() => {
      const d = document.getElementById('pestanaAjena');
      return (d && d.open) || location.pathname !== '/dashboard';
    }, null, { timeout: 25000 }).catch(() => {});
    soltar();
    const sigue = await ctx.request.get(base + '/auth/current_user');
    if (!sigue.ok()) falla(que + ' y cerró la sesión de B (' + sigue.status() + '; salió ' + salidas.join(', ') + ')');
    // Si fue al inicio, la página de la pestaña ya no está para preguntarle.
    if (!(await tapada(t).catch(() => false))) falla(que + ' y la pestaña no se tapa');
    console.log('OK ' + que + ': la sesión de B sigue abierta y la pestaña se tapa');
    await ctx.close();
  }

  // (z25) Con la sesión cerrada en otra pestaña, una escritura manda al
  // login, como antes de ORDEN-1b.
  if (corre('z25')) {
    const que = 'A salió en otra pestaña y guardó un cliente en esta';
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    await nuevoUsuario(ctx, 'ord1z25');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');
    const salida = await salir(ctx);
    if (!salida.ok()) falla('no se pudo salir: ' + salida.status());
    const res = await t.evaluate(() => CDI.api('/api/clientes', { method: 'POST', body: JSON.stringify({ nombre: 'Cliente demo' }) })
      .then(r => 'status ' + r.status, e => 'error: ' + e.message)).catch(() => 'navegó');
    await t.waitForURL(u => u.pathname === '/', { timeout: 15000 }).catch(() => {});
    if (!/[?&]next=%2Fdashboard/.test(t.url())) falla(que + ' y no fue al login (' + res + '; está en ' + t.url() + ')');
    console.log('OK ' + que + ': va al login');
    await ctx.close();
  }

  // (z26) A salió y volvió a entrar y aprieta «Salir» sin que la pestaña
  // pueda comprobar quién es: no va al inicio como si hubiera salido.
  if (corre('z26')) {
    const que = 'A volvió a entrar y apretó «Salir» sin poder comprobar quién es';
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const a = await nuevoUsuario(ctx, 'ord1z26');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');
    const soltar = await retenerUsuario(t);
    const salida = await salir(ctx);
    if (!salida.ok()) falla('no se pudo salir: ' + salida.status());
    await entrar(ctx, a);
    await t.evaluate(() => { CDI.logout(); });
    await t.waitForFunction(() => location.pathname !== '/dashboard' ||
      /No se pudo cerrar la sesión/.test(document.getElementById('toastHost').textContent), null, { timeout: 25000 }).catch(() => {});
    soltar();
    const sigue = (await ctx.request.get(base + '/auth/current_user')).ok();
    if (new URL(t.url()).pathname !== '/dashboard') falla(que + ' y fue al inicio ' + (sigue ? 'con la sesión abierta' : 'cerrando la sesión'));
    if (!/No se pudo cerrar la sesión[^]*No se pudo comprobar la sesión/.test(await t.evaluate(() => document.getElementById('toastHost').textContent))) falla(que + ' y no avisa que no pudo comprobar la sesión');
    console.log('OK ' + que + ': se queda y avisa que no pudo comprobar la sesión');
    await ctx.close();
  }

  // (z27) La telemetría escribe con fetch directo, sin pasar por api(): con
  // B adentro, la pestaña de A no la manda.
  if (corre('z27')) {
    const que = 'entró otro usuario y la pestaña de A mandó telemetría';
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    await nuevoUsuario(ctx, 'ord1z27');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');
    const salen = contarEscrituras(t);
    const telemetria = () => salen.filter(x => x === '/api/session/state').length;
    await t.evaluate(() => CDI.track('prueba_orden1b'));
    await t.waitForTimeout(500);
    if (telemetria() !== 1) falla('la pestaña de A no manda telemetría con su propia sesión: ' + telemetria());
    await nuevoUsuario(ctx, 'ord1z27b');
    await t.evaluate(() => CDI.track('prueba_orden1b'));
    await t.waitForTimeout(500);
    if (telemetria() !== 1) falla(que + ' a nombre de B');
    console.log('OK ' + que + ': no sale');
    await ctx.close();
  }

  // (z28) Como (l), pero sin escrituras: al cargar, el semáforo valida con un
  // POST y el freno de api() ya tapa la pestaña. Acá B entra con la operación
  // ya validada y lo que cambia queda en la pestaña: el que no guarda es
  // usuarioActual.
  if (corre('z28')) {
    const que = 'entró otro usuario y la pestaña de A no escribe nada';
    const ctx = await nuevoContexto('ord1z28');
    const t = await abrir(ctx);
    await cargar(t, 'DE-A-Z28', [prod('Producto cargado por A', '84714900100D', 2, 10)]);
    await esperarBorradores(t, ['DE-A-Z28'], que + ', pero antes de que entre no guarda la operación de A');
    await t.waitForLoadState('networkidle');
    await t.evaluate(() => {
      const api = CDI.api;
      window.__escribe = [];
      CDI.api = (path, o) => {
        if (!['GET', 'HEAD', 'OPTIONS'].includes(((o && o.method) || 'GET').toUpperCase())) window.__escribe.push(path);
        return api(path, o);
      };
    });
    const otro = await nuevoUsuario(ctx, 'ord1z28b');
    await t.evaluate(() => { CDI.state.operacion.numero_factura = 'DE-B-Z28'; });
    await t.waitForTimeout(2 * INTERVALO_MS);
    const escribe = await t.evaluate(() => window.__escribe);
    if (escribe.length) falla(que + ' y quiso escribir: ' + escribe.join(', ') + ' (el caso ya no mide usuarioActual)');
    const sobres = await sobresDe(t, 'DE-B-Z28');
    if (sobres.length) falla(que + ' y lo que cambió después se guardó a nombre de ' + sobres.map(s => s.user).join(', '));
    if (!(await avisa(t))) falla(que + ' y no avisa que dejó de guardar');
    console.log('OK ' + que + ': no guarda lo que cambia y lo avisa (' + otro + ')');
    await ctx.close();
  }

  // Retiene /auth/current_user ya contestado por el servidor, con la sesión
  // de ese momento, hasta soltar(). Lo que la pestaña pide después de
  // cerrar() ni se pregunta hasta soltarResto().
  async function retenerRespuestas(p) {
    let soltar, soltarResto, alTraer = () => {}, cerrado = false, traidas = 0;
    const suelta = new Promise(r => { soltar = r; }), resto = new Promise(r => { soltarResto = r; });
    await p.evaluate(() => {
      const f = window.fetch;
      window.__consultas = 0;
      window.fetch = (u, o) => { if (/\/auth\/current_user$/.test(String(u))) window.__consultas++; return f(u, o); };
    });
    await p.route('**/auth/current_user', async ruta => {
      if (cerrado) { await resto; return ruta.continue().catch(() => {}); }
      const respuesta = await ruta.fetch();
      traidas++;
      alTraer();
      await suelta;
      return ruta.fulfill({ response: respuesta }).catch(() => {});
    });
    // Todas las consultas que hizo la pestaña ya tienen la respuesta del servidor.
    const contestadas = async () => {
      // Cuenta las pedidas antes de leer traidas: una respuesta que llega
      // durante el evaluate ya está sumada y no se espera un aviso perdido.
      const tope = setTimeout(() => falla('el servidor no contestó las consultas de la pestaña en 15 s'), 15000);
      try {
        while (await p.evaluate(() => window.__consultas) > traidas) await new Promise(r => { alTraer = r; });
      } finally { clearTimeout(tope); }
    };
    return { contestadas, cerrar: () => { cerrado = true; }, soltar, soltarResto };
  }
  async function noTomoDatos(p, otro, que) {
    const visto = await p.evaluate(() => [(CDI.currentUser || {}).username || '', document.getElementById('userName').textContent]);
    if (visto.some(v => v.includes(otro))) falla(que + ' y la pestaña tomó los datos de B: ' + visto.join(', '));
  }
  const guardarCliente = (p, nombre) => p.evaluate(n => CDI.api('/api/clientes', { method: 'POST', body: JSON.stringify({ nombre: n }) })
    .then(r => 'status ' + r.status, e => 'error: ' + e.message), nombre);

  // (z29) A sale y vuelve a entrar y guarda un cliente; la pestaña pregunta
  // quién es, el servidor contesta «A» y entra B antes de que llegue: la
  // respuesta ya no dice de quién es la sesión de ahora.
  if (corre('z29')) {
    const que = 'la pestaña de A preguntó quién es, entró otro usuario antes de la respuesta y guardó un cliente';
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const a = await nuevoUsuario(ctx, 'ord1z29');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');
    const r = await retenerRespuestas(t);
    const salida = await salir(ctx);
    if (!salida.ok()) falla('no se pudo salir: ' + salida.status());
    await entrar(ctx, a);
    const cliente = 'Cliente demo ' + a;
    const res = guardarCliente(t, cliente);
    await t.waitForFunction(() => window.__consultas > 0);
    await r.contestadas();
    r.cerrar();
    const otro = await nuevoUsuario(ctx, 'ord1z29b');
    r.soltar();
    const fin = await res;
    r.soltarResto();
    await nadaEnElServidor(a, otro, que, cliente);
    if (!/No se pudo comprobar la sesión/.test(fin)) falla(que + ' y no avisa el error: ' + fin);
    console.log('OK ' + que + ': no queda en ninguna cuenta y avisa el error');
    await ctx.close();
  }

  // Abre la pestaña de A y, antes de que sepa quién es, entra B: la primera
  // respuesta ya dice B y la pestaña se tapa.
  async function abrirYEntraOtro(nombre) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const a = await nuevoUsuario(ctx, nombre);
    const t = await ctx.newPage();
    const soltar = await retenerUsuario(t);
    await t.goto(base + '/dashboard');
    await t.waitForFunction(() => window.CDI && CDI.api);
    const otro = await nuevoUsuario(ctx, nombre + 'b');
    soltar();
    await t.waitForFunction(() => { const d = document.getElementById('pestanaAjena'); return d && d.open; }, null, { timeout: 15000 })
      .catch(() => falla('entró otro usuario antes de que la pestaña de A supiera quién es y no se tapa'));
    return { ctx, a, otro, t };
  }

  // (z30) Tapada desde la primera carga, la pestaña guarda un cliente: la
  // sesión de ahora es la del usuario que contestó, pero no es la del dueño.
  if (corre('z30')) {
    const que = 'la pestaña de A quedó tapada al abrir y guardó un cliente';
    const { ctx, a, otro, t } = await abrirYEntraOtro('ord1z30');
    await noTomoDatos(t, otro, 'entró otro usuario antes de que la pestaña de A supiera quién es');
    const cliente = 'Cliente demo ' + otro;
    const fin = await guardarCliente(t, cliente);
    await nadaEnElServidor(a, otro, que, cliente);
    if (!/Entró otro usuario/.test(fin)) falla(que + ' y no avisa que entró otro: ' + fin);
    console.log('OK ' + que + ': no toma los datos de B ni queda en ninguna cuenta');
    await ctx.close();
  }

  // (z31) Las otras escrituras con B adentro, por las rutas de la app: no
  // sale ninguna de la pestaña de A.
  if (corre('z31')) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    await nuevoUsuario(ctx, 'ord1z31');
    const t = await abrir(ctx);
    await t.waitForLoadState('networkidle');
    await nuevoUsuario(ctx, 'ord1z31b');
    const salen = contarEscrituras(t);
    for (const [metodo, ruta, cuerpo] of [
      ['PUT', '/api/clientes/999999', { nombre: 'Cliente demo' }],
      ['DELETE', '/api/clientes/999999'],
      ['PATCH', '/api/operations/999999/estado', { estado: 'oficializada' }],
    ]) {
      const fin = await t.evaluate(([m, r, c]) => CDI.api(r, Object.assign({ method: m }, c ? { body: JSON.stringify(c) } : {}))
        .then(x => 'status ' + x.status, e => 'error: ' + e.message), [metodo, ruta, cuerpo]);
      if (salen.includes(ruta)) falla('entró otro usuario y la pestaña de A mandó ' + metodo + ' ' + ruta + ' (' + fin + ')');
      console.log('OK entró otro usuario y la pestaña de A no manda ' + metodo + ' ' + ruta);
    }
    await ctx.close();
  }

  // (z32) La pestaña tapada no se destapa con Escape, y «Recargar» recarga.
  if (corre('z32')) {
    const { ctx, t } = await abrirYEntraOtro('ord1z32');
    for (const vez of [1, 2]) {
      await t.keyboard.press('Escape');
      if (!(await tapada(t))) falla('la pestaña tapada se destapa con Escape (vez ' + vez + ')');
    }
    const recarga = t.waitForEvent('load', { timeout: 10000 }).then(() => true, () => false);
    await t.locator('#pestanaAjenaRecargar').click();
    if (!(await recarga)) falla('la pestaña tapada no recarga con «Recargar»');
    console.log('OK la pestaña tapada no se destapa con Escape y recarga con «Recargar»');
    await ctx.close();
  }

  // Abre la vuelta del pago de A y retiene la relectura del usuario hasta que
  // entra B. Con `conCookieDeA` la consulta llega al servidor enseguida, con
  // la sesión de A; si no, sale al soltarla, con la de B. `primero` ('tour' o
  // 'carga') fija cuál de las otras dos consultas de quién es llega antes.
  async function vueltaDelPago(nombre, billing, conCookieDeA, que, primero) {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
    const a = await nuevoUsuario(ctx, nombre);
    const t = await ctx.newPage();
    // El tour y la carga también piden /auth/current_user: cada pedido sale
    // con un header que dice cuál es, y sólo se retiene la relectura.
    await t.addInitScript(() => {
      const programar = window.setTimeout, f = window.fetch;
      let enRelectura = false, leida = null, marcarLeida;
      window.__relecturaLeida = false;
      window.setTimeout = (fn, ...resto) => programar(fn && fn.name === 'loadCurrentUser'
        ? () => { enRelectura = true; try { return fn(); } finally { enRelectura = false; } } : fn, ...resto);
      window.fetch = async (u, o = {}) => {
        if (!/\/auth\/current_user$/.test(String(u))) return f(u, o);
        const cual = enRelectura ? 'relectura' : /checkDemoForceTour/.test(new Error().stack) ? 'tour' : 'carga';
        // Otra consulta (el autoguardado, por ejemplo) vería a B antes y taparía este freno con otro.
        const primera = cual === 'relectura' && !leida;
        if (!primera && leida) await leida;
        const pedido = f(u, { ...o, headers: { ...o.headers, 'X-Prueba-Consulta': cual } });
        if (!primera) return pedido;
        leida = new Promise(r => { marcarLeida = r; });
        return pedido.then(res => {
          const json = res.json.bind(res);
          // Después de la lectura, para que la pestaña termine de procesarla.
          res.json = () => json().finally(() => programar(() => { window.__relecturaLeida = true; marcarLeida(); }));
          return res;
        });
      };
    });
    const cual = r => r.headers()['x-prueba-consulta'];
    let tourListo;
    const tourTermino = new Promise(r => { tourListo = r; });
    t.on('requestfinished', r => { if (cual(r) === 'tour') tourListo(); });
    t.on('requestfailed', r => { if (cual(r) === 'tour' && primero === 'tour') falla(que + ', pero la consulta del tour falló'); });
    let avisar, soltar, retenida = false;
    const hayRetenida = new Promise(r => { avisar = r; }), suelta = new Promise(r => { soltar = r; });
    await t.route('**/auth/current_user', async ruta => {
      const esta = cual(ruta.request());
      if (esta === 'carga' && primero === 'tour') {
        const tope = setTimeout(() => falla(que + ', pero el tour no consultó el usuario en 15 s'), 15000);
        await tourTermino;
        clearTimeout(tope);
      }
      if (esta === 'tour' && primero === 'carga') {
        await t.waitForFunction(() => !!(window.CDI && CDI.currentUser), null, { timeout: 15000 })
          .catch(() => falla(que + ', pero la pestaña no cargó el usuario antes del tour'));
      }
      if (esta !== 'relectura' || retenida) return ruta.continue().catch(() => {});
      retenida = true;
      // Sin dueño todavía, otro freno ataja la cookie nueva y el caso no mediría este.
      if (!(await t.evaluate(() => !!(window.CDI && CDI.currentUser)))) falla(que + ', pero la relectura salió antes de que la pestaña cargara el usuario');
      // route.continue() pone las cookies del momento en que se suelta.
      const respuesta = conCookieDeA ? await ruta.fetch().catch(e => falla(que + ' y la relectura no llegó al servidor: ' + e.message)) : null;
      // Si contestara B, mediría lo mismo que vueltaConOtroAdentro.
      if (respuesta && (await respuesta.json()).username !== a) falla(que + ', pero la relectura retenida no es de A');
      avisar();
      await suelta;
      return (respuesta ? ruta.fulfill({ response: respuesta }) : ruta.continue()).catch(() => {});
    });
    await t.goto(base + '/dashboard?billing=' + billing);
    const tope = setTimeout(() => falla(que + ', pero la pestaña no vuelve a leer el usuario en 15 s'), 15000);
    await hayRetenida;
    clearTimeout(tope);
    const otro = await nuevoUsuario(ctx, nombre + 'b');
    soltar();
    // Sin esto la escritura podría salir antes de que la pestaña lea la relectura.
    await t.waitForFunction(() => window.__relecturaLeida, null, { timeout: 15000 })
      .catch(() => falla(que + ' y la pestaña no leyó la relectura del pago en 15 s: no se escribe sin medirla'));
    return { ctx, a, otro, t };
  }

  // (z34) Al volver del pago, la pestaña de A vuelve a leer el usuario; si
  // entró B, no toma sus datos.
  async function vueltaConOtroAdentro() {
    const que = 'A volvió del pago con B adentro';
    const { ctx, otro, t } = await vueltaDelPago('ord1z34', 'success', false, que);
    await noTomoDatos(t, otro, que);
    console.log('OK ' + que + ': no toma los datos de B');
    await ctx.close();
  }

  // (z35) La relectura de la vuelta del pago contesta A, pero B entró antes
  // de que la pestaña la leyera: esa respuesta no autoriza escribir.
  async function respuestaDeAConOtroAdentro() {
    // VUELTA=<billing> y PRIMERO=<tour|carga> dejan una sola fila, para que el sabotaje vea cada una.
    const filas = ['success', 'topup_success'].flatMap(billing => ['tour', 'carga'].map(primero => ({ billing, primero })))
      .filter(f => (!process.env.VUELTA || f.billing === process.env.VUELTA) && (!process.env.PRIMERO || f.primero === process.env.PRIMERO));
    if (!filas.length) falla('VUELTA o PRIMERO no dejan ninguna fila de z35');
    for (const { billing, primero } of filas) {
      const que = 'la relectura de la vuelta del pago (' + billing + ', primero ' + primero + ') contestó A, entró B antes de leerla y la pestaña guardó un cliente';
      const { ctx, a, otro, t } = await vueltaDelPago('ord1z35', billing, true, que, primero);
      const cliente = 'Cliente demo ' + a;
      const fin = await guardarCliente(t, cliente);
      await nadaEnElServidor(a, otro, que, cliente);
      if (!/Entró otro usuario/.test(fin)) falla(que + ' y no avisa que entró otro: ' + fin);
      console.log('OK ' + que + ': no queda en ninguna cuenta y avisa que entró otro');
      await ctx.close();
    }
  }

  if (corre('z34')) await vueltaConOtroAdentro();
  if (corre('z35')) await respuestaDeAConOtroAdentro();

  await b.close();
  console.log('OK: ORDEN-1 en el navegador');
})().catch(e => falla(e.message));
