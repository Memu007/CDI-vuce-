#!/usr/bin/env bash
# Negativos de ADMIN-1: cada sabotaje le saca el control de admin a una ruta
# y la prueba que recorre las rutas tiene que ponerse roja nombrándola.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/admin1.sh [SHA]
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

# sabotaje <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local nombre="$1" viejo="$2" nuevo="$3" esperado="$4"
  git checkout -q -- proyecto_maria/main.py
  if ! "$PY" - "$viejo" "$nuevo" <<'PYEOF'
import sys
p = "proyecto_maria/main.py"; s = open(p).read()
viejo, nuevo = sys.argv[1], sys.argv[2]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_admin_solo_admin.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

sabotaje "router de admin vuelve a get_current_user" \
  'dependencies=[Depends(require_admin)]' 'dependencies=[Depends(get_current_user)]' \
  'POST /api/admin/errors/clear-old → 200'
sabotaje "cache/refresh sin require_admin" \
  $'    request_data: NCMCacheRefreshRequest,\n    user=Depends(require_admin),' \
  $'    request_data: NCMCacheRefreshRequest,\n    user=Depends(get_current_user),' \
  'POST /api/ncm/cache/refresh → 422'
sabotaje "/api/dev/stats sin require_admin" \
  $'async def get_dev_stats(\n    user=Depends(require_admin),' \
  $'async def get_dev_stats(\n    user=Depends(get_current_user),' \
  'GET /api/dev/stats → 200'
sabotaje "/dev/dashboard sin require_admin" \
  'def dev_dashboard(request: Request, user=Depends(require_admin)):' \
  'def dev_dashboard(request: Request, user=Depends(get_current_user)):' \
  'GET /dev/dashboard → 200'
sabotaje "/api/dev/stats escondida del esquema y sin require_admin" \
  $'@app.get("/api/dev/stats")\nasync def get_dev_stats(\n    user=Depends(require_admin),' \
  $'@app.get("/api/dev/stats", include_in_schema=False)\nasync def get_dev_stats(\n    user=Depends(get_current_user),' \
  'GET /api/dev/stats → 200'
sabotaje "cache/refresh pierde la marca admin (la prueba dejaría de verla)" \
  '@app.post("/api/ncm/cache/refresh", tags=["admin"])' '@app.post("/api/ncm/cache/refresh")' \
  "assert ('POST', '/api/ncm/cache/refresh') in ["

git checkout -q -- proyecto_maria/main.py
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
