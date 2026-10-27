#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_separadores1d.sh [SHA] [venv]
# Negativos discriminantes de SEPARADORES-1d: la regla de miles de 1c vale
# también para cantidades, precios y pesos (D24); el flete y el seguro con
# más de dos decimales avisan qué lleva el TXT, con el mismo redondeo que el
# generador (D25). Cada sabotaje se aplica en un worktree descartable, corre
# los casos y tiene que dar ROJO con el motivo esperado. Si un patrón no se
# encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-separadores1d"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_separadores1d.py tests/test_separadores1c.py tests/test_separadores1b.py"
[ -d /opt/node22/bin ] && export PATH="/opt/node22/bin:$PATH"
correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider $PRUEBA 2>&1 || true
}

# reemplazar <archivo> <viejo> <nuevo> [veces]: falla si <viejo> no aparece
# exactamente esas veces (una, si no se dice)
reemplazar() {
  "$VENV/bin/python" - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
veces = int(sys.argv[4]) if len(sys.argv) > 4 else 1
s = open(p, encoding="utf-8").read()
n = s.count(viejo)
if n != veces:
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

P=proyecto_maria/pdf_extractor.py
F=proyecto_maria/static/v2/screens/finalize.js
T=tests/test_separadores1d.py

# --- 1. Cantidades, precios y pesos (D24)

# 1. vuelve a lo de antes: la regla sólo en el flete y el seguro
reemplazar $P '    # SEPARADORES-1d (D24): la regla de miles de 1c vale para todo número de
    # la factura (flete, seguro, cantidad, precio y peso). «0.500.000» no se
    # lee como 500000: queda vacío, como «12x3».
    if _miles_mal_formados(t, decimal):
        return None
' ''
reemplazar $P "    t = _MONEDA_O_CUENTA_ATRAS.sub('', t).strip()
    miles = re.fullmatch(" "    t = _MONEDA_O_CUENTA_ATRAS.sub('', t).strip()
    if _miles_mal_formados(t, decimal):
        return None
    miles = re.fullmatch("
caso "numero_sin_regla" "FAILED $T::test_en_la_factura_queda_vacio_y_no_multiplicado[cantidad-cantidad-pymupdf]"

# 2. la guarda: lo bien formado con grupos de miles también queda sin leer
reemplazar $P '    if _miles_mal_formados(t, decimal):
        return None
' '    if _miles_mal_formados(t, decimal) or re.search(r"\d[ .,]\d{3}(?!\d)", t):
        return None
'
caso "numero_sin_miles" "FAILED $T::test_lo_bien_formado_se_lee_como_hoy[1.250-,-1250.0]"

# --- 2. Más de dos decimales en el flete y el seguro (D25)

# 3. vuelve a lo de antes: la revisión no suma el aviso
reemplazar $F "        const deLaPantalla = (CDI.despachante && CDI.despachante.avisos ? CDI.despachante.avisos() : [])
            .concat(avisosDeLosMontos((CDI.state && CDI.state.operacion) || {}));" "        const deLaPantalla = CDI.despachante && CDI.despachante.avisos ? CDI.despachante.avisos() : [];"
caso "revision_sin_aviso" "FAILED $T::test_el_aviso_va_junto_a_los_otros_avisos_no_bloqueantes"

# 4. el redondeo con Math.round: 2,675 daría 2,67 y el TXT lleva 2,68
reemplazar $F "        const cent = BigInt(entero + dec.slice(0, 2)) + (dec[2] >= '5' ? 1n : 0n);
        const t = cent.toString().padStart(3, '0');
        return t.slice(0, -2) + ',' + t.slice(-2);" "        return (Math.round(n * 100) / 100).toFixed(2).replace('.', ',');"
caso "redondeo_math_round" "FAILED $T::test_la_pantalla_redondea_igual_que_el_generador"

# 5. la guarda: con dos decimales también avisa
reemplazar $F "        if (dec.length <= 2) return null;" "        if (dec.length < 1) return null;"
caso "aviso_con_dos_decimales" "FAILED $T::test_con_dos_decimales_o_menos_no_hay_aviso[op0]"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 5 sabotajes dan rojo por la razón esperada"
