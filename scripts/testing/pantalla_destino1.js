// DESTINO-1 en el navegador local (sin terceros: /generate_maria se intercepta).
// En la pantalla de validación, el destino de la mercadería ofrece los tres de
// la tabla del despachante, por operación y por producto; un IVAAD1 que ya
// estaba elegido se muestra como «Bien de uso de una persona»; y lo que se
// elige viaja en el pedido a /generate_maria (el servidor saca GANANCIASOP3).
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_destino1.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const TRES = [
  ['NO_VALIDA', 'Comercialización o reventa'],
  ['IVAAD2', 'Bien de uso de la empresa'],
  ['IVAAD1', 'Bien de uso de una persona'],
];
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: 'd1_' + id, password: 'Clave-Inventada-123', email: 'd1' + id + '@ejemplo.test' } });
  const rc = await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente D1', cuit: '30712345678' } });
  const cj = await rc.json(); const cliente = cj.cliente || cj;

  let pedido;
  await page.route('**/generate_maria', async r => { await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, filename: 'MARIA_X.TXT', download_url: '#', preview: '', supuestos: [] }) }); });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante);
  // La operación ya tenía elegido IVAAD1 (el «uso particular» de antes); los
  // productos, ninguno.
  await page.evaluate((cl) => {
    CDI.setClienteActivo(cl);
    CDI.state.operacion = { numero_factura: 'F-D1', moneda: 'DOL', incoterm: 'FOB', sbt_sufijo_valor: 'AA(1)-CA00',
      comprador_cuit: '30712345671', despachante: { iva_adicional: 'IVAAD1' } };
    CDI.state.items = [
      { pieza: '84714900100D', descripcion: 'Equipo uno', origen: 'CN', cantidad: 1, valor_unitario: 10, peso_unitario: 1 },
      { pieza: '84714900100D', descripcion: 'Equipo dos', origen: 'CN', cantidad: 1, valor_unitario: 10, peso_unitario: 1 },
    ];
    CDI.goTo('validating');
  }, cliente);
  await page.waitForFunction(() => document.querySelectorAll('.despachante-iva').length === 2, null, { timeout: 10000 })
    .catch(() => falla('no aparece el destino por producto'));

  const deLaOperacion = await page.$$eval('#despachanteIva option', o => o.map(x => [x.value, x.textContent]));
  if (JSON.stringify(deLaOperacion) !== JSON.stringify(TRES)) falla('opciones de la operación: ' + JSON.stringify(deLaOperacion));
  const delProducto = await page.$$eval('.despachante-iva[data-row="0"] option', o => o.map(x => [x.value, x.textContent]));
  if (JSON.stringify(delProducto) !== JSON.stringify([['', 'Igual que la operación']].concat(TRES))) falla('opciones del producto: ' + JSON.stringify(delProducto));
  console.log('OK los tres destinos de la tabla, por operación y por producto');

  const mostrado = await page.$eval('#despachanteIva', s => s.options[s.selectedIndex].textContent);
  if (mostrado !== 'Bien de uso de una persona') falla('el IVAAD1 elegido se muestra como: ' + mostrado);
  const etiqueta = await page.$eval('#despachanteIva', s => s.closest('label').textContent.trim().split('\n')[0].trim());
  if (etiqueta !== 'Destino de la mercadería') falla('etiqueta: ' + etiqueta);
  console.log('OK el IVAAD1 ya elegido se muestra como «Bien de uso de una persona»');
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });

  // La operación pasa a bien de uso de la empresa; el segundo producto se revende.
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');
  await page.selectOption('#despachanteIva', 'IVAAD2');
  await page.selectOption('.despachante-iva[data-row="1"]', 'NO_VALIDA');
  await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
    .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
  const [req] = await Promise.all([
    page.waitForRequest('**/generate_maria', { timeout: 8000 }).catch(() => falla('no se pidió el TXT')),
    page.click('#validatingGenerate'),
  ]);
  pedido = JSON.parse(req.postData());
  if (pedido.iva_adicional !== 'IVAAD2') falla('operación: ' + pedido.iva_adicional);
  const porItem = pedido.items.map(i => i.iva_adicional == null ? null : i.iva_adicional);
  if (JSON.stringify(porItem) !== JSON.stringify([null, 'NO_VALIDA'])) falla('por producto: ' + JSON.stringify(porItem));
  console.log('OK el pedido lleva IVAAD2 en la operación, el primero sin cambio y el segundo NO_VALIDA');
  await b.close();
  console.log('OK: pantalla DESTINO-1');
})().catch(e => falla(e.message));
