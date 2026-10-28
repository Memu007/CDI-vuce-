#!/usr/bin/env bash
# Negativos de RENDIMIENTO-1c: cada sabotaje vuelve a validar el PDF en el
# proceso de la app, saca la fila por usuario, cuenta hojas antes de mirar
# si está encriptado o culpa al PDF cuando el validador se cae, y la prueba tiene que ponerse roja.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/rendimiento1c.sh [SHA]
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_rendimiento1c.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

FS=proyecto_maria/security/file_security.py
DL=proyecto_maria/core/despacho_lector.py
sabotaje $FS "validar el PDF vuelve al proceso de la app" \
  'await validar_pdf_aparte(contents, _pdf_validate_timeout_s(), clave=clave)' \
  '__import__("proyecto_maria.core.despacho_lector", fromlist=["x"]).validar_pdf(contents)' \
  'FAILED tests/test_rendimiento1c.py::test_un_pdf_que_se_infla_no_hace_crecer_la_app'
sabotaje $DL "sin fila por usuario: todas las validaciones comparten los dos lugares" \
  '    if clave is None:
        return await _leer_aparte(data, limite_s, semaforo, _MAX_CPU_LECTURA, "validar")' \
  '    if True:
        return await _leer_aparte(data, limite_s, semaforo, _MAX_CPU_LECTURA, "validar")' \
  'B esperó detrás de las bombas de A'
sabotaje proyecto_maria/main.py "la subida de facturas no pasa el usuario" \
  "max_size=max_upload_bytes, clave=user[\"username\"])" \
  'max_size=max_upload_bytes)' \
  'B esperó detrás de las bombas de A'
sabotaje $DL "vuelve a contar páginas antes de mirar si está encriptado" \
  '        if pdf.is_encrypted:
            return {"encriptado": True, "paginas": 0}' \
  '        if len(pdf.pages) < 0:
            return {"encriptado": True, "paginas": 0}' \
  'FAILED tests/test_rendimiento1c.py::test_validar_aparte_devuelve_lo_mismo_que_antes'
sabotaje $FS "un validador que se cae vuelve a ser un PDF inválido" \
  'raise HTTPException(500, "No pudimos revisar el PDF. Probá de nuevo en un rato.")' \
  'raise HTTPException(400, "Invalid PDF file: no pudimos abrirlo")' \
  'FAILED tests/test_rendimiento1c.py::test_un_validador_que_se_cae_es_un_error_nuestro'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
