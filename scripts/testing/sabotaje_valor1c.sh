#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_valor1c.sh [SHA] [venv]
# Negativos discriminantes de VALOR-1c: el seguro que calculó el sistema
# con otros importes no se genera sin recalcularlo o dejarlo, el sufijo
# general que nadie usa no se controla (D18), el error de kilos nombra a
# todos si el cero sale del ajuste, sin productos no se genera, y los casos
# que distinguen mutaciones que antes seguían en verde. Cada sabotaje se
# aplica en un worktree descartable, corre los casos y tiene que dar ROJO con
# el motivo esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-valor1c"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_valor1c.py tests/test_valor1.py tests/test_maria9_kilos.py"
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

M=proyecto_maria/main.py
G=proyecto_maria/core/maria_generator.py
J=proyecto_maria/static/v2/screens/finalize.js
T=tests/test_valor1c.py

# --- 1. El seguro calculado con otros importes

# 1. el pedido no dice que el seguro lo calculó el sistema
reemplazar $J '            seguro_calculado: !!op.seguro_calculado,
' ''
caso "pedido_sin_la_marca" "FAILED $T::test_el_pedido_dice_si_el_seguro_lo_calculo_el_sistema"

# 2. el servidor genera igual
reemplazar $M '        if _viejo:
            raise' '        if False:
            raise'
caso "genera_con_seguro_viejo" "FAILED $T::test_un_seguro_calculado_con_otras_cuentas_no_genera"

# 3. los avisos no lo dicen antes
reemplazar $M '    if viejo:
        avisos_valor' '    if False:
        avisos_valor'
caso "avisos_sin_seguro_viejo" "FAILED $T::test_los_avisos_lo_dicen_antes_con_el_mismo_texto"

# 4. frena también al seguro calculado con las cuentas de ahora
reemplazar $M '    if valor["seguro"] == valor["seguro_sugerido"]:
        return None
' ''
caso "frena_al_dia" "FAILED $T::test_un_seguro_calculado_con_las_cuentas_de_ahora_genera"

# 5. frena también al seguro que escribió la persona
reemplazar $M '    if not request.seguro_calculado:
        return None
' ''
caso "frena_sin_la_marca" "FAILED $T::test_un_seguro_que_no_calculo_el_sistema_no_se_toca"

# 6. con las cuentas en error, genera igual
reemplazar $M '    if valor.get("error"):
        return (f"Seguro: lo calculó' '    if valor.get("error"):
        return None
        return (f"Seguro: lo calculó'
caso "error_no_frena" "FAILED $T::test_si_no_se_pueden_hacer_las_cuentas_tampoco_genera"

# 7. si el servidor lo frena, la pantalla no vuelve a las cuentas
reemplazar $J "detail.startsWith('Seguro: lo calculó el sistema')" "detail.startsWith('Seguro calculado: ')"
caso "no_vuelve_a_las_cuentas" "FAILED $T::test_si_el_servidor_lo_frena_se_vuelve_a_las_cuentas"

# 8. vuelve a las cuentas con cualquier error
reemplazar $J "        if (typeof detail === 'string' && detail.startsWith('Seguro: lo calculó el sistema')) {" "        if (typeof detail === 'string') {"
caso "vuelve_con_cualquier_error" "FAILED $T::test_otro_error_se_queda_en_la_pantalla_de_generar[Item"

# 8b. vuelve con cualquier error del seguro, también el mal escrito
reemplazar $J "detail.startsWith('Seguro: lo calculó el sistema')" "detail.startsWith('Seguro: ')"
caso "vuelve_con_el_seguro_mal_escrito" "FAILED $T::test_otro_error_se_queda_en_la_pantalla_de_generar[Seguro"

# 9. «Dejar» se ofrece sólo con las cuentas en error
reemplazar $J '(valor.error || valor.seguro !== valor.seguro_sugerido)' '(valor.error)'
caso "dejar_solo_con_error" "FAILED $T::test_con_otras_cuentas_se_ofrece_dejarlo_como_esta"

# 10. «Dejar» se ofrece aunque el seguro no lo haya calculado el sistema
reemplazar $J '!(valor && op.seguro_calculado &&' '!(valor &&'
caso "dejar_sin_la_marca" "FAILED $T::test_si_no_hay_nada_viejo_no_se_ofrece_dejarlo[no_lo_calculo]"

# 11. con las cuentas en error no se puede dejar
reemplazar $J '(valor.error || valor.seguro !== valor.seguro_sugerido)' '(!valor.error && valor.seguro !== valor.seguro_sugerido)'
caso "error_sin_salida" "FAILED $T::test_con_las_cuentas_en_error_tambien_se_puede_dejar"

# 12. dejarlo no saca la marca
reemplazar $J '        delete op.seguro_calculado;
        cuentasViejas();' '        cuentasViejas();'
caso "dejar_con_la_marca" "FAILED $T::test_dejarlo_saca_la_marca_y_pide_las_cuentas_de_nuevo"

# 13. el botón no está enlazado
reemplazar $J "        if (dejar) dejar.addEventListener('click', dejarSeguro);
" ''
caso "dejar_sin_enlace" "FAILED $T::test_el_boton_de_dejarlo_esta_enlazado"

# --- 2. D18: el sufijo general que nadie usa

# 14. el servidor controla el general aunque nadie lo use
reemplazar $M '[("", sbt_raw)] if sbt_raw and usa_el_general else []' '[("", sbt_raw)] if sbt_raw else []'
caso "d18_servidor" "FAILED $T::test_un_general_que_nadie_usa_no_frena_ni_se_avisa"

# 15. los avisos lo controlan aunque nadie lo use
reemplazar $G '        sufijos = [("", sbt_sufijo_valor)] if usa_el_general else []' '        sufijos = [("", sbt_sufijo_valor)]'
caso "d18_avisos" "FAILED $T::test_un_general_que_nadie_usa_no_frena_ni_se_avisa"

# 16. el general que se usa deja de controlarse
reemplazar $M '        usa_el_general = usa_el_sufijo_de_la_operacion(items, request.iva_adicional)' '        usa_el_general = False'
caso "d18_sin_control" "FAILED $T::test_un_general_que_se_usa_sigue_controlado"

# --- 3. Kilos

# 17. se nombran sólo los que dan cero solos
reemplazar $G '                          if i in solos or not en_cero <= solos]' '                          if i in solos]'
caso "kilos_solo_los_chicos" "FAILED $T::test_si_el_ajuste_deja_en_cero_a_uno_que_no_era_chico_se_nombran_todos"

# 18. el número es el lugar dentro del ítem, no el renglón del pedido
reemplazar $G '                chicos = [lugar_en_el_pedido[id(r)] for i, r in enumerate(renglones)' '                chicos = [i + 1 for i, r in enumerate(renglones)'
caso "kilos_lugar_en_el_item" "FAILED $T::test_el_error_de_kilos_nombra_el_renglon_del_pedido[despues_de_otro]"

# --- 4. Sin productos

# 19. el servidor genera sin productos
reemplazar $M '    if not request.items:
        raise HTTPException(status_code=400, detail=SIN_PRODUCTOS)' '    if False:
        raise HTTPException(status_code=400, detail=SIN_PRODUCTOS)'
caso "genera_sin_productos" "FAILED $T::test_sin_productos_no_se_genera"

# 20. los avisos no lo dicen
reemplazar $M '    if not items:
        avisos_valor = [SIN_PRODUCTOS' '    if False:
        avisos_valor = [SIN_PRODUCTOS'
caso "avisos_sin_productos" "FAILED $T::test_sin_productos_no_se_genera"

# --- 5. Mutaciones que antes seguían en verde

# 21. el seguro sugerido usa el flete sin redondear
reemplazar $G '(fob_base + flete_c)' '(fob_base + Decimal(str(flete or 0)))'
caso "flete_sin_redondear" "FAILED $T::test_el_seguro_sugerido_usa_el_flete_al_centavo"

# 22. la firma de las cuentas no mira los productos
reemplazar $J '        delete resto.operation_id;' '        delete resto.operation_id;
        delete resto.items;'
caso "firma_sin_productos" "FAILED $T::test_un_cambio_en_los_productos_invalida_las_cuentas"

# 23. al entrar a validar quedan las cuentas de antes
reemplazar $J '        pintarValor(null);
' ''
caso "cuentas_de_antes" "FAILED $T::test_al_entrar_a_validar_no_quedan_las_cuentas_de_antes"

# 24. el general se decide sin el IVA adicional de la operación
reemplazar $M '        usa_el_general = usa_el_sufijo_de_la_operacion(items, request.iva_adicional)' '        usa_el_general = usa_el_sufijo_de_la_operacion(items, None)'
caso "general_sin_iva_de_la_operacion" "FAILED $T::test_el_iva_adicional_de_la_operacion_junta_los_renglones"

# 25. los avisos usan los productos sin la procedencia de la operación
reemplazar $M '
    supuestos = _supuestos_maria(request, items, gastos)' '
    supuestos = _supuestos_maria(request, request.items, gastos)'
caso "avisos_sin_procedencia" "FAILED $T::test_los_avisos_usan_la_procedencia_de_la_operacion"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 26 sabotajes dan rojo por la razón esperada"
