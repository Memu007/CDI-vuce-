/* ============================================================
   CDI v2 - Screen Clientes (full-screen two-pane)
   Responsabilidad: CRUD minimo + historial + mapeo Excel.
   Registrado como screen via CDI.registerScreen('clientes').

   Exponemos:
     CDI.openClientesDrawer(opts)   -> alias a CDI.goTo('clientes', opts)
     CDI.closeClientesDrawer()      -> alias a CDI.goBack()
     CDI.getClientesCache()
     CDI.refreshClientes()
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    // -------- DOM refs (poblado en init) --------
    let screenEl, splitEl;
    let searchInput, helpBtn, newBtn;
    let listEl, loadingEl, emptyListEl;
    let emptySelectionEl, detailBodyEl, backBtn;
    let heroEl, kpiOps, kpiValor, kpiUltimo;
    let tabOps, tabMapeo, tabDatos, panelOps, panelMapeo, panelDatos;
    let opsList, opsEmpty;
    let mapeoList, mapeoEmpty, mapeoActions, mapeoReset, mapeoSave;
    let datosGrid;
    let filterChips = [], sortSelect;

    // Modal form refs
    let formModal, formShell, formClose, formCancel, formSave, formTitleEl, formError;
    let fNombre, fCuit, fDireccion, fEmail, fTelefono, fOrigen, fMoneda, fNotas, fFechaInicActiv, fAdvanced;

    // -------- Estado interno --------
    let clientes = [];
    let currentOps = [];
    let currentMapping = null;
    let mappingDraft = null;
    let activeTab = 'ops';
    let filterMode = 'all';          // 'all' | 'favs' | 'recent'
    let sortMode = 'alpha';          // 'alpha' | 'used' | 'value'
    let filterText = '';
    let loading = false;
    let initialized = false;
    let entered = false;

    let editingId = null;            // null = nuevo, string = edit
    let detailClienteId = null;
    let activeIndex = -1;            // indice del item "focuseado" por teclado en vista filtrada
    let visibleIds = [];             // ids en el orden renderizado (para flechas)
    let scrollToOpsNext = false;
    // Cuando entramos con openForm desde otra screen (p.ej. review "Guardar como cliente"),
    // al cerrar el form volvemos automaticamente a la screen previa.
    let autoReturnAfterForm = false;

    const ONLY_FAVS_KEY = 'cdi.v2.clientes.onlyFavs';

    function $(id) { return document.getElementById(id); }

    /* ==========================================================
       Init
       ========================================================== */
    function init() {
        if (initialized) return;
        screenEl       = document.querySelector('[data-screen="clientes"]');
        if (!screenEl) return;

        splitEl        = $('cxSplit');
        searchInput    = $('cxSearch');
        helpBtn        = $('cxHelpBtn');
        newBtn         = $('cxNewBtn');
        listEl         = $('cxList');
        loadingEl      = $('cxLoading');
        emptyListEl    = $('cxEmptyList');
        emptySelectionEl = $('cxEmptySelection');
        detailBodyEl   = $('cxDetailBody');
        backBtn        = $('cxBackBtn');
        heroEl         = $('cxHero');
        kpiOps         = $('cxKpiOps');
        kpiValor       = $('cxKpiValor');
        kpiUltimo      = $('cxKpiUltimo');
        tabOps         = $('cxTabOps');
        tabMapeo       = $('cxTabMapeo');
        tabDatos       = $('cxTabDatos');
        panelOps       = screenEl.querySelector('[data-panel="ops"]');
        panelMapeo     = screenEl.querySelector('[data-panel="mapeo"]');
        panelDatos     = screenEl.querySelector('[data-panel="datos"]');
        opsList        = $('cxOpsList');
        opsEmpty       = $('cxOpsEmpty');
        mapeoList      = $('cxMapeoList');
        mapeoEmpty     = $('cxMapeoEmpty');
        mapeoActions   = $('cxMapeoActions');
        mapeoReset     = $('cxMapeoReset');
        mapeoSave      = $('cxMapeoSave');
        datosGrid      = $('cxDatosGrid');
        filterChips    = Array.from(screenEl.querySelectorAll('.cx-chip[data-filter]'));
        sortSelect     = $('cxSort');

        formModal   = $('cxFormModal');
        formShell   = $('cxFormShell');
        formClose   = $('cxFormClose');
        formCancel  = $('cxFormCancel');
        formSave    = $('cxFormSave');
        formTitleEl = $('cxFormTitle');
        formError   = $('cfError');
        fNombre     = $('cfNombre');
        fCuit       = $('cfCuit');
        fDireccion  = $('cfDireccion');
        fEmail      = $('cfEmail');
        fTelefono   = $('cfTelefono');
        fOrigen     = $('cfOrigen');
        fMoneda     = $('cfMoneda');
        fNotas      = $('cfNotas');
        fFechaInicActiv = $('cfFechaInicActiv');
        fAdvanced   = $('cfAdvanced');

        // Restaurar "solo favoritos" de sesiones previas
        try {
            if (sessionStorage.getItem(ONLY_FAVS_KEY) === '1') filterMode = 'favs';
        } catch (_) {}

        // Search
        if (searchInput) {
            searchInput.addEventListener('input', (ev) => {
                filterText = String(ev.target.value || '').trim().toLowerCase();
                activeIndex = -1;
                renderList();
            });
        }

        // Filter chips (all/favs/recent)
        filterChips.forEach(chip => {
            chip.addEventListener('click', () => {
                const val = chip.getAttribute('data-filter') || 'all';
                setFilterMode(val);
            });
        });

        // Sort
        if (sortSelect) {
            sortSelect.addEventListener('change', (ev) => {
                sortMode = String(ev.target.value || 'alpha');
                renderList();
                CDI.track && CDI.track('clientes_sort_changed', { mode: sortMode });
            });
        }

        if (newBtn) newBtn.addEventListener('click', () => openForm());
        const emptyCreateBtn = $('cxEmptyCreateBtn');
        if (emptyCreateBtn) emptyCreateBtn.addEventListener('click', () => openForm());

        // Tabs
        if (tabOps)   tabOps.addEventListener('click', () => switchTab('ops'));
        if (tabMapeo) tabMapeo.addEventListener('click', () => switchTab('mapeo'));
        if (tabDatos) tabDatos.addEventListener('click', () => switchTab('datos'));
        if (mapeoReset) mapeoReset.addEventListener('click', resetMapping);
        if (mapeoSave)  mapeoSave.addEventListener('click', saveMapping);

        // Back (mobile)
        if (backBtn) backBtn.addEventListener('click', closeDetailMobile);

        // Modal
        if (formClose)  formClose.addEventListener('click', closeForm);
        if (formCancel) formCancel.addEventListener('click', closeForm);
        if (formSave)   formSave.addEventListener('click', submitForm);
        if (formModal) {
            // Click en backdrop cierra (click fuera del shell)
            formModal.addEventListener('click', (ev) => {
                if (ev.target === formModal) closeForm();
            });
            formModal.addEventListener('cancel', (ev) => {
                ev.preventDefault();
                closeForm();
            });
        }
        // Enter en inputs = guardar (excepto textarea)
        [fNombre, fCuit, fDireccion, fEmail, fTelefono].forEach(el => {
            if (!el) return;
            el.addEventListener('keydown', (ev) => {
                if (ev.key === 'Enter') { ev.preventDefault(); submitForm(); }
            });
        });

        // Delegacion en la lista
        if (listEl) {
            listEl.addEventListener('click', onListClick);
            listEl.addEventListener('dblclick', onListDblClick);
        }

        // Keyboard global (scoped a la screen)
        document.addEventListener('keydown', onGlobalKeydown);

        initialized = true;
    }

    /* ==========================================================
       Screen lifecycle
       ========================================================== */
    function onEnter(state) {
        init();
        if (!screenEl) return;
        entered = true;
        state = state || {};

        CDI.track && CDI.track('clientes_screen_open', {
            from: state && state.from ? state.from : undefined,
        });

        // Sync UI para filterMode inicial
        updateFilterChipsUI();
        if (sortSelect) sortSelect.value = sortMode;

        // Reset de seleccion visible al entrar
        detailClienteId = null;
        showEmptySelection();
        if (splitEl) splitEl.classList.remove('is-detail-open');

        refresh().then(() => {
            if (state.openForm) {
                autoReturnAfterForm = true;
                openForm(state.prefill || null);
            } else if (visibleIds.length > 0) {
                activeIndex = 0;
                highlightActive();
            }
        });

        // Focus diferido para no pelear con la transicion de screen
        setTimeout(() => { if (searchInput) searchInput.focus(); }, 220);
    }

    function onLeave() {
        entered = false;
        // Cerrar modal si quedo abierto
        closeForm();
    }

    /* ==========================================================
       API
       ========================================================== */
    async function refresh() {
        if (loading) return;
        loading = true;
        showLoading(true);
        try {
            const res = await CDI.api('/api/clientes');
            const data = await res.json();
            if (!res.ok || !data.success) {
                throw new Error((data && data.detail) || 'No se pudo cargar la lista');
            }
            clientes = Array.isArray(data.clientes) ? data.clientes : [];
            CDI.clientesCache = clientes;
            const activo = CDI.getClienteActivo();
            if (activo && !clientes.find(c => c.id === activo.id)) {
                CDI.setClienteActivo(null);
            }
            renderList();
        } catch (err) {
            console.error('[clientes] refresh', err);
            CDI.toast && CDI.toast.error('Error', String(err && err.message || err));
        } finally {
            loading = false;
            showLoading(false);
        }
    }

    function showLoading(flag) {
        if (!loadingEl) return;
        loadingEl.hidden = !flag;
        if (flag) {
            if (listEl) listEl.hidden = true;
            if (emptyListEl) emptyListEl.hidden = true;
        }
    }

    async function createCliente(body) {
        const res = await CDI.api('/api/clientes', { method: 'POST', body: JSON.stringify(body) });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || 'No se pudo crear el cliente');
        CDI.track && CDI.track('cliente_created');
        return data;
    }

    async function updateCliente(id, body) {
        const res = await CDI.api('/api/clientes/' + encodeURIComponent(id), {
            method: 'PUT', body: JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || 'No se pudo actualizar el cliente');
        CDI.track && CDI.track('cliente_updated', { id });
        return data;
    }

    async function deleteCliente(id) {
        const res = await CDI.api('/api/clientes/' + encodeURIComponent(id), { method: 'DELETE' });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'No se pudo eliminar');
        }
        CDI.track && CDI.track('cliente_deleted', { id });
    }

    async function toggleFavorito(id) {
        const res = await CDI.api('/api/clientes/' + encodeURIComponent(id) + '/favorito', { method: 'POST' });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'No se pudo marcar favorito');
        }
        CDI.track && CDI.track('cliente_fav_toggled', { id });
    }

    /* ==========================================================
       Filtros + orden
       ========================================================== */
    function setFilterMode(mode) {
        filterMode = ['all', 'favs', 'recent'].indexOf(mode) >= 0 ? mode : 'all';
        try { sessionStorage.setItem(ONLY_FAVS_KEY, filterMode === 'favs' ? '1' : '0'); } catch (_) {}
        activeIndex = -1;
        updateFilterChipsUI();
        renderList();
        CDI.track && CDI.track('clientes_filter_changed', { mode: filterMode });
    }

    function updateFilterChipsUI() {
        filterChips.forEach(chip => {
            const active = chip.getAttribute('data-filter') === filterMode;
            chip.classList.toggle('is-active', active);
            chip.setAttribute('aria-selected', active ? 'true' : 'false');
        });
    }

    function applyTextFilter(list, q) {
        if (!q) return list.slice();
        const norm = q.toLowerCase();
        const normDig = q.replace(/\D/g, '');
        return list.filter(c => {
            const nombre = (c.nombre || '').toLowerCase();
            const cuit = CDI.normalizeCuit ? CDI.normalizeCuit(c.cuit) : String(c.cuit || '');
            return nombre.indexOf(norm) !== -1 || (normDig && cuit.indexOf(normDig) !== -1);
        });
    }

    function applyModeFilter(list) {
        if (filterMode === 'favs') return list.filter(c => c.favorito);
        if (filterMode === 'recent') {
            const now = Date.now();
            const thirtyDays = 30 * 24 * 60 * 60 * 1000;
            return list
                .filter(c => c.ultimo && (now - new Date(c.ultimo).getTime()) <= thirtyDays)
                .sort((a, b) => new Date(b.ultimo).getTime() - new Date(a.ultimo).getTime());
        }
        return list;
    }

    function applySort(list) {
        const copy = list.slice();
        if (sortMode === 'used') {
            copy.sort((a, b) => (Number(b.ops_count || 0) - Number(a.ops_count || 0)));
        } else if (sortMode === 'value') {
            copy.sort((a, b) => (Number(b.valor_total || 0) - Number(a.valor_total || 0)));
        } else {
            copy.sort((a, b) => String(a.nombre || '').localeCompare(String(b.nombre || ''), 'es', { sensitivity: 'base' }));
        }
        return copy;
    }

    /* ==========================================================
       Render lista
       ========================================================== */
    let _emptyListOriginalHTML = null;

    function _restoreEmptyListOriginal() {
        if (!emptyListEl) return;
        if (_emptyListOriginalHTML === null) {
            _emptyListOriginalHTML = emptyListEl.innerHTML;
        } else {
            emptyListEl.innerHTML = _emptyListOriginalHTML;
            const btn = $('cxEmptyCreateBtn');
            if (btn) btn.addEventListener('click', () => openForm());
        }
    }

    function renderList() {
        if (!listEl) return;

        if (clientes.length === 0) {
            listEl.hidden = true;
            if (emptyListEl) {
                _restoreEmptyListOriginal();
                emptyListEl.hidden = false;
            }
            visibleIds = [];
            return;
        }

        let base = applyTextFilter(clientes, filterText);
        base = applyModeFilter(base);
        base = applySort(base);

        if (base.length === 0) {
            if (emptyListEl) {
                emptyListEl.hidden = false;
                emptyListEl.innerHTML = '<p>' + (filterText
                    ? 'Sin resultados para "' + CDI.escapeHtml(filterText) + '".'
                    : (filterMode === 'favs'
                        ? 'No hay clientes favoritos.'
                        : 'Sin resultados para el filtro actual.')) + '</p>';
            }
            listEl.hidden = true;
            visibleIds = [];
            return;
        }

        if (emptyListEl) emptyListEl.hidden = true;
        listEl.hidden = false;

        // Agrupamos por fav + resto solo cuando no hay busqueda/filtro que aplique orden distinto
        const rows = [];
        const usarGrupos = !filterText && sortMode === 'alpha' && filterMode === 'all';

        if (usarGrupos) {
            const favs = base.filter(c => c.favorito);
            const others = base.filter(c => !c.favorito);
            if (favs.length) {
                rows.push('<li class="cx-list-section" role="presentation">Favoritos</li>');
                favs.forEach(c => rows.push(renderCard(c)));
            }
            if (others.length) {
                if (favs.length) rows.push('<li class="cx-list-section" role="presentation">Todos</li>');
                others.forEach(c => rows.push(renderCard(c)));
            }
        } else {
            base.forEach(c => rows.push(renderCard(c)));
        }

        listEl.innerHTML = rows.join('');
        visibleIds = base.map(c => c.id);

        // Restaurar seleccion si el cliente sigue visible
        if (detailClienteId && visibleIds.indexOf(detailClienteId) === -1) {
            detailClienteId = null;
            showEmptySelection();
        } else if (detailClienteId) {
            markSelectedCard(detailClienteId);
        }

        // Reposicionar activeIndex si quedo fuera de rango
        if (activeIndex >= visibleIds.length) activeIndex = visibleIds.length - 1;
    }

    function initials(name) {
        const s = String(name || '').trim();
        if (!s) return '?';
        const parts = s.split(/\s+/).slice(0, 2);
        return parts.map(p => p.charAt(0).toUpperCase()).join('') || '?';
    }

    function renderCard(c) {
        const isSelected = detailClienteId === c.id;
        const fav = !!c.favorito;
        const cuitFmt = c.cuit && CDI.formatCuit ? CDI.formatCuit(c.cuit) : (c.cuit || '');
        const ops = Number(c.ops_count || 0);
        const metaParts = [];
        if (cuitFmt) metaParts.push(CDI.escapeHtml(cuitFmt));
        if (ops > 0) metaParts.push(ops + (ops === 1 ? ' op' : ' ops'));
        const meta = metaParts.join(' · ');
        const star = fav ? '★' : '☆';
        return (
            '<li class="cx-card' +
                (isSelected ? ' is-selected' : '') +
                (fav ? ' is-favorite' : '') +
                '" data-cliente-id="' + CDI.escapeHtml(c.id) + '" ' +
                'role="option" aria-selected="' + (isSelected ? 'true' : 'false') + '" ' +
                'tabindex="-1">' +
                '<div class="cx-card-avatar" aria-hidden="true">' + CDI.escapeHtml(initials(c.nombre)) + '</div>' +
                '<div class="cx-card-body">' +
                    '<div class="cx-card-title">' +
                        '<span>' + CDI.escapeHtml(c.nombre || '') + '</span>' +
                        '<span class="cx-card-fav" data-action="fav" role="button" aria-label="' +
                            (fav ? 'Quitar de favoritos' : 'Marcar como favorito') +
                            '" title="' + (fav ? 'Quitar favorito' : 'Favorito') + '">' + star + '</span>' +
                    '</div>' +
                    (meta ? '<div class="cx-card-meta">' + meta + '</div>' : '') +
                '</div>' +
            '</li>'
        );
    }

    function markSelectedCard(id) {
        if (!listEl) return;
        listEl.querySelectorAll('.cx-card').forEach(li => {
            const match = li.getAttribute('data-cliente-id') === id;
            li.classList.toggle('is-selected', match);
            li.setAttribute('aria-selected', match ? 'true' : 'false');
        });
    }

    function highlightActive() {
        if (!listEl) return;
        const cards = Array.from(listEl.querySelectorAll('.cx-card'));
        cards.forEach((li, idx) => {
            if (idx === activeIndex) {
                li.classList.add('is-keyboard-focus');
                try { li.scrollIntoView({ block: 'nearest' }); } catch (_) {}
            } else {
                li.classList.remove('is-keyboard-focus');
            }
        });
        if (listEl && activeIndex >= 0 && visibleIds[activeIndex]) {
            listEl.setAttribute('aria-activedescendant', 'cx-card-' + activeIndex);
        } else {
            listEl.removeAttribute('aria-activedescendant');
        }
    }

    /* ==========================================================
       List events
       ========================================================== */
    function onListClick(ev) {
        const actionEl = ev.target.closest('[data-action]');
        const cardEl = ev.target.closest('.cx-card');
        if (!cardEl) return;
        const id = cardEl.getAttribute('data-cliente-id');
        if (!id) return;

        if (actionEl) {
            const action = actionEl.getAttribute('data-action');
            if (action === 'fav') {
                ev.stopPropagation();
                onFavClick(id);
                return;
            }
        }
        selectCliente(id);
    }

    function onListDblClick(ev) {
        const cardEl = ev.target.closest('.cx-card');
        if (!cardEl) return;
        const id = cardEl.getAttribute('data-cliente-id');
        if (!id) return;
        const c = clientes.find(x => x.id === id);
        if (!c) return;
        selectCliente(id);
    }

    function selectCliente(id) {
        if (!id) return;
        const c = clientes.find(x => x.id === id);
        if (!c) return;
        detailClienteId = id;
        markSelectedCard(id);
        if (splitEl) splitEl.classList.add('is-detail-open');
        hideEmptySelection();
        renderDetail(c);
        CDI.track && CDI.track('clientes_card_selected', { id: id });
    }

    function showEmptySelection() {
        if (emptySelectionEl) emptySelectionEl.hidden = false;
        if (detailBodyEl) detailBodyEl.hidden = true;
    }
    function hideEmptySelection() {
        if (emptySelectionEl) emptySelectionEl.hidden = true;
        if (detailBodyEl) detailBodyEl.hidden = false;
    }

    function closeDetailMobile() {
        if (splitEl) splitEl.classList.remove('is-detail-open');
        detailClienteId = null;
        showEmptySelection();
        markSelectedCard(null);
    }

    /* ==========================================================
       Detail
       ========================================================== */
    function renderDetail(c) {
        renderHero(c);
        renderKpis(null);
        renderOps(null);
        renderMapping(null);
        renderDatos(c);
        currentMapping = null;
        mappingDraft = null;
        switchTab('ops');
        if (scrollToOpsNext) {
            scrollToOpsNext = false;
            setTimeout(() => {
                if (opsList) try { opsList.scrollIntoView({ block: 'nearest' }); } catch (_) {}
            }, 120);
        }
        loadDetailData(c.id);
    }

    function renderHero(c) {
        if (!heroEl) return;
        const cuit = c.cuit && CDI.formatCuit ? CDI.formatCuit(c.cuit) : (c.cuit || '');
        const tags = [];
        if (c.favorito) tags.push('<span class="cx-hero-tag is-favorite">★ Favorito</span>');
        if (c.default_origin) tags.push('<span class="cx-hero-tag">Origen ' + CDI.escapeHtml(c.default_origin) + '</span>');
        if (c.preferred_currency) tags.push('<span class="cx-hero-tag">' + CDI.escapeHtml(c.preferred_currency) + '</span>');

        const metaParts = [];
        if (cuit) metaParts.push(CDI.escapeHtml(cuit));
        if (c.direccion) metaParts.push(CDI.escapeHtml(c.direccion));

        heroEl.innerHTML = (
            '<div class="cx-hero-avatar" aria-hidden="true">' + CDI.escapeHtml(initials(c.nombre)) + '</div>' +
            '<div class="cx-hero-body">' +
                '<h2 class="cx-hero-title">' +
                    '<span>' + CDI.escapeHtml(c.nombre || '') + '</span>' +
                    (tags.length ? '<span class="cx-hero-tags">' + tags.join('') + '</span>' : '') +
                '</h2>' +
                (metaParts.length ? '<p class="cx-hero-meta">' + metaParts.join(' · ') + '</p>' : '') +
            '</div>' +
            '<div class="cx-hero-actions">' +
                '<div class="cx-kebab-wrap" id="cxKebabWrap">' +
                    '<button type="button" class="cx-kebab-btn" id="cxKebabBtn" aria-haspopup="menu" aria-label="Más acciones">' +
                        '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="12" r="1.8"/></svg>' +
                    '</button>' +
                    '<div class="cx-kebab-menu" id="cxKebabMenu" role="menu">' +
                        '<button type="button" class="cx-kebab-item" data-kaction="edit" role="menuitem">Editar</button>' +
                        '<button type="button" class="cx-kebab-item" data-kaction="fav" role="menuitem">' +
                            (c.favorito ? 'Quitar favorito' : 'Marcar favorito') + '</button>' +
                        '<div class="cx-kebab-sep"></div>' +
                        '<button type="button" class="cx-kebab-item" data-kaction="csv" role="menuitem">Descargar CSV</button>' +
                        '<button type="button" class="cx-kebab-item" data-kaction="template" role="menuitem">Descargar plantilla Excel</button>' +
                        '<div class="cx-kebab-sep"></div>' +
                        '<button type="button" class="cx-kebab-item is-danger" data-kaction="delete" role="menuitem">Eliminar cliente</button>' +
                    '</div>' +
                '</div>' +
            '</div>'
        );

        const kebabBtn = $('cxKebabBtn');
        const kebabMenu = $('cxKebabMenu');
        if (kebabBtn && kebabMenu) {
            kebabBtn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                kebabMenu.classList.toggle('is-open');
            });
            kebabMenu.addEventListener('click', (ev) => {
                const btn = ev.target.closest('[data-kaction]');
                if (!btn) return;
                kebabMenu.classList.remove('is-open');
                const action = btn.getAttribute('data-kaction');
                if (action === 'edit')      onEditCurrent();
                else if (action === 'fav')  onFavClick(c.id);
                else if (action === 'csv')  onCsvClick(c.id);
                else if (action === 'template') { detailClienteId = c.id; downloadTemplate(); }
                else if (action === 'delete') onDeleteClick(c.id);
            });
            document.addEventListener('click', () => kebabMenu.classList.remove('is-open'), { once: true });
        }
    }

    function renderKpis(metricas) {
        if (!kpiOps) return;
        if (!metricas) {
            kpiOps.textContent = '—';
            kpiValor.textContent = '—';
            kpiUltimo.textContent = '—';
            return;
        }
        kpiOps.textContent = String(metricas.total_operaciones || 0);
        const v = Number(metricas.valor_total || 0);
        kpiValor.textContent = v > 0 ? formatMoney(v) : '—';
        kpiUltimo.textContent = metricas.ultimo_movimiento || '—';
    }

    function formatMoney(v) {
        if (v >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M';
        if (v >= 1e3) return '$' + (v / 1e3).toFixed(1) + 'k';
        return '$' + Math.round(v);
    }

    function renderOps(operaciones) {
        if (!opsList || !opsEmpty) return;
        if (operaciones == null) {
            currentOps = [];
            opsList.innerHTML = '<li class="caption" style="padding: var(--s-2) 0; color: var(--c-text-3);">Cargando…</li>';
            opsEmpty.hidden = true;
            return;
        }
        currentOps = operaciones.slice();
        if (!operaciones.length) {
            opsList.innerHTML = '';
            opsEmpty.hidden = false;
            return;
        }
        opsEmpty.hidden = true;
        const downloadIcon =
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
                '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>' +
                '<polyline points="7 10 12 15 17 10"/>' +
                '<line x1="12" y1="15" x2="12" y2="3"/>' +
            '</svg>';
        opsList.innerHTML = operaciones.map(op => {
            const fecha = op.fecha ? new Date(op.fecha).toLocaleDateString('es-AR') : '—';
            const items = Number(op.total_items || 0);
            const val = Number(op.total_value || 0);
            const currency = op.currency || 'USD';
            const label = op.op_code || op.generated_file || op.id || 'Operación';
            const dlHref = op.generated_file ? '/download/' + encodeURIComponent(op.generated_file) : '';
            const dlBtn = dlHref
                ? '<a class="cx-ops-download" href="' + dlHref + '" data-action="download" data-op-id="' + CDI.escapeHtml(op.id || '') + '" download title="Descargar TXT">' + downloadIcon + '</a>'
                : '<span class="cx-ops-download" aria-disabled="true" title="Sin archivo generado">' + downloadIcon + '</span>';
            return (
                '<li class="cx-ops-item">' +
                    '<span class="cx-ops-date">' + CDI.escapeHtml(fecha) + '</span>' +
                    '<span class="cx-ops-meta"><strong>' + CDI.escapeHtml(label) + '</strong> · ' + items + ' ítems</span>' +
                    '<span class="cx-ops-value">' + (val > 0 ? formatMoney(val) + ' ' + currency : '—') + '</span>' +
                    dlBtn +
                '</li>'
            );
        }).join('');

        opsList.querySelectorAll('a.cx-ops-download[data-action="download"]').forEach(a => {
            a.addEventListener('click', () => {
                CDI.track && CDI.track('cliente_operacion_download', {
                    id: a.getAttribute('data-op-id') || '',
                });
            });
        });
    }

    function renderDatos(c) {
        if (!datosGrid) return;
        const rows = [
            ['Razón social', c.nombre || '—'],
            ['CUIT', (c.cuit && CDI.formatCuit) ? CDI.formatCuit(c.cuit) : (c.cuit || '—')],
            ['Domicilio', c.direccion || '—'],
            ['Email', c.email || '—'],
            ['Teléfono', c.telefono || '—'],
            ['Origen habitual', c.default_origin || '—'],
            ['Moneda', c.preferred_currency || '—'],
            ['Notas', c.notas || '—'],
        ];
        datosGrid.innerHTML = rows.map(([k, v]) =>
            '<dt>' + CDI.escapeHtml(k) + '</dt><dd>' + CDI.escapeHtml(String(v)) + '</dd>'
        ).join('');
    }

    /* ==========================================================
       Tabs
       ========================================================== */
    function switchTab(tab) {
        activeTab = tab;
        [[tabOps, 'ops'], [tabMapeo, 'mapeo'], [tabDatos, 'datos']].forEach(([btn, t]) => {
            if (!btn) return;
            const active = tab === t;
            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        if (panelOps)   panelOps.hidden   = tab !== 'ops';
        if (panelMapeo) panelMapeo.hidden = tab !== 'mapeo';
        if (panelDatos) panelDatos.hidden = tab !== 'datos';
        if (tab === 'mapeo' && detailClienteId && currentMapping == null) {
            CDI.track && CDI.track('mapping_opened', { id: detailClienteId });
            loadMapping(detailClienteId);
        }
    }

    /* ==========================================================
       Mapeo Excel
       ========================================================== */
    const CANON_LABELS = {
        pieza: 'NCM / Pieza',
        descripcion: 'Descripción',
        origen: 'Origen',
        cantidad: 'Cantidad',
        valor_unitario: 'Valor unitario',
        peso_unitario: 'Peso unitario',
    };
    const CANON_ORDER = ['pieza', 'descripcion', 'origen', 'cantidad', 'valor_unitario', 'peso_unitario'];

    async function loadMapping(id) {
        if (!mapeoList) return;
        renderMapping(null);
        try {
            const res = await CDI.api('/api/clientes/' + encodeURIComponent(id) + '/column_mapping');
            if (!res || !res.ok) throw new Error('No se pudo cargar el mapeo');
            const data = await res.json().catch(() => ({}));
            currentMapping = (data && data.mapping) || {};
            mappingDraft = Object.assign({}, currentMapping);
            renderMapping(mappingDraft);
        } catch (err) {
            console.error('[mapping] load', err);
            renderMapping({});
            CDI.toast && CDI.toast.error('No se pudo cargar el mapeo.');
        }
    }

    function renderMapping(mapping) {
        if (!mapeoList || !mapeoEmpty || !mapeoActions) return;
        if (mapping == null) {
            mapeoList.hidden = true;
            mapeoEmpty.hidden = true;
            mapeoActions.hidden = true;
            return;
        }
        const entries = Object.entries(mapping || {});
        if (!entries.length) {
            mapeoList.hidden = true;
            mapeoEmpty.hidden = false;
            mapeoActions.hidden = true;
            return;
        }
        mapeoEmpty.hidden = true;
        mapeoList.hidden = false;
        mapeoActions.hidden = false;
        mapeoList.innerHTML = entries.map(([header, canon]) => {
            const options = ['<option value="">(ignorar)</option>']
                .concat(CANON_ORDER.map(c =>
                    '<option value="' + c + '"' + (c === canon ? ' selected' : '') + '>' +
                        CDI.escapeHtml(CANON_LABELS[c] || c) + '</option>'
                ));
            return (
                '<li class="cx-mapeo-row">' +
                    '<span class="mapping-src" title="' + CDI.escapeHtml(header) + '">' + CDI.escapeHtml(header) + '</span>' +
                    '<span class="mapping-arrow">→</span>' +
                    '<select data-mapping-header="' + CDI.escapeHtml(header) + '">' + options.join('') + '</select>' +
                '</li>'
            );
        }).join('');
        mapeoList.querySelectorAll('select[data-mapping-header]').forEach(sel => {
            sel.addEventListener('change', (ev) => {
                const h = sel.getAttribute('data-mapping-header');
                const v = String(ev.target.value || '').trim();
                if (!mappingDraft) mappingDraft = {};
                if (v) mappingDraft[h] = v;
                else delete mappingDraft[h];
            });
        });
    }

    async function saveMapping() {
        if (!detailClienteId || !mappingDraft) return;
        mapeoSave.disabled = true;
        try {
            const res = await CDI.api('/api/clientes/' + encodeURIComponent(detailClienteId) + '/column_mapping', {
                method: 'POST', body: JSON.stringify({ mapping: mappingDraft }),
            });
            if (!res || !res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'No se pudo guardar');
            }
            const data = await res.json().catch(() => ({}));
            currentMapping = (data && data.mapping) || {};
            mappingDraft = Object.assign({}, currentMapping);
            renderMapping(mappingDraft);
            CDI.toast && CDI.toast.success('Mapeo guardado');
            CDI.track && CDI.track('mapping_saved', { id: detailClienteId });
        } catch (err) {
            CDI.toast && CDI.toast.error(String(err.message || err));
        } finally {
            mapeoSave.disabled = false;
        }
    }

    async function resetMapping() {
        if (!detailClienteId) return;
        const ok = window.confirm('¿Borrar el mapeo guardado de este cliente?');
        if (!ok) return;
        mapeoReset.disabled = true;
        try {
            const res = await CDI.api('/api/clientes/' + encodeURIComponent(detailClienteId) + '/column_mapping', { method: 'DELETE' });
            if (!res || !res.ok) throw new Error('No se pudo resetear');
            currentMapping = {};
            mappingDraft = {};
            renderMapping({});
            CDI.toast && CDI.toast.success('Mapeo eliminado');
            CDI.track && CDI.track('mapping_reset', { id: detailClienteId });
        } catch (err) {
            CDI.toast && CDI.toast.error(String(err.message || err));
        } finally {
            mapeoReset.disabled = false;
        }
    }

    async function loadDetailData(id) {
        try {
            const [metRes, opsRes] = await Promise.all([
                CDI.api('/api/clientes/' + encodeURIComponent(id) + '/metricas'),
                CDI.api('/api/clientes/' + encodeURIComponent(id) + '/operaciones'),
            ]);
            if (metRes && metRes.ok) {
                const mdata = await metRes.json().catch(() => ({}));
                renderKpis(mdata.metricas || mdata);
            } else {
                renderKpis({ total_operaciones: 0, valor_total: 0, ultimo_movimiento: '—' });
            }
            if (opsRes && opsRes.ok) {
                const odata = await opsRes.json().catch(() => ({}));
                renderOps(odata.operaciones || []);
            } else {
                renderOps([]);
            }
        } catch (err) {
            console.error('[cliente-detail]', err);
            renderKpis({ total_operaciones: 0, valor_total: 0, ultimo_movimiento: '—' });
            renderOps([]);
        }
    }

    async function downloadTemplate() {
        if (!detailClienteId) return;
        try {
            const res = await CDI.api('/api/clientes/' + encodeURIComponent(detailClienteId) + '/plantilla');
            if (!res || !res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || ('Error ' + (res && res.status)));
            }
            const blob = await res.blob();
            const c = clientes.find(x => x.id === detailClienteId);
            const baseName = (c && c.nombre ? c.nombre : 'cliente').toLowerCase()
                .replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'cliente';
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'plantilla_' + baseName + '.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 2000);
            CDI.toast && CDI.toast.success('Descarga iniciada.');
            CDI.track && CDI.track('cliente_template_download', { id: detailClienteId });
        } catch (err) {
            CDI.toast && CDI.toast.error(String(err.message || err));
        }
    }

    /* ==========================================================
       Acciones puntuales
       ========================================================== */
    async function onFavClick(id) {
        try {
            await toggleFavorito(id);
            await refresh();
            if (detailClienteId === id) {
                const c = clientes.find(x => x.id === id);
                if (c) renderHero(c);
            }
        } catch (err) {
            CDI.toast && CDI.toast.error('Error', String(err.message || err));
        }
    }

    async function onDeleteClick(id) {
        const c = clientes.find(x => x.id === id);
        if (!c) return;
        const ok = window.confirm('¿Eliminar "' + c.nombre + '"? Esta acción no se puede deshacer.');
        if (!ok) return;
        try {
            await deleteCliente(id);
            const activo = CDI.getClienteActivo();
            if (activo && activo.id === id) CDI.setClienteActivo(null);
            if (detailClienteId === id) {
                detailClienteId = null;
                showEmptySelection();
            }
            await refresh();
            CDI.toast && CDI.toast.success('Cliente eliminado', c.nombre);
        } catch (err) {
            CDI.toast && CDI.toast.error('No se pudo eliminar', String(err.message || err));
        }
    }

    async function onCsvClick(id) {
        const c = clientes.find(x => x.id === id);
        if (!c) return;
        try {
            const res = await CDI.api('/api/clientes/' + encodeURIComponent(id) + '/operaciones');
            if (!res || !res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || ('Error ' + (res && res.status)));
            }
            const data = await res.json().catch(() => ({}));
            const operaciones = Array.isArray(data.operaciones) ? data.operaciones : [];
            if (!operaciones.length) {
                CDI.toast && CDI.toast.info('Sin operaciones para exportar.');
                return;
            }
            const header = ['Fecha', 'Código', 'Archivo', 'Ítems', 'Valor', 'Moneda'];
            const rows = operaciones.map(op => {
                const fecha = op.fecha ? new Date(op.fecha).toLocaleDateString('es-AR') : '';
                return [
                    fecha,
                    op.op_code || '',
                    op.generated_file || '',
                    String(op.total_items || 0),
                    (op.total_value != null ? String(op.total_value) : ''),
                    op.currency || '',
                ];
            });
            const csv = [header, ...rows].map(r => r.map(csvEscape).join(',')).join('\r\n');
            const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
            const slug = (c.nombre || 'cliente').toLowerCase()
                .replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'cliente';
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'historial_' + slug + '.csv';
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 2000);
            CDI.toast && CDI.toast.success('CSV descargado', operaciones.length + ' ops');
            CDI.track && CDI.track('cliente_csv_export', { id: id, rows: operaciones.length });
        } catch (err) {
            CDI.toast && CDI.toast.error(String(err.message || err));
        }
    }

    function csvEscape(v) {
        const s = String(v == null ? '' : v);
        if (/[",\r\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
        return s;
    }

    function onEditCurrent() {
        const c = clientes.find(x => x.id === detailClienteId);
        if (c) openFormEdit(c);
    }

    /* ==========================================================
       Modal form (nuevo/editar)
       ========================================================== */
    function openForm(prefill) {
        if (!formModal) return;
        editingId = null;
        if (formTitleEl) formTitleEl.textContent = 'Nuevo cliente';
        if (formSave) formSave.textContent = 'Guardar';
        resetFormFields();
        if (prefill) {
            if (fNombre)    fNombre.value    = prefill.nombre || '';
            if (fCuit)      fCuit.value      = prefill.cuit && CDI.formatCuit ? CDI.formatCuit(prefill.cuit) : (prefill.cuit || '');
            if (fDireccion) fDireccion.value = prefill.direccion || '';
        }
        clearFormError();
        showModal();
        setTimeout(() => fNombre && fNombre.focus(), 80);
        CDI.track && CDI.track('clientes_form_open', { mode: 'create', prefilled: !!prefill });
    }

    function openFormEdit(cliente) {
        if (!formModal || !cliente) return;
        editingId = cliente.id;
        if (formTitleEl) formTitleEl.textContent = 'Editar cliente';
        if (formSave) formSave.textContent = 'Guardar cambios';
        resetFormFields();
        fillFormFromCliente(cliente);
        clearFormError();
        showModal();
        setTimeout(() => fNombre && fNombre.focus(), 80);
        CDI.track && CDI.track('clientes_form_open', { mode: 'edit', id: cliente.id });
    }

    function showModal() {
        if (!formModal) return;
        if (typeof formModal.showModal === 'function') {
            try { formModal.showModal(); } catch (_) { formModal.setAttribute('open', ''); }
        } else {
            formModal.setAttribute('open', '');
        }
    }

    function closeForm() {
        if (!formModal) return;
        if (typeof formModal.close === 'function' && formModal.open) {
            try { formModal.close(); } catch (_) { formModal.removeAttribute('open'); }
        } else {
            formModal.removeAttribute('open');
        }
        editingId = null;
        resetFormFields();
        clearFormError();
        // Si entramos con openForm desde otra screen, volver automaticamente.
        if (autoReturnAfterForm) {
            autoReturnAfterForm = false;
            setTimeout(() => { CDI.goBack && CDI.goBack(); }, 60);
        }
    }

    function resetFormFields() {
        if (fNombre) fNombre.value = '';
        if (fCuit) fCuit.value = '';
        if (fDireccion) fDireccion.value = '';
        if (fEmail) fEmail.value = '';
        if (fTelefono) fTelefono.value = '';
        if (fOrigen) fOrigen.value = '';
        if (fMoneda) fMoneda.value = '';
        if (fNotas) fNotas.value = '';
        if (fFechaInicActiv) fFechaInicActiv.value = '';
        if (fAdvanced) fAdvanced.open = false;
    }

    function fillFormFromCliente(c) {
        if (!c) return;
        if (fNombre) fNombre.value = c.nombre || '';
        if (fCuit) fCuit.value = c.cuit && CDI.formatCuit ? CDI.formatCuit(c.cuit) : (c.cuit || '');
        if (fDireccion) fDireccion.value = c.direccion || '';
        if (fEmail) fEmail.value = c.email || '';
        if (fTelefono) fTelefono.value = c.telefono || '';
        if (fOrigen) fOrigen.value = c.default_origin || '';
        if (fMoneda) fMoneda.value = c.preferred_currency || '';
        if (fNotas) fNotas.value = c.notas || '';
        if (fFechaInicActiv) fFechaInicActiv.value = c.fecha_inic_activ || '';
        const hasAdvanced = !!(
            c.email || c.telefono || c.default_origin ||
            c.preferred_currency || c.notas || c.fecha_inic_activ
        );
        if (fAdvanced) fAdvanced.open = hasAdvanced;
    }

    function showFormError(msg) {
        if (!formError) return;
        formError.textContent = msg;
        formError.hidden = false;
    }
    function clearFormError() {
        if (!formError) return;
        formError.textContent = '';
        formError.hidden = true;
    }

    async function submitForm() {
        const nombre = String((fNombre && fNombre.value) || '').trim();
        const cuitRaw = String((fCuit && fCuit.value) || '').trim();
        const direccion = String((fDireccion && fDireccion.value) || '').trim();
        const email = String((fEmail && fEmail.value) || '').trim();
        const telefono = String((fTelefono && fTelefono.value) || '').trim();
        const origen = String((fOrigen && fOrigen.value) || '').trim();
        const moneda = String((fMoneda && fMoneda.value) || '').trim();
        const notas = String((fNotas && fNotas.value) || '').trim();
        const fechaInicActiv = String((fFechaInicActiv && fFechaInicActiv.value) || '').trim();
        clearFormError();

        if (!nombre) {
            showFormError('La razón social es obligatoria.');
            fNombre && fNombre.focus();
            return;
        }
        const cuitNorm = CDI.normalizeCuit ? CDI.normalizeCuit(cuitRaw) : cuitRaw.replace(/\D/g, '');
        if (cuitRaw && cuitNorm.length !== 11) {
            showFormError('El CUIT debe tener 11 dígitos.');
            fCuit && fCuit.focus();
            return;
        }
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showFormError('Email inválido.');
            fEmail && fEmail.focus();
            return;
        }

        const body = {
            nombre: nombre,
            cuit: cuitNorm || '',
            direccion: direccion,
            email: email,
            telefono: telefono,
            default_origin: origen,
            preferred_currency: moneda,
            notas: notas,
            fecha_inic_activ: fechaInicActiv,
        };

        const isEdit = !!editingId;
        const idEdit = editingId;
        formSave.disabled = true;
        const origLabel = formSave.textContent;
        formSave.textContent = 'Guardando…';
        try {
            const resp = isEdit ? await updateCliente(idEdit, body) : await createCliente(body);
            const guardado = resp && resp.cliente ? resp.cliente : null;
            // Mergear in-memory en vez de refrescar la lista entera: el POST/PUT
            // ya devuelve el cliente completo, y la lista se ordena client-side.
            if (guardado) {
                if (isEdit) {
                    const idx = clientes.findIndex(c => c.id === guardado.id);
                    if (idx >= 0) {
                        clientes[idx] = Object.assign({}, clientes[idx], guardado);
                    } else {
                        clientes.push(guardado);
                    }
                } else {
                    const nuevo = Object.assign({
                        ops_count: 0,
                        valor_total: 0,
                        ultimo: null,
                        ncm_top: null,
                    }, guardado);
                    clientes.unshift(nuevo);
                }
                CDI.clientesCache = clientes;

                renderList();
                selectCliente(guardado.id);
            }
            closeForm();
            CDI.toast && CDI.toast.success(isEdit ? 'Cliente actualizado' : 'Cliente creado', nombre);
        } catch (err) {
            showFormError(String(err.message || err));
        } finally {
            formSave.disabled = false;
            formSave.textContent = isEdit ? 'Guardar cambios' : 'Guardar';
            if (origLabel) formSave.textContent = isEdit ? 'Guardar cambios' : 'Guardar';
        }
    }

    /* ==========================================================
       Teclado global
       ========================================================== */
    function isTypingInField(ev) {
        const t = ev.target;
        if (!t) return false;
        const tag = (t.tagName || '').toUpperCase();
        if (t.isContentEditable) return true;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
        return false;
    }

    function onGlobalKeydown(ev) {
        if (!entered) return;

        // Mientras el modal esta abierto, solo manejamos Escape; el resto queda al browser.
        if (formModal && formModal.open) {
            if (ev.key === 'Escape') {
                ev.preventDefault();
                closeForm();
            }
            return;
        }

        // Esc: volver a la screen previa (o upload como fallback)
        if (ev.key === 'Escape') {
            ev.preventDefault();
            CDI.goBack && CDI.goBack();
            return;
        }

        // '/' focusea buscador aunque estemos en otro input "no-typing"
        if (ev.key === '/' && !isTypingInField(ev)) {
            ev.preventDefault();
            if (searchInput) { searchInput.focus(); searchInput.select(); }
            CDI.track && CDI.track('clientes_keyboard_nav', { key: 'slash' });
            return;
        }

        // Si estamos tipeando en un input/textarea de la screen, no atajamos
        if (isTypingInField(ev) && ev.target !== searchInput) return;

        // Buscador: flechas/enter siguen capturadas, el resto no
        const key = ev.key;
        if (key === 'ArrowDown' || key === 'ArrowUp') {
            if (visibleIds.length === 0) return;
            ev.preventDefault();
            const delta = key === 'ArrowDown' ? 1 : -1;
            activeIndex = Math.max(0, Math.min(visibleIds.length - 1, (activeIndex < 0 ? 0 : activeIndex + delta)));
            highlightActive();
            CDI.track && CDI.track('clientes_keyboard_nav', { key: key });
            return;
        }

        if (key === 'Enter' && !isTypingInField(ev)) {
            if (activeIndex >= 0 && visibleIds[activeIndex]) {
                ev.preventDefault();
                selectCliente(visibleIds[activeIndex]);
            }
            return;
        }

        // Shortcuts de letra (solo si no estamos tipeando en algun field de la screen)
        if (!isTypingInField(ev) || ev.target === searchInput) {
            // En searchInput NO queremos atrapar letras comunes porque el usuario esta escribiendo
            if (ev.target === searchInput) return;

            if (key === 'n' || key === 'N') {
                ev.preventDefault();
                openForm();
                return;
            }
            if (!detailClienteId) return;
            if (key === 'f' || key === 'F') {
                ev.preventDefault();
                onFavClick(detailClienteId);
            } else if (key === 'e' || key === 'E') {
                ev.preventDefault();
                onEditCurrent();
            }
        }
    }

    /* ==========================================================
       Public API
       ========================================================== */
    CDI.openClientesDrawer = function (opts) {
        CDI.goTo('clientes', opts || {});
    };
    CDI.closeClientesDrawer = function () {
        if (CDI.goBack) CDI.goBack();
    };
    CDI.refreshClientes = refresh;
    CDI.getClientesCache = () => clientes.slice();

    // Registro de la screen (goTo 'clientes')
    if (CDI.registerScreen) {
        CDI.registerScreen('clientes', { onEnter: onEnter, onLeave: onLeave });
    }

    document.addEventListener('DOMContentLoaded', init);
})();
