# Reproducción CATALOGO-4 (MARIA), 2026-11-19

Entrega `631bed21` (informe `4e39d414`), base `f3c84f7d`. Producto `+36/−19` en `catalog_service.py`
y `client_memory.py`. La rama de PM, desde la base de la entrega, sólo tocó `docs/pm`: la unión tiene
el mismo producto que `631bed21`.

**Primera entrega: devolución. Vuelta sobre `f5395b9f`: aceptada** (abajo, «Vuelta»). En la primera, los cuatro criterios se cumplen, pero el desempate nuevo le da el empate a
una fila sin NCM y esconde el NCM de la otra en un caso donde la base lo sugería.

## Lo que corrí, sobre `631bed21`, en un worktree limpio

| qué | resultado |
|---|---|
| `tests/test_catalogo4.py` | «1 passed» |
| negativo PM: tres filas empatadas, 6 órdenes de carga × cada una confirmada última | «1 passed»; con el arreglo vaciado, «1 failed» |
| vecinos (`test_catalogo3`, `test_catalogo_largo1/2`, `test_guardar1/2`) | «215 passed» |
| `catalogo4.sh` | 8 ROJO, «sabotajes sin rojo: 0» |
| `catalogo3.sh` | 65 ROJO, «fallas: 0» |
| `catalogo4_postgres.py` en Postgres 16 descartable | «fallas: 0» |
| `chequeo-6.py f3c84f7d 631bed21` | «producto +36/−19», «arnés +197/−7», historia vacía, «avisos: 0» |
| `e2e_maria.sh` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| suite completa | no la corrí: la de MARIA dio «6226 passed, 110 skipped, 3 xfailed» y no hay rojo que la contradiga |

## Lo que encontré: la fila sin NCM gana el empate

Dos productos del mismo proveedor que se parecen igual a lo leído («Tornillo acero inox M8 zincado» y
«… hexagonal», con NCM 73181500 y 84714900). Desde el editor del catálogo se le borra el NCM a una
(`PUT …/productos/<clave>` con `ncm: ""`; `update_product` lo guarda como `None` y sella la fecha).

| a quién se le borra el NCM | base `f3c84f7d` | `631bed21` |
|---|---|---|
| a la segunda cargada | sugiere el NCM de la primera | sugiere `None` |
| a la primera cargada | sugiere `None` | sugiere `None` |

Medido en SQLite con `test_pm_sin_ncm.py` (dos órdenes de carga por fila):
```
631bed21:  FAILED [0]  assert [None, None] == ['84714900', '84714900']
           FAILED [1]  assert [None, None] == ['73181500', '73181500']
f3c84f7d:  FAILED [0]  assert [None, None] == ['84714900', '84714900']
           PASSED [1]
```

- La fila `[1]` es lo que rompe la pieza: verde en la base, rojo en la entrega.
- La fila `[0]` ya pasaba antes (gana la primera cargada aunque no tenga NCM).
- Causa: guardar cuenta como confirmar (supuesto 1), así que borrarle el NCM a una fila la vuelve la
  última confirmada, y el desempate premia a una fila que no tiene nada que sugerir.
- Camino de hoy: sólo el editor del catálogo (`catalogo.js`, `saveProduct` manda el NCM que se ve, que
  puede estar vacío). Un NCM inválido en la carga no se blanquea (`ncm_para_guardar` lo guarda como texto
  o lo rechaza). La carga (`finalize.js`, `saveCatalogLearn`) filtra los productos sin NCM. La
  memoria del cliente no guarda filas sin NCM (`identidad_del_producto` exige uno), así que no entra.

## Otros hallazgos del adversario (sonnet alto, sin red)

- Editar sólo la unidad o el precio por la API mueve el ganador: es el supuesto 1, que acepto.
- El tope de parecido 0,8 para un texto con mitad de letras no latinas empata con un parecido real de
  4/5: coherente con la definición de empate. Riesgo escrito, sin código.
- Mezclar fechas con y sin zona en una misma sesión da `TypeError`; no hay endpoint que lo haga. Riesgo.
- No encontró: claves que no coincidan, cambios en la memoria del cliente ni problemas de costo.

## Vuelta sobre `f5395b9f` (informe `7cbdf2f8`): aceptada

Producto de la vuelta `+5/−4` en `catalog_service.py`: el desempate pasa a
`(bool(row.ncm), *confirmada(row), row.product_key)` y la función se llama `_desempate_del_catalogo`.
La rama (`163ad113`) es igual a `f5395b9f` fuera de `docs/pm`; su base es la cabeza de PM `dfa429c6`.

| qué, sobre `f5395b9f` en un worktree limpio | resultado |
|---|---|
| `test_catalogo4.py` + vecinos (`test_catalogo3`, `test_catalogo_largo1/2`, `test_guardar1/2`) | «217 passed» |
| `test_pm_sin_ncm.py` (el ejemplo de la devolución) y `test_pm_tres.py` | verdes |
| negativo PM, no visto: cuatro empatadas, en los 24 órdenes, borrándoles el NCM a las dos últimas confirmadas con `"   "` | verde; con la regla vaciada, rojo (junto con `SIN_NCM` y los dos de `test_pm_sin_ncm`) |
| negativo PM: borrar el NCM a las dos y devolvérselo a una por el editor | verde; no distingue (con la regla vaciada también pasa: devolverlo la vuelve la última) |
| `catalogo4.sh` | 11 ROJO, «sabotajes sin rojo: 0» |
| `catalogo3.sh` | 65 ROJO, «fallas: 0» |
| `catalogo4_postgres.py` en Postgres 16 descartable | «fallas: 0» |
| `chequeo-6.py f3c84f7d f5395b9f` / `631bed21 f5395b9f` | «producto +37/−19», «avisos: 0» / «producto +5/−4», «avisos: 0»; historia vacía |
| `e2e_maria.sh` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| `git status --short` después de todo | vacío |

No corrí, y son de MARIA: la suite completa («6227 passed, 110 skipped, 3 xfailed»), el negativo en
Postgres con la regla vaciada («fallas: 16») y la cuenta «16 de 20». La regla vive en la clave de
orden de Python, así que Postgres no puede ordenarla distinto.

El ejemplo de tres filas con dos sin NCM que me había guardado ya está en `SIN_NCM` (`_TRES[::2]`): el
que cuenta como no visto es el de cuatro filas. Confirma además que el editor no guarda un NCM de
espacios.

Commits: los dos `fix` tocan sólo `catalog_service.py` y `CHANGELOG.md`; la línea del CHANGELOG dice la
regla final.

Riesgos, decididos por la PM:
- El camino exacto no mira el NCM: es «lo idéntico gana primero» (criterio 1) y la devolución ya decía
  «sólo en empates». Riesgo escrito; cambiarlo sería otra pieza, con Emi.
- El sabotaje «un producto nuevo toma la hora de la base» da rojo sólo si dos altas caen en el mismo
  segundo de SQLite. Nace en la primera entrega de esta pieza (no es de la base) y no lo vi en la
  primera revisión. MARIA lo midió 15 de 15 rojo; en mis dos corridas, rojo. Riesgo del arnés, en
  `COLA-LIMPIEZA.md`.
- Una fila sin NCM cuenta como reconocida en `tasa_reconocimiento`: viene de antes, sin tocar. Riesgo
  escrito.

Adversario de la PM (sonnet alto, sin red, sobre `631bed21..f5395b9f`): el editor (`PUT …/productos/<clave>`)
y `POST /api/catalog/{vendor}/productos` guardan cualquier texto de hasta 20 caracteres como NCM
(`ncm_para_guardar` no valida el formato), y en un empate ese texto le gana a una fila sin NCM. Lo
reproduje: «zincado» con `n/a` y «hexagonal» con el NCM borrado sugiere `'n/a'` en `f5395b9f` y también
en la base `f3c84f7d`. Riesgo escrito: «tener NCM» es texto no vacío; validar el NCM del catálogo sería
otra pieza. No encontró otros llamadores rotos ni cambios sin empate.
