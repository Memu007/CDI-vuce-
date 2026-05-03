// Variables globales
let itemCounter = 0;

// Rate limiting para prevenir error 429 de Gemini API
let lastUploadTimestamp = 0;
const UPLOAD_COOLDOWN_MS = 5000; // 5 segundos entre uploads
let uploadCooldownTimer = null;

// ==================== XSS PROTECTION ====================
/**
 * Escapa caracteres HTML para prevenir XSS
 * @param {string} text - Texto a escapar
 * @returns {string} Texto escapado
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== DAILY LIMITS & PLAN MANAGEMENT ====================

/**
 * Obtener uso diario actual desde localStorage
 */
function getCurrentUsage() {
    const today = new Date().toISOString().split('T')[0];
    const stored = localStorage.getItem('daily_usage');

    if (!stored) {
        return { date: today, operations: 0, items_today: 0 };
    }

    const usage = JSON.parse(stored);

    // Si es un día diferente, resetear
    if (usage.date !== today) {
        return { date: today, operations: 0, items_today: 0 };
    }

    return usage;
}

/**
 * Verificar límites diarios según plan del usuario
 * @param {string} type - Tipo de operación: 'operation' o 'item'
 * @param {number} itemsCount - Cantidad de items a procesar (0 para pre-check)
 * @returns {{allowed: boolean, reason: string}}
 */
function checkDailyLimits(type, itemsCount = 0) {
    const userPlan = localStorage.getItem('user_plan') || 'basic';
    const usage = getCurrentUsage();

    // Límites por plan
    const limits = {
        basic: {
            operations_per_day: 5,
            max_items_daily: 50
        },
        premium: {
            operations_per_day: Infinity,
            max_items_daily: Infinity
        }
    };

    const planLimits = limits[userPlan] || limits.basic;

    // Validar operaciones
    if (type === 'operation') {
        if (usage.operations >= planLimits.operations_per_day) {
            return {
                allowed: false,
                reason: `⚠️ Límite diario alcanzado (${planLimits.operations_per_day} operaciones). Upgrade a Premium para ilimitado.`
            };
        }
    }

    // Validar items totales
    const newTotal = usage.items_today + itemsCount;
    if (newTotal > planLimits.max_items_daily) {
        return {
            allowed: false,
            reason: `⚠️ Límite de items alcanzado (${planLimits.max_items_daily} items/día). Procesaste ${usage.items_today}, intentas agregar ${itemsCount}.`
        };
    }

    return { allowed: true, reason: '' };
}

/**
 * Actualizar contadores de uso diario
 * @param {string} type - 'operation' o 'items'
 * @param {number} count - Cantidad a agregar
 */
function updateDailyUsage(type, count = 1) {
    const usage = getCurrentUsage();

    if (type === 'operation') {
        usage.operations += 1;
    }

    if (type === 'operation' && count > 0) {
        usage.items_today += count;
    }

    localStorage.setItem('daily_usage', JSON.stringify(usage));

    // Actualizar badge si existe
    updateDailyLimitsBadge();
}

/**
 * Actualizar badge de plan (Basic/Premium) en el header
 */
function updatePlanBadge() {
    const userPlan = localStorage.getItem('user_plan') || 'basic';
    const planBadge = document.querySelector('.plan-badge-basic');

    if (!planBadge) return;

    if (userPlan === 'premium') {
        // Ocultar badge de básico y mostrar Premium
        planBadge.style.display = 'none';

        // Agregar badge Premium si no existe
        if (!document.getElementById('premiumBadge')) {
            const premiumBadge = document.createElement('div');
            premiumBadge.id = 'premiumBadge';
            premiumBadge.className = 'plan-badge-premium';
            premiumBadge.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>✨ <strong>Plan Premium:</strong> Acceso ilimitado a todas las funcionalidades</div>
                </div>
            `;
            planBadge.parentNode.insertBefore(premiumBadge, planBadge);
        }
    } else {
        // Mostrar badge de básico
        planBadge.style.display = 'block';
        // Actualizar límites
        updateDailyLimitsBadge();
    }
}

/**
 * Actualizar badge de límites diarios
 */
function updateDailyLimitsBadge() {
    const badgeEl = document.getElementById('dailyLimitsBadge');
    if (!badgeEl) return;

    const userPlan = localStorage.getItem('user_plan') || 'basic';

    if (userPlan === 'premium') {
        badgeEl.innerHTML = '';
        return;
    }

    const usage = getCurrentUsage();
    const limits = { operations_per_day: 5, max_items_daily: 50 };

    badgeEl.innerHTML = `📊 Uso hoy: ${usage.operations}/${limits.operations_per_day} operaciones, ${usage.items_today}/${limits.max_items_daily} items`;
}

// ==================== RATE LIMITING PARA VUCE (NOTAS NCM) ====================

// Sistema de queue + throttling para evitar error 429 en /api/ncm/notas/{ncm}
const VUCE_NOTAS_QUEUE = {
    queue: [],              // {tariff, row, resolve, reject}
    processing: false,
    delay: 350,             // 350ms entre requests (≈3 req/s, margen de seguridad)
    cache: new Map(),       // Caché en memoria: tariff → { notas: [], timestamp }
    cacheTTL: 3600000       // 1 hora
};

/**
 * Fetch notas NCM con rate limiting automático (queue system)
 * @param {string} tariff - Código arancelario (4 dígitos)
 * @param {HTMLElement} row - Fila de la tabla (opcional, para actualizar badge)
 * @returns {Promise<{notas: string[]}>}
 */
async function fetchNotasNCMThrottled(tariff, row = null) {
    // Si no hay NCM válido, retornar vacío
    if (!tariff || tariff.length < 4) {
        return { notas: [] };
    }
    
    const ncm4 = tariff.substring(0, 4);
    
    try {
        const response = await fetch(`/api/ncm/notas/${ncm4}`);
        if (!response.ok) {
            return { notas: [] };
        }
        const data = await response.json();
        
        // Si hay row, actualizar el badge
        if (row && data.notas && data.notas.length > 0) {
            updateNoteBadge(row, data.notas);
        }
        
        return data;
    } catch (e) {
        console.warn('Error fetching notas NCM:', e);
        return { notas: [] };
    }
}

/**
 * Procesar queue de notas NCM (throttled, 1 request cada 350ms)
 */
async function processVuceNotasQueue() {
    // VUCE desactivado a pedido
    return;
}

/**
 * Actualizar badge de notas en la fila y marcar botón (usado por fetch throttled)
 */
function updateNoteBadge(row, notas) {
    const notesBtn = row.querySelector('.btn-notes');
    
    if (notas && notas.length > 0) {
        // Marcar botón como que tiene notas (pulsará en rojo)
        if (notesBtn) {
            notesBtn.classList.add('has-notes');
            notesBtn.title = `📝 ${notas.length} nota${notas.length > 1 ? 's' : ''} - Click para ver`;
        }
    } else {
        // Quitar indicador
        if (notesBtn) {
            notesBtn.classList.remove('has-notes');
            notesBtn.title = '📝 Agregar nota a este NCM';
        }
    }
}

// Estado global de validación NCM
window.validationState = {
    status: 'pending', // 'pending' | 'validating' | 'valid' | 'invalid'
    lastValidatedAt: null,
    itemsHash: null
};

// Función para calcular hash de items (detectar cambios)
function getItemsHash(items) {
    if (!items || items.length === 0) return '';
    return items.map(i => `${i.pieza}|${i.origen}|${i.cantidad}`).join('::');
}

// Elementos del DOM
const operationForm = document.getElementById('operationForm');
const uploadForm = document.getElementById('uploadForm');
const pdfForm = null; // eliminado, queda unificado
const itemsContainer = document.getElementById('itemsContainer');
const addItemBtn = document.getElementById('addItemBtn');
const clearBtn = document.getElementById('clearBtn');
const results = document.getElementById('results');
const errorMessage = document.getElementById('errorMessage');
const loading = document.getElementById('loading');
const downloadLink = document.getElementById('downloadLink');
const successMessage = document.getElementById('successMessage');
const clientsSection = document.getElementById('clientsSection');
const clientSelect = document.getElementById('clientSelectorGrouping');
const refreshClientsBtn = document.getElementById('refreshClientsBtn');
const viewHistoryBtn = document.getElementById('viewHistoryBtn');
const saveHistoryToggle = document.getElementById('saveHistoryToggle');

// Cards de modo
const manualModeCard = document.getElementById('manualModeCard');
const uploadModeCard = document.getElementById('uploadModeCard');
const pdfModeCard = document.getElementById('pdfModeCard');
const clientsModeCard = document.getElementById('clientsModeCard');

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // No insertamos un item por default: reduce carga cognitiva del primer
    // viewport (UX Overhaul v2 - Fase 0). El botón "Agregar item" sigue
    // disponible cuando el usuario realmente quiere cargar a mano.
    setupEventListeners();
    setupFileDropZones();
    renderHealthCard();
    updatePlanBadge(); // Actualizar badge de plan
    // Cargar clientes en selector premium si existe
    try { populateClientSelect().then(()=>{ restoreUiPreferences(); setTimeout(refreshMappingStatusHint, 0); }); } catch (_) { restoreUiPreferences(); setTimeout(refreshMappingStatusHint, 0); }

    // Hero de bienvenida: NO se autocierra (es la guía principal del flujo).
    // Solo lo ocultamos si el usuario ya lo cerró antes con la X.
    maybeHideWelcomeHero();
});
async function renderHealthCard(){
    // Funcionalidad eliminada a pedido del usuario
    return;
}

// ==== Mapeo de columnas por cliente ====
function openMappingModal(){
    const overlay = document.getElementById('mappingOverlay');
    const sel = document.getElementById('clientSelectorGrouping');
    if (!sel || !sel.value){ showToast('Info','Seleccioná un cliente primero'); return; }
    const name = sel.options[sel.selectedIndex]?.text || 'cliente';
    document.getElementById('mappingClientName').textContent = name;
    // cargar mapeo existente
    fetch(`/api/clientes/${sel.value}/column_mapping`).then(r=>r.json()).then(d=>{
        const m = d.mapping || {};
        document.getElementById('map_pieza').value = keyByValue(m,'pieza') || '';
        document.getElementById('map_descripcion').value = keyByValue(m,'descripcion') || '';
        document.getElementById('map_origen').value = keyByValue(m,'origen') || '';
        document.getElementById('map_cantidad').value = keyByValue(m,'cantidad') || '';
        document.getElementById('map_valor_unitario').value = keyByValue(m,'valor_unitario') || '';
        document.getElementById('map_peso_unitario').value = keyByValue(m,'peso_unitario') || '';
    }).finally(()=> { overlay.classList.add('active'); setTimeout(()=>{ try{ document.getElementById('map_pieza').focus(); } catch(_){} }, 0); });
}

function hideMappingModal(){
    document.getElementById('mappingOverlay').classList.remove('active');
}

function keyByValue(obj, target){
    for (const k in obj){ if (obj[k] === target) return k; }
    return '';
}

async function saveColumnMapping(){
    try{
        // Obtener el cliente ID desde el dropdown O desde el atributo del overlay
        const overlay = document.getElementById('mappingOverlay');
        const sel = document.getElementById('clientSelectorGrouping');
        let clientId = overlay?.getAttribute('data-current-client-id') || sel?.value;

        if (!clientId){
            showToast('Info','Seleccioná un cliente');
            return;
        }

        const mapping = {};
        const put = (id, val)=>{ const key=(document.getElementById(id).value||'').trim(); if (key) mapping[key.toLowerCase()] = val; };
        put('map_pieza','pieza');
        put('map_descripcion','descripcion');
        put('map_origen','origen');
        put('map_cantidad','cantidad');
        put('map_valor_unitario','valor_unitario');
        put('map_peso_unitario','peso_unitario');

        const r = await fetch(`/api/clientes/${clientId}/column_mapping`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ mapping }) });
        const d = await r.json();
        if (d.success === false){ showToast('Error','No se pudo guardar','error'); return; }
        showToast('Listo','Mapeo guardado');

        // Recargar la lista de clientes si estamos en esa sección
        const clientsSection = document.getElementById('clientsSection');
        if (clientsSection && !clientsSection.classList.contains('hidden')){
            loadClientes();
        }

        hideMappingModal();
    } catch(_){ showToast('Error','No se pudo guardar','error'); }
}

function restoreMappingInputs(){
    try{
        const sel = document.getElementById('clientSelectorGrouping'); if (!sel || !sel.value) return;
        fetch(`/api/clientes/${sel.value}/column_mapping`).then(r=>r.json()).then(d=>{
            const m = d.mapping || {};
            document.getElementById('map_pieza').value = keyByValue(m,'pieza') || '';
            document.getElementById('map_descripcion').value = keyByValue(m,'descripcion') || '';
            document.getElementById('map_origen').value = keyByValue(m,'origen') || '';
            document.getElementById('map_cantidad').value = keyByValue(m,'cantidad') || '';
            document.getElementById('map_valor_unitario').value = keyByValue(m,'valor_unitario') || '';
            document.getElementById('map_peso_unitario').value = keyByValue(m,'peso_unitario') || '';
            showToast('Listo','Restablecido');
        });
    } catch(_){ }
}

async function deleteColumnMapping(){
    try{
        // Obtener el cliente ID desde el dropdown O desde el atributo del overlay
        const overlay = document.getElementById('mappingOverlay');
        const sel = document.getElementById('clientSelectorGrouping');
        let clientId = overlay?.getAttribute('data-current-client-id') || sel?.value;

        if (!clientId){
            showToast('Info','Seleccioná un cliente');
            return;
        }

        const ok = await showConfirmation('¿Seguro que querés borrar el mapeo de este cliente?');
        if (!ok) return;

        const r = await fetch(`/api/clientes/${clientId}/column_mapping`, { method:'DELETE' });
        const d = await r.json();
        if (d.success === false){ showToast('Error','No se pudo borrar','error'); return; }
        ['map_pieza','map_descripcion','map_origen','map_cantidad','map_valor_unitario','map_peso_unitario'].forEach(id=>{ const el=document.getElementById(id); if(el) el.value=''; });
        showToast('Listo','Mapeo borrado');

        // Recargar la lista de clientes si estamos en esa sección
        const clientsSection = document.getElementById('clientsSection');
        if (clientsSection && !clientsSection.classList.contains('hidden')){
            loadClientes();
        }
    } catch(_){ showToast('Error','No se pudo borrar','error'); }
}

// Teclado: Enter=Guardar, Esc=Cerrar dentro del modal
document.addEventListener('keydown', (e)=>{
    const overlay = document.getElementById('mappingOverlay');
    if (!overlay || !overlay.classList.contains('active')) return;
    if (e.key === 'Enter') { e.preventDefault(); saveColumnMapping(); }
    if (e.key === 'Escape') { e.preventDefault(); hideMappingModal(); }
});

function restoreUiPreferences() {
    try {
        const auto = localStorage.getItem('auto_group_toggle');
        if (auto !== null) {
            const el = document.getElementById('autoGroupToggle');
            if (el) el.checked = (auto === '1');
        }
        const lastClient = localStorage.getItem('last_client_id');
        if (lastClient) {
            const sel = document.getElementById('clientSelectorGrouping');
            if (sel && [...sel.options].some(o=>o.value===lastClient)) sel.value = lastClient;
            try {
                const uploadSel = document.getElementById('clientSelector');
                if (uploadSel && [...uploadSel.options].some(o=>o.value===lastClient)) uploadSel.value = lastClient;
            } catch(_){}
        }
        const lastMode = localStorage.getItem('last_mode');
        const validModes = ['upload', 'clients', 'catalog', 'manual'];
        if (lastMode && validModes.includes(lastMode)) {
            switchMode(lastMode);
        } else {
            // Default UX Overhaul v2: arrancar en 'upload' (acción principal del producto)
            // en vez del manual largo que abrumaba al novato.
            switchMode('upload');
        }
        // Restaurar toggle usar mapeo
        const useMap = document.getElementById('useMappingToggleUpload');
        if (useMap) useMap.checked = (localStorage.getItem('use_mapping_toggle') === '1');
    } catch (_) {}
}

// Utilidad: debounce simple para evitar reordenar en exceso
function debounce(fn, delay = 200) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

function debouncedRegroupAllItems() {
    if (!window.__debounceRegroup) {
        window.__debounceRegroup = debounce(regroupAllItems, 200);
    }
    window.__debounceRegroup();
}

// Función para cerrar el hero de bienvenida y recordar la decisión
function closeWelcome() {
    const banner = document.getElementById('welcomeBanner');
    if (banner) {
        banner.style.transform = 'translateY(-100%)';
        banner.style.opacity = '0';
        setTimeout(() => {
            banner.style.display = 'none';
        }, 300);
    }
    try { localStorage.setItem('cdi_welcome_dismissed', '1'); } catch (_) {}
}

// Si el usuario ya cerró el hero antes, no lo volvemos a mostrar.
// (Lo dejamos visible en cada visita las primeras veces para que lo vea
// quien recién está aprendiendo el flujo.)
function maybeHideWelcomeHero() {
    try {
        if (localStorage.getItem('cdi_welcome_dismissed') === '1') {
            const banner = document.getElementById('welcomeBanner');
            if (banner) banner.style.display = 'none';
        }
    } catch (_) {}
}

// Event listeners
function setupEventListeners() {
    // Botones básicos
    addItemBtn.addEventListener('click', addItem);
    clearBtn.addEventListener('click', clearForm);
    
    // Formularios
    operationForm.addEventListener('submit', handleSubmit);
    uploadForm.addEventListener('submit', handleUpload);
    // pdfForm eliminado: flujo unificado en handleUpload

    // Mode cards
    manualModeCard.addEventListener('click', () => switchMode('manual'));
    uploadModeCard.addEventListener('click', () => switchMode('upload'));
    // pdfModeCard puede no existir
    if (pdfModeCard) pdfModeCard.addEventListener('click', () => switchMode('pdf'));
    clientsModeCard.addEventListener('click', () => switchMode('clients'));
    const catalogModeCard = document.getElementById('catalogModeCard');
    if (catalogModeCard) catalogModeCard.addEventListener('click', () => switchMode('catalog'));
    if (refreshClientsBtn) refreshClientsBtn.addEventListener('click', populateClientSelect);
    if (viewHistoryBtn) viewHistoryBtn.addEventListener('click', showHistoryModal);
    const editMappingBtn = document.getElementById('editMappingBtn');
    if (editMappingBtn) editMappingBtn.addEventListener('click', openMappingModal);
    const downloadTemplateBtn = document.getElementById('downloadClientTemplateBtn');
    if (downloadTemplateBtn) downloadTemplateBtn.addEventListener('click', downloadClientTemplate);
    const downloadAvgBlankBtn = document.getElementById('downloadAvgBlankBtn');
    if (downloadAvgBlankBtn) downloadAvgBlankBtn.addEventListener('click', downloadAvgBlankTemplate);

    // Preferencias UI
    const autoToggle = document.getElementById('autoGroupToggle');
    if (autoToggle) {
        autoToggle.addEventListener('change', () => {
            try { localStorage.setItem('auto_group_toggle', autoToggle.checked ? '1' : '0'); } catch(_) {}
        });
    }
    const clientSel = document.getElementById('clientSelectorGrouping');
    if (clientSel) {
        clientSel.addEventListener('change', () => {
            try { localStorage.setItem('last_client_id', clientSel.value || ''); } catch(_) {}
            try {
                const uploadSel = document.getElementById('clientSelector');
                if (uploadSel && [...uploadSel.options].some(o=>o.value===clientSel.value)) {
                    uploadSel.value = clientSel.value;
                }
            } catch(_) {}
            refreshMappingStatusHint();
        });
    }
    // Persistir y restaurar toggle "Usar mapeo" de la subida
    const useMap = document.getElementById('useMappingToggleUpload');
    if (useMap){
        try { useMap.checked = (localStorage.getItem('use_mapping_toggle') === '1'); } catch(_) {}
        useMap.addEventListener('change', ()=>{
            try { localStorage.setItem('use_mapping_toggle', useMap.checked ? '1' : '0'); } catch(_) {}
            refreshMappingStatusHint();
        });
    }
    // Auto validar
    const autoVal = document.getElementById('autoValidateToggle');
    if (autoVal) {
        autoVal.checked = (localStorage.getItem('auto_validate_toggle') === '1');
        autoVal.addEventListener('change', ()=>{
            try { localStorage.setItem('auto_validate_toggle', autoVal.checked ? '1' : '0'); } catch(_) {}
        });
    }
    // Descargar CSV de errores
    const dlBtn = document.getElementById('downloadErrorsBtn');
    if (dlBtn) dlBtn.addEventListener('click', downloadErrorsCsv);
    const extraRules = document.getElementById('extraRulesToggle');
    if (extraRules){
        try { extraRules.checked = (localStorage.getItem('extra_rules_toggle') === '1'); } catch(_){ }
        extraRules.addEventListener('change', ()=>{
            try { localStorage.setItem('extra_rules_toggle', extraRules.checked ? '1' : '0'); } catch(_){ }
            // revalidar si está visible
            try { if (!window.__debouncedValidate) window.__debouncedValidate = debounce(validateCurrentItems, 400); window.__debouncedValidate(); } catch(_){ }
        });
    }

    // Limpiar borrador
    const clearDraftBtn = document.getElementById('clearDraftBtn');
    if (clearDraftBtn) clearDraftBtn.addEventListener('click', clearGroupingDraft);

    // Event listener para toggle input manual de origen en batch bar
    const bulkOrigenSelect = document.getElementById('bulkOrigenSelect');
    if (bulkOrigenSelect) {
        bulkOrigenSelect.addEventListener('change', (e) => {
            const manualInput = document.getElementById('bulkOrigenManual');
            if (manualInput) {
                if (e.target.value === '__otro__') {
                    manualInput.classList.remove('hidden');
                    manualInput.focus();
                } else {
                    manualInput.classList.add('hidden');
                    manualInput.value = '';
                }
            }
        });
    }

    // Atajos en tabla de agrupación: Enter siguiente campo, Esc cancelar edición (blur)
    document.addEventListener('keydown', (e)=>{
        const active = document.activeElement;
        if (!active || !active.classList || !active.classList.contains('edit-input')) return;
        if (e.key === 'Enter') {
            e.preventDefault();
            const inputs = Array.from(document.querySelectorAll('.edit-input'));
            const idx = inputs.indexOf(active);
            if (idx >= 0 && idx < inputs.length - 1) {
                inputs[idx+1].focus();
                inputs[idx+1].select?.();
            }
        } else if (e.key === 'Escape') {
            e.preventDefault();
            active.blur();
        }
    });

    // Delegación: evitar handlers inline bloqueados por CSP
    document.addEventListener('input', (e) => {
        const el = e.target;
        if (el && el.classList && el.classList.contains('edit-input')) {
            try { updateField(el); } catch(_){}
        }
    });
    // Reagrupar también al perder foco por si el browser no dispara input
    document.addEventListener('change', (e) => {
        const el = e.target;
        if (el && el.classList && el.classList.contains('edit-input')) {
            try { updateField(el); debouncedRegroupAllItems(); } catch(_){}
        }
    });

    document.addEventListener('click', (e) => {
        const suggestBtn = e.target && e.target.closest ? e.target.closest('.btn-suggest-ncm') : null;
        if (suggestBtn) { e.preventDefault(); try { suggestNcm(suggestBtn); } catch(_){} return; }
        const infoBtn = e.target && e.target.closest ? e.target.closest('.btn-ncm-info') : null;
        if (infoBtn) { e.preventDefault(); try { openNcmInfo(infoBtn); } catch(_){} return; }
        const ncmCompletoBtn = e.target && e.target.closest ? e.target.closest('.btn-ncm-completo') : null;
        if (ncmCompletoBtn) { e.preventDefault(); try { const ncm = ncmCompletoBtn.dataset.ncm; mostrarDatosCompletos(ncm); } catch(_){} return; }
        const assignBtn = e.target && e.target.closest ? e.target.closest('#assignSelectedBtn') : null;
        if (assignBtn) { e.preventDefault(); try { assignNcmToSelected(); } catch(_){} return; }
        const cancelBtn = e.target && e.target.closest ? e.target.closest('#cancelGroupingBtn') : null;
        if (cancelBtn) { e.preventDefault(); try { cancelGrouping(); } catch(_){} return; }
        const dlLastBtn = e.target && e.target.closest ? e.target.closest('#downloadLastBtn') : null;
        if (dlLastBtn) { e.preventDefault(); try { downloadLastGenerated(); } catch(_){} return; }
        const validateBtn = e.target && e.target.closest ? e.target.closest('#validateItemsBtn') : null;
        if (validateBtn) { e.preventDefault(); try { validateCurrentItems(); } catch(_){} return; }
        const verifyBtn = e.target && e.target.closest ? e.target.closest('#verifyNCMBtn') : null;
        if (verifyBtn) { e.preventDefault(); try { verifyNCMManually(); } catch(_){} return; }
        const enrichVuceBtn = e.target && e.target.closest ? e.target.closest('#enrichVuceBtn') : null;
        if (enrichVuceBtn) { e.preventDefault(); try { enrichItemsWithVuce(); } catch(_){} return; }
        const genBtn = e.target && e.target.closest ? e.target.closest('#generateGroupedBtn') : null;
        if (genBtn) { e.preventDefault(); try { generateGroupedExcel(); } catch(_){} return; }
        const mariaBtn = e.target && e.target.closest ? e.target.closest('#generateMariaBtn') : null;
        if (mariaBtn) { e.preventDefault(); try { generateMariaTxt(); } catch(_){} return; }

        // Event listeners para botones calculadora y plantillas
        const calcBtn = e.target && e.target.closest ? e.target.closest('#openCalculatorBtn') : null;
        if (calcBtn) {
            e.preventDefault();
            try {
                if (typeof openCalculator === 'function') {
                    openCalculator();
                } else {
                    console.error('❌ openCalculator no está definida');
                    showToast('Error', 'Calculadora no disponible', 'error');
                }
            } catch(err) {
                console.error('❌ Error al abrir calculadora:', err);
            }
            return;
        }
        const templatesBtn = e.target && e.target.closest ? e.target.closest('#openTemplatesBtn') : null;
        if (templatesBtn) { e.preventDefault(); try { openTemplates(); } catch(_){} return; }

        // Delegación de acciones en tarjetas de clientes
        const actEl = e.target && e.target.closest ? e.target.closest('[data-action]') : null;
        if (actEl) {
            const action = actEl.getAttribute('data-action');
            const cid = actEl.getAttribute('data-client-id');
            const cname = actEl.getAttribute('data-client-name') || '';
            if (!cid) return;
            e.preventDefault();
            try {
                if (action === 'use-client') return useClientFromCard(cid);
                if (action === 'mapping-client') return openMappingForClient(cid, cname);
                if (action === 'template-client') return downloadClientTemplateForCard(cid, cname);
            } catch(_){}
        }
    });
}

async function downloadClientTemplate(){
    try{
        const sel = document.getElementById('clientSelectorGrouping');
        if (!sel || !sel.value){ showToast('Info','Seleccioná un cliente'); return; }
        const r = await fetch(`/api/clientes/${sel.value}/plantilla`, { method:'POST' });
        const d = await r.json();
        if (!d.success){ showToast('Error', d.detail || 'No se pudo generar la plantilla', 'error'); return; }
        const a = document.createElement('a');
        a.href = d.download_url;
        a.download = d.filename || 'plantilla_cliente.xlsx';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        showToast('Listo', 'Plantilla generada');
    } catch(e){ showToast('Error','No se pudo descargar la plantilla','error'); }
}

async function downloadAvgBlankTemplate(){
    try{
        const r = await fetch('/api/plantillas/avg_blanco');
        const d = await r.json();
        if (!d.success){ showToast('Error', d.detail || 'No se pudo generar la plantilla AVG', 'error'); return; }
        const a = document.createElement('a');
        a.href = d.download_url;
        a.download = d.filename || 'PLANTILLA_AVG.xlsx';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        showToast('Listo', 'Plantilla AVG generada');
    } catch(e){ showToast('Error','No se pudo descargar la plantilla AVG','error'); }
}

// Configurar drag & drop
function setupFileDropZones() {
    const uploadArea = uploadForm.querySelector('.upload-area');
    const pdfUploadArea = null;

    // Excel upload area
    setupDropZone(uploadArea, document.getElementById('excelFile'));
    
    // PDF unificado en upload Excel/PDF
}

function setupDropZone(area, fileInput) {
    area.addEventListener('dragover', (e) => {
        e.preventDefault();
        area.classList.add('file-selected');
    });

    area.addEventListener('dragleave', (e) => {
        e.preventDefault();
        area.classList.remove('file-selected');
    });

    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.classList.remove('file-selected');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateUploadAreaText(area, files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            updateUploadAreaText(area, e.target.files[0]);
        }
    });
}

function updateUploadAreaText(area, file) {
    const h4 = area.querySelector('h4');
    const p = area.querySelector('p');
    
    h4.textContent = `Archivo seleccionado: ${file.name}`;
    p.textContent = `Tamaño: ${(file.size / 1024 / 1024).toFixed(2)} MB`;
    area.classList.add('file-selected');
}

// Cambiar entre modos
function switchMode(mode) {

    // Limpiar estados (incluye sincronizar aria-pressed para a11y)
    document.querySelectorAll('.mode-option').forEach(btn => {
        btn.classList.remove('active');
        if (btn.hasAttribute('aria-pressed')) {
            btn.setAttribute('aria-pressed', 'false');
        }
    });
    const _catalogModeCard = document.getElementById('catalogModeCard');

    operationForm.classList.add('hidden');
    uploadForm.classList.add('hidden');
    if (pdfForm) pdfForm.classList.add('hidden');
    clientsSection.classList.add('hidden');
    const _catalogSection = document.getElementById('catalogSection');
    if (_catalogSection) _catalogSection.classList.add('hidden');
    // Asegurar que se oculte la pantalla de agrupación al cambiar de sección
    try { document.getElementById('groupingSection')?.classList.add('hidden'); resetGroupingUI(); } catch(_) {}
    
    hideResults();
    hideError();

    // Helper para marcar un mode-card como activo (sincroniza aria-pressed)
    const setActive = (card) => {
        if (!card) return;
        card.classList.add('active');
        if (card.hasAttribute('aria-pressed')) {
            card.setAttribute('aria-pressed', 'true');
        }
    };

    // Activar modo seleccionado
    if (mode === 'manual') {
        setActive(manualModeCard);
        operationForm.classList.remove('hidden');
        // Si la tabla manual está vacía, insertar el primer item ahora
        // (antes se hacía en DOMContentLoaded; lo movimos para no abrumar
        // al usuario que solo quería subir un PDF — UX Overhaul Fase 0).
        try {
            if (itemsContainer && itemsContainer.children.length === 0 && typeof addItem === 'function') {
                addItem();
            }
        } catch (_) {}
    } else if (mode === 'upload') {
        setActive(uploadModeCard);
        uploadForm.classList.remove('hidden');
    } else if (mode === 'clients') {
        setActive(clientsModeCard);
        clientsSection.classList.remove('hidden');
        loadClientes();
    } else if (mode === 'catalog') {
        setActive(_catalogModeCard);
        if (_catalogSection) _catalogSection.classList.remove('hidden');
        try { backToCatalogList(); } catch (_) {}
        loadCatalogVendors();
    }

    // Guardar preferencia de modo
    try { localStorage.setItem('last_mode', mode); } catch (_) {}
}

function resetGroupingUI(){
    try {
        // Limpiar tabla
        const body = document.getElementById('itemsToGroup');
        if (body) body.innerHTML = '';
        // Ocultar botón de validación
        const validateBtn = document.getElementById('validateItemsBtn');
        if (validateBtn) validateBtn.style.display = 'none';
        // Ocultar panel de validación
        const panel = document.getElementById('validationPanel');
        if (panel) panel.classList.add('hidden');
        // Reset indicadores
        const stats = document.getElementById('groupingStats');
        if (stats) {
            stats.innerHTML = `
                <div class="grouping-stat"><div class="grouping-stat-number">0</div><div class="grouping-stat-label">Grupos Detectados</div></div>
                <div class="grouping-stat"><div class="grouping-stat-number">0</div><div class="grouping-stat-label">Items Total</div></div>
                <div class="grouping-stat"><div class="grouping-stat-number">$0</div><div class="grouping-stat-label">Valor Total</div></div>
            `;
        }
        // Borrar borrador
        localStorage.removeItem('grouping_draft');
    } catch(_) {}
}

// ============================================================================
// RATE LIMITING - Prevenir error 429 de Gemini API
// ============================================================================

// Función para verificar si puede hacer upload (rate limiting)
function canUploadNow() {
    const now = Date.now();
    const timeSinceLastUpload = now - lastUploadTimestamp;

    if (timeSinceLastUpload < UPLOAD_COOLDOWN_MS) {
        const waitSeconds = Math.ceil((UPLOAD_COOLDOWN_MS - timeSinceLastUpload) / 1000);
        return { allowed: false, waitSeconds };
    }

    return { allowed: true, waitSeconds: 0 };
}

// Actualizar timestamp y UI después de upload exitoso
function markUploadComplete() {
    lastUploadTimestamp = Date.now();
    updateUploadButtonState();
}

// Actualizar estado del botón de upload
function updateUploadButtonState() {
    const uploadBtn = document.querySelector('#uploadForm button[type="submit"]');

    if (!uploadBtn) return;

    const check = canUploadNow();

    if (!check.allowed) {
        // Deshabilitar botón y mostrar countdown
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `<i class="fas fa-clock"></i> Espera ${check.waitSeconds}s (límite API)`;
        uploadBtn.style.opacity = '0.6';
        uploadBtn.style.cursor = 'not-allowed';

        // Actualizar cada segundo
        if (uploadCooldownTimer) clearTimeout(uploadCooldownTimer);
        uploadCooldownTimer = setTimeout(() => updateUploadButtonState(), 1000);
    } else {
        // Habilitar botón
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-magic"></i> Procesar Archivo';
        uploadBtn.style.opacity = '1';
        uploadBtn.style.cursor = 'pointer';
    }
}

// ============================================================================
// HANDLERS DE UPLOAD
// ============================================================================

// Manejar subida de Excel
async function handleUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];

    if (!file) {
        showError('Por favor selecciona un archivo Excel');
        return;
    }

    // Validación de rate limiting (prevenir error 429 de Gemini)
    const rateLimitCheck = canUploadNow();
    if (!rateLimitCheck.allowed) {
        showError(`⏱️ Espera ${rateLimitCheck.waitSeconds} segundos antes de subir otro archivo (límite de API Gemini)`);
        return;
    }

    // Validación 1: Verificar límites de operaciones diarias
    const preCheck = checkDailyLimits('operation', 0);
    if (!preCheck.allowed) {
        showError(preCheck.reason);
        return;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const formData = new FormData();
        formData.append('file', file);
        try{
            const sel = document.getElementById('clientSelector');
            const useMap = document.getElementById('useMappingToggleUpload');
            const cid = sel && useMap && useMap.checked ? (sel.value || '') : '';
            if (cid) formData.append('client_id', cid);
        } catch(_){ }

        // Elegir endpoint según extensión
        const isPdf = file.name.toLowerCase().endsWith('.pdf');
        const endpoint = isPdf ? '/upload_pdf/public' : '/upload_excel/public';

        const response = await fetch(endpoint, { method: 'POST', body: formData });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail?.errors || data.detail || 'Error procesando Excel');
        }

        // Validación 2: Verificar límites con el número real de items procesados
        const itemsCount = (data.items || []).length;
        const finalCheck = checkDailyLimits('operation', itemsCount);
        if (!finalCheck.allowed) {
            showError(finalCheck.reason + ' El archivo fue procesado pero no se guardó.');
            return;
        }

        // Actualizar contador de uso diario
        updateDailyUsage('operation', itemsCount);

        // Marcar upload como completado para rate limiting
        markUploadComplete();

        // Guardar items para agrupación y mostrar pantalla de agrupación
        window.lastProcessedItems = data.items || [];
        
        // Guardar datos de operación extraídos por Gemini
        window.lastOperacionData = data.operacion || {};
        populateOperacionPanel(window.lastOperacionData);
        
        if (!window.lastProcessedItems.length) {
            showToast('Info', 'No se detectaron ítems. Revisa que el PDF/Excel tenga tabla (Model/Price/QTY).');
        }
        showSuccess(data, isPdf ? 'pdf' : 'excel');

    } catch (error) {
        showError(`Error procesando Excel: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Manejar subida de PDF
async function handlePdfUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];

    if (!file) {
        showError('Por favor selecciona un archivo PDF');
        return;
    }

    // Validación de rate limiting (prevenir error 429 de Gemini)
    const rateLimitCheck = canUploadNow();
    if (!rateLimitCheck.allowed) {
        showError(`⏱️ Espera ${rateLimitCheck.waitSeconds} segundos antes de subir otro PDF (límite de API Gemini)`);
        return;
    }

    // Validación 1: Verificar límites de operaciones diarias
    const preCheck = checkDailyLimits('operation', 0);
    if (!preCheck.allowed) {
        showError(preCheck.reason);
        return;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/upload_pdf/public', {
            method: 'POST',
            body: formData
        });

        // Validar respuesta antes de parsear
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.errors || errorData.detail || 'Error procesando PDF');
        }

        const data = await response.json();

        // Validación 2: Verificar límites con el número real de items procesados
        const itemsCount = (data.items || []).length;
        const finalCheck = checkDailyLimits('operation', itemsCount);
        if (!finalCheck.allowed) {
            showError(finalCheck.reason + ' El archivo fue procesado pero no se guardó.');
            return;
        }

        // Actualizar contador de uso diario
        updateDailyUsage('operation', itemsCount);

        // Marcar upload como completado para rate limiting
        markUploadComplete();

        // Guardar items para agrupación y mostrar pantalla de agrupación
        window.lastProcessedItems = data.items || [];
        showSuccess(data, 'pdf');

    } catch (error) {
        showError(`Error procesando PDF: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Manejar formulario manual
async function handleSubmit(e) {
    e.preventDefault();

    try {
        // Validar que el usuario tenga token de autenticación
        const token = localStorage.getItem('access_token');
        if (!token) {
            showToast('Error', 'Sesión expirada. Por favor inicia sesión nuevamente.', 'error');
            setTimeout(() => window.location.href = '/login.html', 1500);
            return;
        }

        const payload = collectFormData();
        const itemsCount = (payload.items || []).length;

        // Validación 1: Verificar límites antes de enviar
        const preCheck = checkDailyLimits('operation', itemsCount);
        if (!preCheck.allowed) {
            showError(preCheck.reason);
            return;
        }

    } catch (error) {
        showError(error.message);
        return;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const payload = collectFormData();

        const response = await fetch('/process_operation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Enviar cookies
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            // Manejo específico de errores de autenticación
            if (response.status === 401 || response.status === 403) {
                showToast('Error', 'Sesión expirada o sin permisos. Redirigiendo...', 'error');
                // Limpiar localStorage (cookies se manejan en backend)
                localStorage.removeItem('user_plan');
                localStorage.removeItem('user_roles');
                setTimeout(() => window.location.href = '/login.html', 1500);
                hideLoading();
                return;
            }
            throw new Error(data.detail?.errors || data.detail || 'Error procesando operación');
        }

        // Actualizar contador de uso diario
        const itemsCount = (payload.items || []).length;
        updateDailyUsage('operation', itemsCount);

        // Para manual, usar los items del formulario para agrupación
        window.lastProcessedItems = payload.items;
        showSuccess(data, 'manual');

    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// Recopilar datos del formulario
function collectFormData() {
    const operationId = document.getElementById('operationId').value.trim();

    if (!operationId) {
        throw new Error('El código de operación es obligatorio');
    }

    const items = [];
    const itemElements = document.querySelectorAll('.item');

    itemElements.forEach(item => {
        const itemNumber = item.dataset.itemId;

        const itemData = {
            pieza: document.getElementById(`pieza_${itemNumber}`).value.trim(),
            descripcion: document.getElementById(`descripcion_${itemNumber}`).value.trim(),
            origen: document.getElementById(`origen_${itemNumber}`).value.trim(),
            peso_unitario: parseFloat(document.getElementById(`peso_unitario_${itemNumber}`).value),
            cantidad: parseFloat(document.getElementById(`cantidad_${itemNumber}`).value),
            valor_unitario: parseFloat(document.getElementById(`valor_unitario_${itemNumber}`).value),
        };

        // Campos opcionales
        const marca = document.getElementById(`marca_${itemNumber}`).value.trim();
        const modelo = document.getElementById(`modelo_${itemNumber}`).value.trim();
        const version = document.getElementById(`version_${itemNumber}`).value.trim();
        const otros = document.getElementById(`otros_${itemNumber}`).value;
        const separador = document.getElementById(`separador_${itemNumber}`).value;
        const ventaja = document.getElementById(`ventaja_${itemNumber}`).value;

        if (marca) itemData.marca = marca;
        if (modelo) itemData.modelo = modelo;
        if (version) itemData.version = version;
        if (otros && otros !== '') itemData.otros = parseFloat(otros);
        if (separador && separador !== '') itemData.separador = parseFloat(separador);
        if (ventaja && ventaja !== '') itemData.ventaja = parseFloat(ventaja);

        // Validaciones básicas
        if (!itemData.pieza || !itemData.descripcion || !itemData.origen) {
            throw new Error(`Item ${itemNumber}: Los campos Pieza, Descripción y Origen son obligatorios`);
        }

        if (itemData.peso_unitario <= 0 || itemData.cantidad <= 0 || itemData.valor_unitario <= 0) {
            throw new Error(`Item ${itemNumber}: Peso unitario, cantidad y valor unitario deben ser mayores a cero`);
        }

        items.push(itemData);
    });

    if (items.length === 0) {
        throw new Error('Debe agregar al menos un item');
    }

    return {
        operation_id: operationId,
        items: items
    };
}

// Agregar item
function addItem() {
    itemCounter++;
    const itemHTML = createItemHTML(itemCounter);
    itemsContainer.insertAdjacentHTML('beforeend', itemHTML);
}

// Crear HTML para item
function createItemHTML(itemNumber) {
    return `
        <div class="item" data-item-id="${itemNumber}">
            <div class="item-header">
                <span class="item-number">Item ${itemNumber}</span>
                <button type="button" class="remove-item" onclick="removeItem(${itemNumber})">
                    <i class="fas fa-times"></i> Remover
                </button>
            </div>
            <div class="item-grid">
                <div class="item-field">
                    <label for="pieza_${itemNumber}">Pieza (NCM)</label>
                    <input type="text" id="pieza_${itemNumber}" name="pieza_${itemNumber}" required placeholder="Ej: 84713010">
                </div>
                <div class="item-field">
                    <label for="descripcion_${itemNumber}">Descripción</label>
                    <input type="text" id="descripcion_${itemNumber}" name="descripcion_${itemNumber}" required placeholder="Ej: Computadora portátil">
                </div>
                <div class="item-field">
                    <label for="origen_${itemNumber}">Origen</label>
                    <input type="text" id="origen_${itemNumber}" name="origen_${itemNumber}" required placeholder="Ej: CN">
                </div>
                <div class="item-field">
                    <label for="peso_unitario_${itemNumber}">Peso Unitario (kg)</label>
                    <input type="number" id="peso_unitario_${itemNumber}" name="peso_unitario_${itemNumber}" step="0.001" min="0" required placeholder="2.5">
                </div>
                <div class="item-field">
                    <label for="cantidad_${itemNumber}">Cantidad</label>
                    <input type="number" id="cantidad_${itemNumber}" name="cantidad_${itemNumber}" step="0.01" min="0" required placeholder="10">
                </div>
                <div class="item-field">
                    <label for="valor_unitario_${itemNumber}">Valor Unitario (USD)</label>
                    <input type="number" id="valor_unitario_${itemNumber}" name="valor_unitario_${itemNumber}" step="0.01" min="0" required placeholder="1500.00">
                </div>
                <div class="item-field">
                    <label for="marca_${itemNumber}">Marca (opcional)</label>
                    <input type="text" id="marca_${itemNumber}" name="marca_${itemNumber}" placeholder="Apple">
                </div>
                <div class="item-field">
                    <label for="modelo_${itemNumber}">Modelo (opcional)</label>
                    <input type="text" id="modelo_${itemNumber}" name="modelo_${itemNumber}" placeholder="MacBook Pro">
                </div>
                <div class="item-field">
                    <label for="version_${itemNumber}">Versión (opcional)</label>
                    <input type="text" id="version_${itemNumber}" name="version_${itemNumber}" placeholder="14.2">
                </div>
                <div class="item-field">
                    <label for="otros_${itemNumber}">Otros (opcional)</label>
                    <input type="number" id="otros_${itemNumber}" name="otros_${itemNumber}" step="0.01" placeholder="100.00">
                </div>
                <div class="item-field">
                    <label for="separador_${itemNumber}">Separador (opcional)</label>
                    <input type="number" id="separador_${itemNumber}" name="separador_${itemNumber}" step="0.01" placeholder="50.00">
                </div>
                <div class="item-field">
                    <label for="ventaja_${itemNumber}">Ventaja (opcional)</label>
                    <input type="number" id="ventaja_${itemNumber}" name="ventaja_${itemNumber}" step="0.01" placeholder="25.00">
                </div>
            </div>
        </div>
    `;
}

// Remover item
function removeItem(itemNumber) {
    const item = document.querySelector(`[data-item-id="${itemNumber}"]`);
    if (item) {
        item.remove();
        reorderItems();
    }
}

// Reordenar items
function reorderItems() {
    const items = document.querySelectorAll('.item');
    itemCounter = items.length;

    items.forEach((item, index) => {
        const newNumber = index + 1;
        item.dataset.itemId = newNumber;
        item.querySelector('.item-number').textContent = `Item ${newNumber}`;

        const inputs = item.querySelectorAll('input');
        inputs.forEach(input => {
            const fieldName = input.name.split('_')[0];
            input.id = `${fieldName}_${newNumber}`;
            input.name = `${fieldName}_${newNumber}`;
        });

        const removeBtn = item.querySelector('.remove-item');
        removeBtn.setAttribute('onclick', `removeItem(${newNumber})`);
    });
}

// Limpiar formulario
function clearForm() {
    if (confirm('¿Estás seguro de que quieres limpiar todos los datos?')) {
        operationForm.reset();
        itemsContainer.innerHTML = '';
        itemCounter = 0;
        addItem();
        hideResults();
        hideError();
    }
}

// Mostrar/ocultar elementos
// Estado del loader con etapas progresivas (UX Overhaul Fase 4).
// El backend (Gemini Vision) no nos da progress events vía fetch, así que
// avanzamos las etapas por timing aproximado para que el usuario vea que algo
// está pasando y no piense que la app se colgó.
let _loadingTimers = [];
function _resetLoadingSteps() {
    document.querySelectorAll('#loadingSteps li').forEach(li => {
        li.classList.remove('active', 'done');
    });
}
function _setStep(stepKey, state) {
    const li = document.querySelector(`#loadingSteps li[data-step="${stepKey}"]`);
    if (!li) return;
    li.classList.remove('active', 'done');
    if (state) li.classList.add(state);
}

function showLoading() {
    if (!loading) return;
    loading.classList.remove('hidden');
    _resetLoadingSteps();
    _setStep('read', 'active');
    _loadingTimers.forEach(t => clearTimeout(t));
    _loadingTimers = [
        setTimeout(() => { _setStep('read', 'done'); _setStep('extract', 'active'); }, 2200),
        setTimeout(() => { _setStep('extract', 'done'); _setStep('finish', 'active'); }, 9000),
    ];
}

function hideLoading() {
    if (!loading) return;
    loading.classList.add('hidden');
    _loadingTimers.forEach(t => clearTimeout(t));
    _loadingTimers = [];
    _resetLoadingSteps();
}

// === NUEVA FUNCIONALIDAD: MOSTRAR AGRUPACIÓN ===
function showGrouping(items, sourceType) {
    
    // Ocultar formularios principales
    operationForm.classList.add('hidden');
    uploadForm.classList.add('hidden');
    if (pdfForm) pdfForm.classList.add('hidden');
    
    // Mostrar sección de agrupación
    document.getElementById('groupingSection').classList.remove('hidden');

    // Tour V4: aviso contextual para que el coach mark/tour avance al paso
    // de "revisión" sólo cuando el usuario realmente subió algo (sin demo data).
    try {
        window.dispatchEvent(new CustomEvent('cdi:grouping-shown', {
            detail: { items: items?.length || 0, sourceType }
        }));
    } catch (_) {}

    // Agrupar automáticamente por código arancelario
    const groups = groupItemsByTariff(items);
    displayItemsForGrouping(items, groups);
    
    // Asegurar que se muestre botón de notas en cada fila
    addNotesButtonsToRows();

    // ── Smart Task Panel: análisis post-carga ───────────────────
    setTimeout(() => {
        try {
            // Obtener vendor del campo real de la operación (id fijo)
            const vendorEl = document.getElementById('op_vendedor_nombre');
            const vendor = vendorEl?.value?.trim() || window.lastVendorName || '';
            analyzeAndShowTaskPanel(items, vendor);
        } catch(e) { /* silencioso */ }
    }, 600);


    // Autovalidar al entrar si está activado
    try {
        const auto = document.getElementById('autoValidateToggle');
        if (auto && auto.checked) {
            if (!window.__debouncedValidate) { window.__debouncedValidate = debounce(validateCurrentItems, 400); }
            window.__debouncedValidate();
        }
    } catch(_) {}

    // Scroll a sección de agrupación
    document.getElementById('groupingSection').scrollIntoView({ behavior: 'smooth' });

    // Autosave: restaurar borrador si existe
    try {
        const draft = localStorage.getItem('grouping_draft');
        if (draft) {
            const arr = JSON.parse(draft);
            if (Array.isArray(arr) && arr.length === items.length) {
                // aplicar valores al DOM
                const rows = document.querySelectorAll('.item-grouping-row');
                arr.forEach((it, i)=>{
                    const row = rows[i]; if (!row) return;
                    const set = (sel, val)=>{ const el=row.querySelector(sel); if(el&&val!=null&&val!==undefined) el.value = val; };
                    set('[data-field="pieza"]', it.pieza);
                    set('[data-field="descripcion"]', it.descripcion);
                    set('[data-field="origen"]', it.origen);
                    set('[data-field="cantidad"]', it.cantidad);
                    set('[data-field="valor_unitario"]', it.valor_unitario);
                    set('[data-field="peso_unitario"]', it.peso_unitario);
                });
                debouncedRegroupAllItems();
            }
        }
    } catch(_) {}
}

function groupItemsByTariff(items) {
    const groups = {};
    
    items.forEach(item => {
        const tariffCode = item.pieza.substring(0, 4); // Primeros 4 dígitos
        if (!groups[tariffCode]) {
            groups[tariffCode] = [];
        }
        groups[tariffCode].push(item);
    });
    
    return groups;
}

/**
 * PRIORIDAD 2: Validar formato de NCM según estándares MERCOSUR/AFIP
 * @param {string} ncm - Código NCM a validar
 * @returns {Object} { valido: boolean, error: string, ncmLimpio: string }
 */
function validarFormatoNCM(ncm) {
    if (!ncm || typeof ncm !== 'string' || ncm.trim() === '') {
        return {
            valido: true,
            error: '',
            ncmLimpio: ''
        };
    }

    // Remover puntos, espacios, guiones
    const ncmLimpio = ncm.replace(/[.\s\-]/g, '');

    // Debe contener solo dígitos
    if (!/^\d+$/.test(ncmLimpio)) {
        return {
            valido: false,
            error: 'NCM debe contener solo números (ej: 290519 o 2905.19.00)',
            ncmLimpio: ''
        };
    }

    // Debe tener entre 6 y 8 dígitos
    if (ncmLimpio.length < 6) {
        return {
            valido: false,
            error: `NCM debe tener mínimo 6 dígitos (ingresaste ${ncmLimpio.length})`,
            ncmLimpio: ''
        };
    }

    if (ncmLimpio.length > 8) {
        return {
            valido: false,
            error: `NCM debe tener máximo 8 dígitos (ingresaste ${ncmLimpio.length})`,
            ncmLimpio: ''
        };
    }

    // Validar que el capítulo (primeros 2 dígitos) esté en rango válido 01-97
    const capitulo = parseInt(ncmLimpio.substring(0, 2));
    if (capitulo < 1 || capitulo > 97) {
        return {
            valido: false,
            error: `Capítulo NCM inválido (${capitulo.toString().padStart(2, '0')}). Debe estar entre 01 y 97`,
            ncmLimpio: ''
        };
    }

    return {
        valido: true,
        error: '',
        ncmLimpio: ncmLimpio
    };
}

/**
 * Auto-formatear NCM al salir del campo (evento blur)
 * Limpia puntos, espacios y guiones, actualizando el campo visual
 * @param {HTMLInputElement} input - Input del NCM
 */
function autoFormatearNCM(input) {
    const ncm = input.value.trim();
    if (!ncm) return;

    const validacion = validarFormatoNCM(ncm);

    if (validacion.valido) {
        // Auto-formatear: actualizar campo con NCM limpio
        if (ncm !== validacion.ncmLimpio) {
            input.value = validacion.ncmLimpio;
            // Feedback visual sutil (borde verde por 1.5 segundos)
            input.style.borderColor = '#10b981';
            setTimeout(() => {
                input.style.borderColor = '';
            }, 1500);
        }
        // Limpiar error si había uno previo
        input.classList.remove('input-error');
    } else {
        // Marcar error visual
        input.classList.add('input-error');
        input.style.borderColor = '#dc2626';
    }
}

/**
 * CÁLCULO DE TRIBUTOS - VERSIÓN 2.0 (03/10/2025)
 *
 * Calcula tributos reales consultando /api/ncm/{codigo}/completo para cada NCM único.
 * Usa rates AFIP oficiales: derechos importación + IVA + tasa estadística.
 *
 * FLUJO:
 * 1. Extraer NCMs únicos de items
 * 2. Fetch paralelo de alícuotas desde /api/ncm/{codigo}/completo
 * 3. Calcular tributos ponderados: Σ(CIF_item × alícuota_NCM)
 * 4. Fallback defensivo a 35% promedio si:
 *    - API error
 *    - NCM sin rates
 *    - Network timeout
 *
 * @param {Array} items - Items con NCM (campo "pieza")
 * @param {Number} totalFOB - Total FOB de la operación
 * @returns {Promise<Object>} { tributosReales, esEstimado, detalleNCMs }
 */
async function calcularTributosReales(items, totalFOB) {
    try {
        // 1. Extraer NCMs únicos (campo "pieza" contiene el NCM)
        // IMPORTANTE: Validar formato antes de procesar
        const ncmsUnicos = [...new Set(items.map(item => item.pieza))]
            .filter(ncm => {
                if (!ncm) return false;
                const validacion = validarFormatoNCM(ncm);
                if (!validacion.valido) {
                    console.warn(`⚠️ NCM inválido ignorado: "${ncm}" - ${validacion.error}`);
                    return false;
                }
                return true;
            })
            .map(ncm => validarFormatoNCM(ncm).ncmLimpio); // Usar NCM limpio

        if (ncmsUnicos.length === 0) {
            console.warn('⚠️ No hay NCMs válidos, usando estimado 35%');
            return {
                tributosReales: totalFOB * 1.06 * 0.35,
                esEstimado: true,
                detalleNCMs: []
            };
        }

        // 2. Fetch paralelo de rates por NCM (máximo 5 segundos timeout)

        const ratesPromises = ncmsUnicos.map(ncm =>
            fetch(`/api/ncm/${ncm}/completo`, {
                credentials: 'include',
                signal: AbortSignal.timeout(5000)
            })
            .then(r => r.ok ? r.json() : null)
            .catch(err => {
                console.warn(`⚠️ Error fetching NCM ${ncm}:`, err.message);
                return null;
            })
        );

        const ratesResponses = await Promise.all(ratesPromises);

        // 3. Mapear NCM → alícuotas
        const ratesPorNCM = {};
        ncmsUnicos.forEach((ncm, idx) => {
            if (ratesResponses[idx] && ratesResponses[idx].alicuotas) {
                ratesPorNCM[ncm] = ratesResponses[idx].alicuotas;
            }
        });

        // 4. Calcular tributos ponderados por item
        let tributosTotal = 0;
        let itemsSinRates = 0;
        const detalleNCMs = [];

        items.forEach(item => {
            const rates = ratesPorNCM[item.pieza];
            if (rates) {
                const fobItem = (item.cantidad || 0) * (item.valor_unitario || 0);
                const cifItem = fobItem * 1.06; // CIF = FOB + 6%

                // Alícuotas desde VUCE (oficial)
                const derechos = rates.arancel_extrazona || 0;
                const iva = rates.iva || 0;
                const tasa = rates.estadistica || 0;
                const alicuotaTotal = (derechos + iva + tasa) / 100;

                const tributosItem = cifItem * alicuotaTotal;
                tributosTotal += tributosItem;

                // Guardar detalle para debug
                detalleNCMs.push({
                    ncm: item.pieza,
                    fob: fobItem,
                    tributos: tributosItem,
                    alicuota: (alicuotaTotal * 100).toFixed(1) + '%'
                });
            } else {
                itemsSinRates++;
            }
        });

        // 5. Fallback si faltan rates (usar estimado)
        if (itemsSinRates > 0) {
            const porcentajeSinRates = (itemsSinRates / items.length) * 100;
            if (porcentajeSinRates > 20) {
                console.warn(`⚠️ ${itemsSinRates} items (${porcentajeSinRates.toFixed()}%) sin rates, usando estimado 35%`);
                return {
                    tributosReales: totalFOB * 1.06 * 0.35,
                    esEstimado: true,
                    detalleNCMs: []
                };
            }
        }

        return {
            tributosReales: tributosTotal,
            esEstimado: false,
            detalleNCMs
        };

    } catch (error) {
        console.error('❌ Error calculando tributos reales:', error);
        // Fallback defensivo a estimado
        return {
            tributosReales: totalFOB * 1.06 * 0.35,
            esEstimado: true,
            detalleNCMs: []
        };
    }
}

/**
 * Actualizar preview de operación con cálculos y alertas
 */
async function updateOperationPreview(items, groups) {
    const preview = document.getElementById('operationPreview');
    if (!preview) return;

    const totalItems = items.length;
    const totalGroups = Object.keys(groups).length;
    const totalFOB = items.reduce((sum, item) => sum + (item.cantidad * item.valor_unitario), 0);

    // Verificar si hay cálculos personalizados guardados en las filas
    const rows = document.querySelectorAll('.item-grouping-row');
    let cifTotalCalculado = 0;
    let tributosTotalesCalculados = 0;
    let itemsConCalculoPersonalizado = 0;

    rows.forEach(row => {
        if (row.dataset.calculoAplicado === 'true') {
            // Esta fila tiene cálculo personalizado de la calculadora
            cifTotalCalculado += parseFloat(row.dataset.cifTotal || 0);
            tributosTotalesCalculados += parseFloat(row.dataset.tributosTotales || 0);
            itemsConCalculoPersonalizado++;
        }
    });

    // Decidir qué CIF usar
    let cifFinal, usandoCalculoPersonalizado;
    if (itemsConCalculoPersonalizado > 0 && itemsConCalculoPersonalizado === rows.length) {
        // TODOS los items tienen cálculo personalizado → usar suma de CIF calculados
        cifFinal = cifTotalCalculado;
        usandoCalculoPersonalizado = true;
    } else {
        // Usar CIF estimado genérico (FOB + 6%)
        cifFinal = totalFOB * 1.06;
        usandoCalculoPersonalizado = false;
    }

    // Actualizar resumen general (valores básicos)
    document.getElementById('preview-items').textContent = totalItems;
    document.getElementById('preview-groups').textContent = totalGroups;
    document.getElementById('preview-fob').textContent = `USD ${totalFOB.toLocaleString('es-AR', {maximumFractionDigits: 0})}`;
    document.getElementById('preview-cif').textContent = `USD ${cifFinal.toLocaleString('es-AR', {maximumFractionDigits: 0})}`;

    // FASE 2: Calcular tributos
    let resultadoTributos;

    if (usandoCalculoPersonalizado) {
        // Usar tributos calculados guardados
        resultadoTributos = {
            tributosReales: tributosTotalesCalculados,
            esEstimado: false,
            detalleNCMs: [],
            esPersonalizado: true
        };
    } else {
        // Calcular tributos reales con rates AFIP por NCM
        document.getElementById('preview-tributos').innerHTML = `
            <span style="color: #6c757d; font-style: italic;">Calculando tributos reales...</span>
        `;
        resultadoTributos = await calcularTributosReales(items, totalFOB);
    }

    if (resultadoTributos.esPersonalizado) {
        // Cálculo personalizado de la calculadora con flete/seguro custom
        document.getElementById('preview-tributos').innerHTML = `
            <span style="color: #8b5cf6; font-weight: bold;">USD ${resultadoTributos.tributosReales.toLocaleString('es-AR', {maximumFractionDigits: 0})}</span>
            <span style="cursor: help; margin-left: 5px; font-size: 1.2em; color: #8b5cf6;" title="Cálculo personalizado aplicado desde la Calculadora (flete/seguro custom)">🧮</span>
        `;
    } else if (resultadoTributos.esEstimado) {
        // Fallback: mostrar estimado con warning
        document.getElementById('preview-tributos').innerHTML = `
            <span style="color: #ffc107;">~USD ${resultadoTributos.tributosReales.toLocaleString('es-AR', {maximumFractionDigits: 0})}</span>
            <span style="cursor: help; margin-left: 5px; font-size: 1.2em;" title="Promedio 35% (rates AFIP no disponibles para algunos NCMs)">⚠️</span>
        `;
    } else {
        // Success: mostrar tributos reales con checkmark verde
        document.getElementById('preview-tributos').innerHTML = `
            <span style="color: #059669; font-weight: bold;">USD ${resultadoTributos.tributosReales.toLocaleString('es-AR', {maximumFractionDigits: 0})}</span>
            <span style="cursor: help; margin-left: 5px; font-size: 1.2em; color: #059669;" title="Rates AFIP reales por NCM (${resultadoTributos.detalleNCMs.length} NCMs consultados)">✅</span>
        `;

        // Log detalle en consola para debug
        if (resultadoTributos.detalleNCMs.length > 0) {
            console.table(resultadoTributos.detalleNCMs);
        }
    }

    // FASE 1: Guardar resultado en variable global para modal de breakdown
    window.lastTributosCalculation = {
        items: items,
        groups: groups,
        totalFOB: totalFOB,
        totalCIF: cifFinal,
        tributosTotal: resultadoTributos.tributosReales,
        detalleNCMs: resultadoTributos.detalleNCMs,
        esEstimado: resultadoTributos.esEstimado,
        timestamp: Date.now()
    };

    // Calcular detalle por NCM
    const groupsSummary = Object.entries(groups).map(([ncm, groupItems]) => {
        const groupFOB = groupItems.reduce((s, i) => s + (i.cantidad * i.valor_unitario), 0);
        // FIX: Evitar división por cero que causa NaN%
        const percentage = totalFOB > 0 ? (groupFOB / totalFOB) * 100 : 0;

        return {
            ncm,
            itemCount: groupItems.length,
            fob: groupFOB,
            percentage,
            // ALERTA: 1 item con >30% del valor → posible error de clasificación
            alert: groupItems.length === 1 && percentage > 30
        };
    }).sort((a, b) => b.fob - a.fob); // Ordenar por FOB descendente


    // Verificar si hay alertas para mostrar banner informativo
    const hayAlertas = groupsSummary.some(g => g.alert);

    // Renderizar banner informativo SI hay alertas
    let bannerHTML = '';
    if (hayAlertas) {
        bannerHTML = `
            <div class="alert-info-banner">
                ℹ️ <strong>Detección Automática de Clasificación</strong><br>
                Las filas marcadas con ⚠️ tienen <strong>1 item que representa más del 30% del valor total</strong>.
                <br><br>
                <strong>Esto puede indicar:</strong>
                <ul style="margin: 0.5rem 0 0.5rem 1.5rem; font-size: 0.9rem;">
                    <li>Productos diferentes agrupados en 1 línea (ej: "repuestos varios")</li>
                    <li>Descripción muy genérica que debería detallarse más</li>
                    <li>Clasificación NCM que podría dividirse en subcategorías</li>
                </ul>
                <small style="display: block; margin-top: 0.5rem;">
                    💡 <strong>Acción sugerida:</strong> Revisar si el item debería dividirse en múltiples líneas con NCMs más específicos.
                    <br>
                    ✅ <strong>¿Es un error?</strong> No necesariamente - puede ser válido si realmente es un solo producto.
                </small>
            </div>
        `;
    }

    // Renderizar tabla de detalle por NCM
    const tbody = document.getElementById('preview-ncm-breakdown');
    const tableContainer = tbody.closest('.preview-breakdown');

    // Insertar banner antes de la tabla (si no existe ya)
    const existingBanner = tableContainer.querySelector('.alert-info-banner');
    if (existingBanner) {
        existingBanner.remove();
    }
    if (bannerHTML) {
        tableContainer.insertAdjacentHTML('afterbegin', bannerHTML);
    }

    // Renderizar filas de la tabla con tooltip mejorado
    tbody.innerHTML = groupsSummary.map(g => `
        <tr class="${g.alert ? 'alert-row' : ''}">
            <td><strong>${g.ncm}</strong></td>
            <td>${g.itemCount}</td>
            <td>USD ${g.fob.toLocaleString('es-AR', {maximumFractionDigits: 0})}</td>
            <td>
                ${g.percentage.toFixed(1)}%
                ${g.alert ? `<span class="alert-icon" title="⚠️ NCM ${g.ncm}: ${g.percentage.toFixed(1)}% del total (umbral: >30%)

¿Es un error? NO necesariamente.
Revisar si debería dividirse en múltiples líneas.">⚠️</span>` : ''}
            </td>
        </tr>
    `).join('');

    // Mostrar preview
    preview.classList.remove('hidden');
}

function displayItemsForGrouping(items, groups) {
    // Actualizar estadísticas INLINE (diseño compacto)
    const totalGroups = Object.keys(groups).length;
    const totalItems = items.length;
    const totalValue = items.reduce((sum, item) => sum + (item.cantidad * item.valor_unitario), 0);
    try { if (totalItems > 100) { showToast('Info', 'Hay más de 100 ítems, la agrupación puede tardar un poco.', 'info', 4000); } } catch(_) {}

    // Formato compacto en una línea
    const statsContainer = document.getElementById('groupingStats');
    if (statsContainer) {
        statsContainer.innerHTML = `
            <span class="stat">${totalGroups} grupos</span>
            <span class="stat">${totalItems} items</span>
            <span class="stat">$${(totalValue / 1000).toFixed(1)}k</span>
        `;
    }

    // Actualizar preview de operación
    updateOperationPreview(items, groups);

    // UX v2.2: Sticky Totals Bar
    (function() {
        const stickyBar = document.getElementById('stickyTotalsBar');
        if (!stickyBar) return;
        if (totalItems > 0) {
            stickyBar.style.display = 'flex';
            const el = (id) => document.getElementById(id);
            if (el('st-items'))  el('st-items').textContent  = totalItems;
            if (el('st-groups')) el('st-groups').textContent = totalGroups;
            if (el('st-fob'))    el('st-fob').textContent    = 'USD ' + totalValue.toLocaleString('es-AR', {maximumFractionDigits: 0});
            const genBtn = el('generateStickyBtn');
            if (genBtn) genBtn.disabled = (totalItems === 0);
        } else {
            stickyBar.style.display = 'none';
        }
    })();

    // UX v2.2: Steps Banner dinámico
    (function() {
        const s1 = document.getElementById('stepUpload');
        const s2 = document.getElementById('stepReview');
        if (!s1 || !s2) return;
        if (totalItems > 0) {
            s1.className = 'step-item step-done';
            s2.className = 'step-item step-active';
        }
    })();

    // UX v2.2: Bulk bar oculta por defecto
    (function() {
        const bulkBar = document.getElementById('ncmBulkBar');
        if (bulkBar) bulkBar.classList.add('bulk-hidden');
    })();

    // Resetear estado de validación (requiere validar nuevamente)
    updateValidationStatus('pending');

    // NO mostrar batch bar automáticamente - solo cuando hay selección
    // (updateBatchSelectionCounter() se encarga)

    // Crear mapeo de códigos arancelarios a colores consistentes
    const uniqueTariffs = Object.keys(groups).sort();
    const tariffColorMap = {};
    
    uniqueTariffs.forEach((tariff, index) => {
        tariffColorMap[tariff] = (index % 5) + 1; // Colores del 1 al 5
    });
    
    // ORDENAR items por grupo antes de mostrar
    const sortedItems = [...items].sort((a, b) => {
        const tariffA = (a.pieza || '').substring(0, 4);
        const tariffB = (b.pieza || '').substring(0, 4);
        return tariffA.localeCompare(tariffB);
    });
    
    // Mostrar items ORDENADOS por grupo
    const itemsContainer = document.getElementById('itemsToGroup');
    itemsContainer.innerHTML = '';
    
    sortedItems.forEach((item, displayIndex) => {
        const originalIndex = items.indexOf(item);
        const currentTariff = (item.pieza || '').substring(0, 4);
        const colorIndex = tariffColorMap[currentTariff] || 1;
        
        const row = document.createElement('div');
        row.className = 'item-grouping-row';
        row.dataset.itemIndex = originalIndex;
        row.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <input type="checkbox" class="row-checkbox" data-item-index="${originalIndex}">
                <span class="item-number">${displayIndex + 1}</span>
            </div>
            <div class="ncm-cell">
                <div class="ncm-autocomplete-wrapper">
                    <input type="text" class="edit-input ncm ncm-autocomplete-input" value="${item.pieza || ''}"
                           data-item-index="${originalIndex}" data-field="pieza"
                           placeholder="NCM..."
                           autocomplete="off">
                    <div class="ncm-autocomplete-list"></div>
                </div>
                <button type="button" class="btn-notes" 
                        onclick="openNoteModal(this.parentElement.querySelector('.ncm').value || '')" 
                        title="📝 Agregar nota a este NCM">
                    📝
                </button>
            </div>
            <div>
                <input type="text" class="edit-input codparte" value="${item.codigo_parte || ''}"
                       data-item-index="${originalIndex}" data-field="codigo_parte"
                       placeholder="Cód..."
                       style="font-size: 0.75rem;">
            </div>
            <div>
                <input type="text" class="edit-input desc-input" value="${item.descripcion}" 
                       data-item-index="${originalIndex}" data-field="descripcion"
                       placeholder="Descripción">
            </div>
            <div>
                <input type="text" class="edit-input" value="${item.origen}" 
                       data-item-index="${originalIndex}" data-field="origen"
                       placeholder="CN" maxlength="3">
            </div>
            <div>
                <input type="number" class="edit-input number" value="${item.cantidad}" 
                       data-item-index="${originalIndex}" data-field="cantidad"
                       placeholder="1" min="0" step="0.01">
            </div>
            <div>
                <input type="number" class="edit-input number" value="${item.valor_unitario}" 
                       data-item-index="${originalIndex}" data-field="valor_unitario"
                       placeholder="100.00" min="0" step="0.01">
            </div>
            <div>
                <input type="number" class="edit-input number" value="${item.peso_unitario}" 
                       data-item-index="${originalIndex}" data-field="peso_unitario"
                       placeholder="1.0" min="0" step="0.001">
            </div>
        `;
        row.dataset.tariff = currentTariff;
        
        itemsContainer.appendChild(row);
    });
    
    // Guardar items y mapeo de colores para uso posterior
    window.currentItems = items;
    window.tariffColorMap = tariffColorMap;

    // ⬇️ NUEVO: Attach auto-complete listeners después de renderizar
    // Pequeño delay para asegurar que DOM está completamente listo
    setTimeout(() => {
        attachAutoCompleteListeners();
        attachNcmSuggestListeners();
    }, 100);

    // Refrescar dropdown de calculadora después de cargar items
    if (typeof refreshCalculatorDropdown === 'function') {
        refreshCalculatorDropdown();
    }

    // Mostrar botón de validación si hay items
    const validateBtn = document.getElementById('validateItemsBtn');
    if (validateBtn && items.length > 0) {
        validateBtn.style.display = 'inline-block';
    }
}

async function suggestNcm(btn){
    try{
        const idx = parseInt(btn.getAttribute('data-item-index'), 10);
        const row = document.querySelector(`.item-grouping-row [data-item-index="${idx}"]`)?.closest('.item-grouping-row');
        if (!row){ showToast('Error','No se pudo localizar la fila','error'); return; }
        const desc = (row.querySelector('[data-field="descripcion"]')?.value || '').trim();
        if (!desc){ showToast('Info','Completá la descripción para sugerir NCM'); return; }
        const r = await fetch('/ncm/suggest', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ descripcion: desc }) });
        const d = await r.json();
        const suggestions = d.suggestions || [];
        if (suggestions.length === 0){ showToast('Info','Sin sugerencias para esta descripción'); return; }
        const first = suggestions[0];
        const input = row.querySelector('.edit-input.ncm');
        if (input){ input.value = first.ncm; updateField(input); showToast('Sugerido', `NCM: ${first.ncm} (${Math.round((first.confidence||0)*100)}%)`); }
    } catch(_){ showToast('Error','No se pudo sugerir NCM','error'); }
}

// ============================================
// AUTO-COMPLETAR DESCRIPCIÓN DESDE NCM
// Feature agregada: 2025-10-02
// Ubicación: Después de suggestNcm() (línea ~1117)
// ============================================

const ENABLE_AUTO_COMPLETE_DESC = true; // Feature flag (cambiar a false para deshabilitar)

/**
 * Auto-completa descripción cuando usuario ingresa NCM
 *
 * REGLAS DE NO-ROMPER:
 * 1. Solo si descripción VACÍA (no sobrescribir)
 * 2. Solo si NCM válido (6-8 dígitos)
 * 3. Errores silenciosos (no crashear)
 * 4. No interferir con listeners existentes
 *
 * @param {HTMLInputElement} ncmInput - Input del NCM que cambió
 */
async function autoCompleteDescripcion(ncmInput) {
    if (!ENABLE_AUTO_COMPLETE_DESC) return;

    try {
        // VALIDACIÓN 1: Input existe
        if (!ncmInput || !ncmInput.value) {
            return;
        }

        // VALIDACIÓN 2: NCM válido (6-8 dígitos numéricos)
        const ncm = ncmInput.value.trim();
        const validacion = validarFormatoNCM(ncm);
        if (!validacion.valido) {
            showToast('NCM Inválido', validacion.error, 'error');
            ncmInput.classList.add('input-error');
            ncmInput.style.borderColor = '#dc2626';
            return;
        }

        // AUTO-FORMATEO: Actualizar campo con NCM limpio (sin puntos)
        if (ncm !== validacion.ncmLimpio) {
            ncmInput.value = validacion.ncmLimpio;
            // Feedback visual sutil
            ncmInput.style.borderColor = '#10b981';
            setTimeout(() => {
                ncmInput.style.borderColor = '';
            }, 1500);
        }

        // Limpiar error si había uno previo
        limpiarErrorNCM(ncmInput);

        // VALIDACIÓN 3: Row existe
        const row = ncmInput.closest('.item-grouping-row');
        if (!row) {
            return;
        }

        // VALIDACIÓN 4: Descripción input existe
        const descInput = row.querySelector('[data-field="descripcion"]');
        if (!descInput) {
            return;
        }

        // VALIDACIÓN 5: Descripción VACÍA (crítico: no sobrescribir)
        if (descInput.value.trim()) {
            return;
        }

        // ✅ Todas las validaciones pasaron

        // Fetch descripción del backend (usar NCM limpio sin puntos/espacios)
        const res = await fetch(`/api/ncm/${validacion.ncmLimpio}/descripcion`);

        if (!res.ok) {
            return; // Error silencioso
        }

        const data = await res.json();

        if (data && data.descripcion) {
            // Completar descripción
            descInput.value = data.descripcion;

            // Feedback visual (fondo verde)
            descInput.style.transition = 'background-color 0.3s ease';
            descInput.style.backgroundColor = '#e8f5e9'; // Verde claro
            setTimeout(() => {
                descInput.style.backgroundColor = '';
            }, 2000);

            // Toast informativo (corto)
            showToast('Info', `✓ ${data.descripcion.substring(0, 40)}...`, 'info', 2000);

            // CRÍTICO: Actualizar groupingData (persistencia)
            const idx = parseInt(ncmInput.getAttribute('data-item-index'), 10);
            if (!isNaN(idx) && window.groupingData && window.groupingData[idx]) {
                window.groupingData[idx].descripcion = data.descripcion;
            }

            // Trigger change event para que sistema detecte el cambio
            descInput.dispatchEvent(new Event('change', { bubbles: true }));
        }

    } catch (err) {
        // Error silencioso (no romper UI)
        console.warn('[AutoComplete] Error:', err);
    }
}

/**
 * Limpia el estilo de error cuando el usuario corrige el NCM
 */
function limpiarErrorNCM(ncmInput) {
    if (ncmInput) {
        ncmInput.classList.remove('input-error');
        ncmInput.style.borderColor = '';
    }
}

/**
 * Handler para blur del input NCM
 * 1. Auto-formatear NCM (limpiar puntos/espacios)
 * 2. Auto-completar descripción si está habilitado
 */
function handleNcmBlur(event) {
    const input = event.target;

    // PASO 1: Auto-formatear NCM (2905.19. → 290519)
    autoFormatearNCM(input);

    // PASO 2: Auto-completar descripción (si está habilitado)
    if (ENABLE_AUTO_COMPLETE_DESC) {
        autoCompleteDescripcion(input);
    }
}

/**
 * Attach listeners a inputs NCM
 * Se llama después de renderizar items
 */
function attachAutoCompleteListeners() {
    if (!ENABLE_AUTO_COMPLETE_DESC) return;

    const inputs = document.querySelectorAll('[data-field="pieza"]');

    inputs.forEach(input => {
        // Prevenir duplicación (check si ya tiene listener)
        if (input.dataset.autoCompleteAttached === 'true') return;

        input.addEventListener('blur', handleNcmBlur);
        input.dataset.autoCompleteAttached = 'true';
        
        // Adjuntar backend de autocomplete propio y local
        if (typeof attachCustomAutocompleteToNcm === 'function') {
            attachCustomAutocompleteToNcm(input);
        }
    });

}

// ========== NCM HISTORIAL ==========

/**
 * Crea el datalist global con NCMs usados anteriormente
 */
function createNcmHistoryDatalist() {
    // Evitar duplicados
    if (document.getElementById('ncm-history-list')) return;
    
    const datalist = document.createElement('datalist');
    datalist.id = 'ncm-history-list';
    
    const favorites = JSON.parse(localStorage.getItem('ncm_history') || '[]');
    
    favorites.forEach(ncm => {
        const option = document.createElement('option');
        option.value = ncm;
        datalist.appendChild(option);
    });
    
    document.body.appendChild(datalist);
}

/**
 * Guarda un NCM en historial cuando se usa
 */
function saveNcmToHistory(ncm) {
    if (!ncm || ncm.length < 6) return;
    
    let history = JSON.parse(localStorage.getItem('ncm_history') || '[]');
    
    // Mover al principio si ya existe, o agregar
    history = history.filter(h => h !== ncm);
    history.unshift(ncm);
    
    // Mantener solo los últimos 30
    history = history.slice(0, 30);
    
    localStorage.setItem('ncm_history', JSON.stringify(history));
    
    // Actualizar datalist
    updateNcmHistoryDatalist();
}

/**
 * Actualiza el datalist con NCMs nuevos
 */
function updateNcmHistoryDatalist() {
    const datalist = document.getElementById('ncm-history-list');
    if (!datalist) return createNcmHistoryDatalist();
    
    const history = JSON.parse(localStorage.getItem('ncm_history') || '[]');
    
    datalist.innerHTML = '';
    history.forEach(ncm => {
        const option = document.createElement('option');
        option.value = ncm;
        datalist.appendChild(option);
    });
}

/**
 * Attach listeners para guardar NCM en historial cuando se edita
 */
function attachNcmHistoryListeners() {
    // Crear datalist global
    createNcmHistoryDatalist();
    
    // Guardar NCM en historial cuando se edita
    document.querySelectorAll('.edit-input.ncm').forEach(input => {
        if (input.dataset.historyListenerAttached) return;
        
        input.addEventListener('change', () => {
            saveNcmToHistory(input.value);
        });
        
        input.dataset.historyListenerAttached = 'true';
    });
}

// Alias para compatibilidad
function attachNcmSuggestListeners() {
    attachNcmHistoryListeners();
    attachBulkNcmListeners();
}

// ========== ASIGNACIÓN MASIVA NCM ==========

/**
 * Attach listeners para asignación masiva de NCM
 */
function attachBulkNcmListeners() {
    const selectAllCheckbox = document.getElementById('selectAllItems');
    const bulkNcmInput = document.getElementById('bulkNcmInput');
    const assignBtn = document.getElementById('assignBulkNcm');
    const tableBody = document.getElementById('itemsToGroup');
    
    if (!selectAllCheckbox || !assignBtn || !tableBody || !bulkNcmInput) {
        return;
    }
    
    // Listener para Seleccionar Todo
    if (!selectAllCheckbox.dataset.listenerAttached) {
        selectAllCheckbox.dataset.listenerAttached = 'true';
        selectAllCheckbox.addEventListener('change', () => {
            const isChecked = selectAllCheckbox.checked;
            document.querySelectorAll('.row-checkbox').forEach(cb => {
                cb.checked = isChecked;
                const row = cb.closest('.item-grouping-row');
                if (row) row.classList.toggle('selected', isChecked);
            });
            updateSelectedCount();
        });
    }
    
    // Listener para tableBody (event delegation)
    if (!tableBody.dataset.bulkListenerAttached) {
        tableBody.dataset.bulkListenerAttached = 'true';
        tableBody.addEventListener('change', (e) => {
            if (e.target.classList.contains('row-checkbox')) {
                const row = e.target.closest('.item-grouping-row');
                if (row) row.classList.toggle('selected', e.target.checked);
                updateSelectedCount();
                
                // Actualizar "seleccionar todo"
                const allCheckboxes = document.querySelectorAll('.row-checkbox');
                const checkedCount = document.querySelectorAll('.row-checkbox:checked').length;
                selectAllCheckbox.checked = (allCheckboxes.length > 0 && checkedCount === allCheckboxes.length);
            }
        });
    }
    
    // Listener para input NCM
    if (!bulkNcmInput.dataset.listenerAttached) {
        bulkNcmInput.dataset.listenerAttached = 'true';
        bulkNcmInput.addEventListener('input', () => {
            updateAssignButtonState();
        });
    }
    
    // Listener para botón asignar
    if (!assignBtn.dataset.listenerAttached) {
        assignBtn.dataset.listenerAttached = 'true';
        assignBtn.addEventListener('click', assignNcmToSelected);
    }
    
    // Listeners para Origen y Peso bulk
    const bulkOrigenInput = document.getElementById('bulkOrigenInput');
    const bulkPesoInput = document.getElementById('bulkPesoInput');
    
    if (bulkOrigenInput && !bulkOrigenInput.dataset.listenerAttached) {
        bulkOrigenInput.dataset.listenerAttached = 'true';
        bulkOrigenInput.addEventListener('input', updateAssignButtonState);
    }
    
    if (bulkPesoInput && !bulkPesoInput.dataset.listenerAttached) {
        bulkPesoInput.dataset.listenerAttached = 'true';
        bulkPesoInput.addEventListener('input', updateAssignButtonState);
    }
    
    // Listeners para Cantidad y Precio bulk
    const bulkCantidadInput = document.getElementById('bulkCantidadInput');
    const bulkPrecioInput = document.getElementById('bulkPrecioInput');
    
    if (bulkCantidadInput && !bulkCantidadInput.dataset.listenerAttached) {
        bulkCantidadInput.dataset.listenerAttached = 'true';
        bulkCantidadInput.addEventListener('input', updateAssignButtonState);
    }
    
    if (bulkPrecioInput && !bulkPrecioInput.dataset.listenerAttached) {
        bulkPrecioInput.dataset.listenerAttached = 'true';
        bulkPrecioInput.addEventListener('input', updateAssignButtonState);
    }
    
}

/**
 * Actualiza contador de seleccionados
 */
function updateSelectedCount() {
    const selected = document.querySelectorAll('.row-checkbox:checked').length;
    const countEl = document.getElementById('selectedCount');
    if (countEl) {
        countEl.textContent = `${selected} seleccionados`;
    }
    updateAssignButtonState();
}

/**
 * Actualiza estado del botón asignar
 */
function updateAssignButtonState() {
    const bulkNcmInput = document.getElementById('bulkNcmInput');
    const assignBtn = document.getElementById('assignBulkNcm');
    const selected = document.querySelectorAll('.row-checkbox:checked').length;
    
    
    // NCM Button
    if (assignBtn && bulkNcmInput) {
        const hasNcm = bulkNcmInput.value.trim().length >= 4;
        const hasSelection = selected > 0;
        const shouldEnable = hasNcm && hasSelection;
        assignBtn.disabled = !shouldEnable;
    }
    
    // Origin Button
    const bulkOrigenInput = document.getElementById('bulkOrigenInput');
    const origenBtn = document.getElementById('assignBulkOrigen');
    if (origenBtn && bulkOrigenInput) {
        const hasOrigen = bulkOrigenInput.value.trim().length > 0;
        origenBtn.disabled = !(hasOrigen && selected > 0);
    }
    
    // Cantidad Button
    const bulkCantidadInput = document.getElementById('bulkCantidadInput');
    const cantidadBtn = document.getElementById('assignBulkCantidad');
    if (cantidadBtn && bulkCantidadInput) {
        const hasCantidad = bulkCantidadInput.value.trim().length > 0;
        cantidadBtn.disabled = !(hasCantidad && selected > 0);
    }
    
    // Precio Button
    const bulkPrecioInput = document.getElementById('bulkPrecioInput');
    const precioBtn = document.getElementById('assignBulkPrecio');
    if (precioBtn && bulkPrecioInput) {
        const hasPrecio = bulkPrecioInput.value.trim().length > 0;
        precioBtn.disabled = !(hasPrecio && selected > 0);
    }
    
    // Weight Button
    const bulkPesoInput = document.getElementById('bulkPesoInput');
    const pesoBtn = document.getElementById('assignBulkPeso');
    if (pesoBtn && bulkPesoInput) {
        const hasPeso = bulkPesoInput.value.trim().length > 0;
        pesoBtn.disabled = !(hasPeso && selected > 0);
    }
}

/**
 * Aplica un valor masivo (origen o peso) a los items seleccionados
 */
function applyBulkValue(field) {
    const selectedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
    if (selectedCheckboxes.length === 0) {
        showToast('Atención', 'Seleccioná al menos un item', 'warning');
        return;
    }
    
    let value;
    if (field === 'origen') {
        value = document.getElementById('bulkOrigenInput').value;
    } else if (field === 'cantidad') {
        value = document.getElementById('bulkCantidadInput').value;
    } else if (field === 'precio') {
        value = document.getElementById('bulkPrecioInput').value;
    } else if (field === 'peso') {
        value = document.getElementById('bulkPesoInput').value;
    }
    
    if (!value) {
        showToast('Error', `Ingresá un valor para ${field}`, 'error');
        return;
    }
    
    let count = 0;
    selectedCheckboxes.forEach(checkbox => {
        const row = checkbox.closest('.item-grouping-row');
        if (row) {
            let input;
            if (field === 'origen') {
                input = row.querySelector('input[data-field="origen"]');
            } else if (field === 'cantidad') {
                input = row.querySelector('input[data-field="cantidad"]');
            } else if (field === 'precio') {
                input = row.querySelector('input[data-field="valor_unitario"]');
            } else if (field === 'peso') {
                input = row.querySelector('input[data-field="peso_unitario"]');
            }
            
            if (input) {
                input.value = value;
                input.dispatchEvent(new Event('change', { bubbles: true }));
                count++;
            }
        }
    });
    
    showToast('Éxito', `${field.charAt(0).toUpperCase() + field.slice(1)} aplicado a ${count} items`, 'success');
    
    // Mantener selección para permitir múltiples cambios
    // (el usuario puede desmarcar manualmente cuando termine)
}

/**
 * Asigna NCM a todos los items seleccionados
 */
function assignNcmToSelected() {
    const bulkNcmInput = document.getElementById('bulkNcmInput');
    const ncm = bulkNcmInput.value.trim();
    
    if (!ncm || ncm.length < 4) {
        showToast('Error', 'Ingresá un NCM válido (mínimo 4 dígitos)', 'error');
        return;
    }
    
    const selectedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
    let count = 0;
    
    selectedCheckboxes.forEach(cb => {
        const itemIndex = cb.dataset.itemIndex;
        const ncmInput = document.querySelector(`.edit-input.ncm[data-item-index="${itemIndex}"]`);
        if (ncmInput) {
            ncmInput.value = ncm;
            ncmInput.dispatchEvent(new Event('change', { bubbles: true }));
            count++;
        }
        
        // Deseleccionar después de asignar
        cb.checked = false;
        const row = cb.closest('.item-grouping-row');
        if (row) row.classList.remove('selected');
    });
    
    // Guardar en historial
    saveNcmToHistory(ncm);
    
    // Limpiar y actualizar
    bulkNcmInput.value = '';
    document.getElementById('selectAllItems').checked = false;
    updateSelectedCount();
    
    showToast('✅ NCM Asignado', `NCM ${ncm} asignado a ${count} items`, 'success');
}

// ========== FIN ASIGNACIÓN MASIVA NCM ==========

// ========== FIN NCM HISTORIAL ==========

function getTariffDescription(code) {
    const descriptions = {
        "8471": "Máquinas de procesamiento",
        "8517": "Aparatos de telefonía",
        "8542": "Circuitos integrados",
        "9031": "Instrumentos de medida",
        "8528": "Monitores y proyectores",
        "8504": "Transformadores",
        "8473": "Partes de máquinas",
        "8518": "Micrófonos y altavoces",
        "8544": "Cables conductores",
        "8536": "Aparatos de protección"
    };
    
    return descriptions[code] || "Otros productos";
}

function updateField(inputElement) {
    const itemIndex = inputElement.dataset.itemIndex;
    const fieldName = inputElement.dataset.field;
    const newValue = inputElement.value.trim();

    // Validaciones específicas por campo
    let isValid = true;
    let processedValue = newValue;

    switch(fieldName) {
        case 'pieza':
            // NCM es opcional — aceptar cualquier valor (vacío, alfanumérico, numérico)
            isValid = true;

            // Si se edita un NCM y ya estaba validado, invalidar estado
            if (window.validationState.status === 'valid') {
                const currentHash = getItemsHash(window.currentItems);
                if (currentHash !== window.validationState.itemsHash) {
                    updateValidationStatus('pending');
                }
            }
            
            // Verificar si hay notas para este NCM y actualizar botón
            if (isValid && inputElement.closest) {
                const row = inputElement.closest('.item-grouping-row');
                if (row) {
                    refreshNoteBadge(row, newValue.substring(0, 4));
                }
            }
            break;

        case 'descripcion':
            // Descripción no puede estar vacía
            isValid = newValue.length > 0;
            break;

        case 'origen':
            // Origen debe ser 2-3 caracteres
            isValid = newValue.length >= 2 && newValue.length <= 3;
            processedValue = newValue.toUpperCase();

            // Si se edita origen y ya estaba validado, invalidar estado
            if (window.validationState.status === 'valid') {
                const currentHash = getItemsHash(window.currentItems);
                if (currentHash !== window.validationState.itemsHash) {
                    updateValidationStatus('pending');
                }
            }

            // Refrescar dropdown de calculadora (el dropdown también muestra origen)
            if (typeof refreshCalculatorDropdown === 'function') {
                refreshCalculatorDropdown();
            }
            break;
            
        case 'cantidad':
        case 'valor_unitario':
        case 'peso_unitario':
            // Números deben ser positivos
            const numValue = parseFloat(newValue);
            isValid = !isNaN(numValue) && numValue > 0;
            processedValue = numValue;
            break;
    }
    
    // Aplicar estilo visual según validación
    if (isValid) {
        inputElement.classList.remove('invalid');
        inputElement.classList.add('valid');
    } else {
        inputElement.classList.remove('valid');
        inputElement.classList.add('invalid');
        
        // Mostrar error visual inmediato para campos críticos
        if (fieldName === 'descripcion') {
            showToast('Error', 'Descripción es obligatoria', 'error');
        }
        return; // No actualizar si es inválido
    }
    
    // Actualizar item en memoria
    if (window.currentItems && window.currentItems[itemIndex]) {
        window.currentItems[itemIndex][fieldName] = processedValue;
    }
    
    // Si cambió el NCM, reagrupar
    if (fieldName === 'pieza') {
        const newTariff = newValue.substring(0, 4);
        document.getElementById(`tariff-${itemIndex}`).textContent = newTariff;
        // Actualizar etiqueta de grupo también
        try {
            const groupEl = document.getElementById(`group-${itemIndex}`);
            if (groupEl) groupEl.textContent = `Grupo ${newTariff}`;
            const row = document.querySelectorAll('.item-grouping-row')[itemIndex];
            if (row) row.dataset.tariff = newTariff;
            
            // Actualizar data-ncm del botón "Datos Completos"
            const ncmCompletoBtn = row.querySelector('.btn-ncm-completo');
            if (ncmCompletoBtn) {
                ncmCompletoBtn.dataset.ncm = newValue;
            }
        } catch(_) {}
        // Mostrar alert si hay notas para este NCM
        maybeShowNcmNotesAlert(newTariff);
        debouncedRegroupAllItems();
        
        // Refrescar dropdown de calculadora si el modal está abierto
        if (typeof refreshCalculatorDropdown === 'function') {
            refreshCalculatorDropdown();
        }
    }
    
    // Si cambió cantidad o precio, recalcular estadísticas y KPIs
    if (['cantidad', 'valor_unitario', 'peso_unitario'].includes(fieldName)) {
        updateGroupingStats();
        // Recalcular KPIs del preview
        if (window.currentItems && typeof updateOperationPreview === 'function') {
            const groups = {};
            window.currentItems.forEach(item => {
                const key = (item.pieza || '').substring(0, 4) || 'SIN-NCM';
                if (!groups[key]) groups[key] = [];
                groups[key].push(item);
            });
            updateOperationPreview(window.currentItems, groups);
        }
    }

    // Autovalidar si está activo (solo si no hay errores previos)
    try {
        const auto = document.getElementById('autoValidateToggle');
        if (auto && auto.checked) {
            // No autovalidar si ya hay errores visibles
            const summaryInline = document.getElementById('validationSummaryInline');
            const hasErrors = summaryInline && !summaryInline.classList.contains('hidden');
            
            if (!hasErrors) {
                if (!window.__debouncedValidate) {
                    window.__debouncedValidate = debounce(validateCurrentItems, 400);
                }
                window.__debouncedValidate();
            }
        }
    } catch(_) {}
    

    // Autosave draft (debounced)
    try {
        if (!window.__debouncedDraft) {
            window.__debouncedDraft = debounce(saveGroupingDraft, 400);
        }
        window.__debouncedDraft();
    } catch(_) {}
}

async function openNcmInfo(btn){
    try{
        const idx = parseInt(btn.getAttribute('data-item-index'), 10);
        const row = document.querySelector(`.item-grouping-row [data-item-index="${idx}"]`)?.closest('.item-grouping-row');
        if (!row){ showToast('Error','No se pudo localizar la fila','error'); return; }
        const ncmFull = (row.querySelector('.edit-input.ncm')?.value || '').trim();
        if (!/^\d{2,8}$/.test(ncmFull)){ showToast('Info','Ingresá un NCM válido primero'); return; }
        const code = ncmFull;
        const overlay = document.getElementById('ncmInfoOverlay');
        const codeEl = document.getElementById('ncmInfoCode');
        const content = document.getElementById('ncmInfoContent');
        if (!overlay || !codeEl || !content) return;
        codeEl.textContent = code;
        content.textContent = 'Cargando...';
        overlay.classList.add('active');
        const r = await fetch(`/ncm/info/${code}`);
        const d = await r.json();
        if (!d.success){ content.innerHTML = '<div class="note-item">Sin información disponible</div>'; return; }
        const info = d.info || {};
        const desc = info.descripcion || '';
        const aec = info.aec || '';
        const fam = info.familia || '';
        const nota = info.nota || '';
        const src = info.source_url ? `<div class="ncm-info-row"><span>Fuente:</span> <a href="${info.source_url}" target="_blank" rel="noopener">Abrir</a></div>` : '';
        content.innerHTML = `
            ${desc ? `<div class="ncm-info-row"><span>Descripción:</span> ${esc(desc)}</div>` : ''}
            ${fam ? `<div class="ncm-info-row"><span>Familia:</span> ${esc(fam)}</div>` : ''}
            ${aec ? `<div class="ncm-info-row"><span>% AEC:</span> ${esc(aec)}</div>` : ''}
            ${nota ? `<div class="ncm-info-note">${esc(nota)}</div>` : '<div class="ncm-info-note">Sin nota</div>'}
            ${src}
        `;
    } catch(_){ showToast('Error','No se pudo cargar info NCM','error'); }
}

function hideNcmInfo(){
    const overlay = document.getElementById('ncmInfoOverlay');
    if (overlay) overlay.classList.remove('active');
}

function esc(s){
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
async function maybeShowNcmNotesAlert(ncm4) {
    try {
        if (!ncm4 || ncm4.length < 4) { document.getElementById('ncmNotesAlert')?.classList.add('hidden'); return; }
        // ✅ Usar sistema throttled en lugar de fetch directo
        const data = await fetchNotasNCMThrottled(ncm4);
        const alertBox = document.getElementById('ncmNotesAlert');
        const codeEl = document.getElementById('ncmNotesCode');
        const listEl = document.getElementById('ncmNotesList');
        const btn = document.getElementById('viewNcmNotesBtn');
        if (!alertBox) return;
        if ((data.notas || []).length === 0) { alertBox.classList.add('hidden'); return; }
        codeEl.textContent = ncm4;
        listEl.innerHTML = data.notas.map(t => `• ${t}`).join('<br>');
        alertBox.classList.remove('hidden');
        btn.onclick = () => openNoteModal(ncm4);
    } catch (_) {}
}

function regroupAllItems() {
    // Obtener todos los NCMs actuales (ahora son inputs con clase edit-input ncm)
    const ncmInputs = document.querySelectorAll('.edit-input.ncm');
    const tariffCodes = {};
    
    // Recopilar todos los códigos arancelarios únicos
    ncmInputs.forEach((input, index) => {
        const ncm = input.value.trim();
        if (ncm.length >= 4) {
            const tariff = ncm.substring(0, 4);
            if (!tariffCodes[tariff]) {
                tariffCodes[tariff] = [];
            }
            tariffCodes[tariff].push(index);
        }
    });
    
    // Crear mapeo consistente de colores (ordenado alfabéticamente)
    const uniqueTariffs = Object.keys(tariffCodes).sort();
    const newColorMap = {};
    
    uniqueTariffs.forEach((tariff, index) => {
        newColorMap[tariff] = (index % 5) + 1;
    });
    
    // REORDENAR tabla por grupos - TODOS los del mismo color juntos
    const tableBody = document.getElementById('itemsToGroup');
    const rows = Array.from(tableBody.children);
    
    // Ordenar filas por código arancelario (con guardas)
    rows.sort((rowA, rowB) => {
        const ncmA = (rowA.dataset && rowA.dataset.tariff) ? rowA.dataset.tariff : (rowA.querySelector('.edit-input.ncm')?.value || '').substring(0,4);
        const ncmB = (rowB.dataset && rowB.dataset.tariff) ? rowB.dataset.tariff : (rowB.querySelector('.edit-input.ncm')?.value || '').substring(0,4);
        return ncmA.localeCompare(ncmB);
    });
    
    // Limpiar tabla y agregar filas ordenadas
    tableBody.innerHTML = '';
    
    rows.forEach((row, newIndex) => {
        // Actualizar número de item
        const itemNumber = row.querySelector('.item-number');
        if (itemNumber) itemNumber.textContent = newIndex + 1;
        
        // Obtener tariff actual
        const ncmInput = row.querySelector('.edit-input.ncm');
        const currentTariff = (ncmInput && ncmInput.value ? ncmInput.value : '').substring(0, 4);
        row.dataset.tariff = currentTariff;
        
        tableBody.appendChild(row);
    });
    
    // Actualizar mapeo global para consistencia
    window.tariffColorMap = newColorMap;
    
    // Actualizar estadísticas
    updateGroupingStats(uniqueTariffs.length, ncmInputs.length);

    // Refrescar dropdown de calculadora después de reagrupar (los items cambiaron)
    if (typeof refreshCalculatorDropdown === 'function') {
        refreshCalculatorDropdown();
    }
}
// Acciones masivas
function toggleSelectAll(el) {
    const checked = el.checked;
    // Las filas reales usan .row-checkbox (ver renderItemsForGrouping y dashboard.html).
    // El selector legacy .row-select nunca encontró nada → la barra batch no aparecía.
    document.querySelectorAll('.row-checkbox').forEach(cb => { cb.checked = checked; });
    if (typeof updateBatchSelectionCounter === 'function') updateBatchSelectionCounter();
}

// NOTA: assignNcmToSelected está definida arriba en la sección "ASIGNACIÓN MASIVA NCM"

function updateGroupingStats(totalGroups, totalItems) {
    // Calcular valor total actual
    let totalValue = 0;
    if (window.currentItems) {
        totalValue = window.currentItems.reduce((sum, item) => sum + (item.cantidad * item.valor_unitario), 0);
    }
    
    document.getElementById('groupingStats').innerHTML = `
        <div class="grouping-stat">
            <div class="grouping-stat-number">${totalGroups}</div>
            <div class="grouping-stat-label">Grupos Únicos</div>
        </div>
        <div class="grouping-stat">
            <div class="grouping-stat-number">${totalItems}</div>
            <div class="grouping-stat-label">Items Total</div>
        </div>
        <div class="grouping-stat">
            <div class="grouping-stat-number">$${totalValue.toLocaleString()}</div>
            <div class="grouping-stat-label">Valor Total</div>
        </div>
    `;
}

// === Validación de items (Solo campos obligatorios) ===
async function validateCurrentItems(){
    try{
        const rows = document.querySelectorAll('.item-grouping-row');
        if (!rows || rows.length === 0) { showToast('Info','No hay ítems para validar'); return; }
        
        // 1. Validación Local (Errores duros: Precio, NCM, Cantidad)
        const pre = collectItemsAndPreErrors();
        
        // Mostrar resultado directamente (Sin validación inteligente)
        renderValidationResult({ 
            success: true, 
            errors: pre.errors || [], 
            warnings: pre.warnings || [],
            valid_count: pre.valid_count, 
            total: pre.total 
        });
        
    } catch(e){ 
        console.error(e);
        showToast('Error', 'Error en validación', 'error'); 
    }
}

function renderValidationResult(data){
    // Usar el nuevo dropdown inline 
    const summaryInline = document.getElementById('validationSummaryInline');
    const summaryText = document.getElementById('validationSummaryText');
    const errorsList = document.getElementById('validationErrorsList');
    const genBtn = document.getElementById('generateGroupedBtn');
    const mariaBtn = document.getElementById('generateMariaBtn');

    // Solo necesitamos los elementos esenciales del nuevo dropdown
    if (!summaryInline || !summaryText || !errorsList) {
        console.warn('⚠️ Elementos de validación no encontrados');
        return;
    }

    if (data && data.success){
        const errors = data.errors || [];
        const warnings = data.warnings || [];
        const allMessages = [...errors, ...warnings.map(w => `⚠️ ${w}`)];

        if (errors.length === 0 && warnings.length === 0){
            // ✅ TODO PERFECTO
            if (genBtn) genBtn.disabled = false;
            if (mariaBtn) mariaBtn.disabled = false;
            summaryInline.classList.add('hidden');
            updateValidationStatus('valid');
            showToast('Éxito', 'Todos los datos son válidos', 'success');
        } else if (errors.length > 0) {
            // ❌ HAY ERRORES BLOQUEANTES
            if (genBtn) genBtn.disabled = true;
            if (mariaBtn) mariaBtn.disabled = true;
            summaryInline.classList.remove('hidden');
            // FIX: Mantener clase validation-dropdown, solo agregar/remover estados
            summaryInline.classList.add('has-errors');
            summaryInline.classList.remove('has-warnings');
            updateValidationStatus('invalid');
            showToast('Error', `${errors.length} error(es) deben corregirse`, 'error');
            summaryText.textContent = `❌ ${errors.length} errores encontrados`;
        } else {
             // ⚠️ SOLO ADVERTENCIAS - PERMITIR CONTINUAR
            if (genBtn) genBtn.disabled = false;
            if (mariaBtn) mariaBtn.disabled = false;
            summaryInline.classList.remove('hidden');
            // FIX: Mantener clase validation-dropdown, solo agregar/remover estados
            summaryInline.classList.remove('has-errors');
            summaryInline.classList.add('has-warnings');
            updateValidationStatus('valid');
            showToast('Aviso', `${warnings.length} advertencia(s) - podés continuar`, 'warning');
            summaryText.textContent = `⚠️ ${warnings.length} advertencias (podés continuar)`;
        }

        // FIX: Solo escribir al dropdown nuevo, no al acordeón viejo
        errorsList.innerHTML = allMessages.map(msg => `
            <div class="error-item">
                <i class="fas ${msg.includes('⚠️') ? 'fa-exclamation-triangle' : 'fa-exclamation-circle'}" style="color: ${msg.includes('⚠️') ? '#f59e0b' : '#ef4444'};"></i>
                <span>${msg}</span>
            </div>
        `).join('');
    } else {
        showToast('Error', data && data.detail ? data.detail : 'Validación fallida', 'error');
    }
}
            


function collectItemsAndPreErrors(){
    const rows = document.querySelectorAll('.item-grouping-row');
    const items = [];
    const errors = [];
    const warnings = [];
    let validCount = 0;
    // limpiar estados previos
    document.querySelectorAll('.item-grouping-row').forEach(r=> r.classList.remove('invalid-row'));
    rows.forEach((row, idx) => {
        let pieza = (row.querySelector('[data-field="pieza"]')?.value || '').trim();
        const descripcion = (row.querySelector('[data-field="descripcion"]')?.value || '').trim();
        const origen = (row.querySelector('[data-field="origen"]')?.value || '').trim().toUpperCase();
        const cantidadRaw = (row.querySelector('[data-field="cantidad"]')?.value || '').toString().replace(',', '.');
        const valorRaw = (row.querySelector('[data-field="valor_unitario"]')?.value || '').toString().replace(',', '.');
        const pesoRaw = (row.querySelector('[data-field="peso_unitario"]')?.value || '').toString().replace(',', '.');
        const cantidad = parseFloat(cantidadRaw);
        const valor_unitario = parseFloat(valorRaw);
        const peso_unitario = parseFloat(pesoRaw);
        let rowHasError = false;

        // VALIDACIÓN NCM: Solo advertencia si es inválido (NCM es opcional)
        const validacionNCM = validarFormatoNCM(pieza);
        if (pieza && pieza.trim() !== '' && !validacionNCM.valido) {
            // NCM tiene valor pero es inválido → advertencia, NO error
            warnings.push(`Advertencia en ítem ${idx+1}: NCM "${pieza}" tiene formato inválido (se acepta igual)`);
        } else if (validacionNCM.valido && pieza && pieza !== validacionNCM.ncmLimpio) {
            // NCM válido pero con formato incorrecto → auto-corregir
            const piezaInput = row.querySelector('[data-field="pieza"]');
            if (piezaInput) {
                piezaInput.value = validacionNCM.ncmLimpio;
                piezaInput.style.borderColor = '#10b981';
                setTimeout(() => {
                    piezaInput.style.borderColor = '';
                }, 1500);
            }
            pieza = validacionNCM.ncmLimpio;
        }

        // VALIDACIÓN DESCRIPCIÓN: Obligatoria (no vacía)
        if (!descripcion || descripcion.trim() === '') {
            errors.push(`Error en ítem ${idx+1} (NCM ${pieza || '----'}): Descripción es obligatoria`);
            rowHasError = true;
        }

        // VALIDACIÓN ORIGEN: Advertencia si vacío o "XX" (no bloquea)
        if (!origen || origen.trim() === '' || origen === 'XX') {
            warnings.push(`Advertencia en ítem ${idx+1} (NCM ${pieza || '----'}): Origen no especificado (se acepta igual)`);
        }

        // VALIDACIÓN CANTIDAD: Mayor a 0
        if (!(cantidad > 0)){
            errors.push(`Error en ítem ${idx+1} (NCM ${pieza || '----'}): cantidad debe ser numérica y > 0. Ej: 10 o 10.00`);
            rowHasError = true;
        }

        // VALIDACIÓN PRECIO: Mayor a 0 (obligatorio para generar)
        if (!(valor_unitario > 0)){
            errors.push(`Error en ítem ${idx+1} (NCM ${pieza || '----'}): Precio debe ser mayor a 0. Ej: 120.50`);
            rowHasError = true;
        }

        if (rowHasError){ row.classList.add('invalid-row'); }
        else { validCount += 1; }
        items.push({ pieza, descripcion, origen, cantidad, valor_unitario, peso_unitario });
    });
    return { items, errors, warnings, valid_count: validCount, total: rows.length };
}

function downloadErrorsCsv(){
    try {
        const items = Array.from(document.querySelectorAll('#validationList .result-item'))
            .map(el => el.innerText.replace(/^\s*\S+\s/, ''));
        if (items.length === 0){ showToast('Info','No hay errores para exportar'); return; }
        const header = 'error\n';
        const body = items.map(e => '"' + e.replace(/"/g,'""') + '"').join('\n');
        const csv = header + body;
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'errores_validacion.csv';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch(_) { showToast('Error','No se pudo exportar','error'); }
}

/**
 * Toggle del dropdown de errores de validación
 */
function toggleValidationDropdown() {
    const dropdown = document.getElementById('validationSummaryInline');
    const content = document.getElementById('validationDropdownContent');
    const btn = dropdown.querySelector('.validation-dropdown-btn');
    
    if (!dropdown || !content || !btn) return;
    
    const isOpen = !content.classList.contains('hidden');
    
    if (isOpen) {
        // Cerrar dropdown
        content.classList.add('hidden');
        btn.classList.remove('open');
    } else {
        // Abrir dropdown
        content.classList.remove('hidden');
        btn.classList.add('open');
    }
}

/**
 * Cerrar dropdown de errores al hacer clic fuera
 */
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('validationSummaryInline');
    if (dropdown && !dropdown.contains(event.target)) {
        const content = document.getElementById('validationDropdownContent');
        const btn = dropdown.querySelector('.validation-dropdown-btn');
        
        if (content && btn) {
            content.classList.add('hidden');
            btn.classList.remove('open');
        }
    }
});

function saveGroupingDraft(){
    try {
        const rows = document.querySelectorAll('.item-grouping-row');
        const data = Array.from(rows).map(row => ({
            pieza: row.querySelector('[data-field="pieza"]').value,
            descripcion: row.querySelector('[data-field="descripcion"]').value,
            origen: row.querySelector('[data-field="origen"]').value,
            cantidad: row.querySelector('[data-field="cantidad"]').value,
            valor_unitario: row.querySelector('[data-field="valor_unitario"]').value,
            peso_unitario: row.querySelector('[data-field="peso_unitario"]').value,
        }));
        localStorage.setItem('grouping_draft', JSON.stringify(data));
        // indicador visual breve
        try {
            const ind = document.getElementById('autosaveIndicator');
            if (ind){ ind.classList.remove('hidden'); setTimeout(()=> ind.classList.add('hidden'), 1200); }
        } catch(_){ }
    } catch(_) {}
}

function clearGroupingDraft(){
    try {
        localStorage.removeItem('grouping_draft');
        showToast('Listo','Borrador de agrupación eliminado');
    } catch(_) {}
}

async function downloadLastGenerated(){
    try{
        const r = await fetch('/generated/');
        const data = await r.json();
        if (!data.success || !data.last_filename){ showToast('Info','No hay archivos recientes'); return; }
        const a = document.createElement('a');
        a.href = `/download/${data.last_filename}`;
        a.download = data.last_filename;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
    } catch(_){ showToast('Error','No se pudo descargar','error'); }
}

async function generateGroupedExcel() {
    if (!window.currentItems) {
        showError('No hay items para procesar');
        return;
    }

    // VALIDACIÓN DE ERRORES: Bloquear si hay errores en los datos
    const pre = collectItemsAndPreErrors();
    if (pre.errors && pre.errors.length > 0) {
        renderValidationResult({ success: true, errors: pre.errors });
        showToast('Error', `Hay ${pre.errors.length} error(es) que corregir antes de generar`, 'error');
        return;
    }

    // VALIDACIÓN NCM: Ya no es obligatoria — se puede generar sin verificar

    const btn = document.getElementById('generateGroupedBtn');
    const originalHTML = btn.innerHTML;

    // Generar Excel directamente (ya está validado)
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generando...';
    
    // Recopilar TODOS los campos editados
    const rows = document.querySelectorAll('.item-grouping-row');
    const groupedItems = [];
    
    rows.forEach((row, index) => {
        const originalIndex = parseInt(row.dataset.itemIndex);
        const originalItem = window.currentItems[originalIndex];
        
        // Obtener valores actuales de todos los campos editables
        const pieza = row.querySelector('[data-field="pieza"]').value.trim();
        const codigo_parte = row.querySelector('[data-field="codigo_parte"]')?.value?.trim() || originalItem.codigo_parte || "";
        const descripcion = row.querySelector('[data-field="descripcion"]').value.trim();
        const origen = row.querySelector('[data-field="origen"]').value.trim().toUpperCase() || "XX";
        const cantidad = parseFloat(row.querySelector('[data-field="cantidad"]').value);
        const valor_unitario = parseFloat(row.querySelector('[data-field="valor_unitario"]').value);
        const peso_unitario = parseFloat(row.querySelector('[data-field="peso_unitario"]').value);

        // Validar que no haya NaN en campos numéricos obligatorios
        // NCM (pieza) puede estar vacío - el despachante lo completa después
        if (!descripcion || isNaN(cantidad) || isNaN(valor_unitario) || isNaN(peso_unitario)) {
            showToast('Error', `Item ${index + 1}: Descripción, cantidad, valor y peso son obligatorios`, 'error');
            btn.innerHTML = originalHTML;
            hideLoading();
            return;
        }

        const updatedItem = {
            pieza: pieza,
            codigo_parte: codigo_parte,
            descripcion: descripcion,
            origen: origen,
            cantidad: cantidad,
            valor_unitario: valor_unitario,
            peso_unitario: peso_unitario,
            // Mantener campos opcionales del item original (strings vacíos en lugar de null para Pydantic StrictStr)
            marca: originalItem.marca || "",
            modelo: originalItem.modelo || "",
            version: originalItem.version || "",
            otros: originalItem.otros || "",
            separador: originalItem.separador || "",
            ventaja: originalItem.ventaja || ""
        };

        groupedItems.push(updatedItem);
    });
    
    // Guardar en historial ANTES de procesar (según estrategia unificada)
    try { 
        // Mostrar toast de "Guardando..." silenciado o sutil
        if (clientSelect && clientSelect.value) {
            await saveOperationToHistory(groupedItems); 
        }
    } catch (_) {
        console.warn('Falló guardado de historial, continuando con generación');
    }

    // Procesar como operación normal pero con agrupación
    await processGroupedItems(groupedItems, btn, originalHTML);
}

async function processGroupedItems(items, btn, originalHTML) {
    showLoading();

    try {
        // Token opcional - el endpoint es público
        const token = localStorage.getItem('access_token');

        const payload = {
            operation_id: `GROUPED_${Date.now()}`,
            items: items
        };

        const headers = {
            'Content-Type': 'application/json'
        };

        const response = await fetch('/process_operation/', {
            method: 'POST',
            headers: headers,
            credentials: 'include', // Cookies automáticas
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            // Manejo específico de errores de autenticación
            if (response.status === 401 || response.status === 403) {
                showToast('Error', 'Sesión expirada o sin permisos. Redirigiendo...', 'error');
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_plan');
                localStorage.removeItem('user_roles');
                setTimeout(() => window.location.href = '/login', 1500);
                hideLoading();
                return;
            }
            throw new Error(data.detail?.errors || data.detail || 'Error procesando agrupación');
        }

        // Feedback de éxito
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check-circle"></i> ¡Generado!';
        btn.classList.add('state-success');

        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('state-success');
        }, 3000);

        showSuccess(data, 'grouped');

        // Si hay URL de descarga, disparamos la descarga automática
        try {
            if (data.download_url) {
                try {
                    const resp = await fetch(data.download_url, { credentials: 'include' });
                    if (resp.ok) {
                        const blob = await resp.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = data.filename || 'AVG_result.xlsx';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        showToast('Éxito', 'Excel descargado correctamente', 'success');
                    } else {
                        console.warn('Download failed:', resp.status);
                    }
                } catch(e) { console.error('Download error:', e); }
            }
        } catch (_) {}

    } catch (error) {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// ========== GENERADOR MARIA TXT ==========
async function generateMariaTxt() {
    
    if (!window.currentItems || window.currentItems.length === 0) {
        alert('No hay items para generar. Por favor cargue un archivo primero.');
        showToast('Error', 'No hay items para generar', 'error');
        return;
    }

    // VALIDACIÓN DE ERRORES: Bloquear si hay errores en los datos
    const pre = collectItemsAndPreErrors();
    if (pre.errors && pre.errors.length > 0) {
        renderValidationResult({ success: true, errors: pre.errors });
        // Usar alert para asegurar que el usuario vea el error
        alert(`Hay ${pre.errors.length} error(es) en los datos que impiden generar el archivo:\n\n- ${pre.errors.slice(0, 3).join('\n- ')}\n${pre.errors.length > 3 ? '...' : ''}`);
        showToast('Error', `Hay ${pre.errors.length} error(es) que corregir antes de generar`, 'error');
        return;
    }

    const btn = document.getElementById('generateMariaBtn');
    const originalHTML = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generando...';

    try {
        // Recopilar items de la tabla
        const rows = document.querySelectorAll('.item-grouping-row');
        const items = [];
        
        rows.forEach((row, index) => {
            const originalIndex = parseInt(row.dataset.itemIndex);
            const originalItem = window.currentItems[originalIndex] || {};
            
            const pieza = row.querySelector('[data-field="pieza"]')?.value?.trim() || '';
            const codigo_parte = row.querySelector('[data-field="codigo_parte"]')?.value?.trim() || originalItem.codigo_parte || '';
            const descripcion = row.querySelector('[data-field="descripcion"]')?.value?.trim() || '';
            const cantidad = parseFloat(row.querySelector('[data-field="cantidad"]')?.value) || 1;
            const valor_unitario = parseFloat(row.querySelector('[data-field="valor_unitario"]')?.value) || 0;
            const peso_unitario = parseFloat(row.querySelector('[data-field="peso_unitario"]')?.value) || 0;
            const origen = row.querySelector('[data-field="origen"]')?.value?.trim() || 'CN';
            
            items.push({
                ncm: pieza,
                pieza: pieza,
                codigo_parte: codigo_parte,
                descripcion: descripcion,
                cantidad: cantidad,
                valor_unitario: valor_unitario,
                valor_total: cantidad * valor_unitario,
                peso_kg: peso_unitario * cantidad,
                origen: origen,
                pais_origen: origen
            });
        });

        // Advertir si hay items sin NCM para MARIA TXT (pero no bloquear)
        const itemsSinNCM = items.filter(item => !item.pieza || item.pieza.trim() === '');
        if (itemsSinNCM.length > 0) {
            const msg = `${itemsSinNCM.length} items no tienen NCM.\nMARIA TXT usará NCM vacío para esos items.\n¿Continuar?`;
            if (!confirm(msg)) {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                return;
            }
        }

        // Obtener datos de operación del panel
        const operacionData = getOperacionData();
        
        // Detectar tipo de operación (Import o Export)
        const operationType = document.querySelector('input[name="operationType"]:checked')?.value || 'import';
        const isExport = operationType === 'export';
        
        let payload, endpoint;
        
        if (isExport) {
            // EXPORTACIÓN - Usando defaults (UI simplificado)
            endpoint = '/generate_maria_export';
            payload = {
                operation_id: operacionData.numero_factura || `EXP${Date.now()}`.slice(0, 12),
                items: items,
                moneda: operacionData.moneda || 'DOL',
                incoterm: operacionData.incoterm || 'FOB',
                exportador_nombre: operacionData.comprador_nombre || '',
                cuit_exportador: operacionData.comprador_cuit || '',
                comprador_nombre: operacionData.vendedor_nombre || '',
                comprador_pais: 'US',  // Default para demo
                flete: operacionData.flete || 0,
                seguro: operacionData.seguro || 0
            };
        } else {
            // IMPORTACIÓN (comportamiento original)
            endpoint = '/generate_maria';
            payload = {
                operation_id: operacionData.numero_factura || `OP${Date.now()}`.slice(0, 10),
                items: items,
                moneda: operacionData.moneda || 'DOL',
                incoterm: operacionData.incoterm || 'FOB',
                vendedor_nombre: operacionData.vendedor_nombre || '',
                vendedor_id: operacionData.vendedor_id || '',
                comprador_nombre: operacionData.comprador_nombre || '',
                comprador_cuit: operacionData.comprador_cuit || '',
                flete: operacionData.flete || 0,
                seguro: operacionData.seguro || 0,
                // Transport data
                bl_numero: operacionData.bl_numero || '',
                puerto_origen: operacionData.puerto_origen || '',
                puerto_destino: operacionData.puerto_destino || 'ARBUE',
                buque_nombre: operacionData.buque_nombre || '',
                viaje_numero: operacionData.viaje_numero || '',
                fecha_embarque: operacionData.fecha_embarque || '',
                // Container data
                contenedor_numero: operacionData.contenedor_numero || '',
                contenedor_tipo: operacionData.contenedor_tipo || '',
                contenedor_peso: operacionData.contenedor_peso || 0
            };
        }

        // === NUEVO: GUARDAR EN HISTORIAL ANTES DE GENERAR ===
        // Estrategia "Save First, Give File Later"
        try {
            if (clientSelect && clientSelect.value) {
                // Pequeño feedback visual opcional
                // showToast('Info', 'Guardando en historial...', 'info');
                await saveOperationToHistory(items);
            }
        } catch (histError) {
            console.warn('⚠️ Error guardando historial (no bloqueante):', histError);
            // No bloqueamos la generación, pero avisamos en consola
        }
        // ====================================================

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail?.errors?.join(', ') || data.detail || 'Error generando MARIA');
        }

        // Éxito - descargar archivo
        btn.innerHTML = '<i class="fas fa-check-circle"></i> ¡Generado!';
        btn.classList.add('state-success');

        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('state-success');
            btn.disabled = false;
        }, 3000);

        // Descargar archivo TXT - DEBUG VERSION 2
        console.log('🔵 MARIA TXT Download - data:', data);
        console.log('🔵 download_url:', data.download_url);
        console.log('🔵 filename:', data.filename);
        
        if (data.download_url) {
            console.log('🟢 Using window.location.href for download');
            window.location.href = data.download_url;
        } else if (data.content) {
            console.log('🟡 Fallback to Blob (no download_url)');
            // Fallback (solo si no hay URL)
            const blob = new Blob([data.content], { type: 'text/plain; charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = data.filename || 'MARIA.TXT';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);
        } else {
            console.log('🔴 No download_url and no content!');
        }

        showToast('Éxito', 'Archivo MARIA TXT generado', 'success');

    } catch (error) {
        console.error('Error generando MARIA:', error);
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        alert('Error generando archivo: ' + (error.message || error));
        showToast('Error', error.message || 'Error generando archivo MARIA', 'error');
    }
}

function cancelGrouping() {
    // Volver a la interfaz principal
    document.getElementById('groupingSection').classList.add('hidden');

    // Ocultar preview de operación
    const preview = document.getElementById('operationPreview');
    if (preview) preview.classList.add('hidden');

    // Mostrar formulario manual por defecto
    switchMode('manual');

    // Limpiar datos
    window.currentItems = null;
}

// === PANEL DATOS DE OPERACIÓN ===

/**
 * Pobla el panel de Datos de Operación con los datos extraídos por Gemini
 */
function populateOperacionPanel(operacion) {
    if (!operacion || Object.keys(operacion).length === 0) {
        return;
    }
    
    
    // Mostrar panel
    const panel = document.getElementById('operacionPanel');
    if (panel) {
        panel.classList.remove('hidden');
    }
    
    // Poblar campos
    const fields = {
        'op_numero_factura': operacion.numero_factura || '',
        'op_fecha_emision': operacion.fecha_emision || '',
        'op_vendedor_nombre': operacion.vendedor_nombre || '',
        'op_vendedor_id': operacion.vendedor_id || '',
        'op_vendedor_pais': operacion.vendedor_pais || 'CN',
        'op_comprador_nombre': operacion.comprador_nombre || '',
        'op_comprador_cuit': operacion.comprador_cuit || '',
        'op_moneda': operacion.moneda || 'DOL',
        'op_incoterm': operacion.incoterm || 'FOB',
        'op_flete': operacion.flete || 0,
        'op_seguro': operacion.seguro || 0
    };
    
    for (const [id, value] of Object.entries(fields)) {
        const el = document.getElementById(id);
        if (el) {
            el.value = value;
        }
    }

    // Drawer Zona 3: refresca el badge "n/12" tras cargar datos del PDF.
    if (typeof refreshOperacionDrawerBadge === 'function') {
        try { refreshOperacionDrawerBadge(); } catch (_) {}
    }

    // Si el vendedor vino del fallback heurístico (no de Vision/LLM),
    // avisar al usuario para que verifique. Solo mostramos el toast una vez
    // por upload usando un flag en window.
    if (operacion.vendedor_detectado_heuristica && operacion.vendedor_nombre &&
        typeof showToast === 'function') {
        showToast(
            'Vendedor detectado',
            `Se autocompletó "${operacion.vendedor_nombre}" desde el PDF. Verificá que sea correcto.`,
            'info',
            5000
        );
    }
}

/**
 * Toggle del panel colapsable
 */
function toggleOperacionPanel() {
    const panel = document.getElementById('operacionPanel');
    if (panel) {
        panel.classList.toggle('collapsed');
    }
}

/**
 * Obtiene los datos actuales del panel de operación
 */
function getOperacionData() {
    return {
        numero_factura: document.getElementById('op_numero_factura')?.value || '',
        fecha_emision: document.getElementById('op_fecha_emision')?.value || '',
        vendedor_nombre: document.getElementById('op_vendedor_nombre')?.value || '',
        vendedor_id: document.getElementById('op_vendedor_id')?.value || '',
        vendedor_pais: document.getElementById('op_vendedor_pais')?.value || 'CN',
        comprador_nombre: document.getElementById('op_comprador_nombre')?.value || '',
        comprador_cuit: document.getElementById('op_comprador_cuit')?.value || '',
        moneda: document.getElementById('op_moneda')?.value || 'DOL',
        incoterm: document.getElementById('op_incoterm')?.value || 'FOB',
        flete: parseFloat(document.getElementById('op_flete')?.value) || 0,
        seguro: parseFloat(document.getElementById('op_seguro')?.value) || 0,
        // Transport data
        bl_numero: document.getElementById('op_bl')?.value || '',
        puerto_origen: document.getElementById('op_puerto_origen')?.value || '',
        puerto_destino: document.getElementById('op_puerto_destino')?.value || 'ARBUE',
        buque_nombre: document.getElementById('op_buque')?.value || '',
        viaje_numero: document.getElementById('op_viaje')?.value || '',
        fecha_embarque: document.getElementById('op_fecha_embarque')?.value || '',
        // Container data
        contenedor_numero: document.getElementById('op_contenedor')?.value || '',
        contenedor_tipo: document.getElementById('op_contenedor_tipo')?.value || '',
        contenedor_peso: parseFloat(document.getElementById('op_contenedor_peso')?.value) || 0
    };
}

function showSuccess(data, type) {
    let content = '';
    
    if (type === 'grouped') {
        const fname = (data && data.filename) ? data.filename : 'AVG_result.xlsx';
        const itemsCount = data && data.validated_items_count ? data.validated_items_count : (window.currentItems ? window.currentItems.length : 0);
        content = `
            <div class="result-item">
                <strong>Excel con agrupación generado:</strong> ${fname}
            </div>
            <div class="result-item">
                <strong>Items procesados:</strong> ${itemsCount}
            </div>
            <div class="result-item">
                <strong>Agrupación:</strong> Personalizada por despachante
            </div>
        `;
    } else if (type === 'manual') {
        // Mostrar agrupación en lugar de resultado directo
        showGrouping(window.lastProcessedItems || [], 'manual');
        return;
    } else if (type === 'excel') {
        // Mostrar agrupación en lugar de resultado directo
        showGrouping(window.lastProcessedItems || [], 'excel');
        return;
    } else if (type === 'pdf') {
        // Mostrar agrupación en lugar de resultado directo
        showGrouping(window.lastProcessedItems || [], 'pdf');
        return;
    }

    content += `
        <div class="result-item highlight">
            <strong>Archivo generado:</strong> ${data.filename}
        </div>
    `;

    successMessage.innerHTML = content;
    if (data && data.filename) {
        // Use fetch+blob for reliable download with auth
        downloadLink.href = '#';
        downloadLink.onclick = async function(e) {
            e.preventDefault();
            try {
                const resp = await fetch(`/download/${data.filename}`, { credentials: 'include' });
                if (resp.ok) {
                    const blob = await resp.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = data.filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                } else {
                    showToast('Error', 'No se pudo descargar el archivo', 'error');
                }
            } catch(err) {
                showToast('Error', 'Error de descarga: ' + err.message, 'error');
            }
            return false;
        };
    }
    results.classList.remove('hidden');
    
    // Scroll suave a resultados
    results.scrollIntoView({ behavior: 'smooth' });
}

// === PREMIUM: SELECTOR DE CLIENTE E HISTORIAL ===
async function populateClientSelect() {
    if (!clientSelect) return;
    clientSelect.innerHTML = '<option value="">Cargando clientes...</option>';
    try {
        const res = await fetch('/api/clientes/public');
        const data = await res.json();
        const opciones = ['<option value="">Selecciona un cliente...</option>']
            .concat((data.clientes || []).map(c => `<option value="${c.id}">${c.nombre}</option>`));
        clientSelect.innerHTML = opciones.join('');
        try{
            const uploadSel = document.getElementById('clientSelector');
            if (uploadSel){
                uploadSel.innerHTML = ['<option value="">(sin mapeo)</option>']
                    .concat((data.clientes || []).map(c => `<option value="${c.id}">${c.nombre}</option>`)).join('');
            }
        } catch(_){ }
    } catch (e) {
        clientSelect.innerHTML = '<option value="">(Error al cargar)</option>';
    }
}

function useClientFromCard(cid){
    try{
        if (clientSelect){ clientSelect.value = cid; localStorage.setItem('last_client_id',''+cid); }
        try {
            const uploadSel = document.getElementById('clientSelector');
            if (uploadSel){ uploadSel.value = cid; localStorage.setItem('last_client_id_upload',''+cid); }
        } catch(_) {}
        showToast('Cliente','Seleccionado en la barra superior');
    } catch(_){}
}

function openMappingForClient(cid, cname){
    try{
        // Seleccionar el cliente en el dropdown si existe
        if (clientSelect){ clientSelect.value = cid; }

        // Si estamos en la sección de clientes, necesitamos abrir el modal directamente
        const overlay = document.getElementById('mappingOverlay');
        const nameSpan = document.getElementById('mappingClientName');
        if (nameSpan) nameSpan.textContent = cname || 'cliente';

        // Cargar mapeo existente
        fetch(`/api/clientes/${cid}/column_mapping`).then(r=>r.json()).then(d=>{
            const m = d.mapping || {};
            document.getElementById('map_pieza').value = keyByValue(m,'pieza') || '';
            document.getElementById('map_descripcion').value = keyByValue(m,'descripcion') || '';
            document.getElementById('map_origen').value = keyByValue(m,'origen') || '';
            document.getElementById('map_cantidad').value = keyByValue(m,'cantidad') || '';
            document.getElementById('map_valor_unitario').value = keyByValue(m,'valor_unitario') || '';
            document.getElementById('map_peso_unitario').value = keyByValue(m,'peso_unitario') || '';
        }).catch(()=>{
            // Si no hay mapeo, dejar campos vacíos
            document.getElementById('map_pieza').value = '';
            document.getElementById('map_descripcion').value = '';
            document.getElementById('map_origen').value = '';
            document.getElementById('map_cantidad').value = '';
            document.getElementById('map_valor_unitario').value = '';
            document.getElementById('map_peso_unitario').value = '';
        });

        // Guardar el cliente ID temporalmente para el guardado
        overlay.setAttribute('data-current-client-id', cid);
        overlay.classList.add('active');
    } catch(err){
        console.error('Error opening mapping modal:', err);
        showToast('Error', 'No se pudo abrir el modal de mapeo', 'error');
    }
}

async function downloadClientTemplateForCard(cid, cname){
    try{
        const r = await fetch(`/api/clientes/${cid}/plantilla`, { method:'POST' });
        const d = await r.json();
        if (!d.success){ showToast('Error', d.detail || 'No se pudo generar la plantilla', 'error'); return; }
        const a = document.createElement('a');
        a.href = d.download_url; a.download = d.filename || `PLANTILLA_${cid}.xlsx`;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        showToast('Listo', `Plantilla de ${cname || 'cliente'}`);
    } catch(_){ showToast('Error','No se pudo descargar la plantilla','error'); }
}

async function refreshMappingStatusHint(){
    try{
        const hint = document.getElementById('mappingStatusHint');
        if (!hint) return;
        const sel = document.getElementById('clientSelector');
        const useMap = document.getElementById('useMappingToggleUpload');
        if (!sel || !useMap || !useMap.checked || !sel.value){ hint.textContent = ''; return; }
        const r = await fetch(`/api/clientes/${sel.value}/column_mapping`);
        const d = await r.json();
        const m = d.mapping || {};
        const mapped = Object.keys(m).length;
        hint.textContent = mapped > 0 ? `Mapeo activo (${mapped} campo(s))` : 'Mapeo activo (0 campos)';
    } catch(_){ }
}

async function saveOperationToHistory(items) {
    
    // Guardar siempre que hay cliente seleccionado (toggle es opcional)
    if (!clientSelect || !clientSelect.value) {
        return;
    }
    
    const resumen = {
        grupos: Array.from(new Set(items.map(i => i.tariff_group))).length,
        items: items.length,
        valor_total: items.reduce((s, i) => s + (i.cantidad || 0) * (i.valor_unitario || 0), 0)
    };
    
    
    try {
        const res = await fetch(`/api/clientes/${clientSelect.value}/operaciones`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ operation_id: `GROUPED_${Date.now()}`, resumen, items })
        });
    } catch (e) {
        console.error('📊 Error saving operation:', e);
    }
}

async function showHistoryModal() {
    if (!clientSelect || !clientSelect.value) {
        alert('Selecciona un cliente para ver su historial');
        return;
    }
    const overlay = document.getElementById('historyOverlay');
    const list = document.getElementById('historyList');
    overlay.classList.add('active');
    list.innerHTML = 'Cargando...';
    try {
        const res = await fetch(`/api/clientes/${clientSelect.value}/operaciones`);
        const data = await res.json();
        if (!data.operaciones || data.operaciones.length === 0) {
            list.innerHTML = '<div class="history-item">Sin operaciones previas</div>';
            return;
        }
        list.innerHTML = data.operaciones.map(op => {
            const fecha = op.fecha ? new Date(op.fecha).toLocaleString() : '-';
            const items = op.total_items || 0;
            const valor = op.total_value || 0;
            const opId = op.id || 'Sin ID';
            return `<div class="history-item"><strong>${opId}</strong> · ${fecha}<br>Items: ${items} · Valor: $${valor.toLocaleString()}</div>`;
        }).join('');
        // Wire export button
        try {
            const btn = document.getElementById('exportCsvBtn');
            if (btn) {
                const cid = clientSelect.value;
                btn.onclick = () => exportarCsv(cid, (clientSelect.options[clientSelect.selectedIndex]?.text || 'cliente'));
            }
        } catch (_) {}
    } catch (e) {
        list.innerHTML = '<div class="history-item">Error al cargar historial</div>';
    }
}

function hideHistoryModal() {
    const overlay = document.getElementById('historyOverlay');
    overlay.classList.remove('active');
}

// === PREMIUM: NOTAS POR NCM ===
function filterClientes() {
    const term = (document.getElementById('clientSearch')?.value || '').toLowerCase();
    const onlyFavs = document.getElementById('onlyFavs')?.checked === true;
    const list = document.getElementById('clientsDashboardList');
    const all = window.__allClients || [];
    const filtered = all.filter(c => {
        const byName = c.nombre.toLowerCase().includes(term);
        const byFav = onlyFavs ? c.favorito === true : true;
        return byName && byFav;
    });
    if (filtered.length === 0) {
        list.innerHTML = '<div class="client-card empty"><div class="client-info"><h4>Sin resultados</h4><p>Prueba otro nombre o quita filtros</p></div></div>';
        return;
    }
    // Render simplificado reutilizando estructura (con estrella SIEMPRE visible)
    list.innerHTML = filtered.map(cliente => `
        <div class=\"client-card\" data-client-id=\"${cliente.id}\" data-favorite=\"${cliente.favorito || false}\">
            <div class=\"client-info\">
                <h4>${cliente.favorito ? '⭐ ' : ''}${cliente.nombre}</h4>
                <p><i class=\"fas fa-envelope\"></i> ${cliente.email || 'Sin email'}</p>
                <p><i class=\"fas fa-phone\"></i> ${cliente.telefono || 'Sin teléfono'}</p>
                ${cliente.direccion ? `<p><i class=\\"fas fa-map-marker-alt\\"></i> ${cliente.direccion}</p>` : ''}
                ${cliente.notas ? `<p class=\\"client-notes\\"><i class=\\"fas fa-sticky-note\\"></i> ${cliente.notas}</p>` : ''}
            </div>
            <div class=\"client-actions\">
                <button class=\"btn-icon fav-btn ${cliente.favorito ? 'active' : ''}\" onclick=\"toggleFavorito('${cliente.id}')\" title=\"${cliente.favorito ? 'Quitar de favoritos' : 'Marcar como favorito'}\"><i class=\"fas fa-star\"></i></button>
                <button class=\"btn-icon edit-btn\" onclick=\"editCliente('${cliente.id}')\" title=\"Editar\"><i class=\"fas fa-edit\"></i></button>
                <button class=\"btn-icon\" onclick=\"quickViewHistory('${cliente.id}', '${cliente.nombre.replace(/'/g, "\\\\'" )}')\" title=\"Historial\"><i class=\"fas fa-history\"></i><span class=\"badge-count\" id=\"hist-${cliente.id}\" style=\"display:none;\">0</span></button>
                <button class=\"btn-icon delete-btn\" onclick=\"deleteCliente('${cliente.id}', '${cliente.nombre}')\" title=\"Eliminar\"><i class=\"fas fa-trash\"></i></button>
            </div>
            <div class=\"client-cta-bar\"><button class=\"cta-history\" onclick=\"quickViewHistory('${cliente.id}', '${cliente.nombre.replace(/'/g, "\\\\'" )}')\"><i class=\"fas fa-history\"></i> Ver historial</button></div>
        </div>`).join('');
    // Reponer contadores
    filtered.forEach(async (c) => {
        try {
            const r = await fetch(`/api/clientes/${c.id}/operaciones`);
            const d = await r.json();
            const el = document.getElementById(`hist-${c.id}`);
            const n = (d.operaciones || []).length;
            if (el && n > 0) { el.textContent = n; el.style.display = 'inline-flex'; }
        } catch (_) {}
    });
}
function addNotesButtonsToRows() {
    const rows = document.querySelectorAll('.item-grouping-row');
    rows.forEach(row => {
        const ncmInput = row.querySelector('.edit-input.ncm');
        const tariff = (ncmInput?.value || '').replace(/[^0-9]/g, '').substring(0, 4);
        
        // Verificar si hay notas para este NCM y marcar el botón
        if (tariff && tariff.length >= 4) {
            refreshNoteBadge(row, tariff);
        }
    });
}

function ensureNoteButton(row, tariff) {
    // Desactivado en tabla simplificada - no hay group-indicator
    return;
}

async function refreshNoteBadge(row, tariff) {
    try {
        if (!tariff || tariff.length < 4) return; // guarda: no pedir si no hay NCM
        // ✅ Usar sistema throttled en lugar de fetch directo
        await fetchNotasNCMThrottled(tariff, row);
    } catch (error) {
        console.warn(`⚠️ No se pudieron cargar notas para ${tariff}:`, error.message);
    }
}

// === SUGERIR NCM CON IA ===
async function sugerirNCM(itemIndex) {
    const row = document.querySelector(`.item-grouping-row[data-item-index="${itemIndex}"]`);
    if (!row) return;
    
    const descInput = row.querySelector('.desc-input');
    const descripcion = descInput?.value?.trim() || '';
    const dropdown = document.getElementById(`ncm-dropdown-${itemIndex}`);
    
    if (!descripcion || descripcion.length < 3) {
        showToast('Info', 'Necesito una descripción para sugerir NCM', 'info');
        return;
    }
    
    // Mostrar loading
    dropdown.innerHTML = '<div class="ncm-sug-loading">✨ Buscando sugerencias...</div>';
    dropdown.classList.remove('hidden');
    
    try {
        const res = await fetch('/api/ncm/sugerir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ descripcion })
        });
        const data = await res.json();
        
        if (!data.sugerencias || data.sugerencias.length === 0) {
            dropdown.innerHTML = '<div class="ncm-sug-empty">Sin sugerencias para esta descripción</div>';
            setTimeout(() => dropdown.classList.add('hidden'), 2000);
            return;
        }
        
        dropdown.innerHTML = `
            <div class="ncm-sug-header">Sugerencias para: <strong>${descripcion.slice(0, 30)}${descripcion.length > 30 ? '...' : ''}</strong></div>
            ${data.sugerencias.map(s => `
                <div class="ncm-sug-item" onclick="aplicarNCM(${itemIndex}, '${s.ncm}', '${descripcion.replace(/'/g, "\\'")}')">
                    <span class="ncm-sug-code">${s.ncm}</span>
                    <span class="ncm-sug-desc">${s.desc}</span>
                    <span class="ncm-sug-badge ${s.source}">${s.source === 'historial' ? '📋 Histórico' : '✨ IA'}</span>
                </div>
            `).join('')}
            <div class="ncm-sug-footer" onclick="cerrarDropdownNCM(${itemIndex})">✕ Cerrar</div>
        `;
    } catch (e) {
        dropdown.innerHTML = '<div class="ncm-sug-empty">Error al obtener sugerencias</div>';
        setTimeout(() => dropdown.classList.add('hidden'), 2000);
    }
}

function aplicarNCM(itemIndex, ncm, descripcion) {
    const row = document.querySelector(`.item-grouping-row[data-item-index="${itemIndex}"]`);
    if (!row) return;
    
    const ncmInput = row.querySelector('.ncm');
    if (ncmInput) {
        ncmInput.value = ncm;
        ncmInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // Guardar en historial para aprender
    fetch('/api/ncm/guardar-uso', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ descripcion, ncm })
    }).catch(() => {});
    
    cerrarDropdownNCM(itemIndex);
    showToast('NCM Aplicado', `${ncm} asignado al item`, 'success');
}

function cerrarDropdownNCM(itemIndex) {
    const dropdown = document.getElementById(`ncm-dropdown-${itemIndex}`);
    if (dropdown) dropdown.classList.add('hidden');
}

// Cerrar dropdowns al hacer click fuera (DESHABILITADO - feature NCM sugerencias no activa)
// document.addEventListener('click', (e) => {
//     if (!e.target.closest('.ncm-cell')) {
//         document.querySelectorAll('.ncm-suggestions-dropdown').forEach(d => d.classList.add('hidden'));
//     }
// });


async function openNoteModal(ncmCode) {
    const ncm = (ncmCode || '').replace(/[^0-9]/g, '').substring(0, 4);
    
    // Validar que haya NCM suficiente
    if (!ncm || ncm.length < 4) {
        showToast('NCM Requerido', 'Ingresá al menos 4 dígitos del NCM para agregar notas', 'info');
        return;
    }
    
    document.getElementById('noteModalNcm').textContent = ncm;
    document.getElementById('noteNcm').value = ncm;
    const overlay = document.getElementById('noteOverlay');
    const list = document.getElementById('noteList');
    overlay.classList.add('active');
    list.innerHTML = 'Cargando...';
    try {
        // ✅ Usar sistema throttled en lugar de fetch directo
        const data = await fetchNotasNCMThrottled(ncm);
        if (!data.notas || data.notas.length === 0) {
            list.innerHTML = '<div class="note-item"><i class="fas fa-info-circle"></i> Sin notas aún.</div>';
        } else {
            list.innerHTML = data.notas.map((t, i) => `
                <div class=\"note-item\">
                    <i class=\"fas fa-sticky-note\"></i>
                    <span contenteditable=\"true\" onblur=\"editarNotaNcm('${ncm}', ${i}, this.innerText)\">${t}</span>
                    <button class=\"btn-icon delete-btn\" title=\"Eliminar\" onclick=\"eliminarNotaNcm('${ncm}', ${i})\"><i class=\"fas fa-trash\"></i></button>
                </div>`).join('');
        }
    } catch (e) {
        list.innerHTML = '<div class="note-item">Error al cargar notas</div>';
    }
}

function hideNoteModal() {
    document.getElementById('noteOverlay').classList.remove('active');
    document.getElementById('noteText').value = '';
}

async function saveNcmNote() {
    const ncm = document.getElementById('noteNcm').value;
    const nota = document.getElementById('noteText').value.trim();
    if (!nota) { showToast('Error', 'Escribe una nota', 'error'); return; }
    try {
        // ✅ Invalidar caché ANTES de hacer POST (la nota será nueva)
        VUCE_NOTAS_QUEUE.cache.delete(ncm);
        await fetch('/api/ncm/notas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ncm, nota })
        });
        // Refrescar modal sin cerrarlo
        document.getElementById('noteText').value = '';
        const list = document.getElementById('noteList');
        list.innerHTML = 'Actualizando...';
        // ✅ Invalidar caché y usar sistema throttled
        VUCE_NOTAS_QUEUE.cache.delete(ncm);
        const data = await fetchNotasNCMThrottled(ncm);
        list.innerHTML = (data.notas || []).map((t,i) => `
            <div class=\"note-item\">
                <i class=\"fas fa-sticky-note\"></i>
                <span contenteditable=\"true\" onblur=\"editarNotaNcm('${ncm}', ${i}, this.innerText)\">${t}</span>
                <button class=\"btn-icon delete-btn\" title=\"Eliminar\" onclick=\"eliminarNotaNcm('${ncm}', ${i})\"><i class=\"fas fa-trash\"></i></button>
            </div>`).join('');
        // Refrescar badges actuales
        document.querySelectorAll('.item-grouping-row').forEach(row => {
            const tariff = row.querySelector('.edit-input.ncm').value.substring(0, 4);
            if (tariff === ncm) refreshNoteBadge(row, tariff);
        });
    } catch (e) {
        alert('Error al guardar nota');
    }
}

async function editarNotaNcm(ncm, idx, texto){
    try {
        await fetch(`/api/ncm/notas/${ncm}/${idx}`, { method: 'PUT', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ nota: texto.trim() })});
        showToast('Completado', 'Nota actualizada');
        // ✅ Invalidar caché después de editar
        VUCE_NOTAS_QUEUE.cache.delete(ncm);
        document.querySelectorAll('.item-grouping-row').forEach(row => { const t = row.querySelector('.edit-input.ncm').value.substring(0,4); if (t===ncm) refreshNoteBadge(row, t); });
    } catch (e) { showToast('Error', 'No se pudo editar la nota', 'error'); }
}

async function eliminarNotaNcm(ncm, idx){
    try {
        await fetch(`/api/ncm/notas/${ncm}/${idx}`, { method: 'DELETE' });
        showToast('Completado', 'Nota eliminada');
        // ✅ Invalidar caché después de eliminar
        VUCE_NOTAS_QUEUE.cache.delete(ncm);
        openNoteModal(ncm); // recargar
        document.querySelectorAll('.item-grouping-row').forEach(row => { const t = row.querySelector('.edit-input.ncm').value.substring(0,4); if (t===ncm) refreshNoteBadge(row, t); });
    } catch (e) { showToast('Error', 'No se pudo eliminar la nota', 'error'); }
}

function hideResults() {
    results.classList.add('hidden');
}

function showError(message) {
    // Toast efímero (notificación inmediata) + panel persistente para que el
    // usuario pueda releer el error y entender qué hacer (UX Overhaul Fase 4).
    try { showToast('Error', message, 'error'); } catch (_) {}
    if (!errorMessage) return;
    errorMessage.innerHTML = `
        <div class="error-banner">
            <div class="error-banner-icon" aria-hidden="true"><i class="fas fa-exclamation-triangle"></i></div>
            <div class="error-banner-text">
                <strong>Algo no funcionó</strong>
                <p>${String(message || '').replace(/</g, '&lt;')}</p>
                <p class="error-banner-hint">Intentá de nuevo. Si persiste, probá con otra factura o ingresá los datos a mano.</p>
            </div>
            <button type="button" class="error-banner-close" onclick="hideError()" aria-label="Cerrar mensaje de error" title="Cerrar">
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
        </div>
    `;
    errorMessage.classList.remove('hidden');
    try { errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (_) {}
}

function hideError() {
    if (!errorMessage) return;
    errorMessage.classList.add('hidden');
    errorMessage.innerHTML = '';
}


// === FUNCIÓN DE LOGOUT ===
async function logout() {
    const confirmed = await showConfirmation('¿Estás seguro de que quieres cerrar sesión?');
    if (confirmed) {
        // Mostrar loading en el botón
        const logoutBtn = document.getElementById('logoutBtn');
        const originalText = logoutBtn.innerHTML;
        logoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cerrando...';
        logoutBtn.disabled = true;
        
        // Llamar al endpoint de logout
        fetch('/logout', {
            method: 'POST'
        })
        .then(response => {
            if (response.ok) {
                // Bug fix: limpiar localStorage para evitar que quede token viejo
                ['access_token', 'user_plan', 'user_name', 'user_roles', 'cdi_new_user'].forEach(k => localStorage.removeItem(k));
                // Redirigir a landing con mensaje de éxito
                window.location.href = '/?logout=success';
            } else {
                throw new Error('Error en logout');
            }
        })
        .catch(error => {
            logoutBtn.innerHTML = originalText;
            logoutBtn.disabled = false;
            alert('Error al cerrar sesión: ' + error.message);
        });
    }
}

// Lógica para el nuevo modal de confirmación
let resolveConfirmation;
const confirmOverlay = document.getElementById('confirmOverlay');
const confirmMessage = document.getElementById('confirmMessage');
const confirmAcceptBtn = document.getElementById('confirmAcceptBtn');
const confirmCancelBtn = document.getElementById('confirmCancelBtn');

confirmAcceptBtn.addEventListener('click', () => {
    confirmOverlay.classList.add('hidden');
    if (resolveConfirmation) resolveConfirmation(true);
});

confirmCancelBtn.addEventListener('click', () => {
    confirmOverlay.classList.add('hidden');
    if (resolveConfirmation) resolveConfirmation(false);
});

function showConfirmation(message) {
    return new Promise(resolve => {
        confirmMessage.textContent = message;
        confirmOverlay.classList.remove('hidden');
        resolveConfirmation = resolve;
    });
}
// FIN Lógica para el nuevo modal de confirmación


// === FUNCIONES DE GESTIÓN DE CLIENTES ===

// Helper to render client cards consistently
function populateClientCards(listEl, orderedClients){
    // Filtrar clientes inválidos
    const validClients = orderedClients.filter(c => c && c.nombre);
    if (validClients.length === 0) {
        listEl.innerHTML = '<div class="client-card empty"><div class="client-info"><h4>No hay clientes cargados</h4><p>Agregá tu primer cliente para empezar</p></div></div>';
        return;
    }
    listEl.innerHTML = validClients.map(cliente => {
        const nombreSafe = (cliente.nombre || 'Sin nombre').replace(/'/g, "\\'");
        return `
        <div class="client-card" data-client-id="${cliente.id}" data-favorite="${cliente.favorito || false}">
            <div class="client-info">
                <h4>${cliente.favorito ? '⭐ ' : ''}${cliente.nombre || 'Sin nombre'}</h4>
                <p><i class="fas fa-envelope"></i> ${cliente.email || 'Sin email'}</p>
                <p><i class="fas fa-phone"></i> ${cliente.telefono || 'Sin teléfono'}</p>
                ${cliente.direccion ? `<p><i class=\"fas fa-map-marker-alt\"></i> ${cliente.direccion}</p>` : ''}
                ${cliente.notas ? `<p class=\"client-notes\"><i class=\"fas fa-sticky-note\"></i> ${cliente.notas}</p>` : ''}
                <div id="mapcov-${cliente.id}" class="mapping-indicator">
                    <span class="mapping-label">Mapeo: <strong>--</strong></span>
                    <div class="mapping-progress">
                        <div class="mapping-progress-bar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            <div class="client-actions">
                <button class="btn-icon fav-btn ${cliente.favorito ? 'active' : ''}" onclick="toggleFavorito('${cliente.id}')" title="${cliente.favorito ? 'Quitar de favoritos' : 'Marcar como favorito'}"><i class="fas fa-star"></i></button>
                <button class="btn-icon edit-btn" onclick="editCliente('${cliente.id}')" title="Editar"><i class="fas fa-edit"></i></button>
                <button class="btn-icon" onclick="quickViewHistory('${cliente.id}', '${nombreSafe}')" title="Historial"><i class="fas fa-history"></i><span class="badge-count" id="hist-${cliente.id}" style="display:none;">0</span></button>
                <button class="btn-icon delete-btn" onclick="deleteCliente('${cliente.id}', '${nombreSafe}')" title="Eliminar"><i class="fas fa-trash"></i></button>
            </div>
            <div class="client-cta-bar">
                <button class="cta-demo" data-action="use-client" data-client-id="${cliente.id}" data-client-name="${nombreSafe}"><i class="fas fa-check"></i> Usar</button>
                <button class="cta-demo" data-action="mapping-client" data-client-id="${cliente.id}" data-client-name="${nombreSafe}"><i class="fas fa-columns"></i> Mapeo</button>
                <button class="cta-demo" data-action="template-client" data-client-id="${cliente.id}" data-client-name="${nombreSafe}"><i class="fas fa-file-excel"></i> Plantilla</button>
                <button class="cta-demo" onclick="exportarCsv('${cliente.id}', '${nombreSafe}')"><i class="fas fa-file-csv"></i> CSV</button>
                <button class="cta-history" onclick="quickViewHistory('${cliente.id}', '${nombreSafe}')"><i class="fas fa-history"></i> Historial</button>
            </div>
        </div>`;
    }).join('');
    // Cargar cobertura de mapeo por cliente
    orderedClients.forEach(async c => {
        try {
            const r = await fetch(`/api/clientes/${c.id}/column_mapping`);
            const d = await r.json();
            const m = d.mapping || {};
            const count = Object.keys(m).length;
            const percentage = Math.round((count / 6) * 100);
            const el = document.getElementById(`mapcov-${c.id}`);
            if (el) {
                const label = el.querySelector('.mapping-label strong');
                const bar = el.querySelector('.mapping-progress-bar');
                if (label) label.textContent = `${count}/6`;
                if (bar) {
                    bar.style.width = `${percentage}%`;
                    bar.style.background = percentage === 100 ? '#10b981' : (percentage >= 50 ? '#3b82f6' : '#f59e0b');
                }
            }
        } catch(_){}
    });
}

// Mostrar modal para agregar cliente
function showAddClientModal() {
    document.getElementById('clientModalTitle').textContent = 'Agregar Cliente';
    document.getElementById('clientForm').reset();
    document.getElementById('clientId').value = '';
    document.getElementById('clientSubmitBtn').innerHTML = '<i class="fas fa-save"></i> Guardar Cliente';
    document.getElementById('clientOverlay').classList.add('active');
    document.getElementById('clientNombre').focus();
}

// Ocultar modal de cliente
function hideClientModal() {
    document.getElementById('clientOverlay').classList.remove('active');
    document.getElementById('clientForm').reset();
}

// Cargar lista de clientes
async function loadClientes() {
    const clientsList = document.getElementById('clientsDashboardList');
    clientsList.innerHTML = '<div class="client-card loading"><div class="client-info"><h4>Cargando clientes...</h4><p>Espera un momento</p></div></div>';

    try {
        const response = await fetch('/api/clientes/public');

        // Validar respuesta antes de parsear
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();

        // Validar estructura de datos
        if (!data.success && !data.clientes) {
            throw new Error(data.detail || 'Respuesta inválida del servidor');
        }

        if (data.clientes && data.clientes.length > 0) {
            // Ordenar favoritos primero
            const ordered = [...data.clientes].sort((a,b)=> (b.favorito===true) - (a.favorito===true));
            window.__allClients = ordered; // guardar en memoria para filtros
            populateClientCards(clientsList, ordered);

            // Cargar contadores de historial en paralelo
            ordered.forEach(async (c) => {
                try {
                    const r = await fetch(`/api/clientes/${c.id}/operaciones`);
                    const d = await r.json();
                    const el = document.getElementById(`hist-${c.id}`);
                    const n = (d.operaciones || []).length;
                    if (el && n > 0) { el.textContent = n; el.style.display = 'inline-flex'; }
                } catch (_) {}
            });
        } else {
            clientsList.innerHTML = '<div class="client-card empty"><div class="client-info"><h4>No hay clientes registrados</h4><p>Agrega tu primer cliente para comenzar</p></div></div>';
        }
    } catch (error) {
        console.error('Error cargando clientes:', error);
        clientsList.innerHTML = '<div class="client-card empty"><div class="client-info"><h4>No hay clientes cargados</h4><p>Agregá tu primer cliente para empezar</p></div></div>';
    }
}

// Ver historial rápido desde la tarjeta
async function quickViewHistory(clienteId, nombre) {
    const overlay = document.getElementById('historyOverlay');
    const list = document.getElementById('historyList');
    const metricsBox = document.getElementById('historyMetrics');
    overlay.classList.add('active');
    list.innerHTML = `Cargando historial de <strong>${nombre}</strong>...`;
    metricsBox.innerHTML = '';
    try {
        // Cargar métricas
        try {
            const mres = await fetch(`/api/clientes/${clienteId}/metricas`);
            const m = await mres.json();
            metricsBox.innerHTML = `
                <div class="history-metrics">
                    <div class="metric-card"><div class="label">Operaciones</div><div class="value">${m.total_operaciones ?? 0}</div></div>
                    <div class="metric-card"><div class="label">Items</div><div class="value">${m.total_items ?? 0}</div></div>
                    <div class="metric-card"><div class="label">Valor Total</div><div class="value">$${(m.valor_total ?? 0).toLocaleString()}</div></div>
                    <div class="metric-card"><div class="label">Promedio Items</div><div class="value">${m.promedio_items_por_operacion ?? 0}</div></div>
                    <div class="metric-card"><div class="label">Último</div><div class="value">${m.ultimo_movimiento ?? '-'}</div></div>
                </div>`;
        } catch (_) {}

        const res = await fetch(`/api/clientes/${clienteId}/operaciones`);
        const data = await res.json();
        if (!data.operaciones || data.operaciones.length === 0) {
            list.innerHTML = '<div class="history-item">Sin operaciones previas</div>';
            return;
        }
        list.innerHTML = data.operaciones.map(op => {
            const fecha = op.fecha ? new Date(op.fecha).toLocaleString() : '-';
            const items = op.total_items || 0;
            const valor = op.total_value || 0;
            const opId = op.id || 'Sin ID';
            return `<div class=\"history-item\"><strong>${opId}</strong> · ${fecha}<br>Items: ${items} · Valor: $${valor.toLocaleString()}</div>`;
        }).join('');
    } catch (e) {
        list.innerHTML = '<div class="history-item">Error al cargar historial</div>';
    }
}

// Cargar operaciones demo y abrir historial
async function cargarDemoYVer(clienteId, nombre) {
    try {
        showToast('Generando', 'Creando operaciones de ejemplo...');
        await fetch(`/api/clientes/${clienteId}/operaciones/demo`, { method: 'POST' });
        await quickViewHistory(clienteId, nombre);
        showToast('Listo', 'Se cargaron operaciones de ejemplo');
    } catch (e) {
        showToast('Error', 'No se pudieron crear operaciones demo', 'error');
    }
}

async function exportarCsv(clienteId, nombre) {
    try {
        showToast('Exportando', `Generando CSV para ${nombre}...`);
        const url = `/api/clientes/${clienteId}/export.csv`;
        const a = document.createElement('a');
        a.href = url;
        a.download = `historial_${nombre}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        showToast('Listo', 'CSV generado');
    } catch (e) {
        showToast('Error', 'No se pudo generar el CSV', 'error');
    }
}
// Editar cliente
function editCliente(clienteId) {
    // Usar datos desde memoria (window.__allClients) en lugar de hacer fetch
    const cliente = (window.__allClients || []).find(c => c.id === clienteId);
    if (cliente) {
        document.getElementById('clientId').value = cliente.id;
        document.getElementById('clientNombre').value = cliente.nombre;
        document.getElementById('clientEmail').value = cliente.email || '';
        document.getElementById('clientTelefono').value = cliente.telefono || '';
        document.getElementById('clientDireccion').value = cliente.direccion || '';
        document.getElementById('clientNotas').value = cliente.notas || '';

        document.getElementById('clientModalTitle').textContent = 'Editar Cliente';
        document.getElementById('clientSubmitBtn').innerHTML = '<i class="fas fa-save"></i> Actualizar Cliente';
        document.getElementById('clientOverlay').classList.add('active');
        document.getElementById('clientNombre').focus();
    } else {
        showToast('Error', 'Cliente no encontrado', 'error');
    }
}

// Eliminar cliente
async function deleteCliente(clienteId, nombre) {
    const confirmed = await showConfirmation(`¿Estás seguro de que quieres eliminar al cliente "${nombre}"?`);
    if (confirmed) {
        try {
            // Usar endpoint público (sin autenticación)
            const response = await fetch(`/api/clientes/public/${clienteId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al eliminar cliente');
            }

            const data = await response.json();

            // Verificar respuesta del servidor
            if (!data.success) {
                throw new Error(data.detail || 'Error al eliminar cliente');
            }

            showToast('✅ Completado', `Cliente "${nombre}" eliminado exitosamente`);

            // Actualizar lista maestra en memoria
            if (window.__allClients) {
                window.__allClients = window.__allClients.filter(c => c.id !== clienteId);
            }

            // Remover la card del DOM sin recargar toda la lista
            const card = document.querySelector(`[data-client-id="${clienteId}"]`);
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => card.remove(), 300);
            }

        } catch (error) {
            console.error('Error eliminando cliente:', error);
            showToast('❌ Error', error.message || 'Error de conexión al eliminar cliente', 'error');
        }
    }
}

// Manejar envío del formulario de cliente
async function handleClientSubmit(event) {
    event.preventDefault();

    const clienteData = {
        nombre: document.getElementById('clientNombre').value.trim(),
        email: document.getElementById('clientEmail').value.trim(),
        telefono: document.getElementById('clientTelefono').value.trim(),
        direccion: document.getElementById('clientDireccion').value.trim(),
        notas: document.getElementById('clientNotas').value.trim()
    };

    // Validar campos requeridos
    if (!clienteData.nombre) {
        showToast('❌ Error', 'El nombre del cliente es requerido', 'error');
        document.getElementById('clientNombre').focus();
        return;
    }

    if (!clienteData.email) {
        showToast('❌ Error', 'El email del cliente es requerido', 'error');
        document.getElementById('clientEmail').focus();
        return;
    }

    // Validar formato de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(clienteData.email)) {
        showToast('❌ Error', 'El formato del email no es válido', 'error');
        document.getElementById('clientEmail').focus();
        return;
    }

    const clienteId = document.getElementById('clientId').value;
    const isEdit = clienteId !== '';

    // Mostrar loading
    const submitBtn = document.getElementById('clientSubmitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
    submitBtn.disabled = true;

    try {
        // Usar endpoints públicos para evitar error 403
        const url = isEdit ? `/api/clientes/public/${clienteId}` : '/api/clientes/public';
        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(clienteData)
        });

        // Validar respuesta antes de parsear
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al guardar cliente');
        }

        const data = await response.json();

        // Validar estructura de respuesta
        if (!data.success && !data.mensaje && !data.id && !data.cliente) {
            throw new Error('Respuesta inválida del servidor');
        }

        showToast('✅ Completado', isEdit ? 'Cliente actualizado exitosamente' : 'Cliente creado exitosamente');
        hideClientModal();
        loadClientes(); // Recargar lista

    } catch (error) {
        console.error('Error guardando cliente:', error);
        showToast('❌ Error', error.message || 'Error de conexión al guardar cliente', 'error');
    } finally {
        // Restaurar botón
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Cerrar modal de cliente con Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideClientModal();
    }
});

// Cerrar modal de cliente haciendo click fuera
document.addEventListener('DOMContentLoaded', function() {
    const clientOverlay = document.getElementById('clientOverlay');
    if (clientOverlay) {
        clientOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                hideClientModal();
            }
        });
    }
});

// === UX extra para modal de confirmación ===
(function () {
    if (typeof window.__confirmModalUXEnhancements === 'boolean') return;
    window.__confirmModalUXEnhancements = true;

    // Cerrar al hacer clic fuera del contenido
    if (typeof confirmOverlay !== 'undefined') {
        confirmOverlay.addEventListener('click', (e) => {
            if (e.target === confirmOverlay) {
                confirmOverlay.classList.add('hidden');
                if (typeof resolveConfirmation === 'function') resolveConfirmation(false);
            }
        });
    }

    // Teclas rápidas: Esc = cancelar, Enter = aceptar
    document.addEventListener('keydown', (e) => {
        if (!confirmOverlay || confirmOverlay.classList.contains('hidden')) return;
        if (e.key === 'Escape') {
            confirmOverlay.classList.add('hidden');
            if (typeof resolveConfirmation === 'function') resolveConfirmation(false);
        } else if (e.key === 'Enter') {
            confirmOverlay.classList.add('hidden');
            if (typeof resolveConfirmation === 'function') resolveConfirmation(true);
        }
    });

    // Enfocar botón Aceptar al abrir
    const originalShowConfirmation = typeof showConfirmation === 'function' ? showConfirmation : null;
    if (originalShowConfirmation) {
        window.showConfirmation = function (message) {
            return new Promise((resolve) => {
                confirmMessage.textContent = message;
                confirmOverlay.classList.remove('hidden');
                resolveConfirmation = resolve;
                // Defer para asegurar que el botón exista y sea visible
                setTimeout(() => {
                    try { confirmAcceptBtn && confirmAcceptBtn.focus(); } catch (_) {}
                }, 0);
            });
        };
    }
})();
// === FIN UX extra modal ===

// === TOASTS UNIFICADOS ===
function showToast(title, msg, type='info', timeout=3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return alert(`${title}: ${msg}`); // fallback
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    const icon = type === 'error' ? 'fa-circle-xmark' : 'fa-circle-check';
    el.innerHTML = `<div class="icon"><i class="fas ${icon}"></i></div><div><div class="title">${title}</div><div class="msg">${msg}</div></div>`;
    container.appendChild(el);
    setTimeout(()=>{ el.remove(); }, timeout);
}

// Favoritos: marcar / desmarcar
async function toggleFavorito(clienteId) {
    try {
        // Buscar la card por data-client-id
        const card = document.querySelector(`[data-client-id="${clienteId}"]`);
        if (!card) {
            throw new Error(`No se encontró la tarjeta del cliente con ID: ${clienteId}`);
        }

        const estadoActual = card.getAttribute('data-favorite') === 'true';
        const nuevo = !estadoActual;

        const res = await fetch(`/api/clientes/${clienteId}/favorito`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ favorito: nuevo })
        });

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'Error al actualizar favorito');
        }

        showToast('✅ Completado', nuevo ? '⭐ Marcado como favorito' : 'Quitado de favoritos');

        // Actualizar la lista maestra en memoria
        if (window.__allClients) {
            const client = window.__allClients.find(c => c.id === clienteId);
            if (client) {
                client.favorito = nuevo;
            }
        }

        // Verificar si el filtro "Solo favoritos" está activo
        const onlyFavsCheckbox = document.getElementById('onlyFavs');
        const onlyFavsActive = onlyFavsCheckbox?.checked === true;

        // Si "Solo favoritos" está activo y se desmarcó un favorito, re-filtrar
        if (onlyFavsActive && !nuevo) {
            // Re-aplicar filtro para que desaparezca de la lista
            filterClientes();
        } else {
            // Actualizar UI de la card sin re-renderizar toda la lista
            card.setAttribute('data-favorite', nuevo);
            const favBtn = card.querySelector('.fav-btn');
            if (favBtn) {
                if (nuevo) {
                    favBtn.classList.add('active');
                    favBtn.title = 'Quitar de favoritos';
                } else {
                    favBtn.classList.remove('active');
                    favBtn.title = 'Marcar como favorito';
                }
                // Forzar que pierda el foco (evita que quede amarillo)
                favBtn.blur();
            }

            // Actualizar título con estrella
            const titleEl = card.querySelector('.client-info h4');
            if (titleEl) {
                const text = titleEl.textContent.replace('⭐ ', '');
                titleEl.textContent = nuevo ? `⭐ ${text}` : text;
            }
        }

    } catch (e) {
        console.error('Error toggleFavorito:', e);
        showToast('❌ Error', e.message || 'No se pudo actualizar favorito', 'error');
    }
}

// ===== BACKUP/RESTORE LOCALSTORAGE =====

/**
 * Backup automático de localStorage al servidor
 */
async function autoBackupLocalStorage() {
    try {
        const data = {
            clients: JSON.parse(localStorage.getItem('clients') || '[]'),
            ncmNotes: JSON.parse(localStorage.getItem('ncmNotes') || '{}'),
            selectedClient: localStorage.getItem('selectedClient'),
            autoNcmEnabled: localStorage.getItem('autoNcmEnabled'),
            timestamp: new Date().toISOString()
        };
        
        const response = await fetch('/api/backup/localStorage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
        } else {
            console.warn('⚠️ Error en backup automático:', result.detail);
        }
    } catch (error) {
        console.error('❌ Error en backup automático:', error);
    }
}

/**
 * Restaurar localStorage desde el servidor al cargar la página
 * NOTA: Restauración de clientes DESACTIVADA para evitar mezcla de datos entre usuarios
 */
async function autoRestoreLocalStorage() {
    try {
        const response = await fetch('/api/restore/localStorage');
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            
            // IMPORTANTE: NO restaurar clientes ya que son por usuario
            // Los clientes deben venir del servidor via /api/clientes/public
            // que debería filtrar por usuario en el futuro
            
            // Solo restaurar notas NCM (que son globales por ahora)
            const currentNotes = localStorage.getItem('ncmNotes');
            if (!currentNotes || currentNotes === '{}') {
                if (data.ncmNotes && Object.keys(data.ncmNotes).length > 0) {
                    localStorage.setItem('ncmNotes', JSON.stringify(data.ncmNotes));
                }
            }
            
            // Restaurar configuraciones (también globales por ahora)
            if (data.autoNcmEnabled && !localStorage.getItem('autoNcmEnabled')) {
                localStorage.setItem('autoNcmEnabled', data.autoNcmEnabled);
            }
            
        } else {
        }
    } catch (error) {
        console.error('❌ Error en restore automático:', error);
    }
}

// Ejecutar restore al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    // Ejecutar restore después de un pequeño delay para asegurar que el DOM esté listo
    setTimeout(autoRestoreLocalStorage, 1000);
});

// Backup automático cada 5 minutos
setInterval(autoBackupLocalStorage, 5 * 60 * 1000);

// Backup automático cuando se detectan cambios importantes
const originalSetItem = localStorage.setItem;
localStorage.setItem = function(key, value) {
    originalSetItem.call(this, key, value);
    
    // Si es un dato crítico, hacer backup inmediato
    if (['clients', 'ncmNotes', 'selectedClient'].includes(key)) {
        // Debounce: solo backup si no se hizo uno en los últimos 30 segundos
        if (!window.lastBackupTime || (Date.now() - window.lastBackupTime) > 30000) {
            window.lastBackupTime = Date.now();
            setTimeout(autoBackupLocalStorage, 2000); // Delay para evitar múltiples backups rápidos
        }
    }
};

// Fix label-for warnings
(function fixLabels(){
    const lbls = document.querySelectorAll('.toolbar-checkbox');
    lbls.forEach((wrap, idx)=>{
        const input = wrap.querySelector('input');
        if (input && !input.id) { input.id = `chk_${idx}`; }
        if (wrap.tagName.toLowerCase() === 'label') {
            wrap.setAttribute('for', input.id);
        }
    });
})();

// ==================== UX IMPROVEMENTS ====================

/**
 * Actualizar contador de items seleccionados en barra batch
 * MEJORADO: Oculta completamente la barra si count = 0
 */
function updateBatchSelectionCounter() {
    // Bug histórico: usaba .row-select pero los checkboxes reales son .row-checkbox.
    // La barra de batch nunca aparecía. Audited en plan UX redesign.
    const selected = document.querySelectorAll('.row-checkbox:checked');
    const bar = document.getElementById('batchActionsBar');
    const label = bar?.querySelector('.batch-counter');

    if (selected.length > 0) {
        const n = selected.length;
        if (label) label.textContent = `${n} item${n === 1 ? '' : 's'} seleccionado${n === 1 ? '' : 's'}`;
        if (bar) bar.classList.remove('hidden');
    } else {
        if (bar) bar.classList.add('hidden');
    }

    // ncmBulkBar fue eliminada por duplicar funcionalidad con batchActionsBar.
    // Si todavía existe en el DOM (legacy), la mantenemos sincronizada por compat.
    const bulkBar = document.getElementById('ncmBulkBar');
    if (bulkBar) {
        if (selected.length > 0) bulkBar.classList.remove('bulk-hidden');
        else bulkBar.classList.add('bulk-hidden');
    }
}

/**
 * Toggle menú de opciones avanzadas
 */
function toggleAdvancedMenu() {
    const menu = document.getElementById('advancedMenu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

/**
 * Toggle menú batch
 */
function toggleBatchMenu() {
    const menu = document.getElementById('batchMenu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

/**
 * Aplicar origen a items seleccionados (versión inline sin modal)
 */
function batchApplyOrigenInline() {
    const select = document.getElementById('bulkOrigenSelect');
    const manualInput = document.getElementById('bulkOrigenManual');

    if (!select) {
        console.error('❌ No se encontró bulkOrigenSelect');
        return;
    }

    let origen = select.value === '__otro__'
        ? manualInput.value.trim().toUpperCase()
        : select.value;

    if (!origen) {
        showNotification('Selecciona un país de origen', 'warning');
        return;
    }

    // Validar formato (2 letras)
    if (!/^[A-Z]{2}$/.test(origen)) {
        showNotification('Código de país inválido (debe ser 2 letras, ej: BR, US)', 'error');
        return;
    }

    const selectedItems = getSelectedItems();
    if (selectedItems.length === 0) {
        showNotification('Selecciona al menos un item', 'warning');
        return;
    }

    showLoading('Aplicando origen...');

    // Actualizar visualmente las filas usando la misma lógica que funciona para NCM
    selectedItems.forEach(index => {
        const origenInput = document.querySelector(`[data-field="origen"][data-item-index="${index}"]`);
        if (origenInput) {
            origenInput.value = origen;
            // Llamar a updateField para que se procese correctamente
            if (typeof updateField === 'function') {
                updateField(origenInput);
            }
            // Feedback visual temporal
            origenInput.style.background = '#d1fae5';
            setTimeout(() => {
                origenInput.style.background = '';
            }, 1500);
        }
    });

    // Resetear dropdown
    select.value = '';
    if (manualInput) {
        manualInput.value = '';
        manualInput.classList.add('hidden');
    }

    hideLoading();
    showNotification(`✅ Origen ${origen} aplicado a ${selectedItems.length} items`, 'success');

    // Actualizar preview si existe
    if (typeof updateOperationPreview === 'function') {
        const updatedData = collectItemsAndPreErrors();
        const groups = groupItemsByTariff(updatedData.items);
        updateOperationPreview(updatedData.items, groups);
    }
}

/**
 * Actualizar estado de validación (semáforo visual)
 */
function updateValidationStatus(status) {
    window.validationState.status = status;

    const badge = document.getElementById('validationStatusBadge');
    const genBtn = document.getElementById('generateGroupedBtn');
    const mariaBtn = document.getElementById('generateMariaBtn');
    const verifyBtn = document.getElementById('verifyNCMBtn');
    const summaryInline = document.getElementById('validationSummaryInline');

    // UX v2.2: Steps Banner
    const stepVerify   = document.getElementById('stepVerify');
    const stepGenerate = document.getElementById('stepGenerate');
    const stepReview   = document.getElementById('stepReview');

    if (!badge) return;

    switch(status) {
        case 'pending':
            badge.className = 'validation-status status-pending';
            badge.textContent = 'Sin validar';
            if (genBtn) genBtn.disabled = true;
            if (mariaBtn) mariaBtn.disabled = true;
            if (verifyBtn) {
                verifyBtn.textContent = 'Validar NCM';
                verifyBtn.disabled = false;
            }
            if (summaryInline) summaryInline.classList.add('hidden');
            if (stepVerify) stepVerify.className = 'step-item';
            if (stepGenerate) stepGenerate.className = 'step-item';
            break;

        case 'validating':
            badge.className = 'validation-status status-validating';
            badge.textContent = 'Validando…';
            if (genBtn) genBtn.disabled = true;
            if (mariaBtn) mariaBtn.disabled = true;
            if (verifyBtn) verifyBtn.disabled = true;
            if (summaryInline) summaryInline.classList.add('hidden');
            if (stepVerify) stepVerify.className = 'step-item step-active';
            if (stepReview) stepReview.className = 'step-item step-done';
            if (stepGenerate) stepGenerate.className = 'step-item';
            break;

        case 'valid':
            badge.className = 'validation-status status-valid';
            badge.textContent = 'Validado';
            if (genBtn) genBtn.disabled = false;
            if (mariaBtn) mariaBtn.disabled = false;
            if (verifyBtn) {
                verifyBtn.textContent = 'Revalidar';
                verifyBtn.disabled = false;
            }
            if (summaryInline) summaryInline.classList.add('hidden');
            // Steps: paso 3 done, paso 4 active
            if (stepVerify)   stepVerify.className   = 'step-item step-done';
            if (stepGenerate) stepGenerate.className  = 'step-item step-active';
            // Habilitar sticky generate button
            const stGenBtn = document.getElementById('generateStickyBtn');
            if (stGenBtn) stGenBtn.disabled = false;
            // Color-code filas validadas
            document.querySelectorAll('.item-grouping-row').forEach(row => {
                const ncmInput = row.querySelector('.edit-input.ncm');
                const ncmVal = ncmInput?.value?.replace(/\D/g,'') || '';
                if (ncmVal.length >= 6) {
                    row.classList.remove('row-no-ncm');
                    row.classList.add('row-validated');
                }
            });
            break;

        case 'invalid':
            badge.className = 'validation-status status-invalid';
            badge.textContent = 'Hay errores para corregir';
            if (genBtn) genBtn.disabled = true;
            if (mariaBtn) mariaBtn.disabled = true;
            if (verifyBtn) {
                verifyBtn.textContent = 'Revalidar';
                verifyBtn.disabled = false;
            }
            if (stepVerify)   stepVerify.className   = 'step-item step-active';
            if (stepGenerate) stepGenerate.className  = 'step-item';
            break;
    }
}

/**
 * Verificar NCM manualmente (obligatorio antes de generar)
 */
async function verifyNCMManually() {
    if (!window.currentItems || window.currentItems.length === 0) {
        showToast('Info', 'No hay items para validar');
        return;
    }

    updateValidationStatus('validating');

    try {
        await validateCurrentItems();

        // Esperar a que se renderice
        await new Promise(r => setTimeout(r, 300));

        // Verificar resultado usando el banner inline
        const summaryInline = document.getElementById('validationSummaryInline');
        const hasErrors = summaryInline && !summaryInline.classList.contains('hidden');

        if (hasErrors) {
            updateValidationStatus('invalid');
            showToast('Atención', 'Hay errores que corregir', 'warning');
        } else {
            updateValidationStatus('valid');
            window.validationState.lastValidatedAt = Date.now();
            window.validationState.itemsHash = getItemsHash(window.currentItems);
            showToast('Éxito', 'Validación completada correctamente', 'success');
        }
    } catch(e) {
        updateValidationStatus('invalid');
        console.error('Error en validación:', e);
    }
}

/**
 * Consultar NCM en Tarifar (Phase 1 - MVT)
 * Abre ventana nueva con búsqueda de NCM en Tarifar
 */
async function consultarTarifar(ncm) {
    if (!ncm || ncm.length < 6) {
        showToast('Info', 'Ingresa un NCM válido primero', 'info');
        return;
    }

    // Trackear analytics (Phase 1 KPI) - enviar a backend
    try {
        await fetch('/api/analytics/tarifar-click', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ncm})
        });
    } catch(e) {
    }

    // Abrir Tarifar con NCM pre-cargado
    const url = `https://app.tarifar.com/search?ncm=${ncm}`;
    window.open(url, '_blank', 'noopener,noreferrer');

    showToast('Info', 'Se abrió Tarifar en nueva pestaña', 'info');
}

/**
 * Mostrar modal con datos completos NCM (Tarifar + VUCE)
 * NUEVA FUNCIÓN - Estrategia Dual API
 */
async function mostrarDatosCompletos(ncm) {
    if (!ncm || ncm.length < 6) {
        showToast('Info', 'Ingresá un NCM válido primero', 'info');
        return;
    }

    // Mostrar loading
    showToast('Info', '🔄 Consultando VUCE...', 'info');

    try {
        const response = await fetch(`/api/ncm/${ncm}/completo`, {
            credentials: 'include'
        });

        if (!response.ok) {
            // Manejo específico de errores de autenticación
            if (response.status === 401 || response.status === 403) {
                showToast('Error', 'Sesión expirada o sin permisos. Redirigiendo...', 'error');
                localStorage.removeItem('user_plan');
                localStorage.removeItem('user_roles');
                setTimeout(() => window.location.href = '/login.html', 1500);
                return;
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Construir HTML del modal
        const html = `
            <div class="ncm-completo-modal">
                <h2>📊 NCM ${ncm} - Datos Certificados</h2>

                <div class="data-badges">
                    ${data.metadata.vuce_disponible
                        ? '<span class="badge badge-success">✅ VUCE Oficial</span>'
                        : '<span class="badge badge-warning">⚠️ VUCE No Disponible</span>'
                    }
                    ${data.metadata.tarifar_disponible
                        ? '<span class="badge badge-success">✅ Tarifar</span>'
                        : '<span class="badge badge-warning">⚠️ Tarifar No Disponible</span>'
                    }
                    <span class="badge badge-info">Nivel: ${data.validacion.nivel_confianza.toUpperCase()}</span>
                </div>

                <div class="data-section">
                    <h3>📌 Descripción Oficial</h3>
                    <p class="descripcion-text">${data.descripcion || 'No disponible'}</p>
                    <small class="text-muted">Fuente: VUCE</small>
                </div>

                <div class="data-section">
                    <h3>💰 Alícuotas (Datos Oficiales)</h3>
                    <table class="alicuotas-table">
                        <tr>
                            <td><strong>Arancel Extrazona:</strong></td>
                            <td class="text-right"><strong>${data.alicuotas.arancel_extrazona}%</strong></td>
                        </tr>
                        <tr>
                            <td><strong>Arancel MERCOSUR:</strong></td>
                            <td class="text-right text-success"><strong>${data.alicuotas.arancel_mercosur}%</strong> (🎯 Preferencial)</td>
                        </tr>
                        <tr>
                            <td><strong>IVA:</strong></td>
                            <td class="text-right">${data.alicuotas.iva}%</td>
                        </tr>
                        <tr>
                            <td><strong>Estadística:</strong></td>
                            <td class="text-right">${data.alicuotas.estadistica}%</td>
                        </tr>
                    </table>
                    <small class="text-muted">✅ Fuente: ${data.alicuotas.fuente}</small>
                </div>

                <div class="data-section">
                    <h3>📋 Licencias Requeridas</h3>
                    ${data.licencias && data.licencias.length > 0
                        ? data.licencias.map(lic => `
                            <div class="licencia-badge">
                                <strong>${lic.codigo}:</strong> ${lic.descripcion}
                            </div>
                        `).join('')
                        : '<p class="text-success">✅ No requiere licencias previas</p>'
                    }
                </div>

                ${data.analisis_origenes
                    ? `<div class="data-section">
                        <h3>🌍 Análisis de Orígenes (Tarifar)</h3>
                        <p><strong>Mejor opción:</strong> ${data.analisis_origenes.mejor_pais} (${data.analisis_origenes.mejor_origen})</p>
                        <p><strong>Costo estimado:</strong> USD ${data.analisis_origenes.costo_estimado.toFixed(2)}</p>
                        <p class="text-success"><strong>Ahorro vs China:</strong> USD ${data.analisis_origenes.ahorro_vs_china.toFixed(2)}</p>
                    </div>`
                    : ''
                }

                ${data.recomendacion_origen
                    ? `<div class="data-section recomendacion-section">
                        <h3>💡 Recomendación</h3>
                        <p><strong>Origen recomendado:</strong> ${data.recomendacion_origen.pais}</p>
                        <p><strong>Razón:</strong> ${data.recomendacion_origen.razon}</p>
                        ${data.recomendacion_origen.advertencias && data.recomendacion_origen.advertencias.length > 0
                            ? `<div class="alert-warning">
                                ⚠️ <strong>Advertencias:</strong>
                                <ul>${data.recomendacion_origen.advertencias.map(adv => `<li>${adv}</li>`).join('')}</ul>
                            </div>`
                            : ''
                        }
                    </div>`
                    : ''
                }

                ${data.validacion.discrepancias && data.validacion.discrepancias.length > 0
                    ? `<div class="alert-warning">
                        ⚠️ <strong>Discrepancias detectadas:</strong>
                        ${data.validacion.discrepancias.map(d => `
                            <p>${d.campo}: Tarifar=${d.tarifar}% vs VUCE=${d.vuce}%</p>
                            <small>→ ${d.recomendacion}</small>
                        `).join('')}
                    </div>`
                    : '<div class="alert-success">✅ Datos verificados y coincidentes entre fuentes</div>'
                }

                <div class="metadata-footer">
                    <small class="text-muted">
                        📅 Consultado: ${new Date(data.metadata.fecha_consulta).toLocaleString('es-AR')}
                        | 🔄 Fuentes: VUCE ${data.metadata.vuce_disponible ? '✅' : '❌'} + Tarifar ${data.metadata.tarifar_disponible ? '✅' : '❌'}
                        ${data.metadata.modo_fake ? ' | ⚠️ Modo Simulación (sin API keys)' : ''}
                    </small>
                </div>
            </div>
        `;

        // Mostrar modal (reutilizar modal existente o crear uno nuevo)
        showModalCustom('Datos Completos NCM', html);

    } catch(error) {
        console.error('[NCM Completo] Error:', error);
        showToast('Error', `No se pudieron obtener los datos: ${error.message}`, 'error');
    }
}

/**
 * Enriquecer todos los items actuales con datos VUCE (batch)
 * Muestra un panel con alícuotas + alertas de licencias
 */
async function enrichItemsWithVuce() {
    const btn = document.getElementById('enrichVuceBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '⏳ Consultando VUCE...';
    }

    // Recolectar items actuales de la tabla
    const rows = document.querySelectorAll('#itemsToGroup .table-row');
    const items = [];
    rows.forEach((row, idx) => {
        const ncm = row.querySelector('.edit-input[data-field="pieza"]')?.value ||
                    row.getAttribute('data-ncm') || '';
        const desc = row.querySelector('.edit-input[data-field="descripcion"]')?.value || '';
        if (ncm) items.push({ pieza: ncm, descripcion: desc, _idx: idx });
    });

    // Intentar desde el estado global de agrupación si la tabla está vacía
    if (items.length === 0 && window.groupedItems) {
        window.groupedItems.forEach((g, idx) => {
            const ncm = g.pieza || g.ncm || '';
            if (ncm) items.push({ pieza: ncm, descripcion: g.descripcion || '', _idx: idx });
        });
    }

    if (items.length === 0) {
        showToast('Info', 'No hay items cargados para enriquecer', 'info');
        if (btn) { btn.disabled = false; btn.innerHTML = '🔍 VUCE'; }
        return;
    }

    try {
        const response = await fetch('/api/ncm/enrich-items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ items })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        // Guardar en estado global para acceso posterior
        window.vuceEnrichData = data;

        // Mostrar panel de resultados
        renderVucePanel(data);

        const nLicencias = data.licencias_warnings?.length || 0;
        const nNcms = data.ncms_consultados || 0;
        showToast(
            nLicencias > 0 ? 'Atención' : 'VUCE',
            nLicencias > 0
                ? `⚠️ ${nLicencias} licencia(s) requerida(s) en ${nNcms} NCM(s) consultados`
                : `✅ ${nNcms} NCM(s) consultados. Sin licencias requeridas.`,
            nLicencias > 0 ? 'warning' : 'success'
        );

    } catch (err) {
        console.error('[VUCE Enrich]', err);
        showToast('Error', `Error consultando VUCE: ${err.message}`, 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '🔍 VUCE'; }
    }
}

/**
 * Renderizar el panel de resultados VUCE debajo de la tabla
 */
function renderVucePanel(data) {
    let panel = document.getElementById('vuceEnrichPanel');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'vuceEnrichPanel';
        panel.style.cssText = `
            margin-top: 1rem;
            border: 2px solid #3b82f6;
            border-radius: 12px;
            background: #eff6ff;
            padding: 1.25rem;
            font-size: 0.875rem;
            animation: fadeIn 0.3s ease;
        `;
        // Insertar después de la tabla o del verifyNCMBtn
        const anchor = document.getElementById('verifyNCMBtn')?.closest('div')
                    || document.getElementById('itemsToGroup')?.closest('.items-grouping-table');
        if (anchor) anchor.after(panel);
        else document.querySelector('.main-table-area')?.appendChild(panel);
    }

    const licencias = data.licencias_warnings || [];
    const alicuotas = data.alicuotas_summary || {};
    const ncmsKeys = Object.keys(alicuotas);
    const modoFake = data.modo_fake;

    // Construir HTML del panel
    const licenciasHtml = licencias.length > 0
        ? licencias.map(l => `
            <div style="display:flex; gap:0.5rem; align-items:center; background:#fef3c7; border:1px solid #f59e0b;
                        border-radius:8px; padding:0.5rem 0.75rem; margin-bottom:0.4rem;">
                <span style="font-size:1rem;">&#x26A0;</span>
                <div>
                    <strong>NCM ${l.ncm}</strong> — requiere <strong>${l.organismo}</strong>
                    <div style="color:#92400e;font-size:0.8rem;">${l.descripcion}</div>
                </div>
            </div>`).join('')
        : '<div style="color:#059669;font-weight:600;">&#x2705; Ningún NCM requiere licencias previas</div>';

    const alicuotasHtml = ncmsKeys.length > 0
        ? `<table style="width:100%;border-collapse:collapse;font-size:0.8rem;">
            <thead><tr style="background:#dbeafe;">
                <th style="padding:0.4rem;text-align:left;">NCM</th>
                <th style="padding:0.4rem;text-align:left;">Descripción</th>
                <th style="padding:0.4rem;text-align:center;">Arancel</th>
                <th style="padding:0.4rem;text-align:center;">IVA</th>
                <th style="padding:0.4rem;text-align:center;">Estadística</th>
            </tr></thead>
            <tbody>
            ${ncmsKeys.map(ncm => {
                const a = alicuotas[ncm];
                return `<tr style="border-bottom:1px solid #bfdbfe;">
                    <td style="padding:0.4rem;font-family:monospace;">${ncm}</td>
                    <td style="padding:0.4rem;color:#475569;">${(a.descripcion || '').substring(0,45)}${a.descripcion?.length > 45 ? '...' : ''}</td>
                    <td style="padding:0.4rem;text-align:center;font-weight:700;color:#1e40af;">${a.arancel}%</td>
                    <td style="padding:0.4rem;text-align:center;">${a.iva}%</td>
                    <td style="padding:0.4rem;text-align:center;">${a.estadistica}%</td>
                </tr>`;
            }).join('')}
            </tbody></table>`
        : '<p style="color:#64748b;">Sin datos de alícuotas disponibles</p>';

    panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <span style="font-size:1.2rem;">&#x1F1E6;&#x1F1F7;</span>
                <strong style="color:#1e40af;font-size:0.95rem;">Datos VUCE</strong>
                ${modoFake ? '<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:12px;font-size:0.72rem;">&#x26A0; Modo Mock</span>' : ''}
            </div>
            <button onclick="document.getElementById('vuceEnrichPanel').remove()" 
                    style="background:none;border:none;cursor:pointer;color:#94a3b8;font-size:1.1rem;" title="Cerrar">&times;</button>
        </div>

        <div style="margin-bottom:1rem;">
            <div style="font-weight:600;color:#1e40af;margin-bottom:0.5rem;">&#x1F4CB; Licencias y Permisos Requeridos</div>
            ${licenciasHtml}
        </div>

        <details open>
            <summary style="font-weight:600;color:#1e40af;cursor:pointer;margin-bottom:0.5rem;">&#x1F4B0; Alícuotas por NCM (datos VUCE)</summary>
            <div style="margin-top:0.5rem;">${alicuotasHtml}</div>
        </details>
    `;
}

/**
 * Mostrar modal personalizado (helper)
 */
function showModalCustom(titulo, html) {
    // Buscar modal existente o crear uno
    let modal = document.getElementById('ncmCompletoModal');

    if (!modal) {
        // Crear modal dinámicamente
        modal = document.createElement('div');
        modal.id = 'ncmCompletoModal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-container modal-large">
                <div class="modal-header">
                    <h2 id="modalTitle">${titulo}</h2>
                    <button class="modal-close" onclick="closeModalCustom()">✕</button>
                </div>
                <div class="modal-body" id="modalBody"></div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Actualizar contenido
    document.getElementById('modalTitle').textContent = titulo;
    document.getElementById('modalBody').innerHTML = html;

    // Mostrar
    modal.classList.add('active');
}

/**
 * Cerrar modal personalizado
 */
function closeModalCustom() {
    const modal = document.getElementById('ncmCompletoModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Toggle panel de validación (acordeón)
 */
function toggleValidationPanel() {
    const content = document.getElementById('validationContent');
    const icon = document.querySelector('.accordion-icon');

    if (!content) return;

    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        content.classList.add('expanded');
        if (icon) icon.textContent = '▴';
    } else {
        content.classList.add('hidden');
        content.classList.remove('expanded');
        if (icon) icon.textContent = '▾';
    }
}

/**
 * Cerrar acordeón de validación
 */
function closeValidationPanel(event) {
    if (event) {
        event.stopPropagation(); // Evitar que se dispare el toggle
    }
    const accordion = document.getElementById('validationAccordion');
    if (accordion) {
        accordion.classList.add('hidden');
    }
    // Resetear el ícono
    const icon = document.querySelector('.accordion-icon');
    if (icon) icon.textContent = '▾';
}

// Cerrar menús al hacer clic fuera
document.addEventListener('click', (e) => {
    // Menú avanzado
    const advMenu = document.getElementById('advancedMenu');
    const advBtn = document.getElementById('advancedMenuBtn');
    if (advMenu && advBtn && !advMenu.contains(e.target) && !advBtn.contains(e.target)) {
        advMenu.classList.add('hidden');
    }

    // Menú batch
    const batchMenu = document.getElementById('batchMenu');
    const batchBtns = document.querySelectorAll('[onclick="toggleBatchMenu()"]');
    let clickedBatchBtn = false;
    batchBtns.forEach(btn => {
        if (btn.contains(e.target)) clickedBatchBtn = true;
    });
    if (batchMenu && !batchMenu.contains(e.target) && !clickedBatchBtn) {
        batchMenu.classList.add('hidden');
    }
});

// Escuchar cambios en checkboxes de selección
document.addEventListener('change', (e) => {
    if (e.target && e.target.classList && e.target.classList.contains('row-select')) {
        try {
            updateBatchSelectionCounter();
        } catch(_) {}
    }
});

// ==================== UPGRADE TO PREMIUM ====================

/**
 * Mostrar modal de upgrade a Premium
 */
function showUpgradeModal() {
    const overlay = document.getElementById('upgradeOverlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('active');
    }
}

/**
 * Ocultar modal de upgrade
 */
function hideUpgradeModal() {
    const overlay = document.getElementById('upgradeOverlay');
    if (overlay) {
        overlay.classList.remove('active');
        overlay.classList.add('hidden');
    }
}

/**
 * Procesar el upgrade a Premium via MercadoPago
 */
async function processUpgradeMP() {
    // TODO: Integrar con MercadoPago SDK real
    // Por ahora, simulamos el flujo
    
    showToast('Info', 'Redirigiendo a MercadoPago...', 'info');
    
    try {
        // Simular llamada al backend para crear preferencia de pago MP
        // En producción: const response = await fetch('/api/create-mp-preference', {...});
        
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Simular éxito del pago (en producción, esto vendría del webhook de MP)
        // Por ahora, actualizamos directamente
        localStorage.setItem('user_plan', 'premium');
        window.userPlan = 'premium';
        if (document && document.body) {
            document.body.setAttribute('data-user-plan', 'premium');
        }
        
        
        // Ocultar modal de upgrade
        hideUpgradeModal();
        
        // Mostrar mensaje de agradecimiento
        showUpgradeThanks();
        
    } catch (error) {
        console.error('Error en upgrade:', error);
        showToast('Error', 'Hubo un error al procesar el pago. Intenta nuevamente.', 'error');
    }
}


/**
 * Formatea automáticamente el campo de vencimiento (MM/AA)
 * para que el usuario solo escriba números (ej: 1111 => 11/11)
 */
function initExpiryAutoFormat() {
    const input = document.getElementById('expiryDate');
    if (!input) {
        return;
    }

    const formatValue = raw => {
        const digits = raw.replace(/\D/g, '').slice(0, 4);
        if (digits.length <= 2) {
            return digits;
        }
        return `${digits.slice(0, 2)}/${digits.slice(2)}`;
    };

    const handler = event => {
        const { selectionStart } = event.target;
        const formatted = formatValue(event.target.value);
        event.target.value = formatted;
        // Mantener el cursor al final del texto para evitar saltos raros
        if (typeof selectionStart === 'number') {
            event.target.setSelectionRange(formatted.length, formatted.length);
        }
    };

    input.addEventListener('input', handler);
    input.addEventListener('blur', handler);
}

/**
 * Formatea automáticamente el número de tarjeta (1111222233334444 -> 1111 2222 3333 4444)
 */
function initCardNumberAutoFormat() {
    const input = document.getElementById('cardNumber');
    if (!input) {
        return;
    }

    const formatValue = raw => {
        const digits = raw.replace(/\D/g, '').slice(0, 16);
        return digits.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
    };

    const handler = event => {
        const { selectionStart } = event.target;
        const formatted = formatValue(event.target.value);
        event.target.value = formatted;
        if (typeof selectionStart === 'number') {
            const newPos = formatted.length;
            event.target.setSelectionRange(newPos, newPos);
        }
    };

    input.addEventListener('input', handler);
    input.addEventListener('blur', handler);
}

// Inicializar helpers específicos del dashboard
document.addEventListener('DOMContentLoaded', () => {
    initExpiryAutoFormat();
    initCardNumberAutoFormat();
});

/**
 * Mostrar modal de agradecimiento y recargar página
 */
function showUpgradeThanks() {
    const thanksOverlay = document.getElementById('upgradeThanksOverlay');
    if (thanksOverlay) {
        thanksOverlay.classList.remove('hidden');
        thanksOverlay.classList.add('active');
        
        // Recargar página después de 3 segundos
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    }
}

// === PASSWORD RECOVERY LOGIC ===

function showForgotPassword(e) {
    if (e) e.preventDefault();
    hideLogin();
    const overlay = document.getElementById('forgotPasswordOverlay');
    if (overlay) {
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function hideForgotPassword() {
    const overlay = document.getElementById('forgotPasswordOverlay');
    if (overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function showResetPassword(token) {
    const overlay = document.getElementById('resetPasswordOverlay');
    const tokenInput = document.getElementById('reset-token');
    
    if (overlay && tokenInput) {
        tokenInput.value = token;
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Hide other overlays if open
        hideLogin();
        hideRegister();
        hideForgotPassword();
    }
}

function hideResetPassword() {
    const overlay = document.getElementById('resetPasswordOverlay');
    if (overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
        
        // Clean URL
        const url = new URL(window.location);
        url.searchParams.delete('reset_token');
        window.history.replaceState({}, '', url);
    }
}

async function handleForgotPassword(e) {
    e.preventDefault();
    const email = document.getElementById('forgot-email').value;
    const btn = e.target.querySelector('button');
    
    // UI Loading state
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    btn.disabled = true;

    try {
        const response = await fetch('/auth/request-password-reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Email Enviado', 'Revisa tu bandeja de entrada (y spam).', 'success');
            hideForgotPassword();
            
            // For dev purposes, if token is returned (simulated email)
            if (data.dev_token_hint) {
            }
        } else {
            showToast('Error', data.detail || 'No se pudo enviar el email.', 'error');
        }
    } catch (error) {
        console.error('Error requesting reset:', error);
        showToast('Error', 'Fallo de conexión.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function handleResetPassword(e) {
    e.preventDefault();
    const token = document.getElementById('reset-token').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const btn = e.target.querySelector('button');

    if (newPassword !== confirmPassword) {
        showToast('Error', 'Las contraseñas no coinciden', 'warning');
        return;
    }

    // UI Loading state
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
    btn.disabled = true;

    try {
        const response = await fetch('/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                token: token, 
                new_password: newPassword 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Éxito', 'Contraseña actualizada. Ingresa con tu nueva clave.', 'success');
            hideResetPassword();
            showLogin();
        } else {
            showToast('Error', data.detail || 'Token inválido o expirado.', 'error');
        }
    } catch (error) {
        console.error('Error resetting password:', error);
        showToast('Error', 'Fallo de conexión.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Check for reset token on load
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('reset_token');
    
    if (resetToken) {
        showResetPassword(resetToken);
    }
});

// ============================================
// REDISEÑO UX / NCM AUTOCOMPLETE Y EXCEL NAV
// ============================================

window.ncmCatalog = [];
async function initNcmCatalog() {
    try {
        const res = await fetch('/static/dummy_ncm.json');
        if (res.ok) {
            window.ncmCatalog = await res.json();
            console.log(`[NCM] Catálogo dummy cargado: ${window.ncmCatalog.length} posiciones`);
        }
    } catch(e) {
        console.error('[NCM] Error al cargar catálogo de NCM', e);
    }
}
document.addEventListener('DOMContentLoaded', initNcmCatalog);

function attachCustomAutocompleteToNcm(input) {
    if (input.dataset.customAutocompleteLocalAttached) return;
    input.dataset.customAutocompleteLocalAttached = 'true';

    const wrapper = input.closest('.ncm-autocomplete-wrapper');
    if (!wrapper) return;
    const list = wrapper.querySelector('.ncm-autocomplete-list');
    if (!list) return;
    let currentFocus = -1;

    input.addEventListener('input', function(e) {
        let val = this.value;
        list.innerHTML = '';
        if (!val || val.length < 2) { list.classList.remove('active'); return; }
        
        const matches = window.ncmCatalog.filter(item => 
            item.ncm.includes(val) || item.desc.toLowerCase().includes(val.toLowerCase())
        ).slice(0, 15);
        
        if (matches.length === 0) { list.classList.remove('active'); return; }
        
        matches.forEach((match, i) => {
            const div = document.createElement('div');
            div.className = 'ncm-autocomplete-item';
            div.innerHTML = `<span class="ncm-autocomplete-code">${match.ncm}</span><span class="ncm-autocomplete-desc">${match.desc}</span>`;
            
            // Mouse down evt (no click para no interconectar con blur tempranamente)
            div.addEventListener('mousedown', function(evt) {
                evt.preventDefault(); // Evitar blur del input padre instantáneo
                input.value = match.ncm;
                list.classList.remove('active');
                
                // Setear descripción también localmente si existe el nodo
                const row = input.closest('.item-grouping-row');
                if (row) {
                    const descInput = row.querySelector('[data-field="descripcion"]');
                    if (descInput && !descInput.value) {
                        descInput.value = match.desc;
                        descInput.style.backgroundColor = '#e8f5e9';
                        setTimeout(() => descInput.style.backgroundColor = '', 2000);
                        
                        const idx = parseInt(input.getAttribute('data-item-index'), 10);
                        if (!isNaN(idx) && window.groupingData && window.groupingData[idx]) {
                            window.groupingData[idx].descripcion = match.desc;
                            window.groupingData[idx].pieza = match.ncm;
                        }
                    }
                }
                
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.blur(); // Dispara handleNcmBlur real
            });
            list.appendChild(div);
        });
        list.classList.add('active');
        currentFocus = -1;
    });

    input.addEventListener('keydown', function(e) {
        if (!list.classList.contains('active')) return;
        const items = list.querySelectorAll('.ncm-autocomplete-item');
        if (e.keyCode === 40) { // DOWN
            currentFocus++;
            addActive(items);
            e.preventDefault();
        } else if (e.keyCode === 38) { // UP
            currentFocus--;
            addActive(items);
            e.preventDefault();
        } else if (e.keyCode === 13) { // ENTER
            e.preventDefault(); // prevenir blur genérico de la fila de excel nav
            if (currentFocus > -1 && items[currentFocus]) {
                const event = new MouseEvent('mousedown', { bubbles: true, cancelable: true });
                items[currentFocus].dispatchEvent(event);
            }
        } else if (e.keyCode === 27) { // ESC
            list.classList.remove('active');
            e.preventDefault();
        }
    });

    function addActive(items) {
        if (!items || items.length === 0) return;
        items.forEach(item => item.classList.remove('selected'));
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (items.length - 1);
        items[currentFocus].classList.add('selected');
        items[currentFocus].scrollIntoView({ block: 'nearest' });
    }

    // click outside
    document.addEventListener('mousedown', function(e) {
        if (e.target !== input) {
            list.classList.remove('active');
        }
    });
}

// NAVEGACIÓN TIPO EXCEL (Atajos Generales por Teclado)
document.addEventListener('keydown', function(e) {
    if (!e.target.classList) return;
    const isEditInput = e.target.classList.contains('edit-input');
    const isCheckbox = e.target.classList.contains('row-checkbox');
    
    if (!isEditInput && !isCheckbox) return;

    // Ignorar si el menú autocomplete está abierto
    const wrapper = e.target.closest('.ncm-autocomplete-wrapper');
    if (wrapper) {
        const list = wrapper.querySelector('.ncm-autocomplete-list');
        if (list && list.classList.contains('active') && [38, 40, 13, 27].includes(e.keyCode)) {
            return; // el Autocomplete toma prioridad
        }
    }

    const row = e.target.closest('.item-grouping-row');
    if (!row) return;

    const allRows = Array.from(document.querySelectorAll('.item-grouping-row'));
    const rowIndex = allRows.indexOf(row);
    
    // Todos los inputs tabulables de esta fila
    const inputsOnRow = Array.from(row.querySelectorAll('.edit-input, .row-checkbox'));
    const colIndex = inputsOnRow.indexOf(e.target);

    if (e.keyCode === 38) { // ARRIBA
        if (rowIndex > 0) {
            const prevRow = allRows[rowIndex - 1];
            const targetInput = prevRow.querySelectorAll('.edit-input, .row-checkbox')[colIndex];
            if (targetInput) { targetInput.focus(); e.preventDefault(); }
        }
    } else if (e.keyCode === 40 || e.keyCode === 13) { // ABAJO / ENTER
        if (rowIndex < allRows.length - 1) {
            const nextRow = allRows[rowIndex + 1];
            const targetInput = nextRow.querySelectorAll('.edit-input, .row-checkbox')[colIndex];
            if (targetInput) { targetInput.focus(); e.preventDefault(); }
        } else if (e.keyCode === 13) {
            // Última fila, enter saca el foco (comportamiento de salvar) o nada
            e.target.blur();
        }
    } else if (e.keyCode === 37) { // IZQUIERDA
        // Solo saltar si cursor está al principio para txt o es numérico entero o checkbox/select
        if (e.target.type === 'checkbox' || e.target.selectionStart === 0 || e.target.type === 'number') {
            if (colIndex > 0) {
                inputsOnRow[colIndex - 1].focus();
                e.preventDefault();
            }
        }
    } else if (e.keyCode === 39) { // DERECHA
        // Solo saltar si cursor está al final
        if (e.target.type === 'checkbox' || e.target.selectionEnd === e.target.value?.length || e.target.type === 'number') {
            if (colIndex < inputsOnRow.length - 1) {
                inputsOnRow[colIndex + 1].focus();
                e.preventDefault();
            }
        }
    }
});

// ═══════════════════════════════════════════════════════════════
// UTILIDAD: escape HTML para prevenir XSS
// ═══════════════════════════════════════════════════════════════

function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// ═══════════════════════════════════════════════════════════════
// SMART TASK PANEL + CATÁLOGO DE PROVEEDORES — CDI v2.2
// ═══════════════════════════════════════════════════════════════

/**
 * Analiza items del PDF contra el catálogo y muestra el panel de tareas.
 * Es el punto de entrada principal del wizard inteligente.
 */
async function analyzeAndShowTaskPanel(items, vendorName) {
    if (!items || items.length === 0) return;

    // Guardar vendor para reutizar
    window.lastVendorName = vendorName;

    // Llamar al endpoint de match
    let analysis = null;
    try {
        const resp = await fetch('/api/catalog/match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items, vendor_name: vendorName })
        });
        if (resp.ok) analysis = await resp.json();
    } catch(e) { /* sin catálogo todavía */ }

    // Calcular qué falta en los items actuales
    const missingNcm    = items.filter(it => !it.pieza || String(it.pieza).replace(/\D/g,'').length < 6);
    const missingOrigin = items.filter(it => !it.origen || it.origen.trim().length < 2);
    const allOk         = missingNcm.length === 0 && missingOrigin.length === 0;

    // Si análisis de catálogo disponible → aplicar datos conocidos a la tabla
    if (analysis && analysis.vendor_known) {
        applyCatalogMatches(analysis);
        // Recalcular faltantes después de aplicar el catálogo
        window._catalogApplied = true;
    }

    showSmartTaskPanel({ items, vendorName, analysis, missingNcm, missingOrigin, allOk });
}

/**
 * Aplica los datos del catálogo directamente a las filas de la tabla.
 */
function applyCatalogMatches(analysis) {
    const rows = document.querySelectorAll('.item-grouping-row');
    let applied = 0;

    analysis.items_matched.forEach(match => {
        if (match.match_type === 'none') return;
        const row = rows[match.idx];
        if (!row) return;

        // Aplicar NCM si la celda está vacía
        const ncmInput = row.querySelector('.edit-input.ncm, [data-field="pieza"]');
        if (ncmInput && (!ncmInput.value || ncmInput.value.trim().length < 6) && match.ncm) {
            ncmInput.value = match.ncm;
            ncmInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        // Aplicar origen si está vacío
        const origenInput = row.querySelector('[data-field="origen"]');
        if (origenInput && (!origenInput.value || origenInput.value.trim().length < 2) && match.origen) {
            origenInput.value = match.origen;
            origenInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        applied++;
    });

    if (applied > 0) {
        window.dispatchEvent(new CustomEvent('catalogApplied', { detail: { count: applied, analysis } }));
    }
}

/**
 * Renderiza el Smart Task Panel arriba de la tabla.
 */
function showSmartTaskPanel({ items, vendorName, analysis, missingNcm, missingOrigin, allOk }) {
    const container = document.getElementById('smartTaskPanel');
    if (!container) return;

    const vendorKnown  = analysis?.vendor_known || false;
    const tasa         = analysis?.tasa_reconocimiento || 0;
    const itemsNuevos  = analysis?.items_nuevos || 0;
    const vendorId     = analysis?.vendor_id || '';

    // === Si todo está completo: notificación verde compacta ===
    if (allOk && vendorKnown && tasa >= 0.95) {
        container.innerHTML = `
          <div class="stp-banner stp-success" id="smartTaskPanelInner">
            <span class="stp-icon">✅</span>
            <span class="stp-text">
              <strong>${items.length}/${items.length} items</strong> reconocidos del catálogo de 
              <em>${escapeHtml(vendorName) || 'proveedor'}</em> — sin datos faltantes.
            </span>
            <button class="stp-close" onclick="hideSmartTaskPanel()">✕</button>
          </div>`;
        container.style.display = 'block';
        container.style.animation = 'fadeIn 0.3s ease';
        return;
    }

    // === Panel de tareas con items faltantes ===
    const tareas = [];

    if (!vendorKnown) {
        tareas.push({
            icon: '🆕', status: 'warn',
            label: vendorName ? `Nuevo proveedor: <strong>${escapeHtml(vendorName)}</strong>` : 'Proveedor no identificado',
            sub: 'Los datos que completes se guardarán para la próxima operación.',
            action: null
        });
    } else if (itemsNuevos > 0) {
        tareas.push({
            icon: '🔄', status: 'info',
            label: `${items.length - itemsNuevos}/${items.length} items reconocidos de <strong>${escapeHtml(vendorName)}</strong>`,
            sub: `${itemsNuevos} producto${itemsNuevos > 1 ? 's' : ''} nuevo${itemsNuevos > 1 ? 's' : ''} no estaban en el catálogo.`,
            action: null
        });
    }

    if (missingNcm.length > 0) {
        tareas.push({
            icon: '⚠️', status: 'warn',
            label: `${missingNcm.length} item${missingNcm.length > 1 ? 's' : ''} sin código arancelario (NCM)`,
            sub: 'Asigná el código de 8 dígitos para cada producto.',
            action: `showNcmAssistant()`
        });
    }

    if (missingOrigin.length > 0) {
        tareas.push({
            icon: '⚠️', status: 'warn',
            label: `${missingOrigin.length} item${missingOrigin.length > 1 ? 's' : ''} sin país de origen`,
            sub: 'Ingresá el código ISO del país (Ej: CN, US, DE, BR).',
            action: `showOriginAssistant()`
        });
    }

    if (missingNcm.length === 0 && missingOrigin.length === 0) {
        tareas.push({
            icon: '✅', status: 'ok',
            label: 'Datos completos — listo para verificar',
            sub: 'Verificá los NCMs con Aduana antes de generar el Excel.',
            action: `verifyNCMManually()`
        });
    }

    const tareasHTML = tareas.map(t => `
      <div class="stp-task stp-task-${t.status}">
        <span class="stp-task-icon">${t.icon}</span>
        <div class="stp-task-body">
          <div class="stp-task-label">${t.label}</div>
          <div class="stp-task-sub">${t.sub}</div>
        </div>
        ${t.action ? `<button class="stp-task-btn" onclick="${t.action}">Completar →</button>` : ''}
      </div>
    `).join('');

    // Guardar datos en window para onclick sin string-escaping
    window._stpVendorId   = vendorId;
    window._stpVendorName = vendorName || '';

    const saveBtnLabel = vendorKnown ? '💾 Actualizar catálogo' : '💾 Guardar para la próxima vez';
    const saveBtn = `<button class="stp-save-btn" onclick="saveToCatalog(window._stpVendorId, window._stpVendorName)">${saveBtnLabel}</button>`;

    container.innerHTML = `
      <div class="stp-panel" id="smartTaskPanelInner">
        <div class="stp-header">
          <span class="stp-title">📋 Completar Operación</span>
          <div style="display:flex;gap:0.5rem;align-items:center;">
            ${saveBtn}
            <button class="stp-close" onclick="hideSmartTaskPanel()" title="Cerrar panel">✕</button>
          </div>
        </div>
        <div class="stp-tasks">${tareasHTML}</div>
      </div>`;
    container.style.display = 'block';
    container.style.animation = 'fadeIn 0.35s ease';
}

function hideSmartTaskPanel() {
    const el = document.getElementById('smartTaskPanel');
    if (el) el.style.display = 'none';
}

// ─────────────────────────────────────────────────────────────
// MINI-MODAL: Asignar País de Origen
// ─────────────────────────────────────────────────────────────

function showOriginAssistant() {
    // Limpiar modal anterior si existe (evitar memory leak)
    document.getElementById('originAssistantModal')?.remove();

    const rows = document.querySelectorAll('.item-grouping-row');
    const itemsToFix = [];

    rows.forEach((row, idx) => {
        const origenInput = row.querySelector('[data-field="origen"]');
        const descInput   = row.querySelector('[data-field="descripcion"]');
        if (origenInput && (!origenInput.value || origenInput.value.trim().length < 2)) {
            itemsToFix.push({
                idx,
                desc: descInput?.value || `Item #${idx + 1}`,
                input: origenInput
            });
        }
    });

    if (itemsToFix.length === 0) {
        showToast('Info', 'Todos los items ya tienen país de origen ✅');
        return;
    }

    const rowsHTML = itemsToFix.map(it => `
      <div class="oam-row" data-idx="${it.idx}">
        <span class="oam-desc">${escapeHtml(it.desc.substring(0, 40))}</span>
        <select class="oam-select" data-idx="${it.idx}">
          <option value="">— Elegir —</option>
          <option value="CN">🇨🇳 CN — China</option>
          <option value="US">🇺🇸 US — Estados Unidos</option>
          <option value="DE">🇩🇪 DE — Alemania</option>
          <option value="BR">🇧🇷 BR — Brasil</option>
          <option value="IT">🇮🇹 IT — Italia</option>
          <option value="ES">🇪🇸 ES — España</option>
          <option value="JP">🇯🇵 JP — Japón</option>
          <option value="KR">🇰🇷 KR — Corea del Sur</option>
          <option value="IN">🇮🇳 IN — India</option>
          <option value="FR">🇫🇷 FR — Francia</option>
          <option value="AR">🇦🇷 AR — Argentina</option>
          <option value="PY">🇵🇾 PY — Paraguay</option>
          <option value="UY">🇺🇾 UY — Uruguay</option>
          <option value="CL">🇨🇱 CL — Chile</option>
          <option value="MX">🇲🇽 MX — México</option>
          <option value="TR">🇹🇷 TR — Turquía</option>
          <option value="TW">🇹🇼 TW — Taiwán</option>
          <option value="GB">🇬🇧 GB — Reino Unido</option>
          <option value="NL">🇳🇱 NL — Países Bajos</option>
        </select>
        <span class="oam-status" id="oam-status-${it.idx}">○</span>
      </div>
    `).join('');

    const modal = document.createElement('div');
    modal.id = 'originAssistantModal';
    modal.className = 'mini-modal-overlay';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-label', 'Asignar País de Origen');
    modal.innerHTML = `
      <div class="mini-modal">
        <div class="mini-modal-header">
          <div class="mini-modal-title">🌍 Asignar País de Origen</div>
          <button class="mini-modal-close" onclick="closeOriginAssistant()">✕</button>
        </div>
        <div class="mini-modal-body">
          <p class="mini-modal-sub">${itemsToFix.length} items sin país de origen</p>
          <div class="oam-bulk">
            <label>Aplicar a todos:</label>
            <select id="bulkOriginSelect">
              <option value="">— Seleccionar —</option>
              <option value="CN">🇨🇳 CN — China</option>
              <option value="US">🇺🇸 US — EE.UU.</option>
              <option value="DE">🇩🇪 DE — Alemania</option>
              <option value="BR">🇧🇷 BR — Brasil</option>
              <option value="IT">🇮🇹 IT — Italia</option>
              <option value="ES">🇪🇸 ES — España</option>
              <option value="AR">🇦🇷 AR — Argentina</option>
            </select>
            <button class="oam-apply-all" onclick="applyBulkOrigin()">Aplicar a todos</button>
          </div>
          <div class="oam-list">${rowsHTML}</div>
        </div>
        <div class="mini-modal-footer">
          <button class="mini-modal-cancel" onclick="closeOriginAssistant()">Cancelar</button>
          <button class="mini-modal-ok" onclick="confirmOriginAssistant()">Guardar orígenes →</button>
        </div>
      </div>`;

    document.body.appendChild(modal);
    // Listeners de cambio individual
    // Cerrar con Escape + focus trap
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeOriginAssistant();
    });
    // Focus en primer select
    setTimeout(() => modal.querySelector('.oam-select')?.focus(), 100);

    modal.querySelectorAll('.oam-select').forEach(sel => {
        sel.addEventListener('change', () => {
            const idx = sel.dataset.idx;
            const status = document.getElementById(`oam-status-${idx}`);
            if (status) status.textContent = sel.value ? '✅' : '○';
        });
    });
}

function applyBulkOrigin() {
    const bulk = document.getElementById('bulkOriginSelect')?.value;
    if (!bulk) return;
    document.querySelectorAll('#originAssistantModal .oam-select').forEach(sel => {
        sel.value = bulk;
        const idx = sel.dataset.idx;
        const status = document.getElementById(`oam-status-${idx}`);
        if (status) status.textContent = '✅';
    });
}

function confirmOriginAssistant() {
    const rows = document.querySelectorAll('.item-grouping-row');
    let applied = 0;
    document.querySelectorAll('#originAssistantModal .oam-select').forEach(sel => {
        if (!sel.value) return;
        const idx = parseInt(sel.dataset.idx);
        const row = rows[idx];
        if (!row) return;
        const origenInput = row.querySelector('[data-field="origen"]');
        if (origenInput) {
            origenInput.value = sel.value;
            origenInput.dispatchEvent(new Event('input', { bubbles: true }));
            applied++;
        }
    });
    closeOriginAssistant();
    if (applied > 0) showToast('Éxito', `✅ ${applied} países de origen asignados`);
    // Refrescar panel
    if (window.currentItems) analyzeAndShowTaskPanel(window.currentItems, window.lastVendorName || '');
}

function closeOriginAssistant() {
    document.getElementById('originAssistantModal')?.remove();
}

// ─────────────────────────────────────────────────────────────
// MINI-MODAL: Asignar NCM
// ─────────────────────────────────────────────────────────────

function showNcmAssistant() {
    // Limpiar modal anterior si existe (evitar memory leak)
    document.getElementById('ncmAssistantModal')?.remove();

    const rows = document.querySelectorAll('.item-grouping-row');
    const itemsToFix = [];

    rows.forEach((row, idx) => {
        const ncmInput  = row.querySelector('.edit-input.ncm, [data-field="pieza"]');
        const descInput = row.querySelector('[data-field="descripcion"]');
        const ncmVal    = ncmInput?.value?.replace(/\D/g, '') || '';
        if (ncmInput && ncmVal.length < 6) {
            itemsToFix.push({
                idx,
                desc: descInput?.value || `Item #${idx + 1}`,
                currentNcm: ncmVal
            });
        }
    });

    if (itemsToFix.length === 0) {
        showToast('Info', 'Todos los items ya tienen NCM ✅');
        return;
    }

    const rowsHTML = itemsToFix.map(it => `
      <div class="ncm-am-row">
        <span class="ncm-am-desc" title="${it.desc}">${escapeHtml(it.desc.substring(0, 38))}</span>
        <input type="text" class="ncm-am-input edit-input ncm" data-idx="${it.idx}"
               value="${it.currentNcm}" maxlength="8" placeholder="Ej: 28432090"
               style="width:110px;font-family:monospace;font-weight:700;color:#1e40af;"
               oninput="this.value=this.value.replace(/\\D/g,'').substring(0,8)">
        <span class="ncm-am-len" id="ncm-am-len-${it.idx}">${it.currentNcm.length}/8</span>
      </div>
    `).join('');

    const modal = document.createElement('div');
    modal.id = 'ncmAssistantModal';
    modal.className = 'mini-modal-overlay';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-label', 'Asignar Código NCM');
    modal.innerHTML = `
      <div class="mini-modal">
        <div class="mini-modal-header">
          <div class="mini-modal-title">🔢 Asignar Código NCM</div>
          <button class="mini-modal-close" onclick="closeNcmAssistant()">✕</button>
        </div>
        <div class="mini-modal-body">
          <p class="mini-modal-sub">${itemsToFix.length} items sin código arancelario (8 dígitos)</p>
          <div class="ncm-am-list">${rowsHTML}</div>
        </div>
        <div class="mini-modal-footer">
          <button class="mini-modal-cancel" onclick="closeNcmAssistant()">Cancelar</button>
          <button class="mini-modal-ok" onclick="confirmNcmAssistant()">Aplicar NCMs →</button>
        </div>
      </div>`;

    document.body.appendChild(modal);

    // Actualizar contador de dígitos en tiempo real
    // Cerrar con Escape + focus en primer input
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeNcmAssistant();
    });
    setTimeout(() => modal.querySelector('.ncm-am-input')?.focus(), 100);

    modal.querySelectorAll('.ncm-am-input').forEach(inp => {
        inp.addEventListener('input', () => {
            const len = document.getElementById(`ncm-am-len-${inp.dataset.idx}`);
            if (len) len.textContent = `${inp.value.length}/8`;
        });
    });
}

function confirmNcmAssistant() {
    const rows = document.querySelectorAll('.item-grouping-row');
    let applied = 0, incomplete = 0;

    document.querySelectorAll('#ncmAssistantModal .ncm-am-input').forEach(inp => {
        const val = (inp.value || '').replace(/\D/g, '');
        if (val.length < 6) { incomplete++; return; }
        const idx = parseInt(inp.dataset.idx);
        const row = rows[idx];
        if (!row) return;
        const ncmInput = row.querySelector('.edit-input.ncm, [data-field="pieza"]');
        if (ncmInput) {
            ncmInput.value = val;
            ncmInput.dispatchEvent(new Event('input', { bubbles: true }));
            applied++;
        }
    });

    closeNcmAssistant();
    if (incomplete > 0) showToast('Atención', `${incomplete} NCMs incompletos (menos de 6 dígitos) — no se aplicaron`);
    if (applied > 0) showToast('Éxito', `✅ ${applied} NCMs asignados`);
    if (window.currentItems) analyzeAndShowTaskPanel(window.currentItems, window.lastVendorName || '');
}

function closeNcmAssistant() {
    document.getElementById('ncmAssistantModal')?.remove();
}

// ─────────────────────────────────────────────────────────────
// GUARDAR EN CATÁLOGO
// ─────────────────────────────────────────────────────────────

async function saveToCatalog(vendorId, vendorName) {
    const rows = document.querySelectorAll('.item-grouping-row');
    const productos = [];

    rows.forEach(row => {
        const desc    = row.querySelector('[data-field="descripcion"]')?.value?.trim() || '';
        const ncm     = row.querySelector('.edit-input.ncm, [data-field="pieza"]')?.value?.trim() || '';
        const origen  = row.querySelector('[data-field="origen"]')?.value?.trim() || '';
        const precio  = row.querySelector('[data-field="valor_unitario"]')?.value || '';
        if (desc) productos.push({ descripcion: desc, ncm, origen, valor_unitario: precio });
    });

    if (productos.length === 0) {
        showToast('Error', 'No hay items para guardar');
        return;
    }

    const name = vendorName || window.lastVendorName || 'Proveedor desconocido';

    try {
        const resp = await fetch(`/api/catalog/${vendorId || 'nuevo'}/productos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vendor_name: name, productos })
        });

        if (resp.ok) {
            const result = await resp.json();
            showToast('Catálogo actualizado', 
                `✅ ${result.productos_nuevos} productos nuevos + ${result.productos_actualizados} actualizados para ${name}.`);
            // Actualizar el vendor_id global
            window._catalogVendorId = result.vendor_id;
        } else {
            throw new Error(`HTTP ${resp.status}`);
        }
    } catch(e) {
        showToast('Error', `No se pudo guardar: ${e.message}`);
    }
}

// ============================================================
// === CATALOG MANAGER (Fase 4) — UI de gestión del catálogo
// ============================================================
//
// Estado runtime:
//   window._catalogVendors        — lista cacheada del último GET /api/catalog/proveedores
//   window._catalogCurrentVendor  — detalle del vendor actualmente abierto en detail view
//
// Endpoints consumidos:
//   GET    /api/catalog/proveedores
//   GET    /api/catalog/{vendor_id}
//   PUT    /api/catalog/{vendor_id}/productos/{product_key}
//   DELETE /api/catalog/{vendor_id}/productos/{product_key}
//   DELETE /api/catalog/{vendor_id}

// Helper de fetch consistente: misma origin + cookie HttpOnly para auth.
async function _catalogFetch(url, opts = {}) {
    const merged = Object.assign({ credentials: 'include' }, opts);
    merged.headers = Object.assign(
        { 'Accept': 'application/json' },
        opts.headers || {}
    );
    if (merged.body && !merged.headers['Content-Type']) {
        merged.headers['Content-Type'] = 'application/json';
    }
    const resp = await fetch(url, merged);
    if (resp.status === 401) {
        showToast('Sesión expirada', 'Volvé a iniciar sesión para usar el catálogo.', 'error', 5000);
        throw new Error('unauthorized');
    }
    return resp;
}

// Alias público para abrir el catálogo desde otros lugares (Smart Task Panel, etc).
function showCatalogManager() {
    switchMode('catalog');
}
window.showCatalogManager = showCatalogManager;

// ── Master view: lista de proveedores ─────────────────────────

async function loadCatalogVendors() {
    const list = document.getElementById('catalogVendorsList');
    if (!list) return;
    list.innerHTML = '<div class="catalog-loading"><i class="fas fa-spinner fa-spin"></i> Cargando catálogo...</div>';
    try {
        const resp = await _catalogFetch('/api/catalog/proveedores');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        window._catalogVendors = Array.isArray(data.proveedores) ? data.proveedores : [];
        renderCatalogVendorsList();
    } catch (e) {
        if (e.message === 'unauthorized') return;
        list.innerHTML = `<div class="catalog-empty"><i class="fas fa-triangle-exclamation"></i><p>Error cargando catálogo: ${escapeHtml(e.message)}</p></div>`;
    }
}
window.loadCatalogVendors = loadCatalogVendors;

function renderCatalogVendorsList() {
    const list = document.getElementById('catalogVendorsList');
    const vendorCountEl = document.getElementById('catalogVendorCount');
    const productCountEl = document.getElementById('catalogProductCount');
    if (!list) return;

    const vendors = window._catalogVendors || [];
    const totalProducts = vendors.reduce((acc, v) => acc + (v.total_productos || 0), 0);
    if (vendorCountEl) vendorCountEl.textContent = String(vendors.length);
    if (productCountEl) productCountEl.textContent = String(totalProducts);

    if (vendors.length === 0) {
        list.innerHTML = `
            <div class="catalog-empty">
                <i class="fas fa-inbox"></i>
                <p><strong>Tu catálogo está vacío.</strong></p>
                <p>Cuando proceses una factura y guardes los productos desde el Smart Task Panel, los proveedores aparecerán acá.</p>
            </div>`;
        return;
    }

    list.innerHTML = vendors.map(v => {
        const name = escapeHtml(v.nombre || v.vendor_id || '');
        const id = escapeHtml(v.vendor_id || '');
        const totalProd = Number(v.total_productos || 0);
        const totalUsos = Number(v.usos_totales || 0);
        const ultima = _catalogFormatDate(v.ultima_vez) || '—';
        return `
            <div class="catalog-vendor-card" data-vendor-id="${id}" onclick="openVendorDetail('${id}')" tabindex="0" role="button" aria-label="Ver catálogo de ${name}">
                <div class="catalog-vendor-card-header">
                    <div class="catalog-vendor-icon"><i class="fas fa-store"></i></div>
                    <div class="catalog-vendor-name" title="${name}">${name}</div>
                </div>
                <div class="catalog-vendor-stats">
                    <span class="catalog-stat-chip"><i class="fas fa-cube"></i> ${totalProd} producto${totalProd === 1 ? '' : 's'}</span>
                    <span class="catalog-stat-chip"><i class="fas fa-bolt"></i> ${totalUsos} usos</span>
                </div>
                <div class="catalog-vendor-footer">
                    <span class="catalog-vendor-last"><i class="fas fa-clock"></i> Última actualización: ${escapeHtml(ultima)}</span>
                    <i class="fas fa-chevron-right catalog-vendor-chevron"></i>
                </div>
            </div>`;
    }).join('');

    // Permitir abrir con Enter/Space cuando el card tiene focus (accesibilidad).
    list.querySelectorAll('.catalog-vendor-card').forEach(card => {
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });
}

function _catalogFormatDate(iso) {
    if (!iso) return null;
    try {
        const d = new Date(iso);
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch (_) { return iso; }
}

// ── Detail view: tabla de productos del vendor ────────────────

async function openVendorDetail(vendorId) {
    if (!vendorId) return;
    try {
        const resp = await _catalogFetch('/api/catalog/' + encodeURIComponent(vendorId));
        if (resp.status === 404) {
            showToast('No encontrado', 'El proveedor ya no existe en el catálogo.', 'error');
            await loadCatalogVendors();
            return;
        }
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const vendor = await resp.json();
        window._catalogCurrentVendor = vendor;
        _showCatalogDetailView(vendor);
    } catch (e) {
        if (e.message === 'unauthorized') return;
        showToast('Error', 'No se pudo cargar el proveedor: ' + e.message, 'error');
    }
}
window.openVendorDetail = openVendorDetail;

function _showCatalogDetailView(vendor) {
    const master = document.getElementById('catalogMasterView');
    const detail = document.getElementById('catalogDetailView');
    if (!master || !detail) return;
    master.classList.add('hidden');
    detail.classList.remove('hidden');

    const nameEl = document.getElementById('catalogDetailVendorName');
    const metaEl = document.getElementById('catalogDetailVendorMeta');
    if (nameEl) nameEl.textContent = vendor.nombre || vendor.vendor_id || '—';
    if (metaEl) {
        const total = Number(vendor.total_productos || 0);
        const ultima = _catalogFormatDate(vendor.ultima_actualizacion) || '—';
        metaEl.textContent = `${total} producto${total === 1 ? '' : 's'} · Última actualización: ${ultima}`;
    }
    renderCatalogProductsTable(vendor);
}

function renderCatalogProductsTable(vendor) {
    const tbody = document.getElementById('catalogProductsTbody');
    const empty = document.getElementById('catalogProductsEmpty');
    const tableWrap = document.querySelector('#catalogDetailView .catalog-products-table-wrapper');
    if (!tbody) return;

    const productos = (vendor && vendor.productos) ? vendor.productos : {};
    const entries = Object.entries(productos);

    if (entries.length === 0) {
        tbody.innerHTML = '';
        if (empty) empty.classList.remove('hidden');
        const table = tableWrap?.querySelector('table');
        if (table) table.classList.add('hidden');
        return;
    }
    if (empty) empty.classList.add('hidden');
    const table = tableWrap?.querySelector('table');
    if (table) table.classList.remove('hidden');

    // Orden: por usos desc, luego descripción
    entries.sort((a, b) => {
        const ua = Number(a[1].usos || 0);
        const ub = Number(b[1].usos || 0);
        if (ub !== ua) return ub - ua;
        return String(a[1].descripcion_original || '').localeCompare(String(b[1].descripcion_original || ''));
    });

    const vendorIdAttr = escapeHtml(vendor.vendor_id || '');
    tbody.innerHTML = entries.map(([key, prod]) => {
        const desc = escapeHtml(prod.descripcion_original || key);
        const ncm = escapeHtml(prod.ncm || '');
        const origen = escapeHtml(prod.origen || '');
        const usos = Number(prod.usos || 0);
        const ultima = escapeHtml(prod.ultima_vez || '—');
        // key se inserta como atributo: usar JSON.stringify para escapar comillas/caracteres
        const keyAttr = escapeHtml(key);
        return `
            <tr data-product-key="${keyAttr}">
                <td class="catalog-cell-desc" title="${desc}">${desc}</td>
                <td class="catalog-cell-ncm">${ncm || '<span class="catalog-cell-empty">—</span>'}</td>
                <td class="catalog-cell-origen">${origen || '<span class="catalog-cell-empty">—</span>'}</td>
                <td class="catalog-cell-num">${usos}</td>
                <td class="catalog-cell-fecha">${ultima}</td>
                <td class="catalog-cell-actions">
                    <button type="button" class="btn-icon" title="Editar producto" aria-label="Editar producto" onclick="openProductEditModal('${vendorIdAttr}', this.closest('tr').dataset.productKey)">
                        <i class="fas fa-pen"></i>
                    </button>
                    <button type="button" class="btn-icon btn-icon-danger" title="Eliminar producto" aria-label="Eliminar producto" onclick="confirmDeleteProductFromUI('${vendorIdAttr}', this.closest('tr').dataset.productKey)">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
    }).join('');
}

function backToCatalogList() {
    const master = document.getElementById('catalogMasterView');
    const detail = document.getElementById('catalogDetailView');
    if (master) master.classList.remove('hidden');
    if (detail) detail.classList.add('hidden');
    window._catalogCurrentVendor = null;
}
window.backToCatalogList = backToCatalogList;

// ── Edit modal ────────────────────────────────────────────────

function openProductEditModal(vendorId, productKey) {
    const vendor = window._catalogCurrentVendor;
    if (!vendor || vendor.vendor_id !== vendorId) {
        showToast('Error', 'No hay un proveedor abierto.', 'error');
        return;
    }
    const prod = (vendor.productos || {})[productKey];
    if (!prod) {
        showToast('No encontrado', 'El producto ya no existe.', 'error');
        return;
    }

    const overlay = document.getElementById('productEditOverlay');
    if (!overlay) return;
    document.getElementById('productEditVendorId').value = vendorId;
    document.getElementById('productEditOriginalKey').value = productKey;
    document.getElementById('productEditDesc').value = prod.descripcion_original || '';
    document.getElementById('productEditNcm').value = prod.ncm || '';
    document.getElementById('productEditOrigen').value = prod.origen || '';
    document.getElementById('productEditUnidad').value = prod.unidad_medida || '';
    document.getElementById('productEditPrecio').value = prod.precio_ref != null ? prod.precio_ref : '';
    const titleEl = document.getElementById('productEditTitle');
    if (titleEl) titleEl.textContent = `Editar producto · ${vendor.nombre || vendorId}`;

    overlay.classList.add('active');
    overlay.style.display = 'flex';
    // Focus + Escape para cerrar
    setTimeout(() => {
        try { document.getElementById('productEditDesc').focus(); } catch (_) {}
    }, 50);
    if (!overlay._catalogEscBound) {
        overlay._catalogEscHandler = (e) => {
            if (e.key === 'Escape' && overlay.classList.contains('active')) {
                e.preventDefault();
                closeProductEditModal();
            }
        };
        document.addEventListener('keydown', overlay._catalogEscHandler);
        overlay._catalogEscBound = true;
    }
    // Click fuera cierra (solo si el target es el overlay mismo, no el modal)
    if (!overlay._catalogClickBound) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeProductEditModal();
        });
        overlay._catalogClickBound = true;
    }
}
window.openProductEditModal = openProductEditModal;

function closeProductEditModal() {
    const overlay = document.getElementById('productEditOverlay');
    if (!overlay) return;
    overlay.classList.remove('active');
    overlay.style.display = 'none';
}
window.closeProductEditModal = closeProductEditModal;

async function submitProductEdit(event) {
    if (event && event.preventDefault) event.preventDefault();
    const vendorId = document.getElementById('productEditVendorId').value;
    const productKey = document.getElementById('productEditOriginalKey').value;
    const desc = document.getElementById('productEditDesc').value.trim();
    const ncm = document.getElementById('productEditNcm').value.trim();
    const origen = document.getElementById('productEditOrigen').value.trim().toUpperCase();
    const unidad = document.getElementById('productEditUnidad').value.trim();
    const precioRaw = document.getElementById('productEditPrecio').value;

    if (!desc) {
        showToast('Falta descripción', 'La descripción es obligatoria.', 'error');
        return;
    }
    if (ncm && !/^\d{8}$/.test(ncm)) {
        showToast('NCM inválido', 'El NCM debe tener exactamente 8 dígitos (o quedar vacío).', 'error');
        return;
    }

    const payload = {
        descripcion_original: desc,
        ncm: ncm,
        origen: origen,
        unidad_medida: unidad,
    };
    if (precioRaw !== '') {
        const num = Number(precioRaw);
        if (!isNaN(num)) payload.precio_ref = num;
    }

    try {
        const url = '/api/catalog/' + encodeURIComponent(vendorId) + '/productos/' + encodeURIComponent(productKey);
        const resp = await _catalogFetch(url, {
            method: 'PUT',
            body: JSON.stringify(payload),
        });
        if (resp.status === 404) {
            const err = await resp.json().catch(() => ({}));
            showToast('No se pudo actualizar', err.detail || 'Producto no encontrado o colisión de descripción.', 'error', 5000);
            return;
        }
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        showToast('Producto actualizado', 'Los cambios se guardaron correctamente.', 'success');
        closeProductEditModal();
        // Refrescar detalle del vendor
        await openVendorDetail(vendorId);
    } catch (e) {
        if (e.message === 'unauthorized') return;
        showToast('Error', 'No se pudo guardar: ' + e.message, 'error');
    }
}
window.submitProductEdit = submitProductEdit;

// ── Delete handlers ───────────────────────────────────────────

async function confirmDeleteProductFromUI(vendorId, productKey) {
    const vendor = window._catalogCurrentVendor;
    const prod = vendor && vendor.productos ? vendor.productos[productKey] : null;
    const desc = prod ? (prod.descripcion_original || productKey) : productKey;
    const confirmFn = window.showConfirmation;
    let ok;
    if (typeof confirmFn === 'function') {
        ok = await confirmFn(`¿Eliminar el producto "${desc}" del catálogo? Esta acción no se puede deshacer.`);
    } else {
        ok = window.confirm(`¿Eliminar el producto "${desc}" del catálogo?`);
    }
    if (!ok) return;
    try {
        const url = '/api/catalog/' + encodeURIComponent(vendorId) + '/productos/' + encodeURIComponent(productKey);
        const resp = await _catalogFetch(url, { method: 'DELETE' });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        if (data.deleted) {
            showToast('Producto eliminado', desc, 'success');
        } else {
            showToast('Sin cambios', 'El producto ya no existía en el catálogo.', 'info');
        }
        await openVendorDetail(vendorId);
    } catch (e) {
        if (e.message === 'unauthorized') return;
        showToast('Error', 'No se pudo eliminar: ' + e.message, 'error');
    }
}
window.confirmDeleteProductFromUI = confirmDeleteProductFromUI;

async function confirmDeleteVendorFromUI() {
    const vendor = window._catalogCurrentVendor;
    if (!vendor || !vendor.vendor_id) return;
    const name = vendor.nombre || vendor.vendor_id;
    const total = Number(vendor.total_productos || 0);
    const confirmFn = window.showConfirmation;
    const msg = `¿Eliminar el proveedor "${name}" y sus ${total} producto${total === 1 ? '' : 's'} del catálogo? Esta acción no se puede deshacer.`;
    let ok;
    if (typeof confirmFn === 'function') {
        ok = await confirmFn(msg);
    } else {
        ok = window.confirm(msg);
    }
    if (!ok) return;
    try {
        const url = '/api/catalog/' + encodeURIComponent(vendor.vendor_id);
        const resp = await _catalogFetch(url, { method: 'DELETE' });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        showToast('Proveedor eliminado', name, 'success');
        backToCatalogList();
        await loadCatalogVendors();
    } catch (e) {
        if (e.message === 'unauthorized') return;
        showToast('Error', 'No se pudo eliminar el proveedor: ' + e.message, 'error');
    }
}
window.confirmDeleteVendorFromUI = confirmDeleteVendorFromUI;

