#!/usr/bin/env bash
# Negativos de ORDEN-1b: cada sabotaje deshace un freno de la pestaña cuyo
# dueño ya no es el de la sesión, y la pantalla (scripts/testing/pantalla_orden1.js,
# casos z12, z20 a z27, z29 a z32, z34 y z35) tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8875] scripts/testing/sabotajes/orden1b.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y sin terceros: no toca
# tu copia ni datos compartidos. Cada corrida levanta la API de nuevo, con una
# base vacía y CSRF_ENFORCE=true, como en producción; z21 y z23 hacen como
# un servidor que no lo exige.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
# Un rojo por otro motivo deja el log de la API y la salida de la pantalla en
# una carpeta que sobrevive a la corrida: se diagnostica, no se reintenta.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8875}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
FALLAS=0
GUARDADOS=""

# guardar <salida>: copia lo que hace falta para entender un rojo dudoso.
guardar() {
  [ -n "$GUARDADOS" ] || GUARDADOS="$(mktemp -d "${TMPDIR:-/tmp}/orden1b-logs.XXXXXX")"
  local base="$GUARDADOS/$FALLAS"
  printf '%s\n' "$1" >"$base-pantalla.log"
  if cp "$TMPD/api.log" "$base-api.log" 2>/dev/null; then
    echo "      guardados: $base-api.log y $base-pantalla.log"
  else
    echo "      guardado: $base-pantalla.log (la API no llegó a arrancar)"
  fi
}

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo.
sabotaje() {
  local archivo="$1" nombre="$2" esperado="$3"; shift 3
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FALLA" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
    guardar "$salida"
  fi
}

export ENVIRONMENT=development GEMINI_API_KEY=test-key CSRF_ENFORCE=true \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
export BASE_URL="http://127.0.0.1:$PUERTO"
correr() {
  rm -f "$TMPD/local.db" "$TMPD/api.log"
  # Con el puerto ocupado, /health lo contestaría otro servidor y la pantalla
  # mediría otro producto.
  if (exec 3<>"/dev/tcp/127.0.0.1/$PUERTO") 2>/dev/null; then
    echo "FALLA: el puerto $PUERTO ya está ocupado"; return 1
  fi
  DATABASE_URL="sqlite+aiosqlite:///$TMPD/local.db" "$PY" -m uvicorn proyecto_maria.main:app \
    --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && break; sleep 1; done
  if ! curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
    echo "FALLA: la API no levantó"; tail -5 "$TMPD/api.log"; kill $API 2>/dev/null; wait $API 2>/dev/null; API=""; return 1
  fi
  local codigo
  node scripts/testing/pantalla_orden1.js 2>&1; codigo=$?
  kill $API 2>/dev/null; wait $API 2>/dev/null; API=""
  return $codigo
}
export CASOS=z12,z20,z21,z22,z23,z24,z25,z26,z27,z29,z30,z31,z32,z34,z35
if ! correr >/dev/null; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi

A=proyecto_maria/static/v2/app_v2.js
H=proyecto_maria/templates/dashboard_v2.html
SIN_CONSULTA=($'            if (getCsrfToken() !== (sesionDelDueno || sesionAlAbrir) && !(await sesionEsDelDueno())) {\n                throw new Error(sesionAjena ? ERROR_AJENA : ERROR_SIN_SESION);\n            }\n' '')

export CASOS=z20
sabotaje $A "la escritura sale sin preguntar quién es" \
  "FALLA: entró otro usuario y la pestaña de A generó enseguida y quedó una operación en la cuenta de B" \
  "${SIN_CONSULTA[@]}"
sabotaje $A "la pestaña de otro usuario no se tapa" \
  "FALLA: entró otro usuario y la pestaña de A generó enseguida y la pestaña no se tapa" \
  "        try { dialogo.showModal(); } catch (_) { dialogo.setAttribute('open', ''); }"$'\n' ''
sabotaje $H "no está el diálogo que tapa la pestaña" \
  "FALLA: entró otro usuario y la pestaña de A generó enseguida y la pestaña no se tapa" \
  'id="pestanaAjena"' 'id="pestanaAjenaNo"'
sabotaje $A "sin poder comprobar quién es, el error dice otra cosa" \
  "FALLA: entró otro usuario y la pestaña de A genera sin poder comprobar quién es y no muestra el error" \
  "throw new Error(sesionAjena ? ERROR_AJENA : ERROR_SIN_SESION);" "throw new Error(ERROR_AJENA);"

export CASOS=z21
sabotaje $A "un cliente se guarda sin preguntar quién es" \
  "FALLA: entró otro usuario y la pestaña de A guardó un cliente y el cliente quedó en la cuenta de B" \
  "${SIN_CONSULTA[@]}"

export CASOS=z22
sabotaje $A "con la sesión cambiada no escribe aunque sea del mismo usuario" \
  "FALLA: A salió, volvió a entrar y generó enseguida y no generó" \
  '!(await sesionEsDelDueno())' 'true'

export CASOS=z23
sabotaje $A "sin CSRF en el servidor, la escritura sale sin preguntar quién es" \
  "FALLA: con un servidor que no exige CSRF, entró otro usuario y la pestaña de A generó enseguida y quedó una operación en la cuenta de B" \
  "${SIN_CONSULTA[@]}"

export CASOS=z24
sabotaje $A "salir no pregunta quién es y cierra la sesión del otro" \
  "FALLA: entró otro usuario y A apretó «Salir» en su pestaña y cerró la sesión de B" \
  "${SIN_CONSULTA[@]}"
sabotaje $A "salir con la sesión de otro deja la pestaña y va al inicio" \
  "FALLA: entró otro usuario y A apretó «Salir» en su pestaña y la pestaña no se tapa" \
  '            if (sesionAjena) return;'$'\n' ''

export CASOS=z25
sabotaje $A "con la sesión cerrada, la escritura no va al login" \
  "FALLA: A salió en otra pestaña y guardó un cliente en esta y no fue al login" \
  '        if (status === 401) irAlLogin();'$'\n' ''

export CASOS=z26
sabotaje $A "salir sin poder comprobar quién es va al inicio" \
  "FALLA: A volvió a entrar y apretó «Salir» sin poder comprobar quién es y fue al inicio con la sesión abierta" \
  $'            if (e.message === ERROR_SIN_SESION) {\n                toast(\'No se pudo cerrar la sesión\', e.message, \'error\');\n                return;\n            }\n' ''

export CASOS=z27
sabotaje $A "la telemetría sale con la sesión de otro" \
  "FALLA: entró otro usuario y la pestaña de A mandó telemetría a nombre de B" \
  '        if (telemetryMuted || getCsrfToken() !== (sesionDelDueno || sesionAlAbrir)) return;' '        if (telemetryMuted) return;'

# D11: la duplicada que no pudo adoptar lo avisa y recupera al confirmar.
export CASOS=z12
sabotaje $A "la duplicada que no puede adoptar no avisa" \
  "FALLA: A volvió a entrar (otra sesión) mientras la duplicada miraba si la original vive y la duplicada no avisa que está comprobando la sesión" \
  "                avisarBorrador('comprobando', 'Comprobando la sesión antes de recuperar la operación guardada…');"$'\n' ''
sabotaje $A "la duplicada no recupera al confirmar la sesión" \
  "FALLA: A volvió a entrar (otra sesión) mientras la duplicada miraba si la original vive y la duplicada no recupera la operación al confirmar la sesión" \
  '                recuperarAlConfirmar = true;'$'\n' ''

sabotaje $A "la duplicada ya recuperada sigue diciendo que comprueba la sesión" \
  "FALLA: A volvió a entrar (otra sesión) mientras la duplicada miraba si la original vive y, ya recuperada, sigue diciendo que comprueba la sesión" \
  "if (['sinsesion', 'red', 'comprobando'].includes(avisoBorrador))" "if (['sinsesion', 'red'].includes(avisoBorrador))"

CONFIRMA="if (sesionAjena || getCsrfToken() !== sesion) return false;"
export CASOS=z29
sabotaje $A "la respuesta vieja de quién es autoriza con la sesión de otro" \
  "FALLA: la pestaña de A preguntó quién es, entró otro usuario antes de la respuesta y guardó un cliente y el cliente quedó en la cuenta de B" \
  "$CONFIRMA" "if (sesionAjena) return false;"

export CASOS=z30
sabotaje $A "la pestaña tapada al abrir escribe con la sesión de otro" \
  "FALLA: la pestaña de A quedó tapada al abrir y guardó un cliente y el cliente quedó en la cuenta de B" \
  "$CONFIRMA" "if (getCsrfToken() !== sesion) return false;"

export CASOS=z31
for verbo in PUT DELETE PATCH; do
  sabotaje $A "$verbo sale sin preguntar quién es" \
    "FALLA: entró otro usuario y la pestaña de A mandó $verbo " \
    "if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {" "if (!['GET', 'HEAD', 'OPTIONS', '$verbo'].includes(method)) {"
done

export CASOS=z32
sabotaje $A "Escape destapa la pestaña" \
  "FALLA: la pestaña tapada se destapa con Escape" \
  "        dialogo.addEventListener('cancel', e => e.preventDefault());"$'\n' ''
sabotaje $A "«Recargar» no recarga" \
  "FALLA: la pestaña tapada no recarga con «Recargar»" \
  "        document.getElementById('pestanaAjenaRecargar').addEventListener('click', () => window.location.reload());"$'\n' ''

export CASOS=z30
LEE="if (!confirmarSesion(user.username, sesionAntes)) return !!currentUser;"
sabotaje $A "la pestaña tapada al abrir toma los datos del otro" \
  "FALLA: entró otro usuario antes de que la pestaña de A supiera quién es y la pestaña tomó los datos de B" \
  "$LEE" "if (!sesionAjena && !confirmarSesion(user.username, sesionAntes)) return !!currentUser;"

export CASOS=z34
sabotaje $A "al volver del pago toma los datos del otro" \
  "FALLA: A volvió del pago con B adentro y la pestaña tomó los datos de B" \
  "$LEE" "confirmarSesion(user.username, sesionAntes);"

export CASOS=z35
# z35 corta en la primera fila que falla: cada vuelta del pago, con el tour
# antes o después de la carga, se mide sola.
for VUELTA in success topup_success; do
  for PRIMERO in tour carga; do
    export VUELTA PRIMERO
    sabotaje $A "la sesión de la respuesta se lee cuando ya llegó ($VUELTA, primero $PRIMERO)" \
      "FALLA: la relectura de la vuelta del pago ($VUELTA, primero $PRIMERO) contestó A, entró B antes de leerla y la pestaña guardó un cliente y el cliente quedó en la cuenta de B" \
      "            const sesionAntes = getCsrfToken();"$'\n' '' \
      "            if (duenoPestana === null) {" $'            const sesionAntes = getCsrfToken();\n            if (duenoPestana === null) {'
  done
done
unset VUELTA PRIMERO

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
