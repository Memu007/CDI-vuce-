// Al entrar a «Validación», el campo del sufijo de valor muestra el de la operación en curso, vacío si no
// tiene: una operación sin sufijo abierta después de otra que lo tenía no genera con el ajeno, y la tarjeta
// del despachante tampoco lo usa. Con el suyo escrito, los avisos y el TXT llevan ese.
// Navegador local, servidor local. Datos inventados.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_sufijo_otra1.js
const { chromium } = require('playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
const cuitDelPerfil = require('./_cuit_perfil');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8825';
const ANTERIOR = { numero_factura: 'INV-2026/0731', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671',
                   fecha_emision: '10/10/2026' };
const ITEM = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };
// Escrito cuando la operación no tenía sufijo: la tarjeta sólo lo marca si compara con uno que no es el suyo.
const ESCRITO = Object.assign({}, ITEM, { descripcion: 'Lona de PVC azul', sufijo: 'AI(Y7)-', sufijo_op: '' });
const AJENO = 'AA(000123)', PROPIO = 'AA(000456)', FRENO = 'Ingresá el sufijo de valor SBT. Es obligatorio.';
const OTRO = 'Lo escribiste con otro sufijo de la operación';
// cómo se llega a la otra operación: si antes se recarga, lo que trae guardado como sufijo, cómo se nombra
const LLEGADAS = [
  [true, {}, 'después de recuperar la anterior'],
  [false, {}, 'sin recargar'],
  [false, { sbt_sufijo_valor: '' }, 'con el sufijo borrado'],
];

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const id = Date.now();
  await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() },
    data: { username: 'so1_' + id, password: 'Clave-Inventada-123', email: 'so1' + id + '@ejemplo.test' } });
  await cuitDelPerfil(page.request, base);
  const esGenerar = r => r.url().endsWith('/generate_maria') && r.method() === 'POST';
  let generados = 0;
  page.on('request', r => { if (esGenerar(r)) generados++; });
  // Entra a «Validación» (con la operación dada, si hay) y devuelve, de ese mismo instante, lo que muestra el
  // campo, lo que guarda la operación y lo que dice la tarjeta del despachante del segundo producto.
  const entrar = (op, items) => page.evaluate(([op, items, otro]) => {
    if (op) CDI.state = { operacion: op, items };
    CDI.goTo('validating');
    const nota = document.querySelector('.despachante-sufijo-nota[data-row="1"]');
    return [document.getElementById('sbtSufijoValor').value, String(CDI.state.operacion.sbt_sufijo_valor || ''),
      !nota ? 'sin segundo producto' : nota.textContent.includes(otro) ? 'lo marca escrito con otro sufijo' : 'sin marca'].join(' / ');
  }, [op, items, OTRO]);

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.currentUser);
  let mal = 0;
  for (const [recargar, guardado, paso] of LLEGADAS) {
    await entrar(ANTERIOR, [ITEM]);
    await page.fill('#sbtSufijoValor', AJENO);
    if (recargar) {
      await page.reload();
      await page.waitForFunction(f => window.CDI && CDI.state && CDI.state.operacion && CDI.state.operacion.numero_factura === f
        && document.querySelector('.screen.is-active')?.dataset.screen === 'review', ANTERIOR.numero_factura, { timeout: 20000 })
        .catch(e => falla(paso + ': al recargar la operación no se recuperó: ' + e.message.split('\n')[0]));
      const volvio = await entrar();
      if (!volvio.startsWith(AJENO + ' / ' + AJENO + ' / ')) falla(paso + ': la anterior no volvió con su sufijo: ' + volvio);
    }
    await page.click('.topbar-nav [data-action="go-upload"]');
    const alEntrar = await entrar(Object.assign({}, ANTERIOR, { numero_factura: 'INV-2026/0732' }, guardado), [ITEM, ESCRITO]);
    const antes = generados;
    await page.click('#validatingGenerate');
    const quedo = await (await page.waitForFunction(freno => {
      const pantalla = document.querySelector('.screen.is-active').dataset.screen;
      if (pantalla !== 'validating') return 'siguió a «' + pantalla + '»';
      // El foco en el campo lo pone el freno de este clic: el aviso puede venir de la operación anterior.
      const el = document.getElementById('sbtFieldError');
      return !el.hidden && el.textContent === freno && document.activeElement.id === 'sbtSufijoValor' && 'frenó';
    }, FRENO, { timeout: 15000 })).jsonValue();
    // Si siguió, se espera a que termine de generar: la fila que sigue arranca sin un pedido en vuelo.
    if (quedo !== 'frenó') await page.waitForFunction(() => ['readyDone', 'readyError'].some(i => !document.getElementById(i).hidden), null, { timeout: 20000 });
    if (alEntrar === ' /  / sin marca' && quedo === 'frenó' && generados === antes) { console.log('OK ' + paso + ': el campo entra vacío, la tarjeta no usa el ajeno y «Generar» frena sin pedir el TXT'); continue; }
    console.error('FALLA: ' + paso + ': al entrar, campo / operación / tarjeta = «' + alEntrar + '»; «Generar» ' + quedo + ' y salieron ' +
      (generados - antes) + ' POST /generate_maria');
    mal++;
  }
  if (mal) process.exit(1);

  await entrar(Object.assign({}, ANTERIOR, { numero_factura: 'INV-2026/0733' }), [ITEM]);
  const avisado = page.waitForRequest(r => r.url().endsWith('/generate_maria/avisos') && (r.postDataJSON() || {}).sbt_sufijo_valor === PROPIO, { timeout: 15000 });
  await page.fill('#sbtSufijoValor', PROPIO);
  await avisado.catch(() => falla('con «' + PROPIO + '» escrito, los avisos no se pidieron con ese sufijo'));
  const txt = page.waitForResponse(r => esGenerar(r.request()), { timeout: 20000 });
  await page.click('#validatingGenerate');
  const r = await txt.catch(() => falla('con su sufijo escrito, «Generar» no pidió el TXT'));
  const en = [...String((await r.json()).content || '').matchAll(/^CSBTSVL=([^\r\n]*)/mg)].map(m => m[1]).join();
  if (r.status() !== 200 || en !== PROPIO) falla('con «' + PROPIO + '» escrito, /generate_maria dio ' + r.status() + ' con CSBTSVL=' + en);
  console.log('OK con su sufijo escrito, los avisos y el TXT llevan «' + PROPIO + '»');
  await b.close();
  console.log('PANTALLA SUFIJO-OTRA OK');
})().catch(e => falla(e && e.stack || e));
