#!/usr/bin/env bash
# ========================================================================
# Preflight de variables de entorno para un deploy de producción
# ========================================================================
#
# Para qué sirve: antes de subir nada, chequea que las variables que va a
# recibir el servidor sean las correctas. Sin esto, el contenedor arranca,
# explota y queda reiniciándose sin explicación clara.
#
# Uso suelto (para revisar a mano):
#   ENVIRONMENT=production JWT_SECRET_KEY=... ALLOWED_ORIGINS=... \
#   DATABASE_URL=... ./scripts/deployment/preflight_env.sh
#
# Uso desde un script de deploy:
#   source ./scripts/deployment/preflight_env.sh   # o llamarlo directo
#
# Devuelve 0 si se puede deployar, 1 si hay algo que rompe el arranque.
# ========================================================================

set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

ERRORES=0
AVISOS=0

err()  { echo -e "${RED}❌ $*${NC}"; ERRORES=$((ERRORES + 1)); }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; AVISOS=$((AVISOS + 1)); }
ok()   { echo -e "${GREEN}✅ $*${NC}"; }

echo "🔎 Preflight de variables para deploy"
echo "------------------------------------"

# ---------------------------------------------------------------- ENVIRONMENT
if [ "${ENVIRONMENT:-}" != "production" ]; then
    err "ENVIRONMENT debe ser 'production' (ahora: '${ENVIRONMENT:-vacío}')."
    echo "   Sin esto: se crean usuarios demo (demo/demo123), /docs queda"
    echo "   público y las cookies de sesión viajan sin flag Secure."
else
    ok "ENVIRONMENT=production"
fi

# ------------------------------------------------------------ JWT_SECRET_KEY
# Mismas reglas que proyecto_maria/main.py: si no las cumple, la app no arranca.
JWT="${JWT_SECRET_KEY:-${SECRET_KEY:-}}"
if [ -z "$JWT" ]; then
    err "Falta JWT_SECRET_KEY. La app aborta el arranque en producción."
    echo "   Generala con: python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""
elif [ ${#JWT} -lt 32 ]; then
    err "JWT_SECRET_KEY tiene ${#JWT} caracteres; se necesitan 32 o más."
else
    JWT_LOWER=$(printf '%s' "$JWT" | tr '[:upper:]' '[:lower:]')
    DEBIL=""
    for palabra in cambiar-en-produccion changeme secret default 12345; do
        case "$JWT_LOWER" in *"$palabra"*) DEBIL="$palabra";; esac
    done
    if [ -n "$DEBIL" ]; then
        err "JWT_SECRET_KEY contiene '${DEBIL}'; la app la rechaza por débil."
    else
        ok "JWT_SECRET_KEY presente y fuerte (${#JWT} caracteres)"
    fi
fi

# ------------------------------------------------------------ ALLOWED_ORIGINS
ORIGINS="${ALLOWED_ORIGINS:-}"
if [ -z "$ORIGINS" ] || [ "$ORIGINS" = "*" ]; then
    err "ALLOWED_ORIGINS vacío o '*'. La app aborta el arranque en producción."
    echo "   Poné la URL real del frontend, ej: https://cdi.tu-dominio.com"
elif [ "${ORIGINS#https://}" = "$ORIGINS" ]; then
    warn "ALLOWED_ORIGINS no usa https ('$ORIGINS'). Con cookies Secure el"
    echo "   navegador no las va a mandar."
else
    ok "ALLOWED_ORIGINS=$ORIGINS"
fi

# -------------------------------------------------------------- DATABASE_URL
DB="${DATABASE_URL:-}"
if [ -z "$DB" ]; then
    err "Falta DATABASE_URL: la app cae a SQLite dentro del contenedor."
    echo "   En Cloud Run / Railway el disco es efímero: usuarios, clientes y"
    echo "   operaciones se borran en cada deploy o reinicio."
elif [ "${DB#sqlite}" != "$DB" ]; then
    err "DATABASE_URL apunta a SQLite. Mismo problema: se pierden los datos."
else
    ok "DATABASE_URL apunta a una base externa (Postgres)"
fi

# ------------------------------------------------------------- GEMINI_API_KEY
if [ -z "${GEMINI_API_KEY:-}" ]; then
    warn "Sin GEMINI_API_KEY: /upload_pdf devuelve 503 (no se puede leer la"
    echo "   factura en PDF). El resto de la app funciona."
else
    ok "GEMINI_API_KEY presente"
fi

# --------------------------------------------------------------- MercadoPago
MP="${MP_ACCESS_TOKEN:-}"
if [ -z "$MP" ]; then
    warn "Sin MP_ACCESS_TOKEN: los pagos quedan en modo demo (no se cobra)."
elif [ "${MP#TEST-}" != "$MP" ]; then
    warn "MP_ACCESS_TOKEN es de sandbox (TEST-): los pagos no son reales."
else
    ok "MP_ACCESS_TOKEN de producción"
    if [ -z "${MP_WEBHOOK_SECRET:-}" ]; then
        warn "Sin MP_WEBHOOK_SECRET: el webhook de pagos no valida la firma."
    fi
fi

# --------------------------------------------------------------------- cierre
echo "------------------------------------"
if [ "$ERRORES" -gt 0 ]; then
    echo -e "${RED}Preflight FALLÓ: ${ERRORES} error(es), ${AVISOS} aviso(s).${NC}"
    echo "Arreglá los errores antes de deployar: con cualquiera de ellos el"
    echo "servicio arranca mal o pierde datos."
    exit 1
fi

if [ "$AVISOS" -gt 0 ]; then
    echo -e "${YELLOW}Preflight OK con ${AVISOS} aviso(s). Revisá si te sirven así.${NC}"
else
    echo -e "${GREEN}Preflight OK. Se puede deployar.${NC}"
fi
exit 0
