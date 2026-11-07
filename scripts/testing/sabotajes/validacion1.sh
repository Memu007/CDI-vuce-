#!/usr/bin/env bash
# Negativos de VALIDACION-1: cada sabotaje deshace una regla de runValidation
# (finalize.js) y scripts/testing/pantalla_validacion1.js tiene que fallar por
# ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/validacion1.sh [SHA]
# Trabaja en un worktree descartable con una API local, SQLite propia y sin
# terceros. La API sirve los archivos del disco: cada sabotaje se ve sin
# reiniciarla. Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -f "$TMPD/api.log"; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0
F=proyecto_maria/static/v2/screens/finalize.js

PUERTO="$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
env ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./pantalla.db \
    JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
    ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
    DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
    nice -n 19 "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" \
    > "$TMPD/api.log" 2>&1 < /dev/null &
API=$!
"$PY" - "$PUERTO" <<'PYEOF' || { echo "ROTO  | la API no levanta"; tail -20 "$TMPD/api.log"; exit 1; }
import sys, time, urllib.request
fin = time.time() + 90
while True:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/health", timeout=2); break
    except Exception:
        if time.time() > fin: sys.exit(1)
        time.sleep(0.5)
PYEOF
correr() { BASE_URL="http://127.0.0.1:$PUERTO" nice -n 19 node scripts/testing/pantalla_validacion1.js 2>&1; }

if ! base="$(correr)"; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje: no se puede medir nada"; grep FALLA <<<"$base"; exit 1
fi
echo "BASE  | en verde"

# sabotaje <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en finalize.js.
sabotaje() {
  local nombre="$1" esperado="$2"; shift 2
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$F" "$@" <<'PYEOF'
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
    echo "VERDE | $nombre: la pantalla no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep FALLA <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

sabotaje "el caché no mira de qué carga es" \
  "FALLA: panel: muestra" \
  'pedido === lastValidationPedido && ' ''
sabotaje "la respuesta de la anterior pinta la que se ve" \
  "FALLA: panel, la anterior contesta después: muestra" \
  $'        if (turno !== turnoValidacion) return;\n' ''
sabotaje "con el validador caído queda el resultado de la anterior" \
  "FALLA: botón, falla el validador: el botón está habilitado pero el clic no genera" \
  $'            lastValidation = null;\n            // Mostrar' '            // Mostrar'
sabotaje "volver a validar la misma con el validador caído borra su resultado" \
  "FALLA: botón, falla al volver a validar la misma: deja generar con el peso en cero" \
  $'            if (lastValidation && pedido === lastValidationPedido) {\n                renderValidation(lastValidation);\n                return;\n            }\n' ''
sabotaje "con una validación en curso, la que se ve no valida" \
  "FALLA: panel, la anterior contesta después: no mostró la validación de la que se ve" \
  '        const turno = ++turnoValidacion;' \
  $'        if (window.__enVuelo) return;\n        window.__enVuelo = true;\n        const turno = ++turnoValidacion;' \
  $'        if (turno !== turnoValidacion) return;\n' \
  $'        window.__enVuelo = false;\n        if (turno !== turnoValidacion) return;\n'

git checkout -q -- proyecto_maria/
echo "FALLAS=$FALLAS"
[ "$FALLAS" -eq 0 ]
