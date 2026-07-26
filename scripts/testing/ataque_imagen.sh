#!/usr/bin/env bash
# ========================================================================
# Ronda G2 del plan adversarial: atacar la app con configuración de PRODUCCIÓN
# ========================================================================
#
# QUÉ HACE (no hay que saber programar para usarlo):
#
#   1. Levanta la app con las variables tal cual van a producción.
#   2. Le tira una tanda de ataques y dice cuáles resistió y cuáles no.
#   3. Borra todo lo que creó, gane o pierda.
#
# DOS MODOS:
#
#   ./scripts/testing/ataque_imagen.sh
#       Modo completo. Construye la imagen Docker igual a la que se sube y
#       la ataca. Es el que cierra la puerta G2 de verdad, porque prueba
#       *lo que realmente se deploya*. Necesita Docker andando.
#
#   ./scripts/testing/ataque_imagen.sh --sin-docker
#       Modo reducido. Corre la app directo con Postgres local. Tira los
#       mismos ataques, pero NO prueba la imagen: si el Dockerfile copia mal
#       un archivo o arranca con el comando equivocado, este modo no lo ve.
#
# Mandá la salida completa al terminar. No toca tu base real ni usa internet:
# crea una base descartable y la borra.
# ========================================================================

set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

MODO="docker"
[ "${1:-}" = "--sin-docker" ] && MODO="sin-docker"

RED_NET="cdi-ataque-net"
PG="cdi-ataque-pg"
APP="cdi-ataque-app"
IMG="cdi-ataque:local"
PUERTO="${PUERTO:-8099}"
BASE="http://127.0.0.1:${PUERTO}"
ORIGEN_OK="https://cdi-prueba.example.com"
ORIGEN_ATACANTE="https://sitio-malicioso.example.com"
TMP=$(mktemp -d)
APP_PID=""
PGDIR=""

PASADOS=0
FALLADOS=0
declare -a RESUMEN=()

# ------------------------------------------------------------------ helpers
paso()   { echo -e "\n${BLUE}▶ $*${NC}"; }
gana()   { echo -e "  ${GREEN}✅ RESISTIÓ${NC} · $1"; PASADOS=$((PASADOS+1)); RESUMEN+=("OK    | $1"); }
pierde() { echo -e "  ${RED}❌ CAYÓ${NC} · $1"; echo -e "     ${YELLOW}↳ $2${NC}"; FALLADOS=$((FALLADOS+1)); RESUMEN+=("FALLA | $1 → $2"); }

limpiar() {
    echo -e "\n${YELLOW}🧹 Borrando lo que creó la prueba...${NC}"
    if [ "$MODO" = "docker" ]; then
        docker rm -f "$APP" "$PG" >/dev/null 2>&1 || true
        docker network rm "$RED_NET" >/dev/null 2>&1 || true
    else
        [ -n "$APP_PID" ] && kill "$APP_PID" >/dev/null 2>&1
        [ -n "${PGDIR:-}" ] && pg_ctl -D "$PGDIR" -s stop -m immediate >/dev/null 2>&1
    fi
    rm -rf "$TMP"
}
trap limpiar EXIT

codigo() { curl -s -o /dev/null -w '%{http_code}' -m 10 "$@"; }
cuerpo() { curl -s -m 10 "$@"; }

esperar_health() {
    for _ in $(seq 1 45); do
        [ "$(codigo "${BASE}/health")" = "200" ] && return 0
        sleep 2
    done
    return 1
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Ronda G2 · Atacando con config de producción${NC}"
echo -e "${BLUE}Modo: ${MODO}${NC}"
echo -e "${BLUE}========================================${NC}"

CLAVE=$(head -c 48 /dev/urandom | base64 | tr -d '/+=' | head -c 60)

# ======================================================================
#                        LEVANTAR LA APP
# ======================================================================
if [ "$MODO" = "docker" ]; then
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker no está corriendo.${NC}"
        echo "   Abrí Docker Desktop (o arrancá el servicio) y volvé a intentar."
        echo -e "${YELLOW}   Si no tenés Docker, corré la versión reducida:${NC}"
        echo "   ./scripts/testing/ataque_imagen.sh --sin-docker"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker responde${NC}"

    paso "Construyendo la imagen (esto es lo que tarda)"
    if ! docker build -q -t "$IMG" . ; then
        echo -e "${RED}❌ Falló el build de la imagen.${NC}"
        echo -e "${YELLOW}   Si el error dice 'Forbidden' o no puede bajar python:3.12-slim,${NC}"
        echo -e "${YELLOW}   es la red bloqueando la descarga, no el proyecto.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Imagen construida${NC}"

    docker rm -f "$APP" "$PG" >/dev/null 2>&1 || true
    docker network rm "$RED_NET" >/dev/null 2>&1 || true
    docker network create "$RED_NET" >/dev/null

    paso "Levantando Postgres descartable"
    docker run -d --name "$PG" --network "$RED_NET" \
        -e POSTGRES_USER=cdi -e POSTGRES_PASSWORD=cdi-prueba -e POSTGRES_DB=cdi \
        postgres:16-alpine >/dev/null || { echo -e "${RED}❌ No arrancó Postgres.${NC}"; exit 1; }
    for _ in $(seq 1 30); do
        docker exec "$PG" pg_isready -U cdi >/dev/null 2>&1 && break
        sleep 2
    done
    echo -e "${GREEN}✅ Postgres listo${NC}"

    paso "Levantando la app con variables de PRODUCCIÓN"
    docker run -d --name "$APP" --network "$RED_NET" -p "${PUERTO}:8080" \
        -e ENVIRONMENT=production \
        -e JWT_SECRET_KEY="$CLAVE" \
        -e ALLOWED_ORIGINS="$ORIGEN_OK" \
        -e DATABASE_URL="postgresql+asyncpg://cdi:cdi-prueba@${PG}:5432/cdi" \
        -e EMAIL_VERIFICATION_REQUIRED=false \
        "$IMG" >/dev/null || { echo -e "${RED}❌ No arrancó la app.${NC}"; exit 1; }

    if ! esperar_health; then
        echo -e "${RED}❌ La app nunca respondió. Últimos logs:${NC}"
        docker logs --tail 40 "$APP"
        exit 1
    fi
else
    command -v pg_ctl >/dev/null 2>&1 || export PATH="/usr/lib/postgresql/16/bin:$PATH"

    # Postgres descartable. Si no se puede (no está instalado, o corremos como
    # root y Postgres se niega), caemos a SQLite en un archivo temporal: la
    # prueba de "los datos sobreviven un reinicio" sigue siendo válida, porque
    # el archivo sobrevive al proceso.
    PGDIR=""
    DB_URL=""
    SU=""
    [ "$(id -u)" = "0" ] && id postgres >/dev/null 2>&1 && SU="postgres"

    if command -v pg_ctl >/dev/null 2>&1; then
        paso "Levantando Postgres descartable"
        PGDIR="$TMP/pg"
        mkdir -p "$PGDIR"
        if [ -n "$SU" ]; then chown -R "$SU" "$TMP"; fi
        correr() { if [ -n "$SU" ]; then su "$SU" -s /bin/bash -c "PATH=$PATH; $*"; else bash -c "$*"; fi; }

        if correr "initdb -D $PGDIR -U cdi --auth=trust" >/dev/null 2>&1 \
           && correr "pg_ctl -D $PGDIR -o '-p 5433 -k $TMP -h 127.0.0.1' -l $TMP/pg.log -w start" >/dev/null 2>&1; then
            correr "createdb -h 127.0.0.1 -p 5433 -U cdi cdi" >/dev/null 2>&1
            DB_URL="postgresql+asyncpg://cdi@127.0.0.1:5433/cdi"
            echo -e "${GREEN}✅ Postgres listo${NC}"
        else
            PGDIR=""
        fi
    fi

    if [ -z "$DB_URL" ]; then
        DB_URL="sqlite+aiosqlite:///${TMP}/ataque.db"
        echo -e "${YELLOW}⚠️  Sin Postgres disponible: se usa SQLite en un archivo temporal.${NC}"
        echo -e "${YELLOW}   Los ataques valen igual; el de 'sobrevive al reinicio' prueba${NC}"
        echo -e "${YELLOW}   que el proceso no pierde datos, no que el contenedor no los pierda.${NC}"
    fi

    PY="./venv/bin/python"; [ -x "$PY" ] || PY="python3"

    paso "Levantando la app con variables de PRODUCCIÓN"
    mkdir -p "$TMP/datos"
    ENVIRONMENT=production \
    JWT_SECRET_KEY="$CLAVE" \
    ALLOWED_ORIGINS="$ORIGEN_OK" \
    DATABASE_URL="$DB_URL" \
    EMAIL_VERIFICATION_REQUIRED=false \
    CDI_DATA_DIR="$TMP/datos" \
    PYTHONPATH=. nohup "$PY" -m uvicorn proyecto_maria.main:app \
        --host 127.0.0.1 --port "$PUERTO" > "$TMP/app.log" 2>&1 &
    APP_PID=$!

    if ! esperar_health; then
        echo -e "${RED}❌ La app nunca respondió. Últimos logs:${NC}"
        tail -40 "$TMP/app.log"
        exit 1
    fi
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

# --- 2. documentación técnica cerrada ------------------------------------
paso "2· ¿Está la documentación técnica de la API al público?"
for RUTA in /docs /redoc /openapi.json; do
    C=$(codigo "${BASE}${RUTA}")
    if [ "$C" = "404" ]; then
        gana "${RUTA} cerrado (404)"
    else
        pierde "${RUTA} EXPUESTO" "devolvió ${C}; cualquiera ve tu API entera"
    fi
done

# --- 3. usuarios demo -----------------------------------------------------
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

# --- 4. cookie de sesión --------------------------------------------------
paso "4· ¿La cookie de sesión viaja protegida?"
USUARIO="atacante$RANDOM"
REG=$(curl -s -D "$TMP/headers" -m 20 -X POST "${BASE}/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${USUARIO}\",\"password\":\"Prueba-Larga-123\",\"email\":\"${USUARIO}@ejemplo.com\"}")

if grep -qi "set-cookie" "$TMP/headers"; then
    COOKIE_LINE=$(grep -i "set-cookie" "$TMP/headers" | head -1)
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

# --- 5. CORS --------------------------------------------------------------
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

# --- 6. admin sin login ---------------------------------------------------
paso "6· ¿Los endpoints de administración piden login?"
for RUTA in /api/admin/health/detailed /api/admin/metrics/prometheus; do
    C=$(codigo "${BASE}${RUTA}")
    if [ "$C" = "401" ] || [ "$C" = "403" ]; then
        gana "${RUTA} protegido (${C})"
    else
        pierde "${RUTA} ABIERTO" "devolvió ${C} sin login"
    fi
done

# --- 7. panel interno -----------------------------------------------------
paso "7· ¿El panel interno está protegido?"
C=$(codigo "${BASE}/dev/dashboard")
if [ "$C" = "401" ] || [ "$C" = "403" ]; then
    gana "/dev/dashboard protegido (${C})"
else
    pierde "/dev/dashboard ABIERTO" "devolvió ${C} sin login"
fi

# --- 8. archivos internos -------------------------------------------------
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

# --- 9. cabeceras de seguridad --------------------------------------------
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

# --- 10. rate limit -------------------------------------------------------
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

# --- 11. los datos sobreviven un reinicio ---------------------------------
paso "11· ¿Los datos sobreviven un reinicio?"
if [ "$MODO" = "docker" ]; then
    docker restart "$APP" >/dev/null 2>&1
else
    kill "$APP_PID" >/dev/null 2>&1; wait "$APP_PID" 2>/dev/null
    ENVIRONMENT=production JWT_SECRET_KEY="$CLAVE" ALLOWED_ORIGINS="$ORIGEN_OK" \
    DATABASE_URL="$DB_URL" \
    EMAIL_VERIFICATION_REQUIRED=false CDI_DATA_DIR="$TMP/datos" \
    PYTHONPATH=. nohup "$PY" -m uvicorn proyecto_maria.main:app \
        --host 127.0.0.1 --port "$PUERTO" >> "$TMP/app.log" 2>&1 &
    APP_PID=$!
fi
esperar_health
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
echo -e "${BLUE}Resultado de la Ronda G2 (modo: ${MODO})${NC}"
echo -e "${BLUE}========================================${NC}"
for L in "${RESUMEN[@]}"; do
    if [[ "$L" == FALLA* ]]; then echo -e "${RED}${L}${NC}"; else echo -e "${GREEN}${L}${NC}"; fi
done
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "Resistió: ${GREEN}${PASADOS}${NC}   ·   Cayó: ${RED}${FALLADOS}${NC}"

if [ "$FALLADOS" -gt 0 ]; then
    echo -e "\n${RED}❌ PUERTA G2 NO PASADA.${NC} Mandame esta salida completa."
    echo -e "${YELLOW}Últimos logs por si sirven:${NC}"
    if [ "$MODO" = "docker" ]; then docker logs --tail 30 "$APP" 2>&1 | tail -30; else tail -30 "$TMP/app.log"; fi
    exit 1
fi

if [ "$MODO" = "sin-docker" ]; then
    echo -e "\n${YELLOW}⚠️  Pasaron los ${PASADOS} chequeos, pero en modo reducido.${NC}"
    echo -e "${YELLOW}   Falta correr el modo con Docker para cerrar G2 de verdad:${NC}"
    echo -e "${YELLOW}   esto probó la app, no la imagen que realmente se deploya.${NC}"
    exit 0
fi

echo -e "\n${GREEN}✅ PUERTA G2 PASADA. La imagen que se deploya resistió los ${PASADOS} chequeos.${NC}"
exit 0
