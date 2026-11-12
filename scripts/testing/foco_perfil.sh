#!/usr/bin/env bash
# ¿Las pantallas que abren «Mi perfil» pierden lo que escriben cuando el foco
# inicial salta a «Mi CUIT»? El perfil pone el foco en #pfCuit un rato después
# de cargar; si eso cae en medio de un fill, el texto va a «Mi CUIT».
#
# En un worktree descartable se cambia ese setTimeout por un reloj que pone el
# foco una sola vez por apertura, en lo primero que pase: que el arnés entre al
# campo del caso (el foco salta enseguida, antes de que el texto llegue) o que
# pasen 3 s. Un arnés que escribe sin esperar el foco pierde lo escrito siempre;
# uno que espera el foco lo recibe a los 3 s y sigue. La página avisa a la API
# (GET /health?foco=… y ?robado=…), y se lee en su log.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8856] scripts/testing/foco_perfil.sh [SHA]
# Sale 0 si ningún caso pierde lo escrito, 1 si alguno lo pierde, 2 si el
# resultado no se puede leer (la API no levanta, rojo sin la firma del foco).
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8856}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -f -- "$TMPD/local.db" "$TMPD/api.log"; rmdir "$TMPD"' EXIT
cd "$WT"
P=proyecto_maria/static/v2/screens/profile.js

# arnés · campo donde el foco salta apenas el arnés entra
CASOS=(
  "scripts/testing/pantalla_estudio1.js·#pfEstudioNombre"
  "scripts/testing/pantalla_estudio1.js·#pfEstudioCuit"
  "scripts/testing/pantalla_cobro_mp1.js·#pfBillingBlock > summary"
)

reloj() {
  git checkout -q -- "$P"
  "$PY" - "$P" "$1" <<'PYEOF'
import json, sys
p, disparo = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
viejo = "setTimeout(() => cuitInput && cuitInput.focus(), 150);"
nuevo = """{
        const disparo = %s, t0 = performance.now();
        let hecho = false, reloj = null;
        const avisar = (q) => fetch('/health?' + new URLSearchParams(q)).catch(() => {});
        const poner = (via) => {
            if (hecho) return;
            hecho = true; clearTimeout(reloj); document.removeEventListener('focusin', alEntrar, true);
            avisar({ foco: via, ms: Math.round(performance.now() - t0) });
            if (via === 'campo') cuitInput.addEventListener('input', () => avisar({ robado: disparo, valor: cuitInput.value }), { once: true });
            cuitInput.focus();
        };
        const alEntrar = (ev) => { if (ev.target.matches(disparo)) queueMicrotask(() => poner('campo')); };
        document.addEventListener('focusin', alEntrar, true);
        reloj = setTimeout(() => poner('reloj'), 3000);
        }""" % json.dumps(disparo)
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

correr() {
  rm -f -- "$TMPD/local.db" "$TMPD/api.log"
  ENVIRONMENT=development JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef \
  EMAIL_VERIFICATION_REQUIRED=false ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x \
  ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x DATABASE_URL="sqlite+aiosqlite:///$TMPD/local.db" \
  GEMINI_API_KEY=test-key DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
    "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  if ! curl -fsS --retry 60 --retry-connrefused --retry-delay 1 "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1; then
    echo "FALLA: la API no levantó"; tail -n 5 "$TMPD/api.log"; kill $API 2>/dev/null; wait $API 2>/dev/null; API=""; return 2
  fi
  local codigo
  BASE_URL="http://127.0.0.1:$PUERTO" node "$1" 2>&1; codigo=$?
  kill $API 2>/dev/null; wait $API 2>/dev/null; API=""
  return $codigo
}

PIERDE=0; ILEGIBLE=0
for caso in "${CASOS[@]}"; do
  js="${caso%%·*}"; campo="${caso#*·}"
  if ! reloj "$campo"; then echo "ROTO        | $caso: no se pudo poner el reloj"; ILEGIBLE=1; continue; fi
  salida="$(correr "$js")"; codigo=$?
  focos="$(grep -o 'GET /health?foco=[a-z]*&ms=[0-9]*' "$TMPD/api.log" | sed 's#GET /health?##' | tr '\n' ' ')"
  robado="$(grep -o 'GET /health?robado=[^ ]*' "$TMPD/api.log" | sed 's#GET /health?##' | tr '\n' ' ')"
  if [ -n "$robado" ]; then
    echo "PIERDE      | $caso: lo escrito cayó en «Mi CUIT» (${robado% }) · focos: $focos"
    grep -m 1 FALLA <<<"$salida"; PIERDE=1
  elif [ "$codigo" -ne 0 ]; then
    echo "ILEGIBLE    | $caso: rojo (salida $codigo) sin texto en «Mi CUIT» · focos: $focos"
    grep -m 3 FALLA <<<"$salida"; ILEGIBLE=1
  elif [ -z "$focos" ]; then
    echo "ILEGIBLE    | $caso: verde, pero el reloj nunca puso el foco"; ILEGIBLE=1
  else
    echo "NO PIERDE   | $caso · focos: $focos"
  fi
done
[ "$ILEGIBLE" -ne 0 ] && exit 2
exit "$PIERDE"
