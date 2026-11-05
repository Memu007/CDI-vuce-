#!/usr/bin/env bash
# Negativos de CSRF-1: cada sabotaje deshace una parte del arreglo y la prueba
# que la cubre tiene que fallar por ese motivo. Lo que se rechaza sin token lo
# mide tests/test_csrf.py; lo que la página manda, scripts/testing/pantalla_csrf1.js
# contra una API con CSRF_ENFORCE=true, como en producción.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8878] scripts/testing/sabotajes/csrf1.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia: no toca tu copia ni
# datos compartidos. Sale con error si un sabotaje no encuentra su patrón o
# no pone rojo con el texto esperado.
PANTALLA=pantalla_csrf1.js
source "$(dirname "$0")/_csrf_comun.sh"

M=proyecto_maria/main.py
A=proyecto_maria/static/v2/app_v2.js
sabotaje pytest_csrf $M "cerrar sesión vuelve a estar exento" \
  "FAILED tests/test_csrf.py::test_enforce_pide_token_a_logout_y_telemetria[/auth/logout-False-403]" \
  '    "/auth/register",' $'    "/auth/register",\n    "/auth/logout",'
sabotaje pytest_csrf $M "la telemetría se exenta en vez de mandar el token" \
  "FAILED tests/test_csrf.py::test_enforce_pide_token_a_logout_y_telemetria[/api/session/state-False-403]" \
  '    "/auth/register",' $'    "/auth/register",\n    "/api/session/state",'
sabotaje pantalla $A "la telemetría de la página sale sin el token" \
  "FALLA: la telemetría de la página dio 403" \
  "'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() }" "'Content-Type': 'application/json' }"
sabotaje pantalla $A "«Salir» sale sin el token" \
  "FALLA: «Salir» no llevó al inicio" \
  "                if (csrf) headers['X-CSRF-Token'] = csrf;" ""
sabotaje pantalla $A "«Salir» rechazado lleva al inicio igual" \
  "FALLA: «Salir» rechazado no avisó y la página fue a /" \
  "            if (!res.ok) {" "            if (false) {"
sabotaje pytest_csrf $M "cerrar sesión borra las cookies aunque no llegue la de sesión" \
  "FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/auth/logout-false]" \
  $'    if request.cookies.get("access_token"):\n        response.delete_cookie' $'    if True:\n        response.delete_cookie'
sabotaje pytest_csrf $M "el alias borra la cookie por su cuenta" \
  "FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/logout-false]" \
  '    return await logout(request, response)' $'    response.delete_cookie("access_token")\n    return {}'
sabotaje pantalla $A "«Salir» sin red lleva al inicio igual" \
  "FALLA: «Salir» sin red no avisó y la página fue a /" \
  "            if (e.message !== 'unauthorized') {" "            if (e.message === ERROR_SIN_SESION) {"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
