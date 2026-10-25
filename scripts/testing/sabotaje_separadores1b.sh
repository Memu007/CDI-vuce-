#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_separadores1b.sh [SHA] [venv]
# Negativos discriminantes de SEPARADORES-1b: lo que la pantalla no puede leer
# viaja tal cual y el servidor lo rechaza con mensaje (D19 b); «4500.000» con
# la pista decimal en contra queda sin leer en la factura y se pregunta en la
# pantalla. Cada sabotaje se aplica en un worktree descartable, corre los
# casos y tiene que dar ROJO con el motivo esperado. Si un patrón no se
# encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-separadores1b"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_separadores1b.py tests/test_separadores1.py tests/test_valor1.py"
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
A=proyecto_maria/static/v2/montos_ar.js
J=proyecto_maria/static/v2/screens/finalize.js
G=proyecto_maria/core/maria_generator.py
M=proyecto_maria/main.py
T=tests/test_separadores1b.py

# --- La factura

# 1. «4500.000» con la coma decimal vuelve a leerse 4500000
reemplazar $P '        if sin_grupo and decimal != sin_grupo.group(1):' '        if False:'
caso "factura_multiplica" "FAILED $T::test_en_la_factura_con_la_pista_en_contra_queda_sin_leer"

# 2. la regla deja sin leer aunque la pista esté a favor
reemplazar $P '        if sin_grupo and decimal != sin_grupo.group(1):' '        if sin_grupo:'
caso "factura_ignora_la_pista" "FAILED $T::test_en_la_factura_lo_demas_sigue_como_hoy[4500.000-.-4500.0]"

# --- La pantalla

# 3. «2500.125» se lee 2500,125 sin preguntar
reemplazar $A "            } else if (/^[1-9]\\d{3,}\$/.test(partes[0]) && partes[1].length === 3) {" "            } else if (false) {"
caso "pantalla_no_pregunta" "FAILED $T::test_en_la_pantalla_se_pregunta"

# 4. el monto que no se pudo leer viaja como 0
reemplazar $J '        if (r.error) return String(v).trim();' '        if (r.error) return 0;'
caso "pedido_monto_cero" "-montoDelPedido] - assert 0 =="

# 5. el ajuste que no se pudo leer no viaja
reemplazar $J '        return r.error ? String(v).trim() : r.valor;' '        return r.valor;'
caso "pedido_ajuste_nada" "-ajusteDelPedido] - assert None =="

# --- El servidor

# 6. el texto se lee como lo lee Python («3.480» → 3,48; «1e3» → 1000)
reemplazar $G '        if not _IMPORTE_ESCRITO.fullmatch(valor):' '        if False:'
caso "servidor_lee_como_python" "FAILED $T::test_el_servidor_no_genera_con_un_monto_ilegible[3.480-flete-Flete: ]"

# 7. el flete vuelve a ser sólo número: el texto da 422 crudo
reemplazar $M '    flete: float | str = 0' '    flete: float = 0'
caso "flete_solo_numero" "assert 422 == 400"

# 8. /generate_maria no pasa los importes a número
reemplazar $M '        _importes_como_numeros(request)
        _viejo =' '        _viejo ='
caso "generar_sin_normalizar" "FAILED $T::test_un_importe_vacio_cuenta_como_cero"

# 9. los avisos no miran los importes
reemplazar $M '        _importes_como_numeros(request)
    except ValueError' '        pass
    except ValueError'
caso "avisos_sin_mirar" "FAILED $T::test_los_avisos_dicen_cual_es_el_monto_ilegible"

# 10. el importe en blanco deja de contar como no vino
reemplazar $G '        if not valor:
            return None
        if not _IMPORTE_ESCRITO' '        if not _IMPORTE_ESCRITO'
caso "blanco_no_es_cero" "FAILED $T::test_un_importe_vacio_cuenta_como_cero"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 10 sabotajes dan rojo por la razón esperada"
