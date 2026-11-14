# D245 (a): reproducción de la PM

Entrega `e17c11e` (informe `a8d7f7b`, canal `PARA-PM-2.md`). Base `1215a8a`. Sólo arnés: tres
pruebas del semáforo afirman además `success`.
Veredicto: **aceptada sobre `e17c11e`**.

## Corrido por la PM (2026-11-14, desde las 05:09 UTC, worktrees descartables)

Con `GEMINI_API_KEY` vacía, `DATABASE_URL` en SQLite, `ENVIRONMENT=test` y los
modos falsos. La Dev corrió con `GEMINI_API_KEY=test-key` y sin `DATABASE_URL`
ni `ENVIRONMENT`: los números coinciden igual.

- `chequeo-6.py 1215a8a7 e17c11ed`: producto +0/−0, arnés +6/−2, historia vacía,
  avisos: 0. Leí el diff entero: sólo las tres afirmaciones de `success`.
- Unión: `git diff --stat e17c11ed a8d7f7b3 -- . ':!docs/pm'` vacío; integro `a8d7f7b3`.

| corrida | sobre | resultado |
|---|---|---|
| `test_punta_a_punta1`, `test_generar_maria_txt`, `test_cobro_corte1` | `e17c11e` | `166 passed, 2 xfailed` |
| el semáforo levanta un error antes de leer los ítems, 11 archivos | `e17c11e` | `36 failed, 546 passed, 2 xfailed`: 14 en los cuatro archivos que afirman `success` y 22 en otros siete, todos con `E KeyError` (18 `'errores'`) |
| el semáforo contesta `success: False`, mismos 11 archivos | `e17c11e` | `14 failed, 568 passed, 2 xfailed`: sólo los cuatro archivos que afirman `success` (8 + 4 + 1 + 1) |
| el mismo `success: False`, los tres archivos | base `1215a8a` | `166 passed, 2 xfailed`: la base no lo ve |

El tercero es el negativo de la PM: ataca el borde que la pieza cierra (200 con
`success` falso) sin el error, y distingue entrega de base. Los 22 de los otros
siete archivos quedan verdes con él: respalda la línea de la Dev para la cola.

Las dos `xfail(strict=True)` siguen `xfailed` con los dos sabotajes: no
distinguen, como dice el informe. Riesgo bajo, no se pide.

Guiones que llaman al semáforo, con la copia de `e17c11e` (`GEMINI_API_KEY` vacía):

| guion | resultado |
|---|---|
| `sabotajes/punta_a_punta1.sh` | `rc=0`, 9 `ROJO`, «sabotajes con falla: 0» |
| `sabotaje_subitems1.sh` | `rc=0`, 11 `ROJO`, «OK: los 11 sabotajes dan rojo por la razón esperada» |
| `sabotajes/destino1.sh` | `rc=0`, 19 `ROJO`, «sabotajes sin rojo: 0» |
| `sabotajes/avisos1.sh` | `rc=0`, 22 `ROJO`, «sabotajes sin rojo: 0» |

Ningún sabotaje viejo cambió de razón por la afirmación nueva.

`sabotajes/cobro_corte1.sh` no lo corrí: espera `test_con_el_tope_lleno_se_valida_y_se_baja_lo_ya_contado`
sólo por su nombre en `FAILED`, y esa prueba ahora mira más, no menos.

## Riesgo

El semáforo contesta 200 con `success: false` ante cualquier excepción
(`main.py:4585-4586`) y nadie miró qué muestra la pantalla con eso. Queda como
riesgo anotado en `NOW.md`; no tiene camino de hoy que lo vuelva devolución.

## No corrido por la PM

La suite, los guiones de cobro (`cobro_corte1`, `cobro_mp1`, `cobro_mp2`), las pantallas, `e2e_maria.sh`, Postgres,
adversario y `/security-review`: la pieza no cambia producto. La corrida se
superpuso con la tanda de fondo (`run6`, sobre `7436c6e5`).
