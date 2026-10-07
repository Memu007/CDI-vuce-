#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria3.sh [SHA] [venv]
# Negativos discriminantes de MARIA-3 (avisos antes de generar, gastos
# anteriores al FOB, procedencia y fecha). Cada sabotaje se aplica en un
# worktree descartable, corre tests/test_maria3_antes_de_generar.py y tiene
# que dar ROJO con el motivo esperado. Si un patrón no se encuentra, el script
# sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria3"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA=tests/test_maria3_antes_de_generar.py
T="FAILED $PRUEBA::"
G=proyecto_maria/core/maria_generator.py
M=proyecto_maria/main.py
X=proyecto_maria/pdf_extractor.py

correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider "$PRUEBA" 2>&1 || true
}

# reemplazar <archivo> <viejo> <nuevo>: falla si <viejo> no aparece una sola vez
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

# reemplazar_primero <archivo> <viejo> <nuevo>: sólo la primera de dos (las
# dos copias del lector)
reemplazar_primero() {
  "$VENV/bin/python" - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p, encoding="utf-8").read()
n = s.count(viejo)
if n != 2:
    sys.exit(f"PATRON NO ENCONTRADO ({n} veces, se esperaban 2) en {p}: {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo, 1))
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

# 1. los gastos anteriores de la pantalla no llegan al TXT
reemplazar $G "    return anteriores
" "    return None
"
caso gastos_no_llegan "${T}test_gastos_anteriores_de_la_pantalla_llegan_al_txt[EXW]"

# 2. FAS sin gastos anteriores
reemplazar $G 'INCOTERMS_GASTOS_ANTERIORES = {"EXW", "FCA", "FAS"}' 'INCOTERMS_GASTOS_ANTERIORES = {"EXW", "FCA"}'
caso fas_sin_gastos "${T}test_gastos_anteriores_de_la_pantalla_llegan_al_txt[FAS]"

# 3. FAS no es condición válida
reemplazar $G '"EXW", "FCA", "FAS", "CFR"' '"EXW", "FCA", "CFR"'
caso fas_no_valida "${T}test_fas_es_una_condicion_valida"

# 4. los gastos anteriores van con cualquier condición
reemplazar $G '    if str(incoterm or "").strip().upper() not in INCOTERMS_GASTOS_ANTERIORES:
        return None
' ''
caso gastos_con_cualquier_condicion "${T}test_gastos_anteriores_con_otra_condicion_no_van_y_se_avisa[FOB]"

# 5. un 0 se declara
reemplazar $G "round(anteriores, 2) <= 0" "round(anteriores, 2) < 0"
caso cero_se_declara "${T}test_exw_sin_gastos_anteriores_no_inventa_y_avisa[0]"

# 6. no se avisa que los gastos cargados no van
reemplazar $G "    if anteriores > 0 and incoterm_norm not in INCOTERMS_GASTOS_ANTERIORES:" "    if False:"
caso sin_aviso_gastos_que_no_van "${T}test_gastos_anteriores_con_otra_condicion_no_van_y_se_avisa[CIF]"

# 7. vuelve la fecha de hoy
reemplazar $G "    fecha_factura = fecha_de_la_factura(fecha_emision)
    if not fecha_factura:" '    fecha_factura = fecha_de_la_factura(fecha_emision) or datetime.now().strftime("%d/%m/%Y")
    if not fecha_factura:'
caso vuelve_la_fecha_de_hoy "${T}test_sin_fecha_valida_no_se_genera[]"

# 8. la fecha no se valida: «None» llega al TXT
reemplazar $G "    fecha_factura = fecha_de_la_factura(fecha_emision)
    if not fecha_factura:" '    fecha_factura = str(fecha_emision or "").strip()
    if not fecha_factura:'
caso fecha_sin_validar "${T}test_sin_fecha_valida_no_se_genera[None]"

# 9. los avisos previos no piden la fecha
reemplazar $G "    if not fecha_ok:" "    if False:"
caso sin_aviso_de_fecha "${T}test_sin_fecha_los_avisos_previos_la_piden"

# 10. la procedencia de la operación no se aplica
reemplazar $M '    procedencia = str(request.procedencia or "").strip()' '    procedencia = ""'
caso procedencia_no_se_aplica "${T}test_procedencia_por_operacion_llega_a_cada_producto"

# 11. la procedencia de la operación pisa la del producto
reemplazar $M "        if isinstance(it, dict) and not procedencia_de(it)" "        if isinstance(it, dict)"
caso procedencia_pisa_la_del_producto "${T}test_la_procedencia_del_producto_gana_sobre_la_de_la_operacion"

# 12. una procedencia que no se reconoce pasa
reemplazar $M "    if not pais_de_la_tabla(procedencia):
        raise HTTPException(
            status_code=400,
            detail=f\"Procedencia" "    if False:
        raise HTTPException(
            status_code=400,
            detail=f\"Procedencia"
caso procedencia_sin_validar "${T}test_procedencia_no_reconocida_se_rechaza[/generate_maria-Narnia]"

# 13. los avisos previos sin sesión
reemplazar $M "async def avisos_maria_endpoint(
    request: MariaRequest,
    user=Depends(get_current_user),
):" "async def avisos_maria_endpoint(
    request: MariaRequest,
):"
caso avisos_sin_sesion "${T}test_los_avisos_previos_sin_sesion_dan_401"

# 14. los avisos previos no usan los gastos de la pantalla
reemplazar $M "    supuestos = _supuestos_maria(request, items, gastos)
    # Lo que al generar" "    supuestos = _supuestos_maria(request, items, request.gastos_fob)
    # Lo que al generar"
caso avisos_previos_distintos "${T}test_los_avisos_previos_son_los_mismos_que_al_generar"

# 15. «N/A», «FREE», «Unknown»… se marcan como sin leer
reemplazar $X "    return str(raw).strip().rstrip('.').strip().upper() in palabras" "    return False"
caso no_aplica_se_marca "${T}test_no_aplica_no_es_un_dato_sin_leer[na_guion-pymupdf]"

# 16. el lector vuelve a poner «None» en la fecha que no vino (una copia)
reemplazar_primero $X "'fecha_emision': _texto(operacion.get('fecha_emision'))," \
  "'fecha_emision': str(operacion.get('fecha_emision', '')),"
caso fecha_none "${T}test_la_fecha_que_no_vino_queda_vacia[None-"

# 17. el año del IEXT vuelve a salir de hoy
reemplazar $G "    anio_iext = fecha_factura[-2:]" '    anio_iext = datetime.now().strftime("%y")'
caso iext_del_anio_de_hoy "${T}test_el_anio_del_iext_sale_de_la_fecha_valida[01/02/2024-/24]"

# 18. un código numérico que no está en la tabla pasa
reemplazar $G '    return bool(re.fullmatch(r"[0-9]+", texto)) and int(texto) in codigos_tabla_oficial()' \
  '    return bool(re.fullmatch(r"[0-9]+", texto))'
caso procedencia_fuera_de_la_tabla "${T}test_procedencia_no_reconocida_se_rechaza[/generate_maria-99999]"

# 19. un importe NaN pasa (el infinito lo ataja el tope)
reemplazar $G "    if not math.isfinite(importe) or importe < 0 or importe > IMPORTE_MAXIMO:" "    if importe < 0 or importe > IMPORTE_MAXIMO:"
caso gastos_no_finitos "${T}test_gastos_que_no_son_un_importe_dan_400[/generate_maria-gastos_anteriores_fob-EXW-nan]"

# 20. un año antes de 1900 sale en el TXT
reemplazar $G '    return fecha.strftime("%d/%m/%Y") if fecha.year >= 1900 else ""' '    return fecha.strftime("%d/%m/%Y")'
caso anio_0026 "${T}test_sin_fecha_valida_no_se_genera[05/03/0026]"

# 21. la procedencia vuelve a la tabla corta del generador
reemplazar $G '    return frozenset(int(p["code"]) for p in json.loads(m.group(1)))' "    return frozenset(PAISES_INDEC.values())"
caso tabla_corta "${T}test_la_procedencia_acepta_todos_los_paises_de_la_pantalla"

# 22. un año de dos cifras es 19AA
reemplazar $G "            anio += 2000" "            anio += 1900"
caso anio_19aa "${T}test_la_fecha_de_la_factura_sale_en_el_txt[01/01/69-01/01/2069]"

# 23. una fecha futura no se avisa
reemplazar $G "        if fecha > hoy + timedelta(days=1):" "        if False:"
caso sin_aviso_futura "${T}test_fecha_futura_o_vieja_se_avisa[40-futura]"

# 24. cifras que no son 0-9 llegan a int()
reemplazar $G '    return bool(re.fullmatch(r"[0-9]+", texto)) and int(texto) in codigos_tabla_oficial()' \
  '    return texto.isdigit() and int(texto) in codigos_tabla_oficial()'
caso cifras_raras "${T}test_procedencia_no_reconocida_se_rechaza[/generate_maria/avisos-"

# 25. una procedencia de producto en blanco pisa la de la operación
reemplazar $G '        valor = str(item.get(clave) or "").strip()' '        valor = str(item.get(clave) or "")'
caso procedencia_en_blanco "${T}test_procedencia_de_item_en_blanco_no_pisa_la_de_la_operacion"

# 26. el generador no valida gastos_fob
reemplazar $G "        importe_gastos = f\"{centavos(_importe_de_gastos(gastos_fob, 'gastos_fob')):.2f}\"" \
  "        importe_gastos = f\"{float(gastos_fob):.2f}\""
caso generador_sin_validar "${T}test_el_generador_tampoco_acepta_gastos_invalidos[inf]"

# 27. los avisos previos no convierten el error de gastos en 400
reemplazar $M '        importe_valido(request.seguro, "Seguro")
    except ValueError as e:' '        importe_valido(request.seguro, "Seguro")
    except ZeroDivisionError as e:'
caso avisos_gastos_500 "${T}test_gastos_que_no_son_un_importe_dan_400[/generate_maria/avisos-gastos_anteriores_fob-EXW-inf]"

# 28. el flete no se valida (con CIF llega a GTOS-POS-FOB)
reemplazar $G '    flete = centavos(importe_valido(flete or 0, "Flete"))' '    flete = Decimal(repr(float(flete or 0)))'
caso flete_sin_validar "${T}test_flete_o_seguro_que_no_son_un_importe_dan_400[/generate_maria-flete-inf]"

# 29. una procedencia de producto no reconocida pasa
reemplazar $G "        if procedencia and not pais_reconocido(procedencia):" "        if False:"
caso procedencia_de_producto "${T}test_codigo_raro_en_el_producto_da_400_con_mensaje_propio[99999-pais_procedencia]"

# 30. sin productos, los avisos no piden la fecha
reemplazar $G "    if not fecha_ok:" "    if items and not fecha_ok:"
caso fecha_sin_productos "${T}test_sin_productos_los_avisos_tambien_piden_la_fecha"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 30 sabotajes dan rojo por la razón esperada"
