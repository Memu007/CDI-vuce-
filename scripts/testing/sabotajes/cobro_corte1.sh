#!/usr/bin/env bash
# Negativos de COBRO-CORTE-1: cada sabotaje deshace una regla de la pieza y la
# prueba tiene que fallar por ese motivo. Primero el servidor
# (tests/test_cobro_corte1.py), después la pantalla
# (scripts/testing/pantalla_cobro_corte1.js) y al final el lock contra un
# Postgres local (scripts/testing/cobro_corte1_postgres.py).
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8854] [PG=postgresql://usuario@127.0.0.1:<puerto>] \
#        scripts/testing/sabotajes/cobro_corte1.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y sin terceros: no toca
# tu copia ni datos compartidos. Cada corrida de la pantalla levanta la API de
# nuevo, con una base vacía. Con PG (un Postgres local y descartable, nunca el
# de producción), cada corrida crea su base y la borra al terminar; sin PG, la
# parte del lock se declara «NO CORRIDO».
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8854}"
PG="${PG:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -f "$TMPD/api.log" "$TMPD/local.db"; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo.
sabotaje() {
  local archivo="$1" nombre="$2" esperado="$3"; shift 3
  git checkout -q -- proyecto_maria/
  rm -f test.db
  if ! "$PY" - "$archivo" "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|FALLA|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

T=tests/test_cobro_corte1.py
M=proyecto_maria/main.py
B=proyecto_maria/services/billing_service.py
A=proyecto_maria/static/v2/app_v2.js
F=proyecto_maria/static/v2/screens/finalize.js

# ------------------------------------------------------------- el servidor
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -W ignore "$T" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba del servidor ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi
echo "BASE  | en verde"

# El corte por estado en cada ruta que gasta Gemini o genera valor (D5 a):
# sin la dependencia, la cuenta impaga pasa.
DEP="    _cobro=Depends(require_billing_vigente),"$'\n'
sin_corte() {
  local ruta="$1" esperado="$2" despues="$3"
  sabotaje $M "$ruta no corta por estado" "$esperado" "$DEP$despues" "$despues"
}
sin_corte process_operation "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-process_operation]" \
  $'):\n    """\n    Recibe los datos de una operación, los valida y genera el Excel.'
sin_corte upload_pdf "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-upload_pdf]" \
  $'):\n    """\n    Sube y procesa un archivo PDF'
# Las dos que generan MARIA tienen además el corte del conteo; lo ya contado
# sólo lo frena la dependencia.
sin_corte generate_maria "FAILED $T::test_regenerar_lo_ya_contado_con_la_cuenta_que_no_esta_al_dia_da_402[impaga-importacion]" \
  $'):\n    """\n    Genera archivo TXT en formato MARIA para el sistema SIM de AFIP.'
sin_corte generate_maria_export "FAILED $T::test_regenerar_lo_ya_contado_con_la_cuenta_que_no_esta_al_dia_da_402[impaga-exportacion]" \
  $'    db: AsyncSession = Depends(get_db),\n):\n    """\n    Genera archivo TXT en formato MARIA para EXPORTACIÓN.'
sin_corte migraciones_analizar "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-migraciones_analizar]" \
  $'    db: AsyncSession = Depends(get_db),\n):\n    """Analiza un CSV/Excel sin crear ni modificar clientes."""'
sin_corte migraciones_confirmar "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-migraciones_confirmar]" \
  $'    db: AsyncSession = Depends(get_db),\n):\n    """Confirma un preview.'
sin_corte "guardar en el cliente" "FAILED $T::test_guardar_lo_ya_generado_con_la_cuenta_que_no_esta_al_dia_da_402[impaga]" \
  $'):\n    """Guarda una operación en el historial del cliente.'
sin_corte ncm_sugerir "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-ncm_sugerir]" \
  $'    db: AsyncSession = Depends(get_db),\n):\n    """Sugiere hasta 5 NCM'

sabotaje $B "la dependencia deja pasar la impaga" \
  "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-ncm_sugerir]" \
  '    if status in ("trial", "active"):' \
  '    if status in ("trial", "active", "past_due"):'

# Cuándo vence (el trial sin gracia, la suscripción con 7 días).
sabotaje $M "el trial vencido no vence" \
  "FAILED $T::test_el_estudio_con_la_prueba_vencida_no_genera_ni_gasta_gemini" \
  '    if entidad.billing_status == "trial" and fin < ahora:' \
  '    if entidad.billing_status == "trial" and fin < ahora - timedelta(days=30):'
sabotaje $M "la suscripción vence sin gracia" \
  "FAILED $T::test_la_suscripcion_dentro_de_la_gracia_genera" \
  '        and fin < ahora - timedelta(days=BILLING_GRACE_DAYS_ACTIVE)' '        and fin < ahora'
sabotaje $M "la fecha sin zona no se toma como UTC" \
  "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[suscripcion_vencida-ncm_sugerir]" \
  $'    if fin.tzinfo is None:\n        fin = fin.replace(tzinfo=timezone.utc)' ''

# El aviso dice la razón real.
sabotaje $M "el impago se avisa como vencido" \
  "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-ncm_sugerir]" \
  '            code = "SUBSCRIPTION_PAST_DUE"'$'\n''            message = ("Tenés un pago pendiente de tu suscripción. "' \
  '            code = "TRIAL_EXPIRED"'$'\n''            message = ("Tenés un pago pendiente de tu suscripción. "'
sabotaje $M "la prueba vencida se avisa como suscripción" \
  "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[prueba_vencida-ncm_sugerir]" \
  '            que = "tu suscripción" if vencio == "active" else "tu prueba gratis"' \
  '            que = "tu prueba gratis" if vencio == "active" else "tu suscripción"'
sabotaje $M "la cancelada no dice que canceló" \
  "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[cancelada-ncm_sugerir]" \
  '        message = "Cancelaste tu suscripción. Reactivala para seguir usando CDI."' \
  '        message = "No tenés una suscripción activa. Suscribite para seguir usando CDI."'
sabotaje $M "la cuenta sin suscripción se avisa como tope" \
  "FAILED $T::test_el_aviso_de_la_cuenta_sin_suscripcion_no_habla_del_tope" \
  '        code = "SUBSCRIPTION_INACTIVE"' '        code = "PLAN_LIMIT_EXCEEDED"'

# Cuándo se cuenta (D4 b).
sabotaje $M "cada generación crea y cuenta otra operación" \
  "FAILED $T::test_generar_cuenta_una_vez_por_id_y_crea_la_operacion" \
  '    if operacion is None:' '    if True:'
sabotaje $M "generar no suma al contador" \
  "FAILED $T::test_generar_cuenta_una_vez_por_id_y_crea_la_operacion" \
  '    billing_service.record_operation_created(entidad)' '    pass'
sabotaje $M "regenerar el mismo contenido gasta una de las 10" \
  "FAILED $T::test_el_mismo_id_no_pasa_de_10_contenidos_distintos" \
  '    if huella in huellas:' '    if False:'
sabotaje $M "el mismo id pasa de 10 contenidos" \
  "FAILED $T::test_el_mismo_id_no_pasa_de_10_contenidos_distintos" \
  '    if len(huellas) >= MARIA_REGENERACIONES:' '    if len(huellas) > MARIA_REGENERACIONES:'
sabotaje $M "se escribe el archivo antes de contar" \
  "FAILED $T::test_con_el_tope_lleno_se_valida_y_se_baja_lo_ya_contado" \
  $'        await _contar_maria(db, user["username"], filename, txt_content,\n                            len(request.items or []))\n\n        # newline="": el archivo lleva los CRLF tal cual, sin traducir (MARIA-7).\n        with open(filepath, \'w\', encoding=\'utf-8\', newline=\'\') as f:\n            f.write(txt_content)\n' \
  $'        with open(filepath, \'w\', encoding=\'utf-8\', newline=\'\') as f:\n            f.write(txt_content)\n        await _contar_maria(db, user["username"], filename, txt_content,\n                            len(request.items or []))\n'
sabotaje $B "la fecha de las recargas sin zona no se toma como UTC" \
  "FAILED $T::test_con_el_tope_lleno_el_extra_paga_la_operacion_nueva" \
  $'    if expires is not None and expires.tzinfo is None:\n        expires = expires.replace(tzinfo=timezone.utc)' \
  $'    if False:\n        pass'
sabotaje $M "cuenta el usuario y no su organización" \
  "FAILED $T::test_la_organizacion_es_la_que_cuenta" \
  $'        if org:\n            return db_user, org' $'        if org:\n            return db_user, db_user'

# Guardar después de generar.
sabotaje $M "guardar no busca la operación generada" \
  "FAILED $T::test_guardar_despues_de_generar_no_cuenta_dos_veces" \
  '        if operation is not None:' '        if False:'
sabotaje $M "guardar toma la operación generada de otra cuenta" \
  "FAILED $T::test_guardar_con_el_archivo_de_otra_cuenta_no_toca_su_operacion" \
  $'        OperationModel.owner_username == owner_username,\n        OperationModel.generated_file == archivo,' \
  $'        OperationModel.generated_file == archivo,'
sabotaje $M "guardar le saca la operación a otro cliente" \
  "FAILED $T::test_guardar_en_otro_cliente_no_le_saca_la_operacion" \
  '            operation = await _operacion_maria(db, username, archivo, client_id)' \
  '            operation = await _operacion_maria(db, username, archivo)'
sabotaje $M "guardar no reusa la operación generada sin cliente" \
  "FAILED $T::test_guardar_despues_de_generar_no_cuenta_dos_veces" \
  '        query = query.where(sa_or(OperationModel.client_id.is_(None),' \
  '        query = query.where(sa_or(False,'
sabotaje $M "guardar sin haber generado no cuenta" \
  "FAILED $T::test_guardar_sin_haber_generado_cuenta_una" \
  $'        else:\n            await _contar_operacion_bloqueada(db, username)' $'        else:\n            pass'
sabotaje $M "guardar toma cualquier id como archivo MARIA" \
  "FAILED $T::test_guardar_con_un_id_que_no_es_un_maria_no_lo_toma_como_archivo" \
  '        if not _ARCHIVO_MARIA.fullmatch(archivo):' '        if False:'
sabotaje $M "guardar dos veces suma los ítems" \
  "FAILED $T::test_guardar_dos_veces_lo_generado_reemplaza_los_items" \
  $'            await db.execute(\n                sa_delete(OperationItemModel).where(\n                    OperationItemModel.operation_id == operation.id\n                )\n            )' \
  '            pass'

# El conteo vuelve a mirar el estado con la cuenta bloqueada. Toda ruta que
# cuenta pasa antes por el corte, así que su prueba llama al conteo directo.
sabotaje $M "el conteo no vence la cuenta" \
  "FAILED $T::test_el_conteo_vence_la_cuenta_que_vencio_despues_del_corte" \
  $'    vencio = _vencer_si_corresponde(entidad)\n    ok, reason' $'    vencio = None\n    ok, reason'

# ------------------------------------------------------------- la pantalla
git checkout -q -- proyecto_maria/
export ENVIRONMENT=development GEMINI_API_KEY=test-key \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
export BASE_URL="http://127.0.0.1:$PUERTO"
correr() {
  rm -f "$TMPD/local.db"
  DATABASE_URL="sqlite+aiosqlite:///$TMPD/local.db" "$PY" -m uvicorn proyecto_maria.main:app \
    --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && break; sleep 1; done
  if ! curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
    echo "FALLA: la API no levantó"; tail -5 "$TMPD/api.log"; kill $API 2>/dev/null; wait $API 2>/dev/null; API=""; return 1
  fi
  local codigo
  node scripts/testing/pantalla_cobro_corte1.js 2>&1; codigo=$?
  # Si la pantalla falla, lo que la API dijo: un «socket hang up» no se
  # diagnostica sin esto, porque el log se pisa en la corrida siguiente.
  [ "$codigo" -ne 0 ] && grep -E "Error|Traceback|Killed" "$TMPD/api.log" | tail -2 | sed 's/^/FALLA de la API: /'
  kill $API 2>/dev/null; wait $API 2>/dev/null; API=""
  return $codigo
}
if ! correr >/dev/null; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi
echo "BASE  | la pantalla en verde"

sabotaje $F "el id sin factura sale de la hora de generar" \
  "FALLA: el id sin factura no sale de cuándo se cargó" \
  '        const cargada = (CDI.state && CDI.state.uploadedAt) || new Date().toISOString();' \
  '        const cargada = new Date().toISOString();'
sabotaje $F "el id sin factura corta en segundos" \
  "FALLA: el id sin factura no sale de cuándo se cargó" \
  "            ('OP_' + String(cargada).replace(/[^0-9]/g, '').slice(0, 17));" \
  "            ('OP_' + String(cargada).replace(/[^0-9]/g, '').slice(0, 14));"
sabotaje $A "el tope tiene otro título" \
  "FALLA: tope: el modal se titula" \
  "                PLAN_LIMIT_EXCEEDED: 'Llegaste al tope de tu plan'," \
  "                PLAN_LIMIT_EXCEEDED: 'Necesitás un plan',"
sabotaje $A "el impago se titula como tope" \
  "FALLA: impago: el modal se titula" \
  "                SUBSCRIPTION_PAST_DUE: 'Tenés un pago pendiente'," \
  "                SUBSCRIPTION_PAST_DUE: 'Llegaste al tope de tu plan',"
sabotaje $A "la cancelada se titula como vencida" \
  "FALLA: cancelada: el modal se titula" \
  "            const cancelo = motivo.billing_status === 'canceled' && motivo.code !== 'PLAN_LIMIT_EXCEEDED';" \
  "            const cancelo = motivo.billing_status === 'cancelada' && motivo.code !== 'PLAN_LIMIT_EXCEEDED';"
sabotaje $A "la cancelada con el tope se titula como cancelada" \
  "FALLA: cancelada con el tope: el modal se titula" \
  "            const cancelo = motivo.billing_status === 'canceled' && motivo.code !== 'PLAN_LIMIT_EXCEEDED';" \
  "            const cancelo = motivo.billing_status === 'canceled';"
sabotaje $A "el modal no muestra el mensaje del servidor" \
  "FALLA: tope: el modal dice" \
  "            const lead = motivo.message || (typeof detail === 'string' && detail) ||" \
  "            const lead = (typeof detail === 'string' && detail) ||"
sabotaje $A "el 402 no le pasa su razón a la generación" \
  "FALLA: tope: el error de la generación dice" \
  '            err.motivo = lead;' '            err.motivo = "";'
sabotaje $F "la generación no muestra la razón del 402" \
  "FALLA: tope: el error de la generación dice" \
  '            showReadyError(String((err && err.motivo) || (err && err.message) || err));' \
  '            showReadyError(String((err && err.message) || err));'
sabotaje $F "el 409 no muestra su mensaje" \
  "FALLA: 409: el error de la generación dice" \
  "(detail && typeof detail === 'object' && detail.message) ? detail.message : detail;" \
  "(false) ? detail.message : detail;"

# ------------------------------------------------------ el lock (Postgres)
git checkout -q -- proyecto_maria/
if [ -z "$PG" ]; then
  echo "NO CORRIDO | lock: falta PG=postgresql://usuario@127.0.0.1:<puerto> (un Postgres local)"
else
  base_pg() {  # base_pg create|drop <nombre>
    "$PY" - "$PG" "$1" "$2" <<'PYEOF'
import sys
import psycopg2
url, que, base = sys.argv[1:]
con = psycopg2.connect(url.rstrip("/") + "/postgres")
con.autocommit = True
con.cursor().execute(f"create database {base}" if que == "create" else f"drop database if exists {base} with (force)")
PYEOF
  }
  correr() {
    local base="cc1sab_$$_$RANDOM" codigo
    base_pg create "$base" || { echo "FALLA | no se pudo crear la base"; return 1; }
    "$PY" scripts/testing/cobro_corte1_postgres.py "${PG%/}/$base" 2>&1; codigo=$?
    base_pg drop "$base"
    return $codigo
  }
  if ! correr >/dev/null; then
    echo "BASE  | el lock ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
  fi
  echo "BASE  | el lock en verde"
  sabotaje $M "no se bloquea la fila del usuario" \
    "FALLA | tope" \
    $'        .where(User.username == username)\n        .with_for_update()' \
    $'        .where(User.username == username)'
  sabotaje $M "no se bloquea la fila de la organización" \
    "FALLA | estudio" \
    $'            .where(Organization.id == db_user.organization_id)\n            .with_for_update()' \
    $'            .where(Organization.id == db_user.organization_id)'
  sabotaje $M "se cuenta con el usuario leído antes del lock" \
    "FALLA | tope" \
    $'        .with_for_update()\n        .execution_options(populate_existing=True)\n    )\n    db_user' \
    $'        .with_for_update()\n    )\n    db_user'
fi

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
