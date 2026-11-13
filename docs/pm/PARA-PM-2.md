# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CUIT-PERFIL (D225): entregada en `af39604`. Reprodujo en rojo y está arreglada: «Mi perfil» ya no guarda un CUIT con el verificador mal. Una decisión: D235. Un rojo de puerta diagnosticado, que no era de la pieza y quedó arreglado en un commit aparte (`orden1`, caso z8)

Integré tu rama hasta `82a231f` (merge `07549dd`). Leí D227 (a), D234 (a)
con su «al día» de las 11:39 y el orden de las piezas. Tus commits propios
tocan sólo `docs/pm/`; lo de `tests/` y `scripts/` que llegó con el merge es
de la Técnica, ya aceptado por vos. Al subir encontré tu rama en `1de18f9` y
la integré (`af39604`): mi canal no cambió; trae documentos tuyos y
`tests/test_excel2d.py` de la Técnica. **Las puertas corrieron sobre
`b99ca0c`**; sobre `af39604`, que tiene el mismo producto y el mismo arnés
mío, corrí el pytest de la pieza y `test_excel2d.py`. Sigo con el lugar 2,
**SUFIJO-BORRADOR (D227)**.

| qué | SHA |
|---|---|
| base (mi informe anterior) | `fdaa2da` |
| los casos, rojos sobre el producto de hoy (pytest y pantalla) | `0dd23d7` |
| el arreglo (producto + `CHANGELOG.md`) | `31d14cf` |
| las cuatro pantallas a `_cuit_perfil.js`, dos pruebas viejas con un CUIT válido y el guion de sabotajes | `a988159` |
| del adversario: verificador 0 y 9 como datos, con su sabotaje | `dc84df3` |
| el guion de sabotajes cuenta sólo las líneas de resumen de pytest | `fd6e7ec` |
| de `/code-review`: la pantalla espera el cierre de «Mi perfil»; el guion apaga su API si lo cortan | `be046c8` |
| tu rama integrada, hasta `82a231f` | `07549dd` |
| la siembra del CUIT guardado sale del cuerpo de la pantalla (`chequeo-6`) | `92c43a8` |
| `orden1`, z8: suelta su ruta antes de cerrar. Sobre éste corrieron las puertas | `b99ca0c` |
| tu rama integrada, hasta `1de18f9`. **El que se entrega** | `af39604` |
| informe | el commit siguiente |

**Resultado.**

- **Reproduce.** Sobre `0dd23d7` (producto igual a `fdaa2da`):
  - pytest, `5 failed, 7 passed`:
    `test_lo_que_no_es_un_cuit_no_se_guarda[verificador equivocado]`,
    `[verificador equivocado, con guiones]`,
    `[verificador equivocado, de una empresa]`,
    `[d\xedgitos de ancho completo]` y
    `test_uno_malo_que_ya_estaba_guardado_queda_hasta_que_se_corrige`.
  - en un navegador, `pantalla_cuit_perfil1.js`:
    `FALLA: «Mi perfil» guardó 20-99999999-8, que tiene el verificador equivocado: el perfil quedó con «20999999998» (guardado)`
- **El arreglo es tu sugerencia:** `PUT /api/user/profile` llama a
  `cuit_valido` en lugar de contar 11 dígitos, y contesta 400 con «El CUIT no
  es válido: 11 dígitos, con o sin guiones, y el último es el verificador.».
  La pantalla no cambió: `profile.js` ya mostraba el `detail` del servidor
  debajo del campo y lo marcaba. Producto **+4/−3**, sólo
  `proyecto_maria/main.py`.
- Sobre el arreglo, la pantalla da:
  `OK con 20-99999999-8 escrito: error: El CUIT no es válido: 11 dígitos, con o sin guiones, y el último es el verificador.`,
  `OK 20-11111111-2 se guarda como 20111111112`,
  `OK con 20-99999999-8 ya guardado, al cambiar el nombre: error: El CUIT no es válido: …`,
  `OK corregido, se guarda con el nombre nuevo`, `PANTALLA CUIT-PERFIL-1 OK`.
- **Los perfiles que ya tienen uno inválido guardado** (no toqué ningún dato
  guardado ni hay migración):
  - el dato queda como está; `GET /api/user/profile` y «Mi perfil» lo
    muestran;
  - cualquier guardado desde «Mi perfil» da el error del CUIT hasta que se
    corrige o se borra, porque la pantalla manda siempre el campo. El nombre
    no se guarda mientras tanto (caso de pytest y de pantalla);
  - un `PUT` sin la clave `cuit` guarda lo demás (la pantalla no lo hace);
  - **la generación lo sigue usando**: `/generate_maria` sólo pide 11
    dígitos (`main.py:5164`). Eso es D235.
  - cuántos perfiles hay así en producción, no lo sé: no tengo acceso ni
    corresponde.
- **Las cuatro pantallas** (`orden1`, `validacion1`, `cobro_corte1`,
  `cobro_mp1_v2`) cargan el CUIT con `_cuit_perfil.js` (`20111111112`). Mandaban
  `20999999998`, que ahora el servidor rechaza. Dos pruebas viejas mandaban también un CUIT inválido al perfil y
  quedaron con uno válido: `test_generate_maria_usa_cuit_del_perfil` y
  `test_update_user_profile_cuit_valido`.
- **`31d14cf` solo no da verde**: esas dos pruebas quedan rojas hasta
  `a988159`, que es donde las corregí. Si alguien bisecta, que lo sepa.
- **Rojo de puerta, diagnosticado.** La primera corrida de las cinco
  pantallas, sobre `92c43a8`, dio `resumen: 4 verdes, 1 rojas: orden1`. No
  sale de mi cambio en ese archivo (líneas 78–113, el CUIT). Es una carrera
  del arnés que ya estaba: detalle en el supuesto 2. Lo arreglé en un commit
  aparte para que lo puedas sacar.

## Decisiones

**D235. La generación acepta un CUIT de despachante con el verificador
mal.** `/generate_maria` limpia guiones y espacios y pide `[0-9]{11}`
(`main.py:5161-5166`); no llama a `cuit_valido`. Vale para los tres orígenes
del CDDTAGR: el perfil, `cuit_agr` mandado en el pedido y el estudio (éste ya
se valida al crearlo, `main.py:7713-7715`). Con esta pieza no entra ninguno
nuevo por «Mi perfil», pero uno que ya esté guardado sigue saliendo en el
TXT, y `cuit_agr` nunca pasó por el control. Lo encontró `/code-review`; lo
confirmé leyendo el código, no generé un TXT. No sé qué hace el SIM con un
CDDTAGR así.

- (a) Pieza aparte: la generación rechaza el CUIT efectivo si no pasa
  `cuit_valido`, con el mismo mensaje. Toca la generación: revisión fuerte.
  El que tenga uno malo guardado no genera hasta corregirlo en «Mi perfil».
- (b) Queda como está, anotado como riesgo.
- (c) Primero contar en producción cuántos perfiles tienen uno inválido
  (una consulta de sólo lectura, que corre Emi), y después (a) o (b).

Recomiendo **(a)**: el control ya existe para el importador y para el
estudio, y el despachante es el único CUIT del TXT que sale sin él. Si
preferís saber antes a cuántos frena, (c) es barato.

**Próxima D libre: D236.**

## Supuestos (reversibles)

1. **Un perfil con CUIT inválido guardado no puede guardar nada desde «Mi
   perfil» hasta corregirlo o borrarlo.** La otra salida era dejar pasar el
   CUIT guardado si llega igual; la descarté porque así el malo se vuelve a
   confirmar en cada guardado. Tiene caso (`test_uno_malo_que_ya_estaba_…`)
   y sabotaje («uno malo ya guardado pasa si llega igual»).
2. **Arreglé z8 de `pantalla_orden1.js`, que no me pediste** (`b99ca0c`,
   sólo arnés, archivo mío). Evidencia:
   - puerta sobre `92c43a8`: `ROJA orden1 rc=1`, después de que z8 imprimió
     su `OK`: `TargetClosedError2: "route.fetch: Target page, context or
     browser has been closed" while running route callback.` Segunda corrida
     de `orden1` solo sobre el mismo SHA: `verde orden1 rc=0`. O sea 1 rojo
     en 2 corridas; la segunda la hice para ver los casos que vienen después
     de z8, no para tapar el rojo.
   - causa: la pestaña a veces manda otro `GET /auth/current_user` al final
     del caso (lo vi en 8 de 24 corridas de z8 solo); entra a la ruta de z8 y
     su `ruta.fetch` queda cortado cuando el caso cierra el contexto.
   - z8 solo, instrumentado: 2 rojos de 10 en `fdaa2da` (antes de mi pieza) y
     1 de 14 en `92c43a8`.
   - forzado (una consulta tardía retenida hasta el cierre): 3 de 3 en rojo
     con el mismo error sobre `92c43a8`; 3 de 3 en verde sobre `b99ca0c`.
   - el arreglo: el caso quita su ruta antes de cerrar
     (`cerrarConRutas`, 4 líneas fuera de la función larga).
   - **no determiné qué código del producto manda esa consulta tardía**, ni
     miré el otro `ruta.fetch` sin `catch` del archivo (línea 1668), que no
     dio rojo.
3. **Mensaje del 400 propio del perfil**, calcado del de estudios sin «del
   estudio».
4. **Dos datos más en el caso de los buenos** (`20111111120`, verificador 0,
   y `20111111189`, resto 1 → 9), pedidos por el adversario. El segundo lo
   acepta `cuit_valido` como está hoy; ARCA no emite CUIT de resto 1. No
   toqué `cuit_valido`: lo comparten estudios e importador.

## Para reproducir

```bash
# el rojo, sobre el producto de hoy: «5 failed, 7 passed»
git worktree add /tmp/cp-rojo 0dd23d7 && cd /tmp/cp-rojo
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_cuit_perfil.py
# la pantalla sobre el mismo SHA: «ROJA cuit_perfil1», con «FALLA: «Mi perfil» guardó 20-99999999-8 …»
SOLO=cuit_perfil1 bash scripts/testing/correr_pantallas.sh 0dd23d7 /tmp/cp-rojo-pant

# el verde, sobre lo que se entrega
cd <repo en b99ca0c>
python -m pytest -q --no-cov tests/test_cuit_perfil.py tests/test_generar_maria_txt.py tests/test_user_profile_coverage.py   # «88 passed»
SOLO="cuit_perfil1 orden1 validacion1 cobro_corte1 cobro_mp1_v2" bash scripts/testing/correr_pantallas.sh b99ca0c /tmp/cp-pant   # «resumen: 5 verdes, 0 rojas» (~11 min)
bash scripts/testing/sabotajes/cuit_perfil.sh b99ca0c   # 11 «ROJO», «sabotajes sin rojo: 0» (~2 min)
```

## Puertas, sobre `b99ca0c` (la última fila, sobre `af39604`)

| puerta | salida |
|---|---|
| cinco pantallas (`correr_pantallas.sh`) | `verde cobro_corte1 rc=0`, `verde cobro_mp1_v2 rc=0`, `verde cuit_perfil1 rc=0`, `verde orden1 rc=0`, `verde validacion1 rc=0`; `resumen: 5 verdes, 0 rojas` (12:30→12:41 UTC). Antes, sobre `92c43a8`: `resumen: 4 verdes, 1 rojas: orden1` (supuesto 2) |
| `sabotajes/cuit_perfil.sh` | `BASE` verde (`14 passed` y `PANTALLA CUIT-PERFIL-1 OK`), 11 `ROJO`, `sabotajes sin rojo: 0`, sale 0 |
| pytest de la pieza (3 archivos) | `88 passed, 15 warnings in 16.47s`, sale 0 |
| `compileall -q proyecto_maria` | sin salida, sale 0 |
| `smoke_friccion.sh` | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, sale 0 |
| `ataque_aislamiento.sh` | 47 `OK`, ningún `FUGA` ni `SIN PROBAR`; `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.`, sale 0 (levanta su propio Postgres descartable) |
| `pytest` entero | `6126 passed, 110 skipped, 3 xfailed, 105 warnings in 1317.83s (0:21:57)`, sale 0 (12:44→13:06 UTC). `tests/test_excel2d.py` verde: el rojo de D234 no apareció |
| `anclas_perdidas.py` (con HEAD en `b99ca0c`) | `revisión HEAD: 102 guiones, 2463 anclas medidas y 11 llamadas sin medir`, sale 0. Las perdidas y las «sin ancla» son, línea por línea, las mismas que en `fdaa2da` (101 guiones, 2452 anclas): ninguna es de esta pieza. Las 11 anclas de `cuit_perfil.sh` están |
| sobre `af39604`: pytest de la pieza (3 archivos) y `tests/test_excel2d.py` | `114 passed, 15 warnings in 21.01s`, sale 0 |

Los once sabotajes y lo que dice cada rojo:

```
BASE  | casos: 14 passed, 5 warnings in 9.72s
BASE  | pantalla: PANTALLA CUIT-PERFIL-1 OK
ROJO  | sólo se cuentan los dígitos: «verificador equivocado: 200», 5 casos
ROJO  | no se mira nada: «diez dígitos: 200», 7 casos
ROJO  | el rechazo deja guardado el resto del pedido: «el pedido rechazado no deja nada guardado», 7 casos
ROJO  | uno malo ya guardado pasa si llega igual: «Con el malo», 1 casos
ROJO  | se guarda como llegó: «'20-11111111-2' == '20111111112'», 4 casos
ROJO  | el vacío no lo borra: «'20111111112' == ''», 1 casos
ROJO  | el verificador sale siempre de «11 − resto»: «assert 400 == 200», 2 casos
ROJO  | el servidor sólo cuenta los dígitos: «FALLA: «Mi perfil» guardó 20-99999999-8, que tiene el verificador equivocado»
ROJO  | la pantalla no dice lo que contestó el servidor: «FALLA: con 20-99999999-8 escrito terminó en «error: No se pudo guardar» y no en el error del CUIT»
ROJO  | el campo no queda marcado: «FALLA: el campo del CUIT no queda marcado»
ROJO  | el que ya estaba guardado no se muestra: «FALLA: con 20-99999999-8 ya guardado, el campo muestra «»»
sabotajes sin rojo: 0
```

Archivos de producto tocados: `proyecto_maria/main.py` (sólo
`update_user_profile`) y `CHANGELOG.md`.

## chequeo-6

```
chequeo-6 fdaa2da..af39604: avisos para mirar, no un veredicto
producto +4/−3
arnés +375/−25
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12270 → 12271
avisos: 0
```

El `arnés` incluye lo que llegó con tu rama en `07549dd` y `af39604` (de la Técnica:
`correr_pantallas.sh`, `conftest.py`, `test_conftest_fork.py`,
`test_excel2d.py`, tres pantallas suyas y `sabotajes/cliente1.sh`). Sobre
`da0adc5`, que tenía el cierre de z8 dentro de la función larga de `orden1`,
daba `AVISO creció una función de más de 150 … 1584 → 1586`: lo saqué a
`cerrarConRutas` y rehice ese commit, que no estaba subido.

## Hallazgos de la autorrevisión

Los subagentes miraron la pieza hasta `a988159` (el adversario) y hasta
`fd6e7ec` (`/code-review`). **`be046c8`, `92c43a8` y `b99ca0c`, que son sólo
arnés, los revisé yo sola.**

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` | Sonnet, alto | Media: todos los CUIT de los casos tenían un verificador que sale de «11 − resto»; con `cuit_valido` roto para resto 0 y resto 1 seguían en verde | Reproducido. Dos datos y un sabotaje más, `dc84df3` |
| `adversario-sonnet-alto` | Sonnet, alto | Baja, de antes de la pieza | No conservé el texto; no lo toqué. No lo doy por cerrado |
| `adversario-sonnet-alto` | Sonnet, alto | Baja: no llegó a correr `pantalla_orden1.js` (se le fue el tiempo a los 280 s) | La corrí yo: es la puerta de arriba |
| `adversario-sonnet-alto` | Sonnet, alto | No rompió: 4200 CUIT válidos al azar se guardan; un pedido rechazado no deja nada guardado (sólo SQLite); la pantalla a 1280×720 y 360×640 | — |
| `/code-review high` | revisores en Fable (heredado), alto | 1. La generación no llama a `cuit_valido` | **D235** |
| `/code-review high` | ídem | 2. `abrir()` de la pantalla nueva reabría «Mi perfil» mientras se cerraba | Confirmado (entre 125 y 128 ms queda con `is-open` y `hidden`). Arreglado en el arnés, `be046c8`. En el producto es un parpadeo si alguien reabre en ese instante: línea propuesta para la cola, baja |
| `/code-review high` | ídem | 3. El perfil saca todo lo que no es dígito antes de validar; el estudio sólo guiones y espacios | No lo cambié (no es la tarea). Línea propuesta para la cola |
| `/code-review high` | ídem | 4. `cuit_perfil.sh`: `API=$!` quedaba en un subshell y, cortado a mitad, la API seguía viva | Confirmado en rojo. Arreglado, `be046c8` |
| `/code-review high` | ídem | 5. `31d14cf` solo deja dos pruebas rojas | Cierto; dicho arriba |
| `/code-review high` | ídem | 6. Un `cuit` JSON «falso» (`0`, `false`, `[]`) borra el CUIT; texto sin dígitos da el error del CUIT | De antes de la pieza, baja. No lo toqué |
| `/code-review high` | ídem | 7. `20111111189` (resto 1) pasa `cuit_valido` | Supuesto 4 |
| `/code-review high` | ídem | 8. `profile.js` sólo cuenta 11 dígitos antes de mandar | El servidor decide y la pantalla muestra su error. Línea propuesta para la cola |
| `/code-review high` | ídem | 9. `cuit_perfil.sh` arma su propio entorno en vez de usar `sabotajes/_entorno_comun.sh` | Línea propuesta para la cola |
| `/code-review high` | ídem | 10. Las listas esperadas del guion usan los ids escapados de pytest (`d\xedgitos`) | Queda: si cambia, el guion falla fuerte, no en silencio |
| `/security-review` | yo, sobre el diff de producto | Sin hallazgos | — |

Líneas que propongo para `COLA-LIMPIEZA.md` (no la toqué):

- «Mi perfil» reabierto a ~125 ms de cerrarlo queda con `is-open` y
  `hidden`. Baja.
- El perfil y el alta de estudio limpian el CUIT distinto antes de validar
  (`main.py:2434` y `:7714`): una sola limpieza.
- `profile.js:213` cuenta 11 dígitos; el verificador lo mira sólo el
  servidor.
- `sabotajes/cuit_perfil.sh` sobre `_entorno_comun.sh`.

## Qué no corrí y riesgos

No corrí:

- **Sobre `af39604`**, nada más que el pytest de la pieza y
  `test_excel2d.py`. Pantallas, sabotajes, `smoke`, ataque y `pytest` entero
  son de `b99ca0c`; entre los dos sólo cambian documentos y
  `tests/test_excel2d.py` (`git diff --stat b99ca0c af39604`).
- **Postgres**, fuera de `ataque_aislamiento.sh` (que levanta el suyo). Los
  casos de la pieza corren sobre SQLite; «un pedido rechazado no deja nada
  guardado» está probado sólo ahí.
- **`e2e_maria.sh`**: la pieza no toca el recorrido MARIA ni `static/v2`.
- **El corredor de pantallas entero**: sólo las cinco pantallas de la pieza.
- **Un TXT generado con un CUIT inválido** (D235): lo leí en el código.
- **Nada contra producción.** No sé cuántos perfiles tienen hoy un CUIT
  inválido guardado.
- Los subagentes no vieron `be046c8`, `92c43a8` ni `b99ca0c` (sólo arnés).
- Las corridas instrumentadas y forzadas de z8 fueron sobre copias del
  archivo fuera del repositorio; en el repositorio no queda ningún guion que
  fuerce esa carrera. Si la querés como caso, es otra pieza.

Riesgos:

- **El que tiene un CUIT inválido guardado** se encuentra con el error la
  próxima vez que guarde cualquier cosa en «Mi perfil» (supuesto 1), y hasta
  entonces sigue generando con ese CUIT (D235).
- **z8** (supuesto 2): arreglé el efecto en el arnés. Qué parte del producto
  manda el `GET /auth/current_user` tardío no lo determiné; el otro
  `ruta.fetch` sin `catch` (línea 1668) puede tener la misma carrera y no lo
  toqué porque no dio rojo.
- `20111111189` (resto 1) pasa `cuit_valido` (supuesto 4).
- Con un caso que falla después de un 400, el log capturado de pytest trae
  `ERROR sqlalchemy.pool.impl.NullPool … Exception closing connection`: sale
  del cliente de prueba con aiosqlite, no lo vi con el servidor levantado
  (`smoke`, pantallas). No lo investigué más.
- El hallazgo «baja, de antes de la pieza» del adversario quedó sin texto en
  mi informe (tabla de arriba): no lo puedo dar por cerrado.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, canal PARA-DEV-2.md / PARA-PM-2.md, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, integrada hasta 1de18f9). CUIT-PERFIL (D225) entregada en af39604 (puertas sobre b99ca0c), espera veredicto; D235 abierta (la generación no valida el verificador del CUIT del despachante). Sigue SUFIJO-BORRADOR (D227): caso de pantalla en rojo primero, corre e2e_maria.sh, y los dos campos como datos en test_lo_que_se_esta_escribiendo_no_se_pisa. Después, los vencidos de sabotajes-conocidos.txt, uno por pieza. Próxima D libre: D236. Reglas: nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sin consejero, subagentes hasta esfuerzo alto, timbre con send_message priority next.
