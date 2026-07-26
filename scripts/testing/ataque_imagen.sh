#!/usr/bin/env bash
# ========================================================================
# Ronda G2 del plan adversarial: atacar la imagen Docker real
# ========================================================================
#
# QUÉ HACE (no hay que saber programar para usarlo):
#
#   1. Construye la imagen Docker igual que la que se sube a producción.
#   2. Levanta un Postgres de prueba y la app con variables de producción.
#   3. Le tira 14 ataques y dice cuáles resistió y cuáles no.
#   4. Borra todo lo que creó, gane o pierda.
#
# CÓMO USARLO:
#
#   ./scripts/testing/ataque_imagen.sh
#
# Después mandame la salida completa. No toca tu base real, no usa internet
# y no necesita ninguna clave: crea contenedores descartables y los borra.
#
# Requisitos: Docker andando. Tarda unos 5-10 minutos la primera vez
# (después la imagen queda cacheada y son 2).
# ========================================================================

set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

RED_NET="cdi-ataque-net"
PG="cdi-ataque-pg"
APP="cdi-ataque-app"
IMG="cdi-ataque:local"
PUERTO="${PUERTO:-8099}"
BASE="http://127.0.0.1:${PUERTO}"
ORIGEN_OK="https://cdi-prueba.example.com"
ORIGEN_ATACANTE="https://sitio-malicioso.example.com"

PASADOS=0
FALLADOS=0
declare -a RESUMEN=()

# ------------------------------------------------------------------ helpers
paso()   { echo -e "\n${BLUE}▶ $*${NC}"; }
gana()   { echo -e "  ${GREEN}✅ RESISTIÓ${NC} · $1"; PASADOS=$((PASADOS+1)); RESUMEN+=("OK   | $1"); }
pierde() { echo -e "  ${RED}❌ CAYÓ${NC} · $1"; echo -e "     ${YELLOW}↳ $2${NC}"; FALLADOS=$((FALLADOS+1)); RESUMEN+=("FALLA| $1 → $2"); }

limpiar() {
    echo -e "\n${YELLOW}🧹 Borrando los contenedores de prueba...${NC}"
    docker rm -f "$APP" "$PG" >/dev/null 2>&1 || true
    docker network rm "$RED_NET" >/dev/null 2>&1 || true
}
trap limpiar EXIT

codigo() { curl -s -o /dev/null -w '%{http_code}' -m 10 "$@"; }
cuerpo() { curl -s -m 10 "$@"; }

# --------------------------------------------------------- chequeos previos
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Ronda G2 · Atacando la imagen real${NC}"
echo -e "${BLUE}========================================${NC}"

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo.${NC}"
    echo "   Abrí Docker Desktop (o arrancá el servicio) y volvé a intentar."
    exit 1
fi
echo -e "${GREEN}✅ Docker responde${NC}"

# --------------------------------------------------------------- preparar
paso "Construyendo la imagen (esto es lo que tarda)"
docker build -q -t "$IMG" . || { echo -e "${RED}❌ Falló el build de la imagen.${NC}"; exit 1; }
echo -e "${GREEN}✅ Imagen construida${NC}"

limpiar 2>/dev/null
docker network create "$RED_NET" >/dev/null

paso "Levantando Postgres de prueba"
docker run -d --name "$PG" --network "$RED_NET" \
    -e POSTGRES_USER=cdi -e POSTGRES_PASSWORD=cdi-prueba -e POSTGRES_DB=cdi \
    postgres:16-alpine >/dev/null || { echo -e "${RED}❌ No arrancó Postgres.${NC}"; exit 1; }

for _ in $(seq 1 30); do
    docker exec "$PG" pg_isready -U cdi >/dev/null 2>&1 && break
    sleep 2
done
echo -e "${GREEN}✅ Postgres listo${NC}"

CLAVE=$(head -c 48 /dev/urandom | base64 | tr -d '/+=' | head -c 60)

paso "Levantando la app con variables de PRODUCCIÓN"
docker run -d --name "$APP" --network "$RED_NET" -p "${PUERTO}:8080" \
    -e ENVIRONMENT=production \
    -e JWT_SECRET_KEY="$CLAVE" \
    -e ALLOWED_ORIGINS="$ORIGEN_OK" \
    -e DATABASE_URL="postgresql+asyncpg://cdi:cdi-prueba@${PG}:5432/cdi" \
    -e EMAIL_VERIFICATION_REQUIRED=false \
    "$IMG" >/dev/null || { echo -e "${RED}❌ No arrancó la app.${NC}"; exit 1; }

echo -n "   Esperando a que responda"
LISTA=0
for _ in $(seq 1 45); do
    if [ "$(codigo "${BASE}/health")" = "200" ]; then LISTA=1; break; fi
    echo -n "."
    sleep 2
done
echo

if [ "$LISTA" != "1" ]; then
    echo -e "${RED}❌ La app nunca respondió. Últimos logs:${NC}"
    docker logs --tail 40 "$APP"
    exit 1
fi
echo -e "${GREEN}✅ App viva${NC}"

# ======================================================================
#                            LOS ATAQUES
# ======================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Ataques${NC}"
echo -e "${BLUE}========================================${NC}"

# --- 1. health -----------------------------------------------------------
paso "1· ¿El health check dice la verdad?"
H=$(cuerpo "${BASE}/health")
if echo "$H" | grep -q '"database":"ok"'; then
    gana "Health check reporta base conectada"
else
    pierde "Health check" "no dice que la base esté ok: $H"
fi

# --- 2-4. documentación técnica cerrada ----------------------------------
paso "2· ¿Está la documentación técnica de la API al público?"
for RUTA in /docs /redoc /openapi.json; do
    C=$(codigo "${BASE}${RUTA}")
    if [ "$C" = "404" ]; then
        gana "${RUTA} cerrado (404)"
    else
        pierde "${RUTA} EXPUESTO" "devolvió ${C}; cualquiera ve tu API entera"
    fi
done

# --- 5-6. usuarios demo ---------------------------------------------------
paso "3· ¿Se puede entrar con los usuarios de demostración?"
for PAR in "demo:demo123" "premium:premium123" "basico:basico123"; do
    U="${PAR%%:*}"; P="${PAR##*:}"
    C=$(codigo -X POST "${BASE}/auth/login" -H 'Content-Type: application/json' \
        -d "{\"username\":\"${U}\",\"password\":\"${P}\"}")
    if [ "$C" = "200" ]; then
        pierde "Usuario demo '${U}' ACTIVO" "entró con la clave por defecto"
    else
        gana "Usuario demo '${U}' no existe (${C})"
    fi
done

# --- 7. cookie de sesión --------------------------------------------------
paso "4· ¿La cookie de sesión viaja protegida?"
USUARIO="atacante$RANDOM"
REG=$(curl -s -D /tmp/cdi_ataque_headers -m 15 -X POST "${BASE}/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${USUARIO}\",\"password\":\"Prueba-Larga-123\",\"email\":\"${USUARIO}@ejemplo.com\"}")

if grep -qi "set-cookie" /tmp/cdi_ataque_headers; then
    COOKIE_LINE=$(grep -i "set-cookie" /tmp/cdi_ataque_headers | head -1)
    FALTA=""
    echo "$COOKIE_LINE" | grep -qi "secure"   || FALTA="${FALTA} Secure"
    echo "$COOKIE_LINE" | grep -qi "httponly" || FALTA="${FALTA} HttpOnly"
    if [ -z "$FALTA" ]; then
        gana "Cookie con Secure y HttpOnly"
    else
        pierde "Cookie de sesión sin protección" "le falta:${FALTA}"
    fi
else
    pierde "No se pudo registrar usuario de prueba" "respuesta: $(echo "$REG" | head -c 200)"
fi

# --- 8. CORS --------------------------------------------------------------
paso "5· ¿Un sitio ajeno puede hablarle a tu API?"
CORS=$(curl -s -D - -o /dev/null -m 10 -H "Origin: ${ORIGEN_ATACANTE}" "${BASE}/health" \
       | grep -i "access-control-allow-origin" || true)
if echo "$CORS" | grep -q "$ORIGEN_ATACANTE"; then
    pierde "CORS abierto" "aceptó el origen malicioso: $CORS"
elif echo "$CORS" | grep -q '\*'; then
    pierde "CORS abierto" "responde con comodín '*'"
else
    gana "CORS rechaza orígenes no autorizados"
fi

# --- 9. admin sin login ---------------------------------------------------
paso "6· ¿Los endpoints de administración piden login?"
for RUTA in /api/admin/health/detailed /api/admin/metrics/prometheus; do
    C=$(codigo "${BASE}${RUTA}")
    if [ "$C" = "401" ] || [ "$C" = "403" ]; then
        gana "${RUTA} protegido (${C})"
    else
        pierde "${RUTA} ABIERTO" "devolvió ${C} sin login"
    fi
done

# --- 10. panel interno ----------------------------------------------------
paso "7· ¿El panel interno está protegido?"
C=$(codigo "${BASE}/dev/dashboard")
if [ "$C" = "401" ] || [ "$C" = "403" ]; then
    gana "/dev/dashboard protegido (${C})"
else
    pierde "/dev/dashboard ABIERTO" "devolvió ${C} sin login"
fi

# --- 11. archivos sensibles por la ruta de estáticos ----------------------
paso "8· ¿Se pueden bajar archivos internos?"
CAIDO=0
for RUTA in "/static/../.env" "/static/maria_data.db" "/static/../../.env" "/static/app.log"; do
    C=$(codigo "${BASE}${RUTA}")
    if [ "$C" = "200" ]; then
        pierde "Archivo interno accesible" "${RUTA} devolvió 200"
        CAIDO=1
    fi
done
[ "$CAIDO" = "0" ] && gana "Ningún archivo interno se puede bajar"

# --- 12. cabeceras de seguridad -------------------------------------------
paso "9· ¿Están las cabeceras de seguridad?"
CAB=$(curl -s -D - -o /dev/null -m 10 "${BASE}/")
FALTAN=""
for C in "content-security-policy" "x-content-type-options" "x-frame-options" "strict-transport-security"; do
    echo "$CAB" | grep -qi "^${C}:" || FALTAN="${FALTAN} ${C}"
done
if [ -z "$FALTAN" ]; then
    gana "Todas las cabeceras de seguridad presentes"
else
    pierde "Faltan cabeceras de seguridad" "${FALTAN}"
fi

# --- 13. rate limit -------------------------------------------------------
paso "10· ¿Se puede martillar la API sin límite?"
LIMITO=0
for _ in $(seq 1 150); do
    C=$(codigo -X POST "${BASE}/auth/login" -H 'Content-Type: application/json' \
        -d '{"username":"inexistente","password":"x"}')
    if [ "$C" = "429" ]; then LIMITO=1; break; fi
done
if [ "$LIMITO" = "1" ]; then
    gana "El rate limit corta (429)"
else
    pierde "Sin rate limit efectivo" "150 intentos de login seguidos sin que corte"
fi

# --- 14. los datos sobreviven un reinicio ---------------------------------
paso "11· ¿Los datos sobreviven un reinicio del contenedor?"
docker restart "$APP" >/dev/null 2>&1
for _ in $(seq 1 45); do
    [ "$(codigo "${BASE}/health")" = "200" ] && break
    sleep 2
done
C=$(codigo -X POST "${BASE}/auth/login" -H 'Content-Type: application/json' \
    -d "{\"username\":\"${USUARIO}\",\"password\":\"Prueba-Larga-123\"}")
if [ "$C" = "200" ] || [ "$C" = "429" ]; then
    gana "El usuario creado sigue existiendo después de reiniciar"
else
    pierde "SE PERDIERON LOS DATOS" "el usuario creado antes del reinicio ya no entra (${C})"
fi

# ======================================================================
#                             RESULTADO
# ======================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Resultado de la Ronda G2${NC}"
echo -e "${BLUE}========================================${NC}"
for L in "${RESUMEN[@]}"; do
    if [[ "$L" == FALLA* ]]; then echo -e "${RED}${L}${NC}"; else echo -e "${GREEN}${L}${NC}"; fi
done
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "Resistió: ${GREEN}${PASADOS}${NC}   ·   Cayó: ${RED}${FALLADOS}${NC}"

if [ "$FALLADOS" -gt 0 ]; then
    echo -e "\n${RED}❌ PUERTA G2 NO PASADA.${NC} Mandame esta salida completa y lo arreglo."
    echo -e "${YELLOW}Últimos logs de la app por si sirven:${NC}"
    docker logs --tail 30 "$APP" 2>&1 | tail -30
    exit 1
fi

echo -e "\n${GREEN}✅ PUERTA G2 PASADA. La imagen que se deploya resistió los 14 ataques.${NC}"
exit 0
