#!/bin/bash

# ========================================================================
# Deployment Script - Google Cloud Run
# ========================================================================
# Deploy rápido de CDI Sistema MARÍA a Google Cloud Run
#
# Prerequisitos:
#   - gcloud CLI instalado y configurado
#   - Proyecto GCP creado
#   - APIs habilitadas (run, cloudbuild, firestore)
#   - Variables de producción en el shell o en el `.env` de la raíz
#
# Uso:
#   ./scripts/deployment/deploy-cloud-run.sh
#
# OJO: este script deploya el servicio `cdi-backend`. En la raíz del repo hay
# otro (`deploy_cloudrun.sh`) que deploya `cdi-maria`. Son dos servicios
# distintos: usá siempre el mismo o vas a tener dos apps vivas con bases
# distintas. Según HANDOFF.md el entorno productivo actual es Railway.
# ========================================================================

set -euo pipefail  # Exit on error

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CDI Sistema MARÍA - Cloud Run Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# ========================================================================
# Configuración
# ========================================================================

PROJECT_ID=${PROJECT_ID:-"cdi-sistema-maria"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="cdi-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}📋 Configuración:${NC}"
echo -e "   Proyecto: ${PROJECT_ID}"
echo -e "   Región: ${REGION}"
echo -e "   Servicio: ${SERVICE_NAME}"
echo -e "${BLUE}========================================${NC}\n"

# ========================================================================
# Variables de producción + validación previa
# ========================================================================
# Se valida ANTES de buildear: si falta JWT_SECRET_KEY o ALLOWED_ORIGINS la
# app aborta el arranque y el servicio queda reiniciándose en loop.

if [ -f .env ]; then
    echo -e "${YELLOW}📦 Leyendo variables de .env${NC}"
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# Un deploy siempre va a producción, aunque el .env local diga otra cosa.
export ENVIRONMENT=production

./scripts/deployment/preflight_env.sh

# ========================================================================
# Verificar gcloud
# ========================================================================

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI no instalado${NC}"
    echo -e "${YELLOW}Instalá desde: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

echo -e "${GREEN}✅ gcloud CLI instalado${NC}"

# ========================================================================
# Verificar autenticación
# ========================================================================

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}⚠️  No estás autenticado. Ejecutando login...${NC}"
    gcloud auth login
fi

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo -e "${GREEN}✅ Autenticado como: ${ACCOUNT}${NC}"

# ========================================================================
# Configurar proyecto
# ========================================================================

echo -e "${YELLOW}📦 Configurando proyecto...${NC}"
gcloud config set project ${PROJECT_ID}

# ========================================================================
# Habilitar APIs necesarias
# ========================================================================

echo -e "${YELLOW}🔧 Habilitando APIs necesarias...${NC}"
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  firestore.googleapis.com

echo -e "${GREEN}✅ APIs habilitadas${NC}"

# ========================================================================
# Build de la imagen Docker
# ========================================================================

echo -e "${YELLOW}🐳 Buildeando imagen Docker...${NC}"
gcloud builds submit --tag ${IMAGE_NAME}:latest

echo -e "${GREEN}✅ Imagen Docker creada${NC}"

# ========================================================================
# Deploy a Cloud Run
# ========================================================================

echo -e "${YELLOW}🚀 Deploying a Cloud Run...${NC}"

# Separador ";" (delimitador custom "^;^" de gcloud): ALLOWED_ORIGINS puede
# tener varias URLs separadas por coma y la coma es el separador por defecto.
ENV_VARS="PORT=8080"
ENV_VARS="${ENV_VARS};ENVIRONMENT=production"
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

gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80 \
  --timeout 120s \
  --set-env-vars "^;^${ENV_VARS}"

# ========================================================================
# Obtener URL del servicio
# ========================================================================

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo -e ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT EXITOSO!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "🌐 URL del servicio:"
echo -e "${BLUE}${SERVICE_URL}${NC}"
echo -e ""
echo -e "📊 Health check:"
echo -e "${BLUE}${SERVICE_URL}/health${NC}"
echo -e ""
echo -e "📱 Dashboard:"
echo -e "${BLUE}${SERVICE_URL}/${NC}"
echo -e ""
echo -e "${YELLOW}Nota: El servicio puede tardar 10-15 segundos en estar listo.${NC}"
echo -e ""

# Test rápido
echo -e "${YELLOW}🧪 Testeando health check...${NC}"
sleep 10
if curl -s "${SERVICE_URL}/health" | grep -q "ok"; then
    echo -e "${GREEN}✅ Servicio funcionando correctamente!${NC}"
else
    echo -e "${YELLOW}⚠️  Servicio aún iniciando, probá en unos segundos${NC}"
fi

echo -e ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deploy completo!${NC}"
echo -e "${GREEN}========================================${NC}"
