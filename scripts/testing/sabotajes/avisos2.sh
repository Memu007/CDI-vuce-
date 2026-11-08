#!/usr/bin/env bash
# Negativos de AVISOS-2: cada sabotaje deja pasar al TXT una destinación que no
# es un código de 4 letras o números ASCII, una de importación en una
# exportación, normaliza un texto enorme entero, vuelve al texto viejo del
# seguro borrado o deja al lector ver sólo lo que saca strip, y el caso tiene
# que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/avisos2.sh [SHA]
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
CASOS=(tests/test_avisos2.py tests/test_doc1_documentos.py)

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
M=proyecto_maria/main.py
A=tests/test_avisos2.py
FORMA="$A::test_lo_que_no_es_un_codigo_da_400_y_no_genera"
EXP="$A::test_la_exportacion_sólo_genera_con_una_ec"
FORMA_RE='if not re.fullmatch(r"[A-Za-z0-9]{4}", codigo):'

sabotaje $G "no mira la forma" \
  "$FORMA_RE" 'if False:' \
  "FAILED $FORMA[IC041-/generate_maria]" "FAILED $EXP[EC011-400]"
sabotaje $G "acepta de 3 a 5" \
  "$FORMA_RE" 'if not re.fullmatch(r"[A-Za-z0-9]{3,5}", codigo):' \
  "FAILED $FORMA[IC041-/generate_maria/avisos]" "FAILED $FORMA[IC0-/generate_maria]"
sabotaje $G "acepta letras y números de cualquier alfabeto" \
  "$FORMA_RE" 'if not re.fullmatch(r"\w{4}", codigo):' \
  "FAILED $FORMA"'[\uff29\uff23\uff10\uff14-/generate_maria]' "FAILED $FORMA"'[\u0131c04-/generate_maria/avisos]'
sabotaje $G "la exportación acepta una de importación" \
  'if es_exportacion(tipo_destinacion) != exportacion:' 'if es_exportacion(tipo_destinacion) and not exportacion:' \
  "FAILED $EXP[IC04-400]" "FAILED $EXP[TRAN-400]"
sabotaje $G "normaliza el texto entero" \
  'str(tipo_destinacion or "").strip()[:64]' 'str(tipo_destinacion or "").strip()' \
  "FAILED $A::test_un_texto_enorme_no_se_normaliza_entero"
sabotaje $G "corta antes de sacar los blancos" \
  'str(tipo_destinacion or "").strip()[:64]' 'str(tipo_destinacion or "")[:64]' \
  "FAILED $EXP[70blancos-EC01-200]" \
  "FAILED tests/test_doc1_documentos.py::test_ec_directa_nunca_entra_a_importacion[70blancos-EC01-/generate_maria]" \
  "FAILED $A::test_el_lector_rechaza_la_exportacion_con_lo_invisible_adelante[documento-70blancos-"
sabotaje $G "el generador corta en vez de rechazar" \
  '    tipo_destinacion = destinacion_del_txt(tipo_destinacion)
' '    if es_exportacion(tipo_destinacion):
        raise ValueError(EXPORTACION_EN_IMPORTACION)
    tipo_destinacion = (str(tipo_destinacion or "").strip().upper() or "IC04")[:4]
' \
  "FAILED $A::test_el_generador_tampoco_escribe_lo_que_no_es_un_codigo[IC041]"
sabotaje $M "la exportación no mira la destinación" \
  '    request.tipo_destinacion = _destinacion_o_400(request.tipo_destinacion, exportacion=True)
' '' \
  "FAILED $EXP[IC04-400]" "FAILED $EXP[EC011-400]"
sabotaje $M "la exportación escribe la destinación sin normalizar" \
  '    request.tipo_destinacion = _destinacion_o_400(request.tipo_destinacion, exportacion=True)' \
  '    _destinacion_o_400(request.tipo_destinacion, exportacion=True)' \
  "FAILED $EXP[ ec01 -200]"
sabotaje $M "los avisos no miran la forma" \
  '    _destinacion_o_400(request.tipo_destinacion)
    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])
    _textos_como_van_al_txt(request)' \
  '    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])
    _textos_como_van_al_txt(request)' \
  "FAILED $FORMA[IC041-/generate_maria/avisos]"
sabotaje $M "el seguro borrado vuelve a decir que está en el precio" \
  'se borró al cambiar el incoterm. ' 'se borró al pasar a un incoterm que ya lo lleva en el precio. ' \
  "FAILED $A::test_el_seguro_borrado_de_vuelta_a_fob_dice_lo_que_paso"
sabotaje proyecto_maria/pdf_extractor.py "el lector sólo saca lo que saca strip" \
  'or any(es_exportacion(destinacion) for destinacion in (' \
  'or any(str(destinacion or "").strip().upper().startswith("EC") for destinacion in (' \
  "FAILED $A::test_el_lector_rechaza_la_exportacion_con_lo_invisible_adelante"'[documento-\u200bEC01-'

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
