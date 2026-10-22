#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria1a.sh [SHA] [venv]
# Negativos discriminantes de MARIA-1a (la factura bien leída: país,
# números y datos faltantes, en las dos copias del lector). Cada sabotaje se aplica en un worktree descartable, corre
# tests/test_maria1a_lectura_factura.py y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria1a"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA=tests/test_maria1a_lectura_factura.py

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
F=proyecto_maria/pdf_extractor.py
T=tests/test_maria1a_lectura_factura.py

# 1. el país vuelve a cortarse a dos letras (CHN → CH, Suiza)
reemplazar $F "    texto = str(raw or '').strip()
    # «NA» en una" "    return str(raw or '')[:2].upper()
    texto = str(raw or '').strip()
    # «NA» en una"
caso "corta_a_dos_letras" "'CH', 'ME'"

# 2. sin la tabla de tres letras
reemplazar $F "if len(mayus) == 3 and mayus in ISO3_A_ISO2:" "if False:"
caso "sin_tabla_iso3" "FAILED $T::test_pais_de_origen_contra_la_tabla_oficial[pdf_directo]"

# 3. se arregla una sola copia: la de producción vuelve a cortar
reemplazar $F "                                    'origen': _origen_desde_factura(item_data.get('origen'))," "                                    'origen': str(item_data.get('origen', ''))[:2].upper(),"
caso "una_sola_copia" "FAILED $T::test_pais_de_origen_contra_la_tabla_oficial[pdf_directo]"

# 4. «1,500» sin pistas se adivina como mil quinientos
reemplazar $F "            return None  # «1,500» o «1.500» sin otra pista: no se adivina" "            t = t.replace(sep, '')"
caso "adivina_1500" "FAILED $T::test_si_no_se_puede_saber_queda_vacio[pdf_directo]"

# 5. la coma decimal se toma como separador de miles («1,5» → 15)
reemplazar $F "        elif propio == sep:
            t = t.replace(sep, '.')" "        elif propio == sep:
            t = t.replace(sep, '')"
caso "coma_como_miles" "FAILED $T::test_numeros_de_una_factura_en_castellano[pdf_directo]"

# 6. vuelve el peso inventado de 0,5 kg (copia de producción)
reemplazar $F "    unitario = unitario if unitario > 0 else 0.0" "    unitario = unitario if unitario > 0 else 0.5"
caso "peso_0_5" "FAILED $T::test_lo_que_falta_no_se_inventa[pdf_directo]"

# 7. vuelve la cantidad inventada de 1 (copia PyMuPDF)
reemplazar $F "                        try:
                            cantidad = _numero_factura(item_data.get('cantidad'), decimal) or 0.0" "                        try:
                            cantidad = _numero_factura(item_data.get('cantidad'), decimal) or 1.0"
caso "cantidad_1" "FAILED $T::test_cantidad_que_falta_queda_vacia[pymupdf]"

# 8. vuelve el pedido a Gemini de estimar el peso
reemplazar $F "- valor_unitario: Precio por unidad
- peso_unitario: Peso neto de UNA unidad en kg (0 si la factura no lo dice; no estimar ni calcular)" "- valor_unitario: Precio por unidad
- peso_unitario: Peso neto de UNA unidad en kg (estimar 0.5 si no aparece)"
caso "prompt_estima_peso" "FAILED $T::test_instrucciones_a_gemini_no_piden_estimar_el_peso"

# 9. vuelve a pegar los dígitos de «12x3» o «500 g»
reemplazar $F "    if not re.fullmatch(" "    t = re.sub(r'[^0-9.,]', '', t)
    if not re.fullmatch("
caso "numero_sucio" "FAILED $T::test_lo_que_no_es_un_numero_limpio_queda_vacio[500 g]"

# 10. «NA» vuelve a ser Namibia
reemplazar $F "texto.upper() in ('NA', 'N/A')" "texto.upper() in ('N/A',)"
caso "na_namibia" "FAILED $T::test_na_no_es_namibia"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 10 sabotajes dan rojo por la razón esperada"
