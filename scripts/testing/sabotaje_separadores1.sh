#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_separadores1.sh [SHA] [venv]
# Negativos discriminantes de SEPARADORES-1: el flete y el seguro de la
# factura con punto de miles («3.480» es 3480, salvo que la factura use el
# punto como decimal), los prompts los piden como texto, y en la pantalla
# «3.480» se lee entero, «1,500» se pregunta bajo el campo y no deja
# continuar. Cada sabotaje se aplica en un worktree descartable, corre los
# casos (o la pantalla, con su propia API) y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-separadores1"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_separadores1.py tests/test_valor1.py tests/test_maria1c_avisos_lectura.py"
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

P=proyecto_maria/pdf_extractor.py
A=proyecto_maria/static/v2/montos_ar.js
R=proyecto_maria/static/v2/screens/review.js
J=proyecto_maria/static/v2/screens/finalize.js
H=proyecto_maria/templates/dashboard_v2.html
T=tests/test_separadores1.py

# --- La factura

# 1. «3.480» se lee como 3,48 (el defecto del 24/10)
reemplazar $P "    return float(t.replace(miles.group(1), ''))" "    return _numero_factura(raw, decimal)"
caso "factura_miles_como_decimal" "FAILED $T::test_flete_sin_otra_pista"

# 2. se adivina aunque la factura use ese separador como decimal
reemplazar $P '    if decimal == miles.group(1):
        return None' '    if False:
        return None'
caso "contradiccion_adivinada" "FAILED $T::test_contradiccion_queda_sin_leer"

# 3. el aviso de «sin leer» no usa la misma lectura
reemplazar $P '                and _monto_factura(raw, decimal) is None):' '                and _numero_factura(raw, decimal) is None):'
caso "aviso_con_otra_lectura" "FAILED $T::test_contradiccion_queda_sin_leer"

# 4. una de las dos copias del lector sigue con la lectura vieja
reemplazar $P "                            'flete': _monto_factura(operacion.get('flete'), decimal) or 0.0," "                            'flete': _numero_factura(operacion.get('flete'), decimal) or 0.0,"
caso "una_copia_vieja" "FAILED $T::test_el_txt_sale_con_el_flete_entero"

# 5. los prompts vuelven a pedir el flete como número
reemplazar $P '11. flete: Valor del flete/freight, copiado tal como aparece en la factura, como texto ("" si no aparece)' '11. flete: Valor del flete/freight (número, 0 si no aparece)' 2
caso "prompt_pide_numero" "FAILED $T::test_los_dos_prompts_piden_flete_y_seguro_como_texto"

# --- Lo que se escribe a mano (montos_ar.js)

# 6. «3.480» se lee como 3,48
reemplazar $A "                entero = partes.join('');  // 3.480: punto de miles" "                entero = partes[0]; decimales = partes[1];"
caso "pantalla_miles_como_decimal" "FAILED $T::test_la_pantalla_lee_el_monto"

# 7. «1,500» se toma como 1500 sin preguntar
reemplazar $A "                if (sep === ',') {" "                if (false) {"
caso "ambiguo_sin_pregunta" "FAILED $T::test_lo_que_no_se_puede_leer_se_dice"

# 8. escribir() deja tres decimales (que leer() toma como miles)
reemplazar $A "(dec.length === 3 ? dec + '0' : dec)" "dec"
caso "escribe_tres_decimales" "FAILED $T::test_lo_que_se_muestra_se_vuelve_a_leer_igual"

# --- La revisión y el pedido

# 9. el campo muestra el monto con Number() (lo que había)
reemplazar $R '            return r.error ? String(val).trim() : CDI.montos.escribir(r.valor);' '            return String(Number(val));'
caso "revision_muestra_con_number" "FAILED $T::test_la_revision_muestra_el_monto_entero"

# 10. un monto que no se lee se guarda como número (y se pierde la pregunta)
reemplazar $R '        return r.error ? String(raw).trim() : r.valor;' '        return r.error ? Number(String(raw).replace(",", ".")) : r.valor;'
caso "ambiguo_guardado_como_numero" "FAILED $T::test_la_revision_guarda_el_monto_entero"

# 11. el pedido lleva el monto con Number()
reemplazar $J '        const n = CDI.montos.leer(v).valor;
        return n === null ? 0 : n;' '        return Number(v) || 0;'
caso "pedido_con_number" "FAILED $T::test_el_pedido_lleva_los_montos_enteros"

# 12. el ajuste del valor vuelve a Number() (VALOR-1)
reemplazar $J '        return CDI.montos.leer(v).valor;' '        return v === "" ? null : Number(v);'
caso "ajuste_con_number" "FAILED $T::test_un_ajuste_con_punto_de_miles"

# 13. el flete vuelve a ser un campo numérico del navegador
reemplazar $H 'type="text" inputmode="decimal" id="f_flete"' 'type="number" id="f_flete"'
caso "campo_numerico" "FAILED $T::test_los_campos_aceptan_punto_y_coma"

# 14. no hay dónde decir el error del flete
reemplazar $H '<span class="field-error" data-error-for="flete" hidden></span>' ''
caso "sin_lugar_para_el_error" "FAILED $T::test_la_revision_tiene_donde_decir_el_error[flete]"

# --- La pantalla: scripts/testing/pantalla_separadores1.js contra una API
# levantada en este worktree. Sirve los archivos del disco: cada sabotaje se
# ve sin reiniciarla.
PUERTO="$("$VENV/bin/python" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
(env ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./pantalla.db \
     JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
     ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
     "$VENV/bin/python" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" \
     > "$TMP/api.log" 2>&1 < /dev/null & echo $! > "$TMP/api.pid")
trap 'kill "$(cat "$TMP/api.pid")" 2>/dev/null || true; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
"$VENV/bin/python" - "$PUERTO" <<'PY2' || { echo "FALLA: la API no levanta"; tail -20 "$TMP/api.log"; exit 1; }
import sys, time, urllib.request
fin = time.time() + 90
while True:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/health", timeout=2); break
    except Exception:
        if time.time() > fin: sys.exit(1)
        time.sleep(0.5)
PY2
pantalla() { BASE_URL="http://127.0.0.1:$PUERTO" node scripts/testing/pantalla_separadores1.js 2>&1 || true; }
caso_pantalla() {  # caso_pantalla <nombre> <texto que la falla tiene que mostrar>
  local nombre="$1" espera="$2" salida
  salida="$(pantalla)"
  git checkout -q -- .
  if grep -q "PANTALLA SEPARADORES-1 OK" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  if grep -qF -- "$espera" <<<"$salida"; then
    echo "ROJO   $nombre: $(grep FALLA: <<<"$salida" | head -1 | cut -c1-110)"
  else
    echo "FALLA  $nombre: rojo, pero sin «$espera»"; FALLAS=$((FALLAS+1)); tail -5 <<<"$salida"
  fi
}
base="$(pantalla)"
grep -q "PANTALLA SEPARADORES-1 OK" <<<"$base" || { echo "FALLA: la pantalla no está verde sin sabotaje"; tail -5 <<<"$base"; exit 1; }
echo "VERDE  pantalla sin sabotaje"

# 15. la revisión no dice el error del monto
reemplazar $R '        if (r.error) return r.error;' '        if (false) return r.error;'
caso_pantalla "error_no_se_dice" "FALLA: «1,500» no muestra nada bajo el flete"

# 16. lo que se escribe se guarda tal cual, sin leerlo
reemplazar $R '            value = montoDelCampo(value);' '            value = value.trim();'
caso_pantalla "guarda_el_texto" "FALLA: la revisión guardó"

# 17. continuar no mira los errores de los campos
reemplazar $R '        if (!allValid || missing.length > 0) {' '        if (missing.length > 0) {'
caso_pantalla "continuar_sin_mirar" "FALLA: con «1,500» continuar pasó a"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 17 sabotajes dan rojo por la razón esperada"
