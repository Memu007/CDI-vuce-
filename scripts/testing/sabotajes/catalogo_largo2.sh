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
sabotaje $CS "sin letras latinas la clave queda vacía" \
  '    return "~" + hashlib.sha256(texto.encode("utf-8", "surrogatepass")).hexdigest()[:40]' \
  '    return ""' \
  "FAILED $T::${SIN}[catalogo]" "FAILED $T::${SIN}[guardar-uso]"
sabotaje $CS "la clave junta ß con ss y ﬁ con fi" \
  '    texto = " ".join(unicodedata.normalize("NFC", descripcion).lower().split())' \
  '    texto = " ".join(unicodedata.normalize("NFC", descripcion).casefold().split())' \
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
      "AND column_name IN ('product_key', 'descripcion', 'origen', 'vendor_nombre') " \
      "AND column_name IN ('product_key', 'descripcion', 'vendor_nombre') " \
      "FALLA | primer arranque: las columnas son text" "FALLA | el catálogo guarda enteros el origen"
    sabotaje $M "el arranque no pasa el proveedor a text" \
      "AND column_name IN ('product_key', 'descripcion', 'origen', 'vendor_nombre') " \
      "AND column_name IN ('product_key', 'descripcion', 'origen') " \
      "FALLA | primer arranque: las columnas son text" "FALLA | el catálogo guarda enteros el origen"
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
