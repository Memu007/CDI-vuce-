/* ============================================================
   CDI v2 — Cliente Picker con búsqueda server-side (Plan 03)

   API:
     CDI.openClientePicker({
         title:      'Asignar a un cliente existente',
         subtitle:   'Buscá por nombre o CUIT',
         onSelect:   function(cliente) {...},
         onCancel:   function() {...},
         excludeIds: [],
     });

   Si el usuario escribe ≥2 caracteres, busca en /api/clientes/search.
   Si borra, vuelve a mostrar todos los clientes cacheados.
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};
    let activePicker = null;
    const DEBOUNCE_MS = 180;

    function escapeHtml(s) {
        if (CDI.escapeHtml) return CDI.escapeHtml(s);
        return String(s || '').replace(/[&<>"']/g, ch => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[ch]));
    }
    function fmtCuit(cuit) {
        if (!cuit) return '';
        return CDI.formatCuit ? CDI.formatCuit(cuit) : cuit;
    }
    function normalize(s) {
        return String(s || '').toLowerCase().trim();
    }

    function close(reason) {
        if (!activePicker) return;
        const { overlay, escHandler, opts } = activePicker;
        document.removeEventListener('keydown', escHandler, true);
        overlay.classList.remove('is-visible');
        setTimeout(() => { overlay.remove(); }, 200);
        activePicker = null;
        if (reason === 'cancel' && typeof opts.onCancel === 'function') {
            try { opts.onCancel(); } catch (_) {}
        }
    }

    async function loadAllClientes() {
        if (Array.isArray(CDI.clientesCache) && CDI.clientesCache.length) {
            return CDI.clientesCache.slice();
        }
        try {
            const res = await CDI.api('/api/clientes');
            const data = await res.json().catch(() => ({}));
            if (!res.ok) return [];
            const list = Array.isArray(data && data.clientes) ? data.clientes : [];
            CDI.clientesCache = list;
            return list.slice();
        } catch (_) {
            return [];
        }
    }

    async function searchServer(query) {
        try {
            const res = await CDI.api('/api/clientes/search?q=' + encodeURIComponent(query));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) return [];
            return Array.isArray(data && data.clientes) ? data.clientes : [];
        } catch (_) {
            return [];
        }
    }

    function renderRow(c, idx) {
        const nombre = escapeHtml(c.nombre || c.name || '—');
        const cuit = c.cuit ? '<span class="cp-row-cuit">' + escapeHtml(fmtCuit(c.cuit)) + '</span>' : '';
        return (
            '<button type="button" class="cp-row" data-idx="' + idx + '" role="option">' +
                '<span class="cp-row-name">' + nombre + '</span>' +
                cuit +
            '</button>'
        );
    }

    function renderList(visibles, listEl, emptyEl, query) {
        if (!visibles.length) {
            listEl.innerHTML = '';
            emptyEl.hidden = false;
            emptyEl.textContent = query
                ? 'Ningún cliente coincide con "' + query + '".'
                : 'Todavía no tenés clientes cargados.';
            return [];
        }
        emptyEl.hidden = true;
        listEl.innerHTML = visibles.map((c, i) => renderRow(c, i)).join('');
        return visibles;
    }

    CDI.openClientePicker = function (opts) {
        opts = opts || {};
        if (typeof opts.onSelect !== 'function') {
            console.warn('[cliente_picker] onSelect requerido');
            return;
        }
        if (activePicker) close('cancel');

        const overlay = document.createElement('div');
        overlay.className = 'cp-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.innerHTML = (
            '<div class="cp-backdrop"></div>' +
            '<div class="cp-modal">' +
                '<div class="cp-header">' +
                    '<div class="cp-header-text">' +
                        '<h3 class="cp-title">' + escapeHtml(opts.title || 'Elegí un cliente') + '</h3>' +
                        '<p class="cp-subtitle">' + escapeHtml(opts.subtitle || 'Buscá por nombre o CUIT') + '</p>' +
                    '</div>' +
                    '<button type="button" class="cp-close" aria-label="Cerrar">&times;</button>' +
                '</div>' +
                '<div class="cp-search-wrap">' +
                    '<input type="text" class="cp-search" placeholder="Buscar..." autocomplete="off" autofocus>' +
                '</div>' +
                '<div class="cp-list" role="listbox" aria-label="Lista de clientes"></div>' +
                '<div class="cp-empty" hidden>Cargando…</div>' +
                '<div class="cp-footer">' +
                    '<button type="button" class="btn btn-ghost btn-sm cp-cancel">Cancelar</button>' +
                '</div>' +
            '</div>'
        );
        document.body.appendChild(overlay);

        const listEl   = overlay.querySelector('.cp-list');
        const emptyEl  = overlay.querySelector('.cp-empty');
        const searchEl = overlay.querySelector('.cp-search');
        let currentVisible = [];
        let allClientes = [];
        let debounceTimer = null;
        let isLoading = false;

        emptyEl.hidden = false;
        emptyEl.textContent = 'Cargando clientes…';
        listEl.innerHTML = '';

        const escHandler = function (e) {
            if (e.key === 'Escape' || e.keyCode === 27) {
                e.stopPropagation();
                close('cancel');
            }
        };
        document.addEventListener('keydown', escHandler, true);

        activePicker = { overlay: overlay, escHandler: escHandler, opts: opts };
        requestAnimationFrame(() => overlay.classList.add('is-visible'));

        overlay.querySelector('.cp-backdrop').addEventListener('click', () => close('cancel'));
        overlay.querySelector('.cp-close').addEventListener('click', () => close('cancel'));
        overlay.querySelector('.cp-cancel').addEventListener('click', () => close('cancel'));

        listEl.addEventListener('click', (e) => {
            const row = e.target.closest('.cp-row');
            if (!row) return;
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const c = currentVisible[idx];
            if (!c) return;
            close('select');
            try { opts.onSelect(c); } catch (err) {
                console.error('[cliente_picker] onSelect error', err);
            }
        });

        function setLoading(flag) {
            isLoading = flag;
            if (flag) {
                emptyEl.hidden = false;
                emptyEl.textContent = 'Buscando…';
                listEl.innerHTML = '';
            }
        }

        async function applySearch(query) {
            const q = String(query || '').trim();
            if (debounceTimer) clearTimeout(debounceTimer);

            // Con menos de 2 caracteres y si tenemos cache, filtramos localmente.
            const useServer = q.length >= 2 || (q.length > 0 && !Array.isArray(allClientes) && allClientes.length === 0);

            if (!useServer) {
                currentVisible = renderList(
                    q
                        ? allClientes.filter(c => normalize(c.nombre || c.name).indexOf(normalize(q)) !== -1)
                        : allClientes,
                    listEl, emptyEl, q
                );
                return;
            }

            debounceTimer = setTimeout(async () => {
                setLoading(true);
                const found = await searchServer(q);
                currentVisible = renderList(found, listEl, emptyEl, q);
            }, DEBOUNCE_MS);
        }

        searchEl.addEventListener('input', () => applySearch(searchEl.value));

        // Cargar todos al abrir
        loadAllClientes().then(list => {
            const exclude = Array.isArray(opts.excludeIds) ? opts.excludeIds : [];
            allClientes = list.filter(c => exclude.indexOf(c.id) === -1);
            currentVisible = renderList(allClientes, listEl, emptyEl, '');
            searchEl.focus();
        });
    };
})();
