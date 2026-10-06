#!/usr/bin/env bash
# uso: docs/pm/herramientas/chequeo-previo.sh [SHA] [puerto]
# Una línea OK / FALLA / AVISO por punto. Sale con 1 si algo falla.
SHA="${1:-HEAD}"
PUERTO="${2:-8080}"
REPO="$(git rev-parse --show-toplevel)"
BASE="${PM_DIR:-/tmp/cdi-pm}"
FULL="$(git -C "$REPO" rev-parse "$SHA" 2>/dev/null)"
WT="$BASE/wt-${FULL:0:8}"
MAL=0
ok(){ echo "OK    $*"; }; falla(){ echo "FALLA $*"; MAL=1; }; aviso(){ echo "AVISO $*"; }

[ -n "$FULL" ] && ok "SHA $SHA existe (${FULL:0:8})" || falla "SHA $SHA no existe"
if [ -d "$WT" ]; then
  [ "$(git -C "$WT" rev-parse HEAD)" = "$FULL" ] && ok "worktree $WT en el SHA" || falla "worktree $WT no está en $SHA"
  [ -z "$(git -C "$WT" status --porcelain --untracked-files=no)" ] && ok "worktree sin cambios" || aviso "worktree con cambios sin commitear"
else
  falla "no hay worktree en $WT (correr levantar.sh $SHA)"
fi
[ -x "$BASE/venv/bin/python" ] && "$BASE/venv/bin/python" -c 'import sys; assert sys.version_info[:2]==(3,12)' 2>/dev/null \
  && ok "entorno virtual con Python 3.12" || falla "falta el entorno virtual 3.12 en $BASE/venv"
N="$(lsof -t -iTCP:"$PUERTO" -sTCP:LISTEN 2>/dev/null | wc -l)"
[ "$N" = "1" ] && ok "un solo proceso escucha en $PUERTO" || falla "$N procesos escuchan en $PUERTO (tiene que ser 1)"
curl -fsS -m 5 "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1 && ok "/health responde" || falla "/health no responde"
curl -fsS -m 5 -o /dev/null "http://127.0.0.1:$PUERTO/dashboard" 2>/dev/null && ok "/dashboard responde" || aviso "/dashboard no responde 200"
if [ -f "$WT/.env" ]; then
  grep -q '^GEMINI_API_KEY=test-key$' "$WT/.env" && ok "Gemini apagado (test-key)" || falla "GEMINI_API_KEY no es test-key: no correr"
  for v in VUCE_MODE TARIFAR_MODE AFIP_MODE; do grep -q "^$v=fake$" "$WT/.env" && ok "$v=fake" || falla "$v no es fake: llamaría a terceros"; done
  grep -qE '^(MP_ACCESS_TOKEN|SMTP_PASSWORD|SENTRY_DSN)=.' "$WT/.env" && falla ".env con credenciales de terceros" || ok ".env sin Mercado Pago, SMTP ni Sentry"
  grep -q 'railway\|rlwy' "$WT/.env" && falla ".env apunta a Railway" || ok ".env sin producción"
fi
CARGA="$(cut -d' ' -f1 /proc/loadavg)"; NUC="$(nproc)"
awk -v c="$CARGA" -v n="$NUC" 'BEGIN{exit !(c < n)}' && ok "carga $CARGA con $NUC núcleos" || aviso "máquina cargada: $CARGA con $NUC núcleos"
exit $MAL
