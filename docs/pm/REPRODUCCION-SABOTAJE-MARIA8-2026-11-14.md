# SABOTAJE-MARIA8: reproducción de la PM

Entrega `50320ff` (informe `87be8f1`, canal `PARA-PM-2.md`). Base `b8571ff`. Sólo
arnés: `sabotaje_maria8.sh` vuelve a encontrar las anclas de los casos 18, 19 y 20, y
sale su línea de `sabotajes-conocidos.txt`. Veredicto: **aceptada sobre `50320ff`**,
con 37 casos válidos; el 20 es D248. D248 (c), decidido por la PM.

## Corrido por la PM (2026-11-14, desde las 06:14 UTC, worktrees descartables)

Con `GEMINI_API_KEY` vacía en las pruebas a mano (el guion pone la suya), SQLite,
`ENVIRONMENT=test` y los modos falsos, desde la copia de `50320ff`. La corrida se
superpuso con la tanda de fondo (`run6`).

- `chequeo-6.py b8571ff7 50320ff1`: producto +0/−0, arnés +8/−4, historia vacía, avisos: 0.
- Diff del guion leído entero: los tres casos y nada más.
- Unión: `git diff --stat 50320ff1 87be8f12 -- . ':!docs/pm'` vacío; integro `87be8f12`.

| criterio | resultado |
|---|---|
| `sabotaje_maria8.sh 50320ff1` | `VERDE sin sabotaje: 46 passed`; 38 `ROJO`, 0 `FALLA` ni `ROJO?`, `rc=0` |
| casos 18, 19 y 20 | `4 failed`, `2 failed`, `2 failed`, igual que el informe |
| `anclas_perdidas.py 50320ff1` | una línea 5 (guiones: 4), varias 1 (guiones: 1); en `b8571ff7`, 6 y 3. `otra cantidad 2` es `valor1b`, ya vencido |

Negativo de D248 (c) repetido por la PM, con más archivos: sacar
`or sufijo_de_la_operacion()` de la línea del renglón da `5 failed, 248 passed` en
`test_maria8`, los dos `test_maria9` y `test_sufijos1`/`2`, entre ellas
`test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion`. Ningún otro guion
ataca esa herencia en la rama del renglón (`sabotaje_sufijos1.sh:92` ataca la del
ítem entero, en la otra dirección).

## Lo que la Dev afirmó y la PM comprobó

«La misma regla ya la atacan `sabotaje_maria9.sh` casos 1 y 9»: **no del todo.** Con
cada uno aplicado sobre `50320ff`, en `test_maria8` y los dos `test_maria9`:

- el caso 1 da `7 failed`, todas con un sufijo de la operación sucio;
- el caso 9 da `2 failed`, las dos por la API.

Ninguno pone roja `test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion`.
Ese caso (todos los renglones con su sufijo y el de la operación vacío) no tiene
una línea que se pueda sacar: lo sostiene que el generador busca el sufijo de la
operación sólo cuando un renglón no trae el suyo. Al retirar el 20, ningún guion lo
nombra. Queda como riesgo aceptado, no como «cubierto por maria9».

## D248: (c), decidido por la PM

(b) no entra por D195 (a): inventa un defecto. Entre (a) y (c), (c) cubre un hueco
medido sin cambiar la cuenta. Lo hace MARIA después de D247 (a).

## Riesgos

- Si el generador nombra mal el renglón en un error de sufijo (`{n}` en lugar del
  lugar en el pedido), ninguna prueba lo ve. La Dev mostró que hoy la API valida
  antes cada sufijo con su número. Aceptado, bajo.
- Que sacar el `.strip()` del sufijo del renglón sobrevive lo dijo el subagente, y
  nadie lo comprobó.
- `50320ff` no pasó por subagente ni por `/code-review`: lo cubre el guion entero,
  que la PM corrió.

## No corrido por la PM

La suite, las pantallas, `e2e_maria.sh`, Postgres, adversario y `/security-review`: la
pieza no cambia producto.
