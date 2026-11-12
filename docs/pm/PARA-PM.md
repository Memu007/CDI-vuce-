# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 J: D188, pares de alta y D205 en el caso natural (sólo arnés)

**Resultado.** La puerta de D188 se cumple sin forzar: en HEAD, «recarga +
alta» con créditos extra vencidos pierde la recarga en **20/20** rondas, sin
deadlock (las dos respuestas dan 200). `chequeo-6`: producto +0/−0, 0 avisos.

Lo que mide el natural, nuevo:

- **D188** se reproduce en HEAD (20/20) y con NO KEY (18/20). NO KEY no lo
  arregla.
- **D205** se reproduce: la renovación da 200, el guardado 402, y la cuenta
  queda `past_due` con el período por delante en 37/40 (HEAD) y 31/40 (NO KEY).
- **Pares de alta:** deadlock en HEAD 5, 8 y 11 de 20; con NO KEY 11, 7 y 10.
  NO KEY saca los deadlocks de las recargas (36 → 0) pero no los de alta: el
  ciclo es entre filas de `users` y `organizations`, no la llave del FK.

| SHA | qué |
|---|---|
| d3f24272 | `test:` el natural suma las filas de D188, los pares de alta y D205 |
| dcd820e0 | merge de la rama de la PM (sólo `docs/pm`) |
| 4f0cfbbd | `test:` cada fila con rótulo; un 402 admitido no cuenta como perdedor |
| (este) | `docs:` informe |

## Decisiones

**D208. ¿Los deadlocks de los pares de alta entran en la pieza de producto CONEXIONES-1?**

En HEAD, cuando el alta de una operación manual (`/api/operations/manual`,
consume una operación) coincide con un guardado, una cancelación o una
reactivación de la misma org, una de las dos da 500 en el 25 al 55 % de
las rondas. El SQL de los deadlocks (primera corrida de J sobre d3f24272, NO KEY) muestra
`organizations ... FOR UPDATE` y `FOR NO KEY UPDATE OF organizations`
contra `users ... FOR NO KEY UPDATE OF users`: los dos caminos toman las
mismas filas en orden distinto.

- (a) Entran: la pieza fija un orden único de toma (primero la org,
  después el usuario) en los caminos del par. Hay que medir cuál de los caminos lo invierte antes
  de escribirlo.
- (b) Pieza aparte, después de CONEXIONES-1: CONEXIONES-1 queda con lo que
  ya tenía.
- (c) No se arreglan: es un 500 en un choque raro (dos acciones de la misma
  org en el mismo instante) y el usuario reintenta.

Recomiendo **(b)**: la causa es otra (orden de filas, no el FK que arregla
NO KEY) y meterla agranda una pieza que ya toca dinero. Pero el perdedor
puede ser el alta (2 o 3 por fila en HEAD) y quien carga ve un 500 al cargar
una operación: si eso pesa, (a).

Nada más para decidir. D205 y D206 siguen con Emi.

## Comandos

```bash
PY=<venv con requirements>
# HEAD: rc 1, «rondas con deadlock: ~60, recargas perdidas: ~20, cuentas mal: ~37»
N=20 PY=$PY timeout 1500 scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_natural.py
# NO KEY: rc 1, recargas 0/20 deadlock por fila; las de alta siguen con deadlock
N=20 PY=$PY PARCHE=conexiones1_parche_nokey.diff timeout 1500 scripts/testing/conexiones1_con_parche.sh scripts/testing/conexiones1_natural.py
docs/pm/herramientas/chequeo-6.py d958df7a 4f0cfbbd
```

Los números varían de corrida a corrida; los ceros (créditos al día, y las
recargas con NO KEY) no cambiaron entre la corrida sobre d3f24272 y esta.

## Medición (N=20, una corrida de cada una, sobre 4f0cfbbd)

N=20: con 10 la corrida I ya mostraba la forma; 20 da margen para que un
0/20 signifique algo.

| fila | HEAD deadlock | HEAD mal | NO KEY deadlock | NO KEY mal |
|---|---|---|---|---|
| recarga + guardado, vencidos | 17/20 (pierde guardado 13, recarga 4) | 0 | 0/20 | 0 |
| recarga + guardado, al día | 0/20 | 0 | 0/20 | 0 |
| recarga + maria, vencidos | 19/20 (pierde maria 19) | 0 | 0/20 | 0 |
| recarga + maria, al día | 0/20 | 0 | 0/20 | 0 |
| **recarga + alta, vencidos (D188)** | 0/20 | **20/20** | 0/20 | **18/20** |
| recarga + alta, al día | 0/20 | 0 | 0/20 | 0 |
| alta + guardado | 5/20 (guardado 3, alta 2) | — | 11/20 (guardado 8, alta 3) | — |
| alta + cancelar | 8/20 (cancelar 6, alta 2) | — | 7/20 (cancelar 4, alta 3) | — |
| alta + reactivar (org cancelada) | 11/20 (reactivar 8, alta 3) | — | 10/20 (alta 7, reactivar 3) | — |
| **renovación + guardado, prueba vencida (D205)** | 0/20 | **18/20** | 0/20 | **16/20** |
| **renovación + guardado, active fuera de gracia (D205)** | 0/20 | **19/20** | 0/20 | **15/20** |
| total | 60 | 20 recargas + 37 cuentas | 28 | 18 recargas + 31 cuentas |

«—»: los pares de alta miden deadlock y códigos, no el estado final.
Todo perdedor de un deadlock dio 500. Las dos corridas salen rc=1.

Líneas textuales:

- D188 (las 20 de HEAD y las 18 de NO KEY):
  `recarga + alta | créditos vencidos | recarga 200, alta 200 | pago aplicado, créditos 0/10 vencidos | RECARGA PERDIDA`.
  Las otras 2 de NO KEY: `pago aplicado, créditos 10/10 vigentes`.
- D205: en las 80 rondas, `renovación 200, guardado 402`. Terminan
  `past_due, período por delante` 37 (HEAD) y 31 (NO KEY); el resto, `active`.
- Las 4 recargas que perdieron el deadlock en HEAD: `recarga 500, guardado 200 |
  pago sin fila, créditos 0/10 vencidos | reintento 200: pago aplicado,
  créditos 10/10 vigentes`. El reintento del aviso las recupera.

## Dónde va cada medición

Las tres van como filas de `FILAS` en `conexiones1_natural.py` (la
sugerencia de la PM): comparten barrera, ronda y conteo de deadlocks. El
archivo tiene 92 líneas, 12 más que el ~80 de §6. Partir D205 a su propio
caso duplicaría la barrera y la ronda; si la PM lo prefiere separado, es un
cambio de arnés sin efecto en las mediciones.

`VENCIDAS` se importa de `conexiones1_renovacion.py` (no lo toqué).
`AL_DIA` queda copiado de `conexiones1_pares.py` como `CREDITOS["créditos al día"]`.

## Puertas

`chequeo-6 d958df7a 4f0cfbbd`, salida entera:

```
chequeo-6 d958df7a..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +53/−38
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Archivos de producto tocados: ninguno.

## Revisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| adversario | Sonnet, alto | la renovación no reintenta después de un deadlock: falso D205 | Los logs lo refutan (80/80 renovaciones 200). Igual: cuenta mal sólo si la renovación dio 200 |
| adversario | Sonnet, alto | «pierde» nombraba al guardado cuando su 402 es el admitido | Corregido |
| adversario | Sonnet, alto | las filas de alta no miden el estado final | Aceptado: dicho en el docstring y acá |
| adversario | Sonnet, alto | un verde no prueba que los pedidos se solaparon | Riesgo, abajo |
| adversario | Sonnet, alto | el total de deadlocks mezclaba unidades | Los números coincidían; ahora suma `bool` por ronda |
| adversario | Sonnet, alto | menores: rótulo `ajuste[:40]`, `"=" in ajuste` | Corregido con rótulo aparte |
| `/code-review` | Opus, alto | renovación sin reintento (igual que arriba) | Igual que arriba |
| `/code-review` | Opus, alto | «recargas perdidas» suma seis filas | La línea por fila muestra que vienen sólo de recarga + alta |
| `/code-review` | Opus, alto | pierde/402; reintento elegido por posición; `"="`; `VENCIDAS` copiado; ESTADO sin recarga; rótulos | Corregidos |
| `/code-review` | Opus, alto | ramas por nombre y más de 80 líneas | Queda: ver «Dónde va cada medición» |

## Riesgos y lo no corrido

- Una ronda sin deadlock ni rojo no prueba que los dos pedidos se
  solaparon: sin tomar la fila desde afuera, sólo lo muestra un deadlock o
  un estado mal.
- Las filas de alta no miden el estado final de la org.
- `PEDIDOS["recarga"]` de `conexiones1_rondas.py` queda sin usar en este
  caso: la recarga necesita el `pid` para el reintento.
- **No corrido:** suite, e2e, arneses de otras piezas y un sabotaje aparte.
  No hay producto en la pieza; el rojo es la medición misma.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué CONEXIONES-1 J (D208 abierta); espero veredicto, nada «apenas entregues».
