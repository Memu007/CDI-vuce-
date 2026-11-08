#!/usr/bin/env bash
# Negativos de EXCEL-2c: cada sabotaje deshace una línea de la pieza y
# tests/test_excel2c.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/excel2c.sh [SHA]
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
T=tests/test_excel2c.py

if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $T >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

# Un tope por forma
sabotaje $F "una fila lejana vuelve a quedar en el carril liviano" \
  '        caro = (fila > tope_de_entorno("EXCEL_LIVIANO_FILAS", 20_000)' \
  '        caro = (False' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[fila con r]"
sabotaje $F "el tope de filas vuelve a no leerse del entorno" \
  'fila > tope_de_entorno("EXCEL_LIVIANO_FILAS", 20_000)' \
  'fila > 20_000' \
  "FAILED $T::test_el_tope_se_lee_del_entorno[EXCEL_LIVIANO_FILAS]"
sabotaje $F "muchas columnas vuelven a quedar en el carril liviano" \
  '                or ancho > tope_de_entorno("EXCEL_LIVIANO_COLUMNAS", 64)' \
  '                or False' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[columna con r]"
sabotaje $F "muchos estilos vuelven a quedar en el carril liviano" \
  '                and _mas_elementos_que(z, ARC_STYLE, tope_de_entorno("EXCEL_LIVIANO_ESTILOS", 5_000))' \
  '                and False' \
  "FAILED $T::test_muchos_estilos_van_al_carril_pesado"
sabotaje $F "muchos textos vuelven a quedar en el carril liviano" \
  '                and _mas_elementos_que(z, textos, tope_de_entorno("EXCEL_LIVIANO_TEXTOS", 40_000)))' \
  '                and False)' \
  "FAILED $T::test_muchos_textos_van_al_carril_pesado"
sabotaje $F "un libro caro vuelve a leerse en los hilos livianos" \
  '            liviano = liviano and not caro' \
  '            liviano = liviano' \
  "FAILED $T::test_la_subida_con_una_fila_lejana_lee_en_los_hilos_pesados"

# Cómo se mide la hoja
sabotaje $F "las filas sin r vuelven a no contar" \
  '                    fila_actual = fila_actual + 1 if r is None else int(float(r))' \
  '                    fila_actual = fila_actual if r is None else int(float(r))' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[filas sin r]"
sabotaje $F "la fila de una celda con r vuelve a no contar" \
  '                        fila = max(fila, f)' \
  '                        pass' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[celda con r en una fila sin r]"
sabotaje $F "las celdas sin r vuelven a no contar" \
  '                        columna_actual += 1' \
  '                        pass' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[celdas sin r]"
sabotaje $F "las celdas sin r vuelven a seguir la cuenta de la fila anterior" \
  $'                    columna_actual = 0\n' \
  $'                    pass\n' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[celdas sin r]"
sabotaje $F "la dimension vuelve a no contar las filas" \
  '                    fila = max(fila, ultima_fila or 0)' \
  '                    pass' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[dimension alta]"
sabotaje $F "la dimension vuelve a no contar las columnas" \
  '                    ancho = max(ancho, ultima_columna or 0)' \
  '                    pass' \
  "FAILED $T::test_la_forma_del_libro_decide_el_carril[dimension ancha]"
sabotaje $F "la dimension ancha vuelve a rechazar el libro" \
  '    return columna, fila, max(ancho, columna)' \
  '    return max(ancho, columna), fila, max(ancho, columna)' \
  "FAILED $T::test_la_dimension_ancha_no_rechaza_el_libro"
sabotaje $F "una referencia que no se lee vuelve a quedar en el carril liviano" \
  '                fila = math.inf' \
  '                pass' \
  "FAILED $T::test_una_referencia_que_no_se_lee_va_al_carril_pesado[fila]"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
