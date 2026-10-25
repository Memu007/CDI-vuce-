/* ============================================================
   CDI v2 — Estudios de la cuenta (ESTUDIO-1)
   El CUIT del despachante (CDDTAGR) se carga por estudio en «Mi perfil»,
   «Mis estudios», y se elige en la operación. Sin estudio elegido sigue el
   CUIT del perfil. Expone CDI.estudios.render(), .listo(),
   .elegido() y .renderPerfil().
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    // Lo que la persona eligió en esta operación ('' es el CUIT del perfil);
    // null mientras no eligió nada: manda la preselección. Cada operación
    // nueva tiene su propio CDI.state.uploadedAt y vuelve a empezar.
    let elegidoAhora = null;
    let elegidoPara = null;
    let renderSeq = 0;
    let perfilSeq = 0;
    let pendiente = Promise.resolve();

    function operacionActual() { return (CDI.state && CDI.state.uploadedAt) || null; }

    function $(id) { return document.getElementById(id); }

    function cuitConGuiones(cuit) {
        const c = String(cuit || '');
        return c.length === 11 ? c.slice(0, 2) + '-' + c.slice(2, 10) + '-' + c.slice(10) : c;
    }

    async function leer() {
        const res = await CDI.api('/api/estudios');
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error((data && data.detail) || 'No se pudieron leer tus estudios.');
        return { estudios: data.estudios || [], preseleccionado: data.preseleccionado || '' };
    }

    /* ---------- El selector de la operación ---------- */
    function render() {
        pendiente = dibujar();
        return pendiente;
    }

    async function dibujar() {
        const wrap = $('estudioWrap');
        const select = $('estudioSelect');
        const hint = $('estudioHint');
        if (!wrap || !select || !hint) return;
        const seq = ++renderSeq;
        const antes = select.hidden ? null : select.value;
        let datos;
        try {
            datos = await leer();
        } catch (err) {
            if (seq !== renderSeq) return;
            select.hidden = true;
            select.innerHTML = '';
            hint.textContent = (CDI.currentUser && CDI.currentUser.cuit)
                ? 'No se pudieron leer tus estudios: se usa el CUIT de tu perfil.'
                : 'No se pudieron leer tus estudios y tu perfil no tiene CUIT: sin el CUIT del despachante no se genera el TXT.';
            avisarSiCambio(wrap, antes, null);
            return;
        }
        if (seq !== renderSeq) return;   // llegó uno más nuevo

        if (elegidoPara !== operacionActual()) {   // otra operación
            elegidoAhora = null;
            elegidoPara = operacionActual();
        }
        const perfil = (CDI.currentUser && CDI.currentUser.cuit) || '';
        select.innerHTML = '';
        if (!datos.estudios.length) {
            select.hidden = true;
            elegidoAhora = null;
            hint.textContent = perfil
                ? 'Se usa el CUIT de tu perfil. Para elegir otro, cargá tus estudios en «Mi perfil», «Mis estudios».'
                : 'Cargá tu estudio en «Mi perfil», «Mis estudios»: sin el CUIT del despachante no se genera el TXT.';
            avisarSiCambio(wrap, antes, null);
            return;
        }
        const primera = document.createElement('option');
        primera.value = '';
        primera.textContent = perfil ? 'CUIT de mi perfil (' + cuitConGuiones(perfil) + ')' : 'Elegí el estudio';
        select.appendChild(primera);
        datos.estudios.forEach(e => {
            const opt = document.createElement('option');
            opt.value = e.id;
            opt.textContent = e.nombre + ' — ' + cuitConGuiones(e.cuit);
            select.appendChild(opt);
        });
        // Lo elegido en esta sesión manda mientras siga en la cuenta; si no,
        // el último usado o el único.
        const ids = datos.estudios.map(e => e.id);
        if (elegidoAhora && ids.indexOf(elegidoAhora) < 0) elegidoAhora = null;   // lo borró
        select.value = elegidoAhora !== null ? elegidoAhora
            : (ids.indexOf(datos.preseleccionado) >= 0 ? datos.preseleccionado : '');
        select.hidden = false;
        hint.textContent = 'Su CUIT va al CDDTAGR del TXT.';
        avisarSiCambio(wrap, antes, select.value);
    }

    // Si el código cambió lo que va al TXT (un alta o un borrado), los avisos
    // se vuelven a pedir: el evento va a la tarjeta, no al selector, para no
    // contar como elección de la persona.
    function avisarSiCambio(wrap, antes, despues) {
        if (antes !== despues) wrap.dispatchEvent(new Event('change'));
    }

    // Espera a que el selector termine de leer los estudios: generar antes
    // mandaría el CUIT del perfil en lugar del preseleccionado.
    function listo() { return pendiente.catch(() => null); }

    function elegido() {
        const select = $('estudioSelect');
        if (!select || select.hidden) return '';
        return select.value || '';
    }

    /* ---------- «Mis estudios» en el perfil ---------- */
    async function renderPerfil() {
        const lista = $('pfEstudiosList');
        const error = $('pfEstudiosError');
        if (!lista) return;
        const seq = ++perfilSeq;
        let datos;
        try {
            datos = await leer();
        } catch (err) {
            if (seq !== perfilSeq) return;
            lista.innerHTML = '';
            if (error) { error.textContent = String(err.message || err); error.hidden = false; }
            return;
        }
        if (seq !== perfilSeq) return;   // llegó uno más nuevo
        mostrarError('');
        lista.innerHTML = '';
        if (!datos.estudios.length) {
            const vacio = document.createElement('p');
            vacio.className = 'caption';
            vacio.textContent = 'Todavía no cargaste estudios. Sin ninguno, se usa «Mi CUIT (despachante)».';
            lista.appendChild(vacio);
        }
        datos.estudios.forEach(e => {
            const row = document.createElement('div');
            row.style.cssText = 'display:flex; align-items:center; justify-content:space-between; padding:6px 8px; border:1px solid var(--c-border,#ddd); border-radius:6px;';
            const info = document.createElement('span');
            info.style.cssText = 'font-size:13px;';
            info.textContent = e.nombre + ' · ' + cuitConGuiones(e.cuit);
            row.appendChild(info);
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-ghost btn-sm';
            btn.textContent = 'Borrar';
            btn.style.cssText = 'font-size:12px; padding:2px 8px;';
            btn.addEventListener('click', () => borrar(e, btn));
            row.appendChild(btn);
            lista.appendChild(row);
        });
    }

    function mostrarError(msg) {
        const error = $('pfEstudiosError');
        if (!error) return;
        error.textContent = msg || '';
        error.hidden = !msg;
    }

    async function alta() {
        const nombreEl = $('pfEstudioNombre');
        const cuitEl = $('pfEstudioCuit');
        const btn = $('pfEstudioAlta');
        if (!nombreEl || !cuitEl || !btn) return;
        mostrarError('');
        btn.disabled = true;
        try {
            const res = await CDI.api('/api/estudios', {
                method: 'POST',
                body: JSON.stringify({ nombre: nombreEl.value, cuit: cuitEl.value })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                const detail = data && data.detail;
                throw new Error(typeof detail === 'string' ? detail : 'No se pudo guardar el estudio.');
            }
            nombreEl.value = '';
            cuitEl.value = '';
            await renderPerfil();
            render();
        } catch (err) {
            mostrarError(String(err.message || err));
        } finally {
            btn.disabled = false;
        }
    }

    async function borrar(estudio, btn) {
        const ok = await CDI.confirm({
            title: 'Borrar estudio',
            lead: '¿Borrar «' + estudio.nombre + '»?',
            text: 'Las operaciones que vengan dejan de poder elegirlo.',
            acceptText: 'Sí, borrar',
            cancelText: 'Cancelar'
        });
        if (!ok) return;
        mostrarError('');
        btn.disabled = true;
        try {
            const res = await CDI.api('/api/estudios/' + encodeURIComponent(estudio.id), { method: 'DELETE' });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error((data && data.detail) || 'No se pudo borrar el estudio.');
            await renderPerfil();
            render();
        } catch (err) {
            mostrarError(String(err.message || err));
            btn.disabled = false;
        }
    }

    function init() {
        const select = $('estudioSelect');
        if (select) select.addEventListener('change', () => {
            elegidoAhora = select.value || '';
            elegidoPara = operacionActual();
        });
        const btn = $('pfEstudioAlta');
        if (btn) btn.addEventListener('click', alta);
        [$('pfEstudioNombre'), $('pfEstudioCuit')].forEach(el => {
            if (!el) return;
            el.addEventListener('keydown', (ev) => {
                if (ev.key === 'Enter') { ev.preventDefault(); alta(); }
            });
        });
        const block = $('pfEstudiosBlock');
        if (block) block.addEventListener('toggle', () => { if (block.open) renderPerfil(); });
    }

    CDI.estudios = { render: render, listo: listo, elegido: elegido, renderPerfil: renderPerfil };
    document.addEventListener('DOMContentLoaded', init);
})();
