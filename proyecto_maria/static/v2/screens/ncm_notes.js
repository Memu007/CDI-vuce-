/* ============================================================
   CDI v2 — Modal de notas por NCM
   Cache simple por prefijo de 4 digitos + modal minimalista para
   agregar/editar/borrar notas. Expone:
     CDI.ncmNotes.prefetch(ncm)        -> Promise<string[]>  (cache-aware)
     CDI.ncmNotes.get(ncm)             -> string[] (cache)
     CDI.ncmNotes.invalidate(ncm)
     CDI.ncmNotes.open(ncm, opts)      -> abre el modal
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const cache = new Map(); // ncmKey -> array of string notes
    const inflight = new Map(); // ncmKey -> promise<string[]>

    let modal, overlay, closeBtn, closeFooterBtn, listEl, newInput, addBtn, errorEl, ncmLabel;
    let currentNcmKey = null;
    let initialized = false;

    function $(id) { return document.getElementById(id); }

    function prefix4(ncm) {
        if (!ncm) return '';
        const digits = String(ncm).replace(/\D/g, '');
        return digits.slice(0, 4);
    }

    function init() {
        if (initialized) return;
        modal = $('ncmNotesModal');
        overlay = $('ncmNotesOverlay');
        closeBtn = $('ncmNotesClose');
        closeFooterBtn = $('ncmNotesCloseFooter');
        listEl = $('nnList');
        newInput = $('nnNewInput');
        addBtn = $('nnAddBtn');
        errorEl = $('nnError');
        ncmLabel = $('nnNcmLabel');
        if (!modal) return;

        closeBtn.addEventListener('click', close);
        closeFooterBtn.addEventListener('click', close);
        overlay.addEventListener('click', close);

        addBtn.addEventListener('click', onAdd);
        newInput.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) {
                ev.preventDefault();
                onAdd();
            }
        });

        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Escape' && !modal.hidden) { close(); }
        });

        initialized = true;
    }

    /* ---------- API publica ---------- */
    async function prefetch(ncm) {
        const key = prefix4(ncm);
        if (!key) return [];
        if (cache.has(key)) return cache.get(key);
        if (inflight.has(key)) return inflight.get(key);
        const p = (async () => {
            try {
                const res = await CDI.api('/api/ncm/notas/' + encodeURIComponent(key));
                if (!res.ok) return [];
                const data = await res.json().catch(() => ({}));
                const notas = Array.isArray(data && data.notas) ? data.notas : [];
                cache.set(key, notas);
                return notas;
            } catch (_) {
                return [];
            } finally {
                inflight.delete(key);
            }
        })();
        inflight.set(key, p);
        return p;
    }

    function getCached(ncm) {
        return cache.get(prefix4(ncm)) || null;
    }

    function invalidate(ncm) {
        cache.delete(prefix4(ncm));
    }

    /* ---------- Modal ---------- */
    function open(ncm) {
        init();
        if (!modal) return;
        currentNcmKey = prefix4(ncm);
        if (!currentNcmKey) return;
        ncmLabel.textContent = currentNcmKey;
        clearError();
        newInput.value = '';
        overlay.hidden = false;
        modal.hidden = false;
        requestAnimationFrame(() => {
            overlay.classList.add('is-visible');
            modal.classList.add('is-open');
        });
        refreshList();
        CDI.track('ncm_notes_open', { ncm: currentNcmKey });
        setTimeout(() => newInput && newInput.focus(), 160);
    }

    function close() {
        if (!modal) return;
        overlay.classList.remove('is-visible');
        modal.classList.remove('is-open');
        setTimeout(() => {
            if (!modal.classList.contains('is-open')) {
                overlay.hidden = true;
                modal.hidden = true;
            }
        }, 220);
    }

    async function refreshList() {
        if (!listEl) return;
        listEl.innerHTML = '<li class="caption" style="color:var(--c-text-3);padding:var(--s-2) 0">Cargando…</li>';
        try {
            invalidate(currentNcmKey);
            const notas = await prefetch(currentNcmKey);
            renderList(notas);
            notifyPillsRefresh(currentNcmKey);
        } catch (err) {
            listEl.innerHTML = '<li class="caption" style="color:var(--c-error)">No se pudieron cargar las notas.</li>';
        }
    }

    function renderList(notas) {
        if (!notas || !notas.length) {
            listEl.innerHTML = '<li class="ncm-notes-empty caption">Sin notas todavía.</li>';
            return;
        }
        listEl.innerHTML = notas.map((n, i) => (
            '<li class="ncm-note-row" data-idx="' + i + '">' +
                '<div class="ncm-note-text" contenteditable="false" data-idx="' + i + '">' +
                    CDI.escapeHtml(n) +
                '</div>' +
                '<div class="ncm-note-actions">' +
                    '<button type="button" class="cliente-item-action" data-action="edit" data-idx="' + i + '" title="Editar">' +
                        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>' +
                    '</button>' +
                    '<button type="button" class="cliente-item-action is-delete" data-action="delete" data-idx="' + i + '" title="Eliminar">' +
                        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6"/></svg>' +
                    '</button>' +
                '</div>' +
            '</li>'
        )).join('');
        listEl.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', onRowAction);
        });
    }

    function onRowAction(ev) {
        const btn = ev.currentTarget;
        const action = btn.getAttribute('data-action');
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        if (!isFinite(idx)) return;
        if (action === 'delete') return onDelete(idx);
        if (action === 'edit') return onEditStart(idx, btn);
    }

    async function onAdd() {
        clearError();
        const val = String(newInput.value || '').trim();
        if (!val) { showError('Escribí una nota.'); newInput.focus(); return; }
        addBtn.disabled = true;
        addBtn.textContent = 'Guardando…';
        try {
            const res = await CDI.api('/api/ncm/notas', {
                method: 'POST',
                body: JSON.stringify({ ncm: currentNcmKey, nota: val })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || 'No se pudo guardar la nota');
            newInput.value = '';
            await refreshList();
            CDI.track('ncm_note_added', { ncm: currentNcmKey });
        } catch (err) {
            showError(String(err.message || err));
        } finally {
            addBtn.disabled = false;
            addBtn.textContent = 'Agregar nota';
        }
    }

    async function onDelete(idx) {
        const ok = window.confirm('¿Eliminar esta nota?');
        if (!ok) return;
        try {
            const res = await CDI.api(
                '/api/ncm/notas/' + encodeURIComponent(currentNcmKey) + '/' + idx,
                { method: 'DELETE' }
            );
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || 'No se pudo eliminar');
            }
            await refreshList();
        } catch (err) {
            showError(String(err.message || err));
        }
    }

    function onEditStart(idx, btn) {
        const row = btn.closest('.ncm-note-row');
        if (!row) return;
        const textEl = row.querySelector('.ncm-note-text');
        if (!textEl) return;
        const originalText = textEl.textContent;
        textEl.setAttribute('contenteditable', 'true');
        textEl.classList.add('is-editing');
        textEl.focus();
        // Seleccionar todo
        const range = document.createRange();
        range.selectNodeContents(textEl);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);

        function finish(commit) {
            textEl.setAttribute('contenteditable', 'false');
            textEl.classList.remove('is-editing');
            textEl.removeEventListener('keydown', onKey);
            textEl.removeEventListener('blur', onBlur);
            const newVal = String(textEl.textContent || '').trim();
            if (commit && newVal && newVal !== originalText) {
                saveEdit(idx, newVal).catch(err => {
                    textEl.textContent = originalText;
                    showError(String(err.message || err));
                });
            } else {
                textEl.textContent = originalText;
            }
        }
        function onKey(ev) {
            if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); finish(true); }
            else if (ev.key === 'Escape') { ev.preventDefault(); finish(false); }
        }
        function onBlur() { finish(true); }
        textEl.addEventListener('keydown', onKey);
        textEl.addEventListener('blur', onBlur);
    }

    async function saveEdit(idx, newText) {
        const res = await CDI.api(
            '/api/ncm/notas/' + encodeURIComponent(currentNcmKey) + '/' + idx,
            { method: 'PUT', body: JSON.stringify({ nota: newText }) }
        );
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'No se pudo actualizar');
        }
        await refreshList();
    }

    function showError(msg) {
        if (!errorEl) return;
        errorEl.textContent = msg;
        errorEl.hidden = false;
    }
    function clearError() {
        if (!errorEl) return;
        errorEl.textContent = '';
        errorEl.hidden = true;
    }

    function notifyPillsRefresh(ncmKey) {
        document.dispatchEvent(new CustomEvent('cdi:ncm-notes-changed', {
            detail: { ncm: ncmKey }
        }));
    }

    /* ---------- Public ---------- */
    CDI.ncmNotes = {
        prefetch,
        getCached,
        invalidate,
        open,
        close,
        prefix4
    };

    document.addEventListener('DOMContentLoaded', init);
})();
