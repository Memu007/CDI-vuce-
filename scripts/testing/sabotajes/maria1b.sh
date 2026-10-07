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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_maria1b_controles.py 2>&1)"; codigo=$?
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
  '        if valor is not None and valor < 0:' \
  '        if False:' \
  "FAILED $T::test_flete_o_seguro_negativo_no_deja_generar[flete]"
sabotaje $C "la NCM sin el 0 inicial deja de proponerse" \
  '    if len(digitos) in (10, 7) and _en_el_nomenclador("0" + digitos[:7]):' \
  '    if False:' \
  "FAILED $T::test_ncm_que_perdio_el_0_inicial_propone_el_0"
sabotaje $C "la NCM fuera del nomenclador deja de avisarse" \
  '        if not _en_el_nomenclador(digitos[:8]):' \
  '        if False:' \
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
sabotaje $C "la NCM vuelve a buscarse recorriendo el catálogo" \
  '    return codigo8 in _CODIGOS' \
  '    from proyecto_maria.core.ncm_catalog import find_by_code
    return find_by_code(codigo8) is not None' \
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
  '                    if any(v is not None and str(v).strip() for v in fila):' \
  '                    if True:' \
  "FAILED $T::test_el_excel_deja_en_la_operacion_lo_que_no_se_leyo"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
