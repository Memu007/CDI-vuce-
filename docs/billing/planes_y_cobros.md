# Planes y cobros de CDI

> Documento de referencia para cualquier asistente que necesite entender el modelo de negocio del billing sin releer todo el código.

## Plan actual (Ola 4 MVP)

| Plan | Precio/mes | Ops/mes | Clientes | Usuarios |
|------|-----------|---------|----------|----------|
| **Premium** | $30.000 ARS | 10 | Ilimitados | 3 |

No hay plan Básico activo. El sistema rechaza `"basic"` con error claro.

## Trial (prueba gratis)

- Todo usuario nuevo entra automáticamente en trial de **14 días**.
- No se pide tarjeta.
- Durante el trial tiene los mismos límites que el plan Premium.
- Al vencerse los 14 días, el estado pasa a `past_due` (vencido) automáticamente.
- Si el usuario no vuelve a entrar nunca, el cron de startup lo marca como vencido igual.

## Top-up (créditos extra)

- Precio: **$10.000 ARS** por **10 operaciones adicionales**.
- Se acumulan hasta un máximo de **100 créditos extra**.
- Vencen a los **30 días** desde la compra.
- Se limpian automáticamente al evaluar el límite de ops.

## Variables de entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `MP_ACCESS_TOKEN` | Sí | Access Token de MercadoPago (empieza con `TEST-` en sandbox, `APP_USR-` en producción). |
| `MP_WEBHOOK_SECRET` | Prod sí, Dev no | Secret HMAC para validar firmas del webhook. En dev puede omitirse. |
| `FRONTEND_URL` | No | URL pública de CDI (ej: `https://cdi-app.up.railway.app`). Si no está, usa `http://127.0.0.1:8000`. |
| `MP_SANDBOX` | No | `true`/`1` para modo sandbox (default en dev). `false` para cobrar de verdad. |
| `MP_TOPUP_PRICE_ARS` | No | Precio del top-up (default: 10000). |
| `MP_TOPUP_OPS` | No | Cantidad de ops por top-up (default: 10). |

## Webhook de MercadoPago

- Endpoint: `POST /api/payments/webhook`
- MercadoPago lo llama cuando un pago cambia de estado.
- CDI consulta el pago por API para confirmar que está `approved` antes de activar.
- El webhook verifica la firma HMAC contra `MP_WEBHOOK_SECRET`.
- Si la firma falla → 401.
- Si el usuario no existe → 400 (MP reintenta).
- Si hay bug inesperado → 500 (MP reintenta).
- Si ya se procesó ese `payment_id` → 200 con "skipped" (evita duplicados).

## Flujo de pago

1. Usuario registrado (trial 14 días).
2. Al vencer, ve banner "Tu plan venció" y un botón de pago.
3. Hace click → backend crea una `preference` de MercadoPago.
4. MP redirige al usuario a su checkout.
5. Usuario paga con tarjeta, débito, etc.
6. MP notifica al webhook → CDI activa el plan y resetea el contador de ops.
7. El usuario vuelve a CDI y ya puede operar.

## Estados de billing

| Estado | Significado |
|--------|-------------|
| `none` | Sin plan (raro, solo usuarios viejos pre-Ola 4). |
| `trial` | Prueba gratis de 14 días. |
| `active` | Pagando. |
| `past_due` | Trial vencido o pago falló. Puede seguir pagando para reactivar. |
| `canceled` | El usuario canceló. Sigue funcionando hasta el fin del período pagado. |

## Límites aplicados

- Crear operación: bloquea si `billing_status` no es `trial` o `active`, o si se pasó el límite de ops/mes. Devuelve HTTP 402.
- Crear cliente: bloquea si se pasó el límite de clientes del plan. Devuelve HTTP 402.
- Frontend: intercepta 402 y muestra modal "Tu plan venció" con CTA a pagar.

## Notas para desarrolladores

- Las suscripciones automáticas de MP (`preapproval`) están preparadas en código pero no activas. Hoy se usa Checkout API (pago manual mes a mes).
- El plan es configurable editando `billing_service.py` → `PLANS`.
- Los precios deben coincidir con lo configurado en el panel de MercadoPago.
