#!/usr/bin/env bash
# Negativos de RENDIMIENTO-1: cada sabotaje vuelve a leer en el hilo del
# servidor (o le saca el tiempo máximo) y la prueba tiene que ponerse roja.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/rendimiento1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
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
FALLAS=0

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_rendimiento1.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
sabotaje $M "el PDF se vuelve a leer en el hilo del servidor" \
  'result = await _leer_pdf_aparte(process_pdf, contents)' \
  'result = process_pdf(contents)' \
  'FAILED tests/test_rendimiento1.py::test_health_responde_mientras_se_lee_un_pdf'
sabotaje $M "el texto del PDF se vuelve a leer en el hilo del servidor" \
  'pdf_text = await _leer_pdf_aparte(_extract_pdf_text, contents)' \
  'pdf_text = _extract_pdf_text(contents)' \
  'FAILED tests/test_rendimiento1.py::test_health_responde_mientras_se_lee_el_texto_del_pdf'
sabotaje $M "Gemini vuelve a correr en el hilo del servidor" \
  '        for sug in await asyncio.to_thread(
            _suggest_ncm_with_gemini, descripcion, 5 - len(sugerencias)
        ):' \
  '        for sug in _suggest_ncm_with_gemini(descripcion, 5 - len(sugerencias)):' \
  'FAILED tests/test_rendimiento1.py::test_health_responde_mientras_gemini_sugiere_ncm'
sabotaje $M "la lectura pierde el tiempo máximo" \
  'asyncio.to_thread(funcion, *args), timeout=_pdf_read_timeout_s()' \
  'asyncio.to_thread(funcion, *args), timeout=None' \
  'FAILED tests/test_rendimiento1.py::test_lectura_con_tiempo_maximo_y_error_claro'
sabotaje proyecto_maria/security/file_security.py "validar el PDF vuelve al hilo del servidor" \
  'asyncio.to_thread(_abrir_pdf, contents),' \
  'asyncio.sleep(0, _abrir_pdf(contents)),' \
  'FAILED tests/test_rendimiento1.py::test_health_responde_mientras_se_valida_el_pdf'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
