#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria5.sh [SHA] [venv]
# Negativos discriminantes de MARIA-5 (peso total de la línea, cuentas al
# centavo y el vacío escrito). Cada sabotaje se aplica en un worktree
# descartable, corre las pruebas de MARIA-5 y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script
# sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria5"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_maria5_peso.py tests/test_maria5_centavos.py tests/test_maria5_caratula_vacia.py tests/test_maria5_lector_productos.py tests/test_maria5_peso_lector.py tests/test_maria5_peso_excel.py"
T="FAILED tests/test_maria5_"
G=proyecto_maria/core/maria_generator.py
M=proyecto_maria/main.py
X=proyecto_maria/pdf_extractor.py

correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider $PRUEBA 2>&1 || true
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
V=proyecto_maria/core/validations.py

# 1. el peso vuelve a ser el de una unidad
reemplazar $G "    return float(item.get('peso_unitario') or 0) * float(item.get('cantidad', 1) or 0)" "    return float(item.get('peso_unitario') or 0)"
caso peso_unitario "${T}peso.py::test_diez_notebooks_de_dos_kilos_y_medio_declaran_25"

# 2. el total que ya viene se multiplica otra vez
reemplazar $G "    if total not in (None, ''):" "    if False:"
caso multiplica_dos_veces "${T}peso.py::test_el_peso_total_que_ya_viene_no_se_multiplica"

# 3. los grupos suman unitarios
reemplazar $G "        combined['peso_kg'] = sum(peso_de_la_linea(it) for it in grupo_items)" "        combined['peso_kg'] = sum(float(it.get('peso_unitario') or 0) for it in grupo_items)"
caso grupo_suma_unitarios "${T}peso.py::test_un_grupo_suma_el_total_de_cada_linea"

# 4. el reparto vuelve a redondear cada ítem por su cuenta
reemplazar $G "    for i in orden[:total_c - sum(enteras)]:" "    enteras = [round(x) for x in partes]
    for i in []:"
caso reparto_sin_ajuste "${T}centavos.py::test_el_flete_de_diez_suma_diez"

# 5. el centavo que sobra va al primero y no al de mayor peso
reemplazar $G "key=lambda i: (-(partes[i] - enteras[i]), -pesos[i], i)" "key=lambda i: (-(partes[i] - enteras[i]), i)"
caso desempate "${T}centavos.py::test_el_flete_de_diez_suma_diez"

# 6. el redondeo vuelve a ser el del binario
reemplazar $G "        numero = Decimal(repr(crudo))" "        numero = Decimal(crudo)"
caso redondeo_binario "${T}centavos.py::test_el_redondeo_es_mitad_hacia_arriba"

# 7. el FOB de la carátula vuelve a sumarse sin redondear las líneas
reemplazar $G "    lines[linea_fob_total] = f\"MDDTFOB={sum(fobs, Decimal('0.00')):.2f}\"" "    lines[linea_fob_total] = f\"MDDTFOB={sum(float(it.get('valor_total') or float(it.get('cantidad', 1)) * float(it.get('valor_unitario', 0))) for it in items_export):.2f}\""
caso fob_carátula "${T}centavos.py::test_cualquier_reparto_cierra["

# 8. NaN vuelve a llegar al TXT
reemplazar $G "        if not math.isfinite(crudo):" "        if False:"
reemplazar $G "    if not numero.is_finite() or abs(numero) > IMPORTE_MAXIMO:" "    if False:"
caso nan_en_el_txt "${T}centavos.py::test_un_importe_que_no_es_numero_no_llega_al_txt["

# 9. la validación vuelve a redondear el total
reemplazar $V '            "total_valor_usd": float(total_valor_txt),' '            "total_valor_usd": round(total_valor, 2),'
caso validacion_otro_redondeo "${T}centavos.py::test_la_validacion_muestra_el_fob_del_txt"

# 10. el servidor deja pasar el «None» escrito
reemplazar $M '_VACIO_ESCRITO = {"NONE", "NULL", "N/A"}' '_VACIO_ESCRITO = set()'
caso none_en_el_servidor "${T}caratula_vacia.py::test_ningun_vacio_escrito_llega_al_txt[None0]"

# 11. sin número de factura, el TXT sale sin el de la operación
reemplazar $M "        operation_id = request.operation_id.strip() or f\"OP_{datetime.now().strftime('%Y%m%d%H%M%S')}\"" "        operation_id = request.operation_id.strip()"
caso sin_numero_de_operacion "${T}caratula_vacia.py::test_ningun_vacio_escrito_llega_al_txt["

# 12. la copia de PDF directo vuelve a leer el producto a su modo
reemplazar $X "                                descripcion, codigo_parte = _texto_del_producto(item_data)
" "                                descripcion, codigo_parte = str(item_data.get('descripcion') or '')[:100], ''
"
caso pdf_directo_a_su_modo "${T}lector_productos.py::test_la_version_se_suma_a_la_descripcion[pdf_directo]"

# 13. el código de parte sin limpiar
reemplazar $X "    return descripcion[:100], _texto(item_data.get('codigo_parte'))[:20]" "    return descripcion[:100], str(item_data.get('codigo_parte') or '')[:20]"
caso codigo_parte_sin_limpiar "${T}lector_productos.py::test_el_vacio_no_queda_escrito["

# 14. cantidad × unitario vuelve a multiplicarse en binario
reemplazar $G "        valor = _exacto(_exacto(item.get('cantidad', 1)) * _exacto(item.get('valor_unitario', 0)))" "        valor = _exacto(float(item.get('cantidad', 1)) * float(item.get('valor_unitario', 0)))"
caso producto_binario "${T}centavos.py::test_cantidad_por_unitario_en_decimal_exacto[3-3.335-10.01]"

# 15. los sub-ítems se redondean cada uno por su cuenta
reemplazar $G "            fobs_sub = repartir(valor_total, crudos_sub)" "            fobs_sub = [centavos(c) for c in crudos_sub]"
caso subitems_sin_reparto "${T}centavos.py::test_los_subitems_cierran_sin_rechazar_un_pedido_valido["

# 16. sin tope: un importe enorme llega al cálculo
reemplazar $G "    if not numero.is_finite() or abs(numero) > IMPORTE_MAXIMO:" "    if not numero.is_finite():"
caso sin_tope "${T}centavos.py::test_un_importe_imposible_da_error_y_no_500[extra"

# 17. el lector no divide el peso de la línea
reemplazar $X "    if unitario <= 0 and total > 0 and cantidad > 0:
        unitario = total / cantidad" "    if unitario <= 0 and total > 0 and cantidad > 0:
        unitario = total"
caso lector_sin_dividir "${T}peso_lector.py::test_el_peso_que_venga_queda_por_unidad["

# 18. el prompt vuelve a pedir un peso sin decir de qué
reemplazar_primero $X "- peso_total_linea: Peso neto de TODA la línea" "- peso_kg: Peso en kg de TODA la línea"
caso prompt_ambiguo "${T}peso_lector.py::test_el_prompt_pide_las_dos_cosas_en_las_dos_copias"

# 19. el Excel no divide el peso total
reemplazar $M '    df["peso_unitario"] = (peso / cantidad).where(cantidad > 0)' '    df["peso_unitario"] = peso'
caso excel_sin_dividir "${T}peso_excel.py::test_el_peso_de_la_linea_se_divide[Peso total-25-2.5]"

# 20. el bruto entra en silencio
reemplazar $M '    if clase == "bruto":
        avisos.append(' '    if False:
        avisos.append('
caso bruto_en_silencio "${T}peso_excel.py::test_el_bruto_solo_se_usa_dividido_y_con_aviso"

# 21. el bruto vuelve a ganarle al neto
reemplazar $M '        "pesokg", "pesototal", "pesoneto",' '        "pesokg", "pesobruto", "pesototal", "pesoneto",'
caso bruto_antes_que_neto "${T}peso_excel.py::test_con_neto_y_bruto_se_usa_el_neto"

# 22. la columna de peso vuelve a mirarse sólo por nombre exacto
reemplazar $M '    if any(p in normal for p in ("total", "neto", "net", "linea")):' '    if normal in ("pesototal", "pesoneto"):'
caso nombre_exacto "${T}peso_excel.py::test_un_mapeo_guardado_con_otro_nombre_tambien_divide"

# 23. un peso que no es número queda en 0 en silencio
reemplazar $M '    if sin_numero:' '    if False:'
caso texto_en_silencio "${T}peso_excel.py::test_un_peso_que_no_es_numero_se_avisa"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 23 sabotajes dan rojo por la razón esperada"
