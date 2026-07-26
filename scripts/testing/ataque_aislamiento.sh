#!/usr/bin/env bash
# ========================================================================
# Ronda G3 del plan adversarial: ¿un despachante puede ver datos de otro?
# ========================================================================
#
# QUÉ HACE (no hay que saber programar para usarlo):
#
#   1. Levanta la app con configuración de producción y una base descartable.
#   2. Crea dos despachantes distintos: Ana y Beto.
#   3. Ana carga un cliente con CUIT y genera su archivo MARIA.TXT.
#   4. Beto intenta ver, modificar, borrar y descargar todo lo de Ana.
#   5. Dice qué pudo y qué no, y borra todo.
#
# CÓMO USARLO:
#
#   ./scripts/testing/ataque_aislamiento.sh
#
# Cada "CAYÓ" es una fuga de datos entre clientes: lo peor que le puede
# pasar a este producto. No toca ninguna base real ni usa internet.
# ========================================================================

set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

PUERTO="${PUERTO:-8098}"
BASE="http://127.0.0.1:${PUERTO}"
TMP=$(mktemp -d)
APP_PID=""
PGDIR=""

PASADOS=0
FALLADOS=0
declare -a RESUMEN=()

paso()   { echo -e "\n${BLUE}▶ $*${NC}"; }
gana()   { echo -e "  ${GREEN}✅ BLOQUEADO${NC} · $1"; PASADOS=$((PASADOS+1)); RESUMEN+=("OK    | $1"); }
pierde() { echo -e "  ${RED}❌ FUGA${NC} · $1"; echo -e "     ${YELLOW}↳ $2${NC}"; FALLADOS=$((FALLADOS+1)); RESUMEN+=("FUGA  | $1 → $2"); }

limpiar() {
    echo -e "\n${YELLOW}🧹 Borrando lo que creó la prueba...${NC}"
    [ -n "$APP_PID" ] && kill "$APP_PID" >/dev/null 2>&1
    [ -n "${PGDIR:-}" ] && pg_ctl -D "$PGDIR" -s stop -m immediate >/dev/null 2>&1
    rm -rf "$TMP"
}
trap limpiar EXIT

codigo()  { curl -s -o /dev/null -w '%{http_code}' -m 10 "$@"; }

# El server usa CSRF double-submit: cookie legible `csrf_token` + header
# `X-CSRF-Token`. Lo replicamos como lo hace el frontend legítimo: acá se
# mide AUTORIZACIÓN (¿Beto puede tocar lo de Ana?), no CSRF.
csrf() { grep -i "csrf_token" "$1" 2>/dev/null | awk '{print $NF}' | tail -1; }
esperar_health() { for _ in $(seq 1 45); do [ "$(codigo "${BASE}/health")" = "200" ] && return 0; sleep 2; done; return 1; }

# Un ataque = Beto pide algo de Ana. Tiene que dar 401/403/404, nunca 200.
atacar() {
    local NOMBRE="$1"; shift
    local C BODY
    BODY=$(curl -s -m 10 -w $'\n%{http_code}' -b "$COOKIE_B" -c "$COOKIE_B" \
        -H "X-CSRF-Token: $(csrf "$COOKIE_B")" "$@")
    C=$(echo "$BODY" | tail -1)
    if [ "$C" = "200" ]; then
        pierde "$NOMBRE" "devolvió 200 · $(echo "$BODY" | head -n -1 | tr -d '\n' | head -c 160)"
    else
        gana "$NOMBRE (${C})"
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Ronda G3 · ¿Se filtran datos entre despachantes?${NC}"
echo -e "${BLUE}========================================${NC}"

# ---------------------------------------------------------------- levantar
export PATH="/usr/lib/postgresql/16/bin:$PATH"
CLAVE=$(head -c 48 /dev/urandom | base64 | tr -d '/+=' | head -c 60)
SU=""
[ "$(id -u)" = "0" ] && id postgres >/dev/null 2>&1 && SU="postgres"
DB_URL=""

if command -v pg_ctl >/dev/null 2>&1; then
    paso "Levantando Postgres descartable"
    PGDIR="$TMP/pg"; mkdir -p "$PGDIR"
    [ -n "$SU" ] && chown -R "$SU" "$TMP"
    correr() { if [ -n "$SU" ]; then su "$SU" -s /bin/bash -c "PATH=$PATH; $*"; else bash -c "$*"; fi; }
    if correr "initdb -D $PGDIR -U cdi --auth=trust" >/dev/null 2>&1 \
       && correr "pg_ctl -D $PGDIR -o '-p 5434 -k $TMP -h 127.0.0.1' -l $TMP/pg.log -w start" >/dev/null 2>&1; then
        correr "createdb -h 127.0.0.1 -p 5434 -U cdi cdi" >/dev/null 2>&1
        DB_URL="postgresql+asyncpg://cdi@127.0.0.1:5434/cdi"
        echo -e "${GREEN}✅ Postgres listo${NC}"
    else
        PGDIR=""
    fi
fi
[ -z "$DB_URL" ] && { DB_URL="sqlite+aiosqlite:///${TMP}/aisl.db"; echo -e "${YELLOW}⚠️  Sin Postgres: se usa SQLite temporal.${NC}"; }

PY="./venv/bin/python"; [ -x "$PY" ] || PY="python3"

paso "Levantando la app con configuración de producción"
mkdir -p "$TMP/datos"
ENVIRONMENT=production JWT_SECRET_KEY="$CLAVE" ALLOWED_ORIGINS="https://cdi-prueba.example.com" \
DATABASE_URL="$DB_URL" EMAIL_VERIFICATION_REQUIRED=false CDI_DATA_DIR="$TMP/datos" \
API_RATE_LIMIT="100000/minute" RATE_LIMIT_PREMIUM="100000/minute" \
PYTHONPATH=. nohup "$PY" -m uvicorn proyecto_maria.main:app \
    --host 127.0.0.1 --port "$PUERTO" > "$TMP/app.log" 2>&1 &
APP_PID=$!
esperar_health || { echo -e "${RED}❌ La app no arrancó:${NC}"; tail -30 "$TMP/app.log"; exit 1; }
echo -e "${GREEN}✅ App viva${NC}"

# ------------------------------------------------------- los dos usuarios
ANA="ana$RANDOM"; BETO="beto$RANDOM"
COOKIE_A="$TMP/ana.txt"; COOKIE_B="$TMP/beto.txt"

registrar() {
    curl -s -m 20 -c "$2" -X POST "${BASE}/auth/register" -H 'Content-Type: application/json' \
        -d "{\"username\":\"$1\",\"password\":\"Clave-Larga-Prueba-1\",\"email\":\"$1@ejemplo.com\"}"
}

paso "Creando dos despachantes distintos: ${ANA} y ${BETO}"
registrar "$ANA"  "$COOKIE_A" >/dev/null
registrar "$BETO" "$COOKIE_B" >/dev/null
[ -s "$COOKIE_A" ] && [ -s "$COOKIE_B" ] || { echo -e "${RED}❌ No se pudieron crear los usuarios.${NC}"; tail -20 "$TMP/app.log"; exit 1; }
echo -e "${GREEN}✅ Los dos registrados${NC}"

# --------------------------------------------------- Ana carga sus datos
paso "Ana carga un cliente con CUIT y genera su MARIA.TXT"
CUIT_ANA="30712345678"
CLI=$(curl -s -m 15 -b "$COOKIE_A" -c "$COOKIE_A" -H "X-CSRF-Token: $(csrf "$COOKIE_A")" \
    -X POST "${BASE}/api/clientes" -H 'Content-Type: application/json' \
    -d "{\"nombre\":\"Importadora Privada de Ana SA\",\"cuit\":\"${CUIT_ANA}\",\"email\":\"privado@ana.com\",\"telefono\":\"1155550000\"}")
# El id de cliente es un UUID (que no se puede adivinar: buena señal de por sí).
ID_CLI=$(echo "$CLI" | grep -oE '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}' | head -1)
[ -z "$ID_CLI" ] && ID_CLI=$(echo "$CLI" | grep -oE '"id"[: ]*[0-9]+' | head -1 | grep -oE '[0-9]+$')
if [ -z "$ID_CLI" ]; then
    echo -e "${RED}❌ Ana no pudo crear su cliente: $(echo "$CLI" | head -c 250)${NC}"; exit 1
fi
echo -e "   Cliente de Ana: id=${ID_CLI}, CUIT=${CUIT_ANA}"

# Nro de factura corto y adivinable, como los reales.
FACTURA="0001-00012345"
OP_ID="FAC_${FACTURA}"
GEN=$(curl -s -m 20 -b "$COOKIE_A" -c "$COOKIE_A" -H "X-CSRF-Token: $(csrf "$COOKIE_A")" \
    -X POST "${BASE}/generate_maria" -H 'Content-Type: application/json' \
    -d "{\"operation_id\":\"${OP_ID}\",\"comprador_nombre\":\"Importadora Privada de Ana SA\",\"comprador_cuit\":\"${CUIT_ANA}\",\"sbt_sufijo_valor\":\"01\",\"items\":[{\"pieza\":\"1\",\"descripcion\":\"MERCADERIA CONFIDENCIAL DE ANA\",\"ncm\":\"84713000900R\",\"cantidad\":10,\"valor_unitario\":100,\"peso_kg\":5,\"origen\":\"310\",\"unidad\":\"01\"}]}")
ARCHIVO=$(echo "$GEN" | grep -oE '"filename"[: ]*"[^"]+"' | head -1 | sed 's/.*"filename"[: ]*"//;s/"//')
if [ -n "$ARCHIVO" ]; then
    echo -e "   MARIA.TXT de Ana: ${ARCHIVO}"
else
    echo -e "${YELLOW}   (no se generó TXT: $(echo "$GEN" | head -c 200))${NC}"
fi

# ======================================================================
#                  BETO ATACA LOS DATOS DE ANA
# ======================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Beto intenta acceder a lo de Ana${NC}"
echo -e "${BLUE}========================================${NC}"

paso "1· Leer la ficha del cliente de Ana"
atacar "Ver cliente de Ana por ID"          "${BASE}/api/clientes/${ID_CLI}"
BYCUIT=$(curl -s -m 10 -b "$COOKIE_B" "${BASE}/api/clientes/by-cuit/${CUIT_ANA}")
if echo "$BYCUIT" | grep -qE "Importadora Privada de Ana|privado@ana.com|1155550000"; then
    pierde "Buscar el cliente de Ana por CUIT" "devolvió sus datos: $(echo "$BYCUIT" | head -c 160)"
else
    gana "Buscar el cliente de Ana por CUIT (sin datos: $(echo "$BYCUIT" | head -c 60))"
fi

paso "2· Leer la actividad del cliente de Ana"
atacar "Ver operaciones de Ana"   "${BASE}/api/clientes/${ID_CLI}/operaciones"
atacar "Ver métricas de Ana"      "${BASE}/api/clientes/${ID_CLI}/metricas"
atacar "Exportar CSV de Ana"      "${BASE}/api/clientes/${ID_CLI}/export.csv"
atacar "Ver catálogo de Ana"      "${BASE}/api/clientes/${ID_CLI}/catalogo/productos"
atacar "Ver plantilla de Ana"     "${BASE}/api/clientes/${ID_CLI}/plantilla"
atacar "Ver mapeo de columnas"    "${BASE}/api/clientes/${ID_CLI}/column_mapping"

paso "3· Modificar o borrar datos de Ana"
atacar "Modificar el cliente de Ana" -X PUT "${BASE}/api/clientes/${ID_CLI}" \
    -H 'Content-Type: application/json' -d '{"nombre":"HACKEADO POR BETO"}'
atacar "Marcar favorito el cliente de Ana" -X POST "${BASE}/api/clientes/${ID_CLI}/favorito" \
    -H 'Content-Type: application/json' -d '{}'
atacar "Cargar una operación en el cliente de Ana" -X POST "${BASE}/api/clientes/${ID_CLI}/operaciones" \
    -H 'Content-Type: application/json' -d '{"items":[],"numero_factura":"INTRUSO"}'
atacar "Borrar el cliente de Ana" -X DELETE "${BASE}/api/clientes/${ID_CLI}"

paso "4· Descargar el MARIA.TXT de Ana (adivinando el nro de factura)"
if [ -n "$ARCHIVO" ]; then
    RESP=$(curl -s -m 10 -w $'\n%{http_code}' -b "$COOKIE_B" "${BASE}/download/${ARCHIVO}")
    C=$(echo "$RESP" | tail -1)
    if [ "$C" = "200" ]; then
        pierde "Descargar el MARIA.TXT de Ana" "bajó la declaración completa; contiene: $(echo "$RESP" | grep -o 'MERCADERIA CONFIDENCIAL DE ANA' | head -1)$(echo "$RESP" | grep -o "$CUIT_ANA" | head -1)"
    else
        gana "Descargar el MARIA.TXT de Ana (${C})"
    fi
else
    echo -e "${YELLOW}  (salteado: Ana no llegó a generar el TXT)${NC}"
fi

paso "4.bis· ¿Ana sigue pudiendo bajar SU propio archivo?"
if [ -n "$ARCHIVO" ]; then
    PROPIO=$(curl -s -m 10 -w $'\n%{http_code}' -b "$COOKIE_A" "${BASE}/download/${ARCHIVO}")
    C=$(echo "$PROPIO" | tail -1)
    if [ "$C" = "200" ] && echo "$PROPIO" | grep -q "$CUIT_ANA"; then
        gana "Ana baja su propio MARIA.TXT (200, con su contenido)"
    else
        pierde "Ana NO puede bajar su propio archivo" "devolvió ${C} - el arreglo rompió la función"
    fi
fi

paso "5· ¿El listado de Beto muestra clientes de Ana?"
LISTA=$(curl -s -m 10 -b "$COOKIE_B" "${BASE}/api/clientes")
if echo "$LISTA" | grep -q "Importadora Privada de Ana"; then
    pierde "Listado de clientes contaminado" "Beto ve el cliente de Ana en su propia lista"
else
    gana "El listado de Beto sólo tiene lo suyo"
fi

paso "6· ¿La búsqueda de Beto encuentra clientes de Ana?"
BUSCA=$(curl -s -m 10 -b "$COOKIE_B" "${BASE}/api/clientes/search?q=Ana")
if echo "$BUSCA" | grep -q "Importadora Privada de Ana"; then
    pierde "Buscador contaminado" "Beto encuentra el cliente de Ana buscando"
else
    gana "El buscador de Beto no ve lo de Ana"
fi

paso "7· Sin estar logueado, ¿se puede algo?"
for RUTA in "/api/clientes" "/api/clientes/${ID_CLI}" "/api/clientes/by-cuit/${CUIT_ANA}" "/api/clientes/${ID_CLI}/export.csv"; do
    C=$(codigo "${BASE}${RUTA}")
    if [ "$C" = "401" ] || [ "$C" = "403" ]; then
        gana "Sin login ${RUTA} (${C})"
    else
        pierde "Sin login ${RUTA} ABIERTO" "devolvió ${C}"
    fi
done
if [ -n "$ARCHIVO" ]; then
    C=$(codigo "${BASE}/download/${ARCHIVO}")
    if [ "$C" = "401" ] || [ "$C" = "403" ]; then
        gana "Sin login no se baja el TXT (${C})"
    else
        pierde "Sin login se baja el TXT" "devolvió ${C}"
    fi
fi

paso "8· ¿Sigue vivo el cliente de Ana después de todo esto?"
VERIF=$(curl -s -m 10 -b "$COOKIE_A" "${BASE}/api/clientes/${ID_CLI}")
if echo "$VERIF" | grep -q "Importadora Privada de Ana"; then
    gana "Los datos de Ana quedaron intactos"
elif echo "$VERIF" | grep -q "HACKEADO POR BETO"; then
    pierde "Beto modificó los datos de Ana" "el nombre del cliente quedó cambiado"
else
    pierde "El cliente de Ana ya no está" "respuesta: $(echo "$VERIF" | head -c 160)"
fi

# ======================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Resultado de la Ronda G3${NC}"
echo -e "${BLUE}========================================${NC}"
for L in "${RESUMEN[@]}"; do
    if [[ "$L" == FUGA* ]]; then echo -e "${RED}${L}${NC}"; else echo -e "${GREEN}${L}${NC}"; fi
done
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "Bloqueado: ${GREEN}${PASADOS}${NC}   ·   Fugas: ${RED}${FALLADOS}${NC}"

if [ "$FALLADOS" -gt 0 ]; then
    echo -e "\n${RED}❌ PUERTA G3 NO PASADA: hay ${FALLADOS} fuga(s) entre despachantes.${NC}"
    exit 1
fi
echo -e "\n${GREEN}✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.${NC}"
exit 0
