# Reproducción DESPACHO-1b vuelta 4 — 2026-11-05 (PM)

Producto `03296d4`, base `1f5480e`, informe `5066042` (rama `claude/dev-maria`).
Adversario Opus alto con contexto nuevo; la PM confirmó el hallazgo 1 en el código.

## Veredicto: devolución por una causa

**Hallazgo 1 (pierde datos):** `services/client_memory.py`
`upsert_client_product_history` hace `INSERT … ON CONFLICT DO NOTHING` (l. 219)
y después `SELECT … with_for_update() … scalar_one()` (l. 229-230). En Postgres
16: una conexión toma la fila con FOR UPDATE; otra hace el UPDATE de clave del
PUT y queda en cola; una tercera escribe el mismo producto; se suelta la
primera. Resultado: `NoResultFound: No row was found when one was required`,
filas `[('TAPA OTRA', 1)]` (el uso no se sumó). Con DELETE en vez de UPDATE: el
mismo error, filas `[]`. En guardar-uso (`main.py` ~10024) el `except Exception`
se lo traga y contesta `{"success": True}`.

**Hallazgo 2 (hueco de prueba):** sin `.with_for_update()`, `test_despacho1b.py`
sigue verde y `despacho1b.sh` no tiene ese sabotaje; sólo `despacho1b_postgres.py`
lo ve: `FALLA | … una fila con 16 usos: ['200'] [(10,)]`.

## Lo que se sostiene

- `tests/test_despacho1b.py` en `03296d4`: `281 passed`.
- `despacho1b_postgres.py` en Postgres 16.15 descartable: 11 OK, `fallas: 0`.
- Migración en Postgres sobre variantes (NFC/NFD, mayúsculas, tabulador, NCM con
  puntos, espacios, guiones, 10 dígitos, `ultima_vez` nula, dos clientes, otra
  cuenta con el mismo `client_id`, filas sin dueño): usos por cuenta y cliente
  iguales antes y después; segunda corrida sin cambios.
- Aislamiento: siete vías con otra cuenta dan 404; lo ajeno queda intacto.
- PUT con 33 cuerpos raros: ningún 500.
- Sabotajes a mano: sin `casefold` → `29 failed`; la migración que no une → `2 failed`.
- chequeo-6 `1f5480e 03296d4`: idéntico al informe (`producto +496/−242`, `avisos: 10`).
- Suite completa con el comando de `ci.yml`: `1 failed, 4507 passed, 102 skipped,
  10 deselected, 2 xfailed`. El rojo, `test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`
  (400 a los 30.2 s), falla 3 de 3 en `1f5480e` y 2 de 3 en `03296d4`: depende
  del tiempo de la máquina, no de esta pieza. Queda como rojo de entorno a
  diagnosticar aparte. El informe de la Dev da `4284 passed, 336 skipped`: otro
  entorno; se le pide el comando.

Bajos, ya declarados o de antes: la operación da 500 con `cantidad: "abc"` (igual
en `1f5480e`); el PUT acepta `descripcion` que no es texto (igual que guardar).

No corrido: `despacho1b.sh` entero, `disco1.sh`, `guardar1.sh`, la medida de CPU
del punto 4, e2e, dos migraciones a la vez.
