#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_subitems1.sh [SHA] [venv]
# Negativos discriminantes de SUBITEMS-1 (controles de cada subítem y el grupo
# sin subítems). Cada sabotaje se aplica en un worktree descartable y tiene
# que dar ROJO con el motivo esperado. La pantalla tiene su rojo antes en
# scripts/testing/pantalla_subitems1.js.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-subitems1"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PRUEBA="tests/test_subitems1.py tests/test_maria_subitems.py tests/test_punta_a_punta1.py"
T="FAILED tests/test_subitems1.py::"
G=proyecto_maria/core/maria_generator.py

correr() { "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider $PRUEBA 2>&1 || true; }
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
caso() {
  local nombre="$1" espera="$2" salida
  salida="$(correr)"
  git checkout -q -- .
  if grep -q "passed" <<<"$salida" && ! grep -q "failed" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  if grep -qF -- "$espera" <<<"$salida"; then
    echo "ROJO   $nombre: $(grep -E '[0-9]+ failed' <<<"$salida" | tail -1)"
  else
    echo "FALLA  $nombre: rojo, pero sin «$espera»"; FALLAS=$((FALLAS+1)); tail -15 <<<"$salida"
  fi
}

base="$(correr)"
if grep -q "failed" <<<"$base" || ! grep -qE "[0-9]+ passed" <<<"$base"; then
  echo "FALLA: la prueba no está verde sin sabotaje"; tail -20 <<<"$base"; exit 1
fi
echo "VERDE  sin sabotaje: $(grep -E 'passed' <<<"$base" | tail -1)"

# 1. sin el control de cada subítem (una cantidad negativa compensada pasa)
reemplazar $G "                    if not math.isfinite(numero) or numero <= 0:" "                    if not math.isfinite(numero):"
caso subitem_en_cero "${T}test_el_error_dice_que_subitem_falla[pares0-2-cantidad]"

# 2. el control mira sólo la cantidad
reemplazar $G '                                               ("valor_unitario", "el valor unitario", valor_unit)):' '                                               ):'
caso sin_valor "${T}test_el_error_dice_que_subitem_falla[pares2-1-valor unitario]"

# 3. el error no dice qué subítem
reemplazar $G '                            f"Item {idx}, sub-ítem {n}: {nombre} «{str(crudo)[:20]}» tiene que ser "' '                            f"Item {idx}: {nombre} «{str(crudo)[:20]}» tiene que ser "'
caso sin_numero_de_subitem "${T}test_el_error_llega_a_la_pantalla"

# 4. un grupo con subítems pasa
reemplazar $G "        if any(it.get('subitems') for it in grupo_items):" "        if False:"
caso grupo_con_subitems "${T}test_un_producto_agrupado_no_lleva_subitems"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 4 sabotajes dan rojo por la razón esperada"
