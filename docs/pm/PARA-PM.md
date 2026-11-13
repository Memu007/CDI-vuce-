# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN1-INTERMITENTE: z22 da lo mismo en cada corrida

| | SHA |
|---|---|
| base | `74e3cc74ec97a72a80d12b5311489f6532e9d0ae` |
| arnés: z22, `forzar_orden1.js`, TOPE 900, maria1c con `chromium.launch()` | `8e775b2ba325774ebae831af7aa60e7815a3dc14` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.**
- La FALLA de z22 sale de una espera fija del propio caso.
  - z22 retenía `/auth/current_user` durante 3 s fijos.
  - Si `salir` + `entrar` tarda más de 3 s, la consulta retenida se suelta todavía sin sesión y vuelve con 401. Con carga, bcrypt se pone lento y eso pasa.
  - Ante ese 401 la pestaña hace lo que tiene escrito: va al login (`/?next=%2Fdashboard`). `#validatingGenerate` queda en null y aparece la FALLA de tu corrida.
- El arreglo saca la espera fija. La consulta queda retenida hasta volver a entrar, y recién ahí se suelta y se aprieta Generar. La condición que se espera es observable: que `entrar` haya vuelto.
- La carrera se puede forzar, y las dos salidas están abajo:
  - la pantalla de hoy da la FALLA de siempre;
  - la arreglada da verde.
- Producto +0/−0. También van los otros dos pedidos: `TOPE` por defecto 900 (D212 a) y `pantalla_maria1c.js` con `chromium.launch()` (D226).

## Decisiones

**D213. Un 401 que llega tarde, de una consulta hecha antes de volver a entrar, manda al login a una sesión que ya es válida.**
- Es lo que forzó la FALLA. En el arnés la causa era la espera fija, y ya no queda.
- A una usuaria real le puede pasar algo parecido: sale y vuelve a entrar en otra pestaña mientras una consulta de esta pestaña sigue en vuelo con la red lenta. No lo reproduje fuera del arnés.
- Opciones:
  - (a) Pieza de producto para quien tenga `app_v2.js`: antes de navegar al login por un 401, releer `current_user`. Si ahora hay sesión, no navegar.
  - (b) Dejarlo. El arnés ya no depende de eso.
- Recomiendo (b) por ahora. Hace falta salir y entrar en el hueco de una sola consulta, y lo peor que pasa es volver al login con la sesión válida (un clic más), sin pérdida de datos. Si Emi lo ve en uso real, (a), y `forzar_orden1.js` ya es su reproducción.

Las decisiones que siguen abiertas de antes son D205, D206 y D208 (las tiene Emi). D211 y D212 ya las contestaste.

## Comandos

```bash
PY=<python del venv>; F=$PWD/scripts/testing/forzar_orden1.js
# 1. Arreglo con la carrera forzada: «la consulta del hueco seguía retenida a los 10 s», «OK A salió, volvió a entrar y generó enseguida…», resumen 1 verdes, rc=0
NODE_OPTIONS="--require $F" CASOS=z22 SOLO=orden1 PY=$PY scripts/testing/correr_pantallas.sh 8e775b2b /tmp/f_arreglo; echo rc=$?; grep -E 'forzar_orden1|FALLA|OK A salió' /tmp/f_arreglo/orden1.log
# 2. Base con la misma carrera: «volvió antes de entrar: 401», «FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')», rc=1
NODE_OPTIONS="--require $F" CASOS=z22 SOLO=orden1 PY=$PY scripts/testing/correr_pantallas.sh 74e3cc74 /tmp/f_base; echo rc=$?; grep -E 'forzar_orden1|FALLA' /tmp/f_base/orden1.log
# 3. Sabotajes de orden1: 29 ROJO, «sabotajes sin rojo: 0», rc=0
PY=$PY scripts/testing/sabotajes/orden1b.sh 8e775b2b
# 4. Corredor completo: «resumen: 30 verdes, 0 rojas», rc=0
PY=$PY scripts/testing/correr_pantallas.sh 8e775b2b /tmp/pant
# 5. chequeo-6: producto +0/−0, avisos: 1 (ver abajo)
$PY docs/pm/herramientas/chequeo-6.py 74e3cc74 8e775b2b
```

En el comando 2 el preload sale de mi árbol por ruta absoluta, porque la base no lo tiene. El preload se activa sólo en `pantalla_orden1` e imprime `forzar_orden1: activo`; en cualquier otra pantalla no hace nada.

## Puertas, sobre 8e775b2b

**Forma repetible, con el corredor oficial (comandos 1 y 2):**

Arreglo, 8e775b2b:
```
verde orden1         rc=0   <S>/o1/f_8e775b2b/orden1.log | OK: ORDEN-1 en el navegador
resumen: 1 verdes, 0 rojas
rc=0
forzar_orden1: activo
forzar_orden1: la consulta del hueco seguía retenida a los 10 s
OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos
OK: ORDEN-1 en el navegador
```

Base, 74e3cc74:
```
ROJA  orden1         rc=1   <S>/o1/f_74e3cc74/orden1.log |     at UtilityScript.<anonymous> (<anonymous>:1:44)
resumen: 0 verdes, 1 rojas: orden1
rc=1
forzar_orden1: activo
forzar_orden1: la consulta del hueco volvió antes de entrar: 401
FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')
```

Cómo fuerza la carrera `forzar_orden1.js`:
- Cuando la pantalla sale, el login siguiente espera a que la pestaña pida `current_user` y a que esa consulta vuelva, con un techo de 10 s.
- En la base la consulta se suelta sola a los 3 s, sin sesión: vuelve 401 y la pestaña va al login.
- En el arreglo la consulta sigue retenida a los 10 s, porque sólo se suelta después de entrar. Ahí el preload deja pasar el login.
- Las dos ramas imprimen por cuál pasaron.

**Sabotajes (`orden1b.sh 8e775b2b`):**
- 29 ROJO, `sabotajes sin rojo: 0`, `rc=0`.
- El de z22: `ROJO  | con la sesión cambiada no escribe aunque sea del mismo usuario: dice «FALLA: A salió, volvió a entrar y generó enseguida y no generó»`.

**Corredor completo:**
- Salida: `resumen: 30 verdes, 0 rojas`, `rc=0`, con el `TOPE` nuevo de 900.
- orden1 dio `OK: ORDEN-1 en el navegador`, con 71 líneas OK.
- maria1c dio `OK: pantalla MARIA-1c`, ya con `chromium.launch()`.

**chequeo-6, 74e3cc74..8e775b2b:**
```
chequeo-6 HEAD~1..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +55/−5
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:284 <anónima> 1584 → 1585, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

Sobre el AVISO:
- La línea neta que suma es el comentario del porqué («Retenida hasta volver a entrar: soltada antes, sale sin sesión y la pestaña va al login.»). Está para que nadie vuelva a poner un temporizador.
- El resto del cambio en z22 reordena líneas que ya estaban.
- Partir el cuerpo anónimo de 1585 líneas va a `COLA-LIMPIEZA.md`. Lo anoto para que lo encole la PM, porque yo no edito ese archivo.

## Riesgos y lo no corrido

- No corrí la suite de pytest: no toqué producto ni tests de Python.
- Tampoco corrí `/code-review`, adversarios, smoke ni el ataque de aislamiento: la tarea dice sin adversarios y es sólo arnés.
- Que el 401 tardío le pase a una usuaria real (D213) no lo probé fuera del arnés.
- Mientras z22 está retenida, si `entrar` falla, `falla()` corta el caso antes de `soltar()`. Pierde la consulta retenida, pero el proceso termina igual. No es un rojo silencioso.
- `forzar_orden1.js` envuelve `chromium.launch` → `newContext`. Si orden1 abre el navegador de otra forma, el preload no fuerza nada. Se nota porque falta la línea `forzar_orden1: activo`.
- `tests/test_conexiones1.py` sigue sin seguimiento, por regla; su copia está en el parche.
- Archivos de producto tocados: ninguno. Del arnés toqué `pantalla_orden1.js`, `pantalla_maria1c.js`, `correr_pantallas.sh` y `forzar_orden1.js` (nuevo). `pantalla_orden1.js` queda libre para Dev MARIA (D225).

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué ORDEN1-INTERMITENTE (arnés 8e775b2b + informe); D213 (401 tardío tras volver a entrar manda al login, recomiendo b); AVISO de chequeo-6 por la función anónima de pantalla_orden1.js para la cola; tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
