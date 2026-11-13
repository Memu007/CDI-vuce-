// CLIENTE-1 en el navegador local, contra el servidor local (sin terceros).
// El alta de cliente muestra arriba lo que pide el MARIA (razón social, CUIT,
// domicilio e inicio de actividad); email y teléfono quedan en «Más datos».
// Se guarda sin esos datos, con un aviso que dice cuáles faltan; con los
// cuatro no hay aviso. El detalle del cliente muestra el inicio de actividad.
// D3: editar no borra una fecha guardada que el campo de fecha no puede mostrar.
// Una fecha tipeada a medias no se guarda callada.
// CLIENTE-1b: la API ya no guarda una fecha que no sirve; las viejas (de antes
// del arreglo) se siembran directo en la base local del servidor (CDI_DB). Una
// fecha conservada que el TXT no acepta se pide en el aviso, y el error de la
// API se ve en el formulario. CLIENTE-1c: si la conservada sirve lo dice el
// servidor, con el criterio del generador.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> CDI_DB=<base sqlite del servidor> node scripts/testing/pantalla_cliente1.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const ipNueva = require('./_ip_nueva');
const registrarCuenta = require('./_registrar');
const { execFileSync } = require('child_process');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const baseLocal = process.env.CDI_DB || falla('falta CDI_DB: la base sqlite local del servidor, para sembrar fechas viejas');
// Una fecha como quedaba guardada antes de CLIENTE-1b, sin pasar por la API.
function sembrarFecha(clienteId, fecha) {
  execFileSync('python3', ['-c',
    'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute("UPDATE clients SET fecha_inic_activ=? WHERE id=?", (sys.argv[3], sys.argv[2])).rowcount; c.commit(); sys.exit(0 if n == 1 else 1)',
    baseLocal, clienteId, fecha]);
}
(async () => {
  const b = await chromium.launch();
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
  await registrarCuenta(page.request, base, { headers: { 'X-Forwarded-For': ipNueva() }, data: { username: 'c1_' + id, password: 'Clave-Inventada-123', email: 'c1' + id + '@ejemplo.test' } });
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

  // Una fecha guardada que no es AAAA-MM-DD (vieja) se muestra tal cual, no
  // como vacía.
  const rTres = await page.request.post(base + '/api/clientes', { data: { nombre: 'Cliente Inventado Tres SA', cuit: '20123456786' } });
  sembrarFecha((await rTres.json()).cliente.id, '01/03/2015');
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
  // sigue andando. CLIENTE-1b: si la conservada no la acepta el TXT, el aviso
  // la pide. Cada caso: fecha guardada, si es vieja (se siembra en la base: la
  // API ya no la acepta), lo que se escribe en el campo (null = no se toca), la
  // fecha que tiene que quedar y si el aviso la pide.
  const casosD3 = [
    ['Nula', null, false, null, null, true],
    ['Vacía', '', false, null, null, true],
    ['Barras', '01/03/2015', true, null, '01/03/2015', false],
    ['Texto', 'mar-2015', true, null, 'mar-2015', true],
    ['None', 'None', true, null, 'None', true],
    ['ISO', '2015-03-01', false, null, '2015-03-01', false],
    ['Reemplazada', '01/03/2015', true, '2016-04-02', '2016-04-02', false],
    ['Borrada', '2015-03-01', false, '', null, true],
    // CLIENTE-1c: el criterio es el del generador, que lee «２０１５-03-15»
    // (no es una falsa alarma) y no «２０１５-０３-15».
    ['Ancho completo', '２０１５-03-15', true, null, '２０１５-03-15', false],
    ['Ancho completo mes', '２０１５-０３-15', true, null, '２０１５-０３-15', true],
    ['Año cero', '0000-01-01', true, null, '0000-01-01', true],
    ['Imposible', '2015-02-30', true, null, '2015-02-30', true],
  ];
  const idsD3 = {};
  for (const [n, guardada, vieja] of casosD3) {
    const datosD3 = { nombre: 'Cliente Inventado D3 ' + n + ' ' + id, cuit: '20123456786', direccion: 'Calle Inventada 1' };
    if (!vieja) datosD3.fecha_inic_activ = guardada;
    const r = await page.request.post(base + '/api/clientes', { data: datosD3 });
    if (!r.ok()) falla(n + ': el alta por la API dio ' + r.status() + ': ' + await r.text());
    idsD3[n] = (await r.json()).cliente.id;
    if (vieja) sembrarFecha(idsD3[n], guardada);
  }
  await page.reload();
  await page.waitForFunction(() => window.CDI && CDI.goTo);
  await page.evaluate(() => CDI.goTo('clientes'));
  let ultimaConservada = false;
  for (const [n, , , escribe, queda, pideFecha] of casosD3) {
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
    if (cli.direccion !== 'Calle Inventada 2') falla(n + ': la edición no se guardó: ' + cli.direccion + ' (razón social: ' + cli.nombre + ')');
    const tiene = cli.fecha_inic_activ || null;
    if (tiene !== queda) falla(n + ': después de editar, la fecha es ' + JSON.stringify(tiene) + ' y tenía que ser ' + JSON.stringify(queda));
    if (/inicio de actividad/i.test(textoD3) !== pideFecha) {
      falla(n + ': el aviso ' + (pideFecha ? 'no dice' : 'dice') + ' que falta el inicio de actividad: ' + textoD3);
    }
    // La conservada que no sirve se nombra como tal, no como si faltara sin más.
    const dicenMala = /la guardada no es una fecha válida/i.test(textoD3);
    const conservadaMala = campoVacio && escribe === null && pideFecha && queda !== null;
    if (dicenMala !== conservadaMala) {
      falla(n + ': el aviso ' + (conservadaMala ? 'no dice' : 'dice') + ' que la fecha guardada no es válida: ' + textoD3);
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
  const textoAlta = (await avisoAlta.innerText()).replace(/\s+/g, ' ');
  if (!/inicio de actividad/i.test(textoAlta)) falla('un alta sin fecha después de editar no avisa que falta el inicio de actividad');
  // El último caso conserva una fecha que no sirve: si pasara al alta, el
  // aviso hablaría de «la guardada» (CLIENTE-1b).
  if (/la guardada no es una fecha válida/i.test(textoAlta)) falla('un alta después de editar habla de la fecha guardada de la edición: ' + textoAlta);
  console.log('OK al editar, la fecha que el campo no muestra se conserva; el aviso la pide sólo si el TXT no la acepta; cargarla o borrarla anda');

  // Una fecha tipeada a medias (el navegador la da como vacía) no se guarda
  // callada: ni conserva la fecha guardada ni la borra; el formulario lo dice.
  for (const [n, guardada] of [['A medias oculta', '01/03/2015'], ['A medias ISO', '2015-03-01']]) {
    const nombreM = 'Cliente Inventado D3 ' + n + ' ' + id;
    const r = await page.request.post(base + '/api/clientes', { data: { nombre: nombreM, cuit: '20123456786', direccion: 'Calle Inventada 1' } });
    const idM = (await r.json()).cliente.id;
    sembrarFecha(idM, guardada);
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

  // CLIENTE-1b: si la API rechaza la fecha, el formulario muestra su error y no
  // se cierra. El campo de fecha no deja escribir una mala: se cambia lo que
  // sale hacia la API.
  const nombreE = 'Cliente Inventado 1b Error ' + id;
  const rE = await page.request.post(base + '/api/clientes', { data: { nombre: nombreE, cuit: '20123456786', direccion: 'Calle Inventada 1', fecha_inic_activ: '2015-03-01' } });
  const idE = (await rE.json()).cliente.id;
  await page.reload();
  await page.waitForFunction(() => window.CDI && CDI.goTo);
  await page.evaluate(() => CDI.goTo('clientes'));
  await page.locator('.cx-card', { hasText: nombreE }).click();
  await page.locator('#cxKebabBtn').click();
  await page.locator('#cxKebabMenu [data-kaction="edit"]').click();
  await formularioListo();
  await page.fill('#cfDireccion', 'Calle Inventada 2');
  await page.route('**/api/clientes/' + idE, ruta => {
    if (ruta.request().method() !== 'PUT') return ruta.continue();
    const cuerpo = JSON.parse(ruta.request().postData());
    cuerpo.fecha_inic_activ = '2015-02-30';
    return ruta.continue({ postData: JSON.stringify(cuerpo) });
  });
  await page.locator('#cxFormSave').click();
  await page.locator('#cfError').waitFor({ state: 'visible', timeout: 5000 })
    .catch(() => falla('la fecha que la API rechaza no muestra error en el formulario'));
  const errorE = await page.locator('#cfError').innerText();
  if (!/fecha de inicio de actividad/i.test(errorE) || !/AAAA-MM-DD/.test(errorE)) falla('el error del formulario no es el de la fecha: ' + errorE);
  if (!(await page.locator('#cxFormModal').evaluate(el => el.open))) falla('con la fecha rechazada el formulario se cerró');
  const cE = (await (await page.request.get(base + '/api/clientes/' + idE)).json());
  const cliE = cE.cliente || cE;
  if (cliE.direccion !== 'Calle Inventada 1' || cliE.fecha_inic_activ !== '2015-03-01') {
    falla('con la fecha rechazada igual se guardó: ' + JSON.stringify([cliE.direccion, cliE.fecha_inic_activ]));
  }
  await page.unroute('**/api/clientes/' + idE);
  await page.keyboard.press('Escape');
  console.log('OK la fecha que la API rechaza se muestra en el formulario y no guarda nada: ' + errorE.replace(/\s+/g, ' '));

  // CLIENTE-1c: la importación deja vacía la fecha que no sirve y la vista
  // previa dice en qué fila. Un CUIT inventado y nuevo en cada corrida.
  function cuitInventado(n) {
    const pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2];
    for (let k = n; ; k++) {
      const base = '30' + String(k % 100000000).padStart(8, '0');
      let v = 11 - [...base].reduce((t, d, i) => t + Number(d) * pesos[i], 0) % 11;
      if (v === 11) v = 0;
      if (v !== 10) return base + v;
    }
  }
  const cuitMala = cuitInventado(id % 90000000), cuitBuena = cuitInventado(id % 90000000 + 7);
  const csv = 'CUIT,RAZON SOCIAL,FECHA INICIO ACTIVIDADES\n'
    + cuitMala + ',Importadora Inventada Mala ' + id + ',20150-01-0\n'
    + cuitBuena + ',Importadora Inventada Buena ' + id + ',01/06/2018\n';
  await page.reload();
  await page.waitForFunction(() => window.CDI && CDI.goTo);
  await page.evaluate(() => CDI.goTo('clientes'));
  await page.locator('#cxImportBtn').click();
  await page.setInputFiles('#importFileInput', { name: 'clientes.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) });
  await page.locator('#importPreviewStep').waitFor({ state: 'visible', timeout: 15000 })
    .catch(() => falla('la importación no llegó a la vista previa'));
  const fechasVisible = await page.locator('#importPreviewFechas').isVisible();
  const avisosFecha = await page.locator('#importPreviewFechas li').allInnerTexts();
  const esperado = 'Fila 2: la fecha de inicio «20150-01-0» no es válida y no se importa.';
  if (!fechasVisible || avisosFecha.length !== 1 || avisosFecha[0] !== esperado) {
    falla('la vista previa no avisa la fecha que no sirve: ' + JSON.stringify([fechasVisible, avisosFecha]));
  }
  await page.locator('#importConfirm').click();
  await page.locator('#importDoneStep').waitFor({ state: 'visible', timeout: 15000 })
    .catch(() => falla('la importación no terminó'));
  for (const [cuitI, queda] of [[cuitMala, ''], [cuitBuena, '2018-06-01']]) {
    const cI = await (await page.request.get(base + '/api/clientes/by-cuit/' + cuitI)).json();
    const fI = (cI.cliente || cI).fecha_inic_activ;
    if ((fI || '') !== queda) falla('la importación guardó «' + fI + '» para ' + cuitI + ', tenía que quedar «' + queda + '»');
  }
  console.log('OK la importación avisa la fila con la fecha que no sirve y la deja vacía: ' + avisosFecha[0]);
  // Sin fechas malas, el aviso no aparece.
  await page.locator('#importClose').click();
  await page.locator('#cxImportBtn').click();
  const cuitSin = cuitInventado(id % 90000000 + 31);
  await page.setInputFiles('#importFileInput', { name: 'clientes.csv', mimeType: 'text/csv',
    buffer: Buffer.from('CUIT,RAZON SOCIAL,FECHA INICIO ACTIVIDADES\n' + cuitSin + ',Importadora Inventada Sin ' + id + ',01/06/2018\n') });
  await page.locator('#importPreviewStep').waitFor({ state: 'visible', timeout: 15000 })
    .catch(() => falla('la segunda importación no llegó a la vista previa'));
  // isVisible() no sirve: un <ul> vacío no ocupa lugar y Playwright lo da por oculto aunque no lo esté.
  if (!(await page.locator('#importPreviewFechas').evaluate(el => el.hidden && el.children.length === 0)))
    falla('sin fechas malas igual aparece el aviso de fechas');
  console.log('OK sin fechas malas no hay aviso de fechas');

  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });
  await b.close();
  console.log('PANTALLA CLIENTE-1 OK (con CLIENTE-1b y 1c)');
})().catch(e => falla(e.message));
