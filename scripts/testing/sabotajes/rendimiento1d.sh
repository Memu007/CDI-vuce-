#!/usr/bin/env bash
# Negativos de RENDIMIENTO-1d: cada sabotaje deshace una línea de la pieza y
# tests/test_rendimiento1d.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/rendimiento1d.sh [SHA]
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
T=tests/test_rendimiento1d.py
CORRE=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T")

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
  salida="$("${CORRE[@]}" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
    grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
L=proyecto_maria/core/despacho_lector.py

if ! "${CORRE[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $M "el texto del vendedor vuelve a sacarse en un hilo de la app" \
  $'leido = await validar_pdf_aparte(\n                    contents, _pdf_vendor_timeout_s(), clave=user["username"], modo="texto")' \
  'leido = {"texto": await _leer_pdf_aparte(__import__("proyecto_maria.pdf_extractor", fromlist=["x"]).extraer_texto_pdf_seguro, contents, limite=_pdf_vendor_timeout_s())}' \
  "la app creció"
sabotaje $L "el texto sin topes por flujo" \
  $'    with apply_configuration(**_TOPES), _tope_de_cpu(limite_cpu_s):\n        return {"texto"' \
  $'    with _tope_de_cpu(limite_cpu_s):\n        return {"texto"' \
  "sacar el texto llegó a"
sabotaje $L "el texto sin tope de CPU" \
  $'    with apply_configuration(**_TOPES), _tope_de_cpu(limite_cpu_s):\n        return {"texto"' \
  $'    with apply_configuration(**_TOPES):\n        return {"texto"' \
  "DID NOT RAISE"
sabotaje $L "el proceso aparte no sabe sacar el texto" \
  '"texto": (texto_plano_del_pdf, "el lector de texto del PDF")' \
  '"texto": (validar_pdf, "el lector de texto del PDF")' \
  "'normal': [200, None]"
sabotaje $L "el texto ocupa los lugares de validar" \
  'lugares = _SACANDO_TEXTO if modo == "texto" else _VALIDANDO' \
  'lugares = _VALIDANDO' \
  "assert 503 == "

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
