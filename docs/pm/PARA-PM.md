# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-CORTE-1, vuelta de la devolución, entregada en `0b9ccde` (informe en el commit de arriba)

| SHA | qué |
|---|---|
| `efaef2b` | producto: la operación se reconoce por su id del servidor, no por el número de factura |
| `069915e` | pruebas: un caso por punto, la pantalla y los sabotajes de la identidad por id |
| `b2ce237` | producto: el período nuevo no hereda regeneraciones, el archivo manual toma el final del id, la importación incluye la fecha de la factura en la huella; CHANGELOG |
| `da8effc` | pruebas: esos cuatro casos con su sabotaje |
| `5c9e4d0` | merge de tu rama hasta `91f79e1`: no cambia nada fuera de `docs/pm` |
| `0b9ccde` | pruebas: dos sabotajes del script siguen a la línea que protege cada caso (abajo, «Puertas») |

Base de la vuelta: `375edbc` (tu merge con COBRO-MP-2 adentro). Producto
`+131/−149`: resta más de lo que suma.

**Resultado.** Una causa, como dijiste: el id `FAC_<factura>` hacía de
identidad. Ahora la identidad es el UUID de `OperationModel`.

- `/generate_maria`, `/generate_maria_export` y el guardado en cliente reciben
  y devuelven `operacion_id`. El servidor busca esa operación filtrando por
  `id` y `owner_username`; una ajena o desconocida es una operación nueva.
- v2 (`finalize.js`, `upload.js`) y v1 (`app.js`) mandan el id que devolvió la
  generación o el guardado, y lo vacían al empezar una carga nueva.
- El nombre del archivo pasa a `<nombre>_<últimos 8 del id>.TXT`: dos
  operaciones con la misma factura ya no comparten archivo ni fila.

**Nada para decidir.** D62 no hizo falta. Supuestos reversibles, abajo.

### Cómo se cumple cada punto

| punto | qué hace el producto | caso (rojo en `75c6476`) | sabotaje |
|---|---|---|---|
| 1. dos operaciones nunca comparten fila | la fila sale del id, no de la factura | `test_dos_operaciones_nunca_comparten_una_fila`, familia como datos: mismo número de dos proveedores, ids que el saneo junta (`A-1/2` y `A-12`), sin número, dos miembros del estudio. Más `test_dos_operaciones_manuales_no_comparten_el_archivo` y `test_guardar_con_la_operacion_de_otra_cuenta_no_la_toca` | «cada generación crea y cuenta otra operación», «dos operaciones con la misma factura comparten el archivo», «el archivo toma el comienzo del id», «se reusa la operación de otra cuenta» |
| 2. el mismo resultado no gasta una de las 10, nunca un callejón | la misma huella reusa la operación sin sumar; la 11.ª distinta es una operación nueva contada (tu sugerencia), no un 409 | `test_el_mismo_resultado_no_gasta_una_de_las_10` (exportación otro día, con la fecha de hoy cambiada), `test_otra_fecha_de_factura_en_la_importacion_gasta_una_de_las_10`, `test_la_11_distinta_es_una_operacion_nueva_contada`, `test_el_periodo_nuevo_no_hereda_las_regeneraciones` (con y sin org), `test_la_operacion_del_mismo_segundo_es_del_periodo` | «el mismo resultado gasta una de las 10», «la fecha de emisión cambia el resultado», «la fecha de la factura importada no cambia el resultado», «la 11.ª distinta reusa la operación», «el período nuevo hereda las regeneraciones», «la operación del mismo segundo parece de otro período» |
| 3. borrar el cliente no recuenta | `delete_cliente` deja las operaciones sin cliente en vez de borrarlas | `test_borrar_el_cliente_no_recuenta_lo_generado` | «borrar el cliente borra sus operaciones» |
| 4. el tope tiene número y está probado | `MARIA_REGENERACIONES = 10` (`main.py:5893`) | `test_la_11_distinta_es_una_operacion_nueva_contada`: afirma el 10, nueve regeneraciones distintas reusan la operación, la 11.ª es otra con su archivo y suma 1, y la primera queda con 10 huellas | «el tope de regeneraciones no es 10» |
| 5a. el 402 no muestra un código crudo | `CDI.api` (`app_v2.js`) lanza el error con la razón como `message`; `clientes.js:449` y `:628` muestran `err.message`, así que ya dicen la razón | pantalla: el error de la generación dice el mensaje del servidor en los cuatro 402 | «el 402 no trae su razón como mensaje» |
| 5b. la misma razón en el primer y el segundo pedido | la razón sale del estado de la cuenta, no de si ese pedido fue el que la venció | `test_la_razon_del_402_es_la_misma_en_el_segundo_pedido`, uno por estado | «el pedido que vence la cuenta da otra razón» |
| 5c. el `trial` legado no da 400 ni 500 | `plan_de_la_cuenta` da premium a un plan que ya no existe | `test_el_plan_legado_trial_genera_exporta_y_guarda` | «el plan legado da error» |
| 6. sin el atajo `testing` en las rutas que cuentan | sacado de las cuatro; sin la fila del usuario, 401 | `test_sin_sesion_las_rutas_que_cuentan_dan_401` | uno por ruta (bloque «Sin usuario en la base») |

D61 (b), tal cual la decidiste: guardar con la operación propia en otro
cliente la mueve y no baja `ops_used`
(`test_guardar_en_otro_cliente_mueve_la_operacion`, sabotaje «guardar en otro
cliente no mueve la operación»).

Lo que no prueba un caso propio: `clientes.js` no tiene un caso en la pantalla
de importación. El arreglo está en `CDI.api`, por donde pasan las dos
llamadas, y la pantalla lo prueba con el error de la generación.

Sabotajes retirados (11): apuntaban a código que ya no existe (`vencio ==`,
`_operacion_maria`, `_ARCHIVO_MARIA`, `err.motivo`, el 409
`MARIA_REGENERACIONES_AGOTADAS`, el manejo del 409 en la pantalla); `grep` de
cada uno en `proyecto_maria` da 0. Sus reglas, si siguen vigentes, tienen
sabotaje nuevo en la tabla de arriba.

Supuestos reversibles:
- **Tolerancia de 1 s.** SQLite guarda `created_at` sin fracción; el inicio
  del período se compara truncado a segundos. Una operación creada hasta 1 s
  antes del inicio cuenta como del período nuevo.
- La respuesta de `DELETE /api/clientes/{id}` dice `operaciones_sin_cliente`
  en vez de `operaciones_eliminadas`. Nadie la lee (`grep` en `static`, `tests`
  y `scripts`: vacío).
- Los TXT generados de un cliente borrado quedan en disco, como las
  operaciones.

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| suite completa | `da8effc` (`0b9ccde` no toca producto ni casos) | `4476 passed, 121 skipped, 3 xfailed in 647.57s (0:10:47)` |
| `test_cobro_corte1.py` | `0b9ccde` | `82 passed` |
| sabotajes `cobro_corte1.sh`, con Postgres | `0b9ccde` | base, pantalla y lock en verde; 60 ROJO; `sabotajes con falla: 0`, `sabotajes salida 0` |
| sabotajes `cobro_corte1.sh`, con Postgres | `da8effc` | `sabotajes con falla: 2`: «cada generación crea y cuenta otra operación» ROTO (el ancla ya no existía) y «el mismo resultado gasta una de las 10» ROJO? (rojo por otro caso). Arreglados en `0b9ccde`, que suma el sabotaje de «con las 10 llenas» |
| `/code-review high` | `375edbc..069915e` | tabla de hallazgos abajo |
| `/security-review` | `375edbc..da8effc` | sin hallazgos (abajo) |

La pantalla (`pantalla_cobro_corte1.js`) corre dentro de los sabotajes: su
base en verde sobre `0b9ccde` es la línea «la pantalla en verde».

`smoke_friccion.sh` y `ataque_aislamiento.sh`: no corridos. La pieza no toca
permisos de clientes ni descargas; el borrado de cliente sigue filtrando por
dueño.

### Rojo antes

`test_cobro_corte1.py` y `conftest.py` de `da8effc` sobre el producto de
`75c6476`: `25 failed, 57 passed`, salida 1. Los 25:

- 17 filas de los casos nuevos de los puntos 1 a 6 y de D61 (las cuatro filas de
  `test_dos_operaciones_nunca_comparten_una_fila`, las dos de
  `test_el_periodo_nuevo_no_hereda_las_regeneraciones`, las dos de
  `test_guardar_sin_una_operacion_generada_cuenta_cada_vez`, y los demás de
  la tabla de arriba);
- `test_la_razon_del_402_es_la_misma_en_el_segundo_pedido[suscripcion_vencida]`
  y las 7 filas `[suscripcion_vencida-*]` de
  `test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini`: es el
  punto 5b, porque el pedido que vencía la cuenta daba otra razón.

Tres casos pasan en `75c6476` porque cuidan defectos que nacieron en esta
vuelta, no en la base: `test_otra_fecha_de_factura_en_la_importacion_gasta_una_de_las_10`,
`test_la_operacion_del_mismo_segundo_es_del_periodo` y
`test_guardar_con_la_operacion_de_otra_cuenta_no_la_toca`. Lo que los
sostiene es su sabotaje («Puertas»). Los cuatro de `b2ce237` sobre `069915e`,
el producto de antes de ese arreglo:

```
FAILED tests/test_cobro_corte1.py::test_otra_fecha_de_factura_en_la_importacion_gasta_una_de_las_10
FAILED tests/test_cobro_corte1.py::test_el_periodo_nuevo_no_hereda_las_regeneraciones[False]
FAILED tests/test_cobro_corte1.py::test_el_periodo_nuevo_no_hereda_las_regeneraciones[True]
FAILED tests/test_cobro_corte1.py::test_dos_operaciones_manuales_no_comparten_el_archivo
============ 4 failed, 1 passed, 77 deselected, 5 warnings in 6.27s ============
```

El que pasa es `test_la_operacion_del_mismo_segundo_es_del_periodo`: en
`069915e` todavía no se miraba el período.

### Hallazgos de la autorrevisión

Adversario Sonnet alto (uno solo, como pide la vuelta), sobre `069915e`:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | por API, un id sirve para 10 facturas distintas | queda: es el diseño de 10 contenidos por operación pagada. La pantalla no cambia la factura sin una carga nueva, que manda id vacío. Riesgo bajo, acotado a 10 |
| 2 | dos operaciones manuales comparten el archivo (`[:8]` del id) | arreglado en `b2ce237`, caso y sabotaje en `da8effc` |
| 3 | una operación del período anterior trae sus regeneraciones | arreglado en `b2ce237`, caso y sabotaje en `da8effc` |
| 4 | en la importación, otra fecha de factura no cambiaba la huella | arreglado en `b2ce237`, caso y sabotaje en `da8effc` |
| 5 | un NUL en el id da 500 en Postgres | plausible, no corrido: no tengo un caso que lo muestre |
| 6 | doble pedido con el id vacío cuenta 2 | queda, igual que el #4 del code-review |
| 7 | v1 cambia el id sin factura cada ~10 o ~100 s y gasta regeneraciones | queda: previo, sólo v1 |
| 8 | v1 (`app.js:3387`) muestra `[object Object]` en un 402 | queda: v1. Parche propuesto: `data.detail?.message \|\| …` |

`/code-review high` (Opus, alto) sobre `375edbc..069915e`:

| # | hallazgo | qué hice |
|---|---|---|
| 2 | v1 conserva `operacionIdActual` y el guardado mueve la operación de A a B | es D61 (b); v1 vacía el id al agrupar una carga nueva y al cancelar |
| 4 | doble clic con el id vacío cuenta 2 | queda como riesgo: hace falta una clave de idempotencia, fuera de la tarea |
| 5 | en v1, recargar la página pierde el id | queda: la próxima generación cuenta otra |
| 6 | `_FECHA_DE_EMISION` y las huellas viejas | queda, de una vez al publicar: la pantalla no tiene el id de una operación generada antes del cambio, así que regenerarla después cuenta una nueva. Las huellas viejas no coinciden con las nuevas |
| 7 | `delete_cliente` deja los TXT y cambia la clave de la respuesta | supuesto reversible (arriba) |
| 9 | una cuenta paga vencida sin MP lee «Venció tu prueba gratis» | queda: texto de un caso sin MP, fuera de la tarea |
| 10 | `dependencies.py:120` repite `plan_de_la_cuenta` | a la cola de limpieza |

`/security-review` (subagente general, alto) sobre `375edbc..da8effc` (`0b9ccde` sólo toca el script de sabotajes): sin
hallazgos altos ni medios. Sus dos notas, el movimiento entre clientes propios
y la tolerancia de 1 s, son de producto y están arriba.

### Riesgos

- Doble pedido o reintento con el id vacío cuenta dos (code-review #4,
  adversario #6). Necesita una clave de idempotencia; lo propongo como pieza.
- v1: recargar pierde el id (#5), el id sin factura cambia con la hora (#7) y
  el 402 muestra `[object Object]` (#8).
- Al publicar, regenerar una operación generada antes del cambio cuenta una nueva, una sola vez (code-review #6).
- Las inversiones de orden de los locks: a la cola, como pediste.
- C10 queda como puerta de publicación.

### chequeo-6

```
chequeo-6 375edbc..0b9ccde: avisos para mirar, no un veredicto
producto +131/−149
arnés +575/−260
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11313 → 11283
  proyecto_maria/services/billing_service.py: 412 → 414
  proyecto_maria/static/app.js: 6759 → 6765
  proyecto_maria/static/v2/app_v2.js: 1203 → 1204
  proyecto_maria/static/v2/screens/finalize.js: 1357 → 1360
  proyecto_maria/static/v2/screens/upload.js: 718 → 718
avisos: 0
salida 0
```

### Para reproducir

```bash
git checkout 0b9ccde
# 1. 82 passed
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_cobro_corte1.py
# 2. todo ROJO, «sabotajes con falla: 0»; sin PG, la parte del lock dice «NO CORRIDO»
PY=$(which python) PG=postgresql://<usuario>@127.0.0.1:<puerto> scripts/testing/sabotajes/cobro_corte1.sh 0b9ccde
# 3. «avisos: 0»
python docs/pm/herramientas/chequeo-6.py 375edbc 0b9ccde
```

### Archivos de producto tocados

`proyecto_maria/main.py` (generar, exportar, guardar, borrar cliente),
`proyecto_maria/services/billing_service.py`,
`proyecto_maria/static/app.js`,
`proyecto_maria/static/v2/app_v2.js`,
`proyecto_maria/static/v2/screens/finalize.js`,
`proyecto_maria/static/v2/screens/upload.js` y `CHANGELOG.md`.

---

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-CORTE-1 (vuelta)
entregada en 0b9ccde (informe en el commit de arriba), sin D. Sigue
COBRO-MP-2, en tu orden. Nada se publica sin el «dale» de Emi; nunca main.
