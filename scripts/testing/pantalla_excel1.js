// EXCEL-1 en el navegador local. La subida del Excel se simula: devuelve 2
// filas sin leer y el catálogo de columnas completo. Antes, el aviso del
// catálogo pisaba al de las filas sin leer y el usuario no se enteraba.
// Comprueba que, terminada la subida, el aviso en pantalla nombra las filas.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_excel1.js <xlsx> [captura.png]
// corredor: argumentos tests/test_facturas.xlsx
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
const AVISO = '2 fila(s) del Excel no se pudieron leer (filas 7, 9)';
function falla(msg) { console.error('FALLA: ' + msg); process.exit(1); }
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await registrarCuenta(page.request, base, { data: { username: 'prueba_' + id, password: 'Clave-Inventada-123', email: 'p' + id + '@ejemplo.test' } });
  await page.route('**/upload_excel_v2/**', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
    message: 'ok', filename: 'factura.xlsx', items_count: 1,
    operacion: { filas_excel_sin_leer: [7, 9], filas_excel_sin_leer_total: 2 },
    filas_descartadas: 2, filas_descartadas_numeros: [7, 9], applied_mapping: true,
    catalogo: { columnas_detectadas: 6, columnas_faltantes: [], total: 6, completo: true },
    items: [{ descripcion: 'Tornillo de acero inoxidable M6', cantidad: 2, valor_unitario: 3, peso_unitario: 1, origen: 'CN', pieza: '84713000' }] }) }));
  await page.goto(base + '/dashboard');
  await page.waitForSelector('#uploadFileInput', { state: 'attached' });
  await page.click('#uploadFormatExcel');
  await page.setInputFiles('#uploadFileInput', process.argv[2]);
  // Sin clientes: se cancela la elección de cliente y se sigue igual.
  await page.getByRole('button', { name: 'Cancelar', exact: true }).first().click({ timeout: 8000 })
    .catch(() => falla('no apareció la elección de cliente'));
  await page.locator('#cdiConfirmAccept').click({ timeout: 8000 })
    .catch(() => falla('no apareció «Continuar igual»'));
  // Terminada la subida (ya en la revisión), el aviso que queda es el de las filas.
  await page.waitForFunction(() => window.CDI && CDI.state && (CDI.state.items || []).length === 1, null, { timeout: 10000 })
    .catch(async () => { if (process.argv[3]) await page.screenshot({ path: process.argv[3] }); falla('la subida simulada no terminó'); });
  await page.waitForTimeout(300);
  const texto = await page.locator('#toastHost').innerText().catch(() => '');
  if (process.argv[3]) await page.screenshot({ path: process.argv[3] });
  if (!texto.includes(AVISO)) falla('el aviso en pantalla no nombra las filas sin leer: «' + texto + '»');
  console.log('OK aviso de filas sin leer visible al terminar la subida');
  await b.close();
  console.log('OK: pantalla EXCEL-1');
})().catch(e => falla(e.message));
