#!/usr/bin/env bash
# Negativos de ORDEN-1: cada sabotaje deshace una parte de la pieza (o rompe
# en una copia lo que la pieza tiene que respetar del generador) y la prueba
# tiene que fallar por ese motivo. Primero el TXT (tests/test_orden1.py),
# después la carga de archivos (tests/test_doc1_upload.js) y al final la
# pantalla (scripts/testing/pantalla_orden1.js).
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8853] scripts/testing/sabotajes/orden1.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y sin terceros: no toca
# tu copia ni datos compartidos. maria_generator.py se sabotea sólo dentro de
# ese worktree. Cada corrida de la pantalla levanta la API de nuevo, con una
# base vacía.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8853}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo.
sabotaje() {
  local archivo="$1" nombre="$2" esperado="$3"; shift 3
  git checkout -q -- proyecto_maria/
  rm -f test.db
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
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|FALLA|AssertionError" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

G=proyecto_maria/core/maria_generator.py
T=tests/test_orden1.py

# ------------------------------------------------------------------ el TXT
# Lo que el orden nuevo tiene que respetar del generador: la prueba ve si el
# generador deja de seguir el orden o separa los subítems.
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider "$T" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba del TXT ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi

sabotaje $G "el generador no sigue el orden de los productos" \
  "FAILED $T::test_el_txt_reordenado_es_el_original_salvo_el_orden_de_los_items" \
  '    for n_renglon, item in enumerate(items):' \
  "    for n_renglon, item in sorted(enumerate(items), key=lambda t: str(t[1].get('pieza') or '')):"
sabotaje $G "los renglones de la misma posición no se juntan (subítems separados)" \
  "FAILED $T::test_los_subitems_quedan_juntos_bajo_su_item" \
  '        if n_renglon in juntos_de:' '        if False:'
sabotaje $G "el ítem de la posición sale en su último renglón" \
  "FAILED $T::test_el_txt_reordenado_es_el_original_salvo_el_orden_de_los_items" \
  'if juntos_de[n_renglon][0] == n_renglon:' 'if juntos_de[n_renglon][-1] == n_renglon:'
sabotaje $G "los ítems no quedan numerados corridos" \
  "FAILED $T::test_los_items_quedan_numerados_corridos" \
  '        lines.append(f"NARTEXT={idx:04d}")' '        lines.append(f"NARTEXT={idx + 1:04d}")'

# ----------------------------------------------------- la carga de archivos
# Empezar otra operación borra el borrador de esta pestaña y no el de otras.
U=proyecto_maria/static/v2/screens/upload.js
correr() { node tests/test_doc1_upload.js 2>&1; }
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | la prueba de la carga ya está en rojo sin sabotaje: no se puede medir nada"; correr | head -3; exit 1
fi
sabotaje $U "empezar otra operación borra el borrador de todas las pestañas" \
  "AssertionError [ERR_ASSERTION]: another tab keeps its draft" \
  'try { CDI.borrador.borrar(); } catch (_) {}' \
  "for (let i = localStorage.length - 1; i >= 0; i--) { const k = localStorage.key(i); if (k && k.indexOf('cdi_v2_state') === 0) localStorage.removeItem(k); }"
sabotaje $U "empezar otra operación borra la clave vieja y no el borrador de la pestaña" \
  "AssertionError [ERR_ASSERTION]: reload cannot restore A draft" \
  'try { CDI.borrador.borrar(); } catch (_) {}' "try { localStorage.removeItem('cdi_v2_state'); } catch (_) {}"

# ------------------------------------------------------------- la pantalla
git checkout -q -- proyecto_maria/
export ENVIRONMENT=development GEMINI_API_KEY=test-key CSRF_ENFORCE=true \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
export BASE_URL="http://127.0.0.1:$PUERTO"
correr() {
  rm -f "$TMPD/local.db"
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
unset CASOS
if ! correr >/dev/null; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi

A=proyecto_maria/static/v2/app_v2.js
N=proyecto_maria/static/v2/screens/ncm.js

# Dos pestañas a la vez.
export CASOS=a
sabotaje $A "todas las pestañas guardan en la misma clave" \
  "FALLA: con dos pestañas abiertas no quedan guardadas las dos operaciones" \
  "    const claveBorrador = BORRADOR + ':' + pestana;" "    const claveBorrador = BORRADOR;"
sabotaje $A "una pestaña nueva toma la operación de otra que sigue abierta" \
  "FALLA: la segunda pestaña tomó la operación de la primera, que sigue abierta" \
  '            if (!b.closed && ahora - b.savedAt < BORRADOR_HUERFANO_MS) return;  // otra pestaña la está usando' ''
export CASOS=a2
sabotaje $A "la pestaña que queda en la carga borra el borrador de todas" \
  "FALLA: la pestaña que quedó en la carga de archivos borró la operación cerrada" \
  $'            borrarBorrador();\n        }\n    }, 2500);' \
  $'            try { Object.keys(localStorage).filter(k => k.indexOf(BORRADOR) === 0).forEach(k => localStorage.removeItem(k)); } catch (_) {}\n        }\n    }, 2500);'

# Arrastrar.
export CASOS=b
sabotaje $N "soltar no reordena" \
  "FALLA: arrastrar el cable arriba de todo deja" \
  '            reorderItems(desde, hacia);' ''
sabotaje $N "el número de la fila no se puede arrastrar" \
  "FALLA: el producto no tiene de dónde arrastrarlo" \
  "                tr.setAttribute('draggable', 'true');" ''
export CASOS=c
sabotaje $N "el grupo no se arrastra" \
  "FALLA: el grupo no tiene de dónde arrastrarlo" \
  $'            const handle = e.target.closest(\'.col-num\');\n            const tr = e.target.closest(\'tr[data-index], tr.row-grouped\');' \
  $'            const handle = e.target.closest(\'.col-num\');\n            const tr = e.target.closest(\'tr[data-index]\');'

# Recargar.
export CASOS=d
sabotaje $A "al irse no se guarda el orden recién arrastrado" \
  "FALLA: al recargar enseguida vuelve el orden de antes" \
  $'            e.returnValue = \'\';\n            guardarBorrador(false);' $'            e.returnValue = \'\';' \
  '        if (enFlujo()) guardarBorrador(true);' '        if (enFlujo()) {}'
export CASOS=e
sabotaje $N "Ctrl+Z después de arrastrar vuelve la lista de antes" \
  "FALLA: Ctrl+Z después de arrastrar vuelve el orden de antes" \
  $'        lastSnapshot = null;\n        try { CDI.track' $'        try { CDI.track'

sabotaje $N "al arrastrar, la selección no sigue a los productos" \
  "FALLA: al arrastrar, la selección no sigue a los productos" \
  '        items.forEach((it, i) => { if (elegidos.has(it)) selectedRows.add(i); });' ''

# Dueño: la operación es del usuario que la dejó.
export CASOS=f
sabotaje $A "otro usuario recupera la operación" \
  "FALLA: otro usuario en la misma computadora recupera la operación" \
  '        if (parsed.user !== user) return null;' ''
sabotaje $A "la clave vieja sin pestaña no se borra" \
  "FALLA: la clave vieja sin pestaña no se descarta" \
  '            try { localStorage.removeItem(clave); } catch (_) {}' ''
sabotaje $A "el sobre de hoy sin dueño no se borra" \
  "FALLA: el borrador de hoy sin dueño no se descarta" \
  "typeof parsed.user !== 'string' || !parsed.user || " ''

# Edad: 7 días.
export CASOS=g
sabotaje $A "un borrador de más de 7 días se recupera" \
  "FALLA: se recupera un borrador de hace más de 7 días" \
  ' || Date.now() - savedAt > BORRADOR_VENCE_MS' ''
sabotaje $A "vence a los 6 días y no a los 7" \
  "FALLA: un borrador de hace casi 7 días no se recupera" \
  'const BORRADOR_VENCE_MS = 7 * 24' 'const BORRADOR_VENCE_MS = 6 * 24'
# Adversario Sonnet alto: el vencido no se recupera pero tampoco se borra; el
# sin dueño se sigue borrando.
sabotaje $A "el vencido no se borra al barrer" \
  "FALLA: el borrador de hace más de 7 días no se borra al barrer" \
  $' || Date.now() - savedAt > BORRADOR_VENCE_MS) {\n            try { localStorage.removeItem(clave); } catch (_) {}\n            return null;\n        }' \
  $') {\n            try { localStorage.removeItem(clave); } catch (_) {}\n            return null;\n        }\n        if (Date.now() - savedAt > BORRADOR_VENCE_MS) return null;'

# Pestaña que murió sin pagehide.
export CASOS=h
sabotaje $A "una pestaña muerta sin avisar no se da por muerta nunca" \
  "FALLA: no se recupera la operación de una pestaña que murió sin avisar" \
  'const BORRADOR_HUERFANO_MS = 3 * 60 * 1000;' 'const BORRADOR_HUERFANO_MS = 1e12;'

# Pestaña viva: la duplicada no toma; la restaurada sí.
export CASOS=i
sabotaje $A "la duplicada toma la operación de la original viva" \
  "FALLA: la pestaña duplicada tomó la operación de la original, que sigue abierta" \
  'if (propio && !(await pestanaViva(pestanaAnterior)))' 'if (propio)'
sabotaje $A "la propia se recupera sólo si se cerró con pagehide" \
  "FALLA: la pestaña restaurada no recupera su operación" \
  'if (propio && !(await pestanaViva(pestanaAnterior)))' 'if (propio && propio.closed)'
sabotaje $A "toda pestaña anterior se da por viva" \
  "FALLA: la pestaña restaurada no recupera su operación" \
  '            .catch(() => true)' '            .then(() => true, () => true)'
# Adversario Sonnet alto: la pestaña no retiene su propio lock.
sabotaje $A "la pestaña no retiene su lock" \
  "FALLA: la pestaña duplicada tomó la operación de la original, que sigue abierta" \
  "        try { navigator.locks.request(BORRADOR_PESTANA + ':' + pestana, () => new Promise(() => {})).catch(() => {}); } catch (_) {}" ''

# Sin usuario al abrir: se vuelve a pedir hasta tenerlo.
export CASOS=j
sabotaje $A "el usuario se pide una sola vez al abrir" \
  "FALLA: con la consulta del usuario caída al abrir, la pestaña no la vuelve a pedir" \
  '        const usuarioListo = cargarUsuarioHastaTenerlo();' '        const usuarioListo = loadCurrentUser();'
# Con un 500 la consulta sale por «if (!res.ok)», no por el «return» del final.
sabotaje $A "el reintento da por cargado al usuario aunque falló" \
  "FALLA: con la consulta del usuario caída al abrir, la pestaña no la vuelve a pedir" \
  '            if (!res.ok) return;' '            if (!res.ok) return true;'
sabotaje $A "el reintento no espera entre pedidos" \
  "FALLA: la pestaña martilla la consulta del usuario" \
  'for (let espera = 1000; ' 'for (let espera = 0; ' \
  'espera = Math.min(espera * 2, 30000))' 'espera = 0)'

# Otro usuario entra en el mismo navegador mientras la pestaña reintenta.
export CASOS=k
sabotaje $A "la pestaña no mira si la sesión cambió desde que abrió" \
  "FALLA: la operación cargada antes de saber el usuario se guardó a nombre de quien entró después" \
  'if (sesionAntes !== sesionAlAbrir || getCsrfToken() !== sesionAlAbrir) {' 'if (false) {'
sabotaje $A "al abrir con otra sesión no se avisa" \
  "FALLA: entró otro usuario mientras la pestaña reintentaba y la pestaña no avisa" \
  '                    marcarAjena();' '                    sesionAjena = true;'

# Devolución 20:08. Otro usuario entra con la pestaña abierta: no se guarda a
# nombre de nadie y se avisa.
export CASOS=l
sabotaje $A "la sesión que cambió se confirma sin mirar el usuario" \
  "FALLA: lo que cargó B en la pestaña de A se guardó a nombre de " \
  '        if (username !== duenoPestana) {' '        if (false) {'
sabotaje $A "otro usuario entra y la pestaña no avisa" \
  "FALLA: la pestaña dejó de guardar y no lo avisa" \
  $'        if (username !== duenoPestana) {\n            marcarAjena();' \
  $'        if (username !== duenoPestana) {\n            sesionAjena = true;'
# El guardián de usuarioActual: en (l) no se ve, porque al cargar el semáforo
# valida con un POST y el freno de api() ya tapa la pestaña. z28 entra con la
# operación ya validada.
export CASOS=z28
sabotaje $A "la pestaña guarda sin mirar si la sesión cambió" \
  "FALLA: entró otro usuario y la pestaña de A no escribe nada y lo que cambió después se guardó a nombre de " \
  '        if (getCsrfToken() !== sesionDelDueno) {' '        if (false) {'
# Lo mismo, pasando por la sesión cerrada.
export CASOS=n
sabotaje $A "sale A, entra B y la sesión se confirma sin mirar el usuario" \
  "FALLA: salió A, entró B y lo cargado se guardó a nombre de " \
  '        if (username !== duenoPestana) {' '        if (false) {'

# El mismo usuario sale y vuelve a entrar: sigue guardando, sin aviso.
export CASOS=m
sabotaje $A "la sesión nueva del dueño no se recuerda" \
  "FALLA: el mismo usuario volvió a entrar y la pestaña dejó de guardar" \
  '        sesionDelDueno = sesion;' ''
export CASOS=m2
sabotaje $A "el aviso de sesión cerrada no se va al volver a entrar" \
  "FALLA: el mismo usuario volvió a entrar y la pestaña sigue avisando que no guarda" \
  "        if (['sinsesion', 'red', 'comprobando'].includes(avisoBorrador)) avisarBorrador(null);" ''

# Con otro usuario adentro, la pestaña del dueño no borra lo que él dejó.
export CASOS=y
sabotaje $A "la pestaña borra el borrador con cualquier sesión" \
  "FALLA: entró otro usuario y la pestaña del dueño borró su operación" \
  '        if (!usuarioActual()) return;' ''

# Salir y volver desde la caché del navegador.
export CASOS=o
sabotaje $A "pagehide no marca la pestaña cerrada" \
  "FALLA: pagehide no la marca cerrada" \
  '        if (enFlujo()) guardarBorrador(true);' '        if (enFlujo()) guardarBorrador(false);'
sabotaje $A "al volver de la caché no se marca en uso" \
  "FALLA: al volver de la caché no queda en uso" \
  '        if (e.persisted) guardarBorrador(false);' ''
sabotaje $A "al volver de la caché se marca en uso sin mirar la sesión" \
  "FALLA: volvió de la caché con otro usuario y la marcó en uso" \
  '        if (e.persisted) guardarBorrador(false);' \
  '        if (e.persisted && enFlujo()) try { localStorage.setItem(claveBorrador, JSON.stringify({ v: 1, user: duenoPestana, savedAt: Date.now(), closed: false, state: CDI.state })); } catch (_) {}'

# Usuario lento o caído al recargar: la operación vuelve cuando llega; si
# mientras tanto se cargó otra, no se pisa y se avisa.
export CASOS=p
sabotaje $A "si el usuario llega tarde, la operación no se recupera" \
  "la operación no vuelve a la pestaña que recargó" \
  '                    usuarioListo.then(() => CDI.borrador.buscar()).then(b => b && adoptarTarde(b))' \
  '                    Promise.resolve(null).then(b => b && adoptarTarde(b))'
sabotaje $A "la operación de antes queda guardada sin aviso" \
  "FALLA: la operación de antes de recargar quedó guardada y la pestaña no lo avisa" \
  "avisarBorrador('pendiente', " "(() => {})('pendiente', "

# El navegador sin lugar: se avisa.
export CASOS=q
sabotaje $A "sin lugar en el navegador no se avisa" \
  "FALLA: el navegador no tiene lugar para guardar la operación y la pestaña no avisa" \
  "avisarBorrador('lleno', 'El navegador no tiene lugar para guardar" \
  "(() => {})('lleno', 'El navegador no tiene lugar para guardar"

# Devolución 20:08, vuelta 2. El usuario llega tarde y la pestaña no está
# vacía: no se mueve de pantalla ni pisa lo que hay, y la de antes se avisa.
export CASOS=z
sabotaje $A "el usuario tarde recupera aunque la pestaña esté fuera de la carga" \
  "FALLA: el usuario llegó tarde y la pestaña se fue de la pantalla en que estaba" \
  "const ocupada = pestanaTocada || currentScreen !== 'upload'" "const ocupada = pestanaTocada"
# Lo mismo con una subida en curso.
export CASOS=z2
sabotaje $A "el usuario tarde recupera aunque haya una subida en curso" \
  "FALLA: el usuario llegó con una subida en curso y la operación de antes de recargar se perdió" \
  '|| (CDI.subidaEnCurso && CDI.subidaEnCurso());' '|| false;'
sabotaje $U "la carga no dice que hay una subida en curso" \
  "FALLA: el usuario llegó con una subida en curso y la operación de antes de recargar se perdió" \
  'CDI.subidaEnCurso = () => subiendo > 0;' 'CDI.subidaEnCurso = () => false;'
# Recargar sin lugar en el navegador: se avisa y el borrador queda.
export CASOS=z3
sabotaje $A "sin lugar al recuperar no se avisa" \
  "FALLA: al recargar sin lugar en el navegador" \
  "avisarBorrador('lleno', 'El navegador no tiene lugar para recuperar" \
  "(() => {})('lleno', 'El navegador no tiene lugar para recuperar"
# La consulta del usuario no contesta nunca: se corta y se avisa.
export CASOS=z4
sabotaje $A "la consulta de la sesión no tiene tope" \
  "FALLA: cambió la sesión, la consulta del usuario no contesta y en 20 s la pestaña no avisa" \
  "{ credentials: 'same-origin', signal: corte.signal }" "{ credentials: 'same-origin' }"
# En la carga de archivos con una operación cargada mientras esperaba: no se
# pisa. En (p) la carga lleva a review y la pantalla ya tapa este mutante.
export CASOS=z5
sabotaje $A "la recuperación tardía pisa la operación cargada mientras" \
  "FALLA: el usuario llegó tarde a la carga de archivos y la operación de antes pisó la cargada" \
  '|| (CDI.state && CDI.state.items && CDI.state.items.length > 0)' '|| false'

# Entra otro usuario con la primera consulta en camino y la consulta sale con
# la sesión nueva: la sesión se compara también al volver la respuesta.
export CASOS=z8
sabotaje $A "la primera consulta no mira si la sesión cambió mientras volvía" \
  "FALLA: entró otro usuario con la primera consulta del usuario en camino y lo cargado se guardó a nombre de él" \
  ' || getCsrfToken() !== sesionAlAbrir' ''

# El diálogo de archivos abierto antes de que llegue el usuario: la pestaña
# ya se tocó y la recuperación tardía no adopta.
export CASOS=z6
sabotaje $A "la recuperación tardía no mira si se tocó la pestaña" \
  "FALLA: se abrió el diálogo de archivos antes de que llegara el usuario y la operación de antes de recargar se perdió" \
  'const ocupada = pestanaTocada || ' 'const ocupada = '

# La consulta del usuario da error o no contesta al recargar: se avisa y,
# colgada, se corta para reintentar.
export CASOS=z7
sabotaje $A "sin usuario a tiempo no se avisa" \
  "FALLA: al recargar la consulta del usuario da error y en 8 s la pestaña no avisa que no guarda" \
  "if (!sinSesion) CDI.borrador.avisar('red', AVISO_RED);" ''
sabotaje $A "la primera consulta colgada no se corta" \
  "FALLA: al recargar la consulta del usuario no contesta y cuando vuelve a contestar la pestaña no se entera en 30 s" \
  "api('/auth/current_user', { signal: corte.signal })" "api('/auth/current_user')"
sabotaje $A "el aviso de espera no se va cuando llega el usuario" \
  "FALLA: al recargar la consulta del usuario da error, cuando vuelve a contestar sigue el aviso" \
  "                    if (avisoBorrador === 'red') avisarBorrador(null);" ''

# Con la sesión vencida (401) no se reintenta.
export CASOS=r
sabotaje $A "un 401 no marca la sesión vencida" \
  "FALLA: con la sesión vencida la pestaña reintenta la consulta del usuario" \
  "            if (err && err.message === 'unauthorized') sinSesion = true;" ''
sabotaje $A "el reintento no corta con la sesión vencida" \
  "FALLA: con la sesión vencida la pestaña reintenta la consulta del usuario" \
  ' && !sinSesion; espera' '; espera'

# Con la red cortada al abrir, se reintenta.
export CASOS=s
sabotaje $A "un corte de red da por cargado al usuario" \
  "FALLA: con la consulta del usuario cortada al abrir, la pestaña no la vuelve a pedir" \
  '        return !!currentUser;' '        return true;'

# La espera entre pedidos: de 1 a 30 segundos.
export CASOS=t
sabotaje $A "la espera crece sin tope" \
  "FALLA: en 200 s de reloj la consulta del usuario se pidió" \
  'Math.min(espera * 2, 30000)' 'espera * 2'
sabotaje $A "la espera no crece" \
  "FALLA: en 200 s de reloj la consulta del usuario se pidió" \
  'Math.min(espera * 2, 30000)' 'Math.min(espera, 30000)'

# La operación terminada se borra, al cerrar y con la pestaña abierta.
export CASOS=v
sabotaje $A "al cerrar no se borra la operación terminada" \
  "FALLA: la operación terminada queda guardada al cerrar la pestaña" \
  $'        if (enFlujo()) guardarBorrador(true);\n        else borrarBorrador();' \
  '        if (enFlujo()) guardarBorrador(true);'
sabotaje $A "con la pestaña abierta no se borra la operación terminada" \
  "FALLA: la operación terminada queda guardada con la pestaña abierta" \
  $'            // Se borra sólo el de esta pestaña: la operación terminó o se canceló\n            borrarBorrador();' \
  '            // sabotaje: no se borra'

# Sobres de otra versión y vencidos de otro usuario.
export CASOS=w
sabotaje $A "se acepta un sobre de otra versión" \
  "FALLA: se recupera un sobre de otra versión" \
  'parsed.v !== 1 || ' ''
sabotaje $A "el vencido se borra sólo si es del usuario" \
  "FALLA: el borrador vencido de otro usuario no se borra al barrer" \
  ' || Date.now() - savedAt > BORRADOR_VENCE_MS) {' ') {' \
  '        if (parsed.user !== user) return null;' \
  $'        if (parsed.user !== user) return null;\n        if (Date.now() - savedAt > BORRADOR_VENCE_MS) { try { localStorage.removeItem(clave); } catch (_) {} return null; }'

# La sesión cambia mientras la duplicada mira si la original vive: no
# adopta la operación de A con otro usuario ni la deja sin dueño.
ADOPTA=$'    function adoptarBorrador(b) {\n        const user = usuarioActual();\n        if (!user) {\n            if (duenoPestana && !sesionAjena) {\n                recuperarAlConfirmar = true;\n                avisarBorrador(\'comprobando\', \'Comprobando la sesión antes de recuperar la operación guardada…\');\n            }\n            return null;\n        }\n'
export CASOS=z9
sabotaje $A "adoptar no mira si cambió la sesión (como antes del arreglo)" \
  "FALLA: entró otro usuario mientras la duplicada miraba si la original vive, al abrir y la pestaña le muestra a" \
  "$ADOPTA" $'    function adoptarBorrador(b) {\n        const user = usuarioActual();\n'
export CASOS=z10
sabotaje $A "adoptar no mira si cambió la sesión y guarda a nombre del dueño de la pestaña" \
  "FALLA: entró otro usuario mientras la duplicada miraba si la original vive, con el usuario tarde y la pestaña le muestra a" \
  "$ADOPTA" $'    function adoptarBorrador(b) {\n        const user = duenoPestana;\n'
export CASOS=z11
sabotaje $A "adoptar no mira si cambió la sesión (como antes), con la sesión cerrada" \
  "FALLA: se cerró la sesión mientras la duplicada miraba si la original vive y la operación que A dejó guardada quedó con otro dueño o se borró: [null]" \
  "$ADOPTA" $'    function adoptarBorrador(b) {\n        const user = usuarioActual();\n'

# Tocar la pestaña de cualquier forma antes de que llegue el usuario frena la
# recuperación tardía: cada evento por separado.
TOQUES="['pointerdown', 'click', 'keydown', 'drop']"
export CASOS=z13
sabotaje $A "un clic sin puntero no cuenta como tocar la pestaña" \
  "FALLA: se tocó la pestaña (un clic sin puntero) antes de que llegara el usuario" \
  "$TOQUES" "['pointerdown', 'keydown', 'drop']"
export CASOS=z14
sabotaje $A "una tecla no cuenta como tocar la pestaña" \
  "FALLA: se tocó la pestaña (una tecla) antes de que llegara el usuario" \
  "$TOQUES" "['pointerdown', 'click', 'drop']"
export CASOS=z15
sabotaje $A "soltar un archivo no cuenta como tocar la pestaña" \
  "FALLA: se tocó la pestaña (soltar un archivo que no es factura) antes de que llegara el usuario" \
  "$TOQUES" "['pointerdown', 'click', 'keydown']"
export CASOS=z16
sabotaje $A "apretar el mouse no cuenta como tocar la pestaña" \
  "FALLA: se tocó la pestaña (apretar el mouse sin soltar) antes de que llegara el usuario" \
  "$TOQUES" "['click', 'keydown', 'drop']"

# Con la sesión cerrada se pregunta una vez por sesión, no en cada guardado.
export CASOS=z17
sabotaje $A "no se recuerda qué sesión ya se revisó" \
  "FALLA: con la sesión cerrada la pestaña pregunta quién es en cada guardado" \
  $'        sesionRevisada = sesion;\n' ''

# Con la red cortada se pregunta cada 10 s y, cuando vuelve, se reintenta.
export CASOS=z18
sabotaje $A "con la red cortada no se espera para volver a preguntar" \
  "FALLA: con la red cortada la pestaña pregunta quién es en cada guardado" \
  ' || Date.now() < revisarDesde' ''
sabotaje $A "después de un error de red no se vuelve a preguntar" \
  "FALLA: la red volvió y en 15 s la pestaña no vuelve a guardar" \
  $'                sesionRevisada = null;\n                revisarDesde' '                revisarDesde'

# El aviso de otro usuario no lo pisa el de la red.
export CASOS=z19
sabotaje $A "el aviso de otro usuario lo pisa cualquier otro" \
  "FALLA: entró otro usuario antes de la primera consulta y la pestaña avisa otra cosa" \
  "        if (avisoBorrador === 'ajena' && motivo !== 'ajena') return;"$'\n' ''
# A vuelve a entrar en la espera: la duplicada confirma la sesión nueva.
export CASOS=z12
sabotaje $A "la sesión confirmada no se recuerda" \
  "FALLA: A volvió a entrar (otra sesión) mientras la duplicada miraba si la original vive y la duplicada no recupera la operación al confirmar la sesión" \
  $'        sesionDelDueno = sesion;\n' ''

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
