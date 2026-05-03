#!/bin/bash

# Script de testing completo para todas las features
# Proyecto MARÍA - Testing antes de demo con despachantes

BASE_URL="http://127.0.0.1:8001"
PASS=0
FAIL=0
TOTAL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🧪 TESTING COMPLETO - PROYECTO MARÍA"
echo "=========================================="
echo ""

# Helper functions
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_field="$5"

    TOTAL=$((TOTAL + 1))
    echo -n "[$TOTAL] Testing $name... "

    if [ "$method" == "GET" ]; then
        response=$(curl -s "$BASE_URL$endpoint")
    else
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    if echo "$response" | grep -q "\"$expected_field\""; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   Response: $response" | head -c 200
        echo ""
        FAIL=$((FAIL + 1))
        return 1
    fi
}

# 0. Health check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏥 HEALTH CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "Health" "GET" "/health" "" "status"
echo ""

# 1. Feature #6: Calculadora (más fácil de probar primero)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧮 FEATURE #6: CALCULADORA VALOR EN PLAZA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "Calcular valor plaza" "POST" "/api/calculator/valor-plaza" \
    '{"ncm":"84713010","origen":"CN","fob_unitario":500,"cantidad":10}' \
    "valor_final"

test_endpoint "Comparar orígenes" "POST" "/api/calculator/comparar-origenes" \
    '{"ncm":"84713010","fob_unitario":500,"cantidad":10}' \
    "mejor_origen"

test_endpoint "Listar NCM rates" "GET" "/api/calculator/ncm-rates" "" "rates"

test_endpoint "Info MERCOSUR" "GET" "/api/calculator/mercosur-info" "" "paises"

test_endpoint "Listar ejemplos" "GET" "/api/calculator/ejemplos" "" "ejemplos"

echo ""

# 2. Feature #2: Items (necesita seed data primero)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✏️  FEATURE #2: CORRECCIÓN RÁPIDA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Crear datos de prueba
echo -n "Creando datos de prueba... "
SEED_RESPONSE=$(curl -s -X POST "$BASE_URL/api/items/_test/seed")
OPERATION_ID=$(echo "$SEED_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['operation_id'])" 2>/dev/null)

if [ -z "$OPERATION_ID" ]; then
    echo -e "${RED}❌ FAIL${NC} - No se pudo crear datos de prueba"
    OPERATION_ID="test-op-123"
else
    echo -e "${GREEN}✅ OK${NC} (Operation ID: ${OPERATION_ID:0:8}...)"
    # Extraer ID del primer item
    ITEM_ID=$(echo "$SEED_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['items'][0]['id'])" 2>/dev/null)
fi

test_endpoint "Actualizar item" "PUT" "/api/items/$ITEM_ID" \
    '{"cantidad":15,"peso_unitario":3.0}' \
    "updated_fields"

test_endpoint "Batch update origen" "POST" "/api/items/batch-update" \
    '{"operation":"apply_origen","value":"BR","filter":{"descripcion_contains":"laptop"}}' \
    "items_updated"

test_endpoint "Duplicar item" "POST" "/api/items/$ITEM_ID/duplicate" \
    '{"cantidad":5}' \
    "duplicated_item"

test_endpoint "Obtener item" "GET" "/api/items/$ITEM_ID" "" "item"

echo ""

# 3. Feature #4: Templates
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 FEATURE #4: PLANTILLAS DESPACHO EXPRESS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Crear plantilla desde operación
TEMPLATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/templates/from-operation" \
    -H "Content-Type: application/json" \
    -d "{\"operation_id\":\"$OPERATION_ID\",\"template_name\":\"Test Template\",\"description\":\"Template de testing\"}")

TEMPLATE_ID=$(echo "$TEMPLATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['template']['id'])" 2>/dev/null)

if [ -z "$TEMPLATE_ID" ]; then
    echo -e "[$TOTAL] Testing Crear plantilla... ${RED}❌ FAIL${NC}"
    FAIL=$((FAIL + 1))
    TEMPLATE_ID="test-template-123"
else
    echo -e "[$TOTAL] Testing Crear plantilla... ${GREEN}✅ PASS${NC}"
    PASS=$((PASS + 1))
fi
TOTAL=$((TOTAL + 1))

test_endpoint "Listar plantillas" "GET" "/api/templates/" "" "templates"

test_endpoint "Ver plantilla" "GET" "/api/templates/$TEMPLATE_ID" "" "template"

test_endpoint "Usar plantilla" "POST" "/api/templates/use" \
    "{\"template_id\":\"$TEMPLATE_ID\",\"overrides\":[{\"item_index\":0,\"cantidad\":150}]}" \
    "operation"

echo ""

# 4. Feature #3: Validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ FEATURE #3: VALIDACIÓN PRE-ENVÍO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "Validar operación OK" "POST" "/api/validation/validate-operation" \
    '{"items":[{"pieza":"84713010","descripcion":"LAPTOP","origen":"CN","cantidad":10,"valor_unitario":500,"peso_unitario":2.5}]}' \
    "valid"

test_endpoint "Validar con error NCM" "POST" "/api/validation/validate-operation" \
    '{"items":[{"pieza":"abc","descripcion":"TEST","origen":"CN","cantidad":10,"valor_unitario":500,"peso_unitario":2.5}]}' \
    "issues"

test_endpoint "Quick check" "POST" "/api/validation/quick-check" \
    '[{"pieza":"84713010","descripcion":"LAPTOP","origen":"CN","cantidad":10,"valor_unitario":500,"peso_unitario":2.5}]' \
    "ok"

echo ""

# Summary
echo "=========================================="
echo "📊 RESUMEN DE TESTING"
echo "=========================================="
echo ""
echo "Total tests: $TOTAL"
echo -e "${GREEN}Pasaron: $PASS${NC}"
echo -e "${RED}Fallaron: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 TODOS LOS TESTS PASARON!${NC}"
    echo "✅ Sistema listo para demo con despachantes"
    exit 0
else
    PERCENTAGE=$((PASS * 100 / TOTAL))
    echo -e "${YELLOW}⚠️  $FAIL tests fallaron ($PERCENTAGE% pasaron)${NC}"
    echo "⚠️  Revisar antes de demo"
    exit 1
fi
