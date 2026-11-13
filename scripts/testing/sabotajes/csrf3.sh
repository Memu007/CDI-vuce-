#!/usr/bin/env bash
# Negativos de CSRF-3: cada sabotaje deshace una regla de la emisión del token a
# una sesión que no lo tiene, y la prueba que la cubre tiene que fallar por ese
# motivo. Qué sesión lo recibe lo mide tests/test_csrf.py; que la página v2 sin
# cookie csrf_token escriba sin el aviso de otro usuario, y que lo avise si otro entra
# antes de saber quién es, scripts/testing/pantalla_csrf3.js contra una API con
# CSRF_ENFORCE=true.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8878] scripts/testing/sabotajes/csrf3.sh [SHA]
PANTALLA=pantalla_csrf3.js
source "$(dirname "$0")/_csrf_comun.sh"

D=proyecto_maria/auth/dependencies.py
M=proyecto_maria/main.py
CASO=tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe
MARCA=$'    # CSRFMiddleware le emite el csrf_token a esta sesión si le falta.\n    request.state.sesion_valida = True\n'
VERIFICA=$'    sesion = await sesion_de_la_request(request, db)\n    if sesion is None:\n        raise HTTPException(status_code=401, detail="Sesión inválida o vencida")\n    user = sesion[0]\n'
EMITE='            if getattr(request.state, "sesion_valida", False) and not request.cookies.get(CSRF_COOKIE_NAME):'
sabotaje pytest_csrf $D "la sesión se marca válida antes de mirar si está revocada" \
  "FAILED $CASO[revocada-/auth/current_user]" "$VERIFICA$MARCA" "$MARCA$VERIFICA"
sabotaje pytest_csrf $D "la sesión se marca válida antes de verificar la firma" \
  "FAILED $CASO[vencida-/auth/current_user]" "$VERIFICA$MARCA" "$MARCA$VERIFICA"
sabotaje pytest_csrf $M "el token se emite sin sesión" \
  "FAILED $CASO[sin_sesion-/auth/current_user]" "$EMITE" '            if not request.cookies.get(CSRF_COOKIE_NAME):'
sabotaje pytest_csrf $M "el token se cambia aunque la sesión ya lo tenga" \
  "FAILED $CASO[presente-/auth/current_user]" "$EMITE" '            if getattr(request.state, "sesion_valida", False):'
sabotaje pytest_csrf $M "una cookie csrf_token vacía cuenta como token" \
  "FAILED $CASO[vacia-/auth/current_user]" "$EMITE" '            if getattr(request.state, "sesion_valida", False) and CSRF_COOKIE_NAME not in request.cookies:'
sabotaje pytest_csrf $M "la sesión sin token no lo recibe" \
  "FAILED $CASO[ausente-/auth/current_user]" "$EMITE" '            if False:'
sabotaje pytest_csrf $M "la página v2 abre sin el token" \
  "FAILED $CASO[ausente-/dashboard]" \
  '        await get_current_user(request, Response(), db)' '        pass'
sabotaje pantalla proyecto_maria/static/v2/app_v2.js "la pestaña no mira si el token cambió" \
  "FALLA: entró otro usuario y la pestaña no lo avisó" \
  "if (sesionAntes !== sesionAlAbrir || getCsrfToken() !== sesionAlAbrir) marcarAjena();" \
  "if (sesionAntes !== sesionAlAbrir) marcarAjena();"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
