'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const puppeteer = require('puppeteer');

const baseUrl = process.env.E2E_BASE_URL;
const fixturePath = process.env.E2E_FIXTURE;
const artifactsDir = process.env.E2E_ARTIFACTS;

if (!baseUrl || !fixturePath || !artifactsDir) {
    throw new Error('Faltan E2E_BASE_URL, E2E_FIXTURE o E2E_ARTIFACTS. Usá scripts/testing/e2e_maria.sh.');
}

function expect(condition, message) {
    assert.ok(condition, message);
}

async function replaceInput(page, selector, value, index = 0) {
    const inputs = await page.$$(selector);
    expect(inputs[index], `No se encontró ${selector} en posición ${index}.`);
    const input = inputs[index];
    // Usamos el setter nativo y eventos de usuario del navegador: así el test
    // ejercita los listeners reales del formulario sin depender del atajo
    // Cmd/Ctrl+A de la plataforma que ejecute Chromium. Scroll/focus también
    // permite editar campos en una fila que todavía quedó fuera del viewport.
    await input.evaluate((element, nextValue) => {
        element.scrollIntoView({ block: 'center', inline: 'nearest' });
        element.focus();
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(element, String(nextValue));
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.blur();
    }, value);
}

async function browserJson(page, endpoint, method = 'GET', payload) {
    return page.evaluate(async ({ endpoint, method, payload }) => {
        const options = { method };
        if (payload !== undefined) options.body = JSON.stringify(payload);
        const response = await window.CDI.api(endpoint, options);
        return {
            status: response.status,
            body: await response.json().catch(() => ({})),
        };
    }, { endpoint, method, payload });
}

async function assertMariaDownload(page) {
    const cdp = await page.browser().target().createCDPSession();
    await cdp.send('Browser.setDownloadBehavior', {
        behavior: 'allow',
        downloadPath: artifactsDir,
        eventsEnabled: true,
    });
    const downloadStarted = new Promise((resolve) => cdp.once('Browser.downloadWillBegin', resolve));
    const downloadCompleted = new Promise((resolve, reject) => cdp.on('Browser.downloadProgress', (event) => {
        if (event.state === 'completed') resolve(event);
        if (event.state === 'canceled') reject(new Error('El navegador canceló la descarga de MARIA.TXT.'));
    }));
    await page.click('#readyDownloadBtn');
    const download = await downloadStarted;
    await downloadCompleted;
    const content = await fs.readFile(path.join(artifactsDir, download.suggestedFilename), 'utf8');
    await cdp.detach();

    for (const block of ['[DDT]', '[CPL]', '[DVD]', '[ART]', '[SBT]']) {
        expect(content.includes(block), `MARIA.TXT no contiene ${block}.`);
    }
    assert.equal((content.match(/\[ART\]/g) || []).length, 1, 'La agrupación debía generar un único [ART].');
}

async function registerAndOpenDashboard(page) {
    await page.goto(`${baseUrl}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#btnOpenAuth');
    await page.click('#btnOpenAuth');
    await page.waitForSelector('#authPopover:not([hidden])');
    await page.click('#loginForm [data-tab="register"]');
    await page.waitForSelector('#registerForm.is-active');

    await page.type('#registerForm input[name="name"]', 'Despachante E2E');
    await page.type('#registerForm input[name="email"]', 'despachante.e2e@cdi.test');
    await page.type('#registerForm input[name="password"]', 'E2e-maria-2026');

    const navigation = page.waitForNavigation({ waitUntil: 'domcontentloaded' });
    await page.click('#registerForm button[type="submit"]');
    await navigation;
    await page.waitForSelector('#uploadPickBtn');
    await page.waitForFunction(() => Boolean(window.CDI && window.CDI.api));
    // El alta real presenta el tour de bienvenida de CDI. Lo cerramos por su
    // control visible antes de iniciar el despacho, evitando que su navegación
    // diferida interrumpa una operación que ya está en curso.
    await page.waitForSelector('#tourWelcomeModal:not([hidden])');
    await page.click('#tourWelcomeSkip');
    await page.waitForSelector('#tourWelcomeModal[hidden]');
}

async function createAndSelectClient(page) {
    const result = await browserJson(page, '/api/clientes', 'POST', {
        nombre: 'Importadora E2E SA',
        cuit: '30715958844',
        direccion: 'Calle de prueba 123',
        fecha_inic_activ: '2020-01-01',
        preferred_currency: 'DOL',
    });
    assert.equal(result.status, 200, `No se pudo preparar el cliente E2E: ${JSON.stringify(result.body)}`);
    expect(result.body.cliente && result.body.cliente.id, 'El alta del cliente E2E no devolvió id.');

    // El dashboard puede llegar antes que los módulos diferidos de cada
    // pantalla. Esta interacción visible vuelve a entrar a Upload y garantiza
    // que sus listeners reales (selector y picker) ya están montados.
    await page.click('[data-action="go-upload"]');
    await page.waitForSelector('[data-screen="upload"].is-active');
    await page.click('#uploadFormatExcel');
    const fileInput = await page.$('#uploadFileInput');
    expect(fileInput, 'No se encontró el input de planilla.');
    await fileInput.uploadFile(fixturePath);
    await page.waitForSelector('[data-testid="client-picker-row"]');
    await page.click('[data-testid="client-picker-row"]');
    await page.waitForSelector('[data-screen="review"].is-active');
    return result.body.cliente;
}

async function confirmReview(page) {
    const summary = await page.$eval('#reviewMetaPill', (el) => el.textContent || '');
    expect(summary.includes('2 items detectados'), 'La revisión no mostró los dos ítems extraídos de la planilla.');
    assert.equal(await page.$eval('#f_comprador_nombre', (el) => el.value), 'Importadora E2E SA');
    await replaceInput(page, '#f_incoterm', 'FOB');
    await page.waitForFunction(() => !document.getElementById('reviewContinueBtn').disabled);
    await page.click('#reviewContinueBtn');
    await page.waitForSelector('[data-screen="ncm"].is-active');
}

async function classifyAndGroup(page) {
    await page.waitForFunction(() => document.querySelectorAll('[data-testid="ncm-sim-input"]').length === 2);
    expect(await page.$eval('#ncmContinueBtn', (el) => el.disabled), 'Una NCM de 8 dígitos no bloqueó el avance a Validación.');

    for (const [selector, value] of [
        ['[data-testid="ncm-origin-input"]', '310'],
        ['[data-testid="ncm-quantity-input"]', '2'],
        ['[data-testid="ncm-value-input"]', '125'],
        ['[data-testid="ncm-weight-input"]', '0.5'],
    ]) {
        await replaceInput(page, selector, value, 0);
        await replaceInput(page, selector, value, 1);
    }
    const corrected = await page.evaluate(() => Object.fromEntries([
        'ncm-origin-input', 'ncm-quantity-input', 'ncm-value-input', 'ncm-weight-input',
    ].map((testId) => [
        testId,
        Array.from(document.querySelectorAll(`[data-testid="${testId}"]`), (input) => input.value),
    ])));
    expect(corrected['ncm-origin-input'].every((value) => value.startsWith('310')), 'El origen corregido no quedó visible en ambas filas.');
    assert.deepEqual(corrected['ncm-quantity-input'], ['2', '2']);
    assert.deepEqual(corrected['ncm-value-input'], ['125', '125']);
    assert.deepEqual(corrected['ncm-weight-input'], ['0.5', '0.5']);

    // Pegar la posición completa en una fila carga 11 dígitos y DC. Al
    // seleccionar ambas, la acción masiva reutiliza esa única SIM y las une.
    await replaceInput(page, '[data-testid="ncm-sim-input"]', '84713000900R');
    await page.waitForFunction(() => document.getElementById('ncmContinueBtn').disabled);
    await page.click('#ncmSelectAll');
    await page.waitForFunction(() => document.getElementById('ncmBatchNcm').value.replace(/\D/g, '').length === 11);
    assert.equal(await page.$eval('#ncmBatchDc', (el) => el.value), 'R');
    await page.click('#ncmBatchAgrupar');
    await page.waitForSelector('#ncmTbody .ncm-grupo-chip');
    await page.waitForFunction(() => !document.getElementById('ncmContinueBtn').disabled);
}

async function verifyBlockingErrorsAndNonBlockingWarnings(page) {
    await replaceInput(page, '[data-testid="ncm-weight-input"]', '0');
    await page.click('#ncmContinueBtn');
    await page.waitForSelector('#validatingResults:not([hidden])');
    expect(
        (await page.$eval('#validatingIssues', (el) => el.textContent || '')).includes('peso unitario debe ser mayor a cero'),
        'La validación no mostró el peso inválido como error.',
    );
    expect(await page.$eval('#validatingGenerate', (el) => el.disabled), 'Un error de peso no bloqueó Generar MARIA.TXT.');

    await page.click('[data-action="go-ncm-from-validating"]');
    await page.waitForSelector('[data-screen="ncm"].is-active');
    await replaceInput(page, '[data-testid="ncm-weight-input"]', '0.5');
    await page.click('#ncmContinueBtn');
    await page.waitForSelector('#validatingResults:not([hidden])');
    await page.click('#validatingRerun');
    await page.waitForFunction(() => !document.getElementById('validatingGenerate').disabled);
    expect(
        (await page.$eval('#validatingIssues', (el) => el.textContent || '')).includes('Computadoras'),
        'La advertencia esperada de la posición 8471 no se mostró.',
    );

    await page.click('#validatingGenerate');
    await page.waitForFunction(() => {
        const error = document.getElementById('sbtFieldError');
        return error && !error.hidden;
    });
    expect(
        (await page.$eval('#sbtFieldError', (el) => el.textContent || '')).includes('obligatorio'),
        'La ausencia de SBT no bloqueó la generación con un mensaje claro.',
    );
    await replaceInput(page, '#sbtSufijoValor', 'AA(E2E)-AB(E2E)-CA00-');
    await page.click('#validatingGenerate');
    await page.waitForSelector('#readyDone:not([hidden])');
}

async function verifyPersistenceAndMemory(page, client) {
    await page.waitForFunction(async (clientId) => {
        const response = await window.CDI.api(`/api/clientes/${encodeURIComponent(clientId)}/operaciones`);
        const data = await response.json().catch(() => ({}));
        return response.ok && Array.isArray(data.operaciones) && data.operaciones.length === 1;
    }, { timeout: 15000 }, client.id);

    const operations = await browserJson(page, `/api/clientes/${encodeURIComponent(client.id)}/operaciones`);
    assert.equal(operations.body.operaciones.length, 1, 'La operación no quedó guardada para el cliente activo.');

    const products = await browserJson(page, `/api/clientes/${encodeURIComponent(client.id)}/catalogo/productos`);
    expect(products.body.productos.length >= 1, 'La operación no alimentó la memoria del cliente.');
    expect(
        products.body.productos.every((product) =>
            String(product.ncm || '').replace(/\D/g, '') === '84713000' && product.origen === '310'
        ),
        'La memoria no conservó la posición SIM y el origen confirmados.',
    );

    const nextInvoice = await browserJson(page, '/api/catalog/lookup', 'POST', {
        client_id: client.id,
        vendor_name: '',
        items: [{ descripcion: 'Modulo de prueba E2E A', pieza: '', origen: 'XX', peso_unitario: 0 }],
    });
    const remembered = nextInvoice.body.items && nextInvoice.body.items[0];
    expect(
        remembered && remembered.source === 'cliente' && remembered.ncm === '84713000' && remembered.origen === '310',
        'La próxima factura no recibe NCM y origen confirmados del cliente.',
    );
    expect(
        !Object.hasOwn(remembered, 'peso_unitario_avg'),
        'La memoria no debe ofrecer peso para autocompletar una próxima factura.',
    );

    const suggestion = await browserJson(page, '/api/ncm/sugerir', 'POST', {
        descripcion: 'Modulo de prueba E2E A',
        client_id: client.id,
    });
    expect(
        suggestion.body.sugerencias.some((item) => item.source === 'historial' && item.ncm === '84713000'),
        'La próxima factura no recibe la sugerencia NCM confirmada del cliente.',
    );
}

async function main() {
    await fs.mkdir(artifactsDir, { recursive: true });
    let browser;
    let page;
    let tracing = false;
    try {
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
            defaultViewport: { width: 1440, height: 1100 },
        });
        page = await browser.newPage();
        page.setDefaultTimeout(15000);
        await page.tracing.start({ path: path.join(artifactsDir, 'trace.json'), screenshots: true });
        tracing = true;
        // El feed editorial de ARCA y las cotizaciones no forman parte del
        // despacho. Los bloqueamos en el navegador para que esta prueba no
        // dependa de Internet ni presente contenido externo como dato del
        // flujo probado.
        await page.setRequestInterception(true);
        page.on('request', (request) => {
            const url = new URL(request.url());
            if (url.origin === baseUrl && ['/api/arca/novedades', '/api/financials'].includes(url.pathname)) {
                void request.abort('blockedbyclient');
                return;
            }
            void request.continue();
        });

        await registerAndOpenDashboard(page);
        const client = await createAndSelectClient(page);
        await confirmReview(page);
        await classifyAndGroup(page);
        await verifyBlockingErrorsAndNonBlockingWarnings(page);
        await assertMariaDownload(page);
        await verifyPersistenceAndMemory(page, client);
        await page.tracing.stop();
        tracing = false;

        console.log('E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.');
    } catch (error) {
        const detail = error && error.stack ? error.stack : String(error);
        await fs.writeFile(path.join(artifactsDir, 'failure.txt'), detail);
        if (page) {
            if (tracing) await page.tracing.stop().catch(() => {});
            await page.screenshot({ path: path.join(artifactsDir, 'failure.png'), fullPage: true }).catch(() => {});
            const html = await page.content().catch(() => '');
            await fs.writeFile(path.join(artifactsDir, 'failure.html'), html).catch(() => {});
        }
        throw error;
    } finally {
        if (browser) await browser.close();
    }
}

main().catch((error) => {
    console.error(error && error.stack ? error.stack : error);
    process.exitCode = 1;
});
