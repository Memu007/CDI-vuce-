# SABOTAJE-SUFIJOS1: reproducción de la PM

Entrega `afeae84` (informe `1215a8a`, canal `PARA-PM-2.md`). Base `4474108`.
Veredicto: **aceptada sobre `afeae84`**. Sólo arnés. D246 (b), decidida por la PM.

## Corrido por la PM (2026-11-14, 04:46–05:10 UTC, worktrees descartables)

Todo con la copia de los guiones de `afeae84`, no la de mi rama.

- `chequeo-6.py 44741085 afeae84`: igual al informe (producto +0/−0, arnés +18/−10,
  historia vacía, avisos: 0). Leí el diff entero: el caso 11 del guion, el bucle
  nuevo de `pantalla_sufijo_otra1.js` y la línea menos de `sabotajes-conocidos.txt`.
- Unión: `git diff --stat afeae84 1215a8a7 -- . ':!docs/pm'` vacío; integré `1215a8a7`.

| corrida | resultado |
|---|---|
| `sabotaje_sufijos1.sh afeae84` | `rc=0` en 300 s, 47 `ROJO`, `OK: los 47 sabotajes dan rojo por la razón esperada` |
| el caso 11 | `ROJO   codigo_vacio_se_genera: 1 failed, 61 passed` |
| `correr_pantallas.sh afeae84`, `maria9 sufijo_borrador1 sufijo_otra1` | `resumen: 3 verdes, 0 rojas` |
| `anclas_perdidas.py afeae84` | «perdida, una línea 6 guiones: 5» |

## Negativos de la PM, cada uno un commit descartable

| cambio en `finalize.js` | sobre | `sufijo_otra1` |
|---|---|---|
| `pintarSufijo` copia el sufijo al campo sólo si la operación trae uno | `afeae84` | `rc=1`, pero por las llegadas viejas («con el sufijo borrado: al entrar … AA(000123)»): no dice nada del dato nuevo |
| `pintarSufijo` esconde el aviso sólo si la operación no trae sufijo | `afeae84` | `rc=1`, `FALLA: otra operación, con su sufijo guardado, entra con el aviso de la anterior a la vista` |
| el mismo | `4474108` | `rc=0`, verde |

El segundo no es otro borde: ahí «la operación no trae sufijo» y «el campo está
vacío» son la misma condición, así que es el negativo de D238 escrito de otra forma.
Reproduce el criterio: con la pantalla nueva da rojo y con la vieja no.

## D246: (b), decidido por la PM

`test_sufijos2.py` lleva `"AA(   )-"` (valor de sólo espacios) entre los datos de
`VACIOS`, que usan `test_un_sufijo_vacio_no_se_genera` y
`test_un_sufijo_vacio_no_genera_y_dice_donde`; `sufijos2.sh:107-110` saca el mismo
`if not limpio.strip():`. La prueba de `test_sufijos1` no agrega una forma de vacío.
Pieza chica después de D245 (a); se acepta con `sabotaje_sufijos1.sh` en 46 `ROJO`,
`sabotajes/sufijos2.sh` entero en `ROJO`, `anclas_perdidas.py` en 6 y
`test_sufijos1.py` y `test_sufijos2.py` verdes.

## Riesgos

El de la Dev (los avisos de una operación sin sufijo no se miran con qué sufijo se
piden) queda como riesgo bajo: el pedido sale de la misma función que el del TXT, que
sí se mira. No se pide.

## No corrido por la PM

Las dos filas de arrastre de la Dev (verde en `c645260`, rojo en `afeae84`): el
arreglo de `afeae84` lo sostiene sólo su medición. Tampoco la suite (no cambió nada
que pytest junte), las demás pantallas, `e2e_maria.sh`, `sufijos2.sh` y los demás
guiones, adversario ni `/security-review`. La corrida se superpuso con la tanda de
fondo (`run6`, sobre `7436c6e5`).
