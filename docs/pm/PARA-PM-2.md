# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D237 (a): entregada en `346a1c9`. (z22) de `orden1` cierra la sesión recién cuando la pestaña terminó lo que pide sola al entrar a «Validación». Forzada, la base da rojo y esto da verde. Sin producto. Una decisión: D241

| qué | SHA |
|---|---|
| base (integración de tu rama hasta `cfc707a`) | `c3eb7cf` |
| (z22) espera los pedidos de la pestaña antes de salir | `1d20002` |
| forzador de la carrera, `scripts/testing/forzar_avisos_orden1.js` | `7a37f46` |
| ajuste después de las revisiones: el sufijo va en la operación, la entrada pasa a una función aparte. **Lo que se entrega** | `346a1c9` |
| integración de tu rama hasta `7104db7` (sólo `docs/pm/`) | `f89dc13` |
| informe | el commit siguiente |

`producto +0/−0`: sólo `scripts/testing/`. Sin línea en `CHANGELOG.md`.

Son tres commits de prueba y no uno porque los dos primeros ya estaban subidos
cuando terminaron las revisiones: lo que salió de ellas va encima, sin
reescribir.

## Decisiones

**D241. La espera nueva no tiene un sabotaje que corra solo.** Sacando la
espera, (z22) sigue verde en una corrida normal; el rojo sólo sale con el
forzador puesto a mano (está abajo, en «Negativos»). Si alguien la saca, vuelve
el rojo intermitente de antes, no un defecto del producto.
- (a) un sabotaje más en `sabotajes/orden1b.sh` que corra (z22) con
  `forzar_avisos_orden1.js` y la espera sacada. El guion es de la Técnica: lo
  hace ella o me lo das. Suma cerca de un minuto a cada corrida del guion.
- (b) queda así: el forzador y el comando están en este informe.
- **Recomiendo (b).** Es una espera del arnés, no un control del producto, y
  §6 pide guion propio sólo para lo de §3.

## Lo que hice distinto de lo que te escribí (supuestos reversibles)

Te había escrito «z22 espera a que terminen los pedidos de avisos de la
entrada a «Validación» antes de cerrar la sesión». Con eso solo no alcanzaba,
y lo que sumé es esto:

1. **Espera también las validaciones.** Al entrar a «Validación» la pestaña
   pide sola cuatro cosas: los avisos dos veces (al entrar y cuando llegan
   las tarjetas, `finalize.js:76-102`) y la validación dos veces (la de la
   pantalla y la del semáforo, que sale de un temporizador a los 500 ms,
   `semaforo.js`). Cualquiera de las cuatro, emitida antes de la salida y
   atendida después, da 401 y manda la pestaña al login.
2. **Espera cantidades (2 y 2), no sólo «ninguno en vuelo».** El semáforo
   sale de un temporizador y el segundo pedido de avisos sale cuando vuelven
   otros: entre uno y otro puede no haber nada en vuelo. **Esto no lo pude
   mostrar con un rojo** (abajo, «Lo que no demostré»).
3. **Entra a «Validación» en un solo paso** (`CDI.state` y `CDI.goTo` en el
   mismo `evaluate`), no con `cargar` y después `goTo`. Con dos pasos la
   pestaña queda un rato en la pantalla de NCM, y si ese rato pasa de 500 ms
   el semáforo valida desde ahí: las validaciones después de entrar son una,
   dos o tres según el tiempo, y la cuenta deja de ser exacta.
4. **El sufijo va en la operación; (z22) ya no lo escribe en el campo.**
   Escribirlo dispara otro pedido de avisos (a los 400 ms) y otra validación
   (a los 500 ms), que salían antes o después del login según cuánto tardara.
   Ahora la pantalla muestra el sufijo de la operación al entrar
   (`finalize.js:195-199`) y «Generar» lo lee del estado (`:681`). En el
   `api.log`, después de la salida la pestaña sólo consulta la sesión y
   genera. **Lo que se pierde con esto**, dicho por el revisor del ajuste y
   comprobado en los logs:
   - (z22) ya no pasa por «lo que la persona escribe en el campo llega a la
     operación». Lo siguen haciendo `generar` y `listaParaGenerar` (z20, z23).
   - En la base, esos dos pedidos solían salir con la sesión ya cambiada y
     quedaban detrás de la consulta de sesión, junto con «Generar». Dependía
     del reloj y ningún chequeo de (z22) lo miraba; ahora no pasa nunca. Con
     el forzador de la Técnica el `api.log` lo muestra: después del login, la
     base tiene dos `GET /auth/current_user` antes de `POST /generate_maria`
     y `346a1c9` tiene una.

   Si preferís que (z22) siga escribiendo el sufijo, vuelve con una línea,
   entre la salida y el login, y vuelven los dos caminos según el reloj.
5. **Un forzador nuevo**, `forzar_avisos_orden1.js`, al lado del de la
   Técnica (`forzar_orden1.js`, que no toqué): el de ella fuerza la consulta
   de sesión del hueco, no este pedido. Se carga igual, con `NODE_OPTIONS`.
   Demora un segundo cada pedido de avisos y hace que el login llegue dos
   segundos después de la salida: es la «respuesta demorada a propósito» de
   tu criterio, no un reloj dentro de la prueba.
6. **Una función nueva, `enValidacionQuieta`**, con la entrada y la espera.
   La función principal de la pantalla, que tiene más de 150 líneas, queda
   del largo que tenía.

Lo que (z22) comprueba no cambió: que genera (`y no generó`), que «Generar»
comprobó la sesión (`y Generar no comprobó la sesión`) y que queda una sola
operación. `listaParaGenerar` y los demás casos no cambiaron.

## Resultado

Todo con `CASOS=z22`, cada corrida con su API y su base nuevas. Textos
copiados de los logs.

| qué | resultado | lo que dice |
|---|---|---|
| base `c3eb7cf` con `forzar_avisos_orden1.js` | rc=1 | `forzar_avisos_orden1: un pedido de avisos sale antes de salir` · `forzar_avisos_orden1: un pedido de avisos sale 964 ms después de salir` · `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')`. En el `api.log`: `POST /auth/logout 200`, `POST /generate_maria/avisos 401`, `POST /auth/login 200`. Es la `FALLA` de mi D237 |
| `346a1c9` con `forzar_avisos_orden1.js` | rc=0 | `forzar_avisos_orden1: un pedido de avisos sale antes de salir`, dos veces · `OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos`. En el `api.log`, las dos validaciones y los dos avisos con 200 antes de `POST /auth/logout` |
| `346a1c9` sola, tres corridas seguidas | rc=0 las tres | `OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos` |
| `346a1c9` con `forzar_orden1.js` (el de la Técnica) | rc=0 | `forzar_orden1: la consulta del hueco se cortó sin respuesta antes de entrar` · el mismo `OK` |
| base `c3eb7cf` con `forzar_orden1.js` | rc=0 | las mismas dos líneas: lo que fuerza ella no cambió |

## Negativos

Cada uno, un commit descartable sobre `346a1c9` (no se suben), con
`CASOS=z22`.

| qué saqué o cambié | resultado | lo que dice |
|---|---|---|
| producto: con la sesión cambiada no escribe aunque sea el mismo usuario (`app_v2.js`) | rc=1 | `FALLA: A salió, volvió a entrar y generó enseguida y no generó: error: No se pudo comprobar la sesión. Recargá la página.` |
| producto: `ESPERA_SESION_MS` de 10000 a 2000 (tu sabotaje de la reproducción) | rc=1 | la misma `FALLA` |
| producto: «Generar» no comprueba la sesión | rc=1 | `FALLA: A salió, volvió a entrar y generó enseguida y Generar no comprobó la sesión` |
| prueba: espera tres pedidos de avisos en vez de dos | rc=1 | `FALLA: A salió, volvió a entrar y generó enseguida: antes de salir, la pestaña no terminó sus pedidos: faltan /generate_maria/avisos (2 de 3); en vuelo: ninguno` |
| prueba: sin la espera, con el forzador | rc=1 | `forzar_avisos_orden1: un pedido de avisos sale 931 ms después de salir` · `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')`. `api.log`: `POST /auth/logout 200`, `POST /generate_maria/avisos 401` |
| prueba: la espera sin cantidades (`terminaron([])`), con el forzador | **rc=0** | `OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos`. Es lo que no demostré |

## Lo que no demostré

- **Las cantidades (2 y 2).** Con la espera puesta pero sin cantidades
  (`terminaron([])`, que espera sólo «ninguno en vuelo») y el forzador, (z22)
  dio **verde**. El hueco que cubren las cantidades es de pocos milisegundos:
  entre que vuelve un pedido y sale el siguiente (el semáforo, desde su
  temporizador). Para abrirlo haría falta un reloj que decida cuándo sale el
  temporizador respecto de la salida, y eso es lo que tu criterio no acepta
  («un reloj que decide… es la carrera»). Queda sostenido por lectura de
  código, no por un rojo. Si preferís la versión sin cantidades, es una línea.
- **La mitad de las validaciones.** El forzador demora los avisos, no
  `/api/validate/smart`. Que una validación atendida después de la salida
  manda al login lo sostiene el código (`api()` → 401 → `irAlLogin`), no un
  rojo de esta entrega.
- **Lo frágil de las cantidades.** Son datos de la prueba, no del producto.
  Si el producto deja de pedir alguna de las cuatro, (z22) falla a los 15 s
  con `la pestaña no terminó sus pedidos: faltan … (1 de 2)`: se ve. Si
  empieza a pedir una quinta, (z22) no se entera y la carrera puede volver,
  sin aviso. Un caso conocido: con estudios cargados la pantalla pide los
  avisos una tercera vez (`estudios.js:105`); el usuario de (z22) no tiene.
- **La barra de arriba** se actualiza sola cada 5 minutos
  (`topbar_financials.js:11`). Si ese pedido cae justo en la salida, la
  carrera es la misma: no lo cubro.
- **El caso contrario ya no se prueba en ningún lado:** «un pedido de A
  atendido después de la salida manda la pestaña al login» era lo que (z22)
  hacía sin querer. Ahora se evita por construcción y ningún caso lo mira.

## Revisión adversarial

| quién | sobre | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` (Sonnet, alto), corrió | `c3eb7cf..7a37f46` | nada que rompa o debilite la prueba. Reprodujo las cuentas 2 y 2 con el servidor frío y caliente, y el rojo de la base forzada por el motivo correcto | |
| | | baja: las etiquetas «antes / después de salir» del forzador se miden en Node, no en el servidor | el `api.log` es lo que vale; lo cito en cada rojo |
| | | baja: sin `CASOS=z22` el forzador demora todos los casos | el comando lleva `CASOS=z22` |
| | | baja: un pedido contado que falla hace esperar los 15 s | riesgo, abajo |
| | | baja: el caso contrario quedó sin prueba | «Lo que no demostré» |
| `adversario-sonnet-alto` (Sonnet, alto), sólo lectura | `7a37f46..346a1c9` | media-baja: lo que (z22) pierde por no escribir el sufijo | supuesto 4 |
| | | baja: la carrera no tiene guardia que corra sola | D241 |
| | | baja: `forzar_orden1.js` sigue diciendo «activo» al cargarse aunque no demore nada | línea para la cola (es de la Técnica) |
| | | baja: un tope de la entrada sale ahora con el prefijo «antes de salir,» | queda: el texto es correcto |

El segundo no corrió nada (había una corrida en curso): lo suyo es lectura.
Lo que afirma del producto lo comprobé en los `api.log` de arriba.

## `/code-review high` sobre `c3eb7cf..7a37f46`

Los revisores heredan Fable. Siete hallazgos:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | las cantidades están fijas: con estudios hay un tercer pedido de avisos; si el producto junta pedidos, (z22) da rojo | «Lo que no demostré» |
| 2 | el forzador muestra sólo la mitad de los avisos | «Lo que no demostré» |
| 3 | escribir el sufijo entre la salida y el login dejaba dos caminos del producto según el reloj, ninguno comprobado | arreglado en `346a1c9`: supuesto 4 |
| 4 | `seguirPedidos` sirve para una sola espera y no cuenta los pedidos que fallan: ahí espera los 15 s | queda: (z22) la usa una vez. Riesgo, abajo |
| 5 | (z22) tenía adentro una copia de `cargar` y `listaParaGenerar` | a medias: pasó a `enValidacionQuieta` (`346a1c9`). Unificarla con `listaParaGenerar` toca (z20) y (z23): línea para la cola |
| 6 | tercera copia del gancho de `launch` y `newContext`; el forzador decía «activo» sin saber si demoraba | lo segundo, arreglado (`346a1c9`); lo primero, línea para la cola |
| 7 | `chequeo-6`: la función principal de la pantalla crecía de 1584 a 1594 líneas | arreglado (`346a1c9`): `avisos: 0` |

Después del ajuste no volví a correr `/code-review`: corrí el adversario de
lectura de arriba y todas las puertas sobre `346a1c9`.

## Comandos

```bash
# desde la raíz del repo, con esta rama; PY es tu python con las dependencias
export PY=/ruta/al/venv/bin/python
F=$PWD/scripts/testing/forzar_avisos_orden1.js
# 1. la base, forzada: rc=1 y «FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')»
NODE_OPTIONS="--require $F" CASOS=z22 SOLO=orden1 env -u DATABASE_URL -u ENVIRONMENT bash scripts/testing/correr_pantallas.sh c3eb7cf /tmp/z22-base
# 2. la entrega, forzada: rc=0 y «OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos»
NODE_OPTIONS="--require $F" CASOS=z22 SOLO=orden1 env -u DATABASE_URL -u ENVIRONMENT bash scripts/testing/correr_pantallas.sh 346a1c9 /tmp/z22-entrega
# 3. el orden en el servidor: en la base, logout y después un avisos con 401; en la entrega, ningún 401
grep -h "auth/logout\|generate_maria\|validate/smart" /tmp/z22-base/orden1.*/api.log /tmp/z22-entrega/orden1.*/api.log
# 4. los sabotajes de la pantalla: 30 «ROJO» y «sabotajes sin rojo: 0»
scripts/testing/sabotajes/orden1b.sh 346a1c9
# 5. producto +0/−0, avisos: 0
python docs/pm/herramientas/chequeo-6.py c3eb7cf 346a1c9
```

El forzador se toma del árbol de trabajo: en `c3eb7cf` no existe.

## Puertas

Todas sobre `346a1c9`, de a una.

| puerta | salida |
|---|---|
| `sabotajes/orden1b.sh 346a1c9` | 30 `ROJO`, `sabotajes sin rojo: 0`, rc=0. Los dos de (z22): `FALLA: A salió, volvió a entrar y generó enseguida y no generó` y `… y no generó: error: No se pudo comprobar la sesión` |
| `SOLO=orden1` entero (todos los casos) | `verde orden1` con `rc=0`, `resumen: 1 verdes, 0 rojas`; 71 líneas `OK`, entre ellas la de (z22) |
| `anclas_perdidas.py 346a1c9` | `102 guiones, 2466 anclas medidas y 11 llamadas sin medir`; salida igual a la de `c3eb7cf`, línea por línea |
| `chequeo-6.py c3eb7cf 346a1c9` | abajo, entera |
| grep de historia de §6 | no aplica: no hay líneas de producto |

**No corrí:** la suite de pytest, `compileall`, `e2e_maria.sh`,
`smoke_friccion.sh`, `ataque_aislamiento.sh` ni `/security-review`. La entrega
son dos archivos de `scripts/testing/` que ninguna prueba de `tests/` lee
(busqué `pantalla_orden1` y `forzar_` en `tests/`, `.github/` y
`docs/pm/herramientas/`: nada) y no toca producto, sesión ni datos.

## `chequeo-6`

```
chequeo-6 c3eb7cf..346a1c9: avisos para mirar, no un veredicto
producto +0/−0
arnés +73/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- Los de «Lo que no demostré»: las cantidades son datos de la prueba y un
  quinto pedido automático del producto pasaría sin aviso.
- Un pedido contado que falla (no que tarda) no se cuenta: (z22) espera el
  tope de 15 s y falla con el texto de `faltan …`. Se ve, pero tarda.
- (z22) tarda ahora lo que tardan esos cuatro pedidos antes de salir. No
  medí cuánto.

## Para la cola de limpieza (propongo; el archivo es tuyo)

- Los tres forzadores (`forzar_arranque.js`, `forzar_orden1.js`,
  `forzar_avisos_orden1.js`) repiten el mismo gancho de `launch` y
  `newContext`, y cargan `require('playwright')` mientras la pantalla carga
  `/opt/node-tools/node_modules/playwright` (`pantalla_orden1.js:78`): si un
  día no son el mismo módulo, no fuerzan nada. `forzar_orden1.js:66` dice
  «activo» al cargarse, lo demore o no. Un ayudante común para los tres.
- `pantalla_orden1.js`: el sufijo de prueba `'AA(DemoPouchs)-CA00-'` está en
  tres lugares (174, 335, 1429) y hay dos formas de dejar una operación lista
  en «Validación» (`listaParaGenerar` y `enValidacionQuieta`).

## Archivos de producto que toqué

Ninguno. De arnés: `scripts/testing/pantalla_orden1.js` ((z22) y dos
funciones nuevas, `seguirPedidos` y `enValidacionQuieta`) y
`scripts/testing/forzar_avisos_orden1.js` (nuevo).

## Sigo con

D238 (a): el aviso «Es obligatorio» del sufijo no queda a la vista de una
operación a otra.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `7104db7`). PAIS-NL aceptada e integrada; D239 y «Holanda» esperan a Emi: no se tocan; D240 (b). D237 (a) entregada sobre `346a1c9` (base `c3eb7cf`; sólo arnés: (z22) de `scripts/testing/pantalla_orden1.js` espera los cuatro pedidos de la entrada a «Validación» antes de salir; forzador `scripts/testing/forzar_avisos_orden1.js`), con D241 (la espera no tiene sabotaje que corra solo; recomiendo (b), queda así) sin contestar. Pieza activa: D238 (a) (el aviso «Es obligatorio» del sufijo no queda a la vista de una operación a la otra; pieza chica aparte; mi texto está en `git show 6fbfefd:docs/pm/PARA-PM-2.md`; borrador de pantalla en el scratch `pantalla_sufijo_otra1.js`). Después: CUIT-GENERAR (D235 a; apartada con las reversiones `3a6f656` y `2f04637`, se recupera revirtiéndolas; hallazgos del adversario en el scratch `cg_adversario.md`; revisión fuerte §3 con `/security-review` y `ataque_aislamiento.sh`; sus D toman número nuevo), y los vencidos de `sabotajes-conocidos.txt`, uno por pieza, primero `sabotaje_subitems1.sh` y `sabotaje_sufijos1.sh`. Próxima D: D242. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, sin secretos ni datos reales, VUCE y Gemini simulados, una corrida por vez, un rojo se diagnostica y no se repite hasta verde, las Devs no usan el consejero ni subagentes de esfuerzo muy alto.
