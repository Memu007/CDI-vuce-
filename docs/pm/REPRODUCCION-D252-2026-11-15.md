# D252 (a): reproducción de la PM

Entrega `bd009cc` (informe `e4561dc`, canal `PARA-PM-2.md`). Base `993825b`. Sólo arnés:
`tests/test_maria8_subitems_por_posicion.py` (de 77 a 83 pruebas) y
`scripts/testing/sabotaje_maria8.sh` (de 43 a 63 sabotajes). Veredicto: **aceptada sobre
`bd009cc`**.

## Corrido por la PM (2026-11-15, entre 04:30 y 05:00 UTC)

Las corridas se superpusieron con `run9c` de fondo (tanda de sabotajes sobre `fc5944fc`).

| Qué | Resultado |
|---|---|
| `chequeo-6.py 993825b bd009cc` | producto +0/−0, arnés +157/−8, historia vacía, `avisos: 0` |
| `git diff --stat 993825b bd009cc` | sólo los dos archivos de arriba, 157+/8− |
| `bd009cc..e4561dc` fuera de `docs/pm` | vacío; la Dev sólo tocó `PARA-PM-2.md` |
| copia del guion de `bd009cc` | `83 passed` sin sabotaje; 63 `ROJO`, 0 `FALLA`, «OK: los 63 sabotajes dan rojo por la razón esperada», `rc=0`; los 8 pedidos (44, 45, 46, 48 a 52) dan `4`, `2`, `2`, `5`, `3`, `3`, `2` y `1 failed`, como en el informe |
| guion de `993825b` sobre `bd009cc` | 43 `ROJO`, 0 `FALLA`, «OK: los 43…», `rc=0`: nada de lo viejo se rompió. Se corrió primero por error (el guion del árbol de la PM en vez de la copia del SHA); queda como esta fila |
| `anclas_perdidas.py bd009cc` | 103 guiones, 2534 anclas, 11 sin medir; perdidas 0, 0 y 0 |
| su bloque 3 (filas 16 y 88 contra «el resto», 21 archivos) | `83 passed` y `1264 passed, 2 xfailed` en las dos, como en el informe |

Negativos míos, en un worktree de `bd009cc`, con `python -B` y sin `.pyc`. Cada cambio se
midió con la prueba de `bd009cc` y con la de `993825b` (`83 passed` y `77 passed` sin cambio):

| Cambio en `proyecto_maria/core/maria_generator.py` | prueba de `bd009cc` | prueba de `993825b` |
|---|---|---|
| sufijos: `idx - 1 not in en_renglones` → `idx not in en_renglones` | `4 failed, 79 passed` | `77 passed` |
| sufijos: `f" del grupo {gid}"` → `f" del grupo {idx}"` | `2 failed, 81 passed` | `77 passed` |
| arancel `:1967`: `f"grupo {item['grupo_id']}"` → `f"grupo {n + 1}"` | `2 failed, 81 passed` | `77 passed` |

Los tres son de la familia del punto 2 del criterio (un renglón que va solo, con o sin grupo,
entre dos que van juntos), dan rojo sólo con la prueba nueva y no están en sus 115 cambios (su
fila 18 es otro: `(n + 1, …` sin «grupo»). El tercero cubre la mitad del arancel.

## Las D

- **D255 (a)**, decidida por la PM: línea para la cola de limpieza. Sacar `en_renglones` y el
  parámetro `juntos` de `_avisos_del_arancel` es producto y resta; el sabotaje 52 se va con ellos.
- **D256 (a)**, decidida por la PM: límite escrito. Con el aviso de cada renglón antes de
  «Sub-ítems: …» no se pierde ni cambia ningún aviso, sólo el orden.
- **D257 (b)**, decidida por la PM: pieza chica, con el criterio por causa en `PARA-DEV-2.md`:
  un segundo grupo (filas 88 y 53) y un grupo sin sufijo propio (filas 55 y 72). Igual que
  D253 y D254, la familia A (topes y cola), la posición del grupo (filas 106 y 104), las filas
  60, 39 y 54 (nada visible o pedido rechazado) y la familia C quedan como límite escrito.

## Supuestos y riesgos

- **Supuesto 1** (12 de los 20 sabotajes nuevos no se pidieron: 47, 53 a 58 y 59 a 63):
  aceptado. Cada uno fija lo que un commit de la entrega rompió y otro arregló. Recortarlos es
  opcional dentro de D257 (b), que abre el mismo archivo; los más débiles frente a «un caso
  por causa» son 59 a 63.
- **Supuestos 2 a 8:** aceptados.
- **Riesgos 1 y 4 a 9:** aceptados.
- **Riesgo 2** (`test_despacho1b`): sigue abierto. No frena D252; frena proponerle a Emi el
  «dale» de `fc5944fc`, donde `sabotajes/despacho1b.sh` también dio `rc=124` en la tanda de la
  PM. Se mide solo y sin carga cuando termine la tanda.
- **Riesgo 3** («renglón» contra «ítem» en el aviso del arancel): pregunta para el
  despachante, como el riesgo 6 de D251. Queda en esta acta y va a Emi si consulta al
  despachante por otra cosa.

## Lo que se arregla en documentos de la PM

- `docs/pm/COLA-LIMPIEZA.md`: el «hoy `43`» pasa a 63, y entran las cuatro líneas que propuso
  (el texto del arancel desde `sufijos_arca`, `-k` en los sabotajes 44 a 63, `LIMPIO` →
  `SE_LIMPIO`, y la de D255 con el sabotaje 52).
