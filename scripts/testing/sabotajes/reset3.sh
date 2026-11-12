#!/usr/bin/env bash
# Negativos de RESET-3: cada sabotaje afloja el tope de pedidos de reset por
# cuenta (lo saca, lo ata a la IP, lo mete entre las claves de la IP, lo sube,
# lo cuenta tarde o le cambia la ventana) y el caso tiene que fallar por ese motivo. Con PG_URL (un Postgres
# local y descartable), también que contar antes de trabar la cuenta no
# suelte la traba, contra scripts/testing/reset1_postgres.py.
#
# uso: PY=/ruta/al/venv/bin/python [PG_URL=postgresql://cdi@127.0.0.1:55432/postgres] \
#        scripts/testing/sabotajes/reset3.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="$(command -v "${PY:-python}")" || exit 2
PG_URL="${PG_URL:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0
T=tests/test_abuso1.py::test_tres_por_hora_por_cuenta_aunque_cambie_la_ip[reset]

casos_sqlite() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_abuso1.py 2>&1
}
caso_pg() { "$PY" -I scripts/testing/reset1_postgres.py "$PG_URL" 2>&1; }
CORRE=casos_sqlite

# aplicar <archivo> <viejo> <nuevo> [<ancla> <lo que va detrás del ancla>]
aplicar() {
  "$PY" - "$@" <<'PYEOF'
import sys
p, *pares = sys.argv[1:]; s = open(p, encoding="utf-8").read()
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
# Con MOVER=(<ancla> <texto>) además pone <texto> detrás de <ancla>. Corre la prueba de $CORRE.
MOVER=()
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo" "${MOVER[@]}"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$($CORRE)"; codigo=$?
  git checkout -q -- proyecto_maria/
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

# Sin sabotaje, verde: si no, ningún rojo de abajo distingue nada.
salida="$(casos_sqlite)" || { echo "BASE  | los casos no pasan sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | $(tail -1 <<<"$salida")"

M=proyecto_maria/main.py
TOPE='    if user and await _tope_por_cuenta(db, f"reset-cuenta:{user.username}"):
        return mensaje
'
TOKEN='    db.add(reset_token)
    await db.commit()
'
TRABA='User.username == user.username, User.email == user.email).with_for_update())).scalars().first()
'
MAIL=("FAILED $T" "AssertionError: el cuarto pedido de la hora mandó el mail")

sabotaje $M "sin el tope por cuenta" "$TOPE" '' "${MAIL[@]}"
sabotaje $M "el tope por cuenta cuenta la IP" \
  'f"reset-cuenta:{user.username}"' 'f"reset-cuenta:{get_client_ip(req)}"' "${MAIL[@]}"
sabotaje $M "la clave de la cuenta cae dentro de las de la IP" \
  'f"reset-cuenta:{user.username}"' 'f"reset:cuenta:{user.username}"' \
  "FAILED tests/test_abuso1.py::test_reset_una_ip_inventada_no_gasta_el_tope_de_la_cuenta" \
  "AssertionError: una IP inventada gastó el tope de la cuenta"
sabotaje $M "el tope deja pasar cuatro" \
  'contar(db, clave, 3600) > 3' 'contar(db, clave, 3600) > 4' "${MAIL[@]}"
MOVER=("$TOKEN" "$TOKEN$TOPE")
sabotaje $M "el tope corta después de crear el link" "$TOPE" '' \
  "FAILED $T" "AssertionError: el cuarto pedido de la hora creó un link"
MOVER=()
sabotaje $M "la ventana dura menos de una hora" \
  'contar(db, clave, 3600)' 'contar(db, clave, 3000)' \
  "FAILED $T" "AssertionError: a los 59 minutos ya mandó otro"
sabotaje $M "la ventana dura dos horas" \
  'contar(db, clave, 3600)' 'contar(db, clave, 7200)' \
  "FAILED $T" "AssertionError: pasada la hora no volvió a mandar"

if [ -n "$PG_URL" ]; then
  CORRE=caso_pg
  if ! salida="$(caso_pg)"; then
    echo "BASE  | la prueba en Postgres ya está en rojo sin sabotaje"; grep -E "^FALLA" <<<"$salida"; FALLAS=$((FALLAS+1))
  else
    echo "BASE  | Postgres: $(tail -1 <<<"$salida")"
    TOPE_TRABADO='        if user and await _tope_por_cuenta(db, f"reset-cuenta:{user.username}"):
            return mensaje
'
    MOVER=("$TRABA" "$TRABA$TOPE_TRABADO")
    sabotaje $M "el tope se cuenta con la cuenta trabada" "$TOPE" '' \
      "FALLA | el tope por cuenta no suelta la traba"
    MOVER=()
  fi
else
  echo "SALTO | sin PG_URL: que contar no suelte la traba no se midió"
fi

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
