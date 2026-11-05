// COBRO-MP-1 vuelta 2, g: la pantalla v1 (/dashboard?v=1) cuenta una sola
// operación por MARIA con cliente elegido. Antes guardaba el historial con
// «GROUPED_<hora>» antes de generar: eso contaba una operación y el MARIA
// otra. Ahora guarda después de generar, con el archivo que devolvió el
// servidor, y si la generación falla no guarda nada.
// Las respuestas de generar se fuerzan con page.route: las pruebas del
// servidor (tests/test_cobro_corte1.py) cubren cuánto cuenta cada pedido.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_cobro_mp1_v2.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const reg = await page.request.post(base + '/auth/register', { data: { username: 'cmp1v_' + id, password: 'Clave-Inventada-123', email: 'cmp1v' + id + '@ejemplo.test' } });
  if (!reg.ok()) falla('no se pudo registrar: ' + reg.status());
  // La v1 manda a la portada si no encuentra el token en localStorage.
  const token = (await reg.json()).access_token;
  if (!token) falla('el registro no devolvió access_token');
  await page.addInitScript(t => localStorage.setItem('access_token', t), token);
  const cli = await page.request.post(base + '/api/clientes', { data: { nombre: 'Importadora Inventada', cuit: '30999999995' } });
  if (!cli.ok()) falla('no se pudo crear el cliente: ' + cli.status());
  const clienteId = String((await cli.json()).cliente.id);
  page.on('dialog', d => d.accept());

  // Lo que pasa por la red, en orden: «generar <ruta>» y «guardar <operation_id>».
  let pasos = [];
  await page.route('**/api/clientes/*/operaciones', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    pasos.push('guardar ' + JSON.parse(route.request().postData()).operation_id);
    route.fulfill({ status: 200, contentType: 'application/json', body: '{"success": true}' });
  });
  let respuesta;
  for (const ruta of ['/generate_maria', '/generate_maria_export']) {
    await page.route('**' + ruta, route => {
      pasos.push('generar ' + ruta);
      route.fulfill(respuesta(ruta));
    });
  }
  const bien = ruta => ({ status: 200, contentType: 'application/json',
    body: JSON.stringify({ filename: ruta === '/generate_maria' ? 'MARIA_FAC_V1.TXT' : 'MARIA-EXPORT_FAC_V1.TXT',
                           content: 'CDDTINCOTE=FOB\r\n', warnings: [], supuestos: [] }) });

  await page.goto(base + '/dashboard?v=1');
  await page.waitForFunction(() => typeof generateMariaTxt === 'function' && typeof displayItemsForGrouping === 'function');
  await page.waitForFunction(id => [...document.querySelectorAll('#clientSelectorGrouping option')].some(o => o.value === id),
                             clienteId, { timeout: 10000 }).catch(() => falla('el cliente no aparece en el selector'));
  await page.evaluate(id => {
    document.getElementById('groupingSection').classList.remove('hidden');
    document.getElementById('clientSelectorGrouping').value = id;
    window.currentItems = [{ pieza: '39219019900Z', codigo_parte: 'L1', descripcion: 'Lona de PVC gris 620 g',
                             cantidad: 750, valor_unitario: 1.85, peso_unitario: 0.62, origen: 'CN' }];
    displayItemsForGrouping(window.currentItems, { '3921': window.currentItems });
    document.getElementById('op_numero_factura').value = 'FAC_V1';
  }, clienteId);

  async function generar(tipo) {
    pasos = [];
    await page.evaluate(t => { document.querySelector(`input[name="operationType"][value="${t}"]`).checked = true; }, tipo);
    await page.evaluate(() => generateMariaTxt());
    return pasos.join(' → ');
  }

  // Importación y exportación: primero se genera y después se guarda con el archivo devuelto.
  respuesta = bien;
  for (const [tipo, ruta, archivo] of [['import', '/generate_maria', 'MARIA_FAC_V1.TXT'],
                                       ['export', '/generate_maria_export', 'MARIA-EXPORT_FAC_V1.TXT']]) {
    const visto = await generar(tipo);
    const esperado = 'generar ' + ruta + ' → guardar ' + archivo;
    if (visto !== esperado) falla(tipo + ': la pantalla hizo «' + visto + '» y tenía que hacer «' + esperado + '»');
    console.log('OK | ' + tipo + ': ' + visto);
  }

  // Si la generación falla, no guarda: guardar sin MARIA contaría una operación sin archivo.
  respuesta = () => ({ status: 400, contentType: 'application/json', body: '{"detail": "Falta el CUIT del comprador"}' });
  const visto = await generar('import');
  if (visto !== 'generar /generate_maria') falla('con la generación rechazada la pantalla hizo «' + visto + '»');
  console.log('OK | generación rechazada: ' + visto);

  await b.close();
})().catch(e => falla(e.stack || e));
