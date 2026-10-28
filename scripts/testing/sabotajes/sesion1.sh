#!/usr/bin/env bash
# Negativos de SESION-1: cada sabotaje deshace una regla (cambiar o resetear la
# contraseña y cerrar sesión revocan, una revocada no vuelve, cambiar el email
# pide la contraseña, la pantalla la pide sólo si el email cambió) y
# tests/test_sesion1.py, tests/test_user_profile_coverage.py o
# scripts/testing/pantalla_sesion1.js tienen que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/sesion1.sh [SHA]
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

# --- cambiar la contraseña: cierra las otras, conserva la propia
sabotaje pytest $M "cambiar la clave vuelve a poner active_jti en NULL" \
  '    revocar_sesiones(db_user, jti_de_la_request(request))' '    db_user.active_jti = None' \
  "FAILED $T::test_cambiar_clave_revoca_las_otras_y_conserva_la_propia" "la otra sesión sigue entrando después de cambiar la clave"
sabotaje pytest $M "cambiar la clave cierra también la propia" \
  '    revocar_sesiones(db_user, jti_de_la_request(request))' '    revocar_sesiones(db_user)' \
  "FAILED $T::test_cambiar_clave_revoca_las_otras_y_conserva_la_propia" "cambiar la clave cerró la sesión de quien la cambió" \
  "FAILED $T::test_cambiar_clave_con_cookie_conserva_el_navegador"

# --- resetear la contraseña: cierra todas
sabotaje pytest $M "resetear la clave vuelve a poner active_jti en NULL" \
  $'    revocar_sesiones(user)\n' $'    user.active_jti = None\n' \
  "FAILED $T::test_resetear_clave_revoca_todas_las_sesiones" "la sesión vigente sigue entrando después del reset"

# --- una revocada no vuelve: revocar todas nunca escribe NULL
sabotaje pytest $D "revocar todas escribe NULL y resucita las viejas" \
  '    user.active_jti = conservar_jti or uuid.uuid4().hex' '    user.active_jti = conservar_jti' \
  "FAILED $T::test_una_sesion_revocada_no_vuelve" "FAILED $T::test_resetear_clave_revoca_todas_las_sesiones"

# --- cerrar sesión: revoca el token con el que se llama, y sólo si es el vigente
sabotaje pytest $M "/auth/logout sólo borra la cookie" \
  $'    """Cierra sesión: revoca el token y elimina la cookie"""\n    await revocar_sesion_de_la_request(request, db)\n' \
  $'    """Cierra sesión: revoca el token y elimina la cookie"""\n' \
  "FAILED $T::test_cerrar_sesion_con_bearer_revoca_la_propia[/auth/logout]" "/auth/logout: el token sigue entrando después de cerrar sesión"
sabotaje pytest $M "/logout sólo borra la cookie" \
  $'(alias de /auth/logout)"""\n    await revocar_sesion_de_la_request(request, db)\n' \
  $'(alias de /auth/logout)"""\n' \
  "FAILED $T::test_cerrar_sesion_con_bearer_revoca_la_propia[/logout]" "/logout: el token sigue entrando después de cerrar sesión"
sabotaje pytest $D "cerrar sesión no mira la cookie" \
  $'    token = _token_de_la_request(request)\n    if not token:\n        return\n' \
  $'    auth = request.headers.get("Authorization") or ""\n    token = auth[7:] if auth.startswith("Bearer ") else None\n    if not token:\n        return\n' \
  "FAILED $T::test_cerrar_sesion_con_cookie_revoca_la_propia" "la cookie robada sigue entrando después de cerrar sesión"
sabotaje pytest $D "cerrar sesión con un token revocado saca la vigente" \
  $'    if user.active_jti is not None and payload.get("jti") != user.active_jti:\n        return\n' '' \
  "FAILED $T::test_cerrar_sesion_con_un_token_revocado_no_saca_la_vigente" "un token ya revocado cerró la sesión vigente"

# --- cambiar el email pide la contraseña actual
# Quitar sólo el chequeo de «sin clave» no basta para romper la regla:
# verify_password igual rechaza None. El defecto real es verificar sólo si
# viene una clave.
sabotaje pytest $M "cambiar el email sin clave no verifica nada" \
  $'        if not isinstance(current_password, str) or not current_password:\n            raise HTTPException(status_code=400, detail="Para cambiar el email ingresá tu contraseña actual")\n        # 400 y no 401: el frontend toma cualquier 401 como sesión vencida y\n        # manda al login.\n        if not await run_in_threadpool' \
  '        if current_password and not await run_in_threadpool' \
  "FAILED $T::test_cambiar_email_sin_clave_falla_y_no_cambia_nada" "assert 200 == 400"
sabotaje pytest $M "cambiar el email acepta cualquier contraseña" \
  $'        if not await run_in_threadpool(verify_password, current_password, u.password):\n            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")\n' '' \
  "FAILED $T::test_cambiar_email_con_clave_equivocada_falla_y_no_cambia_nada" "assert 200 == 400"
sabotaje pytest $M "la clave equivocada da 401 y manda al login" \
  'raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")' \
  'raise HTTPException(status_code=401, detail="La contraseña actual es incorrecta")' \
  "FAILED $T::test_cambiar_email_con_clave_equivocada_falla_y_no_cambia_nada" "assert 401 == 400"
sabotaje pytest $M "vaciar el email no pide la contraseña" \
  'if "email" in body and raw_email != (u.email or "").strip().lower():' \
  'if raw_email and raw_email != (u.email or "").strip().lower():' \
  "FAILED $T::test_vaciar_el_email_tambien_pide_la_clave" "assert 200 == 400"
sabotaje pytest $M "el mismo email en mayúsculas pide la contraseña" \
  'if "email" in body and raw_email != (u.email or "").strip().lower():' \
  'if "email" in body and body.get("email") != u.email:' \
  "FAILED $T::test_guardar_el_perfil_con_el_mismo_email_no_pide_clave" "assert 400 == 200"
sabotaje pytest $M "un email mal escrito pide la contraseña en vez de rechazarse" \
  $'        if raw_email and not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$", raw_email):\n            raise HTTPException(status_code=400, detail="Email no válido")\n        current_password' \
  '        current_password' \
  "FAILED tests/test_user_profile_coverage.py::test_update_user_profile_email_invalido_400" "Email no válido"

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
