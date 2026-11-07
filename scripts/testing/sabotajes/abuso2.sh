#!/usr/bin/env bash
# Negativos de ABUSO-2: cada sabotaje deshace una regla y la prueba de esa
# regla tiene que fallar por ese motivo.
# Login: un login correcto perdona sólo los fallos que la IP hizo con su
# cuenta (tests/test_abuso2.py). Recuperar usuario: el tope de 3 por hora se
# cuenta por la cuenta encontrada y no por el texto pedido; en SQLite lo ve
# tests/test_abuso1.py con mayúsculas y, con PG_URL, la İ que sólo Postgres
# junta lo ve scripts/testing/abuso2_postgres.py.
#
# uso: PY=/ruta/al/venv/bin/python [PG_URL=postgresql://cdi@127.0.0.1:55432/postgres] \
#        scripts/testing/sabotajes/abuso2.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite (y, con PG_URL, una
# base de Postgres local que crea y borra): no toca tu copia ni datos
# compartidos. Sale con error si un sabotaje no encuentra su patrón o no pone
# rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG_URL="${PG_URL:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo. Corre `correr`.
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
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|FALLA|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
L=proyecto_maria/core/limites_auth.py
T=tests/test_abuso2.py
P="FAILED $T::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta"
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -W ignore -rf $T 2>&1; }

T="tests/test_abuso2.py tests/test_abuso1.py"
rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi
echo "BASE  | en verde"
T=tests/test_abuso2.py

# --- el login correcto perdona sólo lo propio
sabotaje $M "el login correcto borra todos los fallos de la IP" "$P[otra_cuenta]" \
  '    await limites_auth.descontar(db, clave_intentos, clave_cuenta)' \
  '    await limites_auth.limpiar(db, clave_intentos)'
sabotaje $M "los fallos de la cuenta no se cuentan aparte" "$P[solo_propios]" \
  $'        if clave_cuenta:\n            await limites_auth.contar' \
  $'        if False:\n            await limites_auth.contar'
sabotaje $L "descontar borra lo propio pero no lo resta de la IP" "$P[mitad_y_mitad]" \
  '            cuenta=_T.c.cuenta - n,' '            cuenta=_T.c.cuenta,'
sabotaje $L "descontar no olvida un bloqueo vencido" "$P[bloqueo_vencido]" \
  '            bloqueado_hasta=case((_T.c.bloqueado_hasta <= ahora, 0.0), else_=_T.c.bloqueado_hasta)))' \
  '            bloqueado_hasta=_T.c.bloqueado_hasta))'
sabotaje $L "descontar deja la fila de la IP en cero o menos" "$P[mas_propios_que_la_ip]" \
  '        await db.execute(delete(_T).where(_T.c.clave == clave, _T.c.cuenta <= 0))' \
  '        pass'
sabotaje $M "el login cuenta los fallos de la IP con el tope de recuperar" "$P[ajeno_tras_el_bloqueo]" \
  'sumar_fallo(db, clave_intentos, exacta=True)' 'sumar_fallo(db, clave_intentos)'

# --- recuperar usuario: el tope va por la cuenta, no por el texto
T=tests/test_abuso1.py
sabotaje $M "el tope de recuperar va por el texto pedido" \
  "FAILED $T::test_s6_recuperar_usuario_corta_en_silencio_por_email" \
  'f"recuperar:cuenta:{user.username}"' 'f"recuperar:cuenta:{request.email}"'
if [ -n "$PG_URL" ]; then
  correr() { "$PY" scripts/testing/abuso2_postgres.py "$PG_URL" 2>&1; }
  sabotaje $M "Postgres: el tope de recuperar va por el texto en minúsculas de Python" \
    "FALLA | cinco variantes del mismo email mandan tres mails" \
    'f"recuperar:cuenta:{user.username}"' 'f"recuperar:cuenta:{request.email.strip().lower()}"'
else
  echo "SIN PG| el sabotaje de la İ necesita PG_URL: no se corrió"
fi

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
exit $((FALLAS > 0))
