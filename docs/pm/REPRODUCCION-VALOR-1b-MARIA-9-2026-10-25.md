# Reproducción de VALOR-1b y MARIA-9 — 2026-10-25

Sobre `efa2e08` (informe `8f529d5`; base de comparación `903d141`, la rama
de la PM sin la entrega). Dos revisores adversariales con contexto nuevo,
cada uno con árboles propios de la base y de la entrega: Opus alto (el
seguro, dinero y API) y Sonnet alto (MARIA-9, sufijos y kilos). La PM corrió
los comandos del informe y leyó el diff. Todo local y con sintéticos.

**Veredicto:** VALOR-1b y MARIA-9, **aceptadas con nota**. Ningún TXT
equivocado, ninguna regresión de plata, ningún 500 nuevo. Lo que queda va a
una pieza chica, **VALOR-1c**, antes de SEPARADORES-1.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| `git log --oneline -1 origin/claude/dev-maria` | `8f529d5 docs: la decisión del sufijo general pasa a D18 (D15 ya es de CLIENTE-1b)` |
| `git diff --stat efa2e08 origin/claude/dev-maria -- . ':!docs/pm'` | vacío: el producto de la rama es el probado |
| `git diff --stat 23ba183 efa2e08 -- tests/fixtures/` | vacío: los golden no cambian |
| `pytest tests/test_valor1.py tests/test_maria9_*.py tests/test_maria7_devolucion.py` sobre `efa2e08` | `213 passed, 5 warnings in 29.64s` |
| `scripts/testing/sabotaje_valor1b.sh efa2e08` | «OK: los 23 sabotajes dan rojo por la razón esperada», rc=0 |
| `scripts/testing/sabotaje_valor1.sh efa2e08` | «OK: los 31 sabotajes dan rojo por la razón esperada», rc=0 |
| `scripts/testing/sabotaje_maria9.sh efa2e08` | «OK: los 30 sabotajes dan rojo por la razón esperada», rc=0 |

## Lo que probaron los revisores

**Opus (VALOR-1b):**
- TXT idéntico byte a byte en 86 casos contra la base, salvo el que pedía
  MARIA-9.1 (`misma_posicion_sufijos`: 400 en la base, 200 ahora).
- `MDDTFOB` = FOB de la factura, `MDDTASS` = seguro y `MDDTFLE` = flete en
  todos.
- Pantalla con Playwright, cuatro caminos (P1–P4: cambiar el flete, volver
  de revisión, el descuento, un pedido que cambia mientras viajan las
  cuentas): el botón nunca pone un seguro calculado con cuentas viejas. Es
  un ejemplo distinto del `usarDescuento` que di en la devolución.
- Redondeo: 93,125 sale 93,13; con flete 0,495, 10,01.
- Ningún 500 nuevo.

**Sonnet (MARIA-9):**
- Fuzz de unas 7000 operaciones: `usa_el_sufijo_de_la_operacion` coincide
  con el generador en todas; `/avisos` anticipa el error del generador en
  6432 de 6432.
- 27 de 27 TXT idénticos byte a byte; fuzz de kilos de 4000 sin una
  diferencia de TXT y con los mismos casos frenados.
- `pantalla_maria9.js` OK; `sabotaje_maria9.sh` desde un clon propio,
  30 de 30 en rojo; `138 passed`.

## Hallazgos

| # | Qué | De quién | Gravedad |
|---|---|---|---|
| H1 | **Generar no mira si el seguro calculado sigue valiendo** (`finalize.js:543`). Con el seguro calculado sobre flete 100 y el flete cambiado a 7925 en revisión, el TXT sale con `MDDTFLE=7925.00` y `MDDTASS=14.88`. Sólo la nota dice «El seguro se calculó con otros importes». No es regresión (la base no tenía el botón), pero el TXT queda incoherente consigo mismo, que es lo que buscaba D13. | Opus | plata, baja |
| H2 | Mientras la firma está vieja, lo que se ve tarda en ponerse al día (`finalize.js:312-317`). Nunca aplica el valor viejo. | Opus | cosmético |
| H3 | El mensaje de kilos nombra sólo el renglón que da cero solo cuando otro da cero por el ajuste. Con kilos 0,005, 0,005, 0,005 y 0,004 nombra sólo el 4; corregido el redondeo, dan cero del 1 al 4. 14 de 601 casos del fuzz. | Sonnet | baja |
| H4 | `/avisos` avisa por un general que nadie usa (el bloque cerca de `main.py:1826-1834` no usa la función nueva). Con `AA(X=Y)` sin usar, `/avisos` dice «sale «AA(X Y)»» y `/generate_maria` da 400 por el `=`. Es D18. | Sonnet | baja |
| H5 | Con `items=[]` y general `""`, ahora sale 200 con un TXT sin `[ART]` (la base daba 400). Con un general válido ya pasaba (`main.py:4341`). | Sonnet | baja |
| H6 | Detalles nuevos de mensaje: se acepta `"1_000"`; `""` sale con comillas vacías «»; `"nan"`, `"inf"` y `"1e400"` en un renglón no dicen el número de renglón. | Opus | cosmético |

### Pruebas que no distinguen (mutaciones que siguen en verde)

| Mutación | De quién | Cambia algo real |
|---|---|---|
| El flete sin redondear en el seguro (`maria_generator.py:934`): el sabotaje `_exacto(flete)` queda verde. FOB 1000 con flete 0,495 los separa. | Opus | un centavo |
| La firma del pedido sin los ítems (`finalize.js:251`) | Opus | sí: un cambio de ítem no pide cuentas nuevas |
| Sacar `pintarValor(null)` (`finalize.js:84`) | Opus | pantalla |
| `None` en vez de `request.iva_adicional` en `main.py:4341` | Sonnet | sí: un caso con IVAAD1 da 200 o 400 |
| `None` en la línea 1837 del generador | Sonnet | — |
| En `/avisos`, `request.items` en vez de los ítems con la procedencia (`main.py:4212`). El de `/generate_maria` (`main.py:4341`) sí da rojo: sabotaje 30, `endpoint_sin_procedencia` | Sonnet | sí: el arreglo de `58f2f79` |
| El número de renglón del error de kilos como índice dentro del ítem | Sonnet | mensaje |

### De antes de esta pieza (riesgo, no se arregla acá)

- Flete o seguro `true` por API cuentan como 1,00.
- `valor_unitario` `"abc"` en `/generate_maria` da 400 con texto de Python
  (la devolución pedía que `/generate_maria` respondiera como antes).
- `grupo_id` como lista da 500.
- `items: []` con un general válido da 200.

## D18

El general se escribe sólo en `CSBTSVL` y siempre pasa por
`limpiar_sufijo`. Si nadie lo usa, no se escribe: saltear los controles de
`=`, caracteres de control y largo no rompe el formato (Sonnet, por
lectura y fuzz). Decidido por la PM: **(b)**, con H4 (`DECISIONS.md`).

## Lo que no se corrió

- La suite completa sobre `efa2e08` (la Dev sí: `2165 passed, 102 skipped,
  2 xfailed`).
- Smoke, `e2e_maria.sh` y `pantalla_maria9.js` por la PM (el último lo
  corrió Sonnet).
- `sabotaje_valor1b.sh` por Opus (arma un worktree; lo corrió la PM).
- La restauración con un seguro calculado (por lectura: `review.js:320-344`
  no lo borra, `:688` sí).
- La carrera real del retardo de 400 ms y la entrada de 1 MB.
- Nada contra producción.
