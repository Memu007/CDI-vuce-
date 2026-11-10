#!/usr/bin/env bash
# El arranque no saca a la usuaria de Clientes (scripts/testing/pantalla_borrador1.js).
# Corre la prueba con el producto (tiene que dar ok) y con cada parte del
# arreglo revertida en un worktree descartable (tiene que dar su FALLA):
#   decide_tarde: el borrador se adopta aunque ya haya pantalla
#   sin_freno:    el arranque cambia de pantalla aunque ya haya una
# Cada corrida levanta la API con una base nueva: el registro tiene límite por hora.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8863] scripts/testing/sabotajes/borrador1.sh [SHA]
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"; PUERTO="${PUERTO:-8863}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export ENVIRONMENT=development GEMINI_API_KEY=test-key \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
export BASE_URL="http://127.0.0.1:$PUERTO"
J=proyecto_maria/static/v2/app_v2.js

levantar() {
  [ -n "$API" ] && { kill "$API" 2>/dev/null; wait "$API" 2>/dev/null; }
  DATABASE_URL="sqlite+aiosqlite:///$TMPD/$1.db" \
    "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api_$1.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && return; sleep 1; done
  echo "ROTO  | $1: la API no levantó"; tail -20 "$TMPD/api_$1.log"; exit 1
}

# cambiar <viejo> <nuevo>: reemplazo exacto en app_v2.js, que tiene que aparecer una vez
cambiar() {
  git checkout -q -- "$J"
  "$PY" - "$J" "$1" "$2" <<'EOF' || { echo "ROTO  | no se encontró una sola vez: $1"; exit 1; }
import sys
p, viejo, nuevo = sys.argv[1:]
t = open(p, encoding='utf-8').read()
assert t.count(viejo) == 1, t.count(viejo)
open(p, 'w', encoding='utf-8').write(t.replace(viejo, nuevo))
EOF
}

FALLAS=0
# correr <nombre> <0 si tiene que dar ok, 1 si tiene que fallar> <texto que tiene que decir>
correr() {
  levantar "$1"
  local salida rc
  salida=$(node scripts/testing/pantalla_borrador1.js 2>&1); rc=$?
  if [ "$2" -eq 0 ]; then
    if [ "$rc" -eq 0 ]; then echo "OK    | $1: $salida"; else echo "ROJO  | $1 tenía que dar ok:"; echo "$salida"; FALLAS=$((FALLAS+1)); fi
  elif [ "$rc" -ne 0 ] && grep -qF "$3" <<<"$salida"; then
    echo "ROJO bien | $1:"; grep FALLA <<<"$salida" | sed 's/^/        /'
  else
    echo "VERDE | $1 no dio la falla esperada «$3» (rc=$rc):"; echo "$salida"; FALLAS=$((FALLAS+1))
  fi
}

git checkout -q -- "$J"
correr producto 0 ""

cambiar "return buscarBorrador().then(b => (!b ? null : currentScreen ? adoptarTarde(b) : adoptarBorrador(b)));" \
        "return buscarBorrador().then(b => (b ? adoptarBorrador(b) : null));"
correr decide_tarde 1 "hay una operación de antes: no apareció el aviso «Quedó guardada la operación»"

cambiar "                if (currentScreen) return;
" ""
correr sin_freno 1 "el usuario no llega a tiempo: el arranque la sacó de Clientes y la llevó a upload"

git checkout -q -- "$J"
echo "corridas que no dieron lo esperado: $FALLAS"
[ "$FALLAS" -eq 0 ]
