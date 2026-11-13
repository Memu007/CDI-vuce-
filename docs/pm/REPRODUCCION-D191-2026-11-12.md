# D191 (a) de la Dev MARIA: reproducción de la PM (2026-11-12)

Entrega `f1809e95` (anclas `c9d1d954`, mutaciones del 2 y el 3 `f1809e95`,
informe `07bcee12`) en `claude/dev-maria`, base `3ff4e77`. Sólo arnés:
`scripts/testing/sabotaje_maria9.sh` con las anclas de hoy.

## Lo corrido

| qué | resultado | informe de la Dev |
|---|---|---|
| `sabotaje_maria9.sh f1809e95` (copia en el scratchpad, venv de la PM) | `VERDE pantalla sin sabotaje`, 29 `ROJO`, `FALLA endpoint_sin_procedencia: quedó verde`, rc=1, 290 s | igual |

Corrió a la par de la reproducción de la limpieza de CONEXIONES-1 (otro
worktree, PG 16 propio).

## D192: la prueba del 30 todavía distingue

Cada mutación sola sobre `f1809e95`, en un worktree descartable:

| mutación | qué corrí | resultado |
|---|---|---|
| `main.py:5073` `items = _items_con_procedencia(request)` → `items = request.items` | `test_maria3_antes_de_generar.py`, `test_punta_a_punta1.py` | 22 failed, 121 passed, 2 xfailed (igual que la Dev) |
| la misma | `test_el_endpoint_agrupa_con_la_procedencia_de_la_operacion` sola | 1 passed |

La misma prueba sola, con la mutación de cada sabotaje que toca
`usa_el_general` o la condición del propio (cada ancla aparece una vez):

| sabotaje | mutación | resultado |
|---|---|---|
| 2 | `if usa_el_general:` → `if False:` | passed |
| 3 | `if usa_el_general:` → `if True:` | passed |
| 7 | `elif sin_propio(item.get("sufijo")):` → `elif True:` | **failed** |
| 8 | `elif sin_propio(item.get("sufijo")):` → `elif False:` | passed |
| 9 | `if not sbt_raw and usa_el_general:` → `if not sbt_raw:` | **failed** |
| 10 | `if not sbt_raw and usa_el_general:` → `if False:` | passed |

La prueba no mira la procedencia, pero sí que el endpoint no pida el sufijo
de la operación cuando cada renglón trae el suyo. Por eso D192 va (a) y no
(b): se saca el sabotaje 30 y la prueba queda, con otro nombre.

## El escape es más ancho que SUFIJOS-1

Cuántas veces aparece cada ancla vieja en `proyecto_maria/core/maria_generator.py`:

| ancla vieja | `3df999c8^` | `3df999c8` | `a099655` | `fe95a49b^` |
|---|---|---|---|---|
| 24 `if min(valores).quantize(Decimal("0.01"), ROUND_HALF_UP) <= 0]` | 1 | 0 | 0 | 0 |
| 27 `chicos = chicos or [lugar_en_el_pedido[id(r)] for r in renglones]` | 1 | 0 | 0 | 0 |
| 28 `for r, *valores in zip(renglones, *propios)` | 1 | 0 | 0 | 0 |
| 2 a 10 `usa_el_sufijo_de_la_operacion(items, iva_adicional)` | 1 | 1 | 1 | 1 |

- La última vez que el guion dio 30 de 30 fue sobre `efa2e08` (VALOR-1b,
  `REPRODUCCION-VALOR-1b-MARIA-9-2026-10-25.md`). `3df999c8` no está en
  `efa2e08`.
- VALOR-1c (`3df999c8`) cambió las anclas 24, 27 y 28. Se aceptó sobre
  `a099655`, que la contiene; su acta
  (`REPRODUCCION-SEPARADORES-1-VALOR-1c-2026-10-25.md`) corrió
  `sabotaje_valor1c.sh` y `sabotaje_separadores1.sh`, no este.
- Después, SUFIJOS-1 (`fe95a49b`) cambió las de 2 a 10 y la del 30.

El acta de D145 nombraba sólo a SUFIJOS-1: queda corregida acá.

## No corrido

- La suite y `e2e_maria.sh`: la pieza no toca producto.
- `chequeo-6`: lo corrió la Dev (+0/−0, arnés +13/−13, 0 avisos); lo corro
  sobre la vuelta.

## Vuelta: aceptada sobre `4723280` (2026-11-12 16:05 UTC)

Commits: prueba `3dbf198`, `5f9a16e` y `4723280`; guion `63066ce`. Cada uno
toca un solo archivo.

- **El guion, entero.** Lo corrí con el `sabotaje_maria9.sh` de `4723280`
  (`git show`, `cmp` igual al del worktree) y la venv `/tmp/cdi-pm/venv`,
  de 15:56 a 16:00 UTC. Dio 29 `ROJO`, `VERDE pantalla sin sabotaje`,
  «OK: los 29 sabotajes dan rojo por la razón esperada» y rc=0.
- **`tests/test_maria9_sufijo_operacion.py`:** 27 passed.
- **`chequeo-6`:**
  - contra `c8247e95`, que incluye la primera entrega de D191: producto
    +0/−0, arnés +16/−22, 0 avisos;
  - la Dev midió contra la unión: +4/−10, 0 avisos. El producto es igual en
    las dos, así que vale para la unión.
- **La mutación del 9** (`if not sbt_raw and usa_el_general:` →
  `if not sbt_raw:`): 2 failed, la renombrada y
  `…los_renglones_con_propio_generan[]`.
- **La de la Dev** (`"sufijo": None` en `_items_con_procedencia`, `main.py:4852`):
  1 failed, sólo la renombrada. Reproduce su «única».
- **Mi negativo:** saqué el sufijo de todo renglón sin `pais_procedencia`
  propio, justo después de `_items_con_procedencia`. Dio 3 failed
  (`…generan[ROJO]`, `…generan[]` y la renombrada).
- `git grep` del nombre viejo de la prueba en `scripts`, `tests` y `.github`
  de `4723280`: vacío.
- **Error mío:** la primera corrida usó el guion de mi rama, que tiene las
  anclas viejas. Dio `PATRON NO ENCONTRADO` en el 2 y rc=1. No es de la
  entrega.

No corrido: la suite y `e2e_maria.sh`, porque el producto no cambia; los
otros guiones de sabotaje.
