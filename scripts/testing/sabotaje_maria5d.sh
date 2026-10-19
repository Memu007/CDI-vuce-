#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria5d.sh [SHA] [venv]
# Negativos discriminantes de MARIA-5d (el bruto de una unidad y las columnas
# por unidad). Cada sabotaje se aplica en un worktree descartable y tiene que
# dar ROJO con el motivo esperado.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria5d"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PRUEBA="tests/test_maria5d.py tests/test_maria5d_unit_kg.py tests/test_maria5_peso_excel.py tests/test_devolucion2_maria5_ncm.py"
T="FAILED tests/test_maria5d.py::"
M=proyecto_maria/main.py

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

# 1. el bruto de una unidad vuelve a ser bruto de la línea (se divide)
reemplazar $M '        return "bruto_unidad" if _bruto_de_una_unidad(normal) else "bruto"' '        return "bruto"'
caso bruto_dividido "${T}test_el_bruto_de_una_unidad_no_se_divide[Peso bruto unitario]"

# 2. el bruto de una unidad le gana a un peso de una unidad
reemplazar $M '"dudosa": 3, "bruto": 4, "bruto_unidad": 4}' '"dudosa": 3, "bruto": 4, "bruto_unidad": 0}'
caso bruto_primero "${T}test_el_bruto_de_una_unidad_va_ultimo[Peso bruto unitario]"

# 3. sin el aviso de bruto
reemplazar $M '    if clase == "bruto_unidad":
        avisos.append(' '    if False:
        avisos.append('
caso sin_aviso "${T}test_el_bruto_de_una_unidad_no_se_divide[Gross weight per unit]"

# 4. «kg/u» y «c/u» vuelven a ser dudosas
reemplazar $M ' or sin_parentesis.endswith("/u")' ''
caso barra_u "${T}test_las_que_dicen_por_unidad_no_son_dudosas[Peso c/u]"

# 5. «Peso U.» vuelve a ser dudosa
reemplazar $M '            or sin_parentesis in ("pesou", "pesobrutou"))' '            )'
caso peso_u "${T}test_las_que_dicen_por_unidad_no_son_dudosas[Peso U.]"

# 6. un bruto de la línea que menciona unidades deja de dividirse
reemplazar $M '    if "total" in normal or "linea" in normal or "unidades" in normal or "units" in normal:
        return False' '    if False:
        return False'
caso bruto_total_unidades "${T}test_un_bruto_de_la_linea_que_menciona_unidades_se_divide[Peso Bruto Total/U]"

# 7. «Peso Bruto Unid.» vuelve a dividirse
reemplazar $M '(unit|unid|/u|brutou)(kgs?)?$' '(unit|/u|brutou)(kgs?)?$'
caso bruto_unid "${T}test_el_bruto_de_una_unidad_no_se_divide[Peso Bruto Unid.]"

# 8. una unidad de medida después de «unit» vuelve a ocultar que es unitario
reemplazar $M '(unit|unid|/u|brutou)(kgs?)?$' '(unit|unid|/u|brutou)$'
caso unit_con_kg "FAILED tests/test_maria5d_unit_kg.py::test_bruto_unitario_con_unidad_de_medida[Peso bruto unit (kg)-automatico]"

# 9. el orden «Unit gross weight» vuelve a dividirse
reemplazar $M 'unitweight|unitgrossweight|' 'unitweight|'
caso unit_gross_weight "FAILED tests/test_maria5d_unit_kg.py::test_bruto_unitario_con_unidad_de_medida[Unit gross weight-mapeo_guardado]"

# 10. convertir todo bruto en unitario tiene que dar rojo por el total
reemplazar $M '        return "bruto_unidad" if _bruto_de_una_unidad(normal) else "bruto"' '        return "bruto_unidad"'
caso todo_bruto_unitario "FAILED tests/test_maria5d_unit_kg.py::test_bruto_total_o_plural_sigue_dividiendose[Peso bruto total unit (kg)]"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 10 sabotajes dan rojo por la razón esperada"
