#!/usr/bin/env bash
# Control de CONEXIONES-1: el medidor (scripts/testing/conexiones1_medir.py)
# tiene que dar verde sin sabotaje y rojo cuando la sonda cancela algunos
# AsyncSession.close() a propósito, reteniendo la sesión o soltándola.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/conexiones1.sh [SHA] [-- flags del medidor]
# Trabaja en un worktree descartable y cada corrida levanta su propio
# Postgres 16 con scripts/testing/con_pg16.sh.
# Sale con error si una corrida no da lo esperado.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"; shift || true
[ "${1:-}" = "--" ] && shift
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0

# corrida <sabotaje> <salida esperada> <texto que el log tiene que tener>
corrida() {
  local sabotaje="$1" esperada="$2" texto="$3" salida codigo; shift 3
  salida="$(CONEXIONES1_SABOTAJE="$sabotaje" PY="$PY" scripts/testing/con_pg16.sh \
    "$PY" scripts/testing/conexiones1_medir.py "$@" 2>&1)"; codigo=$?
  local nombre="${ETIQUETA:-${sabotaje:-sin sabotaje}}"
  if [ "$codigo" -ne "$esperada" ]; then
    echo "MAL   | $nombre: salida $codigo, esperaba $esperada"; tail -15 <<<"$salida"
    FALLAS=$((FALLAS+1))
  elif ! grep -qF -- "$texto" <<<"$salida"; then
    echo "MAL   | $nombre: salida $codigo, pero sin «$texto»"; tail -15 <<<"$salida"
    FALLAS=$((FALLAS+1))
  else
    echo "BIEN  | $nombre: salida $codigo, dice «$texto»"
  fi
}

# en_codigo <viejo> <nuevo>...: cambia connection.py para que el producto no
# cierre la sesión; lo deshace la llamada siguiente o el final del script.
en_codigo() {
  git checkout -q -- .
  "$PY" - "$@" <<'PYEOF' || { echo "PATRÓN | $1"; FALLAS=$((FALLAS+1)); return 1; }
import sys
p = "proyecto_maria/database/connection.py"; s = open(p, encoding="utf-8").read()
for viejo, nuevo in zip(sys.argv[1::2], sys.argv[2::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez: {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

corrida ""                       0 "sin conexiones tomadas" "$@"
corrida close_cancelado          1 "QUEDAN CONEXIONES TOMADAS" "$@"
corrida close_cancelado_suelto   1 "QUEDAN CONEXIONES TOMADAS" "$@"

ABRE='    async with AsyncSessionLocal() as session:'
SIN_WITH='    if (session := AsyncSessionLocal()) is not None:'
CIERRA='            await session.close()'
# El producto no cierra la sesión y la guarda: el pool nunca vuelve a cero.
en_codigo "$ABRE" "$SIN_WITH" "$CIERRA" \
  '            get_async_session.__dict__.setdefault("vivas", []).append(session)' &&
  ETIQUETA="el producto guarda la sesión sin cerrar" corrida "" 1 "QUEDAN CONEXIONES TOMADAS" "$@"
# El producto no cierra la sesión y la suelta: el recolector la levanta y avisa.
en_codigo "$ABRE" "$SIN_WITH" "$CIERRA" '            pass' &&
  ETIQUETA="el producto suelta la sesión sin cerrar" corrida "" 1 "QUEDAN CONEXIONES TOMADAS" "$@"
git checkout -q -- .
exit $((FALLAS > 0))
