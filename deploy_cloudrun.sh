#!/bin/bash
# ========================================================================
# Script de Despliegue para Google Cloud Run
# ========================================================================
# Requisitos:
# 1. Tener instalado el Google Cloud CLI (gcloud)
# 2. Estar autenticado (`gcloud auth login`)
# 3. Tener un proyecto configurado (`gcloud config set project [TU_PROYECTO]`)

PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="cdi-maria"
REGION="us-central1" # Puedes cambiar esto a la región más cercana

echo "🚀 Iniciando despliegue en Google Cloud Run..."
echo "📦 Construyendo imagen y empujando a Google Container Registry..."

# Enviamos el build directamente a la nube (usando el Dockerfile)
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "⚡ Desplegando servicio..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars ENVIRONMENT=production \
  --port 8080

echo "✅ ¡Despliegue finalizado!"
