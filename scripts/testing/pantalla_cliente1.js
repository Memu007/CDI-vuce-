// CLIENTE-1 en el navegador local, contra el servidor local (sin terceros).
// El alta de cliente muestra arriba lo que pide el MARIA (razón social, CUIT,
// domicilio e inicio de actividad); email y teléfono quedan en «Más datos».
// Se guarda sin esos datos, con un aviso que dice cuáles faltan; con los
// cuatro no hay aviso. El detalle del cliente muestra el inicio de actividad.
// D3: editar no borra una fecha guardada que el campo de fecha no puede mostrar.
// Una fecha tipeada a medias no se guarda callada.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_cliente1.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  // openForm() pone el foco en la razón social con un temporizador: si se
  // llena otro campo antes de que llegue, lo escrito cae en la razón social
  // («Nombre20-12345678-6») y el CUIT queda vacío. Se espera ese foco.
  async function formularioListo() {
    await page.locator('#cfNombre').waitFor({ state: 'visible', timeout: 10000 });
    await page.waitForFunction(() => document.activeElement && document.activeElement.id === 'cfNombre', null, { timeout: 10000 })
      .catch(() => falla('el formulario abierto no puso el foco en la razón social'));
  }
  await page.request.post(base + '/auth/register', { data: { username: 'c1_' + id, password: 'Clave-Inventada-123', email: 'c1' + id + '@ejemplo.test' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo);
  await page.evaluate(() => CDI.goTo('clientes'));
  await page.locator('#cxNewBtn').click();
  await formularioListo();

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
  await formularioListo();
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

  // D3: editar un cliente sin tocar la fecha no la borra aunque el campo de
  // fecha no la pueda mostrar (no es AAAA-MM-DD, o no es una fecha válida); si
  // se conserva, el aviso no dice que falta. Cargar o borrar una fecha a mano
  // sigue andando. Cada caso: fecha guardada, lo que se escribe en el campo
  // (null = no se toca), la fecha que tiene que quedar y si el aviso la pide.
  const casosD3 = [
    ['Nula', null, null, null, true],
    ['Vacía', '', null, null, true],
    ['Barras', '01/03/2015', null, '01/03/2015', false],
    ['Texto', 'mar-2015', null, 'mar-2015', false],
    ['ISO', '2015-03-01', null, '2015-03-01', false],
    ['Reemplazada', '01/03/2015', '2016-04-02', '2016-04-02', false],
    ['Borrada', '2015-03-01', '', null, true],
    ['Imposible', '2015-02-30', null, '2015-02-30', false],
  ];
  // Sin fecha, el campo no se manda: así guarda la pantalla (un null explícito
  // la API lo guarda como el texto «None»; queda anotado, fuera de D3).
  const idsD3 = {};
  for (const [n, guardada] of casosD3) {
    const datosD3 = { nombre: 'Cliente Inventado D3 ' + n + ' ' + id, cuit: '20123456786', direccion: 'Calle Inventada 1' };
    if (guardada !== null) datosD3.fecha_inic_activ = guardada;
    const r = await page.request.post(base + '/api/clientes', { data: datosD3 });
    idsD3[n] = (await r.json()).cliente.id;
  }
  await page.reload();
  await page.waitForFunction(() => window.CDI && CDI.goTo);
  await page.evaluate(() => CDI.goTo('clientes'));
  let ultimaConservada = false;
  for (const [n, , escribe, queda, pideFecha] of casosD3) {
    const nombreD3 = 'Cliente Inventado D3 ' + n + ' ' + id;
    await page.locator('.cx-card', { hasText: nombreD3 }).click();
    await page.locator('#cxKebabBtn').click();
    await page.locator('#cxKebabMenu [data-kaction="edit"]').click();
    await formularioListo();
    const campoVacio = (await page.inputValue('#cfFechaInicActiv')) === '';
    await page.fill('#cfDireccion', 'Calle Inventada 2');
    if (escribe !== null) await page.fill('#cfFechaInicActiv', escribe);
    await page.locator('#cxFormSave').click();
    const avisoD3 = page.locator('#toastHost .toast', { hasText: nombreD3 });
    await avisoD3.waitFor({ timeout: 10000 }).catch(() => falla(n + ': no apareció el aviso al guardar'));
    const textoD3 = (await avisoD3.innerText()).replace(/\s+/g, ' ');
    const c = (await (await page.request.get(base + '/api/clientes/' + idsD3[n])).json());
    const cli = c.cliente || c;
    if (cli.direccion !== 'Calle Inventada 2') falla(n + ': la edición no se guardó: ' + cli.direccion);
    const tiene = cli.fecha_inic_activ || null;
    if (tiene !== queda) falla(n + ': después de editar, la fecha es ' + JSON.stringify(tiene) + ' y tenía que ser ' + JSON.stringify(queda));
    if (/inicio de actividad/i.test(textoD3) !== pideFecha) {
      falla(n + ': el aviso ' + (pideFecha ? 'no dice' : 'dice') + ' que falta el inicio de actividad: ' + textoD3);
    }
    ultimaConservada = campoVacio && escribe === null && queda !== null;
  }
  // Lo recordado de la última edición (una fecha conservada) no pasa a un alta.
  // Sólo se ve si el último caso dejó una fecha conservada.
  if (!ultimaConservada) falla('el último caso de D3 tiene que dejar una fecha conservada (campo vacío, sin tocar, y queda)');
  await page.locator('#cxNewBtn').click();
  await formularioListo();
  await page.fill('#cfNombre', 'Cliente Inventado D3 Alta ' + id);
  await page.fill('#cfCuit', '20-12345678-6');
  await page.fill('#cfDireccion', 'Calle Inventada 3');
  await page.locator('#cxFormSave').click();
  const avisoAlta = page.locator('#toastHost .toast', { hasText: 'Cliente Inventado D3 Alta ' + id });
  await avisoAlta.waitFor({ timeout: 10000 }).catch(() => falla('no apareció el aviso del alta después de editar'));
  if (!/inicio de actividad/i.test(await avisoAlta.innerText())) falla('un alta sin fecha después de editar no avisa que falta el inicio de actividad');
  console.log('OK al editar, la fecha que el campo no muestra se conserva y no se avisa como faltante; cargarla o borrarla anda');

  // Una fecha tipeada a medias (el navegador la da como vacía) no se guarda
  // callada: ni conserva la fecha guardada ni la borra; el formulario lo dice.
  for (const [n, guardada] of [['A medias oculta', '01/03/2015'], ['A medias ISO', '2015-03-01']]) {
    const nombreM = 'Cliente Inventado D3 ' + n + ' ' + id;
    const r = await page.request.post(base + '/api/clientes', { data: { nombre: nombreM, cuit: '20123456786', direccion: 'Calle Inventada 1', fecha_inic_activ: guardada } });
    const idM = (await r.json()).cliente.id;
    await page.reload();
    await page.waitForFunction(() => window.CDI && CDI.goTo);
    await page.evaluate(() => CDI.goTo('clientes'));
    await page.locator('.cx-card', { hasText: nombreM }).click();
    await page.locator('#cxKebabBtn').click();
    await page.locator('#cxKebabMenu [data-kaction="edit"]').click();
    await formularioListo();
    await page.fill('#cfDireccion', 'Calle Inventada 2');
    await page.fill('#cfFechaInicActiv', '');
    await page.locator('#cfFechaInicActiv').click();
    await page.keyboard.type('03');
    const aMedias = await page.locator('#cfFechaInicActiv').evaluate(el => el.validity.badInput && el.value === '');
    if (!aMedias) falla(n + ': no se pudo dejar la fecha a medias en el campo');
    await page.locator('#cxFormSave').click();
    await page.locator('#cfError').waitFor({ state: 'visible', timeout: 5000 })
      .catch(() => falla(n + ': una fecha a medias se guardó sin decir nada'));
    const errorM = await page.locator('#cfError').innerText();
    if (!/inicio de actividad/i.test(errorM)) falla(n + ': el error no habla del inicio de actividad: ' + errorM);
    const cM = (await (await page.request.get(base + '/api/clientes/' + idM)).json());
    const cliM = cM.cliente || cM;
    if (cliM.direccion !== 'Calle Inventada 1' || (cliM.fecha_inic_activ || null) !== guardada) {
      falla(n + ': con la fecha a medias igual se guardó: ' + JSON.stringify([cliM.direccion, cliM.fecha_inic_activ]));
    }
    await page.keyboard.press('Escape');
  }
  console.log('OK una fecha tipeada a medias no se guarda: el formulario avisa');

  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });
  await b.close();
  console.log('PANTALLA CLIENTE-1 OK');
})().catch(e => falla(e.message));
