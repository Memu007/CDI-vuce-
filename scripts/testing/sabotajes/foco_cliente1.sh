#!/usr/bin/env bash
# PRUEBAS-1 a): la espera del foco en scripts/testing/pantalla_cliente1.js
# distingue. openForm() (clientes.js) enfoca la razón social con un
# temporizador; si cae en medio de un fill, lo escrito va al nombre.
#
# Corre la prueba N veces con la espera y el temporizador del producto (80 ms).
# Después, M veces con el temporizador cambiado para que caiga siempre en el
# peor momento: el foco vuelve a la razón social apenas otro campo lo toma, entre
# el foco y la escritura del fill (o a los 3 s, si nadie lo toma). Con la
# espera no falla nunca; sin ella falla siempre con el síntoma: lo escrito en
# otro campo (el CUIT del alta, el domicilio de la edición) cae en la razón
# social. Con 10 ms en vez de esto, sin la espera a veces no falla en 30
# (PRUEBAS-1, «no distingue»): depende de la suerte. Una falla sin el síntoma
# se muestra y no cuenta. El temporizador sólo se cambia en un worktree
# descartable, nunca en el producto.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8851] [N=100] [M=5] \
#        scripts/testing/sabotajes/foco_cliente1.sh [SHA]
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"; PUERTO="${PUERTO:-8851}"; N="${N:-100}"; M="${M:-5}"
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
export CDI_DB="$WT/local.db"   # CLIENTE-1b: la prueba siembra ahí las fechas viejas

J=proyecto_maria/static/v2/screens/clientes.js
P=scripts/testing/pantalla_cliente1.js
SIN="$TMPD/sin_espera.js"
# La misma prueba, con cada espera del foco cambiada por la espera vieja (visible).
sed "s/await formularioListo();/await page.locator('#cfNombre').waitFor({ state: 'visible', timeout: 10000 });/" "$P" >"$SIN"
cp "$SIN" scripts/testing/pantalla_cliente1_sin_espera.js   # junto a la original: mismos require relativos
grep -q "formularioListo();" scripts/testing/pantalla_cliente1_sin_espera.js && { echo "ROTO  | no se pudo sacar la espera"; exit 1; }

T80="setTimeout(() => fNombre && fNombre.focus(), 80);"
# El peor momento: el primer foco en otro campo devuelve el foco a la razón
# social antes de que el fill escriba (la escritura es otro mensaje del
# navegador, llega después del setTimeout 0).
PEOR="(() => { let hecho = false; const enfocar = () => { if (!hecho \&\& fNombre) { hecho = true; fNombre.focus(); } }; const robar = (e) => { if (e.target !== fNombre) { formModal.removeEventListener('focusin', robar); setTimeout(enfocar, 0); } }; formModal.addEventListener('focusin', robar); setTimeout(() => { formModal.removeEventListener('focusin', robar); enfocar(); }, 3000); })();"
temporizador() {
  git checkout -q -- "$J"
  local n; n=$(grep -cF "$T80" "$J")
  [ "$n" -eq 2 ] || { echo "ROTO  | esperaba 2 temporizadores de 80 ms en $J y hay $n"; exit 1; }
  [ "$1" = producto ] && return
  sed -i "s/setTimeout(() => fNombre \&\& fNombre.focus(), 80);/$PEOR/" "$J"
  [ "$(grep -c "formModal.addEventListener('focusin', robar)" "$J")" -eq 2 ] || { echo "ROTO  | no se pudo cambiar el temporizador"; exit 1; }
}

SINTOMA="el aviso dice que falta el CUIT, y se cargó|la edición no se guardó: .*(razón social: .*Calle Inventada 2)"
# medir <prueba> <producto|peor> <veces>: deja «ok», «mal» y «sintoma» (fallas con el síntoma)
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
medir "$P" producto "$N"; echo "con espera, 80 ms: $ok bien, $mal fallas de $N"
[ "$mal" -eq 0 ] || FALLAS=$((FALLAS+1))
medir "$P" peor "$M"; echo "con espera, en el peor momento: $ok bien, $mal fallas de $M"
[ "$mal" -eq 0 ] || FALLAS=$((FALLAS+1))
medir scripts/testing/pantalla_cliente1_sin_espera.js peor "$M"; echo "sin espera, en el peor momento: $ok bien, $mal fallas de $M ($sintoma con lo de otro campo en la razón social)"
[ "$sintoma" -eq "$M" ] || { echo "VERDE | sin la espera no falló siempre con el síntoma: esta medición no distingue"; FALLAS=$((FALLAS+1)); }
git checkout -q -- "$J"
echo "tardó $((SECONDS-inicio)) s"
echo "mediciones con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
