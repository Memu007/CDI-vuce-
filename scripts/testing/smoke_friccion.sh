#!/usr/bin/env bash
# Smoke rápido: telemetría, alias /api/session/state, auth en by-cuit.
set -euo pipefail

BASE="${BASE_URL:-http://127.0.0.1:8000}"

say() { printf "\n==> %s\n" "$*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

say "Fricción / Wave 1 contra ${BASE}"

curl -sf "${BASE}/health" | grep -q '"database"' || fail "/health incompleto"

E=$(curl -s -X POST "${BASE}/api/ui/event" \
  -H 'Content-Type: application/json' \
  -d '{"action":"smoke_wave1","screen":"scripts","dry":true}')
echo "$E" | grep -q '"ok":true' || fail "POST /api/ui/event"

S=$(curl -s -X POST "${BASE}/api/session/state" \
  -H 'Content-Type: application/json' \
  -d '{"action":"smoke_session_state_alias","screen":"scripts"}')
echo "$S" | grep -q '"ok":true' || fail "POST /api/session/state (alias)"

CODE=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/api/clientes/by-cuit/20123456789")
[ "$CODE" = "401" ] || fail "by-cuit debería exigir login (401), obtuvo ${CODE}"

say "OK · telemetría + alias session/state + by-cuit protegido"
