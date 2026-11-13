#!/usr/bin/env bash
# Negativos de ENTRADAS-1: cada sabotaje deshace una regla de la pieza y
# tests/test_entradas1.py tiene que fallar en el caso de esa regla.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entradas1.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia: no toca tu copia ni
# datos compartidos. En SQLite el NUL se guarda: los nombres se miden por lo
# que quedó guardado; el 500 del NUL en Postgres está en scripts/testing/entradas1_postgres.py.
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
X="FAILED $T::test_texto_del_alta_que_no_se_puede_guardar_da_400"
N="FAILED $T::test_nombre_que_no_se_puede_guardar_queda_con_reemplazo"
H="FAILED $T::test_el_manejador_del_422_nunca_responde_json_invalido"
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
    name: Annotated[TextoCodificable, Field(max_length=100)] = None" "    password: str
    name: Annotated[TextoCodificable, Field(max_length=100)] = None"
sabotaje $M "el alta de estudio acepta cualquier clave" "$C[estudio-surrogate]" \
  "    username: str
    password: ClaveNueva
    email: str" "    username: str
    password: str
    email: str"

# --- Qué rechaza el validador
sabotaje $M "sin el tope de 72 bytes" "$C[reset-73_bytes]" \
  ' or len(clave.encode("utf-8")) > 72:' ':'
sabotaje $M "el tope corta antes del byte 73" "FAILED $T::test_clave_de_72_bytes_entra[reset]" \
  'len(clave.encode("utf-8")) > 72' 'len(clave.encode("utf-8")) > 71'
sabotaje $M "el tope deja pasar 73 bytes" "$C[reset-73_bytes]" \
  'len(clave.encode("utf-8")) > 72' 'len(clave.encode("utf-8")) > 73'
sabotaje $M "el tope cuenta caracteres y no bytes" "$C[reset-multibyte_en_el_borde]" \
  'len(clave.encode("utf-8")) > 72' 'len(clave) > 72'
sabotaje $M "sin mirar caracteres que no se guardan" "$C[reset-surrogate]" \
  '    if _NO_GUARDABLE_EN_PG.search(clave) or len(' '    if len('
sabotaje $M "el NUL no cuenta como no guardable" "$N[registro_nombre-nul]" \
  're.compile("[\x00\ud800-\udfff]")' 're.compile("[\ud800-\udfff]")'
sabotaje $M "el surrogate bajo cuenta como guardable" "$C[reset-surrogate_bajo]" \
  're.compile("[\x00\ud800-\udfff]")' 're.compile("[\x00\ud800-\udbff]")'
sabotaje $M "el rechazo de la clave la repite" "$C[reset-surrogate]" \
  'raise ValueError("La contraseña puede' 'raise ValueError(clave + "La contraseña puede'

# --- Textos del alta
sabotaje $M "el nombre del registro sin validar" "$N[registro_nombre-surrogate]" \
  "    name: Annotated[TextoCodificable, Field(max_length=100)] = None" "    name: str = None"
sabotaje $M "la invitación sin validar" "$X[registro_invitacion-surrogate]" \
  "    invite_token: TextoCodificable | None = None" "    invite_token: str | None = None"
sabotaje $M "el nombre del estudio sin validar" "$N[estudio_nombre-surrogate]" \
  "    name: Annotated[TextoCodificable, Field(max_length=200)]" "    name: str"
sabotaje $M "el alta de estudio sin la regla de email" "$X[estudio_email-surrogate]" \
  "    # Validar email duplicado
    clean_email = _email_valido(req.email)" "    # Validar email duplicado
    clean_email = req.email.strip().lower()"
sabotaje $M "la regla de email acepta cualquier cosa" "$X[registro_email-surrogate]" \
  "    if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\$', limpio) or" \
  "    if not limpio or"

# --- Topes y cuerpos
L="FAILED $T::test_texto_mas_largo_que_su_columna_da_4xx_y_el_justo_entra"
sabotaje $M "el nombre del registro sin tope" "$L[registro_nombre]" \
  "Field(max_length=100)" "Field(max_length=101)"
sabotaje $M "el nombre del estudio sin tope" "$L[estudio_nombre]" \
  "Field(max_length=200)" "Field(max_length=201)"
sabotaje $M "el email sin tope de largo" "$L[registro_email]" \
  " or len(limpio) > 100:" ":"
sabotaje $M "el perfil sin la regla de email" "$L[perfil_email]" \
  "            _email_valido(raw_email)" "            pass"
sabotaje $M "el nombre del perfil sin validar" "$N[perfil_nombre-surrogate]" \
  "u.name = _guardable_en_pg(str(raw_name).strip()[:100]) or None" "u.name = str(raw_name).strip()[:100] or None"
G="FAILED $T::test_agrupar_con_cuerpo_raro_da_4xx_en_json"
sabotaje $M "agrupar sin modelo" "$G[agrupar_no_json]" \
  "    pedido: AgruparRequest," "    pedido: Request," \
  "    item_ids = pedido.item_ids" "    item_ids = (await pedido.json()).get(\"item_ids\", [])"
sabotaje $M "los ítems de agrupar sin validar" "$G[agrupar_surrogate]" \
  "    item_ids: list[TextoCodificable] = " "    item_ids: list[str] = "
sabotaje $M "desagrupar sin tope del entero" "$G[desagrupar_enorme]" \
  "Field(ge=-2**31, le=2**31 - 1)" "Field()"

# --- Lo que se responde
R="FAILED $T::test_el_400_que_repite_texto_ajeno_en_una_lista_es_json_valido"
sabotaje $M "el 400 se codifica en UTF-8 estricto" "$R" \
  '.encode("utf-8", "backslashreplace")' '.encode("utf-8")'
sabotaje $M "el 400 sale con la respuesta común" "$R" \
  "    return _JSONConTextoAjeno(
        status_code=exc.status_code," "    return JSONResponse(
        status_code=exc.status_code,"
sabotaje $M "el 422 repite lo que llegó" "FAILED $T::test_el_422_de_un_cuerpo_raro_es_json_valido[nan]" \
  'if k != "input"' 'if True'
sabotaje $M "el 422 repite la clave que llegó" "$C[reset-surrogate]" \
  'if k != "input"' 'if True'
sabotaje $M "el 422 repite el cuerpo de un campo que falta" \
  "FAILED $T::test_el_422_de_un_campo_que_falta_no_repite_la_clave[reset]" \
  'if k != "input"' 'if k != "input" or isinstance(v, dict)'
sabotaje $M "el 422 sale con la respuesta común" "$H[surrogate_en_msg]" \
  'return _JSONConTextoAjeno({"detail"' 'return JSONResponse({"detail"'
sabotaje $M "el 422 escribe NaN" "$H[nan_en_ctx]" \
  'allow_nan=False' 'allow_nan=True'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
