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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_excel1_rendimiento.py tests/test_excel1_lectura.py 2>&1)"; codigo=$?
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
            _leer_excel_ruta, temp_filename, engine,
            limite=_excel_read_timeout_s(), que="el Excel",
        )' \
  '        df = _leer_excel_ruta(temp_filename, engine)' \
  "FAILED $T::test_health_responde_mientras_se_lee_un_excel[upload_excel_v2]"
sabotaje $M "leer un Excel pierde el tiempo máximo" \
  '    return _segundos_de_entorno("EXCEL_READ_TIMEOUT_S", 60.0)' \
  '    return 1e9' \
  "FAILED $T::test_leer_un_excel_tiene_tiempo_maximo[clientes_import]"
sabotaje $F "validar el Excel vuelve al hilo del servidor" \
  'asyncio.to_thread(_contar_hojas_excel, contents, file_ext),' \
  'asyncio.sleep(0, _contar_hojas_excel(contents, file_ext)),' \
  "FAILED $T::test_health_responde_mientras_se_valida_un_excel"
sabotaje $M "«Valor» vuelve a ganar sobre el precio unitario" \
  '        "valorunitario", "preciounitario", "unitprice",' \
  '        "valorunitario", "valor", "preciounitario", "unitprice",' \
  "FAILED $L::test_precio_unitario_gana_sobre_valor_total"
sabotaje $M "el peso bruto vuelve a usarse como peso unitario" \
  '        "peso", "weight",
    ],' \
  '        "peso", "weight", "pesobruto", "pesototal",
    ],' \
  "FAILED $L::test_peso_bruto_o_total_no_se_toma_como_peso_unitario"
sabotaje $M "las filas de subtotal vuelven a entrar" \
  '            if _FILA_DE_TOTAL_RE.match(descripcion) or _FILA_DE_TOTAL_RE.match(pieza):' \
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
  '            if canon not in cubiertos and src not in effective_mapping:' \
  '            if False:' \
  "FAILED $L::test_mapeo_guardado_no_deja_afuera_encabezados_nuevos"
sabotaje $M "las filas descartadas dejan de avisarse" \
  '            "filas_descartadas": len(descartes),' \
  '            "filas_descartadas": 0,' \
  "FAILED $L::test_filas_descartadas_se_avisan"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
