#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria2.sh [SHA] [venv]
# Negativos discriminantes de MARIA-2 (sin clave de Gemini no se inventan
# productos). Cada sabotaje se aplica en un worktree descartable, corre
# tests/test_maria2_sin_clave_gemini.py y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria2"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA=tests/test_maria2_sin_clave_gemini.py

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

# 1. vuelve el modo demostración
reemplazar proyecto_maria/pdf_extractor.py \
  "raise LecturaAutomaticaNoDisponible(MENSAJE_LECTURA_NO_DISPONIBLE)" \
  'return [{"pieza": "", "descripcion": "ITEM DEMOSTRACION (Falta API Key)", "cantidad": 10.0, "valor_unitario": 150.0, "origen": "CN", "peso_unitario": 1.0}]'
caso "vuelve_la_demo" "ITEM DEMOSTRACION"

# 1b. vuelve la demo y el endpoint no pregunta antes: llega a la pantalla
reemplazar proyecto_maria/pdf_extractor.py \
  "raise LecturaAutomaticaNoDisponible(MENSAJE_LECTURA_NO_DISPONIBLE)" \
  'return [{"pieza": "", "descripcion": "ITEM DEMOSTRACION (Falta API Key)", "cantidad": 10.0, "valor_unitario": 150.0, "origen": "CN", "peso_unitario": 1.0}]'
reemplazar proyecto_maria/main.py \
  "        if not lectura_automatica_disponible():
            # Sin lector con IA: cero productos, sin descontar" \
  "        if False:
            # Sin lector con IA: cero productos, sin descontar"
caso "demo_en_pantalla" "FAILED tests/test_maria2_sin_clave_gemini.py::test_endpoint_sin_lector_no_inventa_productos[sin_clave]"

# 2. el endpoint descuenta la cuota antes de saber si hay lector
reemplazar proyecto_maria/main.py \
  "        if not lectura_automatica_disponible():
            # Sin lector con IA: cero productos, sin descontar" \
  "        if False:
            # Sin lector con IA: cero productos, sin descontar"
caso "gasta_cuota" "FAILED tests/test_maria2_sin_clave_gemini.py::test_sin_lector_no_gasta_cuota_diaria"

# 2b. además no atrapa el error propio (cae al 500 genérico)
reemplazar proyecto_maria/main.py \
  "        if not lectura_automatica_disponible():
            # Sin lector con IA: cero productos, sin descontar" \
  "        if False:
            # Sin lector con IA: cero productos, sin descontar"
reemplazar proyecto_maria/main.py \
  "        except LecturaAutomaticaNoDisponible as e:" \
  "        except ZeroDivisionError as e:"
caso "endpoint_sin_503" "assert 500 == 503"

# 3. arreglo de más: el lector corta también con clave
reemplazar proyecto_maria/pdf_extractor.py \
  "    if not lectura_automatica_disponible():
        # Sin lector con IA no" \
  "    if True:
        # Sin lector con IA no"
caso "corta_con_clave" "assert 503 == 200"

# 4. el camino viejo deja escapar el error
reemplazar proyecto_maria/pdf_extractor.py \
  "        except LecturaAutomaticaNoDisponible:
            return []" \
  "        except ZeroDivisionError:
            return []"
caso "robust_sin_atrapar" "LecturaAutomaticaNoDisponible"

# 5. el 503 sin el código que distingue la pantalla
reemplazar proyecto_maria/main.py \
  '"code": "lectura_automatica_no_disponible"' \
  '"code": ""'
caso "sin_codigo" "lectura_automatica_no_disponible"

# 6. una clave hecha de espacios cuenta como clave
reemplazar proyecto_maria/pdf_extractor.py \
  "bool((os.environ.get('GEMINI_API_KEY') or '').strip())" \
  "bool(os.environ.get('GEMINI_API_KEY'))"
caso "clave_en_blanco" "FAILED tests/test_maria2_sin_clave_gemini.py::test_endpoint_sin_lector_no_inventa_productos[clave_en_blanco]"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 8 sabotajes dan rojo por la razón esperada"
