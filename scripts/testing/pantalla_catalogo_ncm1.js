// CATALOGO-NCM-1 en el navegador local, contra el servidor local (sin terceros).
// El historial del despachante tiene un celular con la NCM 8517.12.31, que se
// dio de baja en el nomenclador vigente. Al abrir el asistente de NCM, la
// sugerencia aparece con el aviso de la baja (no como «Lista para asignar»).
// La validación avisa la baja sin frenar.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_catalogo_ncm1.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await registrarCuenta(page.request, base, { data: { username: 'ncm1_' + id, password: 'Clave-Inventada-123', email: 'ncm1' + id + '@ejemplo.test' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api);
  const desc = 'Telefono celular de prueba ' + id;
  const r = await page.evaluate(d => CDI.api('/api/ncm/guardar-uso', { method: 'POST', body: JSON.stringify({ descripcion: d, ncm: '85171231' }) }).then(x => x.status), desc);
  if (r !== 200) falla('no se pudo guardar el historial (' + r + ')');

  await page.evaluate(d => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = { numero_factura: 'F-NCM1', moneda: 'DOL', incoterm: 'FOB', fecha_emision: '22/06/2026' };
    CDI.state.items = [{ pieza: '', descripcion: d, origen: 'CN', cantidad: 2, valor_unitario: 100, peso_unitario: 0.2 }];
    CDI.goTo('ncm');
  }, desc);
  await page.locator('[data-assist="0"]').first().click({ timeout: 10000 }).catch(() => falla('no se pudo abrir el asistente de NCM'));
  const item = page.locator('#spotResults .spotlight-item', { hasText: '8517.12.31' }).first();
  await item.waitFor({ timeout: 15000 }).catch(() => falla('el asistente no muestra la sugerencia del historial'));
  const texto = await item.innerText();
  if (!/se dio de baja/.test(texto) || !/buscá la nueva/.test(texto)) falla('la sugerencia dada de baja no lo dice: ' + texto);
  if (/Lista para asignar/.test(texto)) falla('la sugerencia dada de baja dice «Lista para asignar»');
  if (!(await item.evaluate(el => el.classList.contains('is-baja')))) falla('la sugerencia no tiene la marca de baja');
  console.log('OK el asistente propone 8517.12.31 diciendo que se dio de baja: ' + texto.replace(/\s+/g, ' '));
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: false });

  // Escribir el código en el asistente también lo dice (revisión adversaria):
  // la SIM completa se puede asignar, con el aviso; la partida sola, el aviso.
  // Se mira el resultado del código escrito, no la sugerencia de antes.
  const manual = page.locator('#spotResults .spotlight-item', { hasText: 'Asignar este código manualmente' });
  const vacio = page.locator('#spotResults .spotlight-empty');
  for (const [escrito, dice, donde] of [['8517.12.31.000X', /se dio de baja/, manual], ['8517.12', /se dieron de baja/, vacio]]) {
    await page.fill('#spotSearch', escrito);
    await donde.filter({ hasText: dice }).first().waitFor({ timeout: 10000 })
      .catch(async () => falla('escribir ' + escrito + ' no avisa la baja: ' + await page.locator('#spotResults').innerText()));
  }
  const respuesta = page.waitForResponse(r => r.url().includes('/api/ncm/aviso') && r.url().includes('8471'), { timeout: 10000 });
  await page.fill('#spotSearch', '8471.49.00.100D');
  const aviso = await (await respuesta.catch(() => falla('no se pidió el aviso de 8471.49.00.100D'))).json();
  if (aviso.aviso) falla('el servidor avisa en falso: ' + aviso.aviso);
  await page.locator('#spotResults', { hasText: 'Asignar este código manualmente' }).waitFor({ timeout: 10000 });
  if (/baja|nomenclador/.test(await page.locator('#spotResults').innerText())) falla('una SIM vigente avisa en falso');
  console.log('OK escribir 8517.12.31.000X o 8517.12 avisa la baja; 8471.49.00.100D, no');

  const v = await page.evaluate(d => CDI.api('/api/validate/smart', { method: 'POST', body: JSON.stringify({ items: [
    { pieza: '85171231000X', descripcion: d, origen: 'CN', cantidad: 2, valor_unitario: 100, peso_unitario: 0.2 }] }) })
    .then(x => x.json()), desc);
  if (!(v.advertencias || []).some(a => /se dio de baja/.test(a))) falla('la validación no avisa la baja: ' + JSON.stringify(v.advertencias));
  if ((v.errores || []).some(e => /baja/.test(e))) falla('la baja frena: ' + JSON.stringify(v.errores));
  console.log('OK la validación avisa la baja sin frenar');
  await b.close();
  console.log('OK: pantalla CATALOGO-NCM-1');
})().catch(e => falla(e.message));
