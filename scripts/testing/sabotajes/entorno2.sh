#!/usr/bin/env bash
# Negativos de ENTORNO-2: cada sabotaje vuelve a dejar un control de producción
# como en desarrollo con ENVIRONMENT ausente o desconocido, y
# tests/test_entorno1.py tiene que fallar por ese control. El lugar único y el
# contrapunto los cubre scripts/testing/sabotajes/entorno1.sh.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entorno2.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
source "$(dirname "$0")/_entorno_comun.sh"
PROD='os.getenv("ENVIRONMENT", "development") == "production"'

sabotaje $M "la bandera abre el cobro simulado fuera de desarrollo" \
  $'    if not _es_desarrollo():\n        raise HTTPException(status_code=404, detail="Not Found")\n\n    result = await db.execute(select(User).where(User.username == user["username"]))' \
  $'    if not _es_desarrollo() and os.getenv("ENABLE_SIMULATE_CHARGE", "false").lower() != "true":\n        raise HTTPException(status_code=404, detail="Not Found")\n\n    result = await db.execute(select(User).where(User.username == user["username"]))' \
  "$C[cobro_simulado]"
sabotaje $M "CSRF sólo avisa salvo en producción" \
  'default = "false" if _es_desarrollo() else "true"' 'default = "true" if IS_PRODUCTION else "false"' \
  "$C[csrf_que_solo_avisa]" "csrf_que_solo_avisa $VIEJO"
sabotaje $M "cookie de sesión sin Secure salvo en producción" \
  'secure=not _es_desarrollo(), samesite="strict",' 'secure=IS_PRODUCTION, samesite="strict",' \
  "$C[cookies_sin_secure]"
sabotaje $M "cookie CSRF sin Secure salvo en producción" \
  $'        secure=not _es_desarrollo(),\n        samesite="strict",' $'        secure=IS_PRODUCTION,\n        samesite="strict",' \
  "$C[cookies_sin_secure]"
sabotaje $M "openapi abierto salvo en producción" \
  'openapi_url="/openapi.json" if _es_desarrollo() else None' 'openapi_url=None if IS_PRODUCTION else "/openapi.json"' \
  "$C[docs_y_openapi]"
sabotaje $M "docs, redoc y openapi abiertos salvo en producción" \
  'docs_url="/docs" if _es_desarrollo() else None,
    redoc_url="/redoc" if _es_desarrollo() else None,
    openapi_url="/openapi.json" if _es_desarrollo() else None' \
  'docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json"' \
  "$C[docs_y_openapi]" "docs_y_openapi $VIEJO"
sabotaje proyecto_maria/database/connection.py "SQLite sin DATABASE_URL salvo en producción" \
  '    if not es_desarrollo():' "    if $PROD:" \
  "$C[sqlite_sin_database_url]" "sqlite_sin_database_url $VIEJO"
sabotaje proyecto_maria/core/vuce_connector.py "VUCE simulado salvo en producción" \
  '            if not es_desarrollo():' "            if $PROD:" \
  "$C[vuce_simulado]" "vuce_simulado $VIEJO"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
