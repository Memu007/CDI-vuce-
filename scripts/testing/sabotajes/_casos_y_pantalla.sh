# Arnés común de los sabotajes que miran casos de pytest y un guion de pantalla.
# Se carga con `source` después de definir T (el archivo de casos) y PANTALLA
# (el guion de navegador). Deja el worktree descartable del SHA, `sabotaje` y
# FALLAS, y comprueba que sin sabotaje todo pasa: si no, ningún rojo distingue nada.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT" || exit 2
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0

correr_casos() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider "$T" 2>&1
}

# Levanta una API nueva con su base, corre la pantalla y la apaga: main.py no se
# vuelve a leer con el servidor andando. Se llama dentro de «$(…)»: la trampa es
# de ese subshell y apaga la API también si lo cortan.
correr_pantalla() {
  local puerto rc api
  puerto="$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
  rm -f "$TMPD/pantalla.db"
  env ENVIRONMENT=development DATABASE_URL="sqlite+aiosqlite:///$TMPD/pantalla.db" CDI_DATA_DIR="$TMPD/data" \
      JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
      ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
      nice -n 19 "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$puerto" \
      > "$TMPD/api.log" 2>&1 < /dev/null &
  api=$!
  trap "kill $api 2>/dev/null" EXIT
  local hasta=$((SECONDS + 90))
  until curl -fsS "http://127.0.0.1:$puerto/health" >/dev/null 2>&1; do
    if ! kill -0 "$api" 2>/dev/null || [ $SECONDS -ge $hasta ]; then
      echo "FALLA: la API no levanta"; tail -5 "$TMPD/api.log"; return 2
    fi
    sleep 0.2
  done
  BASE_URL="http://127.0.0.1:$puerto" CDI_DB="$TMPD/pantalla.db" \
    nice -n 19 node "$PANTALLA" 2>&1; rc=$?
  kill "$api" 2>/dev/null; wait "$api" 2>/dev/null
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
    # Sólo el resumen de pytest: el log capturado también trae líneas «ERROR    …».
    vistos="$(grep -E "^(FAILED|ERROR) [^ ]" <<<"$salida" | sed -E "s/^[A-Z]+ //; s/ - .*//" | sort)"
    esperados="$(printf "$T::%s\n" "$@" | sort)"
    if [ "$vistos" != "$esperados" ]; then
      echo "ANCHO | $nombre: no fallan los casos esperados"
      diff <(echo "$esperados") <(echo "$vistos") | grep '^[<>]'; FALLAS=$((FALLAS+1)); return
    fi
  fi
  echo "ROJO  | $nombre: «$frase»$([ $# -gt 0 ] && echo ", $# casos")"
}

salida="$(correr_casos)" || { echo "BASE  | los casos no pasan sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | casos: $(tail -1 <<<"$salida")"
salida="$(correr_pantalla)" || { echo "BASE  | la pantalla no pasa sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | pantalla: $(tail -1 <<<"$salida")"
