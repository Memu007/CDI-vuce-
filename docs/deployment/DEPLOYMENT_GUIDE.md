# 🚀 Guía de Deployment - Google Cloud Run

## ✅ Archivos Creados

Todos los archivos de configuración están listos:

1. **Dockerfile** - Imagen Docker optimizada (multi-stage, 4 workers Gunicorn)
2. **.dockerignore** - Excluye archivos innecesarios
3. **firebase.json** - Configuración Firebase Hosting (frontend)
4. **.firebaserc** - Proyecto Firebase
5. **cloudbuild.yaml** - CI/CD automático
6. **deploy-cloud-run.sh** - Script de deployment fácil
7. **test-docker-local.sh** - Test local antes de deployar

---

## 📋 Prerequisitos

### 1. Google Cloud Account
- Creá cuenta en: https://console.cloud.google.com
- **Nuevos usuarios:** $300 USD gratis por 90 días

### 2. Instalar gcloud CLI
Ya lo tenés instalado en:
```bash
/home/user/CDI/google-cloud-sdk/
```

Inicializar:
```bash
gcloud init
gcloud auth login
```

### 3. Crear Proyecto GCP
```bash
gcloud projects create cdi-sistema-maria --name="CDI Sistema MARÍA"
gcloud config set project cdi-sistema-maria
```

### 4. Habilitar Billing
- Ir a: https://console.cloud.google.com/billing
- Vincular tarjeta (no se cobra nada en tier gratuito)

---

## 🚀 DEPLOYMENT RÁPIDO (3 Opciones)

### Opción 1: Script Automático (RECOMENDADO)

```bash
# Un solo comando hace todo:
./deploy-cloud-run.sh
```

Este script:
- ✅ Verifica gcloud CLI
- ✅ Habilita APIs necesarias
- ✅ Buildea la imagen Docker
- ✅ Deploya a Cloud Run
- ✅ Te da la URL final

**Tiempo:** ~5-10 minutos

---

### Opción 2: Manual Paso a Paso

#### Paso 1: Habilitar APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Paso 2: Build de la imagen
```bash
gcloud builds submit --tag gcr.io/cdi-sistema-maria/cdi-backend
```

#### Paso 3: Deploy a Cloud Run
```bash
gcloud run deploy cdi-backend \
  --image gcr.io/cdi-sistema-maria/cdi-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars "GEMINI_API_KEY=tu-api-key"
```

#### Paso 4: Obtener URL
```bash
gcloud run services describe cdi-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

---

### Opción 3: CI/CD Automático (Avanzado)

#### Configurar Cloud Build Trigger
```bash
gcloud builds triggers create github \
  --repo-name=CDI \
  --repo-owner=Memu007 \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

Después de esto, cada `git push` a `main` deploya automáticamente!

---

## 🧪 TESTING LOCAL (Opcional)

Si tenés Docker instalado:

```bash
# Test local antes de deployar
./test-docker-local.sh
```

Esto:
- Buildea la imagen localmente
- Corre el container en puerto 8080
- Testea health check y endpoints
- Verifica los 4 workers

**Para testear manualmente:**
```bash
docker build -t cdi-test .
docker run -p 8080:8080 -e PORT=8080 cdi-test
```

---

## 💰 COSTO ESTIMADO

### Para 2000 usuarios (10% concurrentes = 200):

**Cloud Run:**
- Requests: 60,000/mes
- **Tier gratuito:** 2,000,000 req/mes
- **Costo:** $0/mes ✅

**Cloud Build (deployment):**
- **Tier gratuito:** 120 builds/día
- **Costo:** $0/mes ✅

**Container Registry:**
- Storage: ~500MB
- **Tier gratuito:** Primeros GB gratis
- **Costo:** ~$0.05/mes

**Total:** ~$0.05 - $0.50/mes 🎉

---

## 🔧 CONFIGURACIÓN AVANZADA

### Variables de Entorno

Configurar después del deployment:

```bash
gcloud run services update cdi-backend \
  --set-env-vars "GEMINI_API_KEY=tu-key,DATABASE_URL=postgresql://..."
```

### Secrets (Recomendado para API keys)

```bash
# Crear secret
echo -n "tu-api-key" | gcloud secrets create gemini-api-key --data-file=-

# Usar en Cloud Run
gcloud run services update cdi-backend \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

### Custom Domain

```bash
gcloud run domain-mappings create \
  --service cdi-backend \
  --domain api.tudominio.com \
  --region us-central1
```

---

## 📊 MONITORING

### Logs en Tiempo Real
```bash
gcloud run services logs tail cdi-backend --project cdi-sistema-maria
```

### Métricas
```bash
# Ver en consola:
https://console.cloud.google.com/run/detail/us-central1/cdi-backend/metrics
```

### Alertas
Configurar desde Cloud Console:
- Requests > 1000/min → Email
- Error rate > 5% → SMS
- Latency p99 > 2s → Email

---

## 🐛 TROUBLESHOOTING

### Build falla
```bash
# Ver logs detallados
gcloud builds list --limit=1
gcloud builds log <BUILD_ID>
```

### Service no arranca
```bash
# Ver logs
gcloud run services logs read cdi-backend --limit=50

# Revisar configuración
gcloud run services describe cdi-backend
```

### Test health check
```bash
SERVICE_URL=$(gcloud run services describe cdi-backend --format='value(status.url)')
curl ${SERVICE_URL}/health
```

---

## 🎯 PRÓXIMOS PASOS

Después del deployment:

1. **Configurar Firebase Hosting** (frontend):
```bash
firebase login
firebase init hosting
firebase deploy
```

2. **Configurar Firestore** (base de datos):
```bash
gcloud firestore databases create --location=us-central
```

3. **Configurar CI/CD** (Cloud Build Triggers)

4. **Configurar Domain Custom**

5. **Setup Monitoring y Alertas**

---

## 📚 RECURSOS

- Cloud Run Docs: https://cloud.google.com/run/docs
- Pricing Calculator: https://cloud.google.com/products/calculator
- Cloud Console: https://console.cloud.google.com
- Firebase Console: https://console.firebase.google.com

---

## ✅ CHECKLIST PRE-DEPLOYMENT

- [ ] Cuenta GCP creada
- [ ] Billing habilitada
- [ ] gcloud CLI instalado y configurado
- [ ] Proyecto creado
- [ ] GEMINI_API_KEY lista
- [ ] Dockerfile testeado (opcional)
- [ ] Revisar variables de entorno

---

## 🚀 COMANDO ÚNICO PARA DEPLOYAR

```bash
./deploy-cloud-run.sh
```

**Eso es todo!** En ~10 minutos tenés la app corriendo en:
```
https://cdi-backend-xxxxx-uc.a.run.app
```

---

**¿Dudas?** Revisar logs con:
```bash
gcloud run services logs tail cdi-backend --project cdi-sistema-maria
```
