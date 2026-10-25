#!/usr/bin/env bash
# PRUEBAS-1 a): la espera del foco en scripts/testing/pantalla_cliente1.js
# distingue. openForm() (clientes.js) enfoca la razón social con un
# temporizador; si cae en medio de un fill, lo escrito va al nombre.
#
# Corre la prueba N veces con la espera y el temporizador del producto (80 ms),
# y M veces con el temporizador acortado a 10 ms con y sin la espera: con la
# espera no falla nunca; sin ella tiene que fallar al menos una vez con el
# síntoma: lo que se escribió en el domicilio aparece en la razón social. Una
# falla sin ese síntoma se muestra y no cuenta como prueba. El temporizador
# sólo se acorta en un worktree descartable, nunca en el producto.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8851] [N=100] [M=30] \
#        scripts/testing/sabotajes/foco_cliente1.sh [SHA]
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"; PUERTO="${PUERTO:-8851}"; N="${N:-100}"; M="${M:-30}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./local.db GEMINI_API_KEY=test-key \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
"$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
API=$!
for _ in $(seq 1 60); do curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null || { echo "BASE  | la API no levantó"; tail -20 "$TMPD/api.log"; exit 1; }
export BASE_URL="http://127.0.0.1:$PUERTO"

J=proyecto_maria/static/v2/screens/clientes.js
P=scripts/testing/pantalla_cliente1.js
SIN="$TMPD/sin_espera.js"
# La misma prueba, con cada espera del foco cambiada por la espera vieja (visible).
sed "s/await formularioListo();/await page.locator('#cfNombre').waitFor({ state: 'visible', timeout: 10000 });/" "$P" >"$SIN"
cp "$SIN" scripts/testing/pantalla_cliente1_sin_espera.js   # junto a la original: mismos require relativos
grep -q "formularioListo();" scripts/testing/pantalla_cliente1_sin_espera.js && { echo "ROTO  | no se pudo sacar la espera"; exit 1; }

temporizador() {
  git checkout -q -- "$J"
  local n; n=$(grep -c "setTimeout(() => fNombre && fNombre.focus(), 80);" "$J")
  [ "$n" -ge 1 ] || { echo "ROTO  | no encontré el temporizador de 80 ms en $J"; exit 1; }
  sed -i "s/setTimeout(() => fNombre \&\& fNombre.focus(), 80);/setTimeout(() => fNombre \&\& fNombre.focus(), $1);/" "$J"
}

SINTOMA="la edición no se guardó: .*(razón social: .*Calle Inventada 2)"
# medir <prueba> <ms> <veces>: deja «ok», «mal» y «sintoma» (fallas con el síntoma)
medir() {
  temporizador "$2"; ok=0; mal=0; sintoma=0
  local salida linea
  for _ in $(seq 1 "$3"); do
    if salida=$(node "$1" 2>&1); then ok=$((ok+1)); continue; fi
    mal=$((mal+1))
    linea=$(grep -m1 "FALLA" <<<"$salida" || tail -1 <<<"$salida")
    grep -qE "$SINTOMA" <<<"$linea" && sintoma=$((sintoma+1))
    echo "        ${linea:0:220}"
  done
}

FALLAS=0
inicio=$SECONDS
medir "$P" 80 "$N"; echo "con espera, 80 ms: $ok bien, $mal fallas de $N"
[ "$mal" -eq 0 ] || FALLAS=$((FALLAS+1))
medir "$P" 10 "$M"; echo "con espera, 10 ms: $ok bien, $mal fallas de $M"
[ "$mal" -eq 0 ] || FALLAS=$((FALLAS+1))
medir scripts/testing/pantalla_cliente1_sin_espera.js 10 "$M"; echo "sin espera, 10 ms: $ok bien, $mal fallas de $M ($sintoma con el texto del domicilio en la razón social)"
[ "$sintoma" -ge 1 ] || { echo "VERDE | sin la espera no falló nunca con el síntoma: esta medición no distingue"; FALLAS=$((FALLAS+1)); }
git checkout -q -- "$J"
echo "tardó $((SECONDS-inicio)) s"
echo "mediciones con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
