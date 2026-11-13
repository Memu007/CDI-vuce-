#!/usr/bin/env bash
# Corre todas las scripts/testing/pantalla_*.js sobre un SHA, cada una con su
# uvicorn y su base sqlite nuevos (el registro admite 5 cuentas por hora e IP).
# Escribe una línea por pantalla y al final un resumen; sale con 1 si hay rojas.
#
# Lo que una pantalla necesita lo dice su cabecera (las líneas // de arriba):
#   // corredor: servidor VAR=valor ...   variables para el servidor
#   // corredor: argumentos a b ...       argumentos, relativos a la raíz
#   // corredor: sin servidor             no levanta servidor ni base
# Toda pantalla recibe BASE_URL, CDI_DB (la base del servidor), PY y CHROMIUM.
#
# uso: PY=<python del proyecto> scripts/testing/correr_pantallas.sh [SHA] [salida]
#   SHA     por defecto HEAD
#   salida  carpeta donde queda el log de cada pantalla (por defecto, una nueva)
#   TOPE    segundos por pantalla (600)
#   SOLO    nombres de las pantallas a correr, separados por espacio (todas)
set -u
SHA=$(git rev-parse --verify "${1:-HEAD}^{commit}") || exit 2
SAL=${2:-$(mktemp -d -t pantallas.XXXX)}
mkdir -p "$SAL" || exit 2
SAL=$(cd "$SAL" && pwd)
PY=${PY:-python}
case "$PY" in */*) PY=$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY") ;; esac
CHROMIUM=${CHROMIUM:-/opt/pw-browsers/chromium}
TOPE=${TOPE:-600}

WT=$(mktemp -d -t pantallas-wt.XXXX)
# Un TERM o un Ctrl-C a mitad de una pantalla no deja vivos su node ni su uvicorn.
hijo= api=
retirar() {
  [ -n "$hijo" ] && kill "$hijo" 2>/dev/null; [ -n "$api" ] && kill "$api" 2>/dev/null; wait
  git worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$WT" 2>/dev/null
}
trap retirar EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
git worktree add --detach "$WT" "$SHA" >/dev/null 2>&1 || { echo "no pude armar el worktree de $SHA"; exit 2; }

# Una línea por pedido de la cabecera que empieza con $2, sin el prefijo.
cabecera() { awk -v k="$2" '!/^\/\//{exit} index($0, "// corredor: " k) == 1 {print substr($0, length("// corredor: " k) + 2)}' "$1"; }

puerto_libre() { "$PY" -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }

# Espera a que /health conteste; falla si el servidor se muere antes o pasa un minuto.
esperar_salud() {
  local hasta=$((SECONDS + 60))
  until curl -fsS "http://127.0.0.1:$1/health" >/dev/null 2>&1; do
    kill -0 "$2" 2>/dev/null && [ $SECONDS -lt $hasta ] || return 1
    sleep 0.2
  done
}

# Corre la pantalla en segundo plano: así bash atiende un TERM sin esperar a que termine.
correr_nodo() {  # $1 = log; el resto, variables y argumentos de node
  local log=$1; shift
  (cd "$WT" && exec env PY="$PY" CHROMIUM="$CHROMIUM" "$@") >"$log" 2>&1 &
  hijo=$!; wait "$hijo"; RC=$?; hijo=
}

correr_una() {  # $1 = nombre; deja rc en RC y el log en $SAL/$1.log
  local js=scripts/testing/pantalla_$1.js d log=$SAL/$1.log extra args puerto
  d=$(mktemp -d -p "$SAL" "$1.XXXX")
  args=$(cabecera "$WT/$js" argumentos)
  if cabecera "$WT/$js" 'sin servidor' | grep -q '^'; then
    correr_nodo "$log" timeout "$TOPE" node "$js" $args
    return
  fi
  extra=$(cabecera "$WT/$js" servidor)
  for v in $extra; do
    [[ $v =~ ^[A-Z_][A-Z0-9_]*=[^[:space:]]*$ ]] || { echo "FALLA: cabecera: «$v» no es VAR=valor" >"$log"; RC=2; return; }
  done
  puerto=$(puerto_libre)
  (cd "$WT" && exec env ENVIRONMENT=development JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef \
    EMAIL_VERIFICATION_REQUIRED=false GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
    DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x \
    ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
    DATABASE_URL="sqlite+aiosqlite:///$d/local.db" CDI_DATA_DIR="$d/data" $extra \
    "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$puerto") >"$d/api.log" 2>&1 &
  api=$!
  if esperar_salud "$puerto" "$api"; then
    correr_nodo "$log" BASE_URL="http://127.0.0.1:$puerto" CDI_DB="$d/local.db" timeout "$TOPE" node "$js" $args
  else
    { echo "FALLA: el servidor no contestó /health"; tail -5 "$d/api.log"; } >"$log"; RC=2
  fi
  kill "$api" 2>/dev/null; wait "$api" 2>/dev/null; api=
}

echo "pantallas sobre $SHA; logs en $SAL"
verdes=0; rojas=()
for f in "$WT"/scripts/testing/pantalla_*.js; do
  n=$(basename "$f" .js); n=${n#pantalla_}
  [ -n "${SOLO:-}" ] && [[ " $SOLO " != *" $n "* ]] && continue
  correr_una "$n"
  ultima=$(sed -E 's/\x1b\[[0-9;]*m//g' "$SAL/$n.log" | grep -v '^[[:space:]]*$' | tail -1)
  if [ "$RC" -eq 0 ]; then estado=verde; verdes=$((verdes + 1)); else estado=ROJA; rojas+=("$n"); fi
  printf '%-5s %-14s rc=%-3s %s | %s\n' "$estado" "$n" "$RC" "$SAL/$n.log" "${ultima:0:160}"
done
echo "resumen: ${verdes} verdes, ${#rojas[@]} rojas${rojas:+: ${rojas[*]}}"
[ ${#rojas[@]} -eq 0 ]
