#!/bin/bash
# ========================================================================
# Script de Despliegue para Google Cloud Run
# ========================================================================
# Requisitos:
# 1. Tener instalado el Google Cloud CLI (gcloud)
# 2. Estar autenticado (`gcloud auth login`)
# 3. Tener un proyecto configurado (`gcloud config set project [TU_PROYECTO]`)
# 4. Tener las variables de producción cargadas en el shell o en un `.env`
#
# Uso:
#   ./deploy_cloudrun.sh
#
# Las variables se leen del entorno (o del `.env` local si existe) y se
# validan ANTES de buildear. Si falta alguna crítica el script corta: el
# contenedor no arrancaría igual y quedaría reiniciándose en loop.
# ========================================================================

set -euo pipefail

cd "$(dirname "$0")"

# Cargar .env local si está (no está en git, es solo tu copia).
if [ -f .env ]; then
    echo "📦 Leyendo variables de .env"
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# En un deploy siempre vamos a producción, aunque el .env local diga otra cosa.
export ENVIRONMENT=production

# ---- Validación previa (corta si falta algo crítico) --------------------
./scripts/deployment/preflight_env.sh

PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="cdi-maria"
REGION="${REGION:-us-central1}" # Puedes cambiar esto a la región más cercana

echo "🚀 Iniciando despliegue en Google Cloud Run..."
echo "📦 Construyendo imagen y empujando a Google Container Registry..."

# Enviamos el build directamente a la nube (usando el Dockerfile)
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "⚡ Desplegando servicio..."

# Nota: --set-env-vars deja los valores a la vista en la consola de Cloud Run.
# Para secretos de verdad conviene Secret Manager (ver cloudbuild.yaml, que
# usa --set-secrets).
# Separamos con ";" (delimitador custom "^;^" de gcloud) porque
# ALLOWED_ORIGINS puede tener varias URLs separadas por coma y la coma es el
# separador por defecto: se partiría en variables truncadas.
ENV_VARS="ENVIRONMENT=production"
ENV_VARS="${ENV_VARS};ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"
ENV_VARS="${ENV_VARS};JWT_SECRET_KEY=${JWT_SECRET_KEY:-${SECRET_KEY:-}}"
ENV_VARS="${ENV_VARS};DATABASE_URL=${DATABASE_URL}"
ENV_VARS="${ENV_VARS};EMAIL_VERIFICATION_REQUIRED=${EMAIL_VERIFICATION_REQUIRED:-false}"
if [ -n "${GEMINI_API_KEY:-}" ]; then
    ENV_VARS="${ENV_VARS};GEMINI_API_KEY=${GEMINI_API_KEY}"
fi
if [ -n "${SENTRY_DSN:-}" ]; then
    ENV_VARS="${ENV_VARS};SENTRY_DSN=${SENTRY_DSN}"
fi

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "^;^${ENV_VARS}" \
  --port 8080

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed --region $REGION --format 'value(status.url)')

echo "✅ ¡Despliegue finalizado!"
echo "🌐 URL: ${SERVICE_URL}"
echo "🩺 Verificá: curl ${SERVICE_URL}/health"
