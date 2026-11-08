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
#   4. Beto intenta ver, modificar, borrar y descargar todo lo de Ana:
#      clientes, el TXT, operaciones, presupuestos, notas NCM y estudios.
#   5. Dos estudios con cuenta compartida: uno no ve ni toca al otro.
#   6. Un despachante común no entra a lo de administrador.
#   7. Dice qué pudo y qué no, y borra todo.
#
# CÓMO USARLO:
#
#   ./scripts/testing/ataque_aislamiento.sh
#
# Cada "FUGA" es una fuga de datos entre clientes: lo peor que le puede
# pasar a este producto. Cada "SIN PROBAR" es un caso que no llegó a medir
# (faltó lo de Ana, o la app contestó otra cosa que la esperada): la puerta
# tampoco pasa. No toca ninguna base real ni usa internet.
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
DUDOSOS=0
declare -a RESUMEN=()

paso()   { echo -e "\n${BLUE}▶ $*${NC}"; }
gana()   { echo -e "  ${GREEN}✅ BLOQUEADO${NC} · $1"; PASADOS=$((PASADOS+1)); RESUMEN+=("OK    | $1"); }
pierde() { echo -e "  ${RED}❌ FUGA${NC} · $1"; echo -e "     ${YELLOW}↳ $2${NC}"; FALLADOS=$((FALLADOS+1)); RESUMEN+=("FUGA  | $1 → $2"); }
duda()   { echo -e "  ${YELLOW}⚠️  SIN PROBAR${NC} · $1"; echo -e "     ${YELLOW}↳ $2${NC}"; DUDOSOS=$((DUDOSOS+1)); RESUMEN+=("DUDA  | $1 → $2"); }

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
# Un tercer usuario es administrador, para comprobar que las rutas de admin
# existen y que el 403 de Beto es por no serlo. El dólar apunta a un puerto
# cerrado: el presupuesto usa su valor de reserva sin salir a internet.
# FRONTEND_URL: en producción el link de invitación la exige.
JEFE="jefe$RANDOM"
ENVIRONMENT=production JWT_SECRET_KEY="$CLAVE" ALLOWED_ORIGINS="https://cdi-prueba.example.com" \
FRONTEND_URL="https://cdi-prueba.example.com" \
DATABASE_URL="$DB_URL" EMAIL_VERIFICATION_REQUIRED=false CDI_DATA_DIR="$TMP/datos" \
API_RATE_LIMIT="100000/minute" RATE_LIMIT_PREMIUM="100000/minute" ADMIN_USERNAMES="$JEFE" \
DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares" \
PYTHONPATH=. nohup "$PY" -m uvicorn proyecto_maria.main:app \
    --host 127.0.0.1 --port "$PUERTO" > "$TMP/app.log" 2>&1 &
APP_PID=$!
esperar_health || { echo -e "${RED}❌ La app no arrancó:${NC}"; tail -30 "$TMP/app.log"; exit 1; }
echo -e "${GREEN}✅ App viva${NC}"

# ------------------------------------------------------- los dos usuarios
ANA="ana$RANDOM"; BETO="beto$RANDOM"
COOKIE_A="$TMP/ana.txt"; COOKIE_B="$TMP/beto.txt"

# registrar USUARIO COOKIE [TOKEN DE INVITACIÓN]
registrar() {
    local INV=""; [ -n "${3:-}" ] && INV=",\"invite_token\":\"$3\""
    curl -s -m 20 -c "$2" -X POST "${BASE}/auth/register" -H 'Content-Type: application/json' \
        -d "{\"username\":\"$1\",\"password\":\"Clave-Larga-Prueba-1\",\"email\":\"$1@ejemplo.com\"${INV}}"
}

paso "Creando dos despachantes distintos: ${ANA} y ${BETO}"
registrar "$ANA"  "$COOKIE_A" >/dev/null
registrar "$BETO" "$COOKIE_B" >/dev/null
[ -s "$COOKIE_A" ] && [ -s "$COOKIE_B" ] || { echo -e "${RED}❌ No se pudieron crear los usuarios.${NC}"; tail -20 "$TMP/app.log"; exit 1; }
echo -e "${GREEN}✅ Los dos registrados${NC}"

# --------------------------------------------------- Ana carga sus datos
paso "Ana carga un cliente con CUIT y genera su MARIA.TXT"
CUIT_ANA="30712345671"  # inventado, con dígito verificador válido (MARIA-1b lo exige al generar)
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
    -d "{\"operation_id\":\"${OP_ID}\",\"comprador_nombre\":\"Importadora Privada de Ana SA\",\"comprador_cuit\":\"${CUIT_ANA}\",\"moneda\":\"DOL\",\"incoterm\":\"FOB\",\"fecha_emision\":\"18/07/2025\",\"sbt_sufijo_valor\":\"AA(DEMO)-AB(DEMO)-CA00-\",\"cuit_agr\":\"20111111112\",\"items\":[{\"pieza\":\"1\",\"descripcion\":\"MERCADERIA CONFIDENCIAL DE ANA\",\"ncm\":\"84713000900R\",\"cantidad\":10,\"valor_unitario\":100,\"peso_kg\":5,\"origen\":\"310\",\"unidad\":\"01\"}]}")
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
#   AISLAMIENTO-2: operaciones, presupuestos, notas, estudios y admin
# ======================================================================
# Cada caso comprueba antes que Ana tiene lo suyo, y espera un código
# concreto: un 500 o un 503 también frenan a Beto, pero por la razón
# equivocada, y entonces el caso queda SIN PROBAR (la puerta no pasa).

# pedir COOKIE args...: el cuerpo y, en la última línea, el código.
pedir()  { local CK="$1"; shift; curl -s -m 20 -w $'\n%{http_code}' -b "$CK" -c "$CK" -H "X-CSRF-Token: $(csrf "$CK")" "$@"; }
cuerpo() { echo "$1" | head -n -1; }
cod()    { echo "$1" | tail -1; }
resumir() { cuerpo "$1" | tr -d '\n' | head -c 160; }

# atacar_como COOKIE NOMBRE CÓDIGO args...: un 2xx es fuga; el código esperado
# es bloqueo; cualquier otro, sin probar.
atacar_como() {
    local CK="$1" NOMBRE="$2" ESPERA="$3"; shift 3
    local R C; R=$(pedir "$CK" "$@"); C=$(cod "$R")
    if [[ "$C" == 2?? ]]; then pierde "$NOMBRE" "devolvió $C · $(resumir "$R")"
    elif [ "$C" = "$ESPERA" ]; then gana "$NOMBRE ($C)"
    else duda "$NOMBRE" "devolvió $C y se esperaba $ESPERA · $(resumir "$R")"; fi
}

# no_ve NOMBRE RESPUESTA TEXTO...: la respuesta (200) no tiene ninguno.
no_ve() {
    local NOMBRE="$1" R="$2" P; shift 2
    if [ "$(cod "$R")" != "200" ]; then duda "$NOMBRE" "devolvió $(cod "$R"): no se pudo mirar"; return; fi
    for P in "$@"; do
        if cuerpo "$R" | grep -qF -- "$P"; then pierde "$NOMBRE" "aparece «$P»"; return; fi
    done
    gana "$NOMBRE"
}

# sigue NOMBRE RESPUESTA TEXTO: lo de Ana sigue ahí después de los ataques.
sigue() {
    if [ "$(cod "$2")" = "200" ] && cuerpo "$2" | grep -qF -- "$3"; then gana "$1"
    else pierde "$1" "ya no está «$3» · $(cod "$2") $(resumir "$2")"; fi
}

# Los ids de los ítems de una operación no salen por ninguna API: se leen de
# la base. Se mide autorización suponiendo que Beto los conoce.
sql() {
    if [ -n "$PGDIR" ]; then
        psql -h 127.0.0.1 -p 5434 -U cdi -d cdi -tAc "$1"
    else
        "$PY" -c 'import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
for r in con.execute(sys.argv[2]).fetchall():
    print("|".join("" if v is None else str(v) for v in r))
con.commit()' "$TMP/aisl.db" "$1"
    fi
}

json() { "$PY" -c 'import json, sys
d = json.loads(sys.stdin.read() or "null")
for k in sys.argv[1].split("."):
    d = d.get(k) if isinstance(d, dict) else None
print("" if d is None else d)' "$1" 2>/dev/null; }

operaciones() {
    paso "9· Operaciones de Ana: verlas, cambiarles el estado, agruparlas"
    local R OP ITEMS I1 I2 G ANTES
    R=$(pedir "$COOKIE_A" -X POST "${BASE}/api/operations/manual" -H 'Content-Type: application/json' \
        -d "{\"client_id\":\"${ID_CLI}\",\"items\":[{\"descripcion\":\"REPUESTO PRIVADO DE ANA\",\"cantidad\":2,\"valor_unitario\":50,\"pieza\":\"84713000900R\",\"origen\":\"310\",\"unidad\":\"01\",\"peso_unitario\":1},{\"descripcion\":\"REPUESTO PRIVADO DE ANA 2\",\"cantidad\":3,\"valor_unitario\":40,\"pieza\":\"84713000900R\",\"origen\":\"310\",\"unidad\":\"01\",\"peso_unitario\":1}]}")
    OP=$(cuerpo "$R" | json operation_id)
    [ -n "$OP" ] || { duda "Operaciones" "Ana no pudo crear su operación: $(cod "$R") $(resumir "$R")"; return; }
    OP_ANA="$OP"
    ITEMS=$(sql "select id from operation_items where operation_id='${OP}' order by id")
    I1=$(echo "$ITEMS" | sed -n 1p); I2=$(echo "$ITEMS" | sed -n 2p)
    [ -n "$I1" ] && [ -n "$I2" ] || { duda "Operaciones" "no se leyeron los ítems de Ana en la base"; return; }
    R=$(pedir "$COOKIE_A" -X POST "${BASE}/api/operacion/${OP}/agrupar" -H 'Content-Type: application/json' \
        -d "{\"item_ids\":[\"${I1}\",\"${I2}\"]}")
    G=$(cuerpo "$R" | json grupo_id)
    [ -n "$G" ] || { duda "Operaciones" "Ana no pudo agrupar sus ítems: $(cod "$R") $(resumir "$R")"; return; }
    R=$(pedir "$COOKIE_A" "${BASE}/api/operations")
    cuerpo "$R" | grep -qF "$OP" || { duda "Operaciones" "Ana no ve su operación en su listado"; return; }
    ANTES=$(sql "select coalesce(estado,'') || '|' || coalesce(canal,'') from operations where id='${OP}'")

    no_ve "El listado de operaciones de Beto no tiene las de Ana" "$(pedir "$COOKIE_B" "${BASE}/api/operations")" \
        "$OP" "Importadora Privada de Ana"
    atacar_como "$COOKIE_B" "Cambiar el estado de la operación de Ana" 404 -X PATCH "${BASE}/api/operations/${OP}/estado" \
        -H 'Content-Type: application/json' -d '{"estado":"liberada","canal":"rojo"}'
    atacar_como "$COOKIE_B" "Agrupar los ítems de Ana" 404 -X POST "${BASE}/api/operacion/${OP}/agrupar" \
        -H 'Content-Type: application/json' -d "{\"item_ids\":[\"${I1}\",\"${I2}\"]}"
    atacar_como "$COOKIE_B" "Desagrupar los ítems de Ana" 404 -X POST "${BASE}/api/operacion/${OP}/desagrupar" \
        -H 'Content-Type: application/json' -d "{\"grupo_id\":${G}}"

    if [ "$(sql "select coalesce(estado,'') || '|' || coalesce(canal,'') from operations where id='${OP}'")" = "$ANTES" ]; then
        gana "El estado de la operación de Ana quedó como estaba"
    else
        pierde "Beto cambió el estado de la operación de Ana" "quedó $(sql "select estado, canal from operations where id='${OP}'")"
    fi
    if [ "$(sql "select count(*) from operation_items where operation_id='${OP}' and grupo_id=${G}")" = "2" ]; then
        gana "Los ítems de Ana siguen en su grupo"
    else
        pierde "Beto tocó el grupo de Ana" "grupos: $(sql "select grupo_id from operation_items where operation_id='${OP}'" | tr '\n' ' ')"
    fi
}

presupuestos() {
    paso "10· Compartir el presupuesto de una operación de Ana"
    [ -n "${OP_ANA:-}" ] || { duda "Presupuestos" "Ana no tiene operación (falló el paso 9)"; return; }
    # Sin internet el cálculo de aranceles da 503 en producción: pasar el control
    # de dueño es llegar al cálculo (200 o 503); no pasarlo, un 404 antes.
    local R CA CB
    R=$(pedir "$COOKIE_A" -X POST "${BASE}/api/quotes/share" -H 'Content-Type: application/json' -d "{\"operation_id\":\"${OP_ANA}\"}")
    CA=$(cod "$R")
    if ! { [ "$CA" = "200" ] || { [ "$CA" = "503" ] && cuerpo "$R" | grep -qF tarifar_unavailable; }; }; then
        duda "Presupuestos" "Ana no llega a calcular el suyo: $CA $(resumir "$R")"; return
    fi
    R=$(pedir "$COOKIE_B" -X POST "${BASE}/api/quotes/share" -H 'Content-Type: application/json' -d "{\"operation_id\":\"${OP_ANA}\"}")
    CB=$(cod "$R")
    if [ "$CB" = "404" ]; then gana "Compartir el presupuesto de la operación de Ana (404)"
    elif [ "$CB" = "$CA" ]; then pierde "Compartir el presupuesto de la operación de Ana" "Beto llegó al cálculo como Ana: $CB · $(resumir "$R")"
    else duda "Compartir el presupuesto de la operación de Ana" "devolvió $CB y se esperaba 404 · $(resumir "$R")"; fi
}

notas() {
    paso "11· Notas NCM de Ana: verlas, cambiarlas, borrarlas"
    local R
    R=$(pedir "$COOKIE_A" -X POST "${BASE}/api/ncm/notas" -H 'Content-Type: application/json' \
        -d '{"ncm":"84713000","nota":"NOTA PRIVADA DE ANA"}')
    [ "$(cod "$R")" = "200" ] || { duda "Notas" "Ana no pudo guardar su nota: $(cod "$R") $(resumir "$R")"; return; }
    cuerpo "$(pedir "$COOKIE_A" "${BASE}/api/ncm/notas/8471")" | grep -qF "NOTA PRIVADA DE ANA" \
        || { duda "Notas" "Ana no ve su propia nota"; return; }

    no_ve "Beto no ve la nota de Ana" "$(pedir "$COOKIE_B" "${BASE}/api/ncm/notas/8471")" "NOTA PRIVADA DE ANA"
    atacar_como "$COOKIE_B" "Cambiar la nota de Ana" 404 -X PUT "${BASE}/api/ncm/notas/8471/0" \
        -H 'Content-Type: application/json' -d '{"nota":"HACKEADO POR BETO"}'
    atacar_como "$COOKIE_B" "Borrar la nota de Ana" 404 -X DELETE "${BASE}/api/ncm/notas/8471/0"
    sigue "La nota de Ana quedó intacta" "$(pedir "$COOKIE_A" "${BASE}/api/ncm/notas/8471")" "NOTA PRIVADA DE ANA"
}

estudios() {
    paso "12· Estudio (CUIT de despachante) de Ana: verlo, borrarlo, usarlo"
    local R EST
    R=$(pedir "$COOKIE_A" -X POST "${BASE}/api/estudios" -H 'Content-Type: application/json' \
        -d '{"nombre":"Estudio Privado de Ana","cuit":"20111111112"}')
    EST=$(cuerpo "$R" | json estudio.id)
    [ -n "$EST" ] || { duda "Estudios" "Ana no pudo cargar su estudio: $(cod "$R") $(resumir "$R")"; return; }

    no_ve "Beto no ve el estudio de Ana" "$(pedir "$COOKIE_B" "${BASE}/api/estudios")" "$EST" "Estudio Privado de Ana"
    atacar_como "$COOKIE_B" "Borrar el estudio de Ana" 404 -X DELETE "${BASE}/api/estudios/${EST}"
    # Generar con el estudio de Ana: el TXT de Beto saldría con el CUIT de Ana.
    R=$(pedir "$COOKIE_B" -X POST "${BASE}/generate_maria" -H 'Content-Type: application/json' \
        -d "{\"operation_id\":\"FAC_0001-00099999\",\"estudio_id\":\"${EST}\",\"comprador_nombre\":\"Importadora de Beto SA\",\"comprador_cuit\":\"${CUIT_ANA}\",\"moneda\":\"DOL\",\"incoterm\":\"FOB\",\"fecha_emision\":\"18/07/2025\",\"sbt_sufijo_valor\":\"AA(DEMO)-AB(DEMO)-CA00-\",\"items\":[{\"pieza\":\"1\",\"descripcion\":\"MERCADERIA DE BETO\",\"ncm\":\"84713000900R\",\"cantidad\":1,\"valor_unitario\":100,\"peso_kg\":1,\"origen\":\"310\",\"unidad\":\"01\"}]}")
    if [[ "$(cod "$R")" == 2?? ]]; then
        pierde "Generar un TXT con el estudio de Ana" "devolvió $(cod "$R") · $(resumir "$R")"
    elif [ "$(cod "$R")" = "400" ] && cuerpo "$R" | grep -qF "no está en tu cuenta"; then
        gana "Generar un TXT con el estudio de Ana (400, no está en su cuenta)"
    else
        duda "Generar un TXT con el estudio de Ana" "devolvió $(cod "$R") por otra razón · $(resumir "$R")"
    fi
    sigue "El estudio de Ana quedó intacto" "$(pedir "$COOKIE_A" "${BASE}/api/estudios")" "$EST"
}

organizaciones() {
    paso "13· Dos estudios con cuenta compartida: uno no ve ni toca al otro"
    local OA="orga$RANDOM" OB="orgb$RANDOM" MIE="miem$RANDOM" MIE2="miem$RANDOM"
    local CK_OA="$TMP/orga.txt" CK_OB="$TMP/orgb.txt" CK_M="$TMP/miem.txt" CK_M2="$TMP/miem2.txt"
    crear_org() {
        curl -s -m 20 -c "$3" -X POST "${BASE}/api/organizations/create" -H 'Content-Type: application/json' \
            -d "{\"name\":\"$2\",\"username\":\"$1\",\"password\":\"Clave-Larga-Prueba-1\",\"email\":\"$1@ejemplo.com\"}"
    }
    # sumar_miembro USUARIO COOKIE: el estudio A lo invita y se registra con el token.
    sumar_miembro() {
        local R TOK
        R=$(pedir "$CK_OA" -X POST "${BASE}/api/organizations/invite" -H 'Content-Type: application/json' -d "{\"email\":\"$1@ejemplo.com\"}")
        TOK=$(cuerpo "$R" | json invite_link | sed 's/.*invite=//')
        [ -n "$TOK" ] || { duda "Organizaciones" "el estudio A no pudo invitar: $(cod "$R") $(resumir "$R")"; return 1; }
        registrar "$1" "$2" "$TOK" >/dev/null
        # En Postgres registrarse con la invitación da 500 (C7 de la auditoría,
        # la arregla ORG-1). Esto mide aislamiento, no la invitación: si no
        # entró, se registra sin token y se vincula al estudio A como lo haría
        # el registro (sólo pone organization_id).
        if ! cuerpo "$(pedir "$CK_OA" "${BASE}/api/organizations/mine")" | grep -qF "\"$1\""; then
            echo -e "  ${YELLOW}AVISO: el registro con invitación no vinculó a $1 (C7); se vincula por SQL${NC}"
            registrar "$1" "$2" >/dev/null
            sql "update users set organization_id=(select organization_id from users where username='$OA') where username='$1'" >/dev/null
        fi
        cuerpo "$(pedir "$CK_OA" "${BASE}/api/organizations/mine")" | grep -qF "\"$1\"" \
            || { duda "Organizaciones" "$1 no quedó en el estudio A"; return 1; }
    }
    [ -n "$(crear_org "$OA" "Estudio Org de Ana" "$CK_OA" | json org_id)" ] \
        || { duda "Organizaciones" "no se pudo crear el estudio A"; return; }
    [ -n "$(crear_org "$OB" "Estudio Org de Beto" "$CK_OB" | json org_id)" ] \
        || { duda "Organizaciones" "no se pudo crear el estudio B"; return; }
    sumar_miembro "$MIE" "$CK_M" && sumar_miembro "$MIE2" "$CK_M2" || return

    no_ve "El estudio B no ve al estudio A ni a sus miembros" "$(pedir "$CK_OB" "${BASE}/api/organizations/mine")" \
        "Estudio Org de Ana" "\"$MIE\"" "\"$OA\""
    atacar_como "$CK_OB" "El estudio B saca a un miembro del estudio A" 404 -X DELETE "${BASE}/api/organizations/members/${MIE}"
    atacar_como "$CK_M" "Un miembro (no administrador) saca a otro miembro de su estudio" 403 -X DELETE "${BASE}/api/organizations/members/${MIE2}"
    local MINE; MINE=$(pedir "$CK_OA" "${BASE}/api/organizations/mine")
    sigue "El miembro que quiso sacar el estudio B sigue en el estudio A" "$MINE" "\"$MIE\""
    sigue "El miembro que quiso sacar otro miembro sigue en el estudio A" "$MINE" "\"$MIE2\""
}

administrador() {
    paso "14· Un despachante común no entra a lo de administrador"
    local CK_J="$TMP/jefe.txt" RUTA METODO
    registrar "$JEFE" "$CK_J" >/dev/null
    for RUTA in "GET /api/admin/stats/summary" "GET /api/admin/logs/recent/5" "GET /api/admin/errors/insights" \
                "GET /api/dev/stats" "GET /dev/dashboard"; do
        METODO="${RUTA%% *}"; RUTA="${RUTA#* }"
        # El administrador entra: la ruta existe y el 403 de Beto es por no serlo.
        if [ "$(cod "$(pedir "$CK_J" -X "$METODO" "${BASE}${RUTA}")")" != "200" ]; then
            duda "Admin ${METODO} ${RUTA}" "el administrador tampoco entra: no prueba nada"; continue
        fi
        atacar_como "$COOKIE_B" "Beto en ${METODO} ${RUTA}" 403 -X "$METODO" "${BASE}${RUTA}"
    done
}

OP_ANA=""
operaciones
presupuestos
notas
estudios
organizaciones
administrador

# ======================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Resultado de la Ronda G3${NC}"
echo -e "${BLUE}========================================${NC}"
for L in "${RESUMEN[@]}"; do
    if [[ "$L" == FUGA* ]]; then echo -e "${RED}${L}${NC}"; elif [[ "$L" == DUDA* ]]; then echo -e "${YELLOW}${L}${NC}"; else echo -e "${GREEN}${L}${NC}"; fi
done
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "Bloqueado: ${GREEN}${PASADOS}${NC}   ·   Fugas: ${RED}${FALLADOS}${NC}   ·   Sin probar: ${YELLOW}${DUDOSOS}${NC}"

if [ "$FALLADOS" -gt 0 ]; then
    echo -e "\n${RED}❌ PUERTA G3 NO PASADA: hay ${FALLADOS} fuga(s) entre despachantes.${NC}"
    exit 1
fi
# Sin el TXT de Ana el paso 4 no se prueba, y un caso sin probar no cuenta
# como bloqueado: la puerta no pasa por la razón equivocada (por ejemplo, si
# generar pide un dato nuevo).
if [ -z "$ARCHIVO" ]; then
    echo -e "\n${RED}❌ PUERTA G3 SIN PROBAR: Ana no llegó a generar su MARIA.TXT.${NC}"
    exit 1
fi
if [ "$DUDOSOS" -gt 0 ]; then
    echo -e "\n${RED}❌ PUERTA G3 SIN PROBAR: ${DUDOSOS} caso(s) no llegaron a medir.${NC}"
    exit 1
fi
echo -e "\n${GREEN}✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.${NC}"
exit 0
