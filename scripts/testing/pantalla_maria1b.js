// MARIA-1b en el navegador local. La subida del Excel se simula: devuelve 2
// filas sin leer y otra hoja con datos, sin moneda y con un CUIT inválido.
// Comprueba que el semáforo: muestra las filas y la hoja sin leer, las sigue
// mostrando después de otra validación, las saca con «Descartar», y muestra
// los errores de la cabecera que controla el servidor (moneda y CUIT).
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria1b.js <xlsx> [captura.png]
// corredor: argumentos tests/test_facturas.xlsx
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
const FILAS = '2 fila(s) del Excel no se pudieron leer (filas 7, 9)';
const HOJAS = 'El Excel tiene otras hojas con datos que no se leyeron (Hoja2)';
const SIN_REVISAR = 'No se revisaron todas las hojas del libro';
const CUIT = 'El CUIT del importador';
const MONEDA = 'Falta la moneda de la operación.';
function falla(msg) { console.error('FALLA: ' + msg); process.exit(1); }
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await registrarCuenta(page.request, base, { data: { username: 'prueba_' + id, password: 'Clave-Inventada-123', email: 'p' + id + '@ejemplo.test' } });
  await page.route('**/upload_excel_v2/**', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
    message: 'ok', filename: 'factura.xlsx', items_count: 1, applied_mapping: true,
    operacion: { comprador_cuit: '30712345670', incoterm: 'FOB',
                 filas_excel_sin_leer: [7, 9], filas_excel_sin_leer_total: 2, hojas_excel_sin_leer: ['Hoja2'],
                 hojas_excel_sin_revisar: true },
    catalogo: { columnas_detectadas: 6, columnas_faltantes: [], total: 6, completo: true },
    items: [{ descripcion: 'Tornillo de acero inoxidable M6', cantidad: 2, valor_unitario: 3, peso_unitario: 1, origen: 'CN', pieza: '84713000' }] }) }));
  await page.goto(base + '/dashboard');
  await page.waitForSelector('#uploadFileInput', { state: 'attached' });
  await page.click('#uploadFormatExcel');
  await page.setInputFiles('#uploadFileInput', process.argv[2]);
  await page.getByRole('button', { name: 'Cancelar', exact: true }).first().click({ timeout: 8000 })
    .catch(() => falla('no apareció la elección de cliente'));
  await page.locator('#cdiConfirmAccept').click({ timeout: 8000 }).catch(() => falla('no apareció «Continuar igual»'));
  await page.waitForFunction(() => window.CDI && CDI.state && (CDI.state.items || []).length === 1, null, { timeout: 10000 })
    .catch(() => falla('la subida simulada no terminó'));

  const lista = page.locator('.semaforo-list');
  const abrir = async () => { if (!(await lista.first().isVisible().catch(() => false))) await page.locator('#semaforoFAB').click(); };
  const esperar = async (texto, presente, que) => {
    await abrir();
    const l = page.locator('.semaforo-item', { hasText: texto });
    await (presente ? l.first().waitFor({ timeout: 10000 }) : l.first().waitFor({ state: 'detached', timeout: 10000 }))
      .catch(() => falla(que));
  };
  await esperar(FILAS, true, 'el semáforo no muestra las filas sin leer');
  await esperar(HOJAS, true, 'el semáforo no muestra la otra hoja con datos');
  await esperar(SIN_REVISAR, true, 'el semáforo no dice que no se revisaron todas las hojas');
  await esperar(CUIT, true, 'el semáforo no muestra el CUIT inválido');
  await esperar(MONEDA, true, 'el semáforo no muestra la moneda que falta');
  if (process.argv[3]) await page.screenshot({ path: process.argv[3] });
  console.log('OK semáforo: filas, hoja, hojas sin revisar, CUIT y moneda');

  // Otra validación (cambia un dato) no se lleva el aviso.
  await page.evaluate(() => { CDI.state.items[0].cantidad = 3; CDI.semaforo && CDI.semaforo.refresh && CDI.semaforo.refresh(); });
  await page.waitForTimeout(1500);
  await esperar(FILAS, true, 'el aviso de filas se fue sin descartarlo');
  console.log('OK el aviso sigue después de otra validación');

  await page.locator('.semaforo-item', { hasText: FILAS }).locator('.semaforo-descartar').click()
    .catch(() => falla('el aviso de filas no tiene «Descartar»'));
  // Sin volver a abrirlo: «Descartar» no cierra el semáforo.
  await page.waitForTimeout(300);
  if (!(await lista.first().isVisible().catch(() => false))) falla('«Descartar» cerró el semáforo');
  await esperar(FILAS, false, '«Descartar» no saca el aviso de filas');
  await esperar(HOJAS, true, 'descartar las filas se llevó también el de la hoja');
  console.log('OK «Descartar» saca sólo ese aviso');
  await b.close();
  console.log('OK: pantalla MARIA-1b');
})().catch(e => falla(e.message));
