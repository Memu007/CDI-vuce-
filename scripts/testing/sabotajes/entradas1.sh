#!/usr/bin/env bash
# Negativos de ENTRADAS-1: cada sabotaje deshace una regla de la pieza y
# tests/test_entradas1.py tiene que fallar en el caso de esa regla.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entradas1.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia: no toca tu copia ni
# datos compartidos. El NUL sólo rompe en Postgres, así que acá cada regla se
# mide con el surrogate; el lado del NUL está en scripts/testing/entradas1_postgres.py.
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

T=tests/test_entradas1.py
C="FAILED $T::test_clave_nueva_que_no_se_puede_hashear_da_422_y_no_cambia_nada"
X="FAILED $T::test_texto_del_alta_que_no_se_puede_guardar_no_da_500"
M=proyecto_maria/main.py
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -W ignore -rf "$T" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi
echo "BASE  | en verde"

# --- La clave nueva pasa por el validador en las cuatro vías
sabotaje $M "reset acepta cualquier clave" "$C[reset-surrogate]" \
  "    token: TextoCodificable
    new_password: ClaveNueva" "    token: TextoCodificable
    new_password: str"
sabotaje $M "cambio de clave acepta cualquier clave" "$C[cambio-surrogate]" \
  "    current_password: str
    new_password: ClaveNueva" "    current_password: str
    new_password: str"
sabotaje $M "el registro acepta cualquier clave" "$C[registro-surrogate]" \
  "    password: ClaveNueva
    name: TextoCodificable = None" "    password: str
    name: TextoCodificable = None"
sabotaje $M "el alta de estudio acepta cualquier clave" "$C[estudio-surrogate]" \
  "    name: TextoCodificable
    username: str
    password: ClaveNueva" "    name: TextoCodificable
    username: str
    password: str"

# --- Qué rechaza el validador
sabotaje $M "sin el tope de 72 bytes" "$C[reset-73_bytes_o_mas]" \
  ' or len(clave.encode("utf-8")) > 72:' ':'
sabotaje $M "el tope corta antes del byte 73" "FAILED $T::test_clave_de_72_bytes_entra[reset]" \
  'len(clave.encode("utf-8")) > 72' 'len(clave.encode("utf-8")) > 71'
sabotaje $M "sin mirar caracteres que no se guardan" "$C[reset-surrogate]" \
  '    if _NO_GUARDABLE_EN_PG.search(clave) or len(' '    if len('

# --- Textos del alta
sabotaje $M "el nombre del registro sin validar" "$X[registro_nombre-surrogate]" \
  "    name: TextoCodificable = None" "    name: str = None"
sabotaje $M "la invitación sin validar" "$X[registro_invitacion-surrogate]" \
  "    invite_token: TextoCodificable | None = None" "    invite_token: str | None = None"
sabotaje $M "el nombre del estudio sin validar" "$X[estudio_nombre-surrogate]" \
  "class CreateOrgRequest(BaseModel):
    name: TextoCodificable" "class CreateOrgRequest(BaseModel):
    name: str"
sabotaje $M "el alta de estudio sin la regla de email" "$X[estudio_email-surrogate]" \
  "    clean_email = _email_valido(req.email)" "    clean_email = req.email.strip().lower()"
sabotaje $M "la regla de email acepta cualquier cosa" "$X[registro_email-surrogate]" \
  "    if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\$', limpio):" \
  "    if not limpio:"

# --- Lo que se responde
sabotaje $M "el 400 repite el detalle tal cual" "$X[registro_plan-surrogate]" \
  "    detail = _guardable_en_pg(exc.detail) if exc.detail" "    detail = exc.detail if exc.detail"
sabotaje $M "el 422 repite lo que llegó" "FAILED $T::test_el_422_de_un_cuerpo_raro_es_json_valido[nan]" \
  'if k != "input"' 'if True'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
