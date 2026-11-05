# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CSRF-1 vuelta 2, entregada en `9e37673` (informe en el commit de arriba)

**Resultado.** Un POST a `/auth/logout` o `/logout` que llega sin la cookie
de sesión ya no borra nada. Así llega un `<form>` de otro sitio. Vale con
`CSRF_ENFORCE` en `true` y en `false`. Con la cookie de sesión, el middleware
sigue pidiendo el token, como en la vuelta 1. «Salir» lleva al inicio sólo si
el cierre se confirmó. Si el servidor lo rechaza o el pedido no sale, avisa y
queda en la página. Si no pudo comprobar de quién es la sesión, el aviso lo
dice. Producto de la vuelta `+12/−12`, en `main.py` y `app_v2.js`.

**Cambié de enfoque dentro de la vuelta.** Primero (`965b990`/`44b966f`)
hice que el middleware pidiera el token en las dos rutas de cierre aunque no
llegara la cookie. Mi `/code-review high` lo objetó y lo descarté:

- en modo reporte (`false`, lo de dev/test) el ataque seguía, porque el
  middleware sólo registra en el log;
- el cierre con Bearer daba 403;
- el adversario mostró que con `root_path` el middleware no reconoce la ruta
  y el cierre pasa sin token.

Ahora el chequeo está en el endpoint: si no llegó `access_token`, no hay
sesión que cerrar y responde 200 sin `Set-Cookie`. No depende de enforce ni
de la ruta. Probé `root_path="/pfx"` con `TestClient`: las dos rutas dan
`200 set-cookie: None`.

### Decisiones

Nada nuevo para decidir. Un supuesto reversible:

- **El alias `/logout` ahora delega en `/auth/logout`, así que también borra
  `csrf_token`.** Eso adelanta un ítem de CSRF-2 (D56 b). Lo hice porque si
  no, el chequeo nuevo quedaba repetido en los dos handlers (§6). Si lo
  querés en CSRF-2, se revierte volviendo al handler propio con el mismo
  `if`.

### SHAs (desde `16d3a61`, tu merge)

| SHA | Qué |
|---|---|
| `965b990` | test, enfoque descartado: el caso del pedido sin cookies; la fase de `pantalla_csrf1.js` con el pedido cortado (`route.abort`); sabotajes 6 y 7 |
| `44b966f` | fix, enfoque descartado: el middleware pedía el token a las rutas de cierre sin cookie; «Salir» sin red no navega |
| `252abaa` | test: `test_logout_desde_otro_sitio_no_borra_la_sesion`, parametrizado por ruta y por enforce, reemplaza al de `965b990`; `test_security.py:647` dice algo cierto; sale el chequeo `abierta` de la pantalla, que no podía fallar; sabotaje 6 nuevo y 8 |
| `78cf716` | fix: el endpoint borra sólo si llegó la cookie de sesión; el alias delega; aviso neutro en «Salir»; `CHANGELOG.md` |
| `b9910f4` | fix: sale `if (sesionAjena) return;` de `logout()`, que ya no cambiaba nada (abajo, «ORDEN-1b sobre `78cf716`») |
| `fa954e9` | test: los sabotajes z24 y z26 de `orden1b.sh` se reanclan al `if` de `'unauthorized'` |
| `cc66150` | fix: el motivo propio del aviso queda sólo para `ERROR_SIN_SESION`; con `ERROR_AJENA` el modal tapa el aviso |
| `c4df110` | test: z26 pide que el aviso diga «No se pudo comprobar la sesión»; sabotaje nuevo que pone el motivo genérico |
| `9e37673` | test: z26 mira título y motivo en la misma aserción, para no sumar una rama a una función de más de 150 líneas (aviso de chequeo-6 sobre `c4df110`) |
| (este) | docs: informe |

### Rojos antes

El caso nuevo, copiado sobre el producto de `b1c9d70`:

```
FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/auth/logout-true]
FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/auth/logout-false]
FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/logout-true]
FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/logout-false]
=================== 4 failed, 11 passed, 5 warnings in 4.84s ===================
```

Sobre el producto de `44b966f`, el enfoque descartado, también
`4 failed, 11 passed`. En `true` falla por el 403
(`"code":"csrf_failed"`); en `false`, porque borra.

`pantalla_csrf1.js` de `78cf716` contra una API de `b1c9d70` con
`CSRF_ENFORCE=true`:

```
FALLA: «Salir» sin red no avisó y la página fue a /
```

### ORDEN-1b sobre `78cf716`

`orden1b.sh 78cf716` dio `sabotajes sin rojo: 2`, salida 1:

```
VERDE | salir con la sesión de otro deja la pestaña y va al inicio: la prueba no lo vio
ROTO  | salir sin poder comprobar quién es va al inicio: el sabotaje no encontró su patrón
```

- **El VERDE.** Desde `78cf716`, cualquier error que no sea 401 deja la
  pestaña en su lugar. El `if (sesionAjena) return;` que el sabotaje sacaba
  ya no cambiaba nada. Saqué esa línea (`b9910f4`) y el sabotaje ahora deja
  pasar `ERROR_AJENA` por la rama del 401 (`fa954e9`).
- **El ROTO.** El patrón era la rama propia de `ERROR_SIN_SESION`, que
  `78cf716` unió a la general. Se reancló al mismo `if` (`fa954e9`).

Sobre `9e37673`: base en verde, 29 ROJO, ningún VERDE ni ROTO, «sabotajes sin rojo: 0», salida 0.

El aviso con el motivo no tenía prueba. Con `fa954e9`, z26 pasaba igual con
el motivo genérico. El sabotaje nuevo de `c4df110` pone ese motivo y da:

```
ROJO  | salir sin poder comprobar quién es no dice por qué: dice «FALLA: A volvió a entrar y apretó «Salir» sin poder comprobar quién es y no avisa que no pudo comprobar la sesión»
```

### `test_security.py:647`

El cliente guarda las cookies del login y no manda `X-CSRF-Token`, así que
con enforce ese `/logout` da 403. El docstring ahora dice «Muestra si el JWT
sigue sirviendo después de cerrar sesión: es stateless.», y un comentario
explica el 403. La clase `TestAuthenticationFailures` sigue salteada entera,
como antes.

### Sabotajes (`csrf1.sh 9e37673`)

```
ROJO  | cerrar sesión vuelve a estar exento: dice «FAILED tests/test_csrf.py::test_enforce_pide_token_a_logout_y_telemetria[/auth/logout-False-403]»
ROJO  | la telemetría se exenta en vez de mandar el token: dice «FAILED tests/test_csrf.py::test_enforce_pide_token_a_logout_y_telemetria[/api/session/state-False-403]»
ROJO  | la telemetría de la página sale sin el token: dice «FALLA: la telemetría de la página dio 403»
ROJO  | «Salir» sale sin el token: dice «FALLA: «Salir» no llevó al inicio»
ROJO  | «Salir» rechazado lleva al inicio igual: dice «FALLA: «Salir» rechazado no avisó y la página fue a /»
ROJO  | cerrar sesión borra las cookies aunque no llegue la de sesión: dice «FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/auth/logout-false]»
ROJO  | el alias borra la cookie por su cuenta: dice «FAILED tests/test_csrf.py::test_logout_desde_otro_sitio_no_borra_la_sesion[/logout-false]»
ROJO  | «Salir» sin red lleva al inicio igual: dice «FALLA: «Salir» sin red no avisó y la página fue a /»
sabotajes con falla: 0
salida 0
```

### Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| `csrf1.sh` | `9e37673` | dos bases en verde, 8 ROJO con su texto, «sabotajes con falla: 0», salida 0. Igual que sobre `78cf716` |
| Suite completa, worktree limpio | `9e37673` | `4427 passed, 121 skipped, 3 xfailed, 100 warnings in 632.53s (0:10:32)`, salida 0 |
| `orden1.sh` (usa `salir()` de `pantalla_orden1.js`) | `9e37673` | bases en verde, 76 ROJO, «sabotajes sin rojo: 0», salida 0 |
| `orden1b.sh` | `9e37673` | base en verde, 29 ROJO, «sabotajes sin rojo: 0», salida 0 |
| `test_csrf` + `test_prelaunch_block1`, con `CSRF_ENFORCE` en `true` y en `false` | `9e37673` | `59 passed, 3 warnings` las dos |
| `smoke_friccion.sh`, API con `CSRF_ENFORCE=true` | `78cf716` | `==> OK · telemetría + alias session/state + by-cuit protegido`, salida 0. Después de `78cf716` sólo cambiaron `app_v2.js` y el arnés |
| `compileall -q proyecto_maria` | `9e37673` | salida 0 |
| chequeo-6 `885ee89..9e37673` y `b14e10c..9e37673` | `9e37673` | 0 avisos, abajo. Sobre `c4df110` dio uno, arreglado en `9e37673` |
| Historia (grep de §6) | `9e37673` | vacío |

Sólo Chromium. No corrí `ataque_aislamiento.sh`: la vuelta toca el cierre
de sesión y el botón, no clientes ni descargas.

### chequeo-6

Desde la base de la pieza:

```
chequeo-6 885ee89..9e37673: avisos para mirar, no un veredicto
producto +18/−15
arnés +207/−13
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11307 → 11307
  proyecto_maria/static/v2/app_v2.js: 1199 → 1202
avisos: 0
```

Esta vuelta:

```
chequeo-6 b14e10c..9e37673: avisos para mirar, no un veredicto
producto +12/−12
arnés +39/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11306 → 11307
  proyecto_maria/static/v2/app_v2.js: 1203 → 1202
avisos: 0
```

Sobre `c4df110` dio `AVISO: creció una función de más de 150:
scripts/testing/pantalla_orden1.js:282 <anónima> 1584 → 1586`. En
`9e37673` las dos aserciones nuevas de z26 van en el `if` que ya estaba.

### Revisiones

| Quién | Modelo y esfuerzo | Sobre | Hallazgo | Qué hice |
|---|---|---|---|---|
| `/code-review high` | esta sesión, alto | `16d3a61..44b966f` | 1. El `/logout` de v1 sin cookie daba 403 | Lo resuelve el enfoque nuevo. v1 con cookie sigue sin token: CSRF-2 (D56 b) |
| | | | 2. Cerrar sesión con Bearer daba 403 | Resuelto: sin cookie, 200 sin borrar |
| | | | 3. El arreglo iba en el middleware y no en el endpoint | Aplicado en `78cf716` |
| | | | 4. El aviso «No hubo respuesta del servidor» salía ante cualquier error | Texto neutro: «El cierre no se confirmó. La sesión sigue abierta.» |
| | | | 5. Los dos handlers divergían | El alias delega |
| | | | 6. El chequeo `abierta` de la pantalla no podía fallar | Sacado |
| | | | 7. La aserción del `Set-Cookie` ya la implicaba el 403 | El caso pide 200 sin borrado, con enforce en `true` y en `false` |
| | | | 8. `test_security` no afirmaba nada cierto | Docstring y comentario corregidos. La clase sigue salteada |
| `adversario-sonnet-alto` | Sonnet, alto | `44b966f` | 1. Media, condicional: con `root_path` el middleware no reconoce la ruta y el cierre pasa sin token (lo reprodujo con `--root-path /pfx`) | No aplica a `78cf716`: el chequeo no mira la ruta. Con `root_path="/pfx"`, `200 set-cookie: None` en las dos |
| | | | 2. Baja, ya existía: sin cookie `csrf_token`, «Salir» avisa y no cierra; un login nuevo la repone | D57 (a) |
| | | | 3. Baja: un 402 abre el modal de pago además del aviso; un pedido colgado no tiene timeout y el botón no hace nada | El texto del aviso ya es neutro. El 402 no es alcanzable: el cierre no cobra. El timeout queda como riesgo |
| | | | 4. Baja, sólo leído: `?v=1` fija la pantalla vieja con una cookie `lax` desde un enlace de otro sitio | No toca `access_token`. El cierre de la pantalla vieja es CSRF-2 |
| | | | 5. Baja: ninguna prueba cubre la rama `'unauthorized'` de `logout()` | Queda: con la sesión vencida `irAlLogin()` ya navega, así que el sabotaje casi no cambia nada |
| | | | Un `<form>` real desde otro sitio, por cinco rutas, no cerró la sesión. Métodos, codificaciones y variantes de ruta: 403, 404 o 405 | — |
| `/code-review high` | esta sesión, alto | `78cf716..fa954e9` | 1. Un 401 durante «Salir» lleva a `/` y pisa el `/?next=` que armó `irAlLogin()` | Ya pasaba antes. Riesgo bajo, abajo |
| | | | 2. Con `ERROR_AJENA` en la lista del motivo, el aviso sale debajo del modal y no se ve | Vuelve a la ternaria en `cc66150` |
| | | | 3. El motivo «No se pudo comprobar la sesión» no tenía prueba | z26 lo pide y suma su sabotaje en `c4df110` |
| | | | 5. Igual que el 1, por otro camino | Riesgo bajo |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `16d3a61..78cf716` | «Sin hallazgos». Leyó el código, no corrió `TestClient` | Comprobé lo que da por cierto: las cookies de sesión salen con `samesite="strict"` (`main.py:2890`, `3183`, `3241`, `9918`) |

### Riesgos

- **Bajo, D57 (a).** Sin la cookie `csrf_token`, «Salir» avisa y no cierra.
- **Bajo.** Si el pedido de cierre queda colgado, «Salir» no hace nada
  hasta que el navegador lo corte. No hay timeout en `api()`.
- **Bajo, CSRF-2.** Con enforce, el «Salir» de la pantalla vieja (con
  cookie) y la telemetría de la landing (con sesión) siguen dando 403.
- Una cookie `csrf_token` que llega sin `access_token` no se borra. No da
  acceso a nada.
- **Bajo, ya pasaba.** Si el servidor contesta 401 durante «Salir», la
  página va a `/` y pierde el `/?next=`. No hay sesión abierta que proteger.
- `CSRF_ENFORCE` sigue como esté en Railway. Esta pieza no lo prende.

### Comandos para reproducir

```bash
# 1. Sabotajes: dos bases en verde, 8 ROJO, «sabotajes con falla: 0»
PY=venv/bin/python scripts/testing/sabotajes/csrf1.sh 9e37673
# 2. Salir con la sesión de otro o sin poder comprobarla: base en verde, 29 ROJO, «sabotajes sin rojo: 0»
PY=venv/bin/python scripts/testing/sabotajes/orden1b.sh 9e37673
# 3. El caso, con y sin enforce: 15 passed las dos
CSRF_ENFORCE=true  python -m pytest -q --no-cov tests/test_csrf.py
CSRF_ENFORCE=false python -m pytest -q --no-cov tests/test_csrf.py
# 4. Números de §6: 0 avisos
python docs/pm/herramientas/chequeo-6.py b14e10c 9e37673
```

### Archivos de producto tocados

`proyecto_maria/main.py` y `proyecto_maria/static/v2/app_v2.js` (y
`CHANGELOG.md`).

---

/compact conservar: Dev 1, rama claude/dev-tecnica. CSRF-1 vuelta 2 entregada en
9e37673 (informe en el commit de arriba), sin decisiones nuevas; el alias que
borra csrf_token es un supuesto reversible. COBRO-MP-1 vuelta 5 aceptada.
Sigue CSRF-2, en tu orden. Nada se publica sin el «dale» de Emi; nunca main.
