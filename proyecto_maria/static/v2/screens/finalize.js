/* ============================================================
   CDI v2 — Screens 4 y 5: Validating + Ready
   Pantalla 4 (validating): llama /api/validate/smart, muestra stats
   y lista de errores / advertencias / sugerencias. Boton "Generar"
   bloqueado si hay errores criticos.
   Pantalla 5 (ready): llama /generate_maria, muestra preview, boton
   de descarga y opcion de empezar nueva operacion.
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    /* ---------- shared refs ---------- */
    let vLoading, vResults, vStatus, vTitle, vSubtitle, vStats, vIssues, vRerun, vGenerate;
    let rGenerating, rDone, rSubtitle, rDownload, rCopy, rFilename, rPreview, rError;
    let sbtInput, sbtError;
    let initialized = false;

    let lastValidation = null;    // { errores, advertencias, sugerencias, estadisticas }
    let lastValidationTs = 0;
    let lastValidationPedido = '';  // el pedido del que salió lastValidation
    let lastMaria = null;         // { filename, download_url, content }
    let turnoValidacion = 0;      // sólo la validación más reciente pinta la pantalla
    let generateInFlight = false;
    // Lo que se pide mientras otra generación espera se genera cuando ésa vuelve.
    let pedidaMientrasOtra = false;

    function $(id) { return document.getElementById(id); }
    function show(el) { if (el) el.hidden = false; }
    function hide(el) { if (el) el.hidden = true; }
    // «None», «null» o «N/A» de una operación guardada con el lector viejo no
    // son un número de factura (MARIA-5).
    function numeroDeFactura(op) {
        const leida = String((op && op.numero_factura) || '').trim();
        return /^(none|null|n\/a)$/i.test(leida) ? '' : leida;
    }

    function init() {
        if (initialized) return;
        // validating
        vLoading   = $('validatingLoading');
        vResults   = $('validatingResults');
        vStatus    = $('validatingStatus');
        vTitle     = $('validatingTitle');
        vSubtitle  = $('validatingSubtitle');
        vStats     = $('validatingStats');
        vIssues    = $('validatingIssues');
        vRerun     = $('validatingRerun');
        vGenerate  = $('validatingGenerate');

        // ready
        rGenerating = $('readyGenerating');
        rDone       = $('readyDone');
        rSubtitle   = $('readySubtitle');
        rDownload   = $('readyDownloadBtn');
        rCopy       = $('readyCopyBtn');
        rFilename   = $('readyFilename');
        rPreview    = $('readyPreview');
        rError      = $('readyError');
        sbtInput    = $('sbtSufijoValor');
        sbtError    = $('sbtFieldError');

        if (!vLoading || !rGenerating) return;

        if (vRerun)    vRerun.addEventListener('click', () => runValidation(/* force */ true));
        if (vGenerate) vGenerate.addEventListener('click', onGenerate);
        if (rDownload) rDownload.addEventListener('click', onDownload);
        if (rCopy)     rCopy.addEventListener('click', onCopy);

        initialized = true;
    }

    /* ==========================================================
       Pantalla 4: validating
       ========================================================== */
    function onEnterValidating() {
        // MARIA-4: lo que decide el despachante, antes de generar. MARIA-3:
        // los avisos del TXT se piden con lo que hay y otra vez cuando llega
        // la propuesta del cliente o la persona cambia algo en la tarjeta.
        // Hasta que llegue la respuesta, nada de los avisos de otra operación.
        const avisosPanel = document.getElementById('validatingAvisosPanel');
        if (avisosPanel) avisosPanel.hidden = true;
        // ESTUDIO-1: el estudio elegido también cambia los avisos.
        Promise.all([
            Promise.resolve(CDI.despachante ? CDI.despachante.render() : null).catch(() => null),
            Promise.resolve(CDI.estudios ? CDI.estudios.render() : null).catch(() => null),
        ]).then(refrescarAvisos);
        enlazarAvisos();
        enlazarValor();
        pintarValor(null);
        refrescarAvisos();
        init();
        if (!vLoading) return;
        const items = (CDI.state && CDI.state.items) || [];
        if (!items.length) {
            CDI.toast('Sin ítems', 'Volvé a cargar el PDF.', 'error');
            CDI.goTo('upload');
            return;
        }
        runValidation(false);
    }

    async function runValidation(force) {
        init();
        show(vLoading);
        hide(vResults);
        const items = buildItemsForValidation();
        const pedido = JSON.stringify({ items, operacion: cabeceraParaValidar() });
        const turno = ++turnoValidacion;
        // Se reusa sólo el resultado de este mismo pedido, de hace menos de 60 s.
        if (!force && lastValidation && pedido === lastValidationPedido && (Date.now() - lastValidationTs) < 60000) {
            renderValidation(lastValidation);
            return;
        }
        lastValidation = null;
        const startedAt = Date.now();
        let data = null, err = null;
        try {
            const res = await CDI.api('/api/validate/smart', { method: 'POST', body: pedido });
            data = await res.json();
            if (!res.ok || !data || data.success === false) {
                throw new Error((data && data.detail) || 'No se pudo validar');
            }
        } catch (e) {
            err = e;
        }
        // Otra carga pidió después: esta respuesta ya no es la que se ve.
        if (turno !== turnoValidacion) return;
        if (err) {
            console.error('[validating]', err);
            CDI.track('validation_error', { message: String(err && err.message || err) });
            CDI.toast('Error al validar', String(err && err.message || err), 'error');
            // Mostrar resultados "vacios" para no bloquear: permitimos seguir
            renderValidation({
                errores: [],
                advertencias: ['No se pudo contactar al validador. Podés continuar con revisión manual.'],
                sugerencias: [],
                estadisticas: { total_items: items.length, total_valor_usd: 0, total_peso_kg: 0, ncms_unicos: 0 }
            });
            return;
        }
        lastValidation = data;
        lastValidationTs = Date.now();
        lastValidationPedido = pedido;
        CDI.track('validation_ok', {
            errores: (data.errores || []).length,
            advertencias: (data.advertencias || []).length,
            sugerencias: (data.sugerencias || []).length,
            duration_ms: Date.now() - startedAt
        });
        renderValidation(data);
    }

    function buildItemsForValidation() {
        const items = (CDI.state && CDI.state.items) || [];
        return items.map(it => ({
            pieza: String(it.pieza || '').trim(),
            descripcion: String(it.descripcion || '').trim(),
            origen: String(it.origen || 'XX').trim().toUpperCase() || 'XX',
            cantidad: toNumber(it.cantidad, 0),
            valor_unitario: toNumber(it.valor_unitario, 0),
            peso_unitario: toNumber(it.peso_unitario, 0),
            // El grupo va en una línea del TXT: la validación cuenta igual.
            grupo_id: it.grupo_id == null ? null : it.grupo_id
        }));
    }

    /* ---------- Avisos antes de generar (MARIA-3) ---------- */
    let avisosSeq = 0;
    let avisosTimer = null;
    let avisosEnlazados = false;

    function enlazarAvisos() {
        const wrap = document.getElementById('despachanteWrap');
        if (avisosEnlazados || !wrap) return;
        avisosEnlazados = true;
        const programar = () => {
            clearTimeout(avisosTimer);
            avisosTimer = setTimeout(refrescarAvisos, 400);
        };
        wrap.addEventListener('change', programar);
        wrap.addEventListener('input', programar);
        // El sufijo de la operación cambia lo que viaja por producto.
        const sbt = document.getElementById('sbtSufijoValor');
        if (sbt) sbt.addEventListener('input', programar);
        const estudio = document.getElementById('estudioWrap');
        if (estudio) estudio.addEventListener('change', programar);
    }

    // SEPARADORES-1d (D25): el flete y el seguro van al TXT con dos
    // decimales. Si tienen más, se avisa sin frenar qué se escribió y qué
    // lleva el TXT. Lo que no se lee o es negativo ya lo frena la revisión.
    function avisosDeLosMontos(op) {
        return [['Flete', op.flete], ['Seguro', op.seguro]].map(function (par) {
            const r = CDI.montos.leer(par[1]);
            if (r.error || r.valor === null || r.valor < 0) return null;
            const txt = alCentavoDelTxt(r.valor);
            if (txt === null) return null;
            const escrito = typeof par[1] === 'string' ? par[1].trim() : CDI.montos.escribir(r.valor);
            return par[0] + ': escribiste «' + escrito + '». El TXT lleva ' + txt + '.';
        }).filter(Boolean);
    }

    // Como centavos() del generador: el número más corto que lo escribe
    // (String de JS da lo mismo que repr de Python) y la mitad hacia arriba,
    // con cuentas de texto: Math.round(2.675 * 100) da 267. null si tiene dos
    // decimales o menos.
    function alCentavoDelTxt(n) {
        const s = String(n);
        if (/e/i.test(s)) return /e-/i.test(s) ? '0,00' : null;   // menos de 0,000001 o más de 1e21
        const [entero, dec = ''] = s.split('.');
        if (dec.length <= 2) return null;
        const cent = BigInt(entero + dec.slice(0, 2)) + (dec[2] >= '5' ? 1n : 0n);
        const t = cent.toString().padStart(3, '0');
        return t.slice(0, -2) + ',' + t.slice(-2);
    }

    async function refrescarAvisos() {
        const panel = document.getElementById('validatingAvisosPanel');
        const list = document.getElementById('validatingAvisosList');
        const count = document.getElementById('validatingAvisosCount');
        const seq = ++avisosSeq;
        if (!panel || !list) return;
        if (!(CDI.state && (CDI.state.items || []).length)) { panel.hidden = true; return; }
        let avisos;
        let valor = null;
        let firma = null;
        // SUFIJOS-1: lo que dicen las celdas del sufijo (el arancel no
        // contestó, lo escrito con otro de la operación, D23). SEPARADORES-1d:
        // el flete o el seguro con más de dos decimales.
        const deLaPantalla = (CDI.despachante && CDI.despachante.avisos ? CDI.despachante.avisos() : [])
            .concat(avisosDeLosMontos((CDI.state && CDI.state.operacion) || {}));
        try {
            const pedido = buildMariaRequest();
            firma = firmaDelPedido(pedido);
            const res = await CDI.api('/generate_maria/avisos', {
                method: 'POST',
                body: JSON.stringify(pedido)
            });
            const data = await res.json();
            if (!res.ok) {
                const detail = data && data.detail;
                avisos = deLaPantalla.concat([typeof detail === 'string' ? detail : 'No se pudieron revisar los avisos.']);
                valor = { error: SIN_CUENTAS };
            } else {
                avisos = deLaPantalla.concat((data && data.avisos) || []);
                valor = (data && data.valor) || null;
            }
        } catch (err) {
            console.warn('[avisos] no se pudieron pedir', err);
            avisos = deLaPantalla.concat(['No se pudieron revisar los avisos; aparecen al generar.']);
            valor = { error: SIN_CUENTAS };
        }
        if (seq !== avisosSeq) return;   // llegó uno más nuevo
        pintarValor(valor, firma);
        panel.hidden = !avisos.length;
        if (count) count.textContent = avisos.length ? '· ' + avisos.length : '';
        list.innerHTML = avisos.map(function (msg) {
            const clean = stripLeadingIcon(String(msg));
            const ref = extractItemRef(clean);
            return '<li>' +
                '<span class="issue-row">' + (ref ? CDI.escapeHtml(ref) : '') + '</span>' +
                '<span class="issue-msg">' + CDI.escapeHtml(clean) + '</span>' +
                '</li>';
        }).join('');
    }

    /* ---------- Ajustes y seguro (VALOR-1) ---------- */
    // Los ajustes los carga la persona: el descuento de la planilla se ofrece
    // con un botón y nunca se pone solo. Las cuentas las hace el servidor,
    // con la misma cuenta del MDDTFOB del TXT.
    let valorEnlazado = false;
    let ultimoValor = null;
    let cuentasCon = null;   // el pedido con el que se hizo ultimoValor
    const SIN_CUENTAS = 'No se pudieron hacer las cuentas: mirá los avisos.';

    // Vacío es sin ajuste (null). Lo que no se puede leer viaja tal cual: el
    // servidor lo dice en las cuentas y no frena el TXT (SEPARADORES-1b, D19).
    // SEPARADORES-1: «1.500» es mil quinientos (montos_ar.js).
    function ajusteDelPedido(v) {
        const r = CDI.montos.leer(v);
        return r.error ? String(v).trim() : r.valor;
    }

    // Por qué un ajuste escrito no se puede leer, o null.
    function ajusteMalEscrito(v) {
        const error = CDI.montos.leer(v).error;
        if (!error) return null;
        return error === CDI.montos.NO_ES_NUMERO ? 'no es un número.' : error;
    }

    // Flete, seguro o gastos de la revisión, que ya frena lo que no se lee.
    // Si igual llega uno así, viaja tal cual y el servidor lo rechaza con su
    // mensaje: nunca un 0 silencioso (SEPARADORES-1b, D19). Vacío es 0.
    function montoDelPedido(v) {
        const r = CDI.montos.leer(v);
        if (r.error) return String(v).trim();
        return r.valor === null ? 0 : r.valor;
    }

    function importeEscrito(n) {
        return Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // El pedido sin lo que cambia solo (el número de operación sin factura
    // lleva la hora): si cambia, las cuentas que se hicieron con él no valen.
    function firmaDelPedido(pedido) {
        const resto = Object.assign({}, pedido);
        delete resto.operation_id;
        return JSON.stringify(resto);
    }

    // Cambió algo de la cuenta: las cuentas a la vista ya no valen, ni las
    // que están por llegar, hasta que vuelvan las nuevas.
    function cuentasViejas() {
        ultimoValor = null;
        avisosSeq++;
        ['valorCalcularSeguro', 'valorDejarSeguro'].forEach(function (id) {
            const boton = document.getElementById(id);
            if (boton) boton.hidden = true;
        });
    }

    function enlazarValor() {
        const wrap = document.getElementById('valorWrap');
        if (valorEnlazado || !wrap) return;
        valorEnlazado = true;
        const programar = () => {
            clearTimeout(avisosTimer);
            avisosTimer = setTimeout(refrescarAvisos, 400);
        };
        const campos = { valorIncluir: 'ajustes_incluir', valorDeducir: 'ajustes_deducir' };
        Object.keys(campos).forEach(function (id) {
            const input = document.getElementById(id);
            if (!input) return;
            input.addEventListener('input', function () {
                const op = CDI.state.operacion = CDI.state.operacion || {};
                op[campos[id]] = input.value;
                cuentasViejas();
                programar();
            });
        });
        const usar = document.getElementById('valorUsarDescuento');
        if (usar) usar.addEventListener('click', usarDescuento);
        const seguro = document.getElementById('valorCalcularSeguro');
        if (seguro) seguro.addEventListener('click', calcularSeguro);
        const dejar = document.getElementById('valorDejarSeguro');
        if (dejar) dejar.addEventListener('click', dejarSeguro);
    }

    // El seguro que calculó el sistema con otros importes queda como está:
    // pasa a ser de la persona y el servidor deja de frenarlo (VALOR-1c).
    function dejarSeguro() {
        const op = CDI.state.operacion = CDI.state.operacion || {};
        delete op.seguro_calculado;
        cuentasViejas();
        refrescarAvisos();
    }

    function usarDescuento() {
        const op = CDI.state.operacion = CDI.state.operacion || {};
        const descuento = Number(op.descuento);
        if (!(descuento > 0) || otroDeducir(op, descuento)) return;
        op.ajustes_deducir = CDI.montos.escribir(descuento);
        const input = document.getElementById('valorDeducir');
        if (input) input.value = op.ajustes_deducir;
        cuentasViejas();
        refrescarAvisos();
    }

    // Ajustes a deducir ya trae algo distinto del descuento: no se pisa.
    function otroDeducir(op, descuento) {
        const v = op.ajustes_deducir;
        return v !== undefined && v !== null && String(v).trim() !== '' && ajusteDelPedido(v) !== descuento;
    }

    // El seguro sugerido lo calculó el servidor con el pedido de ahora. Si
    // algo cambió desde entonces (un ajuste, el descuento, el seguro, otra
    // operación), no se usa: se piden las cuentas de nuevo.
    function calcularSeguro() {
        if (!ultimoValor || ultimoValor.error) return;
        let ahora = null;
        try { ahora = firmaDelPedido(buildMariaRequest()); } catch (err) { ahora = null; }
        if (!cuentasCon || cuentasCon !== ahora) {
            cuentasViejas();
            refrescarAvisos();
            return;
        }
        const op = CDI.state.operacion = CDI.state.operacion || {};
        op.seguro = ultimoValor.seguro_sugerido;
        op.seguro_calculado = true;
        // Ya está completo: deja de avisarse que no se leyó (MARIA-1c).
        if (Array.isArray(op.campos_sin_leer) && op.campos_sin_leer.includes('seguro')) {
            const completados = new Set(op.campos_completados || []);
            completados.add('seguro');
            op.campos_completados = Array.from(completados);
        }
        cuentasViejas();
        refrescarAvisos();
        if (CDI.semaforo && CDI.semaforo.refresh) CDI.semaforo.refresh();
    }

    function seguroSinLeer(op) {
        return Array.isArray(op.campos_sin_leer) && op.campos_sin_leer.includes('seguro') &&
            !(Array.isArray(op.campos_completados) && op.campos_completados.includes('seguro'));
    }

    function pintarValor(valor, firma) {
        ultimoValor = valor;
        cuentasCon = firma || null;
        const op = (CDI.state && CDI.state.operacion) || {};
        const incluir = document.getElementById('valorIncluir');
        const deducir = document.getElementById('valorDeducir');
        // Lo que la persona está escribiendo no se pisa, y un número mal
        // escrito queda a la vista para que lo corrija.
        if (incluir && document.activeElement !== incluir && !ajusteMalEscrito(op.ajustes_incluir)) {
            incluir.value = op.ajustes_incluir == null ? '' : op.ajustes_incluir;
        }
        if (deducir && document.activeElement !== deducir && !ajusteMalEscrito(op.ajustes_deducir)) {
            deducir.value = op.ajustes_deducir == null ? '' : op.ajustes_deducir;
        }

        const ofrece = document.getElementById('valorDescuento');
        const ofreceTexto = document.getElementById('valorDescuentoTexto');
        const descuento = Number(op.descuento);
        // Ya usado como ajuste, no se vuelve a ofrecer.
        if (ofrece) ofrece.hidden = !(descuento > 0) || ajusteDelPedido(op.ajustes_deducir) === descuento;
        const otro = descuento > 0 && otroDeducir(op, descuento);
        const usar = document.getElementById('valorUsarDescuento');
        if (usar) usar.hidden = otro;
        if (ofreceTexto && descuento > 0) {
            const filas = Array.isArray(op.filas_excel_descuento) ? op.filas_excel_descuento : [];
            ofreceTexto.textContent = 'La planilla trae un descuento de ' + importeEscrito(descuento) +
                (filas.length ? ' (fila ' + filas.slice(0, 5).join(', ') + ')' : '') + '.' +
                (otro ? ' Ajustes a deducir ya tiene otro importe: si el descuento va aparte, sumalo a mano.' : '');
        }

        const error = document.getElementById('valorError');
        const errores = [];
        if (ajusteMalEscrito(op.ajustes_incluir)) errores.push('Ajustes a incluir: ' + ajusteMalEscrito(op.ajustes_incluir));
        if (ajusteMalEscrito(op.ajustes_deducir)) errores.push('Ajustes a deducir: ' + ajusteMalEscrito(op.ajustes_deducir));
        if (valor && valor.error) errores.push(valor.error);
        if (error) {
            error.textContent = errores.join(' ');
            error.hidden = !errores.length;
            error.style.color = 'var(--danger,#c0392b)';
        }

        const cuentas = document.getElementById('valorCuentas');
        const boton = document.getElementById('valorCalcularSeguro');
        const nota = document.getElementById('valorSeguroNota');
        const ok = valor && !valor.error;
        if (cuentas) {
            const filas = ok ? [
                ['FOB de la factura (va al TXT)', valor.fob_factura],
                ['+ Ajustes a incluir', valor.ajustes_incluir],
                ['− Ajustes a deducir', valor.ajustes_deducir],
                ['= FOB casillero', valor.fob_casillero],
                ['Flete', valor.flete],
                ['Seguro', valor.seguro]
            ] : [];
            cuentas.innerHTML = filas.map(function (f) {
                return '<tr><td>' + CDI.escapeHtml(f[0]) + '</td><td style="text-align:right">' +
                    CDI.escapeHtml(importeEscrito(f[1])) + '</td></tr>';
            }).join('');
        }
        // El botón, cuando no hay seguro o cuando el que hay lo puso él.
        const calculado = ok && op.seguro_calculado;
        // Sobre qué FOB va el 1 % lo dice el servidor (BASE_SEGURO_SUGERIDO, D13).
        const base = (ok && valor.base_seguro) || 'FOB';
        const mostrar = ok && (!(valor.seguro > 0) || calculado) && valor.seguro !== valor.seguro_sugerido;
        if (boton) {
            boton.hidden = !mostrar;
            boton.textContent = (calculado ? 'Recalcular seguro' : 'Calcular seguro') +
                ' (1 % de ' + base + ' + flete): ' + (ok ? importeEscrito(valor.seguro_sugerido) : '');
        }
        // Lo calculó con otros importes, o ya no se puede comprobar: el
        // servidor no genera hasta que se recalcule o se deje (VALOR-1c).
        const dejar = document.getElementById('valorDejarSeguro');
        if (dejar) dejar.hidden = !(valor && op.seguro_calculado &&
            (valor.error || valor.seguro !== valor.seguro_sugerido));
        if (nota) {
            nota.textContent = !ok ? '' :
                (calculado && valor.seguro !== valor.seguro_sugerido) ? 'El seguro se calculó con otros importes.' :
                calculado ? 'Seguro calculado: 1 % de (' + base + ' + flete).' :
                valor.seguro > 0 ? 'La operación ya trae seguro.' :
                mostrar && seguroSinLeer(op) ? 'La factura puede traer un seguro que no pudimos leer: ' +
                    'revisala antes de calcularlo.' : '';
        }
    }

    function subitemsDelPedido(it) {
        const subs = Array.isArray(it.subitems) ? it.subitems : [];
        if (!subs.length) return undefined;
        return subs.map(s => {
            const sub = { cantidad: toNumber(s.cantidad, 0), valor_unitario: toNumber(s.valor_unitario, 0) };
            const sufijo = String(s.sufijo || '').trim();
            if (sufijo) sub.sufijo = sufijo;
            return sub;
        });
    }

    function toNumber(v, fallback) {
        const n = Number(v);
        return isFinite(n) ? n : fallback;
    }

    function renderValidation(data) {
        hide(vLoading);
        show(vResults);

        const errores = data.errores || [];
        const advertencias = data.advertencias || [];
        const sugerencias = data.sugerencias || [];
        const stats = data.estadisticas || {};

        // Status pill
        let kind = 'clean';
        let label = 'Todo listo para generar';
        let subtitle = 'No se detectaron problemas críticos. El archivo MARIA puede generarse.';
        if (errores.length > 0) {
            kind = 'error';
            label = errores.length + (errores.length === 1 ? ' error para corregir' : ' errores para corregir');
            subtitle = 'Revisá los puntos en rojo antes de generar el archivo.';
        } else if (advertencias.length > 0) {
            kind = 'warning';
            label = advertencias.length + (advertencias.length === 1 ? ' advertencia para revisar' : ' advertencias para revisar');
            subtitle = 'Se puede continuar, pero conviene revisar las advertencias para evitar demoras en AFIP.';
        }
        vStatus.className = 'validating-status is-' + kind;
        vStatus.innerHTML = '<span class="dot-status is-' + (kind === 'clean' ? 'success' : kind) + '"></span>' +
            CDI.escapeHtml(label);
        vSubtitle.textContent = subtitle;

        // Stats
        const statsHtml = [
            statCell(stats.total_items, 'Ítems', ''),
            statCell(stats.ncms_unicos, 'NCMs distintos', ''),
            statCell(
                '$' + formatNumber(stats.total_valor_usd || 0),
                'Valor (USD)', ''
            ),
            statCell(
                formatNumber(stats.total_peso_kg || 0) + ' kg',
                'Peso total', ''
            )
        ].join('');
        vStats.innerHTML = statsHtml;

        // Issues
        const groups = [];
        if (errores.length)       groups.push(renderGroup('error',   'Errores críticos', errores));
        if (advertencias.length)  groups.push(renderGroup('warning', 'Advertencias',     advertencias));
        if (sugerencias.length)   groups.push(renderGroup('info',    'Sugerencias',      sugerencias));
        vIssues.innerHTML = groups.join('');

        // Generate button
        vGenerate.disabled = errores.length > 0;
        vGenerate.title = errores.length > 0 ? 'Corregí los errores antes de generar' : '';
    }

    function statCell(value, label) {
        const v = (value === null || value === undefined || value === '') ? '—' : String(value);
        return (
            '<div class="validating-stat">' +
                '<div class="validating-stat-num">' + CDI.escapeHtml(v) + '</div>' +
                '<div class="validating-stat-label">' + CDI.escapeHtml(label) + '</div>' +
            '</div>'
        );
    }

    function renderGroup(kind, title, list) {
        const rows = list.map(msg => {
            const clean = stripLeadingIcon(String(msg));
            const rowRef = extractItemRef(clean);
            return (
                '<li>' +
                    (rowRef ? '<span class="issue-row">' + CDI.escapeHtml(rowRef) + '</span>' : '<span class="issue-row"></span>') +
                    '<span class="issue-msg">' + CDI.escapeHtml(clean) + '</span>' +
                '</li>'
            );
        }).join('');
        return (
            '<div class="issue-group is-' + kind + '">' +
                '<header class="issue-group-header">' +
                    '<strong>' + CDI.escapeHtml(title) + '</strong>' +
                    '<span class="caption">· ' + list.length + '</span>' +
                '</header>' +
                '<ul class="issue-list">' + rows + '</ul>' +
            '</div>'
        );
    }

    // Backend a veces manda "✅ ", "⚠️ ", "📋 ", etc. Sacamos el emoji inicial
    // para que la UI quede consistente con el style minimalista.
    function stripLeadingIcon(s) {
        return s.replace(/^[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\s]+/u, '').trim();
    }
    function extractItemRef(s) {
        const m = /\b(i|I)tem\s+(\d+)/.exec(s);
        return m ? ('#' + m[2]) : '';
    }

    function formatNumber(n) {
        const num = Number(n) || 0;
        try {
            return num.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        } catch (_) {
            return String(num.toFixed(2));
        }
    }

    /* ==========================================================
       Pantalla 5: ready (generar + descargar)
       ========================================================== */
    async function onGenerate() {
        if (lastValidation && (lastValidation.errores || []).length > 0) return;

        // Guardar SBT del input al estado antes de generar
        CDI.state = CDI.state || {};
        CDI.state.operacion = CDI.state.operacion || {};
        if (sbtInput) {
            CDI.state.operacion.sbt_sufijo_valor = sbtInput.value.trim();
        }
        // Validación frontend: si está vacío, mostrar error junto al campo.
        // No hace falta si todos los productos llevan sufijo propio, en sus
        // subítems (SUBITEMS-1) o en «Lo que decide el despachante»
        // (SUFIJOS-1); el servidor tampoco lo pide.
        const todosConSufijoPropio = Boolean(CDI.despachante && CDI.despachante.todosConPropio());
        if (!CDI.state.operacion.sbt_sufijo_valor && !todosConSufijoPropio) {
            if (sbtError) {
                sbtError.textContent = 'Ingresá el sufijo de valor SBT. Es obligatorio.';
                sbtError.hidden = false;
            }
            if (sbtInput) sbtInput.focus();
            return;
        }
        if (sbtError) sbtError.hidden = true;
        // MARIA-4: origen argentino sin estado no se genera (no se inventa).
        if (CDI.despachante && !CDI.despachante.leer()) return;

        CDI.goTo('ready', { fromValidating: true });
    }

    function onEnterReady() {
        init();
        if (!rGenerating) return;
        hide(rDone);
        hide(rError);
        show(rGenerating);
        generateMaria();
    }

    async function generateMaria() {
        if (generateInFlight) { pedidaMientrasOtra = true; return; }
        generateInFlight = true;
        if (CDI.estudios) await CDI.estudios.listo();

        const items = (CDI.state && CDI.state.items) || [];
        if (!items.length) {
            showReadyError('No hay ítems para generar. Volvé a cargar el PDF.');
            generateInFlight = false;
            return;
        }

        // Una carga nueva reemplaza CDI.state: la respuesta tardía se anota en la suya.
        const carga = CDI.state;
        const foto = fotoDeLaPantalla();
        const body = buildMariaRequest();
        // Regenerar la misma operación no la cuenta otra vez: el servidor la reconoce por su id.
        body.operacion_id = carga.operacionId || '';
        try {
            const startedAt = Date.now();
            const res = await CDI.api('/generate_maria', {
                method: 'POST',
                body: JSON.stringify(body)
            });
            const data = await res.json();
            const dur = Date.now() - startedAt;
            const fallo = !res.ok || !data || data.success === false;
            // El error de una carga que ya no está en pantalla no la cambia de paso.
            if (fallo && carga !== CDI.state) return;
            if (fallo) {
                const detail = (data && (data.detail || data.message)) || res.statusText;
                // El error de un subítem (su sufijo incluido) va bajo ese
                // subítem, en el paso de NCM (SUBITEMS-1, MARIA-9).
                const sub = typeof detail === 'string' &&
                    /^(?:Item|Sufijo de valor del ítem) (\d+), sub-ítem (\d+): /.exec(detail);
                if (sub && CDI.ncmBatch && CDI.ncmBatch.marcarErrorDeSubitem &&
                        CDI.ncmBatch.marcarErrorDeSubitem(parseInt(sub[1], 10) - 1, parseInt(sub[2], 10) - 1, detail)) {
                    CDI.goTo('ncm');
                    throw new Error(detail);
                }
                // Si el error es de SBT o del sufijo de la operación, mostrar
                // junto al campo y volver a validación
                if (typeof detail === 'string' && (detail.toLowerCase().includes('sbt') ||
                        detail.startsWith('Sufijo de valor de la operación: '))) {
                    if (sbtError) {
                        sbtError.textContent = detail;
                        sbtError.hidden = false;
                    }
                    CDI.goTo('validating');
                    throw new Error(detail);
                }
                // El seguro calculado con otros importes se resuelve en
                // «Ajustes y seguro» (VALOR-1c).
                if (typeof detail === 'string' && detail.startsWith('Seguro: lo calculó el sistema')) {
                    CDI.goTo('validating');
                    throw new Error(detail);
                }
                // Los controles de antes de generar llegan como {errors: [...]}.
                const texto = (detail && Array.isArray(detail.errors)) ? detail.errors.join(' ') : detail;
                throw new Error(texto || 'No se pudo generar el archivo');
            }
            carga.operacionId = data.operacion_id || '';
            CDI.track('maria_generated', {
                items: items.length,
                filename: data.filename,
                duration_ms: dur
            });
            if (carga === CDI.state) mostrarListo(data);
            // Best-effort: guardar en historial del cliente activo (si hay)
            saveOperationToHistory(items, data, carga, foto).catch(err => {
                console.warn('[history] no se pudo guardar operacion', err);
            });
            // Best-effort: aprender productos en catalogo del proveedor
            saveCatalogLearn(items, carga).catch(err => {
                console.warn('[catalog] no se pudo aprender', err);
            });
        } catch (err) {
            console.error('[ready] generate error', err);
            CDI.track('maria_generate_error', { message: String(err && err.message || err) });
            showReadyError(String(err && err.message || err));
        } finally {
            generateInFlight = false;
            const otra = pedidaMientrasOtra;
            pedidaMientrasOtra = false;
            // Con lo que hay ahora en pantalla, que puede haber cambiado mientras ésta esperaba.
            if (otra) onEnterReady();
        }
    }

    // Lo que muestra «Listo» es de la carga en pantalla: una respuesta tardía no lo pisa.
    function mostrarListo(data) {
        lastMaria = {
            filename: data.filename,
            download_url: data.download_url,
            content: data.content || '',
            warnings: data.warnings || []
        };
        renderReady();
    }

    // La cabecera que controla el servidor antes de generar (MARIA-1b), tal
    // como saldría en /generate_maria.
    function cabeceraParaValidar() {
        const req = buildMariaRequest();
        return {
            moneda: req.moneda, incoterm: req.incoterm, comprador_cuit: req.comprador_cuit,
            flete: req.flete, seguro: req.seguro,
        };
    }

    function buildMariaRequest() {
        const op = (CDI.state && CDI.state.operacion) || {};
        const stats = (lastValidation && lastValidation.estadisticas) || {};

        // Sin moneda o incoterm no se inventan DOL ni FOB: el control de antes
        // de generar lo marca (MARIA-1b).
        const moneda = (op.moneda || '').toString().trim().toUpperCase();
        const incoterm = (op.incoterm || '').toString().trim().toUpperCase();

        const factura = numeroDeFactura(op);
        // Sin factura, el nombre del archivo sale de cuándo se cargó la operación,
        // así regenerarla no lo cambia. La operación se reconoce por operacionId.
        const cargada = (CDI.state && CDI.state.uploadedAt) || new Date().toISOString();
        const operation_id = factura ? ('FAC_' + factura.replace(/[^a-zA-Z0-9_-]/g, '')) :
            ('OP_' + String(cargada).replace(/[^0-9]/g, '').slice(0, 17));

        const items = (CDI.state.items || []).map((it, i) => ({
            pieza: String(it.pieza || '').trim(),
            descripcion: String(it.descripcion || '').trim(),
            origen: String(it.origen || 'XX').trim().toUpperCase() || 'XX',
            cantidad: toNumber(it.cantidad, 0),
            valor_unitario: toNumber(it.valor_unitario, 0),
            peso_unitario: toNumber(it.peso_unitario, 0),
            codigo_parte: String(it.codigo_parte || '').trim(),
            grupo_id: it.grupo_id || null,
            // MARIA-7: la de la factura y la estadística, elegidas en «Lo
            // que decide el despachante».
            ...(CDI.despachante && CDI.despachante.unidadesDe ? CDI.despachante.unidadesDe(it, i)
                : { unidad: it.unidad || null }),
            estado: it.estado || null,
            iva_adicional: it.iva_adicional || null,
            // El suyo o el propuesto del arancel; vacío, el de la operación (SUFIJOS-1).
            sufijo: (CDI.despachante && CDI.despachante.sufijoDe ? CDI.despachante.sufijoDe(it, i) : '') || null,
            // Partido en subítems (SUBITEMS-1); sin subítems no va el campo.
            subitems: subitemsDelPedido(it)
        }));

        // Cliente activo propaga domicilio + fecha inicio actividad del importador
        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;

        // CUIT del despachante: si el user tiene en perfil, lo usamos
        // automaticamente (backend tambien hace fallback, aca vamos explicitos).
        const cuit_agr = String(
            op.cuit_agr || (CDI.currentUser && CDI.currentUser.cuit) || ''
        ).replace(/[-\s]/g, '');

        return {
            operation_id: operation_id,
            // El número real, para LDVDREFDOC (MARIA-7).
            numero_factura: factura,
            items: items,
            ...(CDI.despachante ? CDI.despachante.valores()
                : { banco_bcra: '', empresa_digitalizacion: null, iva_adicional: null }),
            moneda: moneda,
            incoterm: incoterm,
            cuit_agr: cuit_agr,
            // ESTUDIO-1: si hay uno elegido, su CUIT manda sobre cuit_agr.
            estudio_id: CDI.estudios ? CDI.estudios.elegido() : '',
            vendedor_nombre: String(op.vendedor_nombre || '').trim(),
            vendedor_id: String(op.vendedor_id || '').trim(),
            comprador_nombre: String(op.comprador_nombre || '').trim(),
            comprador_cuit: String(op.comprador_cuit || '').replace(/[-\s]/g, ''),
            comprador_domicilio: String(
                op.comprador_domicilio ||
                (cliente && cliente.direccion) || ''
            ).trim(),
            comprador_fecha_inic_activ: String(
                op.comprador_fecha_inic_activ ||
                (cliente && cliente.fecha_inic_activ) || ''
            ).trim(),
            flete: montoDelPedido(op.flete),
            seguro: montoDelPedido(op.seguro),
            seguro_calculado: !!op.seguro_calculado,
            // MARIA-3: el servidor decide si van al TXT (sólo EXW, FCA o FAS).
            gastos_anteriores_fob: montoDelPedido(op.gastos_anteriores_fob),
            // VALOR-1: sólo para las cuentas; no van al TXT (D12).
            ajustes_incluir: ajusteDelPedido(op.ajustes_incluir),
            ajustes_deducir: ajusteDelPedido(op.ajustes_deducir),
            procedencia: (function () {
                const raw = String(op.procedencia || '').trim();
                return (raw && CDI.paisesMaria && CDI.paisesMaria.resolve(raw)) || raw;
            })(),
            bl_numero: String(op.bl || op.bl_numero || '').trim(),
            puerto_origen: String(op.puerto_origen || '').trim(),
            puerto_destino: String(op.puerto_destino || 'ARBUE').trim() || 'ARBUE',
            buque_nombre: String(op.buque || op.buque_nombre || '').trim(),
            viaje_numero: String(op.viaje_numero || '').trim(),
            fecha_embarque: String(op.fecha_embarque || '').trim(),
            fecha_emision: String(op.fecha_emision || '').trim(),
            contenedor_numero: String(op.contenedor_numero || '').trim(),
            contenedor_tipo: String(op.contenedor_tipo || '').trim(),
            contenedor_peso: toNumber(op.contenedor_peso, 0),
            aduana_codigo: String(op.aduana_codigo || '001').trim() || '001',
            tipo_destinacion: String(op.tipo_destinacion || 'IC04').trim().toUpperCase() || 'IC04',
            sbt_sufijo_valor: String(op.sbt_sufijo_valor || '').trim()
        };
    }

    function renderReady() {
        hide(rGenerating);
        hide(rError);
        show(rDone);
        if (!lastMaria) return;

        const stats = (lastValidation && lastValidation.estadisticas) || {};
        const total = stats.total_items || ((CDI.state.items || []).length);
        rSubtitle.textContent =
            'MARIA.TXT generado. ' + total + ' ítems · ' +
            '$' + formatNumber(stats.total_valor_usd || 0) + ' USD.';

        rFilename.textContent = lastMaria.filename || 'MARIA.TXT';
        rPreview.textContent = trimPreview(lastMaria.content || '', 60);

        // Render de advertencias de KIT Maria (no bloquean la descarga)
        renderReadyWarnings(lastMaria.warnings || []);

        // Render del panel "operación huérfana": aparece solo si no hay
        // cliente activo y el user no hizo "Más tarde" en esta operación.
        renderOrphanPanel();
    }

    /* ---------- Advertencias de KIT Maria ---------- */
    function renderReadyWarnings(warnings) {
        const panel = document.getElementById('readyWarningsPanel');
        const list = document.getElementById('readyWarningsList');
        const count = document.getElementById('readyWarningsCount');
        if (!panel || !list) return;
        if (!warnings || !warnings.length) {
            panel.hidden = true;
            list.innerHTML = '';
            return;
        }
        panel.hidden = false;
        if (count) count.textContent = '· ' + warnings.length;
        list.innerHTML = warnings.map(function (msg) {
            var clean = stripLeadingIcon(String(msg));
            var ref = extractItemRef(clean);
            return '<li>' +
                (ref ? '<span class="issue-row">' + CDI.escapeHtml(ref) + '</span>' : '<span class="issue-row"></span>') +
                '<span class="issue-msg">' + CDI.escapeHtml(clean) + '</span>' +
                '</li>';
        }).join('');
    }

    /* ---------- Panel "operación huérfana" ---------- */
    function renderOrphanPanel() {
        const panel = document.getElementById('readyOrphanPanel');
        if (!panel) return;
        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;
        const opCode = (lastMaria && lastMaria.filename) || null;
        const dismissedFor = (CDI.state && CDI.state.orphanDismissedFor) || null;
        const wasDismissed = !!(dismissedFor && opCode && dismissedFor === opCode);

        if (cliente && cliente.id) { panel.hidden = true; return; }
        if (wasDismissed) { panel.hidden = true; return; }

        panel.hidden = false;
        // Reset del form interno por si quedó abierto antes
        const form = document.getElementById('readyOrphanCreateForm');
        if (form) form.hidden = true;
        clearOrphanCreateError();
        setupOrphanPanelListeners();
        renderOrphanDetectedData();
        prefillOrphanCreateForm();
        try { CDI.track && CDI.track('op_orphan_panel_shown'); } catch (_) {}
    }

    let _orphanListenersWired = false;
    function setupOrphanPanelListeners() {
        if (_orphanListenersWired) return;
        const btnCreate = document.getElementById('orphanCreateBtn');
        const btnAssign = document.getElementById('orphanAssignBtn');
        const btnLater  = document.getElementById('orphanLaterBtn');
        const btnSave   = document.getElementById('orphanCreateSaveBtn');
        const btnCancel = document.getElementById('orphanCreateCancelBtn');
        const form      = document.getElementById('readyOrphanCreateForm');

        if (btnCreate) btnCreate.addEventListener('click', () => {
            CDI.track && CDI.track('op_orphan_create_clicked');
            if (form) form.hidden = false;
            const inp = document.getElementById('orphanCreateNombre');
            if (inp) inp.focus();
        });
        if (btnCancel) btnCancel.addEventListener('click', () => {
            if (form) form.hidden = true;
            clearOrphanCreateError();
        });
        if (btnAssign) btnAssign.addEventListener('click', orphanAssignClick);
        if (btnLater)  btnLater.addEventListener('click', orphanLaterClick);
        if (btnSave)   btnSave.addEventListener('click', orphanCreateSubmit);

        _orphanListenersWired = true;
    }

    function prefillOrphanCreateForm() {
        const op = (CDI.state && CDI.state.operacion) || {};
        const inpNom = document.getElementById('orphanCreateNombre');
        const inpCuit = document.getElementById('orphanCreateCuit');
        const inpDir = document.getElementById('orphanCreateDireccion');
        if (inpNom && !inpNom.value) inpNom.value = String(op.comprador_nombre || '').trim();
        if (inpCuit && !inpCuit.value) {
            const c = String(op.comprador_cuit || '').trim();
            inpCuit.value = (CDI.formatCuit && c) ? CDI.formatCuit(c) : c;
        }
        if (inpDir && !inpDir.value) inpDir.value = String(op.comprador_domicilio || '').trim();
    }

    function renderOrphanDetectedData() {
        const box = document.getElementById('readyOrphanDetected');
        if (!box) return;
        const op = (CDI.state && CDI.state.operacion) || {};
        const rows = [
            ['Razón social', String(op.comprador_nombre || '').trim() || 'No detectado'],
            ['CUIT', formatDetectedCuit(op.comprador_cuit) || 'No detectado'],
            ['Factura', numeroDeFactura(op)],
            ['Fecha', String(op.fecha_emision || '').trim()],
        ].filter(row => row[1]);
        box.innerHTML = rows.map(row => (
            '<div class="ready-orphan-detected-row">' +
                '<span>' + escapeHtml(row[0]) + '</span>' +
                '<strong>' + escapeHtml(row[1]) + '</strong>' +
            '</div>'
        )).join('');
        box.hidden = !rows.length;
        try {
            CDI.track && CDI.track('op_orphan_invoice_data_prefilled', {
                has_cuit: !!String(op.comprador_cuit || '').trim(),
                has_address: !!String(op.comprador_domicilio || '').trim()
            });
        } catch (_) {}
    }

    function formatDetectedCuit(cuit) {
        const raw = String(cuit || '').trim();
        if (!raw) return '';
        return (CDI.formatCuit ? CDI.formatCuit(raw) : raw);
    }

    function escapeHtml(value) {
        return String(value || '').replace(/[&<>"']/g, ch => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[ch]));
    }

    function showOrphanCreateError(msg) {
        const el = document.getElementById('orphanCreateError');
        if (!el) return;
        el.textContent = msg || '';
        el.hidden = !msg;
    }
    function clearOrphanCreateError() { showOrphanCreateError(''); }

    function showReadyClientSuccess(title, text) {
        const el = document.getElementById('readyClientSuccess');
        if (!el) return;
        const titleEl = el.querySelector('[data-client-success-title]');
        const textEl = el.querySelector('[data-client-success-text]');
        if (titleEl) titleEl.textContent = title || '';
        if (textEl) textEl.textContent = text || '';
        el.hidden = false;
        try { el.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } catch (_) {}
    }

    async function lookupClienteByCuit(cuit) {
        try {
            const res = await CDI.api('/api/clientes/by-cuit/' + encodeURIComponent(cuit));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) return null;
            if (data.match === 'exact' && data.cliente) return data.cliente;
            return null;
        } catch (_) { return null; }
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

    async function orphanCreateSubmit() {
        const btn = document.getElementById('orphanCreateSaveBtn');
        const inpNom = document.getElementById('orphanCreateNombre');
        const inpCuit = document.getElementById('orphanCreateCuit');
        const inpDir = document.getElementById('orphanCreateDireccion');
        const nombre = String((inpNom && inpNom.value) || '').trim();
        const cuitRaw = String((inpCuit && inpCuit.value) || '').trim();
        const cuit = (CDI.normalizeCuit && cuitRaw) ? CDI.normalizeCuit(cuitRaw) : '';
        const direccion = String((inpDir && inpDir.value) || '').trim();
        clearOrphanCreateError();
        if (!nombre) {
            showOrphanCreateError('Ingresá la razón social.');
            if (inpNom) inpNom.focus();
            return;
        }
        if (cuit && cuit.length !== 11) {
            showOrphanCreateError('El CUIT debe tener 11 dígitos.');
            if (inpCuit) inpCuit.focus();
            return;
        }
        if (btn) btn.disabled = true;
        try {
            // Pre-check: si ya existe un cliente con este CUIT, ofrecer usar ese.
            if (cuit) {
                const existente = await lookupClienteByCuit(cuit);
                if (existente) {
                    CDI.track && CDI.track('op_orphan_create_blocked_by_cuit_match');
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
                        await reSaveOperationAndClosePanel('create');
                    }
                    return;
                }
            }
            const body = { nombre: nombre };
            if (cuit) body.cuit = cuit;
            if (direccion) body.direccion = direccion;
            const res = await CDI.api('/api/clientes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const out = await res.json().catch(() => ({}));
            if (!res.ok || !out.success || !out.cliente) {
                showOrphanCreateError(humanizeApiError(out.detail, 'No se pudo crear el cliente.'));
                return;
            }
            CDI.clientesCache = [];
            CDI.setClienteActivo(out.cliente);
            await reSaveOperationAndClosePanel('create');
        } catch (err) {
            showOrphanCreateError('Error de red. Probá de nuevo.');
            console.warn('[orphan] crear cliente', err && err.message);
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    function orphanAssignClick() {
        if (!CDI.openClientePicker) return;
        CDI.track && CDI.track('op_orphan_assign_clicked');
        CDI.openClientePicker({
            title: 'Asignar a un cliente existente',
            subtitle: 'La operación va a quedar guardada en su historial',
            onSelect: async (c) => {
                CDI.setClienteActivo(c);
                await reSaveOperationAndClosePanel('assign');
            },
        });
    }

    function orphanLaterClick() {
        const opCode = (lastMaria && lastMaria.filename) || null;
        if (opCode) {
            CDI.state = CDI.state || {};
            CDI.state.orphanDismissedFor = opCode;
        }
        const panel = document.getElementById('readyOrphanPanel');
        if (panel) panel.hidden = true;
        CDI.track && CDI.track('op_orphan_dismissed');
    }

    async function reSaveOperationAndClosePanel(via) {
        const items = (CDI.state && CDI.state.items) || [];
        await saveOperationToHistory(items, lastMaria || {});
        const panel = document.getElementById('readyOrphanPanel');
        if (panel) panel.hidden = true;
        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;
        const nombre = (cliente && cliente.nombre) || 'cliente';
        showReadyClientSuccess(
            via === 'assign' ? 'Cliente asignado a esta operación' : 'Cliente creado con éxito',
            'Operación asociada a ' + nombre + '. La próxima factura con este CUIT se detecta sola.'
        );
        CDI.toast && CDI.toast(
            'Cliente guardado',
            'La próxima factura con este CUIT se detecta sola. Operación asociada a ' + nombre + '.',
            'success'
        );
        CDI.track && CDI.track('op_orphan_resolved', { via: via });
    }

    // Cliente, totales y valores del despachante, tomados al pedir: lo que cambie después no los pisa.
    function fotoDeLaPantalla() {
        return { cliente: (CDI.state && CDI.state.clienteActivo) || null,
                 stats: (lastValidation && lastValidation.estadisticas) || {},
                 maria: CDI.despachante ? CDI.despachante.valores() : {} };
    }

    async function saveOperationToHistory(items, mariaData, carga, foto = fotoDeLaPantalla()) {
        carga = carga || (CDI.state = CDI.state || {});
        // Sin cliente al pedir, el que se le eligió a esa carga mientras esperaba.
        const cliente = foto.cliente || carga.clienteActivo || null;
        if (!cliente || !cliente.id) {
            console.warn('[history] no hay cliente activo, no se guarda al historial');
            return { ok: false, reason: 'sin_cliente' };
        }
        const opCode = (mariaData && mariaData.filename) || null;
        // Idempotencia: si ya guardamos esta misma operación para este mismo
        // cliente, no la re-posteamos (cubre re-entry a Listo, F5 suave, etc.).
        const savedFor = carga.operationSavedFor || null;
        if (savedFor && savedFor.cliente_id === cliente.id && savedFor.op_code === opCode) {
            return { ok: true, reason: 'ya_guardada' };
        }
        const stats = foto.stats;
        const op = carga.operacion || {};
        const total_valor = Number(stats.total_valor_usd || 0);
        const total_peso = Number(stats.total_peso_kg || 0);
        const body = {
            operation_id: opCode,
            operacion_id: carga.operacionId || '',
            source: 'pdf_v2',
            currency: (op.moneda || 'USD').toString().toUpperCase(),
            comprador_domicilio: op.comprador_domicilio || '',
            comprador_fecha_inic_activ: op.comprador_fecha_inic_activ || '',
            resumen: {
                items: items.length,
                valor_total: total_valor,
                peso_total: total_peso,
                ncms_unicos: stats.ncms_unicos || 0,
                numero_factura: op.numero_factura || '',
                fecha_emision: op.fecha_emision || '',
                // MARIA-4: para proponer el último banco y la última empresa.
                maria: Object.assign(
                    { banco_bcra: '', empresa_digitalizacion: '', iva_adicional: '' },
                    foto.maria,
                    { items: items.map(it => ({ estado: it.estado || null, iva_adicional: it.iva_adicional || null })) }
                )
            },
            items: items.map(it => ({
                pieza: String(it.pieza || '').trim(),
                ncm: String(it.pieza || '').trim(),
                descripcion: String(it.descripcion || '').trim(),
                origen: String(it.origen || '').trim().toUpperCase(),  // sin «XX» inventado (MARIA-1b)
                cantidad: toNumber(it.cantidad, 0),
                valor_unitario: toNumber(it.valor_unitario, 0),
                peso_unitario: toNumber(it.peso_unitario, 0),
                grupo_id: it.grupo_id || null,
                unidad: it.unidad || null
            }))
        };
        try {
            const res = await CDI.api(
                '/api/clientes/' + encodeURIComponent(cliente.id) + '/operaciones',
                { method: 'POST', body: JSON.stringify(body) }
            );
            const data = await res.json().catch(() => ({}));
            if (res.ok && data && data.success) {
                // Guardar antes de generar crea la operación: generar después la completa, no cuenta otra.
                carga.operacionId = data.operation_id || '';
                carga.operationSavedFor = { cliente_id: cliente.id, op_code: opCode };
                CDI.track('operation_saved_to_history', {
                    cliente_id: cliente.id,
                    items: items.length
                });
                return { ok: true, cliente_id: cliente.id };
            }
            // Error real: mostrar al user en vez de silenciar.
            // Preferimos dev_detail (técnico) si vino, para diagnosticar; si no, el detail amigable.
            const dev = data && data.dev_detail;
            const msg = dev || (data && data.detail) || ('HTTP ' + res.status);
            console.error('[history] save_client_operation fallo:', msg, data);
            CDI.track('operation_save_failed', {
                cliente_id: cliente.id,
                status: res.status,
                detail: String(msg).slice(0, 120)
            });
            CDI.toast && CDI.toast(
                'No se guardó al cliente',
                'La operación no quedó en el historial de ' + (cliente.nombre || 'el cliente') + '. Detalle: ' + String(msg).slice(0, 100),
                'error'
            );
            return { ok: false, reason: 'http_error', error: msg };
        } catch (err) {
            if (err && err.code === 'payment_required') {
                console.warn('[history] save_client_operation: 402 payment required');
                return { ok: false, reason: 'payment_required', error: 'Plan vencido o límite alcanzado' };
            }
            console.error('[history] save_client_operation excepción:', err);
            CDI.track('operation_save_failed', {
                cliente_id: cliente.id,
                detail: String(err && err.message || err).slice(0, 120)
            });
            CDI.toast && CDI.toast(
                'No se guardó al cliente',
                'Error de red al guardar la operación al historial. Volvé a Listo y reintentá.',
                'error'
            );
            return { ok: false, reason: 'network', error: String(err) };
        }
    }

    // Expongo para que el panel huérfano u otro lugar pueda forzar un reintento.
    CDI.saveOperationToHistory = saveOperationToHistory;

    async function saveCatalogLearn(items, carga) {
        const op = (carga && carga.operacion) || {};
        const vendorName = String(op.vendedor_nombre || '').trim();
        if (!vendorName || !Array.isArray(items) || !items.length) return;

        const productos = items.map(it => ({
            descripcion: String(it.descripcion || '').trim(),
            ncm: String(it.pieza || '').trim(),
            origen: String(it.origen || '').trim().toUpperCase(),
            unidad_medida: String(it.unidad_medida || '').trim(),
        })).filter(p => p.descripcion && p.ncm);

        if (!productos.length) return;

        // Derivar vendor_id slug (mismo criterio que backend: alfanumerico lowercased sin acentos)
        const vendor_id = vendorName
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
            .slice(0, 64) || 'proveedor';
        try {
            const res = await CDI.api('/api/catalog/' + encodeURIComponent(vendor_id) + '/productos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vendor_name: vendorName, productos }),
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                CDI.track('catalog_learn', {
                    vendor_id,
                    productos: productos.length,
                    saved: data && (data.saved || data.added) || 0,
                    updated: data && data.updated || 0,
                });
            }
        } catch (_) { /* best-effort */ }
    }

    function trimPreview(text, maxLines) {
        if (!text) return '';
        const lines = text.split(/\r?\n/);
        if (lines.length <= maxLines) return text;
        return lines.slice(0, maxLines).join('\n') + '\n…';
    }

    function showReadyError(msg) {
        hide(rGenerating);
        hide(rDone);
        show(rError);
        const errText = document.getElementById('readyErrorText');
        if (errText) errText.textContent = msg || 'No se pudo generar el archivo.';
        else rError.textContent = msg || 'No se pudo generar el archivo.';
    }

    /* ---------- Actions ---------- */
    function onDownload() {
        if (!lastMaria || !lastMaria.download_url) {
            CDI.toast('Archivo no disponible', 'Volvé a generarlo.', 'error');
            return;
        }
        CDI.track('maria_download_click', { filename: lastMaria.filename });
        // Descarga con token via anchor: como el endpoint /download/<file>
        // no requiere auth en este proyecto, basta con un anchor.
        const a = document.createElement('a');
        a.href = lastMaria.download_url;
        a.download = lastMaria.filename || 'MARIA.TXT';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    async function onCopy() {
        if (!lastMaria || !lastMaria.content) return;
        try {
            await navigator.clipboard.writeText(lastMaria.content);
            CDI.toast('Copiado', 'El contenido del TXT está en el portapapeles.', 'success');
            CDI.track('maria_copied');
        } catch (err) {
            CDI.toast('No se pudo copiar', 'Seleccioná y copiá manualmente.', 'error');
        }
    }

    document.addEventListener('click', (e) => {
        const t = e.target.closest('[data-action="go-ncm-from-validating"]');
        if (t) {
            e.preventDefault();
            CDI.goTo('ncm');
        }
        
        const retry = e.target.closest('[data-action="retry-generate"]');
        if (retry) {
            e.preventDefault();
            // Oculta el error, y con él el botón: un segundo clic no pide otra generación.
            onEnterReady();
        }
    });

    /* ---------- Registro ---------- */
    CDI.registerScreen('validating', {
        onEnter: onEnterValidating,
        onLeave() { /* nada */ }
    });
    CDI.registerScreen('ready', {
        onEnter: onEnterReady,
        onLeave() {
            // Si el usuario va a 'upload' (nueva operacion), limpiamos cache
            lastMaria = null;
            // Fuera de «Listo», la carga que esperaba no genera sola.
            pedidaMientrasOtra = false;
        }
    });

    document.addEventListener('DOMContentLoaded', init);
})();
