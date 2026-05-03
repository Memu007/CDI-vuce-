# 📚 DOCUMENTACIÓN TÉCNICA - CDI (Carga y Despacho Inteligente)

## 🧭 Roadmap del Proyecto

Consulta el plan por fases, criterios de aceptación y próximos pasos en:
- `documentacion_tecnica/ROADMAP.md`

## 📒 Playbook del Proyecto

Reglas de simplicidad, roles y registro vivo de decisiones:
- `documentacion_tecnica/PLAYBOOK.md`

## 🎯 **Para Programadores y Desarrolladores**

Esta carpeta contiene **toda la documentación técnica** del sistema CDI. Está diseñada para que cualquier programador pueda entender, mantener y extender el código fácilmente.

---

## 📁 **ARCHIVOS EN ESTA CARPETA**

### 📖 **1. GUIA_PARA_PROGRAMADOR.md**
**🎯 EMPEZAR AQUÍ** - Guía principal para desarrolladores
- **Stack tecnológico** completo explicado
- **Arquitectura del sistema** paso a paso
- **Patrones de diseño** implementados
- **Decisiones técnicas** justificadas
- **Ejemplos de código** comentados
- **Testing strategy** completa
- **Roadmap de mejoras** futuras

### 🏗️ **2. DOCUMENTACION_CODIGO.md**
**📊 Arquitectura detallada** del proyecto
- **Estructura de carpetas** explicada
- **Flujo de datos** completo
- **Responsabilidades** de cada módulo
- **Diagramas conceptuales** del sistema

### 💻 **3. COMENTARIOS_CODIGO.py**
**🔍 Explicación conceptual** profunda
- **Patrones de diseño** identificados
- **Algoritmos** explicados paso a paso
- **Estrategias de implementación**
- **Mejores prácticas** aplicadas

---

## 🚀 **ORDEN DE LECTURA RECOMENDADO**

### **Para programador nuevo en el proyecto:**
1. **GUIA_PARA_PROGRAMADOR.md** ← Empezar aquí
2. **DOCUMENTACION_CODIGO.md** ← Arquitectura general
3. **COMENTARIOS_CODIGO.py** ← Detalles técnicos profundos

### **Para debugging/troubleshooting:**
1. Logs del servidor: `python server_nuevo.py`
2. Consola del navegador: `F12 → Console`
3. Tests: `pytest -v`

### **Para agregar funcionalidades:**
1. Leer **GUIA_PARA_PROGRAMADOR.md** sección "Extensibilidad"
2. Seguir patrones existentes en `core/`
3. Agregar tests correspondientes

---

## 🔧 **QUICK START PARA DESARROLLADORES**

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar tests
pytest --cov=.

# 3. Iniciar servidor de desarrollo
python server_nuevo.py

# 4. Ver documentación API
# http://127.0.0.1:8001/api/docs
```

---

## 🎯 **CONCEPTOS CLAVE**

### **🤖 "IA" del Sistema:**
No es machine learning complejo, sino **patrones regex inteligentes** que:
- Detectan códigos NCM en texto
- Identifican precios y cantidades
- Extraen descripciones de productos
- Se adaptan a diferentes formatos

### **📊 Detección de Columnas:**
**Algoritmo de mapeo** que prueba diferentes combinaciones:
```python
possible_mappings = [
    {'pieza': ['codigo', 'ncm', 'pieza'], 'descripcion': ['desc', 'descripcion']},
    {'pieza': ['part_number', 'item'], 'descripcion': ['description', 'product']}
]
```

### **✅ Validación en Capas:**
1. **Frontend**: Validación básica (campos requeridos)
2. **Pydantic**: Validación de tipos automática
3. **Business Logic**: Reglas específicas del dominio aduanero

---

## 🔍 **DEBUGGING TIPS**

### **Logs útiles:**
```python
# Backend (server_nuevo.py)
print(f"📄 Procesando: {filename}")
print(f"📊 Items extraídos: {len(items)}")
print(f"✅ Items válidos: {len(valid_items)}")

# Frontend (script_caca.js)
console.log('🔄 Iniciando procesamiento...');
console.log('📊 Datos recibidos:', data);
```

### **Archivos a revisar si hay problemas:**
- **Excel no procesa**: `core/excel_generator.py` + `extract_items_from_excel()`
- **PDF no extrae datos**: `core/pdf_processor.py` + patrones regex
- **Validación falla**: `core/validations.py` + reglas de negocio
- **UI no responde**: `script_caca.js` + event listeners

---

## 🎪 **PARA LA REUNIÓN**

### **Puntos técnicos que puedes mencionar:**
- **"Sistema modular"** - fácil agregar nuevos formatos
- **"Validación robusta"** - múltiples capas de verificación
- **"IA integrada"** - extracción automática de patrones
- **"Arquitectura escalable"** - preparado para crecimiento

### **Si preguntan detalles técnicos:**
- **Stack**: "FastAPI + Pandas + JavaScript puro"
- **Testing**: "pytest con cobertura completa"
- **Deployment**: "Docker ready, nginx compatible"
- **Escalabilidad**: "Microservicios, async, stateless"

---

## 📞 **SOPORTE TÉCNICO**

### **Comandos útiles:**
```bash
# Ver logs en tiempo real
python server_nuevo.py

# Ejecutar tests
pytest -v

# Verificar dependencias
pip list

# Limpiar archivos temporales
rm temp_*.* AVG_*.xlsx
```

### **Archivos importantes:**
- `server_nuevo.py` - Servidor principal
- `requirements.txt` - Dependencias
- `pytest.ini` - Configuración de tests
- `README_REUNION_FINAL.md` - Guía de presentación

---

**¡Documentación completa y organizada para máxima comprensión técnica!** 🚀✨

