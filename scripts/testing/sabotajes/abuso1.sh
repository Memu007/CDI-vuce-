#!/usr/bin/env bash
# Negativos de ABUSO-1: cada sabotaje deshace una regla y tests/test_abuso1.py
# tiene que fallar por ese motivo.
# S5: un evento de más de 16 KB da 413 y no se guarda, venga o no
# Content-Length; uno de hasta 16 KB se guarda; ninguno escribe
# logs/ui_events.jsonl.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/abuso1.sh [SHA]
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

pytest_a1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_abuso1.py 2>&1
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

# juzgar <nombre> <salida> <código> <lo que el rojo tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3"; shift 3
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^(FAILED|E )" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
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
  salida="$(pytest_a1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
T=tests/test_abuso1.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_a1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi

# --- S5: más de 16 KB da 413 y no se guarda
sabotaje $M "sin tope: se lee y se guarda cualquier cuerpo" \
  $'        if total > tope:\n            return None\n' '' \
  "FAILED $T::test_s5_evento_de_5mb_no_se_guarda[False-/api/ui/event]" \
  "FAILED $T::test_s5_evento_de_5mb_no_se_guarda[True-/api/session/state]" \
  "FAILED $T::test_s5_sin_content_length_tambien_corta[/api/ui/event]" "(200, '{\"ok\":true}')"
sabotaje $M "el tope deja afuera un evento de 16 KB justos" \
  '        if total > tope:' '        if total >= tope:' \
  "FAILED $T::test_s5_el_tope_es_16kb[/api/ui/event]" "Evento demasiado grande"
sabotaje $M "el tope es de 32 KB" \
  '_UI_EVENT_MAX_BYTES = 16 * 1024' '_UI_EVENT_MAX_BYTES = 32 * 1024' \
  "FAILED $T::test_s5_el_tope_es_16kb[/api/session/state]" "{\"ok\":true}"
sabotaje $M "el evento grande da 200 en vez de 413" \
  'return JSONResponse({"ok": False, "detail": "Evento demasiado grande"}, status_code=413)' \
  'return JSONResponse({"ok": False, "detail": "Evento demasiado grande"})' \
  "FAILED $T::test_s5_evento_de_5mb_no_se_guarda[True-/api/ui/event]" "AssertionError: (200, '{\"ok\":false"

# --- S5: el evento no se escribe en logs/ui_events.jsonl
sabotaje $M "vuelve la escritura a logs/ui_events.jsonl" \
  $'        try:\n            await _persist_ui_telemetry_row(db, username, payload)' \
  $'        os.makedirs(os.path.join(basedir, "logs"), exist_ok=True)\n        with open(os.path.join(basedir, "logs", "ui_events.jsonl"), "a", encoding="utf-8") as fh:\n            fh.write(_json.dumps(payload) + "\\n")\n        try:\n            await _persist_ui_telemetry_row(db, username, payload)' \
  "FAILED $T::test_s5_un_evento_chico_se_guarda_y_no_escribe_el_jsonl[/api/ui/event]" "assert _tamano_jsonl() == antes"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
