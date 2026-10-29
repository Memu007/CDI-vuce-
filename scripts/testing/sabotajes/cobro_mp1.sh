#!/usr/bin/env bash
# Negativos de COBRO-MP-1 (pasos 1 a 4 y D31): cada sabotaje deshace una línea
# de la pieza y tests/test_cobro_mp1.py tiene que ponerse roja por ese motivo.
# La devolución del 2026-10-28 (B a E) se mide con tests/test_cobro_corte1.py
# (B), tests/test_cobro_mp1_cde.py (C y E), la carrera de D en un Postgres 16
# descartable (scripts/testing/cobro_mp1d_postgres.py, con con_pg16.sh) y la
# pantalla del perfil (scripts/testing/pantalla_cobro_mp1.js; PUERTO, 8854).
# Los «sin_rojo» deshacen algo que no es la garantía y la prueba tiene que
# seguir en verde (D31: lo que frena el doble cobro es la clave primaria, no
# mirar antes).
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cobro_mp1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no da lo esperado.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0
T=tests/test_cobro_mp1.py
M=proyecto_maria/main.py
B=proyecto_maria/services/billing_service.py
H=proyecto_maria/templates/dev_dashboard.html

# aplicar <archivo> <texto original> <texto saboteado>: vuelve todo al SHA y
# cambia el texto, que tiene que estar una sola vez.
aplicar() {
  git checkout -q -- proyecto_maria/
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
}

correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider "$T" 2>&1; }

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^(E |FAILED)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

# sin_rojo <archivo> <nombre> <texto original> <texto saboteado>
sin_rojo() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida
  if salida="$(correr)"; then
    echo "VERDE | $nombre: sigue en verde, como tiene que ser ($(tail -1 <<<"$salida"))"
  else
    echo "ROJO! | $nombre: se puso rojo y no tenía que"; grep -E "^(E |FAILED)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi
echo "BASE  | en verde"

# ── Paso 1: cada pago se aplica una sola vez ──
sabotaje $M "un pago ya aplicado vuelve a aplicarse (usuario)" \
  '            estado = await _registrar_pago_mp(session, payment_id, username, update, pay_resp, control)' \
  '            estado = "aplicado"' \
  "FAILED $T::test_alternar_dos_pagos_viejos_no_renueva"
sabotaje $M "un pago ya aplicado vuelve a aplicarse (organización)" \
  '                estado = await _registrar_pago_mp(session, payment_id, f"org:{org_id}", update, pay_resp, control)' \
  '                estado = "aplicado"' \
  "FAILED $T::test_organizacion_alternar_dos_pagos_viejos_no_renueva"
sabotaje $M "el pago se registra sin su tipo" \
  '        tipo="topup" if update.get("action") == "topup" else str(update.get("plan") or ""),' \
  '        tipo="",' \
  "FAILED $T::test_el_pago_aplicado_queda_registrado"

# ── Paso 3: el período se extiende desde su fin ──
sabotaje $M "pagar con la cuenta activa vuelve a contar desde hoy" \
  '    desde = fin if (vigente and fin and fin > ahora) else ahora' \
  '    desde = ahora' \
  "FAILED $T::test_pagar_con_la_cuenta_activa_extiende_desde_el_fin"
sabotaje $M "una cuenta vencida suma desde el fin viejo" \
  '    desde = fin if (vigente and fin and fin > ahora) else ahora' \
  '    desde = fin if fin else ahora' \
  "FAILED $T::test_pagar_con_la_cuenta_vencida_cuenta_desde_hoy"
sabotaje $M "la organización vuelve a contar desde hoy" \
  '                _extender_periodo(db_org, update)' \
  '                pass' \
  "FAILED $T::test_organizacion_pagar_activa_extiende_desde_el_fin"

# ── Paso 2: el monto se controla (D29) ──
sabotaje $M "se acepta otra moneda" \
  '    if moneda != "ARS":' \
  '    if False:' \
  "FAILED $T::test_un_plan_en_otra_moneda_no_se_aplica"
sabotaje $M "no se compara lo pagado con el precio" \
  '    if pagado is None or pagado + 0.005 < esperado:' \
  '    if pagado is None:' \
  "FAILED $T::test_un_plan_pagado_de_menos_no_se_aplica_y_queda_rechazado"
sabotaje $M "el precio de la recarga sin link es otro" \
  '                esperado = float(billing_service.TOPUP_PRICE_ARS)' \
  '                esperado = 1.0' \
  "FAILED $T::test_una_recarga_pagada_de_menos_no_suma"
sabotaje $M "se ignora el precio de cuando se armó el link" \
  '        esperado = _monto_mp(meta.get("precio_esperado"))' \
  '        esperado = None' \
  "FAILED $T::test_un_link_con_el_precio_de_cuando_se_armo_se_respeta"
sabotaje $B "el link del plan no guarda el precio" \
  '        "metadata": {"precio_esperado": plan["price"]},' \
  '' \
  "FAILED $T::test_el_link_de_pago_guarda_el_precio"
sabotaje $B "el link de la recarga no guarda el precio" \
  '        "metadata": {"precio_esperado": TOPUP_PRICE_ARS},' \
  '' \
  "FAILED $T::test_el_link_de_pago_guarda_el_precio"
sabotaje $M "la suscripción se compara con PLANS y no con su monto" \
  '        esperado = _monto_mp(recurrente.get("transaction_amount"))' \
  '        esperado = float(billing_service.PLANS["premium"]["price"])' \
  "FAILED $T::test_una_suscripcion_se_compara_con_su_monto_en_mercado_pago"
sabotaje $M "la suscripción de otra cuenta vale" \
  '        if suscripcion.get("external_reference") != external_ref:' \
  '        if False:' \
  "FAILED $T::test_la_suscripcion_de_otra_cuenta_no_vale"
sabotaje $M "una suscripción ilegible se rechaza en vez de reintentar" \
  '            raise _SuscripcionMPIlegible(str(suscripcion_id))' \
  '            return None, "ilegible"' \
  "FAILED $T::test_si_no_se_puede_leer_la_suscripcion_mercado_pago_reintenta"
sabotaje $M "el rechazo no se guarda" \
  '    if await _guardar_pago_mp(session):' \
  '    if True:' \
  "FAILED $T::test_un_plan_pagado_de_menos_no_se_aplica_y_queda_rechazado"
sabotaje $M "cualquier usuario ve los pagos rechazados" \
  $'async def get_dev_pagos_mp_rechazados(\n    user=Depends(require_admin),' \
  $'async def get_dev_pagos_mp_rechazados(\n    user=Depends(get_current_user),' \
  "FAILED $T::test_emi_ve_los_pagos_rechazados_y_un_usuario_comun_no"
sabotaje $H "el panel no pide los pagos rechazados" \
  "fetch('/api/dev/pagos-mp-rechazados')" \
  "fetch('/api/dev/pagos')" \
  "FAILED $T::test_el_panel_muestra_los_pagos_rechazados"

# ── D31: la clave primaria frena el segundo aviso ──
sabotaje $M "la clave repetida se da por guardada" \
  $'    except IntegrityError:\n        await session.rollback()\n        return False' \
  $'    except IntegrityError:\n        await session.rollback()\n        return True' \
  "FAILED $T::test_dos_avisos_del_mismo_pago_a_la_vez_se_aplican_una_sola_vez"
sabotaje $M "la clave repetida no se atrapa" \
  $'    try:\n        await session.commit()\n        return True\n    except IntegrityError:\n        await session.rollback()\n        return False' \
  $'    await session.commit()\n    return True' \
  "FAILED $T::test_dos_avisos_del_mismo_pago_a_la_vez_se_aplican_una_sola_vez"
sin_rojo $M "sin mirar antes de insertar" \
  $'    if await session.get(PagoMercadoPagoAplicado, str(payment_id)) is not None:\n        return None' \
  $'    if False:\n        return None'

# ── Paso 4: renovaciones de una suscripción ──
sabotaje $M "el aviso IPN de una renovación se ignora" \
  '            if topic in ("payment", "subscription_authorized_payment"):' \
  '            if topic in ("payment",):' \
  "FAILED $T::test_una_renovacion_extiende_el_periodo_una_sola_vez[ipn]"
sabotaje $M "vuelve a decidir el estado que copia el cobro" \
  '    return str(pago["id"]), suscripcion_id' \
  $'    if cobro.get("status") != "approved":\n        raise _CobroMPFormaInesperada("cobro no aprobado")\n    return str(pago["id"]), suscripcion_id' \
  "FAILED $T::test_lo_que_decide_es_el_estado_del_pago_y_no_el_que_copia_el_cobro[sin_estado]"
sabotaje $M "el id del cobro arma cualquier ruta" \
  '_ID_COBRO_MP = re.compile(r"[0-9A-Za-z_-]{1,64}")' \
  '_ID_COBRO_MP = re.compile(r".{0,200}")' \
  "FAILED $T::test_leer_un_cobro_no_arma_una_ruta_con_lo_que_mande_cualquiera"
sabotaje $M "un 500 de Mercado Pago no reintenta" \
  $'    if resp.status_code != 200:\n        raise _CobroMPIlegible(' \
  $'    if False:\n        raise _CobroMPIlegible(' \
  "FAILED $T::test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada[http_500]"
sabotaje $M "sin conexión no reintenta" \
  $'    except httpx.HTTPError as e:\n        raise _CobroMPIlegible(' \
  $'    except KeyError as e:\n        raise _CobroMPIlegible(' \
  "FAILED $T::test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada[sin_conexion]"
sabotaje $M "una respuesta que no es JSON rompe" \
  $'    except ValueError as e:\n        raise _CobroMPFormaInesperada(f"{cobro_id}: la respuesta no es JSON") from e' \
  $'    except KeyError as e:\n        raise _CobroMPFormaInesperada(f"{cobro_id}: la respuesta no es JSON") from e' \
  "FAILED $T::test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada[no_es_json]"
sabotaje $M "un id de pago booleano pasa" \
  '            or isinstance(pago.get("id"), bool) or not str(pago.get("id")):' \
  '            or not str(pago.get("id")):' \
  "FAILED $T::test_un_cobro_con_forma_inesperada_no_aplica_nada[pago_id_booleano]"
sabotaje $M "un cobro sin suscripción pasa" \
  '    if not isinstance(suscripcion_id, str) or not suscripcion_id:' \
  '    if False:' \
  "FAILED $T::test_un_cobro_con_forma_inesperada_no_aplica_nada[sin_suscripcion]"
sabotaje $M "la renovación no toma la referencia de la suscripción" \
  '                pay_resp["external_reference"] = ref' \
  '                pass' \
  "FAILED $T::test_una_renovacion_extiende_el_periodo_una_sola_vez[ipn]"
sabotaje $M "la suscripción ilegible de una renovación no reintenta" \
  '                if not isinstance(resp_sus, dict) or resp_sus.get("status") != 200:' \
  '                if not isinstance(resp_sus, dict):' \
  "FAILED $T::test_si_no_se_puede_leer_la_suscripcion_de_una_renovacion_reintenta"
sabotaje $M "una suscripción sin referencia sigue" \
  '                if not isinstance(ref, str) or not ref:' \
  '                if False:' \
  "FAILED $T::test_una_renovacion_de_una_suscripcion_sin_referencia_no_aplica_nada[None]"
sabotaje $M "el pago de la renovación no se ata a su suscripción" \
  '            pay_resp = {**pay_resp, "preapproval_id": suscripcion_del_cobro}' \
  '            pay_resp = dict(pay_resp)' \
  "FAILED $T::test_una_renovacion_cuyo_pago_dice_otra_cuenta_no_se_aplica"

# ── Devolución de los adversarios: el id del pago ──
sabotaje $M "el id del aviso arma cualquier ruta" \
  $'            if not _ID_COBRO_MP.fullmatch(payment_id):\n                logger.warning("Webhook MP: payment_id inválido %r", payment_id[:80])' \
  $'            if False:\n                logger.warning("Webhook MP: payment_id inválido %r", payment_id[:80])' \
  "FAILED $T::test_un_id_con_barras_no_llega_a_mercado_pago"
sabotaje $M "el pago se anota con el id del aviso y no con el de Mercado Pago" \
  '        canonico = pay_resp.get("id")' \
  '        canonico = payment_id' \
  "FAILED $T::test_el_mismo_pago_escrito_de_otra_forma_no_se_aplica_otra_vez[cero]"
sabotaje $M "un pago aprobado sin id reconocible se anota igual" \
  $'            return {"success": True, "skipped": "pago con forma inesperada"}' \
  $'            payment_id = str(canonico)' \
  "FAILED $T::test_un_pago_aprobado_sin_id_reconocible_no_se_aplica[nulo]"
sabotaje $M "el último pago de antes del registro vuelve a aplicarse (usuario)" \
  '            if db_user.last_payment_id == payment_id:' \
  '            if False:' \
  "FAILED $T::test_el_ultimo_pago_de_antes_del_registro_no_se_aplica_otra_vez[usuario]"
sabotaje $M "el último pago de antes del registro vuelve a aplicarse (organización)" \
  '                if db_org.last_payment_id == payment_id:' \
  '                if False:' \
  "FAILED $T::test_el_ultimo_pago_de_antes_del_registro_no_se_aplica_otra_vez[organizacion]"
sabotaje $M "sin token, la renovación se da por procesada" \
  '        if event_type in ("payment", "subscription_authorized_payment"):' \
  $'        if event_type == "subscription_authorized_payment" and not MP_ACCESS_TOKEN:\n            return {"success": True, "skipped": "not a payment event"}\n        if event_type in ("payment", "subscription_authorized_payment"):' \
  "FAILED $T::test_sin_token_el_aviso_de_una_renovacion_no_se_pierde"

# A: ningún pago de antes del registro se vuelve a aplicar, sea o no el último.
C=proyecto_maria/database/connection.py
sabotaje $M "sin el control de fecha, un pago viejo se aplica otra vez" \
  '            control = await _control_de_fecha_mp(session, pay_resp, control)' \
  '            pass' \
  "FAILED $T::test_un_pago_viejo_que_no_es_el_ultimo_no_se_aplica_otra_vez[usuario]"
sabotaje $M "una fecha sin zona se acepta" \
  '    if aprobado is None or aprobado.tzinfo is None:' \
  '    if aprobado is None:' \
  "FAILED $T::test_un_pago_sin_fecha_de_aprobacion_legible_no_se_aplica[sin_zona]"
sabotaje $C "el inicio del registro es siempre ahora" \
  '    conn.execute(inicio.insert().values(id=1, desde=desde or datetime.now(timezone.utc)))' \
  '    conn.execute(inicio.insert().values(id=1, desde=datetime.now(timezone.utc)))' \
  "FAILED $T::test_el_inicio_del_registro_es_el_primer_pago_registrado_y_no_se_mueve"
sabotaje $C "el inicio del registro se mueve al rearrancar" \
  $'    if conn.execute(select(inicio.c.id).where(inicio.c.id == 1)).first() is not None:\n        return\n' \
  $'    conn.execute(inicio.delete())\n' \
  "el inicio del registro se movió al rearrancar"

# ── Devolución del 2026-10-28: B, C, D y E ──
# B: la exportación cuenta la operación (tests/test_cobro_corte1.py).
T=tests/test_cobro_corte1.py
sabotaje $M "B: la exportación no cuenta la operación" \
  $'        await _contar_maria(db, user["username"], filename, txt_content,\n                            len(request.items or []))\n\n        with open(filepath, \'w\', encoding=\'utf-8\') as f:' \
  $'        with open(filepath, \'w\', encoding=\'utf-8\') as f:' \
  "la exportación no cuenta la operación"

# C y E: cancelar desde past_due y reactivar una prueba con recarga.
T=tests/test_cobro_mp1_cde.py
sabotaje $M "C: past_due no puede cancelar" \
  '    if db_user.billing_status not in ("trial", "active", "past_due") and not cancelada_con_suscripcion:' \
  '    if db_user.billing_status not in ("trial", "active") and not cancelada_con_suscripcion:' \
  "past_due no se puede cancelar"
sabotaje $M "C: cancelar desde past_due deja los días que quedaban" \
  '            db_user.trial_ends_at = ahora' \
  '            pass' \
  "cancelar desde past_due da acceso"
sabotaje $M "E: decide payment_provider aunque haya pagos registrados" \
  $'    if not tipos:\n        return db_user.payment_provider == "mercadopago"\n' \
  $'    return db_user.payment_provider == "mercadopago"\n' \
  "una prueba con recarga no vuelve a la prueba"
sabotaje $M "E: la recarga cuenta como plan pagado" \
  '    return any(tipo != "topup" for tipo in tipos)' \
  '    return bool(tipos)' \
  "una prueba con recarga no vuelve a la prueba"
sabotaje $M "E: un pago rechazado cuenta como plan" \
  $',\n               PagoMercadoPagoAplicado.estado == "aplicado")' \
  ')' \
  "un plan rechazado cuenta como plan"
# Lo de antes: un rechazo hace que la cuenta tenga filas y deja de decidir
# payment_provider.
sabotaje $M "E: un rechazo saca la decisión de payment_provider" \
  $'               PagoMercadoPagoAplicado.estado == "aplicado")\n    )).scalars().all()\n    if not tipos:' \
  $'               PagoMercadoPagoAplicado.estado == "aplicado")\n    )).scalars().all()\n    if not tipos and not (await db.execute(select(PagoMercadoPagoAplicado.payment_id).where(PagoMercadoPagoAplicado.cuenta == db_user.username))).first():' \
  "una cuenta pagada volvió como prueba"

# La cancelada que reabrió el checkout (hallazgo del adversario Opus).
sabotaje $M "C: una cancelada con suscripción nueva no puede cancelarla" \
  ' and not cancelada_con_suscripcion:' \
  ':' \
  "la suscripción nueva no se puede cancelar"
sabotaje $M "C: una cancelada sin suscripción vuelve a cancelar" \
  '    cancelada_con_suscripcion = db_user.billing_status == "canceled" and db_user.mp_preapproval_id' \
  '    cancelada_con_suscripcion = db_user.billing_status == "canceled"' \
  "assert 200 == 409"
sabotaje $M "C: /billing/me nunca dice que hay suscripción abierta" \
  '        "suscripcion_abierta": db_user.billing_status == "canceled" and bool(db_user.mp_preapproval_id),' \
  '        "suscripcion_abierta": False,' \
  "cancelada_con_checkout"
sabotaje $M "C: /billing/me dice abierta a cualquier cancelada" \
  '        "suscripcion_abierta": db_user.billing_status == "canceled" and bool(db_user.mp_preapproval_id),' \
  '        "suscripcion_abierta": db_user.billing_status == "canceled",' \
  "cancelada_sin"

# D, el backend: la carrera de dos checkouts en un Postgres 16 descartable.
T=scripts/testing/cobro_mp1d_postgres.py
correr() {
  PY="$PY" timeout 300 scripts/testing/con_pg16.sh bash -c '"$0" "$1" "$BACKUP1A_PG_URL"' "$PY" "$T" 2>&1
}
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | la carrera en Postgres ya está en rojo (o no hay Postgres 16): no se puede medir D"; FALLAS=$((FALLAS+1))
else
  echo "BASE  | la carrera en Postgres, en verde"
  sabotaje $M "D: el checkout no bloquea la cuenta" \
    '    result = await db.execute(select(User).where(User.username == username).with_for_update())' \
    '    result = await db.execute(select(User).where(User.username == username))' \
    "FALLA | sin suscripción anterior: queda una sola suscripción viva en Mercado Pago"
  sabotaje $M "D: cancelar no espera al checkout en curso" \
    '    result = await db.execute(select(User).where(User.username == user["username"]).with_for_update())' \
    '    result = await db.execute(select(User).where(User.username == user["username"]))' \
    "FALLA | cancelar durante un checkout: no queda ninguna suscripción viva en Mercado Pago"
fi

# C y D en el perfil: la pantalla, con la API levantada desde el worktree y
# una base vacía en cada corrida.
P=proyecto_maria/static/v2/screens/profile.js
APP=proyecto_maria/static/v2/app_v2.js
PUERTO="${PUERTO:-8854}"
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -f -- "$TMPD/local.db" "$TMPD/api.log"; rmdir "$TMPD"' EXIT
correr() {
  rm -f -- "$TMPD/local.db"
  ENVIRONMENT=development JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef \
  EMAIL_VERIFICATION_REQUIRED=false ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x \
  ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x DATABASE_URL="sqlite+aiosqlite:///$TMPD/local.db" \
    "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1 && break; sleep 1; done
  if ! curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1; then
    echo "FALLA: la API no levantó"; tail -5 "$TMPD/api.log"; kill $API 2>/dev/null; wait $API 2>/dev/null; API=""; return 1
  fi
  local codigo
  BASE_URL="http://127.0.0.1:$PUERTO" node scripts/testing/pantalla_cobro_mp1.js 2>&1; codigo=$?
  kill $API 2>/dev/null; wait $API 2>/dev/null; API=""
  return $codigo
}
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; FALLAS=$((FALLAS+1))
else
  echo "BASE  | la pantalla, en verde"
  sabotaje $P "C: past_due no muestra «Cancelar plan»" \
    "        if (status === 'trial' || status === 'active' || status === 'past_due'" \
    "        if (status === 'trial' || status === 'active'" \
    "FALLA: past_due: no se ve «Cancelar plan»"
  sabotaje $P "C: una cancelada con suscripción abierta no ve «Cancelar plan»" \
    "            || (status === 'canceled' && b && b.suscripcion_abierta)) {" \
    "            || false) {" \
    "FALLA: canceled con suscripción abierta: no se ve «Cancelar plan»"
  sabotaje $P "C: cualquier cancelada ve «Cancelar plan»" \
    "            || (status === 'canceled' && b && b.suscripcion_abierta)) {" \
    "            || (status === 'canceled')) {" \
    "FALLA: canceled sin suscripción: se ve «Cancelar plan»"
  sabotaje $P "C: la confirmación de past_due promete el período ya pagado" \
    "        const vencido = billingStatusEl && billingStatusEl.dataset.status === 'past_due';" \
    "        const vencido = false;" \
    "FALLA: past_due: la confirmación promete el período ya pagado"
  sabotaje $P "C: el botón de aceptar vuelve a confirmText" \
    "            acceptText: 'Sí, cancelar'," \
    "            confirmText: 'Sí, cancelar'," \
    "FALLA: past_due: el botón de aceptar dice"
  sabotaje $APP "D: irAlCheckout no deshabilita el botón" \
    "        boton.disabled = true;" \
    "" \
    "FALLA: el botón «Activar plan» no se deshabilita mientras pide el checkout"
  sabotaje $APP "D: el botón no vuelve después del error" \
    "        boton.disabled = false;" \
    "" \
    "FALLA: el botón «Activar plan» no vuelve a su estado después del error"
  sabotaje $APP "D: irAlCheckout rehabilita el botón al ir a Mercado Pago" \
    "                window.location.href = data.init_point;" \
    "                boton.disabled = false; window.location.href = data.init_point;" \
    "FALLA: «Activar plan» se vuelve a habilitar mientras el navegador va a Mercado Pago"
  sabotaje $P "D: «Reactivar plan» se rehabilita al ir a Mercado Pago" \
    "if (seguir && await CDI.irAlCheckout(planElegido(), billingReactivateBtn)) return;" \
    "if (seguir && await CDI.irAlCheckout(planElegido(), billingReactivateBtn)) { billingReactivateBtn.disabled = false; return; }" \
    "FALLA: «Reactivar plan» se vuelve a habilitar mientras el navegador va a Mercado Pago"
  sabotaje $APP "D: el aviso rehabilita «Activar plan ahora» al ir a Mercado Pago" \
    "irAlCheckout((user && user.plan) || 'premium', cta);" \
    "irAlCheckout((user && user.plan) || 'premium', cta).then(() => { cta.disabled = false; });" \
    "FALLA: «Activar plan ahora» se vuelve a habilitar mientras el navegador va a Mercado Pago"
  sabotaje $APP "D: volver con «Atrás» no recarga la página" \
    "if (ev.persisted) window.location.reload();" \
    "" \
    "FALLA: volver de Mercado Pago con «Atrás» no recarga la página"
  sabotaje $APP "D: otro botón pide un segundo checkout mientras hay uno en curso" \
    "        if (checkoutEnCurso) return false;" \
    "" \
    "FALLA: «Activar plan ahora» y después «Activar plan» pidieron 2 checkouts"
  sabotaje $APP "D: un checkout fallido deja trabados los demás" \
    "        checkoutEnCurso = false;" \
    "" \
    "FALLA: después de un checkout fallido, «Activar plan» no vuelve a pedirlo"
fi

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
