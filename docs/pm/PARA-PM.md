# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN1-INTERMITENTE, vuelta 2: z22 vuelve a probar la sesión lenta bajo el tope

| | SHA |
|---|---|
| base | `74e3cc74ec97a72a80d12b5311489f6532e9d0ae` |
| arnés: z22, `forzar_orden1.js`, sabotaje ESPERA 2000 | `6d1f1365d73bef636d8db7a158b68b3725f54fbd` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.**
- z22 vuelve a probar Generar con la consulta de sesión lenta pero bajo el tope, y da lo mismo en cada corrida.
  - Cada `/auth/current_user` de la pestaña vuelve a los 3 s, y ninguna vuelve antes de que llegue la de Generar. Así, la que decide siempre es la de Generar, lenta y bajo los 10 s.
  - Sigue tu sugerencia, adaptada: se mantienen los 3 s y la retención se suelta con una condición observable (llegó la consulta de Generar), no con una espera fija.
  - El caso falla también si Generar no comprobó la sesión. Así no puede quedar verde sin probar lo que dice probar.
- Con `ESPERA_SESION_MS` en 2000, `CASOS=z22` da rojo. Ese sabotaje está en `orden1b.sh`, anclado en el código.
- Carrera forzada: la base da la FALLA de siempre y 6d1f1365 da verde.
- La familia (z20a, z21, z23, z24) no comparte la carrera. Su tabla está abajo.
- Producto +0/−0. `chequeo-6`: 0 avisos. El AVISO de la función anónima de la vuelta anterior ya no sale, porque z22 quedó con menos líneas.
- TOPE 900 y maria1c con `chromium.launch()` quedan como estaban.

## La familia: z20a, z21, z23, z24

En estos cuatro casos, la consulta de sesión que decide siempre sale después de que B se registra. `revisarSesion` sólo se dispara cuando `usuarioActual` ve una cookie que no es la del dueño, y eso pasa recién cuando B ya entró. No hay una consulta en el hueco que pueda volver antes de tiempo, como pasaba en z22.

Para comprobarlo, `forzar_orden1.js` ahora también demora 4 s el registro de B con la pestaña abierta (más que los 3 s de `retenerUsuario`) y cuenta cuántas consultas hizo la pestaña mientras tanto.

| caso | forzado, base 74e3cc74 | forzado, arnés | `ESPERA_SESION_MS` 2000, sin forzar |
|---|---|---|---|
| z20a | OK | OK | «FALLA: entró otro usuario y la pestaña de A generó enseguida y la pestaña no se tapa: error: No se pudo comprobar la sesión. Recargá la página.» |
| z21 | OK | OK | «FALLA: entró otro usuario y la pestaña de A guardó un cliente (error: No se pudo comprobar la sesión. Recargá la página.) y la pestaña no se tapa» |
| z23 | OK | OK | «FALLA: con un servidor que no exige CSRF, entró otro usuario y la pestaña de A generó enseguida y la pestaña no se tapa: error: No se pudo comprobar la sesión. Recargá la página.» |
| z24 | OK | OK | «FALLA: entró otro usuario y A apretó «Salir» en su pestaña y la pestaña no se tapa» |

- **Forzado:** las dos corridas dan `resumen: 1 verdes, 0 rojas` y rc=0. Cada caso imprime «forzar_orden1: el registro de B tardó 4 s más; consultas de la pestaña mientras tanto: 0».
  - La base y el arnés coinciden porque no hay carrera que forzar: la pestaña no consulta nada mientras B se registra.
  - El preload de la vuelta anterior no alcanzaba a estos casos: ninguno sale con `ctx.request`, y z24 sale desde la pestaña. El preload nuevo sí los alcanza, y muestra que no hay hueco.
- **ESPERA 2000:** los cuatro dan rojo. Ya probaban la comprobación lenta bajo el tope, y no hacía falta cambiarlos.
- La columna «forzado, arnés» es sobre 6d1f1365 (comando 5). Da `resumen: 1 verdes, 0 rojas`, rc=0, y seis líneas «consultas de la pestaña mientras tanto: 0» (z20a, z20b, z20c, z21, z23 y z24).
- La columna de ESPERA 2000 corrió sobre un commit provisorio, `ab9a2ff2`: el arnés de entonces más `app_v2.js` con 2000. Desde ese commit, el arnés sólo cambió en el orden de los dos chequeos finales de z22, que no toca a la familia. No la repetí sobre 6d1f1365.

## Decisiones

Nada nuevo para decidir. D213 (b) queda para la cola, como dijiste. Siguen abiertas de antes D205, D206 y D208, que tiene Emi.

## Comandos

```bash
PY=<python del venv>; F=$PWD/scripts/testing/forzar_orden1.js
# 1. Carrera forzada sobre el arnés: «seguía retenida a los 10 s», «OK A salió, volvió a entrar y generó enseguida…», 1 verdes, rc=0
NODE_OPTIONS="--require $F" CASOS=z22 SOLO=orden1 PY=$PY scripts/testing/correr_pantallas.sh 6d1f1365 /tmp/f_sha; echo rc=$?; grep -E 'forzar_orden1|FALLA|OK A salió' /tmp/f_sha/orden1.log
# 2. La misma carrera sobre la base: «volvió antes de entrar: 401», «FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')», rc=1
NODE_OPTIONS="--require $F" CASOS=z22 SOLO=orden1 PY=$PY scripts/testing/correr_pantallas.sh 74e3cc74 /tmp/f_base; echo rc=$?; grep -E 'forzar_orden1|FALLA' /tmp/f_base/orden1.log
# 3. Sabotajes de orden1, con el de ESPERA 2000: 30 ROJO, «sabotajes sin rojo: 0», rc=0
PY=$PY scripts/testing/sabotajes/orden1b.sh 6d1f1365
# 4. Corredor completo: «resumen: 30 verdes, 0 rojas», rc=0
PY=$PY scripts/testing/correr_pantallas.sh 6d1f1365 /tmp/pant
# 5. Familia forzada, en la base y en el arnés: cuatro «consultas de la pestaña mientras tanto: 0», 1 verdes, rc=0
for s in 74e3cc74 6d1f1365; do NODE_OPTIONS="--require $F" CASOS=z20,z21,z23,z24 SOLO=orden1 PY=$PY scripts/testing/correr_pantallas.sh $s /tmp/fam_$s; echo rc=$?; grep -E 'forzar_orden1: el registro|FALLA' /tmp/fam_$s/orden1.log; done
# 6. chequeo-6: producto +0/−0, avisos: 0
$PY docs/pm/herramientas/chequeo-6.py 74e3cc74 6d1f1365
```

Para ESPERA 2000 sobre la familia, `orden1b.sh` cubre el rojo de z22. Para ver los otros cuatro, cambiá `const ESPERA_SESION_MS = 10000;` por `2000` en `proyecto_maria/static/v2/app_v2.js` de un worktree de 6d1f1365, commitealo ahí y corré `CASOS=z20,z21,z23,z24 SOLO=orden1` sobre ese commit.

## Puertas, sobre 6d1f1365

**Carrera forzada (comandos 1 y 2):**

Arnés, 6d1f1365:
```
verde orden1         rc=0   <S>/g6d/f_sha/orden1.log | OK: ORDEN-1 en el navegador
resumen: 1 verdes, 0 rojas
rc=0
forzar_orden1: activo
forzar_orden1: la consulta del hueco seguía retenida a los 10 s
OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos
```

Base, 74e3cc74:
```
ROJA  orden1         rc=1   <S>/g6d/f_base/orden1.log |     at UtilityScript.<anonymous> (<anonymous>:1:44)
resumen: 0 verdes, 1 rojas: orden1
rc=1
forzar_orden1: activo
forzar_orden1: la consulta del hueco volvió antes de entrar: 401
FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')
```

**Sabotajes (`orden1b.sh 6d1f1365`):** 30 ROJO, `sabotajes sin rojo: 0`, `rc=0`. Los dos de z22:
```
ROJO  | con la sesión cambiada no escribe aunque sea del mismo usuario: dice «FALLA: A salió, volvió a entrar y generó enseguida y no generó»
ROJO  | la comprobación de la sesión corta antes de lo que tarda: dice «FALLA: A salió, volvió a entrar y generó enseguida y no generó: error: No se pudo comprobar la sesión»
```

**Corredor completo (`correr_pantallas.sh 6d1f1365`):** `resumen: 30 verdes, 0 rojas`, `rc=0`. TOPE 900 sin cambios. orden1 deja 71 líneas `OK`.
```
verde maria1c        rc=0   <S>/g6d/pant/maria1c.log | OK: pantalla MARIA-1c
verde orden1         rc=0   <S>/g6d/pant/orden1.log | OK: ORDEN-1 en el navegador
resumen: 30 verdes, 0 rojas
rc=0
```

**chequeo-6, 74e3cc74..6d1f1365:**
```
chequeo-6 74e3cc74..6d1f1365: avisos para mirar, no un veredicto
producto +0/−0
arnés +94/−5
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos y lo no corrido

- No corrí pytest, `/code-review`, adversarios, smoke ni el ataque de aislamiento. La tarea es sólo de arnés y dice que sin adversarios.
- La familia con ESPERA 2000 corrió sobre un commit provisorio y no la repetí sobre 6d1f1365 (ver arriba). La familia forzada sí corrió sobre 6d1f1365.
- Para marcar la consulta de Generar, z22 mira que `generateMaria` esté en la pila del `fetch`. Si alguien renombra esa función, `comprobo()` da falso y el caso da rojo con «Generar no comprobó la sesión». Es un rojo que avisa, no un verde mudo.
- Si el producto dejara de consultar la sesión al apretar Generar, la retención nunca se suelta: Generar no termina y el caso cae por el tope de la pantalla. Es un rojo, pero con un texto menos claro.
- `tests/test_conexiones1.py` sigue sin seguimiento, por regla; su copia está en el parche.
- Archivos de producto tocados: ninguno. Del arnés toqué `pantalla_orden1.js`, `forzar_orden1.js` y `sabotajes/orden1b.sh`.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué ORDEN1-INTERMITENTE vuelta 2 (arnés 6d1f1365 + informe): z22 retiene current_user 3 s hasta la consulta de Generar, sabotaje ESPERA 2000 en orden1b.sh, la familia z20a/z21/z23/z24 sin carrera (0 consultas en el hueco); D213 (b) a la cola; D205, D206, D208 con Emi; próxima D214; tests/test_conexiones1.py sin seguimiento; espero veredicto.
