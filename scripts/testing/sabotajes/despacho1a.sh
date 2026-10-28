#!/usr/bin/env bash
# Negativos de DESPACHO-1a: cada sabotaje deshace una parte de la descarga del
# catálogo en Excel y tests/test_despacho1a.py (o, el del botón,
# scripts/testing/pantalla_despacho1a.js) tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8853] scripts/testing/sabotajes/despacho1a.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8853}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
export BASE_URL="http://127.0.0.1:$PUERTO"
FALLAS=0

pytest_d1a() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_despacho1a.py 2>&1
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
pantalla() { node scripts/testing/pantalla_despacho1a.js 2>&1; }

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
      grep -E "^(FAILED|FALLA)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_d1a)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
T=tests/test_despacho1a.py
CONSULTA=$'        ClientProductHistoryModel.owner_username == username,\n        ClientProductHistoryModel.client_id == client_id,\n    ).order_by(sa_desc(ClientProductHistoryModel.ultima_vez))\n    rows = (await db.execute(stmt)).scalars().all()\n    contenido'

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_d1a >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi
levantar
if ! pantalla >"$TMPD/base_pantalla.log"; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje"; grep FALLA "$TMPD/base_pantalla.log"; exit 1
fi

# --- Aislamiento
sabotaje $M "no se mira de quién es el cliente" \
  "    client = await _get_owned_client(db, client_id, username)"$'\n\n'"    stmt = sa_select(ClientProductHistoryModel)" \
  "    client = (await db.execute(sa_select(ClientModel).where(ClientModel.id == client_id))).scalars().first()"$'\n\n'"    stmt = sa_select(ClientProductHistoryModel)" \
  "FAILED $T::test_otro_dueno_recibe_el_mismo_404_que_en_el_catalogo" "assert 200 == 404"
sabotaje $M "la consulta no filtra por dueño" \
  "$CONSULTA" "${CONSULTA/        ClientProductHistoryModel.owner_username == username,$'\n'/}" \
  "FAILED $T::test_no_se_mezclan_los_productos_de_otro_cliente_ni_de_otro_dueno" "trae productos de otro dueño"
sabotaje $M "la consulta no filtra por cliente" \
  "$CONSULTA" "${CONSULTA/        ClientProductHistoryModel.client_id == client_id,$'\n'/}" \
  "FAILED $T::test_no_se_mezclan_los_productos_de_otro_cliente_ni_de_otro_dueno" "trae productos de otro cliente"
sabotaje $M "se puede bajar sin sesión" \
  $'async def download_client_catalogo_productos(\n    client_id: str,\n    user=Depends(get_current_user),' \
  $'async def download_client_catalogo_productos(\n    client_id: str,\n    user: dict = {"username": "test_user"},' \
  "FAILED $T::test_sin_sesion_da_401" "assert 404 == 401"

# --- Fórmulas
sabotaje $M "«=» queda como fórmula" \
  $'                celda.value = texto\n                celda.data_type = "s"\n' \
  $'                celda.value = texto\n' \
  "FAILED $T::test_una_descripcion_con_formula_queda_como_texto[=HYPERLINK" "assert 'f' == 's'"
sabotaje $M "sin el apóstrofo invisible (+, - y @ se vuelven fórmula al editarlos)" \
  $'                if texto[:1] in ("=", "+", "-", "@"):\n                    celda.quotePrefix = True\n' '' \
  "FAILED $T::test_una_descripcion_con_formula_queda_como_texto[+1+1]" \
  "FAILED $T::test_una_descripcion_con_formula_queda_como_texto[@SUMA(A1)]" "quotePrefix"

# --- Posición como texto
sabotaje $M "la posición sólo de dígitos sale como número" \
  $'                if campo == "ncm":\n                    celda.number_format = "@"' \
  $'                if campo == "ncm" and texto.isdigit():\n                    celda.value = int(texto)' \
  "FAILED $T::test_la_posicion_sale_como_texto_con_ceros_y_letra" "1012100"
sabotaje $M "la posición sin formato de texto" \
  $'                if campo == "ncm":\n                    celda.number_format = "@"' \
  $'                if campo == "ncm":\n                    pass' \
  "FAILED $T::test_la_posicion_sale_como_texto_con_ceros_y_letra" "number_format"

# --- Lo guardado y el vacío
sabotaje $M "el orden no es el de la pantalla" \
  "$CONSULTA" "${CONSULTA/sa_desc(ClientProductHistoryModel.ultima_vez)/ClientProductHistoryModel.ultima_vez}" \
  "FAILED $T::test_el_archivo_se_abre_y_trae_lo_guardado" "TELEFONO INVENTADO"
sabotaje $M "cantidad y peso cruzados" \
  $'    ("Cantidad promedio", "cantidad_avg"),\n    ("Peso unitario promedio", "peso_unitario_avg"),' \
  $'    ("Cantidad promedio", "peso_unitario_avg"),\n    ("Peso unitario promedio", "cantidad_avg"),' \
  "FAILED $T::test_el_archivo_se_abre_y_trae_lo_guardado" "450.25"
sabotaje $M "el catálogo vacío sale sin encabezados" \
  "    ws.append([titulo for titulo, _ in _CATALOGO_XLSX_COLUMNAS])" \
  "    if productos: ws.append([titulo for titulo, _ in _CATALOGO_XLSX_COLUMNAS])" \
  "FAILED $T::test_un_catalogo_vacio_trae_solo_los_encabezados"

# --- Lo que haría fallar la descarga
sabotaje $M "no se limpian los caracteres de control" \
  '                texto = ILLEGAL_CHARACTERS_RE.sub("", valor)' '                texto = valor' \
  "FAILED $T::test_una_descripcion_con_caracteres_de_control_no_rompe_la_descarga" "IllegalCharacterError"
sabotaje $M "el nombre del archivo va como viene" \
  '    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", nombre.encode("ascii", "ignore").decode())[:40]' \
  '    safe_name = client.name' \
  "FAILED $T::test_el_nombre_del_archivo_es_ascii" "UnicodeEncodeError"

# --- El botón (en el navegador, con la API andando; el JS se lee en cada pedido)
git checkout -q -- proyecto_maria/
if aplicar proyecto_maria/static/v2/screens/clientes.js \
  $'        if (catalogoExcelBtn) catalogoExcelBtn.addEventListener(\'click\', downloadCatalogoExcel);\n' ''; then
  salida="$(pantalla)"; codigo=$?
  juzgar "el botón no está conectado" "$salida" "$codigo" "FALLA: 1280 px: el botón no bajó nada"
else
  echo "ROTO  | el botón no está conectado: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1))
fi

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
