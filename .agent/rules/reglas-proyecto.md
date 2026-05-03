# Reglas del Proyecto CDI-MARÍA

> **IMPORTANTE**: Este archivo es leído automáticamente por Antigravity.

---

## 👤 Sobre el Usuario

- **No sabe programar** - Usar lenguaje natural, sin jerga técnica
- **Quiere resultados** - Soluciones concretas, no explicaciones largas
- **Valora simplicidad** - Menos es más

---

## 🚫 NO Hacer (Overengineering)

- ❌ No abstracciones innecesarias
- ❌ No dependencias "por si acaso"
- ❌ No refactorizar código que funciona sin razón
- ❌ No arquitecturas enterprise para problemas simples
- ❌ No microservicios cuando un monolito alcanza
- ❌ No código duplicado ni funciones de 200+ líneas

---

## ✅ SÍ Hacer

- ✅ Nombres descriptivos (español o inglés claro)
- ✅ Funciones pequeñas con propósito claro
- ✅ Comentarios solo cuando agregan valor
- ✅ Soluciones elegantes a problemas complejos
- ✅ UX intuitiva y moderna
- ✅ Explicar en lenguaje natural qué se hizo

---

## 🛠️ Stack Técnico

- **Backend**: FastAPI + Python
- **Frontend**: HTML/CSS/JS plano (sin frameworks)
- **Base de datos**: SQLite dev, PostgreSQL prod
- **LLM**: Gemini (Google AI)

### Servidor Local
```bash
cd /Users/Emi/CDI
set -a && source .env && set +a
PYTHONPATH=. DATABASE_URL="sqlite+aiosqlite:///./test.db" \
uvicorn proyecto_maria.main:app --reload --port 8010
```

---

## 📁 Archivos Clave

| Archivo | Qué es |
|---------|--------|
| `proyecto_maria/main.py` | Entry point backend |
| `proyecto_maria/routers/` | Endpoints organizados |
| `proyecto_maria/static/app.js` | Lógica frontend principal |
| `proyecto_maria/static/app.css` | Estilos dashboard |
| `tests/test_regression_phase0.py` | Tests de regresión |

---

## 🔄 Flujo de Trabajo

1. **LEER** contexto (ARCHITECTURE.md, README.md)
2. **ENTENDER** qué se pide
3. **PLANIFICAR** cambios mínimos necesarios
4. **IMPLEMENTAR** de forma limpia
5. **VERIFICAR** que funciona (tests si aplica)
6. **EXPLICAR** en lenguaje natural qué se hizo

---

## 📊 Contrato API (FastAPI)

### Respuestas JSON estándar:
```json
{
  "success": true/false,
  "detail": "mensaje opcional"
}
```

### Reglas:
- Rutas con y sin barra final (/endpoint y /endpoint/)
- Archivos con multipart/form-data
- Errores de validación: 200 con success=false
- Recursos no encontrados: HTTPException 404

---

## 💬 Comunicación con Usuario

### ✅ Decir:
> "El sistema lee la tabla del Excel. Si no encuentra bien los datos, usa inteligencia artificial"

### ❌ NO Decir:
> "El parser extrae mediante heurísticas con fallback al LLM..."

### Reglas:
- Lenguaje simple y directo
- Ejemplos visuales concretos
- Evitar: endpoint, payload, parser, heurística, flag, cache, API key
- Priorizar "cómo se usa" sobre "cómo funciona"
- Analogías del mundo real

---

## 🎯 Presentar Opciones

```
🎯 Objetivo: [Lo que quiere lograr]

🏃 Opción 1: [Nombre simple]
  ✅ Ventaja | ❌ Desventaja

🤖 Opción 2: [Nombre simple]
  ✅ Ventaja | ❌ Desventaja

�� Recomendación: [Cuál elegir y por qué]
```

---

## 🔧 Resolución de Problemas

1. **Diagnóstico silencioso** - Revisar logs/código sin decirle
2. **Explicación simple** - Una línea sin jerga
3. **Solución proactiva** - Arreglar sin pedir permiso
4. **Confirmación** - "Listo, lo arreglé. Probá [acción]"

---

## 📝 Documentación

Al hacer cambios importantes actualizar `DEPLOY_CHANGES_SUMMARY.md`:
- Fecha
- Qué cambió (bullets cortos)
- Archivos modificados

---

## ⚠️ Cuándo Parar y Avisar

Si algo no es coherente o es muy difícil:
1. **Parar** antes de implementar
2. **Explicar** por qué es problemático
3. **Proponer alternativas** más simples
4. **Preguntar** si seguir adelante

---

## 🧪 Testing

```bash
pytest tests/test_regression_phase0.py -v --no-cov
```

Tests solo cuando aportan valor (lógica crítica y regresiones).

---

## 🚨🚨🚨 ALERTA DE CONTEXTO - REGLA CRÍTICA 🚨🚨🚨

### CUANDO EL CONTEXTO SE ESTÉ ACABANDO (aprox 70-80% usado):

**DEBO HACER INMEDIATAMENTE:**

1. **AVISAR EN MAYÚSCULAS Y LLAMATIVO:**
```
⚠️⚠️⚠️ ATENCIÓN: EL CONTEXTO SE ESTÁ AGOTANDO ⚠️⚠️⚠️

🔴 ACCIÓN REQUERIDA: Necesito que abras una nueva ventana
```

2. **CREAR BACKUP DE CONTEXTO:**
   - Crear archivo `handoff_context.md` en artifacts con:
     - Estado actual del trabajo
     - Últimos cambios realizados
     - Próximos pasos pendientes
     - Archivos clave modificados

3. **REPETIR LA ALERTA** si el usuario no responde:
```
🚨🚨🚨 ÚLTIMA ADVERTENCIA 🚨🚨🚨
EL CONTEXTO SE AGOTA. ABRÍ NUEVA VENTANA AHORA.
COPIÁ ESTE CONTEXTO: [pegar resumen]
```

4. **DAR EL CONTEXTO LISTO PARA COPIAR** al usuario

### Señales de contexto agotándose:
- Respuestas más lentas
- Errores de memoria
- Pérdida de información previa
- Repitiendo cosas ya dichas

**NUNCA DEJAR QUE EL CONTEXTO SE AGOTE SIN AVISAR.**
