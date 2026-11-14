# D250 (a): reproducción de la PM

Entrega `450f4cb` (informe `01bc9df`, canal `PARA-PM-2.md`). Base `5682f6e`. Sólo arnés:
`tests/test_maria8_subitems_por_posicion.py` (de 46 a 61 pruebas; el caso
`test_los_avisos_dicen_si_todos_los_subitems_llevan_el_mismo_sufijo` con 16 datos y un ítem
vecino de tres renglones) y `scripts/testing/sabotaje_maria8.sh` (de 38 a 39 sabotajes).
Veredicto: **aceptada sobre `450f4cb`**.

## Corrido por la PM (2026-11-14, entre 13:58 y 14:20 UTC)

Las corridas se superpusieron con `run7` de fondo (suite entera sobre `fc5944fc`).

| Qué | Resultado |
|---|---|
| `chequeo-6.py 5682f6e 450f4cb` | producto +0/−0, arnés +50/−6, historia vacía, `avisos: 0` |
| unión `450f4cb..01bc9df` y `450f4cb..origin/claude/dev-maria` fuera de `docs/pm` | vacías |
| copia del guion de `450f4cb` | `61 passed` sin sabotaje; `OK: los 39 sabotajes dan rojo por la razón esperada`, `rc=0` |
| guion de `5682f6e` sobre `450f4cb` | `OK: los 38 sabotajes…`, `rc=0`: nada de lo viejo se rompió |
| guion de `450f4cb` sobre la base `5682f6e` | 37 `ROJO`, 2 `FALLA` (los dos de D250), `rc=1`: ver abajo |
| `anclas_perdidas.py 450f4cb` | 103 guiones, 2510 anclas, 11 sin medir; 0, 0 y 0 |

Negativos míos, en un worktree de `450f4cb`, sobre el archivo de la prueba (`61 passed` sin cambio):

| Cambio en `maria_generator.py` | Resultado |
|---|---|
| el sufijo del aviso cortado en 8 y no en 80 | `16 failed, 45 passed` |
| avisa aunque ninguno lleve sufijo (sin `"" not in`) | `1 failed`, `[ninguno]` |
| avisa aunque los sufijos difieran (`>= 1`) | `2 failed`, `[solo_el_ultimo_distinto]`, `[uno_propio_y_el_resto_hereda_otro]` |
| el sufijo propio no se limpia | `1 failed`, `[propios_iguales]` |
| con un sufijo que no se separa, avisa igual | `2 failed`, `[uno_propio_no_se_separa]`, `[el_de_la_operacion_no_se_separa]` |

## Guion nuevo sobre la base

El guion de `450f4cb` sobre `5682f6e` (las pruebas viejas, `46 passed` sin sabotaje): 37 `ROJO`,
2 `FALLA`, `rc=1`. Fallan justo los dos que D250 tocó: `sin_aviso_sufijo` da rojo pero sin los
datos nombrados `[heredan]` y `[propios_iguales]`, y `aviso_operacion_sin_limpiar` queda verde.
Lo que los atrapa es el arnés nuevo, no algo que ya estaba.

## D251: los cuatro verdes, reproducidos

Los cuatro dan `61 passed` sobre `450f4cb`:
- `:2225` `_enumerar(list(range(ns[0] + 1, ns[-1] + 2)))`;
- `:2242` `los {ns[-1] - ns[0] + 1} sub-ítems`;
- `:2224` `for ns in juntos[:2]`;
- `:2225` `ns[:4]`.

El camino existe hoy: con los renglones A, B, A, `supuestos_declarados` dice «los renglones
1 y 3 van en un solo ítem con 2 sub-ítems» y el aviso del sufijo dice «los renglones 1 y 3
los 2». La causa es una sola: el texto de los renglones y su cantidad salen de la lista del
grupo, y las pruebas sólo usan renglones seguidos, dos grupos como mucho y cuatro renglones
como mucho. La lista la comparte el aviso «van en un solo ítem», que viene de MARIA-8: el hueco
es previo a D250 aunque toque «el texto que muestra» de su criterio 1. Por eso se acepta D250 y
el hueco va como pieza chica (D251 (a)). Decidido por la PM.

## Riesgo 1 de la Dev: `/code-review` sobre `39fa7aa`, no sobre `450f4cb`

Aceptado, decidido por la PM:
- lo que vino después (`39fa7aa..450f4cb`) es sólo arnés, +17/−9, y lo leí;
- mis cinco negativos corrieron sobre `450f4cb`;
- según la Dev, el SHA entregado pasó por la cuarta pasada del adversario; eso no lo verifiqué.

Para que no se reabra, `.claude/skills/entregar/SKILL.md` dice desde hoy sobre qué SHA corre:
el que se entrega, y un commit que nace de sus hallazgos pasa por el adversario.

## Lo demás

- Supuestos 1 a 4: aceptados.
- Riesgo 3 (la tabla de renglones escrita a mano): entra en D251 (a), porque un grupo de cinco
  renglones la rompe.
- Riesgos 2, 4 y 5: aceptados. El 2 es D251.
- Propuestas de la Dev para la cola: los literales `SUCIO` y `LIMPIO`, a la cola. El aviso «van
  en un solo ítem» mirado con un solo ítem y por un pedazo del texto: tiene la misma causa que
  D251 y entra en D251 (a).
- `.upper()`: «previo, fuera de D249» en el acta de D249 y la línea de la cola dicen lo mismo:
  quedó fuera de la pieza y va a la cola a propósito.

## No corrido

- Suite entera, `-k`, `e2e_maria.sh` y pantallas sobre `450f4cb`: sin cambio de producto.
- Los `1176 passed` de los 8 archivos y las 43 mutaciones rojas de la tabla de la Dev: son de
  la Dev.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- `/code-review` de la PM.
