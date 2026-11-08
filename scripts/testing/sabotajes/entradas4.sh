#!/usr/bin/env bash
# Negativos de ENTRADAS-4: cada sabotaje deshace una regla de la pieza y
# tests/test_entradas4.py más scripts/testing/entradas4_postgres.py, contra
# PG_URL, tienen que fallar en esa regla.
#
# uso: PY=/ruta/al/venv/bin/python PG_URL=postgresql://cdi@127.0.0.1:55432/postgres \
#        scripts/testing/sabotajes/entradas4.sh [SHA]
# Trabaja en un worktree descartable y una base de Postgres que crea y borra.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG_URL="${PG_URL:?falta PG_URL: un Postgres local y descartable}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT" || exit 2
FALLAS=0
correr() {
  local codigo=0
  rm -f test.db
  GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
    DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares ENVIRONMENT=test DATABASE_URL=sqlite+aiosqlite:///./test.db \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_entradas4.py 2>&1 || codigo=1
  env -u DATABASE_URL "$PY" scripts/testing/entradas4_postgres.py "$PG_URL" 2>&1 || codigo=1
  return $codigo
}

# sabotaje <archivo> <nombre> <viejo> <nuevo> <lo que el rojo tiene que decir>...
# <viejo> tiene que aparecer una sola vez en <archivo>.
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p, viejo, nuevo = sys.argv[1:]; s = open(p, encoding="utf-8").read()
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  git checkout -q -- proyecto_maria/
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "FALLA|^E |Error" <<<"$salida" | head -4; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

if ! correr >"$TMPD/base.log"; then
  echo "BASE  | ya está en rojo sin sabotaje: no se puede medir nada"; grep -E "FALLA|^E " "$TMPD/base.log" | head -4; exit 1
fi
echo "BASE  | en verde"

M=proyecto_maria/main.py
CLI="    cliente_id: TextoCodificable | None = Form(default=None),"
RUTA='@app.post("/upload_excel_v2/")'
SIN="campos Form de texto sin _guardable_en_pg:"
sabotaje $M "el cliente del Excel llega con su NUL a la base" \
  "$CLI" "    cliente_id: str | None = Form(default=None)," \
  "$SIN [('/upload_excel_v2/', 'cliente_id')]" "FALLA | NUL en cliente_id de /upload_excel_v2/: 500"
sabotaje $M "un campo Form de texto nuevo en la ruta" \
  "$CLI" "$CLI
    nota: str | None = Form(default=None)," \
  "$SIN [('/upload_excel_v2/', 'nota')]" "FALLA | campos Form de texto:"
sabotaje $M "un campo Form de texto en una dependencia" \
  "$RUTA" "def _sabotaje(nota: str = Form(default='')):
    return nota


@app.post(\"/upload_excel_v2/\", dependencies=[Depends(_sabotaje)])" \
  "$SIN [('/upload_excel_v2/', 'nota')]"
sabotaje $M "un modelo de texto como Form" \
  "$RUTA" "class _Sabotaje(BaseModel):
    nota: str = ''


@app.post(\"/sabotaje/\")
async def _sabotaje(datos: Annotated[_Sabotaje, Form()]):
    return {}


$RUTA" \
  "$SIN [('/sabotaje/', 'datos')]"
sabotaje proyecto_maria/routers/quote_router.py "un campo Form de texto en un router" \
  '@router.post("/share")' '@router.post("/sabotaje")
async def _sabotaje(nota: str = __import__("fastapi").Form(default="")):
    return {}


@router.post("/share")' \
  "$SIN [('/api/quotes/sabotaje', 'nota')]"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
