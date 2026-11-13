# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SUFIJO-BORRADOR, vuelta de la devolución con D236 (b): entregada en `52f13ca`. Una operación sin sufijo ya no genera con el de la anterior: el campo entra vacío, la tarjeta del despachante no usa el ajeno y «Generar» frena sin pedir el TXT. Una decisión: D238 (el aviso «Es obligatorio» queda a la vista de una operación a otra)

Integré tu rama hasta `de4d121` (merge `c18039c`). Tus commits propios tocan
sólo `docs/pm/`; los de `tests/` que llegan son de la Técnica. Encima va un
commit más, `52f13ca`: corrige un comentario mío de `92f4ec1` que quedó falso
con `a0acbe7` (decía que «Generar» toma el sufijo del campo).

Antes del informe integré otra vez tu rama, hasta `6e4a427` (`1163424`):
`git diff --stat 52f13ca 1163424` da sólo `docs/pm/NOW.md`, que ningún test ni
guion de las puertas lee. Las puertas son sobre `52f13ca` y no las repetí
sobre esa integración. Mi canal no cambió.

**Una puerta en rojo:** en la corrida entera de pantallas, `orden1` cayó en
z22 con la carrera de D237. Diagnóstico y segunda corrida, abajo.

| qué | SHA |
|---|---|
| base (integración de tu rama hasta `32dfcd5`) | `0d4cd72` |
| producto: el campo muestra el sufijo de la operación en curso, vacío si no tiene (+ `CHANGELOG.md`) | `92f4ec1` |
| el caso, primera versión | `bcb3e9c` |
| producto: «Generar» toma el sufijo de la operación, no del campo | `a0acbe7` |
| el caso mira la tarjeta del despachante y que el freno sea de ese clic | `a0c1c69` |
| el caso, partido en dos funciones (mismas comprobaciones) | `ebbe181` |
| integración de tu rama hasta `de4d121` | `c18039c` |
| producto, sólo un comentario: quién lee el campo. **Lo que se entrega** | `52f13ca` |
| integración de tu rama hasta `6e4a427` (sólo cambia `docs/pm/NOW.md`) | `1163424` |
| informe | el commit siguiente |

**Tu objeción era correcta.** Escribí que la herencia «venía de antes y no la
cambié», y la entrega le sumaba un camino: recuperar A, «Nueva operación», B
sin sufijo, «Generar». Lo reproduje antes de tocar nada: con el caso nuevo
sobre `ee2ee3c` (commit descartable `b1e5cdb`) las tres llegadas dan
`«Generar» siguió a «ready» y salieron 1 POST /generate_maria`.

**Dos cosas que subí y no son entrega.**
- CUIT-GENERAR ya estaba subida (`64079aa`, `bb01070`, `4b42b42`, `f249547`)
  cuando leí «apartalo». La aparté con dos reversiones, `3a6f656` (producto) y
  `2f04637` (pruebas), las dos antes de la base `0d4cd72`:
  `git diff 765db40 2f04637 -- proyecto_maria scripts tests CHANGELOG.md` da
  vacío. Se recupera revirtiendo esas dos.
- `a0c1c69` quedó en el remoto antes de las puertas (para no perder el trabajo
  del contenedor). Las puertas de abajo son todas sobre `52f13ca`.

## Decisiones

**D238. El aviso «Ingresá el sufijo de valor SBT. Es obligatorio.» queda a la
vista de una operación a otra.** Venía de antes; no lo toqué. `#sbtFieldError`
sólo se esconde cuando «Generar» pasa. Medido con una sonda (commit
descartable `15893f6`, salida en el bloque de comandos): después de que A
frena, B entra con su sufijo guardado en el campo **y el aviso a la vista**; y
en una operación sin sufijo el aviso sigue ahí después de escribirlo, hasta
tocar «Generar».
- (a) pieza chica aparte: el aviso se esconde cuando se escribe en el campo y
  cuando se entra a «Validación» con otra operación;
- (b) dejarlo.

Recomiendo **(a)**, aparte: con D236 (b) el campo entra vacío más seguido y un
aviso rojo de otra operación al lado confunde. No lo metí acá porque no es la
causa de la devolución, y esconderlo siempre al entrar rompe el camino del
error del servidor, que pone el aviso y vuelve a «Validación».

## Resultado

Lo pedido, y dónde se prueba (`scripts/testing/pantalla_sufijo_otra1.js`):

| pedido | cómo lo prueba el caso |
|---|---|
| al entrar a «Validación» el campo muestra el sufijo de la operación en curso, vacío si no tiene | lee campo y operación en el mismo instante de entrar; con la anterior recuperada, exige antes que haya vuelto con `AA(000123)` en los dos |
| una B sin sufijo no genera | cuenta los `POST /generate_maria` y exige el aviso con el foco en el campo, que lo pone el freno de ese clic (en dos llegadas el aviso ya estaba a la vista desde la anterior: D238) |
| avisos, tarjeta del despachante y TXT usan el mismo valor | B lleva un segundo producto con sufijo escrito cuando la operación no tenía ninguno: la tarjeta lo marca «Lo escribiste con otro sufijo de la operación» sólo si compara contra uno ajeno. Con `AA(000456)` escrito, los avisos se piden con ese y todos los `CSBTSVL` del TXT son ese |

La familia va como datos de un caso: después de recuperar la anterior, sin
recargar, y con el sufijo borrado (`sbt_sufijo_valor: ''`).

**Producto +5/−11** (`finalize.js`, 1494 → 1488 líneas). Dos cambios:
- `pintarSufijo` pinta siempre lo que guarda la operación, vacío si no guarda
  nada (`92f4ec1`);
- «Generar» ya no copia el campo a la operación: el control de «Es
  obligatorio» lee la operación, igual que los avisos y el TXT (`a0acbe7`). Era
  la copia por la que el sufijo ajeno llegaba al TXT.

`CHANGELOG.md`: una entrada (`92f4ec1`), que cubre los dos commits de
producto; dice también que quien carga varias operaciones seguidas escribe el
sufijo en cada una.

**Rojos, cada uno un commit descartable sobre el caso final** (salidas copiadas
del log; las tres llegadas dicen lo mismo en cada uno):

| qué se le saca al producto | SHA | qué dice el caso |
|---|---|---|
| todo: `finalize.js` de la primera entrega | `3e1f90d` | `al entrar, campo / operación / tarjeta = «AA(000123) /  / lo marca escrito con otro sufijo»; «Generar» siguió a «ready» y salieron 1 POST /generate_maria` |
| el orden: pintar el campo después de la tarjeta | `740b38a` | `al entrar, campo / operación / tarjeta = « /  / lo marca escrito con otro sufijo»; «Generar» frenó y salieron 0 POST /generate_maria` |
| sólo el pintado (vuelve el «pinta si hay») | `8a9a8f6` | `al entrar, campo / operación / tarjeta = «AA(000123) /  / lo marca escrito con otro sufijo»; «Generar» frenó y salieron 0 POST /generate_maria` |
| sólo el freno de «Es obligatorio» | `8e6b598` | `al entrar, campo / operación / tarjeta = « /  / sin marca»; «Generar» siguió a «ready» y salieron 1 POST /generate_maria` |

Los tres últimos corrieron con el caso de `a0c1c69`; `ebbe181` sólo saca dos
funciones del recorrido, y el primero se volvió a correr sobre `52f13ca`.

El tercero muestra para qué sirve sacar la copia: con el pintado viejo de
vuelta, el campo muestra el ajeno pero «Generar» frena y no sale ningún
pedido. Con la copia puesta (la primera fila), salía.

**Lo que ningún caso distingue.** Volver a poner sola la copia campo →
operación deja todo en verde: con el campo bien pintado copia lo mismo que ya
está guardado. La saqué porque sobra y porque era el camino del defecto, no
porque un caso la pida.

## Lo que cambia además (supuestos reversibles)

- **Un valor que llega al campo sin evento `input` ya no se genera.** Antes
  «Generar» lo levantaba del campo; ahora frena con «Es obligatorio» con el
  texto a la vista. No encontré un camino de una persona en Chromium (teclado,
  pegar, deshacer y rehacer disparan `input`; el campo tiene
  `autocomplete="off"`). No corrido: IME, autocompletar de extensiones,
  Firefox, WebKit. Si preferís la copia de vuelta, es revertir `a0acbe7`: el
  caso sigue en verde.
- La operación guarda el sufijo como se escribió, con sus espacios; el pedido
  lo recorta, como ya hacía. Antes «Generar» lo dejaba recortado en la
  operación.

## Revisión adversarial

| quién | sobre | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` (Sonnet, alto) | `0d4cd72..bcb3e9c` | media, del caso: sin la copia campo → operación en «Generar» (`6f0e9f9`) el caso seguía en verde | la copia salió del producto (`a0acbe7`); el rojo `8a9a8f6` muestra la diferencia |
| | | baja, de antes: un valor puesto en el campo sin evento `input` daba el TXT bien y los avisos con `""` (`13e4dd8`) | ahora frena; va en supuestos reversibles |
| | | baja, diseño anterior: si el arancel propone sufijo para todos los productos, una B sin sufijo genera con `sbt_sufijo_valor=''` y el propio de cada producto (no el de A) | queda: es la regla de «todos con sufijo propio»; lo anoto en riesgos |
| | | baja, del caso: el orden «pintar el campo antes que la tarjeta» no lo protegía nada (no lo corrió) | el caso mira la tarjeta (`a0c1c69`); rojo `740b38a` |
| `adversario-sonnet-alto` (Sonnet, alto) | `bcb3e9c..a0c1c69` | ninguno. Informativo: quedan dos fuentes, «Generar» lee la operación y la tarjeta lee el campo | riesgo, abajo, con línea para la cola |

El primero no encontró camino de usuario que llegue a `/generate_maria`, a los
avisos o a la tarjeta con un sufijo ajeno. El segundo corrió una sonda con
teclado y mouse (commit descartable `f78b781`): espacios al final, ir a
«ready» y volver, borrar todo, deshacer y rehacer, pegar 130 caracteres, error
del servidor y vuelta, ir a «clientes» y volver, borrador y recarga; campo y
operación iguales en cada paso. No reprodujo arrastrar texto (en el navegador
sin ventana no hubo arrastre) ni corrió IME ni autocompletar.

## `/code-review high` sobre `0d4cd72..bcb3e9c`

Los revisores heredan Fable. Cinco hallazgos:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | el aviso `#sbtFieldError` de una operación queda bajo el campo repintado de la siguiente | de antes: D238 |
| 2 | en dos llegadas el «frenó» del caso ya era cierto antes del clic | el caso exige el foco en el campo (`a0c1c69`); rojo `8e6b598` |
| 3 | el caso no miraba la tarjeta del despachante | la mira (`a0c1c69`); rojo `740b38a` |
| 4 | dos fuentes de verdad: `despachante.js` lee el sufijo del campo del DOM | no toco `despachante.js`: riesgo y línea para la cola |
| 5 | quedaba la copia campo → operación en «Generar», que mi D236 decía que se iba con (b) | sacada (`a0acbe7`) |

No volví a correr `/code-review` sobre `bcb3e9c..52f13ca`: lo que cambió
después son los arreglos de esta tabla, y el producto nuevo (−7/+2) lo miró la
segunda pasada adversarial.

## Comandos

```bash
S=<carpeta descartable>; PY=<python del entorno virtual>
# verde: los dos casos del sufijo
SOLO="sufijo_otra1 sufijo_borrador1" env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/correr_pantallas.sh 52f13ca $S/verde   # resumen: 2 verdes, 0 rojas
# rojo: el caso de hoy con el producto de la primera entrega (commit descartable)
git worktree add -q --detach $S/wt 52f13ca
ROJO=$(cd $S/wt && git checkout -q ee2ee3c -- proyecto_maria/static/v2/screens/finalize.js \
  && git -c user.name=x -c user.email=x@x commit -qm descartable && git rev-parse HEAD)
git worktree remove --force $S/wt
SOLO=sufijo_otra1 env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/correr_pantallas.sh $ROJO $S/rojo   # resumen: 0 verdes, 1 rojas: sufijo_otra1
grep FALLA $S/rojo/sufijo_otra1.log   # tres líneas: campo «AA(000123)», la tarjeta lo marca, «siguió a «ready»» y 1 POST
```

La sonda de D238 (`15893f6`, no está en la rama) dio:

```
SONDA A sin sufijo, al entrar: oculto «»
SONDA A sin sufijo, después de «Generar»: a la vista «Ingresá el sufijo de valor SBT. Es obligatorio.»
SONDA B con sufijo guardado, al entrar: campo «AA(000456)», cartel a la vista «Ingresá el sufijo de valor SBT. Es obligatorio.»
SONDA C sin sufijo, al entrar: cartel a la vista «Ingresá el sufijo de valor SBT. Es obligatorio.»
SONDA C después de escribir su sufijo: cartel a la vista «Ingresá el sufijo de valor SBT. Es obligatorio.»
PANTALLA SONDA-CARTEL OK
```

## Puertas

Todas sobre `52f13ca`, una por vez.

| puerta | salida |
|---|---|
| `pytest -q --no-cov --timeout=120` (entera, con la guarda de conexiones) | `6130 passed, 110 skipped, 3 xfailed, 106 warnings in 1299.87s (0:21:39)` (antes, sobre `c18039c`: `6130 passed, 110 skipped, 3 xfailed, 109 warnings in 1331.38s (0:22:11)`) |
| `python -m compileall -q proyecto_maria` | sin salida, sale 0 |
| `correr_pantallas.sh 52f13ca` (las 34) | `resumen: 33 verdes, 1 rojas: orden1` (z22: abajo) |
| `SOLO=orden1 correr_pantallas.sh 52f13ca`, una vez | `resumen: 1 verdes, 0 rojas` |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `sabotaje_valor1.sh 52f13ca` | `OK: los 32 sabotajes dan rojo por la razón esperada` |
| `sabotaje_valor1c.sh 52f13ca` | `OK: los 25 sabotajes dan rojo por la razón esperada` |
| `anclas_perdidas.py 52f13ca` | `revisión 52f13ca: 102 guiones, 2466 anclas medidas y 11 llamadas sin medir` (igual que la base `0d4cd72`, fila por fila) |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |

### El rojo de `orden1` (z22, la carrera de D237)

- En la corrida entera, z22:
  `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')`.
- El servidor registró, en ese orden: `POST /generate_maria/avisos 200`,
  `POST /auth/logout 200`, `POST /generate_maria/avisos 401`,
  `GET /?next=%2Fdashboard 200`, `POST /auth/login 200`. Es la firma de D237:
  un pedido de avisos llega con la sesión cerrada, la pestaña se va al login y
  «Generar» ya no está en la página.
- Corrí `orden1` sola una vez más, no para taparlo: con z22 en rojo el guion
  corta y los casos que siguen no habían corrido sobre este SHA. Dio verde
  (71 `OK`; la corrida roja llegó a 52). Van las dos.
- **No probado:** que esta pieza no cambie la frecuencia de la carrera. No toca
  los pedidos de avisos ni su demora, y z22 escribe el sufijo igual que antes;
  la medición forzada sobre la base es la de la primera entrega.
- Con D237 (a) todavía pendiente, la puerta de pantallas de PAIS-NL puede
  volver a dar este rojo.

No corrí: `smoke_friccion.sh` ni `ataque_aislamiento.sh` (la pieza no toca
servidor, datos, sesión ni permisos), `/security-review` (lo mismo), Firefox
ni WebKit. Sin guion de sabotaje propio: la pieza no es de §3; los rojos van
arriba, una vez cada uno.

## `chequeo-6`

```
chequeo-6 0d4cd72..52f13ca: avisos para mirar, no un veredicto
producto +5/−11
arnés +210/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/screens/finalize.js: 1494 → 1488
avisos: 0
```

De `arnés +210/−1`, 99 líneas son mías (`pantalla_sufijo_otra1.js`); las otras
111/−1 son `tests/conftest.py` y `tests/test_guarda_conexiones.py`, de la
Técnica, que llegaron con la integración de tu rama.

## Riesgos

- **Medio-bajo: dos fuentes del sufijo.** «Generar», los avisos y el TXT leen
  la operación; la tarjeta del despachante lee el campo
  (`despachante.js:255`, `sufijoDeLaOperacion`). Hoy coinciden porque el campo
  se pinta al entrar y cada tecla va a la operación. Línea que propongo para
  `COLA-LIMPIEZA.md`: «`despachante.js`: `sufijoDeLaOperacion()` lee el sufijo
  del campo del DOM; que lea la operación, como «Generar» y los avisos».
- **Bajo: todos los productos con sufijo propio.** Si el arancel propone
  sufijo para cada producto, una operación sin sufijo genera sin frenar, con el
  propio de cada producto. Es la regla anterior («No hace falta si todos los
  productos llevan sufijo propio»); no lleva el sufijo de la operación
  anterior. Tu «una B sin sufijo no genera» vale cuando algún producto depende
  del de la operación, que es lo que prueba el caso.
- **Bajo: el aviso viejo a la vista** (D238).
- El caso tiene 99 líneas contra las ~80 de §6: tres llegadas, la tarjeta y el
  positivo de avisos y TXT en un solo caso; `chequeo-6` no lo marca.
- Los avisos con el sufijo a medio escribir se corrigen solos 400 ms después
  de la última tecla. Ya era así.

## Archivos de producto que toqué

`proyecto_maria/static/v2/screens/finalize.js`, `CHANGELOG.md`.

## Sigo con

**PAIS-NL**: primero el rojo en `tests/test_catalogo3.py`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `6e4a427`). SUFIJO-BORRADOR, vuelta de la devolución con D236 (b), entregada sobre `52f13ca` (base `0d4cd72`), con D238 (el aviso «Es obligatorio» queda a la vista entre operaciones; recomiendo (a), pieza aparte) sin contestar. Pieza activa: PAIS-NL (toda sigla de Países Bajos da 423 en TXT, catálogo y pantalla; `PAISES_INDEC` sin claves repetidas; «HOLANDA» queda en 434; ninguna otra entrada cambia; rojo cambiando `tests/test_catalogo3.py:291` y `:298`; las formas de escribirlo como datos de un caso; en el informe, medido y no arreglado, qué queda guardado con «NL» y si algo ya guardado en 434 no se distingue; sin migración). Después: D237 (a) (z22 de `pantalla_orden1.js` espera los avisos, sin espera fija), CUIT-GENERAR (D235 a; apartada con las reversiones `3a6f656` y `2f04637`, se recupera revirtiéndolas; hallazgos del adversario en el scratch `cg_adversario.md`; revisión fuerte §3 con `/security-review`; sus D toman número nuevo), y los vencidos de `sabotajes-conocidos.txt`, uno por pieza. Próxima D: D239. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, sin secretos ni datos reales, VUCE y Gemini simulados, una corrida por vez, un rojo se diagnostica y no se repite hasta verde, las Devs no usan el consejero ni subagentes de esfuerzo muy alto.
