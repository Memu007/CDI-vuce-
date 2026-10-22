// SUBITEMS-1 en el navegador local, contra el servidor local (sin terceros).
// El producto del archivo real con subítems (6 equipos de 1197, 33 kg) se
// parte en el panel de subítems del paso de NCM en 2 + 4, con sus sufijos de
// valor. El panel dice si suman; un subítem en 0 da el error con su número;
// un producto con subítems no se agrupa. El TXT que sale de la pantalla trae
// los dos [SBT] del archivo real (salvo el número de operación). El error de
// un subítem sale bajo ese subítem, y el panel hace la misma cuenta que el
// servidor.
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

  // Revisión adversaria: la suma sigue al producto, y una cantidad con más
  // de dos decimales se marca (el TXT la declara con dos).
  await page.fill('input[data-row="0"][data-field="cantidad"]', '10');
  if (!/⚠ Suman 6 de 10/.test(await suma.innerText())) falla('cambiar la cantidad del producto no actualiza la suma: ' + await suma.innerText());
  await page.fill('input[data-row="0"][data-field="cantidad"]', '6');
  await page.locator('input[data-row="0"][data-field="cantidad"]').blur();
  await page.fill(campo(0, 'cantidad'), '1.996');
  await page.fill(campo(1, 'cantidad'), '4.004');
  if (!/⚠/.test(await suma.innerText()) || !/dos decimales/.test(await suma.innerText())) falla('una cantidad de tres decimales no se marca: ' + await suma.innerText());
  await page.fill(campo(0, 'cantidad'), '2');
  await page.fill(campo(1, 'cantidad'), '4');
  console.log('OK la suma sigue a la cantidad del producto y marca una cantidad de tres decimales');

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

  // Borrar y volver a cargar deja lo mismo. Antes, una acción masiva
  // (×2 en el otro producto): deshacerla no resucita el subítem borrado.
  await page.check('[data-row-check="1"]');
  await page.fill('#ncmBatchFactor', '2');
  await page.click('#ncmBatchApplyQty');
  await page.click('[data-sub-borrar="0"][data-sub-idx="1"]');
  if ((await page.evaluate(() => CDI.state.items[0].subitems.length)) !== 1) falla('borrar no saca el subítem');
  await page.locator('body').click({ position: { x: 5, y: 300 } });
  await page.keyboard.press('Control+z');
  if ((await page.evaluate(() => CDI.state.items[0].subitems.length)) !== 1) falla('deshacer la acción masiva resucitó el subítem borrado');
  console.log('OK deshacer una acción masiva no pisa los subítems');
  await page.click('[data-sub-agregar="0"]');
  await page.fill(campo(1, 'sufijo'), SUF_B);
  await page.evaluate(() => { CDI.state.items.splice(1, 1); });

  // Generar desde la pantalla.
  await page.evaluate(() => CDI.goTo('validating'));
  await page.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 }).catch(() => falla('no aparece la validación'));
  // Todos los subítems traen su sufijo: el general puede quedar vacío.
  await page.fill('#sbtSufijoValor', '');
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

  // Devolución, punto 10: el error del sufijo de un subítem sale bajo ese
  // subítem, no bajo el sufijo general; al corregirlo se va.
  await page.evaluate(() => { CDI.goTo('ncm'); const s = CDI.state.items[0].subitems; s[0].cantidad = 2; s[1].cantidad = 4; s[1].sufijo = 'CSBTSVL=S2'; CDI.goTo('validating'); });
  await page.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 });
  const conIgual = await generar();
  if (conIgual.status() !== 400) falla('un sufijo con «=» no da 400: ' + conIgual.status());
  const bajoElSubitem = page.locator('[data-sub-error="0"][data-sub-idx="1"]');
  await bajoElSubitem.waitFor({ state: 'visible', timeout: 5000 }).catch(() => falla('el error del sufijo no sale bajo el subítem 2'));
  if (!/sub-ítem 2/.test(await bajoElSubitem.innerText())) falla('el error bajo el subítem no es el suyo: ' + await bajoElSubitem.innerText());
  if (await page.locator('#sbtFieldError').isVisible() && /sub-ítem/.test(await page.locator('#sbtFieldError').innerText()))
    falla('el error del subítem sale bajo el sufijo general');
  await page.fill(campo(1, 'sufijo'), SUF_B);
  if (await bajoElSubitem.count()) falla('corregir el sufijo no saca el error');
  // Revisión adversaria: el error es de un subítem en su lugar; borrar o
  // agregar uno lo saca (si no, quedaba sobre otra fila).
  await page.evaluate(() => CDI.ncmBatch.marcarErrorDeSubitem(0, 1, 'Item 1, sub-ítem 2: error de prueba'));
  await page.evaluate(() => { CDI.goTo('validating'); CDI.goTo('ncm'); });
  await bajoElSubitem.waitFor({ state: 'visible', timeout: 5000 });
  await page.click('[data-sub-agregar="0"]');
  if (await page.locator('[data-sub-error="0"]').count()) falla('agregar un subítem deja el error sobre otra fila');
  await page.click('[data-sub-borrar="0"][data-sub-idx="2"]');
  await page.evaluate(() => CDI.ncmBatch.marcarErrorDeSubitem(0, 1, 'Item 1, sub-ítem 2: error de prueba'));
  await page.evaluate(() => { CDI.goTo('validating'); CDI.goTo('ncm'); });
  await page.click('[data-sub-borrar="0"][data-sub-idx="0"]');
  if (await page.locator('[data-sub-error="0"]').count()) falla('borrar un subítem deja el error sobre otra fila');
  await page.click('[data-sub-agregar="0"]');
  await page.fill(campo(0, 'cantidad'), '2');
  await page.fill(campo(1, 'cantidad'), '4');
  await page.fill(campo(0, 'sufijo'), SUF_A);
  await page.fill(campo(1, 'sufijo'), SUF_B);
  console.log('OK el error del sufijo de un subítem sale bajo el subítem 2 y se va al corregirlo');

  // Devolución, puntos 8 y 9: el panel hace la misma cuenta que el servidor
  // (decimal exacto, 0,01 de tolerancia) y muestra las cantidades con sus
  // decimales.
  const casos = [
    [1, 6.32, [[1, 6.33]]],                 // 0,01 justo: el servidor genera
    [1, 0.03, [[1, 0.04]]],                 // 0,01 justo; en float, 0,010000000000000002
    [2, 0.015, [[2, 0.02]]],
    [1, 6.32, [[1, 6.3301]]],               // 0,0101: el servidor da 400
    [1, 6.33, [[1, 6.32]]],
    [3, 3.335, [[1, 3.335], [2, 3.34]]],    // 10,005 contra 10,015
    [19, 0.333, [[10, 0.333], [9, 0.334]]],
    [10, 0.7, [[3, 0.71], [7, 0.69]]],
    [3, 1, [[1.5, 1], [1.4, 1]]],           // 2,9 de 3 unidades
  ];
  for (const [cant, unit, partes] of casos) {
    await page.evaluate(([cant, unit, partes]) => {
      CDI.goTo('ncm');
      CDI.state.items = [{ pieza: '84714900100D', descripcion: 'Equipo de demostracion para prueba', origen: 'CN', cantidad: cant,
        valor_unitario: unit, peso_unitario: 1, estado: '2', subitems: partes.map(([c, v]) => ({ cantidad: c, valor_unitario: v, sufijo: '' })) }];
      CDI.goTo('validating'); CDI.goTo('ncm');
    }, [cant, unit, partes]);
    await page.click('[data-subitems="0"]');
    const texto = await page.locator('[data-sub-suma="0"]').innerText();
    const r = await page.evaluate(async ([cant, unit, partes]) => {
      const res = await CDI.api('/generate_maria', { method: 'POST', body: JSON.stringify({
        operation_id: 'OP1', fecha_emision: '22/06/2026', sbt_sufijo_valor: 'AA(DemoPouchs)-CA00-', moneda: 'DOL', incoterm: 'EXW',
        comprador_cuit: '30999999995', items: [{ pieza: '84714900100D', descripcion: 'Equipo de demostracion para prueba', origen: 'CN',
          cantidad: cant, valor_unitario: unit, peso_unitario: 1, estado: '2',
          subitems: partes.map(([c, v]) => ({ cantidad: c, valor_unitario: v })) }] }) });
      return { status: res.status, cuerpo: await res.text() };
    }, [cant, unit, partes]);
    const panelOk = texto.startsWith('✓');
    if (panelOk !== (r.status === 200)) falla('el panel y el servidor no coinciden con ' + JSON.stringify([cant, unit, partes]) + ': «' + texto + '» contra ' + r.status + ' ' + r.cuerpo.slice(0, 200));
    if (!panelOk && !/no suman|Revisá el subítem/.test(texto)) falla('el aviso no dice qué falla: ' + texto);
  }
  const decimales = await page.locator('[data-sub-suma="0"]').innerText();
  if (!/Suman 2,9 de 3 unidades/.test(decimales) || !/cantidades/.test(decimales)) falla('la suma no muestra las cantidades con sus decimales: ' + decimales);
  console.log('OK el panel y el servidor coinciden en ' + casos.length + ' casos del borde; «' + decimales + '»');
  await b.close();
  console.log('OK: pantalla SUBITEMS-1');
})().catch(e => falla(e.message));
