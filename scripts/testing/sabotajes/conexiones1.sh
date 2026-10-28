#!/usr/bin/env bash
# Negativos de CONEXIONES-1: cada sabotaje hace que la sesión de la base no
# devuelva su conexión y scripts/testing/conexiones1_medir.py tiene que salir
# con 1 por ese motivo. Antes corre el medidor sin sabotear: tiene que dar 0.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/conexiones1.sh PG_ADMIN [SHA]
#   PG_ADMIN: URL de un Postgres 16 descartable con permiso para crear bases,
#   por ejemplo postgresql://cdi@127.0.0.1:55432/postgres
# Trabaja en un worktree descartable; cada corrida crea y borra su propia base.
# Sale con error si un sabotaje no encuentra su patrón o el medidor no lo ve.
set -uo pipefail
PG="${1:?falta la URL de Postgres}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${2:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
C=proyecto_maria/database/connection.py
FALLAS=0

medir() {
  "$PY" scripts/testing/conexiones1_medir.py "$PG" --n 40 --normales 20 --cortes 10 --plazo 15 2>&1
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

# juzgar <nombre> <salida> <código> <código esperado> <lo que tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3" esperado_codigo="$4"; shift 4
  if [ "$codigo" -ne "$esperado_codigo" ]; then
    echo "MAL   | $nombre: salió con $codigo y tenía que salir con $esperado_codigo"
    tail -25 <<<"$salida"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "MAL   | $nombre: salió con $codigo, pero sin «$esperado»"
      tail -25 <<<"$salida"; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "OK    | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <nombre> <reemplazos: viejo nuevo ...> -- <lo que tiene que decir>...
sabotaje() {
  local nombre="$1"; shift
  git checkout -q -- .
  while [ "$1" != "--" ]; do
    aplicar "$C" "$1" "$2" || { echo "PATRÓN | $nombre"; FALLAS=$((FALLAS+1)); return; }
    shift 2
  done
  shift
  local salida codigo
  salida="$(medir)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" 1 "$@"
}

salida="$(medir)"; codigo=$?
juzgar "sin sabotaje" "$salida" "$codigo" 0 "sin conexiones tomadas" "cancelados: 0"

# La sesión no se cierra y queda referenciada: el pool nunca vuelve a cero.
sabotaje "la sesión no se cierra y queda viva" \
  '    async with AsyncSessionLocal() as session:' \
  '    if (session := AsyncSessionLocal()) is not None:' \
  '            await session.close()' \
  '            get_async_session.__dict__.setdefault("vivas", []).append(session)' \
  -- "QUEDAN CONEXIONES TOMADAS" "  NO  "

# La sesión no se cierra y se suelta: el recolector la levanta y lo avisa.
sabotaje "la sesión no se cierra y se suelta" \
  '    async with AsyncSessionLocal() as session:' \
  '    if (session := AsyncSessionLocal()) is not None:' \
  '            await session.close()' \
  '            pass' \
  -- "QUEDAN CONEXIONES TOMADAS"

git checkout -q -- .
echo "FALLAS $FALLAS"
[ "$FALLAS" -eq 0 ]
