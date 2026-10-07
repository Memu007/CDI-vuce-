#!/usr/bin/env bash
# Negativos de RENDIMIENTO-1b: cada sabotaje deshace un punto de la pieza y
# la prueba tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/rendimiento1b.sh [SHA]
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_rendimiento1b.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
E=proyecto_maria/pdf_extractor.py
F=proyecto_maria/security/file_security.py
sabotaje $E "el vendedor vuelve a leer con pdfminer" \
  '        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        paginas = []' \
  '        return _extract_pdf_text(data)
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        paginas = []' \
  'FAILED tests/test_rendimiento1b.py::test_el_vendedor_se_adivina_sin_pdfminer_ni_pdfplumber'
sabotaje $M "los tiempos en 0 o negativos ya no caen al defecto" \
  '    return valor if math.isfinite(valor) and valor > 0 else defecto' \
  '    return valor' \
  'FAILED tests/test_rendimiento1b.py::test_tiempo_de_lectura_en_cero_o_negativo_usa_el_de_siempre[0]'
sabotaje $F "el tiempo de validación en 0 o negativo ya no cae al defecto" \
  '    return valor if math.isfinite(valor) and valor > 0 else 30.0' \
  '    return valor' \
  'FAILED tests/test_rendimiento1b.py::test_tiempo_de_validacion_en_cero_o_negativo_usa_el_de_siempre[-5]'
sabotaje $E "el vendedor vuelve a leer páginas de contenido enorme" \
  '                    continue
                paginas.append(p.extract_text() or '"''"')' \
  '                    pass
                paginas.append(p.extract_text() or '"''"')' \
  'FAILED tests/test_rendimiento1b.py::test_texto_del_vendedor_no_se_traba_con_un_contenido_enorme'
sabotaje $M "un tiempo infinito vuelve a apagar el tiempo máximo" \
  '    return valor if math.isfinite(valor) and valor > 0 else defecto' \
  '    return valor if valor > 0 else defecto' \
  'FAILED tests/test_rendimiento1b.py::test_tiempos_infinitos_o_raros_usan_el_de_siempre[inf]'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
