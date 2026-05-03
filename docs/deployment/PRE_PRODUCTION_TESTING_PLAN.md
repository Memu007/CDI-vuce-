# Plan de Testing Pre-Producción
## CDI Sistema MARÍA - Despliegue para 2000 Usuarios

**Fecha:** 2025-10-21
**Versión:** 1.0
**Branch:** claude/review-project-011CUK6vjo4ui6MfAg5Q3ztA

---

## 📋 Resumen Ejecutivo

Este plan define las pruebas pre-producción para un despliegue de **escala pequeña** (máximo 2000 usuarios concurrentes). El enfoque es **pragmático y eficiente**, evitando sobre-ingeniería mientras garantiza robustez para producción.

**Estado de Seguridad:** ✅ COMPLETADO (100% defensa contra ataques)

---

## 1️⃣ SMOKE TESTING (Pruebas de Humo)
### Objetivo: Verificar que las funcionalidades críticas funcionan end-to-end

**Duración Estimada:** 30-45 minutos
**Responsable:** Desarrollador/QA

### ✅ Checklist de Rutas Críticas

#### **A. Gestión de Clientes**
```bash
# Test 1: Crear cliente nuevo
curl -X POST http://localhost:8000/api/clientes/public \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test Cliente SA",
    "email": "test@cliente.com",
    "cuit": "20-12345678-9",
    "direccion": "Calle Falsa 123"
  }'

# Resultado Esperado:
# - Status 200
# - JSON con {"success": true, "id": <numero>}
# - Email formateado a lowercase
# - CUIT formateado con guiones
# - Nombre sanitizado (sin HTML)
```

#### **B. Upload de Excel**
```bash
# Test 2: Subir Excel válido
curl -X POST http://localhost:8000/upload_excel \
  -F "file=@test_facturas.xlsx" \
  -F "client_id=1"

# Resultado Esperado:
# - Status 200
# - JSON con {"success": true, "items": [...]}
# - Archivo procesado correctamente
# - Items extraídos del Excel
```

#### **C. Upload de PDF**
```bash
# Test 3: Subir PDF público
curl -X POST http://localhost:8000/upload_pdf/public \
  -F "file=@test_factura.pdf"

# Resultado Esperado:
# - Status 200
# - JSON con {"success": true, "items": [...]}
# - PDF validado (magic bytes)
# - Extracción de datos exitosa
```

#### **D. Descarga de Archivos**
```bash
# Test 4: Descargar archivo generado
curl -O http://localhost:8000/download/facturas_cliente_1.xlsx

# Resultado Esperado:
# - Status 200
# - Archivo descargado correctamente
# - Protección contra path traversal activa
```

#### **E. Health Check**
```bash
# Test 5: Verificar salud del sistema
curl http://localhost:8000/health

# Resultado Esperado:
# - Status 200
# - JSON con {"status": "healthy", ...}
# - Conexión a DB verificada
# - Conexión a Redis verificada
```

#### **F. Security Headers**
```bash
# Test 6: Verificar headers de seguridad
curl -I http://localhost:8000/

# Headers Esperados:
# - X-Frame-Options: DENY
# - X-Content-Type-Options: nosniff
# - Content-Security-Policy: default-src 'self'...
# - Strict-Transport-Security: max-age=31536000
```

### 📊 Criterio de Aceptación
- **6/6 tests deben pasar** para continuar con siguientes etapas
- Cualquier fallo requiere investigación y fix inmediato

---

## 2️⃣ LOAD TESTING (Pruebas de Carga)
### Objetivo: Verificar rendimiento bajo carga realista para 2000 usuarios

**Duración Estimada:** 1-2 horas
**Herramienta Recomendada:** Apache JMeter, Locust, o Artillery

### 📈 Escenarios de Carga

#### **Escenario 1: Carga Normal (Baseline)**
- **Usuarios concurrentes:** 50
- **Duración:** 10 minutos
- **Operaciones:**
  - 40% consultas (GET /api/clientes, GET /health)
  - 30% creación clientes (POST /api/clientes/public)
  - 20% uploads Excel (POST /upload_excel)
  - 10% uploads PDF (POST /upload_pdf/public)

**Métricas Esperadas:**
```
✅ Response Time (p95): < 500ms
✅ Response Time (p99): < 1000ms
✅ Error Rate: < 0.1%
✅ Throughput: > 100 req/seg
✅ CPU Usage: < 60%
✅ Memory Usage: < 2GB
```

#### **Escenario 2: Carga Pico (Peak Load)**
- **Usuarios concurrentes:** 200
- **Duración:** 5 minutos
- **Operaciones:** Misma distribución que Escenario 1

**Métricas Esperadas:**
```
✅ Response Time (p95): < 1000ms
✅ Response Time (p99): < 2000ms
✅ Error Rate: < 1%
✅ Throughput: > 150 req/seg
✅ CPU Usage: < 80%
✅ Memory Usage: < 4GB
```

#### **Escenario 3: Stress Test (Límite del Sistema)**
- **Usuarios concurrentes:** 500
- **Duración:** 3 minutos
- **Objetivo:** Encontrar el punto de quiebre

**Métricas Esperadas:**
```
⚠️ Response Time (p95): < 3000ms
⚠️ Error Rate: < 5%
⚠️ Sistema debe degradarse gradualmente (no crash)
⚠️ Rate limiting debe activarse correctamente
```

### 🔧 Configuración de Locust (Ejemplo)

```python
# locustfile.py
from locust import HttpUser, task, between

class CDIUser(HttpUser):
    wait_time = between(1, 5)  # Usuarios esperan 1-5s entre requests

    @task(4)
    def get_health(self):
        self.client.get("/health")

    @task(3)
    def create_client(self):
        self.client.post("/api/clientes/public", json={
            "nombre": "Test Cliente",
            "email": f"test{self.user_id}@test.com",
            "cuit": "20-12345678-9"
        })

    @task(2)
    def upload_excel(self):
        files = {'file': open('test_facturas.xlsx', 'rb')}
        self.client.post("/upload_excel", files=files, data={"client_id": "1"})

    @task(1)
    def upload_pdf(self):
        files = {'file': open('test_factura.pdf', 'rb')}
        self.client.post("/upload_pdf/public", files=files)

# Ejecutar con:
# locust -f locustfile.py --users 50 --spawn-rate 10 --run-time 10m
```

### 📊 Criterio de Aceptación
- Escenario 1 (Carga Normal) debe cumplir todas las métricas
- Escenario 2 (Pico) debe cumplir al menos 80% de métricas
- Escenario 3 (Stress) debe degradarse gracefully sin crashes

---

## 3️⃣ DATABASE PERFORMANCE (Rendimiento de DB)
### Objetivo: Verificar que PostgreSQL maneja la carga esperada

**Duración Estimada:** 30 minutos

### 🗄️ Tests de Base de Datos

#### **Test 1: Query Performance**
```sql
-- Verificar índices en tablas críticas
EXPLAIN ANALYZE
SELECT * FROM clientes WHERE email = 'test@test.com';

-- Resultado Esperado:
-- - Execution Time < 5ms
-- - Index Scan (no Seq Scan)
-- - Rows examined < 100
```

#### **Test 2: Concurrent Writes**
```python
# test_concurrent_db.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def concurrent_inserts(n=100):
    """Simular 100 inserts concurrentes"""
    tasks = []
    for i in range(n):
        task = insert_client(f"Cliente {i}", f"test{i}@test.com")
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    errors = [r for r in results if isinstance(r, Exception)]

    print(f"✅ Inserts exitosos: {n - len(errors)}/{n}")
    print(f"❌ Errores: {len(errors)}")

    # Criterio: < 1% error rate
    assert len(errors) < n * 0.01

# Ejecutar:
# python test_concurrent_db.py
```

#### **Test 3: Connection Pool**
```bash
# Verificar configuración de pool en server_funcional.py
grep -A 5 "pool_size" proyecto_maria/server_funcional.py

# Configuración Recomendada para 2000 usuarios:
# pool_size=20
# max_overflow=10
# pool_timeout=30
# pool_recycle=3600
```

### 📊 Criterio de Aceptación
- Queries con índices < 10ms
- 100 inserts concurrentes con < 1% error rate
- Connection pool configurado adecuadamente

---

## 4️⃣ INTEGRATION TESTING (Servicios Externos)
### Objetivo: Verificar integración con Gemini LLM y servicios externos

**Duración Estimada:** 30 minutos

### 🔗 Tests de Integración

#### **Test 1: Gemini API Connection**
```python
# test_gemini_integration.py
import os
from google.generativeai import GenerativeModel

def test_gemini_connection():
    """Verificar conexión y quota de Gemini API"""
    api_key = os.getenv("GEMINI_API_KEY")
    assert api_key, "GEMINI_API_KEY no configurada"

    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Test connection")

    assert response.text, "Gemini API no respondió"
    print(f"✅ Gemini API conectada: {response.text[:50]}...")

# Resultado Esperado:
# - API key válida
# - Respuesta en < 3 segundos
# - Quota suficiente para 2000 usuarios (check console.cloud.google.com)
```

#### **Test 2: PDF Processing Pipeline**
```bash
# Test end-to-end: Upload PDF → Gemini → Response
curl -X POST http://localhost:8000/upload_pdf_gemini_only \
  -F "file=@test_factura_compleja.pdf" \
  -F "client_id=1"

# Resultado Esperado:
# - Status 200
# - Items extraídos correctamente con Gemini
# - Response time < 10 segundos
# - Fallback a PyPDF2 si Gemini falla
```

#### **Test 3: Redis Cache**
```python
# test_redis_cache.py
import redis

def test_redis_connection():
    """Verificar Redis para caché/sesiones"""
    r = redis.Redis(host='localhost', port=6379, db=0)

    # Test write/read
    r.set('test_key', 'test_value')
    value = r.get('test_key')

    assert value == b'test_value', "Redis read/write falló"
    print("✅ Redis conectado y funcionando")

    # Verificar memoria
    info = r.info('memory')
    used_mb = info['used_memory'] / 1024 / 1024
    print(f"📊 Redis usando {used_mb:.2f} MB")

# Resultado Esperado:
# - Redis accesible
# - Read/write funcionales
# - Memoria < 100MB
```

### 📊 Criterio de Aceptación
- Gemini API responde en < 5 segundos
- PDF processing completo < 15 segundos
- Redis read/write < 5ms

---

## 5️⃣ SECURITY VERIFICATION (Verificación Final)
### Objetivo: Confirmar que todas las defensas están activas

**Duración Estimada:** 15 minutos
**Estado Actual:** ✅ COMPLETADO (ver FINAL_ATTACK_RETEST_REPORT.md)

### 🔒 Quick Security Check

```bash
# Test 1: Path Traversal bloqueado
curl "http://localhost:8000/download/../../etc/passwd"
# Esperado: 404 Not Found

# Test 2: Malicious file upload bloqueado
curl -X POST http://localhost:8000/upload_excel \
  -F "file=@malicious.php.xlsx"
# Esperado: 400 Invalid file type

# Test 3: XSS sanitizado
curl -X POST http://localhost:8000/api/clientes/public \
  -H "Content-Type: application/json" \
  -d '{"nombre": "<script>alert(1)</script>", "email": "test@test.com"}'
# Esperado: 200 con nombre = "&lt;script&gt;alert(1)&lt;/script&gt;"

# Test 4: Rate limiting activo
for i in {1..150}; do
  curl -s http://localhost:8000/health > /dev/null &
done
wait
# Esperado: Algunos requests con 429 Too Many Requests

# Test 5: Security headers presentes
curl -I http://localhost:8000/ | grep -E "(X-Frame|CSP|HSTS)"
# Esperado: 3+ security headers
```

### 📊 Referencia Completa
Ver **FINAL_ATTACK_RETEST_REPORT.md** para:
- 10 tipos de ataques testeados (100% bloqueados)
- 20 ataques concurrentes (100% defendidos)
- Stress test a 98.7 ataques/segundo
- Rating de seguridad: EXCELENTE (10/10)

---

## 6️⃣ USER ACCEPTANCE TESTING (UAT)
### Objetivo: Validar con usuarios reales antes de producción

**Duración Estimada:** 3-5 días
**Participantes:** 5-10 usuarios beta

### 👥 Escenarios de Usuario Real

#### **Perfil 1: Agente de Aduana (3 usuarios)**
**Tareas:**
1. Crear 5 clientes nuevos con datos reales
2. Subir 10 facturas Excel de clientes diferentes
3. Subir 5 PDFs de documentación aduanera
4. Descargar reportes generados
5. Verificar cálculos de aranceles

**Feedback Requerido:**
- ¿La interfaz es intuitiva?
- ¿Los tiempos de respuesta son aceptables?
- ¿Encontraste algún error o comportamiento inesperado?
- ¿Qué mejorarías?

#### **Perfil 2: Administrador (2 usuarios)**
**Tareas:**
1. Gestionar múltiples clientes (crear, editar, eliminar)
2. Subir archivos batch (20+ facturas)
3. Revisar logs y reportes
4. Verificar integridad de datos

**Feedback Requerido:**
- ¿El sistema maneja bien múltiples operaciones simultáneas?
- ¿Los reportes son precisos?
- ¿Necesitas funcionalidades adicionales?

#### **Perfil 3: Cliente Final (2 usuarios)**
**Tareas:**
1. Consultar estado de trámites
2. Descargar documentación
3. Verificar cálculos de costos

**Feedback Requerido:**
- ¿Entiendes la información presentada?
- ¿Confías en los cálculos mostrados?
- ¿El sistema es fácil de usar?

### 📋 Checklist de UAT

```markdown
- [ ] 5+ usuarios completaron todas las tareas asignadas
- [ ] 0 errores críticos reportados (blockers)
- [ ] < 3 errores menores reportados
- [ ] Satisfacción general > 7/10
- [ ] Todos los cálculos validados como correctos
- [ ] Interfaz usable sin capacitación extensa
- [ ] Feedback documentado en JIRA/Trello/GitHub Issues
```

---

## 7️⃣ BACKUP & RECOVERY (Respaldo y Recuperación)
### Objetivo: Garantizar que los datos pueden recuperarse en caso de fallo

**Duración Estimada:** 1 hora

### 💾 Tests de Backup

#### **Test 1: Database Backup**
```bash
# Crear backup de PostgreSQL
pg_dump -U postgres -d cdi_db -F c -f backup_pre_prod_$(date +%Y%m%d).dump

# Verificar backup
pg_restore --list backup_pre_prod_*.dump | head -20

# Criterio: Backup completo < 5 minutos para DB con 10k registros
```

#### **Test 2: Database Restore**
```bash
# Crear DB de prueba
createdb -U postgres cdi_db_restore_test

# Restaurar backup
pg_restore -U postgres -d cdi_db_restore_test backup_pre_prod_*.dump

# Verificar integridad
psql -U postgres -d cdi_db_restore_test -c "SELECT COUNT(*) FROM clientes;"

# Limpiar
dropdb -U postgres cdi_db_restore_test

# Criterio: Restore completo < 10 minutos, 0 errores
```

#### **Test 3: File System Backup**
```bash
# Backup de archivos generados
tar -czf generated_files_backup_$(date +%Y%m%d).tar.gz generated/

# Verificar
tar -tzf generated_files_backup_*.tar.gz | wc -l

# Criterio: Todos los archivos incluidos, compresión > 50%
```

### 📊 Criterio de Aceptación
- Backup automatizado configurado (cron job)
- Restore testeado exitosamente
- RTO (Recovery Time Objective) < 1 hora
- RPO (Recovery Point Objective) < 24 horas

---

## 8️⃣ MONITORING & ALERTING (Monitoreo)
### Objetivo: Configurar observabilidad para producción

**Duración Estimada:** 2 horas

### 📊 Métricas a Monitorear

#### **Application Metrics**
```python
# Agregar a server_funcional.py
from prometheus_client import Counter, Histogram, Gauge

# Contadores
requests_total = Counter('http_requests_total', 'Total HTTP requests')
requests_failed = Counter('http_requests_failed', 'Failed HTTP requests')

# Histogramas (latencia)
request_duration = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Gauges (estado actual)
active_users = Gauge('active_users', 'Number of active users')
db_connections = Gauge('db_connections_active', 'Active DB connections')

# Endpoint de métricas
@app.get('/metrics')
async def metrics():
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type='text/plain')
```

#### **Infrastructure Metrics (para 2000 usuarios)**

**CPU Usage:**
```bash
# Alerta si CPU > 80% por 5 minutos
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
```

**Memory Usage:**
```bash
# Alerta si memoria > 85%
free | grep Mem | awk '{print ($3/$2) * 100.0}'
```

**Disk Space:**
```bash
# Alerta si disco > 80%
df -h / | awk 'NR==2 {print $5}' | sed 's/%//'
```

**Response Time:**
```bash
# Alerta si p95 > 1 segundo
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/health
```

### 🔔 Alertas Configuradas

**Críticas (Pager/SMS):**
- ❌ API down (health check failed)
- ❌ Error rate > 5%
- ❌ Database unreachable
- ❌ Disk space > 90%

**Warnings (Email):**
- ⚠️ CPU > 80% for 10 minutes
- ⚠️ Memory > 85%
- ⚠️ Response time p95 > 2 seconds
- ⚠️ Rate limiting triggered > 100 times/hour

**Info (Dashboard):**
- ℹ️ Requests per minute
- ℹ️ Active users count
- ℹ️ Successful uploads count
- ℹ️ Gemini API usage

### 🛠️ Herramientas Recomendadas (para proyecto pequeño)

**Opción 1: Simple y Gratis**
- **Logs:** PM2 + log rotation
- **Uptime:** UptimeRobot (50 monitors gratis)
- **Métricas:** Grafana Cloud (free tier 10k series)

**Opción 2: Self-hosted**
- **Stack:** Prometheus + Grafana
- **Logs:** Loki
- **Alerting:** Alertmanager

**Opción 3: Managed (Pago)**
- **Datadog** (para 2000 usuarios: ~$30/mes)
- **New Relic** (free tier hasta 100GB/mes)
- **Sentry** (error tracking: free tier 5k errors/mes)

---

## 9️⃣ DEPLOYMENT CHECKLIST (Pre-Deploy)
### Objetivo: Verificación final antes de desplegar a producción

### ✅ Checklist Completo

#### **A. Código y Configuración**
- [ ] Todas las variables de entorno configuradas en producción
- [ ] `.env` con valores de producción (no development)
- [ ] `DEBUG=False` en producción
- [ ] Secrets rotados (API keys, DB passwords)
- [ ] Dependencias actualizadas (`pip list --outdated`)
- [ ] Requirements.txt actualizado
- [ ] Git branch mergeado a main/production
- [ ] Tag de versión creado (ej: v1.0.0)

#### **B. Base de Datos**
- [ ] Migraciones aplicadas en producción
- [ ] Índices creados en tablas críticas
- [ ] Connection pool configurado (pool_size=20)
- [ ] Backup automatizado configurado
- [ ] Recovery testeado exitosamente

#### **C. Seguridad**
- [ ] Todos los tests de seguridad pasando (ver FINAL_ATTACK_RETEST_REPORT.md)
- [ ] Security headers activos
- [ ] Rate limiting configurado
- [ ] HTTPS/TLS configurado (certificado válido)
- [ ] CORS configurado correctamente
- [ ] Firewall reglas configuradas

#### **D. Performance**
- [ ] Load testing completado exitosamente
- [ ] Caché configurado (Redis)
- [ ] Static files servidos eficientemente
- [ ] Compression habilitado (gzip)
- [ ] CDN configurado (opcional para 2000 usuarios)

#### **E. Monitoreo**
- [ ] Health check endpoint funcionando
- [ ] Logging configurado (nivel INFO en prod)
- [ ] Métricas siendo recolectadas
- [ ] Alertas configuradas
- [ ] Dashboard de monitoreo accesible

#### **F. Infraestructura**
- [ ] Servidor dimensionado correctamente (4 CPU, 8GB RAM mínimo)
- [ ] Disco con espacio suficiente (100GB+)
- [ ] Backups automatizados
- [ ] Proceso de deployment documentado
- [ ] Rollback plan definido

#### **G. Documentación**
- [ ] README actualizado
- [ ] API documentation actualizada
- [ ] Runbook de operaciones creado
- [ ] Contactos de emergencia documentados
- [ ] Postmortem template preparado

#### **H. Legal y Compliance**
- [ ] Términos de servicio publicados
- [ ] Política de privacidad actualizada
- [ ] GDPR/datos personales compliance (si aplica)
- [ ] SLA definido y comunicado

---

## 🔟 RECURSOS NECESARIOS

### 👨‍💻 Equipo
- **1 Developer:** Ejecutar tests técnicos (6-8 horas)
- **1 QA/Tester:** Coordinar UAT y smoke tests (4-6 horas)
- **5-10 Beta Users:** UAT (2-3 horas cada uno)
- **1 DevOps (opcional):** Configurar monitoring (2-4 horas)

### 🖥️ Infraestructura
- **Staging Environment:** Réplica de producción para tests
  - 2-4 vCPUs
  - 4-8 GB RAM
  - 50 GB Disco
  - PostgreSQL 14+
  - Redis 6+

### 🛠️ Herramientas
- **Load Testing:** Locust (gratis, Python)
- **Monitoring:** Grafana + Prometheus (gratis, self-hosted)
- **Uptime:** UptimeRobot (gratis, 50 monitors)
- **Error Tracking:** Sentry (free tier 5k errors/mes)

### 💰 Costo Estimado
- **Infraestructura staging:** $20-50/mes (DigitalOcean/AWS)
- **Monitoring (managed):** $0-30/mes (free tiers)
- **Total:** < $100/mes para entorno de testing

---

## 📅 CRONOGRAMA SUGERIDO

```
Día 1 (4 horas):
├─ Smoke Testing (1h)
├─ Database Performance Tests (1h)
├─ Integration Testing (1h)
└─ Security Verification (1h)

Día 2 (3 horas):
├─ Load Testing - Escenario 1 (1h)
├─ Load Testing - Escenario 2 (1h)
└─ Load Testing - Escenario 3 (1h)

Día 3-7 (UAT):
├─ Reclutar beta users (1 día)
├─ UAT Sessions (3 días)
├─ Feedback consolidation (1 día)
└─ Fix critical issues (1-2 días)

Día 8 (2 horas):
├─ Backup & Recovery Tests (1h)
└─ Monitoring Setup (1h)

Día 9 (2 horas):
├─ Deployment Checklist Review (1h)
└─ Go/No-Go Meeting (1h)

Día 10:
└─ 🚀 DEPLOY TO PRODUCTION
```

**Total Time to Production:** 10 días laborables

---

## 🎯 CRITERIOS DE GO/NO-GO

### ✅ GO TO PRODUCTION SI:
1. **Smoke Tests:** 6/6 tests pasando
2. **Load Tests:** Escenario 1 y 2 cumplen métricas
3. **Security:** Todos los tests de seguridad pasando
4. **UAT:** > 80% satisfacción, 0 blockers
5. **Backup:** Restore testeado exitosamente
6. **Monitoring:** Alertas configuradas y funcionando
7. **Checklist:** > 90% items completados

### ❌ NO-GO (DEFER DEPLOY) SI:
1. **Errores críticos** sin resolver
2. **Load test Escenario 1** falla > 20% métricas
3. **Security test** falla cualquier check
4. **UAT** revela blockers
5. **Backup/Restore** no funciona
6. **Monitoring** no configurado

---

## 📊 MÉTRICAS DE ÉXITO POST-DEPLOY

### Primera Semana
- ✅ Uptime > 99.5%
- ✅ Error rate < 0.1%
- ✅ Response time p95 < 1 segundo
- ✅ 0 security incidents
- ✅ 0 data loss events

### Primer Mes
- ✅ Uptime > 99.8%
- ✅ User satisfaction > 7/10
- ✅ < 5 bugs reportados
- ✅ Backup/restore testeado semanalmente
- ✅ Monitoreo funcionando 24/7

---

## 📝 NOTAS ADICIONALES

### Para Proyecto de 2000 Usuarios

**Buenas Noticias:**
- ✅ No necesitas Kubernetes (overkill para esta escala)
- ✅ Un servidor decente (4 CPU, 8GB RAM) es suficiente
- ✅ No necesitas microservicios complejos
- ✅ Free tiers de servicios cloud son suficientes
- ✅ Database única (no sharding necesario)

**Recomendaciones:**
- 🔧 Usar PM2 para process management (simple y efectivo)
- 🔧 PostgreSQL con réplica read (opcional, pero útil)
- 🔧 Redis para cache/sessions (baja memoria)
- 🔧 Nginx como reverse proxy
- 🔧 Certbot para HTTPS gratis (Let's Encrypt)

**Evitar Over-Engineering:**
- ❌ No necesitas CDN global (usuarios probablemente locales)
- ❌ No necesitas auto-scaling (carga predecible)
- ❌ No necesitas service mesh
- ❌ No necesitas distributed tracing (monolito está bien)

### Arquitectura Recomendada para 2000 Usuarios

```
                    ┌─────────────┐
                    │   Cloudflare │ (DNS + DDoS protection - Free)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Nginx    │ (Reverse proxy + SSL)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
         │ PM2:    │  │ PM2:   │  │ PM2:   │
         │ Worker1 │  │ Worker2│  │ Worker3│ (3-4 workers)
         └────┬────┘  └───┬────┘  └───┬────┘
              │           │            │
              └───────────┼────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼─────┐   ┌─────▼────┐   ┌──────▼─────┐
    │PostgreSQL│   │  Redis   │   │  File      │
    │  (Main)  │   │ (Cache)  │   │  Storage   │
    └──────────┘   └──────────┘   └────────────┘
```

**Costo Mensual Estimado:**
- VPS (4 CPU, 8GB): $40/mes
- Database managed: $15/mes (opcional, puede ser self-hosted)
- Redis managed: $0-10/mes (free tier o self-hosted)
- Monitoring: $0-30/mes (free tiers)
- **Total:** $55-95/mes

---

## 🚀 CONCLUSIÓN

Este plan de testing pre-producción está diseñado específicamente para un **proyecto de escala pequeña (2000 usuarios)**, equilibrando:

1. **Pragmatismo:** Solo lo necesario, sin sobre-ingeniería
2. **Robustez:** Cobertura suficiente para producción confiable
3. **Eficiencia:** 10 días laborables total
4. **Costo-efectividad:** < $100/mes en herramientas

**Estado de Seguridad:** ✅ Ya completado al 100% (ver FINAL_ATTACK_RETEST_REPORT.md)

**Próximo Paso Inmediato:** Comenzar con Smoke Testing (Día 1)

---

**Generado por:** Claude Code
**Para:** CDI Sistema MARÍA
**Versión:** 1.0
**Fecha:** 2025-10-21
