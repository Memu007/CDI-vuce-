/* ============================================================
   CDI v2 — Bootstrap JS
   Responsabilidad: router entre pantallas, fetch con Bearer,
   telemetria comun v1/v2 para comparar funnel.
   Las pantallas reales viven en /static/v2/screens/*.js (D2-D5).
   ============================================================ */
(function () {
    'use strict';

    const CDI = window.CDI = window.CDI || {};

    /* ---------- 1. Auth & fetch ---------- */
    // La sesión va siempre por la cookie HttpOnly `access_token` que el
    // servidor setea al hacer login. No se lee ni escribe localStorage para
    // el token — evita exposición XSS. La cookie se envía automáticamente
    // en peticiones same-origin por el browser.

    // CSRF double-submit: leemos la cookie csrf_token y la mandamos como header
    function getCsrfToken() {
        const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    async function api(path, options = {}) {
        const headers = Object.assign({}, options.headers || {});
        if (options.body && !(options.body instanceof FormData) &&
            !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }
        const method = (options.method || 'GET').toUpperCase();
        if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
            // Si la sesión del navegador cambió desde la que se confirmó para
            // la pestaña, la escritura no sale hasta saber que es del mismo
            // usuario: si entró otro, saldría a su nombre. No depende de que
            // el servidor exija CSRF.
            if (getCsrfToken() !== (sesionDelDueno || sesionAlAbrir) && !(await sesionEsDelDueno())) {
                throw new Error(sesionAjena ? ERROR_AJENA : ERROR_SIN_SESION);
            }
            if (!headers['X-CSRF-Token']) {
                const csrf = getCsrfToken();
                if (csrf) headers['X-CSRF-Token'] = csrf;
            }
        }
        const res = await fetch(path, Object.assign({}, options, { headers, credentials: 'same-origin' }));
        if (res.status === 401) irAlLogin();
        if (res.status === 402) {
            // Impago, vencido, cancelado o tope del plan: el modal dice la
            // razón que manda el servidor (COBRO-CORTE-1).
            let detail = null;
            try { detail = (await res.clone().json()).detail; } catch (_) {}
            const motivo = (detail && typeof detail === 'object') ? detail : {};
            const titulos = {
                PLAN_LIMIT_EXCEEDED: 'Llegaste al tope de tu plan',
                SUBSCRIPTION_PAST_DUE: 'Tenés un pago pendiente',
                SUBSCRIPTION_INACTIVE: 'No tenés una suscripción activa',
            };
            const titulo = motivo.billing_status === 'canceled' ? 'Cancelaste tu suscripción'
                : (titulos[motivo.code] || 'Tu plan venció');
            const lead = motivo.message || (typeof detail === 'string' && detail) ||
                'Necesitás renovar tu suscripción para seguir usando CDI.';
            if (CDI.confirm) {
                CDI.confirm({
                    title: titulo,
                    lead: lead,
                    text: 'Después de pagar podés volver a usar todas las funciones.',
                    acceptText: 'Ir a pagar',
                    cancelText: 'Volver',
                    kind: 'warning',
                }).then(ok => {
                    if (ok) {
                        if (typeof CDI.openProfileModal === 'function') {
                            CDI.openProfileModal();
                        } else {
                            window.location.reload();
                        }
                    }
                });
            }
            const err = new Error('payment_required');
            err.motivo = lead;
            throw err;
        }
        return res;
    }

    function irAlLogin() {
        window.location.href = '/?next=' + encodeURIComponent(window.location.pathname + window.location.search);
        throw new Error('unauthorized');
    }

    async function logout() {
        try {
            await api('/auth/logout', { method: 'POST' });
        } catch (e) {
            // La sesión es de otro: no se cierra y la pestaña queda tapada.
            if (sesionAjena) return;
            // No salió el pedido: la sesión sigue abierta.
            if (e.message === ERROR_SIN_SESION) {
                toast('No se pudo cerrar la sesión', e.message, 'error');
                return;
            }
        }
        window.location.href = '/';
    }

    /* ---------- 2. Router de pantallas ---------- */
    // Screens del flujo principal (aparecen en la barra de progreso).
    const FLOW_SCREENS = ['upload', 'review', 'ncm', 'validating', 'ready'];
    // Screens auxiliares registradas pero fuera del flujo (clientes, etc).
    // Se consideran validas si hay handler o nodo data-screen.
    let currentScreen = null;
    let previousScreen = null;
    const handlers = {};

    function registerScreen(name, handler) {
        handlers[name] = handler || {};
    }

    function screenExists(name) {
        if (FLOW_SCREENS.includes(name)) return true;
        if (handlers[name]) return true;
        return !!document.querySelector('[data-screen="' + name + '"]');
    }

    function goTo(name, state) {
        if (!screenExists(name)) {
            console.warn('[CDI v2] screen desconocida:', name);
            return;
        }
        if (currentScreen) {
            // Evento global de cleanup: distintos modulos cierran overlays
            // locales cuando cambia la pantalla.
            try {
                document.dispatchEvent(new CustomEvent('cdi:screen-leave', {
                    detail: { from: currentScreen, to: name }
                }));
            } catch (_) {}
            if (handlers[currentScreen] && typeof handlers[currentScreen].onLeave === 'function') {
                try { handlers[currentScreen].onLeave(); } catch (err) { console.error('[CDI v2] onLeave:', err); }
            }
        }
        // Solo guardamos previousScreen para screens auxiliares (permite "volver")
        if (currentScreen && !FLOW_SCREENS.includes(name)) {
            previousScreen = currentScreen;
        }
        document.querySelectorAll('.screen').forEach(el => el.classList.remove('is-active'));
        const next = document.querySelector('[data-screen="' + name + '"]');
        if (next) next.classList.add('is-active');
        currentScreen = name;
        updateProgress(name);
        if (handlers[name] && typeof handlers[name].onEnter === 'function') {
            try { handlers[name].onEnter(state || {}); } catch (err) { console.error('[CDI v2] onEnter:', err); }
        }
        // Evento global para que modulos externos (ej. tour de bienvenida)
        // sepan a que pantalla acaba de llegar el usuario y reaccionen sin
        // hacer polling.
        try {
            document.dispatchEvent(new CustomEvent('cdi:screen-enter', {
                detail: { screen: name, state: state || {} }
            }));
        } catch (_) {}
        track('screen_shown', { screen: name });
    }

    function goBack() {
        // Si estamos en una screen auxiliar y hay una previa, volvemos.
        // Caso contrario, caemos a upload como fallback seguro.
        if (previousScreen && FLOW_SCREENS.includes(previousScreen)) {
            const back = previousScreen;
            previousScreen = null;
            goTo(back);
            return;
        }
        goTo('upload');
    }

    function updateProgress(activeName) {
        // Screens auxiliares: ocultar/desactivar la barra de progreso.
        const progressNav = document.querySelector('nav.progress');
        const isFlow = FLOW_SCREENS.includes(activeName);
        if (progressNav) {
            progressNav.classList.toggle('is-hidden-flow', !isFlow);
        }
        if (!isFlow) {
            document.querySelectorAll('.progress-step[data-step]').forEach(step => {
                step.classList.remove('is-active', 'is-done');
            });
            return;
        }
        const idx = FLOW_SCREENS.indexOf(activeName);
        document.querySelectorAll('.progress-step[data-step]').forEach(step => {
            const stepIdx = FLOW_SCREENS.indexOf(step.getAttribute('data-step'));
            step.classList.remove('is-active', 'is-done');
            if (stepIdx < idx) step.classList.add('is-done');
            else if (stepIdx === idx) step.classList.add('is-active');
        });
    }

    /* ---------- 3. Telemetria comun v1/v2 ---------- */
    const TELEMETRY_ENDPOINT = '/api/session/state';
    const sessionStartMs = Date.now();
    let telemetryMuted = false;

    function track(action, extra) {
        // Sale con fetch directo, sin el freno de api(): con la sesión
        // cambiada se pierde el evento antes que mandarlo a nombre de otro.
        if (telemetryMuted || getCsrfToken() !== (sesionDelDueno || sesionAlAbrir)) return;
        const payload = Object.assign({
            version: 'v2',
            screen: currentScreen || 'boot',
            action: action,
            duration_ms: Date.now() - sessionStartMs,
            ts: new Date().toISOString()
        }, extra || {});
        const body = JSON.stringify(payload);
        try {
            fetch(TELEMETRY_ENDPOINT, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
                body: body,
                keepalive: true
            }).catch(() => { telemetryMuted = true; });
        } catch (_) {
            telemetryMuted = true;
        }
        if (window.__CDI_DEBUG__) console.log('[telemetry]', payload);
    }

    /* ---------- 4. Toast ---------- */
    let toastTimer = null;
    function toast(title, text, kind) {
        const host = document.getElementById('toastHost');
        if (!host) return;
        host.innerHTML = '';
        const el = document.createElement('div');
        el.className = 'toast' + (kind ? ' is-' + kind : '');
        el.innerHTML = [
            '<div class="toast-icon">',
            (kind === 'error' || kind === 'warning') ? '!' : (kind === 'success' ? '✓' : 'i'),
            '</div>',
            '<div class="toast-body">',
            '<p class="toast-title"></p>',
            '<p class="toast-text"></p>',
            '</div>'
        ].join('');
        el.querySelector('.toast-title').textContent = title || '';
        el.querySelector('.toast-text').textContent = text || '';
        host.appendChild(el);
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => { host.innerHTML = ''; }, 4000);
    }

    let confirmRefs = null;
    let confirmResolve = null;
    function getConfirmRefs() {
        if (confirmRefs) return confirmRefs;
        const modal = document.getElementById('cdiConfirmModal');
        if (!modal) return null;
        confirmRefs = {
            modal: modal,
            title: document.getElementById('cdiConfirmTitle'),
            close: document.getElementById('cdiConfirmClose'),
            icon: document.getElementById('cdiConfirmIcon'),
            lead: document.getElementById('cdiConfirmLead'),
            text: document.getElementById('cdiConfirmText'),
            cancel: document.getElementById('cdiConfirmCancel'),
            accept: document.getElementById('cdiConfirmAccept'),
        };
        const closeAsCancel = () => closeConfirm(false);
        if (confirmRefs.close) confirmRefs.close.addEventListener('click', closeAsCancel);
        if (confirmRefs.cancel) confirmRefs.cancel.addEventListener('click', closeAsCancel);
        if (confirmRefs.accept) confirmRefs.accept.addEventListener('click', () => closeConfirm(true));
        modal.addEventListener('click', (ev) => {
            if (ev.target === modal) closeConfirm(false);
        });
        modal.addEventListener('cancel', (ev) => {
            ev.preventDefault();
            closeConfirm(false);
        });
        document.addEventListener('keydown', (ev) => {
            if (ev.key !== 'Escape') return;
            if (!modal.open) return;
            ev.preventDefault();
            ev.stopPropagation();
            closeConfirm(false);
        }, true);
        return confirmRefs;
    }

    function closeConfirm(ok) {
        const refs = confirmRefs;
        if (refs && refs.modal) {
            if (typeof refs.modal.close === 'function' && refs.modal.open) {
                try { refs.modal.close(); } catch (_) { refs.modal.removeAttribute('open'); }
            } else {
                refs.modal.removeAttribute('open');
            }
        }
        const resolve = confirmResolve;
        confirmResolve = null;
        if (resolve) resolve(!!ok);
    }

    function confirmDialog(options) {
        const refs = getConfirmRefs();
        if (!refs) {
            toast('No se pudo abrir la confirmación', 'Probá de nuevo en unos segundos.', 'error');
            return Promise.resolve(false);
        }
        if (confirmResolve) closeConfirm(false);
        const cfg = Object.assign({
            title: 'Confirmar acción',
            lead: '¿Querés continuar?',
            text: 'Confirmá para seguir.',
            acceptText: 'Aceptar',
            cancelText: 'Cancelar',
            kind: 'info',
        }, options || {});
        if (refs.title) refs.title.textContent = cfg.title || '';
        if (refs.lead) refs.lead.textContent = cfg.lead || '';
        if (refs.text) refs.text.textContent = cfg.text || '';
        if (refs.cancel) refs.cancel.textContent = cfg.cancelText || 'Cancelar';
        if (refs.accept) {
            refs.accept.textContent = cfg.acceptText || 'Aceptar';
            refs.accept.className = 'btn ' + (cfg.kind === 'danger' ? 'btn-danger' : 'btn-primary');
        }
        if (refs.icon) {
            refs.icon.className = 'cdi-confirm-icon';
            if (cfg.kind === 'warning') refs.icon.classList.add('is-warning');
            if (cfg.kind !== 'danger' && cfg.kind !== 'warning') refs.icon.classList.add('is-info');
            refs.icon.textContent = cfg.kind === 'danger' ? '!' : (cfg.kind === 'warning' ? '!' : 'i');
        }
        return new Promise(resolve => {
            confirmResolve = resolve;
            if (typeof refs.modal.showModal === 'function') {
                try { refs.modal.showModal(); } catch (_) { refs.modal.setAttribute('open', ''); }
            } else {
                refs.modal.setAttribute('open', '');
            }
            setTimeout(() => refs.cancel && refs.cancel.focus(), 80);
        });
    }

    /* ---------- 5. Toggle a v1 ---------- */
    function goToLegacy() {
        document.cookie = 'cdi_ui=; Path=/; Max-Age=0; SameSite=Lax';
        track('toggle_to_v1');
        setTimeout(() => { window.location.href = '/dashboard'; }, 100);
    }

    /* ---------- 6. Usuario actual (avatar + saludo) ---------- */
    let currentUser = null;
    // La pestaña es del primer usuario que conoce, y sólo si la sesión no
    // cambió desde que abrió: si otro entra en el mismo navegador mientras
    // ésta reintenta, o la consulta trae después otro usuario, lo cargado no
    // es de él y la pestaña deja de guardar y de recuperar.
    // La sesión se reconoce por la cookie CSRF, que cambia en cada login:
    // sesionDelDueno es la que tenía cuando se confirmó al dueño. Si cambia,
    // la pestaña no guarda hasta volver a preguntar quién es (revisarSesion).
    const sesionAlAbrir = getCsrfToken();
    let duenoPestana = null, sesionAjena = false, sinSesion = false, sesionDelDueno = null;
    const ERROR_AJENA = 'Entró otro usuario en este navegador. Recargá la página.';
    const ERROR_SIN_SESION = 'No se pudo comprobar la sesión. Recargá la página.';

    // La pestaña deja de escribir para siempre y lo tapa todo: lo que tiene
    // cargado es del dueño y la sesión es de otro. Sólo se sale recargando.
    function marcarAjena() {
        if (sesionAjena) return;
        sesionAjena = true;
        avisarBorrador('ajena', AVISO_AJENA);
        const dialogo = document.getElementById('pestanaAjena');
        if (!dialogo || dialogo.open) return;
        dialogo.addEventListener('cancel', e => e.preventDefault());
        document.getElementById('pestanaAjenaRecargar').addEventListener('click', () => window.location.reload());
        try { dialogo.showModal(); } catch (_) { dialogo.setAttribute('open', ''); }
    }
    // Devuelve si ya se sabe quién es el usuario (sin él no hay autoguardado).
    async function loadCurrentUser() {
        try {
            const sesionAntes = getCsrfToken();
            // Una consulta que no contesta cuenta como error y se reintenta.
            const corte = new AbortController();
            const tope = setTimeout(() => corte.abort(), ESPERA_SESION_MS);
            let user;
            try {
                const res = await api('/auth/current_user', { signal: corte.signal });
                if (!res.ok) return;
                user = await res.json();
            } finally {
                clearTimeout(tope);
            }
            if (duenoPestana === null) {
                duenoPestana = user.username || '';
                if (sesionAntes !== sesionAlAbrir || getCsrfToken() !== sesionAlAbrir) marcarAjena();
            }
            if (!confirmarSesion(user.username, sesionAntes)) return !!currentUser;
            currentUser = user;
            CDI.currentUser = user;
            // Banner de billing (trial / past_due / activar plan).
            renderBillingBanner(user);
            // Cachear defaults de operacion del despachante (los usa Revisar como fallback)
            CDI.userDefaults = {
                aduana_codigo: user.default_aduana_codigo || '',
                puerto_destino: user.default_puerto_destino || '',
                tipo_destinacion: user.default_tipo_destinacion || ''
            };
            const avatar = document.getElementById('userAvatar');
            const name = document.getElementById('userName');
            const initialsEl = document.getElementById('userAvatarInitials');
            const initials = ((user.name || user.username || '?')
                .split(/\s+/).map(s => s[0]).slice(0, 2).join('') || '?').toUpperCase();
            if (initialsEl) initialsEl.textContent = initials;
            else if (avatar) avatar.textContent = initials;
            if (name) name.textContent = user.name || user.username || '';
        } catch (err) {
            if (err && err.message === 'unauthorized') sinSesion = true;
            console.warn('[CDI v2] no se pudo cargar usuario:', err);
        }
        return !!currentUser;
    }

    // Un 500 o un corte al abrir no deja la pestaña sin dueño para siempre:
    // reintenta de 1 a 30 segundos; un 401 o una pestaña ajena cortan, porque
    // ya mandan al login o a recargar.
    async function cargarUsuarioHastaTenerlo() {
        for (let espera = 1000; !(await loadCurrentUser()) && !sinSesion && !sesionAjena; espera = Math.min(espera * 2, 30000)) {
            await new Promise(r => setTimeout(r, espera));
        }
    }

    /* ---------- 6b. Cliente de la operación actual ---------- */
    const CLIENTE_KEY = 'cdi_cliente_activo';

    function normalizeCuit(raw) {
        let value = String(raw || '').trim().toUpperCase();
        if (value.indexOf('AR') === 0) value = value.slice(2);
        return value.replace(/\D/g, '');
    }

    function formatCuit(raw) {
        const d = normalizeCuit(raw);
        if (d.length !== 11) return raw || '';
        return d.slice(0, 2) + '-' + d.slice(2, 10) + '-' + d.slice(10);
    }

    function getClienteActivo() {
        if (CDI.state && CDI.state.clienteActivo) return CDI.state.clienteActivo;
        return null;
    }

    function setClienteActivo(cliente) {
        CDI.state = CDI.state || {};
        CDI.state.clienteActivo = cliente || null;
        try {
            localStorage.removeItem(CLIENTE_KEY);
        } catch (_) {}
        updateClientePill();
        try {
            document.dispatchEvent(new CustomEvent('cdi:cliente-activo-cambio', { detail: cliente }));
        } catch (_) {}
    }

    function matchClienteByCuit(cuitRaw, lista) {
        const needle = normalizeCuit(cuitRaw);
        if (!needle || !Array.isArray(lista)) return null;
        for (const c of lista) {
            if (normalizeCuit(c.cuit) === needle) return c;
        }
        return null;
    }

    // Carga clientes una sola vez si la cache aun no fue poblada por la pantalla
    // de clientes. Lo necesitamos para auto-detectar importador en upload/review
    // sin obligar al user a abrir el drawer.
    let _clientesCachePromise = null;
    function ensureClientesCache() {
        if (Array.isArray(CDI.clientesCache) && CDI.clientesCache.length >= 0 && CDI.clientesCache.__loaded) {
            return Promise.resolve(CDI.clientesCache);
        }
        if (_clientesCachePromise) return _clientesCachePromise;
        _clientesCachePromise = (async () => {
            try {
                const res = await api('/api/clientes');
                const data = await res.json();
                if (!res.ok || !data.success) return [];
                const list = Array.isArray(data.clientes) ? data.clientes : [];
                list.__loaded = true;
                CDI.clientesCache = list;
                return list;
            } catch (_) {
                return [];
            } finally {
                _clientesCachePromise = null;
            }
        })();
        return _clientesCachePromise;
    }

    function updateClientePill() {
        const pill = document.getElementById('clientePill');
        if (!pill) return;
        const activo = getClienteActivo();
        if (activo && activo.nombre) {
            pill.classList.add('is-active');
            pill.classList.remove('is-empty');
            pill.title = activo.cuit ? 'Cliente de esta operación: ' + activo.nombre + ' · ' + formatCuit(activo.cuit) : activo.nombre;
            pill.innerHTML =
                '<span class="dot-status is-success"></span>' +
                '<span class="cliente-pill-label">Cliente operación:</span> ' +
                '<span class="cliente-pill-name"></span>';
            pill.querySelector('.cliente-pill-name').textContent = activo.nombre;
        } else {
            pill.classList.add('is-empty');
            pill.classList.remove('is-active');
            pill.title = 'Sin cliente para esta operación';
            pill.innerHTML =
                '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>' +
                '<span class="cliente-pill-label">Cliente</span>';
        }
    }

    /* ---------- 7. Error handler global ---------- */
    window.addEventListener('error', (ev) => {
        track('session_error', { message: String(ev.message || ev.error), source: ev.filename });
    });
    window.addEventListener('unhandledrejection', (ev) => {
        track('session_error', { message: String(ev.reason), kind: 'unhandled_rejection' });
    });

    /* ---------- 8. Public API ---------- */
    CDI.api = api;
    CDI.irAlCheckout = irAlCheckout;
    CDI.logout = logout;
    CDI.goTo = goTo;
    CDI.goBack = goBack;
    CDI.goToLegacy = goToLegacy;
    CDI.track = track;
    CDI.confirm = confirmDialog;
    // Exponemos toast como funcion y tambien con .success/.error/.info
    // porque distintos modulos (clientes.js) usan ambas formas.
    toast.success = (title, text) => toast(title, text, 'success');
    toast.error = (title, text) => toast(title, text, 'error');
    toast.info = (title, text) => toast(title, text, 'info');
    CDI.toast = toast;
    CDI.registerScreen = registerScreen;
    CDI.getClienteActivo = getClienteActivo;
    CDI.setClienteActivo = setClienteActivo;
    CDI.matchClienteByCuit = matchClienteByCuit;
    CDI.ensureClientesCache = ensureClientesCache;
    CDI.normalizeCuit = normalizeCuit;
    CDI.formatCuit = formatCuit;
    CDI.updateClientePill = updateClientePill;

    /* ---------- 9. Helpers expuestos ---------- */
    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }
    CDI.escapeHtml = escapeHtml;

    // Mascara de fecha DD/MM/AAAA: inserta los '/' solos mientras tipeas,
    // respeta backspace y acepta pegar strings como "19/04/2026" o "19042026".
    function maskDate(input) {
        if (!input || input.__cdiMaskDateApplied) return;
        input.__cdiMaskDateApplied = true;
        input.setAttribute('inputmode', 'numeric');
        input.setAttribute('maxlength', '10');

        function format(raw) {
            const d = String(raw || '').replace(/\D/g, '').slice(0, 8);
            if (d.length <= 2) return d;
            if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
            return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
        }

        function applyFormat() {
            const prev = input.value;
            const caret = input.selectionStart == null ? prev.length : input.selectionStart;
            // Digitos antes del cursor (para re-posicionar el caret despues)
            const digitsBefore = prev.slice(0, caret).replace(/\D/g, '').length;
            const next = format(prev);
            if (next === prev) return;
            input.value = next;
            // Re-ubicar el cursor al mismo "conteo de digitos" que tenia antes
            let digits = 0;
            let pos = next.length;
            for (let i = 0; i < next.length; i++) {
                if (/\d/.test(next[i])) {
                    digits++;
                    if (digits === digitsBefore) { pos = i + 1; break; }
                }
            }
            try { input.setSelectionRange(pos, pos); } catch (_) {}
        }

        input.addEventListener('input', applyFormat);
        input.addEventListener('paste', () => setTimeout(applyFormat, 0));
        input.addEventListener('blur', () => {
            const val = input.value;
            if (/^\d{2}\/\d{2}\/\d{2}$/.test(val)) {
                const parts = val.split('/');
                const y = parseInt(parts[2], 10);
                parts[2] = (y > 50 ? '19' : '20') + (y < 10 ? '0' + y : y);
                input.value = parts.join('/');
                // Trigger change to validate
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
        // Normalizar value inicial si venia prefilleado
        if (input.value) applyFormat();
    }
    CDI.maskDate = maskDate;

    // Formato de NCM/posición SIM. La pantalla de declaración valida por
    // separado que existan 11 dígitos y la letra de control (DC).
    function formatNcm(raw) {
        const s = String(raw == null ? '' : raw).trim();
        // Extraer letra sufijo (A-Z, mayuscula)
        const letterMatch = s.match(/[A-Za-z]$/);
        const letter = letterMatch ? letterMatch[0].toUpperCase() : '';
        const d = s.replace(/[^0-9]/g, '').slice(0, 11);
        let base;
        if (d.length <= 4) base = d;
        else if (d.length <= 6) base = d.slice(0, 4) + '.' + d.slice(4);
        else if (d.length <= 8) base = d.slice(0, 4) + '.' + d.slice(4, 6) + '.' + d.slice(6);
        else base = d.slice(0, 4) + '.' + d.slice(4, 6) + '.' + d.slice(6, 8) + '.' + d.slice(8);
        return base + (letter ? ' ' + letter : '');
    }
    CDI.formatNcm = formatNcm;

    // Máscara: inserta los puntos mientras se tipea y permite pegar tanto una
    // NCM de búsqueda como una posición SIM completa con DC.
    function maskNcm(input) {
        if (!input || input.__cdiMaskNcmApplied) return;
        input.__cdiMaskNcmApplied = true;
        input.setAttribute('inputmode', 'text');
        input.setAttribute('maxlength', '17');

        function applyFormat() {
            const prev = input.value;
            const caret = input.selectionStart == null ? prev.length : input.selectionStart;
            const digitsBefore = prev.slice(0, caret).replace(/\D/g, '').length;
            const next = formatNcm(prev);
            if (next === prev) return;
            input.value = next;
            let digits = 0;
            let pos = next.length;
            for (let i = 0; i < next.length; i++) {
                if (/\d/.test(next[i])) {
                    digits++;
                    if (digits === digitsBefore) { pos = i + 1; break; }
                }
            }
            try { input.setSelectionRange(pos, pos); } catch (_) {}
        }

        input.addEventListener('input', applyFormat);
        input.addEventListener('paste', () => setTimeout(applyFormat, 0));
        if (input.value) applyFormat();
    }
    CDI.maskNcm = maskNcm;

    /* ---------- Banner "Datos de muestra" ---------- */
    // Se muestra cuando al menos un NCM de la operacion activa devolvio
    // `source=fake` desde /api/ncm/{ncm}/completo. Escucha el evento
    // `cdi:ncm-source` emitido por `screens/ncm.js`.
    function setupFakeSourceBanner() {
        const banner = document.getElementById('fakeSourceBanner');
        const closeBtn = document.getElementById('fakeSourceBannerClose');
        if (!banner) return;
        const fakeNcms = new Set();
        let dismissed = false;
        document.addEventListener('cdi:ncm-source', (e) => {
            const det = e && e.detail ? e.detail : {};
            const src = String(det.source || '').toLowerCase();
            const ncm = det.ncm || '';
            if (!ncm) return;
            if (src === 'fake' || src.indexOf('fake') >= 0) {
                fakeNcms.add(ncm);
            } else {
                fakeNcms.delete(ncm);
            }
            if (!dismissed) banner.hidden = fakeNcms.size === 0;
        });
        // Limpiar cuando se arranca una operacion nueva
        document.addEventListener('cdi:nueva-operacion', () => {
            fakeNcms.clear();
            dismissed = false;
            banner.hidden = true;
        });
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                dismissed = true;
                banner.hidden = true;
                track('fake_banner_dismissed');
            });
        }
    }

    /* Pide el checkout del plan y lleva el navegador a Mercado Pago. El botón
       queda deshabilitado mientras pide y mientras el navegador se va: otro
       clic pediría un segundo checkout, que cancela la suscripción adonde va
       (COBRO-MP-1, D). Sólo vuelve a su estado si el checkout falla; entonces
       devuelve false. Si vuelve con «Atrás» y el navegador restaura la página
       de su caché, se recarga: el botón y el estado de cobro quedaron viejos.
       Lo mismo vale entre botones: el aviso de arriba y el perfil pueden estar
       a la vista a la vez, y mientras uno pide el checkout el otro no hace
       nada. */
    let checkoutEnCurso = false;
    async function irAlCheckout(plan, boton) {
        if (checkoutEnCurso) return false;
        checkoutEnCurso = true;
        const textoBoton = boton.textContent;
        boton.disabled = true;
        boton.textContent = 'Abriendo…';
        let motivo = 'No se pudo iniciar el cobro.';
        try {
            const res = await api('/api/billing/checkout', {
                method: 'POST',
                body: JSON.stringify({ plan })
            });
            const data = (await res.json().catch(() => null)) || {};
            if (res.ok && data.init_point) {
                window.addEventListener('pageshow', (ev) => {
                    if (ev.persisted) window.location.reload();
                }, { once: true });
                window.location.href = data.init_point;
                return true;
            }
            if (typeof data.detail === 'string' && data.detail) motivo = data.detail;
        } catch (err) {
            console.warn('[billing] checkout error', err);
        }
        if (CDI.toast) CDI.toast('Error', motivo, 'error');
        boton.disabled = false;
        boton.textContent = textoBoton;
        checkoutEnCurso = false;
        return false;
    }

    /* ---------- Billing banner (trial / past_due / activar plan) ----------
       Renderiza un banner soft con días de trial restantes, o uno urgente si
       el trial ya venció. Click en CTA → POST /api/billing/checkout → redirige
       al init_point de MercadoPago (o demo si no hay credenciales).
       Se llama desde loadCurrentUser una vez que tenemos billing_status. */
    function renderBillingBanner(user) {
        const banner = document.getElementById('billingBanner');
        const text = document.getElementById('billingBannerText');
        const cta = document.getElementById('billingBannerCta');
        const close = document.getElementById('billingBannerClose');
        if (!banner || !text || !cta) return;

        const status = (user && user.billing_status) || 'none';
        const trialEnd = user && user.trial_ends_at ? new Date(user.trial_ends_at) : null;
        const now = new Date();
        const daysLeft = trialEnd ? Math.ceil((trialEnd - now) / (1000 * 60 * 60 * 24)) : 0;

        // Estados visibles para el user:
        //  - trial activo → banner soft con días restantes.
        //  - past_due (trial venció) → banner urgente.
        //  - active / canceled / none → ocultar.
        if (status === 'trial' && daysLeft > 0) {
            banner.classList.remove('is-urgent');
            text.innerHTML = '<strong>' + daysLeft + ' día' + (daysLeft === 1 ? '' : 's') + '</strong> de prueba gratis. Activá el plan cuando quieras.';
            cta.textContent = 'Activar plan';
            close.hidden = false;
            banner.hidden = false;
        } else if (status === 'past_due') {
            banner.classList.add('is-urgent');
            text.innerHTML = '<strong>Tu prueba gratis terminó.</strong> Activá el plan para seguir generando TXT.';
            cta.textContent = 'Activar plan ahora';
            close.hidden = true;
            banner.hidden = false;
        } else {
            banner.hidden = true;
            return;
        }

        // Click en CTA → abrir checkout MP en la misma ventana.
        if (!cta._wired) {
            cta._wired = true;
            cta.addEventListener('click', () => {
                track('billing_cta_clicked', { status: status });
                irAlCheckout((user && user.plan) || 'premium', cta);
            });
        }
        if (close && !close._wired) {
            close._wired = true;
            close.addEventListener('click', () => {
                banner.hidden = true;
                track('billing_banner_dismissed', { status: status });
            });
        }
        track('billing_banner_shown', { status: status, days_left: daysLeft });
    }

    /* ---------- 9b. Vuelta del checkout MP (?billing=success|failure|pending) ---------- */
    function handleBillingReturn() {
        const params = new URLSearchParams(window.location.search);
        const status = params.get('billing');
        if (!status) return;
        // Limpiar la URL para que un refresh no repita el toast
        params.delete('billing');
        const clean = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
        try { window.history.replaceState({}, '', clean); } catch (_) {}
        if (status === 'success' || status === 'success_preapproval') {
            toast.success('¡Pago recibido!', 'Tu plan se activa en unos segundos.');
            track('billing_return_success');
            setTimeout(loadCurrentUser, 4000);
        } else if (status === 'topup_success') {
            toast.success('Top-up acreditado', 'Ya tenés 10 operaciones adicionales.');
            track('billing_return_topup_success');
            setTimeout(loadCurrentUser, 2000);
        } else if (status === 'pending') {
            toast.info('Pago pendiente', 'Te avisamos cuando se acredite. Podés seguir usando la app.');
            track('billing_return_pending');
        } else {
            toast.error('El pago no se completó', 'Podés reintentar desde el banner o tu perfil.');
            track('billing_return_failure');
        }
    }

    /* ---------- 10. Bootstrap ---------- */
    // Si la persona ya tocó la pestaña (un clic, una tecla, soltar un
    // archivo), la recuperación tardía no la cambia: puede tener abierto el
    // diálogo de archivos o haber elegido algo. 'click' cubre la activación
    // sin puntero (tecnología asistiva o programática).
    let pestanaTocada = false;
    ['pointerdown', 'click', 'keydown', 'drop'].forEach(ev =>
        document.addEventListener(ev, () => { pestanaTocada = true; }, true));
    const recuperada = parsed => {
        CDI.state = parsed;
        if (parsed.clienteActivo) setClienteActivo(parsed.clienteActivo);
        if (CDI.toast) CDI.toast.info('Recuperado', 'Se recuperó la operación en curso.');
    };
    // La recuperación que llega cuando la pestaña ya pudo empezar otra cosa
    // (otra pantalla, otra operación o una subida en curso): eso no se pisa y
    // la de antes queda guardada.
    function adoptarTarde(b) {
        const ocupada = pestanaTocada || currentScreen !== 'upload'
            || (CDI.state && CDI.state.items && CDI.state.items.length > 0)
            || (CDI.subidaEnCurso && CDI.subidaEnCurso());
        if (ocupada) {
            avisarBorrador('pendiente', 'Quedó guardada la operación que tenías antes de recargar. Para seguirla, abrí el sistema en otra pestaña.');
            return;
        }
        const parsed = adoptarBorrador(b);
        if (!parsed) return;
        recuperada(parsed);
        goTo('review');
    }
    document.addEventListener('DOMContentLoaded', () => {
        try { localStorage.removeItem(CLIENTE_KEY); } catch (_) {}
        const usuarioListo = cargarUsuarioHastaTenerlo();
        handleBillingReturn();
        updateClientePill();
        setupFakeSourceBanner();
        track('session_start');

        // El link "Volver a la version clasica" esta en el footer como
        // #goLegacyBtn2 con onclick inline a CDI.goToLegacy() (ver
        // dashboard_v2.html). No necesitamos listener aca.

        // Click en la pill de cliente -> abre el drawer
        document.addEventListener('click', (e) => {
            const pill = e.target.closest('#clientePill');
            if (!pill) return;
            e.preventDefault();
            if (CDI.openClientesDrawer) CDI.openClientesDrawer();
        });

        // Click en el avatar -> abre el modal de perfil
        document.addEventListener('click', (e) => {
            const av = e.target.closest('#userAvatar');
            if (!av) return;
            e.preventDefault();
            if (CDI.openProfileModal) CDI.openProfileModal();
        });

        document.body.addEventListener('click', (e) => {
            const target = e.target.closest('[data-action]');
            if (!target) return;
            const action = target.getAttribute('data-action');
            if (action === 'go-upload' || action === 'back-to-upload') {
                e.preventDefault();
                CDI.state = {};
                setClienteActivo(null);
                document.dispatchEvent(new CustomEvent('cdi:nueva-operacion'));
                goTo('upload');
            } else if (action === 'go-clientes') {
                e.preventDefault();
                if (typeof CDI.openClientesDrawer === 'function') {
                    CDI.openClientesDrawer();
                }
            } else if (action === 'go-cockpit') {
                e.preventDefault();
                goTo('cockpit');
            }
        });

        // Persistence: Load from localStorage. El borrador es de un usuario:
        // se recupera después de saber quién entró (con tope, para no dejar la
        // pantalla en blanco si la red no contesta). Si el usuario llega
        // después del tope, se recupera entonces (adoptarTarde).
        const espera = new Promise(r => setTimeout(r, ESPERA_USUARIO_MS));
        Promise.race([usuarioListo, espera])
            .then(() => {
                if (!CDI.borrador.usuario()) {
                    // Sin usuario no se guarda: se avisa hasta que llegue.
                    if (!sinSesion) CDI.borrador.avisar('red', AVISO_RED);
                    usuarioListo.then(() => CDI.borrador.buscar()).then(b => b && adoptarTarde(b))
                        .catch(e => console.warn('[app_v2] failed to restore state', e));
                    return null;
                }
                return recuperarBorrador();
            })
            .catch(e => { console.warn('[app_v2] failed to restore state', e); return null; })
            .then(parsed => {
                if (parsed) recuperada(parsed);
                // Si ya había items (por ej. carga asíncrona de PDF, o restaurado recién)
                // nos vamos a review. Sino, arrancamos en upload.
                if (CDI.state && CDI.state.items && CDI.state.items.length > 0) {
                    goTo('review');
                } else {
                    goTo('upload');
                }
            });
    });

    /* ---------- 11. Persistence Auto-Save & BeforeUnload ---------- */
    // Cada pestaña guarda su operación en su propia clave (ORDEN-1): con una
    // sola clave, dos pestañas abiertas se pisaban y la que quedaba en la carga
    // de archivos borraba la operación de la otra.
    //   cdi_v2_state:<pestaña> = { v: 1, user, savedAt, closed, state }
    // La pestaña estrena un id en cada carga y adopta el borrador del id
    // anterior (recargar); si no lo tiene, el más reciente que nadie usa: el de
    // una pestaña cerrada o uno que no se guarda hace rato. Adoptar copia y
    // después borra, así que dos pestañas que adoptan el mismo a la vez lo
    // duplican, no lo pierden.
    // Sólo se recupera un borrador del usuario que entró y de menos de 7 días;
    // el más viejo, y el que no tiene dueño (la clave de antes, sin pestaña),
    // se borran al barrer.
    // Una pestaña duplicada trae el id de la original en sessionStorage: cada
    // pestaña retiene un Web Lock con su id mientras vive, y el borrador del id
    // anterior se adopta sólo si ese lock se libera (recargar, o restaurar una
    // pestaña que se cerró sin pagehide). Sin Web Locks, se adopta como antes.
    const BORRADOR = 'cdi_v2_state';
    const BORRADOR_PESTANA = 'cdi_v2_tab';
    const BORRADOR_HUERFANO_MS = 3 * 60 * 1000;
    const BORRADOR_VENCE_MS = 7 * 24 * 60 * 60 * 1000;
    const ESPERA_USUARIO_MS = 4000;
    const ESPERA_PESTANA_MS = 1500;
    const ESPERA_SESION_MS = 10000;
    const AVISO_RED = 'No se pudo comprobar la sesión: esta pestaña no guarda la operación por ahora.';
    const AVISO_AJENA = 'Entró otro usuario en este navegador: esta pestaña ya no guarda la operación. Recargá la página.';
    const pestanaAnterior = (() => {
        try { return sessionStorage.getItem(BORRADOR_PESTANA); } catch (_) { return null; }
    })();
    const pestana = (() => {
        try { if (window.crypto && crypto.randomUUID) return crypto.randomUUID(); } catch (_) {}
        return Date.now().toString(36) + Math.random().toString(36).slice(2);
    })();
    const claveBorrador = BORRADOR + ':' + pestana;
    try { sessionStorage.setItem(BORRADOR_PESTANA, pestana); } catch (_) {}
    const hayLocks = (() => {
        try { return !!(navigator.locks && navigator.locks.request); } catch (_) { return false; }
    })();
    if (hayLocks) {
        try { navigator.locks.request(BORRADOR_PESTANA + ':' + pestana, () => new Promise(() => {})).catch(() => {}); } catch (_) {}
    }

    // ¿Sigue viva la pestaña que usó ese id? Si su lock no se libera a tiempo,
    // sí: esta es una copia de ella.
    function pestanaViva(id) {
        if (!hayLocks) return Promise.resolve(false);
        const corte = new AbortController();
        const reloj = setTimeout(() => corte.abort(), ESPERA_PESTANA_MS);
        return navigator.locks.request(BORRADOR_PESTANA + ':' + id, { signal: corte.signal }, () => false)
            .catch(() => true)
            .finally(() => clearTimeout(reloj));
    }

    // El dueño, si la sesión de ahora es la que se confirmó con él. Si la
    // sesión cambió, null hasta que revisarSesion diga quién es.
    function usuarioActual() {
        if (sesionAjena || !duenoPestana || !CDI.currentUser) return null;
        if (getCsrfToken() !== sesionDelDueno) {
            revisarSesion();
            return null;
        }
        return duenoPestana;
    }

    // Lo que contestó /auth/current_user con la sesión `sesion` (la cookie
    // antes del pedido; si cambió mientras tanto, no se sabe de quién es).
    function confirmarSesion(username, sesion) {
        if (sesionAjena || getCsrfToken() !== sesion) return false;
        if (username !== duenoPestana) {
            marcarAjena();
            return false;
        }
        sesionDelDueno = sesion;
        if (['sinsesion', 'red', 'comprobando'].includes(avisoBorrador)) avisarBorrador(null);
        if (recuperarAlConfirmar) {
            recuperarAlConfirmar = false;
            buscarBorrador().then(b => b && adoptarTarde(b))
                .catch(e => console.warn('[app_v2] failed to restore state', e));
        }
        return true;
    }

    // Con fetch directo: con un 401 api() manda al login y la pestaña
    // perdería lo cargado. Si no contesta en ESPERA_SESION_MS, es un error.
    function consultarUsuario() {
        const corte = new AbortController();
        const tope = setTimeout(() => corte.abort(), ESPERA_SESION_MS);
        return fetch('/auth/current_user', { credentials: 'same-origin', signal: corte.signal })
            .then(async res => ({ status: res.status, user: res.ok ? await res.json() : null }))
            .finally(() => clearTimeout(tope));
    }

    // Antes de una escritura, con la sesión cambiada.
    async function sesionEsDelDueno() {
        const sesion = getCsrfToken();
        const { status, user } = await consultarUsuario().catch(() => ({}));
        if (status === 401) irAlLogin();
        return !!(user && duenoPestana !== null && confirmarSesion(user.username, sesion));
    }

    // Una consulta por cada cambio de sesión.
    let revisando = false, sesionRevisada = null, revisarDesde = 0;
    function revisarSesion() {
        const sesion = getCsrfToken();
        if (revisando || sesionAjena || sesion === sesionRevisada || Date.now() < revisarDesde) return;
        revisando = true;
        sesionRevisada = sesion;
        consultarUsuario()
            .then(({ status, user }) => {
                if (status === 401) {
                    if (getCsrfToken() === sesion) {
                        avisarBorrador('sinsesion', 'Se cerró la sesión: esta pestaña no guarda la operación hasta que vuelvas a entrar.');
                    } else {
                        sesionRevisada = null;
                    }
                    return;
                }
                if (!user) throw new Error('current_user ' + status);
                if (getCsrfToken() !== sesion) { sesionRevisada = null; return; }
                if (confirmarSesion(user.username, sesion)) guardarBorrador(false);
            })
            .catch(() => {
                sesionRevisada = null;
                revisarDesde = Date.now() + 10000;
                avisarBorrador('red', AVISO_RED);
            })
            .finally(() => { revisando = false; });
    }

    // Un solo aviso a la vez. El de otro usuario no se va: hay que recargar.
    let avisoBorrador = null;
    function avisarBorrador(motivo, texto) {
        if (avisoBorrador === 'ajena' && motivo !== 'ajena') return;
        avisoBorrador = motivo;
        const el = document.getElementById('avisoBorrador');
        if (!el) return;
        el.textContent = motivo ? texto : '';
        el.hidden = !motivo;
    }

    function enFlujo() {
        const state = CDI.state || {};
        return !!(state.items && state.items.length > 0 && currentScreen !== 'upload' && currentScreen !== 'ready');
    }

    function guardarBorrador(cerrada) {
        const user = usuarioActual();
        if (!enFlujo() || !user) return;
        const sobre = { v: 1, user, savedAt: Date.now(), closed: !!cerrada, state: CDI.state };
        try {
            localStorage.setItem(claveBorrador, JSON.stringify(sobre));
            if (avisoBorrador === 'lleno') avisarBorrador(null);
        } catch (_) {
            avisarBorrador('lleno', 'El navegador no tiene lugar para guardar la operación: si cerrás o recargás esta pestaña, se pierde.');
        }
    }

    // Lo guardado es del dueño: si la sesión ya no es la suya, no se borra.
    function borrarBorrador() {
        if (!usuarioActual()) return;
        try { localStorage.removeItem(claveBorrador); } catch (_) {}
    }

    // Devuelve el borrador si es del usuario. El que no tiene dueño (la clave
    // vieja guardaba la operación sola) o tiene más de 7 días se borra, sea de
    // quien sea.
    function leerBorrador(clave, user) {
        let parsed = null;
        try { parsed = JSON.parse(localStorage.getItem(clave) || 'null'); } catch (_) { return null; }
        if (!parsed || typeof parsed !== 'object') return null;
        const savedAt = Number(parsed.savedAt) || 0;
        if (parsed.v !== 1 || typeof parsed.user !== 'string' || !parsed.user || Date.now() - savedAt > BORRADOR_VENCE_MS) {
            try { localStorage.removeItem(clave); } catch (_) {}
            return null;
        }
        if (parsed.user !== user) return null;
        const state = parsed.state;
        if (!state || !Array.isArray(state.items) || state.items.length === 0) return null;
        return { clave, savedAt, closed: !!parsed.closed, state };
    }

    // Si el navegador no tiene lugar, el borrador queda donde estaba y se avisa.
    // Si la sesión cambió desde que se buscó (mientras se miraba si la pestaña
    // anterior vive o llegaba el usuario), usuarioActual() da null hasta
    // confirmarla y el borrador no se toca: puede ser de otro. Se avisa, y si
    // la sesión resulta del dueño, se recupera entonces.
    let recuperarAlConfirmar = false;
    function adoptarBorrador(b) {
        const user = usuarioActual();
        if (!user) {
            if (duenoPestana && !sesionAjena) {
                recuperarAlConfirmar = true;
                avisarBorrador('comprobando', 'Comprobando la sesión antes de recuperar la operación guardada…');
            }
            return null;
        }
        try {
            localStorage.setItem(claveBorrador, JSON.stringify({ v: 1, user, savedAt: Date.now(), closed: false, state: b.state }));
        } catch (_) {
            avisarBorrador('lleno', 'El navegador no tiene lugar para recuperar la operación guardada: liberá espacio y recargá la página.');
            return null;
        }
        if (b.clave !== claveBorrador) {
            try { localStorage.removeItem(b.clave); } catch (_) {}
        }
        return b.state;
    }

    // El borrador que le toca a esta pestaña, sin adoptarlo todavía.
    async function buscarBorrador() {
        const user = usuarioActual();
        if (!user) return null;
        if (pestanaAnterior) {
            const propio = leerBorrador(BORRADOR + ':' + pestanaAnterior, user);
            if (propio && !(await pestanaViva(pestanaAnterior))) return propio;
        }
        let claves = [];
        try { claves = Object.keys(localStorage); } catch (_) { return null; }
        const ahora = Date.now();
        let elegido = null;
        claves.forEach(clave => {
            if (clave === claveBorrador) return;
            if (clave !== BORRADOR && clave.indexOf(BORRADOR + ':') !== 0) return;
            const b = leerBorrador(clave, user);
            if (!b) return;
            if (!b.closed && ahora - b.savedAt < BORRADOR_HUERFANO_MS) return;  // otra pestaña la está usando
            if (!elegido || b.savedAt > elegido.savedAt) elegido = b;
        });
        return elegido;
    }

    async function recuperarBorrador() {
        const b = await buscarBorrador();
        return b ? adoptarBorrador(b) : null;
    }

    CDI.borrador = { borrar: borrarBorrador, buscar: buscarBorrador, adoptar: adoptarBorrador, avisar: avisarBorrador, usuario: usuarioActual };

    window.addEventListener('beforeunload', (e) => {
        if (enFlujo()) {
            e.preventDefault();
            e.returnValue = '';
            guardarBorrador(false);
        }
    });

    // Al irse de verdad la pestaña queda marcada como cerrada, para que otra la
    // pueda recuperar; si la operación ya terminó o se canceló, se borra.
    window.addEventListener('pagehide', () => {
        if (enFlujo()) guardarBorrador(true);
        else borrarBorrador();
    });
    // Vuelve desde la caché del navegador (atrás/adelante): sigue en uso, si
    // la sesión es la del dueño (guardarBorrador pasa por usuarioActual).
    window.addEventListener('pageshow', (e) => {
        if (e.persisted) guardarBorrador(false);
    });

    setInterval(() => {
        // Auto-guardamos si estamos a mitad de flujo
        if (enFlujo()) {
            guardarBorrador(false);
        } else if (currentScreen === 'upload' || currentScreen === 'ready') {
            // Se borra sólo el de esta pestaña: la operación terminó o se canceló
            borrarBorrador();
        }
    }, 2500);
})();
