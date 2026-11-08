#!/usr/bin/env bash
# Smoke rápido: telemetría y su alias /api/session/state sin sesión, auth en by-cuit.
set -euo pipefail

BASE="${BASE_URL:-http://127.0.0.1:8000}"

say() { printf "\n==> %s\n" "$*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

say "Fricción / Wave 1 contra ${BASE}"

curl -sf "${BASE}/health" | grep -q '"database"' || fail "/health incompleto"

# Sin sesión sólo se guardan las acciones previas al login; el resto se rechaza.
rechaza_sin_sesion() {
  local r
  r=$(curl -s -X POST "${BASE}$1" -H 'Content-Type: application/json' -d "$2")
  echo "$r" | grep -qF '"ok":false,"detail":"Evento sin sesión no admitido"' \
    || fail "POST $1 sin sesión debería rechazarse, obtuvo: ${r}"
}

rechaza_sin_sesion /api/ui/event '{"action":"smoke_wave1","screen":"scripts","dry":true}'
rechaza_sin_sesion /api/session/state '{"action":"smoke_session_state_alias","screen":"scripts"}'

CODE=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/api/clientes/by-cuit/20123456789")
[ "$CODE" = "401" ] || fail "by-cuit debería exigir login (401), obtuvo ${CODE}"

say "OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido"
