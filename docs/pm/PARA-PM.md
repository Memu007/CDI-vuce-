# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## VALIDACION-1, entregada en `c24a266` (producto `0bd4b6c`; informe en el commit de arriba)

COBRO-MP-2 (vuelta) y COBRO-MP-3 siguen en su informe, `a06c0c8`; **D64 y D66 siguen abiertas ahí**. Este informe no las cubre.

### Decisiones

Nada para decidir. Hay una propuesta de pieza aparte en «Riesgos» (el historial con el validador caído), por si la querés.

Supuesto reversible: **una validación en curso ya no impide validar la carga que se ve.** Antes, `validatingInFlight` cortaba la segunda validación si la primera no había terminado; así, la carga B se quedaba sin validar o con la de A. Ahora cada validación toma un turno (`turnoValidacion`) y sólo la más reciente pinta la pantalla. Las viejas siguen hasta el final y su resultado se descarta (riesgo 3).

### Resultado

Lo que se muestra, lo que se guarda en el historial y lo que habilita «Generar» salen de la carga que se ve:

- **El caché de 60 s se usa sólo si el pedido es el mismo** (`lastValidationPedido`, la cabecera y los ítems en JSON). Con otra carga se valida de nuevo, y el resultado anterior se descarta antes de pedir.
- **Una respuesta que llega después de que otra carga pidió no pinta ni guarda nada** (`turnoValidacion`).
- **Con el validador caído:**
  - si es otra carga, el panel queda sin la validación de la anterior y «Generar» no frena por errores ajenos;
  - si es la misma carga, se vuelve a mostrar su resultado, y «Generar» sigue frenando por sus propios errores.
- **Salir de «Listo»** ya no borra la validación (`db31e0e`): toda validación nueva limpia la anterior o reusa la del mismo pedido.

Archivo de producto tocado: `proyecto_maria/static/v2/screens/finalize.js` (`runValidation` y el estado del módulo). Además, `CHANGELOG.md`.

### SHAs

| SHA | qué |
|---|---|
| `18f2928` | base |
| `e59ae3c` | trabajo en curso al corte |
| `e4c79a1` | producto |
| `60023d6` | arnés: `pantalla_validacion1.js` y `sabotajes/validacion1.sh` |
| `0b9d476` | arnés: el caso del validador caído corta la carga que se ve y mira la generación real |
| `db31e0e` | producto: salir de «Listo» ya no borra la validación |
| `193c65d` | merge de tu rama |
| `0bd4b6c` | producto: volver a validar la misma carga con el validador caído conserva su resultado |
| `591f301` | arnés: caso «botón, falla al volver a validar la misma» y espera por respuesta leída |
| `c24a266` | arnés: la misma carga reusa su validación; misma carga con otra cabecera vuelve a pedir |

### Rojo antes que verde

**Base (`18f2928`, `finalize.js` de la base con el arnés de `c24a266`):**

```
OK | panel, misma carga sin cambios
FALLA: panel: muestra 1, $1.387,5, 465 kg; la carga que se ve da 1, $20, 0,4 kg
FALLA: panel, la anterior contesta después: no mostró la validación de la que se ve
FALLA: botón, error sólo en la que se ve: deja generar con el peso en cero
FALLA: botón, error sólo en la anterior: no deja generar por el error de la anterior
FALLA: botón, falla el validador: no deja generar por el error de la anterior
FALLA: botón, falla al volver a validar la misma: deja generar con el peso en cero
FALLA: cabecera distinta, mismos ítems: no volvió a validar con la cabecera cambiada
FALLA: historial: guardó valor 1387.5 y peso 465; la carga que se ve da 20 y 0.4
salida=1
```

«panel, misma carga sin cambios» pasa en la base a propósito: es el reuso legítimo, que la pieza tiene que conservar; su sabotaje está abajo.

**El caso que vino del code-review** (producto `db31e0e`, arnés `591f301`, antes de las dos filas nuevas): pasan 6 casos y falla uno, `FALLA: botón, falla al volver a validar la misma: deja generar con el peso en cero`, salida=1.

**Verde (`0bd4b6c` con `c24a266`):** el BASE del guion de sabotajes de abajo, que exige los 9 OK y `pantalla VALIDACION-1: OK`.

El caso es uno solo, `pantalla_validacion1.js`, con clics en la pantalla real: dos cargas distintas en menos de 60 s. La familia va como datos: panel, la anterior contesta después, botón (error sólo en la que se ve, error sólo en la anterior, falla el validador, falla al volver a validar la misma), historial, la misma carga sin cambios (no vuelve a pedir) y los mismos ítems con otra cabecera (vuelve a pedir).

### Lo que corregí en el camino

- **`0b9d476`, el arnés no distinguía el defecto.** El simulador elegía qué pedido cortar por su número de orden, y la comprobación de que se generó aceptaba `/generate_maria/avisos` como si fuera la generación. Con el resultado de la anterior retenido, el caso «falla el validador» daba OK. Ahora el simulador corta según la carga del pedido, y la comprobación espera exactamente `/generate_maria`.
- **`db31e0e`, saqué las dos líneas de `onLeave`** que borraban la validación. Sobraban: a «Listo» sólo se llega desde la validación.
- **`c24a266`, dos huecos del arnés que encontró el adversario:** todos los casos usaban la misma cabecera, así que sacar la cabecera del pedido no se veía; y ningún caso miraba el reuso legítimo, así que deshacer el caché entero tampoco. Ahora hay una fila para cada uno, con su sabotaje.
- **`0bd4b6c`, regresión mía que encontró el code-review** (hallazgo 3): con el validador caído, volver a validar la misma carga borraba su resultado y dejaba generar con errores ya conocidos. En el mismo commit, el armado del pedido (`cabeceraParaValidar`) vuelve adentro del `try` y el turno se toma primero, como en la base (hallazgo 1).

### Sabotajes, `scripts/testing/sabotajes/validacion1.sh c24a266`

```
BASE  | en verde
ROJO  | el caché no mira de qué carga es: dice «FALLA: panel: muestra»
ROJO  | la respuesta de la anterior pinta la que se ve: dice «FALLA: panel, la anterior contesta después: muestra»
ROJO  | con el validador caído queda el resultado de la anterior: dice «FALLA: botón, falla el validador: el botón está habilitado pero el clic no genera»
ROJO  | volver a validar la misma con el validador caído borra su resultado: dice «FALLA: botón, falla al volver a validar la misma: deja generar con el peso en cero»
ROJO  | con una validación en curso, la que se ve no valida: dice «FALLA: panel, la anterior contesta después: no mostró la validación de la que se ve»
ROJO  | el caché no mira la cabecera: dice «FALLA: cabecera distinta, mismos ítems: no volvió a validar con la cabecera cambiada»
ROJO  | sin caché: siempre vuelve a pedir: dice «FALLA: panel, misma carga sin cambios: volvió a pedir la validación de la misma carga»
FALLAS=0
salida=0
```

### Puertas, sobre `0bd4b6c` (producto) y `c24a266` (arnés)

| puerta | resultado |
|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`) | `4570 passed, 101 skipped, 3 xfailed in 721.36s`, 0 failed, sobre `0bd4b6c`. Después sólo cambió `scripts/testing/`, que pytest no corre |
| `compileall -q proyecto_maria` | salida 0 |
| pantalla `pantalla_validacion1.js` | 9 OK, `pantalla VALIDACION-1: OK` (BASE del guion) |
| sabotajes | 7 ROJO, `FALLAS=0` |
| chequeo-6 | abajo, 2 AVISO con su porqué |
| `/code-review high` (Opus, alto) | 9 hallazgos, tabla abajo |
| `/security-review` (Sonnet alto) | sin hallazgos de confianza 8 o más |
| adversario de comportamiento (Sonnet alto) | sin caminos que muestren, guarden o habiliten con lo de otra carga; 3 pre-existentes (riesgos); 2 huecos del arnés arreglados en `c24a266` |

**`/code-review high`, Opus alto, sobre `18f2928..db31e0e`**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | `cabeceraParaValidar` quedó afuera del `try` y antes del turno | arreglado en `0bd4b6c`. Sin rojo: no encontré un camino real que la haga fallar |
| 2 | con el validador caído y sin validación previa, el historial guarda 0 | ya pasaba en la base; riesgo 1 |
| 3 | volver a validar la misma carga con el validador caído borraba su resultado | arreglado en `0bd4b6c`, con su rojo (arriba) y su sabotaje |
| 4 | espera fija (`setTimeout(0)`) en el arnés | arreglado en `591f301`: espera a que se lean las respuestas |
| 5 | el arnés no miraba la validación de la anterior | arreglado en `591f301` |
| 6 | las respuestas descartadas no llegan a `console.error` ni a la telemetría `validation_error` | riesgo 2 |
| 7 | las validaciones viejas no se cancelan: siguen hasta el final y se descartan | riesgo 3 |
| 8 | el resultado sigue siendo estado del módulo (tres variables) y no de la carga | riesgo 4 |
| 9 | el comentario de `onLeave` habla de limpiar el caché | queda: ahora se refiere al caché de `lastMaria`, que sí se limpia |

**`/security-review`:** sin hallazgos de confianza 8 o más. Miró la caché por pestaña, `logout` con recarga, el XSS (todo pasa por `CDI.escapeHtml` y el diff no agrega `innerHTML`), la telemetría (sólo contadores) y la inyección (`JSON.stringify`). Dejó una observación de confianza 3, que es de corrección y no de seguridad: el pedido que se compara no lleva todos los campos que el servidor podría usar en el futuro.

**Adversario de comportamiento, Sonnet alto, sobre `0bd4b6c`**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | con el validador caído y sin validación previa, el historial guarda 0 y «Listo» dice «$0 USD» | ya pasaba en la base; riesgo 1, ahora con «Listo» |
| 2 | «Calcular seguro» cambia el seguro después de validar y «Generar» no vuelve a comparar el pedido | ya pasaba en la base; riesgo 6 |
| 3 | el pedido que se compara no lleva el vendedor, los gastos anteriores ni los subítems, que sí mira el control de antes de generar | ya pasaba en la base; según el adversario, los frena `/generate_maria` con 400; riesgo 5 |
| 4 | huecos del arnés: una sola cabecera para todos los casos y ningún caso de reuso legítimo | arreglado en `c24a266`, con dos sabotajes |

El adversario no encontró un camino en el que el panel, «Generar» o el historial usen la validación de otra carga.

### chequeo-6, `18f2928 0bd4b6c`

```
chequeo-6 18f2928..0bd4b6c: avisos para mirar, no un veredicto
producto +66/−3383
arnés +257/−929
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/controles_maria.py: 270 → 270
  proyecto_maria/core/ncm_catalog.py: 381 → 380
  proyecto_maria/core/validations.py: 331 → 331
  proyecto_maria/routers/admin_router.py: 403 → 403
  proyecto_maria/services/fecha_inic_activ.py: 27 → 27
  AVISO comentario nuevo de 3 líneas: proyecto_maria/services/fecha_inic_activ.py:1 (§6: una o dos)
  proyecto_maria/services/migration_service.py: 681 → 681
  proyecto_maria/static/v2/montos_ar.js: 91 → 91
  proyecto_maria/static/v2/screens/despachante.js: 498 → 498
  proyecto_maria/static/v2/screens/estudios.js: 238 → 238
  proyecto_maria/static/v2/screens/finalize.js: 1387 → 1391
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1379 → 1383, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 2
salida=0
```

- **Lo propio de la pieza es `producto +36/−32`, en `finalize.js`** (`git diff --numstat 18f2928 0bd4b6c`), más `CHANGELOG.md` +6/−2. El resto del +66/−3383, y los demás archivos, vienen de tus merges: el borrado de `proyecto_maria/tests/` y tu limpieza.
- **AVISO de `fecha_inic_activ.py`:** no es de esta pieza. Entró con un merge.
- **AVISO de `finalize.js:9`:** es la función anónima que envuelve toda la pantalla, y el estado del módulo vive ahí. No hay forma de sumar estado sin que crezca. Partirla va a la cola de limpieza.

### Riesgos

1. **El historial con el validador caído y sin validación previa guarda 0** en valor y peso, y «Listo» muestra «$0 USD». Ya pasaba en la base. Propuesta, como pieza aparte: calcular los totales desde los ítems de la carga cuando no hay validación.
2. **Las respuestas descartadas no se registran.** Si una validación vieja falla después de que otra carga pidió, no llega a `console.error` ni a `CDI.track('validation_error')`, así que la telemetría cuenta de menos las caídas del validador.
3. **Las validaciones viejas no se cancelan.** Siguen en el servidor hasta el final y su resultado se descarta. Se podría cortar con un `AbortController` al tomar un turno nuevo; no lo hice porque la tarea no lo pide.
4. **El resultado sigue siendo estado del módulo** (`lastValidation`, `lastValidationPedido`, `turnoValidacion`), y no de la carga. Hoy cada lector pasa por el pedido o por el turno. Guardarlo en la carga lo haría vacío por construcción en una carga nueva; eso va a la cola de limpieza.
5. **El pedido que se compara** es la cabecera y los ítems que se mandan al validador. Hoy `/api/validate/smart` mira sólo eso (`main.py`, `controles_antes_de_generar(items_data, operacion)` con la cabecera que va en el pedido), así que el mismo pedido da el mismo resultado. Según el adversario, el control de `/generate_maria` mira además el vendedor, los gastos anteriores y los subítems; eso no pasa por el panel y lo frena el servidor con 400. Si el validador un día usa otro dato que no va en el pedido, dos cargas con el mismo pedido compartirían resultado.
6. **«Calcular seguro» después de validar** cambia el seguro sin volver a validar, y «Generar» usa la validación de antes. Es la misma carga y ya pasaba en la base.

### Lo que no se corrió

- La pantalla en otros navegadores: sólo Chromium.
- Contra el validador real con IA: el arnés simula `/api/validate/smart`.
- El adversario de comportamiento no pudo correr Playwright (a su entorno le faltaba fastapi) y probó con un simulador en Node. Los huecos del arnés (hallazgo 4) los reproduje con sus dos sabotajes; los hallazgos 1 a 3 son lectura de código, no los reproduje.

### Para reproducir

```bash
git checkout c24a266
# 1. BASE en verde (los 9 casos), 7 ROJO, «FALLAS=0», «salida=0»
PY=$(which python) scripts/testing/sabotajes/validacion1.sh c24a266
# 2. «avisos: 2», los dos explicados arriba
python docs/pm/herramientas/chequeo-6.py 18f2928 0bd4b6c
# 3. sólo finalize.js: «36	32»
git diff --numstat 18f2928 0bd4b6c -- proyecto_maria/static/v2/screens/finalize.js
```

---

/compact conservar: Dev 1, rama claude/dev-tecnica. VALIDACION-1 entregada en c24a266 más el commit del informe (producto 0bd4b6c), nada para decidir. COBRO-MP-2 vuelta y COBRO-MP-3 en a06c0c8 con D64 y D66 abiertas. Sigue: COBRO-MP-3 si vuelve, AISLAMIENTO-2 / LIMPIEZA-1 → BACKUP-1a → EXCEL-2c. Nada se publica sin el «dale» de Emi; nunca main.
