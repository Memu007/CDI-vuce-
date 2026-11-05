# Arnés común de los sabotajes de CSRF: se carga con `source` después de fijar
# PANTALLA (el caso de navegador que corre `pantalla`) y deja listos los
# corredores pytest_csrf y pantalla, la función sabotaje y la base en verde.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8878}"
PANTALLA="${PANTALLA:?falta PANTALLA}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
# pantalla corre dentro de $(...): el PID de la API pasa por archivo para que la trampa lo vea.
trap '[ -s "$TMPD/api.pid" ] && kill "$(cat "$TMPD/api.pid")" 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
FALLAS=0

pytest_csrf() {
  DATABASE_URL="sqlite+aiosqlite:///$TMPD/pytest.db" GEMINI_API_KEY=test-key ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_csrf.py 2>&1
}

pantalla() {
  rm -f "$TMPD/local.db"
  if (exec 3<>"/dev/tcp/127.0.0.1/$PUERTO") 2>/dev/null; then
    echo "FALLA: el puerto $PUERTO ya está ocupado"; return 1
  fi
  ENVIRONMENT=development GEMINI_API_KEY=test-key CSRF_ENFORCE=true \
    JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
    ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
    DATABASE_URL="sqlite+aiosqlite:///$TMPD/local.db" "$PY" -m uvicorn proyecto_maria.main:app \
    --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  local api=$! codigo=1
  echo "$api" >"$TMPD/api.pid"
  for _ in $(seq 1 60); do curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1 && codigo=0 && break; sleep 1; done
  if [ "$codigo" -ne 0 ]; then echo "FALLA: la API no arrancó"; tail -5 "$TMPD/api.log"
  else BASE_URL="http://127.0.0.1:$PUERTO" node "scripts/testing/$PANTALLA" 2>&1; codigo=$?; fi
  kill "$api" 2>/dev/null; wait "$api" 2>/dev/null; : >"$TMPD/api.pid"
  return $codigo
}

# sabotaje <corredor> <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo>
# <viejo> tiene que aparecer una sola vez en el archivo.
sabotaje() {
  local corredor="$1" archivo="$2" nombre="$3" esperado="$4" viejo="$5" nuevo="$6"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p, viejo, nuevo = sys.argv[1:]
s = open(p, encoding="utf-8").read()
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$($corredor)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
    grep -E "FAILED|FALLA" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

for corredor in pytest_csrf pantalla; do
  if ! salida="$($corredor)"; then
    echo "BASE  | $corredor ya está en rojo sin sabotaje: no se puede medir nada"
    grep -E "FAILED|FALLA" <<<"$salida" | head -5; exit 1
  fi
done

