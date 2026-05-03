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
        } else if (count === 1) {
            label.textContent = '1 aviso';
        } else {
            label.textContent = count + ' avisos';
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
                html.push('<li class="semaforo-item is-warning" data-msg="' + CDI.escapeHtml(msg) + '">' + CDI.escapeHtml(stripEmojis(msg)) + '</li>');
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
        if (inFlight) return;
        var now = Date.now();
        if (now - lastRequestMs < MIN_INTERVAL_MS) return;

        var items = itemsPayload();
        if (!hasEnoughData(items)) {
            setState('empty', 0);
            lastIssues = { errores: [], advertencias: [], sugerencias: [], total: 0 };
            renderPopover(lastIssues);
            return;
        }

        inFlight = true;
        lastRequestMs = now;
        try {
            var resp = await CDI.api('/api/validate/smart', {
                method: 'POST',
                body: JSON.stringify({ items: items })
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            if (!data || data.success === false) {
                setState('empty', 0);
                return;
            }
            var errs = data.errores || [];
            var warns = data.advertencias || [];
            var tips = data.sugerencias || [];
            lastIssues = {
                errores: errs,
                advertencias: warns,
                sugerencias: tips,
                resumen: data.resumen,
                total: errs.length + warns.length + tips.length
            };

            var kind = 'ok';
            if (errs.length > 0) kind = 'error';
            else if (warns.length > 0) kind = 'warning';

            var visibleCount = errs.length + warns.length;
            setState(kind, visibleCount);
            renderPopover(lastIssues);
        } catch (err) {
            // Fallo silencioso; mantenemos el ultimo estado.
            setState('empty', 0);
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
