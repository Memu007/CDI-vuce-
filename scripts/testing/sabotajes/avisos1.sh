#!/usr/bin/env bash
# Negativos de AVISOS-1: cada sabotaje afloja o estira el rechazo de una
# destinación de exportación (EC*), que generar, los avisos y el generador
# comparten, o deshace lo que la persona lee del seguro y dónde lo lee, y el
# caso tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/avisos1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="$(command -v "${PY:-python}")" || exit 2
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0
CASOS=(tests/test_doc1_documentos.py tests/test_generar_maria_txt.py tests/test_avisos1_seguro.py)

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

G=proyecto_maria/core/maria_generator.py
T=tests/test_doc1_documentos.py::test_ec_directa_nunca_entra_a_importacion
P='return re.match(r"[^A-Z0-9]*EC", texto) is not None'

sabotaje $G "sólo se saca lo que saca strip" \
  "$P" 'return texto.strip().startswith("EC")' \
  "FAILED $T"'[\u200bEC01-True-/generate_maria]' \
  "FAILED $T"'[\x00EC01-True-/generate_maria/avisos]'
sabotaje $G "sólo saltea lo que no es palabra" \
  "$P" 'return re.match(r"[\W_]*EC", texto) is not None' \
  "FAILED $T"'[\u3164EC01-True-/generate_maria]' \
  "FAILED tests/test_doc1_documentos.py::test_generador_directo_rechaza_ec[\u3164EC01]"
sabotaje $G "no lleva el ancho completo a EC" \
  'unicodedata.normalize("NFKC", str(tipo_destinacion or ""))' 'str(tipo_destinacion or "")' \
  "FAILED $T"'[\uff25\uff2301-True-/generate_maria/avisos]'
sabotaje $G "distingue mayúsculas" \
  'str(tipo_destinacion or "")).upper()' 'str(tipo_destinacion or ""))' \
  "FAILED $T"'[ ec01 -True-/generate_maria]'
sabotaje $G "exige algo delante" \
  "$P" 'return re.match(r"[^A-Z0-9]+EC", texto) is not None' \
  "FAILED $T"'[EC02-True-/generate_maria]'
sabotaje $G "rechaza cualquier destinación" \
  "$P" 'return re.match(r"[^A-Z0-9]*[A-Z]", texto) is not None' \
  "FAILED $T"'[IC04-False-/generate_maria/avisos]' \
  "FAILED $T"'[\u200bIC04-False-/generate_maria/avisos]'

# El seguro borrado al pasar a un incoterm con el seguro en el precio, y el
# motivo del 400 a la vista en la revisión.
M=proyecto_maria/main.py
F=proyecto_maria/static/v2/screens/finalize.js
R=proyecto_maria/static/v2/screens/review.js
A=tests/test_avisos1_seguro.py
FAM="$A::test_cada_400_que_cambia_de_pantalla_deja_el_motivo_a_la_vista"
sabotaje $M "el servidor no mira el borrado" \
  'return SEGURO_BORRADO if request.seguro_borrado else SEGURO_PARA_COMPLETAR' 'return SEGURO_PARA_COMPLETAR' \
  "FAILED $A::test_el_seguro_borrado_no_genera_y_dice_lo_que_paso"
sabotaje $F "borrarlo no lo marca" \
  '        op.seguro_borrado = true;
' '' \
  "FAILED $A::test_pasar_a_cif_marca_el_borrado_y_la_nota_lo_dice"
sabotaje $F "el pedido no dice que se borró" \
  '            seguro_borrado: !!op.seguro_borrado,
' '' \
  "FAILED $A::test_pasar_a_cif_marca_el_borrado_y_la_nota_lo_dice"
sabotaje $F "la nota dice que no se leyó" \
  '(seguroSinLeer(op) ? (op.seguro_borrado ?' '(seguroSinLeer(op) ? (false ?' \
  "FAILED $A::test_pasar_a_cif_marca_el_borrado_y_la_nota_lo_dice"
sabotaje $F "de vuelta a FOB la nota dice que no se leyó" \
  'mostrar && seguroSinLeer(op) ? (op.seguro_borrado ?' 'mostrar && seguroSinLeer(op) ? (false ?' \
  "FAILED $A::test_de_vuelta_a_fob_el_borrado_sigue_diciendo_lo_que_paso"
sabotaje proyecto_maria/static/v2/screens/semaforo.js "el semáforo dice que no se leyó" \
  "if (c === 'seguro' && op.seguro_borrado) {" 'if (false) {' \
  "FAILED $A::test_el_semaforo_dice_si_el_seguro_se_borro_o_no_se_leyo[True"
sabotaje $F "recalcularlo deja la marca de borrado" \
  '        delete op.seguro_borrado;
' '' \
  "FAILED $A::test_la_marca_de_borrado_se_va[recalcularlo]"
sabotaje $R "escribirlo deja la marca de borrado" \
  "            if (String(el.value).trim() !== '') delete op.seguro_borrado;
" '' \
  "FAILED $A::test_la_marca_de_borrado_se_va[escribirlo]"
sabotaje $R "vaciarlo borra la marca de borrado" \
  "if (String(el.value).trim() !== '') delete op.seguro_borrado;" 'delete op.seguro_borrado;' \
  "FAILED $A::test_vaciar_el_campo_deja_la_marca_de_borrado"
sabotaje $R "marcar no muestra el motivo" \
  '{ errEl.textContent = texto; errEl.hidden = false; }' '{ errEl.textContent = texto; }' \
  "FAILED $A::test_marcar_en_la_revision_pone_el_motivo_junto_al_campo"
sabotaje $R "marcar no lleva el campo a la vista" \
  "        if (el) { try { el.scrollIntoView({ block: 'center' }); } catch (_) {} }
" '' \
  "FAILED $A::test_marcar_en_la_revision_pone_el_motivo_junto_al_campo"
sabotaje $R "la revisión no exporta la marca" \
  '    CDI.marcarEnLaRevision = marcarEnLaRevision;
' '' \
  "FAILED $A::test_la_revision_exporta_la_marca"
sabotaje $F "el 400 del seguro no se marca" \
  "                    if (CDI.marcarEnLaRevision) CDI.marcarEnLaRevision('seguro', detail);
" '' \
  "FAILED $FAM[seguro_sin_leer]" "FAILED $FAM[seguro_borrado]"
sabotaje $F "se marca antes de entrar a la revisión" \
  "                    CDI.goTo('review');
                    if (CDI.marcarEnLaRevision) CDI.marcarEnLaRevision('seguro', detail);
" "                    if (CDI.marcarEnLaRevision) CDI.marcarEnLaRevision('seguro', detail);
                    CDI.goTo('review');
" \
  "FAILED $FAM[seguro_sin_leer]" "FAILED $FAM[seguro_borrado]"
sabotaje $F "el borrado no vuelve a la revisión" \
  '(no pudimos leerlo|el que calculó el sistema se borró)' '(no pudimos leerlo)' \
  "FAILED $FAM[seguro_borrado]"
sabotaje proyecto_maria/templates/dashboard_v2.html "la pista no pide el 0" \
  'Si la factura no trae seguro, escribí 0.</span>' 'Dejar en 0 si no aplica.</span>' \
  "FAILED $A::test_la_pista_del_seguro_pide_el_0_si_la_factura_no_lo_trae"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
