// COBRO-MP-1 vuelta 2, g: la pantalla Listo de la v2 cuenta una sola
// operación por MARIA con cliente elegido: pide /generate_maria y recién
// después guarda la operación en el historial del cliente, con el archivo que
// devolvió el servidor; si la generación falla, no guarda nada. Hasta el
// 2026-11-05 esto se medía en la pantalla v1, que se retiró.
// Las respuestas de generar y de guardar se fuerzan con page.route: las
// pruebas del servidor (tests/test_cobro_corte1.py) cubren cuánto cuenta cada pedido.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_cobro_mp1_v2.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const OP = { moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671', fecha_emision: '10/10/2026', numero_factura: 'FAC_V2' };
const LONA = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  const reg = await page.request.post(base + '/auth/register', { data: { username: 'cmp1v_' + id, password: 'Clave-Inventada-123', email: 'cmp1v' + id + '@ejemplo.test' } });
  if (!reg.ok()) falla('no se pudo registrar: ' + reg.status());
  // Sin el CUIT del despachante no se genera el TXT (ESTUDIO-1); inventado.
  const perfil = await page.request.put(base + '/api/user/profile', { data: { cuit: '20999999998' } });
  if (!perfil.ok()) falla('no se pudo cargar el CUIT del perfil: ' + perfil.status());
  const cli = await page.request.post(base + '/api/clientes', { data: { nombre: 'Importadora Inventada', cuit: '30999999995' } });
  if (!cli.ok()) falla('no se pudo crear el cliente: ' + cli.status());
  const cliente = (await cli.json()).cliente;
  page.on('dialog', d => d.accept());

  // Lo que pasa por la red, en orden: «generar <ruta>» y «guardar <operation_id>».
  let pasos = [];
  await page.route('**/api/clientes/*/operaciones', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    pasos.push('guardar ' + JSON.parse(route.request().postData()).operation_id);
    route.fulfill({ status: 200, contentType: 'application/json', body: '{"success": true}' });
  });
  let respuesta;
  await page.route('**/generate_maria', route => { pasos.push('generar /generate_maria'); route.fulfill(respuesta()); });
  const bien = () => ({ status: 200, contentType: 'application/json',
    body: JSON.stringify({ success: true, filename: 'MARIA_FAC_V2.TXT', download_url: '#',
                           content: 'CDDTINCOTE=FOB\r\n', warnings: [], supuestos: [] }) });
  const guardo = () => pasos.some(p => p.startsWith('guardar'));

  // Carga la operación con el cliente elegido, pide el TXT desde «Generar» y
  // devuelve lo que la pantalla hizo por la red, en orden.
  async function generar() {
    pasos = [];
    await page.goto(base + '/dashboard');
    // El arranque elige su pantalla sin esperar: hasta que lo hace, pisaría la de la prueba.
    await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && CDI.setClienteActivo && document.querySelector('.screen.is-active'));
    await page.evaluate(([op, item, cl]) => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = op;
      CDI.state.items = [item];
      CDI.state.uploadedAt = new Date().toISOString();
      CDI.state.operationSavedFor = null;
      CDI.setClienteActivo(cl);
      CDI.goTo('validating');
    }, [OP, LONA, cliente]);
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(async () => falla('no deja generar: ' + await page.$eval('#validatingIssues', el => el.textContent.trim().slice(0, 400))));
    await page.fill('#sbtSufijoValor', 'AA(1)-CA00-');
    await page.click('#validatingGenerate');
    // Listo termina con el archivo a la vista o con su error.
    await page.waitForFunction(() => {
      const ok = document.getElementById('readyFilename'), err = document.getElementById('readyErrorText');
      return (ok && ok.offsetParent !== null && ok.textContent.trim()) || (err && err.offsetParent !== null && err.textContent.trim());
    }, null, { timeout: 15000 }).catch(() => falla('Listo no terminó ni con el archivo ni con un error'));
    // El guardado sale después de mostrar el archivo: se le da un momento, y
    // el mismo momento sirve para ver que con un rechazo no guarda nada.
    for (let i = 0; i < 30 && !guardo(); i++) await page.waitForTimeout(100);
    return pasos.join(' → ');
  }

  // Primero se genera y después se guarda con el archivo devuelto.
  respuesta = bien;
  const visto = await generar();
  const esperado = 'generar /generate_maria → guardar MARIA_FAC_V2.TXT';
  if (visto !== esperado) falla('import: la pantalla hizo «' + visto + '» y tenía que hacer «' + esperado + '»');
  console.log('OK | import: ' + visto);

  // Si la generación falla, no guarda: guardar sin MARIA contaría una operación sin archivo.
  respuesta = () => ({ status: 400, contentType: 'application/json', body: '{"detail": "Falta el CUIT del comprador"}' });
  const rechazada = await generar();
  if (rechazada !== 'generar /generate_maria') falla('con la generación rechazada la pantalla hizo «' + rechazada + '»');
  console.log('OK | generación rechazada: ' + rechazada);

  await b.close();
})().catch(e => falla(e.stack || e));
