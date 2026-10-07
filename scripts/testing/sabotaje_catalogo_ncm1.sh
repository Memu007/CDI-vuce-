#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_catalogo_ncm1.sh [SHA] [venv]
# Negativos discriminantes de CATALOGO-NCM-1 (el catálogo vigente y
# el aviso de las bajas). Cada sabotaje se aplica en un worktree
# descartable, corre las pruebas de CATALOGO-NCM-1 y tiene que dar ROJO con el motivo
# esperado. Si un patrón no se encuentra, el script
# sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-catalogo-ncm1"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PRUEBA="tests/test_catalogo_ncm1.py tests/test_ncm_sugerir_catalog.py"
T="FAILED tests/test_catalogo_ncm1.py::"
C=proyecto_maria/core/ncm_catalog.py
M=proyecto_maria/main.py
V=proyecto_maria/core/validations.py

correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider $PRUEBA 2>&1 || true
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

# reemplazar_primero <archivo> <viejo> <nuevo>: sólo la primera de dos (las
# dos copias del lector)
reemplazar_primero() {
  "$VENV/bin/python" - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p, encoding="utf-8").read()
n = s.count(viejo)
if n != 2:
    sys.exit(f"PATRON NO ENCONTRADO ({n} veces, se esperaban 2) en {p}: {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo, 1))
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


# 1. el catálogo vuelve a ser el de 2018
git show "$(git log --format=%H -1 -- proyecto_maria/data/ncm_arca.csv.gz)~1:proyecto_maria/data/ncm_arca.csv.gz" > proyecto_maria/data/ncm_arca.csv.gz
caso catalogo_viejo "${T}test_el_catalogo_es_el_vigente"

# 2. la baja avisa sólo «no está»
reemplazar $C "    baja = ncm_de_baja(codigo)
    if baja:" "    baja = ncm_de_baja(codigo)
    if False:"
caso baja_como_desconocida "${T}test_el_aviso_dice_que_paso[85171231-se dio de baja]"

# 3. sin aviso para lo que no está en el vigente
reemplazar $C "    if not catalogo or codigo in catalogo:" "    if True:"
caso sin_aviso "${T}test_el_aviso_dice_que_paso[99999999-"

# 4. una NCM vigente avisa en falso
reemplazar $C "    if not catalogo or codigo in catalogo:" "    if not catalogo:"
caso aviso_en_falso "${T}test_sin_aviso_para_una_vigente_o_incompleta[85171300]"

# 5. la validación no avisa la baja
reemplazar $V "        if aviso_ncm:" "        if False:"
caso validacion_sin_aviso "${T}test_la_validacion_avisa_la_baja_sin_frenar"

# 6. la validación frena por la baja
reemplazar $V '            advertencias.append(f"⚠️ Ítem {i} ({pieza}): {aviso_ncm[0].upper()}{aviso_ncm[1:]}")' '            errores.append(f"⚠️ Ítem {i} ({pieza}): {aviso_ncm[0].upper()}{aviso_ncm[1:]}")'
caso baja_frena "${T}test_la_validacion_avisa_la_baja_sin_frenar"

# 7. la sugerencia del historial no dice que se dio de baja
reemplazar $M "        if ncm_catalog.ncm_de_baja(ncm_key):" "        if False:"
caso sugerencia_sin_aviso "${T}test_la_sugerencia_del_historial_marca_la_baja"

# 8. el código escrito dado de baja no lo dice
reemplazar $M "        if _looks_like_ncm_code_query(descripcion) and ncm_catalog.ncm_de_baja(descripcion):" "        if False:"
caso codigo_escrito_sin_aviso "${T}test_un_codigo_dado_de_baja_escrito_lo_dice"

# 9. vuelve el respaldo con códigos que no existen
reemplazar $C "    selected_path = csv_path
" "    selected_path = csv_path if csv_path.exists() else DATA_DIR / \"ncm_mercosur.csv\"
"
git show "$(git log --format=%H -1 -- proyecto_maria/data/ncm_mercosur.csv)~1:proyecto_maria/data/ncm_mercosur.csv" > proyecto_maria/data/ncm_mercosur.csv
caso respaldo_viejo "${T}test_el_respaldo_con_codigos_viejos_no_se_usa"
rm -f proyecto_maria/data/ncm_mercosur.csv

# 10. el importador no guarda las bajas
reemplazar $C "        return json.loads(path.read_text(encoding=\"utf-8\")).get(\"codigos\") or {}" "        return {}"
caso sin_bajas "${T}test_una_ncm_dada_de_baja_se_reconoce"

if [ "$FALLAS" -ne 0 ]; then echo "SABOTAJES CON FALLA: $FALLAS"; exit 1; fi
echo "OK: los 10 sabotajes dan rojo por la razón esperada"
