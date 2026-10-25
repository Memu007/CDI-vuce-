// SUFIJOS-1 en el navegador local (sin terceros: /generate_maria se
// intercepta; el arancel es la tabla local del repositorio).
// En «Lo que decide el despachante», cada producto entero muestra el sufijo
// propuesto con lo que leyó la IA (marca y código) y dice de dónde sale y
// qué falta; la posición que no está en el arancel queda vacía y marcada. Lo
// que escribe la persona reemplaza a la propuesta, y borrado usa el de la
// operación. El pedido lleva el sufijo de cada producto (lo propuesto junto
// con el de la operación) y kilos si la posición los pide. Si se borra un
// producto y se genera enseguida, con el arancel lento, ningún producto se
// lleva la propuesta de otro. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_sufijos1.js [captura-telefono.png]
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const FUENTE = 'arancel de ARCA del 07/10/2026';
(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  await page.request.post(base + '/auth/register', { data: { username: 's1_' + id, password: 'Clave-Inventada-123', email: 's1' + id + '@ejemplo.test' } });
  await page.route('**/generate_maria', async r => { await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, filename: 'MARIA_X.TXT', download_url: '#', content: '', supuestos: [] }) }); });

  // 3920.10.10.100F pide AA y AI, en kilos; 3921.13.90.999F no está en el
  // arancel (3921.13.90.900 sí, con otra letra de control).
  const ITEMS = [
    { pieza: '39201010100F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62, unidad: '03', marca: 'Marca Demo', codigo_parte: '620G-GRIS' },
    { pieza: '39201010100F', descripcion: 'Lona de PVC negra', origen: 'CN', cantidad: 10, valor_unitario: 5, peso_unitario: 1, unidad: '03', marca: 'Marca Demo', codigo_parte: '620G-NEGRA' },
    { pieza: '39211390999F', descripcion: 'Lona inventada', origen: 'CN', cantidad: 5, valor_unitario: 2, peso_unitario: 1, unidad: '03' },
    { pieza: '39201010100F', descripcion: 'Lona de PVC azul', origen: 'CN', cantidad: 8, valor_unitario: 4, peso_unitario: 1, unidad: '03', marca: 'Marca Demo', codigo_parte: '620G-AZUL' },
  ];
  const propuestos = ['AA(Marca Demo)-CA00-AI(620G GRIS)-', 'AA(Marca Demo)-CA00-AI(620G NEGRA)-', '', 'AA(Marca Demo)-CA00-AI(620G AZUL)-'];
  async function cargar() {
    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante && CDI.despachante.sufijoDe);
    await page.evaluate(items => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = { numero_factura: 'INV-2026/0457', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026' };
      CDI.state.items = items;
      CDI.goTo('validating');
    }, ITEMS);
    await page.waitForFunction(() => {
      const s = document.querySelectorAll('.despachante-sufijo');
      return s.length === 4 && s[0].value;
    }, null, { timeout: 10000 }).catch(() => falla('no aparece el sufijo propuesto por producto'));
    let valores = await page.$$eval('.despachante-sufijo', s => s.map(x => x.value));
    const solos = propuestos.map(v => v.replace('CA00-', ''));
    if (JSON.stringify(valores) !== JSON.stringify(solos)) falla('sufijos propuestos sin el de la operación: ' + JSON.stringify(valores));
    // Se escribe el de la operación: las celdas que nadie escribió lo suman.
    await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
    valores = await page.$$eval('.despachante-sufijo', s => s.map(x => x.value));
    if (JSON.stringify(valores) !== JSON.stringify(propuestos)) falla('sufijos propuestos con el de la operación: ' + JSON.stringify(valores));
  }
  async function generar() {
    const pedida = page.waitForRequest('**/generate_maria', { timeout: 15000 }).catch(() => falla('no se pidió el TXT'));
    await page.click('#validatingGenerate');
    return JSON.parse((await pedida).postData()).items.map(i => [i.sufijo, i.unidad_estadistica]);
  }
  async function puedeGenerar() {
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
  }

  await cargar();
  console.log('OK se propone marca y código de cada producto junto con el de la operación (CA00 queda); la posición fuera del arancel queda vacía');

  const notas = await page.$$eval('.despachante-sufijo', s => s.map(x => (x.nextElementSibling && x.nextElementSibling.textContent) || ''));
  if (!notas[0].includes('Según el ' + FUENTE) || !notas[0].includes('unidad estadística 01')) falla('nota del producto 1: ' + notas[0]);
  if (!notas[2].includes('no está en el ' + FUENTE)) falla('nota del producto fuera del arancel: ' + notas[2]);
  console.log('OK cada nota dice de dónde sale: ' + notas[0]);

  // La persona corrige el segundo y borra el primero (va el de la operación).
  await page.fill('.despachante-sufijo[data-row="1"]', 'AA(OTRA)-AI(X1)-');
  await page.fill('.despachante-sufijo[data-row="0"]', '');
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

  await puedeGenerar();
  let s = await generar();
  if (JSON.stringify(s) !== JSON.stringify([[null, '01'], ['AA(OTRA)-AI(X1)-', '01'], [null, null], [propuestos[3], '01']]))
    falla('sufijo y estadística del pedido: ' + JSON.stringify(s));
  console.log('OK el pedido lleva el sufijo escrito, el de la operación donde se borró, el propuesto donde nadie escribió, y kilos donde la posición los pide');

  // Se borra el primer producto y se genera enseguida, con el arancel lento:
  // el que queda en cada lugar no se lleva la propuesta del que estaba antes.
  await cargar();
  await puedeGenerar();
  await page.route('**/api/sufijos/propuesta', async r => { await new Promise(f => setTimeout(f, 1500)); await r.continue(); });
  await page.evaluate(() => { CDI.state.items.splice(0, 1); });
  s = await generar();
  if (JSON.stringify(s) !== JSON.stringify([[propuestos[1], '01'], [null, null], [propuestos[3], '01']]))
    falla('después de borrar un producto, sufijo y estadística del pedido: ' + JSON.stringify(s));
  console.log('OK borrado un producto, cada uno va con su propia propuesta aunque el arancel tarde');
  await b.close();
  console.log('PANTALLA SUFIJOS-1 OK');
})().catch(e => falla(e && e.stack || e));
