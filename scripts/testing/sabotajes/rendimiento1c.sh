#!/usr/bin/env bash
# Negativos de RENDIMIENTO-1c: cada sabotaje vuelve a validar el PDF en el
# proceso de la app, saca la fila por usuario, cuenta hojas antes de mirar
# si está encriptado, culpa al PDF cuando el validador se cae o cuando no hubo
# lugar, deja de topear la espera, le cobra la espera al PDF o valida sin tope
# de CPU, y la prueba tiene que ponerse roja.
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
        return await _leer_aparte(data, limite_s, semaforo, _MAX_CPU_LECTURA, modo, hasta)' \
  '    if True:
        return await _leer_aparte(data, limite_s, semaforo, _MAX_CPU_LECTURA, modo, hasta)' \
  'B esperó detrás de las bombas de A'
sabotaje proyecto_maria/main.py "la subida de facturas no pasa el usuario" \
  "max_size=max_upload_bytes, clave=user[\"username\"])" \
  'max_size=max_upload_bytes)' \
  'B esperó detrás de las bombas de A'
sabotaje $DL "vuelve a contar páginas antes de mirar si está encriptado" \
  '            if pdf.is_encrypted:
                return {"encriptado": True, "paginas": 0}' \
  '            if len(pdf.pages) < 0:
                return {"encriptado": True, "paginas": 0}' \
  'FAILED tests/test_rendimiento1c.py::test_validar_aparte_devuelve_lo_mismo_que_antes'
sabotaje $FS "un validador que se cae vuelve a ser un PDF inválido" \
  'raise HTTPException(500, "No pudimos revisar el PDF. Probá de nuevo en un rato.")' \
  'raise HTTPException(400, "Invalid PDF file: no pudimos abrirlo")' \
  'FAILED tests/test_rendimiento1c.py::test_un_validador_que_se_cae_es_un_error_nuestro'
sabotaje proyecto_maria/main.py "la lectura de despachos no pasa el usuario" \
  'max_size=_get_max_upload_bytes(),
                                      clave=user["username"])' \
  'max_size=_get_max_upload_bytes())' \
  'despacho: B esperó detrás de las bombas de A'
sabotaje $DL "esperar el turno del usuario no tiene tiempo máximo" \
  'await asyncio.wait_for(fila[0].acquire(), timeout=limite_s)' \
  'await fila[0].acquire()' \
  'FAILED tests/test_rendimiento1c.py::test_esperar_un_lugar_no_culpa_al_archivo'
sabotaje $DL "sin tope de validaciones a la vez" \
  '_VALIDANDO_A_LA_VEZ = 2' '_VALIDANDO_A_LA_VEZ = 1000' \
  "(['b', 'c'], 'pasó')"
sabotaje $DL "la fila del usuario no se borra" \
  '        if not fila[1]:
            del filas[clave]' \
  '        if not fila[1]:
            pass' \
  "(['b', 'c'], {'"
sabotaje $DL "esperar un lugar libre vuelve a culpar al archivo" \
  '    except TimeoutError:
        raise SinLugar from None
    try:
        codigo, salida, errores' \
  '    except TimeoutError:
        raise
    try:
        codigo, salida, errores' \
  "(['b', 'c'], (400, 'No pudimos abrir el PDF: tardó demasiado"
sabotaje $DL "la espera por un lugar se descuenta del tiempo para validar" \
  'await asyncio.wait_for(correr(), timeout=limite_s)' \
  'await asyncio.wait_for(correr(), timeout=hasta - loop.time())' \
  'FAILED tests/test_rendimiento1c.py::test_esperar_casi_todo_el_tope_no_culpa_al_archivo[validar-menos-que-un-pdf]'
sabotaje $DL "validar no corre bajo el tope de CPU" \
  '        with _tope_de_cpu(limite_cpu_s):
            pdf = PdfReader' \
  '        if True:
            pdf = PdfReader' \
  'FAILED tests/test_rendimiento1c.py::test_validar_tiene_tope_de_cpu'
sabotaje $DL "el proceso aparte no le pasa el tope a validar" \
  '_MODOS[modo][0](data, limite_cpu_s)' '_MODOS[modo][0](data)' \
  'FAILED tests/test_rendimiento1c.py::test_validar_tiene_tope_de_cpu'
sabotaje $DL "pasar el tope de CPU no sale como demasiado pesado" \
  'except (MemoryError, _DemasiadoTrabajo):' 'except MemoryError:' \
  'FAILED tests/test_rendimiento1c.py::test_validar_tiene_tope_de_cpu'
sabotaje $DL "esperar el turno del usuario vuelve a culpar al archivo" \
  '        except TimeoutError:
            raise SinLugar from None
        try:' \
  '        except TimeoutError:
            raise
        try:' \
  "(['a'], (400, 'No pudimos abrir el PDF: tardó demasiado"
sabotaje $FS "sin lugar vuelve a ser un 400" \
  'raise HTTPException(503, "Hay muchos PDFs en revisión. Probá de nuevo en un rato.")' \
  'raise HTTPException(400, "No pudimos abrir el PDF: tardó demasiado. Probá con otro archivo.")' \
  "(['b', 'c'], (400, 'No pudimos abrir el PDF: tardó demasiado"
sabotaje $DL "quedarse sin memoria en C vuelve a ser un PDF inválido" \
  'except (MemoryError, SystemError) as e:' 'except MemoryError as e:' \
  'DID NOT RAISE'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
