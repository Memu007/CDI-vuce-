/* ============================================================
   CDI v2 — Lo que decide el despachante (MARIA-4)
   En la pantalla de validación, antes de generar: banco, empresa de
   digitalización e IVA adicional por operación; estado de la mercadería
   (y cambio de IVA) por producto. MARIA-7: la unidad de la factura y la
   estadística, por operación y con cambio por producto. SUFIJOS-1: el
   sufijo de valor de cada producto y la unidad estadística que pide su
   posición, del arancel de ARCA (POST /api/sufijos/propuesta).

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
    // Códigos MARIA de core/maria_generator.py (UNIDADES_MARIA).
    const UNIDADES = [
        ['07', 'Unidad (07)'], ['03', 'Metro cuadrado (03)'], ['01', 'Kilogramo (01)'],
        ['02', 'Metro (02)'], ['04', 'Metro cúbico (04)'], ['05', 'Litro (05)'],
        ['08', 'Par (08)'], ['09', 'Docena (09)'], ['11', 'Millar (11)'],
        ['14', 'Gramo (14)'], ['29', 'Tonelada (29)'],
    ];
    // La estadística: la misma que la declarada o kilos (con otra no se sabe
    // la cantidad). Sin elegir, la que pide la posición si es kilos.
    const ESTADISTICA = [['DCL', 'Igual que la de la factura'], ['01', 'Kilogramo (01)']];

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
            html.push('<option value="' + CDI.escapeHtml(v) + '"' + (String(elegido) === v ? ' selected' : '') + '>' +
                CDI.escapeHtml(t) + '</option>');
        });
        return html.join('');
    }
    // La unidad que trae el producto (planilla, operación guardada) y no es
    // un código de la lista se muestra tal cual, para no esconderla.
    function unidadesPara(it) {
        const propia = String(it.unidad || '').trim();
        return propia && !UNIDADES.some(([v]) => v === propia)
            ? [[propia, propia + ' (como vino)']].concat(UNIDADES) : UNIDADES;
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

    // Lo que el arancel dice de cada producto (SUFIJOS-1): por fila, el
    // sufijo propuesto y lo que falta; por posición, la unidad estadística.
    // Se pide de nuevo si cambian los productos; si falla, no se propone nada.
    let arancel = { clave: null, fuente: '', filas: [] };
    let tabla = {};
    function posicionDe(it) { return String((it && it.pieza) || '').trim().toUpperCase(); }
    function recordarTabla(t) { tabla = t || {}; }
    function cuerpoDeSufijos() {
        const cuerpo = { items: (CDI.state.items || []).map(it => ({
            pieza: posicionDe(it), marca: String(it.marca || ''), modelo: String(it.modelo || ''),
            codigo_parte: String(it.codigo_parte || ''),
        })) };
        return { clave: JSON.stringify(cuerpo) };
    }
    async function pedirSufijos() {
        const clave = cuerpoDeSufijos().clave;
        if (arancel.clave === clave) return false;
        let nuevo = { clave: clave, fuente: '', filas: [] };
        try {
            const r = await CDI.api('/api/sufijos/propuesta', { method: 'POST', body: clave });
            if (r && r.ok) {
                const d = await r.json();
                nuevo = { clave: clave, fuente: d.fuente || '', filas: d.items || [] };
            } else {
                nuevo.clave = null;
            }
        } catch (e) {
            nuevo.clave = null;
            console.warn('[despachante] sin arancel:', e && e.message);
        }
        if (cuerpoDeSufijos().clave !== clave) return false;   // cambiaron mientras tanto
        arancel = nuevo;
        const t = {};
        nuevo.filas.forEach(f => { if (f && f.en_la_tabla) t[String(f.posicion || '').toUpperCase()] = f; });
        recordarTabla(t);
        return true;
    }
    // El sufijo propuesto, sólo para un producto que sale con su propio
    // sufijo: no en sub-ítems (cada uno lleva el suyo) ni en un grupo (va
    // uno solo para todos y lo escribe la persona).
    function propuestaDe(it, i) {
        if (!it || it.grupo_id || (Array.isArray(it.subitems) && it.subitems.length)) return null;
        const f = arancel.filas[i];
        return f && posicionDe(it) === String(f.posicion || '').toUpperCase() ? f : null;
    }
    // El sufijo de un producto como va al pedido: el que escribió la persona
    // (aunque lo haya borrado, para usar el de la operación) o el propuesto.
    function sufijoDe(it, i) {
        if (it && it.sufijo != null) return String(it.sufijo).trim();
        const f = propuestaDe(it, i);
        return f ? String(f.sufijo || '') : '';
    }
    function notaDe(it, i) {
        if (!it || it.grupo_id || (Array.isArray(it.subitems) && it.subitems.length)) return '';
        const f = arancel.filas[i];
        if (!f || posicionDe(it) !== String(f.posicion || '').toUpperCase() || !posicionDe(it)) return '';
        if (!f.en_la_tabla) return 'La posición no está en el ' + arancel.fuente + ': cargalo a mano.';
        const partes = ['Según el ' + arancel.fuente + ': unidad estadística ' + f.unidad_estadistica + '.'];
        if ((f.faltan || []).length) partes.push('Falta: ' + f.faltan.join('; ') + '.');
        return partes.join(' ');
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
        $('despachanteUnidad').innerHTML = opciones(UNIDADES, e.unidad || '', 'Sin elegir (sale 07, unidad)');
        $('despachanteUnidadEst').innerHTML = opciones(ESTADISTICA, e.unidad_estadistica || '',
            'Según el arancel de ARCA (si no, la de la factura)');
        $('despachanteItems').innerHTML = items.map((it, i) => {
            const porDefecto = esArgentino(it.origen) ? '' : '2';
            const estado = it.estado != null && it.estado !== '' ? String(it.estado) : porDefecto;
            return '<tr>' +
                '<td>' + (i + 1) + '. ' + CDI.escapeHtml(String(it.descripcion || '').slice(0, 60)) + '</td>' +
                '<td><select class="form-input despachante-estado" data-row="' + i + '">' +
                opciones(estadosPara(it.origen), estado, 'Elegí el estado') + '</select></td>' +
                '<td><select class="form-input despachante-iva" data-row="' + i + '">' +
                opciones(IVA, it.iva_adicional || '', 'Igual que la operación') + '</select></td>' +
                '<td><select class="form-input despachante-unidad" data-row="' + i + '">' +
                opciones(unidadesPara(it), it.unidad || '', 'Igual que la operación') + '</select></td>' +
                '<td><select class="form-input despachante-unidad-est" data-row="' + i + '">' +
                opciones(ESTADISTICA, it.unidad_estadistica || '', 'Igual que la operación') + '</select></td>' +
                '<td>' + celdaSufijo(it, i) + '</td>' +
                '</tr>';
        }).join('');
        $('despachanteError').hidden = true;
    }
    function celdaSufijo(it, i) {
        if (Array.isArray(it.subitems) && it.subitems.length) {
            return '<span class="caption">Va en cada sub-ítem.</span>';
        }
        const nota = notaDe(it, i);
        return '<input type="text" class="form-input despachante-sufijo" data-row="' + i + '" maxlength="120"' +
            ' autocomplete="off" placeholder="El de la operación" value="' + CDI.escapeHtml(sufijoDe(it, i)) + '">' +
            (nota ? '<div class="caption" style="font-size:.8rem;color:var(--muted,#666)">' + CDI.escapeHtml(nota) + '</div>' : '');
    }

    // Lo que la persona toca se guarda en el momento.
    function alElegir(ev) {
        const t = ev.target;
        const e = elegidos();
        const items = CDI.state.items || [];
        if (t.id === 'despachanteBanco') e.banco_bcra = String(t.value || '').trim();
        else if (t.id === 'despachanteEmpresa') e.empresa_digitalizacion = t.value;
        else if (t.id === 'despachanteIva') e.iva_adicional = t.value;
        else if (t.id === 'despachanteUnidad') e.unidad = t.value || null;
        else if (t.id === 'despachanteUnidadEst') e.unidad_estadistica = t.value;
        else if (t.classList.contains('despachante-estado')) {
            const it = items[Number(t.dataset.row)];
            if (it) {
                it.estado = t.value || null;
                it.estado_origen = t.value ? claseOrigen(it.origen) : null;
            }
        } else if (t.classList.contains('despachante-iva')) {
            const it = items[Number(t.dataset.row)];
            if (it) it.iva_adicional = t.value || null;
        } else if (t.classList.contains('despachante-unidad')) {
            const it = items[Number(t.dataset.row)];
            if (it) it.unidad = t.value || null;
        } else if (t.classList.contains('despachante-unidad-est')) {
            const it = items[Number(t.dataset.row)];
            if (it) it.unidad_estadistica = t.value || null;
        } else if (t.classList.contains('despachante-sufijo')) {
            const it = items[Number(t.dataset.row)];
            if (it) it.sufijo = t.value;
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
        const [, cambio] = await Promise.all([pedirPropuesta(), pedirSufijos()]);
        if (propuesta.cliente !== antes || propuesta.ok || cambio) pintar();
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

    // Las unidades de un producto como van al pedido: la suya o la de la
    // operación; la estadística sólo viaja si es kilos (si no, el servidor
    // usa la declarada). Si nadie la eligió, la de la posición cuando es
    // kilos (SUFIJOS-1); otra la avisa el servidor.
    function unidadesDe(it) {
        const e = elegidos();
        const fila = tabla[posicionDe(it)];
        const est = (it && it.unidad_estadistica) || e.unidad_estadistica ||
            (fila && fila.unidad_estadistica) || 'DCL';
        return {
            unidad: (it && it.unidad) || e.unidad || null,
            unidad_estadistica: est === '01' ? '01' : null,
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

    CDI.despachante = { render, leer, valores, unidadesDe, sufijoDe, recordarTabla };
})();
