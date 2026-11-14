#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_valor1b.sh [SHA] [venv]
# Negativos discriminantes de VALOR-1b: el botón del seguro sólo usa cuentas
# hechas con el pedido de ahora, el seguro calculado deja de avisarse como no
# leído, la base es el FOB de la factura (D13) y un ajuste o un renglón que no
# es número va en la tarjeta con un mensaje claro. Cada sabotaje se aplica en un
# worktree descartable, corre tests/test_valor1.py y tiene que dar ROJO con el
# motivo esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-valor1b"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_valor1.py"
[ -d /opt/node22/bin ] && export PATH="/opt/node22/bin:$PATH"
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

F=proyecto_maria/core/maria_generator.py
M=proyecto_maria/main.py
JS=proyecto_maria/static/v2/screens/finalize.js
RV=proyecto_maria/static/v2/screens/review.js
T=tests/test_valor1.py


# 1. usar el descuento deja el botón con las cuentas de antes
reemplazar $JS '        if (input) input.value = op.ajustes_deducir;
        cuentasViejas();' '        if (input) input.value = op.ajustes_deducir;'
caso "descuento_cuentas_viejas" "FAILED $T::test_despues_de_usar_el_descuento_no_se_calcula_con_las_cuentas_de_antes"

# 2. el botón no compara el pedido de ahora con el de las cuentas
reemplazar $JS '        if (!cuentasCon || cuentasCon !== ahora) {' '        if (!cuentasCon) {'
caso "seguro_a_mano_pisado" "FAILED $T::test_un_seguro_puesto_despues_de_las_cuentas_no_se_pisa_con_el_sugerido_viejo"

# 3. el mismo sabotaje, por el flete
reemplazar $JS '        if (!cuentasCon || cuentasCon !== ahora) {' '        if (!cuentasCon) {'
caso "flete_cambiado" "FAILED $T::test_un_flete_cambiado_despues_de_las_cuentas_no_se_calcula_con_el_viejo"

# 4. el mismo sabotaje, por una cuenta vieja que llega tarde
reemplazar $JS '        if (!cuentasCon || cuentasCon !== ahora) {' '        if (!cuentasCon) {'
caso "cuenta_vieja_tarde" "FAILED $T::test_una_cuenta_vieja_que_llega_tarde_no_pisa_el_seguro_recien_calculado"

# 5. las cuentas que vuelven no guardan con qué pedido se hicieron
reemplazar $JS '        pintarValor(valor, firma);' '        pintarValor(valor);'
caso "avisos_sin_firma" "FAILED $T::test_las_cuentas_quedan_atadas_al_pedido_que_se_mando"

# 5b. la firma se toma cuando vuelven las cuentas, no cuando se mandó el pedido
reemplazar $JS '        pintarValor(valor, firma);' '        pintarValor(valor, firmaDelPedido(buildMariaRequest()));'
caso "firma_tardia" "FAILED $T::test_un_pedido_que_cambia_mientras_viajan_las_cuentas_no_se_les_pega"

# 6. sin firma se calcula igual
reemplazar $JS '        if (!cuentasCon || cuentasCon !== ahora) {' '        if (cuentasCon && cuentasCon !== ahora) {'
caso "sin_firma_calcula" "FAILED $T::test_sin_firma_no_se_calcula"

# 7. la firma lleva el número de operación (sin factura cambia con la hora)
reemplazar $JS '        delete resto.operation_id;
' ''
caso "firma_con_hora" "FAILED $T::test_la_firma_no_cambia_por_el_numero_de_operacion_y_si_por_lo_demas"

# 8. después de calcular, el botón sigue con las cuentas de antes
reemplazar $JS '            op.campos_completados = Array.from(completados);
        }
        cuentasViejas();
' '            op.campos_completados = Array.from(completados);
        }
'
caso "calculado_cuentas_viejas" "FAILED $T::test_el_boton_del_seguro_pone_el_sugerido_y_pide_las_cuentas_de_nuevo"

# 9. el seguro calculado se sigue avisando como no leído
reemplazar $JS "            completados.add('seguro');
" ''
caso "sigue_sin_leer" "FAILED $T::test_el_seguro_calculado_deja_de_avisarse_como_no_leido"

# 10. el semáforo no se entera del seguro calculado
reemplazar $JS '        if (CDI.semaforo && CDI.semaforo.refresh) CDI.semaforo.refresh();
    }
' '    }
'
caso "semaforo_sin_refrescar" "FAILED $T::test_el_seguro_calculado_deja_de_avisarse_como_no_leido"

# 11. el botón no avisa que la factura puede traer un seguro sin leer
reemplazar $JS "                mostrar && seguroSinLeer(op) ?" "                false ?"
caso "sin_aviso_de_no_leido" "FAILED $T::test_si_la_factura_puede_traer_seguro_se_avisa_antes_de_calcularlo"

# 12. el aviso de no leído sigue aunque ya se completó
reemplazar $JS "            !(Array.isArray(op.campos_completados) && op.campos_completados.includes('seguro'));" '            true;'
caso "aviso_no_leido_completo" "FAILED $T::test_si_la_factura_puede_traer_seguro_se_avisa_antes_de_calcularlo"

# 13. la base vuelve al FOB casillero (D13)
reemplazar $F 'BASE_SEGURO_SUGERIDO = "fob_factura"' 'BASE_SEGURO_SUGERIDO = "fob_casillero"'
caso "base_casillero" "FAILED $T::test_el_seguro_va_sobre_el_fob_de_la_factura"

# 14. un ajuste que no es número vuelve a dar 422 y se pierden los avisos
reemplazar $M '    ajustes_deducir: Any = None' '    ajustes_deducir: float | None = None'
caso "ajuste_422" "FAILED $T::test_un_ajuste_que_no_es_numero_va_en_la_tarjeta_con_todos_los_avisos[texto]"

# 15. el mismo, en /generate_maria
reemplazar $M '    ajustes_incluir: Any = None' '    ajustes_incluir: float | None = None'
caso "ajuste_422_txt" "FAILED $T::test_un_ajuste_que_no_es_numero_no_frena_el_txt"

# 16. verdadero se toma como 1
reemplazar $F '    if isinstance(valor, bool) or not' '    if not'
caso "verdadero_es_uno" "FAILED $T::test_un_ajuste_que_no_es_numero_va_en_la_tarjeta_con_todos_los_avisos[verdadero]"

# 16b. un objeto en un ajuste se muestra como lo escribe Python
reemplazar $F '        raise ValueError(f"{nombre}: no es un importe.")' '        return importe_valido(valor, nombre)'
caso "ajuste_repr" "FAILED $T::test_un_ajuste_que_no_es_numero_va_en_la_tarjeta_con_todos_los_avisos[objeto]"

# 16c. una lista en un renglón se muestra como la escribe Python
reemplazar $F '            escrito = f" «{valor[:20]}»" if isinstance(valor, str) else ""' '            escrito = f" «{str(valor)[:20]}»"'
caso "renglon_repr" "FAILED $T::test_un_renglon_con_texto_en_vez_de_numero_se_nombra_sin_texto_de_python[lista]"

# 17. un renglón con texto muestra el texto de Python
reemplazar $F '    _numeros_de_los_renglones(items)
' ''
caso "renglon_texto_python" "FAILED $T::test_un_renglon_con_texto_en_vez_de_numero_se_nombra_sin_texto_de_python[cantidad]"

# 17b. verdadero o falso en un renglón se toma como 1 o 0
reemplazar $F '            if not isinstance(valor, bool):' '            if True:'
caso "renglon_verdadero" "FAILED $T::test_un_renglon_con_texto_en_vez_de_numero_se_nombra_sin_texto_de_python[verdadero]"

# 18. un error de tipo que se escapa muestra el texto de Python
reemplazar $M '        return {"error": "Hay un dato que no es un número: no se pueden hacer las cuentas."}, []' '        raise'
caso "tipo_crudo" "FAILED $T::test_un_error_de_tipo_que_se_escape_no_muestra_el_texto_de_python"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 22 sabotajes dan rojo por la razón esperada"
