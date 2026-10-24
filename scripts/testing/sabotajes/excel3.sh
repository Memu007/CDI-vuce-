#!/usr/bin/env bash
# Negativos de EXCEL-3: cada sabotaje deshace una línea de la pieza y
# tests/test_excel3.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/excel3.sh [SHA]
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_excel3.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
T=tests/test_excel3.py
XLS="FAILED $T::test_la_proforma_xls_se_lee_tal_como_viene"

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $T >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $M "«Item» vuelve a ser la descripción" \
  '"specification", "specifications", "item",' '"item",' "$XLS"
sabotaje $M "la cantidad vuelve a ser la de rollos" \
  $'    nuevo = {src: canon for src, canon in mapeo.items() if canon != "cantidad"}\n    nuevo[elegida] = "cantidad"' \
  '    nuevo = dict(mapeo)' "$XLS"
sabotaje $M "el mapeo guardado en rollos vuelve a ganar" \
  $'        effective_mapping, unidad, avisos_de_lo_usado = _cantidad_en_la_unidad_del_precio(\n            effective_mapping, list(df.columns))' \
  '        unidad, avisos_de_lo_usado = _unidad, []' \
  "FAILED $T::test_el_mapeo_guardado_con_la_cantidad_en_rollos_no_gana"
sabotaje $M "los renglones del grupo vuelven a quedar sin descripción" \
  $'                descripcion, parte = grupo\n' $'                pass\n' "$XLS"
sabotaje $M "hereda aunque el renglón no tenga medidas" \
  'if (not pieza and not parte and grupo and con_medidas and' 'if (not pieza and not parte and grupo and' \
  "FAILED $T::test_un_subtotal_sin_rotulo_ni_medidas_no_es_un_producto"
sabotaje $M "con la combinada se pierde el código de parte" \
  'descripcion in ("", grupo[0])' 'descripcion == ""' \
  "FAILED $T::test_con_la_especificacion_combinada_hacia_abajo_cada_renglon_conserva_su_codigo"
sabotaje $M "el flete y el descuento vuelven a no leerse" \
  $'                    (flete if _FILA_DE_FLETE_RE.match(rotulo) else descuento).append((_ + 2, monto))\n                    continue' \
  '                    pass' "$XLS"
sabotaje $M "el rótulo de otra columna no se mira" \
  '                 if t and _numero_factura(t, decimal) is None' \
  '                 if False and t and _numero_factura(t, decimal) is None' "$XLS"
sabotaje $M "un flete sin monto sigue en el grupo de arriba" \
  $'                grupo = None  # nunca hereda la descripción de arriba\n' '' \
  "FAILED $T::test_un_flete_sin_monto_no_hereda_la_descripcion_del_grupo"
sabotaje $M "el peso en kilos pasa a ser la cantidad" \
  '             and not _es_nombre_de_peso(_normalize_header(c))]' ']' \
  "FAILED $T::test_precio_por_kilo_no_toma_el_peso_como_cantidad"
sabotaje $M "la NCM vuelve a ser obligatoria" \
  'if not all([desc_col, cant_col, valor_col]):' 'if not all([pieza_col, desc_col, cant_col, valor_col]):' "$XLS"
sabotaje $M "ancho y largo no van en la descripción" \
  '            if tamaño and descripcion:' '            if False:' "$XLS"
sabotaje $M "el descuento negativo en el precio vuelve a ser un producto" \
  '                    precio = _monto_de_fila(row[valor_col], decimal) or 0.0' \
  '                    precio = valor_unitario' \
  "FAILED $T::test_un_descuento_negativo_en_el_precio_sin_importe_tambien_se_lee"
sabotaje $M "la unidad no viaja con el producto" \
  '**({"unidad": unidad} if unidad else {}),' '' "$XLS"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
