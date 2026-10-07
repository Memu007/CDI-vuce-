// SUBITEMS-1 en el navegador local, contra el servidor local (sin terceros).
// El producto del archivo real con subítems (6 equipos de 1197, 33 kg) se
// parte en el panel de subítems del paso de NCM en 2 + 4, con sus sufijos de
// valor. El panel dice si suman; un subítem en 0 da el error con su número;
// un producto con subítems no se agrupa. El TXT que sale de la pantalla trae
// los dos [SBT] del archivo real (salvo el número de operación).
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_subitems1.js [captura.png]
const fs = require('fs');
const path = require('path');
const { chromium } = require('/opt/node-tools/node_modules/playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const SUF_A = 'AA(DemoPouchs)-AB(MODELO-A 001)-ZA(016384)-ZB(004400)-ZC(000256)-ZD(000001)-CA00-NA00-NB00-NC01-ND01-NE00-NF01-';
const SUF_B = SUF_A.replace('MODELO-A 001', 'MODELO-B 002');
const REAL = fs.readFileSync(path.join(__dirname, '..', '..', 'tests', 'fixtures', 'maria_golden_subitems_anon.TXT'), 'utf8');
const bloquesSbt = txt => txt.replace(/\r\n/g, '\n').split('\n\n').filter(b => b.startsWith('[SBT]'))
  .map(b => b.split('\n').filter(l => l && !l.startsWith('IDDT=')).map(l => l.trimEnd()).join('\n'));

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'sub1_' + id, password: 'Clave-Inventada-123', email: 'sub1' + id + '@ejemplo.test' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api);
  await page.evaluate(() => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = { numero_factura: '110', moneda: 'DOL', incoterm: 'EXW', fecha_emision: '22/06/2026',
                            flete: 365, seguro: 75.47, comprador_cuit: '30999999995', comprador_nombre: 'IMPORTADORA DEMO S.A.',
                            vendedor_nombre: 'PROVEEDOR DEMO', aduana_codigo: '073' };
    CDI.state.items = [
      { pieza: '84714900100D', descripcion: 'Equipo de demostracion para prueba', origen: 'CN', cantidad: 6, valor_unitario: 1197, peso_unitario: 5.5, estado: '2' },
      { pieza: '84714900100D', descripcion: 'Otro equipo de demostracion', origen: 'CN', cantidad: 1, valor_unitario: 10, peso_unitario: 1, estado: '2' },
    ];
    CDI.goTo('ncm');
  });

  // El panel: dos subítems con la cantidad que falta propuesta.
  await page.click('[data-subitems="0"]').catch(() => falla('no aparece el botón «Subítems» del producto'));
  await page.locator('[data-subitems-panel="0"]', { hasText: 'Sin subítems' }).waitFor({ timeout: 5000 })
    .catch(() => falla('no se abre el panel de subítems'));
  const campo = (k, f) => '[data-sub-row="0"][data-sub-idx="' + k + '"][data-sub-field="' + f + '"]';
  await page.click('[data-sub-agregar="0"]');
  if ((await page.inputValue(campo(0, 'cantidad'))) !== '6') falla('el primer subítem no propone la cantidad del producto');
  await page.fill(campo(0, 'cantidad'), '2');
  await page.fill(campo(0, 'sufijo'), SUF_A);
  await page.click('[data-sub-agregar="0"]');
  if ((await page.inputValue(campo(1, 'cantidad'))) !== '4') falla('el segundo subítem no propone la cantidad que falta (4)');
  await page.fill(campo(1, 'sufijo'), SUF_B);
  const suma = page.locator('[data-sub-suma="0"]');
  if (!/✓ Suman 6 de 6 unidades y 7\.182,00 de 7\.182,00/.test(await suma.innerText())) falla('la suma no cierra: ' + await suma.innerText());
  console.log('OK el panel carga 2 + 4 subítems y dice que suman: ' + await suma.innerText());

  // Un subítem en 0 se ve en el panel.
  await page.fill(campo(1, 'cantidad'), '0');
  if (!/⚠/.test(await suma.innerText()) || !(await suma.evaluate(el => el.classList.contains('is-error')))) falla('un subítem en 0 no se marca: ' + await suma.innerText());
  await page.fill(campo(1, 'cantidad'), '4');
  console.log('OK un subítem en 0 se marca en el panel');
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: false });

  // Un producto con subítems no se agrupa.
  const grupo = await page.evaluate(() => CDI.ncmBatch.applyNcmAndGroup(CDI.state.items, new Set([0, 1]), '8471.49.00.100D'));
  if (grupo.ok || !/subítems/.test(grupo.title)) falla('un producto con subítems se agrupó: ' + JSON.stringify(grupo));
  console.log('OK un producto con subítems no se agrupa: ' + grupo.title);

  // Borrar y volver a cargar deja lo mismo.
  await page.click('[data-sub-borrar="0"][data-sub-idx="1"]');
  if ((await page.evaluate(() => CDI.state.items[0].subitems.length)) !== 1) falla('borrar no saca el subítem');
  await page.click('[data-sub-agregar="0"]');
  await page.fill(campo(1, 'sufijo'), SUF_B);
  await page.evaluate(() => { CDI.state.items.splice(1, 1); });

  // Generar desde la pantalla.
  await page.evaluate(() => CDI.goTo('validating'));
  await page.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 }).catch(() => falla('no aparece la validación'));
  await page.fill('#sbtSufijoValor', 'AA(DemoPouchs)-CA00-');
  const generar = async () => {
    const resp = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
    await page.click('#validatingGenerate');
    return resp.catch(() => falla('no se pidió el TXT'));
  };
  const r = await generar();
  const pedido = JSON.parse(r.request().postData());
  const datos = await r.json().catch(() => null);
  if (!datos || !datos.content) falla('no se generó el TXT: ' + JSON.stringify(datos) + ' · subitems: ' + JSON.stringify(pedido.items[0].subitems));
  const txt = datos.content;
  if (!/^CARTSBITEM=S/m.test(txt)) falla('el TXT no declara el ítem partido');
  const esperado = bloquesSbt(REAL), obtenido = bloquesSbt(txt);
  if (JSON.stringify(obtenido) !== JSON.stringify(esperado)) falla('los [SBT] no son los del archivo real:\n' + obtenido.join('\n\n') + '\n---\n' + esperado.join('\n\n'));
  for (const c of ['QARTKGRNET=33.000', 'MARTFOB=7182.00', 'QARTUNTDCL=6.00']) if (!txt.includes(c)) falla('falta ' + c);
  console.log('OK el TXT de la pantalla trae los dos [SBT] del archivo real (2394,00 y 4788,00 con sus sufijos)');

  // El error del servidor dice qué subítem falla.
  await page.evaluate(() => { CDI.goTo('ncm'); CDI.state.items[0].subitems[1].cantidad = -1; CDI.state.items[0].subitems[0].cantidad = 7; CDI.goTo('validating'); });
  await page.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 });
  await page.fill('#sbtSufijoValor', 'AA(DemoPouchs)-CA00-');
  const malo = await generar();
  const cuerpo = await malo.text();
  if (malo.status() !== 400 || !/sub-ítem 2/.test(cuerpo)) falla('el error no dice qué subítem falla: ' + malo.status() + ' ' + cuerpo);
  await page.locator('text=sub-ítem 2').first().waitFor({ timeout: 5000 }).catch(() => falla('la pantalla no muestra el error del subítem'));
  console.log('OK un subítem con cantidad -1 da «' + JSON.parse(cuerpo).detail + '» y la pantalla lo muestra');
  await b.close();
  console.log('OK: pantalla SUBITEMS-1');
})().catch(e => falla(e.message));
