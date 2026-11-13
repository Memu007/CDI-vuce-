// MARIA-5 en el navegador local, contra el servidor local (sin terceros).
// Primero, la pantalla de NCM (peso de la línea y grupos). Después, una
// operación con 10 notebooks de 2,5 kg y dos productos más, flete 10 y
// seguro 10. La validación muestra el peso total y el valor; el TXT que sale
// de la pantalla declara el mismo peso (25 kg) y el mismo FOB, y sus cuentas
// cierran al centavo (el flete de los ítems suma 10,00).
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria5.js [captura.png]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
const cargarCuitDelPerfil = require('./_cuit_perfil');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const centavos = s => Math.round(parseFloat(s) * 100);
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();
  await registrarCuenta(page.request, base, { data: { username: 'm5_' + id, password: 'Clave-Inventada-123', email: 'm5' + id + '@ejemplo.test' } });
  await cargarCuitDelPerfil(page.request, base);

  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.despachante);

  // Pantalla de NCM: el peso de la línea debajo del unitario, y un grupo que
  // se edita reparte entre sus productos lo que muestra (antes copiaba el
  // total del grupo a cada producto y el TXT sumaba de más).
  await page.evaluate(() => {
    CDI.state = CDI.state || {};
    CDI.state.operacion = { numero_factura: 'F-M5', moneda: 'DOL', incoterm: 'FOB', fecha_emision: '22/06/2026' };
    CDI.state.items = [
      { pieza: '84713012100F', descripcion: 'Notebook importada de prueba', origen: 'CN', cantidad: 10, valor_unitario: 10, peso_unitario: 2.5 },
      { pieza: '94037000000X', descripcion: 'Silla de madera de prueba', origen: 'CN', cantidad: 3, valor_unitario: 50, peso_unitario: 3, grupo_id: 1 },
      { pieza: '94037000000X', descripcion: 'Mesa de madera de prueba', origen: 'CN', cantidad: 1, valor_unitario: 7.5, peso_unitario: 1, grupo_id: 1 },
    ];
    CDI.goTo('ncm');
  });
  // SOLO_GRUPO=1 saltea el peso de la línea (para ver el rojo del grupo antes de la pieza).
  if (!process.env.SOLO_GRUPO) {
  await page.locator('[data-peso-total="0"]', { hasText: '25 kg' }).waitFor({ timeout: 10000 }).catch(() => falla('no se ve el peso de la línea (25 kg) debajo del unitario'));
  await page.fill('input[data-row="0"][data-field="cantidad"]', '4');
  await page.locator('[data-peso-total="0"]', { hasText: '10 kg' }).waitFor({ timeout: 5000 }).catch(() => falla('el peso de la línea no se actualiza al cambiar la cantidad'));
  console.log('OK la pantalla de NCM muestra el peso de la línea y lo actualiza');
  }
  const estado = () => page.evaluate(() => CDI.state.items.filter(it => it.grupo_id === 1)
    .map(it => ({ c: it.cantidad, v: it.valor_unitario, p: it.peso_unitario })));
  const sel = campo => 'input[data-grupo-id="1"][data-field="' + campo + '"]';
  const grupo = async (campo, valor) => {
    await page.fill(sel(campo), valor);
    await page.locator(sel(campo)).blur();
  };
  const antes = JSON.stringify(await estado());
  // La fila muestra el promedio redondeado (39,38): pasar por el campo no cambia nada.
  await page.locator(sel('valor_unitario')).focus();
  await page.locator(sel('peso_unitario')).focus();
  await page.locator(sel('peso_unitario')).blur();
  if (JSON.stringify(await estado()) !== antes) falla('pasar por el grupo sin editar cambió los productos: ' + JSON.stringify(await estado()));
  // Un 0 no borra la proporción: vuelve lo que estaba.
  await grupo('valor_unitario', '0');
  if (JSON.stringify(await estado()) !== antes) falla('un 0 en el grupo cambió los productos: ' + JSON.stringify(await estado()));
  if ((await page.inputValue(sel('valor_unitario'))) === '0') falla('el 0 quedó escrito en la fila del grupo');
  console.log('OK pasar por el grupo sin editar, o poner 0, no toca los productos');
  await grupo('cantidad', '8');
  await grupo('valor_unitario', '40');
  await grupo('peso_unitario', '4');
  const g = await estado();
  const cant = g.reduce((s, x) => s + x.c, 0);
  const fob = g.reduce((s, x) => s + x.c * x.v, 0);
  const peso = g.reduce((s, x) => s + x.c * x.p, 0);
  if (cant !== 8 || g.some(x => !Number.isInteger(x.c))) falla('la cantidad del grupo quedó ' + JSON.stringify(g));
  if (Math.abs(fob - 320) > 1e-6) falla('el FOB del grupo es ' + fob + ' y la fila muestra 8 × 40 = 320');
  if (Math.abs(peso - 32) > 1e-6) falla('el peso del grupo es ' + peso + ' y la fila muestra 8 × 4 = 32');
  if (!(g[0].v > g[1].v)) falla('se perdió la proporción de valores del grupo: ' + JSON.stringify(g));
  const fila = [await page.inputValue(sel('cantidad')), await page.inputValue(sel('valor_unitario')), await page.inputValue(sel('peso_unitario'))];
  if (fila.join('|') !== '8|40|4') falla('la fila del grupo muestra ' + fila.join(' | ') + ' y no lo guardado');
  console.log('OK editar el grupo reparte: cantidad 8, FOB 320, peso 32; la silla sigue valiendo más que la mesa y la fila muestra lo guardado');
  // Devolución de MARIA-5 (5): bajar la cantidad de un grupo nunca deja un
  // producto en 0 (antes 1/1/1 bajado a 2 quedaba [1,1,0] y «Generar» se
  // bloqueaba). Menos que un producto cada uno se rechaza; si alcanza, el
  // que no llega a uno lo toma del que más tiene.
  // SIN_CERO=1 saltea este paso (para ver el rojo de la validación antes de la devolución).
  if (!process.env.SIN_CERO) {
  const grupoNuevo = async cants => {
    await page.evaluate(cs => {
      CDI.state.items = cs.map((c, i) => ({ pieza: '94037000000X', descripcion: 'Mueble de madera de prueba ' + i,
        origen: 'CN', cantidad: c, valor_unitario: 10, peso_unitario: 1, grupo_id: 1 }));
      CDI.goTo('review'); CDI.goTo('ncm');
    }, cants);
    await page.locator(sel('cantidad')).waitFor({ timeout: 5000 });
  };
  await grupoNuevo([1, 1, 1]);
  await grupo('cantidad', '2');
  if ((await estado()).map(x => x.c).join(',') !== '1,1,1') falla('1/1/1 bajado a 2 quedó ' + JSON.stringify(await estado()));
  if ((await page.inputValue(sel('cantidad'))) !== '3') falla('la fila del grupo quedó en ' + await page.inputValue(sel('cantidad')));
  await grupoNuevo([1, 1, 100]);
  await grupo('cantidad', '5');
  const cinco = (await estado()).map(x => x.c);
  if (cinco.reduce((a, c) => a + c, 0) !== 5 || cinco.some(c => c < 1)) falla('1/1/100 bajado a 5 quedó ' + cinco.join('/'));
  console.log('OK el grupo no deja productos en 0: 1/1/1 a 2 se rechaza; 1/1/100 a 5 queda ' + cinco.join('/'));
  }
  await page.evaluate(() => {
    CDI.state = CDI.state || {};
    // Con MARIA-1b integrada no se genera sin CUIT del importador válido.
    CDI.state.operacion = { numero_factura: 'None', moneda: 'DOL', incoterm: 'CIF', fecha_emision: '22/06/2026',
                            flete: 10, seguro: 10, sbt_sufijo_valor: 'AA(1)-CA00',
                            comprador_cuit: '30999999995', comprador_nombre: 'IMPORTADORA DEMO S.A.',
                            vendedor_nombre: 'PROVEEDOR DEMO' };
    CDI.state.items = [
      { pieza: '84713012100F', descripcion: 'Notebook importada de prueba', origen: 'CN', cantidad: 10, valor_unitario: 10, peso_unitario: 2.5 },
      // De otro origen: con la misma posición y origen, los dos renglones irían en un solo ítem.
      { pieza: '84713012100F', descripcion: 'Notebook importada de prueba B', origen: 'US', cantidad: 1, valor_unitario: 100, peso_unitario: 1 },
      { pieza: '84714900100D', descripcion: 'Equipo importado de prueba', origen: 'CN', cantidad: 4, valor_unitario: 100, peso_unitario: 0.5 },
      // Un grupo de tres de 6,675: el TXT declara una línea de 20,03.
      ...[1, 2, 3].map(n => ({ pieza: '84714900100D', descripcion: 'Accesorio importado de prueba ' + n, origen: 'CN',
                               cantidad: 1, valor_unitario: 6.675, peso_unitario: 0.5, grupo_id: 3 })),
    ];
    CDI.goTo('validating');
  });

  await page.locator('#validatingGenerate').waitFor({ state: 'visible', timeout: 10000 }).catch(() => falla('no aparece la validación'));
  await page.locator('text=Peso total').first().waitFor({ timeout: 10000 }).catch(() => falla('no aparece el peso total en la validación'));
  const tarjetas = await page.evaluate(() => document.body.innerText);
  if (!/29[.,]50? kg/.test(tarjetas.replace(/\s+/g, ' '))) falla('la validación no muestra 29,5 kg de peso total');
  console.log('OK la validación muestra el peso total: 25 + 1 + 2 + 1,5 = 29,5 kg');
  const fobValidacion = (tarjetas.replace(/\s+/g, ' ').match(/\$\s?([\d.,]+)/) || [])[1] || '';
  if (process.argv[2]) await page.screenshot({ path: process.argv[2], fullPage: true });

  await page.fill('#sbtSufijoValor', 'AA(1)-CA00');
  const respuesta = page.waitForResponse(r => r.url().endsWith('/generate_maria') && r.request().method() === 'POST', { timeout: 15000 });
  await page.click('#validatingGenerate');
  const r = await respuesta.catch(() => falla('no se pidió el TXT'));
  const pedido = JSON.parse(r.request().postData());
  if (/none/i.test(pedido.operation_id)) falla('la pantalla manda el número de operación ' + pedido.operation_id);
  const generado = await r.json().catch(() => null);
  if (!generado || !generado.content) falla('no se generó el TXT: ' + JSON.stringify(generado));
  if (/none/i.test(generado.filename)) falla('el archivo se llama ' + generado.filename);
  const txt = generado.content;
  const campo = c => [...txt.matchAll(new RegExp('^' + c + '=(\\S+)', 'gm'))].map(m => m[1]);
  const pesos = campo('QARTKGRNET');
  if (pesos[0] !== '25.000') falla('las 10 notebooks de 2,5 kg declaran ' + pesos[0]);
  console.log('OK el TXT declara 25 kg para 10 × 2,5 kg (pesos: ' + pesos.join(', ') + ')');
  for (const [item, cab] of [['MARTFOB', 'MDDTFOB'], ['MARTFLE', 'MDDTFLE'], ['MARTASS', 'MDDTASS']]) {
    const suma = campo(item).reduce((a, v) => a + centavos(v), 0);
    if (suma !== centavos(campo(cab)[0])) falla(item + ' suma ' + suma / 100 + ' y ' + cab + ' es ' + campo(cab)[0]);
  }
  if (campo('MDDTFLE')[0] !== '10.00') falla('el flete de la carátula es ' + campo('MDDTFLE')[0]);
  // Devolución de MARIA-5 (6): una sola cuenta. Antes la validación sumaba
  // 6,68 × 3 y mostraba 620,04; el TXT dice 620,03.
  if (campo('MDDTFOB')[0] !== '620.03') falla('el FOB del TXT es ' + campo('MDDTFOB')[0]);
  if (fobValidacion.replace(/\./g, '').replace(',', '.') !== '620.03' && fobValidacion.replace(/,/g, '') !== '620.03')
    falla('la validación muestra $' + fobValidacion + ' y el TXT ' + campo('MDDTFOB')[0]);
  console.log('OK la validación y el TXT dicen el mismo FOB: $' + fobValidacion + ' = ' + campo('MDDTFOB')[0]);
  console.log('OK las cuentas cierran al centavo: flete por ítem ' + campo('MARTFLE').join(' + ') + ' = 10.00');
  await b.close();
  console.log('OK: pantalla MARIA-5');
})().catch(e => falla(e.message));
