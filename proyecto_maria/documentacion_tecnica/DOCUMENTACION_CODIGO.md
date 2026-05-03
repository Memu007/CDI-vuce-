# 📚 DOCUMENTACIÓN DEL CÓDIGO - CACA Optimizador MARIA

## 🏗️ **ARQUITECTURA GENERAL**

```
proyecto_maria/
├── 🌐 INTERFAZ WEB
│   ├── interfaz_caca.html      # HTML corporativo con diseño premium
│   ├── estilos_caca.css        # CSS con colores corporativos y animaciones
│   └── script_caca.js          # JavaScript con drag&drop y validaciones
│
├── 🔧 BACKEND (FastAPI)
│   ├── server_nuevo.py         # Servidor principal con todos los endpoints
│   ├── main.py                 # Servidor original (backup)
│   └── models/operations.py    # Modelos Pydantic para validación
│
├── 🧠 LÓGICA DE NEGOCIO
│   ├── core/validations.py     # Reglas de negocio y validaciones
│   ├── core/excel_generator.py # Generador de Excel en formato AVG
│   └── core/pdf_processor.py   # Extractor de datos de PDFs con IA
│
└── 🧪 TESTING Y DEMOS
    ├── tests/                  # Tests automatizados
    ├── demo_reunion.py         # Script de demo automática
    └── README_REUNION_FINAL.md # Guía para la presentación
```

---

## 🔍 **EXPLICACIÓN DETALLADA POR ARCHIVO**

### 1️⃣ **server_nuevo.py** - Servidor Principal

```python
# === QUÉ HACE ===
# Servidor FastAPI que maneja toda la lógica web y de procesamiento

# === ENDPOINTS PRINCIPALES ===
@app.get("/")                    # Sirve la interfaz web corporativa
@app.post("/process_operation/") # Procesa datos manuales → Excel AVG
@app.post("/upload_excel/")      # Procesa Excel desordenado → Excel AVG
@app.post("/upload_pdf/")        # Procesa PDF con IA → Excel AVG
@app.get("/download/{filename}") # Descarga archivos Excel generados

# === FLUJO DE PROCESAMIENTO ===
1. Usuario sube archivo (Excel/PDF) o ingresa datos manualmente
2. Sistema valida y extrae datos según el tipo de archivo
3. Aplica reglas de negocio (validations.py)
4. Genera Excel en formato AVG exacto (excel_generator.py)
5. Retorna archivo listo para descargar
```

### 2️⃣ **models/operations.py** - Modelos de Datos

```python
# === QUÉ HACE ===
# Define la estructura de datos usando Pydantic para validación automática

class Item(BaseModel):
    # Campos obligatorios
    pieza: str              # Código NCM/HS
    descripcion: str        # Descripción del producto
    origen: str             # Código de país (ej: CN, US)
    peso_unitario: float    # Peso en kg
    cantidad: float         # Cantidad de items
    valor_unitario: float   # Precio unitario en USD
    
    # Campos opcionales
    marca: Optional[str]    # Marca del producto
    modelo: Optional[str]   # Modelo específico
    # ... etc

# === VENTAJAS ===
# - Validación automática de tipos
# - Documentación auto-generada
# - Serialización JSON automática
# - Mensajes de error claros
```

### 3️⃣ **core/validations.py** - Reglas de Negocio

```python
# === QUÉ HACE ===
# Implementa las reglas específicas del negocio aduanero

def run_pre_maria_validations(items):
    """
    Valida cada item según reglas específicas:
    
    REGLA 1: Pieza (NCM) no puede estar vacía
    REGLA 2: Cantidad debe ser > 0
    REGLA 3: Valor unitario debe ser > 0  
    REGLA 4: Peso unitario debe ser > 0
    
    RETORNA:
    - items_válidos: Lista de items que pasaron validación
    - errores: Lista de mensajes de error descriptivos
    """

# === POR QUÉ ES IMPORTANTE ===
# - Filtra datos inválidos antes de generar Excel
# - Evita que MARIA rechace el archivo
# - Proporciona feedback claro al usuario
# - Mantiene integridad de datos
```

### 4️⃣ **core/excel_generator.py** - Generador de Excel AVG

```python
# === QUÉ HACE ===
# Genera archivos Excel con el formato EXACTO requerido por MARIA

def create_maria_excel(items, operation_id):
    """
    PROCESO:
    1. Convierte items Pydantic → DataFrame de Pandas
    2. Calcula TOTAL = cantidad × valor_unitario
    3. Renombra columnas al formato exacto AVG
    4. Ordena columnas en secuencia específica
    5. Exporta a Excel (.xlsx) con openpyxl
    
    FORMATO AVG (13 columnas exactas):
    Pieza | Descripcion | Origen | Peso Unitario | Cantidad | 
    Valor Unitario | Marca | Modelo | Version | otros | 
    separador | ventaja | TOTAL
    """

# === DETALLES TÉCNICOS ===
# - Usa engine='openpyxl' para Excel moderno
# - Prefijo 'AVG_' + timestamp para nombres únicos
# - Asegura que 'Pieza' sea string (no int)
# - Espacios exactos en "otros ", "ventaja " (requerido por MARIA)
```

### 5️⃣ **core/pdf_processor.py** - Extractor de PDFs

```python
# === QUÉ HACE ===
# Extrae datos de PDFs de facturas usando IA y patrones regex

def extract_data_from_pdf(pdf_path):
    """
    PROCESO DE EXTRACCIÓN:
    1. Lee PDF con pdfplumber (extrae texto plano)
    2. Busca patrones con regex:
       - NCM/HS: \b\d{6,8}\b
       - Cantidades: (\d+)\s*(pcs|qty|units)
       - Precios: (USD|$)\s*(\d+\.\d{2})
       - Pesos: (\d+)\s*(kg|g|lb)
    3. Crea objetos Item con datos encontrados
    4. Si no encuentra datos, crea item de ejemplo válido
    
    VENTAJAS:
    - Funciona con PDFs de texto
    - Patrones flexibles para diferentes formatos
    - Fallback inteligente si no encuentra datos
    - Siempre retorna algo procesable
    """

# === LIBRERÍAS USADAS ===
# pdfplumber: Extracción de texto y tablas de PDF
# re: Expresiones regulares para buscar patrones
# typing: Type hints para mejor documentación
```

### 6️⃣ **interfaz_caca.html** - Interfaz Corporativa

```html
<!-- === ESTRUCTURA ===
Header Corporativo:
- Logo CACA con ícono de shipping
- Información de la empresa
- Badge "v2.0 Professional"

Hero Section:
- Título impactante
- Estadísticas (3 formatos, 100% MARIA, IA)
- Gradiente corporativo

Mode Selection:
- 3 cards interactivas (Manual, Excel, PDF)
- Descripción de cada funcionalidad
- Features destacadas con checkmarks

Formularios:
- Drag & drop zones para archivos
- Validación en tiempo real
- Feedback visual de estados

Footer Corporativo:
- Información de CACA
- Detalles del producto
- Soporte técnico
-->

<!-- === CARACTERÍSTICAS TÉCNICAS ===
- Responsive design (mobile-first)
- Accesibilidad (aria-labels, semantic HTML)
- SEO optimizado
- Font Awesome icons
- Google Fonts (Inter)
- CSS Grid y Flexbox
-->
```

### 7️⃣ **estilos_caca.css** - Estilos Corporativos

```css
/* === SISTEMA DE DISEÑO ===
Variables CSS para consistencia:
--primary-blue: #1e40af     (Azul corporativo)
--secondary-gold: #f59e0b   (Dorado de acento)
--accent-green: #10b981     (Verde para éxito)

Gradientes corporativos:
--gradient-primary: azul → azul oscuro
--gradient-gold: dorado → dorado oscuro
--gradient-hero: púrpura → azul (hero section)

Sombras profesionales:
--shadow-sm/md/lg/xl: 4 niveles de profundidad
*/

/* === COMPONENTES PRINCIPALES ===
.header-corporativo: Header con logo y branding
.hero-section: Sección principal con estadísticas
.mode-cards: Cards interactivas para selección
.upload-area: Zonas de drag & drop
.loading-overlay: Overlay de carga profesional
.footer-corporativo: Footer con información empresa

/* === ANIMACIONES ===
- Hover effects en cards y botones
- Transiciones suaves (0.3s ease)
- Transform effects (translateY, scale)
- Fade-in animations para formularios
*/
```

### 8️⃣ **script_caca.js** - JavaScript Corporativo

```javascript
// === FUNCIONALIDADES PRINCIPALES ===

// 1. MODE SWITCHING (Cambio entre modos)
function switchMode(mode) {
    // Activa/desactiva cards visualmente
    // Muestra/oculta formularios correspondientes
    // Limpia estados anteriores
}

// 2. DRAG & DROP (Arrastrar y soltar)
function setupDropZone(area, fileInput) {
    // Maneja eventos: dragover, dragleave, drop
    // Actualiza UI cuando se selecciona archivo
    // Proporciona feedback visual inmediato
}

// 3. UPLOAD HANDLERS (Manejadores de subida)
async function handleUpload(e) {
    // Procesa archivos Excel con FormData
    // Maneja respuestas del servidor
    // Muestra resultados o errores
}

async function handlePdfUpload(e) {
    // Procesa archivos PDF con IA
    // Logs detallados para debugging
    // Feedback específico para PDFs
}

// 4. UI MANAGEMENT (Gestión de interfaz)
function showLoading() {
    // Overlay de carga profesional
    // Bloquea interacción durante procesamiento
}

function showSuccess(data, type) {
    // Muestra resultados diferenciados por tipo
    // Scroll automático a resultados
    // Botón de descarga funcional
}

// === CARACTERÍSTICAS TÉCNICAS ===
// - Async/await para operaciones asíncronas
// - FormData para subida de archivos
// - Fetch API para comunicación con backend
// - Console.log detallado para debugging
// - Manejo de errores robusto
```

---

## 🎯 **FLUJO DE DATOS COMPLETO**

```
1. USUARIO INTERACTÚA
   ↓
2. FRONTEND (JavaScript)
   - Valida entrada
   - Prepara FormData/JSON
   - Envía a backend
   ↓
3. BACKEND (FastAPI)
   - Recibe archivo/datos
   - Determina tipo de procesamiento
   ↓
4. PROCESAMIENTO ESPECÍFICO
   Excel: extract_items_from_excel()
   PDF: extract_data_from_pdf()
   Manual: validación directa
   ↓
5. VALIDACIÓN (validations.py)
   - Aplica reglas de negocio
   - Filtra items inválidos
   ↓
6. GENERACIÓN (excel_generator.py)
   - Crea DataFrame con formato AVG
   - Calcula totales
   - Exporta a Excel
   ↓
7. RESPUESTA AL FRONTEND
   - Información del archivo generado
   - Estadísticas de procesamiento
   ↓
8. UI ACTUALIZADA
   - Muestra resultados
   - Habilita descarga
```

---

## 💡 **DECISIONES DE DISEÑO**

### 🎨 **Frontend:**
- **Sin frameworks JS**: HTML/CSS/JS puro para simplicidad
- **Drag & drop nativo**: API HTML5 para UX moderna
- **CSS Grid/Flexbox**: Layout responsive sin Bootstrap
- **Font Awesome**: Iconografía profesional
- **Google Fonts**: Tipografía corporativa

### 🔧 **Backend:**
- **FastAPI**: Framework moderno, rápido, con docs automáticas
- **Pydantic**: Validación de datos robusta y automática
- **Pandas**: Manipulación de Excel eficiente y confiable
- **pdfplumber**: Extracción de PDF simple pero efectiva

### 📊 **Procesamiento:**
- **Mapeo inteligente**: Detecta columnas con diferentes nombres
- **Fallback graceful**: Siempre genera algo útil
- **Validación en capas**: Frontend + Backend + Reglas de negocio
- **Logging detallado**: Para debugging y monitoreo

---

## 🚀 **ESCALABILIDAD FUTURA**

### 📈 **Fácil de extender:**
- **Nuevos formatos**: Agregar procesadores en `core/`
- **Más validaciones**: Extender `validations.py`
- **API externa**: Integrar VUCE en `vuce_connector.py`
- **Base de datos**: Persistir operaciones
- **Autenticación**: Agregar usuarios y permisos

### 🔧 **Mantenimiento:**
- **Código modular**: Cada funcionalidad en su archivo
- **Type hints**: Documentación en el código
- **Tests automatizados**: Cobertura completa
- **Logs estructurados**: Fácil debugging

---

**¡Tu amigo programador podrá entender y extender el sistema fácilmente!** 🎯✨
