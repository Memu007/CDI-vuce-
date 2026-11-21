#!/usr/bin/env bash
# Negativos de la carga de créditos extra desde el panel de admin: cada sabotaje
# deshace una línea de la regla de acreditar, de la ruta o del diálogo. Tienen
# que fallar con su frase tests/test_admin_creditos1.py o la pantalla.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/admin_creditos1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y una API local por
# corrida de pantalla: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_admin_creditos1.py
PANTALLA=scripts/testing/pantalla_admin_creditos1.js
source "$(dirname "$0")/_casos_y_pantalla.sh"

R=proyecto_maria/routers/admin_router.py
B=proyecto_maria/services/billing_service.py
M=proyecto_maria/main.py
H=proyecto_maria/templates/dev_dashboard.html
ACREDITAN=("test_acreditar_extra[0-None-10-True-0-10]" "test_acreditar_extra[None-None-1-True-0-1]"
           "test_acreditar_extra[90-vence2-10-True-90-100]" "test_acreditar_extra[5-vence4-10-True-0-10]"
           "test_acreditar_extra[95-vence5-100-True-0-100]")
RUTA=("test_carga[solo]" "test_carga[estudio]" "test_carga[vencidos]" "test_carga[llena_el_tope]"
      "test_carga[vencidos_y_cien]")

# 1. La regla: lo que entra vence a 30 días y cuenta como recarga.
sabotaje casos $B "lo cargado no vence a 30 días" '        cuenta.extra_ops_expires_at = ahora + timedelta(days=30)
' '' "AssertionError" "${ACREDITAN[@]}" "${RUTA[@]}"
sabotaje casos $B "la carga no cuenta como recarga" '        cuenta.last_topup_at = ahora
' '' "AssertionError" "${ACREDITAN[@]}" "${RUTA[@]}"

# 2. Un pedido carga una sola vez, también si la primera llenó el tope.
sabotaje casos $R "el pedido no se busca antes del tope" '    previa = await db.get(CreditoAdmin, carga.pedido)
    ya = previa is not None' '    previa = None
    ya = previa is not None' "assert 409 == 200" "test_carga[llena_el_tope]" "test_carga[vencidos_y_cien]"
sabotaje casos $R "el mismo pedido sirve para otra carga" \
  '    if (previa.usuario, previa.cantidad) != (username, carga.cantidad):' '    if False:' \
  "assert 200 == 409" "test_otra_carga_con_el_mismo_pedido[cantidad]" "test_otra_carga_con_el_mismo_pedido[usuario]"

# 3. El registro dice qué cuenta pagó.
sabotaje casos $R "el registro nombra al usuario aunque pague el estudio" \
  '                              cuenta=f"org:{cuenta.id}" if cuenta is not db_user else username,' \
  '                              cuenta=username,' "AssertionError" "test_carga[estudio]" "test_carga[vencidos_y_cien]"

# 4. Lo que no entra se dice con el número que entra.
sabotaje casos $R "el 409 no dice cuántas entran" 'entran como mucho {max(0, tope - vigentes)}.' 'entran como mucho {tope}.' \
  "mo mucho 100.'" "test_no_entra[91-10]" "test_no_entra[1-100]" "test_no_entra[120-1]"
sabotaje casos $R "el 409 da un número negativo" 'entran como mucho {max(0, tope - vigentes)}.' \
  'entran como mucho {tope - vigentes}.' "omo mucho -20." "test_no_entra[120-1]"

# 5. El cuerpo: un entero de 1 a 100 y un pedido con forma de UUID en minúsculas.
CANTIDAD='    cantidad: StrictInt = Field(ge=1, le=billing_service.EXTRA_OPS_MAX)'
sabotaje casos $R "la cantidad acepta texto y booleanos" "$CANTIDAD" \
  '    cantidad: int = Field(ge=1, le=billing_service.EXTRA_OPS_MAX)' "assert 200 == 422" \
  "test_cuerpo_invalido[cuerpo4]" "test_cuerpo_invalido[cuerpo5]"
sabotaje casos $R "la cantidad acepta cero o menos" "$CANTIDAD" \
  '    cantidad: StrictInt = Field(le=billing_service.EXTRA_OPS_MAX)' "== 422" \
  "test_cuerpo_invalido[cuerpo0]" "test_cuerpo_invalido[cuerpo1]"
sabotaje casos $R "la cantidad pasa del tope" "$CANTIDAD" '    cantidad: StrictInt = Field(ge=1)' \
  "assert 409 == 422" "test_cuerpo_invalido[cuerpo2]"
sabotaje casos $R "el pedido acepta cualquier texto" \
  '    pedido: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")' \
  '    pedido: str' "assert 200 == 422" \
  "test_cuerpo_invalido[cuerpo7]" "test_cuerpo_invalido[cuerpo8]" "test_cuerpo_invalido[cuerpo9]"

# 6. Quién y a quién.
sabotaje casos $R "la cuenta inexistente no da 404" '    if bloqueada is None:
        raise HTTPException(status_code=404, detail="No existe esa cuenta")
' '' "cannot unpack" "test_usuario_inexistente"
sabotaje casos $M "las rutas de admin no piden admin" '        admin_router.router,
        dependencies=[Depends(require_admin)]' '        admin_router.router,' \
  "assert 200 == 403" "test_quien_carga[no_admin]"

# 7. El diálogo: un pedido por carga sin confirmar, también al reabrir; el token CSRF,
# el texto del servidor y el refresco.
sabotaje pantalla $H "el doble clic manda dos pedidos" '            enviar.disabled = true;
' '' "FALLA: el doble clic mandó 2 pedidos"
sabotaje pantalla $H "la página no manda el token CSRF" '    <script src="/static/csrf.js"></script>
' '' "FALLA: doble clic: el diálogo dice «Token CSRF invalido"
sabotaje pantalla $H "cada envío usa otro pedido" \
  '            const pedido = previa && previa.cantidad === cantidad ? previa.pedido : crypto.randomUUID();' \
  '            const pedido = crypto.randomUUID();' "FALLA: reintento"
sabotaje pantalla $H "reabrir olvida la carga sin confirmar" '            const previa = sinConfirmar[u.usuario];' \
  '            const previa = undefined;' "FALLA: reabrir:"
sabotaje pantalla $H "otra cantidad usa el mismo pedido" 'previa && previa.cantidad === cantidad ? previa.pedido' \
  'previa ? previa.pedido' "FALLA: otra cantidad"
sabotaje pantalla $H "la carga confirmada sigue sin confirmar" '                delete sinConfirmar[esta.usuario];
' '' "FALLA: reabrir después de confirmar"
sabotaje pantalla $H "el 409 no muestra el texto del servidor" \
  "            const detalle = data && typeof data.detail === 'string' ? data.detail : null;" \
  '            const detalle = null;' "FALLA: tope"
sabotaje pantalla $H "el error deja el botón apagado" '            enviar.disabled = false;
        }' '        }' "FALLA: después de perder la respuesta no se puede reintentar"
sabotaje pantalla $H "la respuesta vieja escribe en otro diálogo" '            if (!carga || carga.pedido !== pedido) return;
' '' "FALLA: el diálogo de otra cuenta muestra «Cargada."
sabotaje pantalla $H "reabrir con la carga en vuelo no retoma su pedido" \
  '            carga = { usuario: u.usuario, pedido: previa && previa.pedido };' \
  '            carga = { usuario: u.usuario };' "FALLA: reabrir en vuelo:"
sabotaje pantalla $H "el diálogo no anota el pedido que envió" '            esta.pedido = pedido;
' '' "FALLA: doble clic: el diálogo no dice cómo terminó"
sabotaje pantalla $H "abrir otro diálogo deja el botón apagado" \
  "            document.getElementById('carga-enviar').disabled = false;" '' \
  "abrió sin poder cargar"
sabotaje pantalla $H "la tabla no se refresca después de cargar" '            if (response && response.ok) fetchUsuarios(0);
' '' "FALLA: la fila no muestra los 5 cargados"
sabotaje pantalla $H "las cargas sin confirmar se guardan en un objeto común" \
  '        const sinConfirmar = new Map();' \
  '        const sinConfirmar = { get(k) { return this[k]; }, set(k, v) { this[k] = v; }, delete(k) { delete this[k]; } };' \
  "FALLA: abrir __proto__"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
