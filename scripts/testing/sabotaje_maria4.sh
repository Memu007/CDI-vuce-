#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria4.sh [SHA] [venv]
# Negativos discriminantes de MARIA-4 (lo que decide el despachante): cada
# sabotaje devuelve un valor fijo de antes. Pantalla: scripts/testing/pantalla_maria4.js. Cada sabotaje se aplica en un worktree descartable, corre
# tests/test_maria4_despachante.py y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria4"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA=tests/test_maria4_despachante.py

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
F=proyecto_maria/core/maria_generator.py
T=tests/test_maria4_despachante.py

# 1. CARTUSO vuelve a ser 3 fijo
reemplazar $F '        lines.append(f"CARTUSO={_estado_item(item, idx, pais_codigo)}")' '        lines.append("CARTUSO=3")'
caso "cartuso_fijo" "FAILED $T::test_por_defecto_estado_2_reventa_modoc_y_sin_banco"

# 2. IVA adicional vuelve a IVAAD1 fijo
reemplazar $F '        lines.append(f"MCPL={iva_item:<40}")' "        lines.append(f\"MCPL={'IVAAD1':<40}\")"
caso "iva_fijo" "FAILED $T::test_por_defecto_estado_2_reventa_modoc_y_sin_banco"

# 3. la empresa vuelve a PSAD06 fija
reemplazar $F '    lines.append(f"MCPL={empresa_digitalizacion:<40}")' "    lines.append(f\"MCPL={'PSAD06':<40}\")"
caso "empresa_fija" "FAILED $T::test_banco_y_lakaut"

# 4. el banco no se emite nunca
reemplazar $F '    if banco_bcra:
        lines.append("[CPL]")' '    if False:
        lines.append("[CPL]")'
caso "sin_banco" "FAILED $T::test_archivo_real_2026_cuatro_campos_y_su_orden"

# 5. con origen argentino se inventa un estado
reemplazar $F '        if pais_codigo == PAIS_ARGENTINA:
            raise ValueError(' '        if False:
            raise ValueError('
caso "argentino_inventado" "FAILED $T::test_origen_argentino_sin_estado_no_se_inventa"

# 6. los listados no devuelven lo elegido (la pantalla no puede proponerlo)
reemplazar proyecto_maria/main.py '    return {k: (maria.get(k) if isinstance(maria.get(k), str) else "")[:12]' '    return {k: ""'
caso "listados_sin_maria" "FAILED $T::test_lo_elegido_se_guarda_con_la_operacion_y_vuelve_en_los_listados"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 6 sabotajes dan rojo por la razón esperada"
