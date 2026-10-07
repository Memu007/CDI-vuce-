#!/usr/bin/env bash
# Negativos de EXCEL-2: cada sabotaje deshace una línea de la pieza y
# tests/test_excel2.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/excel2.sh [SHA]
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_excel2.py 2>&1)"; codigo=$?
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
C=proyecto_maria/core/controles_maria.py
P=tests/test_excel2.py
T=tests/test_excel2.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $P >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

# De paso: montos que no son números y los otros CUIT
sabotaje $C "un entero enorme vuelve a dar OverflowError" \
  $'    except OverflowError:\n        return math.inf' \
  $'    except OverflowError:\n        raise' \
  "FAILED $T::test_un_monto_que_no_es_un_numero_da_400[item0-"
sabotaje $C "una lista vuelve a no contar como monto inválido" \
  $'    if isinstance(valor, (list, dict)):\n        return math.nan' \
  $'    if isinstance(valor, (list, dict)):\n        return None' \
  "FAILED $T::test_un_monto_que_no_es_un_numero_da_400[item3-"
sabotaje $M "/generate_maria vuelve a seguir con un monto que no es número" \
  '        if montos_fuera_de_rango(request.items, {}):' \
  '        if False:' \
  "FAILED $T::test_un_monto_que_no_es_un_numero_da_400[item3-"
sabotaje $M "la exportación vuelve a validar antes los montos" \
  '            raise HTTPException(status_code=400, detail={"errors": _montos})' \
  '            pass' \
  "FAILED $T::test_la_exportacion_con_un_monto_que_no_es_un_numero_da_400"
sabotaje $C "los otros CUIT vuelven a aceptar dígitos raros" \
  '    return any(c.isdigit() and not ("0" <= c <= "9") for c in str(valor or ""))' \
  '    return False' \
  "FAILED $T::test_cuit_del_despachante_o_id_del_vendedor_con_digitos_raros_no_deja_generar[vendedor_id-"
# D26 (a)
sabotaje $F "validar vuelve a abrir el libro con openpyxl" \
  '        return _contar_hojas_xlsx(contents)' \
  '        import openpyxl; return len(openpyxl.load_workbook(io.BytesIO(contents), read_only=True).sheetnames)' \
  "FAILED $T::test_validar_un_xlsx_no_lo_abre_con_openpyxl"
sabotaje $F "los textos compartidos enormes vuelven a pasar" \
  '        if textos and textos in nombres and z.getinfo(textos).file_size > tope_textos:' \
  '        if False:' \
  "FAILED $T::test_textos_compartidos_enormes_se_rechazan_antes_de_abrir"
sabotaje $F "una primera hoja enorme vuelve a pasar" \
  '        if hojas and z.getinfo(hojas[0][1]).file_size > tope_hoja:' \
  '        if False:' \
  "FAILED $T::test_una_primera_hoja_enorme_se_rechaza_antes_de_abrir"
sabotaje $M "leer la factura vuelve a abrir el libro entero" \
  $'        contenido, combinadas = _xlsx_solo_primera_hoja(ruta)\n        origen = _io.BytesIO(contenido)' \
  $'        contenido, combinadas = _xlsx_solo_primera_hoja(ruta)\n        origen = ruta' \
  "FAILED $T::test_leer_la_factura_abre_un_libro_con_una_sola_hoja"
sabotaje $M "el historial vuelve a abrir el libro entero" \
  '        contenido, _ = _xlsx_solo_primera_hoja(content)' \
  '        contenido = content' \
  "FAILED $T::test_el_historial_en_excel_lee_solo_la_primera_hoja"
# D18
sabotaje $M "el encabezado vuelve a buscarse sólo en la fila 1" \
  '    if len(_detect_item_columns(actuales)) + sum(1 for c in actuales if c in conocidas) >= 3:' \
  '    if True:' \
  "FAILED $T::test_el_encabezado_no_tiene_que_estar_en_la_fila_1"
sabotaje $M "la columna de origen vuelve a ser obligatoria" \
  '    if not all([pieza_col, desc_col, cant_col, valor_col]):' \
  '    if not all([pieza_col, desc_col, origen_col, cant_col, valor_col]):' \
  "FAILED $T::test_sin_columna_de_origen_entra_con_el_origen_vacio_y_avisa"
sabotaje $M "sin columna de origen deja de avisarse" \
  '        if not find_column(df.columns, ["origen", "Origen", "pais", "País", "country", "Country"]):' \
  '        if False:' \
  "FAILED $T::test_sin_columna_de_origen_entra_con_el_origen_vacio_y_avisa"
sabotaje $M "una celda combinada vuelve a valer sólo en su primera fila" \
  '            df.loc[filas, col] = valor' \
  '            pass' \
  "FAILED $T::test_una_celda_combinada_hacia_abajo_vale_para_todas_sus_filas"
# Aviso de mapeo
sabotaje $M "el aviso de mapeo deja de nombrar la columna" \
  $'                f"Para «{_NOMBRE_DEL_CAMPO.get(canon, canon)}» se usó la columna «{elegido}» "' \
  $'                f"Para «{_NOMBRE_DEL_CAMPO.get(canon, canon)}» se usó una columna "' \
  "FAILED $T::test_el_aviso_de_mapeo_nombra_la_columna_que_se_uso"
# CSV del historial
sabotaje $M "el CSV vuelve a leerse sólo como UTF-8" \
  '                texto = crudo.decode("cp1252", errors="replace")' \
  '                texto = crudo.decode("utf-8", errors="replace")' \
  "FAILED $T::test_el_csv_del_historial_se_lee_con_coma_punto_y_coma_latin1_o_bom[latin-1-"
sabotaje $M "el CSV vuelve a leerse siempre con coma" \
  $'        separador = max((",", ";", "\\t"), key=encabezado.count)' \
  $'        separador = ","' \
  "FAILED $T::test_el_csv_del_historial_se_lee_con_coma_punto_y_coma_latin1_o_bom[punto y coma-"
# Lo que encontró la revisión
sabotaje $M "una combinada vuelve a copiar números hacia abajo" \
  $'        if lo_que_es and lo_que_es <= _COMBINADAS_SE_COPIAN:' \
  $'        if True:\n            lo_que_es = lo_que_es or {"descripcion"}' \
  "FAILED $T::test_una_combinada_con_cantidad_y_precio_no_duplica_el_producto"
sabotaje $M "las combinadas vuelven a copiarse antes de buscar el encabezado" \
  '    df = _con_encabezado(pd.read_excel(origen, engine=engine, dtype=object), nombres)' \
  '    df = _con_encabezado(_rellenar_combinadas(pd.read_excel(origen, engine=engine, dtype=object), combinadas, mapeo), nombres)' \
  "FAILED $T::test_un_encabezado_en_dos_filas_combinadas_no_da_un_producto_fantasma"
sabotaje $F "el libro vuelve a buscarse en xl/workbook.xml" \
  '    libro = _find_workbook_part(manifiesto).PartName[1:]' \
  '    libro = "xl/workbook.xml"' \
  "FAILED $T::test_un_libro_senuelo_no_engana_a_la_validacion_ni_a_la_lectura"
sabotaje $F "los textos compartidos vuelven a buscarse por nombre" \
  '    return libro, get_rels_path(libro), (textos.PartName[1:] if textos is not None else None)' \
  '    return libro, get_rels_path(libro), "xl/sharedStrings.xml"' \
  "FAILED $T::test_textos_compartidos_con_otro_nombre_tambien_se_rechazan"
sabotaje $M "un encabezado enorme vuelve a normalizarse" \
  '    headers = [h for h in headers if len(str(h or "")) <= 200]' \
  '    pass' \
  "FAILED $T::test_un_texto_enorme_arriba_no_traba_la_busqueda_del_encabezado"
sabotaje $M "el mapeo del cliente deja de contar para el encabezado" \
  '    if len(_detect_item_columns(actuales)) + sum(1 for c in actuales if c in conocidas) >= 3:' \
  '    if len(_detect_item_columns(actuales)) >= 3:' \
  "FAILED $T::test_con_mapeo_del_cliente_el_pie_no_se_toma_como_encabezado"
sabotaje $M "un CSV UTF-8 con un byte raro vuelve a leerse como cp1252" \
  '            if validas and len(validas) >= sueltos:' \
  '            if False:' \
  "FAILED $T::test_un_csv_utf8_con_un_byte_raro_no_se_rompe_entero"
sabotaje $M "el separador vuelve a contar lo que va entre comillas" \
  $'        encabezado = _re.sub(r\'"[^"]*"\', "", texto.split("\\n", 1)[0])' \
  $'        encabezado = texto.split("\\n", 1)[0]' \
  "FAILED $T::test_el_separador_no_cuenta_lo_que_va_entre_comillas"
sabotaje $M "el CUIT del despachante vuelve a aceptar cualquier cosa" \
  '            if not _re_cuit.fullmatch(r"[0-9]{11}", effective_cuit_agr):' \
  '            if False:' \
  "FAILED $T::test_el_cuit_del_despachante_va_solo_con_11_digitos"
sabotaje $M "un producto mal formado vuelve a dar 500" \
  '            if not isinstance(_it, dict) or (' \
  '            if False and (' \
  "FAILED $T::test_productos_mal_formados_dan_400"

# Devolución (veredicto 2034b85)
sabotaje $M "una combinada vuelve a recorrerse hasta su última fila" \
  $'            filas = df.index[(df.index >= desde) & (df.index <= hasta)]\n            df.loc[filas, col] = valor' \
  $'            for fila in range(f1 - 1, f2 - 1):\n                if fila in df.index:\n                    df.at[fila, col] = valor' \
  "FAILED $T::test_una_combinada_gigante_repetida_no_traba_la_lectura"
sabotaje $M "cantidad y precio combinados vuelven a copiarse" \
  '_COMBINADAS_SE_COPIAN = {"descripcion", "origen", "pieza"}' \
  '_COMBINADAS_SE_COPIAN = {"descripcion", "origen", "pieza", "cantidad", "valor_unitario", "peso_unitario"}' \
  "FAILED $T::test_una_combinada_en_cantidad_o_precio_con_texto_no_se_copia[5 UN-USD 100]"
sabotaje $M "el mapeo del cliente deja de contar para las combinadas" \
  '    mapeados = dict(mapeo or {})' \
  '    mapeados = {}' \
  "FAILED $T::test_una_combinada_en_la_columna_de_cantidad_del_mapeo_del_cliente_tampoco_se_copia"
sabotaje $M "una fila vacía dentro de una combinada vuelve a ser «sin leer»" \
  '    return _rellenar_combinadas(df, combinadas, mapeo)[~vacias]' \
  '    return _rellenar_combinadas(df, combinadas, mapeo).dropna(how="all")' \
  "FAILED $T::test_una_fila_vacia_dentro_de_una_combinada_no_es_una_fila_sin_leer"
sabotaje $M "el CSV vuelve a ir a UTF-8 por un solo par" \
  '            if validas and len(validas) >= sueltos:' \
  '            if validas:' \
  "FAILED $T::test_un_csv_cp1252_con_un_par_que_parece_utf8_no_pierde_las_tildes[\xc2\xb0]"
sabotaje $M "en el CSV vuelve a contar cualquier secuencia UTF-8" \
  '            validas = [q for q in secuencias if _plausible(q)]' \
  '            validas = secuencias' \
  "FAILED $T::test_un_csv_cp1252_con_letras_que_arman_utf8_raro_se_lee_bien"
sabotaje $M "el CSV mezclado deja de avisar" \
  '            if validas and sueltos:' \
  '            if False:' \
  "FAILED $T::test_un_csv_con_codificacion_dudosa_avisa"
sabotaje $C "con la cantidad mala vuelve a nombrar valor y peso" \
  '        por = None if cantidad_mala else cantidad' \
  '        por = cantidad' \
  "FAILED $T::test_una_cantidad_mala_nombra_solo_la_cantidad"
sabotaje $F "los estilos vuelven a tener sólo tope de MB" \
  '                                     or _mas_elementos_que(z, parte, tope_elementos)):' \
  '                                     or False):' \
  "FAILED $T::test_estilos_con_millones_de_elementos_se_rechazan_antes_de_abrir[xf]"
sabotaje $F "una relación de Type raro vuelve a no ser hoja" \
  '        if "chartsheet" in (r.get("Type") or ""):' \
  '        if not (r.get("Type") or "").endswith("/worksheet"):' \
  "FAILED $T::test_una_hoja_con_una_relacion_rara_cuenta_y_sale_de_la_copia"
sabotaje $F "la primera hoja vuelve a tener tope de 30 MB" \
  '        tope_hoja = _mb_de_entorno("EXCEL_MAX_PRIMERA_HOJA_MB", 10)' \
  '        tope_hoja = _mb_de_entorno("EXCEL_MAX_PRIMERA_HOJA_MB", 30)' \
  "FAILED $T::test_una_primera_hoja_de_27_mb_se_rechaza"
sabotaje $F "un libro con entidades vuelve a pasar" \
  '                if b"<!DOCTYPE" in trozo or b"<!ENTITY" in trozo:' \
  '                if False:' \
  "FAILED $T::test_un_libro_con_entidades_xml_se_rechaza_antes_de_abrir[xl/styles.xml]"
sabotaje $F "los estilos vuelven a contar sólo prefijos ASCII" \
  '    abre = re.compile(rb"<[^/!?\s>]")' \
  '    abre = re.compile(rb"<[A-Za-z_]")' \
  "FAILED $T::test_estilos_con_un_prefijo_no_ascii_tambien_se_cuentan"
sabotaje $M "la copia vuelve a dejar las hojas de gráfico" \
  '        afuera = {ruta_hoja for _n, rid, ruta_hoja, _g in todas if rid != rid_primera}' \
  '        afuera = {ruta_hoja for _n, rid, ruta_hoja, g in todas if rid != rid_primera and not g}' \
  "FAILED $T::test_la_copia_de_la_primera_hoja_saca_las_hojas_de_grafico"
sabotaje $F "los .rels vuelven a no tener tope" \
  '            if nombre.lower().endswith(".rels") and z.getinfo(nombre).file_size > 2**20:' \
  '            if False:' \
  "FAILED $T::test_un_rels_de_hoja_enorme_se_rechaza"
sabotaje $F "una celda en la columna XFD vuelve a pasar" \
  '        if hojas and _ultima_columna(z.read(hojas[0][1])) > _EXCEL_MAX_COLUMNAS:' \
  '        if False:' \
  "FAILED $T::test_una_celda_en_la_ultima_columna_se_rechaza_antes_de_abrir"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
