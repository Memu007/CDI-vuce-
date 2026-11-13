# CONFTEST-TMP — reproducción de la PM (2026-11-13)

Pieza de la Técnica: que una corrida de pytest no deje su `cdi_pytest_*.db`.
Base `5eb910fe`, arreglo `8dd99fa1`, merge `2a41bb6a`, informe `eea0eab5`.
Sólo pruebas (`tests/conftest.py`, +11/−1); producto +0/−0.

**Veredicto: aceptada sobre `8dd99fa1` e integrada (`eea0eab5`).** Dos riesgos
a la cola, sin devolución.

## Lo que corrí

Worktrees en `5eb910fe` y `8dd99fa1`, venv de la PM, entorno de pruebas sin
red (`GEMINI_API_KEY=test-key`, modos `fake`).

| qué | base `5eb910fe` | arreglo `8dd99fa1` |
|---|---|---|
| puerta de la Dev, corrida sana (`test_excel2d.py`), archivos `cdi_pytest_*` | 4149 → **4150**, `7 passed` | 4150 → **4150**, `7 passed` |
| `chequeo-6.py 5eb910fe 8dd99fa1` | — | producto +0/−0, arnés +11/−1, historia vacía, 0 `AVISO`: igual que el informe |
| mi negativo: un hijo con `fork` que sale normal (`atexit._run_exitfuncs()` y `os._exit(0)`), ¿sigue la base del padre? | `1 passed` | `1 failed`, «el hijo borró la base del padre» |

El negativo, entero:

```python
import atexit, os

def test_un_hijo_que_sale_no_borra_la_base_del_padre():
    ruta = os.environ["DATABASE_URL"].split("///", 1)[1]
    assert os.path.exists(ruta)
    pid = os.fork()
    if pid == 0:
        atexit._run_exitfuncs()  # lo que hace un hijo que sale normal
        os._exit(0)
    os.waitpid(pid, 0)
    assert os.path.exists(ruta), "el hijo borró la base del padre"
```

## Por qué el `fork` es riesgo y no devolución

Hoy no hay camino: sobre `8dd99fa1`, `git grep -nE '\bfork(pty)?\(' -- '*.py'`
da vacío; `cdi_pytest` fuera de `tests/conftest.py` sólo aparece en `docs/pm`;
`tests/medir_excel2.py` no es una prueba recolectada y sólo se nombra a sí
mismo. El único pool de procesos en pruebas es `tests/medir_excel2.py:151`
(`ProcessPoolExecutor`, se corre a mano con pytest, así que carga el
`conftest`): una prueba mía con `ProcessPoolExecutor(4)` sobre `9d192d30`
(Python 3.12, arranque `fork`) da `1 passed`, la base del padre sigue. Va a la cola con el negativo de arriba. Sugerencia (no criterio):
borrar sólo desde el proceso que creó la base.

## SIGTERM: leído, no corrido

`timeout` (el corte más común de nuestras puertas) manda TERM, y con TERM
`atexit` no corre: el archivo queda. La base hace lo mismo, así que no es
regresión. El informe nombra SIGKILL y el corte de luz, no TERM. A la cola.

## No reproducido por mí

Las filas de la Dev con falla, Ctrl-C, importación rota y la suite entera
(`6110 passed` en las dos; 110 contra 111 avisos, explicados como avisos de
hilos y del recolector). La CI de la PR sobre la cabeza nueva es la segunda
máquina; no la doy por medida hasta verla (puede cortarla el tope de 20 min).
