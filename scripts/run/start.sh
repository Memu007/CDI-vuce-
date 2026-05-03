#!/bin/bash

# ========================================================================
# CDI Sistema MARÍA - Production Startup Script
# ========================================================================
# Inicia el servidor con Gunicorn + Uvicorn workers para producción
# Configurado para 2000 usuarios (200 concurrentes)
# ========================================================================

set -e  # Exit on error

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CDI Sistema MARÍA - Starting Server${NC}"
echo -e "${BLUE}========================================${NC}"

# Verificar que gunicorn esté instalado
if ! command -v gunicorn &> /dev/null; then
    echo -e "${YELLOW}⚠️  Gunicorn no instalado. Instalando...${NC}"
    pip install gunicorn
fi

# Configuración
WORKERS=${WORKERS:-4}           # 4 workers por defecto
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKER_CLASS="uvicorn.workers.UvicornWorker"

echo -e "${GREEN}✅ Configuración:${NC}"
echo -e "   Workers: ${WORKERS}"
echo -e "   Host: ${HOST}"
echo -e "   Port: ${PORT}"
echo -e "   Worker Class: ${WORKER_CLASS}"
echo -e "${BLUE}========================================${NC}\n"

# Iniciar servidor
echo -e "${GREEN}🚀 Iniciando servidor...${NC}\n"

gunicorn proyecto_maria.main:app \
  --workers ${WORKERS} \
  --worker-class ${WORKER_CLASS} \
  --bind ${HOST}:${PORT} \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 50
