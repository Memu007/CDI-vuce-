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
PRUEBA="tests/test_maria7_rechazos_24_10.py tests/test_maria7_fechas.py"

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
reemplazar $F 'sufijo_sbt = limpiar_sufijo((sbt_sufijo_valor or "").strip())[0]' 'sufijo_sbt = (sbt_sufijo_valor or "").strip()'
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
reemplazar proyecto_maria/main.py "operacion_data.pop('avisos_fecha', []) + " ""
caso "pregunta_perdida" "FAILED $TF::test_la_pregunta_llega_a_la_pantalla"

# 14. a Gemini se le vuelve a pedir la fecha convertida
reemplazar $L 'NO la conviertas ni cambies el orden de día, mes y año.' 'Formato DD/MM/YYYY.' 2
caso "gemini_convierte" "FAILED $TF::test_a_gemini_se_le_pide_la_fecha_tal_cual_en_las_dos_copias"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 14 sabotajes dan rojo por la razón esperada"
