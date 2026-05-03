/* ============================================================
   CDI v2 — Calculadora de tributos
   Overlay modal accesible desde la pantalla NCM. Permite estimar
   DI/IVA/tasa estadística/costo total sin generar el TXT.
   Backend: POST /api/ncm/calcular (tarifar_connector).

   Expone:
     CDI.openCalculadora(prefill)
     CDI.closeCalculadora()
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    let modal, overlay, closeBtn, resetBtn, runBtn;
    let inNcm, inFob, inCant, inPeso, inOrigen, errorEl, resultEl;
    let trigger;   // boton en pantalla NCM
    let initialized = false;

    function $(id) { return document.getElementById(id); }

    function init() {
        if (initialized) return;
        modal    = $('calcModal');
        overlay  = $('calcOverlay');
        closeBtn = $('calcClose');
        resetBtn = $('calcReset');
        runBtn   = $('calcRun');
        inNcm    = $('calcNcm');
        inFob    = $('calcFob');
        inCant   = $('calcCantidad');
        inPeso   = $('calcPeso');
        inOrigen = $('calcOrigen');
        errorEl  = $('calcError');
        resultEl = $('calcResult');
        trigger  = $('ncmCalcBtn');
        if (!modal) return;

        closeBtn.addEventListener('click', close);
        overlay.addEventListener('click', close);
        resetBtn.addEventListener('click', reset);
        runBtn.addEventListener('click', run);
        if (trigger) trigger.addEventListener('click', () => openFromNcmScreen());

        // Mascara de NCM en input
        if (inNcm && CDI.maskNcm) {
            inNcm.addEventListener('input', () => {
                const pos = inNcm.selectionStart;
                const masked = CDI.maskNcm(inNcm.value);
                if (masked !== inNcm.value) inNcm.value = masked;
                try { inNcm.setSelectionRange(pos, pos); } catch (_) {}
            });
        }

        // Enter en cualquier input dispara calcular (salvo select)
        [inNcm, inFob, inCant, inPeso].forEach(el => {
            if (!el) return;
            el.addEventListener('keydown', (ev) => {
                if (ev.key === 'Enter') { ev.preventDefault(); run(); }
            });
        });

        document.addEventListener('keydown', (ev) => {
            if (ev.key !== 'Escape') return;
            if (!modal.classList.contains('is-open')) return;
            close();
        });

        initialized = true;
    }

    function openFromNcmScreen() {
        // Prefill con el primer item que tenga NCM + valor_unitario, si hay
        const items = (CDI.state && CDI.state.items) || [];
        const first = items.find(it => (it.pieza || it.ncm) && Number(it.valor_unitario) > 0)
            || items.find(it => (it.pieza || it.ncm))
            || null;
        open(first ? {
            ncm: first.pieza || first.ncm,
            valor_fob: first.valor_unitario,
            cantidad: first.cantidad,
            peso_unitario: first.peso_unitario,
            origen: first.origen,
        } : {});
    }

    function open(prefill) {
        init();
        if (!modal) return;
        clearError();
        if (resultEl) { resultEl.hidden = true; resultEl.innerHTML = ''; }
        modal.hidden = false;
        overlay.hidden = false;
        requestAnimationFrame(() => {
            modal.classList.add('is-open');
            overlay.classList.add('is-visible');
        });
        if (prefill) applyPrefill(prefill);
        setTimeout(() => { if (inFob) inFob.focus(); }, 150);
        CDI.track && CDI.track('calc_opened', {
            prefill: !!prefill && !!(prefill.ncm || prefill.valor_fob),
        });
    }

    function applyPrefill(p) {
        if (p.ncm && inNcm) {
            inNcm.value = CDI.formatNcm ? CDI.formatNcm(p.ncm) : p.ncm;
        }
        if (p.valor_fob != null && inFob) inFob.value = Number(p.valor_fob) || '';
        if (p.cantidad != null && inCant) inCant.value = Number(p.cantidad) || 1;
        if (p.peso_unitario != null && inPeso) inPeso.value = Number(p.peso_unitario) || 1;
        if (p.origen && inOrigen) {
            const val = String(p.origen).toUpperCase();
            const match = Array.from(inOrigen.options).find(o => o.value === val);
            if (match) inOrigen.value = val;
        }
    }

    function close() {
        if (!modal) return;
        modal.classList.remove('is-open');
        overlay.classList.remove('is-visible');
        setTimeout(() => {
            if (!modal.classList.contains('is-open')) {
                modal.hidden = true;
                overlay.hidden = true;
            }
        }, 240);
    }

    function reset() {
        if (inNcm)   inNcm.value = '';
        if (inFob)   inFob.value = '';
        if (inCant)  inCant.value = 1;
        if (inPeso)  inPeso.value = 1;
        if (inOrigen) inOrigen.value = 'CN';
        clearError();
        if (resultEl) { resultEl.hidden = true; resultEl.innerHTML = ''; }
    }

    function clearError() {
        if (!errorEl) return;
        errorEl.hidden = true;
        errorEl.textContent = '';
    }
    function showError(msg) {
        if (!errorEl) return;
        errorEl.hidden = false;
        errorEl.textContent = msg;
    }

    async function run() {
        clearError();
        const ncmClean = (inNcm.value || '').replace(/\D/g, '');
        const fob = parseFloat(inFob.value);
        const cant = parseFloat(inCant.value);
        const peso = parseFloat(inPeso.value);
        const origen = (inOrigen.value || 'CN').trim().toUpperCase();

        if (ncmClean.length < 6) { showError('NCM debe tener al menos 6 dígitos.'); inNcm.focus(); return; }
        if (!(fob > 0)) { showError('Valor FOB debe ser mayor a 0.'); inFob.focus(); return; }
        if (!(cant > 0)) { showError('Cantidad debe ser mayor a 0.'); inCant.focus(); return; }
        if (!(peso > 0)) { showError('Peso unitario debe ser mayor a 0.'); inPeso.focus(); return; }

        runBtn.disabled = true;
        runBtn.textContent = 'Calculando…';
        try {
            const res = await CDI.api('/api/ncm/calcular', {
                method: 'POST',
                body: JSON.stringify({
                    ncm: ncmClean,
                    valor_fob: fob,
                    cantidad: cant,
                    peso_unitario: peso,
                    origen: origen,
                    simular_origenes: true,
                }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || 'No se pudo calcular');
            renderResult(data);
            CDI.track && CDI.track('calc_computed', {
                ncm: ncmClean, origen, fob, cantidad: cant,
            });
        } catch (err) {
            showError(String(err.message || err));
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = 'Calcular tributos';
        }
    }

    /* ==========================================================
       Render de resultado
       ========================================================== */
    function fmtUsd(v) {
        const n = Number(v) || 0;
        return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function renderResult(data) {
        if (!resultEl) return;
        resultEl.hidden = false;
        const calc = data && data.calculo;
        const itemCalc = calc && calc.items && calc.items[0] && calc.items[0].calculo;
        if (!itemCalc) {
            resultEl.innerHTML = '<p class="caption">Sin resultado disponible.</p>';
            return;
        }

        const aranceles = itemCalc.aranceles || {};
        const impuestos = itemCalc.impuestos || {};
        const tasas = itemCalc.tasas || {};

        function rows(obj, clazz) {
            const keys = Object.keys(obj || {}).filter(k => Number(obj[k]) > 0);
            if (!keys.length) return '';
            return keys.map(k => (
                '<tr><td class="calc-row-label">' + CDI.escapeHtml(labelize(k)) + '</td>' +
                '<td class="calc-row-value ' + (clazz || '') + '">' + fmtUsd(obj[k]) + '</td></tr>'
            )).join('');
        }

        const sim = data.simulacion_origenes;
        const simRows = (sim && sim.simulaciones) ? Object.keys(sim.simulaciones).sort((a, b) =>
            sim.simulaciones[a].costo_total - sim.simulaciones[b].costo_total
        ).map(code => {
            const s = sim.simulaciones[code];
            const mercosur = s.es_mercosur ? ' <span class="calc-badge is-mercosur">Mercosur</span>' : '';
            return (
                '<tr>' +
                    '<td>#' + s.ranking + '</td>' +
                    '<td>' + CDI.escapeHtml(s.pais) + ' <span class="caption">' + CDI.escapeHtml(code) + '</span>' + mercosur + '</td>' +
                    '<td class="calc-row-value">' + fmtUsd(s.costo_total) + '</td>' +
                '</tr>'
            );
        }).join('') : '';

        const rec = sim && sim.recomendacion;
        const ahorro = rec && rec.ahorro_vs_china > 0
            ? '<p class="caption calc-hint">Pasando de China a ' + CDI.escapeHtml(rec.pais) +
              ' ahorrás ' + fmtUsd(rec.ahorro_vs_china) + ' por operación.</p>'
            : '';

        const mode = (calc.metadata && calc.metadata.source) || 'desconocido';
        let modeChip;
        if (mode === 'tarifar_fake' || mode === 'fake' || mode === 'desconocido') {
            modeChip = '<span class="source-chip is-sample" title="Valores simulados">Muestra</span>';
        } else if (mode.indexOf('api') !== -1 || mode === 'oficial') {
            modeChip = '<span class="source-chip is-official" title="Datos oficiales VUCE">Oficial</span>';
        } else if (mode === 'tarifar_scrape_partial') {
            modeChip = '<span class="source-chip is-market" title="Parte de los ítems usa datos reales; otros fallaron a muestra">Mercado parcial</span>';
        } else {
            modeChip = '<span class="source-chip is-market" title="Datos reales de mercado (scraping público)">Mercado</span>';
        }

        // Banner "datos con latencia" cuando el backend reporta cache viejo.
        let staleBanner = '';
        const meta = calc.metadata || {};
        if (meta.cache_hit && mode.indexOf('fake') === -1) {
            const ageH = Number(meta.cache_age_hours);
            const threshold = String(mode).indexOf('scrape') !== -1 ? 24 : 72;
            if (isFinite(ageH) && ageH >= threshold) {
                const human = ageH < 24
                    ? Math.round(ageH) + ' h'
                    : Math.round(ageH / 24) + ' día' + (ageH >= 48 ? 's' : '');
                staleBanner = '<div class="calc-stale-banner">⏱ Datos con latencia de ' + CDI.escapeHtml(human) + '</div>';
            }
        }

        resultEl.innerHTML = (
            '<div class="calc-result-head">' +
                '<div><span class="caption">Costo final estimado</span>' +
                    '<div class="calc-total">' + fmtUsd(itemCalc.costo_total) + '</div>' +
                '</div>' +
                modeChip +
            '</div>' +
            staleBanner +
            '<div class="calc-breakdown">' +
                '<table class="calc-table">' +
                    '<thead><tr><th>Componente</th><th>Valor</th></tr></thead>' +
                    '<tbody>' +
                        '<tr class="calc-row-subtotal"><td>Valor FOB total</td>' +
                        '<td class="calc-row-value">' + fmtUsd(itemCalc.valor_total_fob) + '</td></tr>' +
                        rows(aranceles, '') +
                        rows(impuestos, '') +
                        rows(tasas, '') +
                        '<tr class="calc-row-total"><td>Costo total (CIF + tributos)</td>' +
                        '<td class="calc-row-value">' + fmtUsd(itemCalc.costo_total) + '</td></tr>' +
                    '</tbody>' +
                '</table>' +
            '</div>' +
            (simRows
                ? '<h4 class="calc-section-title">Comparativa por origen</h4>' +
                  '<table class="calc-table calc-origins">' +
                      '<thead><tr><th>#</th><th>País</th><th>Costo total</th></tr></thead>' +
                      '<tbody>' + simRows + '</tbody>' +
                  '</table>' +
                  ahorro
                : '')
        );
    }

    function labelize(key) {
        return String(key || '').replace(/_/g, ' ')
            .replace(/\barancel\b/i, 'Arancel')
            .replace(/\biva\b/i, 'IVA')
            .replace(/\biibb\b/i, 'IIBB')
            .replace(/\bextrazona\b/i, 'extrazona')
            .replace(/\bestadistica\b/i, 'estadística');
    }

    CDI.openCalculadora = open;
    CDI.closeCalculadora = close;

    document.addEventListener('DOMContentLoaded', init);
})();
