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

const scenes = [
  { type: 'card', start: 0, end: 2.9, fade: 0.5, eyebrow: 'Para despachantes de aduana',
    lines: [{ text: 'El despacho arranca con un PDF.' }, { text: 'Todo lo demás, te lo hago yo.', cls: 'accent' }] },
  { type: 'clip', clip: 'subir', n: 1, step: '01', title: 'Subís la factura.', desc: 'PDF o planilla Excel del proveedor. CDI la lee y la asocia a tu cliente.' },
  { type: 'clip', clip: 'revisar', n: 2, step: '02', title: 'Revisás los datos.', desc: 'Importador, ítems, precios y moneda ya cargados. Corregís sólo lo que haga falta.' },
  { type: 'clip', clip: 'ncm', n: 3, step: '03', title: 'Confirmás la posición.', desc: 'NCM, SIM y letra de control por ítem. CDI la recuerda para la próxima factura de ese cliente.' },
  { type: 'clip', clip: 'validar', n: 4, step: '04', title: 'Validás antes.', desc: 'Pesos, valores y nomenclador vigente de ARCA, con las advertencias a la vista.' },
  { type: 'clip', clip: 'listo', n: 5, step: '05', title: 'Descargás el MARIA.TXT.', desc: 'Un click y lo importás en el Kit MARIA.', hold: 1.0 },
  { type: 'card', start: 0, end: 0, fade: 0.5, brand: true,
    lines: [{ text: 'Menos tipeo.' }, { text: 'Más despachos.', cls: 'accent' }],
    sub: 'Diseñado para despachantes que valoran su tiempo.' },
];
// línea de tiempo: cada escena entra 0.45 s antes de que termine la anterior (fundido encadenado)
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
const total = scenes[scenes.length - 1].end;
const nFrames = Math.round(total * FPS);
console.log('escenas', scenes.map((s) => `${s.type === 'clip' ? s.clip : 'card'} ${s.start.toFixed(2)}-${s.end.toFixed(2)}`).join(' | '), 'total', total.toFixed(2), 's', nFrames, 'frames');

(async () => {
  const framesDir = path.join(WORK, 'frames');
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', (m) => console.log('[page]', m.text()));
  await page.goto('file://' + path.join(S, 'composer.html'));
  const cfg = { clipsDir: 'file://' + path.join(WORK, 'clips'), scenes: scenes.map(({ el, frames, img, ...rest }) => rest) };
  await page.evaluate((c) => window.init(c), cfg);
  const t0 = Date.now();
  for (let i = 0; i < nFrames; i++) {
    await page.evaluate((tt) => window.seek(tt), i / FPS);
    await page.screenshot({ path: path.join(framesDir, `${String(i).padStart(5, '0')}.png`), type: 'png' });
    if (i % 100 === 0) console.log('frame', i, '/', nFrames, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  await browser.close();
  fs.writeFileSync(path.join(WORK, 'timeline.json'), JSON.stringify(scenes.map(({ el, frames, img, ...r }) => r), null, 2));
  const { execFileSync } = require('node:child_process');
  execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(framesDir, '%05d.png'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', OUT_MP4]);
  fs.copyFileSync(path.join(framesDir, String(Math.round(scenes[5].start * FPS) + 45).padStart(5, '0') + '.png'), OUT_MP4.replace(/\.mp4$/, '-poster.png'));
  console.log('listo', nFrames, 'cuadros →', OUT_MP4);
})().catch((e) => { console.error(e); process.exit(1); });
