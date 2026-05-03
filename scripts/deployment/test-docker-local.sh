#!/bin/bash

# ========================================================================
# Test Docker Local - CDI Sistema MARÍA
# ========================================================================
# Prueba la imagen Docker localmente antes de deployar a Cloud Run
# ========================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Docker Image Locally${NC}"
echo -e "${BLUE}========================================${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker instalado${NC}"

# Build de la imagen
echo -e "${YELLOW}🐳 Buildeando imagen...${NC}"
docker build -t cdi-sistema-maria:test .

echo -e "${GREEN}✅ Imagen buildeada${NC}"

# Limpiar containers viejos
echo -e "${YELLOW}🧹 Limpiando containers viejos...${NC}"
docker rm -f cdi-test 2>/dev/null || true

# Ejecutar container
echo -e "${YELLOW}🚀 Iniciando container en puerto 8080...${NC}"
docker run -d \
  --name cdi-test \
  -p 8080:8080 \
  -e PORT=8080 \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  cdi-sistema-maria:test

# Esperar que arranque
echo -e "${YELLOW}⏳ Esperando que el servidor arranque...${NC}"
sleep 15

# Test health check
echo -e "${YELLOW}🧪 Testeando health check...${NC}"
if curl -s http://localhost:8080/health | grep -q "ok"; then
    echo -e "${GREEN}✅ Health check OK!${NC}"
else
    echo -e "${RED}❌ Health check FAIL${NC}"
    echo -e "${YELLOW}Logs del container:${NC}"
    docker logs cdi-test
    exit 1
fi

# Test root
echo -e "${YELLOW}🧪 Testeando root endpoint...${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
if [ "$STATUS" = "200" ] || [ "$STATUS" = "405" ]; then
    echo -e "${GREEN}✅ Root endpoint OK (${STATUS})${NC}"
else
    echo -e "${RED}❌ Root endpoint FAIL (${STATUS})${NC}"
fi

# Test workers
echo -e "${YELLOW}🧪 Verificando workers...${NC}"
WORKERS=$(docker exec cdi-test ps aux | grep -c "[g]unicorn.*worker" || echo "0")
if [ "$WORKERS" -ge 4 ]; then
    echo -e "${GREEN}✅ $WORKERS workers corriendo${NC}"
else
    echo -e "${YELLOW}⚠️  Solo $WORKERS workers (esperados 4+)${NC}"
fi

# Mostrar info del container
echo -e ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Container Info${NC}"
echo -e "${GREEN}========================================${NC}"
docker ps | grep cdi-test

echo -e ""
echo -e "${BLUE}Para ver logs en tiempo real:${NC}"
echo -e "  docker logs -f cdi-test"

echo -e ""
echo -e "${BLUE}Para testear manualmente:${NC}"
echo -e "  curl http://localhost:8080/health"
echo -e "  curl http://localhost:8080/"

echo -e ""
echo -e "${BLUE}Para detener el container:${NC}"
echo -e "  docker stop cdi-test"
echo -e "  docker rm cdi-test"

echo -e ""
echo -e "${GREEN}✅ Docker test exitoso!${NC}"
echo -e "${GREEN}La imagen está lista para deployar a Cloud Run${NC}"
