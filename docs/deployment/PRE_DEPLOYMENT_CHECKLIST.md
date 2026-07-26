# 📋 Pre-Deployment Checklist - CDI Sistema MARÍA
**Objetivo:** Deployment a Google Cloud Run mañana - TODO listo y probado

---

## ✅ COMPLETADO - Listo para deployment

### 🔧 Fixes Críticos Aplicados
- [x] **requirements.txt limpio** (639→30 packages, sin paths locales)
- [x] **Sentry DSN sin hardcodear** (solo env var)
- [x] **.env creado** con SENTRY_DSN real
- [x] **.env en .gitignore** (verificado)

### 📦 Archivos de Deployment
- [x] **Dockerfile** - Multi-stage, Python 3.12-slim, 1 worker, PORT 8080
- [x] **.dockerignore** - Excluye tests, cache, logs
- [x] **cloudbuild.yaml** - Build + Deploy a Cloud Run
- [x] **scripts/deployment/deploy-cloud-run.sh** - Script automatizado (ejecutable)
- [x] **scripts/deployment/preflight_env.sh** - Valida variables antes de deployar
- [x] **.env.example** - Template sin secrets reales
- [x] **DEPLOYMENT_QUICK_START.md** - Guía paso a paso

### 🧪 Testing
- [x] **Smoke tests** - 11/11 pasados ✅
- [x] **Server startup** - OK con Sentry inicializado ✅
- [x] **Health endpoints** - /health y /api/admin/health/detailed OK ✅
- [x] **Sentry test** - Error capturado correctamente ✅

### 🔒 Seguridad
- [x] **Security headers** - X-Frame-Options, X-Content-Type-Options, CSP
- [x] **Rate limiting** - 3000 req/min configurado
- [x] **Input validation** - File uploads, XSS, path traversal
- [x] **Error sanitization** - Sentry before_send_filter activo
- [x] **Secrets management** - No hardcoded, solo env vars

### ⚡ Performance
- [x] **Workers** - Gunicorn con **1** worker Uvicorn. Es a propósito: sin
      `REDIS_URL` el rate limiting cuenta en memoria del proceso, así que con
      N workers el límite real sería N veces el configurado. Para escalar a
      varios workers hay que agregar Redis primero.
- [x] **GZip compression** - Activo (500 bytes min)
- [x] **Rate limits** - Dimensionado para 2000 usuarios
- [x] **Docker optimizado** - Multi-stage build, slim image

### 📊 Monitoring
- [x] **Sentry** - Error tracking configurado
- [x] **Admin endpoints** - Health, errors, metrics, logs
- [x] **Prometheus metrics** - /api/admin/metrics/prometheus

---

## 🚀 MAÑANA: Deployment en 3 pasos

### Paso 1: Setup GCP (5 min)
```bash
gcloud auth login
gcloud config set project cdi-sistema-maria
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### Paso 2: Deploy (10 min)
```bash
# Las variables se leen del .env local (o del shell) y se validan antes de
# buildear. Si falta alguna crítica el script corta y te dice cuál.
./scripts/deployment/deploy-cloud-run.sh
```

Para chequear las variables sin deployar nada:

```bash
./scripts/deployment/preflight_env.sh
```

### Paso 3: Verificar (2 min)
```bash
# Health check
curl https://cdi-backend-XXXXXXXXXX.run.app/health

# Sentry
curl https://cdi-backend-XXXXXXXXXX.run.app/api/admin/test/sentry

# Logs
gcloud run logs tail cdi-backend --region us-central1
```

---

## 📝 Variables a Configurar en Cloud Run

### Sin estas la app NO arranca (aborta y el servicio queda reiniciándose)

| Variable | Por qué |
|---|---|
| `ENVIRONMENT=production` | Sin esto se crean usuarios demo (`demo`/`demo123`), `/docs` queda público y las cookies de sesión viajan sin flag `Secure`. |
| `JWT_SECRET_KEY` | ≥32 caracteres, sin palabras obvias (`secret`, `changeme`, `default`, `12345`). Generala con `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. |
| `ALLOWED_ORIGINS` | La URL real del frontend, ej. `https://cdi.tu-dominio.com`. No puede ser `*` ni quedar vacía: la app usa cookies. |

### Sin esta se pierden los datos

| Variable | Por qué |
|---|---|
| `DATABASE_URL` | Postgres. Si falta, la app cae a SQLite **dentro del contenedor**: en Cloud Run el disco es efímero, así que usuarios, clientes y operaciones se borran en cada deploy o reinicio. |

### Recomendadas

- `GEMINI_API_KEY` — sin esto `/upload_pdf` devuelve 503 (no se puede leer la factura). El resto funciona.
- `SENTRY_DSN` — tomarlo del `.env` local (nunca escribirlo en docs ni en git).
- `EMAIL_VERIFICATION_REQUIRED=false` — en beta cerrada queda así.
- `LOG_LEVEL=INFO`

**El script `scripts/deployment/deploy-cloud-run.sh` toma todas del `.env` o
del shell, las valida con `preflight_env.sh` y corta antes de buildear si
falta alguna crítica.**

---

## ⚠️ Notas Importantes

1. **Primera vez en Cloud Run?** → Tendrás $300 de créditos gratis
2. **Costo estimado:** $0-0.50/mes para 2000 usuarios (dentro de free tier)
3. **Cold start:** Primer request tarda ~15s, después <100ms
4. **Logs:** Ver en Google Cloud Console o con `gcloud run logs tail`
5. **Rollback:** Si algo falla, `gcloud run services update --image=PREVIOUS_IMAGE`

---

## 🎯 Post-Deployment

Después del deploy, verificar:
1. [ ] https://YOUR-SERVICE.run.app/health → status: "ok"
2. [ ] Sentry dashboard → ver evento de test
3. [ ] https://YOUR-SERVICE.run.app/api/admin/health/detailed → uptime > 0s
4. [ ] Configurar alertas en Sentry (error rate > 5%)

---

## 📞 Soporte

- **Deployment guide:** Ver DEPLOYMENT_QUICK_START.md
- **Logs monitoring:** Ver LOGGING_AND_MONITORING_GUIDE.md
- **Testing:** Ver PRE_PRODUCTION_TESTING_PLAN.md

---

## ✨ Resumen Ejecutivo

**ESTADO:** 🟢 LISTO PARA DEPLOYMENT

**BLOQUEANTES RESUELTOS:**
- ✅ requirements.txt limpio
- ✅ Secrets sin hardcodear
- ✅ Tests pasando
- ✅ Sentry funcionando

**TIEMPO ESTIMADO DEPLOYMENT:** 15-20 minutos

**RIESGO:** BAJO - Todo testeado y funcionando localmente

---

**Última verificación:** 2025-10-26
**Próximo paso:** Ejecutar `./deploy-cloud-run.sh` mañana
