# Reproducción del rojo de `despacho1b` (2026-11-07)

PM principal. Rama `claude/dev-maria`, prueba `d69233c`, informe `e400112`,
base `9417c3b`.

**Veredicto: aceptado, sin integrar** (la rama lleva debajo piezas en
devolución). Sólo prueba; el producto no cambia.

| Qué | Salida |
|---|---|
| `chequeo-6.py 9417c3b d69233c` | `producto +0/−0`, `arnés +8/−1`, `avisos: 0` |
| `test_despacho1b.py` en `d69233c` | `283 passed` |
| la causa, medida aparte: `gc.collect()` con 3 M dicts vivos | `0.533` s de CPU; con `gc.freeze()`, `0.0` |
| usos de `leer_despacho` en `proyecto_maria/` | sólo el proceso aparte, como dice el informe |

Una pasada completa del recolector cuesta más que el resto del tope (0,2 s)
del caso, y en producción el lector corre en un proceso aparte con poca
memoria: la causa alcanza y el arreglo no esconde nada del producto.

D106: (a), decidido por la PM. Riesgo: el resto para entender el texto no
tiene mínimo propio; con el tope de producción son 2 s.

No corrido por la PM: el brazo con 3 M objetos dentro de pytest (lo corrió la
Dev, `3 failed, 3 passed` sin arreglo y `6 passed` con él); la suite completa.
