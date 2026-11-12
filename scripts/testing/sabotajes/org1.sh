#!/usr/bin/env bash
# Negativos de ORG-1 con la D40 (un email, una cuenta): cada sabotaje deshace
# una regla o una guarda y su caso en SQLite tiene que fallar por ese motivo. Con
# PG=<url de Postgres sin base> también scripts/testing/org1_postgres.py, en
# una base nueva por sabotaje que se borra al terminar.
#
# uso: PY=/ruta/al/venv/bin/python [PG=postgresql://cdi@127.0.0.1:55432] \
#      scripts/testing/sabotajes/org1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG="${PG:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0

# sqlite <archivo de pruebas>...
sqlite() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov --timeout=120 -p no:randomly -p no:cacheprovider "$@" 2>&1
}

postgres() {
  local base="org1sab_$$_$RANDOM" salida codigo
  psql "$PG/postgres" -qc "create database $base" >/dev/null || { echo "no se pudo crear la base"; return 2; }
  salida="$("$PY" scripts/testing/org1_postgres.py "$PG/$base" 2>&1)"; codigo=$?
  psql "$PG/postgres" -qc "drop database $base" >/dev/null
  grep -E "^(FALLA|fallas)" <<<"$salida"
  [ "$codigo" -eq 0 ] && grep -qx "fallas: 0" <<<"$salida"
}

# aplicar <archivo> <viejo> <nuevo> [<viejo> <nuevo> ...]: cada <viejo>, una sola vez.
aplicar() {
  "$PY" - "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

# juzgar <nombre> <salida> <código> <lo que el rojo tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3"; shift 3
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^(FAILED|FALLA)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <nombre> <rojo en SQLite> <rojo en Postgres> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Los rojos van separados por «|». Uno de SQLite sin «::» es un caso de
# tests/test_org1.py; con «::», de ese archivo. Sin rojo en un motor, no corre ahí.
sabotaje() {
  local nombre="$1" en_sqlite="$2" en_pg="$3" salida codigo r; shift 3
  local -a esperados=() archivos=()
  git checkout -q -- proyecto_maria/
  if ! aplicar proyecto_maria/main.py "$@"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  if [ -n "$en_sqlite" ]; then
    IFS='|' read -ra rojos <<<"$en_sqlite"
    for r in "${rojos[@]}"; do
      [[ "$r" == *::* ]] || r="tests/test_org1.py::$r"
      esperados+=("FAILED $r")
      [[ " ${archivos[*]} " == *" ${r%%::*} "* ]] || archivos+=("${r%%::*}")
    done
    salida="$(sqlite "${archivos[@]}")"; codigo=$?
    juzgar "$nombre (SQLite)" "$salida" "$codigo" "${esperados[@]}"
  fi
  if [ -n "$PG" ] && [ -n "$en_pg" ]; then
    esperados=()
    IFS='|' read -ra rojos <<<"$en_pg"
    for r in "${rojos[@]}"; do esperados+=("FALLA | $r"); done
    salida="$(postgres)"; codigo=$?
    juzgar "$nombre (Postgres)" "$salida" "$codigo" "${esperados[@]}"
  fi
  git checkout -q -- proyecto_maria/
}

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! salida="$(sqlite tests/test_org1.py)" || ! salida="$(sqlite tests/test_despacho1a.py)"; then
  echo "BASE  | test_org1.py o test_despacho1a.py ya está en rojo sin sabotaje: no se puede medir nada"
  grep -E "^FAILED|passed|failed" <<<"$salida"; exit 1
fi
if [ -n "$PG" ] && ! salida="$(postgres)"; then
  echo "BASE  | org1_postgres.py ya está en rojo sin sabotaje: no se puede medir nada"
  echo "$salida"; exit 1
fi
echo "BASE  | verde sin sabotaje en $SHA${PG:+ (SQLite y Postgres)}"

# Regla 1: invitar un email que ya tiene cuenta da 400, sea donde sea la cuenta.
YA="test_invitar_un_email_que_ya_tiene_cuenta_400_sin_ocupar_lugar"
CON_CUENTA='    existing = await db.execute(select(User.username).where(func.lower(User.email) == clean_email))
    if existing.first():
        raise HTTPException(
            status_code=400,
            detail="Ese email ya tiene una cuenta en CDI y no se puede invitar como miembro nuevo.",
        )
'
sabotaje "la regla 1 sólo mira este estudio" "$YA[otro estudio]" "invitar un email con cuenta otro estudio" \
  "select(User.username).where(func.lower(User.email) == clean_email)" \
  "select(User.username).where(func.lower(User.email) == clean_email, User.organization_id == org.id)"
sabotaje "la regla 1 sin mayúsculas" "$YA[vieja en mayusculas]" "invitar un email con cuenta guardada con mayúsculas" \
  "select(User.username).where(func.lower(User.email) == clean_email)" \
  "select(User.username).where(User.email == clean_email)"
sabotaje "sin la regla 1" "$YA[este estudio]" "invitar un email con cuenta este estudio" \
  "    if existing.first():" "    if False:"
sabotaje "con el estudio lleno, el tope habla antes que la cuenta" \
  "test_con_el_estudio_lleno_un_email_con_cuenta_dice_que_ya_tiene_cuenta" \
  "con el estudio lleno, un email con cuenta dice que ya tiene cuenta" \
  "$CON_CUENTA" "" \
  "    token = _csrf_secrets.token_urlsafe(32)
" "$CON_CUENTA    token = _csrf_secrets.token_urlsafe(32)
"

# Regla 2: al registrarse con una, las otras pendientes de ese email en ese
# estudio quedan usadas, en la misma transacción que la cuenta.
OTRAS='        await db.execute(
            sa_update(Invitation)
            .where(Invitation.org_id == invite_org.id, Invitation.status == "pending",
                   Invitation.expires_at > datetime.now(timezone.utc),
                   func.lower(func.trim(Invitation.email)) == request.email)
            .values(status="accepted")
            .execution_options(synchronize_session=False)
        )
'
sabotaje "sin la regla 2" "test_el_sacado_no_vuelve_a_entrar_con_otra_invitacion_vieja" \
  "el sacado no vuelve a entrar con la segunda" \
  "func.lower(func.trim(Invitation.email)) == request.email)" \
  "func.lower(func.trim(Invitation.email)) == request.email + \"-x\")"
sabotaje "la regla 2 sin mayúsculas ni espacios" "test_registrarse_usa_tambien_una_vieja_con_mayusculas_y_espacios" \
  "registrarse usa las otras del mismo email en ese estudio" \
  "func.lower(func.trim(Invitation.email)) == request.email)" "Invitation.email == request.email)"
sabotaje "la regla 2 en todos los estudios" "test_registrarse_con_una_invitacion_usa_las_otras_del_mismo_email" \
  "registrarse usa las otras del mismo email en ese estudio" \
  ".where(Invitation.org_id == invite_org.id, Invitation.status == \"pending\"," ".where(Invitation.status == \"pending\","
# Una marcada vencida con fecha futura sólo la arma org1_postgres.py: en SQLite
# la marcada ya venció por fecha, y eso lo cuida la línea de expires_at.
sabotaje "la regla 2 despierta a las marcadas vencidas" "" "una vencida sigue vencida al entrar con otra" \
  ".where(Invitation.org_id == invite_org.id, Invitation.status == \"pending\",
                   Invitation.expires_at" ".where(Invitation.org_id == invite_org.id,
                   Invitation.expires_at"
VEN="test_una_invitacion_vencida_sigue_vencida_cuando_entra_con_otra"
sabotaje "la regla 2 usa las vencidas por fecha" "$VEN[sqlite_sin_zona-pending]|$VEN[postgres_con_zona-pending]" "" \
  "                   Invitation.expires_at > datetime.now(timezone.utc),
                   func.lower(func.trim(Invitation.email)) == request.email)
            .values" "                   func.lower(func.trim(Invitation.email)) == request.email)
            .values"
sabotaje "la regla 2 en otra transacción" "test_si_falla_usar_las_otras_invitaciones_no_se_crea_la_cuenta" "" \
  "$OTRAS" "" \
  "    db.add(new_user)
    await db.commit()

    # Email de verificacion" "    db.add(new_user)
    await db.commit()
    if new_user.organization_id:
        await db.execute(
            sa_update(Invitation)
            .where(Invitation.org_id == new_user.organization_id, Invitation.status == \"pending\",
                   Invitation.expires_at > datetime.now(timezone.utc),
                   func.lower(func.trim(Invitation.email)) == request.email)
            .values(status=\"accepted\")
            .execution_options(synchronize_session=False)
        )
        await db.commit()

    # Email de verificacion"

# El tope: una pendiente cuyo email ya tiene cuenta (de un miembro o no) no ocupa lugar.
sabotaje "el tope cuenta las pendientes de emails con cuenta" \
  "test_una_pendiente_cuyo_email_ya_tiene_cuenta_no_ocupa_lugar|test_una_pendiente_al_email_de_un_miembro_no_ocupa_lugar" \
  "una pendiente cuyo email ya tiene cuenta sin link no ocupa lugar|una pendiente al email de un miembro no ocupa lugar" \
  "    emails_pendientes -= {email for (email,) in con_cuenta.all()}
" ""
sabotaje "el tope compara la cuenta sin mayúsculas" \
  "test_una_pendiente_cuyo_email_ya_tiene_cuenta_no_ocupa_lugar[vieja en mayusculas]" "" \
  "select(func.lower(User.email)).where(func.lower(User.email).in_(emails_pendientes))" \
  "select(User.email).where(User.email.in_(emails_pendientes))"
sabotaje "el tope compara la cuenta sin espacios" "test_una_pendiente_a_una_cuenta_con_espacios_ocupa_lugar" "" \
  "select(func.lower(User.email)).where(func.lower(User.email).in_(emails_pendientes))" \
  "select(func.lower(func.trim(User.email))).where(func.lower(func.trim(User.email)).in_(emails_pendientes))"
sabotaje "invitar sin validar el email" "test_invitar_un_email_que_el_registro_rechaza_400_sin_ocupar_lugar" "" \
  "    # registro rechace no la puede usar nadie y ocupa un lugar hasta que vence.
    clean_email = _email_valido(req.email)" \
  "    # registro rechace no la puede usar nadie y ocupa un lugar hasta que vence.
    clean_email = (req.email or \"\").strip().lower()"
sabotaje "la invitación vence a los 8 días" "test_la_invitacion_vence_a_los_7_dias" "" \
  "timedelta(days=7)," "timedelta(days=8),"

# Guardas de invitar, sacar, validar y listar.
SIN_ESTUDIO='    if not db_user or not db_user.organization_id:
        raise HTTPException(status_code=400, detail="No pertenecés a un estudio")
'
sabotaje "invitar sin estudio" "test_invitar_o_sacar_sin_estudio_400" "" \
  "${SIN_ESTUDIO}
    # Bloqueado hasta" "    if False:
        raise HTTPException(status_code=400, detail=\"No pertenecés a un estudio\")

    # Bloqueado hasta"
sabotaje "sacar sin estudio" "test_invitar_o_sacar_sin_estudio_400" "" \
  "${SIN_ESTUDIO}
    org = await db.execute(select(Organization).where(Organization.id == db_user.organization_id))" \
  "    if False:
        raise HTTPException(status_code=400, detail=\"No pertenecés a un estudio\")

    org = await db.execute(select(Organization).where(Organization.id == db_user.organization_id))"
sabotaje "invita quien no es dueño" "test_un_miembro_no_puede_invitar_403" "un miembro no invita" \
  "if user[\"username\"] != org.owner_username:
        raise HTTPException(status_code=403, detail=\"Solo el administrador del estudio puede invitar\")" \
  "if False:
        raise HTTPException(status_code=403, detail=\"Solo el administrador del estudio puede invitar\")"
sabotaje "sacar busca en todos los estudios" "test_sacar_a_alguien_de_otro_estudio_404_y_sigue_en_el_suyo" \
  "no se saca a alguien de otro estudio" \
  "select(User).where(User.username == username, User.organization_id == org.id)" \
  "select(User).where(User.username == username)"
sabotaje "sacar borra al usuario" "test_sacar_no_borra_al_usuario" "" \
  "    member.organization_id = None
" "    await db.delete(member)
"
sabotaje "validar con el estudio borrado" "test_validar_con_el_estudio_borrado_404" "" \
  "    if not org:
        raise HTTPException(status_code=404, detail=\"El estudio ya no existe\")" \
  "    if False:
        raise HTTPException(status_code=404, detail=\"El estudio ya no existe\")"
MINE="test_mine_lista_sólo_los_miembros_del_estudio_y_quién_es_dueño"
sabotaje "/mine lista todos los usuarios" "$MINE" "" \
  "select(User).where(User.organization_id == org.id).order_by(User.username)" \
  "select(User).order_by(User.username)"
sabotaje "/mine: todo miembro es dueño" "$MINE" "" \
  "\"is_owner\": m.username == org.owner_username," "\"is_owner\": True,"
sabotaje "/mine: quien pide es dueño" "$MINE" "" \
  "\"is_owner\": user[\"username\"] == org.owner_username," "\"is_owner\": True,"

# El dueño no se saca a sí mismo, ni con otras mayúsculas, ni después de tocar Mercado Pago.
YO="test_el_duenio_no_se_saca_a_si_mismo_y_el_estudio_queda_igual"
GUARDA='    if username == org.owner_username:
        raise HTTPException(status_code=400, detail="No podés removerte a vos mismo del estudio")
'
sabotaje "el dueño se saca a sí mismo" "$YO" "" "$GUARDA" ""
sabotaje "la guarda va después de Mercado Pago" "$YO" "" "$GUARDA" "" \
  "    member.organization_id = None
" "$GUARDA    member.organization_id = None
"
sabotaje "sacar busca sin mayúsculas" "$YO" "" \
  "select(User).where(User.username == username, User.organization_id == org.id)" \
  "select(User).where(func.lower(User.username) == username.lower(), User.organization_id == org.id)"
sabotaje "sacar busca sin espacios" "$YO" "" \
  "select(User).where(User.username == username, User.organization_id == org.id)" \
  "select(User).where(func.trim(User.username) == username.strip(), User.organization_id == org.id)"

# El título de la columna del archivo de DESPACHO-1a.
sabotaje "el archivo dice «Ultima vez»" "tests/test_despacho1a.py::test_el_archivo_se_abre_y_trae_lo_guardado" "" \
  "    (\"Última vez\", \"ultima_vez\")," "    (\"Ultima vez\", \"ultima_vez\"),"

echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
