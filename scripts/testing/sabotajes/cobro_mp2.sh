#!/usr/bin/env bash
# Negativos de COBRO-MP-2: cada sabotaje deshace una regla de la pieza y la
# prueba (tests/test_cobro_mp2.py, con Mercado Pago simulado, y el caso de la
# cancelada en tests/test_cobro_corte1.py) tiene que fallar en el caso de esa
# regla. Los cruces entre miembros de una organización corren al final en un
# Postgres 16 descartable (scripts/testing/cobro_mp2_postgres.py).
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cobro_mp2.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y sin terceros: no toca
# tu copia ni datos compartidos, y nada sale a Mercado Pago. El perfil
# (profile.js) no tiene prueba en navegador: no hay sabotaje de la pantalla.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
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
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

T=tests/test_cobro_mp2.py
T2=tests/test_cobro_corte1.py
M=proyecto_maria/main.py
B=proyecto_maria/services/billing_service.py
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -W ignore "$T" \
             "$T2::test_la_cancelada_genera_hasta_el_fin_del_periodo" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi
echo "BASE  | en verde"

# --- Cancelar (C2)
sabotaje $M "cancelar no llama a Mercado Pago" \
  "FAILED $T::test_cancelar_cancela_la_suscripcion_en_mp_y_sigue_hasta_el_fin" \
  "            await run_in_threadpool(_cancelar_suscripcion_mp, cuenta.mp_preapproval_id)" "            pass"
sabotaje $M "si Mercado Pago falla, se cancela igual en CDI" \
  "FAILED $T::test_si_mp_no_cancela_no_se_cancela_a_medias" \
  "            await db.commit()
            raise HTTPException(status_code=503, detail=no_se_pudo)" "            await db.commit()"
sabotaje $M "sin token, se cancela igual en CDI" \
  "FAILED $T::test_sin_token_no_cancela_una_suscripcion_a_medias" \
  "    if con_sid and not billing_service.is_configured():
        raise HTTPException(status_code=503, detail=no_se_pudo)" ""
sabotaje $M "si el PUT falla no se pregunta el estado" \
  "FAILED $T::test_si_mp_ya_la_tenia_cancelada_cancelar_sigue" \
  "    except _SuscripcionMPError:
        pass
    if _leer_suscripcion_mp(sid)" "    except _SuscripcionMPError:
        raise
    if _leer_suscripcion_mp(sid)"
sabotaje $M "cancelar sin suscripción llama a Mercado Pago" \
  "FAILED $T::test_cancelar_sin_suscripcion_no_llama_a_mp" \
  "    for cuenta in con_sid:
        try:" "    for cuenta in con_sid or [db_user]:
        try:"
sabotaje $B "la cancelada no sigue hasta el fin del período" \
  "FAILED $T2::test_la_cancelada_genera_hasta_el_fin_del_periodo" \
  "    return fin > (ahora or datetime.now(timezone.utc))" "    return False"

# --- Reactivar pagando (C8, D9, D7.3)
sabotaje $M "reactivar una prueba la deja activa" \
  "FAILED $T::test_cancelar_y_reactivar_una_prueba_no_la_activa" \
  "    entidad.billing_status = \"trial\"
    await db.commit()" "    entidad.billing_status = \"active\"
    await db.commit()"
sabotaje $M "reactivar lo pagado no pasa por el checkout" \
  "FAILED $T::test_reactivar_lo_pagado_lleva_al_checkout_y_dice_que_cobra_ahora" \
  "    if await _pago_un_plan_mp(db, entidad, f\"org:{entidad.id}\" if es_org else db_user.username):" "    if False:"

# --- Una sola suscripción (C4, D7.2)
sabotaje $M "sin el 409 con una suscripción vigente" \
  "FAILED $T::test_el_segundo_checkout_con_una_vigente_se_frena" \
  "        if entidad.billing_status in (\"trial\", \"active\") and fin and fin > datetime.now(timezone.utc):" \
  "        if False:"
# El 409 de la autorizada sin cuenta vigente (D13 de COBRO-MP-1) se sabotea
# en cobro_mp1.sh.
sabotaje $M "la vieja no se cancela antes de crear la nueva" \
  "FAILED $T::test_sin_cuenta_vigente_la_vieja_se_cancela_antes_de_crear[pending]" \
  "if estado_mp != \"cancelled\"]" "if False]"
sabotaje $M "la vieja ya cancelada se vuelve a cancelar" \
  "FAILED $T::test_sin_cuenta_vigente_la_vieja_se_cancela_antes_de_crear[ya_cancelada]" \
  "if estado_mp != \"cancelled\"]" "if True]"
sabotaje $M "si no se puede cancelar la vieja, se crea igual" \
  "FAILED $T::test_si_no_se_puede_cancelar_la_vieja_no_se_crea_nada" \
  "                raise HTTPException(status_code=503, detail=_NO_SE_CONFIRMA_SUSCRIPCION)
            cuenta.mp_preapproval_id = None" "                continue
            cuenta.mp_preapproval_id = None"
sabotaje $M "si no se sabe cómo está la vieja, se crea igual" \
  "FAILED $T::test_si_no_se_sabe_como_esta_la_suscripcion_no_se_crea_otra" \
  "suscripción en MP: {e}\")
        raise HTTPException(status_code=503, detail=_NO_SE_CONFIRMA_SUSCRIPCION)" "suscripción en MP: {e}\")
        estado_mp = \"cancelled\""
sabotaje $M "un estado desconocido de Mercado Pago se acepta" \
  "FAILED $T::test_si_no_se_sabe_como_esta_la_suscripcion_no_se_crea_otra[estado_desconocido]" \
  "    if estado not in _ESTADOS_SUSCRIPCION_MP:" "    if False:"

# --- Una sola suscripción por organización
sabotaje $M "el checkout no mira las suscripciones de los otros miembros" \
  "FAILED $T::test_otro_miembro_no_abre_una_segunda_suscripcion_de_la_org[pending]" \
  "(u is db_user or u.organization_id == org_id)]" "u is db_user]"
sabotaje $M "se cancela una pendiente antes de ver la autorizada de otro" \
  "FAILED $T::test_con_una_autorizada_de_otro_no_se_cancela_ninguna" \
  "    estados = [await _estado_suscripcion_vieja(db, db_user, cuenta) for cuenta in con_sid]
    vivas = [cuenta for cuenta, estado_mp in zip(con_sid, estados) if estado_mp != \"cancelled\"]" \
  "    vivas = list(con_sid)" \
  "            if i:
                # Mientras" "            if True:
                # Mientras"
sabotaje $M "en el checkout, si una no se cancela, las canceladas siguen anotadas" \
  "FAILED $T::test_si_una_de_varias_no_se_cancela_la_cancelada_no_queda_anotada[checkout]" \
  "        # Las ya canceladas no vuelven: se guardan sin el sid.
        await db.commit()
        raise" "        raise"
sabotaje $M "en el checkout, la ya cancelada en Mercado Pago sigue anotada si otra falla" \
  "FAILED $T::test_si_una_no_se_cancela_la_ya_cancelada_en_mp_no_queda_anotada" \
  "    for cuenta in set(con_sid) - set(vivas):" "    for cuenta in ():"
sabotaje $M "no se vuelve a mirar la siguiente después de cancelar una" \
  "FAILED $T::test_la_que_se_autoriza_mientras_se_cancelan_las_otras_no_se_cancela" \
  "            if i:
                # Mientras" "            if False:
                # Mientras"
sabotaje $M "el 409 de la autorizada de otro miembro no dice de quién es" \
  "FAILED $T::test_otro_miembro_no_abre_una_segunda_suscripcion_de_la_org[autorizada_vencida]" \
  "        if cuenta is not db_user:" "        if False:"
sabotaje $M "la suscripción de un miembro no le cobra a la org" \
  "FAILED $T::test_otro_miembro_no_abre_una_segunda_suscripcion_de_la_org[pending]" \
  "create_checkout(db_user, plan_id, org_id=org_id)" "create_checkout(db_user, plan_id, org_id=None)"
sabotaje $M "si el PUT contesta sin cancelar, se da por cancelada" \
  "FAILED $T::test_si_mp_no_cancela_no_se_cancela_a_medias[contesta_sin_cancelar]" \
  "{\"status\": \"cancelled\"}) == \"cancelled\":" "{\"status\": \"cancelled\"}):"

# --- Cancelar y reactivar en una organización
sabotaje $M "en una org, cancelar cambia al usuario y no a la org" \
  "FAILED $T::test_en_una_org_cancelar_cancela_la_suscripcion_y_sigue_hasta_el_fin" \
  "    entidad = org or db_user" "    entidad = db_user"
sabotaje $M "en una org, cualquier miembro cancela el plan" \
  "FAILED $T::test_en_una_org_un_miembro_que_no_la_abrio_no_la_cancela" \
  "    if miembro and db_user not in con_sid:" "    if False:"
sabotaje $M "en una org, un miembro con una pendiente propia cancela el plan" \
  "FAILED $T::test_un_miembro_cuya_suscripcion_no_paga_no_cancela_el_plan_del_estudio[pending-403]" \
  "    if miembro:
        # Una pendiente" "    if False:
        # Una pendiente"
sabotaje $M "en una org, quien abrió una suscripción pausada no la cancela" \
  "FAILED $T::test_en_una_org_cancelar_cancela_la_suscripcion_y_sigue_hasta_el_fin[abrio-paused]" \
  "if estado_mp not in (\"authorized\", \"paused\"):" "if estado_mp not in (\"authorized\",):"
sabotaje $M "en una org, si no se lee la del miembro, cancela igual" \
  "FAILED $T::test_un_miembro_cuya_suscripcion_no_paga_no_cancela_el_plan_del_estudio[_contesta_500-503]" \
  "        except _SuscripcionMPError:
            raise HTTPException(status_code=503, detail=no_se_pudo)
        if estado_mp" "        except _SuscripcionMPError:
            estado_mp = \"authorized\"
        if estado_mp"
sabotaje $M "en una org, reactivar mira al usuario y no a la org" \
  "FAILED $T::test_en_una_org_reactivar_lo_pagado_lleva_al_checkout" \
  "    entidad, es_org = await _get_billing_entity(db, db_user)

    if entidad.billing_status != \"canceled\":" "    entidad, es_org = db_user, False

    if entidad.billing_status != \"canceled\":"
sabotaje $M "si una de varias no se cancela, las canceladas siguen anotadas" \
  "FAILED $T::test_si_una_de_varias_no_se_cancela_la_cancelada_no_queda_anotada[cancelar]" \
  "            await db.commit()
            raise HTTPException(status_code=503, detail=no_se_pudo)" "            raise HTTPException(status_code=503, detail=no_se_pudo)"
sabotaje $M "en una org, los pagos se buscan con el nombre del usuario" \
  "FAILED $T::test_en_una_org_reactivar_lo_pagado_lleva_al_checkout[topup-trial]" \
  "f\"org:{entidad.id}\" if es_org else db_user.username):" "db_user.username):"
sabotaje $M "se saca del estudio a quien abrió la suscripción" \
  "FAILED $T::test_no_se_saca_del_estudio_a_quien_abrio_la_suscripcion" \
  "    if member.mp_preapproval_id:" "    if False:"

# --- Un pago no pierde días (D7.1)
sabotaje $M "el pago suma desde el fin sólo si está activa" \
  "FAILED $T::test_un_pago_suma_desde_el_fin_del_periodo" \
  "in (\"trial\", \"active\", \"canceled\")
    desde" "in (\"active\",)
    desde"

# --- Sin token no hay demo ni «activada» (D7.4, D9)
sabotaje $M "el checkout sin token da demo fuera de pruebas" \
  "FAILED $T::test_sin_token_fuera_de_desarrollo_no_hay_demo" \
  "        if not _demo_permitida():
            raise HTTPException(status_code=503, detail=\"Los pagos" "        if False:
            raise HTTPException(status_code=503, detail=\"Los pagos"
sabotaje $M "sin la variable de entorno hay demo" \
  "FAILED $T::test_sin_token_fuera_de_desarrollo_no_hay_demo[sin_variable]" \
  "os.getenv(\"ENVIRONMENT\") in (\"development\", \"test\", \"testing\")" \
  "os.getenv(\"ENVIRONMENT\", \"development\") in (\"development\", \"test\", \"testing\")"
sabotaje $M "la página de la demo abre fuera de pruebas" \
  "FAILED $T::test_sin_token_fuera_de_desarrollo_no_hay_demo" \
  "    \"\"\"Página de checkout demo cuando no hay credenciales MP\"\"\"
    if not _demo_permitida() or" "    \"\"\"Página de checkout demo cuando no hay credenciales MP\"\"\"
    if"
sabotaje $M "confirmar la demo funciona fuera de pruebas" \
  "FAILED $T::test_sin_token_fuera_de_desarrollo_no_hay_demo" \
  "    \"\"\"Confirma un pago demo: no cobra ni cambia la cuenta.\"\"\"
    if not _demo_permitida() or" "    \"\"\"Confirma un pago demo: no cobra ni cambia la cuenta.\"\"\"
    if"
sabotaje $M "la vuelta del pago dice «activada»" \
  "FAILED $T::test_la_pagina_de_exito_sin_token_no_dice_activada" \
  "        lineas = (\"Tu cuenta se actualiza cuando Mercado Pago confirma el pago.\"," \
  "        lineas = (\"Tu cuenta Premium ha sido activada.\","
sabotaje $M "la vuelta de la demo dice «activada»" \
  "FAILED $T::test_la_demo_no_dice_activada_ni_cambia_la_cuenta" \
  "        lineas = (\"Esto fue un pago de prueba: no se cobró nada y tu cuenta no cambió.\",)" \
  "        lineas = (\"Tu cuenta Premium ha sido activada.\",)"

# --- «Próximo cobro» sólo si lo hay (D7.3)
sabotaje $M "renueva sin suscripción" \
  "FAILED $T::test_billing_me_dice_si_hay_proximo_cobro[sin_suscripcion]" \
  "\"renueva\": (billing_entity.billing_status == \"active\" and bool(db_user.mp_preapproval_id)" \
  "\"renueva\": (billing_entity.billing_status == \"active\" and True"
sabotaje $M "renueva con un checkout sin pagar" \
  "FAILED $T::test_billing_me_dice_si_hay_proximo_cobro[checkout_sin_pagar]" \
  "
                    and getattr(billing_entity, \"payment_provider\", None) == \"mercadopago\")," "),"

# Los cruces entre miembros, en un Postgres 16 descartable.
correr() {
  PY="$PY" timeout 300 scripts/testing/con_pg16.sh bash -c '"$0" "$1" "$BACKUP1A_PG_URL"' "$PY" "$T" 2>&1
}
T=scripts/testing/cobro_mp2_postgres.py
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | los cruces en Postgres ya están en rojo (o no hay Postgres 16): no se pueden medir"; FALLAS=$((FALLAS+1))
else
  echo "BASE  | los cruces en Postgres, en verde"
  sabotaje $M "dos miembros pagan a la vez sin bloquear la organización" \
    "FALLA | dos miembros pagan a la vez: queda una sola suscripción viva en Mercado Pago" \
    "            .with_for_update().execution_options(populate_existing=True)
        )).scalars().first()" "            .execution_options(populate_existing=True)
        )).scalars().first()"
  sabotaje $M "el checkout bloquea la organización antes que a los miembros" \
    "FALLA | un miembro genera mientras otro paga: nadie queda cortado por deadlock" \
    "    nombres = {username, *((await db.execute(otros_con_sid)).scalars().all() if org_previa else ())}" \
    "    nombres = {username, *((await db.execute(otros_con_sid)).scalars().all() if org_previa else ())}
    if org_previa:
        await db.execute(select(Organization.id).where(Organization.id == org_previa).with_for_update())"
fi

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
