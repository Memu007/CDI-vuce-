/* ============================================================
   CDI v2 — Enrich masivo de alícuotas
   Drawer lateral activado desde pantalla NCM. Llama a
   POST /api/ncm/enrich-items y muestra un resumen:
     - Alícuota promedio ponderada por FOB
     - Ítems con licencias requeridas (alerta)
     - Fuentes de datos (oficial/mercado/muestra)
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    let drawer, overlay, closeBtn, subtitle, bodyEl, loadingEl, resultEl;
    let trigger;
    let initialized = false;

    function $(id) { return document.getElementById(id); }

    function init() {
        if (initialized) return;
        drawer   = $('enrichDrawer');
        overlay  = $('enrichOverlay');
        closeBtn = $('enrichClose');
        subtitle = $('enrichSubtitle');
        bodyEl   = $('enrichBody');
        loadingEl = $('enrichLoading');
        resultEl = $('enrichResult');
        trigger  = $('ncmEnrichAllBtn');
        if (!drawer) return;

        closeBtn.addEventListener('click', close);
        overlay.addEventListener('click', close);
        if (trigger) trigger.addEventListener('click', runFromNcmScreen);

        document.addEventListener('keydown', (ev) => {
            if (ev.key !== 'Escape') return;
            if (!drawer.classList.contains('is-open')) return;
            close();
        });
        document.addEventListener('cdi:screen-leave', close);

        initialized = true;
    }

    function open() {
        init();
        if (!drawer) return;
        drawer.hidden = false;
        overlay.hidden = false;
        requestAnimationFrame(() => {
            drawer.classList.add('is-open');
            overlay.classList.add('is-visible');
        });
    }

    function close() {
        if (!drawer) return;
        drawer.classList.remove('is-open');
        overlay.classList.remove('is-visible');
        setTimeout(() => {
            if (!drawer.classList.contains('is-open')) {
                drawer.hidden = true;
                overlay.hidden = true;
            }
        }, 240);
    }

    function showLoading(flag) {
        if (loadingEl) loadingEl.hidden = !flag;
        if (resultEl) resultEl.hidden = flag;
    }

    async function runFromNcmScreen() {
        const items = (CDI.state && CDI.state.items) || [];
        const valid = items.filter(it => {
            const raw = String(it.pieza || it.ncm || '').replace(/\D/g, '');
            return raw.length >= 6;
        });
        if (!valid.length) {
            if (CDI.toast) CDI.toast.info('Todavía no hay ítems con NCM asignado.');
            return;
        }

        open();
        if (subtitle) subtitle.textContent = 'Consultando ' + valid.length + (valid.length === 1 ? ' ítem…' : ' ítems…');
        showLoading(true);
        if (resultEl) resultEl.innerHTML = '';

        try {
            const res = await CDI.api('/api/ncm/enrich-items', {
                method: 'POST',
                body: JSON.stringify({ items: valid }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || 'No se pudo enriquecer');
            renderResult(data, valid);
            CDI.track && CDI.track('ncm_enrich_all', {
                items: valid.length,
                ncms: data.ncms_consultados || 0,
                warnings: (data.licencias_warnings || []).length,
            });
            if ((data.licencias_warnings || []).length) {
                CDI.track && CDI.track('ncm_licencias_alert_shown', {
                    count: data.licencias_warnings.length,
                });
            }
        } catch (err) {
            if (resultEl) {
                resultEl.innerHTML = '<p class="caption" style="color:#c0392b;">' +
                    CDI.escapeHtml(String(err.message || err)) + '</p>';
            }
        } finally {
            showLoading(false);
        }
    }

    function renderResult(data, originalItems) {
        if (!resultEl) return;
        const enriched = Array.isArray(data.enriched) ? data.enriched : [];
        const warnings = Array.isArray(data.licencias_warnings) ? data.licencias_warnings : [];
        const summary = data.alicuotas_summary || {};

        // Promedio ponderado de alícuota (arancel extrazona) por FOB
        let fobTotal = 0;
        let aranceladoFob = 0;
        enriched.forEach(it => {
            const fob = (Number(it.valor_unitario) || 0) * (Number(it.cantidad) || 1);
            const alic = (it.vuce && it.vuce.alicuotas && it.vuce.alicuotas.arancel_extrazona) || 0;
            fobTotal += fob;
            aranceladoFob += fob * (Number(alic) / 100);
        });
        const alicuotaPromedio = fobTotal > 0 ? (aranceladoFob / fobTotal * 100) : 0;

        // Agrupar por NCM para contar items afectados por licencias
        const warnByNcm = {};
        warnings.forEach(w => {
            const k = w.ncm;
            if (!warnByNcm[k]) warnByNcm[k] = [];
            warnByNcm[k].push(w);
        });

        const fakeCount = enriched.filter(it =>
            it.vuce && it.vuce.modo_fake !== false
        ).length;

        const kpiHtml = (
            '<div class="enrich-kpis">' +
                '<div class="enrich-kpi">' +
                    '<span class="caption">Alícuota promedio</span>' +
                    '<span class="enrich-kpi-value">' + alicuotaPromedio.toFixed(1) + '%</span>' +
                '</div>' +
                '<div class="enrich-kpi">' +
                    '<span class="caption">FOB total</span>' +
                    '<span class="enrich-kpi-value">$' + Math.round(fobTotal).toLocaleString('en-US') + '</span>' +
                '</div>' +
                '<div class="enrich-kpi">' +
                    '<span class="caption">NCMs distintos</span>' +
                    '<span class="enrich-kpi-value">' + Object.keys(summary).length + '</span>' +
                '</div>' +
            '</div>'
        );

        const warnHtml = warnings.length
            ? '<div class="enrich-section">' +
                '<h4 class="enrich-section-title enrich-warning-title">' +
                    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' +
                    'Licencias requeridas (' + warnings.length + ')' +
                '</h4>' +
                '<ul class="enrich-warning-list">' +
                    warnings.slice(0, 10).map(w => (
                        '<li>' +
                            '<strong>NCM ' + CDI.escapeHtml(CDI.formatNcm ? CDI.formatNcm(w.ncm) : w.ncm) + '</strong> · ' +
                            '<span class="caption">' + CDI.escapeHtml(w.organismo || '') +
                            (w.descripcion ? ' — ' + CDI.escapeHtml(w.descripcion) : '') +
                            '</span>' +
                        '</li>'
                    )).join('') +
                '</ul>' +
              '</div>'
            : '<p class="caption enrich-ok">Ningún ítem requiere licencia especial.</p>';

        const itemsRows = enriched.map((it, i) => {
            const ncmRaw = String(it.pieza || it.ncm || '').replace(/\D/g, '');
            const ncmFmt = CDI.formatNcm ? CDI.formatNcm(ncmRaw) : ncmRaw;
            const alic = (it.vuce && it.vuce.alicuotas && it.vuce.alicuotas.arancel_extrazona);
            const iva = (it.vuce && it.vuce.alicuotas && it.vuce.alicuotas.iva);
            const tieneLic = !!(it.vuce && it.vuce.licencias && it.vuce.licencias.some(l => l.requerida));
            const fake = it.vuce && it.vuce.modo_fake !== false;
            const chip = fake
                ? '<span class="source-chip is-sample" title="Valor simulado">Muestra</span>'
                : '<span class="source-chip is-market" title="Dato externo">Mercado</span>';
            return (
                '<tr' + (tieneLic ? ' class="has-warning"' : '') + '>' +
                    '<td>' + (i + 1) + '</td>' +
                    '<td>' + CDI.escapeHtml(ncmFmt) + (tieneLic ? ' <span class="calc-badge" style="background:#fff2d9;color:#a05a00;">LIC</span>' : '') + '</td>' +
                    '<td class="enrich-num">' + (alic != null ? alic.toFixed(1) + '%' : '—') + '</td>' +
                    '<td class="enrich-num">' + (iva != null ? iva.toFixed(1) + '%' : '—') + '</td>' +
                    '<td>' + chip + '</td>' +
                '</tr>'
            );
        }).join('');

        const tableHtml = (
            '<div class="enrich-section">' +
                '<h4 class="enrich-section-title">Detalle por ítem</h4>' +
                '<table class="calc-table enrich-table">' +
                    '<thead><tr><th>#</th><th>NCM</th><th class="enrich-num">DI</th><th class="enrich-num">IVA</th><th>Fuente</th></tr></thead>' +
                    '<tbody>' + itemsRows + '</tbody>' +
                '</table>' +
            '</div>'
        );

        const fakeNote = fakeCount > 0
            ? '<p class="caption enrich-fake-note">' + fakeCount + ' ítem(s) con datos de muestra. ' +
                'Forzá un refresh con el botón "Datos de muestra" en el banner superior.</p>'
            : '';

        if (subtitle) {
            subtitle.textContent = enriched.length + ' ítem(s) · ' + Object.keys(summary).length + ' NCM(s)';
        }
        resultEl.innerHTML = kpiHtml + warnHtml + tableHtml + fakeNote;
    }

    CDI.openEnrichDrawer = open;
    CDI.closeEnrichDrawer = close;

    document.addEventListener('DOMContentLoaded', init);
})();
