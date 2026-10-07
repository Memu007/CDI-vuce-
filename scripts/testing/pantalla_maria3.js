// MARIA-3 en el navegador local, contra el servidor local (sin terceros).
// En la revisión se cargan la procedencia (Perú) y los gastos anteriores al
// FOB (150, EXW); la factura vino sin fecha. En la validación, antes de
// generar, aparecen los avisos (la fecha vacía, el banco) y se actualizan al
// cargar el banco. El TXT sale con GTOS-ANT-FOB=150.00, procedencia 222 y la
// fecha vacía (nunca la de hoy).
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
  page.on('response', async r => { if (r.url().endsWith('/generate_maria') && r.request().method() === 'POST') generado = await r.json().catch(() => null); });

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante && CDI.paisesMaria);
  await page.evaluate(() => {
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

  // Se genera contra el servidor local.
  await page.click('#validatingGenerate');
  for (let i = 0; i < 100 && !generado; i++) await page.waitForTimeout(100);
  if (!generado || !generado.content) falla('no se generó el TXT: ' + JSON.stringify(generado));
  const txt = generado.content.replace(/\r\n/g, '\n');
  if (!/CCPL=GTOS-ANT-FOB\s*\nMCPL=150\.00/.test(txt)) falla('el TXT no trae GTOS-ANT-FOB=150.00');
  if (!/CARTPAYPRC=222/.test(txt)) falla('el TXT no trae la procedencia 222');
  const fecha = txt.match(/CCPL=FECHAEMISIONFACT\nMCPL=(.*)/);
  if (!fecha || fecha[1].trim() !== '') falla('la fecha de emisión no sale vacía: ' + (fecha && fecha[1]));
  console.log('OK el TXT sale con GTOS-ANT-FOB=150.00, procedencia 222 y la fecha vacía');
  await b.close();
  console.log('OK: pantalla MARIA-3');
})().catch(e => falla(e.message));
