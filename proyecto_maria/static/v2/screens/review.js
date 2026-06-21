/* ============================================================
   CDI v2 — Screen 2: Review data (revisar datos del PDF)
   Poblamos inputs con CDI.state.operacion. Editable inline.
   Campos requeridos: comprador_cuit (regex AR).
   "Agregar datos de transporte" colapsado en <details>.
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    // Campos que vienen del PDF; los que aparecen aca se consideran "detectados"
    // para el hint verde. Los que esten vacios se marcan como "faltan".
    const FIELDS = [
        'vendedor_nombre', 'vendedor_id', 'vendedor_pais', 'vendedor_direccion',
        'comprador_nombre', 'comprador_cuit',
        'numero_factura', 'fecha_emision',
        'moneda', 'incoterm',
        'flete', 'seguro',
        // Transporte opcional: si vienen en el PDF los precargamos
        'transporte_medio', 'bl', 'buque',
        'puerto_origen', 'puerto_destino', 'fecha_embarque',
        'contenedor_numero', 'contenedor_tipo', 'contenedor_peso',
        // Bloque "Datos para MARIA" (aduana, tipo destinacion). Opcionales.
        'aduana_codigo', 'tipo_destinacion'
    ];

    // Campos obligatorios para pasar a NCM (los demas son "nice to have")
    // CUIT no es obligatorio: clientes extranjeros no tienen CUIT argentino.
    let REQUIRED = ['moneda', 'incoterm'];

    // Whitelist de monedas habituales en despachos (ISO4217 + alias MARIA)
    const MONEDA_WHITELIST = ['DOL', 'EUR', 'BRL', 'ARS', 'CLP', 'UYU', 'GBP', 'JPY', 'CNY'];

    // Helper: valida CUIT de 11 digitos con digito verificador (algoritmo AFIP).
    // Permite con o sin guiones/espacios. Retorna null si OK, string con error si no.
    function validateCuitAR(raw) {
        const norm = String(raw || '').replace(/[-\s]/g, '');
        if (!/^\d{11}$/.test(norm)) return 'Debe tener 11 digitos (con o sin guiones).';
        const mult = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2];
        let sum = 0;
        for (let i = 0; i < 10; i++) sum += parseInt(norm[i], 10) * mult[i];
        const rem = sum % 11;
        const expected = rem === 0 ? 0 : rem === 1 ? 9 : 11 - rem;
        if (expected !== parseInt(norm[10], 10)) return 'CUIT invalido: el digito verificador no coincide.';
        return null;
    }

    // Para acceder a otros campos del form desde un validator.
    function getFieldValue(name) {
        if (!form) return '';
        const el = form.querySelector('[name="' + name + '"]');
        return el ? (el.value || '').trim() : '';
    }

    // Numero argentino con coma decimal o punto, permite miles con '.' o ',' (best effort)
    function parseNumberAR(raw) {
        if (raw === null || raw === undefined) return NaN;
        let s = String(raw).trim();
        if (!s) return NaN;
        // Si tiene ambos separadores, asumimos que el ultimo es decimal
        const lastDot = s.lastIndexOf('.');
        const lastComma = s.lastIndexOf(',');
        if (lastDot !== -1 && lastComma !== -1) {
            if (lastComma > lastDot) {
                s = s.replace(/\./g, '').replace(',', '.');
            } else {
                s = s.replace(/,/g, '');
            }
        } else if (lastComma !== -1) {
            s = s.replace(',', '.');
        }
        return Number(s);
    }

    // Validacion por campo: retorna string con error o null si OK
    const VALIDATORS = {
        comprador_cuit: (v) => {
            // Opcional: solo validar formato si el usuario lo completa.
            if (!v) return null;
            return validateCuitAR(v);
        },
        vendedor_id: (v) => {
            // Si el vendedor es argentino, exigimos CUIT valido.
            // Si no, aceptamos cualquier ID (tax id extranjero) pero no vacio.
            const pais = (getFieldValue('vendedor_pais') || '').toUpperCase();
            if (!v) return null; // opcional (hay PDFs sin tax id del vendedor)
            if (pais === 'AR' || pais === 'ARG' || pais === 'ARGENTINA') {
                return validateCuitAR(v);
            }
            if (String(v).trim().length < 3) return 'Identificador demasiado corto.';
            return null;
        },
        numero_factura: (v) => {
            if (!v) return null; // opcional (lo completa el despachante si falta)
            const s = String(v).trim();
            if (s.length > 30) return 'Maximo 30 caracteres.';
            if (!/[A-Za-z0-9]/.test(s)) return 'Debe contener al menos una letra o numero.';
            return null;
        },
        moneda: (v) => {
            if (!v) return 'Requerido.';
            const upper = String(v).trim().toUpperCase();
            if (MONEDA_WHITELIST.indexOf(upper) === -1) {
                return 'Moneda no reconocida. Usa DOL, EUR, BRL, ARS, etc.';
            }
            return null;
        },
        incoterm: (v) => {
            if (!v) return null;
            const upper = String(v).trim().toUpperCase();
            if (upper.length !== 3) {
                return 'El Incoterm debe tener 3 letras.';
            }
            return null;
        },
        flete: (v) => {
            if (v === '' || v === null || v === undefined) return null;
            const n = parseNumberAR(v);
            if (!isFinite(n)) return 'Debe ser un numero.';
            if (n < 0) return 'No puede ser negativo.';
            return null;
        },
        seguro: (v) => {
            if (v === '' || v === null || v === undefined) return null;
            const n = parseNumberAR(v);
            if (!isFinite(n)) return 'Debe ser un numero.';
            if (n < 0) return 'No puede ser negativo.';
            return null;
        },
        fecha_emision: (v) => {
            if (!v) return null;
            if (!/^\d{2}\/\d{2}\/(\d{2}|\d{4})$/.test(String(v).trim())) {
                return 'Formato esperado: DD/MM/AAAA';
            }
            return null;
        },
        fecha_embarque: (v) => {
            if (!v) return null;
            if (!/^\d{2}\/\d{2}\/(\d{2}|\d{4})$/.test(String(v).trim())) {
                return 'Formato esperado: DD/MM/AAAA';
            }
            return null;
        }
    };

    let form, continueBtn, missingCountEl, metaPillEl;
    let prorrateoPanel, prorrateoBody, prorrateoCaption, incotermWarningEl;
    let initialized = false;
    let prorrateoTrackedOpen = false;
    let incotermWarningTracked = false;
    // Snapshot de los valores que vinieron del PDF (despues de normalizar) para
    // distinguir despues "Detectado del PDF" de "lo escribio el usuario".
    let initialPdfValues = {};

    // Incoterms que tipicamente ya incluyen flete/seguro en el precio CIF.
    // Si el despachante carga flete/seguro aparte con estos incoterms, suele ser
    // doble contabilizacion.
    const INCOTERM_INCLUYE_FLETE = ['CIF', 'CIP', 'DDP', 'DAP', 'CFR', 'CPT'];

    function $(id) { return document.getElementById(id); }

    // Normaliza fechas al formato DD/MM/AAAA sin importar como venga del PDF.
    // Soporta: ISO YYYY-MM-DD, separadores '-' '/' '.', 8 digitos pegados.
    // Detecta heuristicamente si el año esta primero (YYYY 1900-2100).
    function normalizeDateForInput(raw) {
        if (raw === undefined || raw === null) return '';
        const s = String(raw).trim();
        if (!s) return '';
        const digits = s.replace(/\D/g, '');
        if (digits.length !== 8) return s;
        const first4 = parseInt(digits.slice(0, 4), 10);
        if (first4 >= 1900 && first4 <= 2100) {
            return digits.slice(6, 8) + '/' + digits.slice(4, 6) + '/' + digits.slice(0, 4);
        }
        return digits.slice(0, 2) + '/' + digits.slice(2, 4) + '/' + digits.slice(4, 8);
    }

    function init() {
        if (initialized) return;
        form = $('reviewForm');
        continueBtn = $('reviewContinueBtn');
        missingCountEl = $('reviewMissingCount');
        metaPillEl = $('reviewMetaPill');
        prorrateoPanel = $('reviewProrrateoPanel');
        prorrateoBody = $('reviewProrrateoBody');
        prorrateoCaption = $('reviewProrrateoCaption');
        incotermWarningEl = $('reviewIncotermWarning');
        if (!form) return;

        form.addEventListener('input', onFieldChange);
        form.addEventListener('change', onFieldChange);
        form.addEventListener('submit', (e) => e.preventDefault());

        continueBtn.addEventListener('click', onContinue);

        // Mascara de fecha DD/MM/AAAA en los dos inputs de fecha
        if (typeof CDI.maskDate === 'function') {
            ['fecha_emision', 'fecha_embarque'].forEach(name => {
                const el = form.querySelector('[name="' + name + '"]');
                if (el) CDI.maskDate(el);
            });
        }

        // Detalles abrir/cerrar: tracking solo
        const details = $('transportBlock');
        if (details) {
            details.addEventListener('toggle', () => {
                CDI.track(details.open ? 'transport_opened' : 'transport_closed');
            });
        }

        // Panel de prorrateo CIF: track cuando el despachante lo expande por primera vez
        if (prorrateoPanel) {
            prorrateoPanel.addEventListener('toggle', () => {
                if (prorrateoPanel.open && !prorrateoTrackedOpen) {
                    prorrateoTrackedOpen = true;
                    CDI.track('prorrateo_panel_opened');
                }
            });
        }

        // Reaccionar a cambio de cliente activo (desde drawer)
        document.addEventListener('cdi:cliente-activo-cambio', () => {
            if (document.querySelector('[data-screen="review"].is-active')) {
                applyClienteActivo();
                renderMetaPill();
                validateAll();
            }
        });

        initialized = true;
    }

    // Normalizar alias comunes del backend a los values del form
    const MONEDA_ALIAS = { USD: 'DOL', DOLARES: 'DOL', DOLAR: 'DOL', EURO: 'EUR', REAL: 'BRL' };
    const INCOTERM_WHITELIST = ['FOB', 'CIF', 'CFR', 'FCA', 'EXW', 'DAP', 'DDP'];

    function normalizeValueForField(name, val) {
        if (val === undefined || val === null || val === '') return '';
        if (name === 'moneda') {
            const upper = String(val).trim().toUpperCase();
            return MONEDA_ALIAS[upper] || upper;
        }
        if (name === 'incoterm') {
            const upper = String(val).trim().toUpperCase();
            if (upper.length === 3) return upper;
            const m = upper.match(/\b([A-Z]{3})\b/);
            return m ? m[1] : upper.slice(0, 3);
        }
        if (name === 'flete' || name === 'seguro') {
            const n = Number(val);
            return isFinite(n) ? formatNumber(n) : '';
        }
        if (name === 'fecha_emision' || name === 'fecha_embarque') {
            return normalizeDateForInput(val);
        }
        return String(val);
    }

    let fieldsFromUserDefaults = {};
    function applyUserDefaults(op) {
        // Si el despachante guardo en su perfil un puerto/aduana/tipo destinacion
        // habitual, lo usamos cuando la operacion viene vacia. Asi evita tener
        // que abrir el bloque "Datos para MARIA" cada vez que crea una operacion.
        fieldsFromUserDefaults = {};
        const defaults = (CDI && CDI.userDefaults) || {};
        const fieldsFromUser = {
            aduana_codigo: defaults.aduana_codigo,
            puerto_destino: defaults.puerto_destino,
            tipo_destinacion: defaults.tipo_destinacion
        };
        Object.keys(fieldsFromUser).forEach(k => {
            const v = String(fieldsFromUser[k] || '').trim();
            const current = String(op[k] || '').trim();
            if (v && !current) {
                op[k] = v;
                fieldsFromUserDefaults[k] = v;
            }
        });
    }

    function populate() {
        init();
        if (!form) return;
        const op = (CDI.state && CDI.state.operacion) || {};
        applyUserDefaults(op);
        initialPdfValues = {};
        FIELDS.forEach(key => {
            const el = form.querySelector('[name="' + key + '"]');
            if (!el) return;
            const normalized = normalizeValueForField(key, op[key]);
            el.value = normalized;
            // Si el valor viene del default del perfil (no del PDF), NO lo
            // marcamos como "Detectado del PDF" porque seria mentira.
            if (
                normalized !== '' && normalized !== 0 && String(normalized).trim() !== '0'
                && !fieldsFromUserDefaults[key]
            ) {
                initialPdfValues[key] = String(normalized).trim();
            }
            // Sincronizar de vuelta al state (por si normalizamos USD->DOL)
            if (normalized !== op[key]) {
                if (el.type === 'number') {
                    op[key] = normalized === '' ? 0 : Number(normalized);
                } else {
                    op[key] = normalized;
                }
            }
        });
        CDI.state.operacion = op;

        // Aplica el cliente activo (auto-prefill; sin reemplazar al elegido antes)
        applyClienteActivo();
        maybeShowPendingImporterBanner();

        // Auto-expandir bloque de transporte si el PDF trae algo util
        const details = $('transportBlock');
        if (details && hasTransportData(op) && !details.open) {
            details.open = true;
        }

        // Auto-expandir bloque "Datos para MARIA" si tiene valores no-default
        const aduanaBlock = $('aduanaBlock');
        if (aduanaBlock && hasAduanaCustom(op) && !aduanaBlock.open) {
            aduanaBlock.open = true;
        }

        renderMetaPill();
        recomputeHints();
        validateAll({ silent: true });
        renderIncotermWarning();
        renderProrrateoPanel();
    }

    function hasTransportData(op) {
        const keys = ['transporte_medio', 'bl', 'buque',
            'puerto_origen', 'puerto_destino', 'fecha_embarque',
            'contenedor_numero', 'contenedor_tipo', 'contenedor_peso'];
        return keys.some(k => {
            const v = op[k];
            if (v === undefined || v === null || v === '') return false;
            if (typeof v === 'number' && v === 0) return false;
            return true;
        });
    }

    // Devuelve true si el usuario customizo aduana/tipo destinacion
    // (algun valor cargado distinto al default). Asi expandimos el bloque
    // automatico para mostrarle lo que tiene seteado.
    function hasAduanaCustom(op) {
        const aduana = String(op.aduana_codigo || '').trim();
        const tipo = String(op.tipo_destinacion || '').trim().toUpperCase();
        if (aduana && aduana !== '001') return true;
        if (tipo && tipo !== 'IC04') return true;
        return false;
    }

    /* ---------- Integracion con cliente activo ----------
       Sin “swap silencioso”: si ya elegís un cliente, no lo reemplaza el PDF.
       Sin cliente activo: si tenés ese CUIT en tu lista se usa; si no, el PDF queda editable.
       */
    function applyClienteActivo() {
        const activo = CDI.getClienteActivo && CDI.getClienteActivo();
        const op = CDI.state.operacion = CDI.state.operacion || {};

        // Limpiar cualquier prompt anterior
        const saveBtn = document.getElementById('reviewSaveAsClient');
        if (saveBtn) saveBtn.remove();

        const pdfCuit = CDI.normalizeCuit(op.comprador_cuit);
        const pdfNombre = String(op.comprador_nombre || '').trim();
        const pdfHasComprador = !!(pdfCuit || pdfNombre);

        if (!activo) {
            maybeRenderSaveAsCliente(pdfCuit, pdfNombre, op);
            return;
        }

        const clienteCuit = CDI.normalizeCuit(activo.cuit);

        if (!pdfHasComprador) {
            op.comprador_nombre = activo.nombre || '';
            op.comprador_cuit = clienteCuit;
            op.comprador_domicilio = activo.direccion || '';
            op.comprador_fecha_inic_activ = activo.fecha_inic_activ || '';
            setField('comprador_nombre', op.comprador_nombre);
            setField('comprador_cuit', CDI.formatCuit(op.comprador_cuit));
            markHintAsCliente('comprador_nombre');
            markHintAsCliente('comprador_cuit');
            return;
        }

        if (clienteCuit && pdfCuit && clienteCuit === pdfCuit) {
            if (activo.direccion) op.comprador_domicilio = activo.direccion;
            if (activo.fecha_inic_activ) op.comprador_fecha_inic_activ = activo.fecha_inic_activ;
            markHintAsCliente('comprador_cuit');
            return;
        }

        // Cliente activo y PDF difieren: no cambiamos el cliente solo porque
        // el PDF coincide con otro importador ya guardado.
        if (pdfCuit && pdfCuit.length === 11) {
            const cache = CDI.getClientesCache ? CDI.getClientesCache() : [];
            const match = CDI.matchClienteByCuit ? CDI.matchClienteByCuit(pdfCuit, cache) : null;
            if (match) {
                CDI.track && CDI.track('importador_pdf_matches_other_kept_activo', {
                    pdf_cuit: pdfCuit,
                    activo_cuit: clienteCuit || '',
                });
            }
        }

        // Sin coincidencias / sin swap: mismo cliente activo, datos del PDF;
        // ofrecemos alta rapida cuando el PDF trae un CUIT nuevo para tu lista.
        maybeRenderSaveAsCliente(pdfCuit, pdfNombre, op);
    }

    function setField(name, value) {
        const el = form.querySelector('[name="' + name + '"]');
        if (el) el.value = value == null ? '' : String(value);
    }

    function markHintAsCliente(name) {
        const hintEl = form.querySelector('[data-hint-for="' + name + '"]');
        if (!hintEl) return;
        hintEl.classList.remove('is-detected', 'is-missing');
        hintEl.classList.add('is-cliente');
        hintEl.textContent = 'Desde cliente activo';
    }

    function maybeRenderSaveAsCliente(pdfCuit, pdfNombre, op) {
        if (!pdfCuit || pdfCuit.length !== 11) return;
        const cache = CDI.getClientesCache ? CDI.getClientesCache() : [];
        const match = CDI.matchClienteByCuit(pdfCuit, cache);
        if (match) return; // Ya existe, no ofrecer guardar
        const cuitField = form.querySelector('[data-hint-for="comprador_cuit"]');
        if (!cuitField) return;
        // Evitar duplicar el boton
        if (document.getElementById('reviewSaveAsClient')) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.id = 'reviewSaveAsClient';
        btn.className = 'field-action';
        btn.innerHTML =
            '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>' +
            'Guardar como cliente';
        btn.addEventListener('click', () => {
            CDI.track('cliente_save_from_review');
            if (!CDI.openClientesDrawer) return;
            CDI.openClientesDrawer({
                openForm: true,
                prefill: {
                    nombre: pdfNombre || '',
                    cuit: pdfCuit,
                    direccion: ''
                }
            });
        });
        cuitField.appendChild(btn);
    }

    function formatNumber(n) {
        // Mostrar flete/seguro limpio (sin .0 innecesario)
        if (!isFinite(n)) return '';
        return (n === Math.floor(n)) ? String(n) : String(Number(n).toFixed(2));
    }

    function fmtUSD(n) {
        const v = Number(n);
        if (!isFinite(v)) return 'USD 0.00';
        return 'USD ' + v.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // Replica exacta de la formula del backend (maria_generator.py L248-259):
    //   valor_total = item.valor_total || cantidad * valor_unitario
    //   proporcion = valor_total / fob_total
    //   flete_item = flete * proporcion
    //   seguro_item = seguro * proporcion
    //   cif_item   = valor_total + flete_item + seguro_item
    function calcProrrateoCIF(items, flete, seguro) {
        const list = Array.isArray(items) ? items : [];
        const rows = list.map((it, idx) => {
            const cantidad = Number(it && it.cantidad) || 0;
            const valorUnit = Number(it && it.valor_unitario) || 0;
            const vt = (it && it.valor_total !== undefined && it.valor_total !== null && Number(it.valor_total) > 0)
                ? Number(it.valor_total)
                : (cantidad * valorUnit);
            return {
                idx: idx,
                descripcion: String((it && (it.descripcion || it.pieza)) || ('Item ' + (idx + 1))),
                pieza: String((it && it.pieza) || ''),
                fob: vt
            };
        });
        const fobTotal = rows.reduce((acc, r) => acc + (isFinite(r.fob) ? r.fob : 0), 0);
        const fleteNum = Math.max(0, Number(flete) || 0);
        const seguroNum = Math.max(0, Number(seguro) || 0);
        const enriched = rows.map(r => {
            const proporcion = fobTotal > 0 ? (r.fob / fobTotal) : 0;
            const fleteItem = fleteNum * proporcion;
            const seguroItem = seguroNum * proporcion;
            return Object.assign({}, r, {
                proporcion: proporcion,
                flete: fleteItem,
                seguro: seguroItem,
                cif: r.fob + fleteItem + seguroItem
            });
        });
        return {
            rows: enriched,
            totals: {
                fob: fobTotal,
                flete: fleteNum,
                seguro: seguroNum,
                cif: fobTotal + fleteNum + seguroNum
            }
        };
    }

    function renderProrrateoPanel() {
        if (!prorrateoPanel) return;
        const op = (CDI.state && CDI.state.operacion) || {};
        const items = (CDI.state && CDI.state.items) || [];
        const flete = parseNumberAR(op.flete) || 0;
        const seguro = parseNumberAR(op.seguro) || 0;

        // Panel visible solo si hay flete/seguro y hay items
        if ((flete <= 0 && seguro <= 0) || items.length === 0) {
            prorrateoPanel.hidden = true;
            return;
        }
        prorrateoPanel.hidden = false;

        const res = calcProrrateoCIF(items, flete, seguro);
        const rows = res.rows.map((r, idx) => {
            const label = r.descripcion.length > 60 ? r.descripcion.slice(0, 57) + '…' : r.descripcion;
            const piezaBadge = r.pieza
                ? ' <span class="cx-prorrateo-pieza">' + CDI.escapeHtml(r.pieza) + '</span>'
                : '';
            return '<tr>' +
                '<td class="cx-prorrateo-idx">' + (idx + 1) + '</td>' +
                '<td class="cx-prorrateo-desc">' + CDI.escapeHtml(label) + piezaBadge + '</td>' +
                '<td class="cx-prorrateo-num">' + fmtUSD(r.fob) + '</td>' +
                '<td class="cx-prorrateo-num">' + fmtUSD(r.flete) + '</td>' +
                '<td class="cx-prorrateo-num">' + fmtUSD(r.seguro) + '</td>' +
                '<td class="cx-prorrateo-num cx-prorrateo-cif">' + fmtUSD(r.cif) + '</td>' +
                '</tr>';
        }).join('');

        const totals = res.totals;
        const totalsRow = '<tr class="cx-prorrateo-totals">' +
            '<td></td>' +
            '<td><strong>Total</strong></td>' +
            '<td class="cx-prorrateo-num"><strong>' + fmtUSD(totals.fob) + '</strong></td>' +
            '<td class="cx-prorrateo-num"><strong>' + fmtUSD(totals.flete) + '</strong></td>' +
            '<td class="cx-prorrateo-num"><strong>' + fmtUSD(totals.seguro) + '</strong></td>' +
            '<td class="cx-prorrateo-num cx-prorrateo-cif"><strong>' + fmtUSD(totals.cif) + '</strong></td>' +
            '</tr>';

        if (prorrateoBody) {
            prorrateoBody.innerHTML =
                '<div class="cx-prorrateo-table-wrap">' +
                '<table class="cx-prorrateo-table">' +
                '<thead><tr>' +
                '<th>#</th>' +
                '<th>Item</th>' +
                '<th class="cx-prorrateo-num">FOB</th>' +
                '<th class="cx-prorrateo-num">Flete</th>' +
                '<th class="cx-prorrateo-num">Seguro</th>' +
                '<th class="cx-prorrateo-num">CIF</th>' +
                '</tr></thead>' +
                '<tbody>' + rows + totalsRow + '</tbody>' +
                '</table></div>' +
                '<p class="cx-prorrateo-note">Prorrateo proporcional al FOB de cada item (mismo criterio que el generador MARIA). Se recalcula automaticamente al cambiar flete, seguro o items.</p>';
        }

        if (prorrateoCaption) {
            prorrateoCaption.textContent =
                'Total CIF estimado ' + fmtUSD(totals.cif) +
                ' (' + res.rows.length + ' item' + (res.rows.length === 1 ? '' : 's') + ')';
        }
    }

    function renderIncotermWarning() {
        if (!incotermWarningEl) return;
        const op = (CDI.state && CDI.state.operacion) || {};
        const incoterm = String(op.incoterm || '').trim().toUpperCase();
        const flete = parseNumberAR(op.flete) || 0;
        const seguro = parseNumberAR(op.seguro) || 0;
        const tieneGastos = (flete > 0 || seguro > 0);
        const incluye = INCOTERM_INCLUYE_FLETE.indexOf(incoterm) !== -1;

        if (tieneGastos && incluye) {
            incotermWarningEl.hidden = false;
            incotermWarningEl.innerHTML =
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
                '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>' +
                '<span>El incoterm <b>' + CDI.escapeHtml(incoterm) + '</b> normalmente ya incluye ' +
                (incoterm === 'CFR' || incoterm === 'CPT' ? 'flete' : 'flete y seguro') +
                ' en el precio. Verifica que no los estes sumando dos veces.</span>';
            if (!incotermWarningTracked) {
                incotermWarningTracked = true;
                CDI.track('incoterm_flete_warning_shown', { incoterm: incoterm });
            }
        } else {
            incotermWarningEl.hidden = true;
            // permitir volver a trackear si el warning reaparece en otro cambio
            if (!tieneGastos || !incluye) incotermWarningTracked = false;
        }
    }

    function renderMetaPill() {
        if (!metaPillEl) return;
        const op = (CDI.state && CDI.state.operacion) || {};
        const items = (CDI.state && CDI.state.items) || [];
        const activo = CDI.getClienteActivo && CDI.getClienteActivo();
        const parts = [];
        if (activo && activo.nombre) {
            parts.push('<span class="pill pill-accent">' +
                '<span class="dot-status is-success"></span>' +
                CDI.escapeHtml(activo.nombre) +
                '</span>');
        }
        if (CDI.state && CDI.state.filename) {
            parts.push('<span>' + CDI.escapeHtml(CDI.state.filename) + '</span>');
        }
        parts.push('<span>' + items.length + ' items detectados</span>');
        if (op.moneda && op.incoterm) {
            parts.push('<span>' + CDI.escapeHtml(op.moneda) + ' · ' + CDI.escapeHtml(op.incoterm) + '</span>');
        }
        metaPillEl.innerHTML = parts.join('<span class="ctx-sep">·</span>');
    }

    function onFieldChange(ev) {
        const el = ev.target;
        if (!el || !el.name) return;
        const op = CDI.state.operacion = CDI.state.operacion || {};
        let value = el.value;
        if (el.type === 'number') {
            value = value === '' ? 0 : Number(value);
        } else if (typeof value === 'string') {
            value = value.trim();
        }
        op[el.name] = value;

        // Solo este campo: actualizar hint + error
        updateFieldHint(el.name);
        validateField(el.name);
        renderMissingCount();
        updateContinueEnabled();

        // Re-render del panel de prorrateo y warning de incoterm si corresponde
        if (el.name === 'flete' || el.name === 'seguro' || el.name === 'incoterm') {
            renderIncotermWarning();
            renderProrrateoPanel();
        }
    }

    function updateFieldHint(name) {
        const hintEl = form.querySelector('[data-hint-for="' + name + '"]');
        if (!hintEl) return;
        // Si ya esta marcado como "Desde cliente activo", respetarlo y salir.
        if (hintEl.classList.contains('is-cliente')) return;

        const el = form.querySelector('[name="' + name + '"]');
        const val = el && el.value && String(el.value).trim();

        // Flete/seguro tienen su propio hint estatico, no tocar
        if (name === 'flete' || name === 'seguro') return;

        hintEl.classList.remove('is-detected', 'is-missing');
        if (val) {
            const fromPdf = initialPdfValues[name];
            if (fromPdf && fromPdf === val) {
                hintEl.classList.add('is-detected');
                hintEl.textContent = 'Detectado del PDF';
            } else {
                // El usuario lo edito o lo cargo a mano: sin pista verde,
                // que no transmita "esto vino del PDF" si no es cierto.
                hintEl.textContent = '';
            }
        } else {
            if (REQUIRED.indexOf(name) !== -1) {
                hintEl.classList.add('is-missing');
                hintEl.textContent = 'Falta completar';
            } else {
                hintEl.textContent = '';
            }
        }
    }

    function recomputeHints() {
        FIELDS.forEach(updateFieldHint);
    }

    function validateField(name, opts) {
        const silent = !!(opts && opts.silent);
        const el = form.querySelector('[name="' + name + '"]');
        const errEl = form.querySelector('[data-error-for="' + name + '"]');
        if (!el) return true;
        const validator = VALIDATORS[name];
        const value = (el.value || '').trim();

        let errMsg = null;
        if (validator) errMsg = validator(value);

        if (errMsg) {
            if (!silent) {
                el.classList.add('is-error');
                if (errEl) { errEl.textContent = errMsg; errEl.hidden = false; }
            }
            return false;
        }
        el.classList.remove('is-error');
        if (errEl) { errEl.hidden = true; errEl.textContent = ''; }
        return true;
    }

    function validateAll(opts) {
        let okCount = 0;
        FIELDS.forEach(name => { if (validateField(name, opts)) okCount++; });
        renderMissingCount();
        updateContinueEnabled();
        return okCount;
    }

    function missingRequired() {
        const op = (CDI.state && CDI.state.operacion) || {};
        const missing = REQUIRED.filter(name => {
            const v = op[name];
            if (v === undefined || v === null || v === '') return true;
            const validator = VALIDATORS[name];
            if (validator && validator(v)) return true;
            return false;
        });
        
        if (!CDI.state || !CDI.state.items || CDI.state.items.length === 0) {
            missing.push('_no_items');
        }
        
        if (!CDI.state || !CDI.state.clienteActivo) {
            missing.push('_no_cliente');
        }
        
        return missing;
    }

    const REQUIRED_LABELS = {
        comprador_cuit: 'CUIT del importador',
        moneda: 'Moneda',
        incoterm: 'Incoterm',
        vendedor_nombre: 'Razón social del proveedor',
        comprador_nombre: 'Razón social del importador',
        numero_factura: 'Número de factura',
        fecha_emision: 'Fecha de emisión',
        _no_items: 'Al menos 1 producto',
        _no_cliente: 'Cliente (Importador) asignado'
    };

    function renderMissingCount() {
        if (!missingCountEl) return;
        const missing = missingRequired();
        missingCountEl.innerHTML = '';
        if (missing.length === 0) return;

        const labels = missing.map(n => REQUIRED_LABELS[n] || n);
        const textNode = document.createTextNode((missing.length === 1 ? 'Falta: ' : 'Faltan: ') + labels.join(', '));
        missingCountEl.appendChild(textNode);

        // Los botones de crear/asignar cliente viven en el banner azul de arriba (reviewPendingImporterBanner).
        // Solo mostramos el aviso de texto para no duplicar acciones.
    }

    function updateContinueEnabled() {
        if (!continueBtn) return;
        const missing = missingRequired();
        continueBtn.disabled = missing.length > 0;
    }

    function onContinue() {
        const allValid = FIELDS.every(validateField);
        const missing = missingRequired();
        if (!allValid || missing.length > 0) {
            const firstErr = form.querySelector('.input.is-error') ||
                             form.querySelector('[name="' + missing[0] + '"]');
            if (firstErr) {
                try { firstErr.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (_) {}
                try { firstErr.focus({ preventScroll: true }); } catch (_) { firstErr.focus(); }
            }
            CDI.track('review_continue_blocked', { missing: missing });
            return;
        }
        // Snapshot final en state
        CDI.state = CDI.state || {};
        CDI.state.operacion = Object.assign({}, CDI.state.operacion || {});
        CDI.track('review_confirmed', {
            items: (CDI.state.items || []).length,
            has_transport: !!(CDI.state.operacion && (
                CDI.state.operacion.bl || CDI.state.operacion.buque ||
                CDI.state.operacion.contenedor_numero
            ))
        });
        CDI.goTo('ncm', { fromReview: true });
    }

    const _PENDING_IMPORTADOR_KEY = 'cdi.pending_create_client';

    function hidePendingImporterBanner() {
        const el = document.getElementById('reviewPendingImporterBanner');
        if (!el) return;
        el.hidden = true;
        el.setAttribute('aria-hidden', 'true');
    }

    function showReviewClientSuccess(title, text) {
        const el = document.getElementById('reviewClientSuccess');
        if (!el) return;
        const titleEl = el.querySelector('[data-client-success-title]');
        const textEl = el.querySelector('[data-client-success-text]');
        if (titleEl) titleEl.textContent = title || '';
        if (textEl) textEl.textContent = text || '';
        el.hidden = false;
        try { el.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } catch (_) {}
    }

    function maybeShowPendingImporterBanner() {
        const el = document.getElementById('reviewPendingImporterBanner');
        if (!form || !el) return;

        let raw = '';
        try { raw = sessionStorage.getItem(_PENDING_IMPORTADOR_KEY) || ''; } catch (_) {}
        const activo = CDI.getClienteActivo && CDI.getClienteActivo();
        if (!raw || activo) {
            hidePendingImporterBanner();
            return;
        }

        let data = null;
        try {
            data = JSON.parse(raw);
        } catch (_) {
            hidePendingImporterBanner();
            return;
        }
        const nom = String((data && data.nombre) || '').trim();
        const cDigits = CDI.normalizeCuit && CDI.normalizeCuit(data && data.cuit);
        if (!data || !nom) {
            hidePendingImporterBanner();
            return;
        }
        const hasValidCuit = !!(cDigits && cDigits.length === 11);

        el.hidden = false;
        el.removeAttribute('aria-hidden');
        const title = el.querySelector('[data-banner-title]');
        const subtitle = el.querySelector('[data-banner-subtitle]');
        if (title) title.textContent = 'Este importador no está en tus clientes';
        if (subtitle) {
            subtitle.textContent =
                hasValidCuit
                    ? nom + ' · CUIT ' + (CDI.formatCuit ? CDI.formatCuit(cDigits) : cDigits)
                    : nom + ' · CUIT pendiente de completar';
        }

        const btnCrear = el.querySelector('[data-banner-crear]');
        const btnAsignar = el.querySelector('[data-banner-asignar]');
        const btnIgn = el.querySelector('[data-banner-ignorar]');
        const btnNuevo = el.querySelector('[data-banner-nuevo]');
        const quickForm = document.getElementById('reviewQuickClientForm');
        if (btnNuevo && quickForm) {
            btnNuevo.onclick = () => {
                CDI.track && CDI.track('importador_quick_form_open');
                quickForm.hidden = false;
                btnNuevo.hidden = true;
                const nombreInput = quickForm.querySelector('[name="nombre"]');
                const cuitInput = quickForm.querySelector('[name="cuit"]');
                if (nombreInput) nombreInput.value = nom || '';
                if (cuitInput && cDigits) cuitInput.value = CDI.formatCuit ? CDI.formatCuit(cDigits) : cDigits;
                setTimeout(() => { if (nombreInput) nombreInput.focus(); }, 50);
            };
            const btnCancel = quickForm.querySelector('[data-banner-nuevo-cancel]');
            if (btnCancel) {
                btnCancel.onclick = () => {
                    quickForm.hidden = true;
                    if (btnNuevo) btnNuevo.hidden = false;
                };
            }
            quickForm.onsubmit = (ev) => {
                ev.preventDefault();
                const nombreInput = quickForm.querySelector('[name="nombre"]');
                const cuitInput = quickForm.querySelector('[name="cuit"]');
                const formData = {
                    nombre: (nombreInput && nombreInput.value || '').trim(),
                    cuit: CDI.normalizeCuit && cuitInput ? CDI.normalizeCuit(cuitInput.value) : ''
                };
                crearClienteDesdeForm(formData, quickForm);
            };
        }
        if (btnCrear) {
            btnCrear.onclick = () => crearClienteDesdeBanner(data, btnCrear);
        }
        if (btnAsignar) {
            btnAsignar.onclick = () => asignarExistenteDesdeBanner(data);
        }
        if (btnIgn) {
            btnIgn.onclick = () => {
                try { sessionStorage.removeItem(_PENDING_IMPORTADOR_KEY); } catch (_) {}
                hidePendingImporterBanner();
                CDI.track && CDI.track('importador_pending_dismiss');
            };
        }
    }

    // Buscamos si el user ya tiene un cliente con este CUIT antes de crear:
    // evita duplicados que hoy el backend NO valida.
    async function lookupClienteByCuit(cuit) {
        try {
            const res = await CDI.api('/api/clientes/by-cuit/' + encodeURIComponent(cuit));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) return null;
            if (data.match === 'exact' && data.cliente) return data.cliente;
            return null;
        } catch (_) { return null; }
    }

    async function crearClienteDesdeBanner(data, btn) {
        const nombre = String((data && data.nombre) || '').trim();
        const cuitFromField = getFieldValue('comprador_cuit');
        const cuitRaw = cuitFromField || (data && data.cuit);
        const cuit = CDI.normalizeCuit && CDI.normalizeCuit(cuitRaw);
        if (!nombre) return;
        CDI.track && CDI.track('importador_quick_create_clicked');
        if (btn) btn.disabled = true;
        try {
            // Pre-check: si ya tenemos a alguien con este CUIT, ofrecer usar ese.
            const existente = (cuit && cuit.length === 11) ? await lookupClienteByCuit(cuit) : null;
            if (existente) {
                CDI.track && CDI.track('importador_create_blocked_by_cuit_match');
                const ok = await CDI.confirm({
                    title: 'Cliente ya existente',
                    lead: 'Ya tenés a "' + (existente.nombre || 'este cliente') + '" con este CUIT.',
                    text: 'Podés usar ese cliente en esta operación en lugar de crear uno duplicado.',
                    acceptText: 'Usar cliente',
                    cancelText: 'No por ahora',
                    kind: 'info',
                });
                if (ok) {
                    CDI.setClienteActivo(existente);
                    try { sessionStorage.removeItem(_PENDING_IMPORTADOR_KEY); } catch (_) {}
                    hidePendingImporterBanner();
                    populate();
                    showReviewClientSuccess(
                        'Cliente asignado a esta operación',
                        (existente.nombre || 'El cliente') + ' quedó asociado. La próxima vez se detecta por CUIT.'
                    );
                    CDI.toast && CDI.toast('Listo', 'Cliente activado: ' + (existente.nombre || ''), 'success');
                }
                return;
            }
            const body = { nombre: nombre };
            if (cuit && cuit.length === 11) body.cuit = cuit;
            const res = await CDI.api('/api/clientes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const out = await res.json().catch(() => ({}));
            if (!res.ok || !out.success || !out.cliente) {
                const det = humanizeApiError(out.detail, 'No se pudo crear el cliente');
                CDI.toast && CDI.toast('No se pudo crear', det, 'error');
                return;
            }
            CDI.clientesCache = [];
            CDI.setClienteActivo(out.cliente);
            try { sessionStorage.removeItem(_PENDING_IMPORTADOR_KEY); } catch (_) {}
            hidePendingImporterBanner();
            populate();
            showReviewClientSuccess(
                'Cliente creado con éxito',
                (out.cliente.nombre || nombre) + ' quedó asociado a esta operación. La próxima vez se detecta por CUIT.'
            );
            CDI.toast && CDI.toast('Listo', 'Cliente guardado y activado', 'success');
            CDI.track && CDI.track('importador_quick_create_ok', { has_cuit: !!body.cuit });
        } catch (err) {
            CDI.toast && CDI.toast(
                'Error',
                'Podés cargarlo desde la pantalla Clientes.',
                'error'
            );
            console.warn('[review] crear cliente banner', err && err.message);
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    async function crearClienteDesdeForm(data, formEl) {
        const nombre = String((data && data.nombre) || '').trim();
        const cuit = CDI.normalizeCuit && CDI.normalizeCuit(data && data.cuit);
        if (!nombre) {
            CDI.toast && CDI.toast('Falta nombre', 'La razón social es obligatoria.', 'error');
            return;
        }
        const submitBtn = formEl && formEl.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;
        try {
            const existente = (cuit && cuit.length === 11) ? await lookupClienteByCuit(cuit) : null;
            if (existente) {
                const ok = await CDI.confirm({
                    title: 'Cliente ya existente',
                    lead: 'Ya tenés a "' + (existente.nombre || 'este cliente') + '" con este CUIT.',
                    text: '¿Usar este cliente en la operación?',
                    acceptText: 'Usar cliente',
                    cancelText: 'No por ahora',
                    kind: 'info',
                });
                if (ok) {
                    CDI.setClienteActivo(existente);
                    try { sessionStorage.removeItem(_PENDING_IMPORTADOR_KEY); } catch (_) {}
                    hidePendingImporterBanner();
                    populate();
                    showReviewClientSuccess('Cliente asignado a esta operación', (existente.nombre || 'El cliente') + ' quedó asociado.');
                }
                return;
            }
            const body = { nombre: nombre };
            if (cuit && cuit.length === 11) body.cuit = cuit;
            const res = await CDI.api('/api/clientes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const out = await res.json().catch(() => ({}));
            if (!res.ok || !out.success || !out.cliente) {
                const det = humanizeApiError(out.detail, 'No se pudo crear el cliente');
                CDI.toast && CDI.toast('No se pudo crear', det, 'error');
                return;
            }
            CDI.clientesCache = [];
            CDI.setClienteActivo(out.cliente);
            try { sessionStorage.removeItem(_PENDING_IMPORTADOR_KEY); } catch (_) {}
            hidePendingImporterBanner();
            populate();
            showReviewClientSuccess(
                'Cliente creado con éxito',
                (out.cliente.nombre || nombre) + ' quedó asociado a esta operación.'
            );
            CDI.toast && CDI.toast('Listo', 'Cliente guardado y activado', 'success');
            CDI.track && CDI.track('importador_form_create_ok', { has_cuit: !!body.cuit });
        } catch (err) {
            CDI.toast && CDI.toast('Error', 'Podés cargarlo desde la pantalla Clientes.', 'error');
            console.warn('[review] crear cliente form', err && err.message);
        } finally {
            if (submitBtn) submitBtn.disabled = false;
        }
    }

    // "Asignar a uno existente": abre picker; si el cliente no tenía CUIT
    // y nadie más lo tiene, le sumamos el del PDF.
    function asignarExistenteDesdeBanner(data) {
        if (!CDI.openClientePicker) return;
        const cuitFromField = getFieldValue('comprador_cuit');
        const pdfCuit = CDI.normalizeCuit && CDI.normalizeCuit(cuitFromField || (data && data.cuit));
        CDI.track && CDI.track('importador_assign_existing_clicked');
        CDI.openClientePicker({
            title: 'Asignar a un cliente existente',
            subtitle: 'Buscá por nombre o CUIT',
            onSelect: async (c) => {
                CDI.setClienteActivo(c);
                try { sessionStorage.removeItem(_PENDING_IMPORTADOR_KEY); } catch (_) {}
                hidePendingImporterBanner();
                populate();
                showReviewClientSuccess(
                    'Cliente asignado a esta operación',
                    (c.nombre || 'El cliente') + ' quedó asociado a esta operación.'
                );
                CDI.track && CDI.track('importador_assign_existing_ok', { cliente_id: c.id });

                // Si el cliente elegido no tenía CUIT y el del PDF no choca con
                // otro cliente, se lo cargamos. Si choca, no tocamos nada.
                if (pdfCuit && pdfCuit.length === 11 && !c.cuit) {
                    const otro = await lookupClienteByCuit(pdfCuit);
                    if (otro && otro.id !== c.id) {
                        CDI.toast && CDI.toast(
                            'Asignado',
                            'El CUIT del PDF ya está en otro cliente; lo dejamos como estaba.',
                            'success'
                        );
                        return;
                    }
                    try {
                        const res = await CDI.api('/api/clientes/' + encodeURIComponent(c.id), {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ cuit: pdfCuit }),
                        });
                        const out = await res.json().catch(() => ({}));
                        if (res.ok && out && out.success && out.cliente) {
                            CDI.clientesCache = [];
                            CDI.setClienteActivo(out.cliente);
                            CDI.track && CDI.track('importador_cuit_attached_to_existing', { cliente_id: c.id });
                            showReviewClientSuccess(
                                'Cliente asignado y actualizado',
                                (out.cliente.nombre || c.nombre || 'El cliente') + ' quedó asociado con el CUIT del PDF.'
                            );
                            CDI.toast && CDI.toast('Listo', 'Cliente actualizado con CUIT del PDF', 'success');
                            return;
                        }
                    } catch (_) {}
                    CDI.toast && CDI.toast('Asignado', (c.nombre || '') + ' quedó asociado a esta operación', 'success');
                } else {
                    CDI.toast && CDI.toast('Asignado', (c.nombre || '') + ' quedó asociado a esta operación', 'success');
                }
            },
        });
    }

    function humanizeApiError(detail, fallback) {
        if (!detail) return fallback;
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
            const msg = detail.map(d => (d && d.msg) || '').filter(Boolean).join('; ');
            return msg || fallback;
        }
        if (detail.msg) return String(detail.msg);
        try { return JSON.stringify(detail); } catch (_) { return fallback; }
    }

    CDI.registerScreen('review', {
        onEnter() {
            if (!initialized) init();
            const isManual = CDI.state.sourceFormat === 'manual';
            REQUIRED = isManual 
                ? ['vendedor_nombre', 'comprador_nombre', 'numero_factura', 'fecha_emision', 'moneda', 'incoterm']
                : ['moneda', 'incoterm'];
                
            if (form) {
                FIELDS.forEach(name => {
                    const label = form.querySelector('label[for="f_' + name + '"]');
                    if (!label) return;
                    const oldReq = label.querySelector('.field-required');
                    if (oldReq) oldReq.remove();
                    if (REQUIRED.indexOf(name) !== -1) {
                        label.insertAdjacentHTML('beforeend', ' <span class="field-required">· requerido</span>');
                    }
                });
            }
            populate();
        },
        onLeave() {}
    });

    document.addEventListener('DOMContentLoaded', init);
})();
