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
  if grep -q "passed" <<<"$salida" && ! grep -qE "[0-9]+ failed" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  if grep -qF -- "$espera" <<<"$salida"; then
    echo "ROJO   $nombre: $(grep -E '[0-9]+ failed' <<<"$salida" | tail -1)"
  else
    echo "FALLA  $nombre: rojo, pero sin «$espera»"; FALLAS=$((FALLAS+1)); tail -15 <<<"$salida"
  fi
}

base="$(correr)"
if grep -qE "[0-9]+ failed" <<<"$base" || ! grep -qE "[0-9]+ passed" <<<"$base"; then
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
reemplazar $G '                            f"Item {n_item}, sub-ítem {n}: {nombre} «{str(crudo)[:20]}» tiene que ser "' '                            f"Item {n_item}: {nombre} «{str(crudo)[:20]}» tiene que ser "'
caso sin_numero_de_subitem "${T}test_el_error_llega_a_la_pantalla"

# 4. un grupo con subítems pasa
reemplazar $G "        if any(it.get('subitems') for it in grupo_items):" "        if False:"
caso grupo_con_subitems "${T}test_un_producto_agrupado_no_lleva_subitems"

# --- Revisión adversaria ---
M=proyecto_maria/main.py

# 5. una cantidad con más de dos decimales sale redondeada en el TXT
reemplazar $G "                if abs(cant_sub - round(cant_sub, 2)) > 1e-9:" "                if False:"
caso tres_decimales "${T}test_una_cantidad_con_mas_de_dos_decimales_no_sale_redondeada["

# 6. el error del sufijo de un subítem no dice cuál
reemplazar $M '                    _sufijos.append((f"Item {_n}, sub-ítem {_m}: ", sub["sufijo"].strip()))' '                    _sufijos.append(("", sub["sufijo"].strip()))'
caso sufijo_sin_subitem "${T}test_el_error_del_sufijo_dice_que_subitem["

# 7. sub-ítems con otra forma vuelven a dar 500. El control está dos veces
# en /generate_maria: con uno solo puesto, el pedido sigue dando 400.
reemplazar $M "            if _subs is not None and not (isinstance(_subs, list) and all(isinstance(x, dict) for x in _subs)):" "            if False:"
reemplazar $M "            if not isinstance(_subs, list) or not all(isinstance(_s, dict) for _s in _subs):" "            if False:"
caso forma_500 "${T}test_un_pedido_mal_armado_da_400_y_no_500[subitems0]"

# --- Devolución (puntos 7 y 10) ---
C=proyecto_maria/core/controles_maria.py

# 8. los controles de antes de generar revientan con subitems=5. Se ve en el
# semáforo, que los corre sin control de forma antes.
reemplazar $C "        for m, sub in enumerate(subitems if isinstance(subitems, list) else [], start=1):" "        for m, sub in enumerate(subitems or [], start=1):"
caso controles_500 "${T}test_la_validacion_no_revienta_con_subitems_raros[5]"

# 9. el error del sub-ítem dice la línea del TXT y no el producto de la pantalla
reemplazar $G "            n_item = lugar_en_el_pedido.get(id(item), idx)" "            n_item = idx"
caso numero_de_linea "${T}test_el_error_del_subitem_dice_el_numero_de_la_pantalla["

# 10. un sufijo de sub-ítem que no es un texto vuelve a dar 500
reemplazar $M '                if _s.get("sufijo") is not None and not isinstance(_s.get("sufijo"), str):' "                if False:"
caso sufijo_no_texto "${T}test_un_pedido_mal_armado_da_400_y_no_500[subitems2]"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 10 sabotajes dan rojo por la razón esperada"
