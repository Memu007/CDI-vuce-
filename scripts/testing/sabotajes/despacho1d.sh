#!/usr/bin/env bash
# Negativos de DESPACHO-1d: cada sabotaje deshace una línea de la pieza y
# tests/test_despacho1c.py tiene que ponerse roja por ese motivo. Necesita node.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/despacho1d.sh [SHA]
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
T=tests/test_despacho1c.py
PRUEBA=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T")

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
  salida="$("${PRUEBA[@]}" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
    grep -E "^E |^FALLA" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

F=proyecto_maria/static/v2/screens/finalize.js
N=proyecto_maria/static/v2/screens/ncm.js
A=test_lo_que_no_quedo_en_la_memoria_se_avisa
X=test_ninguna_falla_deja_un_exito_a_la_vista
C=test_la_operacion_no_espera_al_catalogo
U=test_cada_cliente_nuevo_se_crea_una_vez

if ! "${PRUEBA[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $F "la operación vuelve a esperar al catálogo" \
  'saveOperationToHistory(items, data, carga, foto).then(r => {' \
  'saveCatalogLearn(items, carga).then(() => saveOperationToHistory(items, data, carga, foto)).then(r => {' \
  "FAILED $T::$C[colgado-guardado]"
sabotaje $F "aprender el catálogo con la red caída no avisa" \
  "            return { ok: false, detail: '' };" \
  "            return { ok: true, detail: '' };" \
  "FAILED $T::$X[aprender-red]"
sabotaje $N "confirmar la posición con la red caída no avisa" \
  '        } catch (_) { /* red caída o plan vencido: el mismo aviso */ }' \
  '        } catch (_) { return false; }' \
  "FAILED $T::$X[confirmar-ncm-red]"
sabotaje $F "el id de proveedor vuelve a llegar a 64" \
  '.slice(0, 60)' '.slice(0, 64)' \
  "FAILED $T::test_el_proveedor_cumple_la_regla_del_servidor"
sabotaje $F "el panel nuevo no olvida el cliente creado para la operación anterior" \
  '        panel.hidden = false;
        clienteCreadoAca = null;' \
  '        panel.hidden = false;' \
  "FAILED $T::$U[crear-y-otra-True-2]"
sabotaje $F "asignar otro entre medio hace que volver a crear cree otro" \
  '            if (clienteCreadoAca) {' \
  '            if (clienteCreadoAca && ((CDI.getClienteActivo && CDI.getClienteActivo()) || {}).id === clienteCreadoAca.id) {' \
  "FAILED $T::$U[crear-asignar-crear-respuesta0-1]"
sabotaje $N "«Memoria activada» aparece aunque el guardado falle" \
  'if (guardado) avisarMemoriaActivada(cliente, op);' \
  'avisarMemoriaActivada(cliente, op);' \
  "FAILED $T::$A[no-guardado-asignar-ncm]"
sabotaje $N "guardar-uso rechazado vuelve a contar como guardado" \
  'guardado = data.success === true && data.historial_guardado !== false;' \
  'guardado = res.ok && data.historial_guardado !== false;' \
  "FAILED $T::$X[asignar-ncm-rechazado]"
sabotaje $F "la operación que no se arma vuelve a quedar callada" \
  "                avisoDeLaOperacion = true;
                CDI.toast && CDI.toast('No se guardó al cliente'," \
  "                avisoDeLaOperacion = true;
                false && CDI.toast('No se guardó al cliente'," \
  "FAILED $T::test_si_la_operacion_no_se_arma_se_avisa"

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
