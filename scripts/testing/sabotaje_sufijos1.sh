#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_sufijos1.sh [SHA] [venv]
# Negativos discriminantes de SUFIJOS-1: el producto entero lleva su propio
# sufijo, un grupo exige uno solo, se avisan lo que la posición pide y falta,
# la posición fuera del arancel, la unidad estadística que no es la suya y el
# AI repetido; la estadística de la tabla va al pedido, el script frena si el
# SHA del ZIP no es el del LEEME y la propuesta pide sesión. Cada sabotaje se
# aplica en un worktree descartable, corre los casos y tiene que dar ROJO con
# el motivo esperado. Si un patrón no se encuentra, el script sale con error.
# La pantalla (pantalla_sufijos1.js) necesita la app levantada: va aparte.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-sufijos1"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_sufijos1.py"
[ -d /opt/node22/bin ] && export PATH="/opt/node22/bin:$PATH"
correr() {
  PYTHONPATH=. "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider $PRUEBA 2>&1 || true
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
CASOS=0
caso() {  # caso <nombre> <texto que el rojo tiene que mostrar>
  local nombre="$1" espera="$2" salida
  CASOS=$((CASOS+1))
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

M=proyecto_maria/main.py
G=proyecto_maria/core/maria_generator.py
D=proyecto_maria/static/v2/screens/despachante.js
I=scripts/import_arancel_sufijos.py
T=tests/test_sufijos1.py

# 1. el producto entero usa el de la operación aunque traiga el suyo
reemplazar $G '            sufijo_sbt = (limpiar_sufijo(str(item.get("sufijo") or "").strip(), donde)[0]
                          or sufijo_de_la_operacion())' '            sufijo_sbt = sufijo_de_la_operacion()'
caso "propio_ignorado" "FAILED $T::test_un_producto_entero_lleva_su_propio_sufijo"

# 2. un grupo con sufijos distintos sale igual
reemplazar $G '        if len(sufijos) != 1:' '        if False:'
caso "grupo_sin_control" "FAILED $T::test_un_grupo_con_sufijos_distintos_no_se_genera"

# 3. lo que la posición pide y falta no se avisa
reemplazar $G '        if falta:' '        if False:'
caso "sin_aviso_de_lo_que_falta" "FAILED $T::test_lo_que_la_posicion_pide_y_falta_se_avisa_con_la_fuente"

# 4. la posición fuera del arancel no se marca
reemplazar $G '    for posicion, ns in fuera.items():' '    for posicion, ns in {}.items():'
caso "sin_aviso_de_fuera" "FAILED $T::test_una_posicion_fuera_del_arancel_se_marca_para_el_despachante"

# 5. la unidad estadística que no es la de la posición no se avisa
reemplazar $G '        if sale != consulta["unidad_estadistica"]:' '        if False:'
caso "sin_aviso_de_unidad" "FAILED $T::test_si_la_unidad_estadistica_no_es_la_del_arancel_se_avisa"

# 6. el AI repetido no se avisa
reemplazar $G '        if len(lugares) > 1:' '        if len(lugares) > 99:'
caso "sin_aviso_de_ai_repetido" "FAILED $T::test_el_codigo_ai_repetido_entre_productos_se_avisa"

# 7. la pantalla no manda la estadística de la tabla
reemplazar $D '            (fila && fila.unidad_estadistica) || ' ''
caso "pantalla_sin_estadistica_de_la_tabla" "FAILED $T::test_la_estadistica_de_la_tabla_va_al_pedido_si_nadie_eligio_otra"

# 8. el script arma la tabla con un ZIP que no es el del LEEME
reemplazar $I '    if sha != esperado:' '    if False:'
caso "sha_sin_control" "FAILED $T::test_el_script_frena_si_el_sha_no_es_el_del_leeme"

# 9. la propuesta sin sesión
reemplazar $M 'async def propuesta_de_sufijos(data: dict, user=Depends(get_current_user)):' \
  'async def propuesta_de_sufijos(data: dict, user=None):'
caso "propuesta_sin_sesion" "FAILED $T::test_la_propuesta_pide_sesion"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los $CASOS sabotajes dan rojo por la razón esperada"
