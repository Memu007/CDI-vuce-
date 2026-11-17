# DESPACHO1B-CARGA-2: `fd4eb1dd` (informe `b0c0b0db`), 2026-11-17, PM

**Veredicto: aceptada, integrada.** Base `8f3a9052`. Sólo cambian pruebas: `tests/pdf_bombas.py`,
`tests/test_despacho1b.py` y `tests/test_rendimiento1d.py`.

## Diff

`chequeo-6.py 8f3a9052 fd4eb1dd`:
```
producto +0/−0
arnés +32/−29
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```
`recolector_sin_la_suite` vive una sola vez, en `tests/pdf_bombas.py`; lo usan los seis casos de
`test_despacho1b.py` y `test_rendimiento1d.py:97`, donde el PDF se arma antes del bloque. En el caso
del finalizador, el `try` interno ahora abarca el primer bucle con su condición.

## Lo que corrí (worktrees en el scratchpad de la PM, 23:37 a 23:59 UTC)

| Qué | SHA | Resultado |
|---|---|---|
| `test_despacho1b.py` + `test_rendimiento1d.py` | `fd4eb1dd` | «297 passed», 0 «Exception ignored» |
| corte desarmado (`yield; return` antes de `signal.signal(signal.SIGPROF, cortar)`) | `fd4eb1dd` | «7 failed, 290 passed»: los seis de antes y `test_el_texto_tiene_tope_de_cpu` |
| temporizador que no se repite (`setitimer(..., 0)` en vez de `0.05`), `-k "finalizador or tope"` | `fd4eb1dd` | «1 failed, 24 passed»: el caso del finalizador, `assert 1 == 2` |
| 7 corridas en paralelo de `test_catalogo3.py` + `test_despacho1b.py` + `test_rendimiento1d.py`, 4 núcleos | `fd4eb1dd` | 7 × «408 passed»; 0 ticks tragados |
| `tests/test_rendimiento1c.py` (importa de `pdf_bombas.py`) | `fd4eb1dd` | «15 passed» |
| negativo mío: el ayudante vaciado (sólo `yield`), `test_despacho1b.py` solo, 4 veces | `fd4eb1dd` | 4 × «285 passed», 0 ticks tragados |
| negativo mío: el ayudante vaciado, la misma carga de 7 | `fd4eb1dd` | 7 × «408 passed», 0 ticks tragados |
| negativo mío, determinista: 50 objetos en ciclo con `__del__`, y adentro del ayudante se crean 200 000 listas (abajo) | `fd4eb1dd` | «0 de 50 dentro»; con el ayudante vaciado, «50 de 50 dentro» |
| el ayudante viejo vaciado, `test_despacho1b.py` solo, 2 veces | `962bc88f` | 2 × «285 passed», 0 ticks tragados (la base `50d32c26`, sin ayudante, daba 3 de 3) |

**Los ceros de `fd4eb1dd` no prueban el ayudante.** Sin él, el mismo árbol también da 0 solo (0 de 4)
y cargado (0 de 7): ni su 0 en 21 ni mi 0 en 7 lo distinguen. Lo que sí lo muestra es el negativo
determinista: con el ayudante, ningún finalizador corre dentro del bloque; vaciado, corren los 50.
Que el tick ya no aparezca sin el ayudante: sin explicar. Pasa ya en `962bc88f` con el ayudante viejo
vaciado, así que no lo trajo esta pieza. Hipótesis, no medida: el `with` alrededor de la lectura ya corre el
momento en que pasa el recolector.

**Escape mío (aceptación de DESPACHO1B-CARGA, 21:03):** comparé la base sin ayudante con el arreglo
y escribí «0 con el arreglo», pero no vacié el ayudante en el mismo SHA. Ese 0 no lo aislaba. Desde
ahora, el negativo de un arreglo se corre en el mismo SHA con el arreglo vaciado.

No reabre ninguna de las dos aceptaciones: el mecanismo está mostrado (el negativo determinista) y
el criterio no pedía una tasa después.

El negativo determinista, desde la raíz del worktree con `PYTHONPATH=.`:
```python
import gc
from tests.pdf_bombas import recolector_sin_la_suite
dentro, vistos = False, []
class Basura:
    def __del__(self): vistos.append(dentro)
gc.collect(); gc.disable()
for _ in range(50):
    b = Basura(); b.yo = b
del b
gc.enable()
with recolector_sin_la_suite():
    dentro = True
    relleno = [[] for _ in range(200_000)]
    dentro = False
print(sum(vistos), "de", len(vistos), "dentro")
```

## No corrido, y por qué

Suite completa, `e2e_maria.sh`, `despacho1b.sh` mío y adversarios: producto +0/−0 y tres archivos de
pruebas; los archivos, los dos sabotajes y la carga alcanzan. Tampoco reproduje su medición de D272
fuera de pytest (18 en 6000 → 0): me alcanza que el caso siga en rojo con los dos sabotajes y que el
`try` cubra la condición del `while`, que es donde caían sus 18.

## Observación

La hora del encabezado del informe (23:40) es posterior al commit (`b0c0b0db`, 23:36): la hora sale de
`date -u` al escribir, no se anticipa.

## Riesgos escritos (de su `/code-review`, quedan)

Un tick entre `setitimer(0)` y la vuelta del manejador en el `finally` del producto (0 en 10 000);
finalizadores por conteo de referencias que el congelado no frena; el ayudante es voluntario para un
caso nuevo; `gc.unfreeze` no se anida; un `gc.collect()` más (~0,1 a 0,2 s).
