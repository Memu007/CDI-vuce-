// SUFIJOS-1 en el navegador local (sin terceros: /generate_maria se
// intercepta; el arancel es la tabla local del repositorio).
// En «Lo que decide el despachante», cada producto entero muestra el sufijo
// propuesto con lo que leyó la IA (marca y código) y dice de dónde sale y
// qué falta; la posición que no está en el arancel queda vacía y marcada.
// Regla de la vuelta: al generar, lo que va al pedido por producto es lo que
// muestra su celda. El de la operación gana y la propuesta sólo agrega los
// códigos que faltan (lo distinto se avisa en la fila); lo escrito por la
// persona va tal cual y avisa si después cambia el de la operación; si el
// arancel no contesta o todavía consulta, no viaja nada de la propuesta
// (ni el sufijo ni los kilos) y la celda y los avisos lo dicen; con el de la
// operación vacío y todos con el propio, se avisa sin frenar (D23). Sale con
// error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_sufijos1.js [captura-telefono.png]
const { chromium } = require('playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const FUENTE = 'arancel de ARCA del 07/10/2026';
const NO_CONTESTO = 'El arancel de ARCA no contestó: no se propone sufijo ni unidad; va el de la operación.';
const CONSULTANDO = 'Consultando el arancel de ARCA…';
const OTRA_OPERACION = 'Lo escribiste con otro sufijo de la operación: revisalo, va tal cual.';
const D23 = 'El sufijo de la operación está vacío: cada producto sale sólo con lo que pide el arancel de ARCA';
(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  await registrarCuenta(page.request, base, { data: { username: 's1_' + id, password: 'Clave-Inventada-123', email: 's1' + id + '@ejemplo.test' } });
  await page.route('**/generate_maria', async r => { await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, filename: 'MARIA_X.TXT', download_url: '#', content: '', supuestos: [] }) }); });

  // 3920.10.10.100F pide AA y AI, en kilos; 3921.13.90.999F no está en el
  // arancel (3921.13.90.900 sí, con otra letra de control).
  const ITEMS = [
    { pieza: '39201010100F', descripcion: 'Film de polietileno verde', origen: 'CN', cantidad: 320, valor_unitario: 2.4, peso_unitario: 0.8, unidad: '03', marca: 'Norteplast', codigo_parte: 'FP-90 VERDE' },
    { pieza: '39201010100F', descripcion: 'Film de polietileno ámbar', origen: 'CN', cantidad: 12, valor_unitario: 6, peso_unitario: 2, unidad: '03', marca: 'Norteplast', codigo_parte: 'FP-90 AMBAR' },
    { pieza: '39211390999F', descripcion: 'Plancha inventada', origen: 'CN', cantidad: 4, valor_unitario: 3, peso_unitario: 1, unidad: '03' },
    { pieza: '39201010100F', descripcion: 'Film de polietileno lila', origen: 'CN', cantidad: 6, valor_unitario: 5, peso_unitario: 1, unidad: '03', marca: 'Norteplast', codigo_parte: 'FP-90 LILA' },
  ];
  const solos = ['AA(Norteplast)-AI(FP 90 VERDE)-', 'AA(Norteplast)-AI(FP 90 AMBAR)-', '', 'AA(Norteplast)-AI(FP 90 LILA)-'];
  const con = op => solos.map(v => v ? op + v : '');
  const celdas = () => page.$$eval('.despachante-sufijo', s => s.map(x => x.value));
  const notas = () => page.$$eval('.despachante-sufijo-nota', s => s.map(x => x.textContent));
  async function entrar(items) {
    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante && CDI.despachante.avisos);
    await page.evaluate(items => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = { numero_factura: 'FA-0003-00009121', moneda: 'DOL', incoterm: 'FOB', comprador_cuit: '30712345671', fecha_emision: '11/10/2026' };
      CDI.state.items = items;
      CDI.goTo('validating');
    }, items);
    await page.waitForFunction(n => document.querySelectorAll('.despachante-sufijo-nota').length === n, items.length, { timeout: 10000 })
      .catch(() => falla('no aparecen las notas del sufijo por producto'));
  }
  // Espera a que las notas dejen de decir «Consultando…».
  async function contesto() {
    await page.waitForFunction(t => [...document.querySelectorAll('.despachante-sufijo-nota')].every(n => !n.textContent.includes(t)),
      CONSULTANDO, { timeout: 10000 }).catch(() => falla('el arancel no contesta en la pantalla'));
  }
  async function avisoVisible(texto) {
    await page.waitForFunction(t => (document.getElementById('validatingAvisosList') || {}).textContent.includes(t), texto, { timeout: 10000 })
      .catch(async () => falla('los avisos no dicen «' + texto + '»: ' + await page.$eval('#validatingAvisosList', el => el.textContent)));
  }
  async function operacion(texto) {
    await page.fill('#sbtSufijoValor', texto);
  }
  async function generar() {
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
    const pedida = page.waitForRequest('**/generate_maria', { timeout: 15000 }).catch(() => falla('no se pidió el TXT'));
    await page.click('#validatingGenerate');
    return JSON.parse((await pedida).postData()).items.map(i => [i.sufijo, i.unidad_estadistica]);
  }
  const igual = (a, b) => JSON.stringify(a) === JSON.stringify(b);

  // 1. La propuesta, sola y con el de la operación.
  await entrar(ITEMS);
  await contesto();
  let v = await celdas();
  if (!igual(v, solos)) falla('sufijos propuestos sin el de la operación: ' + JSON.stringify(v));
  await operacion('CA00-');
  v = await celdas();
  if (!igual(v, con('CA00-'))) falla('sufijos propuestos con el de la operación: ' + JSON.stringify(v));
  console.log('OK se propone marca y código de cada producto, detrás del de la operación; la posición fuera del arancel queda vacía');

  let n = await notas();
  if (!n[0].includes('Según el ' + FUENTE) || !n[0].includes('unidad estadística 01')) falla('nota del producto 1: ' + n[0]);
  if (!n[2].includes('no está en el ' + FUENTE)) falla('nota del producto fuera del arancel: ' + n[2]);
  console.log('OK cada nota dice de dónde sale: ' + n[0]);

  // 2. H5: el AA escrito en la operación gana; lo distinto se avisa en la fila.
  await operacion('AA(PROPIA SA)-CA00-');
  v = await celdas();
  if (v[0] !== 'AA(PROPIA SA)-CA00-AI(FP 90 VERDE)-') falla('el de la operación no ganó: ' + v[0]);
  n = await notas();
  if (!n[0].includes('El arancel propone AA(Norteplast); queda el de la operación: AA(PROPIA SA).')) falla('nota sin lo distinto: ' + n[0]);
  await avisoVisible('Ítem 1: El arancel propone AA(Norteplast)');
  console.log('OK el AA de la operación queda y la fila avisa lo que propone el arancel');

  // 3. La persona corrige el segundo y borra el primero; después cambia el
  // de la operación: el escrito queda y avisa (H2), los demás lo siguen.
  await operacion('CA00-');
  await page.fill('.despachante-sufijo[data-row="1"]', 'AA(OTRA)-AI(Y7)-');
  await page.fill('.despachante-sufijo[data-row="0"]', '');
  await operacion('CA01-');
  n = await notas();
  if (!n[1].includes(OTRA_OPERACION)) falla('la celda escrita no avisa el cambio de la operación: ' + n[1]);
  if (n[0].includes(OTRA_OPERACION)) falla('la celda vaciada avisa: ' + n[0]);
  await avisoVisible('Ítem 2: ' + OTRA_OPERACION);
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });
  // La página entera ya pasaba de 390 antes de SUFIJOS-1 (la fila de
  // «Generar MARIA.TXT»; pantalla_maria7.js da 597 en la base): se mide lo
  // de esta pieza, la tabla con su desplazamiento y la estadística general.
  const anchoPagina = await page.evaluate(() => document.documentElement.scrollWidth);
  console.log('ancho de la página a 390 px: ' + anchoPagina + ' (el de la base, sin cambios)');
  const bordes = await page.evaluate(() => ({
    tabla: Math.round(document.getElementById('despachanteItems').closest('div').getBoundingClientRect().right),
    estadistica: Math.round(document.getElementById('despachanteUnidadEst').getBoundingClientRect().right),
  }));
  console.log('borde derecho de la tabla y de la estadística: ' + JSON.stringify(bordes));
  if (bordes.tabla > 390 || bordes.estadistica > 390) falla('la tabla o la estadística se salen del teléfono: ' + JSON.stringify(bordes));
  let s = await generar();
  if (!igual(s, [[null, '01'], ['AA(OTRA)-AI(Y7)-', '01'], [null, null], ['CA01-' + solos[3], '01']]))
    falla('sufijo y estadística del pedido: ' + JSON.stringify(s));
  console.log('OK el pedido lleva lo de cada celda: el escrito, el de la operación donde se borró, el propuesto con el de la operación nuevo, y kilos donde la nota los dice');

  // 4. H1: el arancel no contesta. Las celdas lo dicen y no viaja nada de
  // la propuesta (ni kilos).
  await page.route('**/api/sufijos/propuesta', r => r.abort());
  await entrar(ITEMS.map(it => Object.assign({}, it)));
  await contesto();
  n = await notas();
  if (!n.every(t => t === NO_CONTESTO)) falla('con el arancel caído las notas dicen: ' + JSON.stringify(n));
  v = await celdas();
  if (!igual(v, ['', '', '', ''])) falla('con el arancel caído las celdas muestran: ' + JSON.stringify(v));
  await avisoVisible(NO_CONTESTO);
  await operacion('CA02-');
  s = await generar();
  if (!igual(s, [[null, null], [null, null], [null, null], [null, null]])) falla('con el arancel caído viajó: ' + JSON.stringify(s));
  console.log('OK sin arancel la celda y los avisos lo dicen y al generar no se agrega ni sufijo ni kilos');

  // 5. Se borra un producto y se genera mientras el arancel todavía
  // consulta: nada de la propuesta viaja (ni la del que estaba antes).
  await page.unroute('**/api/sufijos/propuesta');
  let soltar;
  const frenado = new Promise(r => { soltar = r; });
  await page.route('**/api/sufijos/propuesta', async r => { await frenado; await r.continue().catch(() => {}); });
  await entrar(ITEMS.slice(1).map(it => Object.assign({}, it)));
  n = await notas();
  if (!n.every(t => t === CONSULTANDO)) falla('mientras consulta las notas dicen: ' + JSON.stringify(n));
  await operacion('CA03-');
  s = await generar();
  soltar();
  if (!igual(s, [[null, null], [null, null], [null, null]])) falla('mientras consulta viajó: ' + JSON.stringify(s));
  console.log('OK mientras el arancel consulta, cada celda lo dice y no viaja la propuesta de nadie');
  await page.unroute('**/api/sufijos/propuesta');

  // 6. D23: todos con el propio y el de la operación vacío: avisa y deja generar.
  await entrar([ITEMS[0], ITEMS[1]].map(it => Object.assign({}, it)));
  await contesto();
  await avisoVisible(D23);
  s = await generar();
  if (!igual(s, [[solos[0], '01'], [solos[1], '01']])) falla('con el de la operación vacío: ' + JSON.stringify(s));
  console.log('OK con el de la operación vacío y todos con el propio, se avisa y se genera igual');
  await b.close();
  console.log('PANTALLA SUFIJOS-1 OK');
})().catch(e => falla(e && e.stack || e));
