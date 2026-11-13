# Reproducción de CSRF-1 (2026-11-05, PM principal)

Sobre `b1c9d70` (rama `claude/dev-tecnica`, informe en `2ea9133`). Base:
`885ee89`. Producto: `/auth/logout` sale de las exenciones CSRF (`main.py`),
`track()` manda `X-CSRF-Token` y `logout()` avisa si el servidor rechaza
(`app_v2.js`).

## Lo que corrí

| Qué | Resultado |
|---|---|
| `tests/test_csrf.py` de `b1c9d70` copiado sobre `885ee89` | `1 failed, 10 passed`: falla `[/auth/logout-False-403]`, como dice el informe |
| `csrf1.sh b1c9d70` | 5 ROJO con su texto, «sabotajes con falla: 0», `EXIT=0` |
| `POST /auth/logout` sin ninguna cookie, `Origin: http://otro.example`, `CSRF_ENFORCE=true`, en `b1c9d70` | `200` y `Set-Cookie: access_token=""; Max-Age=0` y `csrf_token=""; Max-Age=0` |

La última fila es el pedido que manda un navegador desde otro sitio: la
cookie de sesión es `SameSite=Strict` y no viaja. El middleware sólo pide el
token si llega `access_token`, así que no lo pide, y la respuesta borra la
sesión igual. El caso nuevo de `test_csrf.py` pega la cookie a un pedido de
otro origen, cosa que un navegador no hace: por eso queda verde.

## Adversarios (Opus alto y Sonnet alto, contexto nuevo)

- **Opus, en Chromium:** una página en otro origen con sólo un
  `<form method=POST action=.../auth/logout>` cierra la sesión
  (`current_user antes 200 despues 401`). Lo mismo con `/logout`. Ya pasaba
  en la base; lo nuevo es que el informe dice que sin token da 403.
- **Opus:** con la red cortada en `/auth/logout` (`route.abort`), «Salir»
  lleva a `/` con `current_user 200`. Ya pasaba en la base, en la función que
  cambió la pieza.
- **Los dos:** sin la cookie `csrf_token` y con la de sesión viva, «Salir»
  avisa y no cierra; ninguna lectura vuelve a emitir la cookie. Es D57.
  Ningún camino del servidor pone `access_token` sin `csrf_token`.
- **Ya pasaba en la base, fuera de esta pieza** (van a CSRF-2):
  - la telemetría de la landing sin token (`landing.html:561`);
  - la pantalla vieja (`app.js`) no manda token en ninguna escritura, `/logout`
    incluido, y ese alias no borra `csrf_token`;
  - las rutas públicas de recuperación de cuenta (`request-password-reset`,
    `recover-username`, `reset-password`, `resend-verification`) dan 403 con
    una cookie de sesión vieja;
  - `"webhook"` en cualquier parte de la ruta saltea el control.
- **Ya pasaba, para SESION-1:** cerrar sesión no invalida `active_jti`; el
  token sirve hasta que vence.
- Sin nada: variantes de ruta, mayúsculas, barra final, `..`, métodos,
  `fetch` no-cors e iframe desde otro sitio; la telemetría con token llega
  (`200`) y no manda un token ajeno.
- No corrido: HTTPS con cookies `Secure`.

## Veredicto

Devolución corta por una causa, con un segundo punto en la misma función.
