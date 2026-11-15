#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria1d.sh [SHA] [venv]
# Negativos discriminantes de MARIA-1d (un campo vacío de la factura no
# llega al TXT como «None»). Cada sabotaje se aplica en un
# worktree descartable, corre tests/test_maria1d_campos_vacios.py y tiene
# que dar ROJO con el motivo esperado. Si un patrón no se encuentra, el script
# sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria1d"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA=tests/test_maria1d_campos_vacios.py
T="FAILED $PRUEBA::"
G=proyecto_maria/core/maria_generator.py
M=proyecto_maria/main.py
X=proyecto_maria/pdf_extractor.py

correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider "$PRUEBA" 2>&1 || true
}

# reemplazar <archivo> <viejo> <nuevo>: falla si <viejo> no aparece una sola vez
reemplazar() {
  "$VENV/bin/python" - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p, encoding="utf-8").read()
n = s.count(viejo)
if n != 1:
    sys.exit(f"PATRON NO ENCONTRADO ({n} veces) en {p}: {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PY
}

# reemplazar_primero <archivo> <viejo> <nuevo>: sólo la primera de dos (las
# dos copias del lector)
reemplazar_primero() {
  "$VENV/bin/python" - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p, encoding="utf-8").read()
n = s.count(viejo)
if n != 2:
    sys.exit(f"PATRON NO ENCONTRADO ({n} veces, se esperaban 2) en {p}: {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo, 1))
PY
}

FALLAS=0
caso() {  # caso <nombre> <texto que el rojo tiene que mostrar>
  local nombre="$1" espera="$2" salida
  salida="$(correr)"
  git checkout -q -- .
  if grep -q "passed" <<<"$salida" && ! grep -q "failed" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  if grep -qF -- "$espera" <<<"$salida"; then
    echo "ROJO   $nombre: $(grep -E '[0-9]+ failed' <<<"$salida" | tail -1)"
  else
    echo "FALLA  $nombre: rojo, pero sin «$espera»"; FALLAS=$((FALLAS+1))
    tail -15 <<<"$salida"
  fi
}

# 0. sin sabotaje: verde
base="$(correr)"
if grep -q "failed" <<<"$base" || ! grep -qE "[0-9]+ passed" <<<"$base"; then
  echo "FALLA: la prueba no está verde sin sabotaje"; tail -20 <<<"$base"; exit 1
fi
echo "VERDE  sin sabotaje: $(grep -E 'passed' <<<"$base" | tail -1)"


# 1. vuelve el «None»
reemplazar $X '    texto = "" if raw is None else str(raw).strip()' '    texto = str(raw).strip()'
reemplazar $X '    return "" if texto.upper() in _TEXTO_VACIO else texto' '    return texto'
caso vuelve_el_none "${T}test_campo_nulo_queda_vacio[vendedor_nombre-pdf_directo]"

# 2. una copia vuelve a inventar la moneda
reemplazar_primero $X "_texto(operacion.get('moneda'))[:3].upper()" "str(operacion.get('moneda', 'DOL'))[:3].upper()"
caso inventa_moneda "${T}test_moneda_e_incoterm_ausentes_no_se_inventan[moneda-pymupdf]"

# 3. sin aviso de la carátula vacía
reemplazar $G "    if items and any(v is not None for v in caratula):" "    if False:"
caso sin_aviso_caratula "${T}test_avisa_lo_que_falta_de_la_caratula"

# 4. al generar, la carátula no llega a los supuestos. La misma función arma
# los avisos previos, que este guion no mira
reemplazar $M "        vendedor_nombre=request.vendedor_nombre,
        comprador_nombre=request.comprador_nombre,
        comprador_cuit=request.comprador_cuit,
        moneda=request.moneda,
" ""
caso endpoint_sin_caratula "${T}test_ningun_none_en_el_txt_de_una_factura_vacia[pdf_directo]"

# 5. lo leído llega con espacios
reemplazar $X '    texto = "" if raw is None else str(raw).strip()' '    texto = "" if raw is None else str(raw)'
caso sin_limpiar "${T}test_lo_que_se_leyo_llega_limpio[pdf_directo]"

# 6. el vacío escrito como texto pasa
reemplazar $X "_TEXTO_VACIO = {'NONE', 'NULL', 'N/A'}" "_TEXTO_VACIO = set()"
caso vacio_como_texto "${T}test_el_vacio_escrito_como_texto_queda_vacio[None-pdf_directo]"

# 7. una descripción que no es texto tira el producto
reemplazar $X "    descripcion = _texto(item_data.get('descripcion'))" "    descripcion = item_data.get('descripcion', '')"
caso descripcion_numero "${T}test_una_descripcion_que_no_es_texto_no_tira_el_producto[pymupdf]"

# 8. los avisos previos no dicen la procedencia rara de un producto
reemplazar $M '"avisos": errores_de_procedencia(items) + ' '"avisos": '
caso procedencia_rara_sin_aviso "${T}test_procedencia_rara_de_un_producto_avisa_igual_antes_y_al_generar["

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 8 sabotajes dan rojo por la razón esperada"
