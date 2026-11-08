#!/usr/bin/env bash
# Negativos de COBRO-MP-4: cada sabotaje deshace una regla de la marca del 503 de
# cancelar y tests/test_cobro_mp2.py (Mercado Pago simulado) tiene que fallar en el
# caso de esa regla; el de la migración lo mide cobro_mp4_postgres.py.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cobro_mp4.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y, para la migración, un
# Postgres 16 propio (con_pg16.sh): no toca tu copia ni datos compartidos, y nada
# sale a Mercado Pago. Sale con error si un sabotaje no encuentra su patrón o no
# pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo. Corre "$CORRER".
sabotaje() {
  local archivo="$1" nombre="$2" esperado="$3"; shift 3
  git checkout -q -- proyecto_maria/
  rm -f test.db
  if ! "$PY" - "$archivo" "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$("$CORRER")"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|FALLA|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

T=tests/test_cobro_mp2.py
M=proyecto_maria/main.py
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov --timeout=120 -p no:cacheprovider -W ignore "$T" -k "marca or concilia" 2>&1; }
correr_pg() {
  PY="$PY" timeout 300 scripts/testing/con_pg16.sh bash -c '"$0" scripts/testing/cobro_mp4_postgres.py "$BACKUP1A_PG_URL"' "$PY" 2>&1
}

rm -f test.db
git checkout -q -- proyecto_maria/
if ! correr >/dev/null || ! correr_pg >/dev/null; then
  echo "BASE  | $T o cobro_mp4_postgres.py ya está en rojo: no se puede medir"; exit 1
fi
echo "BASE  | en verde"

CORRER=correr
CONCILIA="FAILED $T::test_si_mp_cancelo_sin_confirmar_el_reintento_concilia"
SIN_MARCA="FAILED $T::test_un_miembro_sin_la_marca_no_concilia"
sabotaje $M "el 503 de cancelar no anota quién lo recibió" "$CONCILIA[abrio" \
  "            db_user.cancelar_sin_confirmar = cuenta.mp_preapproval_id
" ""
sabotaje $M "conciliar no borra la marca de la dueña" "$CONCILIA[duena" \
  "    db_user.cancelar_sin_confirmar = None
" ""
sabotaje $M "un miembro sin la marca concilia" "$SIN_MARCA[cancelada]" \
  "
                 and db_user.cancelar_sin_confirmar in {c.mp_preapproval_id for c in con_sid})" ")"
sabotaje $M "una marca de una suscripción que ya no está concilia" "$SIN_MARCA[marca_de_otra]" \
  "db_user.cancelar_sin_confirmar in {c.mp_preapproval_id for c in con_sid})" \
  "db_user.cancelar_sin_confirmar is not None)"
sabotaje $M "conciliar deja las marcas de las otras cuentas" \
  "FAILED $T::test_conciliar_borra_las_marcas_de_todo_el_estudio" \
  "cuenta.mp_preapproval_id = cuenta.cancelar_sin_confirmar = None" "cuenta.mp_preapproval_id = None"
sabotaje $M "la marca de otra cuenta del estudio concilia" \
  "FAILED $T::test_la_marca_de_otra_cuenta_no_concilia[abrio-miembro]" \
  "db_user.cancelar_sin_confirmar in {c.mp_preapproval_id for c in con_sid})" \
  "any(c.cancelar_sin_confirmar in {d.mp_preapproval_id for d in con_sid} for c in con_sid))"
sabotaje $M "cancelar empieza por la suscripción de quien pide" \
  "FAILED $T::test_el_reintento_que_falla_en_otra_deja_la_suya_para_volver_a_conciliar" \
  "key=lambda c: (paga[c], c is db_user)" "key=paga.get"

CORRER=correr_pg
sabotaje $M "el arranque no agrega la columna a una base que ya existe" \
  "FALLA | el arranque agrega cancelar_sin_confirmar" \
  '        ("cancelar_sin_confirmar", "VARCHAR(100)"),
' ""

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
