#!/usr/bin/env bash
# Negativos de MARIA-1b: cada sabotaje deshace un arreglo y las pruebas
# tienen que ponerse rojas por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/maria1b.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_maria1b_controles.py tests/test_maria1b_devolucion.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
C=proyecto_maria/core/controles_maria.py
T=tests/test_maria1b_controles.py
D=tests/test_maria1b_devolucion.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $T $D >/dev/null 2>&1; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; exit 1
fi
sabotaje $M "/generate_maria deja de usar los controles" \
  '        if kit_errors or errores_1b:' \
  '        if kit_errors:' \
  "FAILED $T::test_moneda_que_impide_el_txt"
sabotaje $M "los textos vuelven a entrar sin limpiar" \
  '            setattr(request, _campo, limpiar_texto(getattr(request, _campo)))' \
  '            pass' \
  "FAILED $T::test_un_texto_no_mete_lineas_ni_igual_en_el_txt[comprador_nombre]"
sabotaje $C "el «=» vuelve a pasar" \
  '    limpio = re.sub(_SALTOS_Y_CONTROLES + "+", " ", valor).replace("=", "-")' \
  '    limpio = re.sub(_SALTOS_Y_CONTROLES + "+", " ", valor)' \
  "FAILED $T::test_un_texto_no_mete_lineas_ni_igual_en_el_txt"
sabotaje $C "USD vuelve a pasar como moneda" \
  '    elif moneda == "USD":' \
  '    elif moneda == "XXX-NUNCA":' \
  "FAILED $T::test_moneda_que_impide_el_txt[USD-"
sabotaje $C "el incoterm deja de controlarse" \
  '    elif incoterm not in INCOTERMS_ACEPTADOS:' \
  '    elif False:' \
  "FAILED $T::test_incoterm_que_impide_el_txt[FOX-"
sabotaje $C "el dígito verificador del CUIT deja de mirarse" \
  '    return esperado == int(norm[10])' \
  '    return True' \
  "FAILED $T::test_cuit_del_importador[30999999991-"
sabotaje $C "el flete negativo vuelve a pasar" \
  '            importe_valido(valor, nombre)' \
  '            pass' \
  "FAILED $T::test_flete_o_seguro_negativo_no_deja_generar[flete]"
sabotaje $C "la NCM sin el 0 inicial deja de proponerse" \
  '    if len(digitos) in (10, 7) and _en_el_nomenclador("0" + digitos[:7]):' \
  '    if False:' \
  "FAILED $T::test_ncm_que_perdio_el_0_inicial_propone_el_0"
sabotaje $C "la NCM fuera del nomenclador deja de avisarse" \
  '        if aviso:
            advertencias.append(f"Item {n}: {aviso}")' \
  '        if False:
            advertencias.append(f"Item {n}: {aviso}")' \
  "FAILED $T::test_ncm_que_no_esta_en_el_nomenclador_avisa_pero_deja_generar"
sabotaje $C "el CUIT vacío vuelve a dejar generar" \
  '        errores.append("Falta el CUIT del importador.")' \
  '        pass' \
  "FAILED $T::test_cuit_del_importador_vacio_no_deja_generar"
sabotaje $C "los saltos de línea Unicode vuelven a pasar" \
  '_SALTOS_Y_CONTROLES = r"[\x00-\x1f\x7f-\x9f\u2028\u2029]"' \
  '_SALTOS_Y_CONTROLES = r"[\x00-\x1f\x7f]"' \
  "FAILED $T::test_un_texto_no_mete_lineas_ni_igual_en_el_txt"
sabotaje $M "el «=» vuelve a pasar en el sufijo SBT" \
  '            if "=" in _suf:' \
  '            if False:' \
  "FAILED $T::test_sufijo_sbt_con_igual_o_control_no_deja_generar[AA(X)-AB(MOD=1)-]"
sabotaje $M "el servidor vuelve a inventar DOL y FOB" \
  '    moneda: str = ""
    incoterm: str = ""' \
  '    moneda: str = "DOL"
    incoterm: str = "FOB"' \
  "FAILED $T::test_sin_moneda_ni_incoterm_el_servidor_no_inventa_dol_ni_fob"
sabotaje $M "el TXT vuelve a llevar el valor sin normalizar" \
  '        request.incoterm = (request.incoterm or "").strip().upper()' \
  '        pass' \
  "FAILED $T::test_el_txt_lleva_lo_que_se_controla_normalizado"
# Con CATALOGO-NCM-1 el aviso sale de ncm_catalog.aviso_de_ncm: el sabotaje
# le hace recorrer el catálogo entero por cada producto.
sabotaje proyecto_maria/core/ncm_catalog.py "la NCM vuelve a buscarse recorriendo el catálogo" \
  '    catalogo = _codigos_vigentes()' \
  '    catalogo = [item.codigo for item in load_catalog()]' \
  "FAILED $T::test_los_controles_con_miles_de_items_no_traban"
sabotaje $M "la validación previa deja de mirar la cabecera" \
  '        if isinstance(operacion, dict):' \
  '        if False:' \
  "FAILED $T::test_la_validacion_previa_devuelve_los_mismos_errores"
sabotaje $M "vuelve la cantidad 1 al guardar la operación" \
  '                    cantidad=float(item.get("cantidad") or 0),' \
  '                    cantidad=float(item.get("cantidad") or 1),' \
  "FAILED $T::test_guardar_la_operacion_no_inventa_cantidad_peso_ni_origen"
sabotaje $M "vuelve el peso 0,5 al guardar la operación" \
  '                    peso_unitario=float(item.get("peso_unitario") or 0),' \
  '                    peso_unitario=float(item.get("peso_unitario") or 0.5),' \
  "FAILED $T::test_guardar_la_operacion_no_inventa_cantidad_peso_ni_origen"
sabotaje $M "las filas sin leer dejan de quedar en la operación" \
  '            operacion["filas_excel_sin_leer"] = descartes[:50]' \
  '            pass' \
  "FAILED $T::test_el_excel_deja_en_la_operacion_lo_que_no_se_leyo"
sabotaje $M "las otras hojas dejan de avisarse" \
  '            operacion["hojas_excel_sin_leer"] = otras_hojas[:20]' \
  '            pass' \
  "FAILED $T::test_el_excel_deja_en_la_operacion_lo_que_no_se_leyo"
sabotaje $M "una hoja vacía se avisa como hoja con datos" \
  '                return True
    return False' \
  '                return True
    return True' \
  "FAILED $T::test_el_excel_deja_en_la_operacion_lo_que_no_se_leyo"
# Devolución de MARIA-1b
sabotaje $C "NaN e inf vuelven a pasar en la cantidad" \
  '        if _fuera_de_rango(cantidad):' \
  '        if False:' \
  "FAILED $D::test_nan_o_inf_en_un_producto_no_dejan_generar[cantidad-"
sabotaje $C "los subítems dejan de controlarse" \
  '        for m, sub in enumerate(subitems if isinstance(subitems, list) else [], start=1):' \
  '        for m, sub in enumerate([], start=1):' \
  "FAILED $D::test_nan_o_inf_en_un_subitem_no_dejan_generar"
sabotaje $C "los montos que desbordan al multiplicar vuelven a pasar" \
  '    return len(numeros) > 1 and (not math.isfinite(producto) or abs(producto) > IMPORTE_MAXIMO)' \
  '    return False' \
  "FAILED $D::test_montos_finitos_que_desbordan_no_dejan_generar[item2-"
sabotaje $M "la validación previa vuelve a dar 500 con NaN o montos que desbordan" \
  '        return _sin_no_finitos({' \
  '        return ({' \
  "FAILED $D::test_la_validacion_previa_con_nan_o_inf_no_da_500"
sabotaje $M "la exportación vuelve a escribir NaN" \
  '        if _montos:' \
  '        if False:' \
  "FAILED $D::test_la_exportacion_no_escribe_nan_ni_inf"
sabotaje $M "una fórmula sin valor guardado deja de ser un dato" \
  '            if formula is not None and (formula.text or "").strip():' \
  '            if False:' \
  "FAILED $D::test_una_hoja_con_formulas_sin_valor_guardado_se_avisa"
sabotaje $M "una hoja de gráfico vuelve a contar como hoja" \
  '        destinos[r.get("Id")] = (destino, "chartsheet" in (r.get("Type") or ""))' \
  '        destinos[r.get("Id")] = (destino, False)' \
  "FAILED $D::test_una_hoja_de_grafico_primero_no_corre_las_hojas"
sabotaje $C "el CUIT vuelve a aceptar dígitos de otros alfabetos" \
  'if not re.fullmatch(r"[0-9]{11}", norm):' \
  'if not re.fullmatch(r"\d{11}", norm):' \
  "FAILED $D::test_cuit_con_digitos_que_no_son_0_a_9_no_deja_generar"
sabotaje $C "las monedas habituales vuelven a pasar sin aviso" \
  '    elif moneda not in MONEDAS_CONFIRMADAS:' \
  '    elif moneda not in MONEDAS_CONFIRMADAS | {"EUR", "BRL", "CNY"}:' \
  "FAILED $D::test_toda_moneda_que_no_es_dol_avisa_y_deja_generar[EUR]"
sabotaje $M "la exportación vuelve a escribir los textos sin limpiar" \
  '                setattr(request, _campo, limpiar_texto(_valor))' \
  '                pass' \
  "FAILED $D::test_la_exportacion_tampoco_mete_lineas_ni_igual[exportador_nombre]"
sabotaje $M "mirar las otras hojas vuelve a no tener presupuesto" \
  '    def read(self, n: int = -1) -> bytes:
        import time as _time' \
  '    def read(self, n: int = -1) -> bytes:
        return self._archivo.read(n)
        import time as _time' \
  "FAILED $D::test_mirar_las_otras_hojas_de_un_libro_armado_corta_solo"
sabotaje $M "un texto compartido en blanco cuenta como dato" \
  '                    lleno = lista[i]' \
  '                    lleno = True' \
  "FAILED $D::test_mirar_las_otras_hojas_de_un_libro_armado_corta_solo"
sabotaje $M "el semáforo deja de decir que no se revisaron todas las hojas" \
  '            operacion["hojas_excel_sin_revisar"] = True' \
  '            pass' \
  "FAILED $D::test_un_libro_armado_dice_que_no_se_revisaron_todas_las_hojas"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
