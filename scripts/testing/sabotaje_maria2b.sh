#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria2b.sh [SHA] [venv]
# Negativos discriminantes de MARIA-2b (Gemini caído o con clave inválida:
# el 503 de carga manual, en las dos copias del lector). Cada sabotaje se aplica en un worktree descartable, corre
# tests/test_maria2b_gemini_falla.py y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria2b"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA=tests/test_maria2b_gemini_falla.py

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
T=tests/test_maria2b_gemini_falla.py

# 1. la copia de producción no marca la falla de Gemini
reemplazar $F "                except Exception as model_err:
                    gemini_fallo = True" "                except Exception as model_err:
                    gemini_fallo = False"
caso "directo_no_marca" "FAILED $T::test_gemini_falla_da_el_503_de_carga_manual[clave_invalida-pdf_directo]"

# 2. la copia PyMuPDF marca la falla pero no la avisa
reemplazar $F "    if gemini_fallo:
        raise LecturaAutomaticaNoDisponible(MENSAJE_LECTURA_NO_DISPONIBLE)
    return []" "    return []"
caso "pymupdf_no_avisa" "FAILED $T::test_gemini_falla_da_el_503_de_carga_manual[clave_invalida-pymupdf]"

# 3. arreglo de más: sin productos también da 503
reemplazar $F "    print(\"❌ Gemini Vision failed, returning empty\")
    if gemini_fallo:" "    print(\"❌ Gemini Vision failed, returning empty\")
    if True:"
caso "sin_productos_503" "FAILED $T::test_gemini_responde_sin_productos_sigue_el_400[pymupdf]"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 3 sabotajes dan rojo por la razón esperada"
