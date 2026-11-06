#!/usr/bin/env bash
# Negativos de CATALOGO-LARGO-2: cada sabotaje deshace una línea de la pieza y
# tests/test_catalogo_largo2.py tiene que ponerse roja por ese motivo. Con
# PG_URL (un Postgres local y descartable), también la migración contra
# scripts/testing/catalogo_largo2_postgres.py. El tope medido en NFC lo
# distinguen los sabotajes de catalogolargo1.sh.
#
# uso: PY=/ruta/al/venv/bin/python [PG_URL=postgresql://cdi@127.0.0.1:5432/postgres] \
#        scripts/testing/sabotajes/catalogo_largo2.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG_URL="${PG_URL:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0
T=tests/test_catalogo_largo2.py
PRUEBA=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T")
PRUEBA_PG=("$PY" -I scripts/testing/catalogo_largo2_postgres.py "$PG_URL")

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
# Corre la prueba de "${CORRE[@]}".
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado falta=""; shift 4
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
  salida="$("${CORRE[@]}" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
    return
  fi
  for esperado in "$@"; do grep -qF -- "$esperado" <<<"$salida" || falta="$esperado"; done
  if [ -z "$falta" ]; then
    echo "ROJO  | $nombre: dice «$*»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$falta»"
    grep -E "^E |^FALLA" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
CS=proyecto_maria/core/catalog_service.py
MO=proyecto_maria/database/models.py
CM=proyecto_maria/services/client_memory.py
MEM=test_la_memoria_del_cliente_guarda_el_origen_entero
TOPE=test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar
SIN=test_lo_que_no_tiene_letras_latinas_se_guarda_sin_cruzarse

CORRE=("${PRUEBA[@]}")
if ! "${CORRE[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $MO "el origen vuelve a tener tope de 5" \
  '    origen = Column(Text, nullable=True)' \
  '    origen = Column(String(5), nullable=True)' \
  "FAILED $T::test_el_origen_y_el_proveedor_no_tienen_tope_en_la_base" "AssertionError: origen"
sabotaje $MO "el proveedor vuelve a tener tope de 200" \
  '    vendor_nombre = Column(Text, nullable=True)' \
  '    vendor_nombre = Column(String(200), nullable=True)' \
  "FAILED $T::test_el_origen_y_el_proveedor_no_tienen_tope_en_la_base" "AssertionError: vendor_nombre"
sabotaje $CM "la memoria del cliente recorta el origen a 3 al crear" \
  '            origen_frecuente=origen or "XX",' \
  '            origen_frecuente=origen[:3] or "XX",' \
  "FAILED $T::${MEM}[guardar-uso]" "FAILED $T::${MEM}[aprender]" "FAILED $T::${MEM}[operacion]"
sabotaje $CM "la memoria del cliente recorta el origen a 3 al cambiarlo" \
  '        existing.origen_frecuente = origen' \
  '        existing.origen_frecuente = origen[:3]' \
  "FAILED $T::${MEM}[cambiar]"
sabotaje $MO "el origen de la memoria del cliente vuelve a tener tope de 3" \
  '    origen_frecuente = Column(Text, default="XX")' \
  '    origen_frecuente = Column(String(3), default="XX")' \
  "FAILED $T::test_el_origen_y_el_proveedor_no_tienen_tope_en_la_base" "AssertionError: origen_frecuente"
sabotaje $CS "el catálogo no mide el proveedor" \
  '    validar_largo(vendor_name, "El proveedor")' \
  '    pass' \
  "FAILED $T::${TOPE}[catalogo-proveedor]"
sabotaje $CS "guardar en el catálogo no mide el origen" \
  '        validar_largo(origen, "El origen")

' \
  '
' \
  "FAILED $T::${TOPE}[catalogo-origen]"
sabotaje $CS "una fila sin descripción se mide antes de saltarla" \
  '        if not desc:
            continue
        validar_largo(desc)' \
  '        validar_largo(desc)
        validar_largo((prod.get("origen") or "").strip(), "El origen")
        if not desc:
            continue' \
  "FAILED $T::test_una_fila_sin_descripcion_no_frena_el_lote_por_su_origen"
sabotaje $CM "la memoria del cliente no mide el origen" \
  '        validar_largo(origen, "El origen")
    except ValueError:' \
  '        pass
    except ValueError:' \
  "FAILED $T::test_la_memoria_del_cliente_no_guarda_un_origen_de_mas_de_2000[aprender]" \
  "FAILED $T::test_la_memoria_del_cliente_no_guarda_un_origen_de_mas_de_2000[operacion]"
sabotaje $CS "cambiar el origen no lo mide" \
  '        validar_largo(origen, "El origen")
        row.origen' \
  '        row.origen' \
  "FAILED $T::${TOPE}[cambiar-origen-origen]"
sabotaje $M "guardar-uso no mide el proveedor" \
  '        catalog_svc.validar_largo(vendor_name, "El proveedor")' \
  '        pass' \
  "FAILED $T::${TOPE}[guardar-uso-proveedor]"
sabotaje $M "guardar-uso no mide el origen" \
  '        catalog_svc.validar_largo(origin, "El origen")' \
  '        pass' \
  "FAILED $T::${TOPE}[guardar-uso-origen]"
sabotaje $CS "sin letras latinas la clave queda vacía" \
  '    return "~" + hashlib.sha256(texto.encode("utf-8", "surrogatepass")).hexdigest()[:40]' \
  '    return ""' \
  "FAILED $T::${SIN}[catalogo]" "FAILED $T::${SIN}[guardar-uso]"
sabotaje $CS "la clave junta ß con ss" \
  '    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())' \
  '    text = re.sub(r"[^a-z0-9\s]", " ", text.casefold())' \
  "FAILED $T::${SIN}[catalogo]" "FAILED $T::${SIN}[guardar-uso]"
sabotaje $CS "la clave junta ﬁ con fi" \
  '    text = unicodedata.normalize("NFD", text)' \
  '    text = unicodedata.normalize("NFKD", text)' \
  "FAILED $T::${SIN}[catalogo]" "FAILED $T::${SIN}[guardar-uso]"
sabotaje $CS "guardar en el catálogo usa la clave vieja" \
  '        product_key = clave_de_producto(desc)' \
  '        product_key = _normalize(desc)' \
  "FAILED $T::${SIN}[catalogo]" "FAILED $T::${SIN}[guardar-uso]"
sabotaje $CS "buscar en el catálogo usa la clave vieja" \
  '        desc_key = clave_de_producto(desc)' \
  '        desc_key = _normalize(desc)' \
  "FAILED $T::${SIN}[catalogo]" "FAILED $T::${SIN}[guardar-uso]"
sabotaje $CS "cambiar un producto usa la clave vieja" \
  '        candidate = clave_de_producto(new_desc)' \
  '        candidate = _normalize(new_desc)' \
  "FAILED $T::test_cambiar_la_descripcion_a_una_sin_letras_latinas_mueve_la_clave"

if [ -n "$PG_URL" ]; then
  CORRE=("${PRUEBA_PG[@]}")
  git checkout -q -- proyecto_maria/
  if ! "${CORRE[@]}" >/dev/null 2>&1; then
    echo "BASE  | la prueba en Postgres ya está en rojo sin sabotaje"; FALLAS=$((FALLAS+1))
  else
    sabotaje $M "el arranque no pasa el origen a text" \
      "column_name IN ('product_key', 'descripcion', 'origen', 'vendor_nombre')) " \
      "column_name IN ('product_key', 'descripcion', 'vendor_nombre')) " \
      "FALLA | primer arranque: las columnas son text" "FALLA | el catálogo guarda enteros el origen"
    sabotaje $M "el arranque no pasa el proveedor a text" \
      "column_name IN ('product_key', 'descripcion', 'origen', 'vendor_nombre')) " \
      "column_name IN ('product_key', 'descripcion', 'origen')) " \
      "FALLA | primer arranque: las columnas son text" "FALLA | el catálogo guarda enteros el origen"
    sabotaje $M "el arranque no pasa el origen de la memoria del cliente a text" \
      "OR (table_name = 'client_product_history' AND column_name = 'origen_frecuente')) " \
      ") " \
      "FALLA | primer arranque: las columnas son text" "FALLA | guardar-uso con cliente guarda enteros"
    sabotaje $CS "sin letras latinas la clave es el texto entero y no entra en el índice" \
      '    return "~" + hashlib.sha256(texto.encode("utf-8", "surrogatepass")).hexdigest()[:40]' \
      '    return texto' \
      "FALLA | 2000 caracteres CJK por catálogo" "FALLA | 2000 caracteres CJK por guardar-uso" \
      "FALLA | 2000 caracteres CJK por cambiar la descripción"
  fi
else
  echo "SALTO | sin PG_URL: la migración no se midió"
fi

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
