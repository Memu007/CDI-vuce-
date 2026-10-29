# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D14 de COBRO-MP-1: hecha en `4ef59f4`

Hice D14 (a) en un commit de pruebas, sin tocar el producto:

- La barrera de `cobro_mp1_postgres.py` cruza a los dos avisos después de
  buscar el pago en `mp_pagos_aplicados` y antes de `_registrar_pago_mp`.
- Los rojos dudosos de `cobro_mp1.sh` muestran las líneas `FALLA` de
  Postgres.

Las corridas, sobre `4ef59f4`:

- Base de `cobro_mp1_postgres.py`: `fallas: 0`.
- `cobro_mp1.sh` completo: 108 `ROJO`, 5 `BASE`, el `VERDE` de control
  esperado («sin mirar antes de insertar: sigue en verde, como tiene que
  ser») y `sabotajes con falla: 0`, salida 0.
- El sabotaje de D31, a mano, dio rojo las 5 veces: `FALLA | el mismo pago
  dos veces a la vez: uno aplicado y otro salteado ([200, 200], [None,
  None])`.

D13 (c) va en la próxima vuelta de COBRO-MP-1, después de tu veredicto de
ORDEN-1b, con su rojo antes y su sabotaje.

## ORDEN-1b: entregada en `6c459d2` (informe en el commit de arriba)

**Resultado.** Se cumple el criterio en los casos que pediste: ninguna
escritura sale a nombre de otro usuario desde una pestaña cuyo dueño ya no
es el de la sesión.

- Generar con B adentro no crea ni cobra nada en ninguna cuenta.
- Guardar un cliente, que es de otra familia de escritura, tampoco.
- Pasa lo mismo con un servidor que no exige CSRF.
- «Salir» desde la pestaña de A no cierra la sesión de B.
- La telemetría no sale a nombre de B.
- Cuando A sale y vuelve a entrar, la pestaña sigue guardando y generando
  sin falsos bloqueos.
- D11: la duplicada que no pudo adoptar avisa «Comprobando la sesión…» y
  recupera la operación cuando confirma la sesión.

**Una puerta con un rojo dudoso:** el lote de `orden1b.sh` terminó en
`sabotajes sin rojo: 1`. Fue z23 saboteado: dio rojo, pero por
«`apiRequestContext.post: socket hang up`» en vez de por el motivo. Lo
reproduje solo cuatro veces y las cuatro dio el rojo correcto. Lo trato como
rojo de entorno con causa no demostrada (detalle en D15).

Lo que decidís vos: **D15** y **D16**.

| Qué | SHA |
|---|---|
| Base: D14 | `4ef59f4` |
| Pruebas: z12, z20 a z24, en rojo | `95643e3` |
| Producto: el freno, el diálogo, «Salir» y D11 | `9a309a3` |
| Pruebas: z25 y z26, regresiones que encontró el `/code-review` | `ee27d5e` |
| Producto: con la sesión cerrada va al login; «Salir» avisa si no pudo | `91b25f2` |
| Pruebas: z27, telemetría (del adversario) | `267ef10` |
| Producto: la telemetría con el freno | `68a2f37` |
| Pruebas: arreglos de z24 y del texto esperado de z20 en `orden1b.sh` | `629042d` |
| Pruebas: z28 y los patrones de `orden1.sh` que movió ORDEN-1b | `6c459d2` |

Dato menor: el mensaje de `95643e3` dice que el rojo fue «sobre `4ef59f4`».
En realidad lo corrí sobre `be25008`, una versión anterior del mismo commit
de pruebas. Las dos tienen el mismo producto: `git diff be25008 4ef59f4 --
proyecto_maria` sale vacío.

## Decisiones

**D15. El rojo dudoso de z23 en el lote de `orden1b.sh`.**

Qué pasó:

- En el lote, el sabotaje que quita la consulta dio rojo, pero no por el
  motivo: dio «socket hang up» en un `post` de la prueba (registro, entrada
  o la mirada al servidor), no en la pestaña.
- El log de esa API no quedó: el `trap` del script borra la carpeta
  temporal.
- Ese lote corría junto con la suite y la pantalla completa.
- Aislado, en el mismo SHA, con el mismo sabotaje y su log guardado, dio el
  rojo correcto 4 de 4: «FALLA: con un servidor que no exige CSRF, entró
  otro usuario y la pestaña de A generó enseguida y quedó una operación en
  la cuenta de B: 1 creadas, 1 cobradas».
- En esas cuatro corridas, el log de la API no muestra ninguna caída. La
  única línea de error es la de ARCA novedades, que no tiene red y es
  esperada.
- En la corrida anterior, sobre `629042d`, el mismo sabotaje dio `ROJO`.

Mi hipótesis, sin demostrar: una conexión reutilizada que el servidor cierra
justo cuando la prueba la vuelve a usar, más probable con carga.

Opciones:

- **(a)** Aceptar la puerta así, con el rojo dudoso documentado.
- **(b)** Que `orden1b.sh` guarde el log de la API de cada `ROJO?` y que
  la prueba reintente una vez sólo sus propios pedidos (no los de la
  pestaña) cuando el servidor corta la conexión. Va en un commit de
  pruebas, con un sabotaje que muestre que el reintento no tapa un rojo del
  producto.
- **(c)** Sólo guardar el log de cada `ROJO?`, sin reintento, para
  diagnosticarlo la próxima vez que aparezca.

**Recomiendo (c).** Un reintento es justamente lo que puede esconder un
problema que todavía no entiendo. Con el log, la próxima aparición dice si
el servidor se cayó o cortó la conexión.

**D16. `/auth/logout` está exento de CSRF en el servidor.**

`main.py` (~1652) lo deja afuera de la verificación. Por eso, con B
adentro, lo único que impide que la pestaña de A cierre la sesión de B es
el freno de la pestaña (z24). El criterio de ORDEN-1b habla de la pestaña y
ahí se cumple. No es una fuga de datos: el peor caso es que B quede afuera
y tenga que volver a entrar.

Opciones:

- **(a)** Dejarlo así.
- **(b)** Una pieza aparte para que el servidor exija CSRF en el logout,
  con su rojo antes. Revisaría primero quién llama al logout sin el header:
  la v1 no manda CSRF.

**Recomiendo (a) por ahora y (b) en la cola**, detrás de lo que ya está
priorizado: el impacto es una molestia, no datos ni plata.

## Qué cambió, por causa

**El freno: `api()`, en `app_v2.js`.** Antes de cada escritura (todo lo que
no es GET, HEAD ni OPTIONS), la pestaña compara el token CSRF de la cookie
con el de su dueño. El de su dueño es el que ya confirmó o, si todavía no
confirmó ninguno, el que leyó al abrir.

- Si son iguales, la escritura sale sin consulta extra.
- Si son distintos, pregunta `/auth/current_user`:
  - si sigue siendo el dueño, adopta el token nuevo y la escritura sale
    (A salió y volvió a entrar);
  - si es otro usuario, la escritura no sale y la pestaña se tapa;
  - si no se puede comprobar, la escritura no sale y muestra «No se pudo
    comprobar la sesión. Recargá la página.»;
  - si el servidor dice 401, va al login.

**Tu pista del CSRF.** La apliqué en una forma equivalente, porque al pie de
la letra trababa a A cuando vuelve a entrar:

- Con el freno aprobado, el header que sale es el token ya validado. Entre
  la consulta y la lectura de la cookie no hay `await`.
- Si la cookie cambia antes del envío, un servidor con `CSRF_ENFORCE`
  rechaza el pedido, porque el header ya no coincide con la cookie.
- Sin `CSRF_ENFORCE` frena sólo la consulta. Para eso están z21 y z23: hacen
  como un servidor que no lo exige.

**La pestaña tapada.** El diálogo `#pestanaAjena` dice «Entró otro usuario»
y «Esta pestaña ya no puede guardar nada. Recargá la página para seguir con
el usuario que entró.», con el botón «Recargar». Escape no lo cierra.
`marcarAjena()` es el único lugar que lo abre: lo usan el freno y el
chequeo que ya existía.

**«Salir».** Con la sesión de otro, no hace nada, porque la pestaña ya está
tapada. Si no pudo comprobar la sesión, avisa «No se pudo cerrar la sesión»
y no simula haber salido.

**Telemetría.** No sale si el token no es el del dueño.

**D11.** Cuando la duplicada todavía no sabe quién es el usuario, avisa
«Comprobando la sesión antes de recuperar la operación guardada…» y anota
que tiene que recuperar. Al confirmar la sesión, busca el borrador y lo
adopta con la misma regla de antes (`adoptarTarde`, que salió de
`DOMContentLoaded` para no duplicarla).

**Limpieza.** `irAlLogin()` es la única copia de la redirección al login, y
`consultarUsuario()` la única de la consulta con tope de tiempo. Las dos ya
existían duplicadas.

**Casos nuevos en `pantalla_orden1.js`:**

| Caso | Qué prueba |
|---|---|
| z20 | generar con B adentro, en tres momentos |
| z21 | guardar un cliente con B adentro, sin CSRF |
| z22 | A sale, vuelve a entrar y genera |
| z23 | z20 con un servidor que no exige CSRF |
| z24 | «Salir» con B adentro |
| z25 | con la sesión cerrada, va al login |
| z26 | «Salir» sin poder comprobar |
| z27 | telemetría |
| z28 | el guardián de `usuarioActual` |

`orden1b.sh` tiene 14 sabotajes, uno por motivo. En `orden1.sh` actualicé
los patrones que ORDEN-1b movió.

**Un VERDE que explico.** Al cargar, el semáforo hace un POST a
`/api/validate/smart`. Ese POST pasa por el freno y deja confirmado el token
del dueño. Por eso el sabotaje «l» de `orden1.sh` necesitó su propio caso,
z28.

## Riesgos

No arreglé ninguno de estos; la severidad va entre paréntesis.

**Lo que trae ORDEN-1b:**

- **(media)** Sin `CSRF_ENFORCE`, entre que el freno aprueba y el pedido
  sale hay una ventana de microsegundos. Si en ese instante cambia la
  cookie, el pedido sale con la sesión nueva. Con `CSRF_ENFORCE`, el
  servidor lo rechaza. **En Railway no verifiqué `CSRF_ENFORCE`**: por
  defecto vale `true` si `IS_PRODUCTION`, y eso depende de `ENVIRONMENT`.
- **(media)** `/auth/logout` exento de CSRF en el servidor: es D16.
- **(baja)** El freno es del cliente, no del servidor. Una v1 abierta, que
  no manda CSRF ni tiene freno, sigue escribiendo a nombre de quien esté en
  la cookie. Es previo a esta pieza.
- **(baja)** Los GET no pasan por el freno. La pestaña de A puede leer datos
  de B hasta que se tapa. Un GET con efectos tampoco queda cubierto. El
  criterio habla de escrituras.
- **(baja)** `CDI.currentUser` queda con A en una pestaña ya tapada. Es
  cosmético: la pestaña no puede guardar.
- **(baja)** «Comprobando…» puede pisar un momento al aviso de sesión
  cerrada.
- **(baja)** En cockpit o clientes, el diálogo aparece recién en la primera
  escritura o en el chequeo periódico, no al instante.
- **(baja)** Una primera carga con `current_user` caído puede tapar la
  pestaña de más con «Entró otro usuario» cuando el usuario era el mismo. Se
  arregla recargando.
- **(baja)** Algunos POST de sólo lectura, como `/api/validate/smart`, hacen
  la consulta a `current_user` cuando el token cambió. Es una consulta de
  más, no un bloqueo.

**De antes:**

- `X-Forwarded-For` es falseable, y la prueba lo usa para no gastar el
  límite de entradas. Es una propiedad del entorno de prueba.
- La telemetría da 403 con `CSRF_ENFORCE`; es previo.
- Con g saboteado, `test_cobro_corte1.py:577` no falla.
- z7 fue intermitente en ORDEN-1.

## Hallazgos de la revisión

| Fuente | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| `/code-review high` | Opus, alto | #1 y #2: con la sesión cerrada la escritura no iba al login, y «Salir» simulaba salir sin poder comprobar | Arreglados con su rojo antes: z25 y z26 (`ee27d5e`), arreglo en `91b25f2` |
| `/code-review high` | Opus, alto | #3: la falsa «Entró otro usuario» con la primera carga caída | Riesgo (baja) |
| `/code-review high` | Opus, alto | #4: no quedó registrado en mis notas y no lo recuperé | — |
| `/code-review high` | Opus, alto | #5: consultas duplicadas a `current_user` | Riesgo (baja) |
| `/code-review high` | Opus, alto | #6: que el servidor ate la escritura al token | Ya pasa con `CSRF_ENFORCE`; riesgo de Railway arriba |
| `/code-review high` | Opus, alto | #7: `irAlCheckout` tapa `ERROR_SIN_SESION` con su propio toast | Lo dejé: el mensaje se ve igual; es de COBRO |
| `/code-review high` | Opus, alto | #8: `confirmarSesion` puede arrancar la recuperación desde una escritura | Lo dejé: la recuperación respeta `adoptarTarde`, que no pisa una pestaña ocupada |
| `/code-review high` | Opus, alto | #9: la espera está duplicada | Arreglado: `consultarUsuario()` |
| Adversario | Sonnet, alto | La telemetría salía a nombre de B | Arreglado con su rojo antes: z27 (`267ef10`), arreglo en `68a2f37` |
| Adversario | Sonnet, alto | #5 a #8: «Comprobando…» pisa al aviso, Escape, el diálogo tarda en cockpit o clientes, la ventana de microsegundos | Riesgos de arriba. Escape: `cancel` hace `preventDefault`, así que no se cierra en Chromium; en otros navegadores no lo probé |
| Adversario | Sonnet, alto | Fuera del criterio: GET con datos de B, `CDI.currentUser`, `goToLegacy` borra `cdi_ui`, POST de sólo lectura | Riesgos (baja); `goToLegacy` es previo |
| `/security-review` | Opus, alto | Sin hallazgos con confianza ≥ 8 sobre `4ef59f4..6c459d2` | — |

## Archivos de producto tocados

- `proyecto_maria/static/v2/app_v2.js`
- `proyecto_maria/templates/dashboard_v2.html`
- `CHANGELOG.md`

## Puertas, sobre `6c459d2`

| Puerta | Salida |
|---|---|
| Suite completa (SQLite, worktree limpio, `--timeout=120`) | `4345 passed, 121 skipped, 3 xfailed in 673.65s`, salida 0 |
| `pantalla_orden1.js` completa (todos los casos), con `CSRF_ENFORCE=true` | 60 líneas `OK` (cierra con «OK: ORDEN-1 en el navegador»), ninguna `FALLA`, salida 0 |
| `scripts/testing/sabotajes/orden1b.sh` (lote) | 13 `ROJO`, 1 `ROJO?` (z23, D15), `sabotajes sin rojo: 1`, salida 1 |
| z23 saboteado, solo, 4 veces | rojo correcto 4 de 4; detalle en D15 |
| `scripts/testing/sabotajes/orden1.sh` | 76 `ROJO`, `sabotajes sin rojo: 0`, salida 0 |
| `ataque_aislamiento.sh` | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, «PUERTA G3 PASADA», salida 0 |
| `/code-review high` | 9 hallazgos, tabla de arriba; #1, #2 y #9 arreglados |
| `/security-review` | sin hallazgos ≥ 8 |

**El rojo antes** (`95643e3`, sobre el producto sin el freno):

- «FALLA: entró otro usuario y la pestaña de A generó enseguida y quedó una
  operación en la cuenta de B: 1 creadas, 1 cobradas»
- «FALLA: entró otro usuario y la pestaña de A guardó un cliente y el
  cliente quedó en la cuenta de B»
- «FALLA: con un servidor que no exige CSRF, entró otro usuario y la
  pestaña de A generó enseguida y quedó una operación en la cuenta de B: 1
  creadas, 1 cobradas»
- «FALLA: entró otro usuario y A apretó «Salir» en su pestaña y cerró la
  sesión de B (401; salió /auth/logout)»
- «FALLA: A volvió a entrar (otra sesión) mientras la duplicada miraba si
  la original vive y la duplicada no avisa que está comprobando la sesión»

z22 ya pasaba: es el caso de no bloquear de más.

**No corrí:**

- `smoke_friccion.sh`: no toqué el backend.
- `/code-review` y `/security-review` de nuevo sobre `629042d..6c459d2`:
  ese tramo son sólo pruebas.
- El diálogo y Escape en Firefox o Safari: sólo probé Chromium.

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout --detach origin/claude/dev-tecnica
# 1. Sabotajes de ORDEN-1b (levanta su propia API con CSRF_ENFORCE=true en el 8875):
#    14 ROJO y «sabotajes sin rojo: 0»; un ROJO? de z23 por «socket hang up» es D15
PY=python bash scripts/testing/sabotajes/orden1b.sh 6c459d2 | grep -E '^(ROJO|ROTO|VERDE)|sabotajes sin rojo'
# 2. Sabotajes de ORDEN-1 con los patrones nuevos (puerto 8853): «sabotajes sin rojo: 0»
PY=python bash scripts/testing/sabotajes/orden1.sh 6c459d2 | grep -E '^(ROTO|ROJO\?|VERDE)|sabotajes sin rojo'
```

## D15 (c) hecha en 3e30db2

`orden1b.sh` copia el log de la API y la salida de la pantalla de cada
`ROJO?` a una carpeta `orden1b-logs.XXXXXX` en `$TMPDIR` (o `/tmp`), que
sobrevive a la limpieza, y dice dónde quedó. Sin reintento. Un `ROTO` no
tiene log: el patrón falla antes de levantar la API, así que no hay nada
que guardar. Lo probé con una copia descartable que espera un texto falso
en el primer sabotaje de z20. Salida exacta:

```
ROJO? | la escritura sale sin preguntar quién es: rojo (salida 1), pero sin «texto que no aparece»
FALLA: entró otro usuario y la pestaña de A generó enseguida y quedó una operación en la cuenta de B: 1 creadas, 1 cobradas
      guardados: /tmp/orden1b-logs.k18eUD/1-api.log y /tmp/orden1b-logs.k18eUD/1-pantalla.log
sabotajes sin rojo: 1
```

Después del trap, `1-api.log` tenía 85 líneas y `1-pantalla.log`, 1. No
corrí la versión commiteada entera de punta a punta.

D16 (a): no toco el CSRF del logout. Sigo con D13 (c), sin entregarla
hasta tu veredicto de la vuelta 2.

/compact conservar: Dev 1, rama claude/dev-tecnica. ORDEN-1b entregada en
6c459d2 y COBRO-MP-1 vuelta 2 en revisión de la PM. D15 (c) hecha en
3e30db2; D16 (a), sin tocar. En curso: D13 (c) en COBRO-MP-1 (409 a una
authorized vieja en cuenta no vigente), sin entregar hasta el veredicto de
la vuelta 2; lo que pida ahí se suma a esta vuelta. Después CORTE-1, MP-2
(suma la cancelación de organizaciones), AIS2, LIM, BACKUP-1a y EXCEL-2c.
Nada se publica sin el «dale» de Emi; nunca main.
