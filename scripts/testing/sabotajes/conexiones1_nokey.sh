#!/usr/bin/env bash
# Control del caso 6 de scripts/testing/conexiones1_pares.py. El caso sale 1
# también con el arreglo, por los deadlocks que siguen esperados en otros pares,
# así que lo que discrimina es el texto: sin sabotaje los candados son FOR NO KEY
# UPDATE y ninguna fila dice «MAL»; sin key_share o sin of= vuelve FOR UPDATE.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/conexiones1_nokey.sh [SHA]
# Trabaja en un worktree descartable y cada corrida levanta su propio
# Postgres 16 con scripts/testing/con_pg16.sh.
# Sale con error si una corrida no da lo esperado.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
# Relativo, dejaría de valer después del cd al worktree.
case "$PY" in */*) PY="$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY")";; esac
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
cd "$WT"
FALLAS=0

# corrida <nombre> <salida esperada> <texto que el log tiene que tener>...
# NO=<regex>: lo que el log no puede tener.
corrida() {
  local nombre="$1" esperada="$2" salida codigo t; shift 2
  salida="$(PY="$PY" scripts/testing/con_pg16.sh "$PY" scripts/testing/conexiones1_pares.py 2>&1)"; codigo=$?
  if [ "$codigo" -ne "$esperada" ]; then
    echo "MAL   | $nombre: salida $codigo, esperaba $esperada"; tail -15 <<<"$salida"
    FALLAS=$((FALLAS+1)); return
  fi
  for t in "$@"; do
    if ! grep -qF -- "$t" <<<"$salida"; then
      echo "MAL   | $nombre: salida $codigo, pero sin «$t»"; tail -15 <<<"$salida"
      FALLAS=$((FALLAS+1)); return
    fi
  done
  if [ -n "${NO:-}" ] && grep -qE -- "$NO" <<<"$salida"; then
    echo "MAL   | $nombre: salida $codigo, pero el log tiene /$NO/"; grep -E -- "$NO" <<<"$salida"
    FALLAS=$((FALLAS+1)); return
  fi
  echo "BIEN  | $nombre: salida $codigo, dice «$*»"
  grep -E '^(DEADLOCK|deadlocks:)' <<<"$salida" | sed 's/^/        /'
}

# en_codigo <archivo> <viejo> <nuevo>...: cambia el producto; lo deshace la
# llamada siguiente o el final del script.
en_codigo() {
  git checkout -q -- .
  "$PY" - "$@" <<'PYEOF' || { echo "PATRÓN | $2"; FALLAS=$((FALLAS+1)); return 1; }
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
for viejo, nuevo in zip(sys.argv[2::2], sys.argv[3::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez: {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

M=proyecto_maria/main.py
U='.with_for_update(key_share=True, of=User)'
O='.with_for_update(key_share=True, of=Organization)'

NO='\| MAL' corrida "sin sabotaje" 1 \
  "_cuenta_bloqueada después del aviso: FOR NO KEY UPDATE OF users | FOR NO KEY UPDATE OF organizations"
# Sin el arreglo: las dos consultas vuelven a FOR UPDATE y la recarga choca.
en_codigo "$M" "$U" '.with_for_update()' "$O" '.with_for_update()' &&
  corrida "sin key_share ni of=" 1 "FOR UPDATE | FOR UPDATE | MAL" \
    "DEADLOCK | recarga + guardado" "DEADLOCK | recarga + maria"
# Sin of=: vuelve desde la cache el FOR UPDATE compilado por la consulta igual del aviso.
en_codigo "$M" "$U" '.with_for_update(key_share=True)' "$O" '.with_for_update(key_share=True)' &&
  corrida "key_share sin of=" 1 "FOR NO KEY UPDATE | FOR UPDATE | MAL"
git checkout -q -- .
exit $((FALLAS > 0))
