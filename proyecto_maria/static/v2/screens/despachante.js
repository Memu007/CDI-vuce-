/* ============================================================
   CDI v2 — Lo que decide el despachante (MARIA-4)
   En la pantalla de validación, antes de generar: banco, empresa de
   digitalización e IVA adicional por operación; estado de la mercadería
   (y cambio de IVA) por producto. Propone el último banco del cliente y la
   última empresa del usuario (de sus operaciones guardadas).
   Los códigos y nombres salen de core/maria_generator.py (única tabla).
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const ESTADOS = [
        ['1', 'Nuevo sin uso argentino'],
        ['2', 'Nuevo sin uso importado'],
        ['3', 'Sin uso argentino'],
        ['4', 'Sin uso importado'],
        ['5', 'Usado argentino (incluye reacondicionado)'],
        ['6', 'Usado importado (incluye reacondicionado)'],
    ];
    const IVA = [['NO_VALIDA', 'Reventa'], ['IVAAD1', 'Uso particular']];
    const EMPRESAS = [['PSAD06', 'Modoc'], ['PSAD01', 'Lakaut']];

    function $(id) { return document.getElementById(id); }
    function esArgentino(origen) {
        const o = String(origen || '').trim().toUpperCase();
        return o === 'AR' || o === 'ARG' || o === '200' || o === 'ARGENTINA';
    }
    function opciones(lista, elegido, vacio) {
        const html = vacio ? ['<option value="">' + CDI.escapeHtml(vacio) + '</option>'] : [];
        lista.forEach(([v, t]) => {
            html.push('<option value="' + v + '"' + (String(elegido) === v ? ' selected' : '') + '>' +
                CDI.escapeHtml(t) + '</option>');
        });
        return html.join('');
    }

    async function ultimos() {
        // El último banco que usó este cliente y la última empresa del usuario.
        const res = { banco_bcra: '', empresa_digitalizacion: '' };
        try {
            const cliente = CDI.getClienteActivo && CDI.getClienteActivo();
            if (cliente && cliente.id) {
                const r = await CDI.api('/api/clientes/' + encodeURIComponent(cliente.id) + '/operaciones');
                const d = r && r.ok ? await r.json() : {};
                const op = (d.operaciones || []).find(o => o.maria && o.maria.banco_bcra);
                if (op) res.banco_bcra = op.maria.banco_bcra;
            }
            const r2 = await CDI.api('/api/operations');
            const d2 = r2 && r2.ok ? await r2.json() : {};
            const op2 = (d2.operaciones || []).find(o => o.maria && o.maria.empresa_digitalizacion);
            if (op2) res.empresa_digitalizacion = op2.maria.empresa_digitalizacion;
        } catch (e) {
            console.warn('[despachante] sin últimos valores:', e && e.message);
        }
        return res;
    }

    async function render() {
        const wrap = $('despachanteWrap');
        if (!wrap) return;
        const op = CDI.state.operacion = CDI.state.operacion || {};
        const items = CDI.state.items || [];
        if (!op.__despachantePropuesto) {
            const u = await ultimos();
            if (!op.banco_bcra && u.banco_bcra) op.banco_bcra = u.banco_bcra;
            if (!op.empresa_digitalizacion && u.empresa_digitalizacion) op.empresa_digitalizacion = u.empresa_digitalizacion;
            op.__despachantePropuesto = true;
        }
        $('despachanteBanco').value = op.banco_bcra || '';
        $('despachanteEmpresa').innerHTML = opciones(EMPRESAS, op.empresa_digitalizacion || 'PSAD06');
        $('despachanteIva').innerHTML = opciones(IVA, op.iva_adicional || 'NO_VALIDA');
        const filas = items.map((it, i) => {
            const porDefecto = esArgentino(it.origen) ? '' : '2';
            const estado = it.estado != null && it.estado !== '' ? String(it.estado) : porDefecto;
            return '<tr>' +
                '<td>' + (i + 1) + '. ' + CDI.escapeHtml(String(it.descripcion || '').slice(0, 60)) + '</td>' +
                '<td><select class="form-input despachante-estado" data-row="' + i + '">' +
                opciones(ESTADOS, estado, 'Elegí el estado') + '</select></td>' +
                '<td><select class="form-input despachante-iva" data-row="' + i + '">' +
                opciones(IVA, it.iva_adicional || '', 'Igual que la operación') + '</select></td>' +
                '</tr>';
        });
        $('despachanteItems').innerHTML = filas.join('');
        $('despachanteError').hidden = true;
    }

    // Pasa lo elegido al estado y dice si se puede generar.
    function leer() {
        const op = CDI.state.operacion = CDI.state.operacion || {};
        const items = CDI.state.items || [];
        const errores = [];
        const banco = String($('despachanteBanco').value || '').trim();
        if (banco && !/^\d{3}$/.test(banco)) {
            errores.push('El banco va con el código de entidad del BCRA (3 dígitos).');
        }
        op.banco_bcra = banco;
        op.empresa_digitalizacion = $('despachanteEmpresa').value;
        op.iva_adicional = $('despachanteIva').value;
        document.querySelectorAll('.despachante-estado').forEach(sel => {
            const it = items[Number(sel.dataset.row)];
            if (!it) return;
            it.estado = sel.value || null;
            if (!sel.value) {
                errores.push('Ítem ' + (Number(sel.dataset.row) + 1) +
                    ': el origen es argentino; elegí el estado de la mercadería.');
            }
        });
        document.querySelectorAll('.despachante-iva').forEach(sel => {
            const it = items[Number(sel.dataset.row)];
            if (it) it.iva_adicional = sel.value || null;
        });
        const err = $('despachanteError');
        const avisos = banco ? [] : ['Sin banco: la línea del banco no sale en el TXT.'];
        err.textContent = errores.concat(avisos).join(' ');
        err.hidden = !(errores.length || avisos.length);
        err.style.color = errores.length ? 'var(--danger,#c0392b)' : 'var(--c-warning,#b26b00)';
        return errores.length === 0;
    }

    CDI.despachante = { render, leer };
})();
