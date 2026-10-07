// MARIA-4 en el navegador local (sin terceros: /generate_maria se intercepta).
// En la pantalla de validación: un producto importado (estado 2 por defecto) y
// uno argentino (sin estado: no deja generar). Elegido el estado, el pedido a
// /generate_maria lleva banco, empresa, IVA y el estado de cada producto. Con
// un cliente que ya usó el banco 191, la pantalla lo propone.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria4.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'm4_' + id, password: 'Clave-Inventada-123', email: 'm4' + id + '@ejemplo.test' } });
  // Un cliente con una operación anterior que usó el banco 191.
  const rc = await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente M4', cuit: '30712345678' } });
  const cj = await rc.json(); const cliente = cj.cliente || cj;
  await page.request.post(base + '/api/clientes/' + cliente.id + '/operaciones', { data: {
    operation_id: 'ANT-1', source: 'pdf_v2', currency: 'USD',
    resumen: { items: 1, valor_total: 1, peso_total: 1, maria: { banco_bcra: '191', empresa_digitalizacion: 'PSAD01', iva_adicional: 'NO_VALIDA' } },
    items: [{ pieza: '84714900100D', descripcion: 'Anterior', origen: 'CN', cantidad: 1, valor_unitario: 1, peso_unitario: 1 }] } });

  let pedido = null;
  await page.route('**/generate_maria', async r => { pedido = JSON.parse(r.request().postData()); await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, filename: 'MARIA_X.TXT', download_url: '#', preview: '', supuestos: [] }) }); });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante);
  await page.evaluate((cl) => {
    CDI.setClienteActivo(cl);
    CDI.state.operacion = { numero_factura: 'F-M4', moneda: 'DOL', incoterm: 'FOB', sbt_sufijo_valor: 'AA(1)-CA00' };
    CDI.state.items = [
      { pieza: '84714900100D', descripcion: 'Equipo importado', origen: 'CN', cantidad: 1, valor_unitario: 10, peso_unitario: 1 },
      { pieza: '84714900100D', descripcion: 'Equipo argentino', origen: 'AR', cantidad: 1, valor_unitario: 10, peso_unitario: 1 },
    ];
    CDI.goTo('validating');
  }, cliente);

  await page.waitForFunction(() => document.querySelectorAll('.despachante-estado').length === 2, null, { timeout: 10000 }).catch(() => falla('no aparecen los estados por producto'));
  await page.waitForFunction(() => document.getElementById('despachanteBanco').value === '191', null, { timeout: 10000 }).catch(() => falla('no propone el último banco del cliente (191)'));
  const estados = await page.$$eval('.despachante-estado', s => s.map(x => x.value));
  if (estados[0] !== '2' || estados[1] !== '') falla('estados por defecto: ' + JSON.stringify(estados));
  console.log('OK estado 2 por defecto en el importado; el argentino sin estado; banco 191 propuesto');

  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');
  await page.click('#validatingGenerate');
  await page.locator('#despachanteError', { hasText: 'origen es argentino' }).waitFor({ timeout: 5000 }).catch(() => falla('genera sin estado con origen argentino'));
  if (pedido) falla('se pidió el TXT sin elegir el estado');
  console.log('OK sin estado en el argentino no se genera');
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });

  await page.selectOption('.despachante-estado[data-row="1"]', '3');
  await page.selectOption('#despachanteIva', 'IVAAD1');
  await page.click('#validatingGenerate');
  await page.waitForFunction(() => true);
  for (let i = 0; i < 50 && !pedido; i++) await page.waitForTimeout(100);
  if (!pedido) falla('no se pidió el TXT');
  const p = pedido;
  if (p.banco_bcra !== '191' || p.empresa_digitalizacion !== 'PSAD01' || p.iva_adicional !== 'IVAAD1') falla('operación: ' + JSON.stringify([p.banco_bcra, p.empresa_digitalizacion, p.iva_adicional]));
  if (String(p.items[0].estado) !== '2' || String(p.items[1].estado) !== '3') falla('estados: ' + JSON.stringify(p.items.map(i => i.estado)));
  console.log('OK el pedido lleva banco 191, Lakaut, uso particular y estados 2 y 3');
  await b.close();
  console.log('OK: pantalla MARIA-4');
})().catch(e => falla(e.message));
