#!/usr/bin/env bash
# Genera proyecto_maria/static/v2/media/cdi-presentacion.mp4 (y su póster) con
# pantallas reales de la app: levanta una instancia aislada en /tmp, graba el
# recorrido con Playwright y compone el video con Chromium + ffmpeg.
# Requiere: python3 con requirements.txt (PYTHON=... para elegir intérprete),
# node con `playwright` resoluble (NODE_PATH si hace falta) y ffmpeg.
set -euo pipefail
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$ROOT_DIR"
PYTHON="${PYTHON:-python3}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/cdi-video.XXXXXX")"
OUT_MP4="${OUT_MP4:-$ROOT_DIR/proyecto_maria/static/v2/media/cdi-presentacion.mp4}"
SERVER_PID=""
cleanup() { [[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null || true; [[ "${KEEP_WORK:-0}" == 1 ]] || rm -rf "$WORK"; }
trap cleanup EXIT

"$PYTHON" scripts/video/make_fixture.py "$WORK/factura_proveedor.xlsx" "$WORK/clientes.csv"
PORT="$("$PYTHON" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
PYTHONPATH=. DATABASE_URL="sqlite+aiosqlite:///$WORK/cdi_video.db" CDI_DATA_DIR="$WORK/data" \
ENVIRONMENT=testing EMAIL_VERIFICATION_REQUIRED=false VUCE_CI_ENABLED=false VUCE_MODE=api GEMINI_API_KEY= MP_ACCESS_TOKEN= \
"$PYTHON" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PORT" >"$WORK/server.log" 2>&1 &
SERVER_PID=$!
curl --fail --silent --retry 40 --retry-connrefused --retry-delay 1 --retry-max-time 90 "http://127.0.0.1:$PORT/health" >/dev/null

BASE_URL="http://127.0.0.1:$PORT" FIXTURE="$WORK/factura_proveedor.xlsx" CLIENTES_CSV="$WORK/clientes.csv" OUT="$WORK/out" node scripts/video/capture.js
"$PYTHON" scripts/video/cut_clips.py "$WORK/out" "$WORK/clips"
mkdir -p "$(dirname "$OUT_MP4")"
WORK="$WORK" OUT_MP4="$OUT_MP4" node scripts/video/render.js
ffprobe -v error -show_entries format=duration,size -of compact "$OUT_MP4"
