// MARIA-1c en el navegador local: la subida (simulada, sin Gemini ni internet)
// devuelve flete y seguro sin leer; el aviso y el semáforo los nombran, y al
// completar el flete su aviso se apaga.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria1c.js <pdf> <captura.png>
const { chromium } = require('/opt/node-tools/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  await page.request.post(base + '/auth/register', { data: { username: 'prueba_' + Date.now(), password: 'Clave-Inventada-123', email: 'p' + Date.now() + '@ejemplo.test' } });
  // La lectura del PDF se simula: ni Gemini ni internet.
  await page.route('**/upload_pdf/public', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
    message: 'ok', filename: 'factura.pdf', items_count: 1,
    operacion: { numero_factura: 'F-1', flete: 0, seguro: 0, campos_sin_leer: ['flete', 'seguro'] },
    items: [{ descripcion: 'Tornillo', cantidad: 2, valor_unitario: 3, peso_unitario: 1, origen: 'CN', pieza: '' }] }) }));
  await page.goto(base + '/dashboard');
  await page.waitForSelector('#uploadFileInput', { state: 'attached' });
  await page.setInputFiles('#uploadFileInput', process.argv[2]);
  await page.waitForTimeout(2500);
  console.log('toast:', (await page.locator('.toast, [class*="toast"]').allTextContents()).join(' | ').slice(0, 200));
  const fab = page.locator('#semaforoFab, [class*="semaforo-fab"]').first();
  console.log('semaforo:', (await fab.textContent() || '').trim());
  await fab.click().catch(() => {});
  await page.waitForTimeout(300);
  console.log('popover:', ((await page.locator('[class*="semaforo-list"]').allTextContents()).join(' | ')).slice(0, 300));
  await page.screenshot({ path: process.argv[3] });
  await page.fill('[name="flete"]', '1500');
  await page.waitForTimeout(1500);
  console.log('tras completar flete:', ((await page.locator('[class*="semaforo-list"]').allTextContents()).join(' | ')).slice(0, 300));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
