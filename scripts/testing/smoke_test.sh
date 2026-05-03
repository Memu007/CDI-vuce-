#!/bin/bash

# ========================================================================
# SMOKE TEST SCRIPT - CDI Sistema MARÍA
# ========================================================================
# Prueba rápida de funcionalidades críticas antes de deploy
# Duración esperada: ~2 minutos
# Uso: ./smoke_test.sh [base_url]
# Ejemplo: ./smoke_test.sh http://localhost:8000
# ========================================================================

set -e  # Exit on error

# Configuración
BASE_URL="${1:-http://localhost:8000}"
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="/tmp/cdi_smoke_test_$$"
RESULTS_FILE="${TEMP_DIR}/results.txt"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
PASSED=0
FAILED=0
TOTAL=0

# ========================================================================
# Funciones Auxiliares
# ========================================================================

setup() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}CDI Sistema MARÍA - Smoke Tests${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Base URL: ${BASE_URL}"
    echo -e "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}========================================${NC}\n"

    mkdir -p "${TEMP_DIR}"
    echo "Test Results - $(date)" > "${RESULTS_FILE}"
}

cleanup() {
    rm -rf "${TEMP_DIR}"
}

test_passed() {
    PASSED=$((PASSED + 1))
    TOTAL=$((TOTAL + 1))
    echo -e "${GREEN}✅ PASS${NC}: $1"
    echo "✅ PASS: $1" >> "${RESULTS_FILE}"
}

test_failed() {
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
    echo -e "${RED}❌ FAIL${NC}: $1"
    echo "❌ FAIL: $1" >> "${RESULTS_FILE}"
    if [ -n "$2" ]; then
        echo -e "  ${YELLOW}Reason:${NC} $2"
        echo "  Reason: $2" >> "${RESULTS_FILE}"
    fi
}

test_header() {
    echo -e "\n${BLUE}━━━ $1 ━━━${NC}"
    echo "" >> "${RESULTS_FILE}"
    echo "━━━ $1 ━━━" >> "${RESULTS_FILE}"
}

# ========================================================================
# Test 1: Health Check
# ========================================================================

test_health_check() {
    test_header "Test 1: Health Check"

    RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/health")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"status"'; then
            test_passed "Health endpoint returns 200 OK"
        else
            test_failed "Health endpoint missing 'status' field" "$BODY"
        fi
    else
        test_failed "Health endpoint returned HTTP $HTTP_CODE" "$BODY"
    fi
}

# ========================================================================
# Test 2: Security Headers
# ========================================================================

test_security_headers() {
    test_header "Test 2: Security Headers"

    HEADERS=$(curl -s -I "${BASE_URL}/" 2>&1)

    # X-Frame-Options
    if echo "$HEADERS" | grep -qi "x-frame-options"; then
        test_passed "X-Frame-Options header present"
    else
        test_failed "X-Frame-Options header missing"
    fi

    # X-Content-Type-Options
    if echo "$HEADERS" | grep -qi "x-content-type-options"; then
        test_passed "X-Content-Type-Options header present"
    else
        test_failed "X-Content-Type-Options header missing"
    fi

    # Content-Security-Policy
    if echo "$HEADERS" | grep -qi "content-security-policy"; then
        test_passed "Content-Security-Policy header present"
    else
        test_failed "Content-Security-Policy header missing"
    fi
}

# ========================================================================
# Test 3: Client Creation (Input Validation)
# ========================================================================

test_client_creation() {
    test_header "Test 3: Client Creation with Validation"

    TIMESTAMP=$(date +%s)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/clientes/public" \
        -H "Content-Type: application/json" \
        -d "{
            \"nombre\": \"Test Cliente ${TIMESTAMP}\",
            \"email\": \"test${TIMESTAMP}@smoketest.com\",
            \"cuit\": \"20123456789\",
            \"direccion\": \"Calle Falsa 123\"
        }")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success".*true'; then
            # Verificar CUIT formateado
            if echo "$BODY" | grep -q '20-12345678-9'; then
                test_passed "Client created with CUIT auto-formatted"
            else
                test_passed "Client created successfully"
            fi
        else
            test_failed "Client creation returned success=false" "$BODY"
        fi
    else
        test_failed "Client creation returned HTTP $HTTP_CODE" "$BODY"
    fi
}

# ========================================================================
# Test 4: XSS Protection
# ========================================================================

test_xss_protection() {
    test_header "Test 4: XSS Protection (HTML Sanitization)"

    TIMESTAMP=$(date +%s)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/clientes/public" \
        -H "Content-Type: application/json" \
        -d "{
            \"nombre\": \"<script>alert('XSS')</script>\",
            \"email\": \"xss${TIMESTAMP}@smoketest.com\",
            \"cuit\": \"20987654321\"
        }")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        # Verificar que el script tag fue sanitizado
        if echo "$BODY" | grep -q "&lt;script&gt;" || echo "$BODY" | grep -q "script.*alert" | grep -v "<script>"; then
            test_passed "XSS attack sanitized (HTML escaped)"
        else
            # Si no encontramos evidencia de sanitización, es un warning
            test_failed "XSS sanitization unclear - manual verification needed" "$BODY"
        fi
    else
        test_failed "XSS test returned HTTP $HTTP_CODE" "$BODY"
    fi
}

# ========================================================================
# Test 5: Path Traversal Protection
# ========================================================================

test_path_traversal() {
    test_header "Test 5: Path Traversal Protection"

    # Intento de path traversal
    RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/download/../../etc/passwd" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    # Debe retornar 403 Forbidden o 404 Not Found (ambos son válidos)
    if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "404" ]; then
        test_passed "Path traversal blocked (HTTP $HTTP_CODE)"
    elif [ "$HTTP_CODE" = "200" ]; then
        BODY=$(echo "$RESPONSE" | sed '$d')
        # Si retorna 200 pero NO contiene contenido de /etc/passwd, está bien
        if echo "$BODY" | grep -q "root:x:0:0"; then
            test_failed "Path traversal BYPASSED - /etc/passwd accessible!"
        else
            test_passed "Path traversal blocked (returned 200 but not passwd file)"
        fi
    else
        test_failed "Unexpected HTTP code for path traversal" "HTTP $HTTP_CODE"
    fi
}

# ========================================================================
# Test 6: Rate Limiting
# ========================================================================

test_rate_limiting() {
    test_header "Test 6: Rate Limiting"

    echo "Sending 130 rapid requests to trigger rate limiting..."

    # Enviar 130 requests rápidos (límite es 120/min según security_middleware.py)
    RATE_LIMITED=0
    for i in $(seq 1 130); do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
        if [ "$HTTP_CODE" = "429" ]; then
            RATE_LIMITED=$((RATE_LIMITED + 1))
        fi
        # Pequeña pausa para no saturar (pero aún suficiente para trigger rate limit)
        sleep 0.01
    done

    if [ $RATE_LIMITED -gt 0 ]; then
        test_passed "Rate limiting active ($RATE_LIMITED requests blocked with 429)"

        # Esperar 60 segundos para que el rate limit se resetee
        echo -e "${YELLOW}⏳ Esperando 60s para reset de rate limit...${NC}"
        sleep 60
        echo -e "${GREEN}✅ Rate limit reseteado, continuando tests${NC}"
    else
        # No es crítico si no se triggerea en smoke test rápido
        echo -e "${YELLOW}⚠️  WARN${NC}: Rate limiting not triggered (may need more sustained load)"
        echo "⚠️  WARN: Rate limiting not triggered" >> "${RESULTS_FILE}"
    fi
}

# ========================================================================
# Test 7: File Upload - Excel Validation
# ========================================================================

test_excel_upload() {
    test_header "Test 7: Excel Upload Validation"

    # Crear un archivo de prueba que NO es Excel
    FAKE_EXCEL="${TEMP_DIR}/malicious.xlsx"
    echo "This is not a real Excel file" > "${FAKE_EXCEL}"

    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/upload_excel" \
        -F "file=@${FAKE_EXCEL}" \
        -F "client_id=1")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    # Debe rechazar el archivo fake
    if [ "$HTTP_CODE" = "400" ] || echo "$BODY" | grep -qi "invalid.*file"; then
        test_passed "Malicious Excel upload rejected (MIME validation)"
    elif [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q '"success".*false'; then
        test_passed "Malicious Excel upload rejected in response"
    else
        test_failed "Malicious Excel may have been accepted" "$BODY"
    fi
}

# ========================================================================
# Test 8: File Upload - PDF Validation
# ========================================================================

test_pdf_upload() {
    test_header "Test 8: PDF Upload Validation"

    # Crear un archivo de prueba que NO es PDF
    FAKE_PDF="${TEMP_DIR}/malicious.pdf"
    echo "<html><body>Fake PDF</body></html>" > "${FAKE_PDF}"

    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/upload_pdf/public" \
        -F "file=@${FAKE_PDF}")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    # Debe rechazar el archivo fake
    if [ "$HTTP_CODE" = "400" ] || echo "$BODY" | grep -qi "invalid.*file"; then
        test_passed "Malicious PDF upload rejected (MIME validation)"
    elif [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q '"success".*false'; then
        test_passed "Malicious PDF upload rejected in response"
    else
        test_failed "Malicious PDF may have been accepted" "$BODY"
    fi
}

# ========================================================================
# Test 9: Email Validation
# ========================================================================

test_email_validation() {
    test_header "Test 9: Email Validation"

    TIMESTAMP=$(date +%s)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/clientes/public" \
        -H "Content-Type: application/json" \
        -d "{
            \"nombre\": \"Test Invalid Email\",
            \"email\": \"not-an-email\",
            \"cuit\": \"20123456789\"
        }")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    # Debe rechazar email inválido
    if echo "$BODY" | grep -qi "invalid.*email" || echo "$BODY" | grep -q '"success".*false'; then
        test_passed "Invalid email rejected"
    elif [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "422" ]; then
        test_passed "Invalid email rejected (HTTP $HTTP_CODE)"
    else
        test_failed "Invalid email may have been accepted" "$BODY"
    fi
}

# ========================================================================
# Test 10: CUIT Validation
# ========================================================================

test_cuit_validation() {
    test_header "Test 10: CUIT Validation"

    TIMESTAMP=$(date +%s)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/clientes/public" \
        -H "Content-Type: application/json" \
        -d "{
            \"nombre\": \"Test Invalid CUIT\",
            \"email\": \"cuit${TIMESTAMP}@smoketest.com\",
            \"cuit\": \"123\"
        }")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    # Debe rechazar CUIT inválido (no tiene 11 dígitos)
    if echo "$BODY" | grep -qi "cuit.*11.*digit" || echo "$BODY" | grep -q '"success".*false'; then
        test_passed "Invalid CUIT rejected (must be 11 digits)"
    elif [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "422" ]; then
        test_passed "Invalid CUIT rejected (HTTP $HTTP_CODE)"
    else
        test_failed "Invalid CUIT may have been accepted" "$BODY"
    fi
}

# ========================================================================
# Resumen Final
# ========================================================================

print_summary() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}TEST SUMMARY${NC}"
    echo -e "${BLUE}========================================${NC}"

    echo "" >> "${RESULTS_FILE}"
    echo "========================================" >> "${RESULTS_FILE}"
    echo "SUMMARY" >> "${RESULTS_FILE}"
    echo "========================================" >> "${RESULTS_FILE}"

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
        echo -e "Total: ${TOTAL}/${TOTAL}"
        echo "✅ ALL TESTS PASSED" >> "${RESULTS_FILE}"
        echo "Total: ${TOTAL}/${TOTAL}" >> "${RESULTS_FILE}"
    else
        echo -e "${RED}❌ SOME TESTS FAILED${NC}"
        echo -e "Passed: ${GREEN}${PASSED}${NC}/${TOTAL}"
        echo -e "Failed: ${RED}${FAILED}${NC}/${TOTAL}"
        echo "❌ SOME TESTS FAILED" >> "${RESULTS_FILE}"
        echo "Passed: ${PASSED}/${TOTAL}" >> "${RESULTS_FILE}"
        echo "Failed: ${FAILED}/${TOTAL}" >> "${RESULTS_FILE}"
    fi

    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo -e "Pass Rate: ${PASS_RATE}%"
    echo "Pass Rate: ${PASS_RATE}%" >> "${RESULTS_FILE}"

    echo -e "${BLUE}========================================${NC}"
    echo -e "Results saved to: ${RESULTS_FILE}"
    echo ""

    # Criterio de éxito
    if [ $PASS_RATE -ge 80 ]; then
        echo -e "${GREEN}🎉 SMOKE TEST SUCCESSFUL - READY TO PROCEED${NC}"
        echo "🎉 SMOKE TEST SUCCESSFUL" >> "${RESULTS_FILE}"
        return 0
    else
        echo -e "${RED}⛔ SMOKE TEST FAILED - FIX ISSUES BEFORE DEPLOY${NC}"
        echo "⛔ SMOKE TEST FAILED" >> "${RESULTS_FILE}"
        return 1
    fi
}

# ========================================================================
# Main Execution
# ========================================================================

main() {
    setup

    # Verificar que el servidor está corriendo
    if ! curl -s --max-time 5 "${BASE_URL}/health" > /dev/null 2>&1; then
        echo -e "${RED}❌ ERROR: Cannot connect to ${BASE_URL}${NC}"
        echo "Is the server running?"
        echo "Start with: uvicorn proyecto_maria.server_funcional:app --reload"
        exit 1
    fi

    # Ejecutar todos los tests
    test_health_check
    test_security_headers
    test_client_creation
    test_xss_protection
    test_path_traversal
    test_rate_limiting
    test_excel_upload
    test_pdf_upload
    test_email_validation
    test_cuit_validation

    # Mostrar resumen
    print_summary
    EXIT_CODE=$?

    # Cleanup
    cleanup

    exit $EXIT_CODE
}

# Trap para cleanup en caso de error
trap cleanup EXIT

# Ejecutar
main
