#!/usr/bin/env bash
# Negativos de EXCEL-1: cada sabotaje deshace un arreglo y las pruebas
# tienen que ponerse rojas por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/excel1.sh [SHA]
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_excel1_rendimiento.py tests/test_excel1_lectura.py tests/test_excel1_txt.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
F=proyecto_maria/security/file_security.py
T=tests/test_excel1_rendimiento.py
L=tests/test_excel1_lectura.py
sabotaje $M "el Excel v2 se vuelve a leer en el hilo del servidor" \
  '        df = await _leer_pdf_aparte(
            _leer_excel_ruta, temp_filename, engine, tuple((mapping or {}).items()),
            limite=_excel_read_timeout_s(), que="el Excel", pool=_pool_lectura_excel_carril(liviano),
        )
' \
  '        df = _leer_excel_ruta(temp_filename, engine, tuple((mapping or {}).items()))
' \
  "FAILED $T::test_health_responde_mientras_se_lee_un_excel[upload_excel_v2]"
sabotaje $M "leer un Excel pierde el tiempo máximo" \
  '    return _segundos_de_entorno("EXCEL_READ_TIMEOUT_S", 60.0)' \
  '    return 1e9' \
  "FAILED $T::test_leer_un_excel_tiene_tiempo_maximo[ncm_import_historial]"
sabotaje $F "validar el Excel vuelve al hilo del servidor" \
  'asyncio.get_running_loop().run_in_executor(
                        _pool_validar_excel_carril(liviano), _abrir_excel, contents, file_ext
                    ),' \
  'asyncio.sleep(0, _abrir_excel(contents, file_ext)),' \
  "FAILED $T::test_health_responde_mientras_se_valida_un_excel"
sabotaje $M "«Valor» vuelve a ganar sobre el precio unitario" \
  '        "valorunitario", "preciounitario", "unitprice",' \
  '        "valorunitario", "valor", "preciounitario", "unitprice",' \
  "FAILED $L::test_precio_unitario_gana_sobre_valor_total"
# Con MARIA-5 integrada (D23): el bruto se reconoce por el nombre y va
# último; el sabotaje lo vuelve de una unidad.
sabotaje $M "el peso bruto vuelve a usarse como peso unitario" \
  '    if "bruto" in normal or "gross" in normal:
        return "bruto_unidad" if _bruto_de_una_unidad(normal) else "bruto"' \
  '    if False:
        return "bruto"' \
  "FAILED $L::test_peso_bruto_o_total_no_se_toma_como_peso_unitario"
sabotaje $M "las filas de subtotal vuelven a entrar" \
  '            if _es_fila_de_total(rotulo or pieza):' \
  '            if False:' \
  "FAILED $L::test_fila_de_subtotal_no_entra_como_item"
sabotaje $M "«.XLSX» en mayúsculas vuelve a fallar" \
  '        engine = "openpyxl" if temp_filename.lower().endswith(".xlsx") else "xlrd"' \
  '        engine = "openpyxl" if temp_filename.endswith(".xlsx") else "xlrd"' \
  "FAILED $L::test_extension_en_mayusculas"
sabotaje $M "la unidad entre paréntesis vuelve a romper el encabezado" \
  '_normalize_header(re.sub(r"\(.*?\)", "", str(h or "")))' \
  '_normalize_header(str(h or ""))' \
  "FAILED $L::test_encabezados_con_unidades_entre_parentesis"
sabotaje $M "el mapeo guardado vuelve a dejar afuera lo detectado" \
  '        elegido = g or d' \
  '        elegido = g' \
  "FAILED $L::test_mapeo_guardado_no_deja_afuera_encabezados_nuevos"
sabotaje $M "lo detectado vuelve a pisar el mapeo corregido a mano" \
  '            if rg is not None and rd is not None and rd < rg:' \
  '            if rd is not None:' \
  "FAILED $L::test_mapeo_corregido_a_mano_gana_sobre_lo_detectado"
sabotaje $M "el mapeo aprendido vuelve a pisar el precio unitario" \
  '            if rg is not None and rd is not None and rd < rg:' \
  '            if False:' \
  "FAILED $L::test_mapeo_aprendido_no_pisa_el_precio_unitario_ni_el_peso_neto"
sabotaje $F "validar el Excel vuelve a los hilos compartidos" \
  '                        _pool_validar_excel_carril(liviano), _abrir_excel, contents, file_ext' \
  '                        None, _abrir_excel, contents, file_ext' \
  "FAILED $L::test_validar_el_excel_usa_su_propio_grupo_de_hilos"
sabotaje $M "la fila de ejemplo de la plantilla vuelve a entrar" \
  '            if descripcion.strip().lower() == _FILA_DE_EJEMPLO_PLANTILLA.lower():' \
  '            if False:' \
  "FAILED $L::test_la_fila_de_ejemplo_de_la_plantilla_no_entra"
sabotaje $M "el catálogo vuelve a guardar dos columnas para un campo" \
  '        if canon in vistos:' \
  '        if False:' \
  "FAILED $L::test_catalogo_con_dos_columnas_para_el_mismo_campo_no_se_guarda"
sabotaje $M "dos columnas guardadas para un campo vuelven a pasar sin aviso" \
  '        if canon in guardado_por_campo:' \
  '        if False:' \
  "FAILED $L::test_mapeo_viejo_con_dos_columnas_para_el_mismo_campo_avisa_y_no_da_500"
sabotaje $M "vuelven las dos columnas con el mismo nombre (500)" \
  '            df = df.drop(columns=[c for c in df.columns
                                  if str(c).strip().lower() in campos and c not in rename and c not in pesos])' \
  '            pass' \
  "FAILED $L::test_columna_con_el_nombre_del_campo_y_mapeo_a_otra_no_da_500"
sabotaje $M "vuelve a saltearse cualquier producto que empiece con «Total»" \
  '            and all(p in _PALABRAS_DE_TOTAL or p in _PALABRAS_DE_MONTO for p in palabras))' \
  '            and palabras[0] in _PALABRAS_DE_TOTAL)' \
  "FAILED $L::test_productos_que_empiezan_con_total_no_se_pierden"
sabotaje $M "los totales con moneda vuelven a entrar como producto" \
  '    "usd", "us$", "u$s", "eur", "cny", "rmb", "ars", "$", "€", "¥",' \
  '    "us$", "u$s", "eur", "cny", "rmb", "ars", "$", "€", "¥",' \
  "FAILED $L::test_filas_de_total_con_moneda_o_idioma_no_entran[TOTAL USD]"
sabotaje $M "los totales en otro idioma vuelven a entrar como producto" \
  '    "合计", "合計", "总计", "總計", "小计", "小計",' \
  '    "合計", "总计", "總計", "小计", "小計",' \
  "FAILED $L::test_filas_de_total_con_moneda_o_idioma_no_entran["
# El defecto viejo: sólo se miraba la descripción. Con «rotulo» solo no
# alcanza: el rótulo ya toma «TOTAL AMOUNT» de la columna de código.
sabotaje $M "el total en la columna de código vuelve a entrar" \
  '            if _es_fila_de_total(rotulo or pieza):' \
  '            if _es_fila_de_total(descripcion):' \
  "FAILED $L::test_total_en_la_columna_de_codigo_no_entra"
# Desde EXCEL-3c el filtro decide con el rótulo propio de la fila (cargo).
sabotaje $M "el flete vuelve a entrar como producto" \
  $'            else:\n                no_es_mercaderia = bool(_FILA_QUE_NO_ES_MERCADERIA_RE.match(cargo))' \
  $'            else:\n                no_es_mercaderia = False' \
  "FAILED $L::test_total_flete_y_condiciones_no_son_productos"
sabotaje $M "vuelve a descartarse todo producto sin NCM ni origen" \
  $'        if no_es_mercaderia:\n            descartes.append(fila)' \
  $'        if no_es_mercaderia or (not item.pieza and item.origen == "XX"\n                                and any(c[4].pieza or c[4].origen != "XX" for c in candidatos)):\n            descartes.append(fila)' \
  "FAILED $L::test_productos_sin_ncm_ni_origen_entran_aunque_otra_fila_los_traiga"
# Con MARIA-5 integrada (D23): entre «Peso (kg)» y «Peso (bruto)» decide el
# rango del peso, no el orden de las columnas.
sabotaje $M "«Peso (neto)» y «Peso (bruto)» vuelven a confundirse" \
  '_RANGO_DE_PESO = {"neto": 0, "linea": 1, "unidad": 2, "dudosa": 3, "bruto": 4, "bruto_unidad": 4}' \
  '_RANGO_DE_PESO = {"neto": 0, "linea": 1, "unidad": 4, "dudosa": 3, "bruto": 2, "bruto_unidad": 4}' \
  "FAILED $L::test_peso_ambiguo_entre_parentesis_queda_vacio_y_no_se_adivina"
sabotaje $M "el Excel vuelve a usar los hilos del PDF" \
  'def _pool_lectura_excel():
    global _POOL_LECTURA_EXCEL' \
  'def _pool_lectura_excel():
    return _pool_lectura_pdf()
    global _POOL_LECTURA_EXCEL' \
  "FAILED $T::test_excel_y_pdf_no_comparten_los_hilos_de_lectura"
sabotaje $F "un .xlsx que se descomprime a gigas vuelve a abrirse" \
  "    if file_ext == '.xlsx' and _excel_descomprimido_bytes(contents) > _excel_max_descomprimido_bytes():" \
  "    if False:" \
  "FAILED $L::test_xlsx_que_se_descomprime_a_gigas_se_rechaza_antes_de_abrirlo"
sabotaje $M "las filas vacías vuelven a recorrerse una por una" \
  '    return _rellenar_combinadas(df, combinadas, mapeo)[~vacias]' \
  '    return _rellenar_combinadas(df, combinadas, mapeo)' \
  "FAILED $L::test_celda_en_la_ultima_fila_no_recorre_un_millon_de_filas"
sabotaje $F "el índice del .xlsx vuelve a mirarse en el hilo del servidor" \
  "            try:
                hojas = await asyncio.wait_for(" \
  "            if file_ext == '.xlsx' and _excel_descomprimido_bytes(contents) > _excel_max_descomprimido_bytes():
                raise HTTPException(400, 'demasiado grande descomprimido')
            try:
                hojas = await asyncio.wait_for(" \
  "FAILED $L::test_el_indice_del_xlsx_se_mira_fuera_del_hilo_del_servidor"
sabotaje $M "deja de haber tope de filas" \
  '        if len(df) > _MAX_FILAS_EXCEL:' \
  '        if False:' \
  "FAILED $L::test_demasiadas_filas_se_rechazan_con_mensaje_claro"
sabotaje $M "las filas descartadas dejan de avisarse" \
  '            "filas_descartadas": len(descartes),' \
  '            "filas_descartadas": 0,' \
  "FAILED $L::test_filas_sin_descripcion_ni_ncm_se_avisan"
sabotaje $M "las filas con datos faltantes vuelven a perderse" \
  '            # Sin descripción ni NCM no hay ítem que mostrar: se avisa.
            if not pieza and not descripcion:' \
  '            # Sin descripción ni NCM no hay ítem que mostrar: se avisa.
            if not pieza or not descripcion:' \
  "FAILED $L::test_filas_con_datos_faltantes_entran_vacias_y_no_inventadas"
sabotaje $M "vuelve la cantidad 1 inventada" \
  '                "cantidad": float(getattr(it, "cantidad", 0) or 0),' \
  '                "cantidad": float(getattr(it, "cantidad", 1) or 1),' \
  "FAILED $L::test_filas_con_datos_faltantes_entran_vacias_y_no_inventadas"
sabotaje $M "los números en texto vuelven a leerse con float" \
  '                return (_numero_factura(row[col], decimal) or 0.0) if col else 0.0' \
  '                return float(row[col]) if col else 0.0' \
  "FAILED $L::test_numeros_escritos_como_texto"
sabotaje $M "pandas vuelve a convertir el texto de las celdas" \
  '    df = _con_encabezado(pd.read_excel(origen, engine=engine, dtype=object), nombres)' \
  '    df = _con_encabezado(pd.read_excel(origen, engine=engine), nombres)' \
  "FAILED $L::test_numeros_escritos_como_texto[1.500-0]"
sabotaje $M "la NCM numérica vuelve a salir con .0" \
  '    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))' \
  '    if False:
        return str(int(valor))' \
  "FAILED $L::test_extraccion_con_ncm_leida_como_numero_decimal"
sabotaje $M "el país vuelve a cortarse a tres letras" \
  '                origen=_origen_desde_factura(celda_origen) or "XX",' \
  '                origen=str(celda_origen).upper()[:3] or "XX",' \
  "FAILED $L::test_pais_por_nombre_no_se_corta"
sabotaje $M "«País de origen» deja de reconocerse" \
  '        "paisdeorigen", "countryoforigin", "origin", "madein",' \
  '        "countryoforigin", "origin", "madein",' \
  "FAILED tests/test_excel1_txt.py::test_excel_y_pdf_dan_el_mismo_txt"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
