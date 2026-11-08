#!/usr/bin/env bash
# Negativos de AVISOS-1: cada sabotaje afloja o estira el rechazo de una
# destinación de exportación (EC*) en generar y en los avisos, y el caso tiene
# que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/avisos1.sh [SHA]
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
CASOS=(tests/test_doc1_documentos.py)

correr_casos() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider "${CASOS[@]}" 2>&1
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
  salida="$(correr_casos)"; codigo=$?
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
salida="$(correr_casos)" || { echo "BASE  | los casos no pasan sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | $(tail -1 <<<"$salida")"

M=proyecto_maria/main.py
T=tests/test_doc1_documentos.py::test_ec_directa_nunca_entra_a_importacion
P='re.match(r"[\W_]*EC", request.tipo_destinacion or "", re.IGNORECASE)'

sabotaje $M "sólo se saca lo que saca strip" \
  "$P" '(request.tipo_destinacion or "").strip().upper().startswith("EC")' \
  "FAILED $T"'[\u200bEC01-True-/generate_maria]' \
  "FAILED $T"'[\x00EC01-True-/generate_maria/avisos]'
sabotaje $M "distingue mayúsculas" \
  "$P" 're.match(r"[\W_]*EC", request.tipo_destinacion or "")' \
  "FAILED $T"'[ ec01 -True-/generate_maria]'
sabotaje $M "exige algo delante" \
  "$P" 're.match(r"[\W_]+EC", request.tipo_destinacion or "", re.IGNORECASE)' \
  "FAILED $T"'[EC02-True-/generate_maria]'
sabotaje $M "rechaza cualquier destinación" \
  "$P" 're.match(r"[\W_]*[A-Z]", request.tipo_destinacion or "", re.IGNORECASE)' \
  "FAILED $T"'[IC04-False-/generate_maria]' \
  "FAILED $T"'[\u200bIC04-False-/generate_maria/avisos]'

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
