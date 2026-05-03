# 📊 Sistema de Logging y Monitoreo - CDI Sistema MARÍA

## ✅ LO QUE YA TENÉS (Implementado)

Tu app YA tiene un sistema de logging y error tracking **muy completo**:

### 1. **Logging Estructurado** (logging_config.py) ✅

**Características:**
- ✅ **JSON logging** - Logs parseables por herramientas
- ✅ **Rotation automática** - No llena el disco (10MB max, 5 backups)
- ✅ **Archivo separado para errores** - `maria-errors.log`
- ✅ **Múltiples niveles** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **Context metadata** - service, version, environment

**Funciones especializadas:**
```python
log_api_request()      # Logs de cada request API
log_llm_request()      # Logs de llamadas a Gemini
log_database_operation() # Logs de queries DB
log_cache_operation()  # Logs de Redis/cache
```

**Ubicación de logs:**
```
logs/
├── maria.log        # Todos los logs (rotado)
└── maria-errors.log # Solo errores (rotado)
```

---

### 2. **Error Tracking Inteligente** (error_notes_tracker.py) ✅

**Sistema automático de mejora continua:**

**Características:**
- ✅ **Tracking automático** de todos los errores
- ✅ **Frecuencia y priorización** (critical, high, medium, low)
- ✅ **Notas de mejora automáticas** basadas en patrones
- ✅ **Insights dashboard** - Errores más comunes, sugerencias
- ✅ **Backup persistente** - `proyecto_maria/data/error_notes.json`
- ✅ **Memory MCP integration** - Knowledge graph de errores

**Ejemplo de uso:**
```python
from proyecto_maria.core.error_notes_tracker import get_error_tracker

tracker = get_error_tracker()
tracker.track_error(
    error=exception,
    context={
        'endpoint': '/upload_pdf',
        'user_plan': 'premium',
        'file_size': 1024000
    }
)

# Obtener insights
insights = tracker.get_error_insights()
# {
#   'summary': {
#     'total_errors_tracked': 150,
#     'errors_last_24h': 12,
#     'critical_issues': 2,
#     'high_priority_issues': 5
#   },
#   'top_errors': [...],
#   'suggested_improvements': [...]
# }
```

**Priorización automática:**
- **CRITICAL**: > 20 errores en 24h
- **HIGH**: 10-20 errores en 24h
- **MEDIUM**: 3-10 errores en 24h
- **LOW**: 1-2 errores en 24h

**Notas de mejora automáticas:**
```
⚠️ Mensaje de error muy técnico - considerar mensaje user-friendly
💡 Error de validación - agregar validación client-side preventiva
📤 Error en upload - verificar límites y tipos de archivo
🌐 Error de API externa - implementar retry/fallback
```

---

### 3. **Middleware de Logging** (logging_middleware.py) ✅

**Registra automáticamente:**
- ✅ Todas las requests HTTP
- ✅ Response times
- ✅ Status codes
- ✅ IPs de clientes
- ✅ Errores y excepciones

---

### 4. **Monitoring Service** (monitoring_service.py) ✅

**Métricas en tiempo real:**
- ✅ CPU usage
- ✅ Memory usage
- ✅ Disk space
- ✅ Active connections
- ✅ Request rates

---

## 🚀 MEJORAS SUGERIDAS (Para Agregar)

### 1. **Sentry Integration** (Professional Error Tracking)

**Por qué:** Sentry es el estándar de industria para error tracking en producción

**Beneficios:**
- 🔍 Stack traces completos en UI
- 📊 Error grouping inteligente
- 📧 Alertas por email/Slack
- 👥 Affected users count
- 🔄 Release tracking
- **GRATIS:** 5,000 events/mes

**Implementación:**
```python
# Agregar a requirements.txt
sentry-sdk[fastapi]

# En server_funcional.py (inicio)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="tu-sentry-dsn",
    traces_sample_rate=0.1,  # 10% de traces
    environment="production",
    integrations=[FastApiIntegration()]
)
```

---

### 2. **Google Cloud Monitoring** (Para Cloud Run)

**Integración nativa con Cloud Run:**
```python
from google.cloud import monitoring_v3
from google.cloud import error_reporting

# Cloud Error Reporting
error_client = error_reporting.Client()

try:
    # código
except Exception as e:
    error_client.report_exception()
    raise
```

**Métricas custom:**
```python
from google.cloud.monitoring_v3 import MetricServiceClient
from google.cloud.monitoring_v3.types import Point, TimeSeries

def report_custom_metric(metric_name, value):
    client = MetricServiceClient()
    series = TimeSeries()
    # ... configurar metric
    client.create_time_series(name=project_name, time_series=[series])
```

---

### 3. **Prometheus Metrics** (Estándar industria)

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Contadores
requests_total = Counter('http_requests_total', 'Total requests')
requests_failed = Counter('http_requests_failed', 'Failed requests')

# Histogramas (latencia)
request_duration = Histogram('http_request_duration_seconds', 'Latency')

# Gauges (estado actual)
active_users = Gauge('active_users', 'Active users')

# Endpoint de métricas
@app.get('/metrics')
async def metrics():
    return Response(generate_latest(), media_type='text/plain')
```

---

### 4. **Analytics de Uso** (User Behavior)

**Trackear:**
- 📊 Endpoints más usados
- ⏱️ Tiempos de respuesta por endpoint
- 👥 Usuarios activos (DAU, MAU)
- 📈 Uploads por día
- 🔥 Features más usadas

---

### 5. **Health Check Extendido**

Expandir `/health` con más info:

```python
@app.get('/health')
async def extended_health():
    return {
        'status': 'ok',
        'version': '1.0.0',
        'uptime_seconds': get_uptime(),
        'database': check_db(),
        'redis': check_redis(),
        'gemini_api': check_gemini(),
        'memory_mb': get_memory_usage(),
        'cpu_percent': get_cpu_usage(),
        'error_rate_last_hour': get_error_rate(),
        'requests_per_minute': get_rpm()
    }
```

---

## 📈 DASHBOARD DE MONITOREO

### Opción 1: Sentry Dashboard (Recomendado)
- UI profesional
- Gratis hasta 5k events/mes
- Alertas automáticas
- **URL:** https://sentry.io

### Opción 2: Google Cloud Console
- Ya incluido con Cloud Run
- Logs, métricas, traces
- **URL:** https://console.cloud.google.com/monitoring

### Opción 3: Grafana + Prometheus (Self-hosted)
- Control total
- Requiere setup adicional

---

## 🔔 SISTEMA DE ALERTAS

### Alertas Críticas (Email/SMS):
```python
if error_tracker.get_error_insights()['summary']['critical_issues'] > 0:
    send_alert_to_admin(
        title="⚠️ CRITICAL ERRORS DETECTED",
        body=f"Se detectaron {count} errores críticos en las últimas 24h"
    )
```

### Configurar en Sentry:
- Error rate > 5% → Email inmediato
- New error type → Slack notification
- Performance degradation → Alerta

---

## 📊 MÉTRICAS ACTUALES DISPONIBLES

**Ver insights de errores:**
```bash
# Endpoint ya implementado (agregar en server_funcional.py)
GET /api/admin/error-insights

# Response:
{
  "summary": {
    "total_errors_tracked": 150,
    "errors_last_24h": 12,
    "critical_issues": 2
  },
  "top_errors": [
    {
      "error_type": "FileValidationError",
      "endpoint": "/upload_pdf",
      "count": 25,
      "priority": "high",
      "improvement_note": "📤 Error en upload - verificar límites"
    }
  ],
  "suggested_improvements": [...]
}
```

---

## 🛠️ CÓMO USAR EL SISTEMA ACTUAL

### 1. Ver logs en tiempo real (local):
```bash
tail -f logs/maria.log | jq .
```

### 2. Ver solo errores:
```bash
tail -f logs/maria-errors.log | jq .
```

### 3. Ver logs en Cloud Run:
```bash
gcloud run services logs tail cdi-backend --project cdi-sistema-maria
```

### 4. Obtener insights de errores:
```python
from proyecto_maria.core.error_notes_tracker import get_error_tracker

tracker = get_error_tracker()
insights = tracker.get_error_insights()

print(f"Errores últimas 24h: {insights['summary']['errors_last_24h']}")
print(f"Issues críticos: {insights['summary']['critical_issues']}")

for err in insights['top_errors'][:5]:
    print(f"- {err['error_type']} ({err['count']}x): {err['improvement_note']}")
```

### 5. Limpiar logs viejos:
```python
tracker.clear_old_notes(days=30)  # Mantener últimos 30 días
```

---

## 💡 PRÓXIMOS PASOS RECOMENDADOS

**Para producción en Google Cloud:**

1. ✅ **Agregar Sentry** (10 min de setup, gratis)
   - Mejor UI para ver errores
   - Alertas automáticas
   - Stack traces completos

2. ✅ **Activar Google Cloud Logging** (automático en Cloud Run)
   - Logs centralizados
   - Queries avanzadas
   - Retención 30 días gratis

3. ✅ **Agregar endpoint `/metrics`** para Prometheus
   - Métricas estándar
   - Compatible con Grafana

4. ✅ **Configurar alertas**
   - Error rate > 5%
   - Response time p95 > 2s
   - Disk space > 80%

---

## 🎯 RESUMEN

**TU APP YA TIENE:**
- ✅ Logging estructurado (JSON)
- ✅ Error tracking con priorización
- ✅ Insights automáticos
- ✅ Notas de mejora
- ✅ Backup persistente
- ✅ Monitoring básico

**YA AGREGADO EN PRODUCCIÓN:**
- ✅ **Sentry** (error tracking profesional) - COMPLETADO
- ✅ **Admin endpoints** con métricas y health checks - COMPLETADO
- ✅ **Prometheus metrics** endpoint - COMPLETADO

**PENDIENTE:**
- 🚀 Google Cloud Monitoring (métricas nativas)
- 🚀 Alertas automáticas (configurar en Sentry)

**COSTO:**
- Actual: $0 (todo local/gratuito)
- Sentry: $0 (hasta 5k events/mes) ✅
- Google Cloud Logging: $0 (primeros 50GB/mes gratis)
- **Total: $0/mes** 🎉

---

## ✅ SENTRY INTEGRATION COMPLETADA

### ¿Qué se agregó?

1. **sentry_integration.py** - Módulo completo de integración con:
   - `init_sentry()` - Inicialización con FastAPI, Logging, SQLAlchemy
   - `capture_exception()` - Captura manual de excepciones con contexto
   - `capture_message()` - Envío de mensajes personalizados
   - `set_user_context()` - Asociar usuarios a errores
   - `add_breadcrumb()` - Trazabilidad de eventos
   - `before_send_filter()` - Sanitización de datos sensibles

2. **Integración en server_funcional.py**:
   - Sentry se inicializa automáticamente al arrancar el servidor
   - Captura automática de todas las excepciones FastAPI
   - Performance monitoring (10% sample rate)
   - Environment tagging (production/staging/development)

3. **Admin endpoints** (admin_router.py):
   - `/api/admin/health/detailed` - Health check con métricas sistema
   - `/api/admin/errors/insights` - Insights de errores trackeados
   - `/api/admin/errors/top/{limit}` - Top N errores más frecuentes
   - `/api/admin/metrics/prometheus` - Métricas formato Prometheus
   - `/api/admin/logs/recent/{limit}` - Logs recientes
   - `/api/admin/stats/summary` - Dashboard ejecutivo
   - `/api/admin/test/sentry` - Test de Sentry (solo desarrollo)

4. **Configuración en .env.example**:
   - `SENTRY_DSN` configurado con tu DSN
   - `ENVIRONMENT` para diferenciar production/development

### ¿Cómo usar Sentry?

**Ver errores en Sentry Dashboard:**
```
https://sentry.io/organizations/{tu-org}/issues/
```

**Testear integración (solo desarrollo):**
```bash
curl http://localhost:8000/api/admin/test/sentry
```

**Capturar errores manualmente:**
```python
from proyecto_maria.sentry_integration import capture_exception, add_breadcrumb

try:
    # Tu código
    result = do_something()
except Exception as e:
    capture_exception(e, context={
        "tags": {"feature": "upload", "user_plan": "premium"},
        "extra": {"file_size": 1024, "file_type": "pdf"}
    })
    raise
```

**Agregar contexto de usuario:**
```python
from proyecto_maria.sentry_integration import set_user_context

set_user_context(
    user_id="123",
    email="user@example.com",
    plan="premium"
)
```

**Agregar breadcrumbs para trazabilidad:**
```python
from proyecto_maria.sentry_integration import add_breadcrumb

add_breadcrumb(
    "Processing file upload",
    category="upload",
    level="info",
    data={"filename": "invoice.pdf", "size_mb": 2.5}
)
```

### Configuración de Alertas en Sentry

1. Ir a **Sentry → Alerts → Create Alert**
2. Configurar reglas recomendadas:
   - **Error rate > 5%** → Email inmediato
   - **New error type** → Slack notification
   - **Critical errors** → SMS/PagerDuty
   - **Performance degradation** (p95 > 2s) → Email

### Métricas Disponibles

**Endpoint Prometheus:**
```bash
curl http://localhost:8000/api/admin/metrics/prometheus
```

**Métricas incluidas:**
- `cdi_uptime_seconds` - Uptime del servidor
- `cdi_cpu_percent` - Uso de CPU
- `cdi_memory_used_percent` - Uso de memoria
- `cdi_disk_used_percent` - Uso de disco
- `cdi_errors_total` - Total de errores trackeados
- `cdi_errors_last_24h` - Errores últimas 24h
- `cdi_errors_critical` - Errores críticos

**Health check detallado:**
```bash
curl http://localhost:8000/api/admin/health/detailed
```

---
