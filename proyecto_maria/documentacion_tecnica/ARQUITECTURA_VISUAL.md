# 🏗️ ARQUITECTURA VISUAL - CACA Optimizador MARIA

## 📊 **DIAGRAMA DE COMPONENTES**

```
┌─────────────────────────────────────────────────────────────────┐
│                    🏢 CACA - INTERFAZ CORPORATIVA                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │   📝 Manual     │ │   📊 Excel      │ │   📄 PDF        │    │
│  │   Formularios   │ │   Inteligente   │ │   con IA        │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      🚀 FASTAPI BACKEND                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │ /process_op/    │ │ /upload_excel/  │ │ /upload_pdf/    │    │
│  │ (Manual)        │ │ (Excel)         │ │ (PDF + IA)      │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   🧠 PROCESAMIENTO INTELIGENTE                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │ Detección       │ │ Extracción      │ │ Validación      │    │
│  │ Columnas        │ │ PDF con Regex   │ │ Reglas Negocio  │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     📄 GENERADOR EXCEL AVG                      │
│              ┌─────────────────────────────────────┐            │
│              │  13 Columnas Exactas + Cálculos    │            │
│              │  Formato 100% Compatible MARIA     │            │
│              └─────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **FLUJO DE PROCESAMIENTO DETALLADO**

### **📊 Procesamiento de Excel Desordenado:**

```
📁 EXCEL CAÓTICO
│
├── Columnas: ['codigo', 'desc', 'pais', 'peso', 'cant', 'precio']
├── 8 filas con datos mezclados
├── Errores de validación incluidos
└── Columnas extra innecesarias
                                │
                                ▼
🧠 DETECCIÓN INTELIGENTE
│
├── Prueba mapeo 1: 'codigo' → 'pieza' ✅
├── Prueba mapeo 2: 'desc' → 'descripcion' ✅  
├── Prueba mapeo 3: 'pais' → 'origen' ✅
└── Mapeo exitoso encontrado!
                                │
                                ▼
🔍 VALIDACIÓN DE REGLAS
│
├── Item 1: ✅ Válido
├── Item 2: ✅ Válido  
├── Item 3: ❌ Cantidad = 0 (filtrado)
├── Item 4: ✅ Válido
├── Item 5: ❌ Precio negativo (filtrado)
└── Resultado: 5 de 8 items válidos
                                │
                                ▼
📄 EXCEL AVG GENERADO
│
├── Columnas: ['Pieza', 'Descripcion', 'Origen', ...]
├── 5 filas válidas
├── TOTAL calculado automáticamente
└── Formato 100% compatible MARIA
```

### **📄 Procesamiento de PDF con IA:**

```
📄 PDF DE FACTURA
│
├── Texto: "Synergy Global Trading LLC..."
├── Números: "71490347", "689.00", "1,378.00"
├── Tablas: 1 tabla detectada
└── Páginas: 1 página
                                │
                                ▼
🤖 EXTRACCIÓN CON IA (Regex Patterns)
│
├── Patrón NCM: \b\d{6,8}\b → Encuentra: "71490347"
├── Patrón Precio: USD\s*(\d+\.\d{2}) → Encuentra: "689.00"
├── Patrón Cantidad: (\d+)\s*(pcs|qty) → No encuentra
└── Patrón Descripción: description[:\s]+([A-Za-z\s]+) → No encuentra
                                │
                                ▼
🧠 FALLBACK INTELIGENTE
│
├── Datos encontrados: NCM ✅, Empresa ✅
├── Datos faltantes: Cantidad, Descripción específica
├── Crea item válido con defaults inteligentes
└── Item: "71490347 - Synergy Global Trading LLC 848"
                                │
                                ▼
📄 EXCEL AVG GENERADO
│
├── 1 item procesado
├── Datos reales del PDF + defaults
├── Formato AVG válido
└── Listo para MARIA
```

---

## 🎨 **ARQUITECTURA FRONTEND**

### **Componentes de la Interfaz:**

```
🌐 INTERFAZ CACA (interfaz_caca.html)
│
├── 🏢 HEADER CORPORATIVO
│   ├── Logo CACA con ícono shipping
│   ├── "Central Automatizada de Comercio Aduanero"
│   └── Badge "v2.0 Professional"
│
├── 🎯 HERO SECTION
│   ├── Título impactante
│   ├── Descripción del valor
│   └── Estadísticas: [3 Formatos] [100% MARIA] [IA]
│
├── 🃏 MODE CARDS (3 opciones)
│   ├── Card Manual: Formularios web
│   ├── Card Excel: Detección inteligente
│   └── Card PDF: Extracción con IA
│
├── 📝 FORMULARIOS DINÁMICOS
│   ├── Form Manual: Items con campos completos
│   ├── Form Excel: Drag & drop zone
│   └── Form PDF: Upload con feedback IA
│
├── 📊 RESULTADOS
│   ├── Estadísticas de procesamiento
│   ├── Información del archivo generado
│   └── Botón de descarga
│
└── 🏢 FOOTER CORPORATIVO
    ├── Información CACA
    ├── Detalles del producto
    └── Soporte técnico
```

### **Sistema de Estilos (estilos_caca.css):**

```css
/* === SISTEMA DE DISEÑO CORPORATIVO === */

:root {
  /* Colores CACA */
  --primary-blue: #1e40af;      /* Azul corporativo principal */
  --secondary-gold: #f59e0b;    /* Dorado de acento */
  --accent-green: #10b981;      /* Verde para éxito */
  
  /* Gradientes profesionales */
  --gradient-primary: linear-gradient(135deg, azul → azul oscuro);
  --gradient-hero: linear-gradient(135deg, púrpura → azul);
  
  /* Sombras en 4 niveles */
  --shadow-sm/md/lg/xl: Profundidad progresiva;
}

/* === COMPONENTES REUTILIZABLES === */
.mode-card {
  /* Card interactiva con hover effects */
  /* Transform animations */
  /* Estados: normal, hover, active */
}

.upload-area {
  /* Zona drag & drop */
  /* Estados visuales para feedback */
  /* Animaciones suaves */
}

.btn-primary {
  /* Botón principal con gradiente */
  /* Micro-interacciones */
  /* Estados de hover y active */
}
```

### **JavaScript Moderno (script_caca.js):**

```javascript
// === ARQUITECTURA MODULAR ===

// 1. ESTADO DE LA APLICACIÓN
let appState = {
    currentMode: 'manual',
    itemCounter: 0,
    isProcessing: false
};

// 2. GESTIÓN DE EVENTOS
function setupEventListeners() {
    // Centraliza todos los event listeners
    // Evita memory leaks
    // Patrón Observer limpio
}

// 3. MANEJO DE ARCHIVOS
async function handleUpload(e) {
    // Async/await para operaciones no bloqueantes
    // FormData para archivos
    // Fetch API moderna (no jQuery)
    // Error handling robusto
}

// 4. GESTIÓN DE ESTADO UI
function switchMode(mode) {
    // Limpia estados anteriores
    // Activa nuevo estado
    // Animaciones CSS automáticas
}

// 5. DRAG & DROP NATIVO
function setupDropZone(area, fileInput) {
    // HTML5 Drag & Drop API
    // Feedback visual inmediato
    // Compatibilidad universal
}
```

---

## 🧪 **TESTING ARCHITECTURE**

```
tests/
├── 🧪 UNIT TESTS (Rápidos, específicos)
│   ├── test_models.py          # Pydantic validation
│   ├── test_validations.py     # Business rules
│   ├── test_excel_generator.py # Excel creation
│   └── test_pdf_processor.py   # PDF extraction
│
├── 🔗 INTEGRATION TESTS (Componentes juntos)
│   └── test_api_integration.py # Full API workflows
│
└── 🎭 E2E TESTS (Experiencia completa)
    └── demo_reunion.py         # Real user simulation
```

**Cobertura actual:** ~90% del código testeado

---

## 🚀 **DEPLOYMENT STRATEGY**

### **Desarrollo (Actual):**
```bash
python server_nuevo.py  # Puerto 8001, hot reload
```

### **Producción (Futuro):**
```dockerfile
# Dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 80
CMD ["uvicorn", "server_nuevo:app", "--host", "0.0.0.0", "--port", "80"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  caca-app:
    build: .
    ports:
      - "80:80"
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: caca_maria
```

---

## 💡 **EXTENSIONES SUGERIDAS**

### **Corto plazo (1-2 semanas):**
- **API VUCE**: Enriquecimiento automático de NCMs
- **Base de datos**: PostgreSQL para persistir operaciones
- **Autenticación**: Login de usuarios

### **Mediano plazo (1-2 meses):**
- **Dashboard**: Estadísticas y reportes
- **API REST completa**: Para integraciones
- **Batch processing**: Múltiples archivos simultáneos

### **Largo plazo (3-6 meses):**
- **OCR avanzado**: Para PDFs escaneados
- **Machine Learning**: Clasificación automática
- **Multi-tenant**: Múltiples empresas

---

**¡Tu amigo programador tendrá TODO lo necesario para entender y trabajar con el código!** 🎯✨

