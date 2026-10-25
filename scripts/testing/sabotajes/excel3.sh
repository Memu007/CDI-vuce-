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
sabotaje $M "«Specification» le gana a un «Item» con el nombre" \
  '        detected_mapping = _item_o_especificacion(df, _detect_item_columns(list(df.columns)))' \
  '        detected_mapping = _detect_item_columns(list(df.columns))' \
  "FAILED $T::test_item_con_el_nombre_del_producto_sigue_siendo_la_descripcion"
sabotaje $M "«Freight cost» en Item cuenta como nombre" \
  $'            _es_fila_de_total(t) or _FILA_DE_FLETE_RE.match(t) or _FILA_DE_DESCUENTO_RE.match(t)\n            or _FILA_QUE_NO_ES_MERCADERIA_RE.match(t))' \
  '            False)' \
  "FAILED $T::test_un_flete_sin_monto_no_hereda_la_descripcion_del_grupo"
sabotaje $M "la cantidad vuelve a ser la de rollos" \
  $'    nuevo = {src: canon for src, canon in mapeo.items() if canon != "cantidad"}\n    nuevo[elegida] = "cantidad"' \
  '    nuevo = dict(mapeo)' "$XLS"
sabotaje $M "«Cantidad» con mayúscula vuelve a tapar la de m²" \
  $'                                  if str(c).strip().lower() in campos and c not in rename and c not in pesos])' \
  $'                                  if c in rename.values() and c not in rename])' \
  "FAILED $T::test_una_columna_cantidad_con_mayuscula_no_tapa_la_de_m2"
sabotaje $M "la medida de un rollo vuelve a ser la cantidad" \
  '                   and "total" in _normalize_header(c) and not es_peso(c)]' \
  '                   and not es_peso(c)]' \
  "FAILED $T::test_la_medida_de_un_rollo_o_una_caja_no_es_la_cantidad[area_de_un_rollo]"
sabotaje $M "el peso abreviado vuelve a ser la cantidad" \
  '                   and "total" in _normalize_header(c) and not es_peso(c)]' \
  '                   and "total" in _normalize_header(c)]' \
  "FAILED $T::test_el_peso_bruto_abreviado_no_es_la_cantidad"
sabotaje $M "«MT» vuelve a ser metro" \
  '    "m": "m", "meter": "m",' '    "m": "m", "mt": "m", "meter": "m",' \
  "FAILED $T::test_mt_no_se_declara_como_metros"
sabotaje $M "el mapeo guardado en rollos vuelve a ganar" \
  $'        effective_mapping, unidad, avisos_de_lo_usado = _cantidad_en_la_unidad_del_precio(\n            effective_mapping, list(df.columns))' \
  '        unidad, avisos_de_lo_usado = _unidad, []' \
  "FAILED $T::test_el_mapeo_guardado_con_la_cantidad_en_rollos_no_gana"
sabotaje $M "queda el aviso viejo del catálogo" \
  '            avisos_mapeo = [a for a in avisos_mapeo if not a.startswith(viejo)]' \
  '            avisos_mapeo = avisos_mapeo' \
  "FAILED $T::test_el_mapeo_guardado_con_la_cantidad_en_rollos_no_gana"
sabotaje $M "los renglones del grupo vuelven a quedar sin descripción" \
  '                descripcion, parte = grupo[0], parte or grupo[1]' '                pass' "$XLS"
sabotaje $M "hereda aunque el renglón no tenga medidas" \
  'if (not pieza and grupo and con_medidas and' 'if (not pieza and grupo and' \
  "FAILED $T::test_un_renglon_con_precio_y_sin_medidas_no_hereda"
sabotaje $M "un código distinto en cada renglón vuelve a heredar la descripción" \
  '            if grupo and parte and parte != grupo[1] and not descripcion:' \
  '            if False:' \
  "FAILED $T::test_con_un_codigo_distinto_en_cada_renglon_la_descripcion_no_se_hereda"
sabotaje $M "con la combinada se pierde el código de parte" \
  'descripcion in ("", grupo[0])' 'descripcion == ""' \
  "FAILED $T::test_con_la_especificacion_combinada_hacia_abajo_cada_renglon_conserva_su_codigo"
sabotaje $M "el flete y el descuento vuelven a no leerse" \
  '                        (flete if es_flete else descuento).append((_ + 2, abs(monto)))' \
  '                        pass' "$XLS"
sabotaje $M "el rótulo de otra columna no se mira" \
  '                (t for t in (_texto_de_celda(v) for v in row.values)' \
  '                (t for t in (_texto_de_celda(v) for v in ())' "$XLS"
sabotaje $M "una nota de flete en otra columna saca el renglón" \
  '            if sin_ncm_ni_origen and (descripcion or not con_medidas):' \
  '            if sin_ncm_ni_origen:' \
  "FAILED $T::test_una_nota_de_flete_en_otra_columna_de_un_renglon_no_lo_saca[Item]"
sabotaje $M "un producto «Discount …» vuelve a ser descuento" \
  ' and not _DESCUENTO_SOLO_RE.match(cargo):' ' and False:' \
  "FAILED $T::test_un_producto_que_empieza_con_discount_sigue_siendo_producto"
sabotaje $M "un descuento en porcentaje vuelve a entrar" \
  '                    if "%" in cargo or _monto_de_la_linea() < 0 or not valor_unitario:' '                    if False:' \
  "FAILED $T::test_un_descuento_en_porcentaje_no_se_lee_como_monto_ni_como_producto"
sabotaje $M "el descuento negativo en el precio vuelve a ser un producto" \
  '                    precio = _monto_de_fila(row[valor_col], decimal) or 0.0' \
  '                    precio = valor_unitario' \
  "FAILED $T::test_un_descuento_negativo_en_el_precio_sin_importe_tambien_se_lee"
sabotaje $M "«USD -850» vuelve a no leerse" \
  '    m = re.fullmatch(r"(\D*?)\s*[-−]\s*(\d.*)", t)' '    m = None' \
  "FAILED $T::test_un_descuento_con_moneda_adelante_se_lee"
sabotaje $M "un flete negativo vuelve a sumarse" \
  '                    if monto and (monto > 0 or not es_flete):' '                    if monto:' \
  "FAILED $T::test_un_flete_negativo_no_se_suma_como_flete"
sabotaje $M "la NCM vuelve a ser obligatoria" \
  'if not all([desc_col, cant_col, valor_col]):' 'if not all([pieza_col, desc_col, cant_col, valor_col]):' "$XLS"
sabotaje $M "ancho y largo no van en la descripción" \
  '        if agrupada and tamaño and item.descripcion:' '        if False:' "$XLS"
sabotaje $M "las medidas se pegan a una factura común" \
  '        if agrupada and tamaño and item.descripcion:' '        if tamaño and item.descripcion:' \
  "FAILED $T::test_las_medidas_no_se_pegan_a_una_factura_comun"
sabotaje $M "una medida larga sale en notación científica" \
  '    return f"{numero:.6f}".rstrip("0").rstrip(".").replace(".", ",")' \
  '    return f"{numero:g}".replace(".", ",")' \
  "FAILED $T::test_una_medida_larga_no_sale_en_notacion_cientifica"
sabotaje $M "la unidad no viaja con el producto" \
  '**({"unidad": unidad} if unidad else {}),' '' "$XLS"

# EXCEL-3b: lo que dejó el adversario, uno por punto.
B="FAILED $T::test_"
sabotaje $M "3b#2 un subtotal con largo y sin precio vuelve a ser producto" \
  '                    and (valor_unitario or (descripcion and cantidad))):' '                    and (cantidad or valor_unitario)):' \
  "${B}un_subtotal_sin_rotulo_ni_precio_con_medidas_no_es_un_producto[con_largo]"
for variante in flete descuento; do
  sabotaje $M "3b#5 una nota en Remarks vuelve a ser $variante" \
    '                (t for t in (_texto_de_celda(row[c]) for c in columnas_del_rotulo)' \
    '                (t for t in (_texto_de_celda(row[c]) for c in df.columns)' \
    "${B}un_texto_en_otra_columna_no_vuelve_flete_o_descuento_a_un_renglon[$variante]"
done
sabotaje $M "3b#5 el flete en la columna Item deja de leerse" \
  '    columnas_del_rotulo = ([item_col] if item_col else []) + [' \
  '    columnas_del_rotulo = [] + [' "$XLS"
sabotaje $M "3b-2#1 el rótulo a la izquierda de la descripción deja de leerse" \
  'c for c in list(df.columns)[:list(df.columns).index(desc_col)] if c != item_col]' ']' \
  "${B}el_flete_y_el_descuento_con_el_rotulo_a_la_izquierda_se_leen[No.]"
sabotaje $M "3b-2#5 un producto «Discount …» vuelve a cortar el grupo" \
  '                if es_descuento and not _DESCUENTO_SOLO_RE.match(cargo):' \
  $'                if es_descuento:\n                    grupo = None\n                    es_cargo = True\n                if es_descuento and not _DESCUENTO_SOLO_RE.match(cargo):' \
  "${B}un_producto_discount_abre_su_grupo"
sabotaje $M "3b-2#5 un descuento con texto sin leer no corta el grupo" \
  $'                        grupo = None\n                        descartes.append(_ + 2)  # un porcentaje no es un monto' \
  '                        descartes.append(_ + 2)' \
  "${B}un_descuento_con_texto_que_queda_sin_leer_corta_el_grupo"
sabotaje $M "3b-2#4 con el precio combinado los de abajo pierden código y medidas" \
  '                    and (valor_unitario or (descripcion and cantidad))):' '                    and valor_unitario):' \
  "${B}con_la_especificacion_y_el_precio_combinados_cada_renglon_conserva_codigo_y_medidas"
sabotaje $M "3b-2#2 el .xls vuelve a leerse sin sus combinadas" \
  '        combinadas = _combinadas_del_xls(ruta)' '        combinadas = []' \
  "${B}un_xls_con_la_especificacion_combinada_y_un_codigo_por_renglon_da_un_producto_por_renglon"
sabotaje $M "3b#4 un flete sin monto vuelve a abrir un grupo" \
  '            elif descripcion and not es_cargo:' '            elif descripcion:' \
  "${B}un_flete_sin_monto_corta_el_grupo"
sabotaje $M "3b#4 un descuento leído no corta el grupo" \
  '                    grupo = None  # el flete o el descuento cierran el grupo de arriba' \
  '                    pass' \
  "${B}un_descuento_leido_corta_el_grupo"
sabotaje $M "3b#3 un código nuevo sin especificación vuelve a heredar" \
  '            if grupo and parte and parte != grupo[1] and not descripcion:' \
  '            if False:' \
  "${B}un_codigo_nuevo_sin_especificacion_no_hereda_la_del_grupo_anterior"
sabotaje $M "3b#1 un descuento con texto y monto negativo vuelve a ser producto" \
  '                    if "%" in cargo or _monto_de_la_linea() < 0 or not valor_unitario:' '                    if "%" in cargo or not valor_unitario:' \
  "${B}un_descuento_con_texto_y_monto_negativo_se_avisa_y_no_es_producto[importe]"
sabotaje $M "3b#1 el monto negativo en el precio deja de leerse" \
  '                    precio = _monto_de_fila(row[valor_col], decimal) or 0.0' '                    precio = 0.0' \
  "${B}un_descuento_con_texto_y_monto_negativo_se_avisa_y_no_es_producto[precio]"
sabotaje $M "3b#9 un largo con su unidad la repite" \
  '                trae_unidad = numero is None and re.search(r"[^\W\d_]\s*$", texto)' \
  '                trae_unidad = False' \
  "${B}un_largo_escrito_con_su_unidad_no_la_repite"
sabotaje $M "3b-2#10 un largo con rango pierde la unidad" \
  '                trae_unidad = numero is None and re.search(r"[^\W\d_]\s*$", texto)' \
  '                trae_unidad = numero is None' \
  "${B}un_largo_con_rango_conserva_su_unidad"
sabotaje $M "3b#7 la unidad del precio no se avisa" \
  '        if unidad and not avisos_de_lo_usado and precio_col' '        if False and precio_col' \
  "${B}la_unidad_que_sale_del_encabezado_del_precio_se_avisa"
sabotaje $M "3b-2#9 el aviso de la unidad no nombra la cantidad" \
  'f"La unidad que va al TXT se leyó de los encabezados de la cantidad («{cant_col}») "' \
  'f"La unidad que va al TXT se leyó de los encabezados de la cantidad "' \
  "${B}la_unidad_de_la_cantidad_y_el_precio_se_avisa_con_las_dos_columnas"
sabotaje $M "3b#7 se avisa del precio una unidad que no salió de él" \
  ' and _unidad_de_columna(precio_col, True) == unidad:' ':' \
  "${B}una_unidad_que_sale_solo_de_la_cantidad_no_avisa_del_precio"

sabotaje $M "3b-3#1 el origen combinado vuelve producto al flete" \
  '            sin_ncm_ni_origen = not pieza and not _texto_de_celda(origen_propio)' \
  '            sin_ncm_ni_origen = not pieza and not _texto_de_celda(celda_origen)' \
  "${B}un_origen_combinado_que_alcanza_al_flete_no_lo_vuelve_producto[descripcion]"
sabotaje $M "3b-3#1 el origen combinado vuelve producto al seguro" \
  '            sin_ncm_ni_origen = not pieza and not _texto_de_celda(origen_propio)' \
  '            sin_ncm_ni_origen = not pieza and not _texto_de_celda(celda_origen)' \
  "${B}un_origen_combinado_que_alcanza_al_seguro_no_lo_vuelve_producto"
sabotaje $M "3b-3#1 las celdas copiadas no siguen al renombre de la columna" \
  '                    rename.get(c, c): f for c, f in' '                    c: f for c, f in' \
  "${B}un_origen_combinado_que_alcanza_al_flete_no_lo_vuelve_producto[descripcion]"
sabotaje $M "3b-3#1 el producto pierde el origen combinado" \
  '            celda_origen = row[origen_col] if origen_col else None' \
  '            celda_origen = row[origen_col] if origen_col and _propia(origen_col) else None' \
  "${B}un_origen_combinado_que_alcanza_al_flete_no_lo_vuelve_producto[descripcion]"
sabotaje $M "3b-3#3 la especificación copiada tapa el subtotal" \
  '            rotulo = descripcion_propia or next(' '            rotulo = descripcion or next(' \
  "${B}una_especificacion_combinada_que_alcanza_al_subtotal_no_lo_vuelve_producto"
sabotaje $M "3b-3#1 la descripción copiada tapa el rótulo del flete" \
  '            cargo = descripcion_propia or next(' '            cargo = descripcion or next(' \
  "${B}una_descripcion_combinada_que_alcanza_al_flete_no_lo_vuelve_producto"
sabotaje $M "3b-3#2 una nota de descuento sin precio abre un grupo" \
  '                    if "%" in cargo or _monto_de_la_linea() < 0 or not valor_unitario:' \
  '                    if "%" in cargo or _monto_de_la_linea() < 0:' \
  "${B}una_nota_de_descuento_sin_precio_no_abre_un_grupo"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
