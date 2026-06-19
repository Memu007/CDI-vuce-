/* ============================================================
   CDI v2 — Screen 1: Upload (PDF o Excel)
   Acepta un PDF de proveedor (endpoint /upload_pdf/public) o una
   planilla Excel con el mapeo del cliente activo (/upload_excel_v2/).
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const FORMATS = {
        pdf: {
            label: 'PDF',
            accept: '.pdf,application/pdf',
            allowedExt: ['.pdf'],
            allowedMime: ['application/pdf'],
            maxMB: 10,
            endpoint: '/upload_pdf/public',
            hint: 'Arrastrá el PDF aquí',
            meta: 'PDF · hasta 10 MB',
            progressTitle: 'Procesando PDF…',
            progressSub: 'Extrayendo datos del proveedor y los ítems.',
        },
        excel: {
            label: 'Excel',
            accept: '.xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel',
            allowedExt: ['.xlsx', '.xls'],
            allowedMime: [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel',
                'application/octet-stream',
            ],
            maxMB: 15,
            endpoint: '/upload_excel_v2/',
            hint: 'Arrastrá la planilla Excel aquí',
            meta: 'Excel · .xlsx o .xls · hasta 15 MB',
            progressTitle: 'Procesando Excel…',
            progressSub: 'Leyendo la planilla con el mapeo del cliente.',
        },
    };

    let dz, input, pickBtn, progress, progressTitle, progressSub, errorEl;
    let hintEl, metaEl, excelHint, simulateBtn;
    let formatBtns = [];
    let currentFormat = 'pdf';
    let startTs = 0;
    let busy = false;

    function $(id) { return document.getElementById(id); }

    function init() {
        dz = $('uploadDropzone');
        input = $('uploadFileInput');
        pickBtn = $('uploadPickBtn');
        progress = $('uploadProgress');
        progressTitle = $('uploadProgressTitle');
        progressSub = $('uploadProgressSub');
        errorEl = $('uploadError');
        hintEl = $('uploadDropzoneHint');
        metaEl = $('uploadDropzoneMeta');
        excelHint = $('uploadHintExcel');
        simulateBtn = $('uploadSimulateBtn');
        formatBtns = Array.from(document.querySelectorAll('.upload-format-opt'));
        if (!dz || !input) return;

        if (simulateBtn) {
            simulateBtn.addEventListener('click', (ev) => {
                ev.preventDefault();
                if (busy) return;
                simulateOperation();
            });
        }

        // CTA: descargar plantilla AVG en blanco (caso atipico pero util para
        // el despachante que quiere cargar datos a mano desde Excel).
        const blankTpl = $('uploadBlankTemplateBtn');
        if (blankTpl) {
            blankTpl.addEventListener('click', (ev) => {
                ev.preventDefault();
                if (busy) return;
                downloadBlankTemplate();
            });
        }

        formatBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (busy) return;
                const fmt = btn.getAttribute('data-format');
                if (fmt) setFormat(fmt);
            });
        });

        dz.addEventListener('click', (ev) => {
            if (busy) return;
            ev.preventDefault();
            input.click();
        });
        input.addEventListener('change', (ev) => {
            const file = ev.target.files && ev.target.files[0];
            if (file) handleFile(file);
            input.value = '';
        });

        ['dragenter', 'dragover'].forEach(evt =>
            dz.addEventListener(evt, (e) => {
                e.preventDefault(); e.stopPropagation();
                if (!busy) dz.classList.add('is-dragging');
            })
        );
        ['dragleave', 'drop'].forEach(evt =>
            dz.addEventListener(evt, (e) => {
                e.preventDefault(); e.stopPropagation();
                dz.classList.remove('is-dragging');
            })
        );
        dz.addEventListener('drop', (e) => {
            if (busy) return;
            const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
            if (file) handleFile(file);
        });

        window.addEventListener('dragover', preventDefault);
        window.addEventListener('drop', preventDefault);

        setFormat('pdf');
    }

    function preventDefault(e) {
        if (e && e.preventDefault) e.preventDefault();
    }

    function setFormat(fmt) {
        if (!FORMATS[fmt]) return;
        currentFormat = fmt;
        const def = FORMATS[fmt];
        formatBtns.forEach(btn => {
            const active = btn.getAttribute('data-format') === fmt;
            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        if (input) input.accept = def.accept;
        if (hintEl) hintEl.textContent = def.hint;
        if (metaEl) metaEl.textContent = def.meta;
        if (excelHint) excelHint.hidden = fmt !== 'excel';
        hideError();
        CDI.track && CDI.track('upload_format_change', { format: fmt });
    }

    function validate(file, def) {
        if (!file) return 'No se recibió ningún archivo.';
        const name = (file.name || '').toLowerCase();
        const extOk = def.allowedExt.some(e => name.endsWith(e));
        const mimeOk = !file.type || def.allowedMime.includes(file.type);
        if (!extOk && !mimeOk) {
            return 'El archivo no coincide con el formato seleccionado (' + def.label + ').';
        }
        const maxBytes = def.maxMB * 1024 * 1024;
        if (file.size > maxBytes) {
            return 'El archivo supera los ' + def.maxMB + ' MB.';
        }
        if (file.size === 0) {
            return 'El archivo está vacío.';
        }
        return null;
    }

    function setBusy(on, title, sub) {
        busy = on;
        if (!dz) {
            // La pantalla aún no montó el DOM (raro, pero defensivo).
            console.warn('[upload] setBusy called before dropzone initialized');
            return;
        }
        if (on) {
            dz.classList.add('is-disabled');
            if (progress) progress.hidden = false;
            if (title && progressTitle) progressTitle.textContent = title;
            if (sub && progressSub) progressSub.textContent = sub;
            hideError();
        } else {
            dz.classList.remove('is-disabled');
            if (progress) progress.hidden = true;
        }
    }

    function showError(msg) {
        if (!errorEl) return;
        errorEl.textContent = msg;
        errorEl.hidden = false;
    }
    function hideError() {
        if (!errorEl) return;
        errorEl.hidden = true;
        errorEl.textContent = '';
    }

    async function handleFile(file) {
        hideError();
        const def = FORMATS[currentFormat];
        const err = validate(file, def);
        if (err) {
            showError(err);
            CDI.track('upload_rejected', { format: currentFormat, reason: err, size: file.size });
            return;
        }

        let excelCliente = null;
        if (currentFormat === 'excel') {
            excelCliente = await pickClienteForExcel(file.name);
            if (!excelCliente) {
                const ok = await CDI.confirm({
                    title: 'Excel sin cliente',
                    lead: '¿Continuar sin cliente seleccionado?',
                    text: 'El Excel se procesará con el mapeo genérico de columnas, no con el mapeo personalizado de un cliente.',
                    acceptText: 'Continuar igual',
                    cancelText: 'Elegir cliente',
                    kind: 'warning',
                });
                if (!ok) {
                    CDI.track('upload_cancelled_no_cliente', { format: 'excel' });
                    return;
                }
                CDI.track('upload_excel_sin_cliente', { filename: file.name });
            }
        }

        const form = new FormData();
        form.append('file', file);

        if (currentFormat === 'excel') {
            const cid = (excelCliente && excelCliente.id) || '';
            if (cid) {
                form.append('cliente_id', cid);
                form.append('use_mapping', 'true');
                CDI.setClienteActivo && CDI.setClienteActivo(excelCliente);
            }
        }

        startTs = Date.now();
        CDI.track('upload_start', { format: currentFormat, filename: file.name, size: file.size });
        setBusy(true, 'Subiendo ' + file.name + '…', 'Puede tardar unos segundos.');

        try {
            const slowTimer = setTimeout(() => {
                if (busy) {
                    progressTitle.textContent = def.progressTitle;
                    progressSub.textContent = def.progressSub;
                }
            }, 2500);

            const res = await CDI.api(def.endpoint, {
                method: 'POST',
                body: form,
            });
            clearTimeout(slowTimer);

            let data;
            try { data = await res.json(); } catch (_) { data = null; }

            if (!res.ok) {
                const detail = (data && (data.detail || data.message)) || ('Error ' + res.status);
                throw new Error(detail);
            }

            const durationMs = Date.now() - startTs;
            const operacion = (data && data.operacion) || {};
            const items = (data && data.items) || [];

            if (currentFormat === 'excel' && !items.length) {
                throw new Error('No se detectaron ítems en la planilla. Revisá el mapeo del cliente.');
            }

            CDI.state = CDI.state || {};
            CDI.state.filename = data && data.filename;
            CDI.state.operacion = operacion;
            CDI.state.items = items;
            CDI.state.sourceFormat = currentFormat;
            CDI.state.uploadedAt = new Date().toISOString();
            // Reset flags de la operación anterior: cada PDF nuevo es una
            // operación nueva, el panel huérfana y la idempotencia de
            // guardado deben funcionar de cero.
            CDI.state.operationSavedFor = null;
            CDI.state.orphanDismissedFor = null;

            // Toast sutil si el backend aprendió/actualizó columnas del cliente.
            const catalogo = data && data.catalogo;
            if (currentFormat === 'excel' && catalogo && catalogo.columnas_detectadas > 0 && CDI.toast) {
                const total = catalogo.total || 6;
                const faltan = (catalogo.columnas_faltantes || []).length;
                if (faltan === 0) {
                    CDI.toast('Catálogo aprendido', total + '/' + total + ' columnas reconocidas.', 'success');
                } else {
                    CDI.toast('Catálogo parcial', catalogo.columnas_detectadas + '/' + total + ' columnas reconocidas.', 'info');
                }
            }

            if (currentFormat === 'pdf' && CDI.setClienteActivo) {
                CDI.setClienteActivo(null);
                CDI.track && CDI.track('cliente_activo_cleared_for_pdf', {
                    filename: data && data.filename,
                });
            }

            // Auto-detectar importador desde el CUIT extraido del PDF.
            // Si el user ya tiene un cliente cargado con ese CUIT, lo activa solo.
            // Asi se ahorra abrir el drawer y tocar "Asignar importador" en el 90% de los casos.
            await tryAutoMatchImportador(operacion);

            // Lookup combinado: memoria del cliente + catalogo del proveedor
            const vendorName = operacion && (operacion.vendedor_nombre || operacion.comprador_nombre_vendor);
            const clienteId = (CDI.state && CDI.state.clienteActivo && CDI.state.clienteActivo.id) || null;
            await tryCatalogAutofill(CDI.state.items, vendorName, clienteId);

            CDI.track('pdf_uploaded', {
                format: currentFormat,
                filename: data && data.filename,
                items: items.length,
                duration_ms: durationMs,
            });

            setBusy(false);
            CDI.goTo('review', { fromUpload: true });
        } catch (err) {
            const msg = (err && err.message) || 'No se pudo procesar el archivo.';
            console.error('[CDI v2 upload]', err);
            CDI.track('upload_error', { format: currentFormat, message: msg });
            setBusy(false);
            showError(msg);
        }
    }

    async function tryAutoMatchImportador(operacion) {
        try {
            const pdfCuit = CDI.normalizeCuit && CDI.normalizeCuit(operacion && operacion.comprador_cuit);
            const compradorNombre = String((operacion && operacion.comprador_nombre) || '').trim();

            const activo = CDI.getClienteActivo && CDI.getClienteActivo();
            if (activo) return;

            try { sessionStorage.removeItem('cdi.pending_create_client'); } catch (_) {}

            if (!pdfCuit || pdfCuit.length !== 11) {
                // Sin CUIT válido: intentar match por nombre antes de offering crear.
                if (compradorNombre) {
                    try {
                        const searchRes = await CDI.api('/api/clientes/search?q=' + encodeURIComponent(compradorNombre));
                        if (searchRes && searchRes.ok) {
                            const searchData = await searchRes.json().catch(() => ({}));
                            const results = searchData.clientes || searchData.results || [];
                            // Match exacto (case-insensitive) por nombre
                            const exact = results.find(c => (c.nombre || '').toLowerCase() === compradorNombre.toLowerCase());
                            if (exact) {
                                CDI.setClienteActivo && CDI.setClienteActivo(exact);
                                CDI.track && CDI.track('importador_auto_detected', {
                                    source: 'by_name_api',
                                });
                                if (CDI.toast) {
                                    CDI.toast('Importador detectado', exact.nombre || '', 'success');
                                }
                                return;
                            }
                        }
                    } catch (_) {}

                    // No se encontró por nombre: dejar pendiente para crear.
                    try {
                        sessionStorage.setItem('cdi.pending_create_client', JSON.stringify({
                            cuit: '',
                            nombre: compradorNombre,
                            captured_at: new Date().toISOString(),
                        }));
                    } catch (_) {}
                    CDI.track && CDI.track('importador_no_match', {
                        has_name: true,
                        has_cuit: false,
                    });
                }
                return;
            }

            const res = await CDI.api('/api/clientes/by-cuit/' + encodeURIComponent(pdfCuit));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) return;

            if (data.match === 'exact' && data.cliente) {
                CDI.setClienteActivo(data.cliente);
                CDI.track && CDI.track('importador_auto_detected', {
                    source: 'by_cuit_api',
                });
                if (CDI.toast) {
                    CDI.toast('Importador detectado', data.cliente.nombre || '', 'success');
                }
                return;
            }

            CDI.track && CDI.track('importador_no_match', {
                has_name: !!compradorNombre,
                has_cuit: true,
            });
            if (compradorNombre) {
                try {
                    sessionStorage.setItem('cdi.pending_create_client', JSON.stringify({
                        cuit: pdfCuit,
                        nombre: compradorNombre,
                        captured_at: new Date().toISOString(),
                    }));
                } catch (_) {}
            }
        } catch (err) {
            console.warn('[upload] auto-match importador skip:', err && err.message);
        }
    }

    function pickClienteForExcel(filename) {
        return new Promise(resolve => {
            if (!CDI.openClientePicker) {
                resolve(null);
                return;
            }
            let settled = false;
            function done(cliente) {
                if (settled) return;
                settled = true;
                resolve(cliente || null);
            }
            CDI.openClientePicker({
                title: 'Elegí cliente para este Excel',
                subtitle: 'Así usamos su mapeo de columnas. También podés cancelar y seguir genérico.',
                onSelect: c => {
                    CDI.track && CDI.track('upload_excel_cliente_selected', {
                        cliente_id: c && c.id,
                        filename: filename,
                    });
                    done(c);
                },
                onCancel: () => done(null),
            });
        });
    }

    async function tryCatalogAutofill(items, vendorName, clienteId) {
        if (!Array.isArray(items) || !items.length) return;
        const vn = String(vendorName || '').trim();
        const cid = String(clienteId || '').trim();
        // Si no hay ni proveedor ni cliente, no hay nada para buscar
        if (!vn && !cid) return;

        try {
            const res = await CDI.api('/api/catalog/lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items, vendor_name: vn, client_id: cid || null }),
            });
            if (!res || !res.ok) return;
            const data = await res.json().catch(() => null);
            if (!data) return;

            // Guardamos el valor previo de cada item para permitir "deshacer"
            const undoSnapshot = items.map(it => ({
                pieza: it.pieza || '',
                origen: it.origen || '',
            }));

            let applied = 0;
            const appliedDetails = [];
            (data.items || []).forEach(m => {
                if (!m || m.source === 'ninguno' || !m.ncm) return;
                const it = items[m.idx];
                if (!it) return;
                let changed = false;
                if ((!it.pieza || String(it.pieza).trim() === '') && m.ncm) {
                    it.pieza = m.ncm;
                    changed = true;
                }
                const curOrigen = String(it.origen || '').toUpperCase();
                if ((!curOrigen || curOrigen === 'XX') && m.origen) {
                    it.origen = m.origen;
                    changed = true;
                }
                // Autofill silencioso de peso unitario desde memoria del cliente.
                if (m.source === 'cliente' && m.peso_unitario_avg && !(it.peso_unitario > 0)) {
                    it.peso_unitario = Number(m.peso_unitario_avg);
                    changed = true;
                }
                if (changed) {
                    it.__autofillSource = m.source; // 'cliente' | 'proveedor'
                    it.__autofillConfidence = m.confidence || 0;
                    applied++;
                    appliedDetails.push({ idx: m.idx, source: m.source, ncm: m.ncm });
                }
            });

            // Dejamos un banner disponible para que lo muestre la siguiente pantalla
            CDI.state = CDI.state || {};
            CDI.state.catalogAutofillBanner = applied > 0 ? {
                aplicados_total: applied,
                aplicados_cliente: data.aplicados_cliente || 0,
                aplicados_proveedor: data.aplicados_proveedor || 0,
                total_items: data.total_items || items.length,
                vendor_nombre: data.vendor_nombre || '',
                cliente_id: cid || null,
                undoSnapshot,
                details: appliedDetails,
                shown: false,
            } : null;

            CDI.track && CDI.track('catalog_autofill', {
                vendor_id: data.vendor_id || '',
                vendor_known: !!data.vendor_known,
                client_used: !!cid,
                total: items.length,
                aplicados_cliente: data.aplicados_cliente || 0,
                aplicados_proveedor: data.aplicados_proveedor || 0,
                applied,
            });
        } catch (err) {
            console.warn('[catalog] autofill skip:', err && err.message);
        }
    }

    // ---------- Carga manual ----------
    let manualModal, manualCliente, manualItemsContainer, manualAddBtn, manualSaveBtn, manualCancelBtn;
    let manualInitialized = false;

    function initManualUpload() {
        if (manualInitialized) return;
        manualModal = $('manualUploadModal');
        manualCliente = $('manualCliente');
        manualItemsContainer = $('manualItems');
        manualAddBtn = $('manualAddItem');
        manualSaveBtn = $('manualSave');
        manualCancelBtn = $('manualCancel');
        if (!manualModal) return;

        const manualBtn = $('uploadManualBtn');
        if (manualBtn) manualBtn.addEventListener('click', openManualModal);
        if (manualCancelBtn) manualCancelBtn.addEventListener('click', closeManualModal);
        if (manualSaveBtn) manualSaveBtn.addEventListener('click', saveManualOperation);
        if (manualAddBtn) manualAddBtn.addEventListener('click', addManualRow);
        manualItemsContainer.addEventListener('click', (e) => {
            const btn = e.target && e.target.closest('.manual-remove');
            if (!btn) return;
            const row = btn.closest('.manual-item-row');
            if (row && manualItemsContainer.querySelectorAll('.manual-item-row').length > 1) {
                row.remove();
            }
        });
        manualInitialized = true;
    }

    async function openManualModal() {
        initManualUpload();
        if (!manualModal) return;
        // Cargar clientes
        try {
            manualCliente.innerHTML = '<option value="">Elegí un cliente…</option>';
            const res = await CDI.api('/api/clientes');
            if (res.ok) {
                const data = await res.json();
                (data.clientes || []).forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = c.nombre + (c.cuit ? ' (' + c.cuit + ')' : '');
                    manualCliente.appendChild(opt);
                });
            }
        } catch (_) {}
        // Reset filas
        manualItemsContainer.innerHTML = '';
        addManualRow();
        manualModal.hidden = false;
        requestAnimationFrame(() => manualModal.classList.add('is-visible'));
        CDI.track && CDI.track('manual_upload_open');
    }

    function closeManualModal() {
        if (!manualModal) return;
        manualModal.classList.remove('is-visible');
        setTimeout(() => { manualModal.hidden = true; }, 220);
    }

    function addManualRow() {
        if (!manualItemsContainer) return;
        const row = document.createElement('div');
        row.className = 'manual-item-row';
        row.innerHTML =
            '<input type="text" class="input manual-desc" placeholder="Descripción del producto" required>' +
            '<input type="number" class="input manual-qty" placeholder="Cantidad" min="1" value="1" required>' +
            '<input type="number" class="input manual-price" placeholder="Precio unitario" min="0" step="0.01" required>' +
            '<input type="text" class="input manual-ncm" placeholder="NCM (opcional)" maxlength="10">' +
            '<button type="button" class="btn btn-ghost btn-sm manual-remove" title="Quitar">×</button>';
        manualItemsContainer.appendChild(row);
    }

    async function saveManualOperation() {
        const clientId = manualCliente.value;
        if (!clientId) {
            if (CDI.toast) CDI.toast.error('Elegí un cliente primero');
            return;
        }
        const rows = manualItemsContainer.querySelectorAll('.manual-item-row');
        const items = [];
        for (const row of rows) {
            const desc = row.querySelector('.manual-desc').value.trim();
            const qty = parseFloat(row.querySelector('.manual-qty').value) || 0;
            const price = parseFloat(row.querySelector('.manual-price').value) || 0;
            const ncm = row.querySelector('.manual-ncm').value.trim();
            if (!desc || qty <= 0 || price < 0) {
                if (CDI.toast) CDI.toast.error('Completá todos los campos obligatorios');
                return;
            }
            items.push({
                descripcion: desc,
                cantidad: qty,
                valor_unitario: price,
                pieza: ncm,
                origen: 'XX',
                peso_unitario: 0,
            });
        }
        if (!items.length) {
            if (CDI.toast) CDI.toast.error('Agregá al menos un producto');
            return;
        }

        manualSaveBtn.disabled = true;
        manualSaveBtn.textContent = 'Guardando…';
        try {
            const res = await CDI.api('/api/operations/manual', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_id: clientId, items: items }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data.detail || 'Error al guardar');
            }

            CDI.state = CDI.state || {};
            CDI.state.filename = 'carga_manual';
            CDI.state.operacion = { comprador_nombre: '', comprador_cuit: '' };
            CDI.state.items = items;
            CDI.state.sourceFormat = 'manual';
            CDI.state.uploadedAt = new Date().toISOString();
            CDI.state.operationSavedFor = null;
            CDI.state.orphanDismissedFor = null;

            // Setear cliente activo
            const clienteNombre = manualCliente.options[manualCliente.selectedIndex].text;
            CDI.setClienteActivo && CDI.setClienteActivo({ id: clientId, nombre: clienteNombre });

            CDI.track('manual_upload_saved', { items: items.length });
            closeManualModal();
            CDI.goTo('review', { fromUpload: true });
        } catch (err) {
            if (CDI.toast) CDI.toast.error(err.message || 'No se pudo guardar');
        } finally {
            manualSaveBtn.disabled = false;
            manualSaveBtn.textContent = 'Guardar y continuar';
        }
    }

    async function downloadBlankTemplate() {
        try {
            const res = await CDI.api('/api/plantillas/avg_blanco');
            if (!res || !res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || ('Error ' + (res && res.status)));
            }
            const blob = await res.blob();
            const ts = new Date().toISOString().slice(0, 10);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'plantilla_avg_' + ts + '.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 2000);
            if (CDI.toast) CDI.toast.success('Plantilla descargada');
            CDI.track && CDI.track('upload_blank_template_download');
        } catch (err) {
            if (CDI.toast) CDI.toast.error(String(err.message || err));
        }
    }

    function simulateOperation() {
        const today = new Date();
        const iso = today.toISOString().slice(0, 10);
        const operacion = {
            numero_factura: 'SIM-' + today.getTime().toString().slice(-6),
            fecha_emision: iso,
            moneda: 'USD',
            incoterm: 'FOB',
            vendedor_nombre: 'Acme Global Trading Co. Ltd.',
            vendedor_id: '91320000MA1K3F2X5P',
            vendedor_pais: 'CN',
            vendedor_direccion: '12F, Tower B, Huamei Plaza, Shenzhen, Guangdong, China',
            comprador_nombre: 'Importadora del Sur SRL',
            comprador_cuit: '30-71234567-8',
            comprador_domicilio: 'Av. Corrientes 1234, CABA, Argentina',
        };
        const items = [
            { pieza: '', descripcion: 'Cable HDMI 2m premium con conectores dorados', origen: 'CN', cantidad: 100, valor_unitario: 2.45, peso_unitario: 0.18, codigo_parte: 'HDMI-2M-GOLD' },
            { pieza: '', descripcion: 'Adaptador USB-C a HDMI 4K', origen: 'CN', cantidad: 50, valor_unitario: 6.90, peso_unitario: 0.09, codigo_parte: 'USBC-HDMI-4K' },
            { pieza: '', descripcion: 'Cargador USB-C 20W con certificación PD', origen: 'CN', cantidad: 75, valor_unitario: 4.80, peso_unitario: 0.14, codigo_parte: 'PD-20W' },
            { pieza: '', descripcion: 'Funda silicona para auriculares inalámbricos', origen: 'CN', cantidad: 200, valor_unitario: 0.85, peso_unitario: 0.03, codigo_parte: 'CASE-TWS' },
            { pieza: '', descripcion: 'Protector de pantalla vidrio templado 6.1"', origen: 'CN', cantidad: 150, valor_unitario: 1.20, peso_unitario: 0.02, codigo_parte: 'SP-61-GLASS' },
        ];

        CDI.state = CDI.state || {};
        CDI.state.filename = 'simulado.pdf';
        CDI.state.operacion = operacion;
        CDI.state.items = items;
        CDI.state.sourceFormat = 'pdf';
        CDI.state.simulated = true;
        CDI.state.uploadedAt = new Date().toISOString();

        CDI.track && CDI.track('upload_simulated', { items: items.length });
        CDI.goTo('review', { fromUpload: true, simulated: true });
    }

    CDI.registerScreen('upload', {
        onEnter() {
            // init() primero: asigna dz y demas refs. Evita el race donde
            // app_v2 dispara goTo('upload') antes de que corra el init propio.
            if (!dz || !dz.isConnected) init();
            hideError();
            setBusy(false);
        },
        onLeave() { /* nothing to cleanup yet */ },
    });

    document.addEventListener('DOMContentLoaded', init);
})();
