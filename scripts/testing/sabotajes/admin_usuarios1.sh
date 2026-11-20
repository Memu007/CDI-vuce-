#!/usr/bin/env bash
# Negativos de la lista de usuarios del panel de admin: cada sabotaje deshace
# un punto (sólo admin, nada secreto, mirar no escribe, el saldo que se ve, las
# páginas, el texto de la pantalla) y su prueba tiene que ponerse roja por eso.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/admin_usuarios1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT" || exit 2
[ -d "$REPO/config/node_modules" ] && ln -s "$REPO/config/node_modules" config/node_modules
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0
M=proyecto_maria/main.py
R=proyecto_maria/routers/admin_router.py
B=proyecto_maria/services/billing_service.py
H=proyecto_maria/templates/dev_dashboard.html

servidor() {
  "$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_admin_usuarios1.py tests/test_admin_solo_admin.py 2>&1
}
pantalla() { node scripts/testing/pantalla_panel_dev.js 2>&1; }

aplicar() {
  git checkout -q -- proyecto_maria/
  "$PY" - "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
for viejo, nuevo in zip(sys.argv[2::2], sys.argv[3::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

# sabotaje <archivo> <nombre> <viejo> <nuevo> [<viejo> <nuevo>...] <lo que el rojo tiene que decir>
# La plantilla la mira la pantalla; lo demás, pytest.
sabotaje() {
  local archivo="$1" nombre="$2" esperado="${!#}" corredor=servidor
  [ "$archivo" = "$H" ] && corredor=pantalla
  if ! aplicar "$archivo" "${@:3:$#-3}"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$("$corredor")"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
    grep -E "^(E |FAILED|FALLA)" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

# Sin sabotaje las dos tienen que estar en verde: si no, cualquier «ROJO» de
# abajo sería del rojo que ya había.
for c in servidor pantalla; do
  if ! "$c" >/dev/null; then echo "BASE  | $c ya está en rojo sin sabotaje"; "$c" | tail -5; exit 1; fi
done
echo "BASE  | en verde"

sabotaje $M "el router de admin se monta sin require_admin" \
  "        admin_router.router,
        dependencies=[Depends(require_admin)]
    )" "        admin_router.router,
    )" \
  "FAILED tests/test_admin_usuarios1.py::test_quien_pide_la_lista[no_admin]"
sabotaje $R "la respuesta trae una clave prohibida" \
  '"email": fila.email,' '"email": fila.email, "password": None,' \
  "FAILED tests/test_admin_usuarios1.py::test_la_respuesta_no_trae_nada_secreto"
sabotaje $R "la respuesta trae el id de pago con otro nombre" \
  '"email": fila.email,' '"email": fila.email, "pago": fila.last_payment_id,' \
  'columnas = [User.username,' 'columnas = [User.last_payment_id, User.username,' \
  "FAILED tests/test_admin_usuarios1.py::test_la_respuesta_no_trae_nada_secreto"
sabotaje $R "mirar vence los créditos y guarda" \
  '    return {"total": total,' '    for u in (await db.execute(select(User).where(*filtro))).scalars():
        billing_service._expire_extra_ops(u)
    await db.commit()
    return {"total": total,' \
  "FAILED tests/test_admin_usuarios1.py::test_mirar_no_cambia_la_base"
sabotaje $R "los créditos vencidos se ven vigentes" \
  'vencidos = billing_service.extra_vencidos(saldo["extra_ops_expires_at"])' 'vencidos = False' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "el vencimiento se mira en la cuenta y no en quien paga" \
  'vencidos = billing_service.extra_vencidos(saldo["extra_ops_expires_at"])' 'vencidos = billing_service.extra_vencidos(fila.extra_ops_expires_at)' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "mirar vence los créditos de los estudios y guarda" \
  '    return {"total": total,' '    for o in (await db.execute(select(Organization))).scalars():
        billing_service._expire_extra_ops(o)
    await db.commit()
    return {"total": total,' \
  "FAILED tests/test_admin_usuarios1.py::test_mirar_no_cambia_la_base"
sabotaje $B "la regla de vencido compara al revés" \
  'datetime.now(timezone.utc) > expires' 'datetime.now(timezone.utc) < expires' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "el integrante muestra su saldo y no el del estudio" \
  'getattr(fila, ("org_" if del_estudio else "") + c)' 'getattr(fila, c)' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "el integrante no dice que el saldo es del estudio" \
  '"saldo_del_estudio": del_estudio,' '"saldo_del_estudio": False,' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "nadie figura como admin" \
  '"admin": "admin" in roles_de({"roles": fila.roles}),' '"admin": False,' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "un rol que contiene «admin» cuenta como admin" \
  '"admin": "admin" in roles_de({"roles": fila.roles}),' '"admin": "admin" in str(fila.roles),' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "la búsqueda no filtra" \
  '    if buscar.strip():' '    if False:' \
  "FAILED tests/test_admin_usuarios1.py::test_la_lista_va_por_paginas"
sabotaje $R "la página no tiene tope" \
  '        .limit(cuantos)
' '' \
  "FAILED tests/test_admin_usuarios1.py::test_la_lista_va_por_paginas"
sabotaje $R "se pueden pedir todas de una vez" \
  'cuantos: int = Query(50, ge=1, le=200),' 'cuantos: int = Query(50, ge=1),' \
  "FAILED tests/test_admin_usuarios1.py::test_la_lista_va_por_paginas"
sabotaje $R "se puede pedir una página fuera de rango" \
  'desde: int = Query(0, ge=0, le=1_000_000),' 'desde: int = Query(0, ge=0),' \
  "FAILED tests/test_admin_usuarios1.py::test_la_lista_va_por_paginas"
sabotaje $R "la búsqueda distingue mayúsculas" \
  'User.username.icontains(buscar.strip(), autoescape=True)' 'User.username.contains(buscar.strip(), autoescape=True)' \
  'User.email.icontains(buscar.strip(), autoescape=True)' 'User.email.contains(buscar.strip(), autoescape=True)' \
  "FAILED tests/test_admin_usuarios1.py::test_la_busqueda_por_usuario_o_email"
sabotaje $R "% y _ de la búsqueda son comodines" \
  'User.username.icontains(buscar.strip(), autoescape=True)' 'User.username.icontains(buscar.strip())' \
  'User.email.icontains(buscar.strip(), autoescape=True)' 'User.email.icontains(buscar.strip())' \
  "FAILED tests/test_admin_usuarios1.py::test_la_busqueda_por_usuario_o_email"
sabotaje $R "las fechas sin zona salen sin zona" \
  'return fecha and billing_service.como_utc(fecha).isoformat()' 'return fecha and fecha.isoformat()' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"
sabotaje $R "un estudio que ya no está se toma como estudio" \
  'columnas = [User.username,' 'columnas = [User.organization_id, User.username,' \
  'del_estudio = fila.org_id is not None' 'del_estudio = fila.organization_id is not None' \
  "FAILED tests/test_admin_usuarios1.py::test_cada_cuenta_se_ve_con_su_saldo"

sabotaje $H "sin red la tabla queda como estaba" \
  'if (!response || !response.ok || !data) {' 'if (response && !response.ok) {' \
  "FALLA | sin red dice que no se pudo leer"
sabotaje $H "una respuesta tardía pisa la última búsqueda" \
  '            if (pedido !== ultimoPedidoDeUsuarios) return;
' '' \
  "FALLA | la respuesta tardía de otra búsqueda no pisa la última"
sabotaje $H "la página siguiente sigue el campo y no la búsqueda pedida" \
  'siguientes.onclick = () => fetchUsuarios(hasta, buscar);' 'siguientes.onclick = () => fetchUsuarios(hasta);' \
  "FALLA | la página siguiente pide"
sabotaje $H "los usuarios se escriben como HTML" \
  "if (!data.usuarios.length) tbody.appendChild(fila(['Ninguno']));" "data.usuarios.forEach((u) => { tbody.insertAdjacentHTML('beforeend', '<tr hidden><td>' + u.estudio + '</td></tr>'); });" \
  "FALLA | el texto de los usuarios no crea elementos"
sabotaje $H "la fecha es la de UTC y no la de la Argentina" \
  "new Date(iso).toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })" "iso.slice(0, 10)" \
  "FALLA | usuario 1 como texto"
sabotaje $H "«Anteriores» en la primera página" \
  'anteriores.hidden = data.desde === 0;' 'anteriores.hidden = false;' \
  "FALLA | en la primera página no hay «Anteriores»"
sabotaje $H "«Siguientes» en la última página" \
  'siguientes.hidden = hasta >= data.total;' 'siguientes.hidden = false;' \
  "FALLA | en la última página no hay «Siguientes»"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
