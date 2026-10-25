#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_sufijos1.sh [SHA] [venv]
# El entorno virtual es /tmp/cdi-dev2/venv (o el de $VENV); si es otro, se
# pasa como 2.º argumento.
# Negativos discriminantes de SUFIJOS-1, uno por motivo: el producto entero
# lleva su propio sufijo, un grupo exige uno solo (el «-» final no cuenta),
# se avisan lo que la posición pide y falta (también un código vacío), la
# posición fuera del arancel y la letra de control equivocada, la unidad
# estadística que no es la suya (con sub-ítems, el aviso propio) y el AI
# repetido; la tabla rota es una tabla que falta y la posición se lee entera;
# la estadística de la tabla va al pedido salvo con sub-ítems, el script
# frena si el SHA del ZIP no es el del LEEME y la propuesta pide sesión, lee
# la NCM primero, sanea y recorta el texto, dice si falta la tabla y la letra
# que corresponde. En la pantalla: la propuesta se suma a la de la operación,
# no pasa al producto que queda en su lugar, no se pide dos veces y la nota
# dice si falta la tabla o es la letra; si junto con el de la operación pasa
# del tope no se pierde lo de la operación, un grupo no tiene celda por
# producto y una NCM de 8 no se dice fuera del arancel; un grupo_id que no se
# puede comparar no rompe los avisos. Cada sabotaje se aplica en un
# worktree descartable, corre los casos y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script sale con error.
# La pantalla (pantalla_sufijos1.js) necesita la app levantada: va aparte,
# y con ella la espera de la propuesta al generar (finalize.js).
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
A=proyecto_maria/core/sufijos_arca.py
T=tests/test_sufijos1.py

# 1. el producto entero usa el de la operación aunque traiga el suyo
reemplazar $G '            sufijo_sbt = (limpiar_sufijo(str(item.get("sufijo") or "").strip(), donde)[0]
                          or sufijo_de_la_operacion())' '            sufijo_sbt = sufijo_de_la_operacion()'
caso "propio_ignorado" "FAILED $T::test_un_producto_entero_lleva_su_propio_sufijo"

# 2. un grupo con sufijos distintos sale igual
reemplazar $G "        if len({s.rstrip('-') for s in sufijos}) != 1:" '        if False:'
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

# 10. el «-» final hace distintos los sufijos de un grupo
reemplazar $G "        if len({s.rstrip('-') for s in sufijos}) != 1:" '        if len(set(sufijos)) != 1:'
caso "guion_final_distingue" "FAILED $T::test_en_un_grupo_el_guion_final_no_hace_distintos_los_sufijos"

# 11. un código con el valor vacío cuenta como cargado
reemplazar $G '                                               if v.strip() or len(c) == 4])' '                                               ])'
caso "codigo_vacio_cargado" "FAILED $T::test_un_codigo_con_el_valor_vacio_es_un_codigo_que_falta"

# 12. la letra de control equivocada sale como «no está»
reemplazar $G '        if letra:' '        if False:'
caso "letra_como_no_esta" "FAILED $T::test_la_letra_de_control_equivocada_se_dice_como_tal"

# 13. con sub-ítems, el aviso de unidad manda a elegir kilos
reemplazar $G '        if pide == UNIDAD_KILOGRAMO and con_subitems:' '        if False:'
caso "subitems_aviso_comun" "FAILED $T::test_con_sub_items_el_aviso_de_unidad_no_manda_a_elegir_kilos"

# 14. la posición se lee con letras de más
reemplazar $A '    partes = re.fullmatch(r"(\d{%d})([A-Z]?)" % LARGO_SIM, texto)' '    partes = re.match(r"(\d{%d})([A-Z]?)" % LARGO_SIM, texto)'
caso "posicion_con_letras_de_mas" "FAILED $T::test_la_posicion_se_lee_con_puntos_y_sin_letras_de_mas"

# 15. una letra de control que no es la suya se consulta igual
reemplazar $A '    if not fila or letra_de_control(posicion, tabla):' '    if not fila:'
caso "consulta_con_otra_letra" "FAILED $T::test_la_posicion_se_lee_con_puntos_y_sin_letras_de_mas"

# 16. una tabla que no es un diccionario se usa igual
reemplazar $A '    return tabla if isinstance(tabla, dict) else {}' '    return tabla'
caso "tabla_que_no_es_dict" "FAILED $T::test_una_tabla_rota_es_una_tabla_que_falta"

# 17. una tabla cortada rompe la carga
reemplazar $A '    except (OSError, EOFError, ValueError):' '    except (OSError, ValueError):'
caso "tabla_cortada" "FAILED $T::test_una_tabla_rota_es_una_tabla_que_falta"

# 18. la propuesta no dice que falta la tabla
reemplazar $M '"sin_tabla": not tabla,' '"sin_tabla": False,'
caso "propuesta_sin_aviso_de_tabla" "FAILED $T::test_sin_la_tabla_la_propuesta_lo_dice"

# 19. la propuesta lee la pieza antes que la NCM
reemplazar $M '_texto_del_pedido(it.get("ncm") or it.get("pieza"), 20)' '_texto_del_pedido(it.get("pieza") or it.get("ncm"), 20)'
caso "pieza_antes_que_ncm" "FAILED $T::test_la_propuesta_lee_la_ncm_antes_que_la_pieza"

# 20. el texto del pedido no se sanea
reemplazar $M '    return str(valor or "").encode("utf-8", "replace").decode("utf-8").strip()[:largo]' '    return str(valor or "").strip()[:largo]'
caso "texto_sin_sanear" "FAILED $T::test_la_propuesta_aguanta_texto_que_no_es_utf8_y_recorta_lo_largo"

# 21. el texto del pedido no se recorta
reemplazar $M '{c: _texto_del_pedido(it.get(c), 200) for c in' '{c: _texto_del_pedido(it.get(c), 10**6) for c in'
caso "texto_sin_tope" "FAILED $T::test_la_propuesta_aguanta_texto_que_no_es_utf8_y_recorta_lo_largo"

# 22. la propuesta no dice la letra que corresponde
reemplazar $M '"letra_de_control": sufijos_arca.letra_de_control(posicion, tabla)})' '"letra_de_control": ""})'
caso "propuesta_sin_letra" "FAILED $T::test_la_propuesta_dice_la_letra_de_control_que_corresponde"

# 23. la pantalla usa la propuesta sola, sin el de la operación
reemplazar $D "        return f && f.sufijo ? combinar(sufijoDeLaOperacion(), String(f.sufijo)) : '';" "        return f && f.sufijo ? String(f.sufijo) : '';"
caso "pantalla_sin_el_de_la_operacion" "FAILED $T::test_la_propuesta_se_suma_a_lo_que_trae_el_de_la_operacion"

# 24. la pantalla pierde los códigos propuestos que la operación no trae
reemplazar $D '        prop.forEach(p => { if (!usados[p.codigo]) partes.push(p.texto); });' ''
caso "pantalla_pierde_codigos" "FAILED $T::test_la_propuesta_se_suma_a_lo_que_trae_el_de_la_operacion"

# 25. la propuesta de una fila pasa al producto que queda en su lugar
reemplazar $D '        if (!pedido || JSON.stringify(pedido) !== JSON.stringify(pedidoDe(it))) return null;' '        if (!pedido) return null;'
caso "propuesta_de_otro_producto" "FAILED $T::test_la_propuesta_de_una_fila_no_pasa_al_producto_que_queda_en_su_lugar"

# 26. la pantalla repite el pedido en curso
reemplazar $D '        if (pendiente && pendiente.clave === cuerpo.clave) return pendiente.promesa;' ''
caso "pedido_repetido" "FAILED $T::test_listo_no_repite_el_pedido_en_curso"

# 27. la nota dice «no está» cuando falta la tabla
reemplazar $D "            if (arancel.sin_tabla) return 'Falta la tabla del arancel de ARCA: cargalo a mano.';" ''
caso "nota_sin_tabla" "FAILED $T::test_sin_la_tabla_la_nota_no_dice_que_la_posicion_no_esta"

# 28. la nota dice «no está» cuando es la letra de control
reemplazar $D '            if (f.letra_de_control) {' '            if (false) {'
caso "nota_sin_letra" "FAILED $T::test_con_la_letra_equivocada_la_nota_no_dice_que_la_posicion_no_esta"

# 29. con sub-ítems, la estadística de la tabla va sola al pedido
reemplazar $D '        const fila = it && Array.isArray(it.subitems) && it.subitems.length ? null : tabla[posicionDe(it)];' '        const fila = tabla[posicionDe(it)];'
caso "subitems_con_estadistica_de_la_tabla" "FAILED $T::test_con_sub_items_la_estadistica_de_la_tabla_no_va_sola"

# 30. junto con el de la operación pasa del tope y se cae lo de la operación
reemplazar $D "        return junto.length <= 120 ? junto : '';" "        return junto.length <= 120 ? junto : prop.map(p => p.texto).join('-') + '-';"
caso "tope_pierde_la_operacion" "FAILED $T::test_si_junto_con_el_de_la_operacion_no_entra_no_se_pierde_lo_de_la_operacion"

# 31. en un grupo, una celda por producto
reemplazar $D '        if (it.grupo_id) {' '        if (false) {'
caso "grupo_con_celda_por_producto" "FAILED $T::test_en_un_grupo_la_celda_no_deja_escribir_un_sufijo_por_producto"

# 32. una NCM de 8 se dice fuera del arancel (en el servidor)
reemplazar $G '        if not sufijos_arca.es_sim(posicion):' '        if False:'
caso "ncm_de_ocho_fuera_en_el_servidor" "FAILED $T::test_una_ncm_de_ocho_no_se_dice_fuera_del_arancel"

# 33. una NCM de 8 se dice fuera del arancel (en la nota)
reemplazar $D "            if (!/^[0-9]{11}[A-Z]?\$/.test(posicionDe(it).replace(/[.\\s]/g, ''))) {" '            if (false) {'
caso "ncm_de_ocho_fuera_en_la_nota" "FAILED $T::test_una_ncm_de_ocho_no_se_dice_fuera_del_arancel"

# 34. un grupo_id que no se puede comparar rompe los avisos
reemplazar $G '                    except TypeError:' '                    except KeyError:'
caso "grupo_que_no_se_compara" "FAILED $T::test_un_grupo_que_no_se_puede_comparar_no_rompe_los_avisos"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los $CASOS sabotajes dan rojo por la razón esperada"
