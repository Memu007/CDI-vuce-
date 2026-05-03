# Load Test Final - 50 Usuarios Concurrentes
**Fecha:** 2025-10-24
**Duración:** 3 minutos
**Rate Limiting:** 3000 req/min (ajustado)

## Resultado: ⚠️ SERVIDOR SE CAYÓ

### Métricas Antes del Crash:
- **Requests totales:** 1989
- **Throughput:** ~11 req/seg
- **Response Time p50:** 2ms ✅
- **Response Time p95:** 2ms ✅
- **Response Time p99:** 8ms ✅

### Problema Encontrado:
El servidor (1 worker Uvicorn) se cayó bajo carga de 50 usuarios concurrentes.

## Recomendaciones URGENTES:

### 1. Uvicorn con Múltiples Workers
```bash
uvicorn proyecto_maria.server_funcional:app --workers 4 --host 0.0.0.0 --port 8000
```

### 2. O usar Gunicorn + Uvicorn
```bash
gunicorn proyecto_maria.server_funcional:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. Hardware Mínimo:
- **4 vCPUs**
- **8GB RAM**
- **PostgreSQL connection pool: 20**

## Conclusión:

✅ **Performance excelente** cuando funciona (2ms p95)
✅ **Rate limiting ajustado correctamente**
❌ **Necesita workers para 50+ usuarios**

**Next Step:** Configurar 4 workers y re-testear.
