#!/usr/bin/env bash
# Negativos de SEGURO-2: cada sabotaje deshace una regla de lo que frena la
# generación por el seguro (el que sigue para completar, el 1 % dejado con un
# incoterm que ya lo lleva en el precio, la marca de dejado en la pantalla) y
# los casos tienen que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/seguro2.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0
CASOS=(tests/test_seguro2.py tests/test_seguro1.py
       tests/test_valor1c.py::test_dejarlo_lo_marca_como_dejado_y_pide_las_cuentas_de_nuevo)

correr_casos() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider "${CASOS[@]}" 2>&1
}

aplicar() {
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(correr_casos)"; codigo=$?
  git checkout -q -- proyecto_maria/
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^FAILED" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# Sin sabotaje, verde: si no, ningún rojo de abajo distingue nada.
salida="$(correr_casos)" || { echo "BASE  | los casos no pasan sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | $(tail -1 <<<"$salida")"

M=proyecto_maria/main.py
F=proyecto_maria/static/v2/screens/finalize.js
R=proyecto_maria/static/v2/screens/review.js
T=tests/test_seguro2.py

# 1. El seguro para completar frena; el 0 escrito, no.
sabotaje $M "el servidor no mira si sigue para completar" \
  '    if request.seguro_para_completar:
        return SEGURO_BORRADO if request.seguro_borrado else SEGURO_PARA_COMPLETAR
' '' \
  "FAILED $T::test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen[CIF-]" \
  "FAILED $T::test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen[FOB-]"
sabotaje $M "un 0 también frena" \
  'if request.seguro_para_completar:' 'if request.seguro_para_completar or not request.seguro:' \
  "FAILED $T::test_el_cero_escrito_a_proposito_genera"
sabotaje $M "generar sólo avisa" \
  '        if _por_corregir:
            raise' '        if False:
            raise' \
  "FAILED $T::test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen[CIF-]" \
  "FAILED $T::test_el_uno_por_ciento_dejado_no_genera_con_cif"
sabotaje $F "el pedido no dice que sigue para completar" \
  '            seguro_para_completar: seguroSinLeer(op),
' '' \
  "FAILED $T::test_el_pedido_dice_si_el_seguro_sigue_para_completar[sin_leer]"

sabotaje $R "escribirlo no lo completa" \
  "if (String(el.value).trim() !== '') completados.add(el.name);" 'if (false) completados.add(el.name);' \
  "FAILED $T::test_escribir_el_seguro_sin_leer_lo_completa[0-True]" \
  "FAILED $T::test_escribir_el_seguro_sin_leer_lo_completa[15-True]"
sabotaje $R "el seguro sin leer se ve en 0" \
  "return name === 'seguro' && CDI.seguroSinLeer(op) ? '' : " 'return ' \
  "FAILED $T::test_un_campo_sin_leer_se_ve_vacio_en_la_revision[sin_leer]"
sabotaje $F "finalize no exporta el predicado" \
  '    CDI.seguroSinLeer = seguroSinLeer;
' '' \
  "FAILED $T::test_la_revision_tiene_el_predicado_de_finalize"
sabotaje $R "la revisión no lo usa" \
  'const normalized = valorEnLaRevision(key, op);' 'const normalized = normalizeValueForField(key, op[key]);' \
  "FAILED $T::test_la_revision_muestra_vacio_el_seguro_sin_leer_y_lo_deja_en_0"
sabotaje $R "otro monto sin leer también se vacía" \
  "return name === 'seguro' && CDI.seguroSinLeer(op)" "return CDI.seguroSinLeer(op)" \
  "FAILED $T::test_un_campo_sin_leer_se_ve_vacio_en_la_revision[flete_sin_leer]"
sabotaje $F "el 400 se queda en la pantalla de generar" \
  "                    CDI.goTo('review');
                    if (CDI.marcarEnLaRevision)" '                    if (CDI.marcarEnLaRevision)' \
  "FAILED $T::test_si_el_servidor_pide_completarlo_se_vuelve_a_la_revision"

# 2. El 1 % dejado frena sólo con un incoterm que ya lleva el seguro en el precio.
sabotaje $M "el dejado no frena con CIF" \
  'if not (request.seguro_calculado or request.seguro_dejado):' 'if not request.seguro_calculado:' \
  "FAILED $T::test_el_uno_por_ciento_dejado_no_genera_con_cif"
sabotaje $M "el dejado se compara con las cuentas de ahora" \
  '    if not request.seguro_calculado:
        return None
' '' \
  "FAILED $T::test_el_uno_por_ciento_dejado_genera_con_cfr"
sabotaje $F "el pedido no dice que se dejó" \
  '            seguro_dejado: !!op.seguro_dejado,
' '' \
  "FAILED $T::test_el_pedido_dice_si_el_seguro_se_dejo"

# 3. La marca de dejado: se pone al dejarlo y se va al recalcularlo, escribirlo o borrarlo.
sabotaje $F "dejarlo no lo marca" \
  '        op.seguro_dejado = true;
' '' \
  "FAILED tests/test_valor1c.py::test_dejarlo_lo_marca_como_dejado_y_pide_las_cuentas_de_nuevo"
sabotaje $F "el dejado no se borra al pasar a CIF" \
  '!(op.seguro_calculado || op.seguro_dejado)) return false;' '!op.seguro_calculado) return false;' \
  "FAILED $T::test_el_dejado_se_borra_al_pasar_a_cif_y_queda_para_completar"
sabotaje $F "el borrado deja la marca" \
  '        delete op.seguro_dejado;
        const sinLeer' '        const sinLeer' \
  "FAILED $T::test_el_dejado_se_borra_al_pasar_a_cif_y_queda_para_completar"
sabotaje $F "recalcularlo deja la marca" \
  '        op.seguro_calculado = true;
        delete op.seguro_dejado;
' '        op.seguro_calculado = true;
' \
  "FAILED $T::test_recalcularlo_ya_no_es_el_dejado"
sabotaje $R "escribirlo a mano deja la marca" \
  'delete op.seguro_calculado; delete op.seguro_dejado;' 'delete op.seguro_calculado;' \
  "FAILED $T::test_escribirlo_a_mano_ya_no_es_el_dejado"

# 4. Con CIF, la nota dice que una factura sin seguro necesita un 0.
sabotaje $F "la nota no pide el 0" \
  'completalo en la revisión; si no trae seguro, escribí 0.' 'completalo en la revisión.' \
  "FAILED tests/test_seguro1.py::test_con_cif_y_un_seguro_sin_leer_la_nota_lo_pide"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
