/* ============================================================
   CDI v2 — Screens 4 y 5: Validating + Ready
   Pantalla 4 (validating): llama /api/validate/smart, muestra stats
   y lista de errores / advertencias / sugerencias. Boton "Generar"
   bloqueado si hay errores criticos.
   Pantalla 5 (ready): llama /generate_maria, muestra preview, boton
   de descarga y opcion de empezar nueva operacion.
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    /* ---------- shared refs ---------- */
    let vLoading, vResults, vStatus, vTitle, vSubtitle, vStats, vIssues, vRerun, vGenerate;
    let rGenerating, rDone, rSubtitle, rDownload, rCopy, rFilename, rPreview, rError;
    let initialized = false;

    let lastValidation = null;    // { errores, advertencias, sugerencias, estadisticas }
    let lastValidationTs = 0;
    let lastMaria = null;         // { filename, download_url, content }
    let validatingInFlight = false;
    let generateInFlight = false;

    function $(id) { return document.getElementById(id); }
    function show(el) { if (el) el.hidden = false; }
    function hide(el) { if (el) el.hidden = true; }

    function init() {
        if (initialized) return;
        // validating
        vLoading   = $('validatingLoading');
        vResults   = $('validatingResults');
        vStatus    = $('validatingStatus');
        vTitle     = $('validatingTitle');
        vSubtitle  = $('validatingSubtitle');
        vStats     = $('validatingStats');
        vIssues    = $('validatingIssues');
        vRerun     = $('validatingRerun');
        vGenerate  = $('validatingGenerate');

        // ready
        rGenerating = $('readyGenerating');
        rDone       = $('readyDone');
        rSubtitle   = $('readySubtitle');
        rDownload   = $('readyDownloadBtn');
        rCopy       = $('readyCopyBtn');
        rFilename   = $('readyFilename');
        rPreview    = $('readyPreview');
        rError      = $('readyError');

        if (!vLoading || !rGenerating) return;

        if (vRerun)    vRerun.addEventListener('click', () => runValidation(/* force */ true));
        if (vGenerate) vGenerate.addEventListener('click', onGenerate);
        if (rDownload) rDownload.addEventListener('click', onDownload);
        if (rCopy)     rCopy.addEventListener('click', onCopy);

        initialized = true;
    }

    /* ==========================================================
       Pantalla 4: validating
       ========================================================== */
    function onEnterValidating() {
        init();
        if (!vLoading) return;
        const items = (CDI.state && CDI.state.items) || [];
        if (!items.length) {
            CDI.toast('Sin ítems', 'Volvé a cargar el PDF.', 'error');
            CDI.goTo('upload');
            return;
        }
        runValidation(false);
    }

    async function runValidation(force) {
        init();
        if (validatingInFlight) return;
        const now = Date.now();
        // Cache: si ya tenemos resultado de hace menos de 60s y no forzamos, reusar
        if (!force && lastValidation && (now - lastValidationTs) < 60000) {
            renderValidation(lastValidation);
            return;
        }

        validatingInFlight = true;
        show(vLoading);
        hide(vResults);

        const items = buildItemsForValidation();
        try {
            const startedAt = Date.now();
            const res = await CDI.api('/api/validate/smart', {
                method: 'POST',
                body: JSON.stringify({ items })
            });
            const data = await res.json();
            const dur = Date.now() - startedAt;
            if (!res.ok || !data || data.success === false) {
                throw new Error((data && data.detail) || 'No se pudo validar');
            }
            lastValidation = data;
            lastValidationTs = Date.now();
            CDI.track('validation_ok', {
                errores: (data.errores || []).length,
                advertencias: (data.advertencias || []).length,
                sugerencias: (data.sugerencias || []).length,
                duration_ms: dur
            });
            renderValidation(data);
        } catch (err) {
            console.error('[validating]', err);
            CDI.track('validation_error', { message: String(err && err.message || err) });
            CDI.toast('Error al validar', String(err && err.message || err), 'error');
            // Mostrar resultados "vacios" para no bloquear: permitimos seguir
            renderValidation({
                errores: [],
                advertencias: ['No se pudo contactar al validador. Podés continuar con revisión manual.'],
                sugerencias: [],
                estadisticas: { total_items: items.length, total_valor_usd: 0, total_peso_kg: 0, ncms_unicos: 0 }
            });
        } finally {
            validatingInFlight = false;
        }
    }

    function buildItemsForValidation() {
        const items = (CDI.state && CDI.state.items) || [];
        return items.map(it => ({
            pieza: String(it.pieza || '').trim(),
            descripcion: String(it.descripcion || '').trim(),
            origen: String(it.origen || 'XX').trim().toUpperCase() || 'XX',
            cantidad: toNumber(it.cantidad, 1),
            valor_unitario: toNumber(it.valor_unitario, 0),
            peso_unitario: toNumber(it.peso_unitario, 0)
        }));
    }

    function toNumber(v, fallback) {
        const n = Number(v);
        return isFinite(n) ? n : fallback;
    }

    function renderValidation(data) {
        hide(vLoading);
        show(vResults);

        const errores = data.errores || [];
        const advertencias = data.advertencias || [];
        const sugerencias = data.sugerencias || [];
        const stats = data.estadisticas || {};

        // Status pill
        let kind = 'clean';
        let label = 'Todo listo para generar';
        let subtitle = 'No se detectaron problemas críticos. El archivo MARIA puede generarse.';
        if (errores.length > 0) {
            kind = 'error';
            label = errores.length + (errores.length === 1 ? ' error para corregir' : ' errores para corregir');
            subtitle = 'Revisá los puntos en rojo antes de generar el archivo.';
        } else if (advertencias.length > 0) {
            kind = 'warning';
            label = advertencias.length + (advertencias.length === 1 ? ' advertencia para revisar' : ' advertencias para revisar');
            subtitle = 'Se puede continuar, pero conviene revisar las advertencias para evitar demoras en AFIP.';
        }
        vStatus.className = 'validating-status is-' + kind;
        vStatus.innerHTML = '<span class="dot-status is-' + (kind === 'clean' ? 'success' : kind) + '"></span>' +
            CDI.escapeHtml(label);
        vSubtitle.textContent = subtitle;

        // Stats
        const statsHtml = [
            statCell(stats.total_items, 'Ítems', ''),
            statCell(stats.ncms_unicos, 'NCMs distintos', ''),
            statCell(
                '$' + formatNumber(stats.total_valor_usd || 0),
                'Valor (USD)', ''
            ),
            statCell(
                formatNumber(stats.total_peso_kg || 0) + ' kg',
                'Peso total', ''
            )
        ].join('');
        vStats.innerHTML = statsHtml;

        // Issues
        const groups = [];
        if (errores.length)       groups.push(renderGroup('error',   'Errores críticos', errores));
        if (advertencias.length)  groups.push(renderGroup('warning', 'Advertencias',     advertencias));
        if (sugerencias.length)   groups.push(renderGroup('info',    'Sugerencias',      sugerencias));
        vIssues.innerHTML = groups.join('');

        // Generate button
        vGenerate.disabled = errores.length > 0 || generateInFlight;
        vGenerate.title = errores.length > 0 ? 'Corregí los errores antes de generar' : '';
    }

    function statCell(value, label) {
        const v = (value === null || value === undefined || value === '') ? '—' : String(value);
        return (
            '<div class="validating-stat">' +
                '<div class="validating-stat-num">' + CDI.escapeHtml(v) + '</div>' +
                '<div class="validating-stat-label">' + CDI.escapeHtml(label) + '</div>' +
            '</div>'
        );
    }

    function renderGroup(kind, title, list) {
        const rows = list.map(msg => {
            const clean = stripLeadingIcon(String(msg));
            const rowRef = extractItemRef(clean);
            return (
                '<li>' +
                    (rowRef ? '<span class="issue-row">' + CDI.escapeHtml(rowRef) + '</span>' : '<span class="issue-row"></span>') +
                    '<span class="issue-msg">' + CDI.escapeHtml(clean) + '</span>' +
                '</li>'
            );
        }).join('');
        return (
            '<div class="issue-group is-' + kind + '">' +
                '<header class="issue-group-header">' +
                    '<strong>' + CDI.escapeHtml(title) + '</strong>' +
                    '<span class="caption">· ' + list.length + '</span>' +
                '</header>' +
                '<ul class="issue-list">' + rows + '</ul>' +
            '</div>'
        );
    }

    // Backend a veces manda "✅ ", "⚠️ ", "📋 ", etc. Sacamos el emoji inicial
    // para que la UI quede consistente con el style minimalista.
    function stripLeadingIcon(s) {
        return s.replace(/^[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\s]+/u, '').trim();
    }
    function extractItemRef(s) {
        const m = /\b(i|I)tem\s+(\d+)/.exec(s);
        return m ? ('#' + m[2]) : '';
    }

    function formatNumber(n) {
        const num = Number(n) || 0;
        try {
            return num.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        } catch (_) {
            return String(num.toFixed(2));
        }
    }

    /* ==========================================================
       Pantalla 5: ready (generar + descargar)
       ========================================================== */
    function onGenerate() {
        if (generateInFlight) return;
        if (lastValidation && (lastValidation.errores || []).length > 0) return;
        CDI.goTo('ready', { fromValidating: true });
    }

    function onEnterReady() {
        init();
        if (!rGenerating) return;
        hide(rDone);
        hide(rError);
        show(rGenerating);
        generateMaria();
    }

    async function generateMaria() {
        if (generateInFlight) return;
        generateInFlight = true;

        const items = (CDI.state && CDI.state.items) || [];
        if (!items.length) {
            showReadyError('No hay ítems para generar. Volvé a cargar el PDF.');
            generateInFlight = false;
            return;
        }

        const body = buildMariaRequest();
        try {
            const startedAt = Date.now();
            const res = await CDI.api('/generate_maria', {
                method: 'POST',
                body: JSON.stringify(body)
            });
            const data = await res.json();
            const dur = Date.now() - startedAt;
            if (!res.ok || !data || data.success === false) {
                const detail = (data && (data.detail || data.message)) || res.statusText;
                throw new Error(detail || 'No se pudo generar el archivo');
            }
            lastMaria = {
                filename: data.filename,
                download_url: data.download_url,
                content: data.content || ''
            };
            CDI.track('maria_generated', {
                items: items.length,
                filename: data.filename,
                duration_ms: dur
            });
            renderReady();
            // Best-effort: guardar en historial del cliente activo (si hay)
            saveOperationToHistory(items, data).catch(err => {
                console.warn('[history] no se pudo guardar operacion', err);
            });
            // Best-effort: aprender productos en catalogo del proveedor
            saveCatalogLearn(items).catch(err => {
                console.warn('[catalog] no se pudo aprender', err);
            });
        } catch (err) {
            console.error('[ready] generate error', err);
            CDI.track('maria_generate_error', { message: String(err && err.message || err) });
            showReadyError(String(err && err.message || err));
        } finally {
            generateInFlight = false;
        }
    }

    function buildMariaRequest() {
        const op = (CDI.state && CDI.state.operacion) || {};
        const stats = (lastValidation && lastValidation.estadisticas) || {};

        const moneda = (op.moneda || 'DOL').toString().toUpperCase();
        const incoterm = (op.incoterm || 'FOB').toString().toUpperCase();

        const factura = String(op.numero_factura || '').trim();
        const operation_id = factura ? ('FAC_' + factura.replace(/[^a-zA-Z0-9_-]/g, '')) :
            ('OP_' + new Date().toISOString().replace(/[^0-9]/g, '').slice(0, 14));

        const items = (CDI.state.items || []).map(it => ({
            pieza: String(it.pieza || '').trim(),
            descripcion: String(it.descripcion || '').trim(),
            origen: String(it.origen || 'XX').trim().toUpperCase() || 'XX',
            cantidad: toNumber(it.cantidad, 1),
            valor_unitario: toNumber(it.valor_unitario, 0),
            peso_unitario: toNumber(it.peso_unitario, 0),
            codigo_parte: String(it.codigo_parte || '').trim()
        }));

        // Cliente activo propaga domicilio + fecha inicio actividad del importador
        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;

        // CUIT del despachante: si el user tiene en perfil, lo usamos
        // automaticamente (backend tambien hace fallback, aca vamos explicitos).
        const cuit_agr = String(
            op.cuit_agr || (CDI.currentUser && CDI.currentUser.cuit) || ''
        ).replace(/[-\s]/g, '');

        return {
            operation_id: operation_id,
            items: items,
            moneda: moneda,
            incoterm: incoterm,
            cuit_agr: cuit_agr,
            vendedor_nombre: String(op.vendedor_nombre || '').trim(),
            vendedor_id: String(op.vendedor_id || '').trim(),
            comprador_nombre: String(op.comprador_nombre || '').trim(),
            comprador_cuit: String(op.comprador_cuit || '').replace(/[-\s]/g, ''),
            comprador_domicilio: String(
                op.comprador_domicilio ||
                (cliente && cliente.direccion) || ''
            ).trim(),
            comprador_fecha_inic_activ: String(
                op.comprador_fecha_inic_activ ||
                (cliente && cliente.fecha_inic_activ) || ''
            ).trim(),
            flete: toNumber(op.flete, 0),
            seguro: toNumber(op.seguro, 0),
            bl_numero: String(op.bl || op.bl_numero || '').trim(),
            puerto_origen: String(op.puerto_origen || '').trim(),
            puerto_destino: String(op.puerto_destino || 'ARBUE').trim() || 'ARBUE',
            buque_nombre: String(op.buque || op.buque_nombre || '').trim(),
            viaje_numero: String(op.viaje_numero || '').trim(),
            fecha_embarque: String(op.fecha_embarque || '').trim(),
            fecha_emision: String(op.fecha_emision || '').trim(),
            contenedor_numero: String(op.contenedor_numero || '').trim(),
            contenedor_tipo: String(op.contenedor_tipo || '').trim(),
            contenedor_peso: toNumber(op.contenedor_peso, 0),
            aduana_codigo: String(op.aduana_codigo || '001').trim() || '001',
            tipo_destinacion: String(op.tipo_destinacion || 'IC04').trim().toUpperCase() || 'IC04'
        };
    }

    function renderReady() {
        hide(rGenerating);
        hide(rError);
        show(rDone);
        if (!lastMaria) return;

        const stats = (lastValidation && lastValidation.estadisticas) || {};
        const total = stats.total_items || ((CDI.state.items || []).length);
        rSubtitle.textContent =
            'MARIA.TXT generado. ' + total + ' ítems · ' +
            '$' + formatNumber(stats.total_valor_usd || 0) + ' USD.';

        rFilename.textContent = lastMaria.filename || 'MARIA.TXT';
        rPreview.textContent = trimPreview(lastMaria.content || '', 60);

        // Render del panel "operación huérfana": aparece solo si no hay
        // cliente activo y el user no hizo "Más tarde" en esta operación.
        renderOrphanPanel();
    }

    /* ---------- Panel "operación huérfana" ---------- */
    function renderOrphanPanel() {
        const panel = document.getElementById('readyOrphanPanel');
        if (!panel) return;
        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;
        const opCode = (lastMaria && lastMaria.filename) || null;
        const dismissedFor = (CDI.state && CDI.state.orphanDismissedFor) || null;
        const wasDismissed = !!(dismissedFor && opCode && dismissedFor === opCode);

        if (cliente && cliente.id) { panel.hidden = true; return; }
        if (wasDismissed) { panel.hidden = true; return; }

        panel.hidden = false;
        // Reset del form interno por si quedó abierto antes
        const form = document.getElementById('readyOrphanCreateForm');
        if (form) form.hidden = true;
        clearOrphanCreateError();
        setupOrphanPanelListeners();
        prefillOrphanCreateForm();
        try { CDI.track && CDI.track('op_orphan_panel_shown'); } catch (_) {}
    }

    let _orphanListenersWired = false;
    function setupOrphanPanelListeners() {
        if (_orphanListenersWired) return;
        const btnCreate = document.getElementById('orphanCreateBtn');
        const btnAssign = document.getElementById('orphanAssignBtn');
        const btnLater  = document.getElementById('orphanLaterBtn');
        const btnSave   = document.getElementById('orphanCreateSaveBtn');
        const btnCancel = document.getElementById('orphanCreateCancelBtn');
        const form      = document.getElementById('readyOrphanCreateForm');

        if (btnCreate) btnCreate.addEventListener('click', () => {
            CDI.track && CDI.track('op_orphan_create_clicked');
            if (form) form.hidden = false;
            const inp = document.getElementById('orphanCreateNombre');
            if (inp) inp.focus();
        });
        if (btnCancel) btnCancel.addEventListener('click', () => {
            if (form) form.hidden = true;
            clearOrphanCreateError();
        });
        if (btnAssign) btnAssign.addEventListener('click', orphanAssignClick);
        if (btnLater)  btnLater.addEventListener('click', orphanLaterClick);
        if (btnSave)   btnSave.addEventListener('click', orphanCreateSubmit);

        _orphanListenersWired = true;
    }

    function prefillOrphanCreateForm() {
        const op = (CDI.state && CDI.state.operacion) || {};
        const inpNom = document.getElementById('orphanCreateNombre');
        const inpCuit = document.getElementById('orphanCreateCuit');
        if (inpNom && !inpNom.value) inpNom.value = String(op.comprador_nombre || '').trim();
        if (inpCuit && !inpCuit.value) {
            const c = String(op.comprador_cuit || '').trim();
            inpCuit.value = (CDI.formatCuit && c) ? CDI.formatCuit(c) : c;
        }
    }

    function showOrphanCreateError(msg) {
        const el = document.getElementById('orphanCreateError');
        if (!el) return;
        el.textContent = msg || '';
        el.hidden = !msg;
    }
    function clearOrphanCreateError() { showOrphanCreateError(''); }

    async function lookupClienteByCuit(cuit) {
        try {
            const res = await CDI.api('/api/clientes/by-cuit/' + encodeURIComponent(cuit));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) return null;
            if (data.match === 'exact' && data.cliente) return data.cliente;
            return null;
        } catch (_) { return null; }
    }

    function humanizeApiError(detail, fallback) {
        if (!detail) return fallback;
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
            const msg = detail.map(d => (d && d.msg) || '').filter(Boolean).join('; ');
            return msg || fallback;
        }
        if (detail.msg) return String(detail.msg);
        try { return JSON.stringify(detail); } catch (_) { return fallback; }
    }

    async function orphanCreateSubmit() {
        const btn = document.getElementById('orphanCreateSaveBtn');
        const inpNom = document.getElementById('orphanCreateNombre');
        const inpCuit = document.getElementById('orphanCreateCuit');
        const nombre = String((inpNom && inpNom.value) || '').trim();
        const cuitRaw = String((inpCuit && inpCuit.value) || '').trim();
        const cuit = (CDI.normalizeCuit && cuitRaw) ? CDI.normalizeCuit(cuitRaw) : '';
        clearOrphanCreateError();
        if (!nombre) {
            showOrphanCreateError('Ingresá la razón social.');
            if (inpNom) inpNom.focus();
            return;
        }
        if (cuit && cuit.length !== 11) {
            showOrphanCreateError('El CUIT debe tener 11 dígitos.');
            if (inpCuit) inpCuit.focus();
            return;
        }
        if (btn) btn.disabled = true;
        try {
            // Pre-check: si ya existe un cliente con este CUIT, ofrecer usar ese.
            if (cuit) {
                const existente = await lookupClienteByCuit(cuit);
                if (existente) {
                    CDI.track && CDI.track('op_orphan_create_blocked_by_cuit_match');
                    const ok = window.confirm(
                        'Ya tenés a "' + (existente.nombre || '') + '" con este CUIT.\n' +
                        '¿Querés usar ese cliente en su lugar?'
                    );
                    if (ok) {
                        CDI.setClienteActivo(existente);
                        await reSaveOperationAndClosePanel('create');
                    }
                    return;
                }
            }
            const body = { nombre: nombre };
            if (cuit) body.cuit = cuit;
            const res = await CDI.api('/api/clientes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const out = await res.json().catch(() => ({}));
            if (!res.ok || !out.success || !out.cliente) {
                showOrphanCreateError(humanizeApiError(out.detail, 'No se pudo crear el cliente.'));
                return;
            }
            CDI.clientesCache = [];
            CDI.setClienteActivo(out.cliente);
            await reSaveOperationAndClosePanel('create');
        } catch (err) {
            showOrphanCreateError('Error de red. Probá de nuevo.');
            console.warn('[orphan] crear cliente', err && err.message);
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    function orphanAssignClick() {
        if (!CDI.openClientePicker) return;
        CDI.track && CDI.track('op_orphan_assign_clicked');
        CDI.openClientePicker({
            title: 'Asignar a un cliente existente',
            subtitle: 'La operación va a quedar guardada en su historial',
            onSelect: async (c) => {
                CDI.setClienteActivo(c);
                await reSaveOperationAndClosePanel('assign');
            },
        });
    }

    function orphanLaterClick() {
        const opCode = (lastMaria && lastMaria.filename) || null;
        if (opCode) {
            CDI.state = CDI.state || {};
            CDI.state.orphanDismissedFor = opCode;
        }
        const panel = document.getElementById('readyOrphanPanel');
        if (panel) panel.hidden = true;
        CDI.track && CDI.track('op_orphan_dismissed');
    }

    async function reSaveOperationAndClosePanel(via) {
        const items = (CDI.state && CDI.state.items) || [];
        await saveOperationToHistory(items, lastMaria || {});
        const panel = document.getElementById('readyOrphanPanel');
        if (panel) panel.hidden = true;
        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;
        const nombre = (cliente && cliente.nombre) || 'cliente';
        CDI.toast && CDI.toast('Operación guardada', 'En el historial de ' + nombre, 'success');
        CDI.track && CDI.track('op_orphan_resolved', { via: via });
    }

    async function saveOperationToHistory(items, mariaData) {
        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;
        if (!cliente || !cliente.id) return;
        const opCode = (mariaData && mariaData.filename) || null;
        // Idempotencia: si ya guardamos esta misma operación para este mismo
        // cliente, no la re-posteamos (cubre re-entry a Listo, F5 suave, etc.).
        const savedFor = (CDI.state && CDI.state.operationSavedFor) || null;
        if (savedFor && savedFor.cliente_id === cliente.id && savedFor.op_code === opCode) {
            return;
        }
        const stats = (lastValidation && lastValidation.estadisticas) || {};
        const op = (CDI.state && CDI.state.operacion) || {};
        const total_valor = Number(stats.total_valor_usd || 0);
        const total_peso = Number(stats.total_peso_kg || 0);
        const body = {
            operation_id: opCode,
            source: 'pdf_v2',
            currency: (op.moneda || 'USD').toString().toUpperCase(),
            resumen: {
                items: items.length,
                valor_total: total_valor,
                peso_total: total_peso,
                ncms_unicos: stats.ncms_unicos || 0,
                numero_factura: op.numero_factura || '',
                fecha_emision: op.fecha_emision || ''
            },
            items: items.map(it => ({
                pieza: String(it.pieza || '').trim(),
                ncm: String(it.pieza || '').trim(),
                descripcion: String(it.descripcion || '').trim(),
                origen: String(it.origen || 'XX').trim().toUpperCase() || 'XX',
                cantidad: toNumber(it.cantidad, 1),
                valor_unitario: toNumber(it.valor_unitario, 0),
                peso_unitario: toNumber(it.peso_unitario, 0)
            }))
        };
        try {
            const res = await CDI.api(
                '/api/clientes/' + encodeURIComponent(cliente.id) + '/operaciones',
                { method: 'POST', body: JSON.stringify(body) }
            );
            const data = await res.json().catch(() => ({}));
            if (res.ok && data && data.success) {
                CDI.state = CDI.state || {};
                CDI.state.operationSavedFor = { cliente_id: cliente.id, op_code: opCode };
                CDI.track('operation_saved_to_history', {
                    cliente_id: cliente.id,
                    items: items.length
                });
            }
        } catch (_) { /* best-effort */ }
    }

    async function saveCatalogLearn(items) {
        const op = (CDI.state && CDI.state.operacion) || {};
        const vendorName = String(op.vendedor_nombre || '').trim();
        if (!vendorName || !Array.isArray(items) || !items.length) return;

        const productos = items.map(it => ({
            descripcion: String(it.descripcion || '').trim(),
            ncm: String(it.pieza || '').trim(),
            origen: String(it.origen || '').trim().toUpperCase(),
            unidad_medida: String(it.unidad_medida || '').trim(),
        })).filter(p => p.descripcion && p.ncm);

        if (!productos.length) return;

        // Derivar vendor_id slug (mismo criterio que backend: alfanumerico lowercased sin acentos)
        const vendor_id = vendorName
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
            .slice(0, 64) || 'proveedor';
        try {
            const res = await CDI.api('/api/catalog/' + encodeURIComponent(vendor_id) + '/productos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vendor_name: vendorName, productos }),
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                CDI.track('catalog_learn', {
                    vendor_id,
                    productos: productos.length,
                    saved: data && (data.saved || data.added) || 0,
                    updated: data && data.updated || 0,
                });
            }
        } catch (_) { /* best-effort */ }
    }

    function trimPreview(text, maxLines) {
        if (!text) return '';
        const lines = text.split(/\r?\n/);
        if (lines.length <= maxLines) return text;
        return lines.slice(0, maxLines).join('\n') + '\n…';
    }

    function showReadyError(msg) {
        hide(rGenerating);
        hide(rDone);
        show(rError);
        rError.textContent = msg || 'No se pudo generar el archivo.';
    }

    /* ---------- Actions ---------- */
    function onDownload() {
        if (!lastMaria || !lastMaria.download_url) {
            CDI.toast('Archivo no disponible', 'Volvé a generarlo.', 'error');
            return;
        }
        CDI.track('maria_download_click', { filename: lastMaria.filename });
        // Descarga con token via anchor: como el endpoint /download/<file>
        // no requiere auth en este proyecto, basta con un anchor.
        const a = document.createElement('a');
        a.href = lastMaria.download_url;
        a.download = lastMaria.filename || 'MARIA.TXT';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    async function onCopy() {
        if (!lastMaria || !lastMaria.content) return;
        try {
            await navigator.clipboard.writeText(lastMaria.content);
            CDI.toast('Copiado', 'El contenido del TXT está en el portapapeles.', 'success');
            CDI.track('maria_copied');
        } catch (err) {
            CDI.toast('No se pudo copiar', 'Seleccioná y copiá manualmente.', 'error');
        }
    }

    /* ---------- Back-nav from validating to NCM ---------- */
    document.addEventListener('click', (e) => {
        const t = e.target.closest('[data-action="go-ncm-from-validating"]');
        if (t) { e.preventDefault(); CDI.goTo('ncm'); }
    });

    /* ---------- Registro ---------- */
    CDI.registerScreen('validating', {
        onEnter: onEnterValidating,
        onLeave() { /* nada */ }
    });
    CDI.registerScreen('ready', {
        onEnter: onEnterReady,
        onLeave() {
            // Si el usuario va a 'upload' (nueva operacion), limpiamos cache
            lastMaria = null;
            lastValidation = null;
            lastValidationTs = 0;
        }
    });

    document.addEventListener('DOMContentLoaded', init);
})();
