#!/usr/bin/env bash
# Negativos de PERMISOS-2 y PERMISOS-3: admin es sólo el rol guardado, el arranque se lo pone
# a la cuenta de ADMIN_USERNAMES y nadie registra un nombre de la lista ni uno que se lea igual.
# Cada sabotaje rompe una de esas reglas y la prueba tiene que ponerse roja por ese caso.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/permisos2.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón, no pone rojo o pone rojo donde no debía.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PRUEBAS="tests/test_permisos2.py tests/test_admin_solo_admin.py"
FALLAS=0

# sabotaje <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir> [lo que no]
sabotaje() {
  local nombre="$1" viejo="$2" nuevo="$3" esperado="$4" ajeno="${5:-}"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - proyecto_maria/main.py "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  # shellcheck disable=SC2086
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider $PRUEBAS 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif ! grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^(E |FAILED)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  elif [ -n "$ajeno" ] && grep -qF -- "$ajeno" <<<"$salida"; then
    echo "ROJO? | $nombre: también rojo en «$ajeno»"; FALLAS=$((FALLAS+1))
  else
    echo "ROJO  | $nombre: dice «$esperado»"
  fi
}

T1='FAILED tests/test_permisos2.py::test_un_nombre_de_admin_usernames_no_se_registra'
T2='FAILED tests/test_permisos2.py::test_la_cuenta_de_admin_usernames_sigue_siendo_admin_al_reiniciar'
LLAMADA_REGISTRO='    await _exigir_username_libre(db, request.username)'
LLAMADA_ESTUDIO='    await _exigir_username_libre(db, req.username)'
COMPARA='                if user and "admin" not in roles:'

sabotaje "ADMIN_USERNAMES vuelve a dar admin sin el rol" \
  '    return "admin" in roles_de(user)' \
  '    return user["username"] in _admin_usernames() or "admin" in roles_de(user)' \
  'FAILED tests/test_admin_solo_admin.py::test_en_admin_usernames_sin_el_rol_no_entra'
sabotaje "el registro deja pasar un nombre de la lista" "$LLAMADA_REGISTRO" \
  "$LLAMADA_REGISTRO if request.username not in _admin_usernames() else None" \
  "$T1[solo-/auth/register]" "$T1[solo-/api/organizations/create]"
sabotaje "crear un estudio deja pasar un nombre de la lista" "$LLAMADA_ESTUDIO" \
  "$LLAMADA_ESTUDIO if req.username not in _admin_usernames() else None" \
  "$T1[en_una_lista-/api/organizations/create]" "$T1[solo-/auth/register]"
sabotaje "el chequeo compartido no reserva la lista" \
  '    if username.lower() in {u.lower() for u in _admin_usernames()} or (' '    if (' \
  "$T1[en_una_lista-/auth/register]"
sabotaje "el arranque no pone el rol" "$COMPARA" '                if False:' "$T2[None]"
sabotaje "el arranque mira roles como texto o clave" \
  '                roles = roles_de({"roles": user.roles}) if user else []' \
  '                roles = (user.roles or []) if user else []' \
  "$T2[roles4]" "$T2[roles2]"
sabotaje "el arranque suma admin aunque ya lo tenga" "$COMPARA" '                if user:' "$T2[roles2]"

T3='FAILED tests/test_permisos2.py::test_un_nombre_que_se_ve_como_otro_no_se_registra'
sabotaje "el formato acepta un salto de línea final" \
  '    if not re.fullmatch(r"[a-zA-Z0-9_-]{3,30}", username):' \
  '    if not re.match(r"^[a-zA-Z0-9_-]{3,30}$", username):' \
  "$T3[lf_final-/auth/register]" "$T3[acento-/auth/register]"
sabotaje "la reserva distingue las mayúsculas del pedido" \
  '    if username.lower() in {u.lower()' '    if username in {u.lower()' \
  "$T3[mayusculas-/api/organizations/create]" "$T3[lista_en_mayusculas-/auth/register]"
sabotaje "la reserva distingue las mayúsculas de la lista" \
  'in {u.lower() for u in _admin_usernames()}' 'in _admin_usernames()' \
  "$T3[lista_en_mayusculas-/api/organizations/create]" "$T3[mayusculas-/auth/register]"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
