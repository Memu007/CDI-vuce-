#!/usr/bin/env bash
# Negativos de OBSERVABILIDAD-1: cada sabotaje deshace una regla de la
# migración de `api_logs.owner_username` (se agrega sola al arrancar,
# nullable y sin tocar filas, con su índice sin duplicar, dos veces no hace
# nada ni pide el lock, si falla la app arranca igual y lo dice en el log,
# columna e índice se confirman cada uno por su lado y el log lo anuncia
# después) o de la métrica (guarda el molde de la ruta, no el camino) y
# tests/test_observabilidad1.py o scripts/testing/observabilidad1_arranque.py
# tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python [PG_URL=postgresql://cdi@127.0.0.1:55432/postgres] \
#        scripts/testing/sabotajes/observabilidad1.sh [SHA]
# PY necesita pytest, uvicorn y (con PG_URL) psycopg2. Sin PG_URL, los
# sabotajes que sólo se ven en Postgres salen como «NO CORRIDO».
# Trabaja en un worktree descartable con bases propias: no toca tu copia ni
# datos compartidos. Sale con error si un sabotaje no encuentra su patrón o
# no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG_URL="${PG_URL:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0
NO_CORRIDOS=0

pytest_o1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_observabilidad1.py 2>&1
}
arranque_sqlite() { "$PY" scripts/testing/observabilidad1_arranque.py 2>&1; }
arranque_pg() { "$PY" scripts/testing/observabilidad1_arranque.py "$PG_URL" 2>&1; }

# aplicar <archivo> <viejo> <nuevo> [<viejo> <nuevo>]...: cada patrón tiene
# que estar una sola vez.
aplicar() {
  "$PY" - "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
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
      grep -E "^(FAILED|E |FALLA)" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <corredor> <nombre> <n pares> <viejo> <nuevo> [...] <lo que el rojo tiene que decir>...
# corredor: pytest_o1, arranque_sqlite o arranque_pg.
sabotaje() {
  local corredor="$1" nombre="$2" n="$3"; shift 3
  local pares=("${@:1:$((n*2))}"); shift $((n*2))
  if [ "$corredor" = arranque_pg ] && [ -z "$PG_URL" ]; then
    echo "NO CORRIDO | $nombre: necesita PG_URL"; NO_CORRIDOS=$((NO_CORRIDOS+1)); return
  fi
  git checkout -q -- proyecto_maria/
  if ! aplicar "$M" "${pares[@]}"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$($corredor)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
T=tests/test_observabilidad1.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
for corredor in pytest_o1 arranque_sqlite ${PG_URL:+arranque_pg}; do
  if ! $corredor >"$TMPD/base.log"; then
    echo "BASE  | $corredor ya está en rojo sin sabotaje: no se puede medir nada"
    grep -E "^(FAILED|FALLA)" "$TMPD/base.log"; exit 1
  fi
done

# --- se agrega sola al arrancar
sabotaje arranque_sqlite "el arranque no llama a la migración" 1 \
  $'    await _migrate_add_api_logs_owner_column()\n' '' \
  "FALLA | al arrancar la columna existe" "FALLA | sin «Error logging metrics» en el log"
sabotaje pytest_o1 "no agrega la columna" 1 \
  $'"ALTER TABLE api_logs ADD COLUMN owner_username VARCHAR(50)"\n                    if IS_SQLITE else' \
  $'"SELECT 1"\n                    if IS_SQLITE else' \
  "FAILED $T::test_base_vieja_recibe_columna_nullable_con_indice_y_conserva_filas" "la columna tiene que quedar VARCHAR(50)"
sabotaje arranque_pg "en Postgres no agrega la columna" 1 \
  '"ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS owner_username VARCHAR(50)"' '"SELECT 1"' \
  "FALLA | al arrancar la columna existe" "FALLA | suelta la tabla, el próximo arranque la agrega"

# --- nullable, sin tocar filas
sabotaje pytest_o1 "la columna es NOT NULL con un dueño por defecto" 1 \
  '"ALTER TABLE api_logs ADD COLUMN owner_username VARCHAR(50)"' \
  $'"ALTER TABLE api_logs ADD COLUMN owner_username VARCHAR(50) NOT NULL DEFAULT \'demo\'"' \
  "FAILED $T::test_base_vieja_recibe_columna_nullable_con_indice_y_conserva_filas" "('VARCHAR(50)', 1, \"'demo'\")"
sabotaje arranque_pg "en Postgres la columna tiene un dueño por defecto" 1 \
  '"ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS owner_username VARCHAR(50)"' \
  $'"ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS owner_username VARCHAR(50) DEFAULT \'demo\'"' \
  "FALLA | al arrancar la columna existe, VARCHAR(50), nullable, sin default" "FALLA | y sin dueño inventado"

# --- con índice, sin duplicarlo
sabotaje pytest_o1 "no crea el índice" 1 \
  $'            if not tiene_indice:\n                await ddl(conn,' \
  $'            if False:\n                await ddl(conn,' \
  "FAILED $T::test_base_vieja_recibe_columna_nullable_con_indice_y_conserva_filas" "tiene que quedar un índice sobre owner_username: []" \
  "FAILED $T::test_columna_sin_indice_recibe_el_indice"
sabotaje pytest_o1 "busca el índice por nombre y no por columna" 1 \
  'if primera and primera[0][2] == "owner_username":' 'if nombre == "ix_api_logs_owner_username":' \
  "FAILED $T::test_indice_del_script_viejo_con_otro_nombre_no_se_duplica" "duplicó el índice: ['ix_api_logs_owner', 'ix_api_logs_owner_username']"
sabotaje arranque_pg "en Postgres no crea el índice" 1 \
  $'                tiene_indice = res.first() is not None' $'                tiene_indice = True' \
  "FALLA | con un índice: []"

# --- dos veces no hace nada (ni pide el lock)
sabotaje pytest_o1 "agrega la columna aunque ya esté" 1 \
  'agrega_columna = "owner_username" not in columnas' 'agrega_columna = True' \
  "FAILED $T::test_columna_sin_indice_recibe_el_indice"
sabotaje arranque_pg "en Postgres pide el lock aunque la columna ya esté" 1 \
  'agrega_columna = "owner_username" not in columnas' 'agrega_columna = True' \
  "FALLA | ni falla con una lectura abierta sobre la tabla"
sabotaje pytest_o1 "sin tabla no se va antes" 1 \
  $'            if not columnas:\n                # Base vacía: init_db ya la crea con la columna y el índice.\n                return\n' '' \
  "FAILED $T::test_sin_tabla_no_crea_nada_ni_se_queja"

# --- si falla, la app arranca igual y lo dice en el log
sabotaje pytest_o1 "la falla se propaga" 1 \
  $'"la app arranca igual, pero las métricas no se graban hasta que exista"\n        )\n' \
  $'"la app arranca igual, pero las métricas no se graban hasta que exista"\n        )\n        raise\n' \
  "FAILED $T::test_si_falla_no_levanta_y_deja_el_motivo_en_el_log" "Cannot add a column to a view"
sabotaje arranque_sqlite "la falla frena el arranque" 1 \
  $'"la app arranca igual, pero las métricas no se graban hasta que exista"\n        )\n' \
  $'"la app arranca igual, pero las métricas no se graban hasta que exista"\n        )\n        raise\n' \
  "FALLA | la app arranca igual"
sabotaje pytest_o1 "la falla no va al log" 1 \
  $'        logging.exception(\n            "[OBSERVABILIDAD-1]' $'        (lambda *a: None)(\n            "[OBSERVABILIDAD-1]' \
  "FAILED $T::test_si_falla_no_levanta_y_deja_el_motivo_en_el_log" "la falla no quedó en el log"
sabotaje pytest_o1 "la falla va al log sin el motivo" 1 \
  $'        logging.exception(\n            "[OBSERVABILIDAD-1]' $'        logging.error(\n            "[OBSERVABILIDAD-1]' \
  "FAILED $T::test_si_falla_no_levanta_y_deja_el_motivo_en_el_log" "el log tiene que traer el motivo"
sabotaje arranque_pg "en Postgres espera el lock sin límite" 1 \
  $'            await conn.exec_driver_sql("SET LOCAL lock_timeout = \'5s\'")' $'            pass' \
  "FALLA | la app arranca igual ("
sabotaje arranque_pg "en Postgres el índice espera el lock sin límite" 1 \
  $'                await ddl(conn,\n                    "CREATE INDEX' $'                await conn.exec_driver_sql(\n                    "CREATE INDEX' \
  "FALLA | la app arranca igual con la columna ya puesta"

# --- columna e índice se confirman por separado y el log lo dice después
sabotaje arranque_pg "columna e índice en una sola transacción" 3 \
  $'        async with engine.begin() as conn:\n            if IS_SQLITE:\n                res = await conn.exec_driver_sql("PRAGMA table_info' \
  $'        conn = await engine.connect()\n        await conn.begin()\n        if True:\n            if IS_SQLITE:\n                res = await conn.exec_driver_sql("PRAGMA table_info' \
  $'        async with engine.begin() as conn:\n            if IS_SQLITE:\n                res = await conn.exec_driver_sql("PRAGMA index_list' \
  $'        if True:\n            if IS_SQLITE:\n                res = await conn.exec_driver_sql("PRAGMA index_list' \
  $'        if not tiene_indice:\n            print(' $'        await conn.commit()\n        if not tiene_indice:\n            print(' \
  "FALLA | la columna queda: None"
sabotaje arranque_pg "anuncia la columna antes de confirmarla" 1 \
  $'VARCHAR(50)"\n                )\n        if agrega_columna:' \
  $'VARCHAR(50)"\n                )\n                print("✅ Migracion: agregada columna api_logs.owner_username")\n        if False:' \
  "FALLA | y el log no dice que la agregó"
sabotaje arranque_pg "anuncia el índice antes de confirmarlo" 1 \
  $'"ON api_logs (owner_username)"\n                )\n        if not tiene_indice:' \
  $'"ON api_logs (owner_username)"\n                )\n                print("✅ Migracion: agregado indice ix_api_logs_owner_username")\n        if False:' \
  "FALLA | y el log no lo anuncia"

# --- la métrica guarda el molde de la ruta
sabotaje pytest_o1 "la métrica guarda el camino crudo" 1 \
  'getattr(ruta, "path_format", None) or "<sin ruta>"' 'str(request.url.path)' \
  "FAILED $T::test_la_metrica_guarda_el_molde_de_la_ruta_y_no_el_camino" "la métrica guardó otra cosa que el molde"
sabotaje pytest_o1 "un camino sin ruta guarda el camino" 1 \
  'getattr(ruta, "path_format", None) or "<sin ruta>"' 'getattr(ruta, "path_format", None) or str(request.url.path)' \
  "FAILED $T::test_la_metrica_guarda_el_molde_de_la_ruta_y_no_el_camino" "/no-existe-zq9"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS; no corridos: $NO_CORRIDOS"
[ "$FALLAS" -eq 0 ]
