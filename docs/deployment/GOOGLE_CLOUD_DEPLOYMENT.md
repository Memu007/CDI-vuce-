# Google Cloud / Firebase Deployment - CDI Sistema MARÍA

## ❓ ¿Qué Incluye Tu Suscripción Gemini Advanced ($20/mes)?

### ✅ Lo que SÍ incluye:
- **Gemini API:** Mayor cuota de requests (ya lo estás usando en la app)
- **Gemini Advanced features:** Modelos más potentes (gemini-1.5-pro)
- **Google Workspace integration:** Gemini en Gmail, Docs, etc.

### ❌ Lo que NO incluye:
- **Google Cloud hosting** (Cloud Run, App Engine, Compute Engine)
- **Firebase services** (Hosting, Firestore, Storage)
- **Cloud SQL** (PostgreSQL)
- **Memorystore** (Redis)

**Conclusión:** Tu suscripción Gemini NO incluye infraestructura de hosting, pero podés usar GCP/Firebase con costo separado.

---

## 🚀 Opciones de Deployment en Google Cloud

### Opción 1: **Cloud Run + Firebase** (RECOMENDADO para 2000 usuarios)

**Backend (FastAPI):** Cloud Run
**Frontend:** Firebase Hosting
**Base de Datos:** Cloud SQL (PostgreSQL) o Firestore
**Storage:** Cloud Storage
**Redis:** Memorystore (opcional)

#### ✅ Ventajas:
- **Serverless:** Auto-scaling automático
- **Pay-per-use:** Solo pagas lo que usás
- **Tier gratuito:** 2M requests/mes gratis
- **Fácil deployment:** `gcloud run deploy`
- **HTTPS automático**
- **Muy económico** para 2000 usuarios

#### 💰 Costo Estimado Mensual (2000 usuarios):

```
Cloud Run (backend):
- 2000 usuarios × 30 req/día = 60k req/mes
- Dentro del tier gratuito (2M req/mes)
- Costo: $0/mes 🎉

Firebase Hosting (frontend):
- Spark Plan (gratuito): 10GB storage, 360MB/día bandwidth
- Para tu caso: suficiente
- Costo: $0/mes 🎉

Cloud SQL (PostgreSQL):
- db-f1-micro: 1 vCPU, 614 MB RAM
- Costo: ~$9/mes
- O usar Firestore: gratis hasta 50k reads/día

Cloud Storage (archivos PDF/Excel):
- 5GB standard storage
- Costo: ~$0.10/mes

Gemini API:
- Ya incluido en tu suscripción: $0/mes

TOTAL ESTIMADO: ~$9-10/mes (si usás Cloud SQL)
TOTAL ESTIMADO: ~$0-1/mes (si usás Firestore)
```

---

### Opción 2: **App Engine** (Más simple pero más caro)

**Todo en uno:** App Engine Standard

#### ✅ Ventajas:
- Deployment muy simple
- Auto-scaling incluido
- Integración con Google services

#### ❌ Desventajas:
- Más caro que Cloud Run (~$30-50/mes para 2000 usuarios)
- Menos control

---

### Opción 3: **Compute Engine VM** (Más control pero más trabajo)

**VM dedicada:** e2-small (2 vCPUs, 2GB RAM)

#### ✅ Ventajas:
- Control total del servidor
- Podés usar el mismo setup que ya tenés (Gunicorn + 4 workers)

#### ❌ Desventajas:
- Más caro: ~$25/mes + mantenimiento manual
- Tenés que configurar todo vos

---

## 🏆 RECOMENDACIÓN PARA TU CASO

**Cloud Run + Firebase Hosting + Firestore**

**Por qué:**
1. ✅ **Casi gratis** para 2000 usuarios (~$0-2/mes)
2. ✅ **Auto-scaling** automático
3. ✅ **Serverless** - no te preocupás por servidores
4. ✅ **Deploy super fácil** (un comando)
5. ✅ **HTTPS gratis** (certificado automático)
6. ✅ **Tu Gemini API ya está configurado**

---

## 📝 Arquitectura Propuesta

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Firebase Hosting           │ ← Frontend (HTML/CSS/JS)
│  (CDN Global)               │   GRATIS
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Cloud Run                  │ ← Backend (FastAPI + 4 workers)
│  (Auto-scaling)             │   GRATIS (< 2M req/mes)
└────┬────────────────┬───────┘
     │                │
     ▼                ▼
┌─────────┐    ┌──────────────┐
│Firestore│    │Cloud Storage │ ← Archivos PDF/Excel
│(NoSQL)  │    │(Blob Storage)│   ~$0.10/mes
│GRATIS*  │    └──────────────┘
└─────────┘
     │
     ▼
┌──────────────────┐
│ Gemini API       │ ← Ya incluido en tu plan
│ (Tu suscripción) │   $0 extra
└──────────────────┘

*Firestore: 50k reads/día, 20k writes/día gratis
```

---

## 🛠️ ¿Qué Necesitás para Deployar?

### 1. **Cuenta Google Cloud Platform (GCP)**
- Entrá a: https://console.cloud.google.com
- **Créditos gratis:** $300 USD por 90 días (nuevos usuarios)
- Después: pay-as-you-go

### 2. **Instalar Google Cloud CLI**
```bash
# Ya lo tenés instalado en el proyecto:
/home/user/CDI/google-cloud-sdk/

# Inicializar:
gcloud init
gcloud auth login
```

### 3. **Crear proyecto GCP**
```bash
gcloud projects create cdi-sistema-maria --name="CDI Sistema MARÍA"
gcloud config set project cdi-sistema-maria
```

### 4. **Habilitar APIs necesarias**
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
```

---

## 🚀 Deployment Rápido (3 pasos)

### Paso 1: Deploy Backend a Cloud Run
```bash
# Crear Dockerfile (ya lo tengo listo para vos)
gcloud run deploy cdi-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=tu_api_key

# URL generada automáticamente:
# https://cdi-backend-xxxxx-uc.a.run.app
```

### Paso 2: Deploy Frontend a Firebase Hosting
```bash
# Instalar Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Inicializar
firebase init hosting

# Deploy
firebase deploy --only hosting

# URL:
# https://cdi-sistema-maria.web.app
```

### Paso 3: Configurar Firestore (Base de Datos)
```bash
# Crear Firestore database
gcloud firestore databases create --location=us-central

# O desde consola:
# https://console.firebase.google.com
```

---

## 📊 Comparación de Costos (2000 usuarios)

| Opción | Costo Mensual | Dificultad | Escalabilidad |
|--------|---------------|------------|---------------|
| **Cloud Run + Firebase** | $0-2/mes | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| App Engine | $30-50/mes | ⭐ | ⭐⭐⭐⭐ |
| Compute Engine VM | $25-40/mes | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| DigitalOcean/AWS | $40-60/mes | ⭐⭐⭐ | ⭐⭐⭐ |

---

## ✅ RESPUESTA A TU PREGUNTA

**¿Podés montar la app completa en Google Cloud/Firebase?**
- ✅ **SÍ, completamente**
- ✅ **Costo:** Casi gratis (~$0-2/mes para 2000 usuarios)
- ✅ **Tu suscripción Gemini:** Ya te cubre la API de Gemini
- ⚠️ **Infraestructura:** Es costo separado (pero muy barato)

**¿Qué sigue?**
1. Si tenés cuenta GCP y querés deployar, te creo todos los archivos de configuración
2. Te guío paso a paso con el deployment
3. En ~30 minutos tenés la app corriendo en producción

---

## 🎁 BONUS: Créditos Gratis Disponibles

**Si sos nuevo en Google Cloud:**
- ✅ **$300 USD de créditos** por 90 días
- ✅ Suficiente para 3+ meses gratis con tu app
- ✅ Después pagarías ~$0-2/mes con el tier gratuito

**Enlace:** https://cloud.google.com/free

---

¿Querés que te cree los archivos de configuración para deployar en Cloud Run + Firebase?
