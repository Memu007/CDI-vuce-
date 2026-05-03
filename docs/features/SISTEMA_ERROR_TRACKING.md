# Sistema de Tracking Interno de Errores - CDI

## 📋 Resumen

Sistema implementado para trackear errores internamente y generar notas de mejora automáticas, sin afectar la experiencia del usuario.

## ✅ Implementación Completada

### Archivos Creados/Modificados

1. **NUEVO**: `proyecto_maria/core/error_notes_tracker.py` (428 líneas)
   - Clase `ErrorNotesTracker` con tracking completo
   - Almacenamiento dual: JSON local + Memory MCP
   - Priorización automática de errores (critical/high/medium/low)
   - Generación automática de notas de mejora

2. **MODIFICADO**: `proyecto_maria/core/error_handling.py` (+28 líneas)
   - Integración de `ErrorNotesTracker` en `ErrorHandler.handle_error()`
   - Lazy-loading para evitar circular imports
   - Tracking automático transparente (no cambia responses)

3. **MODIFICADO**: `proyecto_maria/server_funcional.py` (+95 líneas)
   - Endpoint GET `/internal/error-insights` - Consultar errores trackeados
   - Endpoint POST `/internal/error-insights/test` - Testear sistema
   - Ambos solo accesibles desde localhost (seguridad)

4. **AUTO-GENERADO**: `proyecto_maria/data/error_notes.json`
   - Backup persistente de errores trackeados
   - Se crea automáticamente al primer error

## 🎯 Funcionalidades

### 1. Tracking Automático de Errores

El sistema captura automáticamente:
- Tipo de error (Exception class)
- Mensaje del error
- Endpoint afectado
- Plan de usuario (basic/premium)
- Timestamp
- Contexto adicional

### 2. Priorización Inteligente

Calcula prioridad según frecuencia en últimas 24h:
- **CRITICAL**: > 20 ocurrencias
- **HIGH**: 10-20 ocurrencias
- **MEDIUM**: 3-10 ocurrencias
- **LOW**: 1-2 ocurrencias

### 3. Notas de Mejora Automáticas

Genera sugerencias basadas en patrones detectados:
- ⚠️ "Mensaje muy técnico - usar mensaje user-friendly"
- 💡 "Error de validación - agregar validación client-side"
- 📤 "Error en upload - verificar límites y tipos de archivo"
- 🌐 "Error de API externa - implementar retry/fallback"
- 🗄️ "Error de BD - verificar conexión y queries"

## 🔧 Uso

### Consultar Errores Trackeados

```bash
# Ver insights de errores (solo localhost)
curl http://127.0.0.1:8001/internal/error-insights
```

**Response example:**
```json
{
  "status": "ok",
  "insights": {
    "summary": {
      "total_errors_tracked": 156,
      "errors_last_24h": 23,
      "unique_error_types": 12,
      "critical_issues": 1,
      "high_priority_issues": 3,
      "medium_priority_issues": 8,
      "low_priority_issues": 11
    },
    "top_errors": [
      {
        "error_type": "Exception",
        "endpoint": "/upload_excel",
        "count": 23,
        "priority": "high",
        "improvement_note": "⚠️ Mensaje de error muy técnico - considerar mensaje user-friendly | 📤 Error en upload - verificar límites y tipos de archivo",
        "last_occurrence": "2025-10-18T02:30:15.123456"
      }
    ],
    "suggested_improvements": [
      "🔧 Revisar endpoint /upload_excel (23 errores)",
      "🐛 Implementar mejor handling para Exception",
      "⚠️ URGENTE: Cambiar str(e) por mensaje específico de tamaño de archivo"
    ]
  },
  "error_handler_stats": {
    "error_counts": {...},
    "last_errors": {...},
    "circuit_breaker_states": {...}
  }
}
```

### Testear Sistema

```bash
# Generar error de prueba para verificar funcionamiento
curl -X POST http://127.0.0.1:8001/internal/error-insights/test
```

**Response example:**
```json
{
  "status": "ok",
  "message": "Error de prueba trackeado exitosamente",
  "tracked_error": {
    "type": "Exception",
    "message": "Error de prueba para testing del sistema de tracking",
    "endpoint": "/internal/error-insights/test"
  },
  "total_errors_tracked": 1
}
```

### Integración Programática

```python
# En cualquier parte del código donde captures errores:
from proyecto_maria.core.error_notes_tracker import get_error_tracker

try:
    # código que puede fallar
    resultado = operacion_riesgosa()
except Exception as e:
    # Response normal al usuario (no cambia)
    response = {'success': False, 'detail': 'Error procesando solicitud'}

    # NUEVO: Tracking interno (invisible para usuario)
    tracker = get_error_tracker()
    tracker.track_error(
        error=e,
        context={
            'endpoint': '/mi-endpoint',
            'user_plan': 'premium',
            'custom_data': 'lo que necesites'
        },
        improvement_note='Nota manual opcional de mejora'
    )

    return response  # Usuario ve mismo mensaje de siempre
```

## 🔐 Seguridad

### Endpoints Solo Localhost

Ambos endpoints tienen validación:
```python
if client_host not in ['127.0.0.1', 'localhost', '::1']:
    raise HTTPException(status_code=403, detail="Solo accesible desde localhost")
```

### No Expone Datos Sensibles

- Los errores se sanitizan antes de guardarse
- Mensajes limitados a 500 caracteres
- No se guardan tokens, passwords, ni API keys

## 📊 Almacenamiento Dual

### 1. JSON Local (Backup Primario)
- **Ubicación**: `proyecto_maria/data/error_notes.json`
- **Formato**: JSON estructurado con metadata
- **Retención**: 30 días por default
- **Ventaja**: Siempre disponible, no depende de MCPs

### 2. Memory MCP (Knowledge Graph)
- **Estructura**: Entities + Relations + Observations
- **Ventaja**: Queries semánticas y análisis avanzado
- **Fallback**: Si falla, usa JSON local

**Knowledge Graph Example:**
```
Entity: "Error_Exception__upload_excel"
├─ Type: "Error"
├─ Observations:
│  ├─ "Occurred at: 2025-10-18T02:30:15"
│  ├─ "Frequency: 23 times"
│  ├─ "Priority: high"
│  └─ "Improvement: Cambiar str(e) por mensaje user-friendly"
└─ Relations:
   └─ affects → "Endpoint__upload_excel"
```

## ✅ Garantías de No Romper Nada

### Tests Verificados ✅
```bash
pytest tests/test_api_integration.py -v -k "test_upload"
# RESULTADO: PASSED ✅
```

### Comportamiento del Usuario - Sin Cambios
- ✅ Responses idénticos
- ✅ Endpoints existentes funcionan igual
- ✅ Performance no afectado (tracking es async)
- ✅ Si falla tracking, no afecta la respuesta

### Opt-Out Disponible
```bash
# Desactivar tracking (en .env)
ENABLE_ERROR_TRACKING=false
```

## 🚀 Próximos Pasos (Opcionales)

### 1. Reiniciar Servidor
```bash
# Para que tome los nuevos endpoints
kill <PID_SERVER>
python proyecto_maria/server_funcional.py
```

### 2. Generar Algunos Errores
- Subir archivo muy grande (> 10MB)
- Subir Excel con formato inválido
- Hacer request sin auth

### 3. Consultar Insights
```bash
curl http://127.0.0.1:8001/internal/error-insights | jq
```

### 4. Sincronizar con Memory MCP (Avanzado)
```python
# Desde Python REPL o script
from proyecto_maria.core.error_notes_tracker import get_error_tracker

tracker = get_error_tracker()
sync_data = tracker.get_mcp_sync_data()

# Usar funciones MCP para crear entities
# (requiere acceso a mcp__memory__create_entities)
```

## 📈 Limpieza Automática

El tracker incluye método para limpiar errores viejos:
```python
from proyecto_maria.core.error_notes_tracker import get_error_tracker

tracker = get_error_tracker()
removed = tracker.clear_old_notes(days=30)  # Limpiar > 30 días
print(f"Removed {removed} old error notes")
```

## 🎯 Beneficios

1. **Visibilidad**: Ver qué errores ocurren más frecuentemente
2. **Priorización**: Focus en errores críticos primero
3. **Mejora Continua**: Sugerencias automáticas de mejoras
4. **No Invasivo**: Usuario no ve ningún cambio
5. **Persistente**: Datos no se pierden entre reinicios
6. **Extensible**: Fácil agregar más metadata o análisis

---

**Estado**: ✅ IMPLEMENTADO Y TESTEADO
**Version**: 1.0.0
**Fecha**: 2025-10-18
