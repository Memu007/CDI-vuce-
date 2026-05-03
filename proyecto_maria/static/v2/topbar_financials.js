/* ============================================================
   CDI v2 - Topbar financials: dolar BNA + Blue + estado del sistema
   Consume GET /api/financials (cache backend 5 min) y
   GET /api/system/connectors (cache cliente 60 s).
   Auto-refresh cada 5 min. Falla silenciosa.
   ============================================================ */
(function () {
    'use strict';
    var CDI = window.CDI = window.CDI || {};

    var REFRESH_MS = 5 * 60 * 1000;
    var FETCH_TIMEOUT_MS = 4000;
    var CONNECTORS_TTL_MS = 60 * 1000;

    var container, bnaValue, blueValue;
    var telemetryShown = false;
    var refreshTimer = null;

    // Cache cliente para /api/system/connectors
    var connectorsCache = { data: null, fetchedAt: 0, inflight: null };
    // Estado UI del popover
    var popoverEl = null;
    var popoverOpen = false;
    var demoBadgeShownTracked = false;

    function $(id) { return document.getElementById(id); }

    function fmt(value) {
        var n = Number(value);
        if (!isFinite(n) || n <= 0) return '—';
        // Entero si es grande, un decimal si es chico
        return n >= 100 ? Math.round(n).toLocaleString('es-AR') : n.toFixed(1);
    }

    function escapeHtml(s) {
        if (CDI.escapeHtml) return CDI.escapeHtml(s);
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function track(name, props) {
        try { if (CDI.track) CDI.track(name, props || {}); } catch (_) {}
    }

    async function fetchFinancials() {
        if (!container) return;
        var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        var timeoutId = controller ? setTimeout(function () { controller.abort(); }, FETCH_TIMEOUT_MS) : null;
        try {
            var resp = await fetch('/api/financials', {
                credentials: 'same-origin',
                signal: controller ? controller.signal : undefined
            });
            if (timeoutId) clearTimeout(timeoutId);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();

            if (bnaValue && data.dolar_bna) bnaValue.textContent = '$' + fmt(data.dolar_bna.venta);
            if (blueValue && data.dolar_blue) blueValue.textContent = '$' + fmt(data.dolar_blue.venta);
            container.hidden = false;

            if (!telemetryShown) {
                telemetryShown = true;
                track('topbar_financials_shown');
            }
        } catch (err) {
            if (timeoutId) clearTimeout(timeoutId);
            if (bnaValue && bnaValue.textContent === '—') bnaValue.textContent = '—';
            if (blueValue && blueValue.textContent === '—') blueValue.textContent = '—';
            // Mostramos igualmente el contenedor (asi el usuario ve que existe el widget)
            container.hidden = false;
        }
    }

    async function fetchConnectors(force) {
        var now = Date.now();
        if (!force && connectorsCache.data && (now - connectorsCache.fetchedAt) < CONNECTORS_TTL_MS) {
            return connectorsCache.data;
        }
        if (connectorsCache.inflight) return connectorsCache.inflight;

        var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        var timeoutId = controller ? setTimeout(function () { controller.abort(); }, FETCH_TIMEOUT_MS) : null;

        var p = (async function () {
            try {
                var resp = await CDI.api('/api/system/connectors', {
                    signal: controller ? controller.signal : undefined
                });
                if (timeoutId) clearTimeout(timeoutId);
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                var data = await resp.json();
                connectorsCache.data = data;
                connectorsCache.fetchedAt = Date.now();
                return data;
            } catch (err) {
                if (timeoutId) clearTimeout(timeoutId);
                return null;
            } finally {
                connectorsCache.inflight = null;
            }
        })();
        connectorsCache.inflight = p;
        return p;
    }

    // Determina si un conector esta "real" (api o scrape) o "fake"/offline.
    function connectorIsReal(mode) {
        var m = String(mode || '').toLowerCase();
        return m === 'api' || m === 'scrape';
    }

    function summarizeConnectors(data) {
        if (!data) return { overall: 'unknown', items: [], hasFake: false };
        var items = [
            { key: 'vuce', label: 'VUCE', mode: (data.vuce && data.vuce.mode) || 'fake' },
            { key: 'tarifar', label: 'Tarifar', mode: (data.tarifar && data.tarifar.mode) || 'fake' },
            { key: 'afip', label: 'AFIP', mode: (data.afip && data.afip.mode) || 'fake' },
            { key: 'ncm_scraper', label: 'NCM scraper', mode: 'scrape' }
        ];
        var hasFake = items.some(function (it) { return !connectorIsReal(it.mode); });
        var overall = hasFake ? 'demo' : 'real';
        return { overall: overall, items: items, hasFake: hasFake };
    }

    function renderStatusChip(summary) {
        var chip = $('tfSystemChip');
        var dot = $('tfSystemDot');
        var label = $('tfSystemLabel');
        var badge = $('tfDemoBadge');
        if (!chip || !dot || !label) return;

        dot.classList.remove('is-success', 'is-warning', 'is-error');
        if (summary.overall === 'real') {
            dot.classList.add('is-success');
            chip.setAttribute('title', 'Todos los conectores en modo real');
            label.textContent = 'Sistema';
        } else if (summary.overall === 'demo') {
            dot.classList.add('is-warning');
            chip.setAttribute('title', 'Uno o mas conectores en modo demo/fake');
            label.textContent = 'Sistema';
        } else {
            dot.classList.add('is-error');
            chip.setAttribute('title', 'No se pudo obtener el estado del sistema');
            label.textContent = 'Sistema';
        }

        if (badge) {
            if (summary.hasFake) {
                badge.hidden = false;
                if (!demoBadgeShownTracked) {
                    demoBadgeShownTracked = true;
                    track('topbar_demo_badge_shown', { items: summary.items.map(function (it) { return it.key + ':' + it.mode; }) });
                }
            } else {
                badge.hidden = true;
            }
        }
    }

    function modeBadge(mode) {
        var m = String(mode || '').toLowerCase();
        var cls = connectorIsReal(m) ? 'is-success' : 'is-warning';
        var label;
        if (m === 'api') label = 'API real';
        else if (m === 'scrape') label = 'Scrape';
        else if (m === 'fake') label = 'Demo';
        else label = m || '—';
        return '<span class="tf-mode-badge ' + cls + '">' + escapeHtml(label) + '</span>';
    }

    function renderPopoverBody(summary) {
        if (!summary || !summary.items || !summary.items.length) {
            return '<div class="tf-pop-empty">No se pudo leer el estado del sistema.</div>';
        }
        var rows = summary.items.map(function (it) {
            return '<div class="tf-pop-row">' +
                '<span class="tf-pop-label">' + escapeHtml(it.label) + '</span>' +
                modeBadge(it.mode) +
                '</div>';
        }).join('');
        var note = summary.hasFake
            ? '<div class="tf-pop-note">Los conectores en modo <b>Demo</b> devuelven datos simulados, no reales. Cambia a <code>api</code>/<code>scrape</code> en las variables de entorno para produccion.</div>'
            : '<div class="tf-pop-note tf-pop-note-ok">Todos los conectores externos estan operando con fuentes reales.</div>';
        return rows + note;
    }

    function closePopover() {
        if (!popoverEl) return;
        popoverEl.hidden = true;
        popoverOpen = false;
        var chip = $('tfSystemChip');
        if (chip) chip.setAttribute('aria-expanded', 'false');
        document.removeEventListener('click', onDocClick, true);
        document.removeEventListener('keydown', onDocKey, true);
    }

    function onDocClick(ev) {
        if (!popoverEl) return;
        if (popoverEl.contains(ev.target)) return;
        var chip = $('tfSystemChip');
        if (chip && chip.contains(ev.target)) return;
        closePopover();
    }
    function onDocKey(ev) {
        if (ev.key === 'Escape') closePopover();
    }

    async function openPopover() {
        var chip = $('tfSystemChip');
        popoverEl = $('tfSystemPopover');
        if (!chip || !popoverEl) return;
        popoverOpen = true;
        chip.setAttribute('aria-expanded', 'true');
        popoverEl.hidden = false;
        popoverEl.innerHTML = '<div class="tf-pop-loading">Cargando…</div>';
        track('topbar_status_opened');
        var data = await fetchConnectors(false);
        var summary = summarizeConnectors(data);
        popoverEl.innerHTML = renderPopoverBody(summary);
        // Listeners para cerrar
        setTimeout(function () {
            document.addEventListener('click', onDocClick, true);
            document.addEventListener('keydown', onDocKey, true);
        }, 0);
    }

    function onChipClick() {
        if (popoverOpen) closePopover();
        else openPopover();
    }

    async function refreshConnectorsStatus() {
        var data = await fetchConnectors(true);
        var summary = summarizeConnectors(data);
        renderStatusChip(summary);
    }

    async function fetchOnce() {
        await fetchFinancials();
        await refreshConnectorsStatus();
    }

    function init() {
        container = $('topbarFinancials');
        bnaValue = $('tfBnaValue');
        blueValue = $('tfBlueValue');
        if (!container) return;

        var chip = $('tfSystemChip');
        if (chip) chip.addEventListener('click', onChipClick);

        fetchOnce();
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(fetchOnce, REFRESH_MS);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    CDI.refreshFinancials = fetchOnce;
    CDI.refreshSystemStatus = refreshConnectorsStatus;
})();
