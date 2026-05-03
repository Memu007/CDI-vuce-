#!/usr/bin/env bash
set -euo pipefail

BASE=${BASE:-http://127.0.0.1:8001}

say() { printf "\n==> %s\n" "$*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

say "Smoke test contra ${BASE}"

say "1) /health"
H=$(curl -s "${BASE}/health") || fail "/health no responde"
echo "$H" | grep -q '"status"' || fail "Respuesta inválida de /health"

say "2) POST /validate_items/ (comas/puntos)"
V=$(curl -s -X POST "${BASE}/validate_items/" -H 'Content-Type: application/json' -d '{
  "items":[{"pieza":"84713010","descripcion":"Laptop","origen":"argentina","cantidad":"2,5","valor_unitario":"1.000,50","peso_unitario":"1,25"}]
}')
echo "$V" | grep -q '"success"\s*:\s*true' || fail "Validación no fue success=true"
echo "$V" | grep -Eq '"valid_count"\s*:\s*1' || fail "Validación no contó 1 válido"

say "3) POST /process_operation/ (genera Excel)"
P=$(curl -s -X POST "${BASE}/process_operation/" -H 'Content-Type: application/json' -d '{
  "operation_id":"API-REAL-001",
  "items":[{"pieza":"84713010","descripcion":"Laptop","origen":"CN","cantidad":2,"valor_unitario":800,"peso_unitario":2.2}]
}')
echo "$P" | grep -q '"success"\s*:\s*true' || fail "Procesamiento no fue success=true"
echo "$P" | grep -q '"filename"' || fail "Procesamiento no devolvió filename"

say "4) GET /generated/ y descarga del último"
G=$(curl -s "${BASE}/generated/")
echo "$G" | grep -q '"success"\s*:\s*true' || fail "/generated/ no fue success=true"
LAST=$(echo "$G" | jq -r .last_filename)
if [ -z "$LAST" ]; then fail "No hay last_filename en /generated/"; fi
curl -s -o /tmp/avg_smoke.xlsx "${BASE}/download/${LAST}" || fail "No se pudo descargar último archivo"
[ -s /tmp/avg_smoke.xlsx ] || fail "Archivo descargado vacío"

say "5) Negativos útiles"
CODE=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/download/NO_EXISTE.xlsx")
[ "$CODE" = "404" ] || fail "Descarga inexistente no devolvió 404"
BAD=$(curl -s -X POST "${BASE}/process_operation/" -H 'Content-Type: application/json' -d '{"operation_id": "X", "items": [invalid}')
echo "$BAD" | grep -q '"success"\s*:\s*false' || fail "JSON inválido no devolvió success=false"

say "6) POST /ncm/suggest (match esperado: laptop -> 84713010)"
S1=$(curl -s -X POST "${BASE}/ncm/suggest" -H 'Content-Type: application/json' -d '{
  "descripcion": "Laptop portable de 14 pulgadas"
}')
echo "$S1" | grep -q '"success"\s*:\s*true' || fail "/ncm/suggest no fue success=true"
echo "$S1" | grep -q '84713010' || echo "[WARN] No se encontró 84713010 (puede faltar RapidFuzz, se permite continuar)"

say "7) POST /ncm/suggest (sin match claro)"
S2=$(curl -s -X POST "${BASE}/ncm/suggest" -H 'Content-Type: application/json' -d '{
  "descripcion": "Producto desconocido XYZ"
}')
echo "$S2" | grep -q '"success"\s*:\s*true' || fail "/ncm/suggest (desconocido) no fue success=true"

say "8) GET /ncm/info/84713010"
INFO=$(curl -s "${BASE}/ncm/info/84713010")
echo "$INFO" | grep -q '"success"\s*:\s*true' || fail "/ncm/info no fue success=true"

say "9) GET /afip/auth/test (mock)"
A=$(curl -s "${BASE}/afip/auth/test")
echo "$A" | grep -q '"success"\s*:\s*true' || fail "/afip/auth/test no fue success=true"

say "10) POST /afip/cdc/constatar (mock)"
CDC=$(curl -s -X POST "${BASE}/afip/cdc/constatar" -H 'Content-Type: application/json' -d '{"cuit":"20301234567","numero":"ABC123"}')
echo "$CDC" | grep -q '"success"\s*:\s*true' || fail "/afip/cdc/constatar no fue success=true"

say "Smoke OK ✅"

