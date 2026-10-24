#!/usr/bin/env bash
# Negativos de CLIENTE-1: cada sabotaje deshace una línea de la pieza y
# scripts/testing/pantalla_cliente1.js tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python [CHROMIUM=/opt/pw-browsers/chromium] [PUERTO=8841] \
#        scripts/testing/sabotajes/cliente1.sh [SHA]
# Trabaja en un worktree descartable con su propia API, SQLite nueva y sin
# terceros: no toca tu copia ni datos compartidos. La pantalla y el JS se
# leen en cada pedido, así que el sabotaje se aplica con la API andando.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8841}"
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
FALLAS=0

correr() { node scripts/testing/pantalla_cliente1.js 2>&1; }

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep FALLA <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

H=proyecto_maria/templates/dashboard_v2.html
J=proyecto_maria/static/v2/screens/clientes.js

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi

sabotaje $H "el CUIT no se marca" \
  'for="cfCuit">CUIT <span class="field-required">· lo pide el MARIA</span>' 'for="cfCuit">CUIT' \
  "FALLA: el rótulo de CUIT no dice «lo pide el MARIA»"
sabotaje $H "el domicilio no se marca" \
  'for="cfDireccion">Domicilio <span class="field-required">· lo pide el MARIA</span>' 'for="cfDireccion">Domicilio' \
  "FALLA: el rótulo de domicilio no dice «lo pide el MARIA»"
sabotaje $H "el inicio de actividad no se marca" \
  'Inicio de actividad <span class="field-required">· lo pide el MARIA</span>' 'Inicio de actividad' \
  "FALLA: el rótulo de inicio de actividad no dice «lo pide el MARIA»"
sabotaje $H "el inicio de actividad vuelve a esconderse" \
  'type="date" id="cfFechaInicActiv"' 'type="date" hidden id="cfFechaInicActiv"' \
  "FALLA: inicio de actividad no está a la vista en el alta"
sabotaje $J "no avisa lo que falta" \
  '            if (faltan.length && CDI.toast) {' '            if (false && CDI.toast) {' \
  "FALLA: el aviso no es de advertencia"
sabotaje $J "el aviso no dice cuáles faltan" \
  "'. Faltan para el MARIA: ' + faltan.join(', ') + '.'" "'. Faltan datos para el MARIA.'" \
  "FALLA: el aviso no dice qué falta"
sabotaje $J "el CUIT cargado igual figura como faltante" \
  "[cuitNorm, 'CUIT']" "['', 'CUIT']" \
  "FALLA: el aviso dice que falta el CUIT, y se cargó"
sabotaje $J "avisa aunque no falte nada" \
  '            if (faltan.length && CDI.toast) {' '            if (CDI.toast) {' \
  "FALLA: con los cuatro datos igual avisa que falta algo"
sabotaje $J "el detalle no muestra el inicio de actividad" \
  "            ['Inicio de actividad', fechaDdMmAaaa(c.fecha_inic_activ) || '—'],"$'\n' '' \
  "FALLA: el detalle del cliente no muestra el inicio de actividad"
sabotaje $J "el detalle da vuelta día y mes" \
  "m[3] + '/' + m[2] + '/' + m[1]" "m[2] + '/' + m[3] + '/' + m[1]" \
  "FALLA: el detalle no muestra el inicio de actividad cargado"
sabotaje $J "el detalle muestra la fecha sin formatear" \
  "return m ? m[3] + '/' + m[2] + '/' + m[1] : txt;" "return txt;" \
  "FALLA: el detalle no muestra el inicio de actividad cargado como 01/03/2015"
sabotaje $J "una fecha en otro formato se muestra vacía" \
  "m[1] : txt;" "m[1] : '';" \
  "FALLA: una fecha guardada que no es AAAA-MM-DD se muestra como vacía"
sabotaje $J "la pestaña Datos no muestra el detalle" \
  "panelDatos.hidden    = tab !== 'datos';" "panelDatos.hidden    = true;" \
  "FALLA: la pestaña Datos no muestra el detalle del cliente"
sabotaje proyecto_maria/static/v2/app_v2.js "el aviso de advertencia lleva el ícono de información" \
  "(kind === 'error' || kind === 'warning') ? '!'" "kind === 'error' ? '!'" \
  "FALLA: el aviso de advertencia tiene el ícono «i», no «!»"
git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
