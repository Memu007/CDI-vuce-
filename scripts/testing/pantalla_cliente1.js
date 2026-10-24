// CLIENTE-1 en el navegador local, contra el servidor local (sin terceros).
// El alta de cliente muestra arriba lo que pide el MARIA (razón social, CUIT,
// domicilio e inicio de actividad); email y teléfono quedan en «Más datos».
// Se guarda sin esos datos, con un aviso que dice cuáles faltan; con los
// cuatro no hay aviso. El detalle del cliente muestra el inicio de actividad.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_cliente1.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await page.request.post(base + '/auth/register', { data: { username: 'c1_' + id, password: 'Clave-Inventada-123', email: 'c1' + id + '@ejemplo.test' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo);
  await page.evaluate(() => CDI.goTo('clientes'));
  await page.locator('#cxNewBtn').click();
  await page.locator('#cfNombre').waitFor({ state: 'visible', timeout: 10000 });

  // Lo que pide el MARIA, a la vista sin abrir «Más datos» y marcado.
  for (const [campo, nombre] of [['cfCuit', 'CUIT'], ['cfDireccion', 'domicilio'], ['cfFechaInicActiv', 'inicio de actividad']]) {
    if (!(await page.locator('#' + campo).isVisible())) falla(nombre + ' no está a la vista en el alta');
    const rotulo = await page.locator('label[for="' + campo + '"]').innerText();
    if (!/lo pide el MARIA/.test(rotulo)) falla('el rótulo de ' + nombre + ' no dice «lo pide el MARIA»: ' + rotulo);
  }
  for (const campo of ['cfEmail', 'cfTelefono']) {
    if (!(await page.locator('#cfAdvanced #' + campo).count())) falla(campo + ' no está en «Más datos»');
    if (await page.locator('#' + campo).isVisible()) falla(campo + ' está a la vista: tenía que quedar en «Más datos»');
  }
  console.log('OK razón social, CUIT, domicilio e inicio de actividad a la vista; email y teléfono en «Más datos»');

  // Sin domicilio ni inicio de actividad: se guarda, con aviso de cuáles faltan.
  const toast = page.locator('#toastHost .toast');
  await page.fill('#cfNombre', 'Cliente Inventado Uno SA');
  await page.fill('#cfCuit', '20-12345678-6');
  await page.locator('#cxFormSave').click();
  await toast.waitFor({ timeout: 10000 }).catch(() => falla('no apareció ningún aviso al guardar'));
  const aviso = await toast.innerText();
  if (!(await toast.evaluate(el => el.classList.contains('is-warning')))) falla('el aviso no es de advertencia: ' + aviso);
  const icono = await toast.locator('.toast-icon').innerText();
  if (icono.trim() !== '!') falla('el aviso de advertencia tiene el ícono «' + icono + '», no «!»');
  if (!/domicilio/i.test(aviso) || !/inicio de actividad/i.test(aviso)) falla('el aviso no dice qué falta: ' + aviso);
  if (/CUIT/.test(aviso)) falla('el aviso dice que falta el CUIT, y se cargó: ' + aviso);
  const lista = await (await page.request.get(base + '/api/clientes')).json();
  const clientes = lista.clientes || lista;
  const uno = clientes.find(c => c.nombre === 'Cliente Inventado Uno SA');
  if (!uno) falla('el cliente sin domicilio ni inicio de actividad no se guardó');
  if (await page.locator('#cxFormModal').evaluate(el => el.open)) falla('el formulario quedó abierto después de guardar');
  console.log('OK sin domicilio ni inicio de actividad se guarda y avisa: ' + aviso.replace(/\s+/g, ' '));

  // El detalle muestra el inicio de actividad (vacío, con guion), a la vista
  // en la pestaña Datos.
  async function verDatos() {
    await page.locator('#cxTabDatos').click();
    const grid = page.locator('#cxDatosGrid');
    if (!(await grid.isVisible())) falla('la pestaña Datos no muestra el detalle del cliente');
    return grid.innerText();
  }
  const datos = await verDatos();
  if (!/Inicio de actividad\s*—/i.test(datos)) falla('el detalle del cliente no muestra el inicio de actividad: ' + datos);

  // Con los cuatro datos: sin aviso de lo que falta.
  await page.locator('#cxNewBtn').click();
  await page.locator('#cfNombre').waitFor({ state: 'visible', timeout: 10000 });
  await page.fill('#cfNombre', 'Cliente Inventado Dos SRL');
  await page.fill('#cfCuit', '30-71234567-1');
  await page.fill('#cfDireccion', 'Calle Inventada 123, CABA');
  await page.fill('#cfFechaInicActiv', '2015-03-01');
  await page.locator('#cxFormSave').click();
  await page.locator('#toastHost .toast', { hasText: 'Cliente Inventado Dos SRL' }).waitFor({ timeout: 10000 })
    .catch(() => falla('no apareció el aviso de cliente creado'));
  const ok = await toast.innerText();
  if (/falta/i.test(ok) || await toast.evaluate(el => el.classList.contains('is-warning'))) falla('con los cuatro datos igual avisa que falta algo: ' + ok);
  const datos2 = await verDatos();
  if (!/Inicio de actividad\s*01\/03\/2015/i.test(datos2)) falla('el detalle no muestra el inicio de actividad cargado como 01/03/2015: ' + datos2);
  console.log('OK con los cuatro datos no avisa nada y el detalle muestra el inicio de actividad');

  // Una fecha guardada que no es AAAA-MM-DD (por la API) se muestra tal cual,
  // no como vacía.
  await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente Inventado Tres SA', cuit: '20123456786', fecha_inic_activ: '01/03/2015' } });
  await page.reload();
  await page.waitForFunction(() => window.CDI && CDI.goTo);
  await page.evaluate(() => CDI.goTo('clientes'));
  await page.locator('.cx-card', { hasText: 'Cliente Inventado Tres SA' }).click();
  const datos3 = await verDatos();
  if (!/Inicio de actividad\s*01\/03\/2015/i.test(datos3)) falla('una fecha guardada que no es AAAA-MM-DD se muestra como vacía: ' + datos3);
  console.log('OK una fecha guardada en otro formato se muestra tal cual');

  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });
  await b.close();
  console.log('PANTALLA CLIENTE-1 OK');
})().catch(e => falla(e.message));
