#!/usr/bin/env bash
# Negativos de NOMBRES-1: nadie registra un nombre que ya existe con otras mayúsculas, y las
# cuentas viejas que difieren sólo en mayúsculas siguen entrando y promoviéndose por su nombre exacto.
# Cada sabotaje rompe una de esas reglas y la prueba tiene que ponerse roja por ese caso.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/nombres1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si la base no está verde, si un sabotaje no encuentra su patrón, no pone rojo
# o pone rojo donde no debía.
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
PRUEBAS="tests/test_nombres1.py tests/test_permisos2.py"
FALLAS=0

# shellcheck disable=SC2086
if ! base="$("$PY" -m pytest -q --no-cov -p no:cacheprovider $PRUEBAS 2>&1)"; then
  echo "BASE  | en rojo:"; grep -E "^(FAILED|ERROR)" <<<"$base" | head -5; exit 1
fi
echo "BASE  | en verde: $(tail -1 <<<"$base")"

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

T='FAILED tests/test_nombres1.py::test_un_nombre_que_existe_con_otras_mayusculas_no_se_registra'
V='FAILED tests/test_nombres1.py::test_dos_cuentas_viejas_que_difieren_en_mayusculas_siguen_entrando'
CHEQUEO='select(User).where(func.lower(User.username) == username.lower())'

sabotaje "el chequeo vuelve a comparar exacto" "$CHEQUEO" 'select(User).where(User.username == username)' \
  "$T[mayusculas-/auth/register]" "$T[exacto-/auth/register]"
sabotaje "el chequeo no baja la cuenta guardada" "$CHEQUEO" 'select(User).where(User.username == username.lower())' \
  "$T[existe_en_mayusculas-/api/organizations/create]" "$T[mayusculas-/auth/register]"
sabotaje "el chequeo no baja el pedido" "$CHEQUEO" 'select(User).where(func.lower(User.username) == username)' \
  "$T[capitalizada-/auth/register]" "$T[existe_en_mayusculas-/auth/register]"
sabotaje "el login busca sin distinguir mayúsculas" \
  'select(User).where((User.username == username) | (User.email == username))' \
  'select(User).where((func.lower(User.username) == username.lower()) | (User.email == username))' \
  "$V" "$T[mayusculas-/auth/register]"
sabotaje "el arranque promueve sin distinguir mayúsculas" \
  'select(User).where(User.username == identifier))' \
  'select(User).where(func.lower(User.username) == identifier.lower()))' \
  'assert roles.count("admin") == (1 if username == admin else 0)' "$T[mayusculas-/auth/register]"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
