# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DATOS1-DOS-OPERACIONES: borrar un cliente con dos operaciones

| SHA | qué |
|---|---|
| `50124c63` | base |
| `53bd7df1` | `test:` el caso de borrar cliente con dos operaciones, y dos sabotajes en `datos1.sh` |
| este commit | `docs:` informe |

**Nada para decidir.** Producto +0/−0. No hubo adversarios, como pedía la tarea. El nombre de la pieza lo puse yo, porque la tarea no traía uno.

**Cómo quedó.** Seguí tu sugerencia: extendí `test_borrar_cliente_borra_sus_presupuestos_y_no_los_ajenos`, sin cambiarle el nombre, así no se mueve ninguna ancla.
- El cliente borrado tiene dos operaciones, cada una con su presupuesto compartido y un ítem. Van como datos: `borradas = {1: ..., 2: ...}`.
- Antes de borrar, se comprueba que las cuatro operaciones del caso tienen el link en 200 y al menos un ítem. Así, «0 ítems después» no puede salir de un guardado que nunca creó ítems.
- Después de borrar, para cada operación del cliente: el link da 404, quedan 0 presupuestos y 0 ítems. Cada aserción lleva el número de la operación en el mensaje.
- Lo del otro cliente del mismo dueño y lo del otro dueño sigue: link en 200 y sus ítems.
- Sumé `_items_de(op_id)` al lado de `_presupuestos_de`, y el import de `OperationItem`.

**Supuesto reversible:** el caso también comprueba que los ítems de las operaciones ajenas siguen. La tarea decía «lo de otro cliente sigue» sin nombrar los ítems; lo tomé como incluido.

### Comandos para reproducir

```bash
PY=<venv>/bin/python scripts/testing/sabotajes/datos1.sh 53bd7df1   # 22 líneas ROJO, ninguna ROTO/VERDE/ROJO?, «sabotajes sin rojo: 0», salida 0
python scripts/testing/anclas_perdidas.py 53bd7df1                   # ninguna línea de datos1.sh
python docs/pm/herramientas/chequeo-6.py 50124c63 53bd7df1           # producto +0/−0, avisos: 0
```

### Puertas sobre `53bd7df1`

| puerta | resultado (copiado de la salida) |
|---|---|
| `tests/test_datos1.py`, SQLite | `11 passed, 3 warnings in 10.46s` |
| `datos1.sh 53bd7df1` | 22 `ROJO`, `sabotajes sin rojo: 0`, `rc=0` |
| sabotaje nuevo: presupuesto sólo de la primera operación | `ROJO  \| sólo se borra el presupuesto de la primera operación: «FAILED tests/test_datos1.py::test_borrar_cliente_borra_sus_presupuestos_y_no_los_ajenos» «AssertionError: presupuesto de la operación 2» «assert 200 == 404»` |
| sabotaje nuevo: ítems sólo de la primera operación | `ROJO  \| sólo se borran los ítems de la primera operación: «FAILED tests/test_datos1.py::test_borrar_cliente_borra_sus_presupuestos_y_no_los_ajenos» «AssertionError: ítems de la operación 2» «assert 1 == 0»` |
| los dos sabotajes de antes sobre este caso | siguen en `ROJO` con su texto: `assert 200 == 404` y `assert 404 == 200` |
| `anclas_perdidas.py 53bd7df1` | `rc=0`; ninguna línea de `datos1.sh` (las únicas `SIN ANCLA` son `limpieza1.sh:181` y `:185`, que ya estaban) |
| `chequeo-6.py 50124c63 53bd7df1` | ver abajo |

```
chequeo-6 50124c63..53bd7df1: avisos para mirar, no un veredicto
producto +0/−0
arnés +31/−9
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Cada sabotaje nuevo ancla en `PublicQuoteModel.operation_id.in_(...)` o en `OperationItemModel.operation_id.in_(...)`. El texto `.in_([o.id for o in operaciones])` está dos veces en `delete_cliente`, y con el nombre del modelo cada reemplazo encuentra una sola. El rojo de cada uno es por su razón: el de presupuesto cae en el 404 del link de la operación 2; el de ítems pasa el link y los presupuestos, y cae en `ítems de la operación 2`.

### Lo que no se corrió y riesgos

- **No corrido:** la suite completa, los adversarios y Postgres. La tarea pide este archivo, el guion, las anclas y chequeo-6.
- **Archivos de producto tocados:** ninguno.
- **Riesgo bajo, sólo del guion:** `delete_cliente` trae las operaciones sin `order_by`, y el sabotaje usa `operaciones[0]`. En SQLite viene primero la operación 1, y por eso el rojo esperado nombra la 2. Si el orden se diera vuelta, el caso seguiría en rojo (comprueba las dos operaciones), pero el guion marcaría `ROJO?` porque el mensaje diría «operación 1». No da un verde falso.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué DATOS1-DOS-OPERACIONES (53bd7df1 + informe); nada para decidir; tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
