#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_maria1c.sh [SHA] [venv]
# Negativos discriminantes de MARIA-1c (lo que no se pudo leer se avisa).
# La parte de pantalla se verifica con scripts/testing/pantalla_maria1c.js. Cada sabotaje se aplica en un worktree descartable, corre
# tests/test_maria1c_avisos_lectura.py y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-maria1c"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA=tests/test_maria1c_avisos_lectura.py

correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider "$PRUEBA" 2>&1 || true
}

# reemplazar <archivo> <viejo> <nuevo>: falla si <viejo> no aparece una sola vez
reemplazar() {
  "$VENV/bin/python" - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p, encoding="utf-8").read()
n = s.count(viejo)
if n != 1:
    sys.exit(f"PATRON NO ENCONTRADO ({n} veces) en {p}: {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PY
}

FALLAS=0
caso() {  # caso <nombre> <texto que el rojo tiene que mostrar>
  local nombre="$1" espera="$2" salida
  salida="$(correr)"
  git checkout -q -- .
  if grep -q "passed" <<<"$salida" && ! grep -q "failed" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  if grep -qF -- "$espera" <<<"$salida"; then
    echo "ROJO   $nombre: $(grep -E '[0-9]+ failed' <<<"$salida" | tail -1)"
  else
    echo "FALLA  $nombre: rojo, pero sin «$espera»"; FALLAS=$((FALLAS+1))
    tail -15 <<<"$salida"
  fi
}

# 0. sin sabotaje: verde
base="$(correr)"
if grep -q "failed" <<<"$base" || ! grep -qE "[0-9]+ passed" <<<"$base"; then
  echo "FALLA: la prueba no está verde sin sabotaje"; tail -20 <<<"$base"; exit 1
fi
echo "VERDE  sin sabotaje: $(grep -E 'passed' <<<"$base" | tail -1)"
F=proyecto_maria/pdf_extractor.py
T=tests/test_maria1c_avisos_lectura.py

# 1. el flete ilegible no se marca
reemplazar $F "    for campo in ('flete', 'seguro'):" "    for campo in ('seguro',):"
caso "flete_sin_marca" "FAILED $T::test_flete_y_seguro_ilegibles_se_marcan[pdf_directo]"

# 2. se marca también lo que no estaba en la factura
reemplazar $F "        if (raw not in (None, '') and not _no_aplica(raw, _FLETE_NO_APLICA)" "        if (not _no_aplica(raw, _FLETE_NO_APLICA)"
caso "marca_lo_ausente" "FAILED $T::test_lo_que_no_estaba_o_se_leyo_no_se_marca[ausentes-pdf_directo]"

# 3. la copia de producción no manda la marca
reemplazar $F "                        operacion_data['campos_sin_leer'] = _campos_sin_leer(operacion, decimal)" "                        operacion_data['campos_sin_leer'] = []"
caso "directo_sin_marca" "FAILED $T::test_flete_y_seguro_ilegibles_se_marcan[pdf_directo]"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 3 sabotajes dan rojo por la razón esperada"
