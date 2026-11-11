#!/usr/bin/env bash
# Negativos de DATOS-1 y PRESUPUESTO-CLIENTE-1: cada sabotaje deshace una
# regla (/health honesto, los 500 sin detalle técnico, borrar un cliente con
# presupuesto compartido, pasar una operación compartida a otro cliente) y
# tests/test_datos1.py tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/datos1.sh [SHA]
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

pytest_d1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_datos1.py 2>&1
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

# juzgar <nombre> <salida> <código> <lo que el rojo tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3"; shift 3
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^(FAILED|E )" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_d1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
T=tests/test_datos1.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_d1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi

# --- D2: /health
sabotaje $M "/health sin base sigue en 200" \
  '        return JSONResponse(status_code=503, content=checks)' '        return checks' \
  "FAILED $T::test_health_sin_base_503_sin_el_texto_del_error" "assert 200 == 503"
sabotaje $M "/health vuelve a mostrar el error de la base" \
  $'    except Exception:\n        # Sin base la API' $'    except Exception as e:\n        checks["db_error"] = str(e)\n        # Sin base la API' \
  "FAILED $T::test_health_sin_base_503_sin_el_texto_del_error" "assert 'db_error' not in"
sabotaje $M "/health no deja el error en el log" \
  $'        logging.exception("/health: la base no responde")\n' '' \
  "FAILED $T::test_health_sin_base_503_sin_el_texto_del_error" "el error de la base tiene que quedar en el log"

# --- D6: los 500 sin detalle técnico, que va al log; los 4xx igual que antes
sabotaje $M "el 500 de HTTPException vuelve a mandar dev_detail" \
  $'            content={"detail": _FRIENDLY_5XX, "code": "internal_error"},\n        )\n    # 4xx' \
  $'            content={"detail": _FRIENDLY_5XX, "code": "internal_error", "dev_detail": str(exc.detail)},\n        )\n    # 4xx' \
  "FAILED $T::test_http_exception_500_sin_dev_detail" "assert 'dev_detail' not in"
sabotaje $M "el 500 no manejado vuelve a mandar dev_detail" \
  $'        content={"detail": _FRIENDLY_5XX, "code": "internal_error"},\n    )\n\n# Agregar middleware' \
  $'        content={"detail": _FRIENDLY_5XX, "code": "internal_error", "dev_detail": f"{type(exc).__name__}: {exc}"},\n    )\n\n# Agregar middleware' \
  "FAILED $T::test_excepcion_no_manejada_sin_dev_detail" "assert 'dev_detail' not in"
sabotaje $M "el 500 de HTTPException no deja el detalle en el log" \
  $'        logging.error(\n            "HTTPException 500 en %s %s: %s",\n            request.method, request.url.path, exc.detail,\n            exc_info=exc,\n        )\n' '' \
  "FAILED $T::test_http_exception_500_sin_dev_detail" "assert 'connection to server"
sabotaje $M "el 500 no manejado no deja el detalle en el log" \
  $'    logging.error(\n        "Excepcion no manejada en %s %s: %s: %s",\n        request.method, request.url.path, type(exc).__name__, exc,\n        exc_info=exc,\n    )\n' '' \
  "FAILED $T::test_excepcion_no_manejada_sin_dev_detail" "assert 'connection to server"
sabotaje $M "los 4xx pierden su motivo" \
  '        content={"detail": detail},' '        content={"detail": _FRIENDLY_5XX},' \
  "FAILED $T::test_4xx_sigue_con_su_detail" "FAILED $T::test_4xx_de_la_app_sigue_igual"

# --- D5 / D32 (a): borrar un cliente con presupuesto compartido
sabotaje $M "no se borran los presupuestos del cliente" \
  $'            await db.execute(\n                sa_delete(PublicQuoteModel).where(\n                    PublicQuoteModel.operation_id.in_([o.id for o in operaciones])\n                )\n            )\n' '' \
  "FAILED $T::test_borrar_cliente_borra_sus_presupuestos_y_no_los_ajenos" "assert 200 == 404"
sabotaje $M "se borran también los presupuestos ajenos" \
  '                    PublicQuoteModel.operation_id.in_([o.id for o in operaciones])' '                    PublicQuoteModel.operation_id.isnot(None)' \
  "FAILED $T::test_borrar_cliente_borra_sus_presupuestos_y_no_los_ajenos" "assert 404 == 200"
sabotaje $M "el borrado no es una sola transacción" \
  $'        await db.delete(client)\n        await db.commit()\n        return {\n            "success": True,\n            "message": "Cliente eliminado",' \
  $'        await db.commit()\n        await db.delete(client)\n        await db.commit()\n        return {\n            "success": True,\n            "message": "Cliente eliminado",' \
  "FAILED $T::test_si_falla_a_mitad_no_se_borra_nada" "assert 404 == 200"
sabotaje $M "otro dueño puede borrar el cliente" \
  $'        client = await _cliente_con_cuenta_bloqueada(db, client_id, username)\n        op_rows' \
  $'        client = await db.get(ClientModel, client_id)\n        username = client.owner_username\n        op_rows' \
  "FAILED $T::test_otro_dueno_no_borra_el_cliente_ni_su_presupuesto" "assert 200 == 404"

# --- D141 (a): pasar una operación compartida a otro cliente
P="FAILED $T::test_pasar_la_operacion_a_otro_cliente_borra_su_presupuesto"
BORRA=$'    if operation.client_id not in (None, client_id):\n'
sabotaje $M "pasada a otro cliente, el link sigue andando, también al borrar el anterior" \
  "$BORRA" $'    if False:\n' \
  "$P" "FAILED $T::test_borrar_el_cliente_anterior_no_deja_el_link_de_la_operacion_pasada" \
  "AssertionError: (True, 200)" "assert 200 == 404"
sabotaje $M "pasada a otro cliente, sólo se borra uno de sus links" \
  $'        await db.execute(\n            sa_delete(PublicQuoteModel).where(PublicQuoteModel.operation_id == operation.id)\n        )\n' \
  $'        q = (await db.execute(sa_select(PublicQuoteModel).where(PublicQuoteModel.operation_id == operation.id))).scalars().first()\n        await db.delete(q)\n' \
  "$P" "AssertionError: (True, 200)" "assert 200 == 404"
sabotaje $M "borrar el cliente anterior suelta también la operación que ya pasó" \
  $'        op_rows = await db.execute(\n            sa_select(OperationModel).where(\n                OperationModel.client_id == client_id,\n                OperationModel.owner_username == username,\n' \
  $'        op_rows = await db.execute(\n            sa_select(OperationModel).where(\n                OperationModel.owner_username == username,\n' \
  "FAILED $T::test_borrar_el_cliente_anterior_no_deja_el_link_de_la_operacion_pasada" "assert None =="
sabotaje $M "se borra aunque siga en el mismo cliente" \
  "$BORRA" $'    if True:\n' \
  "$P" "AssertionError: (False, 200)" "assert 404 == 200"
sabotaje $M "se borra al recibir cliente por primera vez" \
  "$BORRA" $'    if operation.client_id != client_id:\n' \
  "$P" "AssertionError: sin cliente antes" "assert 404 == 200"
sabotaje $M "el borrado queda aunque el guardado falle" \
  $'PublicQuoteModel.operation_id == operation.id)\n        )\n' \
  $'PublicQuoteModel.operation_id == operation.id)\n        )\n        await db.commit()\n' \
  "$P" "AssertionError: (True, 400)" "assert 404 == 200"
sabotaje $M "se borran también los links de otras operaciones" \
  'sa_delete(PublicQuoteModel).where(PublicQuoteModel.operation_id == operation.id)' \
  'sa_delete(PublicQuoteModel).where(PublicQuoteModel.operation_id.isnot(None))' \
  "$P" "AssertionError: otra operación del mismo cliente" "assert 404 == 200"
sabotaje $M "el guardado encuentra la operación de otro dueño" \
  $'        OperationModel.id == operacion_id,\n        OperationModel.owner_username == username,\n' \
  $'        OperationModel.id == operacion_id,\n' \
  "$P" "AssertionError: assert '" "' != '"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
