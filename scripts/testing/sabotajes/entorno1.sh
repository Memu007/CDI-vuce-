#!/usr/bin/env bash
# Negativos de ENTORNO-1: cada sabotaje vuelve a abrir una puerta de desarrollo
# con ENVIRONMENT ausente o desconocido, y tests/test_entorno1.py tiene que
# fallar por esa puerta. El último cierra todas en desarrollo y tiene que
# fallar el contrapunto.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entorno1.sh [SHA]
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
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
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
VIEJO="ENVIRONMENT en [None, '', 'prod', 'staging', 'Development', ' development', 'TESTING']"

if ! pytest_e1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi

# Cada puerta vuelve a la condición vieja: abierta salvo con «production».
sabotaje $M "usuarios demo salvo en producción" \
  $'            if not _es_desarrollo():\n                demo_users = []' \
  $'            if IS_PRODUCTION:\n                demo_users = []' \
  "$C[demo]" "demo abre con $VIEJO"
sabotaje $M "login con la contraseña guardada salvo en producción" \
  'if not is_valid and _es_desarrollo() and stored_password == password:' \
  'if not is_valid and not IS_PRODUCTION and stored_password == password:' \
  "$C[login_con_lo_guardado]" "login_con_lo_guardado abre con $VIEJO"
sabotaje $M "webhook sin secreto acepta salvo en producción" \
  $'    if not MP_WEBHOOK_SECRET:\n        return _es_desarrollo()' \
  $'    if not MP_WEBHOOK_SECRET:\n        return not IS_PRODUCTION' \
  "$C[webhook_sin_secreto]" "webhook_sin_secreto abre con $VIEJO"
sabotaje $M "link de reset por consola salvo en producción" \
  $'        if not _es_desarrollo():\n            logging.warning("SMTP no configurado' \
  $'        if IS_PRODUCTION:\n            logging.warning("SMTP no configurado' \
  "$C[link_de_reset_en_stdout]" "link_de_reset_en_stdout abre con $VIEJO"
sabotaje $M "cobro simulado salvo en producción" \
  'if not _es_desarrollo() and os.getenv("ENABLE_SIMULATE_CHARGE"' \
  'if IS_PRODUCTION and os.getenv("ENABLE_SIMULATE_CHARGE"' \
  "$C[cobro_simulado]" "cobro_simulado abre con $VIEJO"

# El lugar único: sin mirar mayúsculas ni espacios, o con un valor más.
sabotaje $M "desarrollo sin mirar mayúsculas ni espacios" \
  'return os.getenv("ENVIRONMENT") in ("development", "test", "testing")' \
  'return (os.getenv("ENVIRONMENT") or "").strip().lower() in ("development", "test", "testing")' \
  "$C[demo]" "$C[cobro_simulado]" "ENVIRONMENT en ['Development', ' development', 'TESTING']"
sabotaje $M "staging cuenta como desarrollo" \
  'in ("development", "test", "testing")' 'in ("development", "test", "testing", "staging")' \
  "$C[webhook_sin_secreto]" "ENVIRONMENT en ['staging']"
sabotaje $M "variable ausente cuenta como desarrollo" \
  'return os.getenv("ENVIRONMENT") in' 'return os.getenv("ENVIRONMENT", "development") in' \
  "$C[login_con_lo_guardado]" "ENVIRONMENT en [None]"

# Contrapunto: si las puertas no abren en ningún lado, la prueba lo ve.
sabotaje $M "ninguna puerta abre ni en desarrollo" \
  'return os.getenv("ENVIRONMENT") in ("development", "test", "testing")' 'return False' \
  "FAILED $T::test_puerta_abierta_en_desarrollo[demo]" \
  "FAILED $T::test_puerta_abierta_en_desarrollo[cobro_simulado]" \
  "demo no abre con ENVIRONMENT en ['development', 'test', 'testing']"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
