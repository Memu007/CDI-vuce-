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
export ENVIRONMENT=development GEMINI_API_KEY=test-key \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
export BASE_URL="http://127.0.0.1:$PUERTO"
correr() {
  rm -f "$TMPD/local.db"
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

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
