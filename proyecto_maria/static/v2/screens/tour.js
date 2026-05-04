/* ============================================================
   CDI v2 — Tour de bienvenida (3 pasos contextuales)

   UX v2.1 (mayo 2026):
   - Primera visita: coachmark sutil abajo-a-la-derecha a los 2.5s.
     Pasivo, opt-in. Si el user toca "Ahora no" queda dismissed.
   - Reapertura explícita ("Ver tour" en footer o perfil): arranca
     DIRECTO el paso 1, cerrando drawers abiertos si hacen falta.
     No re-preguntamos: si clickeó "Ver tour", ya decidió.
   - Tooltip con flechita que apunta al target, puntitos de progreso,
     ESC para cerrar, "Saltar tour" siempre visible.
   - Contextual: pasos 2 y 3 retoman solos cuando el user llega a la
     pantalla correspondiente (listener cdi:screen-enter).
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const KEY = 'cdi_tour_v2';
    const FORCE_KEY = 'cdi_tour_forced_after_signup';
    const SIGNUP_SESSION_KEY = 'cdi_force_tour_after_signup';
    const STEPS = [
        {
            id: 'upload',
            screen: 'upload',
            targetId: 'uploadPickBtn',
            title: 'Subí tu primera factura',
            text: 'Arrastrá un PDF o Excel del proveedor y leemos los ítems por vos.',
            cta: 'Entendido',
        },
        {
            id: 'review',
            screen: 'review',
            targetId: 'reviewContinueBtn',
            title: 'Revisá los datos detectados',
            text: 'Editá lo que falte. Cuando estén todos los datos requeridos, podés continuar.',
            cta: 'Siguiente',
        },
        {
            id: 'ready',
            screen: 'ready',
            targetId: 'readyDownloadBtn',
            title: 'Descargá tu MARIA.TXT',
            text: 'Cuando los datos están OK, con un clic descargás el archivo listo para aduana.',
            cta: 'Listo',
        },
    ];

    let currentStep = -1;
    let activeTooltip = null;
    let activeTarget = null;
    let escListener = null;

    function getState() {
        try { return localStorage.getItem(KEY) || 'pending'; }
        catch (_) { return 'pending'; }
    }
    function setState(s) {
        try { localStorage.setItem(KEY, s); } catch (_) {}
    }

    function hasSignupSignal() {
        try {
            const qs = new URLSearchParams(window.location.search || '');
            if (qs.get('verified') === 'true') return true;
        } catch (_) {}
        try {
            if (sessionStorage.getItem(SIGNUP_SESSION_KEY) === '1') return true;
        } catch (_) {}
        return false;
    }

    function shouldForceAfterSignup() {
        if (!hasSignupSignal()) return false;
        try {
            if (sessionStorage.getItem(FORCE_KEY) === '1') return false;
        } catch (_) {}
        return true;
    }

    function markForcedAfterSignup() {
        try { sessionStorage.setItem(FORCE_KEY, '1'); } catch (_) {}
        try { sessionStorage.removeItem(SIGNUP_SESSION_KEY); } catch (_) {}
    }

    function track(action, props) {
        try { CDI.track && CDI.track(action, props || {}); } catch (_) {}
    }

    /* ---------- Coachmark pasivo (solo primera visita) ---------- */
    function init() {
        if (shouldForceAfterSignup()) {
            markForcedAfterSignup();
            setState('welcome_seen');
            setTimeout(() => {
                try { CDI.goTo && CDI.goTo('upload'); } catch (_) {}
                showWelcome();
            }, 700);
            track('tour_forced_after_signup');
            return;
        }
        const state = getState();
        if (state === 'completed' || state === 'dismissed') return;
        if (state.indexOf && state.indexOf('paused_at_') === 0) {
            // Pausado: esperamos a que llegue solo a la pantalla correcta.
            const idx = STEPS.findIndex(s => 'paused_at_' + s.id === state);
            if (idx >= 0) currentStep = idx - 1;
            return;
        }
        setTimeout(showCoachmark, 2500);
    }

    function showCoachmark() {
        const cm = document.getElementById('tourCoachmark');
        if (!cm) return;
        const state = getState();
        if (state === 'completed' || state === 'dismissed' || state === 'started') return;
        cm.hidden = false;
        requestAnimationFrame(() => cm.classList.add('is-visible'));
    }
    function hideCoachmark() {
        const cm = document.getElementById('tourCoachmark');
        if (!cm) return;
        cm.classList.remove('is-visible');
        setTimeout(() => { cm.hidden = true; }, 240);
    }

    const WELCOME_SLIDES_COUNT = 5;
    let welcomeCurrent = 0;

    function renderWelcomeDots() {
        const host = document.getElementById('tourWelcomeDots');
        if (!host) return;
        let html = '';
        for (let i = 0; i < WELCOME_SLIDES_COUNT; i++) {
            const cls = i === welcomeCurrent ? 'dot is-active' : 'dot';
            html += '<span class="' + cls + '"></span>';
        }
        host.innerHTML = html;
    }

    function showWelcomeSlide(idx) {
        welcomeCurrent = idx;
        const slides = document.querySelectorAll('.tour-welcome-slide');
        slides.forEach((s, i) => {
            s.classList.toggle('is-active', i === idx);
        });
        renderWelcomeDots();
        const btnPrev = document.getElementById('tourWelcomePrev');
        const btnNext = document.getElementById('tourWelcomeNext');
        const btnStart = document.getElementById('tourWelcomeStart');
        if (btnPrev) btnPrev.hidden = idx === 0;
        if (btnNext) btnNext.hidden = idx === WELCOME_SLIDES_COUNT - 1;
        if (btnStart) btnStart.hidden = idx !== WELCOME_SLIDES_COUNT - 1;
    }

    function showWelcome() {
        closeOpenOverlays();
        hideCoachmark();
        closeActiveTooltip();
        const modal = document.getElementById('tourWelcomeModal');
        if (!modal) {
            start();
            return;
        }
        welcomeCurrent = 0;
        showWelcomeSlide(0);
        modal.hidden = false;
        requestAnimationFrame(() => modal.classList.add('is-visible'));
        track('tour_welcome_shown');
    }

    function hideWelcome() {
        const modal = document.getElementById('tourWelcomeModal');
        if (!modal) return;
        modal.classList.remove('is-visible');
        setTimeout(() => { modal.hidden = true; }, 180);
    }

    function welcomeNext() {
        if (welcomeCurrent < WELCOME_SLIDES_COUNT - 1) {
            showWelcomeSlide(welcomeCurrent + 1);
        }
    }

    function welcomePrev() {
        if (welcomeCurrent > 0) {
            showWelcomeSlide(welcomeCurrent - 1);
        }
    }

    function startFromWelcome() {
        hideWelcome();
        setState('completed');
        track('tour_welcome_start_operation');
        try { CDI.goTo && CDI.goTo('upload'); } catch (_) {}
    }

    function skipWelcome() {
        hideWelcome();
        setState('dismissed');
        track('tour_welcome_skipped');
    }

    /* ---------- Flow ---------- */
    function start() {
        hideCoachmark();
        setState('started');
        track('tour_started');
        showStep(0);
    }

    function dismiss() {
        setState('dismissed');
        track('tour_dismissed', { at_step: currentStep });
        hideCoachmark();
        closeActiveTooltip();
        removeEscListener();
        currentStep = -1;
    }

    function closeOpenOverlays() {
        // Cerrar drawer de clientes si está abierto.
        try { CDI.closeClientesDrawer && CDI.closeClientesDrawer(); } catch (_) {}
        // Cerrar overlay NCM si está abierto.
        try {
            const ncmOverlay = document.getElementById('ncmOverlay');
            if (ncmOverlay && !ncmOverlay.hidden) ncmOverlay.hidden = true;
        } catch (_) {}
    }

    function addEscListener() {
        if (escListener) return;
        escListener = function (e) {
            if (e.key === 'Escape' || e.keyCode === 27) {
                e.stopPropagation();
                dismiss();
            }
        };
        document.addEventListener('keydown', escListener, true);
    }
    function removeEscListener() {
        if (!escListener) return;
        document.removeEventListener('keydown', escListener, true);
        escListener = null;
    }

    function showStep(idx) {
        closeActiveTooltip();
        if (idx >= STEPS.length) {
            complete();
            return;
        }
        currentStep = idx;
        const step = STEPS[idx];
        const activeScreen = document.querySelector('.screen.is-active');
        const screenName = activeScreen ? activeScreen.getAttribute('data-screen') : null;
        if (step.screen && screenName !== step.screen) {
            setState('paused_at_' + step.id);
            return;
        }
        const target = document.getElementById(step.targetId);
        if (!target || target.offsetParent === null) {
            setState('paused_at_' + step.id);
            return;
        }
        activeTarget = target;
        target.classList.add('tour-spotlight');
        addEscListener();
        try { target.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (_) {}
        setTimeout(() => positionTooltip(target, step, idx), 320);
        track('tour_step_shown', { step: step.id });
    }

    function renderDots(idx) {
        const host = document.getElementById('tourDots');
        if (!host) return;
        const total = STEPS.length;
        let html = '';
        for (let i = 0; i < total; i++) {
            const cls = i < idx ? 'dot is-done' : (i === idx ? 'dot is-active' : 'dot');
            html += '<span class="' + cls + '"></span>';
        }
        host.innerHTML = html;
    }

    function positionTooltip(target, step, idx) {
        const tooltip = document.getElementById('tourTooltip');
        if (!tooltip) return;
        const titleEl = document.getElementById('tourTitle');
        const textEl = document.getElementById('tourText');
        const ctaEl = document.getElementById('tourCta');
        const stepEl = document.getElementById('tourStepLabel');
        if (titleEl) titleEl.textContent = step.title;
        if (textEl) textEl.textContent = step.text;
        if (ctaEl) ctaEl.textContent = step.cta;
        if (stepEl) stepEl.textContent = 'Paso ' + (idx + 1) + ' de ' + STEPS.length;
        renderDots(idx);

        activeTooltip = tooltip;
        tooltip.hidden = false;
        tooltip.style.top = '-9999px';
        tooltip.style.left = '0';

        requestAnimationFrame(() => {
            const rect = target.getBoundingClientRect();
            const ttRect = tooltip.getBoundingClientRect();
            const gap = 14; // espacio para la flechita
            const vw = window.innerWidth;
            const vh = window.innerHeight;

            // Preferimos tooltip DEBAJO del target (flecha apuntando arriba).
            let arrow = 'bottom';
            let top = rect.bottom + gap;
            if (top + ttRect.height > vh - 12) {
                // No entra abajo: lo ponemos arriba.
                top = rect.top - ttRect.height - gap;
                arrow = 'top';
            }
            if (top < 12) { top = 12; arrow = 'none'; }

            let left = rect.left + (rect.width / 2) - (ttRect.width / 2);
            if (left < 12) left = 12;
            if (left + ttRect.width > vw - 12) left = vw - ttRect.width - 12;

            // Calcular X relativa para posicionar la flecha sobre el target.
            const targetCenterX = rect.left + (rect.width / 2);
            let arrowX = targetCenterX - left;
            // Margen mínimo: que la flecha no se pegue al borde del tooltip.
            const minArrow = 18, maxArrow = ttRect.width - 18;
            if (arrowX < minArrow) arrowX = minArrow;
            if (arrowX > maxArrow) arrowX = maxArrow;

            tooltip.style.top = top + 'px';
            tooltip.style.left = left + 'px';
            tooltip.style.setProperty('--arrow-x', arrowX + 'px');
            tooltip.setAttribute('data-arrow', arrow);
            tooltip.classList.add('is-visible');
        });
    }

    function closeActiveTooltip() {
        if (activeTarget) {
            activeTarget.classList.remove('tour-spotlight');
            activeTarget = null;
        }
        if (activeTooltip) {
            const t = activeTooltip;
            t.classList.remove('is-visible');
            setTimeout(() => { t.hidden = true; }, 240);
            activeTooltip = null;
        }
    }

    function next() {
        showStep(currentStep + 1);
    }

    function complete() {
        closeActiveTooltip();
        removeEscListener();
        setState('completed');
        currentStep = -1;
        track('tour_completed');
    }

    /* ---------- Avance contextual ---------- */
    document.addEventListener('cdi:screen-enter', (ev) => {
        const state = getState();
        if (state === 'completed' || state === 'dismissed') return;
        const inProgress = state === 'started' || (state.indexOf && state.indexOf('paused_at_') === 0);
        if (!inProgress) return;
        const screenName = ev.detail && ev.detail.screen;
        if (!screenName) return;
        const idx = STEPS.findIndex(s => s.screen === screenName);
        if (idx === -1) return;
        if (idx <= currentStep && currentStep >= 0) return;
        setTimeout(() => showStep(idx), 250);
    });

    /* ---------- Listeners de UI ---------- */
    function setupListeners() {
        const btnStart = document.getElementById('tourStart');
        const btnLater = document.getElementById('tourLater');
        const btnCta = document.getElementById('tourCta');
        const btnSkip = document.getElementById('tourSkip');
        const btnWelcomeStart = document.getElementById('tourWelcomeStart');
        const btnWelcomeNext = document.getElementById('tourWelcomeNext');
        const btnWelcomePrev = document.getElementById('tourWelcomePrev');
        const btnWelcomeSkip = document.getElementById('tourWelcomeSkip');
        if (btnStart) btnStart.addEventListener('click', start);
        if (btnLater) btnLater.addEventListener('click', dismiss);
        if (btnCta) btnCta.addEventListener('click', next);
        if (btnSkip) btnSkip.addEventListener('click', dismiss);
        if (btnWelcomeStart) btnWelcomeStart.addEventListener('click', startFromWelcome);
        if (btnWelcomeNext) btnWelcomeNext.addEventListener('click', welcomeNext);
        if (btnWelcomePrev) btnWelcomePrev.addEventListener('click', welcomePrev);
        if (btnWelcomeSkip) btnWelcomeSkip.addEventListener('click', skipWelcome);
    }

    /* ---------- Public API: reapertura explícita ---------- */
    // Se llama desde "Ver tour" en footer y desde Mi Perfil.
    // UX: si el user clickeó explícitamente, arrancamos DIRECTO, sin
    // re-preguntar con el coachmark. Cerramos overlays abiertos y vamos
    // a la pantalla del paso 1.
    CDI.openTour = function () {
        closeOpenOverlays();
        hideCoachmark();
        closeActiveTooltip();
        currentStep = -1;
        try { CDI.goTo && CDI.goTo('upload'); } catch (_) {}
        setTimeout(showWelcome, 220);
        track('tour_reopened');
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setupListeners();
            init();
        });
    } else {
        setupListeners();
        init();
    }
})();
