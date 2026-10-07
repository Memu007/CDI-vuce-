/* ============================================================
   CDI v2 — Lo que decide el despachante (MARIA-4)
   En la pantalla de validación, antes de generar: banco, empresa de
   digitalización e IVA adicional por operación; estado de la mercadería
   (y cambio de IVA) por producto.

   Sólo se guarda lo que la persona elige (al elegirlo). Los valores por
   defecto se calculan cada vez con el origen actual y no se guardan: si el
   origen pasa a argentino, el estado se vuelve a pedir, y el servidor avisa
   lo que se usó por defecto. La propuesta (último banco del cliente, última
   empresa del usuario) es del cliente activo y se vuelve a pedir si cambia.
   Códigos y nombres: core/maria_generator.py (ESTADOS_MERCADERIA, etc.).
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
    // El estado corresponde al origen: 1, 3 y 5 argentinos; 2, 4 y 6 importados.
    const ESTADOS_ARGENTINOS = ['1', '3', '5'];
    const IVA = [['NO_VALIDA', 'Reventa'], ['IVAAD1', 'Uso particular']];
    const EMPRESAS = [['PSAD06', 'Modoc'], ['PSAD01', 'Lakaut']];

    function $(id) { return document.getElementById(id); }
    // Igual que el servidor: Argentina es «AR», «200» o el nombre.
    function esArgentino(origen) {
        const o = String(origen || '').trim().toUpperCase().replace(/\./g, '');
        return o === 'AR' || o === '200' || o === 'ARGENTINA';
    }
    function claseOrigen(origen) { return esArgentino(origen) ? 'AR' : 'EXT'; }
    function estadosPara(origen) {
        const arg = esArgentino(origen);
        return ESTADOS.filter(([v]) => ESTADOS_ARGENTINOS.includes(v) === arg);
    }
    // Un estado elegido para otra clase de origen ya no vale: se vuelve a pedir.
    function limpiarEstadosViejos(items) {
        items.forEach(it => {
            if (it.estado != null && it.estado !== '' && it.estado_origen !== claseOrigen(it.origen)) {
                it.estado = null;
                it.estado_origen = null;
            }
        });
    }
    function opciones(lista, elegido, vacio) {
        const html = vacio ? ['<option value="">' + CDI.escapeHtml(vacio) + '</option>'] : [];
        lista.forEach(([v, t]) => {
            html.push('<option value="' + v + '"' + (String(elegido) === v ? ' selected' : '') + '>' +
                CDI.escapeHtml(t) + '</option>');
        });
        return html.join('');
    }
    function clienteId() {
        const c = CDI.getClienteActivo && CDI.getClienteActivo();
        return (c && c.id) || '';
    }
    function elegidos() {
        const op = CDI.state.operacion = CDI.state.operacion || {};
        return op.despachante = op.despachante || {};
    }

    // Propuesta del cliente activo: último banco del cliente y última
    // empresa del usuario. Se pide una vez por cliente; si falla, se reintenta.
    let propuesta = { cliente: null, banco_bcra: '', empresa_digitalizacion: '' };
    async function pedirPropuesta() {
        const cid = clienteId();
        if (propuesta.cliente === cid && propuesta.ok) return;
        const nueva = { cliente: cid, banco_bcra: '', empresa_digitalizacion: '', ok: false };
        try {
            const [r1, r2] = await Promise.all([
                cid ? CDI.api('/api/clientes/' + encodeURIComponent(cid) + '/operaciones') : null,
                CDI.api('/api/operations'),
            ]);
            const d1 = r1 && r1.ok ? await r1.json() : {};
            const d2 = r2 && r2.ok ? await r2.json() : {};
            const op1 = (d1.operaciones || []).find(o => o.maria && o.maria.banco_bcra);
            const op2 = (d2.operaciones || []).find(o => o.maria && o.maria.empresa_digitalizacion);
            nueva.banco_bcra = op1 ? op1.maria.banco_bcra : '';
            nueva.empresa_digitalizacion = op2 ? op2.maria.empresa_digitalizacion : '';
            nueva.ok = (!cid || (r1 && r1.ok)) && r2 && r2.ok;
        } catch (e) {
            console.warn('[despachante] sin propuesta:', e && e.message);
        }
        if (clienteId() === cid) propuesta = nueva;
    }

    function pintar() {
        const wrap = $('despachanteWrap');
        if (!wrap) return;
        const e = elegidos();
        const items = CDI.state.items || [];
        limpiarEstadosViejos(items);
        const banco = $('despachanteBanco');
        if (document.activeElement !== banco) {
            banco.value = e.banco_bcra != null ? e.banco_bcra : (propuesta.banco_bcra || '');
        }
        $('despachanteEmpresa').innerHTML = opciones(EMPRESAS, e.empresa_digitalizacion || propuesta.empresa_digitalizacion || 'PSAD06');
        $('despachanteIva').innerHTML = opciones(IVA, e.iva_adicional || 'NO_VALIDA');
        $('despachanteItems').innerHTML = items.map((it, i) => {
            const porDefecto = esArgentino(it.origen) ? '' : '2';
            const estado = it.estado != null && it.estado !== '' ? String(it.estado) : porDefecto;
            return '<tr>' +
                '<td>' + (i + 1) + '. ' + CDI.escapeHtml(String(it.descripcion || '').slice(0, 60)) + '</td>' +
                '<td><select class="form-input despachante-estado" data-row="' + i + '">' +
                opciones(estadosPara(it.origen), estado, 'Elegí el estado') + '</select></td>' +
                '<td><select class="form-input despachante-iva" data-row="' + i + '">' +
                opciones(IVA, it.iva_adicional || '', 'Igual que la operación') + '</select></td>' +
                '</tr>';
        }).join('');
        $('despachanteError').hidden = true;
    }

    // Lo que la persona toca se guarda en el momento.
    function alElegir(ev) {
        const t = ev.target;
        const e = elegidos();
        const items = CDI.state.items || [];
        if (t.id === 'despachanteBanco') e.banco_bcra = String(t.value || '').trim();
        else if (t.id === 'despachanteEmpresa') e.empresa_digitalizacion = t.value;
        else if (t.id === 'despachanteIva') e.iva_adicional = t.value;
        else if (t.classList.contains('despachante-estado')) {
            const it = items[Number(t.dataset.row)];
            if (it) {
                it.estado = t.value || null;
                it.estado_origen = t.value ? claseOrigen(it.origen) : null;
            }
        } else if (t.classList.contains('despachante-iva')) {
            const it = items[Number(t.dataset.row)];
            if (it) it.iva_adicional = t.value || null;
        }
    }

    let enlazado = false;
    async function render() {
        const wrap = $('despachanteWrap');
        if (!wrap) return;
        if (!enlazado) {
            wrap.addEventListener('change', alElegir);
            wrap.addEventListener('input', alElegir);
            enlazado = true;
        }
        pintar();                       // ya, con lo que hay
        const antes = propuesta.cliente;
        await pedirPropuesta();
        if (propuesta.cliente !== antes || propuesta.ok) pintar();
    }

    // Lo que va al pedido: lo elegido; si no, la propuesta del cliente; si no,
    // nada (el servidor usa su valor por defecto y lo avisa en los supuestos).
    function valores() {
        const e = elegidos();
        return {
            banco_bcra: e.banco_bcra != null ? e.banco_bcra : (propuesta.cliente === clienteId() ? propuesta.banco_bcra : ''),
            empresa_digitalizacion: e.empresa_digitalizacion ||
                (propuesta.cliente === clienteId() && propuesta.empresa_digitalizacion) || null,
            iva_adicional: e.iva_adicional || null,
        };
    }

    // ¿Se puede generar? Muestra los errores y avisos al lado.
    function leer() {
        const items = CDI.state.items || [];
        limpiarEstadosViejos(items);
        const v = valores();
        const errores = [];
        if (v.banco_bcra && !/^[0-9]{3}$/.test(v.banco_bcra)) {
            errores.push('El banco va con el código de entidad del BCRA (3 dígitos).');
        }
        items.forEach((it, i) => {
            if (esArgentino(it.origen) && (it.estado == null || it.estado === '')) {
                errores.push('Ítem ' + (i + 1) + ': el origen es argentino; elegí el estado de la mercadería.');
            }
        });
        const avisos = [];
        if (!v.banco_bcra) avisos.push('Sin banco: la línea del banco no sale en el TXT.');
        else if (elegidos().banco_bcra == null) avisos.push('Banco ' + v.banco_bcra + ': el último que usó este cliente.');
        const err = $('despachanteError');
        err.textContent = errores.concat(avisos).join(' ');
        err.hidden = !(errores.length || avisos.length);
        err.style.color = errores.length ? 'var(--danger,#c0392b)' : 'var(--c-warning,#b26b00)';
        return errores.length === 0;
    }

    CDI.despachante = { render, leer, valores };
})();
