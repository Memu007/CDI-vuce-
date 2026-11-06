# Reproducción de CSRF-1, vuelta 2 (2026-11-05)

Sobre `9e37673` (rama `claude/dev-tecnica`, informe en `c536184`), en un
worktree limpio. Producto de la vuelta: `main.py` y `app_v2.js`, `+12/−12`.

## Lo que corrí

| Qué | Resultado |
|---|---|
| `tests/test_csrf.py` + `test_prelaunch_block1.py`, `CSRF_ENFORCE=true` | `59 passed` |
| lo mismo con `CSRF_ENFORCE=false` | `59 passed` |
| `chequeo-6.py b14e10c 9e37673` | `producto +12/−12`, historia vacía, `avisos: 0` |
| `csrf1.sh 9e37673` | 8 ROJO con su texto, `sabotajes con falla: 0`, salida 0 |
| `orden1b.sh 9e37673` | ver abajo |

La primera corrida de los dos guiones dio `BASE … ya está en rojo` porque les
pasé `PY` con ruta relativa y el guion trabaja en otro worktree. Con la ruta
absoluta, verde. No es de la pieza.

No corrí la suite completa: la Dev la corrió en worktree limpio sobre el
mismo SHA (`4427 passed`) y la vuelta cambia 24 líneas de dos funciones.

## Adversarios (contexto nuevo, alto)

**Opus.** Sin bloqueantes.
- `<form>` de otro sitio en Chromium contra uvicorn local, 16 variantes
  (dos orígenes, dos hosts, las dos rutas, barra final con 307, `text/plain`),
  enforce `true` y `false`: la sesión sigue en todas.
- TestClient: métodos, mayúsculas, dobles barras, `%2F`, cookies vacías,
  con prefijo, repetidas: ninguna borra sin la cookie de sesión.
- Saboteó el `if` del endpoint, el alias que borra sin condición y el
  endpoint que nunca borra: las pruebas nuevas fallan las tres.
- «Salir» con 500, 429 y 402 forzados queda en la página con el aviso.
- **Baja, hueco de prueba:** nada exige que el alias `/logout` cierre de
  verdad. Un alias que devuelve 200 sin borrar deja `8 passed`. Lo usa la
  pantalla vieja: va a CSRF-2.
- Con `CSRF_ENFORCE=false` y la cookie presente, el cierre sin token borra:
  es el modo que sólo registra, igual que todas las escrituras. En
  producción el valor por defecto es `true`.

**Sonnet.** Sin hallazgos en el diff.
- El alias que delega con `await logout(request, response)` borra las dos
  cookies en la respuesta real.
- Con cookie y sin token, bajo enforce, dan 403 sin `Set-Cookie`:
  `/auth/logout`, `/logout`, `change-password`, `reset-password`,
  `resend-verification` y `organizations/create`.
- Sesión vencida con token CSRF: cierra.
- Ya estaba antes y es de CSRF-2: `"webhook"` en cualquier parte de la ruta
  saltea el control (`DELETE /api/catalog/x/productos/abc-webhook` da 200
  con cookie y sin token).
- También previo: `startswith` en `/healthx`, `/staticx`, `/auth/loginx` (hoy
  404) y la sesión sin cookie `csrf_token` que no puede cerrar (D57 a).
