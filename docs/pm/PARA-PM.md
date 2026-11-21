# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ADMIN-CREDITOS-1: plan, sin código de producto

Base: `a17011d1`, tu merge, y nada más mío arriba. Este commit es sólo de `docs/pm/PARA-PM.md`. No
escribí producto ni pruebas, y no corrí nada: cada número de líneas es una estimación. Arranco el
código después de que MARIA entregue D278 (b) y vos la integres, encima de su versión de
`admin_router.py` y `main.py`.

### Decisiones

| D | Pregunta | Opciones | Recomiendo |
|---|---|---|---|
| D232 | Si la carga pasa el tope de 100 | (a) se rechaza entera con 409, sin cargar nada, y el mensaje dice cuántas entran; (b) se carga hasta el tope y se dice cuántas entraron. «Cortar» lo leo como (b) | **(a)**. Es lo que hace hoy `/api/billing/topup` (409 «no entra»), y no carga menos de lo que eligió el admin sin que lo note. Con el número en el mensaje, reintentar con esa cantidad es un clic |
| D233 | Dónde vive el candado | (a) `_cuenta_bloqueada` pasa de `main.py` a un módulo chico, `main.py` la importa con el mismo nombre y la ruta va en `admin_router.py`; (b) la ruta va en `main.py`, con `Depends(require_admin)` escrito a mano; (c) `admin_router` importa de `main` adentro de la función | **(a)**. `main.py` importa `admin_router` (:94), así que importar de `main` arriba de todo es circular, y (c) lo esconde. Con (b), el permiso deja de venir del montaje (:1690), que hoy cubre a todas las rutas de admin, y depende de que nadie se olvide la línea. (a) mueve unas 25 líneas sin cambiarlas |
| D234 | Si la recarga pagada y la del admin comparten la función que acredita | (a) una función `acreditar_extra(cuenta, n, ahora)` en `billing_service`, que usan el webhook y la ruta nueva; (b) sólo la usa la ruta nueva y el webhook queda como está | **(a)**. Con (b), la regla (vencer antes, sumar, vencimiento a 30 días, `last_topup_at`) queda escrita dos veces, y §6 pide ponerla una vez. Toca el webhook de MP, así que lleva revisión fuerte y paso `cobro_mp1.sh` entero |
| D235 | Quién genera la clave que hace que un pedido se cargue una sola vez | (a) el panel la genera al abrir el diálogo (`crypto.randomUUID()`), es obligatoria y el reintento reusa la misma; (b) sin clave: el botón se deshabilita mientras espera y el servidor rechaza la misma carga (admin, cuenta, cantidad) dentro de N segundos | **(a)**. (b) no cubre el reintento después de un corte de red, y rechaza una segunda carga igual que sí era a propósito |
| D236 | Si el admin se puede cargar créditos a sí mismo | (a) sí, y queda registrado como cualquier otra carga; (b) no, 403 | **(a)**. Hoy el único admin es Emi, y el registro dice quién cargó a quién. Si algún día hay más admins, (b) es una línea |

**Supuestos que podés rechazar:**
- Igual que una recarga pagada, la carga **renueva a 30 días el vencimiento de todos los créditos
  vigentes**, no sólo el de los nuevos: hay un solo `extra_ops_expires_at` por cuenta. Por ejemplo,
  si el admin carga 1 a una cuenta con 90 vigentes, esos 90 pasan a vencer a 30 días. Que cada carga
  venza por separado cambia el esquema y queda afuera.
- La cantidad es un entero de 1 a 100. Pydantic rechaza 0, los negativos, los decimales y el texto
  con 422, y así no hay forma de quitar.
- Se puede cargar a una cuenta sin plan activo. Los créditos quedan guardados y se usan cuando la
  cuenta pueda crear operaciones. En la tabla del panel se ve el estado del cobro.
- **Propuesta fuera de alcance:** que el panel muestre el historial de cargas. La tabla nueva lo
  guarda; para mostrarlo falta otra pieza.

### 1. El camino

Es el mismo que el de una recarga pagada, con una sola función y el mismo tipo de candado.

**Ruta.** `POST /api/admin/usuarios/{username}/creditos` en `admin_router.py`, con el cuerpo
`{"cantidad": n, "pedido": "<uuid>"}`.
- `require_admin` le llega del montaje (`main.py:1690`), y el CSRF del middleware (`main.py:2117`).
- El panel no carga hoy `csrf.js` ni hace ningún POST. Hay que sumarle
  `<script src="/static/csrf.js">`, como en `landing.html:451`.

**Adentro, en una transacción:**
1. `_cuenta_bloqueada(db, username)` bloquea primero al usuario y después a su estudio, con
   `FOR NO KEY UPDATE` y `populate_existing`, y devuelve la cuenta que paga. A una integrante se le
   carga al estudio: es la misma regla que usan todas las rutas que cobran. Si el usuario no existe,
   404 y no se escribe nada.
2. `billing_service.acreditar_extra(cuenta, n, ahora)` hace, en este orden:
   - vence los créditos vencidos con `_expire_extra_ops`;
   - mira el tope con la misma cuenta que hoy usa `recarga_entra`, generalizada a `n` (hoy está fija
     en `TOPUP_OPS`);
   - si entra, suma `n`, pone `extra_ops_expires_at = ahora + 30 días` y `last_topup_at = ahora`;
   - si no entra, devuelve que no entra y la ruta responde 409 (D232).
3. Agrega la fila en la tabla nueva y hace commit (punto 2).

**El webhook (D234 a).** La rama de la recarga en `main.py:11739-11762` pasa a llamar a
`acreditar_extra`:
- El bucle de campos deja de copiar `last_topup_at` y `extra_ops_expires_at`, y se borra la línea
  del `+=` (:11762).
- `process_payment` deja de calcular esas dos fechas (`billing_service.py:378-379`) si ningún caso
  las mira. Si alguno las mira, quedan.
- El rechazo por tope del webhook sigue igual: se registra como «rechazado» con su motivo.

**Dónde se cruzan.** Los dos bloquean la fila de la cuenta que paga, y la segunda en llegar espera
el commit de la primera, así ninguna pisa a la otra:
- el webhook, con `FOR UPDATE` común (`main.py:11729`);
- el admin, con `FOR NO KEY UPDATE`.

Los dos candados se excluyen entre sí. El webhook toma una sola fila. El admin toma usuario y
después estudio, y el `KEY SHARE` que el webhook toma sobre `users` al actualizar el estudio no
choca con el `NO KEY UPDATE` del admin. Es el caso que arregló CONEXIONES-1-NOKEY, y se prueba en
Postgres 16 (caso 9), no se supone.

### 2. Una sola vez por pedido

**La clave.** El `pedido` (D235 a) es la clave primaria de la tabla nueva y se inserta en la misma
transacción que suma los créditos. Si hay doble clic, o un reintento después de que el primero ya
hizo commit, el segundo pedido:
1. espera el candado de la cuenta;
2. busca el `pedido` después de tener el candado y lo encuentra;
3. responde 200 con `ya_aplicado: true` y el saldo actual, sin sumar nada.

**Si llegan dos a la vez.** La búsqueda no alcanza para dos pedidos con la misma clave y cuentas
distintas, que no se esperan entre sí. Ahí la garantía es la clave primaria: el `IntegrityError` se
resuelve con rollback y la misma respuesta, como hace `_guardar_pago_mp` (`main.py:11524`).

**Misma clave, otro contenido.** Si llega la misma clave con otro usuario u otra cantidad, la
respuesta es 409 «ese pedido ya se usó para otra carga» y no se suma nada. Así una clave reusada por
error no queda como «ya aplicado».

**Cómo se prueba:**
- En SQLite: el mismo pedido dos veces seguidas suma una sola vez, y la misma clave con otra
  cantidad da 409.
- En Postgres 16: dos pedidos con la misma clave, soltados a la vez con una barrera que no es una
  espera fija, suman una sola vez y dejan una fila.
- En el panel: dos clics rápidos y un reintento después de que la red falle, con `route.fetch` en
  Playwright, cargan una sola vez.

### 3. El tope

Es D232. Con (a), si `vigentes + n` pasa de 100, la respuesta es 409 con el texto «Ya tiene
{vigentes} operaciones extra y el tope es 100: entran como mucho {100 − vigentes}.», y no se suma
nada ni se agrega fila. Los vigentes se cuentan después de vencer los vencidos, con la misma regla
que la recarga.

### 4. La tabla nueva y la base

**`creditos_admin`** sigue el modelo de `mp_pagos_aplicados` (`models.py:584`):

| Columna | Qué guarda |
|---|---|
| `pedido` | `String(36)`, la clave primaria |
| `admin` | `String`: quién cargó, sacado de la sesión y nunca del cuerpo |
| `cuenta` | «usuario» u «org:<id>», como en `mp_pagos_aplicados` |
| `usuario` | el usuario que eligió el admin |
| `cantidad` | `Integer` |
| `vigentes_antes` | `Integer` |
| `cargado_en` | `DateTime(timezone=True)`, con `server_default=func.now()` |

Tiene un índice en `cuenta` y **ninguna clave foránea**. Así, un insert no toma `KEY SHARE` sobre
`users` ni sobre `organizations`, y la fila queda aunque se borre la cuenta.

**Migración.** `init_db` corre `create_all(checkfirst=True)` (`database/connection.py:110`), que
crea la tabla nueva en SQLite y en Postgres. No hace falta un `ALTER`, porque no se agrega ninguna
columna a una tabla que ya existe. El Dockerfile arranca con `--workers 1` (:69), así que no hay dos
procesos creando la misma tabla. Se prueba en Postgres 16 sobre una base con el esquema actual y
datos de prueba:
- al arrancar, la tabla aparece;
- al arrancar de nuevo, no falla;
- las demás tablas no cambian: misma huella con `scripts/datos/copia_base.py`.

**Copia antes de publicar.** Se hace con BACKUP-1a: `copia_base.py copiar` (que verifica sola) y
después `enviar`. Correrlo contra producción lo deciden vos y Emi, como dice el script. Para volver
atrás alcanza con publicar el SHA anterior: la tabla queda sin uso y no molesta.

### 5. Permisos

- **Sólo admin**, con el mismo `require_admin`. Una cuenta que no es admin recibe 403, sin sesión es
  401 y sin `X-CSRF-Token` es 403. En los tres casos no cambia el saldo ni se agrega fila.
- **Qué ve el admin.** La respuesta trae la misma forma que una fila de `GET /api/admin/usuarios`
  (`_cuenta_en_la_lista`: créditos, vencimiento y última recarga), más la carga registrada y, para
  una integrante, el estudio al que se cargó.
- **Qué no ve.** Nada de la cuenta fuera de `_SALDO`: ni contraseña, ni tokens, ni datos de pago.
- **El registro.** `admin` sale del usuario de la sesión, nunca del cuerpo. Si el cuerpo trae un
  campo `admin`, se ignora.

### 6. Casos, sabotajes y tamaño

**Casos.** En `tests/test_admin_creditos1.py` (SQLite), salvo los que digan Postgres:

| # | Caso | Tiene que mostrar |
|---|---|---|
| 1 | Carga simple | Un usuario solo y un estudio: suma `n`, vence a 30 días, `last_topup_at`, una fila con los datos correctos |
| 2 | Integrante | La carga va al estudio; el usuario no cambia |
| 3 | Vencidos | Con 5 vencidos, una carga de 10 deja 10, no 15 |
| 4 | Tope | Datos: 90+10 entra; 91+10 da 409 sin fila; 95 vencidos + 100 entra |
| 5 | Permisos | No admin 403, sin sesión 401, sin CSRF 403; en todos, saldo igual y 0 filas |
| 6 | Cantidad | 0, −1, 101, 1.5 y «10» dan 422 |
| 7 | Una sola vez | Repetido, 200 `ya_aplicado` y una suma; otra cantidad con la misma clave, 409 |
| 8 | Postgres 16: misma clave a la vez | Una suma, una fila |
| 9 | Postgres 16: con una recarga pagada a la vez | Webhook falso, nada contra MP real: se acreditan las dos y no hay deadlock ni 500 |
| 10 | Postgres 16: con un guardado de la integrante a la vez | No hay deadlock (el insert toma `KEY SHARE`) |
| 11 | Postgres 16: migración | Tabla nueva, segundo arranque sin error, huella igual (punto 4) |
| 12 | Panel, en `pantalla_panel_dev.js` | El botón carga, el saldo de la fila se actualiza, un doble clic y un reintento cargan una vez, y el 409 del tope se muestra |
| — | Webhook (D234 a) | `cobro_mp1.sh` y sus casos, enteros, sin cambio |

**Sabotajes.** Van en `scripts/testing/sabotajes/admin_creditos1.sh`, uno por motivo, cada uno con
el texto que tiene que caer y lo que tiene que seguir verde:

| # | Sabotaje | Cae |
|---|---|---|
| 1 | Sin candado (`select` común en la ruta) | 9: se pierde una de las dos cargas |
| 2 | Sin clave primaria en `pedido` | 8: doble suma |
| 3 | Sin buscar el `pedido` con el candado | 7: doble suma en SQLite |
| 4 | Sin `require_admin` en el montaje | 5 |
| 5 | Sin tope | 4 |
| 6 | A la integrante en vez del estudio | 2 |
| 7 | Sin vencer antes | 3: queda 15 |
| 8 | `admin` sacado del cuerpo | 1, con un cuerpo que trae otro `admin` |
| 9 | La ruta en las exenciones de CSRF | 5 |
| 10 | El panel genera una clave por clic | 12: carga dos veces |
| 11 | Misma clave con otro contenido responde «ya aplicado» | 7 |

**Tamaño estimado:**
- **Producto, unas +95/−30:**
  - mover `_cuenta_bloqueada`: +25/−24;
  - `acreditar_extra` y `recarga_entra(n)`: +12/−3;
  - el webhook: +2/−3;
  - el modelo: +12;
  - la ruta: unas 40;
  - el panel: unas 25.

  Son más de 20 líneas netas porque la pieza es una función nueva con su tabla y su pantalla, no un
  arreglo.
- **Pruebas y arnés, unas +450.**

### 7. Riesgos y orden

- **Revisión fuerte**, porque es plata y permisos y toca el webhook: dos adversarios (Opus alto y
  Sonnet alto), `/code-review high` y `/security-review`.
- **Orden con D278 (b).** Toco `admin_router.py` y `main.py` después de la integración de MARIA,
  con `merge`. Si D278 (b) cambia `_SALDO` o `_cuenta_en_la_lista`, la respuesta de la carga sigue
  su forma nueva.
- **`create_all` no crea índices en una tabla que ya existe.** No aplica acá, porque la tabla es
  nueva, pero si la tabla se crea a mano antes de publicar, el índice falta.

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, nunca main; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message priority next; la rutina trig_011UpBfwEu9TUzoNUrviqoP5 me dispara /respondio. Pieza: ADMIN-CREDITOS-1, plan entregado sin producto sobre a17011d1; espero D232-D236 y la integración de D278 (b) de MARIA antes de codear encima de admin_router.py y main.py. Próxima D: D237. Reglas de Emi: sólo la PM me pide tareas, nada se publica sin su «dale» para el SHA, sin secretos ni datos reales, nada contra producción ni MP real.
