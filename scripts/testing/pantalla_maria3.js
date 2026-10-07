// MARIA-3 en el navegador local, contra el servidor local (sin terceros).
// En la revisión se cargan la procedencia (Perú) y los gastos anteriores al
// FOB (150, EXW); la factura vino sin fecha. En la validación, antes de
// generar, aparecen los avisos (la fecha vacía, el banco) y se actualizan al
// cargar el banco. Sin fecha no se genera; con la fecha cargada el TXT sale
// con GTOS-ANT-FOB=150.00, procedencia 222 y esa fecha.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria3.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'm3_' + id, password: 'Clave-Inventada-123', email: 'm3' + id + '@ejemplo.test' } });

  const avisosPedidos = [];
  page.on('request', r => { if (r.url().endsWith('/generate_maria/avisos')) avisosPedidos.push(JSON.parse(r.postData())); });
  let generado = null;
  page.on('request', r => { if (r.url().endsWith('/generate_maria') && r.method() === 'POST') generado = 'pedido'; });

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante && CDI.paisesMaria);
  await page.evaluate(() => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = { numero_factura: 'F-M3', moneda: 'DOL', incoterm: 'EXW', fecha_emision: '', sbt_sufijo_valor: 'AA(1)-CA00' };
    CDI.state.items = [
      { pieza: '84714900100D', descripcion: 'Equipo importado de prueba', origen: 'CN', cantidad: 2, valor_unitario: 10, peso_unitario: 1 },
    ];
    CDI.goTo('review');
  });

  // Revisión: la procedencia acepta sólo países de la tabla.
  await page.waitForSelector('#f_procedencia', { state: 'visible', timeout: 10000 }).catch(() => falla('no aparece el campo de procedencia'));
  const opciones = await page.$$eval('#procedenciaPaises option', o => o.length);
  if (opciones < 200) falla('la lista de países de la procedencia tiene ' + opciones + ' opciones');
  await page.fill('#f_procedencia', 'Narnia');
  await page.locator('[data-error-for="procedencia"]', { hasText: 'no reconocido' }).waitFor({ timeout: 5000 }).catch(() => falla('acepta una procedencia que no es un país'));
  await page.fill('#f_procedencia', '222 · PERU');
  await page.waitForFunction(() => document.querySelector('[data-error-for="procedencia"]').hidden, null, { timeout: 5000 }).catch(() => falla('Perú se marca como no reconocido'));
  await page.fill('#f_gastos_anteriores_fob', '150');
  const reqFecha = await page.textContent('label[for="f_fecha_emision"]');
  if (!/requerido/.test(reqFecha)) falla('la fecha de emisión no figura como requerida en la revisión');
  await page.fill('#f_fecha_emision', '31/02/2026');
  await page.locator('[data-error-for="fecha_emision"]', { hasText: 'no válida' }).waitFor({ timeout: 5000 }).catch(() => falla('la revisión acepta el 31/02/2026'));
  await page.fill('#f_fecha_emision', '');
  console.log('OK la revisión pide la fecha y rechaza el 31/02/2026');
  console.log('OK procedencia: rechaza «Narnia» y acepta Perú; gastos anteriores 150 cargados');

  // Validación: los avisos están antes de generar.
  await page.evaluate(() => CDI.goTo('validating'));
  await page.locator('#validatingAvisosPanel', { hasText: 'Fecha de emisión' }).waitFor({ timeout: 10000 }).catch(() => falla('no aparece el aviso de la fecha antes de generar'));
  if (generado) falla('se generó el TXT antes de tocar el botón');
  const texto = await page.textContent('#validatingAvisosList');
  if (!/Banco: no se declaró/.test(texto)) falla('falta el aviso del banco antes de generar: ' + texto);
  if (/Procedencia:/.test(texto)) falla('avisa la procedencia aunque se cargó: ' + texto);
  if (/Gastos a FOB/.test(texto)) falla('avisa los gastos aunque se cargaron: ' + texto);
  const ultimo = avisosPedidos[avisosPedidos.length - 1] || {};
  if (ultimo.procedencia !== '222' || ultimo.gastos_anteriores_fob !== 150) falla('el pedido de avisos lleva ' + JSON.stringify([ultimo.procedencia, ultimo.gastos_anteriores_fob]));
  console.log('OK antes de generar se ven los avisos (fecha vacía, banco) y no los de lo que se cargó');
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });

  // Al cargar el banco en la tarjeta, el aviso del banco se va.
  await page.fill('#despachanteBanco', '191');
  await page.waitForFunction(() => !/Banco: no se declaró/.test(document.getElementById('validatingAvisosList').textContent), null, { timeout: 8000 })
    .catch(() => falla('al cargar el banco el aviso sigue'));
  console.log('OK al cargar el banco el aviso se actualiza');

  // Sin fecha no se genera: el servidor la pide (devolución de MARIA-3).
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');
  let respuesta = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
  await page.click('#validatingGenerate');
  const sinFecha = await respuesta.catch(() => falla('no se pidió el TXT'));
  if (sinFecha.status() !== 400) falla('sin fecha el servidor respondió ' + sinFecha.status());
  await page.locator('#readyErrorText', { hasText: 'fecha de emisión' }).waitFor({ timeout: 5000 }).catch(() => falla('sin fecha no se muestra que falta la fecha'));
  console.log('OK sin fecha no se genera y la pantalla pide la fecha de emisión');

  // Con la fecha cargada, se genera contra el servidor local.
  await page.evaluate(() => { CDI.state.operacion.fecha_emision = '22/06/2026'; CDI.goTo('validating'); });
  await page.waitForSelector('#validatingGenerate', { state: 'visible' });
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');
  respuesta = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
  await page.click('#validatingGenerate');
  generado = await (await respuesta.catch(() => falla('no se pidió el TXT'))).json().catch(() => null);
  if (!generado || !generado.content) falla('no se generó el TXT: ' + JSON.stringify(generado));
  const txt = generado.content.replace(/\r\n/g, '\n');
  if (!/CCPL=GTOS-ANT-FOB\s*\nMCPL=150\.00/.test(txt)) falla('el TXT no trae GTOS-ANT-FOB=150.00');
  if (!/CARTPAYPRC=222/.test(txt)) falla('el TXT no trae la procedencia 222');
  const fecha = txt.match(/CCPL=FECHAEMISIONFACT\nMCPL=(.*)/);
  if (!fecha || fecha[1].trim() !== '22/06/2026') falla('la fecha de emisión no es la cargada: ' + (fecha && fecha[1]));
  if (!/IEXT=[^\n]*\/26/.test(txt)) falla('el año del IEXT no sale de la fecha');
  console.log('OK el TXT sale con GTOS-ANT-FOB=150.00, procedencia 222, la fecha cargada y el año del IEXT de esa fecha');

  // Otra operación con la respuesta de avisos demorada: mientras tanto no se
  // ven los avisos de la anterior.
  await page.route('**/generate_maria/avisos', async r => { await new Promise(ok => setTimeout(ok, 3000)); await r.continue(); });
  await page.evaluate(() => { CDI.state.operacion = { numero_factura: 'F-M3B', moneda: 'DOL', incoterm: 'FOB', fecha_emision: '01/02/2026' }; CDI.goTo('validating'); });
  await page.waitForTimeout(300);  // dentro de la demora de 3 s: es el momento que se prueba
  if (await page.isVisible('#validatingAvisosPanel')) falla('mientras llega la respuesta se ven los avisos de la operación anterior');
  await page.waitForFunction(() => !document.getElementById('validatingAvisosPanel').hidden, null, { timeout: 10000 }).catch(() => falla('no llegan los avisos de la operación nueva'));
  if (/Fecha de emisión/.test(await page.textContent('#validatingAvisosList'))) falla('quedó el aviso de fecha de la operación anterior');
  console.log('OK con la respuesta demorada no se ven los avisos de la operación anterior');
  await b.close();
  console.log('OK: pantalla MARIA-3');
})().catch(e => falla(e.message));
