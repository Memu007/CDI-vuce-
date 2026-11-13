#!/bin/bash
# ABUSO-1: ¿reciclar el worker de gunicorn borra el bloqueo de login?
# Producción corre gunicorn con --max-requests 1000 y, sin REDIS_URL, los
# contadores de intentos viven en la memoria del worker. Acá se usa
# --max-requests 20 (MR) para verlo rápido, con una base SQLite descartable:
# 7 logins fallidos (el 6.º ya da 429), MR+5 pedidos baratos a /health y otro
# login fallido. Si después da 401 y no 429, el reciclado borró el bloqueo.
# uso: GUNICORN=<venv>/bin/gunicorn bash scripts/testing/abuso1_reciclado.sh
cd "$(dirname "$0")/../.."
GUNICORN=${GUNICORN:-gunicorn}
MR=${MR:-20}
T=$(mktemp -d)
P=$(python3 -c "import socket;s=socket.socket();s.bind(('127.0.0.1',0));print(s.getsockname()[1])")
env -u REDIS_URL DATABASE_URL=sqlite+aiosqlite:///$T/b.db ENVIRONMENT=testing EMAIL_VERIFICATION_REQUIRED=false \
  JWT_SECRET_KEY=clave-solo-para-esta-prueba-con-mas-de-32-caracteres GEMINI_API_KEY=test-key VUCE_MODE=fake \
  TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares CDI_DATA_DIR=$T/data PYTHONPATH=$PWD \
  "$GUNICORN" proyecto_maria.main:app --bind 127.0.0.1:$P --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker --max-requests $MR > $T/g.log 2>&1 &
G=$!
trap 'kill $G 2>/dev/null; wait $G 2>/dev/null; rm -rf $T' EXIT
for i in $(seq 600); do curl -s -o /dev/null http://127.0.0.1:$P/health && break; sleep 0.2; done
L(){ curl -s -o /dev/null -w "%{http_code}" -H 'Content-Type: application/json' \
       -d '{"username":"nadie_reciclado","password":"mal-1234"}' http://127.0.0.1:$P/auth/login; }
echo -n "7 logins fallidos:"; for i in 1 2 3 4 5 6 7; do echo -n " $(L)"; done; echo
echo -n "$((MR+5)) pedidos a /health:"; for i in $(seq $((MR+5))); do curl -s -o /dev/null http://127.0.0.1:$P/health; done; echo " hechos"
for i in $(seq 600); do [ "$(grep -c 'Booting worker' $T/g.log)" -ge 2 ] && curl -s -o /dev/null http://127.0.0.1:$P/health && break; sleep 0.2; done
echo "workers arrancados: $(grep -c 'Booting worker' $T/g.log)"
D=$(L); echo "login fallido después: $D"
[ "$D" = 429 ] && echo "el bloqueo sobrevive al reciclado" || { echo "FALLA: el reciclado borró el bloqueo"; exit 1; }
