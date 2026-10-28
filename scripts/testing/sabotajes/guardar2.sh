#!/usr/bin/env bash
# Negativos de GUARDAR-2: cada sabotaje deshace una línea de la pieza y
# tests/test_guardar2.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/guardar2.sh [SHA]
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_guardar2.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}


M=proyecto_maria/main.py
T=tests/test_guardar2.py

if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $T >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $M "el autorrelleno vuelve a traer los 8 dígitos del cliente" \
  '                        "ncm": _ncm_recordado_con_sim_del_proveedor(mem, vm),' \
  '                        "ncm": mem["ncm"],' \
  "FAILED $T::test_el_autorrelleno_trae_la_sim_del_proveedor"
sabotaje $M "la sugerencia vuelve a traer los 8 dígitos del cliente" \
  '                    sugerencias[0]["ncm"] = _ncm_recordado_con_sim_del_proveedor(recordado, vendor_item)' \
  '                    pass' \
  "FAILED $T::test_la_sugerencia_trae_la_sim_del_proveedor"
sabotaje $M "gana el proveedor aunque sea otra NCM" \
  '            and _ncm_suggestion_key(proveedor) == _ncm_suggestion_key(cliente)):' \
  '            ):' \
  "FAILED $T::test_con_otra_ncm_en_el_proveedor_gana_el_cliente"
sabotaje $M "gana el proveedor aunque no tenga la letra de control" \
  '    if (proveedor and _sim_position_error(proveedor) is None' \
  '    if (proveedor and len(re.sub(r"\D", "", proveedor)) >= 8' \
  "FAILED $T::test_cual_gana[84714900-84714900100-84714900]"
sabotaje $M "gana el proveedor aunque el cliente no tenga 8 dígitos" \
  '    if not re.fullmatch(r"[\d.]+", cliente) or len(re.sub(r"\D", "", cliente)) != 8:' \
  '    if not cliente:' \
  "FAILED $T::test_cual_gana[8471490010-84714900100D-8471490010]"

sabotaje $M "gana la SIM de otro producto parecido del proveedor" \
  '            or del_proveedor["producto_key"] != catalog_svc._normalize(recordado.get("descripcion") or "")):' \
  '            ):' \
  "FAILED $T::test_la_sim_de_otro_producto_parecido_no_gana"
sabotaje $M "la SIM del proveedor sale tal como está guardada" \
  '        return re.sub(r"[.\s]", "", proveedor).upper()' \
  '        return proveedor' \
  "FAILED $T::test_la_sim_del_proveedor_sale_en_la_forma_de_siempre"

# Por dueño: sin el filtro del despachante, lo de otro se cuela.
C=proyecto_maria/core/catalog_service.py
CM=proyecto_maria/services/client_memory.py
sabotaje $C "el catálogo del proveedor de otro despachante cambia la SIM" \
  $'    stmt = select(VendorCatalogProduct).where(\n        VendorCatalogProduct.owner_username == owner_username,\n        VendorCatalogProduct.vendor_id == vendor_id,\n    )\n    result = await db.execute(stmt)\n    return list(' \
  $'    stmt = select(VendorCatalogProduct).where(\n        VendorCatalogProduct.vendor_id == vendor_id,\n    )\n    result = await db.execute(stmt)\n    return list(' \
  "FAILED $T::test_el_catalogo_de_otro_usuario_no_cambia_la_sim"
sabotaje $CM "el historial de un cliente ajeno se usa" \
  $'    q = sa_select(ClientProductHistory).where(\n        ClientProductHistory.owner_username == owner_username,\n        ClientProductHistory.client_id == client_id,\n    )\n    result = await db.execute(q)\n    candidates' \
  $'    q = sa_select(ClientProductHistory).where(\n        ClientProductHistory.client_id == client_id,\n    )\n    result = await db.execute(q)\n    candidates' \
  "FAILED $T::test_el_historial_de_un_cliente_ajeno_no_se_usa"
# Por cliente: dos clientes del mismo despachante no comparten historial.
sabotaje $CM "el historial de otro cliente del mismo despachante se usa" \
  $'        ClientProductHistory.client_id == client_id,\n    )\n    result = await db.execute(q)\n    candidates' \
  $'    )\n    result = await db.execute(q)\n    candidates' \
  "FAILED $T::test_el_historial_de_otro_cliente_del_mismo_despachante_no_se_usa"
# Al guardar (adversario Sonnet alto): el NCM y la descripción buscan sólo en
# el historial del mismo cliente.
sabotaje $CM "guardar el mismo NCM actualiza la fila de otro cliente" \
  $'        ClientProductHistory.client_id == client_id,\n        ClientProductHistory.ncm == ncm,' \
  $'        ClientProductHistory.ncm == ncm,' \
  "FAILED $T::test_guardar_el_mismo_ncm_en_otro_cliente_le_crea_su_propio_historial"
sabotaje $CM "guardar la misma descripción pisa la fila de otro cliente" \
  $'        q_all = sa_select(ClientProductHistory).where(\n            ClientProductHistory.owner_username == owner_username,\n            ClientProductHistory.client_id == client_id,' \
  $'        q_all = sa_select(ClientProductHistory).where(\n            ClientProductHistory.owner_username == owner_username,' \
  "FAILED $T::test_guardar_otro_ncm_con_la_misma_descripcion_en_otro_cliente_no_pisa_al_primero"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
