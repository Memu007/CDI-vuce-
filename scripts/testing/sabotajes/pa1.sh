#!/usr/bin/env bash
# Negativos de PA-1: cada sabotaje deshace uno de los textos de la pieza (o
# cambia uno de los que tienen que seguir diciendo «NCM») y
# tests/test_pa1_textos.py tiene que fallar por ese motivo, y sólo en ese caso.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/pa1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia. No levanta la API.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
FALLAS=0

correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -p no:warnings tests/test_pa1_textos.py 2>&1; }

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="proyecto_maria/$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
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
  local salida codigo fallidos
  salida="$(correr)"; codigo=$?
  fallidos="$(grep -cE '^FAILED ' <<<"$salida")"
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif ! grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E '^E ' <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  elif [ "$fallidos" -ne 1 ]; then
    echo "ROJO? | $nombre: fallaron $fallidos casos, tenía que fallar sólo el suyo"; FALLAS=$((FALLAS+1))
  else
    echo "ROJO  | $nombre: dice «$esperado»"
  fi
}

H=templates/dashboard_v2.html
N=static/v2/screens/ncm.js
C=static/v2/screens/clientes.js
K=static/v2/screens/catalogo.js

if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | tail -5; exit 1
fi

# Vuelve el texto viejo: «sigue diciendo».
sabotaje $H "paso 3 del progreso" '<span class="num">3</span> PA SIM</div>' '<span class="num">3</span> NCM</div>' \
  "sigue diciendo '<span class=\"num\">3</span> NCM</div>'"
sabotaje $H "botón continuar" "Continuar a PA SIM" "Continuar a NCM" "sigue diciendo 'Continuar a NCM'"
sabotaje $H "botón volver" ">Volver a PA SIM<" ">Volver a NCM<" "sigue diciendo '>Volver a NCM<'"
sabotaje $H "memoria del cliente" "recuerda las posiciones arancelarias (PA SIM) y orígenes confirmados" \
  "recuerda los NCM y orígenes confirmados" "sigue diciendo 'recuerda los NCM y orígenes confirmados'"
sabotaje $H "aria del asistente" 'aria-label="Asistente de posición arancelaria (PA SIM)"' 'aria-label="Asistente NCM"' \
  "sigue diciendo 'aria-label=\"Asistente NCM\"'"
sabotaje $N "deshacer al borrar" "scheduleUndoClear('PA SIM ' + formatted" "scheduleUndoClear('NCM ' + formatted" \
  "sigue diciendo \"scheduleUndoClear('NCM ' + formatted\""
sabotaje $N "deshacer del asistente" "scheduleUndoClear('PA SIM ' + result.ncm" "scheduleUndoClear('NCM ' + result.ncm" \
  "sigue diciendo \"scheduleUndoClear('NCM ' + result.ncm\""
sabotaje $N "contador de memoria" "</strong> posiciones arancelarias (PA SIM)' + detailText" "</strong> NCM' + detailText" \
  "sigue diciendo \"</strong> NCM' + detailText\""
sabotaje $N "sugerencias del cliente" "te sugerimos las posiciones arancelarias (PA SIM) que ya usó antes" \
  "te sugerimos los NCM que ya usó antes" "sigue diciendo 'te sugerimos los NCM que ya usó antes'"
sabotaje $N "título de la sugerencia" 'title="PA SIM sugerida desde ' 'title="NCM sugerido desde ' \
  "sigue diciendo 'title=\"NCM sugerido desde '"
sabotaje $N "aviso al guardar en memoria" "'Guardamos esta posición arancelaria (PA SIM) para '" "'Guardamos este NCM para '" \
  "sigue diciendo \"'Guardamos este NCM para '\""
sabotaje $N "título de refrescar" 'title="Refrescar desde el asistente de posición arancelaria"' \
  'title="Refrescar desde el asistente NCM"' "sigue diciendo 'title=\"Refrescar desde el asistente NCM\"'"
sabotaje $C "columna de importación del catálogo" "pieza: 'Posición arancelaria (PA SIM)'," "pieza: 'NCM / Pieza'," \
  "sigue diciendo \"pieza: 'NCM / Pieza',\""
sabotaje $C "título del input del catálogo" 'title="Posición arancelaria (PA SIM)"' 'title="NCM"' \
  "sigue diciendo 'value=\"\\' + CDI.escapeHtml(p.ncm) + \\'\" title=\"NCM\"'"
sabotaje $K "encabezado del catálogo" "'<span>PA SIM</span>' +" "'<span>NCM</span>' +" \
  "sigue diciendo \"'<span>NCM</span>' +\""

# Un texto nuevo que se duplica también es rojo: «no dice».
sabotaje $K "encabezado duplicado" "'<span>PA SIM</span>' +" "'<span>PA SIM</span>' + '<span>PA SIM</span>' +" \
  "no dice \"'<span>PA SIM</span>' +\""

# Lo que habla de los 8 dígitos no se cambia: «ya no dice».
sabotaje $H "ayuda de la NCM de 8" "La NCM tiene 8 dígitos." "La PA SIM tiene 8 dígitos." "ya no dice 'La NCM tiene 8 dígitos."
sabotaje $H "formato corto" "<small>NCM 8 + SIM 3 + DC</small>" "<small>PA SIM 8 + SIM 3 + DC</small>" \
  "ya no dice '<small>NCM 8 + SIM 3 + DC</small>'"
sabotaje $H "formato largo" "NCM 8 + SIM 3 + letra DC" "PA SIM 8 + SIM 3 + letra DC" "ya no dice 'NCM 8 + SIM 3 + letra DC'"
sabotaje $H "calculadora" '<label class="field-label" for="calcNcm">NCM</label>' \
  '<label class="field-label" for="calcNcm">PA SIM</label>' "ya no dice '<label class=\"field-label\" for=\"calcNcm\">NCM</label>'"
sabotaje $H "notas del capítulo" "Recordatorios privados del capítulo NCM" "Recordatorios privados del capítulo PA SIM" \
  "ya no dice 'Recordatorios privados del capítulo NCM'"
sabotaje $H "planilla maestra" "Importar planilla maestra de NCMs" "Importar planilla maestra de PA SIM" \
  "ya no dice 'Importar planilla maestra de NCMs'"
sabotaje $N "NCM sin asignar" "La NCM de 8 dígitos todavía no fue asignada." "La PA SIM todavía no fue asignada." \
  "ya no dice 'La NCM de 8 dígitos todavía no fue asignada.'"
sabotaje $N "NCM que trae VUCE" "'<span class=\"spotlight-vuce-ncm\">NCM ' +" "'<span class=\"spotlight-vuce-ncm\">PA SIM ' +" \
  "ya no dice '\\'<span class=\"spotlight-vuce-ncm\">NCM \\' + CDI.escapeHtml(formattedBaseNcm)'"
sabotaje $N "largo de la posición" "NCM (8) + detalle SIM (3)." "PA SIM (8) + detalle SIM (3)." \
  "ya no dice 'La posición SIM debe tener 11 dígitos: NCM (8) + detalle SIM (3).'"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
