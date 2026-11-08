#!/usr/bin/env bash
# Negativos de EMAIL-1: cada sabotaje deshace una regla y tests/test_email1.py
# tiene que fallar por ese motivo.
# Buscar: recuperar usuario, recuperar contraseña y el login encuentran el
# email sin mirar mayúsculas ni espacios.
# Pares (cuentas viejas con el mismo email en distintas mayúsculas): el exacto
# gana; sin exacto no se elige ninguna y la respuesta es la de un email que no
# existe; el perfil de una cuenta del par se guarda sin reescribir su email.
# Crear o cambiar: el perfil, el registro, el alta de estudio y la invitación
# no dejan repetir un email con otras mayúsculas; el registro de prueba con
# reemplazo archiva todas las cuentas de ese email; el registro con
# invitación acepta el email invitado con otras mayúsculas.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/email1.sh [SHA]
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

pytest_e1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_email1.py 2>&1
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
  salida="$(pytest_e1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_e1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi

# --- Buscar sin mirar mayúsculas
sabotaje $M "recuperar compara el email tal cual" \
  '    res = await db.execute(select(User).where(func.lower(User.email) == func.lower(email)).limit(2))' \
  '    res = await db.execute(select(User).where(User.email == email).limit(2))' \
  "FAILED tests/test_email1.py::test_recuperar_usuario_sin_mayusculas" \
  "FAILED tests/test_email1.py::test_recuperar_contrasena_sin_mayusculas"
sabotaje $M "recuperar no saca los espacios" \
  $'    email = (email or "").strip()\n    if not email:' \
  $'    email = email or ""\n    if not email:' \
  "test_recuperar_usuario_sin_mayusculas[caro@{d}-  CARO@{D}  ]" \
  "test_recuperar_contrasena_sin_mayusculas[caro@{d}-  CARO@{D}  ]"
sabotaje $M "el login no busca sin mayúsculas" \
  '    if not user and "@" in (username or ""):' \
  '    if False:' \
  "FAILED tests/test_email1.py::test_login_por_email_sin_mayusculas"

# --- Pares
sabotaje $M "par sin exacto: se elige la primera" \
  '    if len(cuentas) > 1:' \
  '    if len(cuentas) > 99:' \
  "FAILED tests/test_email1.py::test_par_sin_exacto_no_manda_nada" \
  "FAILED tests/test_email1.py::test_la_respuesta_no_cambia_exista_o_no"
sabotaje $M "par sin exacto: la respuesta lo delata" \
  '        logging.warning("EMAIL-1: el email pedido es de más de una cuenta (mayúsculas distintas); no se elige ninguna")' \
  '        raise HTTPException(status_code=409, detail="Ese email es de varias cuentas")' \
  "FAILED tests/test_email1.py::test_la_respuesta_no_cambia_exista_o_no"
sabotaje $M "par: no gana el exacto" \
  $'    cuenta = exacta.scalars().first()\n    if cuenta:' \
  $'    cuenta = exacta.scalars().first()\n    if False:' \
  "FAILED tests/test_email1.py::test_par_el_exacto_gana[/auth/recover-username-dev_username_hint]" \
  "FAILED tests/test_email1.py::test_par_el_exacto_gana[/auth/request-password-reset-dev_token_hint]"
sabotaje $M "par: el perfil reescribe el email aunque no cambie" \
  $'    # Email editable para contacto/login\n    if cambia_email:' \
  $'    # Email editable para contacto/login\n    if "email" in body:' \
  "FAILED tests/test_email1.py::test_par_el_perfil_se_guarda_sin_tocar_el_email"

# --- Crear o cambiar un email
sabotaje $M "el perfil busca el duplicado tal cual" \
  '                select(User).where(func.lower(User.email) == raw_email, User.username != u.username)' \
  '                select(User).where(User.email == raw_email, User.username != u.username)' \
  "FAILED tests/test_email1.py::test_perfil_no_toma_un_email_ajeno[Gabi@{D}]"
sabotaje $M "el registro busca el duplicado tal cual" \
  '        result = await db.execute(select(User).where(func.lower(User.email) == clean_email))' \
  '        result = await db.execute(select(User).where(User.email == clean_email))' \
  "FAILED tests/test_email1.py::test_registro_no_crea_un_email_existente[Ines@{D}]"
sabotaje $M "el alta de estudio busca el duplicado tal cual" \
  '    existing_email = await db.execute(select(User).where(func.lower(User.email) == clean_email))' \
  '    existing_email = await db.execute(select(User).where(User.email == clean_email))' \
  "FAILED tests/test_email1.py::test_alta_de_estudio_no_crea_un_email_existente"
sabotaje $M "la invitación busca al miembro tal cual" \
  '        select(User).where(func.lower(User.email) == clean_email, User.organization_id == org.id)' \
  '        select(User).where(User.email == clean_email, User.organization_id == org.id)' \
  "FAILED tests/test_email1.py::test_invitacion_a_un_miembro_con_otras_mayusculas"
sabotaje $M "el registro con reemplazo archiva sólo una cuenta" \
  '                for existing_email_user in existing_email_users:' \
  '                for existing_email_user in existing_email_users[:1]:' \
  "FAILED tests/test_email1.py::test_registro_de_prueba_con_reemplazo_archiva_todo_el_par"
# El registro pasa el email a minúsculas dos veces (al validar y al buscar el
# duplicado): sacar una sola no es un defecto, el sabotaje saca las dos.
git checkout -q -- proyecto_maria/
if aplicar $M '    clean_email = (request.email or "").strip().lower()' \
              '    clean_email = (request.email or "").strip()' &&
   aplicar $M '        clean_email = request.email.strip().lower()' \
              '        clean_email = request.email.strip()'; then
  salida="$(pytest_e1)"; codigo=$?
  juzgar "el registro no pasa el email a minúsculas" "$salida" "$codigo" \
    "FAILED tests/test_email1.py::test_registro_con_invitacion_acepta_otras_mayusculas"
else
  echo "ROTO  | el registro no pasa el email a minúsculas: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1))
fi
git checkout -q -- proyecto_maria/

sabotaje $M "la pista de dev vuelve con ENVIRONMENT que falta (RESET-2)" \
  'return not email_sent and IS_TESTING' \
  'return not email_sent and not IS_PRODUCTION' \
  "FAILED tests/test_email1.py::test_la_pista_de_dev_solo_en_el_entorno_de_prueba"

sabotaje $M "un email vacío encuentra la cuenta sin email" \
  '    email = (email or "").strip()
    if not email:' \
  '    email = (email or "").strip()
    if False:' \
  "FAILED tests/test_email1.py::test_un_email_vacio_no_encuentra_la_cuenta_sin_email[/auth/recover-username-dev_username_hint]" \
  "FAILED tests/test_email1.py::test_un_email_vacio_no_encuentra_la_cuenta_sin_email[/auth/request-password-reset-dev_token_hint]"

echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
