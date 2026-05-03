#!/usr/bin/env bash
set -euo pipefail
export DATA_DIR=${DATA_DIR:-data}
export PYTHONPATH=${PYTHONPATH:-$(pwd)}
uvicorn main:app --host 127.0.0.1 --port 8001 --reload


