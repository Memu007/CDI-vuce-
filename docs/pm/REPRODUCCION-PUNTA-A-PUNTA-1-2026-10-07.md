# Reproducción de PUNTA-A-PUNTA-1 — 2026-10-07

**Veredicto: aceptada sobre `3b52bc9`** (sólo pruebas; el producto no cambia).
Integrada en la rama de la PM.

| Qué corrió la PM (worktree limpio, venv del `requirements.txt` nuevo) | Salida |
|---|---|
| `tests/test_punta_a_punta1.py` | `7 passed, 3 xfailed` (D23, D24, D25, estrictos) |
| `scripts/testing/sabotajes/punta_a_punta1.sh 3b52bc9` | 9 en ROJO, «sabotajes con falla: 0» (lector, mapeo del Excel, procedencia, generador: seguro fuera de la base, flete sin repartir, FOB total = el mayor, coma decimal…) |
| Suite | `1226 passed, 102 skipped, 3 xfailed` (la Dev: 1216 con los 10 que deselecciona la CI) |

Sin subagente: es una pieza de pruebas, y lo que hace falta saber es si
distingue los defectos. Eso lo muestran los sabotajes, que corrió la PM.

**Lo que no cubre todavía:** el peso de un producto con más de una unidad
(lo cambia MARIA-5: la Dev 2 suma ese caso al reentregar). La prueba copia
en Python el pedido que arma `finalize.js`: si la pantalla cambia, hay que
actualizarla (está en el docstring de `pedido()`).
