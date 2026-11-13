// Con un CUIT que no es un CUIT guardado en «Mi perfil» (se siembra directo en la base local del servidor,
// CDI_DB: «Mi perfil» no lo guardaría), «Generar» no da el TXT y el error dice dónde se corrige, con el
// nombre que el campo tiene en pantalla. Corregido ahí, «Reintentar» genera con ese CUIT en el CDDTAGR.
// Navegador local, servidor local. Datos inventados. Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> CDI_DB=<base sqlite del servidor> node scripts/testing/pantalla_cuit_generar1.js
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const base = process.env.BASE_URL || 'http://127.0.0.1:8824';
const baseLocal = process.env.CDI_DB || falla('falta CDI_DB: la base sqlite local del servidor, para sembrar un CUIT guardado');
const MALO = '20999999998', BUENO = '20111111112';
const OP = { numero_factura: 'INV-2026/0844', moneda: 'DOL', incoterm: 'CFR', comprador_cuit: '30712345671',
             fecha_emision: '10/10/2026' };
const ITEM = { pieza: '39211390900F', descripcion: 'Lona de PVC gris', origen: 'CN', cantidad: 750,
               valor_unitario: 1.85, peso_unitario: 0.62 };

(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  const usuario = 'cg1_' + Date.now();
  await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() },
    data: { username: usuario, password: 'Clave-Inventada-123', email: usuario + '@ejemplo.test' } });
  execFileSync('python3', ['-c',
    'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute("UPDATE users SET cuit=? WHERE username=?", (sys.argv[3], sys.argv[2])).rowcount; c.commit(); sys.exit(0 if n == 1 else 1)',
    baseLocal, usuario, MALO]);

  // Toca el botón y devuelve lo que quedó a la vista («generado» o el error) y los CDDTAGR del TXT.
  const generar = async boton => {
    const pedido = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 20000 });
    await page.click(boton);
    const cuerpo = await (await pedido.catch(() => falla('no se pidió el TXT'))).json();
    const visto = await (await page.waitForFunction(() => {
      const visible = id => !document.getElementById(id).hidden;
      if (visible('readyDone')) return 'generado';
      return visible('readyError') ? 'error: ' + document.getElementById('readyErrorText').textContent.trim() : false;
    }, null, { timeout: 15000 })).jsonValue();
    return [visto, [...String(cuerpo.content || '').matchAll(/^CDDTAGR=([^\r\n]*)/mg)].map(m => m[1])];
  };

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.openProfileModal && CDI.currentUser);
  await page.evaluate(([op, items]) => { CDI.state = { operacion: op, items }; CDI.goTo('validating'); }, [OP, [ITEM]]);
  await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled, null, { timeout: 15000 })
    .catch(e => falla('la validación no terminó: ' + e.message.split('\n')[0]));
  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');

  let [visto, cddtagr] = await generar('#validatingGenerate');
  if (visto === 'generado') falla('con ' + MALO + ' guardado en el perfil se generó el TXT: CDDTAGR=' + cddtagr.join());
  const donde = 'Corregilo en «Mi perfil», campo «' + (await page.textContent('label[for="pfCuit"]')).trim() + '».';
  if (!visto.includes('«' + MALO + '»') || !visto.endsWith(donde)) {
    falla('con ' + MALO + ' guardado en el perfil, la pantalla no dice cuál es ni «' + donde + '»: ' + visto);
  }
  console.log('OK con ' + MALO + ' guardado en el perfil no se genera: ' + visto);

  await page.evaluate(() => CDI.openProfileModal());
  await page.waitForSelector('#profileModal.is-open');
  await page.fill('#pfCuit', BUENO);
  await page.click('#profileSave');
  await page.waitForFunction(() => !document.getElementById('profileModal').classList.contains('is-open'), null, { timeout: 15000 })
    .catch(async () => falla('«Mi perfil» no guardó ' + BUENO + ': ' + await page.textContent('#pfCuitError')));
  [visto, cddtagr] = await generar('[data-action="retry-generate"]');
  if (visto !== 'generado' || cddtagr.join() !== BUENO) {
    falla('corregido en «Mi perfil», «Reintentar» terminó en «' + visto + '» con CDDTAGR=' + cddtagr.join());
  }
  console.log('OK corregido en «Mi perfil», «Reintentar» genera con CDDTAGR=' + BUENO);
  await b.close();
  console.log('PANTALLA CUIT-GENERAR-1 OK');
})().catch(e => falla(e && e.stack || e));
