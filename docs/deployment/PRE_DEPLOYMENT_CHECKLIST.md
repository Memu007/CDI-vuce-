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
- [x] **Dockerfile** - Multi-stage, Python 3.12-slim, 4 workers, PORT 8080
- [x] **.dockerignore** - Excluye tests, cache, logs
- [x] **cloudbuild.yaml** - Build + Deploy a Cloud Run
- [x] **deploy-cloud-run.sh** - Script automatizado (ejecutable)
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
- [x] **Multi-worker** - Gunicorn con 4 workers Uvicorn
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
./deploy-cloud-run.sh
# Ingresa GEMINI_API_KEY cuando lo pida
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

**Obligatorias:**
- `GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `SENTRY_DSN` - Ya en .env: https://8719fd4a82ee072fc2e1576e34219fb9@...

**Opcionales:**
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`

**El script `deploy-cloud-run.sh` configura automáticamente:**
- PORT=8080
- SENTRY_DSN desde .env
- ENVIRONMENT=production

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
