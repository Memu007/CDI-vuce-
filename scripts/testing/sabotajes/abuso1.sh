#!/usr/bin/env bash
# Negativos de ABUSO-1: cada sabotaje deshace una regla y tests/test_abuso1.py
# tiene que fallar por ese motivo.
# S5: un evento de más de 16 KB da 413 y no se guarda, venga o no
# Content-Length; uno de hasta 16 KB se guarda; ninguno escribe
# logs/ui_events.jsonl.
# S4: la IP es la última de X-Forwarded-For; el 429 del login deja la IP en el
# log; el login correcto borra los fallos.
# S6 y C9: recuperar usuario (5 cada 15 min por IP, 3 por hora por email en
# silencio), registro (5 por hora y 20 por día), recuperar contraseña sin
# pasar el tope con pedidos simultáneos.
# Eventos: 120 por minuto por ruta; sin sesión, sólo los de la lista.
# Tabla: las vencidas se borran al escribir y al arrancar; contar es atómico.
# IP larga: una IP de más de 120 caracteres entra en la clave (comienzo y
# sha256), se bloquea, no pisa a otra con el mismo comienzo y el login correcto
# la limpia; una de hasta 300 también.
# Duración: el bloqueo y el corte por IP de recuperar duran 15 minutos; la
# ventana por email de recuperar, una hora.
# Un surrogate suelto o un NUL en login, reset, recuperar o el token de
# restablecer no da 500, tampoco en el 422.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/abuso1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
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

pytest_a1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_abuso1.py 2>&1
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
      grep -E "^(FAILED|E )" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_a1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
T=tests/test_abuso1.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_a1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi

# --- S5: más de 16 KB da 413 y no se guarda
sabotaje $M "sin tope: se lee y se guarda cualquier cuerpo" \
  $'        if total > tope:\n            return None\n' '' \
  "FAILED $T::test_s5_evento_de_5mb_no_se_guarda[False-/api/ui/event]" \
  "FAILED $T::test_s5_evento_de_5mb_no_se_guarda[True-/api/session/state]" \
  "FAILED $T::test_s5_sin_content_length_tambien_corta[/api/ui/event]" "(200, '{\"ok\":true}')"
sabotaje $M "el tope deja afuera un evento de 16 KB justos" \
  '        if total > tope:' '        if total >= tope:' \
  "FAILED $T::test_s5_el_tope_es_16kb[/api/ui/event]" "Evento demasiado grande"
sabotaje $M "el tope es de 32 KB" \
  '_UI_EVENT_MAX_BYTES = 16 * 1024' '_UI_EVENT_MAX_BYTES = 32 * 1024' \
  "FAILED $T::test_s5_el_tope_es_16kb[/api/session/state]" "{\"ok\":true}"
sabotaje $M "el evento grande da 200 en vez de 413" \
  'return JSONResponse({"ok": False, "detail": "Evento demasiado grande"}, status_code=413)' \
  'return JSONResponse({"ok": False, "detail": "Evento demasiado grande"})' \
  "FAILED $T::test_s5_evento_de_5mb_no_se_guarda[True-/api/ui/event]" "AssertionError: (200, '{\"ok\":false"

# --- S5: el evento no se escribe en logs/ui_events.jsonl
sabotaje $M "vuelve la escritura a logs/ui_events.jsonl" \
  $'        try:\n            await _persist_ui_telemetry_row(db, username, payload)' \
  $'        os.makedirs(os.path.join(basedir, "logs"), exist_ok=True)\n        with open(os.path.join(basedir, "logs", "ui_events.jsonl"), "a", encoding="utf-8") as fh:\n            fh.write(_json.dumps(payload) + "\\n")\n        try:\n            await _persist_ui_telemetry_row(db, username, payload)' \
  "FAILED $T::test_s5_un_evento_chico_se_guarda_y_no_escribe_el_jsonl[/api/ui/event]" "assert _tamano_jsonl() == antes"

R=proyecto_maria/core/rate_limit.py
L=proyecto_maria/core/limites_auth.py

# --- S4: la IP es la última de X-Forwarded-For
sabotaje $R "vuelve la primera IP de X-Forwarded-For" \
  '        return partes[0] if len(partes) < saltos else partes[-saltos]' '        return partes[0]' \
  "FAILED $T::test_s4a_una_ip_inventada_no_esquiva_el_bloqueo_del_login" \
  "FAILED $T::test_s4b_una_ip_inventada_no_bloquea_a_otro" \
  "FAILED $T::test_s4_la_ip_es_la_ultima_de_x_forwarded_for"
sabotaje $M "el 429 del login no deja la IP en el log" \
  '        log_429(request, "login bloqueado")' '        pass' \
  "FAILED $T::test_s4_el_429_del_login_deja_ip_y_entradas_en_el_log"
sabotaje $M "el login correcto no borra los fallos" \
  $'# Login exitoso: limpiar intentos fallidos\n    await limites_auth.limpiar(db, clave_intentos)' \
  $'# Login exitoso: limpiar intentos fallidos\n    pass' \
  "FAILED $T::test_s4_el_login_correcto_borra_los_fallos" "[401, 429, 429, 429]"

# --- S6: recuperar usuario
sabotaje $M "recuperar usuario sin límite por IP" \
  '15 * 60) > 5:' '15 * 60) > 10**6:' \
  "FAILED $T::test_los_limites_por_ip_duran_quince_minutos[/auth/recover-username-cuerpo2-200]" "[200, 200, 200, 200, 200, 200]"
sabotaje $M "recuperar usuario: 4 por hora por email" \
  '3600) > 3:' '3600) > 4:' \
  "FAILED $T::test_s6_recuperar_usuario_corta_en_silencio_por_email" "el cuarto pedido de la hora mandó el mail"
sabotaje $M "recuperar usuario: pasado el tope por email busca y manda igual" \
  $'3600) > 3:\n            return mensaje' $'3600) > 3:\n            pass' \
  "FAILED $T::test_s6_recuperar_usuario_corta_en_silencio_por_email" "el cuarto pedido de la hora mandó el mail"
sabotaje $M "recuperar usuario: la clave por email distingue mayúsculas" \
  'request.email.strip().lower().encode()' 'request.email.strip().encode()' \
  "FAILED $T::test_s6_recuperar_usuario_corta_en_silencio_por_email" "el cuarto pedido de la hora mandó el mail"

# --- C9: registro
sabotaje $M "registro: 6 por hora" \
  '"registro:h:{ip}", 3600) > 5' '"registro:h:{ip}", 3600) > 6' \
  "FAILED $T::test_c9_registro_cinco_por_hora" "FAILED $T::test_c9_registros_simultaneos_no_pasan_el_tope"
sabotaje $M "registro: 21 por día" \
  '24 * 3600) > 20' '24 * 3600) > 21' \
  "FAILED $T::test_c9_registro_veinte_por_dia" "(200, "

# --- Recuperar contraseña: pedidos simultáneos y bloqueo vencido
sabotaje $M "recuperar contraseña vuelve a chequear y después sumar" \
  'sumar_fallo(db, clave, tope=5) > 5:' 'sumar_fallo(db, clave, tope=5) > 10**6:' \
  "FAILED $T::test_reset_pedidos_simultaneos_no_pasan_el_tope"
sabotaje $L "vencido el bloqueo, la cuenta sigue en vez de volver al tope" \
  '    nueva = case((vencido, tope), else_=_T.c.cuenta + 1)' '    nueva = _T.c.cuenta + 1' \
  "FAILED $T::test_reset_cinco_y_despues_uno_cada_quince_minutos" "[429, 429]"

# --- Eventos
sabotaje $M "eventos: 121 por minuto en /api/ui/event" \
  $'@limiter.limit("120/minute")\nasync def ui_event' $'@limiter.limit("121/minute")\nasync def ui_event' \
  "FAILED $T::test_eventos_120_por_minuto_por_ruta[/api/ui/event-/api/session/state]"
sabotaje $M "eventos: sin sesión se guarda cualquier acción" \
  '            if accion not in _UI_EVENT_SIN_SESION:' '            if False:' \
  "FAILED $T::test_eventos_sin_sesion_no_permitidos_no_se_guardan[click-/api/ui/event]"
sabotaje $M "eventos: hero_cta_clicked sale de la lista" \
  '"pricing_cta_clicked", "hero_cta_clicked", ' '"pricing_cta_clicked", ' \
  "FAILED $T::test_eventos_sin_sesion_permitidos_se_guardan[hero_cta_clicked-/api/session/state]"

# --- Tabla: vencidas y atomicidad
sabotaje $L "contar y sumar no borran las vencidas" \
  $'    await db.execute(delete(_T).where(_T.c.vence <= ahora))\n    cuenta =' $'    cuenta =' \
  "FAILED $T::test_tabla_las_vencidas_se_borran_al_escribir[/auth/recover-username]" \
  "FAILED $T::test_los_limites_por_ip_duran_quince_minutos[/auth/recover-username-cuerpo2-200]" \
  "FAILED $T::test_tabla_las_vencidas_se_borran_al_escribir[/auth/request-password-reset]"
sabotaje $M "al arrancar no se borran las vencidas" \
  '    await _migrate_limites_auth()' '    pass' \
  "FAILED $T::test_tabla_las_vencidas_se_borran_al_arrancar"
sabotaje $L "contar lee y después escribe" \
  $'    ins = ins.on_conflict_do_update(index_elements=[_T.c.clave], set_={\n        "cuenta": _T.c.cuenta + 1,\n    })' \
  $'    async with _conn.engine.connect() as conn:\n        leida = (await conn.execute(select(_T.c.cuenta).where(_T.c.clave == clave, _T.c.vence > ahora))).scalar() or 0\n    ins = ins.on_conflict_do_update(index_elements=[_T.c.clave], set_={\n        "cuenta": leida + 1,\n    })' \
  "FAILED $T::test_c9_registros_simultaneos_no_pasan_el_tope"

# --- una IP más larga que la clave de la tabla (120)
sabotaje $L "la clave larga entra tal cual" \
  '    if len(clave) <= 120:' '    if True:' \
  "FAILED $T::test_tabla_una_ip_larga_entra_en_la_clave[/auth/login]"
sabotaje $L "la clave larga se corta sin hash" \
  '    return clave[:50] + ":" + hashlib.sha256(clave.encode()).hexdigest()' '    return clave[:120]' \
  "FAILED $T::test_s4_dos_ips_largas_con_el_mismo_comienzo_no_se_pisan" "(429, "
sabotaje $L "segundos_bloqueado no acorta la clave" \
  $'0 si no está bloqueada."""\n    clave = _clave(clave)' $'0 si no está bloqueada."""' \
  "FAILED $T::test_s4_una_ip_larga_tambien_se_bloquea" "[401, 401, 401, 401, 401, 401]"
sabotaje $L "limpiar no acorta la clave" \
  '    await db.execute(delete(_T).where(_T.c.clave == _clave(clave)))' \
  '    await db.execute(delete(_T).where(_T.c.clave == clave))' \
  "FAILED $T::test_s4_el_login_correcto_borra_los_fallos[True]" "[401, 429, 429, 429]"
sabotaje $L "una clave de hasta 300 entra tal cual" \
  '    if len(clave) <= 120:' '    if len(clave) <= 300:' \
  "FAILED $T::test_tabla_una_ip_larga_entra_en_la_clave[/auth/login]" \
  "FAILED $T::test_tabla_una_ip_larga_entra_en_la_clave[/auth/register]"

# --- cuánto dura cada corte
sabotaje $L "el bloqueo dura un minuto" \
  'bloqueo: float = 15 * 60,' 'bloqueo: float = 60,' \
  "FAILED $T::test_los_limites_por_ip_duran_quince_minutos[/auth/login-cuerpo0-401]" \
  "FAILED $T::test_los_limites_por_ip_duran_quince_minutos[/auth/request-password-reset-cuerpo1-200]"
sabotaje $M "recuperar usuario: el corte por IP dura un minuto" \
  '15 * 60) > 5:' '60) > 5:' \
  "FAILED $T::test_los_limites_por_ip_duran_quince_minutos[/auth/recover-username-cuerpo2-200]"
sabotaje $M "recuperar usuario: la ventana por email es de un minuto" \
  '3600) > 3:' '60) > 3:' \
  "FAILED $T::test_s6_recuperar_usuario_corta_en_silencio_por_email"

# --- un surrogate suelto o un NUL no da 500
for campo in "    username: TextoCodificable@/auth/login" \
             "class PasswordResetRequest(BaseModel):
    email: TextoCodificable@/auth/request-password-reset" \
             "class RecoverUsernameRequest(BaseModel):
    email: TextoCodificable@/auth/recover-username"; do
  viejo="${campo%@*}"; ruta="${campo##*@}"
  sabotaje $M "$ruta acepta un texto que no se puede guardar" \
    "$viejo" "${viejo/TextoCodificable/str}" \
    "FAILED $T::test_un_surrogate_suelto_no_da_500[True-$ruta-" \
    "FAILED $T::test_un_surrogate_suelto_no_da_500[False-$ruta-"
done
sabotaje $M "/auth/reset-password acepta un token que no se puede guardar" \
  $'class PasswordResetConfirm(BaseModel):\n    token: TextoCodificable' \
  $'class PasswordResetConfirm(BaseModel):\n    token: str' \
  "FAILED $T::test_un_surrogate_suelto_no_da_500[True-/auth/reset-password-" \
  "FAILED $T::test_un_surrogate_suelto_no_da_500[False-/auth/reset-password-"
sabotaje $M "el 422 repite lo que llegó con el de FastAPI" \
  '@app.exception_handler(RequestValidationError)' '' \
  "FAILED $T::test_un_surrogate_suelto_no_da_500[True-/auth/recover-username-" \
  "FAILED $T::test_un_surrogate_suelto_no_da_500[False-/auth/login-"
# Que el login, malo o bueno, cuente con la conexión del pedido y no con una
# segunda sólo se ve con el pool de Postgres: lo mide
# scripts/testing/abuso1_motores.py pg.

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
