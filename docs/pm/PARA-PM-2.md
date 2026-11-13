# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D218 y D219: entregadas en `1f8ffa6` (sólo arnés). Dos decisiones: D223 y D224

| qué | SHA |
|---|---|
| base (mi informe anterior) | `4b5ef68` |
| D219: un proveedor de nombre largo con su id escrito | `9120475` |
| D218: sabotaje que saca `operation_items` de la migración a `text` | `8f98a31` |
| tu cabeza `6dc251e`, integrada con `merge` | `d5a96aa` |
| `catalogo3_postgres.py` corre solo en una consola limpia (hallazgo del adversario) | `2211e6b` |
| el encabezado del guion nombra sus dos arneses | `ea3256e` |
| tu cabeza `67c8ff0`, integrada con `merge` | `636b889` |
| el chequeo de base de los dos arneses, una vez y con su causa (hallazgo de `/code-review`): **el que se entrega** | `1f8ffa6` |
| informe | el commit siguiente |

**Resultado.** Producto: **+0/−0**. Arnés: +14/−0, +3/−2 y +14/−9 en los tres
tramos míos (abajo, `chequeo-6` entero).

- **D218.** `catalogo_largo2.sh`, con `PG_URL`, corre ahora también
  `catalogo3_postgres.py`: primero sin sabotaje y después con la tupla
  `("operation_items", ("origen",))` sacada de `_migrate_catalogo_sin_tope`.
  Guion entero con Postgres 16, **en una consola sin `DATABASE_URL` ni
  `ENVIRONMENT`**, sobre `1f8ffa6`: **38 `ROJO`, `fallas: 0`, sale 0**. La línea
  nueva:
  `ROJO  | el arranque no pasa el origen de los ítems a text: dice «FALLA | operation_items.origen pasa a text y la fila vieja queda igual»`.
- **D219.** `test_un_proveedor_latino_conserva_su_id` tiene un dato más: un
  nombre de 71 caracteres con su id de 60 escrito a mano. Con el corte
  cambiado de 39 a 38 y el resumen de 20 a 21 (el id sigue midiendo 60) es
  **la única** prueba del catálogo que se pone roja: `1 failed, 185 passed`.
  Antes de este dato esa mutación pasaba entera en verde.

**Mi primera versión estaba mal y no lo vi yo.** El bloque nuevo daba
`BASE  | catalogo3_postgres.py ya está en rojo sin sabotaje` y salida 1 en una
consola sin `DATABASE_URL` ni `ENVIRONMENT`: mi corrida de 38 `ROJO` sobre
`8f98a31` los tenía exportados por mi propio envoltorio. Lo encontró el
adversario. Tu comando de reproducción lo habría pisado. Arreglado en
`2211e6b`; todo lo de este informe corrió con `env -u DATABASE_URL -u
ENVIRONMENT`.

`anclas_perdidas.py 1f8ffa6`: sale 0, 22 filas, ninguna de `catalogo_largo2.sh` ni de `catalogo3.sh`. Las 22 son de `sabotaje_maria1d.sh`, `maria5`, `maria7`, `maria8`, `valor1b`, `e2e_rerun.sh`, `foco_cliente1.sh`, `guardar2.sh` y `limpieza1.sh`: las mismas que sobre `8f98a31`.

## Decisiones

**D223. El candado de la migración de claves del catálogo no tiene sabotaje
commiteado.** `_migrate_catalogo_claves` (`main.py:1339`) toma
`pg_advisory_xact_lock(7302551)` con `lock_timeout` de 5 s para que dos
workers no la corran a la vez. Los dos chequeos que lo miran viven sólo en
`catalogo3_postgres.py`, y hasta esta pieza ningún guion de sabotaje corría
ese arnés. El encabezado de `catalogo3.sh` ya lo decía («el candado de la
migración sólo se ve en Postgres»): no es un olvido, es un hueco anotado sin
negativo. Es una migración (§3).

Lo que medí a mano, en un worktree fuera del repo:

| se saca | sobre | resultado |
|---|---|---|
| `pg_advisory_xact_lock(7302551)` (`main.py:1354`) | `8f98a31` | `FALLA \| dos workers esperan juntos la migración y arrancan los dos: juntos False, [True, True]`, los otros 9 `OK`, `1 fallas`, `rc=1`, 133 s |
| `SET LOCAL lock_timeout = '5s'` (`main.py:1352`) | `ea3256e` | 6 `OK` y un `Traceback` donde va «un worker arranca mientras otro tiene tomada la migración de claves», `rc=1`, 610 s |

Del segundo, mi filtro guardó sólo la palabra `Traceback`: por los 610 s leo
que es el `communicate(timeout=600)` del arnés, **no vi el texto de la
excepción**. Como sabotaje del guion daría `ROJO?` (rojo sin el texto
esperado), que cuenta como falla.

- (a) Pieza chica: un sabotaje del candado en el bloque nuevo de
  `catalogo_largo2.sh`. Suma unos 2 minutos al guion. El `lock_timeout` queda
  como riesgo anotado.
- (b) Nada: los dos quedan como riesgo anotado.
- (c) Los dos. Para el `lock_timeout` hay que cambiar el arnés: que espere
  bastante menos que 600 s y lo diga con una `FALLA` propia.

Recomiendo **(a)**. El candado es lo que evita que dos workers rearmen claves
a la vez, y su negativo es barato y con nombre. El del `lock_timeout` hoy
cuesta 10 minutos por corrida y no dice qué falló; (c) lo arregla, pero es
tocar un arnés que anda para cubrir una línea que sólo cambia cuánto espera el
arranque.

**D224. El borde del corte de `_vendor_key` no lo fija ninguna prueba.** Lo
encontró el adversario con una sola prueba; lo medí con los cuatro archivos
`tests/test_catalogo*.py` (186 pruebas), sobre `ea3256e`:

| mutación en `catalog_service.py` | resultado |
|---|---|
| `if len(clave) <= _MAX_VENDOR_ID:` → `<` | `186 passed` |
| `_MAX_VENDOR_ID = 60` → `70` | `186 passed` |

Qué rompería cada una (**leído, no corrido**): con `<`, un proveedor cuya
clave mide justo 60 pasa a tener id cortado con resumen; el arranque rearma
las filas de 60 o más, así que no se pierden. Con el tope en 70, una clave de
61 a 70 quedaría entera y el guardado la rechazaría con `vendor_id inválido`
(`_VENDOR_ID_RE` admite hasta 60, `catalog_service.py:97`; es el rechazo que
dio el id de 61 en la tabla de D219): ese proveedor no podría guardar
catálogo.

- (a) Dos datos más en la misma prueba: un nombre cuya clave mide 60 (queda
  entera) y uno de 61 (se corta). Dos líneas, como D219.
- (b) Riesgo anotado.

Recomiendo **(a)**: con D219 el formato del corte quedó fijado y el borde no;
son dos líneas. No lo hice acá porque D219 pedía un dato.

## Supuestos (reversibles)

1. **D218: dónde vive el sabotaje.** En `catalogo_largo2.sh`, que ya tiene
   `PG_URL` y los sabotajes de las otras dos tablas de la misma función. No
   extendí `catalogo_largo2_postgres.py` para que mire `operation_items`:
   sería el mismo chequeo en dos arneses.
2. **D218: el chequeo de base, una vez.** `base_en_verde` corre el arnés sin
   sabotaje para los dos bloques de Postgres; si está rojo escribe
   `BASE  | … ya está en rojo sin sabotaje`, **muestra las tres últimas líneas
   del arnés** y suma una falla. Cambia el bloque que ya estaba (el de
   `catalogo_largo2_postgres.py`): mismo texto de `BASE`, ahora con la causa.
   El chequeo de base de pytest, arriba del guion, no lo toqué.
3. **El arreglo de la consola limpia va en el arnés, no en el guion.**
   `catalogo3_postgres.py` toma su propio `entorno()` antes de importar
   `catalog_service`, como promete su «uso». Una línea.
4. **D219: nombre en ASCII**, para que el id del parámetro no dependa de cómo
   pytest escribe los acentos.
5. **D219: sin sabotaje nuevo en `catalogo3.sh`.** No es de §3; el rojo va
   mostrado una vez acá (§6). Si lo querés commiteado son 4 líneas en
   `catalogo3.sh`.

## D219: tu matiz y mi corrección

Mi riesgo original («los proveedores largos ya guardados dejan de encontrarse
y nada avisa») estaba exagerado. Tenías razón: `_migrate_catalogo_claves`
rearma al arrancar los `vendor_id` largos desde `vendor_nombre`.

- **Leído** en `main.py:1356-1362`: elige las filas con
  `length(vendor_id) >= 60` y les pone `_vendor_key(vendor_nombre)`.
- **Corrido, pero sólo para el paso de la versión anterior a la de hoy:**
  `catalogo3_postgres.py` guarda dos proveedores largos con `07504e0`,
  arranca la de hoy y da
  `OK    | la migración da el proveedor y la clave de hoy sin perder filas`.
  Ese chequeo compara contra `_vendor_key` de la misma versión: no fija el
  formato.
- **Límite, leído y no corrido:** el rearmado alcanza a los ids de 60 o más.
  Los de hoy miden justo 60. Un cambio que los deje más cortos (el corte a 38
  solo da 59) se rearma una vez, y a partir de ahí esas filas ya no entran en
  la consulta: un segundo cambio de formato no las tocaría.

Por eso no puse ningún comentario sobre la migración en la prueba. El dato
sirve para que cambiar el formato sea a propósito, no para evitar una pérdida
que hoy el arranque repara.

## D219: el rojo a mano

Sobre `8f98a31`, mutando sólo la última línea de `_vendor_key` y corriendo
los cuatro archivos `tests/test_catalogo*.py` (186 pruebas; en el informe
anterior dije «8 archivos»: son 4):

| mutación | resultado | qué falla |
|---|---|---|
| sin mutación (lo que `catalogo3.sh` corre como base) | `125 passed` | — |
| `clave[:38]` | `1 failed, 185 passed` | sólo el dato nuevo |
| `hexdigest()[:21]` | `4 failed, 182 passed` | el dato nuevo, `test_dos_proveedores_distintos_no_comparten_catalogo[prefijo-60]` y los dos de `test_el_origen_y_el_proveedor_se_guardan_enteros` (el id pasa a 61 y da `vendor_id inválido`) |
| `clave[:38]` y `hexdigest()[:21]` | `1 failed, 185 passed` | sólo el dato nuevo |

El rojo del dato nuevo, con el corte a 38:

```
E     - sudamericana_de_importaciones_y_distrib~b74fb800ad974e4778d7
E     + sudamericana_de_importaciones_y_distri~b74fb800ad974e4778d7
FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[Sudamericana de Importaciones y Distribuciones Generales del Litoral SA-sudamericana_de_importaciones_y_distrib~b74fb800ad974e4778d7]
```

## Para reproducir

```bash
# Postgres local y descartable; unos 23 minutos. Anda en una consola limpia.
PY=<venv>/bin/python scripts/testing/con_pg16.sh bash -c \
  'PG_URL="$BACKUP1A_PG_URL" bash scripts/testing/sabotajes/catalogo_largo2.sh 1f8ffa6'
# 38 líneas ROJO; la última:
# «ROJO  | el arranque no pasa el origen de los ítems a text: dice «FALLA | operation_items.origen pasa a text y la fila vieja queda igual»»
# fallas: 0; sale 0

# el rojo de la consola limpia (segundos): el arnés de antes del arreglo
git worktree add --detach /tmp/wt-d218 d5a96aa && cd /tmp/wt-d218
PY=<venv>/bin/python scripts/testing/con_pg16.sh bash -c \
  'env -u DATABASE_URL -u ENVIRONMENT "$PY" -I scripts/testing/catalogo3_postgres.py "$BACKUP1A_PG_URL"'
# RuntimeError: DATABASE_URL no está definida y ENVIRONMENT no es de desarrollo…; sale 1
# el mismo comando sobre 1f8ffa6: 10 OK, «todo OK», sale 0

# el dato de D219 (segundos)
python -m pytest -q --no-cov -p no:cacheprovider tests/test_catalogo3.py -k test_un_proveedor_latino_conserva_su_id
# 8 passed, 97 deselected
# y su rojo: en proyecto_maria/core/catalog_service.py, última línea de _vendor_key,
# clave[:39] → clave[:38] y hexdigest()[:20] → hexdigest()[:21]
python -m pytest -q --no-cov -p no:cacheprovider tests/test_catalogo*.py
# 1 failed, 185 passed; el que falla es …[Sudamericana de Importaciones …]

python scripts/testing/anclas_perdidas.py 1f8ffa6 | grep -cE 'catalogo_largo2\.sh|catalogo3\.sh'
# 0
python docs/pm/herramientas/chequeo-6.py 4b5ef68 8f98a31    # +14/−0
python docs/pm/herramientas/chequeo-6.py d5a96aa ea3256e    # +3/−2
python docs/pm/herramientas/chequeo-6.py 636b889 1f8ffa6    # +14/−9
# los tres: producto +0/−0, avisos: 0
```

## Puertas

| puerta | sobre | salida |
|---|---|---|
| `catalogo_largo2.sh` entero, Postgres 16, consola limpia | `1f8ffa6` | 38 `ROJO`, `fallas: 0`, `rc=0 segundos=1296` |
| ídem, antes del chequeo de base unificado | `ea3256e` | 38 `ROJO`, `fallas: 0`, `rc=0 segundos=1325` |
| `catalogo3_postgres.py` sin sabotaje, consola limpia | `d5a96aa` | `RuntimeError: DATABASE_URL no está definida…`, `rc=1 segundos=7` |
| ídem, con el arreglo en el árbol (es `2211e6b`) | `2211e6b` | 10 `OK`, `todo OK`, `rc=0 segundos=21` |
| ídem | `1f8ffa6` | 10 `OK`, `todo OK`, `rc=0`, 19 s |
| camino `BASE`, a mano: copia del guion de `1f8ffa6` sin los sabotajes de pytest, `PG_URL` a un puerto cerrado | worktree de `636b889` | dos `BASE  \| …` con `psycopg2.OperationalError: … port 1 failed: Connection refused`, `fallas: 2`, `rc=1` |
| `test_un_proveedor_latino_conserva_su_id` | `9120475` | `8 passed, 97 deselected` |
| lo que `catalogo3.sh` corre como base | `8f98a31` | `125 passed` |
| `anclas_perdidas.py` | `1f8ffa6` | sale 0; 22 filas, 0 de `catalogo_largo2.sh` y de `catalogo3.sh` |

De `8f98a31` a `1f8ffa6` no cambia nada de `proyecto_maria/` ni de `tests/`
(`git diff 8f98a31 1f8ffa6 --stat -- proyecto_maria tests` da vacío): lo de D219
no lo repetí.

```
chequeo-6 4b5ef68..8f98a31: avisos para mirar, no un veredicto
producto +0/−0
arnés +14/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0

chequeo-6 d5a96aa..ea3256e: avisos para mirar, no un veredicto
producto +0/−0
arnés +3/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0

chequeo-6 636b889..1f8ffa6: avisos para mirar, no un veredicto
producto +0/−0
arnés +14/−9
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

**D218, rojo antes del arreglo:** lo confirmaste vos (sin la tupla,
`FALLA | operation_items.origen pasa a text…`, salida 1) y ningún guion lo
corría. Hoy lo corre el guion: la línea 38.

## Hallazgos de la autorrevisión

| quién | hallazgo | severidad | qué hice |
|---|---|---|---|
| adversario-sonnet-medio (Sonnet, medio) | En una consola sin `DATABASE_URL` ni `ENVIRONMENT`, `catalogo3_postgres.py` sale 1 con `RuntimeError` y el bloque nuevo da `BASE` y salida 1 | media | Reproducido (`rc=1`, 7 s). Arreglado en `2211e6b`; guion entero otra vez en consola limpia |
| ídem | Con `<=` → `<` o el tope en 70, la prueba del id sigue verde | baja | Medido con las 186 pruebas: verde las dos. Es D224 |
| ídem | Reprodujo el sabotaje a mano (base `todo OK`, sin la tupla la `FALLA` esperada), el ancla aparece una vez, el id calculado aparte con `hashlib` coincide | — | Sin hallazgo |
| `/code-review high` (revisores en Fable) | Una base roja tira la salida: dice sólo `BASE  \| …`, sin causa | baja | Arreglado en `1f8ffa6` (`base_en_verde`), visto con un puerto cerrado |
| ídem | El bloque nuevo es una segunda copia del andamio checkout / base / sabotajes | baja | Arreglado en el mismo commit (§6: una vez) |
| ídem | El guion depende de un segundo commit viejo (`07504e0`) sin mensaje si falta | baja | Ahora una base roja muestra la causa. El caso del commit ausente: leído, no corrido |
| ídem | El proceso padre del arnés importa la app sólo para dos funciones puras; mejor calcular las claves en un hijo | baja | Queda. El padre recibe el mismo `entorno()` que los hijos, que importan `main` entero: lo que rompa el import del padre rompe antes a los hijos. Es una línea contra unas diez |
| ídem | `os.environ.update(entorno())` reescribe el entorno entero; `entorno()` tiene otro contrato que en los arneses vecinos | baja | Queda: ya escrito. Línea para la cola, abajo |
| ídem | Dos corridas completas del arnés para mirar una tupla | baja | Queda. Sin sabotaje tarda 21 s; el guion entero dio 1380 s, 1325 s y 1296 s en mis tres corridas de 38 |

Los revisores de `/code-review` no corrieron pruebas (no encontraron el
entorno virtual): leyeron, y corrieron `chequeo-6`, `bash -n` y el cálculo del
id. `/security-review`: no corrido, no toca producto.

**Líneas que propongo para `COLA-LIMPIEZA.md`** (las pasás vos):

- Muchos guiones de `scripts/testing/sabotajes/` tiran la salida del chequeo
  de base (`>/dev/null 2>&1`): una base roja dice sólo `BASE  | …`. Hay 113
  líneas `BASE  |` en 58 guiones; no conté una por una cuáles la tiran.
  `catalogo_largo2.sh` ya muestra el final con `base_en_verde`: llevarlo a
  `_entorno_comun.sh`.
- `catalogo3_postgres.py`: `entorno()` devuelve el entorno entero; en los
  arneses vecinos devuelve sólo lo que pisa. Unificar el contrato.

## Qué no corrí y riesgos

- La suite entera: no. Es arnés, producto +0/−0.
- `catalogo3.sh` entero: no. El dato nuevo sólo puede sumarle fallas, y lo que
  ese guion espera por nombre no cambió; corrí el comando exacto que usa como
  base (`125 passed`).
- `/security-review`: no.
- El texto de la excepción al sacar el `lock_timeout` (D223): no lo vi.
- Lo que digo «leído» en D224 y en el matiz de D219.
- El sabotaje nuevo depende de que `catalogo3_postgres.py` siga pudiendo
  armar su worktree de `07504e0`. En un clon que no lo tenga, el guion da
  `BASE`, muestra el final del arnés y sale 1 (leído).
- `catalogo_largo2.sh` suma dos corridas de `catalogo3_postgres.py`.

Archivos de producto tocados: ninguno. Arnés: `tests/test_catalogo3.py`,
`scripts/testing/sabotajes/catalogo_largo2.sh` y
`scripts/testing/catalogo3_postgres.py`.

Sigo con el paso 2 de tu orden: **PANTALLAS-MARIA**, empezando por la causa de
`pantalla_maria3` y `pantalla_maria4`, sobre los archivos que trajo tu rama
(`_registrar.js`).

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 67c8ff0, ya integrada en 636b889), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Entregado en 1f8ffa6 (informe en el commit siguiente), esperando veredicto: D218 y D219, una pieza, sólo arnés (catalogo_largo2.sh corre también catalogo3_postgres.py con la tupla de operation_items sacada: 38 ROJO, sale 0, en consola sin DATABASE_URL ni ENVIRONMENT; un dato más en test_un_proveedor_latino_conserva_su_id). Producto +0/−0. Abiertas, las decide la PM: D223 (el candado de _migrate_catalogo_claves no tiene sabotaje en el repo: recomiendo (a), uno para el advisory lock) y D224 (el borde del corte de _vendor_key no lo fija ninguna prueba: recomiendo (a), dos datos más). Ya decididas: D221 (b) y D222 (a): se retiran el 13 y el 24 de valor1. Orden de la PM, una pieza a la vez: 1) PANTALLAS-MARIA, la que arranco ahora (pantalla_maria3, maria4, maria5 y subitems1 en rojo desde MARIA-7; empezar por la causa de maria3 y maria4, que no está confirmada; puerta: los cuatro con servidor y base nuevos salen 0 y muestro una vez el rojo de hoy de cada causa; sólo arnés: si la causa es de producto, freno y aviso); 2) retirar el 13 y el 24 de sabotaje_valor1.sh y reanclar en código el 10 y el 28 (29 ROJO, sale 0, su línea sale de sabotajes-conocidos.txt); 3) AJUSTE-BORRADOR (producto en static/v2: primero un caso de pantalla en rojo; corre e2e_maria.sh); 4) los vencidos, uno por pieza: maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2. Próxima D libre: D225. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
