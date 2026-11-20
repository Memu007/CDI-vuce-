// El origen de un país en el navegador local, contra el servidor local (sin terceros).
// En los catálogos del proveedor y del cliente, en el «Origen frecuente» y en la
// procedencia de la revisión, un país guardado o escrito se ve con el código y el
// nombre que salen en el TXT (el 434, como 423); lo que no es un país, como vino.
// Guardar otro campo del catálogo deja el origen guardado como estaba.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> CDI_DB=<base sqlite del servidor> node scripts/testing/pantalla_holanda423.js
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
const { execFileSync } = require('child_process');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const baseLocal = process.env.CDI_DB || falla('falta CDI_DB: la base sqlite local del servidor, para sembrar orígenes que la API ya no guarda');
const CON_434 = ['434', '0434', 434, '434 · HOLANDA', '434 - Holanda', '434 · PAISES BAJOS'];
const PB = '423 · PAISES BAJOS', CHINA = '310 · CHINA', XSS = '<img src=x onerror="window.__xss=1">';
const ETIQUETAS = [...CON_434.map(o => [o, PB]), ['HOLANDA', PB], ['Holanda', PB], ['Países Bajos', PB],
  ['NL', PB], ['CHINA', CHINA], ['310', CHINA], ['CN', CHINA], ['ATLANTIDA', 'ATLANTIDA'], ['Narnia', 'Narnia'],
  ['tierra media', 'tierra media'], [XSS, XSS], ['-', '-']];
const NO_SON_PAISES = ['Narnia', 'tierra media', 'ATLANTIDA', XSS, '-'];
// Lo guardado en los catálogos y cómo se ve: la familia de arriba y cada país de la tabla con su código.
let ORIGENES, USUARIO;
const fila = o => 'Producto ' + ORIGENES.findIndex(([g]) => g === o);
// La fila de ese origen, por su descripción entera: «Producto 1» no es «Producto 10».
const enFila = (page, filas, desc, o) => page.locator(filas).filter({ has: page.locator(desc, { hasText: new RegExp('^' + fila(o) + '$') }) });
const delProveedor = (page, o) => enFila(page, '.catalogo-product-row', '.catalogo-product-desc', o);
const delCliente = (page, o) => enFila(page, '.cx-catalogo-producto-row', '.cx-catalogo-producto-desc', o);

// Lo que muestra cada input de origen, por la descripción de su fila.
async function origenesEnPantalla(page, fila, descripcion) {
  return page.$$eval(fila, (filas, d) => Object.fromEntries(filas.map(f =>
    [f.querySelector(d).textContent.trim(), f.querySelector('input[data-field="origen"]').value])), descripcion);
}
// El catálogo del proveedor no acepta un número como origen: esa fila no está.
function comparar(donde, vistos) {
  const faltan = ORIGENES.filter(([o], i) => typeof o === 'string' && !(('Producto ' + i) in vistos));
  if (faltan.length) falla(donde + ': no se ven las filas de ' + JSON.stringify(faltan));
  ORIGENES.forEach(([o, visto], i) => {
    if (('Producto ' + i) in vistos && vistos['Producto ' + i] !== visto) falla(donde + ': «' + o + '» guardado se ve «' + vistos['Producto ' + i] + '»');
  });
  console.log('OK ' + donde + ': ' + Object.keys(vistos).length + ' orígenes con código y nombre o como vinieron');
}

// El campo muestra entera la etiqueta de los orígenes corrientes, sin salirse de su fila. Emiratos va
// primero porque es la más ancha de los seis: un campo angosto falla ahí, con Inter y con Arial.
async function enteras(donde, filaDe) {
  for (const o of ['331', 'CHINA', 'HOLANDA', '212', '309', '438']) {
    const campo = filaDe(o).locator('input[data-field="origen"]');
    if (await campo.evaluate(i => i.getBoundingClientRect().right > i.closest('.catalogo-product-row, .cx-catalogo-producto-row').getBoundingClientRect().right))
      falla(donde + ': el campo de origen se sale de su fila');
    if (await campo.evaluate(i => i.scrollWidth > i.clientWidth)) falla(donde + ': «' + await campo.inputValue() + '» no entra en el campo');
  }
}

// Lo que no es un país se ve con las letras con que se guardó: el campo no las cambia.
async function comoSeGuardo(donde, filaDe) {
  for (const o of NO_SON_PAISES) {
    if (await filaDe(o).locator('input[data-field="origen"]').evaluate(i => getComputedStyle(i).textTransform !== 'none' || getComputedStyle(i).fontVariantCaps !== 'normal'))
      falla(donde + ': «' + o + '» guardado no se ve con sus letras');
  }
}

// Una fila baja de renglón primero en el ancho más angosto de cada disposición: cada `max-width` de
// la página, más uno, hasta `desde`.
async function enUnRenglon(page, donde, filas, partes, desde) {
  const anchos = await page.evaluate(desde => {
    const cortes = new Set([desde]);
    for (const hoja of document.styleSheets) {
      let reglas;
      try { reglas = [...hoja.cssRules]; } catch { continue; }
      for (const r of reglas) for (const m of (r.media ? r.media.mediaText : '').matchAll(/max-width:\s*(\d+)px/g)) if (+m[1] >= desde) cortes.add(+m[1] + 1);
    }
    return [...cortes].sort((a, b) => b - a);
  }, desde);
  const medir = () => page.$$eval(filas, (fs, partes) => fs.map(f => {
    const rs = [...f.querySelectorAll(partes)].map(e => e.getBoundingClientRect());
    return { origen: f.querySelector('input[data-field="origen"]').value, alto: Math.round(f.getBoundingClientRect().height), partes: rs.length,
      unRenglon: Math.max(...rs.map(r => r.top)) < Math.min(...rs.map(r => r.bottom)) };
  }), partes);
  const antes = await medir();
  if (!antes.length || antes.some(f => f.partes < 2)) falla(donde + ': no encuentra las filas o sus partes');
  for (const ancho of anchos) {
    await page.setViewportSize({ width: ancho, height: 1000 });
    for (const [i, f] of (await medir()).entries()) {
      if (!f.unRenglon) falla(donde + ' a ' + ancho + ' px: baja de renglón la fila de «' + f.origen + '»');
      if (f.alto !== antes[i].alto) falla(donde + ' a ' + ancho + ' px: cambia de alto la fila de «' + f.origen + '» (' + antes[i].alto + ' → ' + f.alto + ')');
    }
  }
  await page.setViewportSize({ width: 1280, height: 1000 });
  console.log('OK ' + donde + ': ' + antes.length + ' filas en un renglón y con su alto a ' + anchos.join(', ') + ' px');
}

const productos = () => ORIGENES.map(([origen], i) => ({ descripcion: 'Producto ' + i, ncm: '84714900', origen }));

// Lo que la API ya no guarda, como pudo quedar de antes.
function sembrarOrigen(vendorId, descripcion, origen) {
  execFileSync('python3', ['-c',
    'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute("UPDATE vendor_catalog_products SET origen=? WHERE owner_username=? AND vendor_id=? AND descripcion=?", sys.argv[2:]).rowcount; c.commit(); sys.exit(0 if n == 1 else 1)',
    baseLocal, origen, USUARIO, vendorId, descripcion]);
}

// Catálogo del proveedor: lo guardado y lo que se escribe y se guarda.
async function catalogoDelProveedor(page, base) {
  const deTexto = productos().filter(p => typeof p.origen === 'string');
  const proveedor = await (await page.request.post(base + '/api/catalog/proveedor_h423/productos', { data: { vendor_name: 'Proveedor H423', productos: deTexto } })).json();
  if (!proveedor.vendor_id) falla('no se guardó el catálogo del proveedor: ' + JSON.stringify(proveedor));
  NO_SON_PAISES.forEach(o => sembrarOrigen(proveedor.vendor_id, fila(o), o));
  await page.evaluate(() => CDI.openCatalogoDrawer());
  await page.locator('.catalogo-vendor-card[data-vendor-id="' + proveedor.vendor_id + '"]').click({ timeout: 10000 });
  await page.waitForFunction(n => document.querySelectorAll('.catalogo-product-row').length === n, deTexto.length, { timeout: 10000 })
    .catch(() => falla('el catálogo del proveedor no muestra los ' + deTexto.length + ' productos'));
  comparar('catálogo del proveedor', await origenesEnPantalla(page, '.catalogo-product-row', '.catalogo-product-desc'));
  const filaChina = delProveedor(page, 'CHINA');
  await enUnRenglon(page, 'catálogo del proveedor', '.catalogo-product-row', '.catalogo-product-field', 320);
  await enteras('catálogo del proveedor', o => delProveedor(page, o));
  await comoSeGuardo('catálogo del proveedor', o => delProveedor(page, o));
  const conPB = () => page.$$eval('.catalogo-product-row input[data-field="origen"]', (c, pb) => c.filter(i => i.value === pb).length, PB);
  const antes = await conPB();
  await filaChina.locator('input[data-field="origen"]').fill('0434');
  await filaChina.locator('[data-action="save-product"]').click();
  await page.waitForFunction(([n, pb]) => [...document.querySelectorAll('.catalogo-product-row input[data-field="origen"]')].filter(i => i.value === pb).length === n, [antes + 1, PB], { timeout: 10000 })
    .catch(() => falla('escribir «0434» en el catálogo del proveedor no se ve «' + PB + '» al guardar'));
  console.log('OK catálogo del proveedor: «0434» escrito y guardado se ve «' + PB + '»');
  for (const o of ['434 · HOLANDA', 'Países Bajos', ...NO_SON_PAISES]) await soloElNcm(page, base, proveedor.vendor_id, o);
  if (await page.evaluate(() => window.__xss)) falla('un origen del catálogo del proveedor con HTML se ejecutó');
}

// Guardar la fila cambiando sólo el NCM deja el origen guardado como estaba.
async function soloElNcm(page, base, vendorId, origen) {
  const guardados = async () => Object.fromEntries(Object.values((await (await page.request.get(base + '/api/catalog/' + vendorId)).json()).productos)
    .map(p => [p.descripcion_original, p.origen]));
  const antes = await guardados();
  const filaGuardada = delProveedor(page, origen);
  await filaGuardada.evaluate(f => { f.dataset.antesDeGuardar = '1'; });
  const guardado = page.waitForResponse(x => x.request().method() === 'PUT' && x.url().includes('/productos/'), { timeout: 10000 });
  await filaGuardada.locator('input[data-field="ncm"]').fill('84713000');
  await filaGuardada.locator('[data-action="save-product"]').click();
  if (!(await guardado).ok()) falla('cambiar el NCM en el catálogo del proveedor no se guarda con el origen «' + origen + '»');
  // El detalle se vuelve a pedir después de guardar: se espera la fila nueva, no la de antes.
  await enFila(page, '.catalogo-product-row:not([data-antes-de-guardar])', '.catalogo-product-desc', origen).waitFor({ timeout: 10000 })
    .catch(() => falla('guardar el NCM en el catálogo del proveedor no vuelve a mostrar la fila de «' + origen + '»'));
  const despues = await guardados();
  if (JSON.stringify(despues) !== JSON.stringify(antes)) falla('cambiar sólo el NCM reescribe el origen guardado «' + origen + '» → «' + despues[fila(origen)] + '»');
  console.log('OK catálogo del proveedor: cambiar sólo el NCM deja el origen guardado ' + JSON.stringify(antes[fila(origen)]));
}

// Catálogo del cliente: lo guardado y lo que se escribe.
async function catalogoDelCliente(page, base) {
  const cliente = await (await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente H423 SA', cuit: '30999999995' } })).json();
  const cid = cliente.id || (cliente.cliente && cliente.cliente.id);
  const items = productos().map(p => ({ ...p, cantidad: 1, valor_unitario: 1, peso_unitario: 1 }));
  const r = await page.request.post(base + '/api/clientes/' + cid + '/catalogo/productos/learn', { data: { items } });
  if (!r.ok()) falla('no se guardó el catálogo del cliente: ' + r.status());
  await origenFrecuente(page, cid);
  await page.locator('#cxTabCatalogo').click();
  await page.waitForFunction(n => document.querySelectorAll('.cx-catalogo-producto-row').length === n, ORIGENES.length, { timeout: 10000 })
    .catch(() => falla('el catálogo del cliente no muestra los ' + ORIGENES.length + ' productos'));
  comparar('catálogo del cliente', await origenesEnPantalla(page, '.cx-catalogo-producto-row', '.cx-catalogo-producto-desc'));
  if (await page.evaluate(() => window.__xss)) falla('un origen del catálogo del cliente con HTML se ejecutó');
  const campo = delCliente(page, '310').locator('input[data-field="origen"]');
  await enUnRenglon(page, 'catálogo del cliente', '.cx-catalogo-producto-row', '.cx-catalogo-producto-sub > *', 460);
  await enteras('catálogo del cliente', o => delCliente(page, o));
  await comoSeGuardo('catálogo del cliente', o => delCliente(page, o));
  const guardado = page.waitForResponse(x => x.request().method() === 'PUT' && x.url().includes('/catalogo/productos/'), { timeout: 10000 });
  await campo.fill('434');
  await campo.press('Enter');
  if (!(await guardado.catch(() => falla('escribir «434» en el catálogo del cliente no se guarda'))).ok()) falla('el catálogo del cliente no guardó «434»');
  await page.waitForFunction(([c, pb]) => c.value === pb, [await campo.elementHandle(), PB], { timeout: 5000 })
    .catch(async () => falla('«434» escrito en el catálogo del cliente se ve «' + await campo.inputValue() + '»'));
  console.log('OK catálogo del cliente: «434» escrito se ve «' + PB + '»');
  await escritoMientrasGuarda(page, campo);
  await otrosEscritos(page, base, cid);
}

// El origen frecuente sale de las operaciones: se responde cada forma guardada.
async function origenFrecuente(page, cid) {
  let guardado;
  await page.route('**/api/clientes/' + cid + '/metricas', ruta => ruta.fulfill({ json: { metricas: { origen_frecuente: guardado } } }));
  for (const [o, visto] of ETIQUETAS) {
    guardado = o;
    await page.evaluate(() => { document.getElementById('cxKpiOrigen').textContent = ''; CDI.goTo('clientes'); });
    await page.locator('.cx-card[data-cliente-id="' + cid + '"]').click({ timeout: 10000 });
    await page.waitForFunction(v => document.getElementById('cxKpiOrigen').textContent === v, visto, { timeout: 5000 })
      .catch(async () => falla('el origen frecuente «' + o + '» se ve «' + await page.textContent('#cxKpiOrigen') + '»'));
    if (await page.$eval('#cxKpiOrigen', el => el.children.length)) falla('el origen frecuente «' + o + '» se ve como HTML');
  }
  if (await page.evaluate(() => window.__xss)) falla('un origen frecuente con HTML se ejecutó');
  console.log('OK origen frecuente: ' + ETIQUETAS.length + ' formas con código y nombre o como vinieron');
}

// Un país escrito por nombre o por sigla se guarda así (la sigla, en mayúsculas) y se ve con código y
// nombre; un peso, como se escribió. Guardar el peso deja el origen guardado como estaba.
async function otrosEscritos(page, base, cid) {
  const guardados = async () => Object.fromEntries((await (await page.request.get(base + '/api/clientes/' + cid + '/catalogo/productos')).json())
    .productos.map(p => [p.descripcion, p.origen]));
  // (fila, campo, lo escrito, cómo se ve, el origen que queda guardado; sin él, el que estaba)
  const escritos = [['CHINA', 'origen', 'nl', PB, 'NL'], ['CHINA', 'origen', 'CHINA', CHINA, 'CHINA'],
    ['CHINA', 'peso_unitario_avg', '434', '434'], ...NO_SON_PAISES.map(o => [o, 'peso_unitario_avg', '2.5', '2.5'])];
  for (const [o, campo, valor, visto, origen] of escritos) {
    const input = delCliente(page, o).locator('input[data-field="' + campo + '"]');
    const antes = await guardados();
    await page.evaluate(() => { document.getElementById('toastHost').innerHTML = ''; });
    await input.fill(valor);
    await input.press('Enter');
    await page.waitForSelector('#toastHost .toast', { timeout: 10000 });
    if (await input.inputValue() !== visto) falla('«' + valor + '» escrito en ' + campo + ' del catálogo del cliente se ve «' + await input.inputValue() + '»');
    const despues = await guardados();
    const quedo = origen || antes[fila(o)];
    if (despues[fila(o)] !== quedo) falla('«' + valor + '» escrito en ' + campo + ' del catálogo del cliente deja el origen «' + despues[fila(o)] + '», no «' + quedo + '»');
  }
  console.log('OK catálogo del cliente: «CHINA» y «nl» escritos se guardan así y se ven con código y nombre; guardar el peso deja el origen');
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
  await page.evaluate(() => { document.getElementById('toastHost').innerHTML = ''; });
  await campo.press('Enter');
  await page.waitForSelector('#toastHost .toast', { timeout: 10000 });
  console.log('OK catálogo del cliente: lo escrito mientras se guarda no se pisa');
}

// Procedencia de la revisión: la del borrador y la que se escribe.
async function procedencia(page) {
  for (const [o, visto] of ETIQUETAS) {
    await page.evaluate(p => {
      CDI.state = CDI.state || {};
      CDI.state.operacion = { numero_factura: '434', moneda: 'DOL', incoterm: 'FOB', procedencia: p };
      CDI.state.items = [{ pieza: '84714900100D', descripcion: 'Producto', origen: 'CN', cantidad: 1, valor_unitario: 1, peso_unitario: 1 }];
      CDI.goTo('review');
    }, o);
    await page.waitForSelector('#f_procedencia', { state: 'visible', timeout: 10000 });
    if (await page.inputValue('#f_procedencia') !== visto) falla('procedencia «' + o + '» del borrador se ve «' + await page.inputValue('#f_procedencia') + '»');
    if (await page.inputValue('#f_numero_factura') !== '434') falla('la factura «434» del borrador se ve «' + await page.inputValue('#f_numero_factura') + '»');
    const enLaOperacion = await page.evaluate(() => String(CDI.state.operacion.procedencia));
    if (enLaOperacion !== String(o)) falla('procedencia «' + o + '» del borrador queda «' + enLaOperacion + '» en la operación');
    // Vaciado antes: escribir el mismo valor que se ve no dispara «change».
    await page.fill('#f_procedencia', '');
    await page.locator('#f_procedencia').blur();
    await page.fill('#f_procedencia', String(o));
    await page.locator('#f_procedencia').blur();
    if (await page.inputValue('#f_procedencia') !== visto) falla('procedencia «' + o + '» escrita se ve «' + await page.inputValue('#f_procedencia') + '»');
    const escrita = await page.evaluate(() => String(CDI.state.operacion.procedencia));
    if (escrita !== String(o)) falla('procedencia «' + o + '» escrita queda «' + escrita + '» en la operación');
  }
  // Distinta de la del borrador: con el mismo valor no hay «change».
  await page.fill('#f_numero_factura', '0434');
  await page.locator('#f_numero_factura').blur();
  if (await page.inputValue('#f_numero_factura') !== '0434') falla('la factura «0434» escrita se ve «' + await page.inputValue('#f_numero_factura') + '»');
  // Tecla por tecla, «434» es el comienzo de «4340»: no se toca hasta salir del campo.
  await page.fill('#f_procedencia', '');
  await page.locator('#f_procedencia').pressSequentially('4340');
  await page.locator('#f_procedencia').blur();
  if (await page.inputValue('#f_procedencia') !== '4340') falla('«4340» escrito tecla por tecla se ve «' + await page.inputValue('#f_procedencia') + '»');
  console.log('OK procedencia: la del borrador o escrita se ve con código y nombre, o como vino, y queda como vino');
}

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  USUARIO = 'h423_' + id;
  await registrarCuenta(page.request, base, { data: { username: USUARIO, password: 'Clave-Inventada-123', email: 'h423' + id + '@ejemplo.test' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && CDI.paisesMaria);
  const tabla = await page.evaluate(() => CDI.paisesMaria.countries.map(c => [c.code, c.code + ' · ' + c.name]));
  ORIGENES = [...ETIQUETAS, ...tabla.filter(([c]) => !ETIQUETAS.some(([o]) => o === c))];
  await catalogoDelProveedor(page, base);
  await catalogoDelCliente(page, base);
  await procedencia(page);
  await b.close();
  console.log('OK: pantalla Holanda→423');
})().catch(e => falla(e.message));
