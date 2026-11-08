#!/usr/bin/env bash
# Negativos de ENTORNO-4: cada sabotaje deja arrancar sin FRONTEND_URL fuera de
# desarrollo o devuelve al cobro su propia URL con localhost, y
# tests/test_entorno1.py tiene que fallar por esa puerta.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entorno4.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros.
source "$(dirname "$0")/_entorno_comun.sh"
B=proyecto_maria/services/billing_service.py

sabotaje $M "arranca sin FRONTEND_URL fuera de desarrollo" \
  $'\nget_frontend_url()\n' $'\n' \
  "$C[arranca_sin_frontend_url]" "arranca_sin_frontend_url no queda cerrada: {None: 'abierta'"
sabotaje $B "el cobro vuelve a su URL con localhost" \
  $'from proyecto_maria.config import get_frontend_url\n' \
  $'def get_frontend_url():\n    return os.environ.get("FRONTEND_URL", "").rstrip("/") or "http://127.0.0.1:8000"\n' \
  "$C[frontend_en_localhost]" "frontend_en_localhost no queda cerrada: {None: 'sin medir'"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
