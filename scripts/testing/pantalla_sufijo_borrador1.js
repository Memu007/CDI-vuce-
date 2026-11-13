// El sufijo de valor de la operación, después de recargar la página: la
// operación se recupera con su sufijo y el campo tiene que mostrarlo, lo haya
// guardado «Generar» (el servidor lo rechaza y devuelve a la validación), se
// haya escrito sin generar o se haya borrado. Navegador local, servidor
// local. Datos inventados.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_sufijo_borrador1.js
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8823';
const OP = { numero_factura: 'INV-2026/0731', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671',
             fecha_emision: '10/10/2026' };
const ITEM = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };
// lo que se escribe, si se genera con eso, cómo se nombra el paso
const SUFIJOS = [
  ['AA(000123)-AB(000456)', false, 'escrito sin generar'],
  ['ROJO', true, 'generado y devuelto a la validación'],
  ['', false, 'borrado sin generar'],
];

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const id = Date.now();
  await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() },
    data: { username: 'sb1_' + id, password: 'Clave-Inventada-123', email: 'sb1' + id + '@ejemplo.test' } });
  const guardado = () => page.evaluate(() => String((CDI.state.operacion || {}).sbt_sufijo_valor || ''));

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.currentUser);
  await page.evaluate(([op, items]) => {
    CDI.state = { operacion: op, items };
    CDI.goTo('validating');
  }, [OP, [ITEM]]);

  let mal = 0;
  for (const [texto, generar, paso] of SUFIJOS) {
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
      .catch(e => falla(paso + ': la validación no terminó: ' + e.message.split('\n')[0]));
    await page.fill('#sbtSufijoValor', texto);
    if (generar) {
      await page.click('#validatingGenerate');
      await page.waitForFunction(t => {
        const el = document.getElementById('sbtFieldError');
        return el && !el.hidden && el.textContent.startsWith('Sufijo de valor de la operación: «' + t + '»');
      }, texto, { timeout: 15000 }).catch(e => falla(paso + ': el servidor no devolvió a la validación: ' + e.message.split('\n')[0]));
    }

    await page.reload();
    await page.waitForFunction(f => window.CDI && CDI.state && CDI.state.operacion && CDI.state.operacion.numero_factura === f
      && document.querySelector('.screen.is-active')?.dataset.screen === 'review', OP.numero_factura, { timeout: 20000 })
      .catch(e => falla(paso + ': al recargar la operación no se recuperó: ' + e.message.split('\n')[0]));
    await page.evaluate(() => CDI.goTo('validating'));
    await page.waitForSelector('#sbtSufijoValor', { state: 'visible' });

    const visto = await page.inputValue('#sbtSufijoValor');
    if (visto === texto && await guardado() === texto) { console.log('OK ' + paso + ': el campo muestra «' + texto + '» después de recargar'); continue; }
    console.error('FALLA: ' + paso + ': se escribió «' + texto + '», la operación recuperada guarda «' + await guardado() +
      '» y el campo muestra «' + visto + '»');
    mal++;
  }
  await b.close();
  if (mal) process.exit(1);
  console.log('PANTALLA SUFIJO-BORRADOR OK');
})().catch(e => falla(e && e.stack || e));
