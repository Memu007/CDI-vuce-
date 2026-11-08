#!/usr/bin/env bash
# Negativos de ENTRADAS-3: cada sabotaje deshace una regla de la pieza y la
# prueba de esa regla tiene que fallar. Lo que sólo se ve en Postgres lo mide
# scripts/testing/entradas3_postgres.py, contra PG_URL.
#
# uso: PY=/ruta/al/venv/bin/python PG_URL=postgresql://cdi@127.0.0.1:55432/postgres \
#        scripts/testing/sabotajes/entradas3.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y una base de Postgres que crea y borra.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG_URL="${PG_URL:?falta PG_URL: un Postgres local y descartable}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo. Corre con $CORRER.
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
  salida="$($CORRER)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|FALLA|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

T=tests/test_entradas3.py
M=proyecto_maria/main.py
HON="FAILED $T::test_cuerpo_mas_hondo_que_la_pila_da_400"
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
pytest_() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -W ignore -rf "$T" 2>&1; }
postgres_() { env -u DATABASE_URL "$PY" scripts/testing/entradas3_postgres.py "$PG_URL" 2>&1; }

rm -f test.db
for CORRER in pytest_ postgres_; do
  if ! $CORRER >/dev/null; then
    echo "BASE  | $CORRER ya está en rojo sin sabotaje: no se puede medir nada"; $CORRER | grep -E "FAILED|FALLA"; exit 1
  fi
done
echo "BASE  | en verde"

CORRER=pytest_
# --- Cuerpo más hondo que la pila
sabotaje $M "aprender productos recorre el cuerpo sin cuidar la pila" "$HON[aprender_productos]" \
  "    body = _cuerpo_guardable(body)
    items" "    body = _sin_nul(body)
    items"
sabotaje $M "guardar el despacho recorre el cuerpo sin cuidar la pila" "$HON[guardar_despacho]" \
  "body = _cuerpo_guardable(body, rechazar_medio_par=False)" "body = _sin_nul(body)"
sabotaje $M "editar el producto recorre el cuerpo sin cuidar la pila" "$HON[editar_producto]" \
  "body = _cuerpo_guardable(body) if isinstance(body, dict) else {}" "body = _sin_nul(body) if isinstance(body, dict) else {}"

# --- Consulta, cliente y números
sabotaje $M "un NUL en la consulta pasa" "FAILED $T::test_nul_en_la_consulta_da_400" \
  'if scope["type"] == "http" and b"\x00" in unquote_to_bytes(' 'if False and b"\x00" in unquote_to_bytes('
sabotaje $M "un campo del cliente que no es texto pasa" \
  "FAILED $T::test_campo_del_cliente_que_no_es_texto_da_400_y_no_guarda[alta" \
  "elif clave in _TEXTOS_DEL_CLIENTE and not isinstance(valor, str):" "elif False:"
NUL_="FAILED $T::test_campo_del_cliente_en_null_queda_vacio_salvo_el_nombre"
sabotaje $M "un null del cliente se guarda como «None»" "$NUL_[alta" \
  "            valor = \"\"
        elif" "            valor = str(valor)
        elif"
sabotaje $M "un nombre null deja al cliente sin nombre" "$NUL_[edicion" \
  'clave != "nombre" and valor is None:' 'valor is None:'
sabotaje $M "un número enorme se guarda" "FAILED $T::test_numero_enorme_da_400_y_no_guarda[1e16" \
  "    if abs(numero) > 1e15:" "    if False:"

CORRER=postgres_
# --- Lo que sólo se ve en Postgres
sabotaje $M "la ruta con NUL no queda en api_logs" "FALLA | NUL en la ruta" \
  "endpoint=_guardable_en_pg(endpoint)[:200]," "endpoint=endpoint[:200],"
sabotaje $M "la ruta larga no queda en api_logs" "FALLA | ruta de 300 caracteres" \
  "endpoint=_guardable_en_pg(endpoint)[:200]," "endpoint=_guardable_en_pg(endpoint),"
sabotaje $M "un número enorme revienta el listado en Postgres" "FALLA | después de 1e308" \
  "    if abs(numero) > 1e15:" "    if False:"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
