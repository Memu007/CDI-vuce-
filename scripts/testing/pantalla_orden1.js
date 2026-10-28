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
//  (e) arrastrar después de una acción masiva: Ctrl+Z no vuelve el orden.
// Datos inventados. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_orden1.js
const { chromium } = require('/opt/node-tools/node_modules/playwright');
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

async function nuevoUsuario(ctx, nombre) {
  const p = await ctx.newPage();
  const id = Date.now() + '_' + Math.floor(Math.random() * 1e6);
  const r = await p.request.post(base + '/auth/register',
    { data: { username: nombre + '_' + id, password: 'Clave-Inventada-123', email: nombre + id + '@ejemplo.test' } });
  if (!r.ok()) falla('no se pudo registrar el usuario de prueba: ' + r.status());
  // Sin el CUIT del despachante no se genera el TXT (ESTUDIO-1); inventado.
  const perfil = await p.request.put(base + '/api/user/profile', { data: { cuit: '20999999998' } });
  if (!perfil.ok()) falla('no se pudo cargar el CUIT del perfil: ' + perfil.status());
  await p.close();
}

async function abrir(ctx) {
  const p = await ctx.newPage();
  p.on('dialog', d => d.accept().catch(() => {}));
  await p.goto(base + '/dashboard');
  await p.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && document.querySelector('.screen.is-active'));
  // El banner de la prueba gratis aparece con el usuario y corre la tabla
  // hacia abajo: sin esperarlo, el mouse aprieta sobre la fila de arriba.
  await p.waitForFunction(() => CDI.currentUser);
  return p;
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
    await p.locator('body').click({ position: { x: 5, y: 300 } });
    await p.keyboard.press('Control+z');
    // El deshacer es sincrónico: si iba a cambiar algo, ya cambió.
    if (!igual(await orden(p), esperado)) falla('Ctrl+Z después de arrastrar vuelve el orden de antes: ' + JSON.stringify(await orden(p)));
    console.log('OK Ctrl+Z después de arrastrar no deshace el orden');
    await ctx.close();
  }

  await b.close();
  console.log('OK: ORDEN-1 en el navegador');
})().catch(e => falla(e.message));
