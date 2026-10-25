#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_valor1.sh [SHA] [venv]
# Negativos discriminantes de VALOR-1: la cuenta del FOB casillero, el seguro
# sugerido, el FOB de la factura igual al MDDTFOB, los ajustes que no van al
# TXT, los avisos y la tarjeta de la pantalla. Cada sabotaje se aplica en un
# worktree descartable, corre tests/test_valor1.py y tiene que dar ROJO con el
# motivo esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-valor1"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_valor1.py"
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
JS=proyecto_maria/static/v2/screens/finalize.js
RV=proyecto_maria/static/v2/screens/review.js
T=tests/test_valor1.py

# 1. el ajuste a deducir se suma
reemplazar $F '    fob_casillero = fob_factura + incluir - deducir' '    fob_casillero = fob_factura + incluir + deducir'
caso "deducir_suma" "FAILED $T::test_fob_casillero_es_el_de_la_factura_mas_lo_que_se_incluye_menos_lo_que_se_deduce"

# 2. el seguro sugerido sin el flete
reemplazar $F 'TASA_SEGURO_SUGERIDO * (fob_base + flete_c)' 'TASA_SEGURO_SUGERIDO * fob_base'
caso "seguro_sin_flete" "FAILED $T::test_sin_ajustes_el_casillero_es_el_fob_de_la_factura"

# 3. el seguro sugerido redondeado al par (10,005 → 10,00)
reemplazar $F 'float(centavos(TASA_SEGURO_SUGERIDO * (fob_base + flete_c)))' 'float((TASA_SEGURO_SUGERIDO * (fob_base + flete_c)).quantize(Decimal("0.01"), "ROUND_HALF_EVEN"))'
caso "seguro_redondeo_float" "FAILED $T::test_el_seguro_sugerido_redondea_la_mitad_hacia_arriba"

# 4. un FOB casillero negativo pasa
reemplazar $F '    if fob_casillero < 0:' '    if fob_casillero < -10**12:'
caso "casillero_negativo" "FAILED $T::test_deducir_mas_que_el_fob_no_es_un_casillero"

# 5. el FOB de la factura suma renglón por renglón, sin juntar el grupo
reemplazar $F '    fob_factura = fob_total_del_txt(items)' '    fob_factura = sum((_fob_de(it) for it in items), Decimal("0.00"))'
caso "fob_sin_grupos" "FAILED $T::test_el_fob_de_la_factura_es_el_mddtfob_del_txt[grupo]"

# 6. el ajuste a incluir no se valida
reemplazar $F 'centavos(importe_valido(ajustes_incluir, "Ajustes a incluir") or 0)' 'centavos(Decimal(str(ajustes_incluir or 0)))'
caso "incluir_sin_validar" "FAILED $T::test_un_ajuste_invalido_dice_cual"

# 7. el aviso del casillero sale sin ajustes
reemplazar $M '    if not (valor["ajustes_incluir"] or valor["ajustes_deducir"]):
        return valor, []
' ''
caso "aviso_sin_ajustes" "FAILED $T::test_sin_ajustes_no_hay_aviso_del_casillero"

# 8. un ajuste inválido frena los avisos
reemplazar $M '        return {"error": str(e)}, []' '        raise'
caso "ajuste_frena_avisos" "FAILED $T::test_un_ajuste_invalido_va_en_la_tarjeta_y_no_tapa_los_otros_avisos"

# 9. los ajustes cambian el TXT
reemplazar $M '            comprador_fecha_inic_activ=request.comprador_fecha_inic_activ,
            flete=request.flete,
            seguro=request.seguro,' '            comprador_fecha_inic_activ=request.comprador_fecha_inic_activ,
            flete=request.flete,
            seguro=request.seguro + (request.ajustes_deducir or 0),'
caso "ajustes_al_txt" "FAILED $T::test_el_txt_es_el_mismo_con_y_sin_ajustes"

# 10. el descuento de la planilla se pone solo
reemplazar $JS '        // Ya usado como ajuste, no se vuelve a ofrecer.' '        if (descuento > 0) op.ajustes_deducir = String(descuento);
        // Ya usado como ajuste, no se vuelve a ofrecer.'
caso "descuento_solo" "FAILED $T::test_el_descuento_de_la_planilla_se_ofrece_y_no_se_pone_solo"

# 11. se ofrece calcular el seguro aunque la factura lo traiga
reemplazar $JS '(!(valor.seguro > 0) || calculado)' 'true'
caso "pisa_seguro_factura" "FAILED $T::test_con_seguro_de_la_factura_no_se_ofrece_calcularlo"

# 12. el seguro calculado no se marca
reemplazar $JS '        op.seguro_calculado = true;
' ''
caso "seguro_sin_marca" "FAILED $T::test_el_boton_del_seguro_pone_el_sugerido_y_pide_las_cuentas_de_nuevo"

# 13. un ajuste mal escrito viaja como texto (daría 422 al generar)
reemplazar $JS '        return isFinite(n) ? n : null;' '        return isFinite(n) ? n : v;'
caso "ajuste_texto_al_pedido" "FAILED $T::test_el_pedido_manda_los_ajustes_y_nunca_algo_que_frene_el_txt"

# 14. el pedido no manda el ajuste a deducir
reemplazar $JS '            ajustes_deducir: ajusteDelPedido(op.ajustes_deducir),
' ''
caso "pedido_sin_deducir" "FAILED $T::test_el_pedido_manda_los_ajustes_y_nunca_algo_que_frene_el_txt"

# 15. un seguro escrito a mano sigue marcado como calculado
reemplazar $RV "        if (el.name === 'seguro') delete op.seguro_calculado;
" ''
caso "seguro_a_mano_marcado" "FAILED $T::test_un_seguro_escrito_a_mano_deja_de_ser_el_calculado"

# 16. la base del seguro no sale de BASE_SEGURO_SUGERIDO
reemplazar $F '}[BASE_SEGURO_SUGERIDO]
    return {' '}["fob_casillero"]
    return {'
caso "base_fija_en_la_cuenta" "FAILED $T::test_la_base_del_seguro_se_cambia_en_un_solo_lugar"

# 17. el botón nombra una base fija en vez de la del servidor
reemplazar $JS "const base = (ok && valor.base_seguro) || 'FOB';" "const base = 'FOB casillero';"
caso "base_fija_en_el_boton" "FAILED $T::test_el_boton_nombra_la_base_que_dice_el_servidor"

# 18. el aviso vuelve a decir que el casillero se carga a mano
reemplazar $M 'f"va al TXT en una próxima versión."' 'f"lo cargás vos en el MARIA."'
caso "aviso_viejo" "FAILED $T::test_los_avisos_traen_las_cuentas_y_dicen_que_el_casillero_va_al_txt_mas_adelante"

# 19. un producto que no es un renglón se saltea sin decir nada
reemplazar $M '    if malos:
        return' '    if False:
        return'
caso "producto_mal_formado_callado" "FAILED $T::test_un_producto_mal_formado_va_en_la_tarjeta_y_no_tira_los_avisos[texto]"

# 20. un número que no entra en un float tira los avisos
reemplazar $M '    except ArithmeticError:' '    except ZeroDivisionError:'
caso "fuera_de_rango_500" "FAILED $T::test_un_producto_mal_formado_va_en_la_tarjeta_y_no_tira_los_avisos[enorme]"

# 21. el descuento pisa otro ajuste a deducir ya escrito
reemplazar $JS '        if (!(descuento > 0) || otroDeducir(op, descuento)) return;' '        if (!(descuento > 0)) return;'
caso "descuento_pisa_deducir" "FAILED $T::test_usar_el_descuento_no_pisa_otro_ajuste_a_deducir"

# 22. con otro ajuste a deducir, el botón del descuento se sigue ofreciendo
reemplazar $JS '        if (usar) usar.hidden = otro;' '        if (usar) usar.hidden = false;'
caso "boton_descuento_con_otro" "FAILED $T::test_usar_el_descuento_no_pisa_otro_ajuste_a_deducir"

# 23. si fallan los avisos la tarjeta queda vacía y sin error
reemplazar $JS '            valor = { error: SIN_CUENTAS };
' '' 2
caso "falla_avisos_callada" "FAILED $T::test_si_fallan_los_avisos_la_tarjeta_lo_dice"

# 24. un ajuste mal escrito se repinta vacío
reemplazar $JS '!ajusteMalEscrito(op.ajustes_incluir)) {' 'true) {'
caso "mal_escrito_se_borra" "FAILED $T::test_un_numero_que_el_campo_no_entiende_queda_marcado_y_a_la_vista"

# 25. al cambiar un ajuste, el botón sigue con las cuentas viejas
reemplazar $JS '                cuentasViejas();
' ''
caso "boton_con_cuentas_viejas" "FAILED $T::test_mientras_se_rehacen_las_cuentas_no_se_calcula_con_las_viejas"

# 26. el seguro sugerido de otra operación se usa
reemplazar $JS '        if (!cuentasCon || cuentasCon !== ahora) {' '        if (false) {'
caso "seguro_de_otra_operacion" "FAILED $T::test_el_seguro_sugerido_de_otra_operacion_no_se_usa"

# 27. se pisa lo que la persona está escribiendo
reemplazar $JS 'document.activeElement !== deducir' 'true'
caso "pisa_lo_que_se_escribe" "FAILED $T::test_lo_que_se_esta_escribiendo_no_se_pisa"

# 28. una respuesta vieja de los avisos pisa la nueva
reemplazar $JS '        if (seq !== avisosSeq) return;   // llegó uno más nuevo
' ''
caso "respuesta_vieja" "FAILED $T::test_una_respuesta_vieja_no_pisa_las_cuentas_nuevas"

# 29. un número que el campo no entiende no se marca
reemplazar $JS "input.validity && input.validity.badInput ? 'mal escrito' : input.value" 'input.value'
caso "bad_input_sin_marca" "FAILED $T::test_un_numero_que_el_campo_no_entiende_queda_marcado_y_a_la_vista"

# 30. con error en las cuentas, el botón pone un seguro igual
reemplazar $JS '        if (!ultimoValor || ultimoValor.error) return;' '        if (!ultimoValor) return;'
caso "seguro_con_error" "FAILED $T::test_con_error_en_las_cuentas_no_se_calcula_el_seguro"

# 31. las cuentas no guardan con qué pedido se hicieron y el botón no hace nada
reemplazar $JS '        cuentasCon = firma || null;' '        cuentasCon = null;'
caso "sin_operacion_no_calcula" "FAILED $T::test_sin_operacion_todavia_el_boton_igual_pone_el_seguro"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 31 sabotajes dan rojo por la razón esperada"
