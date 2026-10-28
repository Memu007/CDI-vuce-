#!/usr/bin/env bash
# Negativos de DESPACHO-1b: cada sabotaje deshace una regla de la lectura de
# despachos para el catálogo y tests/test_despacho1b.py (o, los de la
# pantalla, scripts/testing/pantalla_despacho1b.js) tiene que fallar por ese
# motivo.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8854] scripts/testing/sabotajes/despacho1b.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8854}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
export BASE_URL="http://127.0.0.1:$PUERTO"
FALLAS=0

pytest_d1b() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_despacho1b.py 2>&1
}

levantar() {
  rm -f local.db
  ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./local.db \
  JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
  ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
    "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && return 0; sleep 1; done
  echo "BASE  | la API no levantó"; tail -20 "$TMPD/api.log"; exit 1
}
pantalla() { PY="$PY" node scripts/testing/pantalla_despacho1b.js 2>&1; }

aplicar() {
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

# juzgar <nombre> <salida> <código> <lo que el rojo tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3"; shift 3
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^(FAILED|FALLA|E )" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
# El de la pantalla (sabotaje_pantalla) es igual, pero juzga con el navegador.
_sabotear() {
  local prueba="$1" archivo="$2" nombre="$3" viejo="$4" nuevo="$5"; shift 5
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$($prueba)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}
sabotaje() { _sabotear pytest_d1b "$@"; }
sabotaje_pantalla() { _sabotear pantalla "$@"; }

L=proyecto_maria/core/despacho_lector.py
M=proyecto_maria/main.py
T=tests/test_despacho1b.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_d1b >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi
levantar
if ! pantalla >"$TMPD/base_pantalla.log"; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje"; grep FALLA "$TMPD/base_pantalla.log"; exit 1
fi

# --- La lectura: por rótulo, sin rellenar y marcando lo que falta
sabotaje $L "el subítem toma lo que le falta del ítem" \
  $'    campos = bloque["campos"]\n    avisos = list(bloque["avisos"])' \
  $'    campos = {**(padre["campos"] if padre else {}), **bloque["campos"]}\n    avisos = list(bloque["avisos"])' \
  "FAILED $T::test_lo_que_falta_queda_marcado_y_no_se_rellena" "assert 30.0 is None"
sabotaje $L "lo que falta no se marca" \
  '    renglon["faltantes"] = [c for c in CAMPOS' '    renglon["faltantes"] = [c for c in () if c in CAMPOS' \
  "FAILED $T::test_lo_que_falta_queda_marcado_y_no_se_rellena" "assert [] == ['kilo_neto']"
sabotaje $L "se lee por posición y no por rótulo" \
  $'        for col, rotulo in columnas:\n            if col <= inicio + 2:\n                elegida = rotulo' \
  $'        for col, rotulo in columnas[len(valores):len(valores) + 1]:\n            elegida = rotulo' \
  "FAILED $T::test_un_valor_vacio_no_corre_los_de_al_lado"
sabotaje $L "se aceptan números con otra forma" \
  '_NUMERO_AR = re.compile(r"^\d{1,3}(?:\.\d{3})+(?:,\d+)?$|^\d+(?:,\d+)?$")' \
  '_NUMERO_AR = re.compile(r"^[\d.,]+$")' \
  "FAILED $T::test_numeros_con_punto_de_miles_y_coma_decimal[12.5-None]"
sabotaje $L "un número que no se entiende se lee igual" \
  '        valor = numero_ar(crudo)' \
  '        valor = numero_ar(crudo) if numero_ar(crudo) is not None else float(crudo.replace(",", ""))' \
  "FAILED $T::test_un_numero_con_otra_forma_queda_faltante_con_aviso"
sabotaje $L "los subítems no se separan" \
  '        if it["subitems"]:' '        if False and it["subitems"]:' \
  "FAILED $T::test_con_subitems_sale_un_renglon_por_subitem"
sabotaje $L "la posición heredada no se avisa" \
  $'            heredados.append("posicion_sim")\n' '' \
  "FAILED $T::test_con_subitems_sale_un_renglon_por_subitem" "['origen'] == ['posicion_sim', 'origen']"
sabotaje $L "la divisa es la del flete" \
  '"Divisa FOB Total"' '"Divisa Flete Total"' \
  "FAILED $T::test_la_divisa_es_la_del_fob_y_no_la_del_flete" "'USD' == 'EUR'"
sabotaje $L "un sufijo con espacios no se lee" \
  '(?:\((.*?)\)|(\d{2}))' '(?:\(([^ )]*?)\)|(\d{2}))' \
  "FAILED $T::test_sufijos_con_y_sin_parentesis"
sabotaje $L "un escaneado no avisa" \
  '    if not texto.strip():' '    if False:' \
  "FAILED $T::test_pdf_sin_texto_avisa_y_no_devuelve_renglones" "FAILED $T::test_leer_un_escaneado_avisa"
sabotaje $L "sin kilo se inventa el peso" \
  '    peso = kilo / cantidad if kilo and cantidad else None' \
  '    peso = kilo / cantidad if kilo and cantidad else 0.5' \
  "FAILED $T::test_guardar_sin_kilo_no_inventa_el_peso" "assert 0.5 in (0, 0.0, None)"

# --- Aislamiento
sabotaje $M "leer no mira de quién es el cliente" \
  $'    await _get_owned_client(db, client_id, user["username"])\n\n    from proyecto_maria.security.file_security import validate_file_upload\n    from proyecto_maria.core.despacho_lector import leer_despacho' \
  $'    from proyecto_maria.security.file_security import validate_file_upload\n    from proyecto_maria.core.despacho_lector import leer_despacho' \
  "FAILED $T::test_otro_dueno_no_lee_ni_guarda_en_un_cliente_ajeno" "assert 200 == 404"
sabotaje $M "guardar no mira de quién es el cliente" \
  $'    await _get_owned_client(db, client_id, username)\n\n    from proyecto_maria.core.despacho_lector import MAX_RENGLONES' \
  $'    from proyecto_maria.core.despacho_lector import MAX_RENGLONES' \
  "FAILED $T::test_otro_dueno_no_lee_ni_guarda_en_un_cliente_ajeno" "assert 200 == 404"

# --- Guardar: todo o nada, con tope, sin TXT ni operación
sabotaje $M "se guarda lo que está bien y se descarta el resto" \
  $'    if errores:\n        return JSONResponse(status_code=422' $'    if errores and not listos:\n        return JSONResponse(status_code=422' \
  "FAILED $T::test_guardar_es_todo_o_nada" "assert 200 == 422"
sabotaje $M "guardar acepta una lista vacía" \
  '    if not isinstance(renglones, list) or not renglones:' '    if not isinstance(renglones, list):' \
  "FAILED $T::test_guardar_sin_renglones_da_400[cuerpo1]"
sabotaje $M "guardar no tiene tope" \
  '    if len(renglones) > MAX_RENGLONES:' '    if False:' \
  "FAILED $T::test_guardar_mas_del_tope_da_400" "assert 200 == 400"
sabotaje $M "leer acepta lo que no es PDF" \
  "    contents = await validate_file_upload(file, 'pdf', max_size=_get_max_upload_bytes())"$'\n    try:\n        resultado = await _leer_pdf_aparte(leer_despacho' \
  $'    contents = await file.read()\n    try:\n        resultado = await _leer_pdf_aparte(leer_despacho' \
  "FAILED $T::test_leer_rechaza_lo_que_no_es_pdf"
sabotaje $M "guardar arma un TXT" \
  $'    try:\n        for campos in listos:' $'    generate_maria_txt(listos)\n    try:\n        for campos in listos:' \
  "FAILED $T::test_nunca_arma_un_txt" "armó un TXT"
sabotaje $M "guardar crea una operación" \
  $'                db, owner_username=username, client_id=client_id, **campos)\n        await db.commit()' \
  $'                db, owner_username=username, client_id=client_id, **campos)\n        db.add(OperationModel(owner_username=username, client_id=client_id))\n        await db.commit()' \
  "FAILED $T::test_guardar_lo_revisado_queda_en_el_catalogo_del_cliente" "_contar(Operation) == operaciones"
sabotaje proyecto_maria/pdf_extractor.py "el lector de facturas acepta despachos" \
  '    if (clase["tipo"] != "factura_comercial" or' '    if (clase["tipo"] not in ("factura_comercial", "despacho_aduanero") or' \
  "FAILED $T::test_el_lector_de_facturas_sigue_rechazando_el_despacho"

# --- La pantalla (en el navegador, con la API andando; JS y CSS se leen en cada pedido)
J=proyecto_maria/static/v2/screens/clientes.js
sabotaje_pantalla $J "el botón no está conectado" \
  $'        if (despachoBtn) despachoBtn.addEventListener(\'click\', onDespachoElegir);\n' '' \
  "FALLA: 1280 px: el botón no abre el selector de archivo"
sabotaje_pantalla $J "el faltante no se marca" \
  "(falta ? ' is-faltante' : '')" "''" \
  "FALLA: 1280 px: lo marcado como faltante es []"
sabotaje_pantalla $J "se guarda al leer, sin revisar" \
  '            renderDespacho(data);' '            renderDespacho(data); await onDespachoGuardar();' \
  "FALLA: 1280 px: se pidió guardar antes de tocar «Guardar en el catálogo»"
sabotaje_pantalla proyecto_maria/static/v2/app_v2.css "el panel es más ancho que la pantalla" \
  $'.cx-despacho {\n    margin: 0 0 var(--s-4);' $'.cx-despacho {\n    min-width: 1400px;\n    margin: 0 0 var(--s-4);' \
  "FALLA: 1280 px: el panel mide 1400 px"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
