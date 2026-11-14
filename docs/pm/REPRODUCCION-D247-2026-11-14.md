# D247 (a): reproducción de la PM

Entrega `4a58c68` (informe `ee3ccfd`, canal `PARA-PM-2.md`). Base `87be8f1`. Sólo
arnés: `VACIOS` pasa a pares (sufijo, código que nombra el error) y `sufijos2.sh`
suma el sabotaje «el error del vacío nombra el sufijo entero y no el código».
Veredicto: **aceptada sobre `4a58c68`**. D249 (a), decidido por la PM.

## Corrido por la PM (2026-11-14, entre 06:52 y 07:01 UTC, worktrees descartables)

Con `GEMINI_API_KEY` vacía, SQLite, `ENVIRONMENT=test` y los modos falsos. La corrida
se superpuso con la tanda de fondo (`run6`).

- `chequeo-6.py 87be8f12 4a58c68c`: producto +0/−0, arnés +12/−2, historia vacía, avisos: 0.
- Diff leído entero: sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`.
- `git grep VACIOS`: sólo en `tests/test_sufijos2.py`.
- Unión: `git diff --stat 4a58c68c ee3ccfdc -- . ':!docs/pm'` vacío; integro `ee3ccfdc`.

| criterio | resultado |
|---|---|
| las dos pruebas sin cambio | `171 passed` |
| `«{uno[0][:40]}»` → `«{sufijo[:40]}»` en «está vacío» | `4 failed, 167 passed` en `4a58c68` (las cuatro de `test_un_sufijo_vacio_no_se_genera`); `171 passed` en `0224f01` |
| `sufijos2.sh 4a58c68c` | BASE `110 passed`; 33 `ROJO`, 0 `ROJO?`, 0 `FALLA`; «sabotajes sin rojo: 0»; `rc=0`; el nuevo en `ROJO` con los 4 ids |
| `sabotaje_sufijos1.sh 4a58c68c` | 46 `ROJO`, 0 `ROJO?`, 0 `FALLA`; «OK: los 46 sabotajes dan rojo por la razón esperada»; `rc=0` |
| `anclas_perdidas.py 4a58c68c` | 103 guiones; una línea 5 (guiones: 4), varias 1 (guiones: 1), otra cantidad 2 (guiones: 1, `valor1b`, ya vencido) |

Negativos propios de la PM:

- `«{uno[0][:40].replace(' ', '')}» está vacío`: `1 failed`, el de `[AA(   )-]`.
- orden cambiado (`«…» no se genera: está vacío. Escribí`): `4 failed`.

## D249 medida en la familia

La Dev midió dos fragmentos de `limpiar_sufijo` que nadie distingue. La PM midió la
familia entera, cada cambio solo, sobre `4a58c68`, en las dos pruebas:

| cambio | resultado |
|---|---|
| «cambiaría»: `en «{sufijo[:40]}»` | `171 passed` (de la Dev) |
| «pide»: `«{sufijo[pos:pos + 40]}»` | `171 passed` (de la Dev) |
| «pide»: `«{sufijo[:40]}»` | `1 failed` (`…no_acepta_decimales[AA(X)-ZB(16.384)-CA00-]`): un solo dato lo sostiene |
| «vacío»: `«{uno[0]}»` sin recorte | `171 passed` |
| «cerca de»: `sufijo[pos:pos + 20]` → `sufijo[:20]` | `171 passed` |
| «cerca de»: `sufijo[pos:pos + 20]` → `sufijo[pos:]` | `171 passed` |
| `«{cambiaria[:20]}»` → `«{cambiaria}»` | `171 passed` |
| `«{cambiaria[:20]}»` → `«{sufijo[:20]}»` | `171 passed` |
| «no se puede separar»: `sufijo[:80]` → `sufijo[:10]` | `171 passed` |
| aviso: `limpio[:80]` → `limpio[:10]` | `171 passed` |

D249 (a): lo hace MARIA, con la familia entera en el criterio.

## Escape de la PM

El criterio de D247 pidió el ejemplo (el fragmento del vacío) y no la familia de
fragmentos de `limpiar_sufijo`. Por eso el resto quedó para D249.

## Riesgos

- `4a58c68` no pasó por subagente ni por `/code-review`: lo cubren la lectura del diff
  entero y las mutaciones de arriba.
- Sacar `.upper()` y cambiar el texto de la instrucción («Escribí el valor o sacá el
  código») siguen verdes, según el adversario de la Dev. Son huecos previos, no de
  esta pieza.

## No corrido por la PM

La suite, las pantallas, `e2e_maria.sh`, Postgres, adversario propio y
`/security-review`: la pieza no cambia producto.
