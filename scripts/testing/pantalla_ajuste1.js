// Un ajuste del valor mal escrito, después de recargar la página: la operación
// se recupera con ese texto y el aviso lo nombra, así que el campo tiene que
// mostrarlo para que la persona lo corrija. Navegador local, servidor local.
// Datos inventados. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_ajuste1.js
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8822';
const OP = { numero_factura: 'INV-2026/0612', moneda: 'DOL', incoterm: 'FOB', comprador_cuit: '30712345671',
             comprador_nombre: 'Importadora Inventada SA', vendedor_nombre: 'Proveedor Inventado Ltd',
             fecha_emision: '10/10/2026', flete: 100, seguro: 10 };
const ITEM = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };
// campo, lo que se escribe, cómo lo nombra el aviso
const AJUSTES = [
  ['valorIncluir', 'abc', 'Ajustes a incluir:'],
  ['valorDeducir', '1,500', 'Ajustes a deducir:'],
];

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext()).newPage();
  const id = Date.now();
  await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() },
    data: { username: 'aj1_' + id, password: 'Clave-Inventada-123', email: 'aj1' + id + '@ejemplo.test' } });
  const aviso = () => page.$eval('#valorError', el => el.hidden ? '' : el.textContent);
  const avisoCompleto = () => page.waitForFunction(nombres => {
    const el = document.getElementById('valorError');
    return el && !el.hidden && nombres.every(n => el.textContent.includes(n));
  }, AJUSTES.map(a => a[2]), { timeout: 15000 });

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.currentUser);
  await page.evaluate(([op, items]) => {
    CDI.state = { operacion: op, items };
    CDI.goTo('validating');
  }, [OP, [ITEM]]);
  await page.waitForSelector('#valorIncluir', { state: 'visible' });
  for (const [campo, texto] of AJUSTES) await page.fill('#' + campo, texto);
  await avisoCompleto().catch(async () => falla('antes de recargar el aviso no nombra los dos ajustes: «' + await aviso() + '»'));

  await page.reload();
  await page.waitForFunction(f => window.CDI && CDI.state && CDI.state.operacion && CDI.state.operacion.numero_factura === f
    && document.querySelector('.screen.is-active')?.dataset.screen === 'review', OP.numero_factura, { timeout: 20000 })
    .catch(e => falla('al recargar la operación no se recuperó: ' + e.message.split('\n')[0]));
  await page.evaluate(() => CDI.goTo('validating'));
  await avisoCompleto().catch(async () => falla('después de recargar el aviso no nombra los dos ajustes: «' + await aviso() + '»'));

  let mal = 0;
  for (const [campo, texto, nombre] of AJUSTES) {
    const visto = await page.inputValue('#' + campo);
    if (visto === texto) { console.log('OK ' + nombre + ' el campo muestra «' + texto + '» después de recargar'); continue; }
    console.error('FALLA: el aviso dice «' + await aviso() + '» y el campo de ' + nombre + ' muestra «' + visto + '», no «' + texto + '»');
    mal++;
  }
  await b.close();
  if (mal) process.exit(1);
  console.log('PANTALLA AJUSTE-1 OK');
})().catch(e => falla(e && e.stack || e));
