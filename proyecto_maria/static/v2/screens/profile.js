/* ============================================================
   CDI v2 — Modal de perfil del despachante
   Se abre al clickear el avatar. Solo permite editar nombre y
   CUIT del despachante (el CUIT se usa como CDDTAGR en el MARIA.TXT).
   Expone CDI.openProfileModal().
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    let modal, overlay, closeBtn, cancelBtn, saveBtn;
    let nameInput, cuitInput, emailEl, cuitErrorEl;
    let initialized = false;
    let loading = false;

    function $(id) { return document.getElementById(id); }

    function init() {
        if (initialized) return;
        modal = $('profileModal');
        overlay = $('profileOverlay');
        closeBtn = $('profileClose');
        cancelBtn = $('profileCancel');
        saveBtn = $('profileSave');
        nameInput = $('pfName');
        cuitInput = $('pfCuit');
        emailEl = $('pfEmail');
        cuitErrorEl = $('pfCuitError');
        if (!modal) return;

        closeBtn.addEventListener('click', close);
        cancelBtn.addEventListener('click', close);
        // click en overlay fuera del modal = cerrar
        overlay.addEventListener('click', close);

        saveBtn.addEventListener('click', save);
        [nameInput, cuitInput].forEach(el => {
            if (!el) return;
            el.addEventListener('keydown', (ev) => {
                if (ev.key === 'Enter') { ev.preventDefault(); save(); }
            });
        });
        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Escape' && modal.classList.contains('is-open')) close();
        });

        initialized = true;
    }

    async function open() {
        init();
        if (!modal) return;
        modal.hidden = false;
        overlay.hidden = false;
        requestAnimationFrame(() => {
            modal.classList.add('is-open');
            overlay.classList.add('is-visible');
        });
        clearError();
        // Cargar valores actuales
        await loadProfile();
        setTimeout(() => cuitInput && cuitInput.focus(), 150);
        CDI.track('profile_modal_open');
    }

    function close() {
        if (!modal) return;
        modal.classList.remove('is-open');
        overlay.classList.remove('is-visible');
        setTimeout(() => {
            if (!modal.classList.contains('is-open')) {
                modal.hidden = true;
                overlay.hidden = true;
            }
        }, 220);
    }

    async function loadProfile() {
        if (loading) return;
        loading = true;
        try {
            const res = await CDI.api('/api/user/profile');
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error((data && data.detail) || 'No se pudo cargar');
            const p = data.profile || {};
            nameInput.value = p.name || '';
            cuitInput.value = p.cuit ? CDI.formatCuit(p.cuit) : '';
            emailEl.textContent = p.email || '—';
        } catch (err) {
            CDI.toast('Error', String(err.message || err), 'error');
        } finally {
            loading = false;
        }
    }

    function showError(msg) {
        if (!cuitErrorEl) return;
        cuitErrorEl.textContent = msg;
        cuitErrorEl.hidden = false;
        cuitInput.classList.add('is-error');
    }
    function clearError() {
        if (!cuitErrorEl) return;
        cuitErrorEl.textContent = '';
        cuitErrorEl.hidden = true;
        cuitInput.classList.remove('is-error');
    }

    async function save() {
        clearError();
        const name = String(nameInput.value || '').trim();
        const cuitRaw = String(cuitInput.value || '').trim();
        const cuitNorm = CDI.normalizeCuit(cuitRaw);
        if (cuitRaw && cuitNorm.length !== 11) {
            showError('El CUIT debe tener 11 digitos.');
            return;
        }

        saveBtn.disabled = true;
        saveBtn.textContent = 'Guardando…';
        try {
            const res = await CDI.api('/api/user/profile', {
                method: 'PUT',
                body: JSON.stringify({ name, cuit: cuitNorm })
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error((data && data.detail) || 'No se pudo guardar');
            // Actualizar cache local
            if (CDI.currentUser) {
                CDI.currentUser.name = data.profile.name;
                CDI.currentUser.cuit = data.profile.cuit;
            }
            CDI.toast('Perfil actualizado', cuitNorm ? 'El CUIT se usará en las próximas operaciones.' : 'Datos guardados.', 'success');
            CDI.track('profile_saved', { has_cuit: !!cuitNorm });
            close();
        } catch (err) {
            showError(String(err.message || err));
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Guardar';
        }
    }

    CDI.openProfileModal = open;
    CDI.closeProfileModal = close;

    document.addEventListener('DOMContentLoaded', init);
})();
