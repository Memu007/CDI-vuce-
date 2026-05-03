#!/usr/bin/env bash
set -euo pipefail

LOG_DIR=${LOG_DIR:-data/logs}
FILE=${1:-app.log}
MAX_SIZE=${MAX_SIZE:-5242880} # 5 MB

mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$FILE"

if [ ! -f "$LOG" ]; then
  echo "No existe $LOG, nada para rotar"
  exit 0
fi

# Obtener tamaño (BSD/macOS y GNU/Linux)
SIZE=$( (stat -f%z "$LOG" 2>/dev/null) || (stat -c%s "$LOG" 2>/dev/null) || echo 0 )

if [ "$SIZE" -ge "$MAX_SIZE" ]; then
  TS=$(date +%Y%m%d_%H%M%S)
  NEW_FILE="${FILE%.log}_$TS.log"
  mv "$LOG" "$LOG_DIR/$NEW_FILE"
  : > "$LOG"
  echo "Rotado: $FILE -> $NEW_FILE"
else
  echo "Sin rotar: tamaño $SIZE < max $MAX_SIZE"
fi


