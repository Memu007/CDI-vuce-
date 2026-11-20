// El origen habitual del cliente en el navegador local, contra el servidor local (sin terceros).
// La ficha (la etiqueta de arriba y «Origen habitual») muestra cada país de la tabla con código y
// nombre, en un renglón y sin salirse, en el ancho más angosto de cada disposición; lo que no es un
// país, con las letras con que se guardó. El formulario acepta el nombre o el código, dice por qué
// no guarda lo que no es un país y, si no se toca el origen, lo deja como estaba.
// Sale con error si algo no se cumple. Con una carpeta como argumento, deja ahí las capturas.
// uso: BASE_URL=http://127.0.0.1:<puerto> CDI_DB=<base sqlite del servidor> node scripts/testing/pantalla_origen2.js [carpeta]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const registrarCuenta = require('./_registrar');
const { execFileSync } = require('child_process');
const path = require('path');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const baseLocal = process.env.CDI_DB || falla('falta CDI_DB: la base sqlite local del servidor, para sembrar orígenes que la API ya no guarda');
const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
const XSS = '<img src=x onerror="window.__xss=1">';
// Lo guardado y cómo se ve. Lo recortado a 3 de un nombre y lo que no es un país, como pudo quedar
// de antes, se siembra en la base: la API ya no lo guarda.
const GUARDADOS = [['CN', '310 · CHINA'], ['Holanda', '423 · PAISES BAJOS'], ...['CHI', 'HOL', 'tierra media', XSS].map(o => [o, o])];
// Los orígenes corrientes, Emiratos primero: es la etiqueta más ancha de los seis.
const CORRIENTES = ['331', '310', '423', '212', '309', '438'];
let USUARIO, page;

const api = async (metodo, ruta, data) => {
  const r = await page.request.fetch(base + ruta, { method: metodo, data });
  if (!r.ok()) falla(metodo + ' ' + ruta + ': ' + r.status() + ' ' + await r.text());
  return r.json();
};
const guardado = async cid => (await api('GET', '/api/clientes')).clientes.find(c => c.id === cid).default_origin;

function sembrarOrigen(cid, origen) {
  execFileSync('python3', ['-c',
    'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute("UPDATE clients SET default_origin=? WHERE owner_username=? AND id=?", sys.argv[2:]).rowcount; c.commit(); sys.exit(0 if n == 1 else 1)',
    baseLocal, origen, USUARIO, String(cid)]);
}

// Abre la ficha desde la lista recién pedida, a 1280: más angosta, la lista se oculta con la ficha
// abierta. Espera que muestre `visto` como origen.
async function abrirFicha(cid, visto) {
  await page.setViewportSize({ width: 1280, height: 1000 });
  const lista = page.waitForResponse(x => x.url().endsWith('/api/clientes') && x.request().method() === 'GET', { timeout: 10000 });
  await page.evaluate(() => CDI.goTo('clientes'));
  await lista;
  await page.locator('.cx-card[data-cliente-id="' + cid + '"]').click({ timeout: 10000 });
  await page.locator('#cxTabDatos').click();
  await page.waitForFunction(v => {
    const tag = document.querySelector('#cxHero .cx-hero-tag.is-origen');
    const dt = [...document.querySelectorAll('#cxDatosGrid dt')].find(d => d.textContent === 'Origen habitual');
    return dt && dt.nextElementSibling.textContent === v && tag && tag.textContent === 'Origen ' + v;
  }, visto, { timeout: 5000 }).catch(async () => {
    const f = await medirFicha();
    falla('la ficha muestra «' + f.tag + '» y «' + f.dd + '», no «' + visto + '»');
  });
}

// Cómo se ve el origen en la ficha. Si la etiqueta se corta, el código tiene que verse entero.
const medirFicha = () => page.evaluate(() => {
  const tag = document.querySelector('#cxHero .cx-hero-tag.is-origen');
  const dt = [...document.querySelectorAll('#cxDatosGrid dt')].find(d => d.textContent === 'Origen habitual');
  const dd = dt.nextElementSibling;
  const renglones = el => { const r = document.createRange(); r.selectNodeContents(el); return new Set([...r.getClientRects()].map(x => Math.round(x.top))).size; };
  const t = tag ? tag.getBoundingClientRect() : null;
  let codigoEntero = true;
  const m = tag && /^Origen \d{3}/.exec(tag.textContent);
  if (m && tag.scrollWidth > tag.clientWidth) {
    const r = document.createRange();
    r.setStart(tag.firstChild, 0);
    r.setEnd(tag.firstChild, m[0].length);
    const ctx = document.createElement('canvas').getContext('2d');
    ctx.font = getComputedStyle(tag).font;
    codigoEntero = r.getBoundingClientRect().right + ctx.measureText('…').width <= t.right - parseFloat(getComputedStyle(tag).paddingRight) + 0.5;
  }
  const g = dd.parentElement.getBoundingClientRect();
  return {
    tag: tag ? tag.textContent : null, dd: dd.textContent, html: (tag ? tag.children.length : 0) + dd.children.length,
    mayusculas: [tag, dd].filter(Boolean).some(e => getComputedStyle(e).textTransform !== 'none' || getComputedStyle(e).fontVariantCaps !== 'normal'),
    renglonesTag: tag ? renglones(tag) : 1, renglonesDd: renglones(dd),
    afuera: (t && t.right > Math.min(document.documentElement.clientWidth, tag.closest('.cx-hero').getBoundingClientRect().right) + 0.5)
      || dd.getBoundingClientRect().right > g.right + 0.5,
    cortada: !!tag && tag.scrollWidth > tag.clientWidth, codigoEntero,
    // Lo que no entra no se dibuja afuera de la etiqueta, y se ve que falta.
    sinAviso: !!tag && tag.scrollWidth > tag.clientWidth && (getComputedStyle(tag).overflowX !== 'hidden' || getComputedStyle(tag).textOverflow !== 'ellipsis'),
  };
});

// El ancho más angosto de cada disposición: cada `max-width` de la página, más uno, hasta 320.
const anchos = () => page.evaluate(() => {
  const cortes = new Set([1280, 320]);
  for (const hoja of document.styleSheets) {
    let reglas;
    try { reglas = [...hoja.cssRules]; } catch { continue; }
    for (const r of reglas) for (const m of (r.media ? r.media.mediaText : '').matchAll(/max-width:\s*(\d+)px/g)) if (+m[1] >= 320 && +m[1] < 1280) cortes.add(+m[1] + 1);
  }
  return [...cortes].sort((a, b) => b - a);
});

// Cada país de la tabla guardado por la API se ve con su etiqueta en la ficha, en cada ancho. La
// etiqueta de arriba no baja de renglón; «Origen habitual», como los otros datos, sí, salvo los corrientes.
async function fichaDeCadaPais(cid, tabla, ws) {
  const cortadas = Object.fromEntries(ws.map(w => [w, 0])), dosRenglones = Object.fromEntries(ws.map(w => [w, 0]));
  for (const [codigo, etiqueta] of tabla) {
    await api('PUT', '/api/clientes/' + cid, { default_origin: codigo });
    await abrirFicha(cid, etiqueta);
    for (const w of ws) {
      await page.setViewportSize({ width: w, height: 1000 });
      const f = await medirFicha();
      const donde = '«' + codigo + '» a ' + w + ' px';
      if (f.mayusculas) falla(donde + ': la ficha fuerza las letras del origen');
      if (f.renglonesTag > 1) falla(donde + ': la etiqueta del origen baja de renglón');
      if (f.afuera) falla(donde + ': el origen se sale de la ficha');
      if (f.sinAviso) falla(donde + ': lo que no entra en la etiqueta se sale o se corta sin «…»');
      if (!f.codigoEntero) falla(donde + ': la etiqueta cortada no deja ver el código entero');
      if (CORRIENTES.includes(codigo) && w >= 400 && f.cortada) falla(donde + ': «' + etiqueta + '» no entra entera en la etiqueta');
      if (CORRIENTES.includes(codigo) && f.renglonesDd > 1) falla(donde + ': «Origen habitual» baja de renglón');
      if (f.cortada) cortadas[w]++;
      if (f.renglonesDd > 1) dosRenglones[w]++;
    }
  }
  const porAncho = n => ws.map(w => w + ':' + n[w]).join(' ');
  console.log('OK ficha: ' + tabla.length + ' países con código y nombre, la etiqueta en un renglón y todo adentro a ' + ws.join(', ') + ' px');
  console.log('   etiquetas cortadas a la vista, con el código entero: ' + porAncho(cortadas));
  console.log('   «Origen habitual» en dos renglones: ' + porAncho(dosRenglones));
}

// Lo guardado se ve con su etiqueta, o como se guardó si no es un país, sin HTML; el formulario lo
// muestra igual, y guardar otro dato lo deja como estaba.
async function guardarOtroDato(cids) {
  for (const [o, visto, cid] of cids) {
    await abrirFicha(cid, visto);
    const f = await medirFicha();
    if (f.html) falla('«' + o + '» guardado se ve como HTML');
    if (f.mayusculas) falla('«' + o + '» guardado no se ve con sus letras');
    await abrirEdicion();
    if (await page.inputValue('#cfOrigen') !== visto) falla('el formulario muestra «' + await page.inputValue('#cfOrigen') + '» para «' + o + '»');
    await page.fill('#cfNotas', 'otro dato ' + o);
    const r = await guardar();
    if (!r.ok()) falla('guardar otro dato con «' + o + '» guardado da ' + r.status() + ': ' + await r.text());
    await cerrado();
    if (await guardado(cid) !== o) falla('guardar otro dato reescribe «' + o + '» → «' + await guardado(cid) + '»');
  }
  if (await page.evaluate(() => window.__xss)) falla('un origen con HTML se ejecutó');
  console.log('OK guardar otro dato: ' + cids.map(([o]) => '«' + o + '»').join(', ') + ' se ven con su etiqueta o como se guardaron, y quedan');
}

async function abrirEdicion() {
  await page.locator('#cxKebabBtn').click();
  await page.locator('[data-kaction="edit"]').click();
  await page.waitForSelector('#cxFormModal[open]', { timeout: 5000 });
  await page.evaluate(() => { document.getElementById('cfAdvanced').open = true; });
}

const cerrado = () => page.waitForFunction(() => !document.getElementById('cxFormModal').open, null, { timeout: 5000 })
  .catch(async () => falla('el formulario no se cierra al guardar: «' + await page.textContent('#cfError') + '»'));

async function guardar() {
  const r = page.waitForResponse(x => x.url().includes('/api/clientes') && ['POST', 'PUT'].includes(x.request().method()), { timeout: 10000 });
  await page.click('#cxFormSave');
  return r;
}

// El campo de origen del formulario va solo en su renglón: muestra entera la etiqueta de los
// corrientes y no se sale del formulario.
async function campoDelFormulario(cid, tabla, ws) {
  const opciones = await page.$eval('#cfOrigen', o => (o.list ? o.list.options.length : 0));
  if (opciones !== tabla.length) falla('el formulario ofrece ' + opciones + ' países, no ' + tabla.length);
  for (const codigo of CORRIENTES) {
    await api('PUT', '/api/clientes/' + cid, { default_origin: codigo });
    const etiqueta = tabla.find(([c]) => c === codigo)[1];
    await abrirFicha(cid, etiqueta);
    await abrirEdicion();
    if (await page.inputValue('#cfOrigen') !== etiqueta) falla('el formulario muestra «' + await page.inputValue('#cfOrigen') + '» para «' + codigo + '»');
    for (const w of ws) {
      await page.setViewportSize({ width: w, height: 1000 });
      const f = await page.evaluate(() => {
        const o = document.getElementById('cfOrigen');
        return { entera: o.scrollWidth <= o.clientWidth, mayusculas: getComputedStyle(o).textTransform !== 'none',
          afuera: o.getBoundingClientRect().right > o.closest('.cx-modal-body').getBoundingClientRect().right + 0.5 };
      });
      if (f.mayusculas) falla('el campo de origen fuerza las letras');
      if (f.afuera) falla('el campo de origen se sale del formulario a ' + w + ' px');
      if (w >= 400 && !f.entera) falla('«' + etiqueta + '» no entra en el campo de origen a ' + w + ' px');
    }
    await page.click('#cxFormCancel');
  }
  console.log('OK formulario: ' + tabla.length + ' países para elegir; los corrientes, enteros en el campo a ' + ws.filter(w => w >= 400).join(', ') + ' px y adentro a ' + ws.join(', ') + ' px');
}

// Lo escrito: un nombre se guarda así y se ve con código y nombre; lo que no es un país lo dice.
async function escribir(cid) {
  await api('PUT', '/api/clientes/' + cid, { default_origin: 'CN' });
  await abrirFicha(cid, '310 · CHINA');
  await abrirEdicion();
  await page.fill('#cfOrigen', 'Narnia');
  if ((await guardar()).status() !== 400) falla('«Narnia» no da 400');
  await page.waitForSelector('#cfError:not([hidden])', { timeout: 5000 });
  const error = await page.textContent('#cfError');
  if (error !== 'No reconozco el origen «Narnia»: usá el nombre o el código del país.') falla('«Narnia» dice «' + error + '»');
  if (!await page.$('#cxFormModal[open]') || await guardado(cid) !== 'CN') falla('«Narnia» cierra el formulario o toca el origen');
  await page.fill('#cfOrigen', 'Brasil');
  await guardar();
  await cerrado();
  if (await guardado(cid) !== 'Brasil') falla('«Brasil» escrito se guarda «' + await guardado(cid) + '»');
  const f = await medirFicha();
  if (f.tag !== 'Origen 203 · BRASIL' || f.dd !== '203 · BRASIL') falla('«Brasil» guardado se ve «' + f.tag + '» y «' + f.dd + '»');
  console.log('OK formulario: «Narnia» dice por qué y no guarda; «Brasil» se guarda así y se ve «203 · BRASIL»');

  await page.click('#cxNewBtn');
  await page.waitForSelector('#cxFormModal[open]', { timeout: 5000 });
  await page.evaluate(() => { document.getElementById('cfAdvanced').open = true; });
  await page.fill('#cfNombre', 'Alta con nombre de país');
  await page.fill('#cfOrigen', 'Países Bajos');
  const alta = await (await guardar()).json();
  await cerrado();
  if (alta.cliente.default_origin !== 'Países Bajos') falla('el alta con «Países Bajos» guarda «' + alta.cliente.default_origin + '»');
  await page.locator('#cxTabDatos').click();
  const a = await medirFicha();
  if (a.dd !== '423 · PAISES BAJOS') falla('el alta con «Países Bajos» se ve «' + a.dd + '»');
  console.log('OK formulario: el alta con «Países Bajos» se guarda así y se ve «423 · PAISES BAJOS»');
}

async function capturas(carpeta, cid) {
  await api('PUT', '/api/clientes/' + cid, { default_origin: 'Brasil' });
  await abrirFicha(cid, '203 · BRASIL');
  await page.evaluate(() => { document.getElementById('toastHost').innerHTML = ''; });
  for (const w of [960, 1280]) {
    await page.setViewportSize({ width: w, height: 1000 });
    await page.locator('#cxDetailBody').screenshot({ path: path.join(carpeta, 'origen-2-' + w + '.png') });
  }
  console.log('OK capturas en ' + carpeta);
}

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: process.argv[2] ? 2 : 1 });
  page = await ctx.newPage();
  const id = Date.now();
  USUARIO = 'or2_' + id;
  await registrarCuenta(page.request, base, { data: { username: USUARIO, password: 'Clave-Inventada-123', email: 'or2' + id + '@ejemplo.test' } });
  await page.goto(base + '/dashboard');
  await page.waitForFunction(() => window.CDI && CDI.goTo && CDI.api && CDI.paisesMaria);
  const tabla = await page.evaluate(() => CDI.paisesMaria.countries.map(c => [c.code, c.code + ' · ' + c.name]));
  const nuevo = async nombre => (await api('POST', '/api/clientes', { nombre, cuit: '30999999995', direccion: 'Calle Inventada 123, CABA', default_origin: 'CN', preferred_currency: 'USD' })).cliente.id;
  const cid = await nuevo('Importadora Ejemplo SA');
  const ws = await anchos();
  await fichaDeCadaPais(cid, tabla, ws);
  const guardados = [];
  for (const [o, visto] of GUARDADOS) { const c = await nuevo('Guardado ' + guardados.length); sembrarOrigen(c, o); guardados.push([o, visto, c]); }
  await guardarOtroDato(guardados);
  await campoDelFormulario(cid, tabla, ws);
  await escribir(cid);
  if (process.argv[2]) await capturas(process.argv[2], cid);
  await b.close();
  console.log('OK: pantalla del origen habitual');
})().catch(e => falla(e.message));
