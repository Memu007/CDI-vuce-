#!/usr/bin/env bash
# Negativos de SUFIJOS-2: cada sabotaje deshace una regla de los sufijos de
# valor (la coma de un número, los Z sin decimales, ninguno vacío, un
# número que cambiaría de valor) y
# tests/test_sufijos2.py tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/sufijos2.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0

pytest_s2() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_sufijos2.py 2>&1
}

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

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_s2)"; codigo=$?
  git checkout -q -- proyecto_maria/
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^FAILED" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# Sin sabotaje, verde: si no, ningún rojo de abajo distingue nada.
salida="$(pytest_s2)" || { echo "BASE  | tests/test_sufijos2.py no pasa sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | $(tail -1 <<<"$salida")"

A=proyecto_maria/core/sufijos_arca.py
G=proyecto_maria/core/maria_generator.py

# 1. La coma de un número en un sufijo libre.
sabotaje $A "el punto decimal sale espacio, como antes" \
  'if miles_o_decimales(m[0]) else f"{m[1]},{m[2]}"' 'if miles_o_decimales(m[0]) else " "' \
  "test_un_numero_con_decimales_en_un_sufijo_libre_sale_con_coma" \
  "test_un_sufijo_libre_que_ya_trae_la_coma_sale_igual" \
  "test_la_propuesta_del_arancel_tambien_lleva_la_coma"
sabotaje $A "una cadena con varios puntos se toma como número" \
  '([0-9]+)[.,]([0-9]+)(?![.,]?[0-9])"' '([0-9]+)[.,]([0-9]+)"' \
  "test_un_codigo_con_varios_puntos_no_se_toma_como_numero"

sabotaje $A "un número con dígitos que no son ASCII entra al TXT" \
  '_DECIMAL = r"(?<![0-9])(?<![0-9][.,])([0-9]+)[.,]([0-9]+)(?![.,]?[0-9])"' \
  '_DECIMAL = r"(?<!\d)(?<!\d[.,])(\d+)[.,](\d+)(?![.,]?\d)"' \
  "test_un_numero_que_no_es_ascii_no_entra_al_txt"

# 2. Un sufijo que pide número, sin decimales.
sabotaje $G "un Z con decimales pasa" \
  'if pide_numero and ("," in valor or cambiaria):' 'if False:' \
  "test_un_sufijo_que_pide_numero_no_acepta_decimales" \
  "test_los_decimales_no_generan_y_dicen_donde" \
  "test_el_error_llega_como_400"
sabotaje $G "un Z con decimales se redondea en silencio" \
  'if pide_numero and ("," in valor or cambiaria):' \
  'if pide_numero and ("," in valor or cambiaria) and not (valor := valor.split(",")[0]):' \
  "test_un_sufijo_que_pide_numero_no_acepta_decimales"
sabotaje $G "también los A piden número" \
  'PIDE_NUMERO = ("Z",)' 'PIDE_NUMERO = ("Z", "A")' \
  "test_un_numero_con_decimales_en_un_sufijo_libre_sale_con_coma" \
  "test_por_el_endpoint_la_coma_llega_al_txt"
sabotaje $G "el error de los decimales no dice dónde" \
  'f"Sufijo de valor{donde}: «{uno[0][:40]}» pide' 'f"Sufijo de valor: «{uno[0][:40]}» pide' \
  "test_los_decimales_no_generan_y_dicen_donde"

# 3. Ninguno vacío.
sabotaje $G "un sufijo vacío pasa" \
  'if not valor.strip():' 'if False:' \
  "test_un_sufijo_vacio_no_se_genera" \
  "test_un_sufijo_vacio_no_genera_y_dice_donde"
sabotaje $G "sólo se mira el vacío como vino, no después de limpiar" \
  'if not valor.strip():' 'if not uno[2]:' \
  "test_un_sufijo_vacio_no_se_genera[AA(   )-]" \
  "test_un_sufijo_vacio_no_se_genera[AA(--)-]"

# 4. Un número que cambiaría de valor no se adivina (revisión de SUFIJOS-2).
sabotaje $G "un número que cambiaría sale igual en un libre" \
  'if cambiaria:' 'if False:' \
  "test_un_numero_que_cambiaria_no_se_genera" \
  "test_el_numero_que_cambiaria_no_genera_y_dice_donde"
sabotaje $G "un Z con signo o barra pasa" \
  'signo = _SIGNO_JUNTO_A_NUMERO.search(valor)' 'signo = None' \
  "test_un_sufijo_que_pide_numero_no_acepta_signos[ZA(-5)-]" \
  "test_un_sufijo_que_pide_numero_no_acepta_signos[ZA(1/2)-]"
sabotaje $G "el signo de un número se pierde en un libre" \
  'signo = _SIGNO_DE_UN_NUMERO.search(valor)' 'signo = None' \
  "test_un_numero_que_cambiaria_no_se_genera[AF(-5)-]" \
  "test_un_numero_que_cambiaria_no_se_genera[AJ(ROLLO .5 M)-]"
sabotaje $G "una fracción sale con espacio en un libre" \
  'if "/" in separadores or ' 'if ' \
  "test_un_numero_que_cambiaria_no_se_genera[AF(1/2)-]"
sabotaje $A "los miles se toman como decimales" \
  'return bool(decimales) and len(decimales) == 3 and entero.lstrip("0") != ""' 'return False' \
  "test_un_numero_que_cambiaria_no_se_genera[AJ(ROLLO 1.500 M)-]"
sabotaje $A "un cero adelante también se toma como miles" \
  'and entero.lstrip("0") != ""' '' \
  "test_lo_que_no_cambia_un_numero_sale_como_antes[AJ(0.750)--AJ(0,750)-]"
sabotaje $G "un dígito que no es ASCII junto a un número pasa" \
  'if _junto_a_un_digito_que_no_es_ascii(valor):' 'if False:' \
  "test_un_numero_que_cambiaria_no_se_genera[AF(1\xbd)-]"
sabotaje $G "un dígito que no es ASCII junto a un punto se toma como pegado a un número" \
  'v in "0123456789" for v in' 'v in "0123456789.," for v in' \
  "test_lo_que_no_cambia_un_numero_sale_como_antes[AF(2.5 X٣.٥)--AF(2,5 X   )-]"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
