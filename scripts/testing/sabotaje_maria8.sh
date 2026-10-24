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
T=tests/test_maria8_subitems_por_posicion.py

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
reemplazar $F '                sufijo = limpiar_sufijo(str(renglon.get("sufijo") or "").strip())[0] or sufijo_sbt' '                sufijo = sufijo_sbt'
caso "sufijo_de_la_operacion" "FAILED $T::test_cada_subitem_lleva_lo_de_su_renglon"

# 19. el sufijo del renglón sale sin limpiar
reemplazar $F '                sufijo = limpiar_sufijo(str(renglon.get("sufijo") or "").strip())[0] or sufijo_sbt' '                sufijo = str(renglon.get("sufijo") or "").strip() or sufijo_sbt'
caso "sufijo_sucio" "FAILED $T::test_el_sufijo_del_renglon_se_limpia"

# 20. vuelve a pedir el sufijo de la operación aunque cada renglón tenga el suyo
reemplazar $F '        if not subitems and not renglones and not sufijo_sbt:' '        if not subitems and not sufijo_sbt:'
caso "pide_sufijo_operacion" "FAILED $T::test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion"

# 21. el error del peso no dice el renglón de la pantalla
reemplazar $F '    kilos = [Decimal(f"{peso_valido(peso_de_la_linea(r), lugar[id(r)]):.3f}") for r in renglones]' '    kilos = [Decimal(f"{peso_valido(peso_de_la_linea(r), 1):.3f}") for r in renglones]'
caso "peso_sin_renglon" "FAILED $T::test_un_renglon_sin_peso_dice_su_numero_en_la_pantalla"

# 22. kilos que quedarían negativos se generan igual
reemplazar $F '            if min(cantidades_sub + estadisticas_sub) < 0:' '            if False:'
caso "negativos" "FAILED $T::test_kilos_que_al_restar_quedarian_negativos_no_se_generan"

# 23. los avisos no dicen qué renglones van juntos
reemplazar $F '    for ns in juntos:
        cuales' '    for ns in []:
        cuales'
caso "sin_aviso_juntos" "FAILED $T::test_los_avisos_dicen_que_renglones_van_juntos"

# 24. no avisa que todos los sub-ítems llevan el mismo sufijo
reemplazar $F '        if len(de_cada_uno) == 1 and "" not in de_cada_uno:' '        if False:'
caso "sin_aviso_sufijo" "FAILED $T::test_los_avisos_dicen_si_todos_los_subitems_llevan_el_mismo_sufijo"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 24 sabotajes dan rojo por la razón esperada"
