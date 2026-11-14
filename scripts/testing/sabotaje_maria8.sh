#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria8.sh [SHA] [venv]
# Negativos discriminantes de MARIA-8 (renglones de la misma posición en un
# ítem con un sub-ítem por renglón): cada sabotaje devuelve el comportamiento
# de antes o rompe una regla de la tarea. Cada uno se aplica en un worktree
# descartable, corre tests/test_maria8_subitems_por_posicion.py y tiene que
# dar ROJO con el motivo esperado. Si un patrón no se encuentra, el script
# sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria8"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_maria8_subitems_por_posicion.py"

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
caso() {  # caso <nombre> <texto que el rojo tiene que mostrar>...
  local nombre="$1" espera="${2:?falta el texto esperado}" salida faltan=""
  salida="$(correr)"
  git checkout -q -- .
  if grep -q "passed" <<<"$salida" && ! grep -q "failed" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  for espera in "${@:2}"; do
    grep -qF -- "$espera" <<<"$salida" || faltan+=" «$espera»"
  done
  if [ -n "$faltan" ]; then
    echo "FALLA  $nombre: rojo, pero sin$faltan"; FALLAS=$((FALLAS+1))
    tail -15 <<<"$salida"; return
  fi
  echo "ROJO   $nombre: $(grep -E '[0-9]+ failed' <<<"$salida" | tail -1)"
}

# 0. sin sabotaje: verde
base="$(correr)"
if grep -q "failed" <<<"$base" || ! grep -qE "[0-9]+ passed" <<<"$base"; then
  echo "FALLA: la prueba no está verde sin sabotaje"; tail -20 <<<"$base"; exit 1
fi
echo "VERDE  sin sabotaje: $(grep -E 'passed' <<<"$base" | tail -1)"
F=proyecto_maria/core/maria_generator.py
T=tests/test_maria8_subitems_por_posicion.py
M=proyecto_maria/main.py

# 1. cada renglón vuelve a ser un ítem
reemplazar $F '    return [ns for ns in juntos.values() if len(ns) > 1]' '    return []'
caso "sin_juntar" "FAILED $T::test_doce_renglones_de_una_posicion_son_un_item_con_doce_subitems"

# 2. el ítem junto vuelve a decir CARTSBITEM=N
reemplazar $F 'lines.append("CARTSBITEM=S" if item.get("subitems") or renglones else "CARTSBITEM=N")' 'lines.append("CARTSBITEM=S" if item.get("subitems") else "CARTSBITEM=N")'
caso "sbitem_n" "FAILED $T::test_doce_renglones_de_una_posicion_son_un_item_con_doce_subitems"

# 3-8. la clave deja de mirar cada cosa que separa los ítems
reemplazar $F '        pais_codigo,
        get_pais_codigo(procedencia_de(item) or pais),' '        None,
        get_pais_codigo(procedencia_de(item) or pais),'
caso "clave_sin_origen" "FAILED $T::test_lo_que_cambia_el_item_lo_separa[origen]"
reemplazar $F '        get_pais_codigo(procedencia_de(item) or pais),
        _estado_item' '        None,
        _estado_item'
caso "clave_sin_procedencia" "FAILED $T::test_lo_que_cambia_el_item_lo_separa[procedencia]"
reemplazar $F '        _estado_item(item, donde, pais_codigo),' '        None,'
caso "clave_sin_estado" "FAILED $T::test_lo_que_cambia_el_item_lo_separa[estado]"
reemplazar $F '        unidad,
        unidad_estadistica_de(item, unidad, donde),' '        None,
        unidad_estadistica_de(item, unidad, donde),'
caso "clave_sin_unidad" "FAILED $T::test_lo_que_cambia_el_item_lo_separa[unidad]"
reemplazar $F '        unidad_estadistica_de(item, unidad, donde),
        iva,' '        None,
        iva,'
caso "clave_sin_unidad_est" "FAILED $T::test_lo_que_cambia_el_item_lo_separa[unidad_estadistica]"
reemplazar $F '        iva,
    )' '        None,
    )'
caso "clave_sin_iva" "FAILED $T::test_lo_que_cambia_el_item_lo_separa[iva]"

# 9. la posición se compara tal como viene escrita
reemplazar $F "        re.sub(r\"[.\\s]\", \"\", str(item.get('ncm') or item.get('pieza') or '')).upper()," "        str(item.get('ncm') or item.get('pieza') or '')," 
caso "posicion_cruda" "FAILED $T::test_la_posicion_se_compara_sin_puntos_ni_espacios"

# 10. el ítem sale donde está su último renglón
reemplazar $F '            if juntos_de[n_renglon][0] == n_renglon:' '            if juntos_de[n_renglon][-1] == n_renglon:'
caso "orden_ultimo" "FAILED $T::test_el_item_va_donde_aparece_su_primer_renglon"

# 11. los grupos y sub-ítems a mano se mezclan con los automáticos
reemplazar $F "        if item.get('grupo_id') is not None or item.get('subitems'):
            continue" "        pass"
caso "mezcla_a_mano" "FAILED $T::test_un_grupo_a_mano_y_los_subitems_a_mano_no_se_mezclan"

# 12. el sobrante del redondeo va al primero y no al más grande
reemplazar $F '    partes[mayor] += total - sum(partes, Decimal(0))' '    partes[0] += total - sum(partes, Decimal(0))'
caso "sobrante_al_primero" "FAILED $T::test_los_kilos_son_los_de_cada_renglon_y_el_sobrante_va_al_mas_pesado"

# 13. las partes no cierran con el total
reemplazar $F '    partes[mayor] += total - sum(partes, Decimal(0))' '    pass'
caso "sin_cerrar" "FAILED $T::test_las_sumas_del_item_cierran_exactas"

# 14. en kilos, la estadística de cada sub-ítem vuelve a ser la cantidad
reemplazar $F '                estadisticas_sub, cantidad_est = al_centesimo_cerrando(kilos_renglones)' '                estadisticas_sub, cantidad_est = al_centesimo_cerrando([_exacto(r.get("cantidad", 1)) for r in renglones])'
caso "kilos_como_cantidad" "FAILED $T::test_los_kilos_son_los_de_cada_renglon_y_el_sobrante_va_al_mas_pesado"

# 15. QARTUNTDCL vuelve a la cantidad sin cerrar con los sub-ítems
reemplazar $F '        lines.append(f"QARTUNTDCL={cantidad_dcl:.2f}")' '        lines.append(f"QARTUNTDCL={cantidad:.2f}")'
caso "cantidad_sin_cerrar" "FAILED $T::test_la_cantidad_tambien_cierra_y_el_sobrante_va_al_mas_grande"

# 16. cada sub-ítem lleva una parte pareja del FOB y no el de su renglón
reemplazar $F '                fob_sub = _fob_de(renglon)' '                fob_sub = centavos(valor_total / len(renglones))'
caso "fob_parejo" "FAILED $T::test_cada_subitem_lleva_lo_de_su_renglon"

# 17. el unitario del sub-ítem es el promedio del ítem
reemplazar $F '                unitario = (float(renglon["valor_unitario"]) if' '                unitario = (valor_unit if'
caso "unitario_promedio" "FAILED $T::test_cada_subitem_lleva_lo_de_su_renglon"

# 18. el renglón pierde su sufijo y lleva el de la operación
reemplazar $F '                sufijo = limpiar_sufijo(str(renglon.get("sufijo") or "").strip(),
                                        f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0] or sufijo_de_la_operacion()' '                sufijo = sufijo_de_la_operacion()'
caso "sufijo_de_la_operacion" "FAILED $T::test_cada_subitem_lleva_lo_de_su_renglon"

# 19. el sufijo del renglón sale sin limpiar
reemplazar $F '                sufijo = limpiar_sufijo(str(renglon.get("sufijo") or "").strip(),
                                        f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0]' '                sufijo = str(renglon.get("sufijo") or "").strip()'
caso "sufijo_sucio" "FAILED $T::test_el_sufijo_del_renglon_se_limpia"

# 20. sin sufijo propio, el renglón, el ítem entero y el sub-ítem a mano dejan
# de heredar el de la operación: una prueba por lugar
reemplazar $F 'f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0] or sufijo_de_la_operacion()' 'f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0]'
reemplazar $F '                          or sufijo_de_la_operacion())' '                          )'
reemplazar $F 'f" del ítem {n_item}, sub-ítem {n}")[0] or sufijo_de_la_operacion()' 'f" del ítem {n_item}, sub-ítem {n}")[0]'
caso "sin_herencia" "FAILED $T::test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion" \
  "FAILED $T::test_un_renglon_solo_sale_como_antes" \
  "FAILED $T::test_un_grupo_a_mano_y_los_subitems_a_mano_no_se_mezclan"

# 21. el error del peso no dice el renglón de la pantalla
reemplazar $F '    kilos = [Decimal(f"{peso_valido(peso_de_la_linea(r), lugar[id(r)]):.3f}") for r in renglones]' '    kilos = [Decimal(f"{peso_valido(peso_de_la_linea(r), 1):.3f}") for r in renglones]'
caso "peso_sin_renglon" "FAILED $T::test_un_renglon_sin_peso_dice_su_numero_en_la_pantalla"

# 22. kilos que quedarían negativos se generan igual
reemplazar $F '            if min(cantidades_sub + estadisticas_sub) <= 0:' '            if False:'
caso "negativos" "FAILED $T::test_kilos_que_al_restar_quedarian_negativos_no_se_generan"

# 23. los avisos no dicen qué renglones van juntos
reemplazar $F '    for ns in juntos:
        cuales' '    for ns in []:
        cuales'
JUNTOS="FAILED $T::test_los_avisos_dicen_que_renglones_van_juntos"
caso "sin_aviso_juntos" "$JUNTOS[seguidos]" "$JUNTOS[doce_renglones]"

# 24. no avisa que todos los sub-ítems llevan el mismo sufijo
reemplazar $F '        if len(de_cada_uno) == 1 and "" not in de_cada_uno:' '        if False:'
MISMO="FAILED $T::test_los_avisos_dicen_si_todos_los_subitems_llevan_el_mismo_sufijo"
caso "sin_aviso_sufijo" "$MISMO[heredan]" "$MISMO[propios_iguales]"

# 25. dos renglones sin posición se juntan
reemplazar $F '        if clave[0]:
            juntos' '        if True:
            juntos'
caso "sin_posicion" "FAILED $T::test_los_renglones_sin_posicion_no_se_juntan"

# 26. un renglón con cantidad 0 o negativa sale como sub-ítem
reemplazar $F "        if _exacto(r.get('cantidad', 1)).quantize(Decimal(\"0.01\"), ROUND_HALF_UP) <= 0:" '        if False:'
caso "cantidad_cero" "FAILED $T::test_un_renglon_sin_cantidad_no_es_un_subitem"

# 27. un sub-ítem que al centésimo da 0,00 se genera
reemplazar $F '            if min(cantidades_sub + estadisticas_sub) <= 0:' '            if min(cantidades_sub + estadisticas_sub) < 0:'
caso "cero_al_centesimo" "FAILED $T::test_kilos_de_un_renglon_que_al_centesimo_dan_cero_no_se_generan"

# 28. el unitario del ítem divide por la cantidad sin redondear
reemplazar $F '            valor_unit = float(valor_total) / float(cantidad_dcl)' '            valor_unit = float(valor_total) / float(cantidad)'
caso "unitario_sin_redondear" "FAILED $T::test_el_unitario_del_item_es_el_fob_sobre_la_cantidad_declarada"

# 29. el error del peso de un ítem después de los juntos dice el número del TXT
reemplazar $F '        peso_neto = peso_valido(peso_kg, lugar_en_el_pedido.get(id(item), idx))' '        peso_neto = peso_valido(peso_kg, idx)'
caso "peso_numero_del_txt" "FAILED $T::test_el_peso_de_un_item_despues_de_los_juntos_dice_su_numero_en_la_pantalla"

# 30. el error del sufijo que falta dice el número del TXT
reemplazar $F '                        f"Item {lugar_en_el_pedido[id(renglon)]}: falta el sufijo de valor (CSBTSVL)."' '                        f"Item {idx}: falta el sufijo de valor (CSBTSVL)."'
caso "sufijo_numero_del_txt" "FAILED $T::test_sin_ningun_sufijo_el_error_dice_el_numero_de_la_pantalla"

# 31. no avisa que se limpió el sufijo de un renglón
LIMPIO="FAILED $T::test_los_avisos_dicen_si_se_limpio_el_sufijo_de_un_renglon"
reemplazar $F '            avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))' '            pass'
caso "sin_aviso_limpieza" "$LIMPIO[seguidos]" "$LIMPIO[salteados]" "$LIMPIO[un_grupo_en_el_medio]" "$LIMPIO[tres_items]"

# 32. el endpoint no valida el sufijo de un renglón
reemplazar $M '                _sufijos.append((f"Item {_n}: ", it["sufijo"].strip()))' '                pass'
caso "endpoint_sin_validar" "FAILED $T::test_el_sufijo_de_un_renglon_se_valida_como_los_otros[igual"

# 33. el endpoint no mira el tipo del sufijo de un renglón
reemplazar $M '            if isinstance(_it, dict) and _it.get("sufijo") is not None and not isinstance(_it.get("sufijo"), str):' '            if False:'
caso "endpoint_sin_tipo" "FAILED $T::test_el_sufijo_de_un_renglon_se_valida_como_los_otros[no_texto"

# 34. el FOB del sub-ítem redondea al par
reemplazar $F '                fob_sub = _fob_de(renglon)' '                fob_sub = valor_de_la_linea(renglon).quantize(Decimal("0.01"))'
caso "fob_al_par" "FAILED $T::test_el_fob_de_medio_centavo_sube_y_el_item_cierra"

# 35. si empatan, el sobrante va al último
reemplazar $F '    mayor = max(range(len(valores)), key=lambda i: (valores[i], -i))' '    mayor = max(range(len(valores)), key=lambda i: (valores[i], i))'
caso "empate_al_ultimo" "FAILED $T::test_si_empatan_el_sobrante_va_al_primero"

# 36. un renglón con total y sin unitario sale con unitario 0
reemplazar $F '                            else float(valor_de_la_linea(renglon)) / float(renglon.get("cantidad", 1) or 1))' '                            else 0.0)'
caso "total_sin_unitario" "FAILED $T::test_un_renglon_con_total_y_sin_unitario"

# 37. declarada en kilos, la estadística sale de la cantidad y no de los kilos
reemplazar $F '            if unidad_est == UNIDAD_KILOGRAMO:
                estadisticas_sub' '            if unidad_est == UNIDAD_KILOGRAMO and unidad_codigo != UNIDAD_KILOGRAMO:
                estadisticas_sub'
caso "declarada_en_kilos" "FAILED $T::test_declarada_en_kilos_la_cantidad_y_los_kilos_son_de_cada_renglon"

# 38. el error del estado dice siempre el renglón 1
reemplazar $F '        clave = clave_de_posicion(item, n + 1, iva_por_defecto)' '        clave = clave_de_posicion(item, 1, iva_por_defecto)'
caso "estado_renglon_fijo" "FAILED $T::test_el_estado_que_no_corresponde_en_el_tercer_renglon_dice_el_tres"

# 39. el aviso del mismo sufijo compara el de la operación sin limpiar
reemplazar $F '                or limpiar_sufijo(str(sbt_sufijo_valor or "").strip())[0]' '                or str(sbt_sufijo_valor or "").strip()'
caso "aviso_operacion_sin_limpiar" "$MISMO[heredan_uno_que_se_limpia]" \
  "$MISMO[uno_trae_el_limpio_y_el_resto_hereda]" "$MISMO[el_de_la_operacion_no_se_separa]"

# 40. los avisos dicen los renglones de corrido, del primero al último del ítem
reemplazar $F '        cuales = _enumerar([n + 1 for n in ns])' '        cuales = _enumerar(list(range(ns[0] + 1, ns[-1] + 2)))'
caso "renglones_de_corrido" "$JUNTOS[salteados]" "$JUNTOS[tres_items]"

# 41. el aviso del mismo sufijo cuenta del primer renglón al último del ítem
reemplazar $F 'los {len(ns)} sub-ítems "' 'los {ns[-1] - ns[0] + 1} sub-ítems "'
caso "cuenta_por_extremos" "$JUNTOS[salteados]" "$JUNTOS[tres_items]"

# 42. los avisos salen sólo para los dos primeros ítems
reemplazar $F '    for ns in juntos:' '    for ns in juntos[:2]:'
caso "tope_dos_items" "$JUNTOS[tres_items]"

# 43. los avisos nombran sólo los cuatro primeros renglones del ítem
reemplazar $F '        cuales = _enumerar([n + 1 for n in ns])' '        cuales = _enumerar([n + 1 for n in ns[:4]])'
caso "renglones_tope_4" "$JUNTOS[doce_renglones]" "$MISMO[cinco_renglones]"

# 44. el aviso de cada renglón dice su puesto en el ítem y no su renglón
reemplazar $F 'f" del renglón {n + 1}"' 'f" del renglón {ns.index(n) + 1}"'
caso "aviso_renglon_por_puesto" "$LIMPIO[salteados]" "$LIMPIO[un_grupo_en_el_medio]" "$LIMPIO[tres_items]"

# 45. el aviso de cada renglón sale sólo para los cuatro primeros del ítem
reemplazar $F '        for n in ns:' '        for n in ns[:4]:'
caso "aviso_renglon_tope_4" "$LIMPIO[salteados]"

# 46. el aviso de cada renglón sale sólo para los dos primeros del ítem
reemplazar $F '        for n in ns:' '        for n in ns[:2]:'
caso "aviso_renglon_tope_2" "$LIMPIO[salteados]"

# 47. el aviso de cada renglón sale sólo para los cinco primeros del ítem
reemplazar $F '        for n in ns:' '        for n in ns[:5]:'
caso "aviso_renglon_tope_5" "$LIMPIO[salteados]"

# 48. el aviso de cada renglón sale sólo para el segundo del ítem
reemplazar $F '        for n in ns:' '        for n in ns[1:2]:'
caso "aviso_renglon_solo_el_segundo" "$LIMPIO[seguidos]" "$LIMPIO[salteados]" "$LIMPIO[un_grupo_en_el_medio]" "$LIMPIO[tres_items]"

# 49. el aviso de cada renglón recorre del primero al último, también los que no son del ítem
reemplazar $F '        for n in ns:' '        for n in range(ns[0], ns[-1] + 1):'
caso "aviso_renglon_de_corrido" "$LIMPIO[salteados]" "$LIMPIO[un_grupo_en_el_medio]" "$LIMPIO[tres_items]"

# 50. el aviso de cada renglón recorre tantos renglones seguidos como tiene el ítem
reemplazar $F '        for n in ns:' '        for n in range(ns[0], ns[0] + len(ns)):'
caso "aviso_renglon_seguidos" "$LIMPIO[salteados]" "$LIMPIO[un_grupo_en_el_medio]" "$LIMPIO[tres_items]"

# 51. el que va solo entre dos que van juntos cuenta como renglón y pierde el aviso de su sufijo
reemplazar $F '    en_renglones = {n for ns in juntos for n in ns}
    if sbt_sufijo_valor is not None:' '    en_renglones = {n for ns in juntos for n in range(ns[0], ns[-1] + 1)}
    if sbt_sufijo_valor is not None:'
caso "en_renglones_de_corrido" "$LIMPIO[salteados]" "$LIMPIO[un_grupo_en_el_medio]"

# 52. en los avisos del arancel, el grupo que queda entre dos que van juntos se nombra como ítem
reemplazar $F '        general = ""
    en_renglones = {n for ns in juntos for n in ns}
' '        general = ""
    en_renglones = {n for ns in juntos for n in range(ns[0], ns[-1] + 1)}
'
caso "arancel_en_renglones_de_corrido" "$LIMPIO[un_grupo_en_el_medio]"

# 53. sólo los del primer ítem cuentan como renglones: los de los otros se avisan dos veces
reemplazar $F '    en_renglones = {n for ns in juntos for n in ns}
    if sbt_sufijo_valor is not None:' '    en_renglones = {n for ns in juntos[:1] for n in ns}
    if sbt_sufijo_valor is not None:'
caso "en_renglones_primer_item" "$LIMPIO[tres_items]"

# 54. el renglón sin sufijo se avisa con el de la operación, que ya tiene su aviso
reemplazar $F 'f" del renglón {n + 1}", items[n].get("sufijo")))' 'f" del renglón {n + 1}", items[n].get("sufijo") or sbt_sufijo_valor))'
caso "aviso_renglon_con_el_de_la_operacion" "$LIMPIO[seguidos]"

# 55. el sufijo de un grupo se avisa una vez por cada renglón suyo
reemplazar $F '                    if nuevo:
                        grupos.add(gid)' '                    if True:
                        grupos.add(gid)'
caso "aviso_de_grupo_por_renglon" "$LIMPIO[un_grupo_en_el_medio]"

# 56. los avisos de la operación y de los que no van juntos salen al revés
reemplazar $F '        for donde, sufijo in sufijos:' '        for donde, sufijo in reversed(sufijos):'
caso "avisos_al_reves" "$LIMPIO[seguidos]" "$LIMPIO[salteados]"

# 57. el sufijo de la operación se avisa aunque ningún renglón lo use
reemplazar $F 'sufijos = [("", sbt_sufijo_valor)] if usa_el_general else []' 'sufijos = [("", sbt_sufijo_valor)]'
caso "aviso_de_la_operacion_sin_uso" "$LIMPIO[un_grupo_en_el_medio]" "$LIMPIO[tres_items]"

# 58. los ítems que van solos se avisan del último al primero
reemplazar $F '                    sufijos.append((f" del ítem {idx}", item["sufijo"]))' '                    sufijos.insert(1 if usa_el_general else 0, (f" del ítem {idx}", item["sufijo"]))'
caso "items_solos_al_reves" "$LIMPIO[seguidos]"

# 59. no se mira si el último renglón del pedido usa el sufijo de la operación
reemplazar $F 'usa_el_general = usa_el_sufijo_de_la_operacion(items)' 'usa_el_general = usa_el_sufijo_de_la_operacion(items[:-1])'
caso "sin_mirar_el_ultimo_renglon" "$LIMPIO[el_ultimo_usa_el_de_la_operacion]"

# 60. el último renglón del pedido, que va solo y trae su sufijo, se queda sin su aviso
reemplazar $F '        for idx, item in enumerate(items or [], start=1):' '        for idx, item in enumerate((items or [])[:-1], start=1):'
caso "sin_avisar_el_ultimo_renglon" "$LIMPIO[seguidos]"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 60 sabotajes dan rojo por la razón esperada"
