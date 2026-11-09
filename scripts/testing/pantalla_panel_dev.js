// El panel de dev muestra como texto lo que llega de api_logs: un endpoint,
// un método, una IP o una hora con HTML no crean elementos ni corren código,
// y `<sin ruta>` se lee tal cual. Corre la plantilla real en Chromium con la
// API respondida acá, sin servidor ni base. Sale con error si algo no se cumple.
// uso: node scripts/testing/pantalla_panel_dev.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PLANTILLA = path.join(__dirname, '..', '..', 'proyecto_maria', 'templates', 'dev_dashboard.html');
const ORIGEN = 'http://panel.test';
const ATAQUE = (n) => `<img src=x onerror="window.__inyectado=${n}"><b>${n}</b>`;
const LOGS = [
  { time: ATAQUE(1), method: ATAQUE(2), endpoint: ATAQUE(3), status: 500, latency: ATAQUE(4), ip: ATAQUE(5) },
  { time: '10:00:00', method: 'GET', endpoint: '<sin ruta>', status: 404, latency: 7, ip: '203.0.113.9' },
];
const ESPERADO = LOGS.map((l) => [l.time, l.method, l.endpoint, String(l.status), l.latency + ' ms', l.ip]);
const fallas = [];
const chequear = (ok, que) => { console.log((ok ? 'OK    | ' : 'FALLA | ') + que); if (!ok) fallas.push(que); };

(async () => {
  const b = await chromium.launch();
  const page = await b.newPage();
  await page.route('**/*', (ruta) => {
    const u = new URL(ruta.request().url());
    if (u.origin !== ORIGEN) return ruta.abort();
    const json = (cuerpo) => ruta.fulfill({ contentType: 'application/json', body: JSON.stringify(cuerpo) });
    if (u.pathname === '/dev') return ruta.fulfill({ contentType: 'text/html', body: fs.readFileSync(PLANTILLA) });
    if (u.pathname === '/api/dev/stats') {
      return json({ stats: { total_requests_24h: 2, error_rate: 50, avg_latency_ms: 7 }, logs: LOGS });
    }
    if (u.pathname === '/api/dev/pagos-mp-rechazados') return json({ pagos: [] });
    if (u.pathname.startsWith('/api/dev/')) return json({});
    return ruta.fulfill({ status: 404, body: '' });
  });
  await page.goto(ORIGEN + '/dev');
  await page.waitForFunction((n) => document.querySelectorAll('#logs-body tr').length === n
    && !document.querySelector('#logs-body td[colspan]'), LOGS.length, { timeout: 10000 })
    .catch(() => chequear(false, 'la tabla no llegó a mostrar las filas'));

  const tabla = await page.evaluate(() => ({
    inyectados: document.querySelectorAll('#logs-body img, #logs-body b').length,
    celdas: [...document.querySelectorAll('#logs-body tr')].map((tr) => [...tr.cells].map((td) => td.textContent.trim())),
    clases: [...document.querySelectorAll('#logs-body tr')].map((tr) => tr.cells[3] && tr.cells[3].className),
    insignias: document.querySelectorAll('#logs-body tr td:nth-child(2) > span.badge').length,
  }));
  chequear(tabla.inyectados === 0, `elementos creados por el texto de api_logs: ${tabla.inyectados}`);
  ESPERADO.forEach((fila, i) => chequear(JSON.stringify(tabla.celdas[i]) === JSON.stringify(fila),
    `fila ${i + 1} como texto: ${JSON.stringify(tabla.celdas[i])}`));
  chequear(tabla.clases[0] === 'status-500' && tabla.clases[1] === 'status-400',
    `color del estado: ${JSON.stringify(tabla.clases)}`);
  chequear(tabla.insignias === LOGS.length, `método en su insignia: ${tabla.insignias} de ${LOGS.length}`);

  await b.close();
  console.log(`fallas: ${fallas.length}`);
  process.exit(fallas.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
