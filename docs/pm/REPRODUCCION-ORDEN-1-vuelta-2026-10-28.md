# Reproducción de ORDEN-1, vuelta (2026-10-28)

Entrega de la Dev técnica: informe `a036aba` (rama en `6f2bd5b`), producto
hasta `973a1ed` (sólo `app_v2.js`, +199/−33 desde `47e7110`). Es la vuelta
de la devolución sobre `0d89c20` (dueño, edad, pestaña viva).

## Lo que corrió la PM

API local sobre `973a1ed` con SQLite propia y Chromium (Playwright). Los
nombres de usuario son sintéticos.

1. **El dueño de la pestaña queda fijo después de la primera respuesta.**
   A abre la pestaña T; B entra en el mismo navegador; en T se carga «DE-B»:

   ```
   T currentUser = advA_… (A = advA_…)
   la sesión que usa T ahora es de advB_…
   guardado: true
   borradores en T: [{"user":"advA_…","closed":false,"factura":"DE-B","edad":16}]
   B abre una pestaña y recupera: null
   A entra y recupera: DE-B con usuario advA_…
   ```

   Lo que cargó la sesión de B queda a nombre de A y A lo recupera. La
   pestaña no dejó de guardar. La rama `user.username !== duenoPestana`
   (`app_v2.js:342-348`) sólo se alcanza desde `handleBillingReturn`; la
   comparación del CSRF sólo antes de la primera respuesta buena; `pageshow`
   guarda con el usuario fijo. El informe y el `CHANGELOG` dicen que la
   pestaña «deja de autoguardar»: con este recorrido, no.
2. **Al recargar con el usuario lento, la operación no vuelve.** Con
   `/auth/current_user` demorada 6 s o con 500 durante 5 s:

   ```
   [lenta] después de recargar: pantalla upload ; items en la pestaña: 0 ; borradores: [{"closed":true,"factura":"RECARGA-lenta",…}]
   [lenta] una pestaña nueva recupera: RECARGA-lenta
   [500] después de recargar: pantalla upload ; items en la pestaña: 0 ; borradores: [{"closed":true,"factura":"RECARGA-500",…}]
   [500] una pestaña nueva recupera: RECARGA-500
   ```

   `recuperarBorrador` corre una vez y espera 4 s (`ESPERA_USUARIO_MS`). La
   base recuperaba en el mismo caso. No se pierde, pero no hay aviso y
   aparece en otra pestaña.

## Adversarios (contexto nuevo)

**Opus alto.** Los dos de arriba (la PM los reprodujo), más:
- media, anterior a la pieza: generar el TXT desde T cuenta en las
  operaciones de B (`finalize.js:667`);
- baja: con localStorage lleno el autoguardado falla sin aviso
  (`app_v2.js:890`);
- mutantes vivos contra `pantalla_orden1.js`: m1 (sin la rama del dueño
  distinto), m2 (sin el tope de 30 s), m4 (sin `pageshow`), m5 (sin
  `sinSesion`).

**Sonnet alto**, centrado en cobertura. Sin cruce con el código tal cual
por su camino; mutantes vivos: la rama del dueño distinto (y con ella lo de
A queda a nombre de B), `sinSesion` (las dos líneas), `return !!currentUser`
→ `true`, el tope y el crecimiento de la espera, `ESPERA_PESTANA_MS` en
1 ms, el `borrarBorrador()` del `pagehide` y del intervalo (la operación
terminada vuelve como borrador si se cierra antes de 2,5 s), el barrido de
vencidos de otro usuario, `parsed.v !== 1` y `pageshow`. Más: el mismo
usuario que vuelve a entrar en otra pestaña rota el CSRF y la pestaña deja
de guardar sin aviso (falso positivo).

No corrido por la PM: `orden1.sh`, la suite completa (la Dev informa 4199
passed, 121 skipped, 3 xfailed sobre `d316db2`), Postgres.

## Veredicto

Devolución sobre `973a1ed`. Causa: el usuario de la pestaña se fija una vez
y la sesión no se vuelve a mirar antes de guardar o de recuperar; y la
recuperación depende de una sola espera. El detalle está en `PARA-DEV.md`.
