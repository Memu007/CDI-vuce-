#!/usr/bin/env bash
# Negativos de EXCEL-2b: cada sabotaje deshace una parte del carril liviano
# (o de la medida que decide quién entra) y la prueba tiene que fallar por
# ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/excel2b.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si la base no está en verde, si un sabotaje no encuentra su
# patrón o si no pone rojo.
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
B=tests/test_excel2b.py
D5="tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal"

correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider "$@" 2>&1; }

if ! salida="$(correr $B "$D5")"; then
  echo "la base no está en verde:"; tail -5 <<<"$salida"; exit 1
fi
echo "base en verde"

# sabotaje <archivo> <nombre> <pruebas> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo.
sabotaje() {
  local archivo="$1" nombre="$2" pruebas="$3" esperado="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$@" <<'PYEOF'
import sys
p, pares = sys.argv[1], sys.argv[2:]
s = open(p).read()
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w").write(s)
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  # shellcheck disable=SC2086
  salida="$(correr $pruebas)"; codigo=$?
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

# Los carriles.
sabotaje $F "la subida chica vuelve a validar en los hilos pesados" $B \
  "('validar', 'validar-excel_" \
  $'    if not liviano:\n        return _pool_validar_excel()' $'    if True:\n        return _pool_validar_excel()'
sabotaje $M "la subida chica vuelve a leer en los hilos pesados" $B \
  "('leer', 'lectura-excel_" \
  $'    if not liviano:\n        return _pool_lectura_excel()' $'    if True:\n        return _pool_lectura_excel()'
# D5: con los dos carriles pesados, la normal vuelve a esperar detrás de las
# ocho pesadas; la prueba lo ve por el tiempo, no por el código de respuesta.
sabotaje $F "la normal vuelve a la cola de las pesadas (D5)" "$D5" \
  "esperó detrás de las pesadas" \
  $'    if not liviano:\n        return _pool_validar_excel()' $'    if True:\n        return _pool_validar_excel()'
# La lectura no vuelve a medir: usa lo que midió la validación.
sabotaje $M "la lectura no usa la medida de la validación" $B \
  "('leer', 'lectura-excel-liviano_" \
  "    contents, liviano = await validar_con_carril(file, 'excel', max_size=max_upload_bytes)" \
  $'    contents, liviano = await validar_con_carril(file, \'excel\', max_size=max_upload_bytes)\n    liviano = True'

# La medida.
sabotaje $F "se saltea la medida: todo va al carril liviano" $B \
  "FAILED $B::test_un_libro_con_mas_xml_que_el_umbral_va_al_pesado" \
  $'    umbral = _mb_de_entorno("EXCEL_LIVIANO_MB", 2)\n' $'    return True\n'
sabotaje $F "el umbral deja de salir de la variable de entorno" $B \
  "FAILED $B::test_el_umbral_sale_de_la_variable_de_entorno" \
  '    umbral = _mb_de_entorno("EXCEL_LIVIANO_MB", 2)' '    umbral = 2 * 1024 * 1024'
sabotaje $F "un .xls entra al carril liviano sin medirse" $B \
  "FAILED $B::test_un_xls_se_mide_por_su_tamano" \
  '        return len(contents) <= umbral' '        return True'
sabotaje $F "el índice largo vuelve a leerse en el hilo del servidor" $B \
  "FAILED $B::test_un_indice_largo_va_al_pesado_sin_leerlo" \
  $'        if int.from_bytes(contents[fin + 12:fin + 16], "little") > _LIVIANO_INDICE_MAX:\n            return False' \
  $'        if False:\n            return False'
# Abrir el ZipFile ya lee el índice: vigilar infolist() no lo veía.
sabotaje $F "el índice largo se lee antes del tope y sigue yendo al pesado" $B \
  "el índice largo se leyó en el hilo del servidor" \
  $'        if int.from_bytes(contents[fin + 12:fin + 16], "little") > _LIVIANO_INDICE_MAX:\n            return False' \
  $'        zipfile.ZipFile(io.BytesIO(contents)).close()\n        if int.from_bytes(contents[fin + 12:fin + 16], "little") > _LIVIANO_INDICE_MAX:\n            return False'
sabotaje $F "el zip64 deja de mandarse al carril pesado" $B \
  "FAILED $B::test_un_zip64_que_declara_un_indice_corto_va_al_pesado" \
  $'        if contents[max(0, fin - 20):fin].startswith(b"PK\\x06\\x07"):\n            return False' \
  $'        if False:\n            return False'
sabotaje $F "las imágenes se descuentan por el nombre y no por la firma" $B \
  "FAILED $B::test_una_hoja_con_nombre_de_imagen_cuenta_como_xml" \
  '                if _es_imagen(cabeza):' '                if True:'
sabotaje $F "las imágenes se descuentan sin tope" $B \
  "FAILED $B::test_mas_de_10_mib_de_imagen_no_se_descuentan" \
  $'                if descontado + info.file_size > _LIVIANO_IMAGENES_MAX:\n                    continue' \
  $'                if False:\n                    continue'

sabotaje $F "las cabezas de imagen se leen sin tope de lecturas" $B \
  "FAILED $B::test_no_se_leen_mas_de_20_cabezas_de_imagen" \
  '            for info in candidatas[:_LIVIANO_IMAGENES_LECTURAS]:' '            for info in candidatas:'
# La cabeza se lee desde los bytes subidos, con tope de lo comprimido.
sabotaje $F "la cabeza vuelve a descomprimir la entrada entera" $B \
  "se descomprimieron" \
  '    datos = contents[inicio:inicio + min(info.compress_size, _LIVIANO_CABEZA_COMPRIMIDA)]' \
  '    datos = contents[inicio:inicio + info.compress_size]'
sabotaje $F "la cabeza de una imagen sin comprimir no se lee" $B \
  "FAILED $B::test_una_imagen_guardada_sin_comprimir_tampoco_cuenta" \
  '        return datos[:44]' '        return b""'
sabotaje $F "la cabeza de una imagen comprimida no se lee" $B \
  "FAILED $B::test_una_imagen_de_verdad_no_cuenta" \
  '    return zlib.decompressobj(-15).decompress(datos, 44)' '    return b""'
# Las otras hojas y los ítems leen en el mismo carril que la hoja (punto 2
# de la devolución): con el pool pesado fijo, la subida chica los manda atrás.
sabotaje $M "las otras hojas se leen en los hilos pesados" $B \
  "AssertionError: ('_otras_hojas_con_datos'" \
  $'                _otras_hojas_con_datos, temp_filename, engine,\n                limite=min(10.0, _excel_read_timeout_s()), que="el Excel", pool=_pool_lectura_excel_carril(liviano),' \
  $'                _otras_hojas_con_datos, temp_filename, engine,\n                limite=min(10.0, _excel_read_timeout_s()), que="el Excel", pool=_pool_lectura_excel(),'
sabotaje $M "los ítems se arman en los hilos pesados" $B \
  "AssertionError: ('extract_items_from_excel'" \
  $'            extract_items_from_excel, df, file.filename, descartes, extras,\n            limite=_excel_read_timeout_s(), que="el Excel", pool=_pool_lectura_excel_carril(liviano),' \
  $'            extract_items_from_excel, df, file.filename, descartes, extras,\n            limite=_excel_read_timeout_s(), que="el Excel", pool=_pool_lectura_excel(),'
# Punto 4: ante la duda, pesado; el tope de lecturas; el umbral enorme.
sabotaje $F "un índice que no se puede leer va al carril liviano" $B \
  "FAILED $B::test_un_indice_que_no_se_puede_leer_va_al_pesado" \
  $'    except Exception:\n        return False\n\n\ndef _abrir_excel' $'    except Exception:\n        return True\n\n\ndef _abrir_excel'
sabotaje $F "el tope de lecturas de cabezas sube a 100000" $B \
  "FAILED $B::test_no_se_leen_mas_de_20_cabezas_de_imagen" \
  '_LIVIANO_IMAGENES_LECTURAS = 20' '_LIVIANO_IMAGENES_LECTURAS = 100000'
sabotaje $F "un umbral que no entra en bytes vuelve a dar 500" $B \
  "FAILED $B::test_un_umbral_enorme_no_rompe_la_subida[1e308-2097152]" \
  '    if not math.isfinite(valor * 1024 * 1024) or valor <= 0:' '    if not math.isfinite(valor) or valor <= 0:'
# Hallazgos del adversario Sonnet alto: el cuarto tope, la cuenta exacta de
# lecturas y una entrada que no se puede descomprimir.
sabotaje $F "el tope de lo descomprimido vuelve a su propia lectura" $B \
  "FAILED $B::test_ningun_tope_de_excel_enorme_rompe_la_subida[EXCEL_MAX_DESCOMPRIMIDO_MB]" \
  '    return _mb_de_entorno("EXCEL_MAX_DESCOMPRIMIDO_MB", 100)' \
  $'    import math\n    try:\n        valor = float(os.getenv("EXCEL_MAX_DESCOMPRIMIDO_MB", "") or 100)\n    except (TypeError, ValueError):\n        valor = 100.0\n    if not math.isfinite(valor) or valor <= 0:\n        valor = 100.0\n    return int(valor * 1024 * 1024)'
sabotaje $F "el tope de lecturas de cabezas baja a 19" $B \
  "FAILED $B::test_se_leen_exactamente_20_cabezas_de_imagen" \
  '_LIVIANO_IMAGENES_LECTURAS = 20' '_LIVIANO_IMAGENES_LECTURAS = 19'
sabotaje $F "el tope de lecturas de cabezas sube a 21" $B \
  "FAILED $B::test_se_leen_exactamente_20_cabezas_de_imagen" \
  '_LIVIANO_IMAGENES_LECTURAS = 20' '_LIVIANO_IMAGENES_LECTURAS = 21'
sabotaje $F "una entrada que no se descomprime corta la medida" $B \
  "FAILED $B::test_una_entrada_que_no_se_puede_descomprimir_no_corta_la_medida" \
  $'                except Exception:\n                    continue' $'                except ZeroDivisionError:\n                    continue'
git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
