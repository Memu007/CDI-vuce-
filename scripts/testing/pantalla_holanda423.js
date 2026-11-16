// Holanda→423 en el navegador local, contra el servidor local (sin terceros).
// Un origen guardado o escrito con el código 434 se ve como el 423 que sale en
// el TXT: en el catálogo del proveedor, en el del cliente y en la procedencia de
// la revisión. Los nombres y los demás países se ven como se guardaron.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_holanda423.js
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const CON_434 = ['434', '0434', 434, '434 · HOLANDA', '434 - Holanda', '434 · PAISES BAJOS'];
const CONTROL = ['HOLANDA', 'Holanda', 'Países Bajos', 'NL', 'CHINA', '310'];
const esperado = o => (CON_434.includes(o) ? '423' : String(o));

// Lo que muestra cada input de origen, por la descripción de su fila.
async function origenesEnPantalla(page, fila, descripcion) {
  return page.$$eval(fila, (filas, d) => Object.fromEntries(filas.map(f =>
    [f.querySelector(d).textContent.trim(), f.querySelector('input[data-field="origen"]').value])), descripcion);
}
// El catálogo del proveedor no acepta un número como origen: esa fila no está.
function comparar(donde, vistos, origenes) {
  origenes.forEach((o, i) => {
    if (('Producto ' + i) in vistos && vistos['Producto ' + i] !== esperado(o)) falla(donde + ': «' + o + '» guardado se ve «' + vistos['Producto ' + i] + '»');
  });
  console.log('OK ' + donde + ': ' + JSON.stringify(vistos));
}

const origenes = CON_434.concat(CONTROL);
const productos = origenes.map((origen, i) => ({ descripcion: 'Producto ' + i, ncm: '84714900', origen }));

// Catálogo del proveedor: lo guardado y lo que se escribe y se guarda.
async function catalogoDelProveedor(page, base) {
  const deTexto = productos.filter(p => typeof p.origen === 'string');
  const proveedor = await (await page.request.post(base + '/api/catalog/proveedor_h423/productos', { data: { vendor_name: 'Proveedor H423', productos: deTexto } })).json();
  if (!proveedor.vendor_id) falla('no se guardó el catálogo del proveedor: ' + JSON.stringify(proveedor));
  await page.evaluate(() => CDI.openCatalogoDrawer());
  await page.locator('.catalogo-vendor-card[data-vendor-id="' + proveedor.vendor_id + '"]').click({ timeout: 10000 });
  await page.waitForFunction(n => document.querySelectorAll('.catalogo-product-row').length === n, deTexto.length, { timeout: 10000 })
    .catch(() => falla('el catálogo del proveedor no muestra los ' + deTexto.length + ' productos'));
  comparar('catálogo del proveedor', await origenesEnPantalla(page, '.catalogo-product-row', '.catalogo-product-desc'), origenes);
  const filaChina = page.locator('.catalogo-product-row', { hasText: 'Producto ' + origenes.indexOf('CHINA') });
  await filaChina.locator('input[data-field="origen"]').fill('0434');
  await filaChina.locator('[data-action="save-product"]').click();
  const con423 = deTexto.filter(p => CON_434.includes(p.origen)).length + 1;
  await page.waitForFunction(n => [...document.querySelectorAll('.catalogo-product-row input[data-field="origen"]')].filter(i => i.value === '423').length === n, con423, { timeout: 10000 })
    .catch(() => falla('escribir «0434» en el catálogo del proveedor no se ve 423 al guardar'));
  console.log('OK catálogo del proveedor: «0434» escrito y guardado se ve 423');
  await soloElNcm(page, base, proveedor.vendor_id);
}

// Guardar la fila cambiando sólo el NCM deja el origen guardado como estaba.
async function soloElNcm(page, base, vendorId) {
  const guardados = async () => Object.fromEntries(Object.values((await (await page.request.get(base + '/api/catalog/' + vendorId)).json()).productos)
    .map(p => [p.descripcion_original, p.origen]));
  const antes = await guardados();
  const fila = page.locator('.catalogo-product-row', { hasText: 'Producto ' + origenes.indexOf('434 · HOLANDA') });
  const guardado = page.waitForResponse(x => x.request().method() === 'PUT' && x.url().includes('/productos/'), { timeout: 10000 });
  await fila.locator('input[data-field="ncm"]').fill('84713000');
  await fila.locator('[data-action="save-product"]').click();
  if (!(await guardado).ok()) falla('cambiar el NCM en el catálogo del proveedor no se guarda');
  const despues = await guardados();
  if (JSON.stringify(despues) !== JSON.stringify(antes)) falla('cambiar sólo el NCM reescribe el origen guardado: ' + JSON.stringify(antes) + ' → ' + JSON.stringify(despues));
  console.log('OK catálogo del proveedor: cambiar sólo el NCM deja el origen guardado ' + JSON.stringify(antes['Producto ' + origenes.indexOf('434 · HOLANDA')]));
}

// Catálogo del cliente: lo guardado y lo que se escribe.
async function catalogoDelCliente(page, base) {
  const cliente = await (await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente H423 SA', cuit: '30999999995' } })).json();
  const cid = cliente.id || (cliente.cliente && cliente.cliente.id);
  const items = productos.map(p => ({ ...p, cantidad: 1, valor_unitario: 1, peso_unitario: 1 }));
  const r = await page.request.post(base + '/api/clientes/' + cid + '/catalogo/productos/learn', { data: { items } });
  if (!r.ok()) falla('no se guardó el catálogo del cliente: ' + r.status());
  await page.evaluate(() => CDI.goTo('clientes'));
  await page.locator('.cx-card[data-cliente-id="' + cid + '"]').click({ timeout: 10000 });
  await page.locator('#cxTabCatalogo').click();
  await page.waitForFunction(n => document.querySelectorAll('.cx-catalogo-producto-row').length === n, origenes.length, { timeout: 10000 })
    .catch(() => falla('el catálogo del cliente no muestra los ' + origenes.length + ' productos'));
  comparar('catálogo del cliente', await origenesEnPantalla(page, '.cx-catalogo-producto-row', '.cx-catalogo-producto-desc'), origenes);
  const campo = page.locator('.cx-catalogo-producto-row', { hasText: 'Producto ' + origenes.indexOf('310') }).locator('input[data-field="origen"]');
  const guardado = page.waitForResponse(x => x.request().method() === 'PUT' && x.url().includes('/catalogo/productos/'), { timeout: 10000 });
  await campo.fill('434');
  await campo.press('Enter');
  if (!(await guardado.catch(() => falla('escribir «434» en el catálogo del cliente no se guarda'))).ok()) falla('el catálogo del cliente no guardó «434»');
  await page.waitForFunction(c => c.value === '423', await campo.elementHandle(), { timeout: 5000 })
    .catch(async () => falla('«434» escrito en el catálogo del cliente se ve «' + await campo.inputValue() + '»'));
  console.log('OK catálogo del cliente: «434» escrito se ve 423');
  await escritoMientrasGuarda(page, campo);
}

// Lo que se vuelve a escribir mientras se guarda no se pisa con lo guardado.
async function escritoMientrasGuarda(page, campo) {
  let soltar;
  const retenido = new Promise(r => { soltar = r; });
  await page.route('**/catalogo/productos/*', async route => { await retenido; await route.continue(); });
  const guardado = page.waitForResponse(x => x.request().method() === 'PUT' && x.url().includes('/catalogo/productos/'), { timeout: 10000 });
  await campo.fill('434');
  await campo.press('Enter');
  await campo.fill('CN');
  // El aviso de «Producto actualizado» sale después de que la pantalla usó la respuesta.
  await page.evaluate(() => { document.getElementById('toastHost').innerHTML = ''; });
  soltar();
  await guardado;
  await page.waitForSelector('#toastHost .toast', { timeout: 10000 });
  await page.unroute('**/catalogo/productos/*');
  if (await campo.inputValue() !== 'CN') falla('lo escrito mientras se guardaba «434» quedó «' + await campo.inputValue() + '»');
  console.log('OK catálogo del cliente: lo escrito mientras se guarda no se pisa');
}

// Procedencia de la revisión: la del borrador y la que se escribe.
async function procedencia(page) {
  for (const o of origenes) {
    await page.evaluate(p => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = { numero_factura: 'F-H423', moneda: 'DOL', incoterm: 'FOB', procedencia: p };
      CDI.state.items = [{ pieza: '84714900100D', descripcion: 'Producto', origen: 'CN', cantidad: 1, valor_unitario: 1, peso_unitario: 1 }];
      CDI.goTo('review');
    }, o);
    await page.waitForSelector('#f_procedencia', { state: 'visible', timeout: 10000 });
    if (await page.inputValue('#f_procedencia') !== esperado(o)) falla('procedencia «' + o + '» del borrador se ve «' + await page.inputValue('#f_procedencia') + '»');
    const enLaOperacion = await page.evaluate(() => String(CDI.state.operacion.procedencia));
    if (enLaOperacion !== String(o)) falla('procedencia «' + o + '» del borrador queda «' + enLaOperacion + '» en la operación');
    await page.fill('#f_procedencia', String(o));
    await page.locator('#f_procedencia').blur();
    if (await page.inputValue('#f_procedencia') !== esperado(o)) falla('procedencia «' + o + '» escrita se ve «' + await page.inputValue('#f_procedencia') + '»');
  }
  // Tecla por tecla, «434» es el comienzo de «4340»: no se toca hasta salir del campo.
  await page.fill('#f_procedencia', '');
  await page.locator('#f_procedencia').pressSequentially('4340');
  await page.locator('#f_procedencia').blur();
  if (await page.inputValue('#f_procedencia') !== '4340') falla('«4340» escrito tecla por tecla se ve «' + await page.inputValue('#f_procedencia') + '»');
  console.log('OK procedencia: el código 434 del borrador o escrito se ve 423; lo demás, como vino');
}

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await registrarCuenta(page.request, base, { data: { username: 'h423_' + id, password: 'Clave-Inventada-123', email: 'h423' + id + '@ejemplo.test' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && CDI.paisesMaria);
  await catalogoDelProveedor(page, base);
  await catalogoDelCliente(page, base);
  await procedencia(page);
  await b.close();
  console.log('OK: pantalla Holanda→423');
})().catch(e => falla(e.message));
