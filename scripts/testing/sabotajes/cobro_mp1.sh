#!/usr/bin/env bash
# Negativos de COBRO-MP-1 (pasos 1 a 4 y D31): cada sabotaje deshace una línea
# de la pieza y tests/test_cobro_mp1.py o tests/test_cobro_mp1_vuelta2.py
# tienen que ponerse rojas por ese motivo.
# La devolución del 2026-10-28 (B a E) se mide con tests/test_cobro_corte1.py
# (B), tests/test_cobro_mp1_cde.py (C y E), la carrera de D en un Postgres 16
# descartable (scripts/testing/cobro_mp1d_postgres.py, con con_pg16.sh) y la
# pantalla del perfil (scripts/testing/pantalla_cobro_mp1.js; PUERTO, 8854).
# La del 2026-10-29 (vuelta 2, a a g) con tests/test_cobro_mp1_vuelta2.py,
# tests/test_cobro_corte1.py (g), la carrera de a y de D31 en Postgres
# (scripts/testing/cobro_mp1_postgres.py) y la pantalla v1
# (scripts/testing/pantalla_cobro_mp1_v2.js).
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
T1=tests/test_cobro_mp1.py
V=tests/test_cobro_mp1_vuelta2.py
T="$T1 $V"
M=proyecto_maria/main.py
B=proyecto_maria/services/billing_service.py
H=proyecto_maria/templates/dev_dashboard.html

# aplicar <archivo> <original> <saboteado> [<original> <saboteado>…]: vuelve
# todo al SHA y cambia cada texto, que tiene que estar una sola vez.
aplicar() {
  git checkout -q -- proyecto_maria/
  "$PY" - "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
for viejo, nuevo in zip(sys.argv[2::2], sys.argv[3::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w").write(s)
PYEOF
}

# shellcheck disable=SC2086  # $T son varios archivos
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider $T 2>&1; }

# sabotaje <archivo> <nombre> <original> <saboteado> [<original> <saboteado>…] <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" esperado="${!#}"
  if ! aplicar "$archivo" "${@:3:$#-3}"; then
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
REGISTRO='            estado = await _registrar_pago_mp(session, payment_id, cuenta_ref, update, pay_resp, control)'
sabotaje $M "un pago ya aplicado vuelve a aplicarse (usuario)" \
  "$REGISTRO" '            estado = "aplicado"' \
  "FAILED $T1::test_alternar_dos_pagos_viejos_no_renueva"
sabotaje $M "un pago ya aplicado vuelve a aplicarse (organización)" \
  "$REGISTRO" '            estado = "aplicado"' \
  "FAILED $T1::test_organizacion_alternar_dos_pagos_viejos_no_renueva"
sabotaje $M "el pago se registra sin su tipo" \
  '        tipo="topup" if update.get("action") == "topup" else str(update.get("plan") or ""),' \
  '        tipo="",' \
  "FAILED $T1::test_el_pago_aplicado_queda_registrado"

# ── Paso 3: el período se extiende desde su fin ──
sabotaje $M "pagar con la cuenta activa vuelve a contar desde hoy" \
  '    desde = fin if (vigente and fin and fin > ahora) else ahora' \
  '    desde = ahora' \
  "FAILED $T1::test_pagar_con_la_cuenta_activa_extiende_desde_el_fin"
sabotaje $M "una cuenta vencida suma desde el fin viejo" \
  '    desde = fin if (vigente and fin and fin > ahora) else ahora' \
  '    desde = fin if fin else ahora' \
  "FAILED $T1::test_pagar_con_la_cuenta_vencida_cuenta_desde_hoy"
sabotaje $M "la organización vuelve a contar desde hoy" \
  '            _extender_periodo(cuenta, update)' \
  '            pass' \
  "FAILED $T1::test_organizacion_pagar_activa_extiende_desde_el_fin"

# ── Paso 2: el monto se controla (D29) ──
sabotaje $M "se acepta otra moneda" \
  '    if moneda != "ARS":' \
  '    if False:' \
  "FAILED $T1::test_un_plan_en_otra_moneda_no_se_aplica"
sabotaje $M "no se compara lo pagado con el precio" \
  '    if pagado is None or pagado + 0.005 < esperado:' \
  '    if pagado is None:' \
  "FAILED $T1::test_un_plan_pagado_de_menos_no_se_aplica_y_queda_rechazado"
sabotaje $M "el precio de la recarga sin link es otro" \
  '                esperado = float(billing_service.TOPUP_PRICE_ARS)' \
  '                esperado = 1.0' \
  "FAILED $T1::test_una_recarga_pagada_de_menos_no_suma"
sabotaje $M "se ignora el precio de cuando se armó el link" \
  '        esperado = _monto_mp(meta.get("precio_esperado"))' \
  '        esperado = None' \
  "FAILED $T1::test_un_link_con_el_precio_de_cuando_se_armo_se_respeta"
sabotaje $B "el link del plan no guarda el precio" \
  '        "metadata": {"precio_esperado": plan["price"]},' \
  '' \
  "FAILED $T1::test_el_link_de_pago_guarda_el_precio"
sabotaje $B "el link de la recarga no guarda el precio" \
  '        "metadata": {"precio_esperado": TOPUP_PRICE_ARS},' \
  '' \
  "FAILED $T1::test_el_link_de_pago_guarda_el_precio"
sabotaje $M "la suscripción se compara con PLANS y no con su monto" \
  '        esperado = _monto_mp(recurrente.get("transaction_amount"))' \
  '        esperado = float(billing_service.PLANS["premium"]["price"])' \
  "FAILED $T1::test_una_suscripcion_se_compara_con_su_monto_en_mercado_pago"
sabotaje $M "la suscripción de otra cuenta vale" \
  '        if suscripcion.get("external_reference") != external_ref:' \
  '        if False:' \
  "FAILED $T1::test_la_suscripcion_de_otra_cuenta_no_vale"
sabotaje $M "una suscripción ilegible se rechaza en vez de reintentar" \
  $'_consultar_mp(lambda: sdk.preapproval().get(str(suscripcion_id)),\n                                    f"suscripción {suscripcion_id}")' \
  '(sdk.preapproval().get(str(suscripcion_id)).get("response") or {})' \
  "FAILED $T1::test_si_no_se_puede_leer_la_suscripcion_mercado_pago_reintenta"
sabotaje $M "el rechazo no se guarda" \
  '    if await _guardar_pago_mp(session):' \
  '    if True:' \
  "FAILED $T1::test_un_plan_pagado_de_menos_no_se_aplica_y_queda_rechazado"
sabotaje $M "cualquier usuario ve los pagos rechazados" \
  $'async def get_dev_pagos_mp_rechazados(\n    user=Depends(require_admin),' \
  $'async def get_dev_pagos_mp_rechazados(\n    user=Depends(get_current_user),' \
  "FAILED $T1::test_emi_ve_los_pagos_rechazados_y_un_usuario_comun_no"
sabotaje $H "el panel no pide los pagos rechazados" \
  "fetch('/api/dev/pagos-mp-rechazados')" \
  "fetch('/api/dev/pagos')" \
  "FAILED $T1::test_el_panel_muestra_los_pagos_rechazados"

# ── D31: la clave primaria frena el segundo aviso ──
# En SQLite el candado de a no bloquea nada: la carrera llega a la clave.
sabotaje $M "la clave repetida se da por guardada" \
  $'    except IntegrityError:\n        await session.rollback()\n        return False' \
  $'    except IntegrityError:\n        await session.rollback()\n        return True' \
  "FAILED $T1::test_dos_avisos_del_mismo_pago_a_la_vez_se_aplican_una_sola_vez"
sabotaje $M "la clave repetida no se atrapa" \
  $'    try:\n        await session.commit()\n        return True\n    except IntegrityError:\n        await session.rollback()\n        return False' \
  $'    await session.commit()\n    return True' \
  "FAILED $T1::test_dos_avisos_del_mismo_pago_a_la_vez_se_aplican_una_sola_vez"
sin_rojo $M "sin mirar antes de insertar" \
  $'    if await session.get(PagoMercadoPagoAplicado, str(payment_id)) is not None:\n        return None' \
  $'    if False:\n        return None'

# ── Paso 4: renovaciones de una suscripción ──
sabotaje $M "el aviso IPN de una renovación se ignora" \
  '            if topic in ("payment", "subscription_authorized_payment"):' \
  '            if topic in ("payment",):' \
  "FAILED $T1::test_una_renovacion_extiende_el_periodo_una_sola_vez[ipn]"
sabotaje $M "vuelve a decidir el estado que copia el cobro" \
  '    suscripcion_id = cobro.get("preapproval_id")' \
  $'    if cobro.get("status") != "approved":\n        raise _MPIlegible("cobro no aprobado")\n    suscripcion_id = cobro.get("preapproval_id")' \
  "FAILED $T1::test_lo_que_decide_es_el_estado_del_pago_y_no_el_que_copia_el_cobro[sin_estado]"
sabotaje $M "el id del cobro arma cualquier ruta" \
  '_ID_COBRO_MP = re.compile(r"[0-9A-Za-z_-]{1,64}")' \
  '_ID_COBRO_MP = re.compile(r".{0,200}")' \
  "FAILED $T1::test_leer_un_cobro_no_arma_una_ruta_con_lo_que_mande_cualquiera"
sabotaje $M "un 500 de Mercado Pago no reintenta" \
  $'    if resp.status_code != 200:\n        raise _MPIlegible(f"cobro' \
  $'    if False:\n        raise _MPIlegible(f"cobro' \
  "FAILED $T1::test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada[http_500]"
sabotaje $M "sin conexión no reintenta" \
  $'    except httpx.HTTPError as e:\n        raise _MPIlegible(f"cobro' \
  $'    except KeyError as e:\n        raise _MPIlegible(f"cobro' \
  "FAILED $T1::test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada[sin_conexion]"
sabotaje $M "una respuesta que no es JSON rompe" \
  $'    except ValueError as e:\n        raise _MPIlegible(f"cobro {cobro_id}: la respuesta no es JSON")' \
  $'    except KeyError as e:\n        raise _MPIlegible(f"cobro {cobro_id}: la respuesta no es JSON")' \
  "FAILED $T1::test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada[no_es_json]"
sabotaje $M "un id de pago booleano pasa" \
  ' or isinstance(pago_id, bool)' \
  '' \
  "FAILED $V::test_una_renovacion_que_todavia_no_dice_que_pago_fue_reintenta[pago_id_booleano]"
sabotaje $M "un cobro sin suscripción se aplica" \
  '        if renovacion and not suscripcion_del_cobro:' \
  '        if False:' \
  "FAILED $V::test_un_cobro_con_su_pago_y_sin_suscripcion_legible_queda_rechazado[sin_suscripcion]"
sabotaje $M "una suscripción que no es texto se toma" \
  '(suscripcion_id if isinstance(suscripcion_id, str) and suscripcion_id else None)' \
  '(suscripcion_id or None)' \
  "FAILED $V::test_un_cobro_con_su_pago_y_sin_suscripcion_legible_queda_rechazado[suscripcion_no_es_texto]"
sabotaje $M "la renovación no toma la referencia de la suscripción" \
  '                pay_resp["external_reference"] = sus.get("external_reference")' \
  '                pass' \
  "FAILED $T1::test_una_renovacion_extiende_el_periodo_una_sola_vez[ipn]"
sabotaje $M "la suscripción ilegible de una renovación no reintenta" \
  $'_consultar_mp(lambda: sdk.preapproval().get(suscripcion_del_cobro),\n                                    f"suscripción {suscripcion_del_cobro}")' \
  '(sdk.preapproval().get(suscripcion_del_cobro).get("response") or {})' \
  "FAILED $T1::test_si_no_se_puede_leer_la_suscripcion_de_una_renovacion_reintenta"
sabotaje $M "el pago de la renovación no se ata a su suscripción" \
  '            pay_resp = {**pay_resp, "preapproval_id": suscripcion_del_cobro}' \
  '            pay_resp = dict(pay_resp)' \
  "FAILED $T1::test_una_renovacion_cuyo_pago_dice_otra_cuenta_no_se_aplica"

# ── Devolución de los adversarios: el id del pago ──
sabotaje $M "el id del aviso arma cualquier ruta" \
  $'            if not _ID_COBRO_MP.fullmatch(payment_id):\n                logger.warning("Webhook MP: payment_id inválido %r", payment_id[:80])' \
  $'            if False:\n                logger.warning("Webhook MP: payment_id inválido %r", payment_id[:80])' \
  "FAILED $T1::test_un_id_con_barras_no_llega_a_mercado_pago"
sabotaje $M "el pago se anota con el id del aviso y no con el de Mercado Pago" \
  '        canonico = pay_resp.get("id")' \
  '        canonico = payment_id' \
  "FAILED $T1::test_el_mismo_pago_escrito_de_otra_forma_no_se_aplica_otra_vez[cero]"
sabotaje $M "un pago aprobado sin id reconocible se anota igual" \
  '            raise _MPIlegible(f"pago aprobado sin id reconocible: {str(canonico)[:80]!r}")' \
  '            payment_id = str(canonico)' \
  "FAILED $V::test_un_pago_aprobado_sin_id_reconocible_reintenta[nulo]"
sabotaje $M "el último pago de antes del registro vuelve a aplicarse (usuario)" \
  '            if cuenta.last_payment_id == payment_id:' \
  '            if False:' \
  "FAILED $T1::test_el_ultimo_pago_de_antes_del_registro_no_se_aplica_otra_vez[usuario]"
sabotaje $M "el último pago de antes del registro vuelve a aplicarse (organización)" \
  '            if cuenta.last_payment_id == payment_id:' \
  '            if False:' \
  "FAILED $T1::test_el_ultimo_pago_de_antes_del_registro_no_se_aplica_otra_vez[organizacion]"
sabotaje $M "sin token, la renovación se da por procesada" \
  '        if event_type in ("payment", "subscription_authorized_payment"):' \
  $'        if event_type == "subscription_authorized_payment" and not MP_ACCESS_TOKEN:\n            return {"success": True, "skipped": "not a payment event"}\n        if event_type in ("payment", "subscription_authorized_payment"):' \
  "FAILED $T1::test_sin_token_el_aviso_de_una_renovacion_no_se_pierde"

# A: ningún pago de antes del registro se vuelve a aplicar, sea o no el último.
C=proyecto_maria/database/connection.py
sabotaje $M "sin el control de fecha, un pago viejo se aplica otra vez" \
  '            control = await _control_de_fecha_mp(session, pay_resp, control)' \
  '            pass' \
  "FAILED $T1::test_un_pago_viejo_que_no_es_el_ultimo_no_se_aplica_otra_vez[usuario]"
sabotaje $M "una fecha sin zona se acepta" \
  '    if aprobado is None or aprobado.tzinfo is None:' \
  '    if aprobado is None:' \
  "FAILED $T1::test_un_pago_sin_fecha_de_aprobacion_legible_no_se_aplica[sin_zona]"
sabotaje $C "el inicio del registro es siempre ahora" \
  '    conn.execute(inicio.insert().values(id=1, desde=desde or datetime.now(timezone.utc)))' \
  '    conn.execute(inicio.insert().values(id=1, desde=datetime.now(timezone.utc)))' \
  "FAILED $T1::test_el_inicio_del_registro_es_el_primer_pago_registrado_y_no_se_mueve"
sabotaje $C "el inicio del registro se mueve al rearrancar" \
  $'    if conn.execute(select(inicio.c.id).where(inicio.c.id == 1)).first() is not None:\n        return\n' \
  $'    conn.execute(inicio.delete())\n' \
  "el inicio del registro se movió al rearrancar"

# ── Vuelta 2, b: una sola regla para lo que se lee de Mercado Pago ──
# No se pudo leer: 503 y una línea de log. Se leyó y no sirve: rechazado y 200.
sabotaje $M "b: un 4xx de Mercado Pago se toma como pago" \
  ' or resp.get("status") != 200' \
  '' \
  "FAILED $V::test_si_no_se_puede_leer_el_pago_mercado_pago_reintenta[http_404]"
sabotaje $M "b: una excepción del SDK da 500" \
  $'    except Exception as e:\n        raise _MPIlegible(f"{que}' \
  $'    except KeyError as e:\n        raise _MPIlegible(f"{que}' \
  "FAILED $V::test_si_no_se_puede_leer_el_pago_mercado_pago_reintenta[excepcion]"
sabotaje $M "b: una respuesta que no es un objeto da 500" \
  ' or not isinstance(resp.get("response"), dict)' \
  '' \
  "FAILED $V::test_si_no_se_puede_leer_el_pago_mercado_pago_reintenta[response_no_es_dict]"
sabotaje $M "b: el 503 no deja una línea de log" \
  '        logger.warning("Webhook MP: no se pudo leer Mercado Pago (%s); reintentará", e)' \
  '        pass' \
  "no quedó una línea de log"
sabotaje $M "b: un pago de una cuenta que no existe da 400" \
  $'                return await _rechazar_sin_cuenta_mp(session, payment_id, cuenta_ref, update, pay_resp,\n                                                     f"la cuenta {cuenta_ref} no existe")' \
  '                raise HTTPException(status_code=400, detail="x")' \
  "FAILED $V::test_un_pago_de_una_cuenta_que_no_existe_queda_rechazado[usuario]"
sabotaje $M "b: una referencia que no es texto da 500" \
  '            if isinstance(external_ref, str) and "|" in external_ref:' \
  '            if "|" in external_ref:' \
  "FAILED $V::test_un_pago_con_referencia_que_no_sirve_queda_rechazado[numero]"
sabotaje $M "b: una referencia desconocida no queda rechazada" \
  '                motivo = f"external_reference desconocida: {str(external_ref)[:80]!r}"' \
  '                return {"success": True, "skipped": "x"}' \
  "FAILED $V::test_un_pago_con_referencia_que_no_sirve_queda_rechazado[nula]"
sabotaje $M "b: el formato viejo sin payer da 500" \
  'str(billing_service._objeto(pay_resp, "payer").get("id", "") or payment_id)' \
  'str(pay_resp.get("payer").get("id", "") or payment_id)' \
  "FAILED $V::test_el_formato_viejo_con_barra_y_sin_payer_se_aplica"
sabotaje $B "b: el usuario «org» no puede pagar" \
  '    elif len(parts) == 2 and parts[0]:' \
  '    elif len(parts) == 2 and parts[0] and parts[0] != "org":' \
  "FAILED $V::test_el_usuario_org_puede_pagar"
sabotaje $B "b: un dato secundario nulo da 500" \
  '    return valor if isinstance(valor, dict) else {}' \
  '    return valor' \
  "FAILED $V::test_un_pago_con_un_dato_secundario_nulo_se_aplica[payer]"

# ── Vuelta 2, e: lo que no mataban los sabotajes de antes ──
sabotaje $M "e: sin el inicio del registro sigue de largo" \
  '        raise HTTPException(status_code=503, detail="Registro de pagos no inicializado. MP reintentará.")' \
  '        return control' \
  "FAILED $V::test_sin_el_inicio_del_registro_no_se_aplica_nada"
sabotaje $M "e: el corte deja pasar lo de un rato antes" \
  '    if aprobado < desde:' \
  '    if aprobado < desde - timedelta(seconds=5):' \
  "FAILED $V::test_el_corte_del_registro_no_tiene_margen[un_segundo_antes]"
sabotaje $M "e: el corte rechaza lo de un rato después" \
  '    if aprobado < desde:' \
  '    if aprobado < desde + timedelta(seconds=5):' \
  "FAILED $V::test_el_corte_del_registro_no_tiene_margen[un_segundo_despues]"
sabotaje $M "e: pagar de más se rechaza" \
  '    if pagado is None or pagado + 0.005 < esperado:' \
  '    if pagado is None or abs(pagado - esperado) > 0.005:' \
  "FAILED $V::test_pagar_de_mas_se_aplica"
sabotaje $M "e: una cuenta en mora suma desde su fin" \
  '    vigente = getattr(cuenta, "billing_status", None) in ("trial", "active", "canceled")' \
  '    vigente = getattr(cuenta, "billing_status", None) in ("trial", "active", "canceled", "past_due")' \
  "FAILED $V::test_una_cuenta_en_mora_con_fin_por_delante_suma_desde_hoy"
sabotaje $M "e: el registro de una organización no dice «org:»" \
  '            cuenta_ref = f"org:{org_id}" if org_id else update["username"]' \
  '            cuenta_ref = str(org_id) if org_id else update["username"]' \
  "FAILED $V::test_el_registro_de_un_pago_de_organizacion_dice_que_es_una_organizacion"
sabotaje $M "e: el panel muestra los rechazados del más viejo al más nuevo" \
  '        .order_by(desc(_Pago.aplicado_en)).limit(200)' \
  '        .order_by(_Pago.aplicado_en).limit(200)' \
  "FAILED $V::test_el_panel_muestra_los_ultimos_200_rechazados_del_mas_nuevo_al_mas_viejo"
sabotaje $M "e: el panel muestra menos de 200 rechazados" \
  '        .order_by(desc(_Pago.aplicado_en)).limit(200)' \
  '        .order_by(desc(_Pago.aplicado_en)).limit(50)' \
  "FAILED $V::test_el_panel_muestra_los_ultimos_200_rechazados_del_mas_nuevo_al_mas_viejo"
sabotaje $H "e: el panel no nombra el tope de la recarga" \
  'la recarga superaba el tope de operaciones extra, ' \
  '' \
  "FAILED $V::test_el_panel_nombra_todos_los_motivos_de_rechazo"
sabotaje $H "e: el panel no nombra la fecha" \
  'su fecha es anterior al registro de pagos o no se lee, ' \
  '' \
  "FAILED $V::test_el_panel_nombra_todos_los_motivos_de_rechazo"

# ── Vuelta 2, f: el tope de 100 operaciones extra ──
sabotaje $M "f: una recarga que no entra se suma" \
  '                if vigentes + update["extra_ops_remaining"] > billing_service.EXTRA_OPS_MAX:' \
  '                if False:' \
  "FAILED $V::test_una_recarga_que_no_entra_queda_rechazada_y_no_suma[95-usuario]"
sabotaje $M "f: una recarga que llega justo a 100 se rechaza" \
  '                if vigentes + update["extra_ops_remaining"] > billing_service.EXTRA_OPS_MAX:' \
  '                if vigentes + update["extra_ops_remaining"] >= billing_service.EXTRA_OPS_MAX:' \
  "FAILED $V::test_una_recarga_que_entra_suma_entera[llega_justo_a_100]"
sabotaje $M "f: el webhook cuenta los extras vencidos" \
  '                billing_service._expire_extra_ops(cuenta)' \
  '                pass' \
  "FAILED $V::test_una_recarga_que_entra_suma_entera[los_vencidos_no_cuentan]"
sabotaje $M "f: con el tope lleno se arma el link" \
  '    if vigentes + billing_service.TOPUP_OPS > billing_service.EXTRA_OPS_MAX:' \
  '    if False:' \
  "FAILED $V::test_con_el_tope_lleno_no_se_arma_el_link_de_recarga[95-usuario]"
sabotaje $M "f: el link mira los extras del usuario y no los de su organización" \
  '    vigentes = entidad.extra_ops_remaining or 0' \
  '    vigentes = db_user.extra_ops_remaining or 0' \
  "FAILED $V::test_con_el_tope_lleno_no_se_arma_el_link_de_recarga[95-organizacion]"
sabotaje $M "f: el link cuenta los extras vencidos" \
  '    billing_service._expire_extra_ops(entidad)' \
  '    pass' \
  "FAILED $V::test_con_los_extras_vencidos_se_puede_recargar[usuario]"

# ── Devolución del 2026-10-28: B, C, D y E ──
# B: la exportación cuenta la operación (tests/test_cobro_corte1.py).
T=tests/test_cobro_corte1.py
sabotaje $M "B: la exportación no cuenta la operación" \
  $'        await _contar_maria(db, user["username"], filename, txt_content,\n                            len(request.items or []))\n\n        with open(filepath, \'w\', encoding=\'utf-8\') as f:' \
  $'        with open(filepath, \'w\', encoding=\'utf-8\') as f:' \
  "la exportación no cuenta la operación"
# Vuelta 2, g: los ids de la exportación no chocan con los de la importación.
sabotaje $M "g: la exportación usa el prefijo de la importación" \
  '        filename = f"MARIA-EXPORT_{safe_id}.TXT"' \
  '        filename = f"MARIA_EXPORT_{safe_id}.TXT"' \
  "la importación reusó la operación de la exportación"
sabotaje $M "g: un id largo de la exportación no se reconoce" \
  '_ARCHIVO_MARIA = re.compile(r"MARIA(?:_|-EXPORT_)[A-Za-z0-9_-]{1,50}\.TXT")' \
  '_ARCHIVO_MARIA = re.compile(r"MARIA_[A-Za-z0-9_-]{1,50}\.TXT")' \
  "volver a exportar el mismo id largo cuenta otra vez"

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

# Las carreras, en un Postgres 16 descartable: D (dos checkouts) y, de la
# vuelta 2, a (dos pagos de la misma cuenta) y D31 (el mismo pago dos veces).
correr() {
  PY="$PY" timeout 300 scripts/testing/con_pg16.sh bash -c '"$0" "$1" "$BACKUP1A_PG_URL"' "$PY" "$T" 2>&1
}
T=scripts/testing/cobro_mp1d_postgres.py
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | la carrera de D en Postgres ya está en rojo (o no hay Postgres 16): no se puede medir D"; FALLAS=$((FALLAS+1))
else
  echo "BASE  | la carrera de D en Postgres, en verde"
  sabotaje $M "D: el checkout no bloquea la cuenta" \
    '    result = await db.execute(select(User).where(User.username == username).with_for_update())' \
    '    result = await db.execute(select(User).where(User.username == username))' \
    "FALLA | sin suscripción anterior: queda una sola suscripción viva en Mercado Pago"
  sabotaje $M "D: cancelar no espera al checkout en curso" \
    '    result = await db.execute(select(User).where(User.username == user["username"]).with_for_update())' \
    '    result = await db.execute(select(User).where(User.username == user["username"]))' \
    "FALLA | cancelar durante un checkout: no queda ninguna suscripción viva en Mercado Pago"
fi
T=scripts/testing/cobro_mp1_postgres.py
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | los pagos a la vez en Postgres ya están en rojo (o no hay Postgres 16): no se puede medir a"; FALLAS=$((FALLAS+1))
else
  echo "BASE  | los pagos a la vez en Postgres, en verde"
  CANDADO='            cuenta = (await session.execute(consulta.with_for_update())).scalars().first()'
  SIN_CANDADO='            cuenta = (await session.execute(consulta)).scalars().first()'
  sabotaje $M "a: dos pagos de la misma cuenta a la vez, sin candado" \
    "$CANDADO" "$SIN_CANDADO" \
    "FALLA | dos recargas del usuario a la vez: suman 20"
  # Con el candado, el segundo aviso del mismo pago espera y después ve el
  # pago ya anotado: no llega a la clave. Para medir que la clave lo frena hay
  # que sacar también el candado.
  sabotaje $M "D31: sin candado y la clave repetida se da por guardada" \
    "$CANDADO" "$SIN_CANDADO" \
    $'    except IntegrityError:\n        await session.rollback()\n        return False' \
    $'    except IntegrityError:\n        await session.rollback()\n        return True' \
    "FALLA | el mismo pago dos veces a la vez: uno aplicado y otro salteado"
fi

# Las pantallas, con la API levantada desde el worktree y una base vacía en
# cada corrida: C y D en el perfil, y g en la v1.
P=proyecto_maria/static/v2/screens/profile.js
APP=proyecto_maria/static/v2/app_v2.js
V1=proyecto_maria/static/app.js
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
  BASE_URL="http://127.0.0.1:$PUERTO" node "$JS" 2>&1; codigo=$?
  kill $API 2>/dev/null; wait $API 2>/dev/null; API=""
  return $codigo
}
JS=scripts/testing/pantalla_cobro_mp1.js
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | la pantalla del perfil ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; FALLAS=$((FALLAS+1))
else
  echo "BASE  | la pantalla del perfil, en verde"
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
JS=scripts/testing/pantalla_cobro_mp1_v2.js
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | la pantalla v1 ya está en rojo sin sabotaje: no se puede medir g"; correr | grep FALLA; FALLAS=$((FALLAS+1))
else
  echo "BASE  | la pantalla v1, en verde"
  sabotaje $V1 "g: la v1 guarda la operación sin el archivo del MARIA" \
    "        await saveOperationToHistory(items, data.filename);" \
    "        await saveOperationToHistory(items);" \
    "FALLA: import: la pantalla hizo"
fi

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
