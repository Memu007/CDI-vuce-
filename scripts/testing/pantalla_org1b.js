// ORG-1b (D27 b) en el navegador local, contra la API de verdad y con datos
// inventados: con una invitación válida, el email del registro viene completo
// con el email invitado y de sólo lectura (readOnly, no disabled, así viaja en
// el envío), con una línea que lo explica. Sin `invite`, con un token que no
// existe, con uno ya usado o con una respuesta válida sin email, el campo queda
// como antes: vacío y editable. El servidor sigue siendo la guarda: si alguien
// cambia el email a mano en el DOM, el registro da 400.
// Sale con error si algo no se cumple.
// uso: BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_org1b.js
const { chromium } = require('playwright');
function falla(m) { console.error('FALLA: ' + m); process.exit(1); }
const CLAVE = 'Clave-Inventada-123';

(async () => {
  const b = await chromium.launch();
  const base = process.env.BASE_URL || 'http://127.0.0.1:8820';
  const id = Date.now();

  // El dueño crea su estudio e invita a un email inventado.
  const dueno = await b.newContext();
  let r = await dueno.request.post(base + '/api/organizations/create', {
    data: { name: 'Estudio Inventado ORG-1b', username: 'o1b_' + id, password: CLAVE, email: 'o1b' + id + '@ejemplo.test' },
  });
  if (!r.ok()) falla('alta del estudio: ' + r.status() + ' ' + await r.text());
  const invitado = 'invitada' + id + '@ejemplo.test';
  r = await dueno.request.post(base + '/api/organizations/invite', { data: { email: invitado } });
  if (!r.ok()) falla('invitación: ' + r.status() + ' ' + await r.text());
  const token = (await r.json()).invite_link.split('invite=')[1];
  if (!token) falla('la invitación no trae token');

  // Abre la landing en un contexto nuevo (sin sesión) y espera a que la
  // pantalla termine de mirar la invitación, si la hay.
  async function abrir(query, rutaFalsa) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    if (rutaFalsa) await page.route('**/api/invitations/**', rutaFalsa);
    const consulta = query
      ? page.waitForResponse(x => x.url().includes('/api/invitations/'), { timeout: 10000 })
          .catch(() => falla(query + ': la pantalla no consultó la invitación'))
      : null;
    await page.goto(base + '/' + query);
    if (consulta) {
      const resp = await consulta;
      await resp.finished();
      if (resp.status() === 200) {
        // válida: la pantalla muestra el aviso del estudio cuando terminó
        await page.waitForSelector('#inviteBanner', { state: 'visible', timeout: 10000 })
          .catch(() => falla(query + ': la invitación válida no muestra el aviso del estudio'));
      } else {
        // no válida: la pantalla no cambia nada visible; se le da un turno
        // para procesar la respuesta antes de mirar el campo
        await page.evaluate(() => new Promise(res => setTimeout(res, 0)));
        if (await page.isVisible('#inviteBanner')) falla(query + ': se ve el aviso con una invitación no válida');
      }
    }
    return { ctx, page };
  }
  async function campo(page) {
    return page.$eval('#registerForm input[name=email]', el => ({
      value: el.value, readOnly: el.readOnly, disabled: el.disabled,
    }));
  }
  async function pista(page) {
    const el = await page.$('#inviteEmailHint');
    return el ? el.isVisible() : false;
  }
  async function registrar(page) {
    await page.fill('#registerForm input[name=name]', 'Invitada Inventada');
    await page.fill('#registerForm input[name=password]', CLAVE);
    const resp = page.waitForResponse(x => x.url().endsWith('/auth/register') && x.request().method() === 'POST', { timeout: 15000 })
      .catch(() => falla('no se pidió el registro'));
    await page.click('#registerForm button[type=submit]');
    return resp;
  }
  async function editableYVacio(query, que, rutaFalsa) {
    const { ctx, page } = await abrir(query, rutaFalsa);
    const c = await campo(page);
    if (c.value !== '' || c.readOnly || c.disabled) falla(que + ': el email no queda vacío y editable: ' + JSON.stringify(c));
    if (await pista(page)) falla(que + ': se ve la línea del email invitado');
    await ctx.close();
    console.log('OK ' + que + ': el email queda vacío y editable');
  }

  // 1. Sin `invite` y con un token que no existe: como antes.
  await editableYVacio('', 'sin invite');
  await editableYVacio('?invite=token-que-no-existe-' + id, 'token inexistente');

  // 2. Válida pero sin email en la respuesta: como antes.
  await editableYVacio('?invite=' + encodeURIComponent(token), 'válida sin email',
    route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ valid: true, email: '', org_name: 'Estudio Inventado ORG-1b' }) }));

  // 3. Válida, con el email cambiado a mano en el DOM: el servidor da 400 y
  // la invitación no se gasta.
  {
    const { ctx, page } = await abrir('?invite=' + encodeURIComponent(token));
    await page.$eval('#registerForm input[name=email]', el => { el.readOnly = false; el.value = 'otra' + Date.now() + '@ejemplo.test'; });
    const resp = await registrar(page);
    if (resp.status() !== 400) falla('con el email cambiado en el DOM el registro dio ' + resp.status() + ', no 400');
    await page.waitForFunction(() => !document.getElementById('registerError').hidden, null, { timeout: 5000 })
      .catch(() => falla('con el email cambiado en el DOM no se muestra el error'));
    const msg = await page.$eval('#registerError', el => el.textContent);
    if (!msg.includes('otro email')) falla('el error del 400 no dice «otro email»: ' + msg);
    await ctx.close();
    console.log('OK con el email cambiado en el DOM, el servidor da 400 («' + msg.trim() + '»)');
  }

  // 4. Válida: email completo, de sólo lectura, con su línea; el registro entra.
  {
    const { ctx, page } = await abrir('?invite=' + encodeURIComponent(token));
    const c = await campo(page);
    if (c.value !== invitado) falla('con invitación válida el email no viene completo: ' + JSON.stringify(c));
    if (!c.readOnly) falla('con invitación válida el email no es de sólo lectura');
    if (c.disabled) falla('con invitación válida el email está disabled (no viajaría en el envío)');
    if (!(await pista(page))) falla('con invitación válida no se ve la línea del email invitado');
    // escribir encima no lo cambia
    await page.type('#registerForm input[name=email]', 'x');
    if ((await campo(page)).value !== invitado) falla('el email de sólo lectura se pudo escribir');
    const resp = await registrar(page);
    if (resp.status() !== 200) falla('con invitación válida el registro dio ' + resp.status() + ': ' + await resp.text());
    const enviado = JSON.parse(resp.request().postData());
    if (enviado.email !== invitado || enviado.invite_token !== token) falla('el registro no mandó el email y el token: ' + JSON.stringify({ email: enviado.email, invite_token: enviado.invite_token }));
    await ctx.close();
    const m = await (await dueno.request.get(base + '/api/organizations/mine')).json();
    const emails = ((m.organization || {}).members || []).map(x => x.email);
    if (!emails.includes(invitado)) falla('la invitada no quedó en el estudio: ' + JSON.stringify(emails));
    console.log('OK con invitación válida el email viene completo y de sólo lectura, y el registro entra al estudio');
  }

  // 5. El mismo token, ya usado: como antes.
  await editableYVacio('?invite=' + encodeURIComponent(token), 'token ya usado');

  await b.close();
  console.log('OK ORG-1b');
})().catch(e => falla(e && e.stack || String(e)));
