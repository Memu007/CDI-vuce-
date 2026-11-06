# Reproducción de OBSERVABILIDAD-1 (2026-10-28)

Entrega de MARIA en `39be45e` (base `88b22c8`). Producto: la función
`_migrate_add_api_logs_owner_column()` en `proyecto_maria/main.py` (cerca de
la línea 1288), llamada en el arranque.

## Lo que corrió la PM

- `tests/test_observabilidad1.py` sobre `39be45e`, SQLite: `8 passed`.
- La fuga del punto 3, en SQLite con la app real (uvicorn, base nueva):
  el script del adversario adaptado a SQLite, desde el scratchpad de la PM.
  `/api/dev/stats`, pedido por el admin, devuelve entre otras:

  ```
  STATS_LOG GET /api/invitations/oFWvZf0lb5Q-Nbg96tsEUg7MDHXWve7vQgGmOiWQpbA 200 127.0.0.1
  STATS_LOG GET /quotes/SECRETQUOTEHASH111 200 127.0.0.1
  STATS_LOG GET /api/payments/demo-checkout/SECRETPREF333 404 127.0.0.1
  STATS_LOG GET /api/quotes/public/SECRETQUOTEHASH222 404 127.0.0.1
  STATS_LOG GET /api/clientes/by-cuit/20123456789 401 127.0.0.1
  STATS_LOG GET /download/SECRETFILE444.xlsx 401 127.0.0.1
  ```

  El primero es un token de invitación real de esa base descartable,
  completo. La query no se guarda (`/auth/verify-email`, `/reset-password`
  y el webhook quedan sin sus parámetros).
- Leído en el código: el `ALTER` y el `CREATE INDEX` van en el mismo
  `engine.begin()`, y el «✅ Migracion: agregada columna» se imprime antes
  del commit.

## Adversario (Sonnet alto, contexto nuevo, Postgres 16 propio)

1. **Media, de la pieza.** El `ALTER` y el índice comparten transacción: el
   lock exclusivo del `ALTER` dura todo el armado del índice y frena
   lecturas y escrituras de `api_logs`. Midió 1,99 s con 4 millones de
   filas y 9,31 s con 16 millones (unos 0,6 s por millón). El
   `lock_timeout` no lo corta. No corrido por la PM; el código lo confirma.
2. **Media, de la pieza.** Con otra transacción que tiene tomada la tabla,
   el `ALTER` espera 5 s, frena a todos los que llegan detrás, falla, y la
   columna recién se reintenta en el próximo arranque. No corrido por la PM.
3. **Media-alta, fuera del diff pero la enciende la pieza. Reproducido por
   la PM** (arriba). `MetricsMiddleware` guarda el camino crudo, y el panel
   de admin lo muestra: tokens de invitación (con el token y el email que
   devuelve `GET /api/invitations/{token}` alcanza para entrar al estudio),
   hashes de presupuestos públicos, nombres de archivo y CUIT. Hoy no pasa
   en producción sólo porque la métrica falla; esta pieza la arregla.
4. **Baja, de la pieza.** El mensaje de columna agregada sale antes del
   commit: si la transacción se revierte (por ejemplo, por un
   `statement_timeout`), el log dice que la agregó y no está. No queda nada
   a medias y el próximo arranque la completa. Confirmado por la PM en el
   código, no corrido.
5. **Baja.** Un índice inválido o parcial con `owner_username` primero se da
   por bueno. Hipotético: nadie los crea así. A riesgos.
6. **Baja, fuera de alcance.** Un camino de más de 200 caracteres pierde su
   métrica en Postgres (`VARCHAR(200)`). A riesgos.

## Veredicto

Devolución sobre `39be45e`. Causa: la pieza vuelve a grabar la métrica sin
mirar qué graba. El detalle está en `PARA-DEV-2.md`.
