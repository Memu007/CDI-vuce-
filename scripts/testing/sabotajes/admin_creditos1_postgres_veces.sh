#!/usr/bin/env bash
# Repite el sabotaje «sin atrapar el choque de la clave» de admin_creditos1_postgres.sh:
# cada corrida tiene que salir 1 con la fila «el mismo pedido para dos cuentas» en [200, 500].
# Una ronda que no se armó sale 4 y cuenta como no roja.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/admin_creditos1_postgres_veces.sh [SHA] [VECES]
# VECES vale 20 si no se da. Sale 0 sólo si todas dan rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
VECES="${2:-20}"
PY="${PY:-python}"
case "$PY" in */*) PY="$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY")";; esac
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
trap 'cd /; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test
"$PY" - <<'PYEOF' || exit 2
p = "proyecto_maria/routers/admin_router.py"; s = open(p, encoding="utf-8").read()
viejo = """        try:
            await db.commit()
        except IntegrityError:
            # Otro pedido con la misma clave entró primero: se deshace lo sumado y se responde con el suyo.
            await db.rollback()
            previa, ya = await db.get(CreditoAdmin, carga.pedido), True"""
if s.count(viejo) != 1:
    raise SystemExit("patrón no encontrado una sola vez")
open(p, "w", encoding="utf-8").write(s.replace(viejo, "        await db.commit()"))
PYEOF
rojas=0
for i in $(seq 1 "$VECES"); do
  salida="$(PY="$PY" scripts/testing/con_pg16.sh "$PY" scripts/testing/admin_creditos1_postgres.py 2>&1)"; codigo=$?
  fila="$(grep -F 'MAL | el mismo pedido para dos cuentas' <<<"$salida" | head -1)"
  if [ "$codigo" -eq 1 ] && grep -qF '[200, 500]' <<<"$fila"; then rojas=$((rojas+1)); v=ROJO; else v=NO; fi
  echo "corrida $i: salida $codigo $v | $fila | $(grep '^filas MAL' <<<"$salida")"
done
echo "rojas: $rojas de $VECES"
[ "$rojas" -eq "$VECES" ]
