#!/usr/bin/env bash
# uso: docs/pm/herramientas/levantar.sh <SHA> [puerto]
# Deja un worktree en ese SHA fuera del repo, con entorno virtual (Python 3.12),
# .env inventado, SQLite nueva y la API arriba. Nada de secretos ni producción.
set -euo pipefail
SHA="${1:?uso: levantar.sh <SHA> [puerto]}"
PUERTO="${2:-8080}"
REPO="$(git rev-parse --show-toplevel)"
BASE="${PM_DIR:-/tmp/cdi-pm}"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
WT="$BASE/wt-${SHA:0:8}"
VENV="$BASE/venv"
mkdir -p "$BASE"

if [ ! -d "$WT" ]; then
  git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
fi
cd "$WT"
test "$(git rev-parse HEAD)" = "$(git -C "$REPO" rev-parse "$SHA")" || { echo "FALLA: worktree no está en $SHA"; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
  python3.12 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q -r requirements.txt pytest pytest-cov pytest-asyncio aiosqlite gunicorn

cat > .env <<ENV
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./local.db
GEMINI_API_KEY=test-key
JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef
EMAIL_VERIFICATION_REQUIRED=false
# sin terceros: conectores simulados, dólar contra un puerto local cerrado,
# sin Mercado Pago, SMTP ni Sentry
VUCE_MODE=fake
TARIFAR_MODE=fake
AFIP_MODE=fake
DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PORT=$PUERTO
ENV
rm -f local.db

# una sola API: se mata sólo la que escucha en este puerto
PIDS="$(lsof -t -iTCP:"$PUERTO" -sTCP:LISTEN 2>/dev/null || true)"
if [ -n "$PIDS" ]; then kill $PIDS; sleep 2; fi

set -a; . ./.env; set +a
(setsid nohup "$VENV/bin/python" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" \
   > "$BASE/api-$PUERTO.log" 2>&1 < /dev/null &)

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1; then
    echo "worktree: $WT"
    echo "API arriba: http://127.0.0.1:$PUERTO/health  y  http://127.0.0.1:$PUERTO/dashboard"
    echo "registro: $BASE/api-$PUERTO.log"
    exit 0
  fi
  sleep 1
done
echo "FALLA: la API no respondió en 60 s; ver $BASE/api-$PUERTO.log"; tail -20 "$BASE/api-$PUERTO.log"; exit 1
