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
U=proyecto_maria/static/v2/screens/upload.js
V1=proyecto_maria/static/app.js

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
# La razón sale del estado, no de si este pedido fue el que venció la cuenta.
sabotaje $M "el pedido que vence la cuenta da otra razón" \
  "FAILED $T::test_la_razon_del_402_es_la_misma_en_el_segundo_pedido[suscripcion_vencida]" \
  $'    if _vencer_si_corresponde(entidad):\n        try:' \
  $'    entidad._vencio = _vencer_si_corresponde(entidad)\n    if entidad._vencio:\n        try:' \
  '            message = "Venció tu prueba gratis. Suscribite para seguir usando CDI."' \
  '            message = "Venció tu suscripción." if getattr(entidad, "_vencio", None) == "active" else "Venció tu prueba gratis. Suscribite para seguir usando CDI."'
sabotaje $B "el plan legado da error" \
  "FAILED $T::test_el_plan_legado_trial_genera_exporta_y_guarda" \
  '    return PLANS.get(getattr(user, "plan", None) or "premium") or PLANS["premium"]' \
  '    return PLANS[getattr(user, "plan", None) or "premium"]' 
sabotaje $M "la cancelada no dice que canceló" \
  "FAILED $T::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[cancelada-ncm_sugerir]" \
  '        message = "Cancelaste tu suscripción. Reactivala para seguir usando CDI."' \
  '        message = "No tenés una suscripción activa. Suscribite para seguir usando CDI."'
sabotaje $M "la cuenta sin suscripción se avisa como tope" \
  "FAILED $T::test_el_aviso_de_la_cuenta_sin_suscripcion_no_habla_del_tope" \
  '        code = "SUBSCRIPTION_INACTIVE"' '        code = "PLAN_LIMIT_EXCEEDED"'

# Cuándo se cuenta: la identidad es la operación de CDI, no el nro de factura.
sabotaje $M "cada generación crea y cuenta otra operación" \
  "FAILED $T::test_generar_cuenta_una_vez_por_operacion_y_la_crea" \
  '    if operacion is not None and (huella in huellas or (len(huellas)' \
  '    if False and (huella in huellas or (len(huellas)'
sabotaje $M "generar no cuenta en la cuenta" \
  "FAILED $T::test_generar_cuenta_una_vez_por_operacion_y_la_crea" \
  $'    await _contar_en_la_cuenta(db, cuenta[1])\n    nuevo_id' $'    pass\n    nuevo_id'
sabotaje $M "generar no suma al contador" \
  "FAILED $T::test_generar_cuenta_una_vez_por_operacion_y_la_crea" \
  '    billing_service.record_operation_created(entidad)' '    pass'
sabotaje $M "el mismo resultado ocupa otra de las 10" \
  "FAILED $T::test_el_mismo_resultado_no_gasta_una_de_las_10" \
  '        if huella not in huellas:' '        if True:'
sabotaje $M "con las 10 llenas, el mismo resultado cuenta otra operación" \
  "FAILED $T::test_la_11_distinta_es_una_operacion_nueva_contada" \
  'huella in huellas or ' ''
sabotaje $M "la fecha de emisión cambia el resultado" \
  "FAILED $T::test_el_mismo_resultado_no_gasta_una_de_las_10" \
  '_FECHA_DE_EMISION.sub(r"\1", txt_content)' 'txt_content'
sabotaje $M "la fecha de la factura importada no cambia el resultado" \
  "FAILED $T::test_otra_fecha_de_factura_en_la_importacion_gasta_una_de_las_10" \
  'sha256(contenido.encode' 'sha256(_FECHA_DE_EMISION.sub(r"\1", contenido).encode'
sabotaje $M "el tope de regeneraciones no es 10" \
  "FAILED $T::test_la_11_distinta_es_una_operacion_nueva_contada" \
  'MARIA_REGENERACIONES = 10' 'MARIA_REGENERACIONES = 11'
sabotaje $M "la 11.ª distinta reusa la operación" \
  "FAILED $T::test_la_11_distinta_es_una_operacion_nueva_contada" \
  'len(huellas) < MARIA_REGENERACIONES' 'len(huellas) <= MARIA_REGENERACIONES'
sabotaje $M "dos operaciones con la misma factura comparten el archivo" \
  "FAILED $T::test_dos_operaciones_nunca_comparten_una_fila" \
  'f"{nombre}_{nuevo_id[-8:]}.TXT"' 'f"{nombre}.TXT"' \
  'f"{nombre}_{operacion.id[-8:]}.TXT"' 'f"{nombre}.TXT"'
sabotaje $M "el archivo toma el comienzo del id" \
  "FAILED $T::test_dos_operaciones_manuales_no_comparten_el_archivo" \
  'f"{nombre}_{nuevo_id[-8:]}.TXT"' 'f"{nombre}_{nuevo_id[:8]}.TXT"' \
  'f"{nombre}_{operacion.id[-8:]}.TXT"' 'f"{nombre}_{operacion.id[:8]}.TXT"'
sabotaje $M "el período nuevo hereda las regeneraciones" \
  "FAILED $T::test_el_periodo_nuevo_no_hereda_las_regeneraciones" \
  $'\n                                                        and _del_periodo(operacion, cuenta[1])' ''
sabotaje $M "la operación del mismo segundo parece de otro período" \
  "FAILED $T::test_la_operacion_del_mismo_segundo_es_del_periodo" \
  'inicio.tzinfo or timezone.utc, microsecond=0)' 'inicio.tzinfo or timezone.utc)'
sabotaje $M "se reusa la operación de otra cuenta" \
  "FAILED $T::test_guardar_con_la_operacion_de_otra_cuenta_no_la_toca" \
  $'        OperationModel.owner_username == username,\n    ))' $'    ))'
sabotaje $M "borrar el cliente borra sus operaciones" \
  "FAILED $T::test_borrar_el_cliente_no_recuenta_lo_generado" \
  $'            operacion.client_id = None\n' $'            await db.delete(operacion)\n            continue\n'
sabotaje $M "se escribe el archivo antes de contar" \
  "FAILED $T::test_con_el_tope_lleno_se_valida_y_se_baja_lo_ya_contado" \
  $'        operacion_id, filename = await _contar_maria(\n            db, user["username"], request.operacion_id, txt_content, txt_content,\n            len(request.items or []), f"MARIA_{safe_id}")\n' \
  $'        with open(os.path.join(_user_downloads_dir(user["username"]), f"MARIA_{safe_id}.TXT"), \'w\') as f:\n            f.write(txt_content)\n        operacion_id, filename = await _contar_maria(\n            db, user["username"], request.operacion_id, txt_content, txt_content,\n            len(request.items or []), f"MARIA_{safe_id}")\n'
sabotaje $B "la fecha de las recargas sin zona no se toma como UTC" \
  "FAILED $T::test_con_el_tope_lleno_el_extra_paga_la_operacion_nueva" \
  $'    if expires is not None and expires.tzinfo is None:\n        expires = expires.replace(tzinfo=timezone.utc)' \
  $'    if False:\n        pass'
sabotaje $M "cuenta el usuario y no su organización" \
  "FAILED $T::test_la_organizacion_es_la_que_cuenta" \
  $'        if org:\n            return db_user, org' $'        if org:\n            return db_user, db_user'

# Sin usuario en la base, cada paso que cuenta da 401: ningún atajo por entorno.
ATAJO=$'        if os.getenv("ENVIRONMENT", "").startswith("test"):\n'
NO_ESTA=$'        raise HTTPException(status_code=401, detail="Usuario no encontrado")\n'
VIGENTE=$'\n    entidad, _ = await _get_billing_entity(db, db_user)\n    await _vencer_y_guardar(db, entidad)\n    if not billing_service.tiene_acceso'
ACTIVA=$'\n    entidad, _ = await _get_billing_entity(db, db_user)\n    await _vencer_y_guardar(db, entidad)\n    ok, reason'
COMO_ANTES=$'            return User(username=user["username"], plan="premium", billing_status="active")\n'
for paso in vigente activa bloqueada maria; do
  case $paso in
    vigente)   viejo="$NO_ESTA$VIGENTE"; atajo="$COMO_ANTES" ;;
    activa)    viejo="$NO_ESTA$ACTIVA"; atajo="$COMO_ANTES" ;;
    bloqueada) viejo="$NO_ESTA    return await _contar_en_la_cuenta"; atajo=$'            return None\n' ;;
    maria)     viejo="$NO_ESTA"$'\n    operacion = await _operacion_del_usuario'; atajo=$'            return "", nombre\n' ;;
  esac
  sabotaje $M "el paso $paso deja pasar sin usuario en pruebas" \
    "FAILED $T::test_sin_sesion_las_rutas_que_cuentan_dan_401" "$viejo" "$ATAJO$atajo$viejo"
done

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
sabotaje $M "guardar sin una operación generada no cuenta" \
  "FAILED $T::test_guardar_sin_una_operacion_generada_cuenta_cada_vez" \
  $'        else:\n            await _contar_operacion_bloqueada(db, username)' $'        else:\n            pass'
sabotaje $M "guardar dos veces suma los ítems" \
  "FAILED $T::test_guardar_dos_veces_lo_generado_reemplaza_los_items" \
  $'            await db.execute(\n                sa_delete(OperationItemModel).where(\n                    OperationItemModel.operation_id == operation.id\n                )\n            )\n        else:' \
  $'            pass\n        else:'
sabotaje $M "guardar en otro cliente no mueve la operación" \
  "FAILED $T::test_guardar_en_otro_cliente_mueve_la_operacion" \
  '                setattr(operation, campo, valor)' \
  $'                if campo != "client_id":\n                    setattr(operation, campo, valor)'

sabotaje $M "un id que la base no guarda se busca igual" \
  "FAILED $T::test_un_id_que_la_base_no_guarda_es_una_operacion_nueva" \
  '    if not operacion_id or _NO_GUARDABLE_EN_PG.search(operacion_id):' '    if not operacion_id:'

# El conteo vuelve a mirar el estado con la cuenta bloqueada. Toda ruta que
# cuenta pasa antes por el corte, así que su prueba llama al conteo directo.
sabotaje $M "el conteo no vence la cuenta" \
  "FAILED $T::test_el_conteo_vence_la_cuenta_que_vencio_despues_del_corte" \
  $'    _vencer_si_corresponde(entidad)\n    ok, reason = billing_service.can_create_operation(entidad)\n    if not ok:\n        detalle' \
  $'    ok, reason = billing_service.can_create_operation(entidad)\n    if not ok:\n        detalle' 

sabotaje $M "se confirma el conteo antes de escribir" \
  "FAILED $T::test_lo_no_entregado_no_queda_cobrado[importacion_al_escribir]" \
  $'    try:\n        # newline' $'    await db.commit()\n    try:\n        # newline'
sabotaje $M "lo escrito a medias queda en las descargas" \
  "FAILED $T::test_lo_no_entregado_no_queda_cobrado[exportacion_al_escribir]" \
  $'            if os.path.exists(resto):\n                os.remove(resto)' $'            pass'
sabotaje $M "un primer commit fallido deja el archivo en las descargas" \
  "FAILED $T::test_lo_no_entregado_no_queda_cobrado[importacion_al_confirmar]" \
  $'            os.remove(ruta)' $'            pass'
sabotaje $M "los supuestos se arman después de contar" \
  "FAILED $T::test_lo_no_entregado_no_queda_cobrado[importacion_despues_de_contar]" \
  $'        supuestos = _supuestos_maria(request, items, gastos)\n' '' \
  $'        return {\n            "success": True,\n            "operacion_id": operacion_id,\n            "filename": filename,' \
  $'        supuestos = _supuestos_maria(request, items, gastos)\n        return {\n            "success": True,\n            "operacion_id": operacion_id,\n            "filename": filename,'
sabotaje $M "regenerar escribe sobre lo ya entregado" \
  "FAILED $T::test_regenerar_con_una_falla_deja_entero_lo_ya_entregado[al_escribir]" \
  '        with open(temporal, "w"' '        with open(ruta, "w"' $'        os.replace(temporal, ruta)\n' ''
sabotaje $M "un commit fallido deja el archivo nuevo" \
  "FAILED $T::test_regenerar_con_una_falla_deja_entero_lo_ya_entregado[al_confirmar]" \
  '            os.link(ruta, respaldo)' '            pass'
sabotaje $M "se deshace la base antes de devolver el archivo" \
  "FAILED $T::test_regenerar_con_una_falla_deja_entero_lo_ya_entregado[al_confirmar_y_deshacer]" \
  $'        # Los archivos antes que el rollback: si éste también falla, lo entregado ya volvió.\n' $'        await db.rollback()\n' \
  $'            os.remove(ruta)\n        await db.rollback()\n        raise' $'            os.remove(ruta)\n        raise'
sabotaje $M "se restaura un anterior que no es de esta regeneración" \
  "FAILED $T::test_regenerar_con_una_falla_deja_entero_lo_ya_entregado[al_escribir_con_un_anterior_viejo]" \
  $'        if enlazado:\n            os.replace(respaldo, ruta)' $'        if not nuevo and os.path.exists(respaldo):\n            os.replace(respaldo, ruta)'

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
sabotaje $A "el 402 no trae su razón como mensaje" \
  "FALLA: tope: el error de la generación dice" \
  '            const err = new Error(lead);' "            const err = new Error('payment_required');"
sabotaje $F "generar no manda la operación de la pantalla" \
  "FALLA: regenerar manda la operación que devolvió la primera" \
  "        body.operacion_id = carga.operacionId || '';" "        body.operacion_id = '';"
sabotaje $F "guardar no anota la operación que devolvió" \
  "FALLA: guardar antes de generar" \
  "                carga.operacionId = data.operation_id || '';" ''
# Una respuesta tardía se anota en la carga que la pidió, no en la que está en pantalla.
sabotaje $F "v2: generar anota en la carga de la pantalla" \
  "FALLA: v2, generar: la respuesta tardía no se guardó en el cliente de su carga con su operación (mandó «»)" \
  "            carga.operacionId = data.operacion_id || '';" "            CDI.state.operacionId = data.operacion_id || '';"
sabotaje $F "v2: guardar anota en la carga de la pantalla" \
  "FALLA: v2, guardar: la carga nueva quedó con la operación" \
  "                carga.operacionId = data.operation_id || '';" "                CDI.state.operacionId = data.operation_id || '';"
sabotaje $F "v2: generar guarda con la carga de la pantalla" \
  "FALLA: v2, generar: la respuesta tardía no se guardó en el cliente de su carga" \
  "            saveOperationToHistory(items, data, carga, foto).catch(" "            saveOperationToHistory(items, data, undefined, foto).catch("
sabotaje $F "v2: el guardado toma los valores de la pantalla al responder" \
  "FALLA: v2, generar: guardó los valores de la carga nueva" \
  "            saveOperationToHistory(items, data, carga, foto).catch(" "            saveOperationToHistory(items, data, carga).catch("
sabotaje $F "v2: la respuesta tardía marca lista la carga nueva" \
  "FALLA: v2, generar: la respuesta tardía marcó lista la carga nueva" \
  "            if (carga === CDI.state) mostrarListo(data);" "            mostrarListo(data);"
sabotaje $F "v2: el guardado toma el cliente de la pantalla" \
  "FALLA: v2, generar: la respuesta tardía no se guardó en el cliente de su carga" \
  "        const cliente = carga.clienteActivo || null;" "        const cliente = (CDI.getClienteActivo && CDI.getClienteActivo()) || null;"
# La carga nueva que llega a «Listo» mientras la anterior espera genera cuando ésa vuelve, y no hereda su error.
sabotaje $F "v2: la carga nueva en «Listo» no genera" \
  "FALLA: v2, la carga nueva en «Listo» y la anterior vuelve bien: no terminó" \
  "        if (generateInFlight) { pedidaMientrasOtra = true; return; }" "        if (generateInFlight) return;"
sabotaje $F "v2: el error de la anterior cambia de paso a la carga nueva" \
  "FALLA: v2, la carga nueva en «Listo» y la anterior vuelve con un error" \
  $'            if (fallo && carga !== CDI.state) return;\n' ''
sabotaje $F "v2: la anterior sin red le muestra el error a la carga nueva" \
  "FALLA: v2, la anterior se queda sin red: la carga nueva muestra el error" \
  "            if (carga === CDI.state) showReadyError(String(err && err.message || err));" \
  "            showReadyError(String(err && err.message || err));"
sabotaje $V1 "v1: generar anota en la carga nueva" \
  "FALLA: v1, generar: la carga nueva quedó con la operación" \
  "        anotarOperacion(carga, data.operacion_id || '');" "        operacionIdActual = data.operacion_id || '';"
# Generar también guarda: el caso de generar lo ve antes que el del guardado solo.
sabotaje $V1 "v1: guardar anota en la carga nueva" \
  "FALLA: v1, generar: la carga nueva quedó con la operación" \
  "        if (res.ok) anotarOperacion(carga, (await res.json()).operation_id || operacionId);" \
  "        if (res.ok) operacionIdActual = (await res.json()).operation_id || operacionId;"
sabotaje $V1 "v1: el guardado toma el cliente del selector al responder" \
  "FALLA: v1, generar: la respuesta tardía no se guardó en el cliente de su carga" \
  "    if (!carga.cliente) {" "    if (!clientSelect.value) {" \
  '/api/clientes/${carga.cliente}/operaciones' '/api/clientes/${clientSelect.value}/operaciones'
sabotaje $V1 "v1: cancelar no empieza otra carga" \
  "FALLA: v1, generar: la carga nueva quedó con la operación" \
  "function nuevaCarga() { operacionIdActual = ''; cargaActual++; }" "function nuevaCarga() { operacionIdActual = ''; }"
sabotaje $U "una operación nueva arrastra el id de la anterior" \
  "FALLA: una operación nueva manda un operacion_id vacío" \
  "            operacionId: null, operationSavedFor: null, orphanDismissedFor: null," \
  "            operationSavedFor: null, orphanDismissedFor: null," 

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
  sabotaje $M "borrar cliente no espera el candado de la cuenta" \
    "FALLA | borrar cliente" \
    $'        client = await _cliente_con_cuenta_bloqueada(db, client_id, username)\n        op_rows' \
    $'        client = await _get_owned_client(db, client_id, username)\n        op_rows'
  sabotaje $M "el guardado mira el cliente antes del candado" \
    "FALLA | guardar en un cliente que se borró" \
    $'        client = await _cliente_con_cuenta_bloqueada(db, client_id, username)\n        operation' \
    $'        client = await _get_owned_client(db, client_id, username)\n        await _cuenta_bloqueada(db, username)\n        operation'
  sabotaje $M "Postgres recibe el id que no puede comparar" \
    "FALLA | id con NUL" \
    '    if not operacion_id or _NO_GUARDABLE_EN_PG.search(operacion_id):' '    if not operacion_id:'
fi

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
