# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## INTERMITENTES: maria1c y maria7 dan lo mismo siempre

| | SHA |
|---|---|
| base | `90b66c5e33cc36b8d563636554b7ca13983696c3` |
| arnés: las pantallas esperan la primera pantalla del tablero | `aa002538847b99f82819ad5819e63868d695f4d9` |
| arnés: `forzar_arranque.js` carga el mismo playwright | `2d76e41963ade79fc96b547811e581959082c17b` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.** La causa de los dos intermitentes es una sola: la subida le gana al arranque del tablero. Con la carrera forzada por la prueba, la pantalla de hoy da las dos FALLAS de siempre y, con el arreglo, las dos dan verde. Producto +0/−0. El arreglo es una espera a una condición que la pantalla muestra (`[data-screen="upload"].is-active`), sin espera fija.

## Decisiones

**D211. Defecto de producto: una subida anterior a la primera pantalla del tablero se pierde o no prende el semáforo.**
`app_v2.js` (alrededor de la línea 958) espera `/auth/current_user` o 4 s y recién ahí hace `goTo('upload')` si no hay pantalla activa. Si la usuaria sube antes:
- si la subida ya terminó (maria1c): fue a revisión sin `currentScreen`, `goTo` no dispara `cdi:screen-leave`, el semáforo no se muestra (`#semaforoFAB hidden data-kind=empty`);
- si la subida sigue en vuelo (maria7): `goTo('upload')` llama a `onEnter`, que hace `++uploadTicket` (`upload.js:706`) y la respuesta se descarta.
Le pasa a una usuaria real con la red lenta. No lo toqué: la tarea es sólo arnés.
- (a) Pieza de producto: que el `goTo` inicial no pise una pantalla ya activa ni una subida en curso. Es `app_v2.js` y `upload.js`, que hoy toca Dev MARIA.
- (b) Dejarlo: el arnés ya no depende de eso.
Recomiendo (a), para quien tenga abierto `upload.js`; `forzar_arranque.js` ya es su reproducción; que el arreglo de producto haga verde las pantallas de la base bajo la carrera forzada no lo probé.

**D212. `orden1` tarda 581 s contra un tope de 600 por pantalla.**
En la corrida completa la corté yo con `TOPE=300` (rc=124 después de su último OK). Sola, con el tope por defecto, dio verde en 581 s: 20 s de margen. En una máquina más cargada se va a cortar.
- (a) Subir el `TOPE` por defecto de `correr_pantallas.sh` a 900.
- (b) Dejarlo.
Recomiendo (a): una línea del arnés, y un tope sigue existiendo.

## Respuestas a lo que pediste

- **¿Tus corridas sueltas usaron un servidor ya tibio?** Sí. Las corridas sueltas de antes iban contra un uvicorn ya levantado y tibio, donde `/auth/current_user` contesta enseguida y la carrera casi no se da. El corredor levanta un servidor nuevo por pantalla; ahí la primera consulta tarda y la subida le gana.
- **maria1c, confirmada.** Con la consulta de sesión retenida hasta que la subida terminó, da la misma FALLA que la intermitente (abajo).
- **Tu hipótesis del escuchador de `upload.js`:** no es. El input es HTML fijo (`dashboard_v2.html:116`), los scripts van con `defer` (`app_v2.js` en la línea 1741, `upload.js` en la 1751) y `upload.js` hace `init()` en `DOMContentLoaded` y otra vez en `onEnter` si hace falta (`upload.js:710`). El escuchador está; lo que falla es lo de D211.

## Forma repetible

`scripts/testing/forzar_arranque.js` se carga antes de la pantalla con `NODE_OPTIONS`. Retiene `/auth/current_user` y lo suelta:
- `maria1c` (modo `terminada`): cuando la página ya pasó a revisión;
- `maria7` (modo `en_vuelo`): cuando sale la subida, y la subida contesta recién cuando el tablero eligió su primera pantalla.
No toca la pantalla ni el producto. Cada log dice `forzar_arranque: <modo>`.

Sobre la pantalla de hoy (90b66c5e):
```
ROJA  maria1c        rc=1   <S>/forz-hoy3/maria1c.log |        - waiting 500ms
ROJA  maria7         rc=1   <S>/forz-hoy3/maria7.log | FALLA: la pregunta por la fecha no aparece al subir
resumen: 0 verdes, 2 rojas: maria1c maria7
```
En `maria1c.log`:
```
FALLA: locator.click: Timeout 30000ms exceeded.
  - locator resolved to <div hidden="" tabindex="0" role="button" id="semaforoFAB" data-kind="empty" class="semaforo-fab" aria-label="Estado de validacion">…</div>
```
Con el arreglo (2d76e419), bajo la misma condición:
```
verde maria1c        rc=0   <S>/forz-arreglo3/maria1c.log | OK: pantalla MARIA-1c
verde maria7         rc=0   <S>/forz-arreglo3/maria7.log | PANTALLA MARIA-7 OK
resumen: 2 verdes, 0 rojas
```
Corrí cada lado tres veces (`forz-hoy`, `forz-hoy2`, `forz-hoy3`; `forz-arreglo`, `forz-arreglo2`, `forz-arreglo3`): las tres rojas y las tres verdes, iguales. Muestro la tercera.

## sesion1

`pantalla_sesion1.js` lleva `// corredor: servidor ENVIRONMENT=testing`. Corrida sin forzar sobre aa002538 (maria1c, maria7 y sesion1: `3 verdes, 0 rojas`), con una vigía que lee el entorno de cada uvicorn:
```
uvicorn pid=1537 ENVIRONMENT=development CDI_DATA_DIR=maria1c.Ok7o
uvicorn pid=1786 ENVIRONMENT=development CDI_DATA_DIR=maria7.r90f
uvicorn pid=2011 ENVIRONMENT=testing CDI_DATA_DIR=sesion1.MOAJ
```
sesion1: «OK: el perfil pide la contraseña sólo al cambiar el email y no saca a nadie al login».

## Huérfano

**Corrijo el informe anterior.** Decía que el corredor «lo retira al salir (también si se corta con Ctrl-C, por el `trap`)». Era falso para un TERM: bash no atiende el trap mientras espera a un hijo en primer plano, y quedaban el uvicorn y el worktree. Ahora el hijo va en segundo plano con `wait` (y `exec`, para que `$!` sea el proceso real), y el trap mata la pantalla y el uvicorn.

TERM a mitad de `borrador1`, corredor de la base:
```
antes:   2346 2325 python … -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port 60493
         2422 2421 node node scripts/testing/pantalla_borrador1.js
rc del corredor: 143
2 s después: 2346 1 python … uvicorn …        (huérfano, ppid 1; también quedó el worktree)
```
Mismo TERM, corredor nuevo:
```
antes:   2602 2581 python … uvicorn …
         2675 2674 node … pantalla_borrador1.js
rc del corredor: 143
2 s después: (nada vivo)
worktrees del corredor: 0
```

## Corrida completa (30 pantallas, aa002538, `TOPE=300`)

```
ROJA  maria3         rc=1   … | Node.js v22.22.0
ROJA  maria4         rc=1   … |        - waiting 500ms
ROJA  maria5         rc=1   … | FALLA: no se generó el TXT: {"detail":"Falta el CUIT del despachante (CDDTAGR)…
ROJA  orden1         rc=124 … | FALLA: page.waitForFunction: Target page, context or browser has been closed
ROJA  subitems1      rc=1   … | FALLA: no se generó el TXT: {"detail":"Falta el CUIT del despachante (CDDTAGR)…
resumen: 25 verdes, 5 rojas: maria3 maria4 maria5 orden1 subitems1
```
- maria3, maria4, maria5 y subitems1: las conocidas de MARIA, que la tarea dice no tocar.
- orden1: la corté yo con el tope (D212). Sola sobre 2d76e419, con el tope por defecto: `verde orden1 rc=0 | OK: ORDEN-1 en el navegador`, `rc=0 segundos=581`.
- aa002538 y 2d76e419 se diferencian sólo en `forzar_arranque.js`, que sin `NODE_OPTIONS` no se carga.

## chequeo-6

```
chequeo-6 90b66c5e33cc36b8d563636554b7ca13983696c3..2d76e41963ade79fc96b547811e581959082c17b: avisos para mirar, no un veredicto
producto +0/−0
arnés +75/−9
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Comandos

```bash
# 1. La carrera forzada sobre la base: tiene que dar 0 verdes, 2 rojas: maria1c maria7
NODE_OPTIONS="--require $PWD/scripts/testing/forzar_arranque.js" SOLO="maria1c maria7" \
  scripts/testing/correr_pantallas.sh 90b66c5e33cc36b8d563636554b7ca13983696c3 /tmp/forz-base
# 2. La misma sobre la entrega: tiene que dar 2 verdes, 0 rojas, y cada log, «forzar_arranque: terminada» o «en_vuelo»
NODE_OPTIONS="--require $PWD/scripts/testing/forzar_arranque.js" SOLO="maria1c maria7" \
  scripts/testing/correr_pantallas.sh 2d76e41963ade79fc96b547811e581959082c17b /tmp/forz-entrega
# 3. Huérfano: cortá con TERM a mitad de una pantalla; después, ps no muestra uvicorn ni node de la pantalla
SOLO=borrador1 scripts/testing/correr_pantallas.sh HEAD /tmp/huerfano & sleep 60; kill -TERM $!; sleep 2; ps -eo pid,ppid,args | grep -E 'uvicorn|pantalla_' | grep -v grep
```
Ojo: el corredor toma desde el SHA las pantallas y `forzar_arranque.js` se carga desde tu árbol; en el 1 tiene que ser un árbol con 2d76e419.

## No corrido

- **Ctrl-C (SIGINT):** no lo pude probar. Un bash no interactivo en segundo plano ignora SIGINT, así que mandarle INT no reproduce un Ctrl-C de una terminal. El trap `INT` está, sin prueba.
- **pytest:** no aplica; la pieza es sólo arnés (producto +0/−0).
- **Subagentes adversariales y `/code-review`:** la tarea dice «sin adversarios»; no los corrí.

## Supuestos y riesgos

- `SOLO` (elegir pantallas en el corredor) es nuevo: lo necesité para correr sólo maria1c y maria7. Se puede sacar.
- La vigía del entorno y el script del TERM son míos, en el scratchpad, no en el repo.
- `forzar_arranque.js` envuelve `chromium.launch`, `newContext` y `newPage`: si una pantalla abre el navegador de otra forma, no fuerza nada; el log lo muestra porque falta la línea del modo.
- Archivos de producto tocados: ninguno.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué INTERMITENTES (aa002538, 2d76e419 + informe); D211 (defecto de producto del arranque, recomiendo pieza para quien tenga upload.js) y D212 (TOPE 900, recomiendo); tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
