#!/usr/bin/env bash
# Negativos de COBRO-MP-1 (pasos 1 a 4 y D31): cada sabotaje deshace una línea
# de la pieza y tests/test_cobro_mp1.py tiene que ponerse roja por ese motivo.
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
  '    desde = fin if (getattr(cuenta, "billing_status", None) == "active" and fin and fin > ahora) else ahora' \
  '    desde = ahora' \
  "FAILED $T::test_pagar_con_la_cuenta_activa_extiende_desde_el_fin"
sabotaje $M "una cuenta vencida suma desde el fin viejo" \
  '    desde = fin if (getattr(cuenta, "billing_status", None) == "active" and fin and fin > ahora) else ahora' \
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
  '    if resp.status_code != 200:' \
  '    if False:' \
  "FAILED $T::test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada[http_500]"
sabotaje $M "sin conexión no reintenta" \
  '    except httpx.HTTPError as e:' \
  '    except KeyError as e:' \
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

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
