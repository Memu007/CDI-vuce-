#!/usr/bin/env bash
# Negativos de PERMISOS-1: el arranque da admin por username y nunca por email ni nombre.
# Cada sabotaje rompe una de las dos y la prueba tiene que ponerse roja por ese caso.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/permisos1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_admin_bootstrap.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
BUSCA='                result = await session.execute(select(User).where(User.username == identifier))'
T='FAILED tests/test_admin_bootstrap.py::test_lo_que_puso_el_usuario_en_su_perfil_no_da_admin'
sabotaje $M "el arranque busca también por email" "$BUSCA" \
  '                result = await session.execute(select(User).where((User.username == identifier) | (User.email == identifier)))' \
  "$T[tal_cual]"
sabotaje $M "el arranque busca el email sin mirar mayúsculas" "$BUSCA" \
  '                result = await session.execute(select(User).where((User.username == identifier) | (func.lower(User.email) == identifier.lower())))' \
  "$T[mayusculas]"
sabotaje $M "el arranque busca también por nombre" "$BUSCA" \
  '                result = await session.execute(select(User).where((User.username == identifier) | (User.name == identifier)))' \
  "$T[tal_cual]"
sabotaje $M "el arranque no da admin a nadie" "$BUSCA" \
  '                result = await session.execute(select(User).where(User.username == identifier, False))' \
  'FAILED tests/test_admin_bootstrap.py::test_bootstrap_admin_promotes_by_username'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
