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
    let pfDefaultAduana, pfDefaultPuerto, pfDefaultTipoDest;
    let replayTourBtn;
    // Seguridad (cambio password)
    let currentPwdInput, newPwdInput, pwdErrorEl, changePwdBtn;
    // Plan y facturación
    let billingSummary, billingStatusEl, billingNextWrap, billingNextEl;
    let billingPmWrap, billingPmEl;
    let billingPlanWrap, billingPlanSelect, billingUsageWrap, billingUsageEl;
    let billingActivateBtn, billingReactivateBtn, billingCancelBtn, billingTopupBtn;
    // Mi estudio (organización)
    let orgBlock, orgSummaryEl, orgNameEl, orgMembersEl, orgInviteEmailEl, orgInviteBtn, orgInviteHintEl;
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
        pfDefaultAduana = $('pfDefaultAduana');
        pfDefaultPuerto = $('pfDefaultPuerto');
        pfDefaultTipoDest = $('pfDefaultTipoDest');
        replayTourBtn = $('pfReplayTour');
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
            el.addEventListener('input', () => {
                if (cuitErrorEl && !cuitErrorEl.hidden) clearError();
            });
        });
        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Escape' && modal.classList.contains('is-open')) close();
        });

        if (replayTourBtn) {
            replayTourBtn.addEventListener('click', () => {
                close();
                // El tour cierra el modal y arranca desde paso 1.
                setTimeout(() => {
                    if (CDI.openTour) CDI.openTour();
                }, 260);
            });
        }

        // Sección Seguridad (cambio password)
        currentPwdInput = $('pfCurrentPassword');
        newPwdInput = $('pfNewPassword');
        pwdErrorEl = $('pfPasswordError');
        changePwdBtn = $('pfChangePassword');
        if (changePwdBtn) changePwdBtn.addEventListener('click', changePassword);

        // Sección Plan y facturación
        billingSummary = $('pfBillingSummary');
        billingStatusEl = $('pfBillingStatus');
        billingNextWrap = $('pfBillingNextWrap');
        billingNextEl = $('pfBillingNext');
        billingPmWrap = $('pfBillingPmWrap');
        billingPmEl = $('pfBillingPm');
        billingActivateBtn = $('pfBillingActivate');
        billingReactivateBtn = $('pfBillingReactivate');
        billingCancelBtn = $('pfBillingCancel');
        billingPlanWrap = $('pfBillingPlanWrap');
        billingPlanSelect = $('pfBillingPlanSelect');
        billingUsageWrap = $('pfBillingUsageWrap');
        billingUsageEl = $('pfBillingUsage');
        billingTopupBtn = $('pfBillingTopup');
        if (billingActivateBtn) billingActivateBtn.addEventListener('click', () => openCheckout('activate'));
        if (billingReactivateBtn) billingReactivateBtn.addEventListener('click', reactivateBilling);
        if (billingCancelBtn) billingCancelBtn.addEventListener('click', cancelBilling);
        if (billingTopupBtn) billingTopupBtn.addEventListener('click', openTopup);

        // Mi estudio
        orgBlock = $('pfOrgBlock');
        orgSummaryEl = $('pfOrgSummary');
        orgNameEl = $('pfOrgName');
        orgMembersEl = $('pfOrgMembers');
        orgInviteEmailEl = $('pfOrgInviteEmail');
        orgInviteBtn = $('pfOrgInviteBtn');
        orgInviteHintEl = $('pfOrgInviteHint');
        if (orgInviteBtn) orgInviteBtn.addEventListener('click', inviteMember);

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
        clearPasswordError();
        if (currentPwdInput) currentPwdInput.value = '';
        if (newPwdInput) newPwdInput.value = '';
        // Cargar valores actuales
        await Promise.all([loadProfile(), loadBilling(), loadOrg()]);
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
        }, 130);
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
            emailEl.value = p.email || '';
            if (pfDefaultAduana) pfDefaultAduana.value = p.default_aduana_codigo || '';
            if (pfDefaultPuerto) pfDefaultPuerto.value = p.default_puerto_destino || '';
            if (pfDefaultTipoDest) pfDefaultTipoDest.value = p.default_tipo_destinacion || '';
            // Si tiene algun default cargado, mostrar el bloque expandido
            const defBlock = document.getElementById('pfDefaultsBlock');
            const hasAnyDefault = !!(p.default_aduana_codigo || p.default_puerto_destino || p.default_tipo_destinacion);
            if (defBlock && hasAnyDefault) defBlock.open = true;
            // Cachear globalmente para que review/finalize lo lean sin pegarle a la API otra vez
            CDI.userDefaults = {
                aduana_codigo: p.default_aduana_codigo || '',
                puerto_destino: p.default_puerto_destino || '',
                tipo_destinacion: p.default_tipo_destinacion || ''
            };
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
        const emailVal = String(emailEl.value || '').trim().toLowerCase();
        if (cuitRaw && cuitNorm.length !== 11) {
            showError('El CUIT debe tener 11 digitos.');
            return;
        }
        if (emailVal && !emailVal.match(/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/)) {
            if (CDI.toast) CDI.toast('Email no válido', 'Revisá el formato.', 'error');
            return;
        }

        const aduanaVal = pfDefaultAduana ? String(pfDefaultAduana.value || '').trim().toUpperCase() : '';
        const puertoVal = pfDefaultPuerto ? String(pfDefaultPuerto.value || '').trim().toUpperCase() : '';
        const tipoVal = pfDefaultTipoDest ? String(pfDefaultTipoDest.value || '').trim().toUpperCase() : '';

        saveBtn.disabled = true;
        saveBtn.textContent = 'Guardando…';
        try {
            const res = await CDI.api('/api/user/profile', {
                method: 'PUT',
                body: JSON.stringify({
                    name,
                    cuit: cuitNorm,
                    email: emailVal,
                    default_aduana_codigo: aduanaVal,
                    default_puerto_destino: puertoVal,
                    default_tipo_destinacion: tipoVal
                })
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error((data && data.detail) || 'No se pudo guardar');
            // Actualizar cache local
            if (CDI.currentUser) {
                CDI.currentUser.name = data.profile.name;
                CDI.currentUser.cuit = data.profile.cuit;
            }
            CDI.userDefaults = {
                aduana_codigo: data.profile.default_aduana_codigo || '',
                puerto_destino: data.profile.default_puerto_destino || '',
                tipo_destinacion: data.profile.default_tipo_destinacion || ''
            };
            const hasDefaults = !!(aduanaVal || puertoVal || tipoVal);
            const subtitle = hasDefaults
                ? 'Tus defaults se aplicarán en las próximas operaciones.'
                : (cuitNorm ? 'El CUIT se usará en las próximas operaciones.' : 'Datos guardados.');
            CDI.toast('Perfil actualizado', subtitle, 'success');
            CDI.track('profile_saved', { has_cuit: !!cuitNorm, has_defaults: hasDefaults });
            close();
        } catch (err) {
            showError(String(err.message || err));
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Guardar';
        }
    }

    /* ---------- Seguridad: cambio de password ---------- */
    function clearPasswordError() {
        if (!pwdErrorEl) return;
        pwdErrorEl.textContent = '';
        pwdErrorEl.hidden = true;
    }
    function showPasswordError(msg) {
        if (!pwdErrorEl) return;
        pwdErrorEl.textContent = msg;
        pwdErrorEl.hidden = false;
    }

    async function changePassword() {
        clearPasswordError();
        const current = String((currentPwdInput && currentPwdInput.value) || '');
        const next = String((newPwdInput && newPwdInput.value) || '');
        if (!current) { showPasswordError('Ingresá tu contraseña actual.'); return; }
        if (next.length < 8) { showPasswordError('La nueva contraseña debe tener al menos 8 caracteres.'); return; }
        if (next === current) { showPasswordError('La nueva contraseña no puede ser igual a la actual.'); return; }

        changePwdBtn.disabled = true;
        const originalText = changePwdBtn.textContent;
        changePwdBtn.textContent = 'Cambiando…';
        try {
            const res = await CDI.api('/api/user/change-password', {
                method: 'POST',
                body: JSON.stringify({ current_password: current, new_password: next })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success) {
                throw new Error((data && data.detail) || 'No se pudo cambiar la contraseña');
            }
            CDI.toast('Contraseña actualizada', 'Usá la nueva la próxima vez que ingreses.', 'success');
            CDI.track('password_changed');
            currentPwdInput.value = '';
            newPwdInput.value = '';
        } catch (err) {
            showPasswordError(String(err.message || err));
        } finally {
            changePwdBtn.disabled = false;
            changePwdBtn.textContent = originalText;
        }
    }

    /* ---------- Plan y facturación ---------- */
    function formatDateAr(iso) {
        if (!iso) return '—';
        try {
            const d = new Date(iso);
            return d.toLocaleDateString('es-AR', { day: '2-digit', month: 'short', year: 'numeric' });
        } catch (_) { return '—'; }
    }

    async function loadBilling() {
        if (!billingStatusEl) return;
        try {
            const res = await CDI.api('/api/billing/me');
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error((data && data.detail) || 'No se pudo cargar billing');
            renderBilling(data);
        } catch (err) {
            billingStatusEl.textContent = 'No disponible';
            console.warn('[profile] loadBilling error', err);
        }
    }

    function renderBilling(b) {
        const status = (b && b.billing_status) || 'none';
        const trialEnd = b && b.trial_ends_at;
        const pm = b && b.payment_method;

        // Reset visibilidad
        if (billingActivateBtn) billingActivateBtn.hidden = true;
        if (billingReactivateBtn) billingReactivateBtn.hidden = true;
        if (billingCancelBtn) billingCancelBtn.hidden = true;
        if (billingTopupBtn) billingTopupBtn.hidden = true;
        if (billingNextWrap) billingNextWrap.hidden = true;
        if (billingPmWrap) billingPmWrap.hidden = true;
        if (billingPlanWrap) billingPlanWrap.hidden = true;
        if (billingUsageWrap) billingUsageWrap.hidden = true;

        // Etiqueta de estado por estado de billing.
        const labels = {
            none: 'Sin plan',
            trial: 'Prueba gratis',
            active: 'Activo',
            past_due: 'Plan vencido',
            canceled: 'Cancelado'
        };
        billingStatusEl.textContent = labels[status] || status;
        billingSummary.textContent = labels[status] || status;

        // Mostrar uso del mes siempre.
        if (billingUsageWrap && billingUsageEl) {
            billingUsageWrap.hidden = false;
            const used = (b && b.ops_used_this_period) || 0;
            const limit = (b && b.ops_limit) || '—';
            const extra = (b && b.extra_ops_remaining) || 0;
            billingUsageEl.textContent = used + ' / ' + limit + ' ops usadas' + (extra ? ' (' + extra + ' créditos extra)' : '');
        }

        // Selector de plan visible solo si no está active (puede cambiar plan).
        if (billingPlanWrap && billingPlanSelect && status !== 'active') {
            billingPlanWrap.hidden = false;
            billingPlanSelect.value = (b && b.plan) || 'premium';
        }

        // Fecha relevante.
        const nextLabel = document.getElementById('pfBillingNextLabel');
        if (trialEnd && billingNextWrap) {
            billingNextWrap.hidden = false;
            billingNextEl.textContent = formatDateAr(trialEnd);
            if (nextLabel) {
                if (status === 'trial') nextLabel.textContent = 'Trial vence';
                else if (status === 'active') nextLabel.textContent = 'Próximo cobro';
                else if (status === 'canceled') nextLabel.textContent = 'Servicio activo hasta';
                else nextLabel.textContent = 'Fecha';
            }
        }

        // Método de pago si existe.
        if (pm && pm.last4 && billingPmWrap) {
            billingPmWrap.hidden = false;
            const brand = (pm.brand || 'tarjeta').toString();
            billingPmEl.textContent = brand + ' ···· ' + pm.last4;
        }

        // Botones por estado.
        if (status === 'trial' || status === 'active') {
            if (billingCancelBtn) billingCancelBtn.hidden = false;
        }
        if (status === 'past_due' || status === 'none') {
            if (billingActivateBtn) billingActivateBtn.hidden = false;
        }
        if (status === 'canceled') {
            if (billingReactivateBtn) billingReactivateBtn.hidden = false;
        }
        if (billingTopupBtn && status !== 'none' && status !== 'past_due') {
            billingTopupBtn.hidden = false;
        }
    }

    async function openCheckout() {
        try {
            const plan = billingPlanSelect && !billingPlanSelect.hidden ? billingPlanSelect.value : 'premium';
            const res = await CDI.api('/api/billing/checkout', {
                method: 'POST',
                body: JSON.stringify({ plan: plan })
            });
            const data = await res.json().catch(() => ({}));
            if (data && data.init_point) {
                window.location.href = data.init_point;
                return;
            }
            CDI.toast('Error', 'No se pudo iniciar el cobro.', 'error');
        } catch (err) {
            CDI.toast('Error', String(err.message || err), 'error');
        }
    }

    async function openTopup() {
        try {
            const res = await CDI.api('/api/billing/topup', { method: 'POST', body: JSON.stringify({}) });
            const data = await res.json().catch(() => ({}));
            if (data && data.init_point) {
                window.location.href = data.init_point;
                return;
            }
            CDI.toast('Error', 'No se pudo iniciar el top-up.', 'error');
        } catch (err) {
            CDI.toast('Error', String(err.message || err), 'error');
        }
    }

    async function cancelBilling() {
        const ok = await CDI.confirm({
            title: 'Cancelar plan',
            lead: '¿Seguro que querés cancelar?',
            text: 'Vas a poder seguir usando CDI hasta el fin del período ya pagado. Después no se renueva automáticamente. Podés reactivar cuando quieras.',
            confirmText: 'Sí, cancelar',
            cancelText: 'Volver'
        });
        if (!ok) return;
        billingCancelBtn.disabled = true;
        billingCancelBtn.textContent = 'Cancelando…';
        try {
            const res = await CDI.api('/api/billing/cancel', { method: 'POST' });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success) throw new Error((data && data.detail) || 'No se pudo cancelar');
            CDI.toast('Plan cancelado', 'Podés reactivar cuando quieras desde este mismo panel.', 'success');
            CDI.track('billing_canceled');
            await loadBilling();
        } catch (err) {
            CDI.toast('Error', String(err.message || err), 'error');
        } finally {
            billingCancelBtn.disabled = false;
            billingCancelBtn.textContent = 'Cancelar plan';
        }
    }

    async function reactivateBilling() {
        billingReactivateBtn.disabled = true;
        billingReactivateBtn.textContent = 'Reactivando…';
        try {
            const res = await CDI.api('/api/billing/reactivate', { method: 'POST' });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success) throw new Error((data && data.detail) || 'No se pudo reactivar');
            if (data.needs_checkout) {
                CDI.toast('Reactivar plan', 'Tu período pagado terminó. Te llevamos al checkout.', 'info');
                await openCheckout();
                return;
            }
            CDI.toast('Plan reactivado', 'Sigue activo hasta el próximo cobro.', 'success');
            CDI.track('billing_reactivated');
            await loadBilling();
        } catch (err) {
            CDI.toast('Error', String(err.message || err), 'error');
        } finally {
            billingReactivateBtn.disabled = false;
            billingReactivateBtn.textContent = 'Reactivar plan';
        }
    }

    CDI.openProfileModal = open;
    CDI.closeProfileModal = close;

    /* ---------- Mi estudio (organización) ---------- */
    async function loadOrg() {
        if (!orgBlock) return;
        try {
            const res = await CDI.api('/api/organizations/mine');
            const data = await res.json().catch(() => ({}));
            const org = data.organization;
            if (!org) { orgBlock.hidden = true; return; }
            orgBlock.hidden = false;
            orgSummaryEl.textContent = org.name || '—';
            orgNameEl.textContent = org.name || '—';
            // Renderizar miembros
            const members = org.members || [];
            orgMembersEl.innerHTML = '';
            members.forEach(m => {
                const row = document.createElement('div');
                row.style.cssText = 'display:flex; align-items:center; justify-content:space-between; padding:6px 8px; border:1px solid var(--c-border,#ddd); border-radius:6px;';
                const info = document.createElement('span');
                info.style.cssText = 'font-size:13px;';
                const name = m.name || m.username;
                info.textContent = name + (m.is_owner ? ' · admin' : '');
                row.appendChild(info);
                if (!m.is_owner) {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'btn btn-ghost btn-sm';
                    btn.textContent = 'Remover';
                    btn.style.cssText = 'font-size:12px; padding:2px 8px;';
                    btn.addEventListener('click', () => removeMember(m.username, btn));
                    row.appendChild(btn);
                }
                orgMembersEl.appendChild(row);
            });
            // Mostrar invitación solo si es owner
            const inviteWrap = $('pfOrgInviteWrap');
            if (inviteWrap) inviteWrap.hidden = !org.is_owner;
        } catch (err) {
            orgBlock.hidden = true;
        }
    }

    async function inviteMember() {
        const email = (orgInviteEmailEl && orgInviteEmailEl.value || '').trim();
        if (!email) return;
        orgInviteBtn.disabled = true;
        orgInviteBtn.textContent = 'Enviando...';
        orgInviteHintEl.textContent = '';
        try {
            const res = await CDI.api('/api/organizations/invite', {
                method: 'POST',
                body: JSON.stringify({ email })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success) throw new Error((data && data.detail) || 'No se pudo invitar');
            const link = data.invite_link || (window.location.origin + '/?invite=' + (data.token || ''));
            // Sanitizar: solo permitir links http/https (evita javascript: y otros esquemas)
            const safeLink = /^https?:\/\//i.test(link) ? link : '';
            orgInviteHintEl.textContent = '';
            if (safeLink) {
                const a = document.createElement('a');
                a.href = safeLink;
                a.target = '_blank';
                a.textContent = 'Link de invitación: ' + safeLink;
                orgInviteHintEl.appendChild(a);
            } else {
                orgInviteHintEl.textContent = 'Link generado (formato no válido)';
            }
            orgInviteEmailEl.value = '';
            // Copiar al portapapeles
            try { navigator.clipboard.writeText(safeLink || link); } catch (_) {}
            CDI.toast('Invitación creada', 'El link se copió al portapapeles.', 'success');
            await loadOrg();
        } catch (err) {
            orgInviteHintEl.textContent = String(err.message || err);
        } finally {
            orgInviteBtn.disabled = false;
            orgInviteBtn.textContent = 'Invitar';
        }
    }

    async function removeMember(username, btn) {
        const ok = await CDI.confirm({
            title: 'Remover miembro',
            lead: '¿Sacar a ' + username + ' del estudio?',
            text: 'Va a seguir teniendo su cuenta pero como cuenta individual.',
            acceptText: 'Sí, remover',
            cancelText: 'Cancelar'
        });
        if (!ok) return;
        btn.disabled = true;
        btn.textContent = '...';
        try {
            const res = await CDI.api('/api/organizations/members/' + encodeURIComponent(username), { method: 'DELETE' });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success) throw new Error((data && data.detail) || 'No se pudo remover');
            CDI.toast('Miembro removido', username + ' fue sacado del estudio.', 'success');
            await loadOrg();
        } catch (err) {
            CDI.toast('Error', String(err.message || err), 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Remover';
        }
    }

    document.addEventListener('DOMContentLoaded', init);
})();
