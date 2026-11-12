#!/usr/bin/env bash
# Corre un caso de CONEXIONES-1 con un parche aplicado sobre HEAD (por defecto
# conexiones1_parche_b.diff; PARCHE=conexiones1_parche_nokey.diff elige otro), en un
# worktree descartable que se borra al terminar.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/conexiones1_con_parche.sh \
#        scripts/testing/conexiones1_pares.py
# Sale con el código del caso, o 2 si el parche no aplica.
set -euo pipefail
[ "$#" -eq 1 ] || { echo "uso: $0 scripts/testing/<caso>.py" >&2; exit 2; }
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
WT="$(mktemp -d /tmp/cdi-parche.XXXXXX)"
cerrar() { git -C "$RAIZ" worktree remove --force "$WT" || true; }
trap cerrar EXIT
git -C "$RAIZ" worktree add --detach "$WT" HEAD >/dev/null
git -C "$WT" apply "$RAIZ/scripts/testing/${PARCHE:-conexiones1_parche_b.diff}" || exit 2
"$RAIZ/scripts/testing/con_pg16.sh" "${PY:-python3}" "$WT/$1"
