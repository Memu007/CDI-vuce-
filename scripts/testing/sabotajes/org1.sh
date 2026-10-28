#!/usr/bin/env bash
# Negativos de ORG-1 con la D40 (un email, una cuenta): cada sabotaje deshace
# una regla y tests/test_org1.py (SQLite) tiene que fallar por ese motivo. Con
# PG=<url de Postgres sin base> también scripts/testing/org1_postgres.py, en
# una base nueva por sabotaje que se borra al terminar.
#
# uso: PY=/ruta/al/venv/bin/python [PG=postgresql://cdi@127.0.0.1:55432] \
#      scripts/testing/sabotajes/org1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG="${PG:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0

sqlite() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov --timeout=120 -p no:randomly -p no:cacheprovider tests/test_org1.py 2>&1
}

postgres() {
  local base="org1sab_$$_$RANDOM" salida codigo
  psql "$PG/postgres" -qc "create database $base" >/dev/null || { echo "no se pudo crear la base"; return 2; }
  salida="$("$PY" scripts/testing/org1_postgres.py "$PG/$base" 2>&1)"; codigo=$?
  psql "$PG/postgres" -qc "drop database $base" >/dev/null
  grep -E "^(FALLA|fallas)" <<<"$salida"
  [ "$codigo" -eq 0 ] && grep -qx "fallas: 0" <<<"$salida"
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
      grep -E "^(FAILED|FALLA)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <nombre> <texto original> <texto saboteado> <rojo en SQLite> <rojo en Postgres>
sabotaje() {
  local nombre="$1" viejo="$2" nuevo="$3" en_sqlite="$4" en_pg="$5" salida codigo
  git checkout -q -- proyecto_maria/
  if ! aplicar proyecto_maria/main.py "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  salida="$(sqlite)"; codigo=$?
  juzgar "$nombre (SQLite)" "$salida" "$codigo" "FAILED tests/test_org1.py::$en_sqlite"
  if [ -n "$PG" ]; then
    salida="$(postgres)"; codigo=$?
    juzgar "$nombre (Postgres)" "$salida" "$codigo" "FALLA | $en_pg"
  fi
  git checkout -q -- proyecto_maria/
}

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! salida="$(sqlite)"; then
  echo "BASE  | test_org1.py ya está en rojo sin sabotaje: no se puede medir nada"
  grep -E "^FAILED|passed|failed" <<<"$salida"; exit 1
fi
if [ -n "$PG" ] && ! salida="$(postgres)"; then
  echo "BASE  | org1_postgres.py ya está en rojo sin sabotaje: no se puede medir nada"
  echo "$salida"; exit 1
fi
echo "BASE  | verde sin sabotaje en $SHA${PG:+ (SQLite y Postgres)}"

# Regla 1: invitar un email que ya tiene cuenta da 400, sea donde sea la cuenta.
sabotaje "la regla 1 sólo mira este estudio" \
  "select(User.username).where(func.lower(User.email) == clean_email)" \
  "select(User.username).where(func.lower(User.email) == clean_email, User.organization_id == org.id)" \
  "test_invitar_un_email_que_ya_tiene_cuenta_400_sin_ocupar_lugar[otro estudio]" \
  "invitar un email con cuenta otro estudio"
sabotaje "sin la regla 1" \
  "    if existing.first():
        raise HTTPException(
            status_code=400,
            detail=\"Ese email ya tiene una cuenta" \
  "    if False:
        raise HTTPException(
            status_code=400,
            detail=\"Ese email ya tiene una cuenta" \
  "test_invitar_un_email_que_ya_tiene_cuenta_400_sin_ocupar_lugar[este estudio]" \
  "invitar un email con cuenta este estudio"

# Regla 2: al registrarse con una, las otras pendientes de ese email en ese
# estudio quedan usadas.
sabotaje "sin la regla 2" \
  "func.lower(func.trim(Invitation.email)) == request.email)" \
  "func.lower(func.trim(Invitation.email)) == request.email + \"-x\")" \
  "test_el_sacado_no_vuelve_a_entrar_con_otra_invitacion_vieja" \
  "el sacado no vuelve a entrar con la segunda"
sabotaje "la regla 2 sin mayúsculas ni espacios" \
  "func.lower(func.trim(Invitation.email)) == request.email)" \
  "Invitation.email == request.email)" \
  "test_registrarse_usa_tambien_una_vieja_con_mayusculas_y_espacios" \
  "registrarse usa las otras del mismo email en ese estudio"
sabotaje "la regla 2 en todos los estudios" \
  ".where(Invitation.org_id == invite_org.id, Invitation.status == \"pending\"," \
  ".where(Invitation.status == \"pending\"," \
  "test_registrarse_con_una_invitacion_usa_las_otras_del_mismo_email" \
  "registrarse usa las otras del mismo email en ese estudio"

# El tope: una pendiente al email de un miembro no ocupa otro lugar.
sabotaje "el tope cuenta la pendiente al email de un miembro" \
  "    } - set(emails_miembros)" \
  "    }" \
  "test_una_pendiente_al_email_de_un_miembro_no_ocupa_lugar" \
  "una pendiente al email de un miembro no ocupa lugar"

echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
