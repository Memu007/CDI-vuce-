/* ============================================================
   CDI v2 — Lo que decide el despachante
   En la pantalla de validación, antes de generar: banco, empresa de
   digitalización y destino de la mercadería por operación; estado de la
   mercadería (y cambio de destino) por producto. La unidad de la factura y la
   estadística, por operación y con cambio por producto. El
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
    // Destino de la mercadería: se guarda el código de
    // IVAADICIONAL1; el servidor saca el de GANANCIASOP3 de la misma tabla
    // (IVA_ADICIONAL en core/maria_generator.py).
    const IVA = [
        ['NO_VALIDA', 'Comercialización o reventa'],
        ['IVAAD2', 'Bien de uso de la empresa'],
        ['IVAAD1', 'Bien de uso de una persona'],
    ];
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

    // Lo que el arancel dice de cada producto: por fila, el
    // sufijo propuesto y lo que falta; por posición, la unidad estadística.
    // Se pide de nuevo si cambian los productos, y otra vez si falló.
    // Lo que viaja al generar es lo que muestra la celda: sale de lo último
    // que se pintó (`mostrado`), no de lo que llegó después ni de un pedido
    // nuevo. Cada fila guarda lo que se pidió: si se borra o cambia un
    // producto, su propuesta no pasa al que queda en su lugar.
    const TOPE_ARANCEL = 500;       // SUFIJOS_POR_PEDIDO en main.py
    const NO_CONTESTO = 'El arancel de ARCA no contestó: no se propone sufijo ni unidad; va el de la operación.';
    const CONSULTANDO = 'Consultando el arancel de ARCA…';
    const TOPE = 'Con más de ' + TOPE_ARANCEL + ' productos no se consulta el arancel de ARCA: cargá los sufijos a mano.';
    const OTRA_OPERACION = 'Lo escribiste con otro sufijo de la operación: revisalo, va tal cual.';
    const OPERACION_VACIA = 'El sufijo de la operación está vacío: cada producto sale sólo con lo que pide el arancel de ARCA';
    let arancel = { clave: null, fallo: false, fuente: '', sin_tabla: false, filas: [], pedidos: [] };
    let mostrado = { estado: 'consultando', arancel: arancel };
    let pendiente = null;           // { clave, promesa }: el pedido en curso
    function posicionDe(it) { return String((it && it.pieza) || '').trim().toUpperCase(); }
    function conSubitems(it) { return Boolean(it && Array.isArray(it.subitems) && it.subitems.length); }
    function pedidoDe(it) {
        return {
            pieza: posicionDe(it), marca: String((it && it.marca) || ''), modelo: String((it && it.modelo) || ''),
            codigo_parte: String((it && it.codigo_parte) || ''),
        };
    }
    function cuerpoDeSufijos() {
        const items = (CDI.state.items || []).map(pedidoDe);
        return { items: items, clave: JSON.stringify({ items: items }) };
    }
    function estadoArancel() {
        if ((CDI.state.items || []).length > TOPE_ARANCEL) return 'tope';
        if (arancel.clave !== cuerpoDeSufijos().clave) return 'consultando';
        return arancel.fallo ? 'no_contesto' : 'ok';
    }
    async function pedirAlArancel(cuerpo) {
        const clave = cuerpo.clave;
        const nuevo = { clave: clave, fallo: false, fuente: '', sin_tabla: false, filas: [], pedidos: cuerpo.items };
        try {
            const r = await CDI.api('/api/sufijos/propuesta', { method: 'POST', body: clave });
            if (r && r.ok) {
                const d = await r.json();
                nuevo.fuente = d.fuente || '';
                nuevo.sin_tabla = Boolean(d.sin_tabla);
                nuevo.filas = d.items || [];
            } else {
                nuevo.fallo = true;
            }
        } catch (e) {
            nuevo.fallo = true;
            console.warn('[despachante] sin arancel:', e && e.message);
        }
        if (cuerpoDeSufijos().clave !== clave) return false;   // cambiaron mientras tanto
        arancel = nuevo;
        return true;
    }
    // Un solo pedido por estado de los productos: si ya hay uno en curso
    // para los mismos, se espera ése. Con más del tope no se pide.
    function pedirSufijos() {
        const cuerpo = cuerpoDeSufijos();
        if (cuerpo.items.length > TOPE_ARANCEL) return Promise.resolve(false);
        if (arancel.clave === cuerpo.clave && !arancel.fallo) return Promise.resolve(false);
        if (pendiente && pendiente.clave === cuerpo.clave) return pendiente.promesa;
        const este = { clave: cuerpo.clave };
        este.promesa = pedirAlArancel(cuerpo).finally(() => { if (pendiente === este) pendiente = null; });
        pendiente = este;
        return este.promesa;
    }
    // La fila del arancel que se pintó para este producto, si el producto
    // sigue siendo el mismo que se pidió.
    function filaDe(it, i) {
        if (!it || mostrado.estado !== 'ok') return null;
        const pedido = mostrado.arancel.pedidos[i];
        if (!pedido || JSON.stringify(pedido) !== JSON.stringify(pedidoDe(it))) return null;
        return mostrado.arancel.filas[i] || null;
    }
    // La propuesta de la fila, sólo para un producto que sale con su propio
    // sufijo (no en sub-ítems, cada uno lleva el suyo, ni en un grupo, va
    // el de la operación para todos).
    function propuestaDe(it, i) {
        if (!it || it.grupo_id || conSubitems(it) || !posicionDe(it)) return null;
        return filaDe(it, i);
    }

    // Un sufijo partido en sus códigos, con la misma regla que el servidor
    // (limpiar_sufijo en core/maria_generator.py); null si no se puede partir.
    const UN_SUFIJO = /([A-Za-z]{2})(?:\(([^()]*)\)|([0-9]{2}))/y;
    const ENTRE_SUFIJOS = /[\s,;\-]*/y;
    function partesDe(texto) {
        const s = String(texto || '');
        const partes = [];
        ENTRE_SUFIJOS.lastIndex = 0;
        ENTRE_SUFIJOS.exec(s);
        let pos = ENTRE_SUFIJOS.lastIndex;
        while (pos < s.length) {
            UN_SUFIJO.lastIndex = pos;
            const m = UN_SUFIJO.exec(s);
            if (!m) return null;
            partes.push({ codigo: m[1].toUpperCase(), texto: m[0], valor: m[2] != null ? m[2] : m[3] });
            ENTRE_SUFIJOS.lastIndex = UN_SUFIJO.lastIndex;
            ENTRE_SUFIJOS.exec(s);
            pos = ENTRE_SUFIJOS.lastIndex;
        }
        return partes;
    }
    // El sufijo de la operación con lo que se propone para el producto (H5):
    // lo de la operación queda tal cual y la propuesta sólo agrega los
    // códigos que la operación no trae. Si el de la operación no se puede
    // partir, nada (el servidor lo dice); si juntos pasan del tope, tampoco:
    // no se pierde lo de la operación para que entre la propuesta.
    function combinar(op, propuesto) {
        const prop = partesDe(propuesto);
        const deOp = partesDe(op);
        if (!prop || !prop.length || !deOp) return '';
        const tiene = {};
        deOp.forEach(p => { tiene[p.codigo] = true; });
        const partes = deOp.map(p => p.texto)
            .concat(prop.filter(p => !tiene[p.codigo]).map(p => p.texto));
        const junto = partes.join('-') + '-';
        return junto.length <= 120 ? junto : '';
    }
    // Lo que la propuesta trae distinto de lo que ya escribió la operación
    // (mayúsculas y espacios no cuentan).
    function distintos(op, propuesto) {
        const prop = partesDe(propuesto);
        const deOp = partesDe(op);
        if (!prop || !deOp) return [];
        const igual = v => String(v).replace(/\s+/g, ' ').trim().toUpperCase();
        const textos = [];
        prop.forEach(p => {
            const o = deOp.find(x => x.codigo === p.codigo);
            if (o && igual(o.valor) !== igual(p.valor)) {
                textos.push('El arancel propone ' + p.texto + '; queda el de la operación: ' + o.texto + '.');
            }
        });
        return textos;
    }
    function sufijoDeLaOperacion() {
        const campo = $('sbtSufijoValor');
        if (campo) return campo.value;
        return String(((CDI.state || {}).operacion || {}).sbt_sufijo_valor || '');
    }
    // El sufijo de un producto como va al pedido, que es lo que muestra su
    // celda: el que escribió la persona (aunque lo haya borrado, para usar el
    // de la operación) o el propuesto junto con el de la operación. Un grupo
    // y un producto con sub-ítems no llevan uno propio.
    function sufijoDe(it, i) {
        if (!it || it.grupo_id || conSubitems(it)) return '';
        if (it.sufijo != null) return String(it.sufijo).trim();
        const f = propuestaDe(it, i);
        return f && f.sufijo ? combinar(sufijoDeLaOperacion(), String(f.sufijo)) : '';
    }
    // Lo escrito en la celda con un sufijo de la operación que ya no es el
    // de ahora (H2): va tal cual, pero se avisa.
    function escritoConOtraOperacion(it) {
        if (!it || it.grupo_id || conSubitems(it) || it.sufijo == null || it.sufijo_op == null) return false;
        return Boolean(String(it.sufijo).trim()) && it.sufijo_op !== sufijoDeLaOperacion().trim();
    }
    function avisosDeLaFila(it, i) {
        const textos = [];
        const f = it && it.sufijo == null ? propuestaDe(it, i) : null;
        if (f && f.sufijo) textos.push(...distintos(sufijoDeLaOperacion(), String(f.sufijo)));
        if (escritoConOtraOperacion(it)) textos.push(OTRA_OPERACION);
        return textos;
    }
    function notaDelArancel(it, i) {
        if (!it || conSubitems(it) || !posicionDe(it)) return '';
        if (mostrado.estado === 'tope') return TOPE;
        if (mostrado.estado === 'no_contesto') return NO_CONTESTO;
        if (mostrado.estado === 'consultando') return CONSULTANDO;
        const f = filaDe(it, i);
        if (!f) return '';
        const fuente = mostrado.arancel.fuente;
        if (!f.en_la_tabla) {
            if (mostrado.arancel.sin_tabla) return 'Falta la tabla del arancel de ARCA: cargalo a mano.';
            if (!/^[0-9]{11}[A-Z]?$/.test(posicionDe(it).replace(/[.\s]/g, ''))) {
                return 'No es una posición SIM completa (11 dígitos y la letra de control): cargalo a mano.';
            }
            if (f.letra_de_control) {
                return 'En el ' + fuente + ' la letra de control de esta posición es '
                    + f.letra_de_control + ': revisá la posición.';
            }
            return 'La posición no está en el ' + fuente + ': cargalo a mano.';
        }
        const partes = ['Según el ' + fuente + ': unidad estadística ' + f.unidad_estadistica + '.'];
        if ((f.faltan || []).length) partes.push('Falta: ' + f.faltan.join('; ') + '.');
        return partes.join(' ');
    }
    function notaDe(it, i) {
        return [notaDelArancel(it, i)].concat(avisosDeLaFila(it, i)).filter(Boolean).join(' ');
    }
    function refrescarNotas() {
        const items = CDI.state.items || [];
        document.querySelectorAll('.despachante-sufijo-nota').forEach(div => {
            const i = Number(div.dataset.row);
            div.textContent = notaDe(items[i], i);
        });
    }
    // Si cambia el de la operación, las celdas que nadie escribió se
    // actualizan (salvo la que se está escribiendo), y las notas también.
    function alCambiarLaOperacion() {
        const items = CDI.state.items || [];
        document.querySelectorAll('.despachante-sufijo').forEach(campo => {
            const i = Number(campo.dataset.row);
            const it = items[i];
            if (it && it.sufijo == null && document.activeElement !== campo) campo.value = sufijoDe(it, i);
        });
        refrescarNotas();
    }
    // ¿Todos los productos salen con un sufijo propio, en la celda o en cada
    // sub-ítem? Entonces el de la operación no hace falta.
    function todosConPropio() {
        const items = CDI.state.items || [];
        return items.length > 0 && items.every((it, i) => conSubitems(it)
            ? it.subitems.every(s => String((s && s.sufijo) || '').trim())
            : Boolean(sufijoDe(it, i)));
    }
    // Lo que se avisa junto al botón: lo mismo que dicen las celdas.
    function avisos() {
        const items = CDI.state.items || [];
        const lista = [];
        if (items.length && mostrado.estado !== 'ok') lista.push(notaDelArancel({ pieza: '-' }, 0));
        items.forEach((it, i) => avisosDeLaFila(it, i).forEach(t => lista.push('Ítem ' + (i + 1) + ': ' + t)));
        if (!sufijoDeLaOperacion().trim() && todosConPropio()) lista.push(OPERACION_VACIA);
        return lista;
    }

    function pintar() {
        const wrap = $('despachanteWrap');
        if (!wrap) return;
        const e = elegidos();
        const items = CDI.state.items || [];
        limpiarEstadosViejos(items);
        mostrado = { estado: estadoArancel(), arancel: arancel };
        const banco = $('despachanteBanco');
        if (document.activeElement !== banco) {
            banco.value = e.banco_bcra != null ? e.banco_bcra : (propuesta.banco_bcra || '');
        }
        $('despachanteEmpresa').innerHTML = opciones(EMPRESAS, e.empresa_digitalizacion || propuesta.empresa_digitalizacion || 'PSAD06');
        $('despachanteIva').innerHTML = opciones(IVA, e.iva_adicional || 'NO_VALIDA');
        $('despachanteUnidad').innerHTML = opciones(UNIDADES, e.unidad || '', 'Sin elegir (sale 07, unidad)');
        $('despachanteUnidadEst').innerHTML = opciones(ESTADISTICA, e.unidad_estadistica || '',
            'Sin elegir (la del arancel)');
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
        if (conSubitems(it)) return '<span class="caption">Va en cada sub-ítem.</span>';
        // La nota está siempre, aunque vacía: refrescarNotas la llena.
        const nota = '<div class="caption despachante-sufijo-nota" data-row="' + i + '"' +
            ' style="font-size:.8rem;color:var(--muted,#666)">' + CDI.escapeHtml(notaDe(it, i)) + '</div>';
        // Un grupo sale con el de la operación: no se escribe uno por producto.
        if (it.grupo_id) return '<span class="caption">Va el de la operación para todo el grupo.</span>' + nota;
        return '<input type="text" class="form-input despachante-sufijo" data-row="' + i + '" maxlength="120"' +
            ' autocomplete="off" placeholder="El de la operación" value="' + CDI.escapeHtml(sufijoDe(it, i)) + '">' +
            nota;
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
            if (it) {
                it.sufijo = t.value;
                it.sufijo_op = sufijoDeLaOperacion().trim();   // con cuál se escribió (H2)
            }
            refrescarNotas();
        }
    }

    let enlazado = false;
    async function render() {
        const wrap = $('despachanteWrap');
        if (!wrap) return;
        if (!enlazado) {
            wrap.addEventListener('change', alElegir);
            wrap.addEventListener('input', alElegir);
            const sbt = $('sbtSufijoValor');
            if (sbt) sbt.addEventListener('input', alCambiarLaOperacion);
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
    // kilos y el producto no tiene sub-ítems (con sub-ítems,
    // kilos sólo sale si la factura también va en kilos); otra la avisa el
    // servidor. La del arancel, sólo si la nota de la fila la muestra.
    function unidadesDe(it, i) {
        const e = elegidos();
        const f = conSubitems(it) ? null : filaDe(it, i);
        const fila = f && f.en_la_tabla ? f : null;
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

    CDI.despachante = { render, leer, valores, unidadesDe, sufijoDe, notaDe, celdaSufijo, todosConPropio, avisos };
})();
