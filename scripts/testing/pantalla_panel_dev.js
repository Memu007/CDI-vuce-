// El panel de dev muestra como texto lo que llega de api_logs: un endpoint,
// un método, una IP o una hora con HTML no crean elementos ni corren código,
// y `<sin ruta>` se lee tal cual. Lo mismo con la lista de usuarios, que además
// pasa de página con la búsqueda que se pidió. Corre la plantilla real en Chromium con la
// API respondida acá, sin servidor ni base. Sale con error si algo no se cumple.
// uso: node scripts/testing/pantalla_panel_dev.js
// corredor: sin servidor
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PLANTILLA = path.join(__dirname, '..', '..', 'proyecto_maria', 'templates', 'dev_dashboard.html');
const ORIGEN = 'http://panel.test';
const ATAQUE = (n) => `<img src=/inyectado onerror="alert(${n})"><b>${n}</b>`;
const LOGS = [
  { time: ATAQUE(1), method: ATAQUE(2), endpoint: ATAQUE(3), status: 500, latency: ATAQUE(4), ip: ATAQUE(5) },
  { time: '10:00:00', method: 'GET', endpoint: '<sin ruta>', status: 404, latency: 7, ip: '203.0.113.9' },
];
const ESPERADO = LOGS.map((l) => [l.time, l.method, l.endpoint, String(l.status), l.latency + ' ms', l.ip]);
const cuenta = (usuario, extra) => ({ usuario, email: usuario + '@x.test', admin: false, estudio: null,
  saldo_del_estudio: false, plan: 'premium', cobro: 'active', cobro_hasta: null, operaciones_del_periodo: 3,
  creditos_extra: 0, creditos_vencen: null, ultima_recarga: null, ...extra });
const USUARIOS = [
  cuenta(ATAQUE(6), { email: ATAQUE(7), estudio: ATAQUE(8), saldo_del_estudio: true, cobro: 'trial',
    cobro_hasta: '2026-12-01T10:00:00+00:00', creditos_extra: 4, creditos_vencen: '2026-11-30T00:00:00+00:00',
    ultima_recarga: '2026-11-17T09:00:00+00:00' }),
  cuenta('jefa', { admin: true }),
  cuenta('tercera'),
];
const USUARIOS_ESPERADO = [
  [ATAQUE(6), ATAQUE(7), 'no', 'el estudio «' + ATAQUE(8) + '»', 'premium', 'trial hasta 2026-12-01', '3', '4',
    '2026-11-29', '2026-11-17'],
  ['jefa', 'jefa@x.test', 'sí', 'la cuenta', 'premium', 'active', '3', '0', '—', '—'],
];
const pedidosDeUsuarios = [];
let llegoLenta, soltarLenta;
const lentaPedida = new Promise((r) => { llegoLenta = r; });
const fallas = [];
let imagenesPedidas = 0;
const chequear = (ok, que) => { console.log((ok ? 'OK    | ' : 'FALLA | ') + que); if (!ok) fallas.push(que); };

(async () => {
  const b = await chromium.launch();
  const page = await b.newPage();
  await page.route('**/*', (ruta) => {
    const u = new URL(ruta.request().url());
    if (u.origin !== ORIGEN) return ruta.abort();
    const json = (cuerpo) => ruta.fulfill({ contentType: 'application/json', body: JSON.stringify(cuerpo) });
    if (u.pathname === '/inyectado') imagenesPedidas++;
    if (u.pathname === '/dev') return ruta.fulfill({ contentType: 'text/html', body: fs.readFileSync(PLANTILLA) });
    if (u.pathname === '/api/dev/stats') {
      return json({ stats: { total_requests_24h: 2, error_rate: 50, avg_latency_ms: 7 }, logs: LOGS });
    }
    if (u.pathname === '/api/dev/pagos-mp-rechazados') return json({ pagos: [] });
    if (u.pathname === '/api/admin/usuarios') {
      const desde = Number(u.searchParams.get('desde'));
      pedidosDeUsuarios.push(u.search);
      const buscar = u.searchParams.get('buscar');
      if (buscar === 'sin-red') return ruta.abort();
      // La búsqueda «lenta» responde cuando la prueba la suelta, después de «rápida».
      const sola = (usuario) => ({ total: 1, desde: 0, cuantos: 2, usuarios: [cuenta(usuario)] });
      if (buscar === 'lenta') { soltarLenta = () => json(sola('lenta')); llegoLenta(); return; }
      if (buscar === 'rapida') return json(sola('rapida'));
      return json({ total: USUARIOS.length, desde, cuantos: 2, usuarios: USUARIOS.slice(desde, desde + 2) });
    }
    if (u.pathname.startsWith('/api/dev/')) return json({});
    return ruta.fulfill({ status: 404, body: '' });
  });
  await page.goto(ORIGEN + '/dev');
  await page.waitForFunction((n) => document.querySelectorAll('#logs-body tr').length === n
    && !document.querySelector('#logs-body td[colspan]'), LOGS.length, { timeout: 10000 })
    .catch(() => chequear(false, 'la tabla no llegó a mostrar las filas'));
  // Una imagen creada desde el texto, aunque nunca entre a la tabla, se pide antes que esta.
  await Promise.all([page.waitForRequest(ORIGEN + '/centinela'), page.evaluate(() => { new Image().src = '/centinela'; })]);

  const tabla = await page.evaluate(() => ({
    inyectados: document.querySelectorAll('img, b').length,
    celdas: [...document.querySelectorAll('#logs-body tr')].map((tr) => [...tr.cells].map((td) => td.textContent)),
    clases: [...document.querySelectorAll('#logs-body tr')].map((tr) => [...tr.cells].map((td) => td.className)),
    insignias: document.querySelectorAll('#logs-body tr td:nth-child(2) > span.badge').length,
  }));
  chequear(tabla.inyectados === 0, `elementos creados por el texto de api_logs: ${tabla.inyectados}`);
  chequear(imagenesPedidas === 0, `imágenes pedidas por el texto de api_logs: ${imagenesPedidas}`);
  ESPERADO.forEach((fila, i) => chequear(JSON.stringify(tabla.celdas[i]) === JSON.stringify(fila),
    `fila ${i + 1} como texto: ${JSON.stringify(tabla.celdas[i])}`));
  chequear(tabla.clases.map((c) => c[3]).join() === 'status-500,status-400',
    `color del estado: ${JSON.stringify(tabla.clases.map((c) => c[3]))}`);
  chequear(tabla.clases.every((c) => c[0] === 'text-muted' && c[5] === 'text-muted'),
    `hora e IP en gris: ${JSON.stringify(tabla.clases.map((c) => [c[0], c[5]]))}`);
  chequear(tabla.insignias === LOGS.length, `método en su insignia: ${tabla.insignias} de ${LOGS.length}`);

  await page.waitForFunction(() => document.querySelectorAll('#usuarios-body tr').length === 2, null, { timeout: 10000 })
    .catch(() => chequear(false, 'la lista de usuarios no llegó a mostrar las filas'));
  const usuarios = await page.$$eval('#usuarios-body tr', (trs) => trs.map((tr) => [...tr.cells].map((td) => td.textContent)));
  USUARIOS_ESPERADO.forEach((f, i) => chequear(JSON.stringify(usuarios[i]) === JSON.stringify(f),
    `usuario ${i + 1} como texto: ${JSON.stringify(usuarios[i])}`));
  chequear(await page.locator('#usuarios-anteriores').isHidden(), 'en la primera página no hay «Anteriores»');
  // Lo escrito sin buscar no cambia la página siguiente de la búsqueda pedida.
  await page.fill('#usuarios-buscar', 'abc');
  await page.click('#usuarios-buscar ~ button');
  await page.waitForFunction(() => document.getElementById('usuarios-pagina').textContent === '1–2 de 3');
  await page.fill('#usuarios-buscar', 'otra');
  await page.click('#usuarios-siguientes');
  await page.waitForFunction(() => document.getElementById('usuarios-pagina').textContent === '3–3 de 3', null, { timeout: 10000 })
    .catch(() => chequear(false, 'la página siguiente no llegó'));
  chequear(pedidosDeUsuarios.at(-1) === '?buscar=abc&desde=2', `la página siguiente pide ${pedidosDeUsuarios.at(-1)}`);
  chequear(await page.locator('#usuarios-siguientes').isHidden(), 'en la última página no hay «Siguientes»');
  chequear(await page.evaluate(() => document.querySelectorAll('img, b').length) === 0 && imagenesPedidas === 0,
    'el texto de los usuarios no crea elementos');

  const buscarUsuarios = async (texto) => {
    await page.fill('#usuarios-buscar', texto);
    await page.click('#usuarios-buscar ~ button');
  };
  await buscarUsuarios('sin-red');
  await page.waitForFunction(() => document.getElementById('usuarios-body').textContent.startsWith('No se pudo leer'),
    null, { timeout: 10000 }).catch(() => {});
  chequear(await page.textContent('#usuarios-body') === 'No se pudo leer'
    && await page.locator('#usuarios-anteriores').isHidden() && await page.textContent('#usuarios-pagina') === '',
  `sin red dice que no se pudo leer, sin páginas: ${await page.textContent('#usuarios-body')}`);

  await page.evaluate(() => new MutationObserver(() => {
    if (document.getElementById('usuarios-body').textContent.includes('lenta')) window.seVioLenta = true;
  }).observe(document.getElementById('usuarios-body'), { childList: true, subtree: true, characterData: true }));
  await buscarUsuarios('lenta');
  await lentaPedida;
  await buscarUsuarios('rapida');
  await page.waitForFunction(() => document.getElementById('usuarios-body').textContent.startsWith('rapida'),
    null, { timeout: 10000 }).catch(() => {});
  const lentaRespondida = page.waitForEvent('requestfinished', (r) => r.url().includes('buscar=lenta'));
  await soltarLenta();
  await lentaRespondida;
  // Una vuelta más por la red: la respuesta lenta ya se procesó cuando esta llega.
  await Promise.all([page.waitForResponse((r) => r.url().includes('buscar=rapida')),
    page.click('#usuarios-buscar ~ button')]);
  chequear(!await page.evaluate(() => window.seVioLenta) && (await page.textContent('#usuarios-body')).startsWith('rapida'),
    'la respuesta tardía de otra búsqueda no pisa la última');

  await b.close();
  console.log(`fallas: ${fallas.length}`);
  process.exit(fallas.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
