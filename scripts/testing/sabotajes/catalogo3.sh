#!/usr/bin/env bash
# Negativos de CATALOGO-3: cada sabotaje deshace una línea de la pieza y
# tests/test_catalogo3.py (o el caso nombrado de despacho1b/1c) tiene que
# ponerse rojo por ese motivo. Necesita node. El recorte del origen al guardar
# y el candado de la migración sólo se ven en Postgres:
# scripts/testing/catalogo3_postgres.py.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/catalogo3.sh [SHA]
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
T=tests/test_catalogo3.py
B=tests/test_despacho1b.py::test_cambiar_el_origen_valida_igual_que_guardar
A=tests/test_despacho1b.py::test_cambiar_el_origen_guarda_el_codigo_en_mayusculas
D=tests/test_despacho1c.py::test_el_aviso_del_catalogo_nombra_el_producto_que_no_se_aprendio
D2=tests/test_despacho1c.py::test_los_productos_sin_origen_se_avisan
CF="$T::test_cada_forma_del_pais_da_el_mismo_codigo_al_importar_y_exportar"
PS="$T::test_la_pantalla_y_el_servidor_reconocen_los_mismos_paises"
PRUEBA=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T" "$B" "$A" "$D" "$D2")

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
  salida="$("${PRUEBA[@]}" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
    grep -E "^E |^FAILED" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

C=proyecto_maria/core/catalog_service.py
M=proyecto_maria/main.py
G=proyecto_maria/core/maria_generator.py
F=proyecto_maria/static/v2/screens/finalize.js
E=proyecto_maria/core/maria_generator_export.py
J=proyecto_maria/static/v2/paises_maria.js
X=proyecto_maria/pdf_extractor.py

if ! "${PRUEBA[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

# D76: proveedor
sabotaje $C "el proveedor sólo CJK vuelve a quedar con id vacío" \
  'clave = _clave(nombre).replace(" ", "_")' \
  'clave = _normalize(nombre).replace(" ", "_")' \
  "FAILED $T::test_dos_proveedores_distintos_no_comparten_catalogo[cjk]"
sabotaje $C "sin nombre de proveedor vuelve a guardar" \
  '    if not vendor_id:
        raise ValueError("Falta el nombre del proveedor.")' \
  '    if False:
        raise ValueError("Falta el nombre del proveedor.")' \
  "FAILED $T::test_sin_nombre_de_proveedor_no_guarda_ni_encuentra"
sabotaje $C "dos proveedores largos vuelven a compartir los 60 primeros" \
  'return clave[:39] + "~" + hashlib.sha256(clave.encode("utf-8")).hexdigest()[:20]' \
  'return clave[:60]' \
  "FAILED $T::test_dos_proveedores_distintos_no_comparten_catalogo[prefijo-60]"
sabotaje $C "una clave de proveedor de 60 justos se corta" \
  '    if len(clave) <= _MAX_VENDOR_ID:' \
  '    if len(clave) < _MAX_VENDOR_ID:' \
  "FAILED $T::test_un_proveedor_latino_conserva_su_id[60-entra]"
sabotaje $C "una clave de proveedor de 61 se guarda entera" \
  '_MAX_VENDOR_ID = 60' \
  '_MAX_VENDOR_ID = 70' \
  "FAILED $T::test_un_proveedor_latino_conserva_su_id[61-se-corta]"
# D77: producto
sabotaje $C "«º», «ª» y «µ» vuelven a cambiar el id del proveedor latino" \
  'c > "\u024f" and ' \
  '' \
  "FAILED $T::test_un_proveedor_latino_conserva_su_id"
sabotaje $C "«Nº» en el nombre se lee «No» y el proveedor latino cambia de id" \
  'text = unicodedata.normalize("NFD", text)' \
  'text = unicodedata.normalize("NFKD", text)' \
  "FAILED $T::test_un_proveedor_latino_conserva_su_id[Industrias Garc"
sabotaje $C "la clave del producto vuelve a perder las letras no latinas" \
  'return f"{clave}~{sufijo}" if sufijo else clave' \
  'return clave' \
  "FAILED $T::test_productos_sin_letras_latinas_con_la_misma_medida_no_se_pisan"
sabotaje $C "el parecido vuelve a ignorar las letras no latinas" \
  '    if sufijo_a and sufijo_b:
        return 0.0' \
  '' \
  "FAILED $T::test_productos_sin_letras_latinas_con_la_misma_medida_no_se_pisan"
sabotaje $C "la clave vuelve a distinguir lo que se lee igual" \
  'return _clave(_compatible(descripcion))' \
  'return _clave(descripcion)' \
  "FAILED $T::test_lo_que_se_lee_igual_se_encuentra"
sabotaje $C "«Nº» vuelve a ser «No» y no «N°»" \
  'c if c in "ºª№™℠"' \
  'c if c in "№™℠"' \
  "FAILED $T::test_lo_que_se_lee_igual_se_encuentra[Tornillo N"
sabotaje $C "«Bolt™» vuelve a ser «BoltTM» y no «Bolt»" \
  'c if c in "ºª№™℠"' \
  'c if c in "ºª№℠"' \
  "FAILED $T::test_lo_que_se_lee_igual_se_encuentra[Bolt"
sabotaje $C "los símbolos de unidad vuelven a quedar sin NFKC" \
  'c if c in "ºª№™℠" else' \
  'c if c in "ºª№™℠" or unicodedata.category(c)[0] == "S" else' \
  "FAILED $T::test_lo_que_se_lee_igual_se_encuentra[Tubo 10"
sabotaje $C "lo latino y lo que tiene además letras no latinas vuelve a ser exacto" \
  'return min(_similarity(base_a, base_b), FUZZY_THRESHOLD)' \
  'return _similarity(base_a, base_b)' \
  "FAILED $T::test_lo_que_se_lee_igual_se_encuentra[Screw M8-"
sabotaje $M "la migración no le da la clave de hoy al producto" \
  'nueva = catalog_svc.clave_de_producto(descripcion) if descripcion else clave' \
  'nueva = clave' \
  "FAILED $T::test_la_migracion_separa_los_proveedores_y_los_productos_mezclados"
sabotaje $M "la migración no mira las filas sin proveedor" \
  "\"OR vendor_id = '' OR length(vendor_id) >= 60 ORDER BY id\"" \
  '"OR length(vendor_id) >= 60 ORDER BY id"' \
  "FAILED $T::test_la_migracion_separa_los_proveedores_y_los_productos_mezclados"
sabotaje $M "la migración no salta la fila que choca" \
  '"AND o.vendor_id = :nuevo AND o.product_key = :nueva AND o.id <> :id)"' \
  '"AND o.vendor_id = :nuevo AND o.product_key = :nueva AND o.id = -1)"' \
  "FAILED $T::test_la_migracion_separa_los_proveedores_y_los_productos_mezclados"
# D78: memoria y NCM recordado
CM=proyecto_maria/services/client_memory.py
sabotaje $CM "la memoria del cliente compara sin las letras no latinas" \
  'parecido(clave, clave_de_producto(row.descripcion or ""))' \
  'parecido(clave.partition("~")[0], clave_de_producto(row.descripcion or "").partition("~")[0])' \
  "FAILED $T::test_la_memoria_del_cliente_usa_la_misma_clave"
sabotaje $CM "ante un empate vuelve a no preferir el texto idéntico" \
  'propia is not None and propia[2] == row.clave,' \
  'False,' \
  "FAILED $T::test_ante_un_empate_gana_el_texto_identico"
sabotaje $CM "el texto idéntico vuelve a distinguir mayúsculas y espacios" \
  'propia is not None and propia[2] == row.clave,' \
  'propia is not None and propia[1] == (row.descripcion or ""),' \
  'FAILED tests/test_catalogo3.py::test_ante_un_empate_gana_el_texto_identico[Cable 2,5mm\xb2-Cable 2,5mm2-buscados2-'
sabotaje $CM "ante un empate vuelve a ganar una fila fija" \
  $'row.ultima_vez is not None,\n                row.ultima_vez, row.ncm, row.descripcion or "", row.id)' \
  'row.id)' \
  "FAILED $T::test_ante_un_empate_gana_la_ultima_confirmada"
sabotaje $CM "a la misma hora vuelve a decidir el id de la fila" \
  'row.ncm, row.descripcion or "", row.id)' \
  'row.id)' \
  "FAILED $T::test_un_empate_a_la_misma_hora_no_depende_del_orden"
sabotaje $CM "ante un empate vuelve a quedarse la primera fila que trae la base" \
  'key=desempate)' \
  'key=lambda row: 0)' \
  "FAILED $T::test_ante_un_empate_gana"
sabotaje $M "el NCM recordado vuelve a comparar con la clave vieja" \
  'catalog_svc.clave_de_producto(recordado.get("descripcion") or "")' \
  'catalog_svc._normalize(recordado.get("descripcion") or "")' \
  "FAILED $T::test_el_ncm_recordado_compara_con_la_clave_del_catalogo"
# D80: un criterio de origen
sabotaje $G "el criterio vuelve a recortar a 3" \
  'return escrito.upper() if len(escrito) == 2 else escrito' \
  'return escrito.upper()[:3]' \
  "FAILED $T::test_el_extractor_conserva_el_nombre_del_pais"
sabotaje $G "el servidor vuelve a no leer el ancho completo" \
  's = unicodedata.normalize("NFKD", str(pais))' \
  's = unicodedata.normalize("NFD", str(pais))' \
  'FAILED '"$CF"'[\uff23\uff28\uff29\uff2e\uff21]'
sabotaje $J "la pantalla vuelve a no leer el ancho completo" \
  ".normalize('NFKD')" \
  ".normalize('NFD')" \
  "FAILED $PS"
sabotaje $G "el servidor vuelve a aceptar un nombre que contradice el código" \
  '(nombre is None or ' \
  '(True or ' \
  "FAILED $CF[310 - Vietnam]"
sabotaje $J "la pantalla vuelve a aceptar un nombre que contradice el código" \
  "return nombre === null || nombre === normalize(country.name) || ALIASES[nombre] === code[1] ? code[1] : '';" \
  "return code[1];" \
  "FAILED $PS"
sabotaje $J "la pantalla vuelve a reconocer una provincia como país" \
  "const ALIASES = {" \
  'const ALIASES = {"CORDOBA":"256",' \
  "FAILED $PS"
sabotaje $J "la pantalla vuelve a recortar con trim()" \
  "return value.replace(new RegExp('^' + ESPACIO + '+|' + ESPACIO + '+\$', 'g'), '');" \
  "return value.trim();" \
  "first extra item: ('\ufeffCHINA', '310', '')"
sabotaje $J "la pantalla vuelve a contar el largo en UTF-16" \
  "[...raw].length <= 2" \
  "raw.length <= 2" \
  "one more item: ('𝐁𝐑', '203', '')"
sabotaje $J "el nombre después del código vuelve a cortarse en \u2028" \
  "([^\\\\n]+))?\$');" \
  "(.+))?\$');" \
  "one more item: ('302\u2028·\u2028ARABIA\u2028SAUDITA', '', '302')"
sabotaje $J "la pantalla vuelve a colapsar los espacios con \s" \
  ".replace(ESPACIOS, ' ')" \
  ".replace(/\\s+/g, ' ')" \
  "Left contains 3 more items"
sabotaje $G "un espacio raro en el medio vuelve a quedar" \
  'escrito = " ".join(unicodedata.normalize("NFC", str(texto)).split())' \
  'escrito = unicodedata.normalize("NFC", str(texto)).strip()' \
  "FAILED $CF[HONG\\u2009KONG]"
sabotaje $E "la exportación vuelve a tener su propio criterio" \
  '    return get_pais_codigo_import(pais, PAIS_DEFAULT_EXPORT)' \
  '    return PAISES_INDEC.get(str(pais).strip().upper(), PAIS_DEFAULT_EXPORT)' \
  'FAILED '"$CF"'[HONG\u2009KONG]'
sabotaje $G "«ÉS» vuelve a pasar como «ES»" \
  'if len(escrito) <= 2 and not (escrito.isascii() and escrito.isalpha()):' \
  'if False:' \
  "FAILED $B[acento]"
sabotaje $G "«Ñ» con la tilde aparte vuelve a pasar" \
  'escrito = unicodedata.normalize("NFC", str(texto or "")).strip()' \
  'escrito = str(texto or "").strip()' \
  "FAILED $B[acento aparte]"
sabotaje $G "un código de miles de cifras vuelve a dar 500" \
  'm = re.fullmatch(r"0?([0-9]{3})(?:' \
  'm = re.fullmatch(r"0?([0-9]+)(?:' \
  "FAILED $CF[1111"
sabotaje $G "get_pais_codigo vuelve a hacer int() de cualquier tira de cifras" \
  're.fullmatch(r"[0-9]{1,4}", str(pais).strip())' \
  're.fullmatch(r"[0-9]+", str(pais).strip())' \
  "FAILED $T::test_un_origen_de_miles_de_cifras_no_rompe_los_avisos_ni_el_txt"
sabotaje proyecto_maria/pdf_extractor.py "el extractor vuelve a recortar a 3" \
  "origen = origen_valido(str(it.get('origen') or '')) or 'XX'" \
  "origen = str(it.get('origen') or '').strip().upper()[:3] or 'XX'" \
  "FAILED $T::test_el_extractor_conserva_el_nombre_del_pais"
sabotaje $M "guardar-uso vuelve a perder el NCM por el origen" \
  'origin, aviso_origen = catalog_svc.origen_para_guardar(data.get("origen"))' \
  'origin, aviso_origen = catalog_svc.origen_para_guardar(data.get("origen"))
        if aviso_origen:
            raise ValueError(aviso_origen)' \
  "FAILED $T::test_guardar_uso_no_pierde_el_ncm_por_un_origen_que_no_reconoce"
sabotaje $C "el PUT vuelve a perder el NCM por el origen" \
  '        if not aviso:
            textos["origen"] = origen' \
  '        if aviso:
            raise ValueError(aviso)
        textos["origen"] = origen' \
  "FAILED $T::test_cambiar_el_ncm_de_una_fila_con_origen_viejo_guarda_el_ncm"
sabotaje $G "el TXT vuelve a agrupar por la forma del país" \
  "origenes = {clave_de_origen(it.get('pais_origen') or it.get('origen')) for it in grupo_items}" \
  "origenes = {str(it.get('pais_origen') or it.get('origen')) for it in grupo_items}" \
  "FAILED $T::test_el_txt_agrupa_el_mismo_pais_escrito_de_tres_formas"
sabotaje $M "agrupar por la API vuelve a comparar la forma del país" \
  'origenes = {clave_de_origen(it.origen) for it in items}' \
  'origenes = {it.origen for it in items}' \
  "FAILED $T::test_agrupar_por_la_api_acepta_el_mismo_pais_escrito_de_tres_formas"
sabotaje $M "el origen frecuente vuelve a contar la forma" \
  'por_pais.setdefault(clave_de_origen(origen), [0, origen])' \
  'por_pais.setdefault(origen, [0, origen])' \
  "FAILED $T::test_el_origen_frecuente_cuenta_el_pais_y_no_la_forma"
sabotaje proyecto_maria/core/tarifar_connector.py "el estimador vuelve a pedir dos letras" \
  'if not pais_reconocido(item.origen):' \
  'if len(item.origen or "") != 2:' \
  "FAILED $T::test_el_estimador_de_tarifar_reconoce_el_pais_igual_que_el_catalogo[TAIWAN-False]"
# D84: el error nombra el producto
sabotaje $C "el 400 vuelve a no nombrar el producto" \
  'raise ValueError(f"{cual}: {e}") from None' \
  'raise' \
  "FAILED $T::test_el_error_del_catalogo_nombra_el_producto"
sabotaje $F "la pantalla vuelve a decir «algunos»" \
  "detail: res.ok ? '' : textoDeError(data && data.detail, '')" \
  "detail: ''" \
  "FAILED $D"

sabotaje $C "un origen no reconocido vuelve a rechazar el lote" \
  'origen, aviso = origen_para_guardar(prod.get("origen"))' \
  'origen, aviso = origen_para_guardar(prod.get("origen"))
    if aviso:
        raise ValueError(aviso)' \
  "FAILED $T::test_un_origen_que_no_reconoce_no_hace_perder_el_lote"
sabotaje $F "la pantalla vuelve a no avisar los productos sin origen" \
  "r.avisos && r.avisos.length && " \
  "false && " \
  "FAILED $D2"
sabotaje $X "el extractor vuelve a tirar el origen hecho de cifras" \
  "if not texto or texto.upper() in ('NA', 'N/A'):" \
  "if not texto or texto.isdigit() or texto.upper() in ('NA', 'N/A'):" \
  "FAILED $T::test_el_extractor_conserva_el_nombre_del_pais"

sabotaje $C "la clave de cada fila vuelve a calcularse una vez por ítem" \
  "@functools.lru_cache(maxsize=4096)" \
  "@functools.lru_cache(maxsize=0)" \
  "FAILED $T::test_un_pedido_calcula_la_clave_de_cada_fila_una_sola_vez"

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
