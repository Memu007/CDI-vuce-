// DESPACHO-1a en el navegador local, contra la API de verdad y con datos
// inventados: en la pestaña Catálogo del cliente, «Descargar en Excel» baja un
// .xlsx con los mismos productos que muestra la pantalla, en el mismo orden;
// la descripción que empieza con «=» llega como texto. También en un teléfono
// (390 px) el botón se ve entero dentro del ancho de la pantalla. (El tablero
// ya se corre de costado a 390 px antes de esta pieza, con o sin el botón: eso
// no se mide acá.)
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> PY=<python con openpyxl> node scripts/testing/pantalla_despacho1a.js
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const PY = process.env.PY || 'python3';

(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();

  for (const ancho of [1280, 390]) {
    const ctx = await b.newContext({ viewport: { width: ancho, height: 900 }, acceptDownloads: true });
    const page = await ctx.newPage();
    let r = await page.request.post(base + '/auth/register', {
      headers: { 'X-Forwarded-For': ipNueva() },
      data: { username: 'd1a_' + ancho + '_' + id, password: 'Clave-Inventada-123', email: 'd1a' + ancho + id + '@ejemplo.test' },
    });
    if (!r.ok()) falla('registro: ' + r.status() + ' ' + await r.text());
    r = await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente Inventado D1a ' + ancho } });
    if (!r.ok()) falla('alta del cliente: ' + r.status() + ' ' + await r.text());
    const cid = (await r.json()).cliente.id;
    r = await page.request.post(base + '/api/clientes/' + cid + '/catalogo/productos/learn', {
      data: { items: [
        { ncm: '0101.21.00', descripcion: 'CABALLO INVENTADO', origen: 'UY', valor_unitario: 1234.5, cantidad: 2, peso_unitario: 450 },
        { ncm: '8471.30.12', descripcion: '=1+1 NOTEBOOK INVENTADA', origen: 'CN', valor_unitario: 99.5, cantidad: 3, peso_unitario: 1.5 },
      ] },
    });
    if (!r.ok()) falla('productos aprendidos: ' + r.status() + ' ' + await r.text());
    const enPantallaApi = (await (await page.request.get(base + '/api/clientes/' + cid + '/catalogo/productos')).json()).productos;
    if (enPantallaApi.length !== 2) falla('se esperaban 2 productos aprendidos y hay ' + enPantallaApi.length);

    await page.goto(base + '/dashboard');
    await page.waitForFunction(() => window.CDI && CDI.goTo);
    await page.evaluate(() => CDI.goTo('clientes'));
    await page.locator('.cx-card[data-cliente-id="' + cid + '"]').click();
    await page.locator('#cxTabCatalogo').click();
    const filas = page.locator('#cxCatalogoProductosList .cx-catalogo-producto-row');
    await filas.nth(1).waitFor({ timeout: 10000 }).catch(() => falla(ancho + ' px: la pantalla no muestra los dos productos'));
    const enPantalla = await page.locator('#cxCatalogoProductosList .cx-catalogo-producto-desc').allInnerTexts();

    const boton = page.locator('#cxCatalogoExcelBtn');
    if (!(await boton.isVisible())) falla(ancho + ' px: no se ve «Descargar en Excel»');
    const caja = await boton.boundingBox();
    if (!caja || caja.x < 0 || caja.x + caja.width > ancho) falla(ancho + ' px: el botón queda fuera de la pantalla: ' + JSON.stringify(caja));

    const [descarga] = await Promise.all([
      page.waitForEvent('download', { timeout: 10000 }).catch(() => falla(ancho + ' px: el botón no bajó nada')),
      boton.click(),
    ]);
    const nombre = descarga.suggestedFilename();
    if (!/^catalogo_.+\.xlsx$/.test(nombre)) falla(ancho + ' px: el archivo se llama «' + nombre + '»');
    const archivo = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'd1a-')), nombre);
    await descarga.saveAs(archivo);

    // Se lee con openpyxl: descripciones en el orden de la pantalla, la
    // posición como texto y la fórmula como texto.
    const leido = JSON.parse(execFileSync(PY, ['-I', '-c', [
      'import json, sys',
      'from openpyxl import load_workbook',
      'ws = load_workbook(sys.argv[1]).active',
      'filas = list(ws.iter_rows(min_row=2))',
      'print(json.dumps([[f[0].value, f[0].data_type, f[1].value, f[1].data_type] for f in filas]))',
    ].join('\n'), archivo]).toString());
    const descripciones = leido.map(f => f[2]);
    if (JSON.stringify(descripciones) !== JSON.stringify(enPantalla)) {
      falla(ancho + ' px: el Excel trae ' + JSON.stringify(descripciones) + ' y la pantalla muestra ' + JSON.stringify(enPantalla));
    }
    if (JSON.stringify(leido.map(f => f[0])) !== JSON.stringify(enPantallaApi.map(p => p.ncm))) {
      falla(ancho + ' px: las posiciones del Excel no son las guardadas: ' + JSON.stringify(leido.map(f => f[0])));
    }
    if (leido.some(f => f[1] !== 's' || f[3] !== 's')) falla(ancho + ' px: una celda de texto no quedó como texto: ' + JSON.stringify(leido));
    console.log('OK ' + ancho + ' px: «' + nombre + '» trae ' + JSON.stringify(descripciones) + ', posiciones ' + JSON.stringify(leido.map(f => f[0])) + ', todo como texto');
    await ctx.close();
  }
  await b.close();
})().catch(e => falla(String(e && e.stack || e)));
