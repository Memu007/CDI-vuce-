/* ============================================================
   CDI v2 — Hints contextuales "just-in-time"

   Motor chico de micro-tooltips que aparecen UNA sola vez en la
   vida del usuario, en el momento exacto que una feature se activa.
   Cada hint tiene su propia key en localStorage ('cdi_hint_<id>_v1').
   Uso:
     CDI.hint('autocatalogo', {
         target: domEl,      // opcional; si no, se ancla abajo-derecha
         title:  'Titulo corto',
         text:   'Texto 1-2 lineas',
         cta:    'Entendido',   // opcional
         ttl:    8000,          // opcional, default 8000ms
     });
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};
    const KEY_PREFIX = 'cdi_hint_';
    const KEY_SUFFIX = '_v1';
    const DEFAULT_TTL = 8000;
    const activeHints = new Map(); // id -> { el, timer }

    function getState(id) {
        try { return localStorage.getItem(KEY_PREFIX + id + KEY_SUFFIX) || ''; }
        catch (_) { return ''; }
    }
    function markShown(id) {
        try { localStorage.setItem(KEY_PREFIX + id + KEY_SUFFIX, 'shown'); } catch (_) {}
    }

    function ensureHost() {
        let host = document.getElementById('hintHost');
        if (!host) {
            host = document.createElement('div');
            host.id = 'hintHost';
            host.setAttribute('aria-live', 'polite');
            document.body.appendChild(host);
        }
        return host;
    }

    function close(id, reason) {
        const entry = activeHints.get(id);
        if (!entry) return;
        clearTimeout(entry.timer);
        const { el } = entry;
        el.classList.remove('is-visible');
        setTimeout(() => { el.remove(); }, 240);
        activeHints.delete(id);
        try {
            CDI.track && CDI.track('hint_closed', { id: id, reason: reason || 'unknown' });
        } catch (_) {}
    }

    function positionNearTarget(el, target) {
        // Fallback: fija abajo-derecha.
        if (!target || !(target instanceof Element) || target.offsetParent === null) {
            el.style.position = 'fixed';
            el.style.right = '16px';
            el.style.bottom = '16px';
            el.style.left = 'auto';
            el.style.top = 'auto';
            return;
        }
        // Lo ponemos debajo del target, centrado horizontalmente, con fallback arriba si no entra.
        const rect = target.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        el.style.position = 'fixed';
        el.style.right = 'auto';
        el.style.bottom = 'auto';
        // Primero medimos sin posicion final para saber ancho/alto.
        el.style.left = '-9999px';
        el.style.top = '-9999px';
        requestAnimationFrame(() => {
            const elRect = el.getBoundingClientRect();
            const gap = 12;
            let top = rect.bottom + gap;
            if (top + elRect.height > vh - 12) {
                top = rect.top - elRect.height - gap;
            }
            if (top < 12) {
                // Como ultimo recurso, fija abajo-derecha.
                el.style.position = 'fixed';
                el.style.right = '16px';
                el.style.bottom = '16px';
                el.style.left = 'auto';
                el.style.top = 'auto';
                return;
            }
            let left = rect.left + (rect.width / 2) - (elRect.width / 2);
            if (left < 12) left = 12;
            if (left + elRect.width > vw - 12) left = vw - elRect.width - 12;
            el.style.top = top + 'px';
            el.style.left = left + 'px';
        });
    }

    function show(id, opts) {
        if (!id) return;
        // Regla: una sola vez en la vida del usuario.
        if (getState(id) === 'shown') return;
        // Idempotencia dentro de la sesion: si ya hay uno con ese id, no duplicamos.
        if (activeHints.has(id)) return;

        opts = opts || {};
        const host = ensureHost();
        const el = document.createElement('div');
        el.className = 'tour-hint';
        el.setAttribute('role', 'status');
        el.setAttribute('data-hint-id', id);

        const safeTitle = String(opts.title || '');
        const safeText  = String(opts.text  || '');
        const ctaLabel  = String(opts.cta   || 'Entendido');

        el.innerHTML = (
            '<button type="button" class="tour-hint-close" aria-label="Cerrar">&times;</button>' +
            '<div class="tour-hint-body">' +
                '<p class="tour-hint-title"></p>' +
                '<p class="tour-hint-text"></p>' +
            '</div>' +
            '<div class="tour-hint-actions">' +
                '<button type="button" class="btn btn-primary btn-sm tour-hint-cta"></button>' +
            '</div>'
        );
        // Escapamos via textContent para evitar XSS desde nombres de cliente/proveedor.
        el.querySelector('.tour-hint-title').textContent = safeTitle;
        el.querySelector('.tour-hint-text').textContent  = safeText;
        el.querySelector('.tour-hint-cta').textContent   = ctaLabel;

        host.appendChild(el);
        positionNearTarget(el, opts.target || null);

        const timer = setTimeout(() => {
            markShown(id);
            close(id, 'timeout');
        }, Number(opts.ttl) > 0 ? Number(opts.ttl) : DEFAULT_TTL);

        activeHints.set(id, { el: el, timer: timer });

        // Listeners
        el.querySelector('.tour-hint-cta').addEventListener('click', () => {
            markShown(id);
            close(id, 'cta');
        });
        el.querySelector('.tour-hint-close').addEventListener('click', () => {
            markShown(id);
            close(id, 'x');
        });

        requestAnimationFrame(() => el.classList.add('is-visible'));

        try { CDI.track && CDI.track('hint_shown', { id: id }); } catch (_) {}
    }

    // API publica
    CDI.hint = show;
    // Para debugging: resetear todos los hints.
    CDI.resetHints = function () {
        try {
            Object.keys(localStorage).forEach(k => {
                if (k.indexOf(KEY_PREFIX) === 0 && k.indexOf(KEY_SUFFIX) === k.length - KEY_SUFFIX.length) {
                    localStorage.removeItem(k);
                }
            });
        } catch (_) {}
    };
})();
