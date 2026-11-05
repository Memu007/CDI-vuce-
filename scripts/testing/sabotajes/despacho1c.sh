#!/usr/bin/env bash
# Negativos de DESPACHO-1c: cada sabotaje deshace una línea de la pieza y
# tests/test_despacho1c.py tiene que ponerse roja por ese motivo. Necesita node.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/despacho1c.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0
T=tests/test_despacho1c.py
PRUEBA=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T")

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$("${PRUEBA[@]}" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
    grep -E "^E |^FALLA" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
F=proyecto_maria/static/v2/screens/finalize.js
N=proyecto_maria/static/v2/screens/ncm.js
V=test_lo_que_normaliza_a_vacio_no_cruza_el_historial
A=test_lo_que_no_quedo_en_la_memoria_se_avisa

if ! "${PRUEBA[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $M "la consulta vacía se compara igual" \
  '        if desc_norm and guardada and (desc_norm in guardada or guardada in desc_norm):' \
  '        if guardada and (desc_norm in guardada or guardada in desc_norm):' \
  "FAILED $T::$V[consulta-japones]"
sabotaje $M "la fila guardada vacía se compara igual" \
  '        if desc_norm and guardada and (desc_norm in guardada or guardada in desc_norm):' \
  '        if desc_norm and (desc_norm in guardada or guardada in desc_norm):' \
  "FAILED $T::$V[guardada-japones]"
sabotaje $F "guardar la operación no avisa lo que no quedó en la memoria" \
  '                if (data.historial_guardado === false) {' \
  '                if (false) {' \
  "FAILED $T::$A[no-guardado-listo-con-cliente]"
sabotaje $F "«Cliente guardado» tapa el aviso" \
  '        if (guardado.historial_guardado !== false && CDI.toast) {' \
  '        if (CDI.toast) {' \
  "FAILED $T::$A[no-guardado-asignar-cliente]"
sabotaje $N "confirmar la posición no avisa lo que no quedó en la memoria" \
  '            if (res.ok && data.historial_guardado === false && CDI.toast) {' \
  '            if (false) {' \
  "FAILED $T::$A[no-guardado-confirmar-ncm]"

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
