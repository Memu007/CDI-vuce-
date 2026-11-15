#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria7.sh [SHA] [venv]
# Negativos discriminantes de MARIA-7 (lo que el MARIA rechazó el 24/10 y la
# fecha de la factura en su orden): cada sabotaje devuelve el comportamiento
# de antes. Pantalla: scripts/testing/pantalla_maria7.js. Cada sabotaje se
# aplica en un worktree descartable, corre tests/test_maria7_*.py y tiene que
# dar ROJO con el motivo esperado. Si un patrón no se encuentra, el script
# sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria7"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_maria7_rechazos_24_10.py tests/test_maria7_fechas.py tests/test_maria7_revision.py tests/test_maria7_inicio_actividad.py"

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
L=proyecto_maria/pdf_extractor.py
T=tests/test_maria7_rechazos_24_10.py
TF=tests/test_maria7_fechas.py
TR=tests/test_maria7_revision.py
TI=tests/test_maria7_inicio_actividad.py
V2=proyecto_maria/static/v2/screens

# 1. IDSO vuelve a llevar el identificador completo
reemplazar $F 'lines.append(f"IDSO={id_maria}")' 'lines.append(f"IDSO={operation_id}")'
caso "idso_largo" "FAILED $T::test_idso_iddt_e_iartespapu_van_cortos"

# 2. sin CUIT del despachante se genera igual
reemplazar $F '    if not cuit_agr:
        raise ValueError(FALTA_CUIT_DEL_DESPACHANTE)' '    if False:
        raise ValueError(FALTA_CUIT_DEL_DESPACHANTE)'
caso "cddtagr_opcional" "FAILED $T::test_sin_cuit_del_despachante_no_se_genera"

# 3. LDVDREFDOC vuelve a ser «E» + el final del identificador
reemplazar $F 'lines.append(f"LDVDREFDOC={ref_factura}")' 'lines.append("LDVDREFDOC=" + ("E" + id_maria[-6:]).ljust(28))'
caso "ref_inventada" "FAILED $T::test_la_referencia_de_la_factura_es_el_numero_real_con_ancho_fijo"

# 4. «m2» y «m²» dejan de ser 03
reemplazar $F '"m2": "03", "m²": "03", ' ''
caso "m2_sin_alias" "FAILED $T::test_metro_cuadrado_escrito_de_varias_formas"

# 5. en kilos, la cantidad estadística vuelve a ser la cantidad declarada
reemplazar $F 'cantidad_est = kilos_al_centesimo(peso_neto)' 'cantidad_est = Decimal(f"{cantidad:.2f}")'
caso "kilos_es_cantidad" "FAILED $T::test_estadistica_en_kilos_da_el_kilo_neto_al_centesimo"

# 6. el sufijo de la operación sale sin limpiar
reemplazar $F 'return limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")[0]' 'return (sbt_sufijo_valor or "").strip()'
caso "sufijo_sucio" "FAILED $T::test_dentro_del_sufijo_solo_letras_numeros_y_espacios"

# 7. una cuenta del banco vuelve a salir como IDTRIB-PROVEEDOR
reemplazar $F 'idtrib = idtrib_del_proveedor(vendedor_id)' 'idtrib = vendedor_id'
caso "idtrib_cuenta" "FAILED $T::test_una_cuenta_del_banco_no_va_como_idtrib"

# 8. las líneas vuelven a terminar en LF
reemplazar $F 'return "".join(linea + "\r\n" for linea in lines)' 'return "\n".join(lines)'
caso "sin_crlf" "FAILED $T::test_todas_las_lineas_terminan_en_crlf_tambien_la_ultima"

# 9. un salto de línea dentro de un valor pasa
reemplazar $F 'if "\r" in linea or "\n" in linea:' 'if False:'
caso "salto_adentro" "FAILED $T::test_un_salto_de_linea_dentro_de_un_valor_no_genera"

# 10. con el año adelante se lee año/día/mes (lo que salió el 24/10)
reemplazar $L '        anio, mes, dia = (int(g) for g in m.groups())' '        anio, dia, mes = (int(g) for g in m.groups())'
caso "anio_dia_mes" "FAILED $TF::test_con_el_anio_adelante_es_anio_mes_dia_y_llega_asi_al_txt"

# 11. la fecha ambigua se adivina en vez de preguntar
reemplazar $L '        if 1 <= a <= 12 and 1 <= b <= 12 and a != b:' '        if False:'
caso "ambigua_adivinada" "FAILED $TF::test_ambigua_no_se_adivina_se_pregunta"

# 12. con el año al final se lee siempre mes/día
reemplazar $L '        dia, mes = (b, a) if b > 12 else (a, b)' '        dia, mes = (b, a)'
caso "siempre_mes_dia" "FAILED $TF::test_cuando_el_orden_se_puede_saber_no_se_pregunta"

# 13. la pregunta por la fecha no llega a la pantalla
reemplazar proyecto_maria/main.py "avisos_fecha = operacion_data.pop('avisos_fecha', [])" "avisos_fecha = []; operacion_data.pop('avisos_fecha', [])"
caso "pregunta_perdida" "FAILED $TF::test_la_pregunta_llega_a_la_pantalla"

# 14. a Gemini se le vuelve a pedir la fecha convertida
reemplazar $L 'NO la conviertas ni cambies el orden de día, mes y año.' 'Formato DD/MM/YYYY.' 2
caso "gemini_convierte" "FAILED $TF::test_a_gemini_se_le_pide_la_fecha_tal_cual_en_las_dos_copias"

# 15. la revisión vuelve a dar vuelta la fecha que dejó el lector
reemplazar $V2/review.js "        if (m) return dos(m[3]) + '/' + dos(m[2]) + '/' + m[1];
        m = s.match(/^(\d{1,2})[\s\/.\-]+(\d{1,2})[\s\/.\-]+(\d{4})\$/);
        if (m) return dos(m[1]) + '/' + dos(m[2]) + '/' + m[3];
        const digits = s.replace(/\D/g, '');
        if (!/^\d{8}\$/.test(s)) return s;" "        const digits = s.replace(/\D/g, '');
        if (digits.length !== 8) return s;"
caso "revision_da_vuelta" "FAILED $TR::test_la_revision_respeta_el_orden_que_dejo_el_lector"

# 16. un año de dos cifras se adivina
reemplazar $L '        if len(m.group(3)) == 2:
            # «26/08/07»' '        if False:
            # «26/08/07»'
caso "anio_dos_cifras" "FAILED $TR::test_un_anio_de_dos_cifras_no_se_adivina"

# 17. la unidad se busca sin sacarle los puntos
reemplazar $F 'clave = re.sub(r"\.", " ", str(unidad or "").lower())' 'clave = str(unidad or "").lower()'
caso "unidad_con_puntos" "FAILED $TR::test_metro_cuadrado_escrito_de_otras_formas"

# 18. el código chino de crédito social vuelve a tomarse por cuenta
reemplazar $F '    if es_codigo_chino_de_credito_social(compacto):
        return False' '    if False:
        return False'
caso "uscc_es_cuenta" "FAILED $TR::test_una_identificacion_que_parece_cuenta_pero_no_es_sale"

# 19. cualquier cosa con forma de IBAN es cuenta, sin verificar
reemplazar $F 'and _iban_valido(compacto):' ':'
caso "iban_sin_verificar" "FAILED $TR::test_un_iban_valido_sigue_siendo_cuenta_y_uno_con_un_digito_cambiado_no"

# 20. la factura más larga que el campo no se avisa
reemplazar $F 'elif items and numero_factura is not None and len(str(numero_factura).strip()) > LARGO_REF_FACTURA:' 'elif False:'
caso "factura_larga_sin_aviso" "FAILED $TR::test_la_factura_mas_larga_que_el_campo_se_avisa_antes_de_generar"

# 21. (sólo busca el texto) la pantalla deja de mostrar la pregunta por la fecha
reemplazar $V2/upload.js 'if (data && Array.isArray(data.avisos_fecha)) sinLeer.unshift.apply(sinLeer, data.avisos_fecha);' ''
caso "pantalla_sin_fecha" "FAILED $TR::test_la_pantalla_muestra_la_fecha_con_el_titulo_de_la_factura"

# 22. (sólo busca el texto) la unidad del producto entra al HTML sin escapar
reemplazar $V2/despachante.js "'<option value=\"' + CDI.escapeHtml(v) + '\"'" "'<option value=\"' + v + '\"'"
caso "unidad_sin_escapar" "FAILED $TR::test_la_unidad_del_producto_se_escapa_en_la_lista"

# 23. la fecha de inicio de actividad vuelve a salir como se guardó
reemplazar $F '    fecha_ini_act = fecha_inicio_actividad(comprador_fecha_inic_activ)' '    fecha_ini_act = str(comprador_fecha_inic_activ or "").strip()'
caso "inicio_tal_cual" "FAILED $TI::test_sale_dd_mm_aaaa_con_el_ancho_de_siempre"

# 24. una fecha de inicio con la forma pero imposible pasa (2015-02-30)
reemplazar $F '                break  # «2015-02-30»' '                return texto  # «2015-02-30»'
caso "inicio_imposible" "FAILED $TI::test_lo_que_no_es_fecha_no_se_adivina_y_dice_donde_corregirla[2015-02-30]"

# 25. el año vuelve a salir sin completar con ceros («0099» → «99»)
reemplazar $F '                return f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year:04d}"  # %Y no rellena' '                return fecha.strftime("%d/%m/%Y")'
caso "inicio_anio_corto" "FAILED $TI::test_el_anio_sale_con_cuatro_cifras"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 25 sabotajes dan rojo por la razón esperada"
