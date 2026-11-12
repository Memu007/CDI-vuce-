#!/usr/bin/env bash
# Corre un caso de CONEXIONES-1 con un parche aplicado sobre HEAD (por defecto
# conexiones1_parche_b.diff; PARCHE=conexiones1_parche_nokey.diff elige otro), en un
# worktree descartable que se borra al terminar.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/conexiones1_con_parche.sh \
#        scripts/testing/conexiones1_pares.py
# Sale con el código del caso, o con el de git si el parche no aplica.
set -euo pipefail
[ "$#" -eq 1 ] || { echo "uso: $0 scripts/testing/<caso>.py" >&2; exit 2; }
RAIZ="$(git rev-parse --show-toplevel)"
WT="$(mktemp -d /tmp/cdi-parche.XXXXXX)"
cerrar() { git -C "$RAIZ" worktree remove --force "$WT"; }
trap cerrar EXIT
git -C "$RAIZ" worktree add --detach "$WT" HEAD >/dev/null 2>&1
git -C "$WT" apply "$RAIZ/scripts/testing/${PARCHE:-conexiones1_parche_b.diff}"
"$RAIZ/scripts/testing/con_pg16.sh" "${PY:-python3}" "$WT/$1"
