#!/usr/bin/env bash
# Negativos de ENTRADAS-4: cada sabotaje deshace una regla de la pieza y
# scripts/testing/entradas4_postgres.py, contra PG_URL, tiene que fallar en esa regla.
#
# uso: PY=/ruta/al/venv/bin/python PG_URL=postgresql://cdi@127.0.0.1:55432/postgres \
#        scripts/testing/sabotajes/entradas4.sh [SHA]
# Trabaja en un worktree descartable y una base de Postgres que crea y borra.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG_URL="${PG_URL:?falta PG_URL: un Postgres local y descartable}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0
correr() { env -u DATABASE_URL "$PY" scripts/testing/entradas4_postgres.py "$PG_URL" 2>&1; }

# sabotaje <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo>
# <viejo> tiene que aparecer una sola vez en main.py.
sabotaje() {
  local nombre="$1" esperado="$2"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - proyecto_maria/main.py "$3" "$4" <<'PYEOF'
import sys
p, viejo, nuevo = sys.argv[1:]; s = open(p, encoding="utf-8").read()
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FALLA|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

if ! correr >/dev/null; then
  echo "BASE  | ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi
echo "BASE  | en verde"

CLI="    cliente_id: TextoCodificable | None = Form(default=None),"
sabotaje "el cliente del Excel llega con su NUL a la base" "FALLA | NUL en cliente_id de /upload_excel_v2/: 500" \
  "$CLI" "    cliente_id: str | None = Form(default=None),"
sabotaje "un campo Form de texto nuevo no se mide" "FALLA | campos Form de texto:" \
  "$CLI" "$CLI
    nota: str | None = Form(default=None),"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
