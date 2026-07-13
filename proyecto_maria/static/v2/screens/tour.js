/* ============================================================
   CDI v2 — Tour de ingreso (4 pasos)
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const KEY = 'cdi_tour_v3';
    const LEGACY_KEY = 'cdi_tour_v2';
    const FORCE_KEY = 'cdi_tour_forced_after_signup';
    const SIGNUP_SESSION_KEY = 'cdi_force_tour_after_signup';
    const WELCOME_SLIDES_COUNT = 4;
    let welcomeCurrent = 0;
    let welcomeReturnFocus = null;

    function getState() {
        try { return localStorage.getItem(KEY) || 'pending'; }
        catch (_) { return 'pending'; }
    }
    function setState(s) {
        try { localStorage.setItem(KEY, s); } catch (_) {}
    }

    function migrateLegacyState() {
        try {
            if (localStorage.getItem(KEY)) return;
            const legacy = localStorage.getItem(LEGACY_KEY);
            if (legacy === 'completed' || legacy === 'dismissed') {
                localStorage.setItem(KEY, legacy);
            }
        } catch (_) {}
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

    function closeOpenOverlays() {
        try { CDI.closeClientesDrawer && CDI.closeClientesDrawer(); } catch (_) {}
        try {
            const ncmOverlay = document.getElementById('ncmOverlay');
            if (ncmOverlay && !ncmOverlay.hidden) ncmOverlay.hidden = true;
        } catch (_) {}
    }

    function renderWelcomeDots() {
        const host = document.getElementById('tourWelcomeDots');
        if (!host) return;
        let html = '';
        for (let i = 0; i < WELCOME_SLIDES_COUNT; i++) {
            const cls = i === welcomeCurrent ? 'dot is-active' : 'dot';
            const current = i === welcomeCurrent ? ' aria-current="step"' : '';
            html += '<button type="button" class="' + cls + '" data-tour-slide="' + i + '"' +
                current + ' aria-label="Ir al paso ' + (i + 1) + '"></button>';
        }
        host.innerHTML = html;
        host.querySelectorAll('[data-tour-slide]').forEach((dot) => {
            dot.addEventListener('click', () => showWelcomeSlide(Number(dot.dataset.tourSlide)));
        });
    }

    function showWelcomeSlide(idx) {
        welcomeCurrent = idx;
        const slides = document.querySelectorAll('.tour-welcome-slide');
        slides.forEach((s, i) => {
            s.classList.toggle('is-active', i === idx);
        });
        // Forzar reflow en el slide activo para que las animaciones
        // de entrada (icon-pop, num-pop, text-rise, callout-rise, shimmer)
        // vuelvan a dispararse desde 0 cada vez que se entra al slide.
        const active = slides[idx];
        if (active) {
            const elements = active.querySelectorAll('.tour-welcome-icon-wrap, .tour-welcome-step-num, h2, p, .tour-welcome-callout');
            elements.forEach(el => {
                // Reset: quitar y volver a aplicar la animación
                el.style.animation = 'none';
                // Forzar reflow
                void el.offsetWidth;
                el.style.animation = '';
            });
        }
        renderWelcomeDots();

        // Track deslizante: transladar el track al slide activo
        const track = document.getElementById('tourWelcomeTrack');
        if (track) {
            track.style.transform = `translateX(-${idx * 100}%)`;
        }

        // Actualizar barra de progreso
        const progressFill = document.getElementById('tourWelcomeProgressFill');
        if (progressFill) {
            const pct = ((idx + 1) / WELCOME_SLIDES_COUNT) * 100;
            progressFill.style.width = pct + '%';
        }

        // Actualizar counter
        const counter = document.getElementById('tourWelcomeCounter');
        if (counter) {
            counter.textContent = `${idx + 1} / ${WELCOME_SLIDES_COUNT}`;
        }

        // Actualizar kicker + accent dinámico por slide
        const slide = slides[idx];
        if (slide) {
            const accent = slide.dataset.accent || '#0f766e';
            const modal = document.getElementById('tourWelcomeModal');
            if (modal) modal.style.setProperty('--c-accent', accent);
            const isFeatured = slide.classList.contains('is-featured');
            const kicker = document.getElementById('tourWelcomeKicker');
            if (kicker) {
                let label = `Paso ${idx + 1}`;
                if (isFeatured) label = 'Memoria CDI';
                else if (idx === 0) label = 'Bienvenida';
                else if (idx === WELCOME_SLIDES_COUNT - 1) label = 'Cierre';
                kicker.textContent = label;
            }
        }

        const btnPrev = document.getElementById('tourWelcomePrev');
        const btnNext = document.getElementById('tourWelcomeNext');
        const btnStart = document.getElementById('tourWelcomeStart');
        if (btnPrev) btnPrev.hidden = idx === 0;
        if (btnNext) btnNext.hidden = idx === WELCOME_SLIDES_COUNT - 1;
        if (btnStart) btnStart.hidden = idx !== WELCOME_SLIDES_COUNT - 1;
    }

    function showWelcome() {
        closeOpenOverlays();
        const modal = document.getElementById('tourWelcomeModal');
        if (!modal) return;
        welcomeReturnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        welcomeCurrent = 0;
        showWelcomeSlide(0);
        modal.hidden = false;
        requestAnimationFrame(() => {
            modal.classList.add('is-visible');
            const skip = document.getElementById('tourWelcomeSkip');
            if (skip) skip.focus();
        });
        track('tour_welcome_shown');
    }

    function hideWelcome(restoreFocus) {
        const modal = document.getElementById('tourWelcomeModal');
        if (!modal) return;
        modal.classList.remove('is-visible');
        setTimeout(() => {
            modal.hidden = true;
            if (restoreFocus && welcomeReturnFocus && document.contains(welcomeReturnFocus)) {
                welcomeReturnFocus.focus();
            }
        }, 180);
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
        hideWelcome(false);
        setState('completed');
        track('tour_welcome_start_operation');
        try { CDI.goTo && CDI.goTo('upload'); } catch (_) {}
        setTimeout(() => {
            const upload = document.getElementById('uploadPickBtn');
            if (upload) upload.focus();
        }, 240);
    }

    function skipWelcome() {
        hideWelcome(true);
        setState('dismissed');
        track('tour_welcome_skipped');
    }

    function onWelcomeKeydown(event) {
        const modal = document.getElementById('tourWelcomeModal');
        if (!modal || modal.hidden) return;
        if (event.key === 'Tab') {
            const focusable = Array.from(modal.querySelectorAll(
                'button:not([hidden]):not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )).filter((el) => el.offsetParent !== null);
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        } else if (event.key === 'ArrowRight') {
            event.preventDefault();
            welcomeNext();
        } else if (event.key === 'ArrowLeft') {
            event.preventDefault();
            welcomePrev();
        } else if (event.key === 'Escape') {
            event.preventDefault();
            skipWelcome();
        }
    }

    // Demo user: siempre dispara el tour una vez por sesión (para testing/demo).
    // Llamado por init() antes que cualquier otra check.
    const DEMO_SESSION_KEY = 'cdi_tour_demo_session_shown';
    async function checkDemoForceTour() {
        try {
            const r = await fetch('/auth/current_user', { credentials: 'include' });
            if (!r.ok) return false;
            const u = await r.json();
            if (u.username !== 'demo') return false;
            // Una vez por sesión: si ya se mostró en esta sesión, no repetir.
            try {
                if (sessionStorage.getItem(DEMO_SESSION_KEY) === '1') return false;
                sessionStorage.setItem(DEMO_SESSION_KEY, '1');
            } catch (_) {}
            return true;
        } catch (_) {
            return false;
        }
    }

    async function init() {
        migrateLegacyState();
        // Demo user: forzar tour una vez por sesión (override de cualquier estado previo)
        if (await checkDemoForceTour()) {
            setState('pending'); // reset por si estaba 'completed' o 'dismissed'
            setTimeout(() => {
                try { CDI.goTo && CDI.goTo('upload'); } catch (_) {}
                showWelcome();
            }, 700);
            track('tour_forced_demo_user');
            return;
        }
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
    }

    function setupListeners() {
        const btnWelcomeStart = document.getElementById('tourWelcomeStart');
        const btnWelcomeNext = document.getElementById('tourWelcomeNext');
        const btnWelcomePrev = document.getElementById('tourWelcomePrev');
        const btnWelcomeSkip = document.getElementById('tourWelcomeSkip');
        if (btnWelcomeStart) btnWelcomeStart.addEventListener('click', startFromWelcome);
        if (btnWelcomeNext) btnWelcomeNext.addEventListener('click', welcomeNext);
        if (btnWelcomePrev) btnWelcomePrev.addEventListener('click', welcomePrev);
        if (btnWelcomeSkip) btnWelcomeSkip.addEventListener('click', skipWelcome);
        document.addEventListener('keydown', onWelcomeKeydown);
    }

    CDI.openTour = function () {
        closeOpenOverlays();
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
