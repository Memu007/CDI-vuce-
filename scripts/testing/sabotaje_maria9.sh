#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria9.sh [SHA] [venv]
# Negativos discriminantes de MARIA-9: el sufijo de la operación se valida
# sólo si algún producto lo usa, los avisos anticipan su error y la pantalla
# lleva cada error de sufijo a su lugar; los bordes del sufijo y de la
# unidad (punto 3) tienen su caso de cada lado y el error de kilos nombra
# sólo los renglones chicos (punto 4). Cada sabotaje se aplica en un
# worktree descartable, corre los casos de MARIA-9 (o la pantalla, con su
# propia API) y tiene que dar ROJO con el motivo esperado. Si un patrón no se
# encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria9"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_maria9_sufijo_operacion.py tests/test_maria7_devolucion.py tests/test_maria9_bordes.py tests/test_maria9_kilos.py"
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
T=tests/test_maria9_sufijo_operacion.py

# 1. el de la operación se analiza aunque nadie lo use (la regresión)
reemplazar $F '    def sufijo_de_la_operacion():' '    limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")

    def sufijo_de_la_operacion():'
caso "analiza_siempre" "FAILED $T::test_el_de_la_operacion_frena_sólo_si_alguien_lo_usa[renglones_con_propio]"

# 2. los avisos no anticipan el error
reemplazar $F '        if usa_el_sufijo_de_la_operacion(items, iva_adicional):' '        if False:'
caso "sin_aviso" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero]"

# 3. los avisos lo anticipan aunque nadie lo use
reemplazar $F '        if usa_el_sufijo_de_la_operacion(items, iva_adicional):' '        if True:'
caso "aviso_siempre" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[renglones_con_propio]"

# 4. el aviso no tiene el texto del error
reemplazar $F '                limpiar_sufijo(str(sbt_sufijo_valor or "").strip(), " de la operación")' '                limpiar_sufijo(str(sbt_sufijo_valor or "").strip())'
caso "aviso_con_otro_texto" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero]"

# 5. un propio que no se separa cuenta como «sin propio»
reemplazar $F '        except ValueError:
            return False' '        except ValueError:
            return True'
caso "propio_malo_usa_el_general" "FAILED $T::test_un_propio_que_no_se_separa_da_su_error_y_no_el_de_la_operacion"

# 6. un sub-ítem sin propio no cuenta
reemplazar $F 'not isinstance(sub, dict) or sin_propio(sub.get("sufijo")) for sub in subs' 'not isinstance(sub, dict) for sub in subs'
caso "subitem_sin_propio_no_cuenta" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[un_subitem_sin_propio]"

# 7. un ítem que sale entero no cuenta (se ignora si va junto con otros)
reemplazar $F '        elif n not in juntos or sin_propio(item.get("sufijo")):' '        elif sin_propio(item.get("sufijo")):'
caso "item_entero_no_cuenta" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero_con_propio]"

# 8. un renglón sin propio no cuenta
reemplazar $F '        elif n not in juntos or sin_propio(item.get("sufijo")):' '        elif n not in juntos:'
caso "renglon_sin_propio_no_cuenta" "FAILED $T::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[un_renglon_sin_propio]"

# 9. la API sigue exigiendo el general aunque cada renglón traiga el suyo
reemplazar $M '        if not sbt_raw and usa_el_sufijo_de_la_operacion(request.items, request.iva_adicional):' '        if not sbt_raw:'
caso "api_exige_el_general" "FAILED $T::test_por_api_los_renglones_con_propio_generan[]"

# 10. la API deja pasar la falta del general cuando alguien lo usa
reemplazar $M '        if not sbt_raw and usa_el_sufijo_de_la_operacion(request.items, request.iva_adicional):' '        if False:'
caso "api_sin_falta" "FAILED $T::test_por_api_sin_ninguno_falta_el_sufijo"

# --- La pantalla (punto 2): scripts/testing/pantalla_maria9.js contra una API
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
pantalla() { BASE_URL="http://127.0.0.1:$PUERTO" node scripts/testing/pantalla_maria9.js 2>&1 || true; }
caso_pantalla() {  # caso_pantalla <nombre> <texto que la falla tiene que mostrar>
  local nombre="$1" espera="$2" salida
  salida="$(pantalla)"
  git checkout -q -- .
  if grep -q "PANTALLA MARIA-9 OK" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  if grep -qF -- "$espera" <<<"$salida"; then
    echo "ROJO   $nombre: $(grep FALLA: <<<"$salida" | head -1 | cut -c1-110)"
  else
    echo "FALLA  $nombre: rojo, pero sin «$espera»"; FALLAS=$((FALLAS+1)); tail -5 <<<"$salida"
  fi
}
base="$(pantalla)"
grep -q "PANTALLA MARIA-9 OK" <<<"$base" || { echo "FALLA: la pantalla no está verde sin sabotaje"; tail -5 <<<"$base"; exit 1; }
echo "VERDE  pantalla sin sabotaje"
J=proyecto_maria/static/v2/screens/finalize.js

# 11. el error del sufijo de un sub-ítem no va al sub-ítem
reemplazar $J '/^(?:Item|Sufijo de valor del ítem) (\d+), sub-ítem (\d+): /' '/^(?:Item) (\d+), sub-ítem (\d+): /'
caso_pantalla "subitem_no_reconocido" "FALLA: el del sub-ítem: no sale bajo el sub-ítem 2 del ítem 1"

# 12. el error del sufijo de la operación no va a su campo
reemplazar $J "detail.startsWith('Sufijo de valor de la operación: ')" "false"
caso_pantalla "operacion_no_reconocida" "FALLA: el de la operación: no sale bajo el campo"

# 13. el número del ítem no se usa (todo cae en el primero)
reemplazar $J 'marcarErrorDeSubitem(parseInt(sub[1], 10) - 1,' 'marcarErrorDeSubitem(0,'
caso_pantalla "item_ignorado" "FALLA: el del ítem 2: no sale bajo el sub-ítem 1 del ítem 2"

# 14. cualquier error de sufijo va al campo de la operación
reemplazar $J "detail.startsWith('Sufijo de valor de la operación: ')" "detail.startsWith('Sufijo de valor')"
caso_pantalla "todo_al_campo" "FALLA: el error de un sub-ítem que no existe se pierde"

# --- Los bordes (punto 3): cada uno se mueve un paso y algún caso da rojo.
B=tests/test_maria9_bordes.py

# 15. el tope del generador deja afuera el 120
reemplazar $F '    if len(limpio) > SUFIJO_MAXIMO:' '    if len(limpio) >= SUFIJO_MAXIMO:'
caso "tope_generador_120_no_pasa" "FAILED $B::test_el_generador_deja_120_caracteres_y_no_121"

# 16. el tope del generador deja pasar el 121
reemplazar $F '    if len(limpio) > SUFIJO_MAXIMO:' '    if len(limpio) > SUFIJO_MAXIMO + 1:'
caso "tope_generador_121_pasa" "FAILED $B::test_el_generador_deja_120_caracteres_y_no_121"

# 17. el tope del endpoint deja afuera el 120
reemplazar $M '            if len(_suf) > 120:' '            if len(_suf) >= 120:'
caso "tope_endpoint_120_no_pasa" "FAILED $B::test_el_endpoint_deja_120_caracteres_y_no_121[120-True]"

# 18. el tope del endpoint deja pasar el 121 (lo frena otro, con otro texto)
reemplazar $M '            if len(_suf) > 120:' '            if len(_suf) > 121:'
caso "tope_endpoint_121_pasa" "FAILED $B::test_el_endpoint_deja_120_caracteres_y_no_121[121-False]"

# 19. un código numérico de tres cifras pasa
reemplazar $F '(?:\(([^()]*)\)|([0-9]{2}))' '(?:\(([^()]*)\)|([0-9]{2,}))'
caso "codigo_de_tres_cifras" "FAILED $B::test_un_codigo_numerico_tiene_dos_cifras_y_no_tres"

# 20. un código de una letra pasa
reemplazar $F '_UN_SUFIJO = re.compile(r"([A-Za-z]{2})' '_UN_SUFIJO = re.compile(r"([A-Za-z]{1,2})'
caso "codigo_de_una_letra" "FAILED $B::test_un_codigo_tiene_dos_letras_y_no_una"

# 21. el punto y coma no separa
reemplazar $F '_ENTRE_SUFIJOS = re.compile(r"[\s,;\-]*")' '_ENTRE_SUFIJOS = re.compile(r"[\s,\-]*")'
caso "punto_y_coma_no_separa" "FAILED $B::test_el_punto_y_coma_separa_un_codigo_del_otro"

# 22. una unidad con su código se avisa como no reconocida
reemplazar $F '        elif not (clave := _clave_de_unidad(unidad)).isdigit() and clave not in UNIDADES_MARIA:' '        elif (clave := _clave_de_unidad(unidad)) not in UNIDADES_MARIA:'
caso "unidad_con_codigo_avisada" "FAILED $B::test_una_unidad_con_su_codigo_sale_igual_y_no_se_avisa[99]"

# 23. una unidad que no se reconoce no se avisa
reemplazar $F '        elif not (clave := _clave_de_unidad(unidad)).isdigit() and clave not in UNIDADES_MARIA:' '        elif False:'
caso "unidad_desconocida_sin_aviso" "FAILED $B::test_una_unidad_que_no_se_reconoce_se_avisa"

# --- El error de kilos (punto 4).
K=tests/test_maria9_kilos.py

# 24. el error nombra a todos los renglones del ítem (el defecto)
reemplazar $F '                      in zip(renglones, cantidades_sub, estadisticas_sub) if min(cant, est) <= 0]' '                      in zip(renglones, cantidades_sub, estadisticas_sub)]'
caso "nombra_a_todos" "FAILED $K::test_el_error_nombra_sólo_los_renglones_chicos[uno_al_final]"

# 25. sólo mira la cantidad: unos kilos en cero ya no frenan
reemplazar $F 'if min(cant, est) <= 0]' 'if cant <= 0]'
caso "kilos_en_cero_pasan" "FAILED $K::test_el_error_nombra_sólo_los_renglones_chicos[uno_al_final] - Failed: DID NOT RAISE"

# 26. siempre en plural
reemplazar $F 'no cierra" if len(chicos) == 1 else' 'no cierra" if False else'
caso "siempre_plural" "FAILED $K::test_el_error_nombra_sólo_los_renglones_chicos[uno_al_principio]"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 26 sabotajes dan rojo por la razón esperada"
