#!/bin/bash

# ==============================================================================
# Script de Configuración Automática para CDI en Google Cloud
# ==============================================================================
# Este script prepara todo el entorno en GCP para que el deploy sea automático.
# Requisito: Tener 'gcloud' instalado y logueado ('gcloud auth login')
# ==============================================================================

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando configuración de CDI en Google Cloud...${NC}"

# 1. Configurar Proyecto
read -p "Ingrese el ID de su proyecto Google Cloud (PROJECT_ID): " PROJECT_ID
echo -e "${BLUE}Configurando proyecto $PROJECT_ID...${NC}"
gcloud config set project $PROJECT_ID

# 2. Habilitar APIs necesarias
echo -e "${BLUE}Habilitando APIs (esto puede tardar unos minutos)...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com

# 3. Crear repositorio de Artifact Registry
REPO_NAME="cdi-repo"
REGION="us-central1"
echo -e "${BLUE}Verificando repositorio $REPO_NAME en $REGION...${NC}"
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION &>/dev/null; then
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Repositorio Docker para CDI Sistema MARIA"
    echo -e "${GREEN}Repositorio creado.${NC}"
else
    echo -e "${GREEN}Repositorio ya existe.${NC}"
fi

# 4. Configurar Secretos (Env Vars seguras)
echo -e "${BLUE}Configurando secretos en Secret Manager...${NC}"

# Función helper para crear secretos
create_secret() {
    local NAME=$1
    local VALUE=$2
    
    if ! gcloud secrets describe $NAME &>/dev/null; then
        echo -n "$VALUE" | gcloud secrets create $NAME --data-file=-
        echo -e "${GREEN}Secreto $NAME creado.${NC}"
    else
        echo -e "${GREEN}Secreto $NAME ya existe (saltando).${NC}"
    fi
}

echo "Ingrese los valores para producción:"
read -s -p "GEMINI_API_KEY: " GEM_KEY
echo ""
create_secret "gemini-api-key" "$GEM_KEY"

read -s -p "DATABASE_URL (Postgres): " DB_URL
echo ""
create_secret "database-url" "$DB_URL"

# Generar JWT Secret aleatorio si no se provee
generated_jwt=$(openssl rand -hex 32)
echo -e "${BLUE}Generando JWT_SECRET_KEY automático...${NC}"
create_secret "jwt-secret-key" "$generated_jwt"

# 5. Permisos para Cloud Build
echo -e "${BLUE}Asignando permisos a Cloud Build...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CB_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"

# Permiso para desplegar en Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CB_SA" \
    --role="roles/run.admin"

# Permiso para actuar como Service Account (necesario para el runtime)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CB_SA" \
    --role="roles/iam.serviceAccountUser"

# Permiso para leer secretos
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CB_SA" \
    --role="roles/secretmanager.secretAccessor"

echo -e "${GREEN}✅ Configuración completada exitosamente!${NC}"
echo -e "${BLUE}Pasos finales:${NC}"
echo "1. Ve a https://console.cloud.google.com/cloud-build/triggers"
echo "2. Conecta tu repositorio GitHub."
echo "3. Crea un disparador apuntando al archivo 'cloudbuild.yaml'."
echo "4. Haz un 'git push' y mira la magia."
