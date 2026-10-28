#!/usr/bin/env bash
# Negativos de SEGURO-1: cada sabotaje deshace una regla del seguro con los
# incoterms que ya lo llevan en el precio (los cinco, la regla en el
# servidor, el calculado que se borra) y tests/test_seguro1.py tiene que
# fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/seguro1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0

pytest_s1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_seguro1.py 2>&1
}

aplicar() {
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_s1)"; codigo=$?
  git checkout -q -- proyecto_maria/
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^FAILED" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# Sin sabotaje, verde: si no, ningún rojo de abajo distingue nada.
salida="$(pytest_s1)" || { echo "BASE  | tests/test_seguro1.py no pasa sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
echo "BASE  | $(tail -1 <<<"$salida")"

G=proyecto_maria/core/maria_generator.py
M=proyecto_maria/main.py
F=proyecto_maria/static/v2/screens/finalize.js

# 1. Los cinco, y escritos de cualquier manera.
sabotaje $G "DPU fuera de la lista" \
  'INCOTERMS_CON_SEGURO = ("CIF", "CIP", "DPU", "DAP", "DDP")' 'INCOTERMS_CON_SEGURO = ("CIF", "CIP", "DAP", "DDP")' \
  "test_con_los_cinco_no_hay_sugerencia[DPU]" \
  "test_los_avisos_traen_la_regla_del_servidor[DPU]"
sabotaje $G "el incoterm sin normalizar" \
  'return str(incoterm or "").strip().upper() in INCOTERMS_CON_SEGURO' 'return str(incoterm or "") in INCOTERMS_CON_SEGURO' \
  "test_mayusculas_minusculas_y_espacios_dan_lo_mismo" \
  "test_los_avisos_traen_la_regla_del_servidor[cif_con_espacios]"

# 2. La regla vive en el servidor, no sólo en la pantalla.
sabotaje $M "el servidor no le pasa el incoterm a las cuentas" \
  'ajustes_deducir=request.ajustes_deducir,
            incoterm=request.incoterm,
' 'ajustes_deducir=request.ajustes_deducir,
' \
  "test_los_avisos_traen_la_regla_del_servidor[CIF]"
sabotaje $F "la pantalla decide por su cuenta con el incoterm" \
  'const enElPrecio = !!(valor && valor.seguro_en_el_precio);' \
  "const enElPrecio = ['CIF', 'CIP', 'DPU', 'DAP', 'DDP'].includes(String(op.incoterm || '').trim().toUpperCase());" \
  "test_la_pantalla_sigue_al_servidor_y_no_al_incoterm"
sabotaje $F "el botón calcula igual con CIF" \
  'if (!ultimoValor || ultimoValor.error || ultimoValor.seguro_en_el_precio) return;' \
  'if (!ultimoValor || ultimoValor.error) return;' \
  "test_con_cif_el_boton_no_pone_nada"

# 3. El calculado no sobrevive al cambio de incoterm; el escrito, sí.
sabotaje $F "el calculado sobrevive en la pantalla" \
  'if (borrarSeguroCalculado(valor, firma)) return;' '' \
  "test_el_calculado_se_borra_al_pasar_a_cif_y_queda_para_completar[con_cuentas]" \
  "test_el_calculado_que_se_borra_sin_lista_de_sin_leer_la_arma"
sabotaje $M "el calculado sobrevive en el servidor" \
  '    if seguro_en_el_precio(request.incoterm):
' '    if False:
' \
  "test_un_seguro_calculado_con_cif_no_genera" \
  "test_el_cambio_de_incoterm_con_el_seguro_calculado[cfr_a_cif]"
sabotaje $F "se borra también el escrito" \
  '!valor.seguro_en_el_precio || !op.seguro_calculado) return false;' '!valor.seguro_en_el_precio) return false;' \
  "test_el_seguro_escrito_no_se_toca_al_pasar_a_cif"
sabotaje $F "se borra con cuentas de otro pedido" \
  'if (!firma || firma !== ahora) return false;' '' \
  "test_con_cuentas_de_otro_pedido_no_se_borra"
sabotaje $F "el borrado deja el seguro como completado" \
  "op.campos_completados = op.campos_completados.filter(c => c !== 'seguro');" '' \
  "test_el_calculado_se_borra_al_pasar_a_cif_y_queda_para_completar[con_cuentas]"

# 4. Sin respuesta de los avisos no se ofrece dejar el calculado (revisión).
sabotaje $F "sin respuesta de los avisos se ofrece dejarlo" \
  'valor.error !== SIN_CUENTAS &&' '' \
  "test_sin_respuesta_de_los_avisos_no_se_ofrece_dejarlo[CIF]"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
