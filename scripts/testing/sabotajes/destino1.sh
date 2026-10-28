#!/usr/bin/env bash
# Negativos de DESTINO-1: cada sabotaje deshace una parte del destino de la
# mercadería (GANANCIASOP3 + IVAADICIONAL1 de a pares) y tests/test_destino1.py
# o las pruebas del golden (o, los de la pantalla,
# scripts/testing/pantalla_destino1.js) tienen que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8854] scripts/testing/sabotajes/destino1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8854}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
export BASE_URL="http://127.0.0.1:$PUERTO"
FALLAS=0

# Las de DESTINO-1 y las que comparan el golden (D28 a: el golden no se toca
# y esas pruebas esperan USOPAR en su GANANCIASOP3).
PRUEBAS="tests/test_destino1.py tests/test_generar_maria_txt.py tests/test_maria1b_controles.py
         tests/test_punta_a_punta1.py tests/test_maria4_despachante.py tests/test_maria_supuestos.py"
pytest_d1() {
  rm -f test.db
  # shellcheck disable=SC2086
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider $PRUEBAS 2>&1
}

levantar() {
  rm -f local.db
  ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./local.db \
  JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
  ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
    "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && return 0; sleep 1; done
  echo "BASE  | la API no levantó"; tail -20 "$TMPD/api.log"; exit 1
}
bajar() { [ -n "$API" ] && kill "$API" 2>/dev/null && wait "$API" 2>/dev/null; API=""; }
pantalla() { node scripts/testing/pantalla_destino1.js 2>&1; }

aplicar() {
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

# juzgar <nombre> <salida> <código> <lo que el rojo tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3"; shift 3
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^(FAILED|FALLA)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_d1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

# sabotaje_pantalla: igual, pero con la API levantada sobre el sabotaje (la
# plantilla puede quedar en caché) y la prueba del navegador.
sabotaje_pantalla() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  levantar
  local salida codigo
  salida="$(pantalla)"; codigo=$?
  bajar
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

G=proyecto_maria/core/maria_generator.py
T=tests/test_destino1.py
TABLA='GANANCIAS_POR_IVA_ADICIONAL = {"NO_VALIDA": "COMERC", "IVAAD2": "BDEUSO", "IVAAD1": "USOPAR"}'
SALE='        lines.append(f"MCPL={GANANCIAS_POR_IVA_ADICIONAL[iva_item]:<40}")'

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_d1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi
levantar
if ! pantalla >"$TMPD/base_pantalla.log"; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje"; grep FALLA "$TMPD/base_pantalla.log"; exit 1
fi
bajar

# --- Cada par
sabotaje $G "bien de uso de la empresa sale COMERC" \
  "$TABLA" "${TABLA/\"IVAAD2\": \"BDEUSO\"/\"IVAAD2\": \"COMERC\"}" \
  "FAILED $T::test_cada_destino_por_operacion_sale_con_su_par[IVAAD2-BDEUSO]" \
  "FAILED $T::test_cada_destino_por_item_sale_con_su_par[IVAAD2-BDEUSO]" \
  "pares fuera de la tabla del despachante: {'0001': ('COMERC', 'IVAAD2')}"
sabotaje $G "bien de uso de una persona sale COMERC (lo de antes)" \
  "$TABLA" "${TABLA/\"IVAAD1\": \"USOPAR\"/\"IVAAD1\": \"COMERC\"}" \
  "FAILED $T::test_cada_destino_por_operacion_sale_con_su_par[IVAAD1-USOPAR]" \
  "pares fuera de la tabla del despachante: {'0001': ('COMERC', 'IVAAD1')}" \
  "FAILED tests/test_generar_maria_txt.py::test_golden_reproduce_estructura_real"
sabotaje $G "comercialización sale USOPAR" \
  "$TABLA" "${TABLA/\"NO_VALIDA\": \"COMERC\"/\"NO_VALIDA\": \"USOPAR\"}" \
  "FAILED $T::test_cada_destino_por_operacion_sale_con_su_par[NO_VALIDA-COMERC]" \
  "FAILED $T::test_por_defecto_comercializacion_y_se_avisa" \
  "pares fuera de la tabla del despachante: {'0001': ('USOPAR', 'NO_VALIDA')}"
sabotaje $G "GANANCIASOP3 vuelve a ser COMERC fijo" \
  "$SALE" "        lines.append(f\"MCPL={'COMERC':<40}\")" \
  "FAILED $T::test_cada_destino_por_operacion_sale_con_su_par[IVAAD2-BDEUSO]" \
  "FAILED $T::test_cada_destino_por_operacion_sale_con_su_par[IVAAD1-USOPAR]" \
  "FAILED $T::test_cada_item_cambia_el_de_la_operacion"

# --- El defecto y el aviso
sabotaje $G "por defecto, bien de uso de una persona" \
  'IVA_ADICIONAL_POR_DEFECTO = "NO_VALIDA"' 'IVA_ADICIONAL_POR_DEFECTO = "IVAAD1"' \
  "FAILED $T::test_por_defecto_comercializacion_y_se_avisa" "('USOPAR', 'IVAAD1')"
sabotaje $G "el aviso del defecto no dice el par" \
  '"Destino de la mercadería: se declaró comercialización o reventa (COMERC + "' \
  '"Destino de la mercadería: se declaró reventa ("' \
  "FAILED $T::test_por_defecto_comercializacion_y_se_avisa" "comercialización o reventa (comerc + no_valida) por defecto"

# --- El cambio por ítem
sabotaje $G "GANANCIASOP3 sale con el de la operación y no con el del ítem" \
  "$SALE" "${SALE/\[iva_item\]/[iva_adicional]}" \
  "FAILED $T::test_cada_destino_por_item_sale_con_su_par[IVAAD2-BDEUSO]" \
  "FAILED $T::test_cada_item_cambia_el_de_la_operacion" "pares fuera de la tabla del despachante"
sabotaje $G "el ítem ignora su destino" \
  $'            _iva_adicional(item.get("iva_adicional"), f"Ítem {idx}")\n            if item.get("iva_adicional") else iva_adicional\n' \
  $'            iva_adicional\n' \
  "FAILED $T::test_cada_destino_por_item_sale_con_su_par[IVAAD1-USOPAR]" \
  "FAILED $T::test_cada_item_cambia_el_de_la_operacion" \
  "FAILED $T::test_un_destino_por_item_que_no_esta_en_la_tabla_no_genera[BDEUSO]"
sabotaje $G "un grupo con destinos distintos se genera" \
  $'        if len(ivas) != 1:\n' $'        if False:\n' \
  "FAILED $T::test_un_grupo_con_destinos_distintos_no_se_genera" "DID NOT RAISE"

# --- Lo que no está en la tabla
sabotaje $G "se acepta cualquier destino" \
  '    if codigo not in IVA_ADICIONAL:' '    if False:' \
  "FAILED $T::test_un_destino_por_operacion_que_no_esta_en_la_tabla_no_genera[COMERC]" \
  "FAILED $T::test_un_destino_por_item_que_no_esta_en_la_tabla_no_genera[IVAAD3]" \
  "FAILED $T::test_por_la_ruta_un_destino_que_no_esta_en_la_tabla_da_400_sin_archivo"
sabotaje $G "se aceptan los códigos de GANANCIASOP3 como entrada" \
  '    if codigo not in IVA_ADICIONAL:' \
  '    codigo = {g: i for i, g in GANANCIAS_POR_IVA_ADICIONAL.items()}.get(codigo, codigo)'$'\n''    if codigo not in IVA_ADICIONAL:' \
  "FAILED $T::test_un_destino_por_operacion_que_no_esta_en_la_tabla_no_genera[BDEUSO]" \
  "FAILED $T::test_un_destino_por_item_que_no_esta_en_la_tabla_no_genera[USOPAR]" \
  "DID NOT RAISE"

# --- La pantalla
J=proyecto_maria/static/v2/screens/despachante.js
sabotaje_pantalla $J "la pantalla no ofrece bien de uso de la empresa" \
  $'        [\'IVAAD2\', \'Bien de uso de la empresa\'],\n' '' \
  "FALLA: opciones de la operación"
sabotaje_pantalla $J "la pantalla muestra IVAAD1 con el nombre de antes" \
  "['IVAAD1', 'Bien de uso de una persona']" "['IVAAD1', 'Uso particular']" \
  "FALLA: opciones de la operación"
sabotaje_pantalla proyecto_maria/templates/dashboard_v2.html "la etiqueta sigue diciendo IVA adicional" \
  '<label class="form-label">Destino de la mercadería' '<label class="form-label">IVA adicional' \
  "FALLA: etiqueta: IVA adicional"
sabotaje_pantalla $J "el destino del producto no se guarda" \
  $'            if (it) it.iva_adicional = t.value || null;\n' '' \
  'FALLA: por producto: [null,null]'

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
