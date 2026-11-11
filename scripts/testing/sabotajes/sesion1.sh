#!/usr/bin/env bash
# Negativos de SESION-1: cada sabotaje deshace una regla (un solo lugar decide
# si un token es la sesión vigente y se firma con la misma clave, sin
# vencimiento no vale, verificar el email no abre sesión, lo que se guarda tras
# validar la clave no pisa una que cambió en el medio, cambiar o resetear la
# contraseña y cerrar sesión revocan, una revocada no vuelve, la contraseña
# actual da 400 y tiene tope, contar intentos usa la conexión del pedido y
# revisar la sesión devuelve la suya,
# cambiar el email la pide, la pantalla la pide sólo si el email cambió) y
# tests/test_sesion1.py, tests/test_user_profile_coverage.py,
# scripts/testing/pantalla_sesion1.js o, con PG_DSN, sesion1_motores.py pg
# tienen que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python [PG_DSN=postgresql://u@127.0.0.1:<puerto>/<base>] \
#        scripts/testing/sabotajes/sesion1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Los de pantalla levantan uvicorn en un
# puerto libre y necesitan node con playwright (NODE_PATH); sin eso se cuentan
# como no corridos y el script sale con error. Sale con error si un sabotaje
# no encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0

pytest_s1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider \
      tests/test_sesion1.py tests/test_user_profile_coverage.py 2>&1
}

pantalla_s1() {
  local puerto log base pid salida codigo
  puerto="$("$PY" -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')"
  log="$TMPD/uvicorn_$puerto.log"; base="$TMPD/pantalla_$puerto.db"
  DATABASE_URL="sqlite+aiosqlite:///$base" ENVIRONMENT=testing EMAIL_VERIFICATION_REQUIRED=false \
    JWT_SECRET_KEY=clave-solo-para-esta-prueba-con-mas-de-32-caracteres CDI_DATA_DIR="$TMPD/data_$puerto" \
    "$PY" -m uvicorn proyecto_maria.main:app --port "$puerto" >"$log" 2>&1 &
  pid=$!
  for _ in $(seq 1 600); do
    kill -0 "$pid" 2>/dev/null || break
    grep -q "Application startup complete" "$log" && break
    sleep 0.1
  done
  if ! kill -0 "$pid" 2>/dev/null || ! grep -q "Application startup complete" "$log"; then
    kill "$pid" 2>/dev/null; echo "el servidor no arrancó"; tail -5 "$log"; return 99
  fi
  salida="$(BASE_URL="http://127.0.0.1:$puerto" timeout 150 node scripts/testing/pantalla_sesion1.js 2>&1)"; codigo=$?
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  echo "$salida"; return $codigo
}

aplicar() {
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
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
      grep -E "^(FAILED|E |FALLA)" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <pytest|pantalla> <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local prueba="$1" archivo="$2" nombre="$3" viejo="$4" nuevo="$5"; shift 5
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  if [ "$prueba" = pantalla ]; then salida="$(pantalla_s1)"; else salida="$(pytest_s1)"; fi
  codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
D=proyecto_maria/auth/dependencies.py
P=proyecto_maria/static/v2/screens/profile.js
T=tests/test_sesion1.py
L=proyecto_maria/core/limites_auth.py
G="FAILED $T::test_lo_que_cambia_la_clave_mientras_otro_valida_le_gana"

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_s1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi
CON_PANTALLA=1
if ! node -e "require('playwright')" 2>/dev/null; then
  CON_PANTALLA=0; echo "SIN NAVEGADOR | node con playwright no está: los sabotajes de pantalla no se corren"
elif ! pantalla_s1 >"$TMPD/base_pantalla.log"; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje"; cat "$TMPD/base_pantalla.log"; exit 1
fi

# --- un solo lugar decide si un token es la sesión vigente
sabotaje pytest $D "un usuario sin jti (de antes de la columna) no entra" \
  'if user.active_jti is not None and payload.get("jti") != user.active_jti:' \
  'if payload.get("jti") != user.active_jti:' \
  "FAILED $T::test_cambiar_clave_rota_la_sesion_de_quien_la_cambia" "FAILED $T::test_cambiar_clave_con_cookie_conserva_el_navegador" \
  "FAILED $T::test_cerrar_sesion_de_un_usuario_sin_jti_revoca"
sabotaje pytest $D "abrir el token sin verificar la firma" \
  '                          options={"require": ["exp"]})' \
  '                          options={"require": ["exp"], "verify_signature": False})' \
  "FAILED $T::test_ningun_lugar_acepta_un_token_que_no_es_la_sesion_vigente" "otra firma"
sabotaje pytest $D "el token de verificar el email vale como sesión" \
  'if payload is None or payload.get("type") is not None or not payload.get("sub"):' \
  'if payload is None or not payload.get("sub"):' \
  "FAILED $T::test_ningun_lugar_acepta_un_token_que_no_es_la_sesion_vigente" "verificación de email"
sabotaje pytest $D "un token sin vencimiento vale" \
  '                          options={"require": ["exp"]})' '                          )' \
  "FAILED $T::test_un_token_sin_vencimiento_no_es_una_sesion"
sabotaje pytest $D "firmar lee la clave del entorno y verificar la de settings" \
  '    return jwt.encode(datos, settings.jwt_secret, algorithm=settings.jwt_algorithm)' \
  '    return jwt.encode(datos, os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "tu-clave-secreta-super-segura-cambiar-en-produccion"), algorithm=settings.jwt_algorithm)' \
  "FAILED $T::test_se_firma_y_se_verifica_con_la_misma_clave"
sabotaje pytest $D "el header le gana a la cookie" \
  $'    token = request.cookies.get("access_token")\n    if not token:\n        auth_header = request.headers.get("Authorization")\n        if auth_header and auth_header.startswith("Bearer "):\n            token = auth_header\n' \
  $'    token = request.headers.get("Authorization") or request.cookies.get("access_token")\n' \
  "FAILED $T::test_la_cookie_le_gana_al_header"
sabotaje pytest $M "verificar el email abre sesión" \
  $'    await db.commit()\n    return RedirectResponse(url=f"{get_frontend_url()}/dashboard?verified=true")\n' \
  $'    await db.commit()\n    ir = RedirectResponse(url=f"{get_frontend_url()}/dashboard?verified=true")\n    await abrir_sesion(ir, db, user, user.password)\n    return ir\n' \
  "FAILED $T::test_verificar_el_email_no_abre_sesion" "vez 1: el link de verificación abrió sesión"

# --- lo que se guarda después de validar la clave mira que siga siendo la validada
sabotaje pytest $M "guardar no mira si la clave cambió" \
  'User.username == username, User.password == hash_validado).values(**valores))' \
  'User.username == username).values(**valores))' \
  "FAILED $T::test_el_login_no_pisa_una_clave_que_cambio_mientras_validaba" \
  "$G[reset-cambiar la clave]" "$G[reset-cambiar el email]" \
  "$G[otro cambio de clave-cambiar la clave]" "$G[otro cambio de clave-cambiar el email]"
sabotaje pytest $M "el perfil guarda el email sin mirar la clave" \
  $'    elif not await guardar_si_la_clave_sigue(db, u.username, hash_validado, email=raw_email or None):\n        raise HTTPException(status_code=409, detail=CLAVE_CAMBIADA_EN_EL_MEDIO)\n' \
  $'    else:\n        u.email = raw_email or None\n        await db.commit()\n' \
  "$G[reset-cambiar el email]" "$G[otro cambio de clave-cambiar el email]"
sabotaje pytest $M "cambiar la clave compara con la que lee al guardar" \
  '    token = await abrir_sesion(response, db, db_user, hash_validado, password=nuevo)' \
  $'    await db.refresh(db_user)\n    token = await abrir_sesion(response, db, db_user, db_user.password, password=nuevo)' \
  "$G[reset-cambiar la clave]" "$G[otro cambio de clave-cambiar la clave]"
sabotaje pytest $M "cambiar la clave da 200 aunque no se guardó" \
  $'    if token is None:\n        raise HTTPException(status_code=409, detail=CLAVE_CAMBIADA_EN_EL_MEDIO)\n    print(' \
  $'    print(' \
  "$G[reset-cambiar la clave]" "$G[otro cambio de clave-cambiar la clave]"

# --- cambiar la contraseña: cierra todas, en el mismo guardado, y devuelve un token nuevo
sabotaje pytest $M "cambiar la clave la guarda antes de cerrar las otras" \
  '    token = await abrir_sesion(response, db, db_user, hash_validado, password=nuevo)' \
  $'    await guardar_si_la_clave_sigue(db, db_user.username, hash_validado, password=nuevo)\n    token = await abrir_sesion(response, db, db_user, nuevo)' \
  "FAILED $T::test_si_el_token_nuevo_no_sale_la_clave_no_cambia" "la clave cambió sin cerrar las otras sesiones"
sabotaje pytest $M "cambiar la clave no emite un token nuevo" \
  '    token = await abrir_sesion(response, db, db_user, hash_validado, password=nuevo)' \
  $'    token = "sin-token" if await guardar_si_la_clave_sigue(db, db_user.username, hash_validado, password=nuevo, active_jti=uuid.uuid4().hex) else None' \
  "FAILED $T::test_cambiar_clave_rota_la_sesion_de_quien_la_cambia" "FAILED $T::test_cambiar_clave_con_cookie_conserva_el_navegador"

# --- resetear la contraseña: cierra todas
sabotaje pytest $M "resetear la clave vuelve a poner active_jti en NULL" \
  'active_jti=uuid.uuid4().hex):' 'active_jti=None):' \
  "FAILED $T::test_resetear_clave_revoca_todas_las_sesiones" "la sesión vigente sigue entrando después del reset"

# --- una revocada no vuelve: revocar nunca escribe NULL
sabotaje pytest $D "revocar escribe NULL y resucita las viejas" \
  '    user.active_jti = uuid.uuid4().hex' '    user.active_jti = None' \
  "FAILED $T::test_una_sesion_revocada_no_vuelve"

# --- cerrar sesión: revoca el token con el que se llama, y sólo si es el vigente
sabotaje pytest $M "cerrar sesión sólo borra la cookie" \
  $'    try:\n        await revocar_sesion_de_la_request(request, db)\n    except Exception:\n' \
  $'    try:\n        pass\n    except Exception:\n' \
  "FAILED $T::test_cerrar_sesion_con_bearer_revoca_la_propia[/auth/logout]" "FAILED $T::test_cerrar_sesion_con_bearer_revoca_la_propia[/logout]" \
  "FAILED $T::test_cerrar_sesion_con_cookie_revoca_la_propia[/auth/logout]"
sabotaje pytest $M "cerrar sesión sin base no borra la cookie" \
  $'    try:\n        await revocar_sesion_de_la_request(request, db)\n    except Exception:\n        # Sin base no se revoca, pero el navegador igual sale.\n        logging.getLogger(__name__).exception("logout: no se pudo revocar la sesión")\n' \
  $'    await revocar_sesion_de_la_request(request, db)\n' \
  "FAILED $T::test_cerrar_sesion_borra_la_cookie_aunque_falle_la_base"
sabotaje pytest $D "cerrar sesión con un token revocado saca la vigente" \
  $'    sesion = await sesion_de_la_request(request, db)\n    if sesion is None:\n        return\n    revocar_sesiones(sesion[0])\n' \
  $'    token = _token_de_la_request(request)\n    payload = datos_del_token(token) if token else None\n    user = payload and (await db.execute(select(User).where(User.username == payload.get("sub")))).scalars().first()\n    if not user:\n        return\n    revocar_sesiones(user)\n' \
  "FAILED $T::test_cerrar_sesion_con_un_token_revocado_no_saca_la_vigente" "un token ya revocado cerró la sesión vigente"

# --- la contraseña actual: 400, con tope de intentos
sabotaje pytest $M "la clave actual acepta cualquier cosa" \
  $'    if not await run_in_threadpool(verify_password, clave, hash_guardado):\n' $'    if False:\n' \
  "FAILED $T::test_cambiar_email_con_clave_equivocada_falla_y_no_cambia_nada" "FAILED $T::test_cambiar_clave_mal_no_revoca_nada"
sabotaje pytest $M "la clave equivocada da 401 y manda al login" \
  'raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")' \
  'raise HTTPException(status_code=401, detail="La contraseña actual es incorrecta")' \
  "FAILED $T::test_cambiar_email_con_clave_equivocada_falla_y_no_cambia_nada" "FAILED $T::test_cambiar_clave_mal_no_revoca_nada" "assert 401 == 400"
sabotaje pytest $M "la clave equivocada no suma al tope" \
  $'    if not espera and await limites_auth.sumar_fallo(db, clave_intentos) > 5:\n        espera = await limites_auth.segundos_bloqueado(db, clave_intentos)\n' '' \
  "FAILED $T::test_la_clave_actual_tiene_tope_de_intentos"
sabotaje pytest $M "el intento se cuenta después de probar la clave" \
  $'    if not espera and await limites_auth.sumar_fallo(db, clave_intentos) > 5:\n        espera = await limites_auth.segundos_bloqueado(db, clave_intentos)\n    if espera:\n        raise HTTPException(status_code=429, detail=f"Demasiados intentos fallidos. Intente de nuevo en {espera} segundos.")\n    if not await run_in_threadpool(verify_password, clave, hash_guardado):\n' \
  $'    if espera:\n        raise HTTPException(status_code=429, detail=f"Demasiados intentos fallidos. Intente de nuevo en {espera} segundos.")\n    if not await run_in_threadpool(verify_password, clave, hash_guardado):\n        await limites_auth.sumar_fallo(db, clave_intentos)\n' \
  "FAILED $T::test_el_tope_de_la_clave_actual_vale_para_pedidos_a_la_vez"

# --- contar intentos no toma otra conexión mientras el pedido tiene la suya
C="FAILED $T::test_contar_intentos_usa_la_conexion_del_pedido"
sabotaje pytest $L "sumar o contar abre su propia conexión" \
  $'async def _escribir(db: AsyncSession, ahora: float, consulta) -> int:\n    await db.execute(delete(_T).where(_T.c.vence <= ahora))\n    cuenta = (await db.execute(consulta)).scalar_one()\n    await db.commit()\n    return cuenta\n' \
  $'async def _escribir(db: AsyncSession, ahora: float, consulta) -> int:\n    async with _conn.engine.begin() as conn:\n        await conn.execute(delete(_T).where(_T.c.vence <= ahora))\n        return (await conn.execute(consulta)).scalar_one()\n' \
  "$C[login sin usuario]" "$C[login con clave mala]"
sabotaje pytest $L "mirar el bloqueo abre su propia conexión" \
  $'    hasta = (await db.execute(\n' $'    async with _conn.engine.connect() as conn:\n        hasta = (await conn.execute(\n' \
  "$C[perfil]" "$C[cambiar la clave]"
sabotaje pytest $L "limpiar pide otra conexión con la del pedido tomada" \
  $'    await db.execute(delete(_T).where(_T.c.clave == _clave(clave)))\n    await db.commit()\n' \
  $'    await db.execute(select(_T.c.clave).where(_T.c.clave == _clave(clave)))\n    async with _conn.engine.begin() as conn:\n        await conn.execute(delete(_T).where(_T.c.clave == _clave(clave)))\n    await db.commit()\n' \
  "$C[perfil con la clave buena]" "$C[cambiar la clave con la clave buena]"
sabotaje pytest $L "descontar abre su propia conexión" \
  $'    await db.execute(delete(_T).where(_T.c.vence <= ahora))\n    n = ' \
  $'    async with _conn.engine.begin() as conn:\n        await conn.execute(delete(_T).where(_T.c.vence <= ahora))\n    n = ' \
  "$C[login]" "login: 2 conexiones a la vez"
sabotaje pytest $D "revisar la sesión se queda con su conexión durante la ruta" \
  $'    await db.commit()\n\n    team_owner = ' $'\n    team_owner = ' \
  "$C[ver el perfil]" "$C[perfil]" "$C[cambiar la clave]"

# --- cambiar el email pide la contraseña actual
sabotaje pytest $M "cambiar el email sin clave no verifica nada" \
  $'        if not isinstance(current_password, str) or not current_password:\n            raise HTTPException(status_code=400, detail="Para cambiar el email ingresá tu contraseña actual")\n        await verificar_clave_actual(db, u.username, current_password, hash_validado)\n' \
  $'        if current_password:\n            await verificar_clave_actual(db, u.username, current_password, hash_validado)\n' \
  "FAILED $T::test_cambiar_email_sin_clave_falla_y_no_cambia_nada" "assert 200 == 400"
sabotaje pytest $M "la clave actual no se mira si es texto" \
  'if not isinstance(current_password, str) or not current_password:' 'if not current_password:' \
  "FAILED $T::test_perfil_rechaza_una_clave_actual_que_no_es_texto"
sabotaje pytest $M "un email vacío antes no pide la clave" \
  'cambia_email = "email" in body and raw_email != (u.email or "").strip().lower()' \
  'cambia_email = "email" in body and bool(u.email) and raw_email != u.email.strip().lower()' \
  "FAILED $T::test_perfil_pide_la_clave_aunque_el_email_estuviera_vacio"
sabotaje pytest $M "vaciar el email no pide la contraseña" \
  'cambia_email = "email" in body and raw_email != (u.email or "").strip().lower()' \
  'cambia_email = bool(raw_email) and raw_email != (u.email or "").strip().lower()' \
  "FAILED $T::test_vaciar_el_email_tambien_pide_la_clave" "assert 200 == 400"
sabotaje pytest $M "el mismo email en mayúsculas pide la contraseña" \
  'cambia_email = "email" in body and raw_email != (u.email or "").strip().lower()' \
  'cambia_email = "email" in body and body.get("email") != u.email' \
  "FAILED $T::test_guardar_el_perfil_con_el_mismo_email_no_pide_clave" "assert 400 == 200"
sabotaje pytest $M "un email mal escrito pide la contraseña en vez de rechazarse" \
  '            _email_valido(raw_email)' '            pass' \
  "FAILED tests/test_user_profile_coverage.py::test_update_user_profile_email_invalido_400" "Email no válido"

# --- la carrera del login en Postgres: sólo con un Postgres local y descartable
if [ -n "${PG_DSN:-}" ]; then
  git checkout -q -- proyecto_maria/
  if aplicar $M 'User.username == username, User.password == hash_validado).values(**valores))' \
                'User.username == username).values(**valores))'; then
    salida="$("$PY" scripts/testing/sesion1_motores.py pg "$PG_DSN" 2>&1)"; codigo=$?
    juzgar "pg: el login escribe el jti aunque la clave haya cambiado" "$salida" "$codigo" \
      "FALLA | 6. el login con la clave vieja no abre sesión"
  else
    echo "ROTO  | pg: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1))
  fi
  git checkout -q -- proyecto_maria/
else
  echo "NO CORRIDO | pg: sin PG_DSN la carrera del login en Postgres no se sabotea"
fi

# --- la pantalla de perfil
if [ "$CON_PANTALLA" -eq 1 ]; then
  sabotaje pantalla $P "la pantalla no muestra el campo de la clave" \
    '        emailPwdField.hidden = !changed;' '        emailPwdField.hidden = true;' \
    "FALLA: cambiar el email no muestra el campo de la clave"
  sabotaje pantalla $P "la pantalla muestra el campo aunque el email no cambió" \
    '        emailPwdField.hidden = !changed;' '        emailPwdField.hidden = false;' \
    "FALLA: el campo de la clave se ve al abrir el perfil"
  sabotaje pantalla $P "la pantalla manda el PUT sin clave" \
    '        if (emailChanged() && !emailPwd) {' '        if (false) {' \
    "FALLA: sin clave"
  sabotaje pantalla $P "la pantalla no manda la clave" \
    '            if (emailChanged()) payload.current_password = emailPwd;' '' \
    "FALLA: con la clave equivocada no se ve el error"
  sabotaje pantalla $P "la pantalla compara el email distinguiendo mayúsculas" \
    "    function normalizeEmail(v) { return String(v || '').trim().toLowerCase(); }" \
    "    function normalizeEmail(v) { return String(v || ''); }" \
    "FALLA: el campo de la clave se ve con el mismo email en mayúsculas"
fi

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ] && [ "$CON_PANTALLA" -eq 1 ]
