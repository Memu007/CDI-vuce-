#!/usr/bin/env bash
# Negativos de CSRF-2: cada sabotaje deshace una parte del arreglo y la prueba
# que la cubre tiene que fallar por ese motivo. Las rutas exentas y el alias de
# cierre los mide tests/test_csrf.py; lo que mandan la landing y la pantalla
# vieja, scripts/testing/pantalla_csrf2.js contra una API con CSRF_ENFORCE=true.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8878] scripts/testing/sabotajes/csrf2.sh [SHA]
PANTALLA=pantalla_csrf2.js
source "$(dirname "$0")/_csrf_comun.sh"

M=proyecto_maria/main.py
J=proyecto_maria/static/csrf.js
CONTROL='        if method in _CSRF_SAFE_METHODS or path in _CSRF_EXEMPT_PATHS:'
EXENTAS=tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas
sabotaje pytest_csrf $M "el alias responde sin cerrar la sesión" \
  "FAILED tests/test_csrf.py::test_logout_con_token_borra_las_dos_cookies[/logout]" \
  '    return await logout(request, response)' '    return {}'
sabotaje pytest_csrf $M "«webhook» en cualquier parte de la ruta saltea el control" \
  "FAILED $EXENTAS[DELETE /api/catalog/x/productos/abc-webhook]" \
  "$CONTROL" "${CONTROL%:} or \"webhook\" in path:"
sabotaje pytest_csrf $M "las exentas se comparan por prefijo" \
  "FAILED $EXENTAS[POST /auth/loginx]" \
  "$CONTROL" "${CONTROL% or*} or path.startswith(tuple(_CSRF_EXEMPT_PATHS)):"
sabotaje pytest_csrf $M "restablecer la clave vuelve a pedir el token" \
  "FAILED $EXENTAS[POST /auth/reset-password]" \
  $'    "/auth/reset-password",\n' ''
sabotaje pantalla $J "csrf.js no pone el token" \
  "FALLA: la telemetría de la landing dio 403" \
  "        if (!headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', decodeURIComponent(m[1]));" ""
sabotaje pantalla $J "csrf.js manda el token a otro origen" \
  "FALLA: el token CSRF salió hacia otro origen" \
  " || url.origin !== location.origin" ""
sabotaje pantalla proyecto_maria/templates/landing.html "la landing no carga csrf.js" \
  "FALLA: la telemetría de la landing dio 403" \
  $'<script src="/static/csrf.js"></script>\n' ''
sabotaje pantalla proyecto_maria/templates/dashboard.html "la pantalla vieja no carga csrf.js" \
  "FALLA: la copia de la pantalla vieja dio 403" \
  $'    <script src="/static/csrf.js?v={{ version }}" defer></script>\n' ''

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
