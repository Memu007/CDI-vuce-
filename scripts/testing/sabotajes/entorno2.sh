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
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT" || exit 2
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
# Clave propia: el contrapunto cierra desarrollo y sin ella pytest no llega a importar la app.
export JWT_SECRET_KEY=clave-larga-de-cuarenta-y-dos-caracteres-para-sabotaje
FALLAS=0

pytest_e1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_entorno1.py 2>&1
}

aplicar() {
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

# juzgar <nombre> <salida> <código> <lo que el rojo tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3"; shift 3
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^(FAILED|E )" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_e1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
T=tests/test_entorno1.py
C="FAILED $T::test_puerta_cerrada_fuera_de_desarrollo"
VIEJO="no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}"
PROD='os.getenv("ENVIRONMENT", "development") == "production"'

if ! pytest_e1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^(FAILED|ERROR|E )" "$TMPD/base.log" | head -8; exit 1
fi

sabotaje $M "la bandera abre el cobro simulado fuera de desarrollo" \
  $'    if not _es_desarrollo():\n        raise HTTPException(status_code=404, detail="Not Found")\n\n    result = await db.execute(select(User).where(User.username == user["username"]))' \
  $'    if not _es_desarrollo() and os.getenv("ENABLE_SIMULATE_CHARGE", "false").lower() != "true":\n        raise HTTPException(status_code=404, detail="Not Found")\n\n    result = await db.execute(select(User).where(User.username == user["username"]))' \
  "$C[cobro_simulado_con_bandera]"
sabotaje $M "CSRF sólo avisa salvo en producción" \
  'default = "false" if _es_desarrollo() else "true"' 'default = "true" if IS_PRODUCTION else "false"' \
  "$C[csrf_que_sólo_avisa]" "csrf_que_sólo_avisa $VIEJO"
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
