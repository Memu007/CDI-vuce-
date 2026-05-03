#!/usr/bin/env bash
set -euo pipefail
export DATA_DIR=${DATA_DIR:-data}
HOST=${UVICORN_HOST:-0.0.0.0}
PORT=${UVICORN_PORT:-8001}
RELOAD=${UVICORN_RELOAD:-false}
if [ "$RELOAD" = "true" ]; then
  uvicorn main:app --host "$HOST" --port "$PORT" --reload
else
  uvicorn main:app --host "$HOST" --port "$PORT"
fi


