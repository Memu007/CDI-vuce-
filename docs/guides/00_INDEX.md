# 📁 ESTRUCTURA DE DOCUMENTACIÓN - PROYECTO MARÍA

**Sistema de documentación limpio y mantenible**
**Actualizado**: 2025-09-30
**Archivos totales**: 6 (máximo)

---

## 🎯 **FILOSOFÍA**

- **Máximo 6 archivos MD en raíz**
- **Cada archivo tiene un propósito específico**
- **Orden de lectura numerado (00, 01, 02...)**
- **Eliminar obsoletos periódicamente**
- **Una AI puede leer 00_INDEX.md y entender todo**

---

## 📚 **LOS 6 ARCHIVOS ESENCIALES**

### **00_INDEX.md** (ESTE ARCHIVO)
**Propósito**: Índice maestro que guía toda la lectura
**Contenido**:
- Estructura del proyecto
- Orden de lectura
- Qué contiene cada archivo
- Cómo empezar

### **01_PROYECTO.md**
**Propósito**: QUÉ es el proyecto, PARA QUÉ sirve, A QUIÉN apunta
**Contenido**:
- Descripción general
- Problema que resuelve
- Mercado objetivo (despachantes chicos/medianos)
- Propuesta de valor
- Stack tecnológico
- Arquitectura general

### **02_ESTADO_ACTUAL.md**
**Propósito**: DÓNDE estamos HOY (snapshot actual)
**Contenido**:
- Features completadas (con links a código)
- Features en progreso
- Features pendientes
- Métricas (% completado, tests, bugs)
- Últimas decisiones técnicas
- **Se actualiza cada sesión**

### **03_HISTORIAL.md**
**Propósito**: QUÉ hicimos y CUÁNDO (timeline completo)
**Contenido**:
- Changelog ordenado por fecha (más reciente arriba)
- Cada entrada: fecha, feature, cambios, archivos modificados
- Decisiones arquitectónicas importantes
- Problemas resueltos
- **Append-only** (solo agregar, nunca borrar)

### **04_COMO_USAR.md**
**Propósito**: CÓMO probar y usar lo implementado
**Contenido**:
- Guías de testing para cada feature
- Comandos de prueba (curl, bash, python)
- Ejemplos de uso reales
- Troubleshooting común
- **Se actualiza cuando se completa una feature**

### **05_ROADMAP.md**
**Propósito**: HACIA DÓNDE vamos (futuro)
**Contenido**:
- Features vendibles priorizadas
- Plan de implementación (semana 1, 2, 3)
- Features descartadas y por qué
- Decisiones estratégicas
- Próximos pasos

---

## 📖 **ORDEN DE LECTURA PARA UNA AI NUEVA**

### **Lectura Rápida (5 min)**
1. Lee `00_INDEX.md` (este archivo) - Estructura
2. Lee `01_PROYECTO.md` - Qué es MARÍA
3. Lee `02_ESTADO_ACTUAL.md` - Dónde estamos hoy

**Ya tiene contexto suficiente para trabajar**

### **Lectura Completa (15 min)**
1. Lee `00_INDEX.md` - Estructura
2. Lee `01_PROYECTO.md` - Contexto general
3. Lee `02_ESTADO_ACTUAL.md` - Estado actual
4. Lee `03_HISTORIAL.md` - Timeline completo
5. Lee `04_COMO_USAR.md` - Cómo probar
6. Lee `05_ROADMAP.md` - Hacia dónde vamos

**Ahora tiene contexto COMPLETO**

### **Lectura de Código**
Después de leer los docs, revisar:
- `proyecto_maria/server_funcional.py` - Server principal
- `proyecto_maria/routers/` - Endpoints modulares
- `proyecto_maria/core/` - Lógica de negocio

---

## 🗂️ **ESTRUCTURA DE CARPETAS**

```
despachte nuevo/
├── 00_INDEX.md                      ← Índice maestro (EMPEZAR ACÁ)
├── 01_PROYECTO.md                   ← Qué es MARÍA
├── 02_ESTADO_ACTUAL.md              ← Dónde estamos hoy
├── 03_HISTORIAL.md                  ← Qué hicimos (changelog)
├── 04_COMO_USAR.md                  ← Cómo probar features
├── 05_ROADMAP.md                    ← Hacia dónde vamos
│
├── proyecto_maria/                  ← Código fuente
│   ├── server_funcional.py          ← Server FastAPI
│   ├── routers/                     ← Endpoints modulares
│   │   ├── pdf_router.py
│   │   ├── client_router.py
│   │   └── calculator_router.py
│   ├── core/                        ← Lógica de negocio
│   │   ├── calculator.py
│   │   ├── datastore.py
│   │   └── validations.py
│   ├── services/                    ← Servicios
│   │   ├── client_service.py
│   │   └── cache_service.py
│   ├── database/                    ← DB models
│   │   ├── models.py
│   │   └── connection.py
│   └── models/                      ← Pydantic models
│       └── operations.py
│
├── tests/                           ← Tests
│   └── conftest.py
│
├── .env                             ← Variables de entorno
├── requirements.txt                 ← Dependencias
├── docker-compose.yml               ← Docker setup
└── pdf_extractor.py                 ← Extractor standalone
```

---

## 🔄 **PROCESO DE ACTUALIZACIÓN**

### **Después de cada sesión de desarrollo:**

1. **Actualizar `02_ESTADO_ACTUAL.md`**
   - Cambiar estado de features (pending → completed)
   - Actualizar métricas
   - Agregar decisiones técnicas nuevas

2. **Agregar entrada en `03_HISTORIAL.md`**
   - Fecha + feature + cambios
   - Archivos modificados
   - Resultados de tests

3. **Actualizar `04_COMO_USAR.md`** (si aplica)
   - Agregar guía de la feature nueva
   - Ejemplos de uso
   - Comandos de prueba

4. **Revisar `05_ROADMAP.md`** (si aplica)
   - Mover features completadas
   - Ajustar prioridades

### **NO actualizar:**
- `00_INDEX.md` (solo si cambia estructura)
- `01_PROYECTO.md` (solo si cambia scope)

---

## 🗑️ **ARCHIVOS A ELIMINAR (Obsoletos)**

Estos archivos ya NO son necesarios porque su contenido está consolidado:

**Duplicados/Redundantes:**
- `AUDITORIA_COMPLETA_PROYECTO_MARIA.md` → Consolidado en 01_PROYECTO.md
- `CONTEXTO_COMPLETO_PROYECTO_MARIA.md` → Consolidado en 01_PROYECTO.md
- `DOCUMENTACION_TECNICA_COMPLETA_MARIA.md` → Consolidado en 01_PROYECTO.md
- `ESTADO_PROYECTO_RESUMEN.md` → Ahora es 02_ESTADO_ACTUAL.md
- `HISTORIAL_CAMBIOS_MARIA.md` → Ahora es 03_HISTORIAL.md

**Temporales/Sesión:**
- `RESUMEN_SESION_HOY.md` → Movido a 03_HISTORIAL.md
- `LOG_PRUEBAS_2025-09-30.md` → Movido a 04_COMO_USAR.md
- `LEEME_PRIMERO.md` → Reemplazado por 00_INDEX.md

**Específicos de features:**
- `COMO_PROBAR_CALCULADORA.md` → Consolidado en 04_COMO_USAR.md
- `COMO_PROBAR_EXTRACCION_PDF.md` → Consolidado en 04_COMO_USAR.md
- `PLAN_FEATURES_VENDIBLES.md` → Ahora es 05_ROADMAP.md

**Backups/Antiguos:**
- `BACKUP_TESTING_FRAMEWORK.md` → Obsoleto
- `CAMBIOS_IMPLEMENTADOS.md` → Obsoleto
- `CAMBIO_FINAL_GEMINI_PRIORITARIO.md` → Obsoleto
- `FASE1_COMPLETADA.md` → Obsoleto
- `PROMPT_COMPLETO_PROYECTO_MARIA.md` → Obsoleto
- `PROMPT_MEJORADO_EXTRACCION_PDF.md` → Obsoleto
- `RESUMEN_MEJORA_PROMPT.md` → Obsoleto
- `RESUMEN_MEJORA_PROMPT_PDF.md` → Obsoleto
- `REDIS_IMPLEMENTATION_SUMMARY.md` → Obsoleto
- `SISTEMA_PREMIUM_FUNCIONANDO.md` → Obsoleto
- `TESTING_STRATEGY_DEVOPS.md` → Obsoleto

**Planes viejos:**
- `ROADMAP_FASES.md` → Ahora es 05_ROADMAP.md
- `PLAN_MAÑANA.md` → Obsoleto
- `plan.md` → Obsoleto
- `claude_2.md` → Obsoleto

**README genérico:**
- `README.md` → Reemplazado por 00_INDEX.md

**Notas dev:**
- `DEV_NOTES.md` → Movido a 02_ESTADO_ACTUAL.md

---

## ✅ **REGLAS DE ORO**

1. **Máximo 6 archivos MD en raíz** (00 al 05)
2. **Nombres empiezan con número** (para orden)
3. **Un archivo = un propósito** (no mezclar)
4. **Actualizar después de cada sesión** (mínimo 02 y 03)
5. **Eliminar obsoletos inmediatamente** (no acumular)
6. **Fecha de última actualización** en cada archivo

---

## 🎯 **EJEMPLO DE USO**

### **AI nueva llega al proyecto:**

```markdown
1. Abre 00_INDEX.md (este archivo)
2. Lee estructura y orden de lectura
3. Abre 01_PROYECTO.md → Entiende QUÉ es MARÍA
4. Abre 02_ESTADO_ACTUAL.md → Entiende DÓNDE estamos
5. Listo para trabajar!

Si necesita más contexto:
6. Abre 03_HISTORIAL.md → Ve QUÉ se hizo
7. Abre 04_COMO_USAR.md → Aprende CÓMO probar
8. Abre 05_ROADMAP.md → Entiende HACIA DÓNDE vamos
```

### **Developer quiere probar una feature:**

```markdown
1. Abre 04_COMO_USAR.md
2. Busca la feature (ej: "Calculadora")
3. Sigue los comandos de prueba
4. Listo!
```

### **Stakeholder quiere entender estado:**

```markdown
1. Abre 02_ESTADO_ACTUAL.md
2. Ve % completado y features listas
3. Listo!
```

---

## 📅 **MANTENIMIENTO**

**Cada semana:**
- Revisar si hay archivos MD nuevos en raíz → Consolidar o eliminar
- Verificar que los 6 archivos estén actualizados
- Limpiar archivos temporales (logs, backups viejos)

**Cada mes:**
- Archivar entradas viejas de 03_HISTORIAL.md si crece mucho (>1000 líneas)
- Revisar si 05_ROADMAP.md necesita actualización estratégica

---

## 🆘 **TROUBLESHOOTING**

**"¿Dónde está la info de X?"**
→ Busca en 00_INDEX.md qué archivo lo contiene

**"¿Cómo pruebo la feature Y?"**
→ 04_COMO_USAR.md

**"¿Qué se hizo la semana pasada?"**
→ 03_HISTORIAL.md (ordenado por fecha)

**"¿Cuál es el próximo paso?"**
→ 05_ROADMAP.md

---

**Última actualización**: 2025-09-30
**Versión**: 1.0
**Mantenido por**: Claude AI + Emi
