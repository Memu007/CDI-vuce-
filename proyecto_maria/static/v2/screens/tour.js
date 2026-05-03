/* ============================================================
   CDI v2 — Tour de bienvenida (3 pasos contextuales)

   Diseno (heredado del Tour V4 de v1):
   - NO bloquea: coachmark sutil opt-in a los 2.5s.
   - 3 pasos: subir, revisar, descargar (no es feature tour, es outcome tour).
   - Contextual: paso 2 y 3 solo aparecen cuando el user llega a esas
     pantallas (escucha `cdi:screen-enter`).
   - "Salta tour" siempre visible.
   - Estado en localStorage: pending | started | paused_at_<id> |
     dismissed | completed.
   - Reabrible desde "Mi perfil" (CDI.openTour).
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const KEY = 'cdi_tour_v2';
    const STEPS = [
        {
            id: 'upload',
            screen: 'upload',
            targetId: 'uploadPickBtn',
            title: 'Subí tu primera factura',
            text: 'Arrastrá un PDF o Excel del proveedor y leemos los items por vos.',
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

    function getState() {
        try { return localStorage.getItem(KEY) || 'pending'; }
        catch (_) { return 'pending'; }
    }
    function setState(s) {
        try { localStorage.setItem(KEY, s); } catch (_) {}
    }

    function track(action, props) {
        try { CDI.track && CDI.track(action, props || {}); } catch (_) {}
    }

    function init() {
        const state = getState();
        if (state === 'completed' || state === 'dismissed') return;
        if (state.indexOf && state.indexOf('paused_at_') === 0) {
            // Si quedo pausado, NO mostramos el coachmark; esperamos a que
            // el usuario llegue a la pantalla correcta y retomamos solos.
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
        setTimeout(() => { cm.hidden = true; }, 220);
    }

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
        currentStep = -1;
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
        try { target.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (_) {}
        setTimeout(() => positionTooltip(target, step, idx), 320);
        track('tour_step_shown', { step: step.id });
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

        activeTooltip = tooltip;
        tooltip.hidden = false;
        // Reseteamos posicion para medir bien
        tooltip.style.top = '-9999px';
        tooltip.style.left = '0';

        requestAnimationFrame(() => {
            const rect = target.getBoundingClientRect();
            const ttRect = tooltip.getBoundingClientRect();
            let top = rect.bottom + 12;
            let left = rect.left + (rect.width / 2) - (ttRect.width / 2);
            if (top + ttRect.height > window.innerHeight - 12) {
                top = rect.top - ttRect.height - 12;
            }
            if (top < 12) top = 12;
            if (left < 12) left = 12;
            if (left + ttRect.width > window.innerWidth - 12) {
                left = window.innerWidth - ttRect.width - 12;
            }
            tooltip.style.top = top + 'px';
            tooltip.style.left = left + 'px';
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
            setTimeout(() => { t.hidden = true; }, 220);
            activeTooltip = null;
        }
    }

    function next() {
        showStep(currentStep + 1);
    }

    function complete() {
        closeActiveTooltip();
        setState('completed');
        currentStep = -1;
        track('tour_completed');
    }

    // Avance contextual: cuando el user cambia de pantalla, si hay un step
    // pendiente que corresponde a esa pantalla, lo mostramos.
    document.addEventListener('cdi:screen-enter', (ev) => {
        const state = getState();
        if (state === 'completed' || state === 'dismissed') return;
        const inProgress = state === 'started' || (state.indexOf && state.indexOf('paused_at_') === 0);
        if (!inProgress) return;
        const screenName = ev.detail && ev.detail.screen;
        if (!screenName) return;
        const idx = STEPS.findIndex(s => s.screen === screenName);
        if (idx === -1) return;
        // Nunca retrocedemos: si el step ya pasó, no lo volvemos a mostrar.
        if (idx <= currentStep && currentStep >= 0) return;
        setTimeout(() => showStep(idx), 250);
    });

    function setupListeners() {
        const btnStart = document.getElementById('tourStart');
        const btnLater = document.getElementById('tourLater');
        const btnCta = document.getElementById('tourCta');
        const btnSkip = document.getElementById('tourSkip');
        if (btnStart) btnStart.addEventListener('click', start);
        if (btnLater) btnLater.addEventListener('click', dismiss);
        if (btnCta) btnCta.addEventListener('click', next);
        if (btnSkip) btnSkip.addEventListener('click', dismiss);
    }

    // Reabrir el tour desde "Mi perfil"
    CDI.openTour = function () {
        setState('started');
        currentStep = -1;
        closeActiveTooltip();
        // Aseguramos estar en la pantalla del paso 1
        if (CDI.goTo) {
            try { CDI.goTo('upload'); } catch (_) {}
        }
        setTimeout(() => showStep(0), 350);
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
