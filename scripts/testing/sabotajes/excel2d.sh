#!/usr/bin/env bash
# Negativos de EXCEL-2d: cada sabotaje deshace una línea de la pieza y
# tests/test_excel2d.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/excel2d.sh [SHA]
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
  local prueba="${esperado#FAILED }"; prueba="${prueba%%\[*}"
  local salida codigo inicio=$SECONDS corte=""
  salida="$(PYTHONUNBUFFERED=1 timeout "${LIMITE:-90}" "$PY" -m pytest -q --no-cov -p no:cacheprovider "$prueba" 2>&1)"; codigo=$?
  local tardo=$((SECONDS-inicio))
  [ "$codigo" -eq 124 ] && corte=", cortado a los ${LIMITE:-90} s"
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado» (${tardo} s$corte)"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}


F=proyecto_maria/security/file_security.py
M=proyecto_maria/main.py
T=tests/test_excel2d.py

if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $T >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

# formatCode y formatos de celda
sabotaje $F "un formato largo vuelve a abrirse" \
  '                if len(codigo) > _FORMATO_MAX_LARGO or codigo.count("[") > _FORMATO_MAX_CORCHETES:' \
  '                if codigo.count("[") > _FORMATO_MAX_CORCHETES:' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[largo]"
sabotaje $F "un formato con muchos corchetes vuelve a abrirse" \
  '                if len(codigo) > _FORMATO_MAX_LARGO or codigo.count("[") > _FORMATO_MAX_CORCHETES:' \
  '                if len(codigo) > _FORMATO_MAX_LARGO:' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[corchetes]"
sabotaje $F "los corchetes vuelven a contarse en los bytes, sin las entidades" \
  '                if len(codigo) > _FORMATO_MAX_LARGO or codigo.count("[") > _FORMATO_MAX_CORCHETES:' \
  '                if len(codigo) > _FORMATO_MAX_LARGO or z.read(parte).count(b"[") > _FORMATO_MAX_CORCHETES:' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[corchetes escritos como &#91;]"
sabotaje $F "muchos formatos de celda vuelven a abrirse" \
  '                if celdas > _MAX_FORMATOS_DE_CELDA:' \
  '                if False:' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[formatos de celda]"
sabotaje $F "los estilos de celda vuelven a contar como formatos de celda" \
  '                en_celdas += nombre == "cellXfs"' \
  '                en_celdas = 1' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[formatos de celda]"
sabotaje $F "un cellXfs vacío vuelve a cortar la cuenta de formatos de celda" \
  '                en_celdas -= 1' \
  '                en_celdas = 0' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[formatos de celda tras un cellXfs vacío]"
sabotaje $F "los formatos vuelven a no mirarse antes de abrir" \
  '        if ARC_STYLE in nombres and _formatos_que_excel_no_guarda(z, ARC_STYLE):' \
  '        if False:' \
  "FAILED $T::test_la_subida_cara_no_frena_a_nadie[120 000 corchetes en un formato]"

# sqref
sabotaje $F "muchos rangos vuelven a abrirse" \
  '            if rangos > _EXCEL_MAX_RANGOS:' \
  '            if False:' \
  "FAILED $T::test_la_subida_cara_no_frena_a_nadie[640 000 rangos de formato condicional]"
sabotaje $F "los sqref vuelven a contarse por elemento y no por rango" \
  '            rangos += len(elemento.get("sqref", "").split(None, _EXCEL_MAX_RANGOS))' \
  '            rangos += "sqref" in elemento.attrib' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[rangos]"

sabotaje $F "un sqref vuelve a partirse entero aunque pase el tope" \
  '            rangos += len(elemento.get("sqref", "").split(None, _EXCEL_MAX_RANGOS))' \
  '            rangos += len(elemento.get("sqref", "").split())' \
  "FAILED $T::test_la_subida_cara_no_frena_a_nadie[640 000 rangos de formato condicional]"

# .xls
sabotaje $F "los formatos de un .xls vuelven a no mirarse antes de abrir" \
  '    if _formatos_xls_que_excel_no_guarda(contents):' \
  '    if False:' \
  "FAILED $T::test_la_subida_cara_no_frena_a_nadie[tres formatos de 60 000 corchetes en un .xls]"
sabotaje $F "un .xls en OLE vuelve a no leerse por dentro" \
  '        datos = doc.get_named_stream("Workbook") or doc.get_named_stream("Book") or b""' \
  '        datos = b""' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[corchetes en un .xls]"
sabotaje $F "un .xls sin OLE vuelve a no mirarse" \
  $'    datos = contents\n    if contents[:8]' \
  $'    datos = b""\n    if contents[:8]' \
  "FAILED $T::test_un_formato_que_excel_no_guarda_se_rechaza[corchetes en un .xls sin OLE]"

# celdas combinadas
sabotaje $M "cada combinada vuelve a asignarse aparte en pandas" \
  $'            i, j = df.index.searchsorted([desde, hasta + 1])\n            if col not in nuevas:\n                nuevas[col] = df[col].to_numpy(copy=True)\n            nuevas[col][i:j] = valor\n            rellenadas.setdefault(col, set()).update(df.index[i:j])\n' \
  $'            filas = df.index[(df.index >= desde) & (df.index <= hasta)]\n            df.loc[filas, col] = valor\n            rellenadas.setdefault(col, set()).update(filas)\n' \
  "FAILED $T::test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas]"
sabotaje $M "las celdas rellenadas vuelven a copiarse en cada fila" \
  '    filas.attrs = {}' \
  '    pass' \
  "FAILED $T::test_la_subida_cara_no_frena_a_nadie[2499 combinadas en 4998 filas]"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
