#!/usr/bin/env bash
# Negativos de AISLAMIENTO-2: cada sabotaje abre una fuga o un punto ciego y
# la prueba tiene que verlo por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/aislamiento2.sh [prueba|ataque|todo] [SHA]
#   prueba  pytest de admin y roles: WebSocket y ruta exacta sin control,
#           también dentro de un router incluido;
#           roles guardados como texto (un minuto)
#   ataque  ataque_aislamiento.sh completo una vez por filtro saboteado:
#           tiene que dar FUGA en el caso de ese filtro (unos 3 minutos cada
#           uno, uno tras otro porque el ataque usa el puerto 5434 de Postgres)
#   todo    las dos (por omisión)
# El ataque escucha en PUERTO (8131 por omisión).
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón, no pone rojo o un
# control se pone rojo.
set -uo pipefail
QUE="${1:-todo}"
case "$QUE" in prueba|ataque|todo) ;; *) echo "uso: $0 [prueba|ataque|todo] [SHA]"; exit 2;; esac
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${2:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0
M=proyecto_maria/main.py

# saboteo <archivo> <texto original> <texto saboteado>: el original tiene que estar una sola vez
saboteo() {
  git checkout -q -- proyecto_maria/
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
}

# ------------------------------------------------------------------ prueba
PRUEBAS="tests/test_admin_solo_admin.py tests/test_admin2.py tests/test_roles_texto.py"

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  if ! saboteo "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo e
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider $PRUEBAS 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for e in "$@"; do
    if ! grep -qF -- "$e" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$e»"; grep -E "^(E |FAILED|ERROR)" <<<"$salida" | head -6
      FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: dice «$1»"
}

# control <nombre> <texto original> <texto cambiado>: un cambio que está bien no pone rojo
control() {
  local nombre="$1"
  if ! saboteo "$M" "$2" "$3"; then
    echo "ROTO  | control: $nombre: no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida
  if salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider $PRUEBAS 2>&1)"; then
    echo "VERDE | control: $nombre: sigue verde, como debe"
  else
    echo "ROJO  | control: $nombre: se puso rojo y no debía"; grep -E "^(E |FAILED|ERROR)" <<<"$salida" | head -6
    FALLAS=$((FALLAS+1))
  fi
}

# Lo que se agrega va antes de esta ruta, con el import del WebSocket.
ANCLA='@app.get("/api/billing/plans")'
agregar() { printf 'from fastapi import WebSocket\n%s\n\n\n%s' "$1" "$ANCLA"; }
WS_USUARIO='FAILED tests/test_admin_solo_admin.py::test_websocket_de_admin_no_acepta_a_un_usuario_comun'
WS_SIN='FAILED tests/test_admin_solo_admin.py::test_websocket_de_admin_no_acepta_sin_sesion'
R_USUARIO='FAILED tests/test_admin_solo_admin.py::test_usuario_comun_recibe_403_en_toda_ruta_de_admin'
R_SIN='FAILED tests/test_admin_solo_admin.py::test_sin_sesion_recibe_401_en_toda_ruta_de_admin'

prueba() {
  echo "== prueba: admin y roles"
  sabotaje $M "un WebSocket bajo /api/admin/ acepta sin control" "$ANCLA" "$(agregar '@app.websocket("/api/admin/ws")
async def _ws_admin_abierto(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("hola")
    await websocket.close()')" "$WS_USUARIO" "$WS_SIN" "WebSockets de admin que aceptan"
  sabotaje $M "un WebSocket bajo /api/admin/ acepta y enseguida falla" "$ANCLA" "$(agregar '@app.websocket("/api/admin/ws")
async def _ws_admin_abierto(websocket: WebSocket):
    await websocket.accept()
    raise RuntimeError("falla después de aceptar")')" "$WS_USUARIO" "$WS_SIN"
  sabotaje $M "una ruta cruda en /api/admin, sin barra final" "$ANCLA" "$(agregar 'from starlette.responses import JSONResponse as _JR
async def _admin_crudo(request):
    return _JR({"secreto": 1})
app.router.add_route("/api/admin", _admin_crudo)')" "$R_USUARIO" "$R_SIN"
  sabotaje $M "una ruta cruda en /dev, sin barra final" "$ANCLA" "$(agregar 'from starlette.responses import JSONResponse as _JR
async def _dev_crudo(request):
    return _JR({"secreto": 1})
app.router.add_route("/dev", _dev_crudo)')" "$R_USUARIO" "$R_SIN"
  sabotaje $M "una ruta de FastAPI en /api/dev, sin barra final" "$ANCLA" "$(agregar '@app.get("/api/dev")
async def _api_dev_exacto():
    return {"secreto": 1}')" "$R_USUARIO" "$R_SIN"
  # Un router incluido sin require_admin: app.routes no muestra sus rutas.
  sabotaje $M "un WebSocket abierto dentro de un router incluido en /api/dev" "$ANCLA" "$(agregar 'from fastapi import APIRouter as _AR
_r_dev = _AR(prefix="/api/dev")
@_r_dev.websocket("/ws")
async def _ws_dev_abierto(websocket: WebSocket):
    await websocket.accept()
    await websocket.close()
app.include_router(_r_dev)')" "$WS_USUARIO" "$WS_SIN" "/api/dev/ws"
  sabotaje $M "una ruta oculta del esquema dentro de un router incluido en /api/dev" "$ANCLA" "$(agregar 'from fastapi import APIRouter as _AR
_r_dev = _AR(prefix="/api/dev")
@_r_dev.get("/oculta", include_in_schema=False)
async def _dev_oculta():
    return {"secreto": 1}
app.include_router(_r_dev)')" "$R_USUARIO" "$R_SIN" "GET /api/dev/oculta"
  sabotaje $M "_es_admin vuelve a buscar «admin» dentro del texto de roles" \
    '"admin" in roles_de(user)' \
    '"admin" in (user.get("roles") or [])' \
    'FAILED tests/test_roles_texto.py::test_roles_que_no_son_la_lista_admin_no_entran[administrador]' \
    "roles='administrador': 200"
  sabotaje proyecto_maria/auth/roles.py "require_role vuelve a buscar el rol dentro del texto" \
    '        roles = roles_de(user)' \
    '        roles = user.get("roles", [])' \
    'FAILED tests/test_roles_texto.py::test_require_role_no_cuenta_admin_por_una_parte[administrador]'
  sabotaje proyecto_maria/auth/roles.py "un texto deja de valer como un rol entero" \
    '    if isinstance(roles, str):
        return [roles]' \
    '    if isinstance(roles, str):
        return []' \
    'FAILED tests/test_roles_texto.py::test_el_rol_admin_entero_entra[admin]' \
    'FAILED tests/test_roles_texto.py::test_require_role_con_el_rol_en_texto_entra'
  control "un WebSocket bajo /api/admin/ que cierra sin aceptar" "$ANCLA" "$(agregar '@app.websocket("/api/admin/ws")
async def _ws_admin_cerrado(websocket: WebSocket):
    await websocket.close(code=1008)')"
  control "un WebSocket bajo /api/admin/ con Depends(require_admin)" "$ANCLA" "$(agregar '@app.websocket("/api/admin/ws")
async def _ws_admin_con_control(websocket: WebSocket, user=Depends(require_admin)):
    await websocket.accept()
    await websocket.close()')"
}

# ------------------------------------------------------------------ ataque
PUERTO="${PUERTO:-8131}"
# El ataque usa ./venv/bin/python si existe: el del PY que se pasó.
case "$PY" in */bin/python*) ln -sfn "$(cd "$(dirname "$PY")/.." && pwd)" venv ;; esac

# ataque <archivo> <nombre> <texto original> <texto saboteado> <caso que tiene que dar FUGA>...
ataque() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4"; shift 4
  if ! saboteo "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo e
  salida="$(PUERTO="$PUERTO" timeout 900 ./scripts/testing/ataque_aislamiento.sh 2>&1 | sed 's/\x1b\[[0-9;]*m//g')"
  codigo=${PIPESTATUS[0]}
  if grep -qF "PUERTA G3 PASADA" <<<"$salida"; then
    echo "VERDE | $nombre: el ataque no vio la fuga"; FALLAS=$((FALLAS+1)); return
  fi
  for e in "$@"; do
    if ! grep -qF -- "FUGA  | $e" <<<"$salida"; then
      echo "ROJO? | $nombre: no pasó (salida $codigo), pero sin «FUGA  | $e»"
      grep -E "^(FUGA|DUDA)|❌" <<<"$salida" | head -6; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: «FUGA  | $1»"
}

ataques() {
  echo "== ataque: un filtro saboteado por corrida"
  ataque $M "operaciones: el listado no filtra por dueño" \
    '.where(OperationModel.owner_username == username)
        )
        if estado and estado in COCKPIT_ESTADOS:' \
    '
        )
        if estado and estado in COCKPIT_ESTADOS:' \
    "El listado de operaciones de Beto no tiene las de Ana"
  ataque $M "operaciones: cambiar el estado no mira el dueño" \
    'OperationModel.id == operation_id,
            OperationModel.owner_username == username,' \
    'OperationModel.id == operation_id,' \
    "Cambiar el estado de la operación de Ana" "Beto cambió el estado de la operación de Ana"
  ataque $M "operaciones: agrupar no mira el dueño" \
    'OperationModel.owner_username == username,
            OperationItemModel.id.in_(item_ids),' \
    'OperationItemModel.id.in_(item_ids),' \
    "Agrupar los ítems de Ana"
  ataque $M "operaciones: desagrupar no mira el dueño" \
    'OperationModel.owner_username == username,
            OperationItemModel.grupo_id == grupo_id,' \
    'OperationItemModel.grupo_id == grupo_id,' \
    "Desagrupar los ítems de Ana" "Beto tocó el grupo de Ana"
  ataque proyecto_maria/routers/quote_router.py "presupuesto: compartir no mira el dueño" \
    '            Operation.owner_username == user["username"]' \
    '            True' \
    "Compartir el presupuesto de la operación de Ana"
  local TODAS='list((await db.execute(sa_select(NCMNoteModel).where(NCMNoteModel.ncm_code == ncm_key).order_by(NCMNoteModel.created_at.asc()))).scalars().all())'
  ataque $M "notas: ver no filtra por dueño" \
    'return {"notas": []}
    notas = await _fetch_notas_ordered(db, user["username"], ncm_key)' \
    "return {\"notas\": []}
    notas = $TODAS" \
    "Beto no ve la nota de Ana"
  ataque $M "notas: cambiar no filtra por dueño" \
    'nota_text = str(data.get("nota", "")).strip()

    notas = await _fetch_notas_ordered(db, user["username"], ncm_key)' \
    "nota_text = str(data.get(\"nota\", \"\")).strip()

    notas = $TODAS" \
    "Cambiar la nota de Ana" "La nota de Ana quedó intacta"
  ataque $M "notas: borrar no filtra por dueño" \
    '"""Elimina una nota (por índice posicional)."""
    ncm_key = _ncm_prefix(ncm)
    notas = await _fetch_notas_ordered(db, user["username"], ncm_key)' \
    "\"\"\"Elimina una nota (por índice posicional).\"\"\"
    ncm_key = _ncm_prefix(ncm)
    notas = $TODAS" \
    "Borrar la nota de Ana" "La nota de Ana quedó intacta"
  ataque $M "estudios: el listado no filtra por dueño" \
    'select(Estudio).where(Estudio.owner_username == user["username"]).order_by(Estudio.nombre, Estudio.id)' \
    'select(Estudio).order_by(Estudio.nombre, Estudio.id)' \
    "Beto no ve el estudio de Ana"
  ataque $M "estudios: borrar no mira el dueño" \
    'select(Estudio).where(Estudio.id == estudio_id, Estudio.owner_username == user["username"])' \
    'select(Estudio).where(Estudio.id == estudio_id)' \
    "Borrar el estudio de Ana" "El estudio de Ana quedó intacto"
  # Un 204 también es fuga: el ataque no puede contar sólo el 200.
  ataque $M "estudios: borrar no mira el dueño y contesta 204" \
    'select(Estudio).where(Estudio.id == estudio_id, Estudio.owner_username == user["username"])
    )
    estudio = result.scalars().first()
    if estudio is None:
        raise HTTPException(status_code=404, detail="Estudio no encontrado")
    await db.delete(estudio)
    await db.commit()
    return {"success": True}' \
    'select(Estudio).where(Estudio.id == estudio_id)
    )
    estudio = result.scalars().first()
    if estudio is None:
        raise HTTPException(status_code=404, detail="Estudio no encontrado")
    await db.delete(estudio)
    await db.commit()
    return Response(status_code=204)' \
    "Borrar el estudio de Ana"
  ataque $M "estudios: generar acepta el estudio de otro" \
    'select(Estudio).where(Estudio.id == estudio_id, Estudio.owner_username == username)' \
    'select(Estudio).where(Estudio.id == estudio_id)' \
    "Generar un TXT con el estudio de Ana"
  ataque $M "organizaciones: /mine lista a todos los usuarios" \
    'select(User).where(User.organization_id == org.id).order_by(User.username)' \
    'select(User).order_by(User.username)' \
    "El estudio B no ve al estudio A ni a sus miembros"
  ataque $M "organizaciones: sacar un miembro no mira el estudio" \
    'select(User).where(User.username == username, User.organization_id == org.id)' \
    'select(User).where(User.username == username)' \
    "El estudio B saca a un miembro del estudio A" "El miembro que quiso sacar el estudio B sigue en el estudio A"
  ataque $M "organizaciones: un miembro saca a otro sin ser el administrador" \
    '    if user["username"] != org.owner_username:
        raise HTTPException(status_code=403, detail="Solo el administrador puede remover miembros")' \
    '    if False:
        raise HTTPException(status_code=403, detail="Solo el administrador puede remover miembros")' \
    "Un miembro (no administrador) saca a otro miembro de su estudio" "El miembro que quiso sacar otro miembro sigue en el estudio A"
  ataque $M "admin: cualquier usuario es administrador" \
    '    return user["username"] in _admin_usernames() or "admin" in roles_de(user)' \
    '    return True' \
    "Beto en GET /api/admin/stats/summary" "Beto en GET /api/dev/stats" "Beto en GET /dev/dashboard"
}

[ "$QUE" != ataque ] && prueba
[ "$QUE" != prueba ] && ataques
git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
exit $FALLAS
