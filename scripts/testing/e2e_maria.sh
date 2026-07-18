#!/usr/bin/env bash
# E2E de navegador del recorrido crítico MARIA.
# Levanta una aplicación con base, archivos y artefactos aislados en /tmp.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$ROOT_DIR"

TMP_BASE="${TMPDIR:-/tmp}"
RUN_DIR="$(mktemp -d "$TMP_BASE/cdi-maria-e2e.XXXXXX")"
ARTIFACTS_DIR="${E2E_ARTIFACTS:-$RUN_DIR/artifacts}"
SERVER_PID=""

cleanup() {
    local status=$?
    if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi

    if [[ "$status" -eq 0 || "$ARTIFACTS_DIR" != "$RUN_DIR/artifacts" ]]; then
        rm -rf "$RUN_DIR"
    else
        echo "E2E falló. Evidencia preservada en: $ARTIFACTS_DIR" >&2
    fi
}
trap cleanup EXIT

if [[ ! -d "$ROOT_DIR/config/node_modules/puppeteer" ]]; then
    npm ci --prefix "$ROOT_DIR/config"
fi

mkdir -p "$ARTIFACTS_DIR"
python3 scripts/testing/create_e2e_maria_fixture.py "$RUN_DIR/maria_e2e.xlsx"

E2E_PORT="$(python3 -c 'import socket; sock = socket.socket(); sock.bind(("127.0.0.1", 0)); print(sock.getsockname()[1]); sock.close()')"
BASE_URL="http://127.0.0.1:$E2E_PORT"

PYTHONPATH=. \
DATABASE_URL="sqlite+aiosqlite:///$RUN_DIR/cdi_e2e.db" \
CDI_DATA_DIR="$RUN_DIR/data" \
ENVIRONMENT=testing \
EMAIL_VERIFICATION_REQUIRED=false \
VUCE_CI_ENABLED=false \
VUCE_MODE=api \
GEMINI_API_KEY= \
MP_ACCESS_TOKEN= \
python3 -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$E2E_PORT" \
    >"$RUN_DIR/server.log" 2>&1 &
SERVER_PID=$!

if ! curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
    --retry-max-time 45 "$BASE_URL/health" >/dev/null; then
    cat "$RUN_DIR/server.log" >&2 || true
    exit 1
fi

E2E_BASE_URL="$BASE_URL" \
E2E_FIXTURE="$RUN_DIR/maria_e2e.xlsx" \
E2E_ARTIFACTS="$ARTIFACTS_DIR" \
npm --prefix "$ROOT_DIR/config" run test:e2e:maria
