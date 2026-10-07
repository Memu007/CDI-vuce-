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
  "FAILED $T::test_cuit_del_despachante_o_id_del_vendedor_con_digitos_raros_no_deja_generar"
# D26 (a)
sabotaje $F "validar vuelve a abrir el libro con openpyxl" \
  '        return _contar_hojas_xlsx(contents)' \
  '        import openpyxl; return len(openpyxl.load_workbook(io.BytesIO(contents), read_only=True).sheetnames)' \
  "FAILED $T::test_validar_un_xlsx_no_lo_abre_con_openpyxl"
sabotaje $F "los textos compartidos enormes vuelven a pasar" \
  '        if "xl/sharedStrings.xml" in nombres and z.getinfo("xl/sharedStrings.xml").file_size > tope_textos:' \
  '        if False:' \
  "FAILED $T::test_textos_compartidos_enormes_se_rechazan_antes_de_abrir"
sabotaje $F "una primera hoja enorme vuelve a pasar" \
  '        if hojas and hojas[0][1] in nombres and z.getinfo(hojas[0][1]).file_size > tope_hoja:' \
  '        if False:' \
  "FAILED $T::test_una_primera_hoja_enorme_se_rechaza_antes_de_abrir"
sabotaje $M "leer la factura vuelve a abrir el libro entero" \
  $'        contenido, combinadas = _xlsx_solo_primera_hoja(ruta)\n        origen = _io.BytesIO(contenido)' \
  $'        contenido, combinadas = _xlsx_solo_primera_hoja(ruta)\n        origen = ruta' \
  "FAILED $T::test_ocho_libros_armados_sin_medida_no_dejan_sin_lectura_a_una_subida_normal"
sabotaje $M "el historial vuelve a abrir el libro entero" \
  '        contenido, _ = _xlsx_solo_primera_hoja(content)' \
  '        contenido = content' \
  "FAILED $T::test_el_historial_en_excel_lee_solo_la_primera_hoja"
# D18
sabotaje $M "el encabezado vuelve a buscarse sólo en la fila 1" \
  '    if len(_detect_item_columns(list(df.columns))) >= 3:' \
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
  '                df.at[fila - 2, col] = valor' \
  '                pass' \
  "FAILED $T::test_una_celda_combinada_hacia_abajo_vale_para_todas_sus_filas"
# Aviso de mapeo
sabotaje $M "el aviso de mapeo deja de nombrar la columna" \
  $'                f"Para «{_NOMBRE_DEL_CAMPO.get(canon, canon)}» se usó la columna «{elegido}» "' \
  $'                f"Para «{_NOMBRE_DEL_CAMPO.get(canon, canon)}» se usó una columna "' \
  "FAILED $T::test_el_aviso_de_mapeo_nombra_la_columna_que_se_uso"
# CSV del historial
sabotaje $M "el CSV vuelve a leerse sólo como UTF-8" \
  '        for codificacion in ("utf-8-sig", "cp1252", "latin-1"):' \
  '        for codificacion in ("utf-8-sig",):' \
  "FAILED $T::test_el_csv_del_historial_se_lee_con_coma_punto_y_coma_latin1_o_bom[latin-1-"
sabotaje $M "el CSV vuelve a leerse siempre con coma" \
  $'        separador = max((",", ";", "\\t"), key=encabezado.count)' \
  $'        separador = ","' \
  "FAILED $T::test_el_csv_del_historial_se_lee_con_coma_punto_y_coma_latin1_o_bom[punto y coma-"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
