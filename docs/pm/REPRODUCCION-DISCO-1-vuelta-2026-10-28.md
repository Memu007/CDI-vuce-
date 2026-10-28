# Reproducción de DISCO-1, vuelta (2026-10-28)

Entrega de la Dev MARIA: informe `94d05b2`, puertas sobre `a6c82f5`
(producto `47c4d7b` y `5f8707f`, pruebas `772d715` y `8bff4a5`, textos de
`disco1.sh` `a6c82f5`). Base `18cf27d`. Productos tocados:
`proyecto_maria/main.py` y `CHANGELOG.md`.

## Lo que corrió la PM, sobre `a6c82f5`

- `tests/test_disco1.py`: 33 passed.
- `scripts/testing/disco1_postgres.py` contra un Postgres 16 descartable:
  «fallas: 0».
- `disco1.sh`: 42 ROJO, 1 ROJO?, «sabotajes sin rojo: 1». El ROJO? es
  «importar sin el bloqueo por dueño»: el rojo está (el 500 por deadlock
  sale en las tres vueltas), pero el texto esperado pide
  «vuelta 0: [(500,» y el orden de las dos respuestas cambia: vueltas 0 y 1
  `[(200…),(500…)]`, vuelta 2 `[(500…),(200…)]`. Es el texto del sabotaje,
  no el producto.
- Mutantes en Postgres (el script de Postgres sobre una copia de
  `disco1_postgres.py`):

  | Mutante | Resultado |
  |---|---|
  | M14: la carga de archivos viejos sin `_bloquear_historial` | sobrevive, «fallas: 0» |
  | M15: la clave del bloqueo sin el dueño (`"ncm_historial:"`) | sobrevive, «fallas: 0» |
  | M16: importar sin `_bloquear_historial` | muere, 500 por deadlock en las tres vueltas |

## Adversario de la PM (Sonnet alto, contexto nuevo)

Sin altas ni fugas entre dueños o clientes. Lo que sigue lo midió él; la
PM reprodujo M14, M15 y M16 (arriba).

- **Media, sobre el informe.** El riesgo «media» de guardar-uso está mal
  medido. Con cliente y proveedor, una descripción de 301 a 2000
  caracteres ya perdía en silencio la memoria del cliente y el catálogo
  con 200, también en `c996ad4`: `vendor_catalog_products.product_key` es
  `String(300)` y el `except` hace rollback de las dos. La regresión del
  tope de 2000 es sólo «cliente sin proveedor y descripción de 2001 o
  más»: antes se guardaba la memoria del cliente, ahora 400, y el front lo
  traga (`ncm.js:1812`, `app.js:3933`).
- **Baja.** guardar-uso espera mientras importa el mismo dueño: 9,3 s con
  60 000 filas, sin `lock_timeout`, con una conexión del pool ocupada.
- **Baja.** Sugerir con 100 000 filas de un dueño tarda 3 s y frena
  `/health` 2,25 s (el bucle de `normalizar_desc`, anterior a la pieza).
  Ya declarado como «no hay tope de filas».
- **Baja.** La carga de archivos viejos descarta para siempre las
  entradas que no pasan los topes. El log dice cuántas, no cuáles.
- **Baja.** Siguen los 500 anteriores declarados: descripción numérica,
  `ncm: null` y un medio par UTF-16 en sugerir. NCM con dígitos árabes o
  fullwidth se guarda y se sugiere (anterior).
- **Lo que no falló:** dos dueños a la vez con las mismas filas no se
  mezclan; 6 vueltas de 3 importaciones y 60 guardar-uso sin un no-200;
  el orden del archivo se conserva; los rollbacks de sugerir, guardar-uso,
  importar y la carga están; 30 de 37 mutantes mueren con la suite SQLite
  y los de Postgres mueren con el script, salvo M14 y M15.

## Supuestos

1. **Bloqueo por dueño en vez de ordenar por clave: aceptado, decidido por
   la PM.** Ordenar cambiaría las sugerencias (sugerir toma los cinco
   primeros por id). El deadlock lo midió la Dev (10 de 10 sin el bloqueo,
   0 con él) y la PM lo ve con M16.
2. **La carga salta las filas que no pasan los topes y lo anota:
   aceptado.** Riesgo: la pérdida es definitiva.
3. **guardar-uso revisa el cliente antes de escribir: aceptado.**

## No corrido por la PM

La suite completa (la Dev informa 4089 passed sobre `8bff4a5`),
`/code-review`, `/security-review` y el front en un navegador. Dos procesos
arrancando a la vez con migración: razonado, no reproducido.

## Veredicto

Devolución sobre `a6c82f5`, sólo pruebas e informe. El producto queda como
está.
