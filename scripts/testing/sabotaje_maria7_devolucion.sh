#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria7_devolucion.sh [SHA] [venv]
# Negativos discriminantes de la devolución de MARIA-7 (veredicto del
# 2026-10-24): sufijos que se funden, kilo neto al centésimo (D2 b), palabras
# de cuenta con borde, unidad estadística del grupo por código y aviso de la
# unidad que no se reconoce (D6). Cada sabotaje se aplica en un worktree
# descartable, corre las pruebas de MARIA-7 y tiene que dar ROJO con el
# motivo esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria7-dev"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_maria7_devolucion.py tests/test_maria7_rechazos_24_10.py"
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
TD=tests/test_maria7_devolucion.py

# 1. los sufijos vuelven a fundirse: sin guion entre uno y otro
reemplazar $F '    limpio = "-".join(partes) + final' '    limpio = "".join(partes) + final'
caso "sufijos_fundidos" "FAILED $TD::test_limpiar_sufijo_separa_cada_sufijo"

# 2. lo que no se delimita se deja pasar en vez de dar error
reemplazar $F '        if not uno:
            raise ValueError(' '        if not uno:
            break
            raise ValueError('
caso "sufijo_sin_error" "FAILED $TD::test_limpiar_sufijo_rechaza_lo_que_no_se_delimita"

# 3. el error no dice dónde está el sufijo
reemplazar $F 'limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")' 'limpiar_sufijo((sbt_sufijo_valor or "").strip(), "")'
caso "sufijo_sin_lugar" "FAILED $TD::test_un_sufijo_que_no_se_delimita_no_genera_y_dice_donde"

# 4. el sufijo separado no se avisa
reemplazar $F '    if not cambio:
        return []' '    if True:
        return []'
caso "sufijo_sin_aviso" "FAILED $TD::test_el_aviso_dice_que_se_separo_y_no_rompe_con_un_sufijo_malo"

# 5. D2 (b): el kilo neto vuelve a salir con sus milésimos en kilos
reemplazar $F '        kilo_neto = cantidad_est if unidad_est == UNIDAD_KILOGRAMO else peso_neto' '        kilo_neto = peso_neto'
caso "kilo_neto_milesimos" "FAILED $TD::test_con_la_estadistica_en_kilos_el_kilo_neto_sale_al_centesimo"

# 6. (h) el kilo neto al centésimo redondea al par: 465,125 da 465,12
reemplazar $F '    return Decimal(f"{peso_kg:.3f}").quantize(Decimal("0.01"), ROUND_HALF_UP)' '    return Decimal(f"{peso_kg:.3f}").quantize(Decimal("0.01"), "ROUND_HALF_EVEN")'
caso "redondeo_al_par" "FAILED $TD::test_con_la_estadistica_en_kilos_el_kilo_neto_sale_al_centesimo"

# 7. las palabras de cuenta vuelven a buscarse dentro de otras («ARABIC»)
reemplazar $F 'r"(?<![A-Z])(?:IBAN|SWIFT|BIC\b|ACCOUNT|ACCT|CUENTA|CTA\b|BANK|BANCO|A/C)"' 'r"IBAN|SWIFT|BIC\b|ACCOUNT|ACCT|A/C|CUENTA|CTA\b|BANK|BANCO"'
caso "cuenta_sin_borde" "FAILED $TD::test_los_casos_de_la_reproduccion_salen"

# 7b. el borde vuelve a ser \b: «ICBC_ACCOUNT» o «1_BANK» dejan de ser cuenta
reemplazar $F 'r"(?<![A-Z])(?:IBAN|SWIFT|BIC\b|ACCOUNT|ACCT|CUENTA|CTA\b|BANK|BANCO|A/C)"' 'r"\b(?:IBAN|SWIFT|BIC\b|ACCOUNT|ACCT|CUENTA|CTA\b|BANK|BANCO|A/C)"'
caso "cuenta_borde_de_palabra" "FAILED $TD::test_la_palabra_pegada_a_un_numero_o_guion_bajo_sigue_siendo_cuenta"

# 8. el grupo vuelve a comparar la unidad estadística como se escribió
reemplazar $F "        if len({unidad_estadistica_de(it, get_unidad_codigo(it.get('unidad') or it.get('unidad_medida')
                                                            or it.get('um')), f\"del grupo {gid}\")
                for it in grupo_items}) != 1:" "        if len({str(it.get('unidad_estadistica') or '').strip().upper() for it in grupo_items}) != 1:"
caso "grupo_crudo" "FAILED $TD::test_un_grupo_con_la_misma_unidad_estadistica_escrita_distinto_genera"

# 9. D6: la unidad que no se reconoce sale 07 sin aviso
reemplazar $F '            no_reconocida.append(f"{idx} («{str(unidad)[:20]}»)")' '            pass'
caso "unidad_sin_aviso" "FAILED $TD::test_una_unidad_que_no_se_reconoce_sale_07_y_se_avisa"

# 10. el sufijo separado no se mide: puede pasar de 120 caracteres
reemplazar $F '    if len(limpio) > SUFIJO_MAXIMO:' '    if False:'
caso "sufijo_sin_tope" "FAILED $TD::test_un_sufijo_que_separado_pasa_de_120_caracteres_no_genera"

# 11. con estadística en kilos, un kilo neto de 0,00 al centésimo sale igual
reemplazar $F '            if cantidad_est <= 0:
                # D2 (b)' '            if False:
                # D2 (b)'
caso "kilo_neto_cero" "FAILED $TD::test_con_la_estadistica_en_kilos_un_kilo_neto_que_da_cero_al_centesimo_no_genera"

# 12. el grupo vuelve a comparar la unidad declarada como se escribió
reemplazar $F "        unidades = {get_unidad_codigo(it.get('unidad') or it.get('unidad_medida') or it.get('um')) for it in grupo_items}" "        unidades = {str(it.get('unidad') or it.get('unidad_medida') or it.get('um') or '').strip().upper() for it in grupo_items}"
caso "grupo_unidad_cruda" "FAILED $TD::test_un_grupo_con_la_misma_unidad_declarada_escrita_distinto_genera"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 13 sabotajes dan rojo por la razón esperada"
