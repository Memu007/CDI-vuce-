// MARIA-1c en el navegador local. La subida se simula (ni Gemini ni internet):
// devuelve flete y seguro sin leer. Comprueba que el aviso de la subida y el
// semáforo los nombran; que completar el flete con 0 apaga su aviso; que
// borrarlo lo vuelve a mostrar; y que el del seguro sigue mientras tanto.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria1c.js <pdf> [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const FLETE = 'No pudimos leer el flete de la factura: completalo.';
const SEGURO = 'No pudimos leer el seguro de la factura: completalo.';
function falla(msg) { console.error('FALLA: ' + msg); process.exit(1); }
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'prueba_' + id, password: 'Clave-Inventada-123', email: 'p' + id + '@ejemplo.test' } });
  await page.route('**/upload_pdf/public', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
    message: 'ok', filename: 'factura.pdf', items_count: 1,
    operacion: { numero_factura: 'F-1', flete: 0, seguro: 0, campos_sin_leer: ['flete', 'seguro'] },
    items: [{ descripcion: 'Tornillo de acero inoxidable M6', cantidad: 2, valor_unitario: 3, peso_unitario: 1, origen: 'CN', pieza: '' }] }) }));
  await page.goto(base + '/dashboard');
  await page.waitForSelector('#uploadFileInput', { state: 'attached' });
  await page.setInputFiles('#uploadFileInput', process.argv[2]);

  await page.locator('#toastHost .toast', { hasText: FLETE }).waitFor({ timeout: 10000 }).catch(() => falla('el aviso de la subida no nombra el flete'));
  console.log('OK aviso de la subida');

  const lista = page.locator('.semaforo-list');
  const abrir = async () => { if (!(await lista.first().isVisible().catch(() => false))) await page.locator('#semaforoFAB').click(); };
  const esperar = async (texto, presente, que) => {
    await abrir();
    const l = page.locator('.semaforo-item', { hasText: texto });
    await (presente ? l.first().waitFor({ timeout: 8000 }) : l.first().waitFor({ state: 'detached', timeout: 8000 }))
      .catch(() => falla(que));
  };
  await esperar(FLETE, true, 'el semáforo no avisa el flete');
  await esperar(SEGURO, true, 'el semáforo no avisa el seguro');
  if (process.argv[3]) await page.screenshot({ path: process.argv[3] });
  console.log('OK semáforo con flete y seguro');

  await page.fill('[name="flete"]', '0');
  await esperar(FLETE, false, 'completar el flete con 0 no apaga su aviso');
  await esperar(SEGURO, true, 'el aviso del seguro se fue sin completarlo');
  console.log('OK flete en 0 apaga su aviso; el seguro sigue');

  await page.fill('[name="flete"]', '');
  await esperar(FLETE, true, 'borrar el flete no vuelve a mostrar su aviso');
  console.log('OK borrar el flete lo vuelve a avisar');
  await b.close();
  console.log('OK: pantalla MARIA-1c');
})().catch(e => falla(e.message));
