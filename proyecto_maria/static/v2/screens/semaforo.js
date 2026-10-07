/* ============================================================
   CDI v2 - Semaforo flotante de validaciones
   FAB visible en screens review/ncm que llama POST /api/validate/smart
   con los items actuales (debounced) y muestra un dot verde/amarillo/rojo
   + contador de issues. Click abre popover con la lista clicable.
   ============================================================ */
(function () {
    'use strict';
    var CDI = window.CDI = window.CDI || {};

    var ACTIVE_SCREENS = ['review', 'ncm', 'validating'];
    var DEBOUNCE_MS = 500;
    var MIN_INTERVAL_MS = 1200; // piso entre fetches para no saturar

    var fab, dot, label, popover, popoverBody, popoverTitle, popoverEmpty, closeBtn;
    var initialized = false;
    var debounceTimer = null;
    var inFlight = false;
    var lastRequestMs = 0;
    var currentScreen = null;
    var popoverOpen = false;
    var lastIssues = { errores: [], advertencias: [], sugerencias: [], total: 0 };

    function $(id) { return document.getElementById(id); }

    function stripEmojis(s) {
        if (!s) return '';
        // Quita emojis/iconos del principio ("⚠️ Item 2: ...", "💡 ...", "❌ ...")
        return String(s).replace(/^[\s\u2000-\u206F\u2E00-\u2E7F\\'!"#$%&()*+,\-.\/:;<=>?@\[\]^_`{|}~\u2190-\u21FF\u2600-\u27BF\u2700-\u27BF\uD800-\uDBFF\uDC00-\uDFFF]+/u, '').trim();
    }

    function itemsPayload() {
        var items = (CDI.state && CDI.state.items) || [];
        return items.map(function (it) {
            return {
                pieza: String((it && it.pieza) || '').trim(),
                descripcion: String((it && it.descripcion) || '').trim(),
                origen: String((it && it.origen) || 'XX').trim() || 'XX',
                cantidad: Number((it && it.cantidad) || 0),
                valor_unitario: Number((it && it.valor_unitario) || 0),
                peso_unitario: Number((it && it.peso_unitario) || 0)
            };
        });
    }

    // Lo que la factura traía pero no se pudo leer (MARIA-1c): se avisa hasta
    // que la persona lo completa en la pantalla de revisión.
    var NOMBRES_SIN_LEER = {
        flete: 'el flete',
        seguro: 'el seguro',
        vendedor_pais: 'el país del vendedor'
    };
    function camposSinLeer() {
        var op = (CDI.state && CDI.state.operacion) || {};
        var campos = Array.isArray(op.campos_sin_leer) ? op.campos_sin_leer : [];
        var completados = Array.isArray(op.campos_completados) ? op.campos_completados : [];
        return campos.filter(function (c) {
            return completados.indexOf(c) === -1;
        }).map(function (c) {
            return 'No pudimos leer ' + (NOMBRES_SIN_LEER[c] || c) + ' de la factura: completalo.';
        });
    }
    CDI.camposSinLeer = camposSinLeer;

    // Lo que no se leyó del Excel (MARIA-1b, D17 y D18): filas y otras hojas
    // con datos. Queda en el semáforo hasta que la persona lo descarta.
    function avisosDelExcel() {
        var op = (CDI.state && CDI.state.operacion) || {};
        var descartados = Array.isArray(op.avisos_descartados) ? op.avisos_descartados : [];
        var avisos = [];
        var filas = Array.isArray(op.filas_excel_sin_leer) ? op.filas_excel_sin_leer : [];
        var total = Number(op.filas_excel_sin_leer_total) || filas.length;
        if (total > 0 && descartados.indexOf('filas_excel') === -1) {
            avisos.push({
                clave: 'filas_excel',
                texto: total + ' fila(s) del Excel no se pudieron leer' +
                    (filas.length ? ' (filas ' + filas.join(', ') + ')' : '') +
                    '. Revisalas y cargalas a mano.'
            });
        }
        var hojas = Array.isArray(op.hojas_excel_sin_leer) ? op.hojas_excel_sin_leer : [];
        if (hojas.length && descartados.indexOf('hojas_excel') === -1) {
            avisos.push({
                clave: 'hojas_excel',
                texto: 'El Excel tiene otras hojas con datos que no se leyeron (' +
                    hojas.join(', ') + '). Sólo se lee la primera: si hay productos ahí, cargalos a mano.'
            });
        }
        return avisos;
    }
    CDI.avisosDelExcel = function () {
        return avisosDelExcel().map(function (a) { return a.texto; });
    };
    function descartarAviso(clave) {
        var op = CDI.state && CDI.state.operacion;
        if (!op) return;
        if (!Array.isArray(op.avisos_descartados)) op.avisos_descartados = [];
        if (op.avisos_descartados.indexOf(clave) === -1) op.avisos_descartados.push(clave);
    }

    // La cabecera que el servidor controla antes de generar (MARIA-1b).
    function cabeceraPayload() {
        var op = (CDI.state && CDI.state.operacion) || {};
        return {
            moneda: String(op.moneda || '').trim().toUpperCase(),
            incoterm: String(op.incoterm || '').trim().toUpperCase(),
            comprador_cuit: String(op.comprador_cuit || '').replace(/[-\s]/g, ''),
            flete: op.flete,
            seguro: op.seguro
        };
    }

    var descartables = {};
    function conAvisosLocales(data) {
        var delExcel = avisosDelExcel();
        descartables = {};
        delExcel.forEach(function (a) { descartables[a.texto] = a.clave; });
        var locales = delExcel.map(function (a) { return a.texto; }).concat(camposSinLeer());
        var warns = locales.concat(data.advertencias || []);
        var errs = data.errores || [];
        var tips = data.sugerencias || [];
        return {
            errores: errs, advertencias: warns, sugerencias: tips, resumen: data.resumen,
            total: errs.length + warns.length + tips.length
        };
    }

    // Última respuesta del servidor: los avisos locales se recalculan aunque
    // no se pida una validación nueva (en vuelo, o muy seguido).
    var ultimoServidor = {};
    function refrescarLocales() {
        lastIssues = conAvisosLocales(ultimoServidor);
        if (lastIssues.total) mostrar(lastIssues);
        else { setState('empty', 0); renderPopover(lastIssues); }
    }

    function mostrar(data) {
        var kind = 'ok';
        if (data.errores.length > 0) kind = 'error';
        else if (data.advertencias.length > 0) kind = 'warning';
        setState(kind, data.errores.length + data.advertencias.length);
        renderPopover(data);
    }

    function hasEnoughData(items) {
        if (!items.length) return false;
        // Al menos 1 item con descripcion o pieza para que el backend valide algo util
        return items.some(function (it) { return !!(it.pieza || it.descripcion); });
    }

    function setState(kind, count) {
        if (!fab || !dot || !label) return;
        dot.classList.remove('is-success', 'is-warning', 'is-error');
        if (kind === 'ok') dot.classList.add('is-success');
        else if (kind === 'warning') dot.classList.add('is-warning');
        else if (kind === 'error') dot.classList.add('is-error');

        if (kind === 'empty') {
            label.textContent = 'Validacion';
        } else if (count === 0) {
            label.textContent = 'Todo OK';
        } else if (kind === 'error') {
            label.textContent = count === 1 ? '1 error' : count + ' errores';
        } else {
            label.textContent = count === 1 ? '1 aviso' : count + ' avisos';
        }
        fab.dataset.kind = kind;
    }

    function renderPopover(data) {
        if (!popoverBody) return;
        var errs = data.errores || [];
        var warns = data.advertencias || [];
        var tips = data.sugerencias || [];
        var total = errs.length + warns.length + tips.length;

        if (popoverTitle) {
            if (total === 0) popoverTitle.textContent = 'Sin observaciones';
            else popoverTitle.textContent = total + ' observacion' + (total === 1 ? '' : 'es');
        }

        if (total === 0) {
            popoverBody.innerHTML = '';
            if (popoverEmpty) {
                popoverEmpty.textContent = 'Todo OK. ' + (data.resumen ? stripEmojis(data.resumen) : 'Podes seguir.');
                popoverBody.appendChild(popoverEmpty);
            }
            return;
        }

        var html = [];
        if (errs.length) {
            html.push('<div class="semaforo-section">');
            html.push('<h4 class="semaforo-section-title is-error">Errores (' + errs.length + ')</h4>');
            html.push('<ul class="semaforo-list">');
            errs.forEach(function (msg) {
                html.push('<li class="semaforo-item is-error" data-msg="' + CDI.escapeHtml(msg) + '">' + CDI.escapeHtml(stripEmojis(msg)) + '</li>');
            });
            html.push('</ul></div>');
        }
        if (warns.length) {
            html.push('<div class="semaforo-section">');
            html.push('<h4 class="semaforo-section-title is-warning">Advertencias (' + warns.length + ')</h4>');
            html.push('<ul class="semaforo-list">');
            warns.forEach(function (msg) {
                var clave = descartables[msg];
                html.push('<li class="semaforo-item is-warning" data-msg="' + CDI.escapeHtml(msg) + '">' + CDI.escapeHtml(stripEmojis(msg)) +
                    (clave ? ' <button type="button" class="semaforo-descartar" data-clave="' + CDI.escapeHtml(clave) + '">Descartar</button>' : '') +
                    '</li>');
            });
            html.push('</ul></div>');
        }
        if (tips.length) {
            html.push('<div class="semaforo-section">');
            html.push('<h4 class="semaforo-section-title">Sugerencias (' + tips.length + ')</h4>');
            html.push('<ul class="semaforo-list">');
            tips.forEach(function (msg) {
                html.push('<li class="semaforo-item" data-msg="' + CDI.escapeHtml(msg) + '">' + CDI.escapeHtml(stripEmojis(msg)) + '</li>');
            });
            html.push('</ul></div>');
        }
        popoverBody.innerHTML = html.join('');
    }

    async function runValidation() {
        if (!fab || fab.hidden) return;
        if (inFlight || Date.now() - lastRequestMs < MIN_INTERVAL_MS) {
            refrescarLocales();
            if (!inFlight) scheduleValidation();
            return;
        }
        var now = Date.now();

        var items = itemsPayload();
        if (!hasEnoughData(items)) {
            ultimoServidor = {};
            refrescarLocales();
            return;
        }

        inFlight = true;
        lastRequestMs = now;
        try {
            var resp = await CDI.api('/api/validate/smart', {
                method: 'POST',
                body: JSON.stringify({ items: items, operacion: cabeceraPayload() })
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            ultimoServidor = (!data || data.success === false) ? {} : data;
            refrescarLocales();
        } catch (err) {
            // Fallo silencioso; los avisos locales siguen a la vista.
            ultimoServidor = {};
            refrescarLocales();
        } finally {
            inFlight = false;
        }
    }

    function scheduleValidation() {
        if (!fab || fab.hidden) return;
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(runValidation, DEBOUNCE_MS);
    }

    function showFab() {
        if (!fab) return;
        fab.hidden = false;
        scheduleValidation();
    }

    function hideFab() {
        if (!fab) return;
        fab.hidden = true;
        closePopover();
    }

    function openPopover() {
        if (!popover) return;
        popover.hidden = false;
        popoverOpen = true;
        try { CDI.track && CDI.track('semaforo_opened', { kind: (fab && fab.dataset.kind) || 'empty', issues: lastIssues.total }); } catch (_) {}
    }

    function closePopover() {
        if (!popover) return;
        popover.hidden = true;
        popoverOpen = false;
    }

    function togglePopover() {
        if (popoverOpen) closePopover();
        else openPopover();
    }

    function onItemClick(e) {
        var boton = e.target.closest && e.target.closest('.semaforo-descartar');
        if (boton) {
            // Que no llegue al clic de afuera: al redibujar, el botón ya no
            // está en el semáforo y lo cerraría.
            e.stopPropagation();
            descartarAviso(boton.getAttribute('data-clave'));
            try { CDI.track && CDI.track('semaforo_aviso_descartado', { clave: boton.getAttribute('data-clave') }); } catch (_) {}
            refrescarLocales();
            return;
        }
        var li = e.target.closest && e.target.closest('.semaforo-item');
        if (!li) return;
        var msg = li.getAttribute('data-msg') || '';
        try { CDI.track && CDI.track('semaforo_issue_clicked', { msg: msg.slice(0, 120) }); } catch (_) {}
        // Heuristica: si menciona "Item N", intentamos scrollear al item en la pantalla NCM
        var m = msg.match(/[IÍ]tem\s+(\d+)/i);
        if (m) {
            var idx = parseInt(m[1], 10) - 1;
            var row = document.querySelector('[data-screen="ncm"] tbody tr[data-index="' + idx + '"]');
            if (!row) {
                var rows = document.querySelectorAll('[data-screen="ncm"] tbody tr');
                row = rows[idx];
            }
            if (row) {
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                row.classList.add('row-flash');
                setTimeout(function () { row.classList.remove('row-flash'); }, 1400);
            }
        }
    }

    function handleScreenChange(to) {
        currentScreen = to;
        if (ACTIVE_SCREENS.indexOf(to) !== -1) {
            showFab();
        } else {
            hideFab();
        }
    }

    function init() {
        if (initialized) return;
        fab = $('semaforoFAB');
        dot = $('semaforoDot');
        label = $('semaforoLabel');
        popover = $('semaforoPopover');
        popoverBody = $('semaforoBody');
        popoverTitle = $('semaforoPopoverTitle');
        popoverEmpty = $('semaforoEmpty');
        closeBtn = $('semaforoClose');
        if (!fab || !popover) return;

        setState('empty', 0);

        fab.addEventListener('click', togglePopover);
        fab.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); togglePopover(); }
        });
        if (closeBtn) closeBtn.addEventListener('click', closePopover);
        if (popoverBody) popoverBody.addEventListener('click', onItemClick);

        // Cierra popover al click fuera
        document.addEventListener('click', function (e) {
            if (!popoverOpen) return;
            if (popover.contains(e.target)) return;
            if (fab.contains(e.target)) return;
            closePopover();
        });

        // Trigger de re-validacion: cambios en main (form review, tabla NCM)
        var mainEl = document.querySelector('main.main') || document.body;
        mainEl.addEventListener('input', scheduleValidation);
        mainEl.addEventListener('change', scheduleValidation);

        // Eventos custom del sistema: cambios en NCM, notas, cliente
        ['cdi:ncm-source', 'cdi:ncm-notes-changed', 'cdi:cliente-activo-cambio', 'cdi:nueva-operacion'].forEach(function (evt) {
            document.addEventListener(evt, scheduleValidation);
        });

        // Cambio de pantalla
        document.addEventListener('cdi:screen-leave', function (e) {
            if (!e.detail || !e.detail.to) return;
            handleScreenChange(e.detail.to);
        });

        // Primera pantalla activa al montar
        var active = document.querySelector('.screen.is-active');
        if (active) {
            var s = active.getAttribute('data-screen');
            handleScreenChange(s);
        }

        initialized = true;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    CDI.semaforo = { refresh: scheduleValidation, open: openPopover, close: closePopover };
})();
