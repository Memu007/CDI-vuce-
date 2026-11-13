#!/usr/bin/env bash
# Negativos de CUIT-PERFIL: cada sabotaje deshace una regla de lo que «Mi perfil»
# guarda como CUIT (main.py, controles_maria.py) o de cómo la pantalla muestra el rechazo
# (profile.js). Los casos de tests/test_cuit_perfil.py tienen que fallar por ese
# motivo y ningún otro; la pantalla, con su frase.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cuit_perfil.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite, una API local por
# corrida de pantalla y sin terceros: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0
M=proyecto_maria/main.py
C=proyecto_maria/core/controles_maria.py
P=proyecto_maria/static/v2/screens/profile.js
T=tests/test_cuit_perfil.py
MALO=test_lo_que_no_es_un_cuit_no_se_guarda
BUENO=test_un_cuit_bueno_se_guarda_sin_separadores
GUARDADO=test_uno_malo_que_ya_estaba_guardado_queda_hasta_que_se_corrige
VERIFICADOR=("$MALO[verificador equivocado]" "$MALO[verificador equivocado, con guiones]"
             "$MALO[verificador equivocado, de una empresa]" "$MALO[d\\xedgitos de ancho completo]")
LARGO=("$MALO[diez d\\xedgitos]" "$MALO[doce d\\xedgitos]")

correr_casos() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider "$T" 2>&1
}

# Levanta una API nueva con su base, corre la pantalla y la apaga: main.py no se
# vuelve a leer con el servidor andando.
correr_pantalla() {
  local puerto rc
  puerto="$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
  rm -f "$TMPD/pantalla.db"
  env ENVIRONMENT=development DATABASE_URL="sqlite+aiosqlite:///$TMPD/pantalla.db" CDI_DATA_DIR="$TMPD/data" \
      JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
      ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
      nice -n 19 "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$puerto" \
      > "$TMPD/api.log" 2>&1 < /dev/null &
  API=$!
  local hasta=$((SECONDS + 90))
  until curl -fsS "http://127.0.0.1:$puerto/health" >/dev/null 2>&1; do
    if ! kill -0 "$API" 2>/dev/null || [ $SECONDS -ge $hasta ]; then
      echo "FALLA: la API no levanta"; tail -5 "$TMPD/api.log"; kill "$API" 2>/dev/null; API=""; return 2
    fi
    sleep 0.2
  done
  BASE_URL="http://127.0.0.1:$puerto" CDI_DB="$TMPD/pantalla.db" \
    nice -n 19 node scripts/testing/pantalla_cuit_perfil1.js 2>&1; rc=$?
  kill "$API" 2>/dev/null; wait "$API" 2>/dev/null; API=""
  return $rc
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

# sabotaje <casos|pantalla> <archivo> <nombre> <texto original> <texto saboteado> <frase del rojo> [<casos en rojo>...]
# Con «casos», los que fallan tienen que ser exactamente los nombrados.
sabotaje() {
  local corre="$1" archivo="$2" nombre="$3" viejo="$4" nuevo="$5" frase="$6"; shift 6
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$("correr_$corre")"; codigo=$?
  git checkout -q -- proyecto_maria/
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  if ! grep -qF -- "$frase" <<<"$salida"; then
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$frase»"
    grep -E "^(FAILED|FALLA)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
  fi
  if [ "$corre" = casos ]; then
    local vistos esperados
    vistos="$(grep -E "^(FAILED|ERROR) " <<<"$salida" | sed -E "s/^[A-Z]+ //; s/ - .*//" | sort)"
    esperados="$(printf "$T::%s\n" "$@" | sort)"
    if [ "$vistos" != "$esperados" ]; then
      echo "ANCHO | $nombre: no fallan los casos esperados"
      diff <(echo "$esperados") <(echo "$vistos") | grep '^[<>]'; FALLAS=$((FALLAS+1)); return
    fi
  fi
  echo "ROJO  | $nombre: «$frase»$([ $# -gt 0 ] && echo ", $# casos")"
}

# Sin sabotaje, verde: si no, ningún rojo de abajo distingue nada.
salida="$(correr_casos)" || { echo "BASE  | los casos no pasan sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | casos: $(tail -1 <<<"$salida")"
salida="$(correr_pantalla)" || { echo "BASE  | la pantalla no pasa sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | pantalla: $(tail -1 <<<"$salida")"

# 1. Lo que se guarda es un CUIT: once dígitos y su verificador.
sabotaje casos $M "sólo se cuentan los dígitos" \
  'if not cuit_valido(digits):' 'if len(digits) != 11:' \
  "verificador equivocado: 200" "${VERIFICADOR[@]}" "$GUARDADO"
sabotaje casos $M "no se mira nada" \
  'if not cuit_valido(digits):' 'if False:' \
  "diez dígitos: 200" "${VERIFICADOR[@]}" "${LARGO[@]}" "$GUARDADO"
sabotaje casos $M "el rechazo deja guardado el resto del pedido" \
  '            if not cuit_valido(digits):
' '            if not cuit_valido(digits):
                await db.commit()
' \
  "el pedido rechazado no deja nada guardado" "${VERIFICADOR[@]}" "${LARGO[@]}" "$GUARDADO"
sabotaje casos $M "uno malo ya guardado pasa si llega igual" \
  'if not cuit_valido(digits):' 'if not cuit_valido(digits) and digits != u.cuit:' \
  "Con el malo" "$GUARDADO"

# 2. Uno bueno queda sin separadores; el vacío lo borra.
sabotaje casos $M "se guarda como llegó" \
  '            u.cuit = digits' '            u.cuit = raw_cuit' \
  "'20-11111111-2' == '20111111112'" \
  "$BUENO['20-11111111-2']" "$BUENO[' 20 11111111 2 ']" "$BUENO['20.11111111.2']" "$BUENO['30-71234567-1']"
sabotaje casos $M "el vacío no lo borra" \
  '            u.cuit = None' '            pass' \
  "'20111111112' == ''" "$BUENO['']"
sabotaje casos $C "el verificador sale siempre de «11 − resto»" \
  'esperado = 0 if resto == 0 else 9 if resto == 1 else 11 - resto' 'esperado = 11 - resto' \
  "assert 400 == 200" "$BUENO['20111111120']" "$BUENO['20111111189']"

# 3. En la pantalla: no se guarda, el error del servidor queda junto al campo y
#    el malo que ya estaba se muestra.
sabotaje pantalla $M "el servidor sólo cuenta los dígitos" \
  'if not cuit_valido(digits):' 'if len(digits) != 11:' \
  "FALLA: «Mi perfil» guardó 20-99999999-8, que tiene el verificador equivocado"
sabotaje pantalla $P "la pantalla no dice lo que contestó el servidor" \
  "throw new Error((data && data.detail) || 'No se pudo guardar');" "throw new Error('No se pudo guardar');" \
  "FALLA: con 20-99999999-8 escrito terminó en «error: No se pudo guardar» y no en el error del CUIT"
sabotaje pantalla $P "el campo no queda marcado" \
  "        cuitInput.classList.add('is-error');
" '' \
  "FALLA: el campo del CUIT no queda marcado"
sabotaje pantalla $P "el que ya estaba guardado no se muestra" \
  "cuitInput.value = p.cuit ? CDI.formatCuit(p.cuit) : '';" "cuitInput.value = '';" \
  "FALLA: con 20-99999999-8 ya guardado, el campo muestra «»"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
