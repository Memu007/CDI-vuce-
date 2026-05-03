// Variables globales
let itemCounter = 0;

// Elementos del DOM
const form = document.getElementById('operationForm');
const uploadForm = document.getElementById('uploadForm');
const pdfForm = document.getElementById('pdfForm');
const itemsContainer = document.getElementById('itemsContainer');
const addItemBtn = document.getElementById('addItemBtn');
const clearBtn = document.getElementById('clearBtn');
const results = document.getElementById('results');
const errorMessage = document.getElementById('errorMessage');
const loading = document.getElementById('loading');
const downloadLink = document.getElementById('downloadLink');
const successMessage = document.getElementById('successMessage');

// Elementos del selector de modo
const manualModeBtn = document.getElementById('manualModeBtn');
const uploadModeBtn = document.getElementById('uploadModeBtn');
const pdfModeBtn = document.getElementById('pdfModeBtn');

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    addItem(); // Agregar primer item por defecto
    setupEventListeners();
});

// Configurar event listeners
function setupEventListeners() {
    addItemBtn.addEventListener('click', addItem);
    clearBtn.addEventListener('click', clearForm);
    form.addEventListener('submit', handleSubmit);

    // Event listeners para el selector de modo
    manualModeBtn.addEventListener('click', () => switchMode('manual'));
    uploadModeBtn.addEventListener('click', () => switchMode('upload'));
    pdfModeBtn.addEventListener('click', () => switchMode('pdf'));

    // Event listener para el formulario de subida
    uploadForm.addEventListener('submit', handleUpload);

    // Event listener para el formulario de PDF
    pdfForm.addEventListener('submit', handlePdfUpload);
}

// Agregar un nuevo item
function addItem() {
    itemCounter++;
    const itemHTML = createItemHTML(itemCounter);
    itemsContainer.insertAdjacentHTML('beforeend', itemHTML);
}

// Crear HTML para un item
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
                    <label for="pieza_${itemNumber}">Pieza (NCM):</label>
                    <input type="text" id="pieza_${itemNumber}" name="pieza_${itemNumber}" required
                           placeholder="Ej: 84713010">
                </div>
                <div class="item-field">
                    <label for="descripcion_${itemNumber}">Descripción:</label>
                    <input type="text" id="descripcion_${itemNumber}" name="descripcion_${itemNumber}" required
                           placeholder="Ej: Computadora portátil">
                </div>
                <div class="item-field">
                    <label for="origen_${itemNumber}">Origen:</label>
                    <input type="text" id="origen_${itemNumber}" name="origen_${itemNumber}" required
                           placeholder="Ej: CN">
                </div>
                <div class="item-field">
                    <label for="peso_unitario_${itemNumber}">Peso Unitario (kg):</label>
                    <input type="number" id="peso_unitario_${itemNumber}" name="peso_unitario_${itemNumber}"
                           step="0.001" min="0" required placeholder="Ej: 2.5">
                </div>
                <div class="item-field">
                    <label for="cantidad_${itemNumber}">Cantidad:</label>
                    <input type="number" id="cantidad_${itemNumber}" name="cantidad_${itemNumber}"
                           step="0.01" min="0" required placeholder="Ej: 10">
                </div>
                <div class="item-field">
                    <label for="valor_unitario_${itemNumber}">Valor Unitario (USD):</label>
                    <input type="number" id="valor_unitario_${itemNumber}" name="valor_unitario_${itemNumber}"
                           step="0.01" min="0" required placeholder="Ej: 1500.00">
                </div>
                <div class="item-field">
                    <label for="marca_${itemNumber}">Marca (opcional):</label>
                    <input type="text" id="marca_${itemNumber}" name="marca_${itemNumber}"
                           placeholder="Ej: Apple">
                </div>
                <div class="item-field">
                    <label for="modelo_${itemNumber}">Modelo (opcional):</label>
                    <input type="text" id="modelo_${itemNumber}" name="modelo_${itemNumber}"
                           placeholder="Ej: MacBook Pro">
                </div>
                <div class="item-field">
                    <label for="version_${itemNumber}">Versión (opcional):</label>
                    <input type="text" id="version_${itemNumber}" name="version_${itemNumber}"
                           placeholder="Ej: 14.2">
                </div>
                <div class="item-field">
                    <label for="otros_${itemNumber}">Otros (especificaciones técnicas):</label>
                    <input type="text" id="otros_${itemNumber}" name="otros_${itemNumber}"
                           placeholder="Ej: DIN EN10305-5 +CR1">
                </div>
                <div class="item-field">
                    <label for="separador_${itemNumber}">Separador (interno):</label>
                    <input type="text" id="separador_${itemNumber}" name="separador_${itemNumber}"
                           placeholder="Campo interno AVG">
                </div>
                <div class="item-field">
                    <label for="ventaja_${itemNumber}">Ventaja (características):</label>
                    <input type="text" id="ventaja_${itemNumber}" name="ventaja_${itemNumber}"
                           placeholder="Ej: Alta resistencia">
                </div>
                <div class="item-field total-field">
                    <label>Total (calculado):</label>
                    <input type="text" id="total_${itemNumber}" readonly
                           placeholder="Se calcula automáticamente" class="calculated-field">
                </div>
            </div>
        </div>
    `;
}

// Remover un item
function removeItem(itemNumber) {
    const item = document.querySelector(`[data-item-id="${itemNumber}"]`);
    if (item) {
        item.remove();
        // Reordenar números de items restantes
        reorderItems();
    }
}

// Reordenar números de items después de remover uno
function reorderItems() {
    const items = document.querySelectorAll('.item');
    itemCounter = items.length;

    items.forEach((item, index) => {
        const newNumber = index + 1;
        const oldNumber = item.dataset.itemId;

        item.dataset.itemId = newNumber;
        item.querySelector('.item-number').textContent = `Item ${newNumber}`;

        // Actualizar IDs y names de inputs
        const inputs = item.querySelectorAll('input');
        inputs.forEach(input => {
            const fieldName = input.name.split('_')[0];
            input.id = `${fieldName}_${newNumber}`;
            input.name = `${fieldName}_${newNumber}`;
        });

        // Actualizar onclick del botón remover
        const removeBtn = item.querySelector('.remove-item');
        removeBtn.setAttribute('onclick', `removeItem(${newNumber})`);
    });
}

// Cambiar entre modos (manual/upload/pdf)
function switchMode(mode) {
    // Limpiar todos los estados activos
    manualModeBtn.classList.remove('active');
    uploadModeBtn.classList.remove('active');
    pdfModeBtn.classList.remove('active');
    
    // Ocultar todos los formularios
    operationForm.classList.add('hidden');
    uploadForm.classList.add('hidden');
    pdfForm.classList.add('hidden');
    
    hideResults();
    hideError();

    if (mode === 'manual') {
        manualModeBtn.classList.add('active');
        operationForm.classList.remove('hidden');
    } else if (mode === 'upload') {
        uploadModeBtn.classList.add('active');
        uploadForm.classList.remove('hidden');
    } else if (mode === 'pdf') {
        pdfModeBtn.classList.add('active');
        pdfForm.classList.remove('hidden');
    }
}

// Manejar subida de archivo Excel
async function handleUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];

    if (!file) {
        showError('Por favor selecciona un archivo Excel');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showError('El archivo Excel es demasiado grande (máximo 10MB)');
        return;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/upload_excel/', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail?.errors || data.detail || 'Error desconocido');
        }

        showSuccess(data);

    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// Manejar subida de archivo PDF
async function handlePdfUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];

    if (!file) {
        showError('Por favor selecciona un archivo PDF');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showError('El archivo PDF es demasiado grande (máximo 10MB)');
        return;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const formData = new FormData();
        formData.append('file', file);

        // Obtener método de extracción seleccionado
        const extractionMethod = document.getElementById('extractionMethod').value;
        let endpoint = '/upload_pdf_llm/'; // Default híbrido
        
        if (extractionMethod === 'gemini_only') {
            endpoint = '/upload_pdf_gemini_only/';
        } else if (extractionMethod === 'traditional') {
            endpoint = '/upload_pdf/'; // Parser tradicional
        }
        
        console.log(`🔄 Usando método: ${extractionMethod}, endpoint: ${endpoint}`);

        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Error procesando PDF');
        }

        // Mostrar items extraídos para revisión
        if (data.items && data.items.length > 0) {
            displayExtractedItems(data.items);
            showPdfSuccess(data);
        } else {
            throw new Error('No se encontraron items en el PDF');
        }

    } catch (error) {
        showError(`Error procesando PDF: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Limpiar formulario
function clearForm() {
    if (confirm('¿Estás seguro de que quieres limpiar todo? Se perderán todos los datos.')) {
        form.reset();
        itemsContainer.innerHTML = '';
        itemCounter = 0;
        addItem(); // Agregar un item vacío
        hideResults();
        hideError();
    }
}

// Manejar envío del formulario
async function handleSubmit(e) {
    e.preventDefault();

    showLoading();
    hideError();
    hideResults();

    try {
        const payload = collectFormData();

        const response = await fetch('/process_operation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail?.errors || data.detail || 'Error desconocido');
        }

        showSuccess(data);

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
        const otros = document.getElementById(`otros_${itemNumber}`).value.trim();
        const separador = document.getElementById(`separador_${itemNumber}`).value.trim();
        const ventaja = document.getElementById(`ventaja_${itemNumber}`).value.trim();

        // Agregar campos opcionales como strings
        if (marca) itemData.marca = marca;
        if (modelo) itemData.modelo = modelo;
        if (version) itemData.version = version;
        if (otros) itemData.otros = otros;
        if (separador) itemData.separador = separador;
        if (ventaja) itemData.ventaja = ventaja;

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

// Mostrar/ocultar elementos
function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function showSuccess(data) {
    let operationInfo = '';
    let itemsInfo = '';

    // Determinar el tipo de respuesta (manual vs upload)
    if (data.validated_items_count !== undefined) {
        // Respuesta de ingreso manual
        operationInfo = `<p><strong>Operación:</strong> ${data.filename.replace('AVG_', '').split('_')[0]}</p>`;
        itemsInfo = `<p><strong>Items validados:</strong> ${data.validated_items_count}</p>`;
    } else if (data.items_procesados !== undefined) {
        // Respuesta de subida de archivo
        operationInfo = `<p><strong>Archivo procesado:</strong> ${data.filename.replace('AVG_', '').split('_')[0]}</p>`;
        itemsInfo = `
            <p><strong>Items extraídos:</strong> ${data.items_extraidos}</p>
            <p><strong>Items procesados:</strong> ${data.items_procesados}</p>
        `;
    }

    successMessage.innerHTML = `
        ${operationInfo}
        ${itemsInfo}
        <p><strong>Archivo generado:</strong> ${data.filename}</p>
    `;

    downloadLink.href = `/download/${data.filename}`;
    results.classList.remove('hidden');
}

function hideResults() {
    results.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

// Nuevas funciones para manejo de PDF
function displayExtractedItems(items) {
    // Limpiar items existentes
    itemsContainer.innerHTML = '';
    itemCounter = 0;
    
    // Generar código de operación automático
    const operationIdField = document.getElementById('operationId');
    if (!operationIdField.value) {
        const timestamp = new Date().toISOString().slice(0,10).replace(/-/g,'');
        operationIdField.value = `PDF_${timestamp}`;
    }
    
    // Agregar cada item extraído
    items.forEach((item, index) => {
        addItem();
        const currentItemNumber = itemCounter;
        
        // Llenar campos con datos extraídos
        fillItemFields(currentItemNumber, item);
    });
    
    // Cambiar a modo manual para mostrar los items
    switchMode('manual');
    
    // Scroll al primer item
    const firstItem = document.querySelector('.item');
    if (firstItem) {
        firstItem.scrollIntoView({ behavior: 'smooth' });
    }
}

function fillItemFields(itemNumber, itemData) {
    // Campos básicos
    setValue(`pieza_${itemNumber}`, itemData.pieza || '');
    setValue(`descripcion_${itemNumber}`, itemData.descripcion || '');
    setValue(`origen_${itemNumber}`, itemData.origen || 'XX');
    setValue(`peso_unitario_${itemNumber}`, itemData.peso_unitario || 0);
    setValue(`cantidad_${itemNumber}`, itemData.cantidad || 1);
    setValue(`valor_unitario_${itemNumber}`, itemData.valor_unitario || 0);
    
    // Campos nuevos
    setValue(`marca_${itemNumber}`, itemData.marca || '');
    setValue(`modelo_${itemNumber}`, itemData.modelo || '');
    setValue(`version_${itemNumber}`, itemData.version || '');
    setValue(`otros_${itemNumber}`, itemData.otros || '');
    setValue(`separador_${itemNumber}`, itemData.separador || '');
    setValue(`ventaja_${itemNumber}`, itemData.ventaja || '');
    
    // Calcular y mostrar total
    updateCalculatedTotal(itemNumber);
}

function setValue(fieldId, value) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = value;
        // Trigger change event para cualquier listener
        field.dispatchEvent(new Event('change'));
    }
}

function updateCalculatedTotal(itemNumber) {
    const cantidad = parseFloat(document.getElementById(`cantidad_${itemNumber}`).value) || 0;
    const valorUnitario = parseFloat(document.getElementById(`valor_unitario_${itemNumber}`).value) || 0;
    const total = (cantidad * valorUnitario).toFixed(2);
    
    const totalField = document.getElementById(`total_${itemNumber}`);
    if (totalField) {
        totalField.value = `$${total}`;
    }
}

function showPdfSuccess(data) {
    const itemCount = data.items ? data.items.length : 0;
    const method = data.extraction_method || 'automático';
    
    showSuccess({
        filename: `PDF_extraido_${new Date().toISOString().slice(0,10)}.xlsx`,
        validated_items_count: itemCount,
        items_extraidos: itemCount,
        items_procesados: itemCount
    });
    
    // Mensaje específico para PDF
    const successMsg = document.getElementById('successMessage');
    successMsg.innerHTML = `
        <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
            <h3 style="color: #0ea5e9; margin: 0 0 0.5rem 0;">
                <i class="fas fa-file-pdf"></i> PDF Procesado Exitosamente
            </h3>
            <p><strong>Items extraídos:</strong> ${itemCount}</p>
            <p><strong>Método:</strong> ${method}</p>
            <p><strong>Estado:</strong> Listo para revisar y generar Excel</p>
            <p style="margin: 0; font-size: 0.9em; color: #64748b;">
                💡 Revisa los datos extraídos arriba y haz clic en "Generar Excel AVG" cuando estés listo.
            </p>
        </div>
    ` + successMsg.innerHTML;
}
