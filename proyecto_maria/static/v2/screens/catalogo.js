/* ============================================================
   CDI v2 — Drawer lateral de "Mi catálogo aprendido"
   Responsabilidad: permitir ver y limpiar el catálogo de
   proveedores/productos que el sistema aprende silenciosamente
   al generar MARIA.TXT. La creación de proveedores/productos
   sigue siendo implícita (no hay CTA de "nuevo") para evitar
   duplicar el flujo natural — aca solo mantenemos lo existente.

   Expone:
     CDI.openCatalogoDrawer()
     CDI.refreshCatalogo()
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    // DOM refs
    let drawer, overlay, closeBtn, searchInput, listEl, loadingEl, emptyEl;
    let detailEl, detailBack, detailTitle, detailHeader, productList, productEmpty, vendorDeleteBtn;

    // Estado
    let vendors = [];
    let filterText = '';
    let loading = false;
    let initialized = false;
    let detailVendorId = null;
    let detailVendor = null;  // snapshot del vendor activo (con productos)

    function $(id) { return document.getElementById(id); }

    function init() {
        if (initialized) return;
        drawer       = $('catalogoDrawer');
        overlay      = $('catalogoOverlay');
        closeBtn     = $('catalogoDrawerClose');
        searchInput  = $('catalogoSearch');
        listEl       = $('catalogoList');
        loadingEl    = $('catalogoLoading');
        emptyEl      = $('catalogoEmpty');
        detailEl     = $('catalogoDetail');
        detailBack   = $('catalogoDetailBack');
        detailTitle  = $('catalogoDetailTitle');
        detailHeader = $('catalogoDetailHeader');
        productList  = $('catalogoProductList');
        productEmpty = $('catalogoProductEmpty');
        vendorDeleteBtn = $('catalogoVendorDelete');
        if (!drawer) return;

        closeBtn.addEventListener('click', close);
        overlay.addEventListener('click', close);
        if (detailBack) detailBack.addEventListener('click', closeDetail);
        if (vendorDeleteBtn) vendorDeleteBtn.addEventListener('click', onDeleteVendor);

        searchInput.addEventListener('input', (ev) => {
            filterText = String(ev.target.value || '').trim().toLowerCase();
            renderList();
        });

        document.addEventListener('keydown', (ev) => {
            if (ev.key !== 'Escape') return;
            if (!drawer.classList.contains('is-open')) return;
            if (detailEl && !detailEl.hidden) { closeDetail(); return; }
            close();
        });
        document.addEventListener('cdi:screen-leave', close);
        initialized = true;
    }

    async function open() {
        init();
        if (!drawer) return;
        drawer.hidden = false;
        overlay.hidden = false;
        requestAnimationFrame(() => {
            drawer.classList.add('is-open');
            overlay.classList.add('is-visible');
        });
        CDI.track && CDI.track('catalogo_drawer_open');
        closeDetail();
        await refresh();
        setTimeout(() => { if (searchInput) searchInput.focus(); }, 220);
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
        }, 320);
        CDI.track && CDI.track('catalogo_drawer_close');
    }

    /* ==========================================================
       API
       ========================================================== */
    async function refresh() {
        if (loading) return;
        loading = true;
        showLoading(true);
        try {
            const res = await CDI.api('/api/catalog/proveedores');
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || 'No se pudo cargar el catálogo');
            vendors = Array.isArray(data.proveedores) ? data.proveedores : [];
            renderList();
        } catch (err) {
            console.error('[catalogo] refresh', err);
            if (CDI.toast) CDI.toast.error(String(err.message || err));
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
            if (emptyEl) emptyEl.hidden = true;
        }
    }

    /* ==========================================================
       Render: lista de proveedores
       ========================================================== */
    function renderList() {
        if (!listEl) return;
        if (vendors.length === 0) {
            listEl.hidden = true;
            emptyEl.hidden = false;
            return;
        }
        const q = filterText;
        const filtered = q
            ? vendors.filter(v =>
                String(v.nombre || v.vendor_id || '').toLowerCase().indexOf(q) !== -1)
            : vendors.slice();

        if (!filtered.length) {
            emptyEl.hidden = true;
            listEl.hidden = false;
            listEl.innerHTML =
                '<li class="catalogo-vendor-empty">' +
                    '<p class="caption">Sin resultados para "' + CDI.escapeHtml(q) + '".</p>' +
                '</li>';
            return;
        }

        emptyEl.hidden = true;
        listEl.hidden = false;
        listEl.innerHTML = filtered.map(renderVendorItem).join('');
        attachVendorHandlers();
    }

    function renderVendorItem(v) {
        const nombre = v.nombre || v.vendor_id || 'Proveedor';
        const count = Number(v.total_productos || 0);
        const usos = Number(v.usos_totales || 0);
        const meta = [];
        meta.push(count + (count === 1 ? ' producto' : ' productos'));
        if (usos > 0) meta.push(usos + (usos === 1 ? ' uso' : ' usos'));
        return (
            '<li class="catalogo-vendor-card" data-vendor-id="' + CDI.escapeHtml(v.vendor_id) + '">' +
                '<div class="catalogo-vendor-main">' +
                    '<div class="catalogo-vendor-name">' + CDI.escapeHtml(nombre) + '</div>' +
                    '<div class="catalogo-vendor-meta">' + CDI.escapeHtml(meta.join(' · ')) + '</div>' +
                '</div>' +
                '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>' +
            '</li>'
        );
    }

    function attachVendorHandlers() {
        if (!listEl) return;
        listEl.querySelectorAll('.catalogo-vendor-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = card.getAttribute('data-vendor-id');
                if (id) openDetail(id);
            });
        });
    }

    /* ==========================================================
       Detalle del proveedor
       ========================================================== */
    async function openDetail(vendorId) {
        if (!detailEl) return;
        detailVendorId = vendorId;
        detailEl.hidden = false;
        detailHeader.innerHTML = '<p class="caption">Cargando…</p>';
        productList.innerHTML = '';
        productEmpty.hidden = true;
        CDI.track && CDI.track('catalogo_vendor_open', { vendor_id: vendorId });

        try {
            const res = await CDI.api('/api/catalog/' + encodeURIComponent(vendorId));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || 'No se pudo cargar el proveedor');
            detailVendor = data;
            renderDetail(data);
        } catch (err) {
            console.error('[catalogo] detail', err);
            if (CDI.toast) CDI.toast.error(String(err.message || err));
            closeDetail();
        }
    }

    function closeDetail() {
        if (!detailEl) return;
        detailEl.hidden = true;
        detailVendorId = null;
        detailVendor = null;
    }

    function renderDetail(data) {
        const nombre = data.nombre || data.vendor_id || 'Proveedor';
        if (detailTitle) detailTitle.textContent = nombre;
        const prods = data.productos || {};
        const keys = Object.keys(prods);
        const total = keys.length;
        const ultima = data.ultima_actualizacion
            ? new Date(data.ultima_actualizacion).toLocaleDateString('es-AR')
            : null;
        const metaParts = [];
        metaParts.push(total + (total === 1 ? ' producto' : ' productos'));
        if (ultima) metaParts.push('Actualizado ' + ultima);
        detailHeader.innerHTML =
            '<div class="catalogo-detail-name">' + CDI.escapeHtml(nombre) + '</div>' +
            '<div class="catalogo-detail-sub">' + CDI.escapeHtml(metaParts.join(' · ')) + '</div>';

        if (!total) {
            productList.innerHTML = '';
            productEmpty.hidden = false;
            return;
        }
        productEmpty.hidden = true;
        const rows = keys.map(k => renderProductRow(k, prods[k]));
        productList.innerHTML = rows.join('');
        attachProductHandlers();
    }

    function renderProductRow(key, p) {
        const desc = p.descripcion_original || key;
        const ncm = p.ncm || '';
        const origen = p.origen || '';
        const usos = Number(p.usos || 0);
        const ncmFmt = ncm && CDI.formatNcm ? CDI.formatNcm(ncm) : ncm;
        const subParts = [];
        if (usos > 0) subParts.push(usos + (usos === 1 ? ' uso' : ' usos'));
        if (p.ultima_vez) subParts.push(p.ultima_vez);
        const sub = subParts.join(' · ');
        return (
            '<li class="catalogo-product-row" data-product-key="' + CDI.escapeHtml(key) + '">' +
                '<div class="catalogo-product-main">' +
                    '<div class="catalogo-product-desc">' + CDI.escapeHtml(desc) + '</div>' +
                    (sub ? '<div class="catalogo-product-sub">' + CDI.escapeHtml(sub) + '</div>' : '') +
                '</div>' +
                '<div class="catalogo-product-fields">' +
                    '<label class="catalogo-product-field">' +
                        '<span>NCM</span>' +
                        '<input type="text" data-field="ncm" value="' + CDI.escapeHtml(ncmFmt) + '" placeholder="0000.00.00" inputmode="numeric">' +
                    '</label>' +
                    '<label class="catalogo-product-field">' +
                        '<span>Origen</span>' +
                        '<input type="text" data-field="origen" value="' + CDI.escapeHtml(origen) + '" placeholder="XX" maxlength="3">' +
                    '</label>' +
                '</div>' +
                '<div class="catalogo-product-actions">' +
                    '<button type="button" class="btn btn-ghost btn-sm" data-action="save-product">Guardar</button>' +
                    '<button type="button" class="btn btn-ghost btn-sm is-danger" data-action="delete-product" aria-label="Eliminar producto">' +
                        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>' +
                    '</button>' +
                '</div>' +
            '</li>'
        );
    }

    function attachProductHandlers() {
        productList.querySelectorAll('.catalogo-product-row').forEach(row => {
            const key = row.getAttribute('data-product-key');
            const ncmInput = row.querySelector('input[data-field="ncm"]');
            if (ncmInput && CDI.maskNcm) {
                ncmInput.addEventListener('input', () => {
                    const pos = ncmInput.selectionStart;
                    const masked = CDI.maskNcm(ncmInput.value);
                    if (masked !== ncmInput.value) ncmInput.value = masked;
                    try { ncmInput.setSelectionRange(pos, pos); } catch (_) {}
                });
            }
            row.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', (ev) => {
                    ev.preventDefault();
                    const action = btn.getAttribute('data-action');
                    if (action === 'save-product')   saveProduct(row, key);
                    else if (action === 'delete-product') deleteProduct(row, key);
                });
            });
        });
    }

    async function saveProduct(row, productKey) {
        if (!detailVendorId) return;
        const ncmRaw = (row.querySelector('input[data-field="ncm"]').value || '').trim();
        const origen = (row.querySelector('input[data-field="origen"]').value || '').trim().toUpperCase();
        // Normalizamos NCM quitando puntos (lo que guardamos en server).
        const ncmClean = ncmRaw.replace(/\./g, '');
        try {
            const res = await CDI.api(
                '/api/catalog/' + encodeURIComponent(detailVendorId) +
                '/productos/' + encodeURIComponent(productKey),
                {
                    method: 'PUT',
                    body: JSON.stringify({ ncm: ncmClean, origen: origen }),
                }
            );
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || 'No se pudo guardar');
            if (CDI.toast) CDI.toast.success('Producto actualizado');
            CDI.track && CDI.track('catalogo_producto_edited', {
                vendor_id: detailVendorId,
                product_key: productKey,
            });
            // Refrescamos el detail (puede haber cambiado la clave)
            await openDetail(detailVendorId);
        } catch (err) {
            if (CDI.toast) CDI.toast.error(String(err.message || err));
        }
    }

    async function deleteProduct(row, productKey) {
        if (!detailVendorId) return;
        const ok = window.confirm('¿Eliminar este producto del catálogo?');
        if (!ok) return;
        try {
            const res = await CDI.api(
                '/api/catalog/' + encodeURIComponent(detailVendorId) +
                '/productos/' + encodeURIComponent(productKey),
                { method: 'DELETE' }
            );
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'No se pudo eliminar');
            }
            if (CDI.toast) CDI.toast.success('Producto eliminado');
            CDI.track && CDI.track('catalogo_producto_deleted', {
                vendor_id: detailVendorId,
                product_key: productKey,
            });
            await openDetail(detailVendorId);
            await refresh();  // counts cambiaron
        } catch (err) {
            if (CDI.toast) CDI.toast.error(String(err.message || err));
        }
    }

    async function onDeleteVendor() {
        if (!detailVendorId) return;
        const nombre = (detailVendor && (detailVendor.nombre || detailVendor.vendor_id)) || 'este proveedor';
        const ok = window.confirm('¿Eliminar "' + nombre + '" del catálogo? Esto borra todos sus productos aprendidos.');
        if (!ok) return;
        try {
            const res = await CDI.api('/api/catalog/' + encodeURIComponent(detailVendorId), {
                method: 'DELETE',
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'No se pudo eliminar');
            }
            if (CDI.toast) CDI.toast.success('Proveedor eliminado');
            CDI.track && CDI.track('catalogo_vendor_deleted', { vendor_id: detailVendorId });
            closeDetail();
            await refresh();
        } catch (err) {
            if (CDI.toast) CDI.toast.error(String(err.message || err));
        }
    }

    /* ==========================================================
       Public API
       ========================================================== */
    CDI.openCatalogoDrawer = open;
    CDI.refreshCatalogo = refresh;

    document.addEventListener('DOMContentLoaded', init);
})();
