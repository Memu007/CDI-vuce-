// MARIA-5 en el navegador local, contra el servidor local (sin terceros).
// Una operación con 10 notebooks de 2,5 kg y dos productos más, flete 10 y
// seguro 10. La validación muestra el peso total y el valor; el TXT que sale
// de la pantalla declara el mismo peso (25 kg) y el mismo FOB, y sus cuentas
// cierran al centavo (el flete de los ítems suma 10,00).
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria5.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const centavos = s => Math.round(parseFloat(s) * 100);
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'm5_' + id, password: 'Clave-Inventada-123', email: 'm5' + id + '@ejemplo.test' } });

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante);
  await page.evaluate(() => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = { numero_factura: 'None', moneda: 'DOL', incoterm: 'CIF', fecha_emision: '22/06/2026',
                            flete: 10, seguro: 10, sbt_sufijo_valor: 'AA(1)-CA00' };
    CDI.state.items = [
      { pieza: '84713012100F', descripcion: 'Notebook importada de prueba', origen: 'CN', cantidad: 10, valor_unitario: 10, peso_unitario: 2.5 },
      { pieza: '84713012100F', descripcion: 'Notebook importada de prueba B', origen: 'CN', cantidad: 1, valor_unitario: 100, peso_unitario: 1 },
      { pieza: '84714900100D', descripcion: 'Equipo importado de prueba', origen: 'CN', cantidad: 4, valor_unitario: 100, peso_unitario: 0.5 },
    ];
    CDI.goTo('validating');
  });

  await page.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 }).catch(() => falla('no aparece la validación'));
  await page.locator('text=Peso total').first().waitFor({ timeout: 10000 }).catch(() => falla('no aparece el peso total en la validación'));
  const tarjetas = await page.evaluate(() => document.body.innerText);
  if (!/28[.,]0?0? kg/.test(tarjetas.replace(/\s+/g, ' ')) && !/\b28 kg/.test(tarjetas)) falla('la validación no muestra 28 kg de peso total');
  console.log('OK la validación muestra el peso total: 25 + 1 + 2 = 28 kg');
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });

  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');
  const respuesta = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
  await page.click('#validatingGenerate');
  const r = await respuesta.catch(() => falla('no se pidió el TXT'));
  const pedido = JSON.parse(r.request().postData());
  if (/none/i.test(pedido.operation_id)) falla('la pantalla manda el número de operación ' + pedido.operation_id);
  const generado = await r.json().catch(() => null);
  if (!generado || !generado.content) falla('no se generó el TXT: ' + JSON.stringify(generado));
  if (/none/i.test(generado.filename)) falla('el archivo se llama ' + generado.filename);
  const txt = generado.content;
  const campo = c => [...txt.matchAll(new RegExp('^' + c + '=(\\S+)', 'gm'))].map(m => m[1]);
  const pesos = campo('QARTKGRNET');
  if (pesos[0] !== '25.000') falla('las 10 notebooks de 2,5 kg declaran ' + pesos[0]);
  console.log('OK el TXT declara 25 kg para 10 × 2,5 kg (pesos: ' + pesos.join(', ') + ')');
  for (const [item, cab] of [['MARTFOB', 'MDDTFOB'], ['MARTFLE', 'MDDTFLE'], ['MARTASS', 'MDDTASS']]) {
    const suma = campo(item).reduce((a, v) => a + centavos(v), 0);
    if (suma !== centavos(campo(cab)[0])) falla(item + ' suma ' + suma / 100 + ' y ' + cab + ' es ' + campo(cab)[0]);
  }
  if (campo('MDDTFLE')[0] !== '10.00') falla('el flete de la carátula es ' + campo('MDDTFLE')[0]);
  console.log('OK las cuentas cierran al centavo: flete por ítem ' + campo('MARTFLE').join(' + ') + ' = 10.00');
  await b.close();
  console.log('OK: pantalla MARIA-5');
})().catch(e => falla(e.message));
