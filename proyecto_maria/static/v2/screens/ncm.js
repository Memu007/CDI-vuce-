/* ============================================================
   CDI v2 — Screen 3: asignar NCM
   Tabla de items, col NCM editable inline, overlay Spotlight
   con sugerencias desde /api/ncm/sugerir, persistencia con
   /api/ncm/guardar-uso.
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    let tbody, summaryEl, continueBtn;
    let overlay, spotSearch, spotResults, spotItemRef, spotItemDesc, spotProgress;
    let spotVuce;
    let initialized = false;

    // Batch selection / acciones en lote
    const selectedRows = new Set();
    const expandedGroups = new Set();
    let batchBar, batchCount, batchFactor, batchApplyQty, batchNcm, batchDc, batchApplyNcm, batchOrigin, batchApplyOrigin, batchClear, batchAgrupar, selectAllBox;
    let lastSnapshot = null;   // { items: [...], label: 'x2 a 3 items', ts: ms }
    let undoTimer = null;

    // Estado spotlight
    let spotActiveIdx = -1;            // indice del item (fila) que estamos resolviendo
    let spotSuggestions = [];          // [{ncm, desc, source, count?}]
    let spotSelectedSugIdx = 0;        // cursor en la lista
    let spotSearchDebounce = null;
    let spotLastQuery = '';

    // Cache VUCE y debounce del preview en el spotlight
    const vuceCache = new Map();       // ncm -> data
    let vuceDebounce = null;
    let vuceLastNcm = '';

    function $(id) { return document.getElementById(id); }

    function getCountryCatalog() {
        return CDI.paisesMaria || null;
    }

    function getOriginCode(value) {
        const catalog = getCountryCatalog();
        return catalog ? catalog.resolve(value) : '';
    }

    function getOriginLabel(value) {
        const catalog = getCountryCatalog();
        return catalog ? (catalog.label(value) || String(value || '').trim()) : String(value || '').trim();
    }

    function splitSimPosition(value) {
        const raw = String(value || '').trim();
        const letterMatch = raw.match(/([A-Za-z])\s*$/);
        return {
            digits: raw.replace(/\D/g, '').slice(0, 11),
            dc: letterMatch ? letterMatch[1].toUpperCase() : ''
        };
    }

    function buildSimPosition(digits, dc) {
        const cleanDigits = String(digits || '').replace(/\D/g, '').slice(0, 11);
        const cleanDc = String(dc || '').replace(/[^A-Za-z]/g, '').slice(0, 1).toUpperCase();
        const formatted = CDI.formatNcm ? CDI.formatNcm(cleanDigits) : cleanDigits;
        return formatted + (cleanDc ? ' ' + cleanDc : '');
    }

    function simErrorDetail(value) {
        const parts = splitSimPosition(value);
        if (parts.digits.length === 8) {
            return 'La NCM está identificada, pero faltan los 3 dígitos SIM y la letra de control (DC).';
        }
        if (parts.digits.length < 11) {
            return 'La posición SIM debe tener 11 dígitos: NCM (8) + detalle SIM (3).';
        }
        if (!parts.dc) {
            return 'Falta la letra de control. Completala en el campo DC.';
        }
        return 'Usá 11 dígitos y una única letra de control (DC). Ejemplo: 8471.30.00.900 · R.';
    }

    function ensureCountryDatalist() {
        const catalog = getCountryCatalog();
        if (!catalog || document.getElementById('ncmCountries')) return;
        const list = document.createElement('datalist');
        list.id = 'ncmCountries';
        list.innerHTML = catalog.optionMarkup();
        document.body.appendChild(list);
    }

    function init() {
        if (initialized) return;
        tbody = $('ncmTbody');
        summaryEl = $('ncmSummary');
        continueBtn = $('ncmContinueBtn');
        overlay = $('ncmOverlay');
        spotSearch = $('spotSearch');
        spotResults = $('spotResults');
        spotItemRef = $('spotItemRef');
        spotItemDesc = $('spotItemDesc');
        spotProgress = $('spotProgress');
        spotVuce = $('spotVuce');
        const ncmAddRowBtn = $('ncmAddRowBtn');
        if (!tbody) return;
        ensureCountryDatalist();

        if (ncmAddRowBtn) {
            ncmAddRowBtn.addEventListener('click', () => {
                if (!CDI.state) CDI.state = {};
                if (!CDI.state.items) CDI.state.items = [];
                // Invalidamos deshacer antes de agregar fila
                lastSnapshot = null;
                CDI.state.items.push({
                    pieza: '',
                    cantidad: 1,
                    valor_unitario: 0,
                    descripcion: ''
                });
                render();
                updateBatchBar();
                try { CDI.track && CDI.track('ncm_row_added_manually'); } catch (_) {}
            });
        }

        continueBtn.addEventListener('click', onContinue);

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeSpotlight();
        });
        spotSearch.addEventListener('input', onSpotInput);
        spotSearch.addEventListener('keydown', onSpotKeydown);
        spotResults.addEventListener('click', onSpotResultClick);
        if (spotVuce) spotVuce.addEventListener('click', onVuceSimClick);

        // Keyboard global: ESC cierra overlay
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !overlay.hidden) {
                e.preventDefault();
                closeSpotlight();
            }
        });

        // Refrescar pills cuando cambian las notas
        document.addEventListener('cdi:ncm-notes-changed', () => {
            refreshAllPills();
        });

        // ---------- Batch actions ----------
        batchBar = $('ncmBatchBar');
        batchCount = $('ncmBatchCount');
        batchFactor = $('ncmBatchFactor');
        batchApplyQty = $('ncmBatchApplyQty');
        batchNcm = $('ncmBatchNcm');
        batchDc = $('ncmBatchDc');
        batchApplyNcm = $('ncmBatchApplyNcm');
        batchOrigin = $('ncmBatchOrigin');
        batchApplyOrigin = $('ncmBatchApplyOrigin');
        batchClear = $('ncmBatchClear');
        batchAgrupar = $('ncmBatchAgrupar');
        selectAllBox = $('ncmSelectAll');

        if (batchNcm && CDI.maskNcm) CDI.maskNcm(batchNcm);
        if (batchNcm) batchNcm.addEventListener('input', onBatchSimInput);
        if (batchDc) batchDc.addEventListener('input', onBatchDcInput);

        if (selectAllBox) {
            selectAllBox.addEventListener('change', (e) => onSelectAll(e.target.checked));
        }
        if (tbody) {
            tbody.addEventListener('change', (e) => {
                const cb = e.target && e.target.matches && e.target.matches('[data-row-check]');
                if (!cb) return;
                const gidAttr = e.target.getAttribute('data-group-check');
                if (gidAttr) {
                    const gid = parseInt(gidAttr, 10);
                    const items = (CDI.state && CDI.state.items) || [];
                    items.forEach((it, i) => {
                        if (it.grupo_id === gid) {
                            if (e.target.checked) selectedRows.add(i);
                            else selectedRows.delete(i);
                        }
                    });
                } else {
                    const idx = parseInt(e.target.getAttribute('data-row-check'), 10);
                    if (!isFinite(idx)) return;
                    if (e.target.checked) selectedRows.add(idx);
                    else selectedRows.delete(idx);
                }
                updateBatchBar();
            });
            // Delegación de clicks para botones Asistente y pills de notas
            tbody.addEventListener('click', (e) => {
                const assist = e.target && e.target.closest && e.target.closest('[data-assist]');
                if (assist) {
                    e.preventDefault();
                    e.stopPropagation();
                    const idx = parseInt(assist.getAttribute('data-assist'), 10);
                    try {
                        openSpotlight(idx);
                    } catch (err) {
                        console.error('[ncm] ERROR opening spotlight', err);
                    }
                    return;
                }
                const notePill = e.target && e.target.closest && e.target.closest('[data-note-pill]');
                if (notePill) {
                    e.preventDefault();
                    e.stopPropagation();
                    try {
                        onNotePillClick.call(notePill, e);
                    } catch (err) {
                        console.error('[ncm] ERROR on note pill click', err);
                    }
                    return;
                }
                const grupoChip = e.target && e.target.closest && e.target.closest('.ncm-grupo-chip');
                if (grupoChip) {
                    e.preventDefault();
                    e.stopPropagation();
                    const gid = parseInt(grupoChip.getAttribute('data-grupo'), 10);
                    if (isFinite(gid)) desagrupar(gid);
                    return;
                }
                const expandBtn = e.target && e.target.closest && e.target.closest('[data-expand-grupo]');
                if (expandBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    const gid = parseInt(expandBtn.getAttribute('data-expand-grupo'), 10);
                    if (isFinite(gid)) {
                        if (expandedGroups.has(gid)) expandedGroups.delete(gid);
                        else expandedGroups.add(gid);
                        render();
                    }
                    return;
                }
            });
        }
        if (batchApplyQty) batchApplyQty.addEventListener('click', applyBatchMultiply);
        if (batchApplyNcm) batchApplyNcm.addEventListener('click', applyBatchNcm);
        if (batchApplyOrigin) batchApplyOrigin.addEventListener('click', applyBatchOrigin);
        if (batchAgrupar) batchAgrupar.addEventListener('click', agruparSeleccionados);
        if (batchClear) batchClear.addEventListener('click', () => {
            selectedRows.clear();
            if (selectAllBox) selectAllBox.checked = false;
            render();
            updateBatchBar();
        });

        // ---------- Drag & Drop filas ----------
        setupRowDragAndDrop();

        initialized = true;
    }

    function setupRowDragAndDrop() {
        if (!tbody) return;
        // Solo habilitar draggable cuando el mousedown arranca en el handle (col-num)
        tbody.addEventListener('mousedown', (e) => {
            const handle = e.target.closest('.col-num');
            const tr = e.target.closest('tr[data-index]');
            if (handle && tr) {
                tr.setAttribute('draggable', 'true');
            }
        });
        tbody.addEventListener('mouseup', () => {
            tbody.querySelectorAll('tr[draggable="true"]').forEach(r => r.removeAttribute('draggable'));
        });

        tbody.addEventListener('dragstart', (e) => {
            const tr = e.target.closest && e.target.closest('tr[data-index]');
            if (!tr || tr.getAttribute('draggable') !== 'true') { e.preventDefault(); return; }
            const idx = tr.getAttribute('data-index');
            try { e.dataTransfer.setData('text/plain', idx); } catch (_) {}
            try { e.dataTransfer.effectAllowed = 'move'; } catch (_) {}
            tr.classList.add('is-dragging');
            document.body.classList.add('cdi-dragging-row');
        });

        tbody.addEventListener('dragend', () => {
            tbody.querySelectorAll('tr.is-dragging').forEach(r => r.classList.remove('is-dragging'));
            tbody.querySelectorAll('tr.row-dragover').forEach(r => r.classList.remove('row-dragover'));
            tbody.querySelectorAll('tr[draggable="true"]').forEach(r => r.removeAttribute('draggable'));
            document.body.classList.remove('cdi-dragging-row');
        });

        tbody.addEventListener('dragover', (e) => {
            const tr = e.target.closest && e.target.closest('tr[data-index]');
            if (!tr) return;
            e.preventDefault();
            try { e.dataTransfer.dropEffect = 'move'; } catch (_) {}
            tbody.querySelectorAll('tr.row-dragover').forEach(r => { if (r !== tr) r.classList.remove('row-dragover'); });
            tr.classList.add('row-dragover');
        });

        tbody.addEventListener('dragleave', (e) => {
            const tr = e.target.closest && e.target.closest('tr[data-index]');
            if (tr) tr.classList.remove('row-dragover');
        });

        tbody.addEventListener('drop', (e) => {
            e.preventDefault();
            const tr = e.target.closest && e.target.closest('tr[data-index]');
            if (!tr) return;
            const toIdx = parseInt(tr.getAttribute('data-index'), 10);
            let fromIdx = NaN;
            try { fromIdx = parseInt(e.dataTransfer.getData('text/plain'), 10); } catch (_) {}
            if (!isFinite(fromIdx) || !isFinite(toIdx) || fromIdx === toIdx) return;
            reorderItems(fromIdx, toIdx);
        });
    }

    function reorderItems(fromIdx, toIdx) {
        const items = (CDI.state && CDI.state.items) || [];
        if (fromIdx < 0 || fromIdx >= items.length) return;
        if (toIdx < 0 || toIdx >= items.length) return;
        const [moved] = items.splice(fromIdx, 1);
        items.splice(toIdx, 0, moved);
        // Actualizar set de seleccion: recalcular indices post-movida
        const wasSelected = new Set();
        selectedRows.forEach(i => {
            if (i === fromIdx) { wasSelected.add(toIdx); return; }
            let newIdx = i;
            if (fromIdx < toIdx) {
                if (i > fromIdx && i <= toIdx) newIdx = i - 1;
            } else {
                if (i < fromIdx && i >= toIdx) newIdx = i + 1;
            }
            wasSelected.add(newIdx);
        });
        selectedRows.clear();
        wasSelected.forEach(i => selectedRows.add(i));
        try { CDI.track && CDI.track('ncm_row_reordered', { from: fromIdx, to: toIdx }); } catch (_) {}
        render();
    }

    function onSelectAll(checked) {
        const items = (CDI.state && CDI.state.items) || [];
        selectedRows.clear();
        if (checked) items.forEach((_, i) => selectedRows.add(i));
        tbody.querySelectorAll('[data-row-check], [data-group-check]').forEach(cb => { cb.checked = checked; });
        updateBatchBar();
    }

    function updateBatchBar() {
        if (!batchBar || !batchCount) return;
        const n = selectedRows.size;
        if (n === 0) {
            batchBar.hidden = true;
            if (selectAllBox) selectAllBox.indeterminate = false;
            if (batchAgrupar) batchAgrupar.disabled = true;
            return;
        }
        batchBar.hidden = false;
        batchCount.textContent = n + (n === 1 ? ' ítem seleccionado' : ' ítems seleccionados');
        const allItems = ((CDI.state && CDI.state.items) || []);
        const grupos = new Set();
        let realTotal = 0;
        allItems.forEach(it => {
            if (it.grupo_id) {
                if (!grupos.has(it.grupo_id)) { grupos.add(it.grupo_id); realTotal++; }
            } else realTotal++;
        });
        const total = realTotal;
        if (selectAllBox) {
            selectAllBox.checked = n === total;
            selectAllBox.indeterminate = n > 0 && n < total;
        }
        if (batchAgrupar) batchAgrupar.disabled = n < 2;
    }

    function snapshotItems() {
        const items = (CDI.state && CDI.state.items) || [];
        return items.map(it => Object.assign({}, it));
    }

    function scheduleUndoClear(label) {
        if (undoTimer) clearTimeout(undoTimer);
        undoTimer = setTimeout(() => { lastSnapshot = null; }, 10000);
        // Toast con accion undo
        if (CDI.toast) {
            CDI.toast('Cambio aplicado', label + ' · deshace con Ctrl+Z', 'success');
        }
    }

    function undoLastBatch() {
        if (!lastSnapshot) return false;
        if (!CDI.state || !Array.isArray(CDI.state.items)) return false;
        CDI.state.items = lastSnapshot.items;
        lastSnapshot = null;
        render();
        updateBatchBar();
        if (CDI.toast) CDI.toast('Deshecho', 'Se restauraron los valores previos', 'info');
        try { CDI.track && CDI.track('ncm_batch_undo'); } catch (_) {}
        return true;
    }

    function applyBatchMultiply() {
        const items = (CDI.state && CDI.state.items) || [];
        if (selectedRows.size === 0 || !items.length) return;
        const factor = Number(batchFactor && batchFactor.value);
        if (!isFinite(factor) || factor <= 0) {
            if (CDI.toast) CDI.toast('Factor inválido', 'Usá un número mayor a 0', 'error');
            return;
        }
        if (factor === 1) {
            if (CDI.toast) CDI.toast('Sin cambios', 'El factor es 1', 'info');
            return;
        }
        lastSnapshot = { items: snapshotItems(), ts: Date.now() };
        let touched = 0;
        selectedRows.forEach(i => {
            const it = items[i];
            if (!it) return;
            const prev = Number(it.cantidad) || 0;
            it.cantidad = prev * factor;
            touched++;
        });
        try { CDI.track && CDI.track('ncm_batch_multiply', { count: touched, factor: factor }); } catch (_) {}
        const label = '× ' + factor + ' a ' + touched + (touched === 1 ? ' item' : ' items');
        scheduleUndoClear(label);
        render();
        updateBatchBar();
    }

    function onBatchSimInput() {
        const parts = splitSimPosition(batchNcm && batchNcm.value);
        if (batchNcm) batchNcm.value = CDI.formatNcm ? CDI.formatNcm(parts.digits) : parts.digits;
        if (parts.dc && batchDc) batchDc.value = parts.dc;
    }

    function onBatchDcInput() {
        if (!batchDc) return;
        batchDc.value = String(batchDc.value || '').replace(/[^A-Za-z]/g, '').slice(0, 1).toUpperCase();
    }

    function batchSimValue() {
        return buildSimPosition(batchNcm && batchNcm.value, batchDc && batchDc.value);
    }

    function applyBatchNcm() {
        const items = (CDI.state && CDI.state.items) || [];
        if (selectedRows.size === 0 || !items.length) return;
        const formatted = normalizeBatchNcm(batchSimValue());
        if (!formatted) {
            if (CDI.toast) CDI.toast('Posición SIM incompleta', simErrorDetail(batchSimValue()), 'error');
            return;
        }
        lastSnapshot = { items: snapshotItems(), ts: Date.now() };
        let touched = 0;
        selectedRows.forEach(i => {
            const it = items[i];
            if (!it) return;
            it.pieza = formatted;
            touched++;
        });
        try { CDI.track && CDI.track('ncm_batch_ncm_applied', { count: touched, ncm: formatted }); } catch (_) {}
        scheduleUndoClear('NCM ' + formatted + ' a ' + touched + (touched === 1 ? ' item' : ' items'));
        render();
        updateBatchBar();
    }

    function applyBatchOrigin() {
        const items = (CDI.state && CDI.state.items) || [];
        if (selectedRows.size === 0 || !items.length) return;
        const raw = (batchOrigin && batchOrigin.value || '').trim();
        const origin = getOriginCode(raw);
        if (!origin) {
            if (CDI.toast) CDI.toast('Origen inválido', 'Elegí un país de la tabla MARIA, por ejemplo 310 · CHINA.', 'error');
            return;
        }
        lastSnapshot = { items: snapshotItems(), ts: Date.now() };
        let touched = 0;
        selectedRows.forEach(i => {
            const it = items[i];
            if (!it) return;
            it.origen = origin;
            touched++;
        });
        if (batchOrigin) batchOrigin.value = getOriginLabel(origin);
        try { CDI.track && CDI.track('ncm_batch_origin_applied', { count: touched, origin: origin }); } catch (_) {}
        scheduleUndoClear('Origen ' + getOriginLabel(origin) + ' a ' + touched + (touched === 1 ? ' item' : ' items'));
        render();
        updateBatchBar();
    }

    // Atajo Ctrl+Z / Cmd+Z para undo del ultimo batch
    document.addEventListener('keydown', (e) => {
        if (!lastSnapshot) return;
        const isMod = e.metaKey || e.ctrlKey;
        if (isMod && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) {
            // Solo si estamos en pantalla NCM
            const activeScreen = document.querySelector('.screen.is-active');
            if (!activeScreen || activeScreen.getAttribute('data-screen') !== 'ncm') return;
            // Y no dentro de un input text activo (para no pisar undo nativo)
            const tag = document.activeElement && document.activeElement.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA') return;
            e.preventDefault();
            undoLastBatch();
        }
    });

    /* ---------- Render tabla ---------- */
    function render() {
        init();
        if (!tbody) return;
        const items = (CDI.state && CDI.state.items) || [];
        // Limpia selecciones que quedaron fuera de rango (si cambiaron los items)
        Array.from(selectedRows).forEach(i => { if (i >= items.length) selectedRows.delete(i); });
        const renderRows = buildRenderRows(items);
        tbody.innerHTML = renderRows.map(r => r.type === 'group' ? renderGroupedRow(r) : renderRow(r.item, r.index)).join('');
        renderAutofillBanner();

        // Listeners inline por fila
        tbody.querySelectorAll('.ncm-input').forEach(inp => {
            if (CDI.maskNcm) CDI.maskNcm(inp);
            inp.addEventListener('input', onNcmInput);
            inp.addEventListener('blur', onNcmBlur);
            inp.addEventListener('keydown', onNcmKeydown);
        });
        tbody.querySelectorAll('.sim-dc-input').forEach(inp => {
            inp.addEventListener('input', onSimDcInput);
            inp.addEventListener('blur', onNcmBlur);
            inp.addEventListener('keydown', onNcmKeydown);
        });
        tbody.querySelectorAll('.ncm-edit').forEach(inp => {
            inp.addEventListener('input', onFieldInput);
            inp.addEventListener('blur', onFieldBlur);
            inp.addEventListener('keydown', onFieldKeydown);
        });
        tbody.querySelectorAll('[data-note-pill]').forEach(btn => {
            btn.addEventListener('click', onNotePillClick);
        });
        updateSummary();
        updateBatchBar();
        prefetchAllNotes();
    }

    async function prefetchAllNotes() {
        if (!CDI.ncmNotes) return;
        const items = (CDI.state && CDI.state.items) || [];
        const uniq = new Set();
        items.forEach(it => {
            const key = CDI.ncmNotes.prefix4(it.pieza || '');
            if (key) uniq.add(key);
        });
        await Promise.all(Array.from(uniq).map(k => CDI.ncmNotes.prefetch(k).catch(() => null)));
        refreshAllPills();
    }

    function refreshAllPills() {
        if (!tbody || !CDI.ncmNotes) return;
        tbody.querySelectorAll('[data-note-pill]').forEach(btn => {
            const ncm = btn.getAttribute('data-ncm');
            const cached = CDI.ncmNotes.getCached(ncm);
            const count = cached ? cached.length : 0;
            btn.classList.toggle('is-empty', count === 0);
            let countEl = btn.querySelector('.ncm-note-pill-count');
            if (count > 0) {
                if (!countEl) {
                    countEl = document.createElement('span');
                    countEl.className = 'ncm-note-pill-count';
                    btn.appendChild(countEl);
                }
                countEl.textContent = String(count);
            } else if (countEl) {
                countEl.remove();
            }
            if (cached && cached.length) {
                const tooltip = cached[0].slice(0, 80) + (cached.length > 1 ? '  (+' + (cached.length - 1) + ')' : '');
                btn.setAttribute('title', tooltip);
            }
        });
    }

    function onNotePillClick(ev) {
        ev.stopPropagation();
        const btn = ev.currentTarget;
        const ncm = btn.getAttribute('data-ncm');
        if (!ncm || !CDI.ncmNotes) return;
        CDI.ncmNotes.open(ncm);
    }

    function renderRow(it, i) {
        const pieza = (it.pieza || '').trim();
        const isValid = isValidNcm(pieza);
        const isOk = !!pieza && isValid;
        const isError = !!pieza && !isValid;
        const rowClass = isOk ? 'row-ok' : 'row-pending';
        const desc = CDI.escapeHtml(it.descripcion || it.codigo_parte || '');
        const ref = CDI.escapeHtml(it.codigo_parte || '—');
        const origen = CDI.escapeHtml(getOriginLabel(it.origen));
        const cantidad = it.cantidad != null ? Number(it.cantidad) : '';
        const valorUnitario = Number(it.valor_unitario || 0);
        const pesoUnitario = Number(it.peso_unitario || 0);
        const simParts = splitSimPosition(pieza);
        const simValue = CDI.escapeHtml(CDI.formatNcm ? CDI.formatNcm(simParts.digits) : simParts.digits);
        const dcValue = CDI.escapeHtml(simParts.dc);
        const assistText = isOk ? 'Cambiar' : 'Asistente';
        const notesPill = renderNotesPill(pieza, i);
        const checked = selectedRows.has(i) ? ' checked' : '';
        const autofillChip = renderAutofillChip(it);
        const grupoChip = renderGrupoChip(it);
        const fmtMoney = (v) => v ? '$' + v.toLocaleString('es-AR', { maximumFractionDigits: 2 }) : '';
        const fmtPeso = (v) => v ? v.toLocaleString('es-AR', { maximumFractionDigits: 2 }) : '';
        const cantVal = cantidad === '' ? '' : cantidad;
        const inputClass = 'ncm-input' + (isError ? ' is-error' : '');
        return (
            '<tr class="' + rowClass + '" data-row="' + i + '" data-index="' + i + '">' +
                '<td class="col-check"><input type="checkbox" class="ncm-row-check" data-row-check="' + i + '"' + checked + ' aria-label="Seleccionar item ' + (i + 1) + '"></td>' +
                '<td class="col-num" title="Arrastrar para reordenar"><span class="drag-grip" aria-hidden="true">⋮⋮</span>' + (i + 1) + '</td>' +
                '<td class="col-ref">' + ref + '</td>' +
                '<td class="col-desc">' + desc + '</td>' +
                '<td class="col-pais"><input class="ncm-edit ncm-edit-pais input input-sm" type="text" list="ncmCountries" value="' + origen + '" data-row="' + i + '" data-field="origen" aria-label="Origen item ' + (i + 1) + '"></td>' +
                '<td class="col-cant"><input class="ncm-edit ncm-edit-cant input input-sm" type="number" min="1" step="1" value="' + cantVal + '" data-row="' + i + '" data-field="cantidad" aria-label="Cantidad item ' + (i + 1) + '"></td>' +
                '<td class="col-valor"><input class="ncm-edit ncm-edit-valor input input-sm" type="number" min="0" step="0.01" value="' + (valorUnitario || '') + '" data-row="' + i + '" data-field="valor_unitario" aria-label="Valor unitario item ' + (i + 1) + '"></td>' +
                '<td class="col-peso"><input class="ncm-edit ncm-edit-peso input input-sm" type="number" min="0" step="0.01" value="' + (pesoUnitario || '') + '" data-row="' + i + '" data-field="peso_unitario" aria-label="Peso unitario item ' + (i + 1) + '"></td>' +
                '<td class="col-ncm">' +
                    '<div class="ncm-cell">' +
                        '<div class="sim-position-fields">' +
                            '<input class="' + inputClass + '" type="text" placeholder="0000.00.00.000"' +
                            ' data-row="' + i + '" aria-label="Posición SIM item ' + (i + 1) + '"' +
                            ' value="' + simValue + '">' +
                            '<label class="sim-dc-field"><span>DC</span>' +
                                '<input class="sim-dc-input' + (isError ? ' is-error' : '') + '" type="text" maxlength="1"' +
                                ' data-row="' + i + '" aria-label="Letra de control item ' + (i + 1) + '" value="' + dcValue + '">' +
                            '</label>' +
                        '</div>' +
                        notesPill +
                        autofillChip +
                    '</div>' +
                '</td>' +
                '<td class="col-actions">' +
                    (isOk ? '<span class="check" aria-label="asignado">✓</span> ' : '') +
                    grupoChip +
                    '<button type="button" class="btn-assist" data-assist="' + i + '">' +
                        assistText +
                    '</button>' +
                '</td>' +
            '</tr>'
        );
    }

    function buildRenderRows(items) {
        const used = new Set();
        const rows = [];
        items.forEach((it, i) => {
            if (used.has(i)) return;
            if (it.grupo_id) {
                const indices = [];
                const groupItems = [];
                items.forEach((other, j) => {
                    if (other.grupo_id === it.grupo_id) {
                        indices.push(j);
                        groupItems.push(other);
                        used.add(j);
                    }
                });
                const totalCant = groupItems.reduce((s, x) => s + Number(x.cantidad || 0), 0);
                const totalValue = groupItems.reduce((s, x) => s + Number(x.valor_unitario || 0) * Number(x.cantidad || 0), 0);
                const totalPeso = groupItems.reduce((s, x) => s + Number(x.peso_unitario || 0) * Number(x.cantidad || 0), 0);
                const avgValor = totalCant > 0 ? Math.round((totalValue / totalCant) * 100) / 100 : 0;
                const avgPeso = totalCant > 0 ? Math.round((totalPeso / totalCant) * 100) / 100 : 0;
                const descs = [...new Set(groupItems.map(x => (x.descripcion || '').trim()).filter(Boolean))];
                const desc = descs.length === 1 ? descs[0] : descs.join(' · ').slice(0, 80);
                rows.push({
                    type: 'group', grupo_id: it.grupo_id, indices, items: groupItems,
                    aggregated: {
                        descripcion: desc, origen: it.origen || '',
                        cantidad: totalCant, valor_unitario: avgValor,
                        peso_unitario: avgPeso, pieza: it.pieza || '',
                        codigo_parte: it.codigo_parte || '',
                    }
                });
            } else {
                rows.push({ type: 'single', index: i, item: it });
            }
        });
        return rows;
    }

    function renderGroupedRow(r) {
        const it = r.aggregated;
        const gid = r.grupo_id;
        const pieza = (it.pieza || '').trim();
        const isValid = isValidNcm(pieza);
        const isOk = !!pieza && isValid;
        const rowClass = isOk ? 'row-ok' : 'row-pending';
        const desc = CDI.escapeHtml(it.descripcion || '');
        const ref = CDI.escapeHtml(it.codigo_parte || '—');
        const origen = CDI.escapeHtml(getOriginLabel(it.origen));
        const cantVal = it.cantidad != null ? Number(it.cantidad) : '';
        const valorUnitario = Number(it.valor_unitario || 0);
        const pesoUnitario = Number(it.peso_unitario || 0);
        const simParts = splitSimPosition(pieza);
        const simValue = CDI.escapeHtml(CDI.formatNcm ? CDI.formatNcm(simParts.digits) : simParts.digits);
        const dcValue = CDI.escapeHtml(simParts.dc);
        const notesPill = renderNotesPill(pieza, r.indices[0]);
        const allSelected = r.indices.every(i => selectedRows.has(i));
        const checked = allSelected ? ' checked' : '';
        const isExpanded = expandedGroups.has(gid);
        const expandIcon = isExpanded ? '▾' : '▸';
        const grupoLabel = 'Grupo ' + gid + ' (' + r.items.length + ' ítems)';
        const inputClass = 'ncm-input ncm-group-input' + (pieza && !isValid ? ' is-error' : '');
        let html = '<tr class="' + rowClass + ' row-grouped" data-grupo-id="' + gid + '">' +
            '<td class="col-check"><input type="checkbox" class="ncm-row-check" data-group-check="' + gid + '"' + checked + ' aria-label="Seleccionar grupo ' + gid + '"></td>' +
            '<td class="col-num"><button type="button" class="ncm-expand-btn" data-expand-grupo="' + gid + '" aria-label="Expandir grupo">' + expandIcon + '</button></td>' +
            '<td class="col-ref">' + ref + '</td>' +
            '<td class="col-desc">' + desc + '</td>' +
            '<td class="col-pais"><input class="ncm-edit ncm-edit-pais input input-sm" type="text" list="ncmCountries" value="' + origen + '" data-grupo-id="' + gid + '" data-field="origen" aria-label="Origen grupo ' + gid + '"></td>' +
            '<td class="col-cant"><input class="ncm-edit ncm-edit-cant input input-sm" type="number" min="1" step="1" value="' + cantVal + '" data-grupo-id="' + gid + '" data-field="cantidad" aria-label="Cantidad grupo ' + gid + '"></td>' +
            '<td class="col-valor"><input class="ncm-edit ncm-edit-valor input input-sm" type="number" min="0" step="0.01" value="' + (valorUnitario || '') + '" data-grupo-id="' + gid + '" data-field="valor_unitario" aria-label="Valor grupo ' + gid + '"></td>' +
            '<td class="col-peso"><input class="ncm-edit ncm-edit-peso input input-sm" type="number" min="0" step="0.01" value="' + (pesoUnitario || '') + '" data-grupo-id="' + gid + '" data-field="peso_unitario" aria-label="Peso grupo ' + gid + '"></td>' +
            '<td class="col-ncm"><div class="ncm-cell"><div class="sim-position-fields">' +
                '<input class="' + inputClass + '" type="text" placeholder="0000.00.00.000" value="' + simValue + '" data-grupo-id="' + gid + '" data-field="pieza" aria-label="Posición SIM grupo ' + gid + '">' +
                '<label class="sim-dc-field"><span>DC</span><input class="sim-dc-input' + (pieza && !isValid ? ' is-error' : '') + '" type="text" maxlength="1" value="' + dcValue + '" data-grupo-id="' + gid + '" aria-label="Letra de control grupo ' + gid + '"></label>' +
            '</div>' + notesPill + '</div></td>' +
            '<td class="col-actions">' + (isOk ? '<span class="check" aria-label="asignado">✓</span> ' : '') +
            '<button type="button" class="ncm-grupo-chip" data-grupo="' + gid + '" title="Clic para desagrupar">' + grupoLabel + '</button></td>' +
        '</tr>';
        if (isExpanded) {
            html += r.items.map((subIt, j) => renderSubRow(subIt, r.indices[j], gid)).join('');
        }
        return html;
    }

    function renderSubRow(it, idx, gid) {
        const desc = CDI.escapeHtml(it.descripcion || it.codigo_parte || '');
        const ref = CDI.escapeHtml(it.codigo_parte || '—');
        const origen = CDI.escapeHtml(getOriginLabel(it.origen));
        const cantidad = it.cantidad != null ? Number(it.cantidad) : '';
        const valorUnitario = Number(it.valor_unitario || 0);
        const pesoUnitario = Number(it.peso_unitario || 0);
        const fmtMoney = (v) => v ? '$' + v.toLocaleString('es-AR', { maximumFractionDigits: 2 }) : '';
        const fmtPeso = (v) => v ? v.toLocaleString('es-AR', { maximumFractionDigits: 2 }) : '';
        return '<tr class="row-sub" data-grupo-id="' + gid + '">' +
            '<td class="col-check"></td>' +
            '<td class="col-num"></td>' +
            '<td class="col-ref">' + ref + '</td>' +
            '<td class="col-desc">' + desc + '</td>' +
            '<td class="col-pais"><span class="ncm-sub-val">' + origen + '</span></td>' +
            '<td class="col-cant"><span class="ncm-sub-val">' + cantidad + '</span></td>' +
            '<td class="col-valor"><span class="ncm-sub-val">' + fmtMoney(valorUnitario) + '</span></td>' +
            '<td class="col-peso"><span class="ncm-sub-val">' + fmtPeso(pesoUnitario) + '</span></td>' +
            '<td class="col-ncm"></td>' +
            '<td class="col-actions"></td>' +
        '</tr>';
    }

    function normalizeBatchNcm(rawValue) {
        const raw = String(rawValue || '').trim();
        if (!raw) return '';
        const formatted = CDI.formatNcm ? CDI.formatNcm(raw) : raw;
        return isValidNcm(formatted) ? formatted : '';
    }

    function applyNcmAndGroup(items, indices, rawNcm) {
        const selectedIndices = Array.from(indices || []).filter(i => items[i]);
        if (selectedIndices.length < 2) {
            return { ok: false, title: 'Seleccioná 2+ ítems', message: 'Marcá los productos que forman una sola unidad clasificatoria.' };
        }
        const selected = selectedIndices.map(i => items[i]);
        const requestedNcm = normalizeBatchNcm(rawNcm);
        if (String(rawNcm || '').trim() && !requestedNcm) {
            return { ok: false, title: 'Posición SIM incompleta', message: simErrorDetail(rawNcm) };
        }

        const existingNcms = new Set(selected.map(it => normalizeBatchNcm(it.pieza)).filter(Boolean));
        const targetNcm = requestedNcm || (existingNcms.size === 1 ? Array.from(existingNcms)[0] : '');
        if (!targetNcm) {
            return { ok: false, title: 'Indicá la posición SIM', message: 'Escribí los 11 dígitos y la letra DC: se asignarán a todos y se unirán en el mismo paso.' };
        }

        // CN, China y 310 son el mismo país: los normalizamos antes de decidir
        // si se pueden unir y persistimos el código MARIA en el nuevo grupo.
        const origenes = new Set(selected.map(it => getOriginCode(it.origen) || String(it.origen || '').trim().toUpperCase()));
        if (origenes.size > 1) {
            return { ok: false, title: 'Origen distinto', message: 'Para unirlos deben tener el mismo origen. Corregilo o usá “Origen para todos”.' };
        }
        const unidades = new Set(selected.map(it => String(it.unidad || '').trim().toUpperCase()));
        if (unidades.size > 1) {
            return { ok: false, title: 'Unidad distinta', message: 'No se pueden unir productos con unidades de medida diferentes.' };
        }

        const maxGrupo = items.reduce((mx, it) => Math.max(mx, Number(it.grupo_id) || 0), 0);
        const nuevoGrupo = maxGrupo + 1;
        selectedIndices.forEach(i => {
            items[i].pieza = targetNcm;
            items[i].origen = Array.from(origenes)[0];
            items[i].grupo_id = nuevoGrupo;
        });
        return { ok: true, grupo_id: nuevoGrupo, count: selectedIndices.length, ncm: targetNcm };
    }

    // API pequeña y determinística para probar la acción masiva sin navegador.
    CDI.ncmBatch = CDI.ncmBatch || {};
    CDI.ncmBatch.applyNcmAndGroup = applyNcmAndGroup;
    CDI.ncmBatch.isValidSimPosition = isValidNcm;

    function agruparSeleccionados() {
        const items = (CDI.state && CDI.state.items) || [];
        if (!items.length) return;
        const before = snapshotItems();
        const result = applyNcmAndGroup(items, selectedRows, batchSimValue());
        if (!result.ok) {
            if (CDI.toast) CDI.toast(result.title, result.message, 'error');
            return;
        }
        lastSnapshot = { items: before, ts: Date.now() };
        CDI.track && CDI.track('ncm_agrupar', { grupo_id: result.grupo_id, items: result.count, ncm: result.ncm, batch: true });
        scheduleUndoClear('NCM ' + result.ncm + ' · ' + result.count + ' ítems → 1 unidad clasificatoria');

        selectedRows.clear();
        if (batchNcm) batchNcm.value = '';
        if (batchDc) batchDc.value = '';
        if (selectAllBox) selectAllBox.checked = false;
        render();
        updateBatchBar();
    }

    function desagrupar(grupoId) {
        const items = (CDI.state && CDI.state.items) || [];
        let count = 0;
        items.forEach(it => {
            if (it.grupo_id === grupoId) { it.grupo_id = null; count++; }
        });
        if (count > 0) {
            CDI.track && CDI.track('ncm_desagrupar', { grupo_id: grupoId, items: count });
            if (CDI.toast) CDI.toast('Desagrupado', count + ' ítems liberados del grupo ' + grupoId, 'info');
            render();
            updateBatchBar();
        }
    }

    function renderGrupoChip(it) {
        if (!it || !it.grupo_id) return '';
        return '<button type="button" class="ncm-grupo-chip" data-grupo="' + it.grupo_id + '"' +
            ' title="Clic para desagrupar">Grupo ' + it.grupo_id + '</button>';
    }

    function renderAutofillBanner() {
        const host = document.getElementById('screen-ncm') || tbody && tbody.closest('section');
        if (!host) return;

        // Siempre limpiamos el banner anterior para evitar duplicados
        const prev = host.querySelector('#ncmAutofillBanner');
        if (prev) prev.remove();

        const banner = CDI.state && CDI.state.catalogAutofillBanner;
        if (!banner || !banner.aplicados_total) return;

        const div = document.createElement('div');
        div.id = 'ncmAutofillBanner';
        div.className = 'ncm-autofill-banner';
        const cli = banner.aplicados_cliente || 0;
        const prov = banner.aplicados_proveedor || 0;
        const total = banner.aplicados_total;
        const totalItems = banner.total_items || '';
        let detail = [];
        if (cli) detail.push(cli + ' de memoria del cliente');
        if (prov) detail.push(prov + ' del catalogo del proveedor');
        const detailText = detail.length ? ' (' + detail.join(' + ') + ')' : '';

        div.innerHTML = (
            '<div class="ncm-autofill-banner-inner">' +
                '<span class="ncm-autofill-icon" aria-hidden="true">✨</span>' +
                '<span class="ncm-autofill-text">Se autocompletaron <strong>' + total +
                ' de ' + totalItems + '</strong> NCM' + detailText +
                '. Revisalos antes de continuar.</span>' +
                '<button type="button" class="ncm-autofill-undo" id="ncmAutofillUndo">Deshacer</button>' +
                '<button type="button" class="ncm-autofill-close" id="ncmAutofillClose" aria-label="Cerrar">×</button>' +
            '</div>'
        );

        // Insertar al inicio del screen
        host.insertBefore(div, host.firstChild);

        const undoBtn = div.querySelector('#ncmAutofillUndo');
        const closeBtn = div.querySelector('#ncmAutofillClose');
        if (undoBtn) undoBtn.addEventListener('click', onAutofillUndo);
        if (closeBtn) closeBtn.addEventListener('click', () => {
            CDI.state.catalogAutofillBanner = null;
            div.remove();
        });

        // Hint contextual: la primera vez que el user ve este banner,
        // le explicamos qué es el auto-catálogo en lenguaje simple.
        try {
            if (CDI.hint) {
                CDI.hint('banner_autofill', {
                    target: div,
                    title: '✨ Auto-catálogo en acción',
                    text: 'Reconocimos al proveedor de este PDF y te sugerimos los NCM que ya usó antes. Revisalos: vos confirmás, la AI propone.',
                    cta: 'Entendido',
                    ttl: 12000,
                });
            }
        } catch (_) {}
    }

    function onAutofillUndo() {
        const banner = CDI.state && CDI.state.catalogAutofillBanner;
        if (!banner || !banner.undoSnapshot) return;
        const items = (CDI.state && CDI.state.items) || [];
        banner.undoSnapshot.forEach((snap, i) => {
            const it = items[i];
            if (!it) return;
            it.pieza = snap.pieza || '';
            it.origen = snap.origen || '';
            delete it.__autofillSource;
            delete it.__autofillConfidence;
        });
        CDI.state.catalogAutofillBanner = null;
        CDI.track && CDI.track('catalog_autofill_undo', { aplicados: banner.aplicados_total });
        if (CDI.toast) CDI.toast.info('Autocompletado deshecho');
        render();
    }

    function renderAutofillChip(it) {
        if (!it || !it.__autofillSource) return '';
        const src = it.__autofillSource;
        let label = '', cls = '', icon = '';
        if (src === 'cliente') { label = 'Cliente'; cls = 'chip-cliente'; icon = '📚 '; }
        else if (src === 'proveedor') { label = 'Proveedor'; cls = 'chip-proveedor'; }
        else return '';
        const conf = it.__autofillConfidence ? ' (' + Math.round(it.__autofillConfidence * 100) + '%)' : '';
        return '<span class="ncm-autofill-chip ' + cls + '" title="NCM sugerido desde ' + label.toLowerCase() + conf + '">' + icon + label + '</span>';
    }

    function renderNotesPill(ncm, rowIdx) {
        if (!ncm || !CDI.ncmNotes) return '';
        const ncmKey = CDI.ncmNotes.prefix4(ncm);
        if (!ncmKey) return '';
        const cached = CDI.ncmNotes.getCached(ncm);
        const count = cached ? cached.length : null;
        const hidden = count === 0 ? ' is-empty' : '';
        const tooltip = cached && cached.length
            ? cached[0].slice(0, 80) + (cached.length > 1 ? '  (+' + (cached.length - 1) + ')' : '')
            : 'Agregar nota al capítulo ' + ncmKey;
        return (
            '<button type="button" class="ncm-note-pill' + hidden + '"' +
                ' data-note-pill="' + rowIdx + '" data-ncm="' + ncmKey + '"' +
                ' title="' + CDI.escapeHtml(tooltip) + '">' +
                '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/></svg>' +
                (count ? '<span class="ncm-note-pill-count">' + count + '</span>' : '') +
            '</button>'
        );
    }

    function updateSummary() {
        const items = (CDI.state && CDI.state.items) || [];
        // Contar grupos como 1 ítem cada uno
        const grupos = new Set();
        let realTotal = 0;
        items.forEach(it => {
            if (it.grupo_id) {
                if (!grupos.has(it.grupo_id)) {
                    grupos.add(it.grupo_id);
                    realTotal++;
                }
            } else {
                realTotal++;
            }
        });
        const total = realTotal;
        // Un item esta "listo" solo si su NCM cumple el formato (8 o 10 digitos).
        const seenGrupos = new Set();
        let done = 0, incomplete = 0;
        items.forEach(it => {
            if (it.grupo_id) {
                if (seenGrupos.has(it.grupo_id)) return;
                seenGrupos.add(it.grupo_id);
            }
            if (isValidNcm(it.pieza)) done++;
            else if (String(it.pieza || '').trim()) incomplete++;
        });
        const empty = total - done - incomplete;
        const missing = empty + incomplete;
        if (summaryEl) {
            if (missing === 0) {
                summaryEl.innerHTML = total + ' productos · <strong style="color: var(--c-success);">todos listos</strong>';
            } else {
                let breakdown = '<strong style="color: var(--c-warning);">' + missing + ' sin posición SIM completa</strong>';
                if (incomplete > 0 && empty > 0) {
                    breakdown += ' (' + empty + ' vacíos · ' + incomplete + ' incompletos)';
                } else if (incomplete > 0) {
                    breakdown += ' (' + incomplete + ' incompleto' + (incomplete > 1 ? 's' : '') + ')';
                }
                summaryEl.innerHTML = total + ' productos · ' + breakdown + ' · ' + done + ' listos';
            }
        }
        if (continueBtn) {
            continueBtn.disabled = missing > 0 || total === 0;
            continueBtn.firstChild.nodeValue = missing === 0
                ? 'Continuar a validar '
                : 'Completar ' + missing + ' posición' + (missing > 1 ? 'es SIM ' : ' SIM ');
        }
    }

    function onNcmInput(ev) {
        const inp = ev.target;
        const fields = inp.closest('.sim-position-fields');
        const dcInput = fields && fields.querySelector('.sim-dc-input');
        const parts = splitSimPosition(inp.value);
        inp.value = CDI.formatNcm ? CDI.formatNcm(parts.digits) : parts.digits;
        if (parts.dc && dcInput) dcInput.value = parts.dc;
        const val = buildSimPosition(parts.digits, dcInput && dcInput.value);
        const gidAttr = inp.getAttribute('data-grupo-id');
        const items = CDI.state.items || [];
        lastSnapshot = null;
        if (gidAttr) {
            const gid = parseInt(gidAttr, 10);
            items.forEach(it => { if (it.grupo_id === gid) it.pieza = val; });
        } else {
            const idx = parseInt(inp.getAttribute('data-row'), 10);
            if (!items[idx]) return;
            items[idx].pieza = val;
        }
        inp.classList.remove('is-error');
        if (dcInput) dcInput.classList.remove('is-error');
        updateSummary();
    }

    function onSimDcInput(ev) {
        const inp = ev.target;
        inp.value = String(inp.value || '').replace(/[^A-Za-z]/g, '').slice(0, 1).toUpperCase();
        const fields = inp.closest('.sim-position-fields');
        const simInput = fields && fields.querySelector('.ncm-input');
        if (!simInput) return;
        const val = buildSimPosition(simInput.value, inp.value);
        const items = CDI.state.items || [];
        const gidAttr = inp.getAttribute('data-grupo-id');
        if (gidAttr) {
            const gid = parseInt(gidAttr, 10);
            items.forEach(it => { if (it.grupo_id === gid) it.pieza = val; });
        } else {
            const idx = parseInt(inp.getAttribute('data-row'), 10);
            if (!items[idx]) return;
            items[idx].pieza = val;
        }
        inp.classList.remove('is-error');
        simInput.classList.remove('is-error');
        updateSummary();
    }

    function onNcmBlur(ev) {
        const inp = ev.target;
        const fields = inp.closest('.sim-position-fields');
        const simInput = fields && fields.querySelector('.ncm-input');
        const dcInput = fields && fields.querySelector('.sim-dc-input');
        if (!simInput || !dcInput) return;
        const val = buildSimPosition(simInput.value, dcInput.value);
        const gidAttr = inp.getAttribute('data-grupo-id');
        const items = CDI.state.items || [];
        let targetItems = [];
        if (gidAttr) {
            const gid = parseInt(gidAttr, 10);
            targetItems = items.filter(it => it.grupo_id === gid);
        } else {
            const idx = parseInt(inp.getAttribute('data-row'), 10);
            if (!items[idx]) return;
            targetItems = [items[idx]];
        }
        if (!targetItems.length) return;
        if (val && !isValidNcm(val)) {
            simInput.classList.add('is-error');
            dcInput.classList.add('is-error');
            if (CDI.toast) CDI.toast('Posición SIM incompleta', simErrorDetail(val), 'error');
            return;
        }
        simInput.classList.remove('is-error');
        dcInput.classList.remove('is-error');
        targetItems.forEach(it => { it.pieza = val; });
        if (val && isValidNcm(val) && targetItems[0].descripcion) {
            saveNcmUsage(targetItems[0].descripcion, val);
        }
        const tr = inp.closest('tr');
        if (tr) {
            tr.classList.toggle('row-ok', isValidNcm(val));
            tr.classList.toggle('row-pending', !isValidNcm(val));
        }
        updateSummary();
        if (val && isValidNcm(val)) render();
    }

    function onNcmKeydown(ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            const gidAttr = ev.target.getAttribute('data-grupo-id');
            if (gidAttr) return;
            const idx = parseInt(ev.target.getAttribute('data-row'), 10);
            openSpotlight(idx);
        }
    }

    function setItemField(idx, field, raw) {
        const items = CDI.state && CDI.state.items;
        if (!items || !items[idx]) return;
        const it = items[idx];
        let value = raw;
        if (field === 'origen') {
            value = getOriginCode(raw) || String(raw || '').trim();
        } else {
            const n = Number(raw);
            value = Number.isFinite(n) ? n : 0;
        }
        it[field] = value;
        return value;
    }

    function setGroupField(gid, field, raw) {
        const items = CDI.state && CDI.state.items;
        if (!items) return;
        let value = raw;
        if (field === 'origen') {
            value = getOriginCode(raw) || String(raw || '').trim();
        } else if (field === 'pieza') {
            value = String(raw || '').trim();
        } else {
            const n = Number(raw);
            value = Number.isFinite(n) ? n : 0;
        }
        items.forEach(it => {
            if (it.grupo_id === gid) it[field] = value;
        });
        return value;
    }

    function markFieldError(inp, isError) {
        if (isError) inp.classList.add('is-error');
        else inp.classList.remove('is-error');
    }

    function onFieldInput(ev) {
        const inp = ev.target;
        if (!inp) return;
        const field = inp.getAttribute('data-field');
        if (!field) return;
        const gidAttr = inp.getAttribute('data-grupo-id');

        lastSnapshot = null;

        if (field === 'origen') {
            const val = inp.value.trim();
            markFieldError(inp, val.length >= 2 && !getOriginCode(val));
        }

        if (gidAttr) {
            const gid = parseInt(gidAttr, 10);
            setGroupField(gid, field, inp.value);
        } else {
            const idx = parseInt(inp.getAttribute('data-row'), 10);
            if (isNaN(idx)) return;
            setItemField(idx, field, inp.value);
        }
        updateSummary();
    }

    function onFieldBlur(ev) {
        const inp = ev.target;
        if (!inp) return;
        const field = inp.getAttribute('data-field');
        if (!field) return;
        const gidAttr = inp.getAttribute('data-grupo-id');

        let finalValue;
        if (gidAttr) {
            const gid = parseInt(gidAttr, 10);
            finalValue = setGroupField(gid, field, inp.value);
        } else {
            const idx = parseInt(inp.getAttribute('data-row'), 10);
            if (isNaN(idx)) return;
            finalValue = setItemField(idx, field, inp.value);
        }
        if (field === 'origen') {
            const countryCode = getOriginCode(finalValue);
            inp.value = countryCode ? getOriginLabel(countryCode) : (finalValue || '');
            markFieldError(inp, !countryCode && finalValue.length > 0);
            if (!countryCode && finalValue.length > 0) {
                if (CDI.toast) CDI.toast('Origen no reconocido', 'Elegí un país de la tabla MARIA, por ejemplo 310 · CHINA.', 'warning');
            }
        }
        updateSummary();
    }

    function onFieldKeydown(ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            ev.target.blur();
            const idx = parseInt(ev.target.getAttribute('data-row'), 10);
            const field = ev.target.getAttribute('data-field');
            const next = ev.target.closest('tr') && ev.target.closest('tr').nextElementSibling;
            if (next) {
                const nextInput = next.querySelector('.ncm-edit[data-field="' + field + '"]');
                if (nextInput) nextInput.focus();
            }
        }
    }

    function isValidNcm(v) {
        // Para generar MARIA no alcanza con la NCM de 8 dígitos: se exige
        // posición SIM completa (NCM 8 + detalle SIM 3) y DC de una letra.
        const norm = String(v || '').replace(/[.\s]/g, '').toUpperCase();
        return /^\d{11}[A-Z]$/.test(norm);
    }

    // Tolerancia para mientras el usuario tipea en el spotlight (todavia
    // no termino de escribir el codigo): 4-11 digitos y DC opcional.
    function isPartialNcm(v) {
        const norm = String(v || '').replace(/[.\s]/g, '');
        return /^\d{4,11}[A-Za-z]?$/.test(norm);
    }

    /* ---------- Spotlight ---------- */
    function openSpotlight(idx) {
        const items = CDI.state.items || [];
        if (!items[idx]) return;
        spotActiveIdx = idx;
        const it = items[idx];
        spotItemRef.textContent = it.codigo_parte || ('Item ' + (idx + 1));
        spotItemDesc.textContent = it.descripcion || '';

        const total = items.length;
        spotProgress.textContent = 'Item ' + (idx + 1) + ' de ' + total;

        spotSearch.value = (it.pieza || '').trim();
        spotLastQuery = '';
        spotSuggestions = [];
        spotSelectedSugIdx = 0;
        overlay.hidden = false;
        hideVucePreview();
        renderSpotLoading();
        // Prefetch sugerencias con la descripcion del item
        fetchSuggestions(it.descripcion || '', /* initial */ true);
        // Si ya hay un NCM asignado, mostrar preview VUCE de ese codigo
        const initialNcm = String(it.pieza || '').replace(/\D/g, '');
        if (initialNcm.length >= 6) scheduleVucePreview(initialNcm.slice(0, 8));
        setTimeout(() => {
            spotSearch.focus();
            try { spotSearch.select(); } catch (_) {}
        }, 30);
        CDI.track('ncm_spotlight_opened', { row: idx });
    }

    function closeSpotlight() {
        const prevIdx = spotActiveIdx;
        if (overlay.hidden) return;
        overlay.classList.add('is-closing');
        setTimeout(() => {
            overlay.hidden = true;
            overlay.classList.remove('is-closing');
        }, 160);
        spotActiveIdx = -1;
        hideVucePreview();
        clearTimeout(vuceDebounce);
        vuceLastNcm = '';
        // Devolver foco al input de la fila que abrio el spotlight, para
        // accesibilidad y para que se pueda seguir tabulando sin saltar al body.
        if (prevIdx >= 0) {
            const sel = 'input.ncm-input[data-row="' + prevIdx + '"]';
            const inp = tbody && tbody.querySelector(sel);
            if (inp) {
                try { inp.focus({ preventScroll: false }); } catch (_) { inp.focus(); }
            }
        }
    }

    function onSpotInput() {
        const q = spotSearch.value.trim();
        clearTimeout(spotSearchDebounce);
        spotSearchDebounce = setTimeout(() => {
            if (q === spotLastQuery) return;
            spotLastQuery = q;
            if (q.length === 0) {
                // Volver a sugerencias iniciales (con descripcion del item)
                const it = (CDI.state.items || [])[spotActiveIdx] || {};
                fetchSuggestions(it.descripcion || '', true);
                hideVucePreview();
            } else if (q.length >= 3 && !isPartialNcm(q)) {
                fetchSuggestions(q, false);
                hideVucePreview();
            } else if (isPartialNcm(q)) {
                // El usuario esta tipeando un NCM directo: ofrecer asignar ese
                renderDirectCode(q);
                // Si tiene 6+ digitos, consultar VUCE para mostrar descripcion oficial y alicuotas
                const clean = String(q).replace(/\D/g, '');
                if (clean.length >= 6) scheduleVucePreview(clean.slice(0, 8));
                else hideVucePreview();
            } else {
                renderSpotEmpty('Escribí al menos 3 caracteres o un código NCM.');
                hideVucePreview();
            }
        }, 220);
    }

    function onSpotKeydown(ev) {
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            moveSpotSelection(1);
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            moveSpotSelection(-1);
        } else if (ev.key === 'Enter') {
            ev.preventDefault();
            confirmSpotSelection();
        }
    }

    function onSpotResultClick(ev) {
        const el = ev.target.closest('.spotlight-item');
        if (!el) return;
        const i = parseInt(el.getAttribute('data-idx'), 10);
        if (!isFinite(i)) return;
        spotSelectedSugIdx = i;
        confirmSpotSelection();
    }

    function moveSpotSelection(delta) {
        if (!spotSuggestions.length) return;
        spotSelectedSugIdx = (spotSelectedSugIdx + delta + spotSuggestions.length) % spotSuggestions.length;
        rerenderSpotSelection();
    }

    function rerenderSpotSelection() {
        spotResults.querySelectorAll('.spotlight-item').forEach(el => {
            const i = parseInt(el.getAttribute('data-idx'), 10);
            el.classList.toggle('is-selected', i === spotSelectedSugIdx);
            if (i === spotSelectedSugIdx) {
                el.scrollIntoView({ block: 'nearest' });
            }
        });
    }

    function confirmSpotSelection() {
        let chosen = null;
        const q = spotSearch.value.trim();
        if (spotSuggestions.length && spotSelectedSugIdx >= 0 && spotSelectedSugIdx < spotSuggestions.length) {
            chosen = spotSuggestions[spotSelectedSugIdx];
        } else if (isValidNcm(q)) {
            chosen = { ncm: (CDI.formatNcm ? CDI.formatNcm(q) : q), desc: '', source: 'manual' };
        } else {
            return;
        }
        applyNcmToActiveRow(chosen);
    }

    function applyNcmToActiveRow(sugg) {
        const items = CDI.state.items || [];
        const it = items[spotActiveIdx];
        if (!it || !sugg || !sugg.ncm) return;
        const ncmFmt = CDI.formatNcm ? CDI.formatNcm(sugg.ncm) : sugg.ncm;
        if (!isValidNcm(ncmFmt)) {
            spotSearch.value = ncmFmt;
            const clean = String(ncmFmt).replace(/\D/g, '');
            if (clean.length >= 8) scheduleVucePreview(clean.slice(0, 8));
            if (CDI.toast) CDI.toast('Falta la posición SIM', 'La sugerencia identifica la NCM de 8 dígitos. Elegí abajo la posición SIM completa con su DC.', 'info');
            return;
        }
        it.pieza = ncmFmt;
        // Guardamos la fuente del dato enriquecido si ya la tenemos cacheada.
        // Sirve para el banner "Datos de muestra" y para mostrar chips por fila.
        const cacheKey = String(ncmFmt).replace(/\D/g, '').slice(0, 8);
        const cached = vuceCache && vuceCache.get(cacheKey);
        if (cached) {
            it.ncm_source = sourceOf(cached);
        } else if (sugg.source) {
            it.ncm_source = sugg.source;
        }
        CDI.track('ncm_assigned', {
            row: spotActiveIdx,
            ncm: ncmFmt,
            source: sugg.source || 'manual',
            data_source: it.ncm_source || 'unknown'
        });
        if (it.descripcion) saveNcmUsage(it.descripcion, ncmFmt);

        // Hint contextual: la primera vez que el user asigna un NCM,
        // le contamos que se va a guardar para [cliente] + [proveedor].
        try {
            if (CDI.hint) {
                const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;
                const op = (CDI.state && CDI.state.operacion) || {};
                const cliNombre = (cliente && cliente.nombre) ? cliente.nombre : 'el cliente activo';
                const provNombre = String(op.vendedor_nombre || '').trim() || 'el proveedor';
                CDI.hint('autocatalogo', {
                    title: '🧠 Memoria activada',
                    text: 'Guardamos este NCM para ' + cliNombre + ' · ' + provNombre +
                          '. En la próxima factura del mismo proveedor ya te lo sugerimos.',
                    cta: 'Entendido',
                });
            }
        } catch (_) {}

        const activeIdx = spotActiveIdx;
        closeSpotlight();
        render();

        // Devolver foco al boton de la fila recien asignada para que el despachante
        // decida cuando pasar al siguiente (sin cascadas automaticas).
        try {
            const btn = tbody && tbody.querySelector('[data-assist="' + activeIdx + '"]');
            if (btn) btn.focus();
        } catch (_) {}
    }

    /* ---------- Fetch sugerencias ---------- */
    async function fetchSuggestions(descripcion, isInitial) {
        if (!descripcion || descripcion.trim().length < 3) {
            renderSpotEmpty('Escribí al menos 3 caracteres para buscar.');
            return;
        }
        renderSpotLoading();
        try {
            const res = await CDI.api('/api/ncm/sugerir', {
                method: 'POST',
                body: JSON.stringify({ descripcion: descripcion })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                renderSpotEmpty('No se pudieron obtener sugerencias (' + res.status + ').');
                return;
            }
            spotSuggestions = (data && data.sugerencias) || [];
            spotSelectedSugIdx = spotSuggestions.length ? 0 : -1;
            renderSpotResults(isInitial);
        } catch (err) {
            console.error('[ncm.sugerir]', err);
            renderSpotEmpty('No se pudieron obtener sugerencias.');
        }
    }

    async function saveNcmUsage(descripcion, ncm) {
        try {
            await CDI.api('/api/ncm/guardar-uso', {
                method: 'POST',
                body: JSON.stringify({ descripcion: descripcion, ncm: ncm })
            });
        } catch (_) { /* best effort */ }
    }

    function renderSpotLoading() {
        spotResults.innerHTML =
            '<div class="spotlight-loading"><span class="spinner" aria-hidden="true"></span>' +
            '<span>Buscando sugerencias…</span></div>';
    }
    function renderSpotEmpty(msg) {
        spotSuggestions = [];
        spotSelectedSugIdx = -1;
        spotResults.innerHTML = '<div class="spotlight-empty">' + CDI.escapeHtml(msg || 'Sin coincidencias.') + '</div>';
    }
    function renderDirectCode(code) {
        const fmt = CDI.formatNcm ? CDI.formatNcm(code) : code;
        if (!isValidNcm(fmt)) {
            renderSpotEmpty('NCM identificada. Falta elegir la posición SIM completa (11 dígitos + DC).');
            return;
        }
        spotSuggestions = [{ ncm: fmt, desc: 'Asignar este código manualmente', source: 'manual' }];
        spotSelectedSugIdx = 0;
        renderSpotResults(false);
    }
    function renderSpotResults(initial) {
        if (!spotSuggestions.length) {
            renderSpotEmpty(initial
                ? 'Sin historial ni sugerencias para este ítem. Escribí para buscar.'
                : 'Sin coincidencias. Probá con otras palabras.'
            );
            return;
        }
        const groups = { historial: [], ia: [], manual: [] };
        spotSuggestions.forEach((s, i) => {
            const key = groups[s.source] ? s.source : 'ia';
            groups[key].push({ sug: s, idx: i });
        });
        const chunks = [];
        if (groups.historial.length) {
            chunks.push('<div class="spotlight-section-label">Tu historial</div>');
            groups.historial.forEach(e => chunks.push(renderSpotItem(e)));
        }
        if (groups.ia.length) {
            chunks.push('<div class="spotlight-section-label">Sugerencias de IA</div>');
            // Disclaimer: las sugerencias son orientativas. La responsabilidad
            // final del NCM es del despachante. Aparece solo cuando hay IA en
            // pantalla para no inflar la UI.
            chunks.push(
                '<div class="spotlight-ia-disclaimer">' +
                'Orientativas: contrastá con la mercadería y VUCE antes de asignar.' +
                '</div>'
            );
            groups.ia.forEach(e => chunks.push(renderSpotItem(e)));
        }
        if (groups.manual.length) {
            chunks.push('<div class="spotlight-section-label">Asignar manualmente</div>');
            groups.manual.forEach(e => chunks.push(renderSpotItem(e)));
        }
        spotResults.innerHTML = chunks.join('');
        rerenderSpotSelection();
    }
    function renderSpotItem(entry) {
        const s = entry.sug;
        const selected = entry.idx === spotSelectedSugIdx ? ' is-selected' : '';
        const meta = s.source === 'historial' && s.count
            ? 'Usado ' + s.count + ' vez' + (s.count > 1 ? 'es' : '') + ' en el historial'
            : (s.source === 'ia' ? 'Sugerencia IA' : (s.source === 'manual' ? 'Código ingresado' : ''));
        return (
            '<button type="button" class="spotlight-item' + selected + '"' +
                ' data-idx="' + entry.idx + '" role="option" tabindex="-1">' +
                '<span class="spotlight-item-code">' + CDI.escapeHtml((CDI.formatNcm ? CDI.formatNcm(s.ncm || '') : (s.ncm || ''))) + '</span>' +
                '<div class="spotlight-item-body">' +
                    '<div class="spotlight-item-title">' + CDI.escapeHtml(s.desc || '—') + '</div>' +
                    (meta ? '<div class="spotlight-item-meta">' + CDI.escapeHtml(meta) + '</div>' : '') +
                '</div>' +
            '</button>'
        );
    }

    /* ---------- Preview VUCE en el spotlight ---------- */
    function scheduleVucePreview(ncm) {
        clearTimeout(vuceDebounce);
        if (vuceCache.has(ncm)) {
            renderVucePreview(vuceCache.get(ncm));
            return;
        }
        showVuceLoading(ncm);
        vuceDebounce = setTimeout(() => fetchVucePreview(ncm), 320);
    }

    async function fetchVucePreview(ncm) {
        vuceLastNcm = ncm;
        try {
            const res = await CDI.api('/api/ncm/' + encodeURIComponent(ncm) + '/completo');
            if (!res.ok) {
                // 404 u otro: ocultamos sin ruido
                if (vuceLastNcm === ncm) hideVucePreview();
                return;
            }
            const data = await res.json();
            vuceCache.set(ncm, data);
            if (vuceLastNcm === ncm && !overlay.hidden) {
                renderVucePreview(data);
                const src = sourceOf(data);
                CDI.track('ncm_vuce_preview', { ncm: ncm, source: src });
                // Notificar al banner global (ver dashboard_v2.html)
                document.dispatchEvent(new CustomEvent('cdi:ncm-source', {
                    detail: { ncm: ncm, source: src }
                }));
            }
        } catch (_) {
            if (vuceLastNcm === ncm) hideVucePreview();
        }
    }

    function sourceOf(data) {
        if (!data) return 'unknown';
        return (data.source)
            || (data.metadata && data.metadata.source)
            || (data.metadata && data.metadata.modo_fake ? 'fake' : '')
            || (data.alicuotas && data.alicuotas.fuente)
            || 'unknown';
    }

    function sourceChipMeta(src) {
        const s = String(src || '').toLowerCase();
        if (s.startsWith('api:') || s === 'oficial' || s.indexOf('api_real') >= 0) {
            return { label: 'Oficial', cls: 'is-official', title: 'Datos oficiales VUCE' };
        }
        if (s.startsWith('scrape:')) {
            const origen = s.split(':')[1] || '';
            return { label: 'Mercado', cls: 'is-market', title: 'Datos de mercado (' + origen + ')' };
        }
        if (s === 'cache') {
            return { label: 'Caché', cls: 'is-cache', title: 'Último dato real disponible' };
        }
        if (s === 'fake' || s.indexOf('fake') >= 0) {
            return { label: 'Muestra', cls: 'is-sample', title: 'Datos de muestra (fuente no disponible)' };
        }
        return { label: s || 'N/A', cls: 'is-unknown', title: 'Fuente desconocida' };
    }

    function showVuceLoading(ncm) {
        if (!spotVuce) return;
        spotVuce.hidden = false;
        spotVuce.innerHTML =
            '<div class="spotlight-vuce-head">' +
                '<span class="spotlight-vuce-tag">VUCE</span>' +
                '<span class="spotlight-vuce-ncm">' + CDI.escapeHtml(ncm) + '</span>' +
                '<span class="spotlight-vuce-status">Consultando…</span>' +
            '</div>';
    }

    function hideVucePreview() {
        if (!spotVuce) return;
        spotVuce.hidden = true;
        spotVuce.innerHTML = '';
    }

    function renderVucePreview(data) {
        if (!spotVuce || !data) return;
        const ncm = data.ncm || '';
        const desc = data.descripcion_vuce || data.descripcion || '—';
        const ali = data.alicuotas || {};
        const src = sourceOf(data);
        const meta = sourceChipMeta(src);
        const licencias = Array.isArray(data.licencias) ? data.licencias.filter(l => l && l.requerida) : [];
        const alicuotaChips = [];
        if (ali.arancel_extrazona != null) alicuotaChips.push(renderChip('DI', pct(ali.arancel_extrazona)));
        if (ali.arancel_mercosur != null && Number(ali.arancel_mercosur) > 0) alicuotaChips.push(renderChip('MCS', pct(ali.arancel_mercosur)));
        if (ali.iva != null) alicuotaChips.push(renderChip('IVA', pct(ali.iva)));
        if (ali.estadistica != null) alicuotaChips.push(renderChip('Estad.', pct(ali.estadistica)));
        const licBlock = licencias.length
            ? '<div class="spotlight-vuce-lic">⚠️ ' + licencias.length + ' licencia' + (licencias.length > 1 ? 's' : '') + ' requerida' + (licencias.length > 1 ? 's' : '') + '</div>'
            : '';
        const staleBanner = renderStaleBanner(data);
        const simOptions = [];
        if (data.codigo_sim && isValidNcm(data.codigo_sim)) {
            simOptions.push({ codigo_sim: data.codigo_sim, descripcion: desc });
        }
        (Array.isArray(data.sim_alternativas) ? data.sim_alternativas : []).forEach(pos => {
            const code = typeof pos === 'string' ? pos : pos && pos.codigo_sim;
            if (code && isValidNcm(code) && !simOptions.some(x => x.codigo_sim === code)) {
                simOptions.push({ codigo_sim: code, descripcion: (pos && pos.descripcion) || '' });
            }
        });
        const simChooser = simOptions.length ?
            '<div class="spotlight-sim-chooser">' +
                '<label for="spotSimSelect">Posición SIM completa <span>11 dígitos + DC</span></label>' +
                '<div class="spotlight-sim-controls">' +
                    '<select id="spotSimSelect" class="input input-sm">' + simOptions.map(pos => {
                        const formatted = CDI.formatNcm ? CDI.formatNcm(pos.codigo_sim) : pos.codigo_sim;
                        const optionText = formatted + (pos.descripcion ? ' — ' + pos.descripcion : '');
                        return '<option value="' + CDI.escapeHtml(pos.codigo_sim) + '">' + CDI.escapeHtml(optionText) + '</option>';
                    }).join('') + '</select>' +
                    '<button type="button" class="btn btn-primary btn-sm" data-use-sim>Usar esta posición</button>' +
                '</div>' +
            '</div>' : '';
        spotVuce.hidden = false;
        spotVuce.innerHTML =
            '<div class="spotlight-vuce-head">' +
                '<span class="spotlight-vuce-tag">VUCE</span>' +
                '<span class="spotlight-vuce-ncm">' + CDI.escapeHtml(data.codigo_sim ? data.codigo_sim : ncm) + '</span>' +
                '<span class="source-chip ' + meta.cls + '" title="' + CDI.escapeHtml(meta.title) + '">' + CDI.escapeHtml(meta.label) + '</span>' +
            '</div>' +
            '<div class="spotlight-vuce-desc">' + CDI.escapeHtml(desc) + '</div>' +
            simChooser +
            (alicuotaChips.length ? '<div class="spotlight-vuce-chips">' + alicuotaChips.join('') + '</div>' : '') +
            staleBanner +
            licBlock;
    }

    function onVuceSimClick(ev) {
        const button = ev.target && ev.target.closest && ev.target.closest('[data-use-sim]');
        if (!button) return;
        const select = spotVuce && spotVuce.querySelector('#spotSimSelect');
        const codigo = select && select.value;
        if (!codigo || !isValidNcm(codigo)) return;
        applyNcmToActiveRow({ ncm: codigo, desc: '', source: 'vuce_oficial' });
    }

    // Renderiza un aviso "Datos con latencia de N" si el backend indica que
    // el payload vino de cache y tiene `cache_age_hours` alto. Para scrape,
    // marcamos a partir de 24h. Para api oficial, 72h. Para fake, nunca.
    function renderStaleBanner(data) {
        const meta = (data && data.metadata) || {};
        const src = String((data && data.source) || meta.source || '').toLowerCase();
        if (!meta.cache_hit) return '';
        if (src === 'fake' || !src) return '';
        const ageH = Number(meta.cache_age_hours);
        if (!isFinite(ageH) || ageH <= 0) return '';
        const threshold = src.startsWith('scrape:') ? 24 : 72;
        if (ageH < threshold) return '';
        const human = ageH < 24
            ? Math.round(ageH) + ' h'
            : Math.round(ageH / 24) + ' día' + (ageH >= 48 ? 's' : '');
        return '<div class="spotlight-vuce-stale" title="Refrescar desde el asistente NCM">' +
               'Datos con latencia de ' + CDI.escapeHtml(human) +
               '</div>';
    }

    function renderChip(label, value) {
        return '<span class="spotlight-vuce-chip"><span class="chip-label">' + CDI.escapeHtml(label) + '</span><span class="chip-value">' + CDI.escapeHtml(value) + '</span></span>';
    }

    function pct(n) {
        const num = Number(n);
        if (!isFinite(num)) return '—';
        // Mostrar entero si es entero, si no 1 decimal
        return (num % 1 === 0 ? num.toFixed(0) : num.toFixed(1)) + '%';
    }

    /* ---------- Continuar ---------- */
    function onContinue() {
        const items = CDI.state.items || [];
        if (items.length === 0) return;
        const missing = items.filter(it => !isValidNcm(it.pieza)).length;
        if (missing > 0) return;
        CDI.track('ncm_all_assigned', { items: items.length });
        CDI.goTo('validating', { fromNcm: true });
    }

    /* ---------- Back to review ---------- */
    document.addEventListener('click', (e) => {
        const t = e.target.closest('[data-action="go-review"]');
        if (t) { e.preventDefault(); CDI.goTo('review'); }
    });

    /* ---------- Importar planilla maestra NCM ---------- */
    let ncmImportInitialized = false;
    let ncmImportModal, ncmImportInput, ncmImportDropzone, ncmImportPickBtn, ncmImportFilenameEl;
    let ncmImportProgress, ncmImportResult, ncmImportCancel;

    function initNcmImport() {
        if (ncmImportInitialized) return;
        ncmImportModal     = document.getElementById('importNcmModal');
        ncmImportInput     = document.getElementById('importNcmFileInput');
        ncmImportDropzone  = document.getElementById('importNcmDropzone');
        ncmImportPickBtn   = document.getElementById('importNcmPickBtn');
        ncmImportFilenameEl = document.getElementById('importNcmFilename');
        ncmImportProgress  = document.getElementById('importNcmProgress');
        ncmImportResult    = document.getElementById('importNcmResult');
        ncmImportCancel    = document.getElementById('importNcmCancel');
        if (!ncmImportModal) return;

        if (ncmImportPickBtn) ncmImportPickBtn.addEventListener('click', () => ncmImportInput.click());
        if (ncmImportDropzone) {
            ncmImportDropzone.addEventListener('click', (e) => {
                if (e.target === ncmImportPickBtn) return;
                ncmImportInput.click();
            });
            ['dragenter', 'dragover'].forEach(evt =>
                ncmImportDropzone.addEventListener(evt, (e) => {
                    e.preventDefault(); e.stopPropagation();
                    ncmImportDropzone.classList.add('is-dragging');
                })
            );
            ['dragleave', 'drop'].forEach(evt =>
                ncmImportDropzone.addEventListener(evt, (e) => {
                    e.preventDefault(); e.stopPropagation();
                    ncmImportDropzone.classList.remove('is-dragging');
                })
            );
            ncmImportDropzone.addEventListener('drop', (e) => {
                const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
                if (file) handleNcmImportFile(file);
            });
        }
        if (ncmImportInput) {
            ncmImportInput.addEventListener('change', (e) => {
                const file = e.target.files && e.target.files[0];
                if (file) handleNcmImportFile(file);
                ncmImportInput.value = '';
            });
        }
        if (ncmImportCancel) ncmImportCancel.addEventListener('click', closeNcmImportModal);
        ncmImportModal.addEventListener('click', (e) => {
            if (e.target === ncmImportModal) closeNcmImportModal();
        });
        ncmImportInitialized = true;
    }

    function openNcmImportModal() {
        initNcmImport();
        if (!ncmImportModal) return;
        if (ncmImportResult) { ncmImportResult.hidden = true; ncmImportResult.innerHTML = ''; ncmImportResult.classList.remove('is-error'); }
        if (ncmImportFilenameEl) ncmImportFilenameEl.textContent = 'CSV · XLSX · XLS';
        ncmImportModal.hidden = false;
        requestAnimationFrame(() => ncmImportModal.classList.add('is-visible'));
        CDI.track && CDI.track('import_ncm_maestra_open');
    }

    function closeNcmImportModal() {
        if (!ncmImportModal) return;
        ncmImportModal.classList.remove('is-visible');
        setTimeout(() => { ncmImportModal.hidden = true; }, 220);
    }

    async function handleNcmImportFile(file) {
        if (!file) return;
        const name = file.name || '';
        const ok = /\.(csv|xlsx|xls)$/i.test(name);
        if (!ok) {
            showNcmImportError('Formato no soportado. Usá CSV, XLSX o XLS.');
            return;
        }
        if (ncmImportFilenameEl) ncmImportFilenameEl.textContent = name;
        if (ncmImportProgress) ncmImportProgress.hidden = false;
        if (ncmImportResult) { ncmImportResult.hidden = true; ncmImportResult.innerHTML = ''; ncmImportResult.classList.remove('is-error'); }

        const form = new FormData();
        form.append('file', file);

        try {
            const res = await CDI.api('/api/ncm/import-historial', { method: 'POST', body: form });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || ('Error ' + res.status));
            renderNcmImportResult(data);
            CDI.track && CDI.track('import_ncm_maestra_done', {
                importados: data.importados, duplicados: data.duplicados
            });
        } catch (err) {
            showNcmImportError(err.message || 'No se pudo importar');
        } finally {
            if (ncmImportProgress) ncmImportProgress.hidden = true;
        }
    }

    function renderNcmImportResult(d) {
        if (!ncmImportResult) return;
        const errCount = (d.errores || []).length;
        ncmImportResult.innerHTML =
            '<div class="import-result-stat"><span>Importados</span><strong>' + (d.importados || 0) + '</strong></div>' +
            '<div class="import-result-stat"><span>Duplicados actualizados</span><strong>' + (d.duplicados || 0) + '</strong></div>' +
            '<div class="import-result-stat"><span>Filas con error</span><strong>' + errCount + '</strong></div>' +
            (errCount ? '<div class="import-result-error">Primer error: fila ' +
                d.errores[0].fila + ' — ' + d.errores[0].error + '</div>' : '');
        ncmImportResult.hidden = false;
        ncmImportResult.classList.remove('is-error');
        if (CDI.toast) CDI.toast.success('Importación completa', (d.importados || 0) + ' NCMs cargados');
    }

    function showNcmImportError(msg) {
        if (!ncmImportResult) return;
        ncmImportResult.innerHTML = '<strong>Error:</strong> ' + CDI.escapeHtml(msg);
        ncmImportResult.classList.add('is-error');
        ncmImportResult.hidden = false;
    }

    // Listener del botón "Importar planilla NCM"
    document.addEventListener('click', (e) => {
        const btn = e.target.closest && e.target.closest('#ncmImportMaestraBtn');
        if (btn) { e.preventDefault(); openNcmImportModal(); }
    });

    CDI.registerScreen('ncm', {
        onEnter() { render(); },
        onLeave() {
            if (overlay && !overlay.hidden) closeSpotlight();
        }
    });

    document.addEventListener('DOMContentLoaded', init);
})();
