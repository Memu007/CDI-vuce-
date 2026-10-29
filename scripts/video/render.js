'use strict';
// Compone el video de presentación (1920x1080, 30 fps): tarjetas + clips reales
// con ventana, cuadro por cuadro en Chromium, y lo codifica con ffmpeg.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const S = __dirname;
const WORK = process.env.WORK || S;
const OUT_MP4 = process.env.OUT_MP4 || path.join(WORK, 'cdi-presentacion.mp4');
const FPS = 30;
const count = (name) => fs.readdirSync(path.join(WORK, 'clips', name)).length;

const INTRO = { type: 'card', start: 0, end: 2.9, fade: 0.5, eyebrow: 'Para despachantes de aduana',
  lines: [{ text: 'El despacho arranca con un PDF.' }, { text: 'Todo lo demás, te lo hago yo.', cls: 'accent' }] };
const PASOS = [
  { type: 'clip', clip: 'subir', n: 1, step: '01', title: 'Subís la factura.', desc: 'PDF o planilla Excel del proveedor. CDI la lee y la asocia a tu cliente.' },
  { type: 'clip', clip: 'revisar', n: 2, step: '02', title: 'Revisás los datos.', desc: 'Importador, ítems, precios y moneda ya cargados. Corregís sólo lo que haga falta.' },
  { type: 'clip', clip: 'ncm', n: 3, step: '03', title: 'Confirmás la posición.', desc: 'NCM, SIM y letra de control por ítem. CDI la recuerda para la próxima factura de ese cliente.' },
  { type: 'clip', clip: 'validar', n: 4, step: '04', title: 'Validás antes.', desc: 'Pesos, valores y nomenclador vigente de ARCA, con las advertencias a la vista.' },
  { type: 'clip', clip: 'listo', n: 5, step: '05', title: 'Descargás el MARIA.TXT.', desc: 'Un click y lo importás en el Kit MARIA.', hold: 1.0 },
];
const DESPUES = [
  { type: 'clip', clip: 'tablero', n: 5, step: '06', title: 'Seguís cada despacho.', desc: 'Todas las operaciones en un tablero, con estado y canal. Sin planilla aparte.' },
  { type: 'clip', clip: 'cliente', n: 5, step: '07', title: 'Todo queda en la ficha del cliente.', desc: 'Historial con cada TXT para volver a bajar, exportación a CSV para controlar en Excel y plantilla con sus columnas.' },
  { type: 'clip', clip: 'columnas', n: 5, step: '08', title: 'Catálogos flexibles.', desc: 'Las columnas del Excel de cada cliente se aprenden solas, y las corregís acá.' },
  { type: 'clip', clip: 'catalogo', n: 5, step: '09', title: 'Lo aprendido se edita.', desc: 'Cada proveedor con sus productos, NCM y origen. Corregís, guardás, y la próxima factura ya lo trae.' },
  { type: 'clip', clip: 'importar', n: 5, step: '10', title: 'Traé tus clientes.', desc: 'Subís la planilla que ya usás. CDI muestra qué encontró antes de guardar nada.' },
];
const OUTRO = { type: 'card', start: 0, end: 0, fade: 0.5, brand: true,
  lines: [{ text: 'Menos tipeo.' }, { text: 'Más despachos.', cls: 'accent' }],
  sub: 'Diseñado para despachantes que valoran su tiempo.' };

function timeline(scenes) {
  // cada escena entra 0.45 s antes de que termine la anterior (fundido encadenado)
  const XF = 0.45;
  let t = scenes[0].end - XF;
  for (let i = 1; i < scenes.length; i++) {
    const s = scenes[i];
    s.start = t; s.fade = XF;
    if (s.type === 'clip') { s.count = count(s.clip); s.end = s.start + s.count / FPS + (s.hold || 0) + 0.15; }
    else { s.end = s.start + 2.9; }
    t = s.end - XF;
  }
  scenes[scenes.length - 1].end += XF; // la última no se funde con nada
  return scenes;
}
const copy = (o) => JSON.parse(JSON.stringify(o));
const VERSIONES = {
  corto: () => timeline([copy(INTRO), ...copy(PASOS), copy(OUTRO)]),
  largo: () => timeline([copy(INTRO), ...copy(PASOS), ...copy(DESPUES), copy(OUTRO)]),
};
const largoDisponible = fs.existsSync(path.join(WORK, 'clips', 'tablero'));
const pedidas = (process.env.VERSIONES || (largoDisponible ? 'largo,corto' : 'corto')).split(',');

(async () => {
  const browser = await chromium.launch();
  for (const version of pedidas) {
    const scenes = VERSIONES[version]();
    const total = scenes[scenes.length - 1].end;
    const nFrames = Math.round(total * FPS);
    const outMp4 = version === 'largo' ? OUT_MP4 : OUT_MP4.replace(/\.mp4$/, `-${version}.mp4`);
    console.log(version, scenes.map((s) => `${s.type === 'clip' ? s.clip : 'card'} ${s.start.toFixed(2)}-${s.end.toFixed(2)}`).join(' | '), 'total', total.toFixed(2), 's', nFrames, 'frames');
    const framesDir = path.join(WORK, 'frames-' + version);
    fs.rmSync(framesDir, { recursive: true, force: true });
    fs.mkdirSync(framesDir);
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    page.on('console', (m) => console.log('[page]', m.text()));
    await page.goto('file://' + path.join(S, 'composer.html'));
    const cfg = { clipsDir: 'file://' + path.join(WORK, 'clips'), scenes };
    await page.evaluate((c) => window.init(c), cfg);
    const t0 = Date.now();
    for (let i = 0; i < nFrames; i++) {
      await page.evaluate((tt) => window.seek(tt), i / FPS);
      await page.screenshot({ path: path.join(framesDir, `${String(i).padStart(5, '0')}.png`), type: 'png' });
      if (i % 200 === 0) console.log('frame', i, '/', nFrames, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    await page.close();
    fs.writeFileSync(path.join(WORK, `timeline-${version}.json`), JSON.stringify(scenes, null, 2));
    const { execFileSync } = require('node:child_process');
    execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(framesDir, '%05d.png'),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', outMp4]);
    if (version === pedidas[0]) {
      fs.copyFileSync(path.join(framesDir, String(Math.round(scenes[5].start * FPS) + 45).padStart(5, '0') + '.png'), OUT_MP4.replace(/\.mp4$/, '-poster.png'));
    }
    console.log('listo', version, nFrames, 'cuadros →', outMp4);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
