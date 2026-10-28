# Reproducción de DISCO-1 (2026-10-28)

Entrega de la Dev MARIA en `88b22c8`, encima de `c996ad4`. El historial de
NCM pasa de `ncm_historial_<usuario>.json` a una tabla por dueño, con la
carga de los archivos viejos al arrancar.

## Adversario (Sonnet alto, contexto nuevo)

Postgres 16 descartable y SQLite. La migración desde una base de `c996ad4`
con datos y archivos, dos arranques seguidos, dejó 8 filas con cuenta total
10 en cada motor, sin duplicados; los dueños quedaron separados; el archivo
roto quedó en su lugar con aviso; `disco1_postgres.py` `fallas: 0`.

Hallazgos:

1. **Regresión, reproducida por la PM en Postgres 16.** Si el paso 1
   (memoria del cliente) o el 2 (catálogo del proveedor) de
   `POST /api/ncm/sugerir` fallan contra la base, la excepción se atrapa sin
   `rollback`; la transacción queda abortada, `load_ncm_historial` del paso
   3 falla y la sugerencia del historial se pierde sin aviso. Rompiendo una
   columna de `client_product_history`: sobre `c996ad4` `despues 200
   ['historial']`; sobre `88b22c8` `despues 200 []`. El mutante que quita
   el `rollback` del paso 3 sobrevive a `test_disco1.py` y a
   `disco1_postgres.py`.
2. **Regresión, reproducida por la PM en Postgres 16.** Un NUL en la
   descripción o en el NCM de `guardar-uso` da `500 internal_error` (el
   archivo lo aceptaba).
3. **Reproducido por la PM.** Sin tope de tamaño: `guardar-uso` aceptó 5 MB
   y 30 MB de descripción (`200`). Según el adversario, con 35 MB guardados
   cada sugerencia tarda 20 s.
4. **Del adversario, no reproducido por la PM.** Importaciones simultáneas
   del mismo dueño con las filas en distinto orden: `DeadlockDetectedError`
   en 2 de 4 y 3 de 4 corridas (en el mismo orden, 0).
5. **Del adversario, no reproducido por la PM.** Al migrar,
   `os.replace(ruta, ruta + ".migrado")` pisa un `.migrado` anterior.
6. **Mutantes que sobreviven** (del adversario): sin `order_by` en la carga
   del historial; `_HISTORIAL_FILAS_POR_SENTENCIA = 10**6` (con 7000 filas
   el real da ok y el mutante `InterfaceError`); sin `or count < 1`; sin
   `not desc.strip()`; `os.replace` por `os.remove` (sólo lo mata el script
   de Postgres, no la suite).

## Veredicto

Devolución sobre `88b22c8`: la causa del 1 y lo que piden el 2, el 6 y,
dentro de lo barato, el 3 y el 4. La migración en sí está bien.
