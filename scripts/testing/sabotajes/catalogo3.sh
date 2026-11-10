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
PRUEBA=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T" "$B" "$A" "$D")

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

if ! "${PRUEBA[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

# D76: proveedor
sabotaje $C "el proveedor sólo CJK vuelve a quedar con id vacío" \
  'clave = clave_de_producto(nombre).replace(" ", "_")' \
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
# D77: producto
sabotaje $C "«º», «ª» y «µ» vuelven a cambiar el id del proveedor latino" \
  'c > "\u024f" and ' \
  '' \
  "FAILED $T::test_un_proveedor_latino_conserva_su_id"
sabotaje $C "la clave del producto vuelve a perder las letras no latinas" \
  'return f"{clave}~{sufijo}" if sufijo else clave' \
  'return clave' \
  "FAILED $T::test_productos_sin_letras_latinas_con_la_misma_medida_no_se_pisan"
sabotaje $C "el parecido vuelve a ignorar las letras no latinas" \
  '    if sufijo_a != sufijo_b:
        return 0.0' \
  '' \
  "FAILED $T::test_productos_sin_letras_latinas_con_la_misma_medida_no_se_pisan"
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
sabotaje proyecto_maria/services/client_memory.py "la memoria del cliente compara sin las letras no latinas" \
  'score = parecido(clave, clave_de_producto(row.descripcion or ""))' \
  'score = parecido(clave.partition("~")[0], clave_de_producto(row.descripcion or "").partition("~")[0])' \
  "FAILED $T::test_la_memoria_del_cliente_usa_la_misma_clave"
sabotaje $M "el NCM recordado vuelve a comparar con la clave vieja" \
  'catalog_svc.clave_de_producto(recordado.get("descripcion") or "")' \
  'catalog_svc._normalize(recordado.get("descripcion") or "")' \
  "FAILED $T::test_el_ncm_recordado_compara_con_la_clave_del_catalogo"
# D80: un criterio de origen
sabotaje $G "el criterio vuelve a recortar a 3" \
  'return escrito.upper() if len(escrito) == 2 else escrito' \
  'return escrito.upper()[:3]' \
  "FAILED $T::test_el_extractor_conserva_el_nombre_del_pais"
sabotaje $G "el ancho completo vuelve a pasar" \
  'if not escrito or unicodedata.normalize("NFKC", escrito) != escrito:' \
  'if not escrito:' \
  "FAILED $B[nombre ancho completo]"
sabotaje $G "«ÉS» vuelve a pasar como «ES»" \
  'if len(escrito) <= 2 and not (escrito.isascii() and escrito.isalpha()):' \
  'if False:' \
  "FAILED $B[acento]"
sabotaje $G "«É» con el acento aparte vuelve a pasar" \
  'escrito = unicodedata.normalize("NFC", str(texto or "")).strip()' \
  'escrito = str(texto or "").strip()' \
  "FAILED $A[acento aparte]"
sabotaje $G "un código de miles de cifras vuelve a dar 500" \
  're.fullmatch(r"[0-9]{1,4}", texto)' \
  're.fullmatch(r"[0-9]+", texto)' \
  "FAILED $B[cifras de mas]"
sabotaje $G "get_pais_codigo vuelve a hacer int() de cualquier tira de cifras" \
  're.fullmatch(r"[0-9]{1,4}", str(pais).strip())' \
  're.fullmatch(r"[0-9]+", str(pais).strip())' \
  "FAILED $T::test_un_origen_de_miles_de_cifras_no_rompe_los_avisos_ni_el_txt"
sabotaje proyecto_maria/pdf_extractor.py "el extractor vuelve a recortar a 3" \
  "origen = origen_valido(str(it.get('origen') or '')) or 'XX'" \
  "origen = str(it.get('origen') or '').strip().upper()[:3] or 'XX'" \
  "FAILED $T::test_el_extractor_conserva_el_nombre_del_pais"
sabotaje $M "guardar-uso vuelve a aceptar cualquier origen" \
  'origin = catalog_svc.origen_para_guardar(data.get("origen"))' \
  'origin = str(data.get("origen") or "")' \
  "FAILED $T::test_guardar_uso_con_un_origen_que_no_es_pais_da_400_y_no_suma"
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
  'raise ValueError(f"Producto {n}{cual}: {e}") from None' \
  'raise' \
  "FAILED $T::test_el_error_del_catalogo_nombra_el_producto"
sabotaje $F "la pantalla vuelve a decir «algunos»" \
  "detail: res.ok ? '' : textoDeError(data && data.detail, '')" \
  "detail: ''" \
  "FAILED $D"

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
