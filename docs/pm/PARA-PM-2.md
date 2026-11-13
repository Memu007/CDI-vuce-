# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D238 (a): entregada en `80cd954`. El aviso rojo del sufijo SBT se va al escribir en el campo y no entra con la pantalla de «Validación»; el rechazo del servidor sigue saliendo bajo el campo. Una decisión: D242

| qué | SHA |
|---|---|
| base (informe de D237) | `73f8db7` |
| producto: `finalize.js` y `CHANGELOG.md` | `e1ecc29` |
| pruebas. **Lo que se entrega** | `80cd954` |
| integración de tu rama hasta `543671b` (sólo `docs/pm/`), después de las puertas | `202e3b4` |
| informe | el commit siguiente |

`producto +7/−1` (más 5 líneas de `CHANGELOG.md`). Ninguna función nueva.

**Lo primero que tenés que saber: mi primera versión rompía cinco pruebas de
pytest y no lo vi yo ni la primera ronda de revisión; lo encontró la suite
completa.** Detalle en «Lo que salió mal». Lo que entrego es la tercera
versión; todo lo de abajo está corrido sobre `80cd954`.

## Decisiones

**D242. El motivo de un rechazo del servidor también se va con la primera
tecla.** El aviso bajo el campo tiene dos orígenes: el de la pantalla
(«Ingresá el sufijo de valor SBT. Es obligatorio.») y el del servidor al
generar («Sufijo de valor de la operación: falta AA00.», «… queda de 121
caracteres y no puede superar los 120», y también los «Item N: … SBT …», que
caen ahí porque la pantalla manda bajo ese campo todo rechazo que nombre
«sbt», `finalize.js:753`). Hoy el arreglo no los distingue: cualquier cosa
que se escriba en el campo esconde el aviso, sea de quien sea. Antes el del
servidor quedaba a la vista hasta el próximo «Generar».
- (a) queda así. El aviso habla del valor que había al tocar «Generar»; al
  cambiarlo deja de ser cierto, y el servidor lo repite en el próximo
  «Generar» si sigue mal. Lo que se pierde: quien corrige un sufijo largo
  deja de ver qué le faltaba («falta AA00») en cuanto empieza a escribir, y
  un «Item 3: …» se va aunque lo que se escriba en el campo de la operación
  no arregle el ítem 3.
- (b) pieza chica aparte: sólo el aviso de la pantalla se va al escribir; el
  del servidor queda hasta el próximo «Generar» o hasta salir de
  «Validación». Unas tres líneas de producto y un caso. Lo que se pierde: el
  motivo del servidor puede quedar a la vista al lado de un sufijo ya
  corregido, que es el mismo defecto de esta pieza dentro de una operación.
- **Recomiendo (a)**: es lo que te escribí («se esconde cuando se escribe en
  el campo») y no deja un aviso viejo en ningún camino. Si un despachante se
  queja de que pierde el motivo, (b) es chica. No lo probé con una persona.

## Lo que hice distinto de lo que te escribí (supuestos reversibles)

Te había escrito: «el aviso se esconde cuando se escribe en el campo y
cuando se entra a «Validación» con otra operación».

1. **Se esconde en toda entrada a «Validación», no sólo «con otra
   operación».** Distinguir «otra operación» pide guardar cuál era la
   anterior; esconderlo siempre no pide estado. Lo que cambia para la
   persona: sale de «Validación» con el aviso a la vista, vuelve con la misma
   operación y el aviso no está; «Generar» lo vuelve a poner.
2. **El rechazo del servidor ahora vuelve a «Validación» primero y pone el
   aviso después** (`finalize.js:755-760`). Antes era al revés, y con el
   punto 1 la entrada lo habría borrado: es el camino que me marcaste que no
   había que romper. `CDI.goTo` corre la entrada de la pantalla en el momento
   (`app_v2.js:139-177`), así que el orden alcanza.
3. **Toqué un caso de pytest que ya existía**, `tests/test_avisos1_seguro.py`:
   su `CDI.goTo` de mentira ahora esconde el aviso al entrar a «Validación»,
   como la pantalla. Sin eso, pytest no veía el orden del punto 2 (lo marcó
   `/code-review`). Los otros dieciséis casos del archivo no cambian de
   resultado.

Lo que no toqué: `enlazarValor`, `onGenerate` (su línea que esconde el aviso
cuando el sufijo está) y el texto de los avisos.

## Lo que salió mal

La primera versión (`2d1dea7`, local, nunca subida) sumaba una función
chica, `quitarAvisoDelSufijo`, y la llamaba desde `enlazarValor` y
`pintarSufijo`. La pantalla andaba y el caso nuevo daba verde. La suite
completa sobre esa versión dio `5 failed, 6126 passed, 110 skipped,
3 xfailed`: tres casos de `tests/test_valor1.py` y dos de
`tests/test_valor1c.py`, todos con `ReferenceError: quitarAvisoDelSufijo is
not defined`. Esos archivos sacan funciones de `finalize.js` por nombre y las
corren en node con un DOM de mentira: una función nueva llamada desde una de
las que sacan no existe ahí.

Lo arreglé sin función nueva: el oyente va en `init()` (que ninguna prueba
saca) y `pintarSufijo` esconde el aviso con dos líneas propias. La primera
ronda de revisión (adversario y `/code-review`) leyó la versión rota y no lo
encontró; por eso repetí las dos sobre la segunda versión y un adversario
más sobre la tercera. Abajo dice qué SHA leyó cada una. Los SHA de las dos
primeras versiones (`2d1dea7`/`ca5f257` y `0e1526f`/`76d9d90`) fueron
locales y los reescribí antes de subir: no están en la rama. Sus registros
quedaron en mi scratch, no en el repositorio.

## Resultado

**Rojo antes del arreglo.** `finalize.js` de `73f8db7` con las pruebas de
`80cd954`, en un worktree descartable (textos copiados de la salida):

| qué | resultado | lo que dice |
|---|---|---|
| `SOLO=sufijo_otra1`, arreglo revertido | `rc=1`, `resumen: 0 verdes, 1 rojas: sufijo_otra1` | `FALLA: otra operación entra con el aviso de la anterior a la vista: «Ingresá el sufijo de valor SBT. Es obligatorio.»` |
| `tests/test_avisos1_seguro.py`, arreglo revertido | `1 failed, 16 passed` | `test_cada_400_que_cambia_de_pantalla_deja_el_motivo_a_la_vista[sufijo]`: `AssertionError: assert None == 'Sufijo de valor de la operación: falta AA00.'` |
| `SOLO=sufijo_otra1`, entrega | `rc=0`, `resumen: 1 verdes, 0 rojas` | `PANTALLA SUFIJO-OTRA OK` |
| `tests/test_avisos1_seguro.py`, entrega | `17 passed` | |

El rojo de pytest con el arreglo revertido no dice que la base estuviera
mal en ese camino: en la base el aviso del servidor se veía. Cae porque el
`goTo` de mentira ya modela la pantalla nueva. El que discrimina de verdad es
el negativo «sin reordenar», abajo.

El caso de pantalla, en su parte nueva (`pantalla_sufijo_otra1.js:88-95`):
la última de las tres llegadas frenó y dejó su aviso a la vista (lo afirma,
no lo supone); entra otra operación y el aviso no está; «Generar» sin sufijo
frena con su aviso; se escribe el sufijo y el aviso se va. Ninguna espera
fija nueva.

## Negativos

Uno por mitad del arreglo, cada uno un commit descartable sobre `80cd954`
(no se suben). La pieza no es de las de §3: no lleva guion de sabotaje
propio.

| negativo | corrida | resultado | lo que dice |
|---|---|---|---|
| `pintarSufijo` no esconde el aviso | `SOLO=sufijo_otra1` | `rc=1` | `FALLA: otra operación entra con el aviso de la anterior a la vista: «Ingresá el sufijo de valor SBT. Es obligatorio.»` |
| sin el oyente de `input` | `SOLO=sufijo_otra1` | `rc=1` | `FALLA: con el sufijo ya escrito, el aviso sigue a la vista: «Ingresá el sufijo de valor SBT. Es obligatorio.»` |
| el rechazo pone el aviso y después vuelve (orden viejo) | `SOLO="sufijo_borrador1 maria9"` | `rc=1`, `resumen: 0 verdes, 2 rojas: maria9 sufijo_borrador1` | `FALLA: generado y devuelto a la validación: el servidor no devolvió a la validación: page.waitForFunction: Timeout 15000ms exceeded.` · `FALLA: el de la operación: no sale bajo el campo del sufijo de la operación` |
| el mismo | `tests/test_avisos1_seguro.py` | `1 failed, 16 passed` | `…[sufijo]`: `AssertionError: assert None == 'Sufijo de valor de la operación: falta AA00.'` |

El tercero muestra que el camino del rechazo del servidor ya estaba cubierto
por dos pantallas que no toqué (`maria9` y `sufijo_borrador1`).

## Revisión adversarial

Pieza chica de pantalla: Sonnet, medio, según la tabla. Tres rondas porque
hubo tres versiones.

| quién | sobre | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-medio` (Sonnet, medio), corrió | `73f8db7..ca5f257` (primera versión, la rota) | nada que rompa; cuatro menores. **No vio las cinco pruebas de pytest rotas** | la versión se descartó |
| `adversario-sonnet-medio` (Sonnet, medio), corrió | `73f8db7..76d9d90` (segunda) | nada que rompa. Comprobó el oyente, las pruebas que sacan funciones, las anclas de los sabotajes y los caminos del aviso | |
| `adversario-sonnet-medio` (Sonnet, medio), sólo lectura | `73f8db7..80cd954` (la entrega) | nada que rompa. Repasó los tres lugares que escriben el aviso, los dos `goTo('validating')`, el oyente, el `goTo` de mentira para los otros parámetros del caso y las anclas | |
| | | menor, ya existía: con el aviso a la vista, quien completa el sufijo de cada producto en la tarjeta del despachante lo sigue viendo hasta el próximo «Generar» | riesgo, abajo |
| | | estilo: `pintarSufijo` busca el nodo con `getElementById` en vez de usar `hide(sbtError)` | queda: corre antes que `init()`, y `tests/test_valor1c.py:247` la saca sola |

El tercero no corrió nada (había una suite en curso): lo suyo es lectura.

## `/code-review high` sobre `73f8db7..76d9d90`

Los revisores heredan Fable. Dos corridas: la primera leyó la versión rota
(`73f8db7..ca5f257`, ocho hallazgos bajos, ninguno era la rotura) y se
descartó con ella. La segunda, sobre la segunda versión, ocho hallazgos
bajos:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | con el aviso a la vista, llenar el sufijo de cada producto en la tarjeta del despachante no lo esconde | riesgo, abajo: ya era así y la pieza no lo pide |
| 2 | los «Item N: … SBT …» del servidor salen bajo el campo de la operación, y ahora escribir ahí los esconde | D242 |
| 3 | el motivo de un rechazo del servidor se pierde con la primera tecla y al salir y volver con la misma operación | D242 y supuesto 1 |
| 4 | el `goTo` de mentira de `tests/test_avisos1_seguro.py` no modelaba que «Validación» entra sin aviso | arreglado en `80cd954`: supuesto 3, con su negativo |
| 5 | la precondición de la parte nueva del caso era un comentario | arreglado en `80cd954`: ahora es una afirmación (`pantalla_sufijo_otra1.js:89`) |
| 6 | el rechazo tardío de un «Generar» anterior deja un aviso sobre un sufijo que ya no está en el campo | riesgo, abajo: ventana angosta, ya existía |
| 7 | tres formas de esconder el aviso; `pintarSufijo` podría usar `hide($(…))` | queda: la razón de arriba |
| 8 | el comentario de `pintarSufijo` había quedado de tres líneas | arreglado en `e1ecc29` |

Después de esos tres ajustes (un comentario de producto, una afirmación en el
caso y una línea del `goTo` de mentira) no volví a correr `/code-review`:
corrí el adversario de lectura de arriba y todas las puertas sobre
`80cd954`.

`/security-review` y `ataque_aislamiento.sh`: no corresponden. La pieza no
toca sesión, permisos ni datos de otro usuario.

## Comandos

```bash
# desde la raíz del repo, con esta rama; PY es tu python con las dependencias
export PY=/ruta/al/venv/bin/python
# 1. la entrega: rc=0 y «PANTALLA SUFIJO-OTRA OK»
SOLO=sufijo_otra1 env -u DATABASE_URL -u ENVIRONMENT bash scripts/testing/correr_pantallas.sh 80cd954 /tmp/d238-verde
# 2. el arreglo revertido: «FALLA: otra operación entra con el aviso de la anterior a la vista: …»
git worktree add -q --detach /tmp/d238-wt 80cd954
git -C /tmp/d238-wt checkout -q 73f8db7 -- proyecto_maria/static/v2/screens/finalize.js
git -C /tmp/d238-wt -c user.name=x -c user.email=x@x commit -qam descartable
SOLO=sufijo_otra1 env -u DATABASE_URL -u ENVIRONMENT bash scripts/testing/correr_pantallas.sh $(git -C /tmp/d238-wt rev-parse HEAD) /tmp/d238-rojo
# 3. en ese mismo worktree: «1 failed, 16 passed», el caso [sufijo]
(cd /tmp/d238-wt && GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake env -u DATABASE_URL -u ENVIRONMENT $PY -m pytest -q --no-cov -p no:cacheprovider tests/test_avisos1_seguro.py)
git worktree remove --force /tmp/d238-wt
# 4. el camino del rechazo del servidor: «resumen: 2 verdes, 0 rojas»
SOLO="sufijo_borrador1 maria9" env -u DATABASE_URL -u ENVIRONMENT bash scripts/testing/correr_pantallas.sh 80cd954 /tmp/d238-servidor
# 5. producto +7/−1, avisos
python docs/pm/herramientas/chequeo-6.py 73f8db7 80cd954
```

## Puertas

Todas sobre `80cd954`, de a una.

| puerta | salida |
|---|---|
| suite completa de pytest | `6131 passed, 110 skipped, 3 xfailed` en 0:20:51, `rc=0`. La misma cuenta que la tuya sobre `a2c6dc6`: no hay casos nuevos de pytest, cambió uno |
| `compileall -q proyecto_maria` | `rc=0`, sin salida |
| las 34 pantallas (`correr_pantallas.sh 80cd954`) | `resumen: 34 verdes, 0 rojas`, `rc=0` |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, `rc=0` |
| `anclas_perdidas.py 80cd954` | `102 guiones, 2466 anclas medidas y 11 llamadas sin medir`; salida igual a la de `73f8db7`, línea por línea |
| `chequeo-6.py 73f8db7 80cd954` | abajo, entera |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |

**No corrí:** `smoke_friccion.sh` (no toqué backend), `ataque_aislamiento.sh`
ni `/security-review` (arriba), ni los guiones de sabotaje de piezas
anteriores que anclan en `finalize.js` (`sabotaje_maria9.sh`,
`sabotajes/avisos1.sh` y los demás): `anclas_perdidas.py` dice que ninguno
perdió un ancla, pero correrlos enteros es lo de antes de publicar. Las
puertas corrieron sobre `80cd954`; la integración de tu rama vino después y
sólo trae `docs/pm/`.

## `chequeo-6`

```
chequeo-6 73f8db7..80cd954: avisos para mirar, no un veredicto
producto +7/−1
arnés +10/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/screens/finalize.js: 1488 → 1494
avisos: 0
```

## Riesgos

- D242: el motivo de un rechazo del servidor se va con la primera tecla.
- Con el aviso «Es obligatorio» a la vista, quien completa el sufijo de cada
  producto en la tarjeta del despachante (en vez del campo de la operación)
  lo sigue viendo hasta el próximo «Generar», que ya no frena. Ya era así;
  no lo toqué porque la pieza no lo pide.
- Si el rechazo de un «Generar» llega cuando la persona ya cambió el sufijo
  o de operación, el aviso habla de un valor que ya no está. Ventana angosta
  y ya existía; ahora se va al escribir o al volver a entrar.
- El orden «volver y después avisar» depende de que `CDI.goTo` corra la
  entrada de la pantalla en el momento. Si un día `goTo` pasa a ser
  diferido, el aviso del servidor se borra: lo frenan `maria9`,
  `sufijo_borrador1` y el caso `[sufijo]` de pytest.
- No lo probé con una persona ni en un navegador que no sea el Chromium de
  las pruebas.

## Archivos de producto que toqué

`proyecto_maria/static/v2/screens/finalize.js` (`init`, `pintarSufijo` y el
camino del rechazo del sufijo en `generateMaria`) y `CHANGELOG.md`. De
pruebas: `scripts/testing/pantalla_sufijo_otra1.js` y
`tests/test_avisos1_seguro.py`.

## Sigo con

CUIT-GENERAR (D235 a), con revisión fuerte (§3).

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `543671b`). D237 (a) aceptada, D241 (b). D239 y «Holanda» esperan a Emi: no se tocan; D240 (b). D238 (a) entregada sobre `80cd954` (base `73f8db7`, producto `e1ecc29`: `finalize.js`, el aviso del sufijo se va al escribir y al entrar a «Validación», y el rechazo del servidor vuelve a «Validación» antes de poner el aviso), con D242 (el motivo del servidor también se va con la primera tecla; recomiendo (a), queda así) sin contestar. Pieza activa: CUIT-GENERAR (D235 a; apartada con las reversiones `3a6f656` y `2f04637`, se recupera revirtiéndolas; hallazgos del adversario en el scratch `cg_adversario.md`; revisión fuerte §3: suite completa, Opus y Sonnet alto, `/security-review` y `ataque_aislamiento.sh`; sus D toman número nuevo). Después: los vencidos de `sabotajes-conocidos.txt`, uno por pieza, primero `sabotaje_subitems1.sh` y `sabotaje_sufijos1.sh`. Próxima D: D243. Lección de D238: las pruebas de `tests/test_valor1.py`, `test_valor1c.py` y `test_avisos1_seguro.py` sacan funciones de `finalize.js` por nombre; una función auxiliar nueva llamada desde ellas las rompe, y eso sólo lo ve la suite completa. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, sin secretos ni datos reales, VUCE y Gemini simulados, una corrida por vez, un rojo se diagnostica y no se repite hasta verde, las Devs no usan el consejero ni subagentes de esfuerzo muy alto.
