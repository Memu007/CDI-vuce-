#!/usr/bin/env bash
# Negativos de CLIENTE-1b en la API y en el script de datos: cada sabotaje
# deshace una línea de la pieza y tests/test_cliente1b*.py tiene que fallar
# por ese motivo. (Los de la pantalla están en cliente1.sh.)
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cliente1b.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia: no toca tu copia ni
# datos compartidos. Sale con error si un sabotaje no encuentra su patrón o no
# pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0

correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_cliente1b.py tests/test_cliente1b_script.py 2>&1; }

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/ scripts/datos/
  rm -f test.db
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep FAILED <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
D=scripts/datos/clientes_fecha_inic_activ.py

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi

# La API
sabotaje $M "el alta guarda lo que llega, como antes" \
  'fecha_inic_activ = _fecha_inic_activ_de_api(client.get("fecha_inic_activ"))' \
  'fecha_inic_activ = str(client.get("fecha_inic_activ", "")).strip()[:10]' \
  "FAILED tests/test_cliente1b.py::test_el_alta_valida_la_fecha_de_inicio[None]"
sabotaje $M "la edición guarda lo que llega, como antes" \
  'fecha_inic_activ = _fecha_inic_activ_de_api(client_data["fecha_inic_activ"])' \
  'fecha_inic_activ = str(client_data["fecha_inic_activ"] or "").strip()[:10]' \
  "FAILED tests/test_cliente1b.py::test_la_edicion_valida_la_fecha_de_inicio['2015-02-30']"
sabotaje $M "un null se guarda «None»" \
  $'    if raw is None:\n        return ""' $'    if raw is None:\n        return "None"' \
  "FAILED tests/test_cliente1b.py::test_el_alta_valida_la_fecha_de_inicio[None]"
sabotaje $M "DD/MM/AAAA no se pasa a AAAA-MM-DD" \
  "        return date(anio, mes, dia).isoformat()" $'        date(anio, mes, dia)\n        return texto' \
  "FAILED tests/test_cliente1b.py::test_el_alta_valida_la_fecha_de_inicio['15/03/2015']"
sabotaje $M "no se mira que la fecha exista" \
  "        return date(anio, mes, dia).isoformat()" "        return f\"{anio:04d}-{mes:02d}-{dia:02d}\"" \
  "FAILED tests/test_cliente1b.py::test_la_edicion_valida_la_fecha_de_inicio['2015-02-30']"
sabotaje $M "DD/MM/AAAA con año de dos cifras pasa" \
  'r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})"' 'r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{2,4})"' \
  "FAILED tests/test_cliente1b.py::test_el_alta_valida_la_fecha_de_inicio['15/03/15']"
sabotaje $M "el error no dice qué formatos sirven" \
  '"usá AAAA-MM-DD o DD/MM/AAAA, o dejala vacía."' '"revisala."' \
  "FAILED tests/test_cliente1b.py::test_el_alta_valida_la_fecha_de_inicio['None']"
sabotaje $M "la edición sin la fecha la borra" \
  $'    if "fecha_inic_activ" in client_data:\n        client.fecha_inic_activ = fecha_inic_activ' \
  $'    client.fecha_inic_activ = fecha_inic_activ if "fecha_inic_activ" in client_data else ""' \
  "FAILED tests/test_cliente1b.py::test_editar_sin_mandar_la_fecha_la_conserva"

# El script
sabotaje $D "sin la opción igual arregla" \
  "            if arreglar_none:" "            if True:" \
  "FAILED tests/test_cliente1b_script.py::test_sin_la_opcion_informa_y_no_cambia_nada"
sabotaje $D "con la opción arregla también otras" \
  '"WHERE id = :id AND fecha_inic_activ = :fecha"' '"WHERE fecha_inic_activ IS NOT NULL OR id = :id OR id = :fecha"' \
  "FAILED tests/test_cliente1b_script.py::test_con_la_opcion_deja_vacias_solo_las_none"
sabotaje $D "con la opción vacía sólo la «None» exacta" \
  '{"id": cid, "fecha": fecha}' '{"id": cid, "fecha": "None"}' \
  "FAILED tests/test_cliente1b_script.py::test_con_la_opcion_vacia_cada_none_que_informa"
sabotaje $D "una URL sqlite:/// no se pasa al driver async" \
  $'    if url.startswith("sqlite://"):\n        return "sqlite+aiosqlite://" + url[len("sqlite://"):]\n' '' \
  "FAILED tests/test_cliente1b_script.py::test_acepta_la_url_sqlite_sin_driver"
sabotaje $D "una fecha que no sirve no se informa" \
  "            no_sirven.append(cid)" "            pass" \
  "FAILED tests/test_cliente1b_script.py::test_sin_la_opcion_informa_y_no_cambia_nada"
sabotaje $D "el informe muestra la fecha" \
  '            no_sirven.append(cid)' '            no_sirven.append(f"{cid} {texto}")' \
  "FAILED tests/test_cliente1b_script.py::test_sin_la_opcion_informa_y_no_cambia_nada"
sabotaje $D "la base sale de DATABASE_URL" \
  'p.add_argument("--base", required=True,' 'p.add_argument("--base", default=os.environ.get("DATABASE_URL"),' \
  "FAILED tests/test_cliente1b_script.py::test_la_base_es_obligatoria"

git checkout -q -- proyecto_maria/ scripts/datos/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
