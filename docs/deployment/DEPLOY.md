# 🚀 DEPLOY - Guía Ultra Rápida

## Prerrequisitos (una sola vez)
```bash
# 1. Tener gcloud instalado y logueado
brew install google-cloud-sdk  # o desde https://cloud.google.com/sdk/docs/install
gcloud auth login
```

---

## Deploy en 3 Pasos

### Paso 1: Configurar GCP (5 min, solo la primera vez)
```bash
./setup_gcp.sh
```
Te pedirá:
- ID del proyecto GCP
- GEMINI_API_KEY
- DATABASE_URL (PostgreSQL)

### Paso 2: Conectar GitHub (2 min, solo la primera vez)
1. Ir a: https://console.cloud.google.com/cloud-build/triggers
2. Click "Conectar repositorio"
3. Seleccionar: `Memu007/CDI`
4. Crear trigger apuntando a `cloudbuild.yaml`

### Paso 3: Deploy (30 seg, cada vez)
```bash
git add .
git commit -m "deploy: descripción del cambio"
git push
```
¡Listo! Cloud Build hace todo automáticamente. 🎉

---

## Verificar Deploy
```bash
# Ver logs del build
gcloud builds list --limit=1

# Ver URL del servicio
gcloud run services describe cdi-backend --region=us-central1 --format='value(status.url)'
```

---

## Rollback (si algo sale mal)
```bash
# Volver a versión anterior
gcloud run services update-traffic cdi-backend --region=us-central1 --to-revisions=PREVIOUS_REVISION=100
```

---

## Variables de Entorno en Producción
| Variable | Origen | Descripción |
|----------|--------|-------------|
| `GEMINI_API_KEY` | Secret Manager | API de IA |
| `DATABASE_URL` | Secret Manager | PostgreSQL |
| `JWT_SECRET_KEY` | Secret Manager | Auto-generado |
| `ENVIRONMENT` | cloudbuild.yaml | `production` |
| `ENABLE_HSTS` | cloudbuild.yaml | `true` |

---

**¿Problemas?** Revisar logs: `gcloud builds log $(gcloud builds list --limit=1 --format='value(id)')`
