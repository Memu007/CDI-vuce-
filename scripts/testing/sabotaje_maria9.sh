#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria9.sh [SHA] [venv]
# Negativos discriminantes de MARIA-9: el sufijo de la operación se valida
# sólo si algún producto lo usa, y los avisos anticipan su error. Cada
# sabotaje se aplica en un worktree descartable, corre los casos de MARIA-9 y
# tiene que dar ROJO con el motivo esperado. Si un patrón no se encuentra, el
# script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria9"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_maria9_sufijo_operacion.py tests/test_maria7_devolucion.py"
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

F=proyecto_maria/core/maria_generator.py
M=proyecto_maria/main.py
T=tests/test_maria9_sufijo_operacion.py

# 1. el de la operación se analiza aunque nadie lo use (la regresión)
reemplazar $F '    def sufijo_de_la_operacion():' '    limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")

    def sufijo_de_la_operacion():'
caso "analiza_siempre" "FAILED $T::test_el_de_la_operacion_frena_sólo_si_alguien_lo_usa[renglones_con_propio]"

# 2. los avisos no anticipan el error
reemplazar $F '        if usa_el_sufijo_de_la_operacion(items, iva_adicional):' '        if False:'
caso "sin_aviso" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero]"

# 3. los avisos lo anticipan aunque nadie lo use
reemplazar $F '        if usa_el_sufijo_de_la_operacion(items, iva_adicional):' '        if True:'
caso "aviso_siempre" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[renglones_con_propio]"

# 4. el aviso no tiene el texto del error
reemplazar $F '                limpiar_sufijo(str(sbt_sufijo_valor or "").strip(), " de la operación")' '                limpiar_sufijo(str(sbt_sufijo_valor or "").strip())'
caso "aviso_con_otro_texto" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero]"

# 5. un propio que no se separa cuenta como «sin propio»
reemplazar $F '        except ValueError:
            return False' '        except ValueError:
            return True'
caso "propio_malo_usa_el_general" "FAILED $T::test_un_propio_que_no_se_separa_da_su_error_y_no_el_de_la_operacion"

# 6. un sub-ítem sin propio no cuenta
reemplazar $F 'not isinstance(sub, dict) or sin_propio(sub.get("sufijo")) for sub in subs' 'not isinstance(sub, dict) for sub in subs'
caso "subitem_sin_propio_no_cuenta" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[un_subitem_sin_propio]"

# 7. un ítem que sale entero no cuenta (se ignora si va junto con otros)
reemplazar $F '        elif n not in juntos or sin_propio(item.get("sufijo")):' '        elif sin_propio(item.get("sufijo")):'
caso "item_entero_no_cuenta" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero]"

# 8. un renglón sin propio no cuenta
reemplazar $F '        elif n not in juntos or sin_propio(item.get("sufijo")):' '        elif n not in juntos:'
caso "renglon_sin_propio_no_cuenta" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[un_renglon_sin_propio]"

# 9. la API sigue exigiendo el general aunque cada renglón traiga el suyo
reemplazar $M '        if not sbt_raw and usa_el_sufijo_de_la_operacion(request.items, request.iva_adicional):' '        if not sbt_raw:'
caso "api_exige_el_general" "FAILED $T::test_por_api_los_renglones_con_propio_generan[]"

# 10. la API deja pasar la falta del general cuando alguien lo usa
reemplazar $M '        if not sbt_raw and usa_el_sufijo_de_la_operacion(request.items, request.iva_adicional):' '        if False:'
caso "api_sin_falta" "FAILED $T::test_por_api_sin_ninguno_falta_el_sufijo"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 10 sabotajes dan rojo por la razón esperada"
