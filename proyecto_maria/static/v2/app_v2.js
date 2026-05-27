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

    async function api(path, options = {}) {
        const headers = Object.assign({}, options.headers || {});
        if (options.body && !(options.body instanceof FormData) &&
            !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }
        const res = await fetch(path, Object.assign({}, options, { headers, credentials: 'same-origin' }));
        if (res.status === 401) {
            window.location.href = '/?next=' + encodeURIComponent(window.location.pathname + window.location.search);
            throw new Error('unauthorized');
        }
        return res;
    }

    async function logout() {
        try { await api('/auth/logout', { method: 'POST' }); } catch (_) {}
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
        if (telemetryMuted) return;
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
                headers: { 'Content-Type': 'application/json' },
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
            kind === 'error' ? '!' : (kind === 'success' ? '✓' : 'i'),
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
    async function loadCurrentUser() {
        try {
            const res = await api('/auth/current_user');
            if (!res.ok) return;
            const user = await res.json();
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
            const initials = ((user.name || user.username || '?')
                .split(/\s+/).map(s => s[0]).slice(0, 2).join('') || '?').toUpperCase();
            if (avatar) avatar.textContent = initials;
            if (name) name.textContent = user.name || user.username || '';
        } catch (err) {
            console.warn('[CDI v2] no se pudo cargar usuario:', err);
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
        // Normalizar value inicial si venia prefilleado
        if (input.value) applyFormat();
    }
    CDI.maskDate = maskDate;

    // Formato canonico de NCM: XXXX.XX.XX (8 digitos). Si vienen mas (SIM),
    // respetamos hasta XXXX.XX.XX.XXX. Si vienen menos, formateamos parcial.
    function formatNcm(raw) {
        const d = String(raw == null ? '' : raw).replace(/\D/g, '').slice(0, 11);
        if (d.length <= 4) return d;
        if (d.length <= 6) return d.slice(0, 4) + '.' + d.slice(4);
        if (d.length <= 8) return d.slice(0, 4) + '.' + d.slice(4, 6) + '.' + d.slice(6);
        return d.slice(0, 4) + '.' + d.slice(4, 6) + '.' + d.slice(6, 8) + '.' + d.slice(8);
    }
    CDI.formatNcm = formatNcm;

    // Mascara NCM: inserta los puntos solos mientras se tipea, respeta backspace
    // y acepta pegar "85444200" o "8544.42.00".
    function maskNcm(input) {
        if (!input || input.__cdiMaskNcmApplied) return;
        input.__cdiMaskNcmApplied = true;
        input.setAttribute('inputmode', 'numeric');
        input.setAttribute('maxlength', '14');

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
            cta.addEventListener('click', async () => {
                cta.disabled = true;
                cta.textContent = 'Abriendo...';
                track('billing_cta_clicked', { status: status });
                try {
                    const res = await api('/api/billing/checkout', { method: 'POST' });
                    const data = await res.json().catch(() => ({}));
                    if (data && data.init_point) {
                        window.location.href = data.init_point;
                        return;
                    }
                    if (CDI.toast) CDI.toast('Error', 'No se pudo iniciar el cobro. Probemos de nuevo.', 'error');
                } catch (err) {
                    console.warn('[billing] checkout error', err);
                    if (CDI.toast) CDI.toast('Error', 'No se pudo iniciar el cobro.', 'error');
                } finally {
                    cta.disabled = false;
                    cta.textContent = status === 'past_due' ? 'Activar plan ahora' : 'Activar plan';
                }
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

    /* ---------- Welcome card (primera vez) ----------
       Muestra el cartel de bienvenida solo si el user no lo cerró antes
       (localStorage.cdi_welcome_seen). Una vez cerrado, no vuelve. */
    function setupWelcomeCard() {
        const card = document.getElementById('welcomeCard');
        if (!card) return;
        let seen = '0';
        try { seen = localStorage.getItem('cdi_welcome_seen') || '0'; } catch (_) {}
        if (seen === '1') return; // ya lo vio
        card.hidden = false;
        const dismiss = () => {
            card.hidden = true;
            try { localStorage.setItem('cdi_welcome_seen', '1'); } catch (_) {}
            track('welcome_card_dismissed');
        };
        const cta = document.getElementById('welcomeCta');
        const close = document.getElementById('welcomeClose');
        if (cta) cta.addEventListener('click', dismiss);
        if (close) close.addEventListener('click', dismiss);
        track('welcome_card_shown');
    }

    /* ---------- 10. Bootstrap ---------- */
    document.addEventListener('DOMContentLoaded', () => {
        try { localStorage.removeItem(CLIENTE_KEY); } catch (_) {}
        loadCurrentUser();
        updateClientePill();
        setupFakeSourceBanner();
        setupWelcomeCard();
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
            }
        });

        goTo('upload');
    });
})();
