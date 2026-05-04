/* ============================================================
   CDI v2 — Wizard de bienvenida (5 slides)
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const KEY = 'cdi_tour_v2';
    const FORCE_KEY = 'cdi_tour_forced_after_signup';
    const SIGNUP_SESSION_KEY = 'cdi_force_tour_after_signup';
    const WELCOME_SLIDES_COUNT = 5;
    let welcomeCurrent = 0;

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
        const modal = document.getElementById('tourWelcomeModal');
        if (!modal) return;
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
