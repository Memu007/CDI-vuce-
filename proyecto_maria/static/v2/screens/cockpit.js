/* ============================================================
   CDI v2 - Cockpit de operaciones
   Tablero unico: lista todas las operaciones del despachante con
   estado/canal editables. Reemplaza el Excel de seguimiento.
   Endpoints: GET /api/operations, PATCH /api/operations/{id}/estado
   ============================================================ */
(function () {
    'use strict';
    var CDI = window.CDI = window.CDI || {};

    // Estados (hitos) en orden. Deben coincidir con COCKPIT_ESTADOS del backend.
    var ESTADOS = [
        { id: 'borrador', label: 'Borrador' },
        { id: 'oficializada', label: 'Oficializada' },
        { id: 'canal', label: 'Canal asignado' },
        { id: 'liberada', label: 'Liberada' }
    ];
    var CANALES = ['verde', 'naranja', 'rojo'];

    var filtroActivo = null; // null = todos
    var ultimoData = null;

    function $(id) { return document.getElementById(id); }

    function fmtMoney(value, currency) {
        var n = Number(value || 0);
        try {
            return n.toLocaleString('es-AR', { style: 'currency', currency: currency || 'USD', maximumFractionDigits: 0 });
        } catch (_) {
            return (currency || 'USD') + ' ' + n.toFixed(0);
        }
    }

    function fmtFecha(iso) {
        if (!iso) return '—';
        try {
            return new Date(iso).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: '2-digit' });
        } catch (_) { return '—'; }
    }

    function estadoLabel(id) {
        var e = ESTADOS.find(function (x) { return x.id === id; });
        return e ? e.label : (id || 'Borrador');
    }

    function show(el, on) { if (el) el.hidden = !on; }

    function renderFiltros(counts, total) {
        var host = $('ckFilters');
        if (!host) return;
        var chips = [];
        chips.push(chip(null, 'Todas', total));
        ESTADOS.forEach(function (e) {
            chips.push(chip(e.id, e.label, (counts && counts[e.id]) || 0));
        });
        host.innerHTML = chips.join('');

        function chip(id, label, n) {
            var active = (id === filtroActivo) ? ' is-active' : '';
            return '<button type="button" class="ck-chip' + active + '" data-estado="' +
                (id || '') + '">' + CDI.escapeHtml(label) +
                ' <span class="ck-chip-count">' + n + '</span></button>';
        }
    }

    function estadoSelect(op) {
        var opts = ESTADOS.map(function (e) {
            var sel = (op.estado === e.id) ? ' selected' : '';
            return '<option value="' + e.id + '"' + sel + '>' + CDI.escapeHtml(e.label) + '</option>';
        }).join('');
        return '<select class="ck-estado-select" data-op="' + CDI.escapeHtml(op.id) +
            '" aria-label="Estado de la operación">' + opts + '</select>';
    }

    function canalCell(op) {
        // Solo relevante cuando el estado es 'canal' o 'liberada'
        var opts = ['<option value="">—</option>'].concat(CANALES.map(function (c) {
            var sel = (op.canal === c) ? ' selected' : '';
            return '<option value="' + c + '"' + sel + '>' + c.charAt(0).toUpperCase() + c.slice(1) + '</option>';
        })).join('');
        return '<select class="ck-canal-select ck-canal-' + (op.canal || 'none') +
            '" data-op="' + CDI.escapeHtml(op.id) + '" aria-label="Canal aduanero">' + opts + '</select>';
    }

    function renderTabla(ops) {
        var body = $('ckTableBody');
        if (!body) return;
        body.innerHTML = ops.map(function (op) {
            return '<tr>' +
                '<td class="ck-op-code">' + CDI.escapeHtml(op.op_code || op.id) + '</td>' +
                '<td>' + CDI.escapeHtml(op.cliente || 'Sin cliente') + '</td>' +
                '<td>' + estadoSelect(op) + '</td>' +
                '<td>' + canalCell(op) + '</td>' +
                '<td>' + (op.total_items || 0) + '</td>' +
                '<td>' + fmtMoney(op.total_value, op.currency) + '</td>' +
                '<td>' + fmtFecha(op.fecha) + '</td>' +
                '</tr>';
        }).join('');
    }

    async function cargar() {
        show($('ckLoading'), true);
        show($('ckError'), false);
        show($('ckEmpty'), false);
        show($('ckTableWrap'), false);
        try {
            var url = '/api/operations' + (filtroActivo ? ('?estado=' + filtroActivo) : '');
            var resp = await CDI.api(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            ultimoData = data;
            show($('ckLoading'), false);

            renderFiltros(data.counts, data.total);

            var ops = data.operaciones || [];
            if (data.total === 0) {
                show($('ckEmpty'), true);
                return;
            }
            if (!ops.length) {
                // Hay operaciones pero ninguna en este filtro
                $('ckTableBody').innerHTML =
                    '<tr><td colspan="7" class="ck-empty-filter">No hay operaciones en este estado.</td></tr>';
                show($('ckTableWrap'), true);
                return;
            }
            renderTabla(ops);
            show($('ckTableWrap'), true);
        } catch (err) {
            console.error('[CDI cockpit] error:', err);
            show($('ckLoading'), false);
            var e = $('ckError');
            if (e) { e.textContent = 'No se pudieron cargar las operaciones. Probá de nuevo.'; show(e, true); }
        }
    }

    async function actualizar(opId, patch) {
        try {
            var resp = await CDI.api('/api/operations/' + encodeURIComponent(opId) + '/estado', {
                method: 'PATCH',
                body: JSON.stringify(patch)
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            CDI.toast && CDI.toast.success('Guardado', 'La operación se actualizó.');
            CDI.track && CDI.track('cockpit_estado_update', patch);
            // Recargar para refrescar contadores de los chips
            cargar();
        } catch (err) {
            console.error('[CDI cockpit] update error:', err);
            CDI.toast && CDI.toast.error('No se pudo guardar', 'Probá de nuevo en unos segundos.');
        }
    }

    function bindEvents() {
        var shell = document.querySelector('[data-screen="cockpit"]');
        if (!shell) return;

        // Filtros (chips)
        shell.addEventListener('click', function (e) {
            var chip = e.target.closest('.ck-chip');
            if (!chip) return;
            var est = chip.getAttribute('data-estado') || null;
            filtroActivo = est || null;
            cargar();
        });

        // Cambios de estado / canal
        shell.addEventListener('change', function (e) {
            var sel = e.target;
            var opId = sel.getAttribute('data-op');
            if (!opId) return;
            if (sel.classList.contains('ck-estado-select')) {
                actualizar(opId, { estado: sel.value });
            } else if (sel.classList.contains('ck-canal-select')) {
                actualizar(opId, { canal: sel.value });
            }
        });
    }

    if (CDI.registerScreen) {
        CDI.registerScreen('cockpit', {
            onEnter: function () { cargar(); },
            onLeave: function () {}
        });
    }

    document.addEventListener('DOMContentLoaded', bindEvents);
})();
