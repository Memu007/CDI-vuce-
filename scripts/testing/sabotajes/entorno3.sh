#!/usr/bin/env bash
# Negativos de ENTORNO-3: cada sabotaje vuelve a mirar sólo "production" en
# FRONTEND_URL, ALLOWED_ORIGINS, HSTS o el pase de 127.0.0.1, y
# tests/test_entorno1.py tiene que fallar por esa puerta.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entorno3.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros.
source "$(dirname "$0")/_entorno_comun.sh"
PROD='os.getenv("ENVIRONMENT", "development") == "production"'
SM=proyecto_maria/security/security_middleware.py

sabotaje $M "el link de los emails cae a localhost salvo en producción" \
  $'    if not _es_desarrollo():\n        # Fail fast' $'    if IS_PRODUCTION:\n        # Fail fast' \
  "$C[frontend_en_localhost]" "frontend_en_localhost $VIEJO"
sabotaje $M "sin ALLOWED_ORIGINS arranca salvo en producción" \
  'elif not _es_desarrollo():' 'elif IS_PRODUCTION:' \
  "$C[origenes_de_localhost]" "origenes_de_localhost $VIEJO"
sabotaje $SM "HSTS sólo en producción" \
  'if not es_desarrollo() or os.getenv("ENABLE_HSTS"' "if $PROD or os.getenv(\"ENABLE_HSTS\"" \
  "$C[sin_hsts]" "sin_hsts $VIEJO"
sabotaje $SM "127.0.0.1 sin límite salvo en producción" \
  'if es_desarrollo() and client_ip' "if not $PROD and client_ip" \
  "$C[sin_limite_desde_127]" "sin_limite_desde_127 $VIEJO"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
