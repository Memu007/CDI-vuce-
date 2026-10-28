// DESPACHO-1b en el navegador local, contra la API de verdad y con el despacho
// sintético de tests/test_despacho1b.py (valores inventados): en la pestaña
// Catálogo del cliente, «Cargar desde despacho» lee el PDF y muestra un
// renglón por producto; el kilo neto que no estaba se ve marcado; nada se
// guarda antes de «Guardar en el catálogo»; un renglón incompleto se marca y
// no se guarda ninguno; corregido, los tres llegan a «Productos aprendidos».
// En 1280 y 390 px, los botones se ven enteros, el panel no ensancha la
// página y nada se sale del panel.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> PY=<python del proyecto> node scripts/testing/pantalla_despacho1b.js
// (se corre desde la raíz del repositorio)
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const PY = process.env.PY || 'python3';

// El mismo PDF que usan las pruebas, armado por ellas.
function despachoSintetico() {
  const archivo = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'd1b-')), 'despacho_inventado.pdf');
  execFileSync(PY, ['-c', [
    'import sys',
    'sys.path.insert(0, ".")',
    'from tests.test_despacho1b import _despacho',
    'open(sys.argv[1], "wb").write(_despacho())',
  ].join('\n'), archivo], {
    env: Object.assign({}, process.env, {
      DATABASE_URL: 'sqlite+aiosqlite:///:memory:', GEMINI_API_KEY: 'test-key', ENVIRONMENT: 'test',
      VUCE_MODE: 'fake', TARIFAR_MODE: 'fake', AFIP_MODE: 'fake',
    }),
  });
  return archivo;
}

async function productosGuardados(page, base, cid) {
  const r = await page.request.get(base + '/api/clientes/' + cid + '/catalogo/productos');
  if (!r.ok()) falla('catálogo: ' + r.status() + ' ' + await r.text());
  return (await r.json()).productos;
}

async function dentroDelAncho(page, ancho, selector, que) {
  const cajas = await page.locator(selector).evaluateAll(els => els
    .filter(el => el.offsetParent !== null)
    .map(el => { const r = el.getBoundingClientRect(); return { x: r.left, d: r.right, id: el.id || el.className }; }));
  if (!cajas.length) falla(ancho + ' px: no se ve ' + que);
  const fuera = cajas.filter(c => c.x < 0 || c.d > ancho + 0.5);
  if (fuera.length) falla(ancho + ' px: ' + que + ' queda fuera de la pantalla: ' + JSON.stringify(fuera));
}

(async () => {
  const pdf = despachoSintetico();
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();

  for (const ancho of [1280, 390]) {
    const ctx = await b.newContext({ viewport: { width: ancho, height: 900 } });
    const page = await ctx.newPage();
    // Guardar sólo se pide al tocar el botón: cualquier pedido anterior es
    // guardar sin revisar.
    let tocoGuardar = false;
    page.on('request', req => {
      if (req.method() === 'POST' && req.url().includes('/catalogo/despacho/guardar') && !tocoGuardar) {
        falla(ancho + ' px: se pidió guardar antes de tocar «Guardar en el catálogo»');
      }
    });
    let r = await page.request.post(base + '/auth/register', {
      data: { username: 'd1b_' + ancho + '_' + id, password: 'Clave-Inventada-123', email: 'd1b' + ancho + id + '@ejemplo.test' },
    });
    if (!r.ok()) falla('registro: ' + r.status() + ' ' + await r.text());
    r = await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente Inventado D1b ' + ancho } });
    if (!r.ok()) falla('alta del cliente: ' + r.status() + ' ' + await r.text());
    const cid = (await r.json()).cliente.id;

    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.goTo);
    await page.evaluate(() => CDI.goTo('clientes'));
    await page.locator('.cx-card[data-cliente-id="' + cid + '"]').click();
    await page.locator('#cxTabCatalogo').click();

    const boton = page.locator('#cxDespachoBtn');
    await boton.waitFor({ state: 'visible', timeout: 10000 }).catch(() => falla(ancho + ' px: no se ve «Cargar desde despacho»'));
    await page.evaluate(() => window.scrollTo(0, window.scrollY));
    await dentroDelAncho(page, ancho, '#cxDespachoBtn, #cxCatalogoExcelBtn', 'un botón del catálogo');
    const paginaAntes = await page.evaluate(() => document.documentElement.scrollWidth);

    const [elegir] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 10000 }).catch(() => falla(ancho + ' px: el botón no abre el selector de archivo')),
      boton.click(),
    ]);
    await elegir.setFiles(pdf);

    const renglones = page.locator('#cxDespachoRenglones > .cx-despacho-renglon');
    await renglones.nth(2).waitFor({ timeout: 15000 }).catch(async () =>
      falla(ancho + ' px: no aparecen los tres renglones; el estado dice «' + await page.locator('#cxDespachoEstado').innerText() + '»'));
    if (await renglones.count() !== 3) falla(ancho + ' px: se esperaban 3 renglones y hay ' + await renglones.count());
    const titulos = await page.locator('#cxDespachoRenglones .cx-despacho-renglon-titulo').allInnerTexts();
    if (JSON.stringify(titulos) !== JSON.stringify(['Ítem 0001', 'Ítem 0002 · subítem 0001', 'Ítem 0002 · subítem 0002'])) {
      falla(ancho + ' px: los renglones son ' + JSON.stringify(titulos));
    }
    await page.waitForLoadState('networkidle');  // un pedido de guardar tardío cae antes del clic

    // Lo que faltaba: sólo el kilo neto del subítem rojo, marcado y vacío.
    const faltantes = await page.locator('#cxDespachoRenglones .cx-despacho-campo.is-faltante input, #cxDespachoRenglones .cx-despacho-campo.is-faltante textarea')
      .evaluateAll(els => els.map(el => [el.id, el.value]));
    if (JSON.stringify(faltantes) !== JSON.stringify([['cxDesp2_kilo_neto', '']])) {
      falla(ancho + ' px: lo marcado como faltante es ' + JSON.stringify(faltantes));
    }
    const nota = await page.locator('#cxDesp2_kilo_neto').locator('xpath=..').innerText();
    if (!nota.includes('No estaba en el despacho')) falla(ancho + ' px: el faltante no dice que no estaba: «' + nota + '»');
    if (await page.locator('#cxDesp1_kilo_neto').inputValue() !== '12,5') falla(ancho + ' px: el kilo del azul es «' + await page.locator('#cxDesp1_kilo_neto').inputValue() + '»');
    const estilo = el => getComputedStyle(el).borderTopColor + ' ' + getComputedStyle(el).backgroundColor;
    const color = await page.locator('#cxDesp2_kilo_neto').evaluate(estilo);
    const colorSano = await page.locator('#cxDesp1_kilo_neto').evaluate(estilo);
    if (color === colorSano) falla(ancho + ' px: el faltante se ve igual que un campo completo (' + color + ')');

    // El tablero ya se corre de costado a 390 px antes de esta pieza (ver
    // pantalla_despacho1a.js): se mide que el panel no lo ensanche, que no
    // se salga de la pestaña y que nada se salga del panel.
    const paginaDespues = await page.evaluate(() => document.documentElement.scrollWidth);
    if (paginaDespues > paginaAntes) falla(ancho + ' px: el panel ensancha la página de ' + paginaAntes + ' a ' + paginaDespues + ' px');
    const medida = await page.locator('#cxDespacho').evaluate(panel => {
      const caja = el => { const r = el.getBoundingClientRect(); return { x: r.left, d: r.right }; };
      const p = caja(panel), padre = caja(panel.parentElement);
      const fuera = Array.from(panel.querySelectorAll('input, textarea, button, label, .cx-despacho-renglon'))
        .filter(el => el.offsetParent !== null)
        .map(el => Object.assign({ id: el.id || el.className }, caja(el)))
        .filter(c => c.x < p.x - 0.5 || c.d > p.d + 0.5);
      return { ancho: p.d - p.x, sePasaDelPadre: p.x < padre.x - 0.5 || p.d > padre.d + 0.5, desborda: panel.scrollWidth > panel.clientWidth, fuera };
    });
    if (medida.ancho > ancho) falla(ancho + ' px: el panel mide ' + medida.ancho + ' px');
    if (medida.sePasaDelPadre) falla(ancho + ' px: el panel se sale de la pestaña Catálogo');
    if (medida.desborda || medida.fuera.length) falla(ancho + ' px: algo se sale del panel: ' + JSON.stringify(medida.fuera));

    if ((await productosGuardados(page, base, cid)).length) falla(ancho + ' px: se guardó algo antes de tocar «Guardar en el catálogo»');

    // Un renglón incompleto: se marca y no se guarda ninguno.
    await page.locator('#cxDesp0_descripcion').fill('');
    tocoGuardar = true;
    await page.locator('#cxDespachoGuardar').click();
    const error = page.locator('#cxDespachoRenglones > .cx-despacho-renglon.is-error');
    await error.first().waitFor({ timeout: 10000 }).catch(() => falla(ancho + ' px: el renglón sin descripción no se marcó'));
    const marcados = await error.evaluateAll(els => els.map(el => [el.dataset.indice, el.querySelector('.cx-despacho-errores').innerText]));
    if (marcados.length !== 1 || marcados[0][0] !== '0' || !marcados[0][1].includes('Falta la descripción.')) {
      falla(ancho + ' px: lo marcado es ' + JSON.stringify(marcados));
    }
    if ((await productosGuardados(page, base, cid)).length) falla(ancho + ' px: con un renglón incompleto se guardó algo');

    // Corregido y con el kilo del rojo completado a mano: se guardan los tres.
    await page.locator('#cxDesp0_descripcion').fill('NOTEBOOK INVENTADA DE TIPO PORTATIL');
    await page.locator('#cxDesp2_kilo_neto').fill('5,00');
    await page.locator('#cxDespachoGuardar').click();
    await page.locator('#cxDespacho').waitFor({ state: 'hidden', timeout: 10000 }).catch(async () =>
      falla(ancho + ' px: el panel no se cerró al guardar; dice «' + await page.locator('#cxDespachoEstado').innerText() + '»'));
    const filas = page.locator('#cxCatalogoProductosList .cx-catalogo-producto-row');
    await filas.nth(2).waitFor({ timeout: 10000 }).catch(() => falla(ancho + ' px: «Productos aprendidos» no muestra los tres guardados'));
    const enPantalla = (await page.locator('#cxCatalogoProductosList .cx-catalogo-producto-desc').allInnerTexts()).sort();
    const esperados = ['NOTEBOOK INVENTADA DE TIPO PORTATIL', 'TAPA INVENTADA AZUL', 'TAPA INVENTADA ROJA'];
    if (JSON.stringify(enPantalla) !== JSON.stringify(esperados)) falla(ancho + ' px: «Productos aprendidos» muestra ' + JSON.stringify(enPantalla));

    const guardados = await productosGuardados(page, base, cid);
    const roja = guardados.find(p => p.descripcion === 'TAPA INVENTADA ROJA');
    if (!roja || roja.ncm !== '39269090' || roja.origen !== 'BR' || Math.abs(roja.peso_unitario_avg - 0.1) > 1e-9) {
      falla(ancho + ' px: la tapa roja quedó ' + JSON.stringify(roja));
    }
    console.log('OK ' + ancho + ' px: 3 renglones, faltante marcado ' + JSON.stringify(faltantes) + ', nada guardado antes ni con error, ' +
      'guardados ' + JSON.stringify(enPantalla) + ', panel de ' + Math.round(medida.ancho) + ' px sin desbordes, página de ' + paginaAntes + ' px antes y después');
    await ctx.close();
  }
  await b.close();
})().catch(e => falla(String(e && e.stack || e)));
