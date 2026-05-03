# Deploy a Google Cloud Run - Quick Start

## Pre-requisitos (5 min)
- [ ] Google Cloud account
- [ ] `gcloud` CLI instalado ([docs](https://cloud.google.com/sdk/docs/install))
- [ ] Proyecto GCP creado

## Deployment en 3 Pasos (10 min)

### 1. Setup inicial
```bash
gcloud auth login
gcloud config set project cdi-sistema-maria
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com
```

### 2. Configurar variables
```bash
cp .env.example .env
# Editar .env con tus valores:
# - SENTRY_DSN (tu DSN de Sentry)
# - GEMINI_API_KEY (obligatorio)
# - DATABASE_URL (opcional)
```

### 3. Deploy
```bash
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
# El script te pedirá GEMINI_API_KEY interactivamente
```

### 4. Verificación
```bash
SERVICE_URL=$(gcloud run services describe cdi-backend --region us-central1 --format 'value(status.url)')
curl $SERVICE_URL/health
```

## Troubleshooting

**Permission denied** → `gcloud auth login` y verificar IAM

**Build failed** → Verificar Docker: `docker ps`

**Service not responding** → Esperar 15s (cold start), ver logs: `gcloud run logs read cdi-backend --region us-central1`

## Post-deployment Checklist
- [ ] Health check OK: `curl https://tu-servicio.run.app/health`
- [ ] Sentry recibiendo eventos
- [ ] Admin endpoints accesibles

## Ver logs
```bash
gcloud run logs tail cdi-backend --region us-central1
```
