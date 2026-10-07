#!/usr/bin/env bash
# Negativos de PUNTA-A-PUNTA-1: cada sabotaje rompe una línea del lector del
# PDF, del mapeo del Excel, de la ruta o del generador, y la prueba de todo el recorrido
# (tests/test_punta_a_punta1.py) tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/punta_a_punta1.sh [SHA]
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
  local salida codigo
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_punta_a_punta1.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
E=proyecto_maria/pdf_extractor.py
G=proyecto_maria/core/maria_generator.py
P=tests/test_punta_a_punta1.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $P >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi
# Lector del PDF, la copia «pdf_directo» (la de producción): el flete leído se pierde.
sabotaje $E "el lector pierde el flete de la factura" \
  "                            'flete': _numero_factura(operacion.get('flete'), decimal) or 0.0," \
  "                            'flete': 0.0," \
  'FAILED tests/test_punta_a_punta1.py::test_pdf_de_punta_a_punta_da_el_archivo_real'
# Mapeo del Excel: el precio y el peso quedan cruzados.
sabotaje $M "el mapeo del Excel cruza precio y peso" \
  '                mapping[norm_to_orig[alias]] = canon' \
  '                mapping[norm_to_orig[alias]] = {"valor_unitario": "peso_unitario", "peso_unitario": "valor_unitario"}.get(canon, canon)' \
  'FAILED tests/test_punta_a_punta1.py::test_excel_de_punta_a_punta_da_el_archivo_real'
# Generador: la base imponible sin el seguro.
sabotaje $G "el generador deja el seguro fuera de la base imponible" \
  '        base_imponible = valor_total + flete_item + seguro_item' \
  '        base_imponible = valor_total + flete_item' \
  'FAILED tests/test_punta_a_punta1.py::test_pdf_de_punta_a_punta_da_el_archivo_real'
# Generador: el FOB de cada subítem sin la cantidad (con MARIA-5, el valor
# exacto de cada subítem, del que se reparte el MARTFOB).
sabotaje $G "el generador calcula el FOB del subítem sin la cantidad" \
  '                valor_de_la_linea({"cantidad": s.get("cantidad", 0) or 0,' \
  '                valor_de_la_linea({"cantidad": 1,' \
  'FAILED tests/test_punta_a_punta1.py::test_subitems_de_punta_a_punta_dan_el_archivo_real[pdf]'
# Ruta /generate_maria: la procedencia de la operación (MARIA-3) no llega a los productos.
sabotaje $M "la procedencia de la operación no llega a los productos" \
  '    procedencia = str(request.procedencia or "").strip()
    if not procedencia:' \
  '    procedencia = ""
    if not procedencia:' \
  'FAILED tests/test_punta_a_punta1.py::test_pdf_de_punta_a_punta_da_el_archivo_real'
# Generador: la NCM con el formato de la pantalla («8479.89.99.900 H») llega con el espacio.
sabotaje $G "el generador deja el espacio de la NCM de la pantalla" \
  "             ncm = ncm_raw.replace(' ', '')" \
  "             ncm = ncm_raw" \
  'FAILED tests/test_punta_a_punta1.py::test_pdf_de_punta_a_punta_da_el_archivo_real'
# Generador: el flete y el seguro, enteros a cada producto.
sabotaje $G "el generador no reparte el flete por el FOB" \
  '        proporcion = valor_total / fob_total if fob_total > 0 else 0' \
  '        proporcion = 1' \
  'FAILED tests/test_punta_a_punta1.py::test_dos_productos_reparten_flete_y_seguro_por_su_fob'
# Generador: el FOB total sólo del producto mayor.
sabotaje $G "el generador toma como FOB total el del producto mayor" \
  '    fob_total = sum(' \
  '    fob_total = max(' \
  'FAILED tests/test_punta_a_punta1.py::test_dos_productos_reparten_flete_y_seguro_por_su_fob'
# Lector: la coma decimal deja de reconocerse.
sabotaje $E "el lector lee siempre el punto como decimal" \
  "    vistos = {_separador_decimal(v) for v in valores if isinstance(v, str)}" \
  "    vistos = {'.'}" \
  'FAILED tests/test_punta_a_punta1.py::test_una_factura_con_coma_decimal_da_el_mismo_archivo'

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
