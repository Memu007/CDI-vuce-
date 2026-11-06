# Reproducción de la auditoría externa de Argon — 2026-10-24

Sobre `8b45207` (lo publicado). Cuatro revisores Opus, uno por área, cada uno
en su propio worktree de `8b45207` y su propia instancia local; la PM
re-verificó en el código lo principal de cada uno. Todo local: datos
inventados, ninguna llamada a Mercado Pago, a Railway ni a terceros.

Nada de esto entra al roadmap sin el «dale» de Emi. Los scripts de
reproducción no se suben (usan CUIT de prueba con dígito válido y son
recetas de ataque); acá queda la causa, la salida y la línea.

## Confiabilidad del informe

Las causas de fondo son casi todas reales. Varias «salidas observadas» no
pueden haber salido de este código: rutas y clases que no existen
(`/api/billing/status`, `BillingService`, plan `pro`,
`POST /api/organizations/members`, campo `PARTPRO`), líneas citadas que no
dicen lo que el informe dice (`maria_generator.py:917`, `:528`) y un JSON
de ejemplo que da 400. Conviene leer los informes de Argon como pistas, no
como evidencia.

## Tabla

Gravedad real después de reproducir. «Conocido» = ya figuraba en `docs/pm`.

| # | Qué pasa | Veredicto | Gravedad | Conocido |
|---|---|---|---|---|
| 1 | Excel de 2,7 KB con una hoja «escondida» (sin prefijo `r:`) llena la memoria del servidor (OOM). Cualquier usuario logueado | REPRODUCIDO | alta | no |
| 2 | Contador de filas/columnas se esquiva (`r="XFD1 "` con espacio, `<c>` sin `r`): 2,1 KB → OOM | REPRODUCIDO; arreglo previo incompleto | alta | sí, BLOQUEANTE de REVISION-EXCEL2 (variante con comilla ya cerrada) |
| 3.1 | `/api/migrations/analyze` lee dos veces una bomba en la hoja 2 | REPRODUCIDO | alta | no |
| 3.2 | import-historial sin tope de filas → OOM; corre en el hilo principal | PARCIAL («omite validación» es falso) | media | no |
| 3.3 | Rasterizar PDF | rama muerta (fitz no instalado) | baja | no |
| 4.1 | Después de comprar recarga, guardar operaciones da error 500 para siempre | PARCIAL: sí con columna `TIMESTAMP` sin zona; no con `timestamptz` | alta si la columna de producción es sin zona | no |
| 4.2 | `/api/billing/status` 500 | NO REPRODUCIDO (la ruta no existe) | — | — |
| 5.1 | El webhook no controla monto, moneda, reembolso ni receptor | REPRODUCIDO en código; que MP permita fabricar el pago, NO PROBADO | media | sí, COBRO-MP-1 |
| 5.2 | Carrera que multiplica una recarga | NO REPRODUCIDO (siempre +10) | baja | C6 en general |
| 5.3 | Repetir avisos de dos pagos viejos alternados: renueva la suscripción para siempre y la recarga hasta 100, sin autenticarse | REPRODUCIDO, también sin `MP_WEBHOOK_SECRET` en producción | alta | sí, C3 / COBRO-MP-1 (con dos detalles nuevos, abajo) |
| 6.1 | Alta de suscripción con `status:"authorized"` sin tarjeta: si MP lo rechaza, nadie puede suscribirse | payload REPRODUCIDO; rechazo de MP NO PROBADO | alta si MP rechaza | no |
| 6.2 | Los avisos propios de suscripción se descartan | PARCIAL | media | no |
| 6.3 | `mp_preapproval_id` se guarda en el usuario y no en el estudio | REPRODUCIDO, sin efecto hoy | baja | relacionado con C2 |
| 7 | Miembros de un estudio no ven clientes ni operaciones del estudio; el estudio pago ve «tu prueba terminó»; cancelar opera sobre el usuario; un miembro raso puede generar cobros del estudio; sacar un miembro le devuelve el trial; vaciar el email permite otra prueba | REPRODUCIDO; **no hay fuga de datos entre cuentas** | media / baja | parcial: ORG-1, C2, C7, C9 |
| 8.1 | Posición arancelaria con espacios pasa cruda al TXT (la pantalla la muestra bien) | REPRODUCIDO desde un Excel común | media-alta | no |
| 8.2 | Unidad no reconocida → 07 sin aviso por celda; `²` → `0²` | REPRODUCIDO | media | parte, MARIA-7 (m²) |
| 9.1 | `valor_total` que no cierra; `valor_unitario` vacío → 500 | REPRODUCIDO, sólo por API | baja-media | no |
| 9.2 | Cantidades del ítem redondeadas a 2 decimales (1250,375 → 1250,38; 0,004 → 0,00; 2,675 da 2,67 en cantidad y 2,68 en monto) | REPRODUCIDO desde el Excel | media-alta | parte, M9 |
| 10 | El link de verificación de email sirve 24 h, varias veces, entra a la cuenta aunque se haya cambiado la clave y saca al dueño | REPRODUCIDO | alta si se mandan mails de verificación | no |
| 11 | Agrupar pierde la procedencia; `grupo_id` vacío/0 junta ítems; 500 en `/generate_maria_export`; número ilegible → 0 al subir | REPRODUCIDO / PARCIAL, sólo por API | baja | no |
| 12.1 | Registrarse con un email ajeno | REPRODUCIDO, pero sólo con `REGISTER_TEST_EMAIL_REPLACE=true` (por defecto apagado) | depende de Railway | no |
| 12.2 | Choque de nombres de plantilla en `DATA_DIR/generated` | REPRODUCIDO | baja | no |
| 13.1 | Una ruta con «webhook» en el camino se saltea CSRF | REPRODUCIDO; SameSite=Strict mitiga | media-baja | no |
| 13.2 | Con una cookie vieja, restablecer la clave da 403 | REPRODUCIDO | media | no |
| 14 | El propio login exitoso reinicia el contador de intentos; bloqueo perpetuo del pedido de reset; tokens de reset paralelos no se revocan; `/auth/me` ignora el jti | REPRODUCIDO | media | parte, S3 / S4 |

## Lo que Argon no vio

- **El camino IPN no tiene firma** (`main.py:9282-9297`): se acepta también
  en producción sin `MP_WEBHOOK_SECRET`. El comentario de `main.py:9031-9033`
  dice lo contrario. Definir el secreto no cierra 5.3.
- **Dos recargas distintas a la vez** (5.4): el cliente paga dos paquetes y
  recibe uno. 8 de 8 corridas; el webhook responde 200 y MP no reintenta.
  Causa: suma leer-modificar-escribir sin bloqueo (`main.py:9388`,
  `9418-9420`, `9428`; estudio `9365-9366`).
- Repetir una suscripción vieja también resetea las operaciones usadas y
  extiende 30 días desde hoy.
- `dev_detail` se muestra en producción (`main.py:409-447`).

## Causas y evidencia por área

**Subida de archivos (1-3).** `sheets_del_libro` no ve hojas sin el prefijo
`r:` (`security/file_security.py:145/165`) y `_xlsx_solo_primera_hoja`
devuelve el archivo intacto (`main.py:3460`); el contador de filas ignora
`r` (`main.py:3445`) y `_ultima_columna` (`file_security.py:327`) no
normaliza espacios. La memoria llega al tope de 4 GB con 2,7 KB y 2,1 KB.
`migration_service.py:309/326/348` lee la hoja dos veces; import-historial
no tiene `max_filas` (`main.py:3823`).

**Cobro (4-6).** `_expire_extra_ops` compara `datetime.now(timezone.utc)`
con un valor sin zona (`services/billing_service.py:103`); la columna nace
`TIMESTAMP` cuando la agrega la migración (`main.py:688`, `1185`) y
`timestamptz` cuando la crea `create_all`. Salida: `TypeError: can't compare
offset-naive and offset-aware datetimes`, 500 en `/api/operations/manual` y
en guardar operación del cliente. Deduplicación por un único
`last_payment_id` (`main.py:9399`, `9403`; estudio `9353`, `9357`):
alternando dos pagos, el saldo de recarga fue 10, 20 … 100. Con
`ENVIRONMENT=production` sin secreto: JSON sin firma 401, IPN sin firma 200
y acredita. `process_payment` (`billing_service.py:289-347`) acepta $1 ARS,
1 USD y un reembolso parcial. Preapproval: `billing_service.py:182-188`.

**Organizaciones (7).** `effective_owner = team_owner_username or username`
(`auth/dependencies.py:113-114`) y los estudios sólo asignan
`organization_id`. Trial evaluado sobre el usuario
(`auth/dependencies.py:97-106`; `_check_expired_trials`, `main.py:717-747`).
Cancelar/reactivar sobre el usuario (`main.py:1995-2065`). En Postgres el
registro por invitación da 500 (C7), así que los miembros se vincularon por
SQL local.

**TXT MARIA (8, 9, 11).** IESPNCE crudo: `maria_generator.py:913-928`,
`main.py:4740`. Unidad por celda ignorada: `main.py:5733-5754`. Cantidades:
`maria_generator.py:969-976`; el control de decimales existe sólo para
`[SBT]`.

**Sesión (10, 12-14).** `verify_email` no mira `is_verified` y siempre
emite sesión, pisando `active_jti` (`main.py:2987-3037`; 3010, 3018 y 3023
re-verificadas por la PM); el token no queda atado al email ni a la clave.
CSRF: `"webhook" in path` (`main.py:1686`).

## Lo que no se corrió

- Nada contra producción, Railway ni Mercado Pago.
- No se sabe el tipo real de `extra_ops_expires_at` en la base de Railway
  (decide 4.1). Consulta de sólo lectura para quien tenga acceso:
  `SELECT table_name, data_type FROM information_schema.columns WHERE column_name='extra_ops_expires_at';`
  — si dice `timestamp without time zone`, 4.1 vale en producción.
- No se sabe si MP rechaza el alta de suscripción (6.1): se ve en los logs de
  Railway («MP rechazó preapproval» / «Error creando checkout MP») o
  preguntando si alguien se suscribió con éxito.
- No se sabe si producción manda mails de verificación (decide 10) ni si
  `REGISTER_TEST_EMAIL_REPLACE` está encendida (decide 12.1).
- Que MP permita fabricar un pago aprobado barato con referencia de CDI (5.1).

## Propuesta de prioridad (la decide Emi)

1. Archivos que tiran el servidor (1, 2, 3.1, 3.2): reabrir REVISION-EXCEL2
   como incompleta.
2. Cobro (5.3 + IPN sin firma + 5.4, después 5.1 y 6): ampliar COBRO-MP-1.
3. Link de verificación (10) y la familia S3/S4 (13, 14).
4. TXT (8.1, 9.2, 8.2): sumar a MARIA-7 / M9.
5. Estudios (7): ORG-1.
6. Lo bajo (3.3, 6.3, 9.1, 11, 12.2): lote de limpieza.
