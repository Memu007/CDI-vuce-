# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DESPACHO-1b, devolución v4 sobre `03296d4`: **entregada** en `b5fb03a` (2026-11-05)

**Resultado:** si mientras se espera la fila otro pedido le cambia la clave o la borra, ninguna de las cuatro vías pierde el uso ni contesta éxito sin guardarlo. El upsert vuelve a insertar hasta 3 veces; si las 3 fallan, sale un error (500), nunca un 200 mudo. En Postgres 16, con la familia como datos (PUT que cambia la clave y DELETE, por operación, aprender, guardar y guardar-uso), `despacho1b_postgres.py` da «fallas: 8» con el producto de `03296d4` y «fallas: 0» con el de `b5fb03a`. Además, confirmar un NCM devuelve `historial_guardado: false` cuando la base falla o el producto no entra (la descripción crece al normalizarla): antes contestaba sólo `{"success": true}`. `despacho1b.sh` con `PG_DSN`: 136 ROJO, «sabotajes sin rojo: 0», «sin Postgres, no corridos: 0». Suite, con el comando de `ci.yml` y con el mío: «4278 passed» y «4288 passed», sin fallas.

### Decisiones

- **D51. La pantalla no lee `historial_guardado`.** El backend lo devuelve en la operación y, ahora, en confirmar un NCM. La UI no lo muestra: si no se guardó, el usuario no se entera.
  - (a) Dejarlo así: el dato queda en la respuesta y en el registro.
  - (b) Pieza aparte y chica: un aviso en la pantalla cuando llega `false`.
  - **Recomiendo (b), después de CATALOGO-LARGO-1.** Es un cambio de pantalla, fuera de esta devolución.

- **D52. Una descripción sin letras latinas se sugiere para cualquier consulta.** `normalizar_desc` (`main.py:9626`) deja sólo `a-z0-9`: «日本語の製品», «क़क़» o «--- …» quedan en `''`. El paso 3 de `sugerir_ncm` compara con `desc_norm in normalizar_desc(guardada)`, y `'' in x` es siempre verdadero, así que esa fila del historial sale como sugerencia «historial» para cualquier producto. Esto existe desde `a77e6ad` (2026-10-07). Lo encontré porque mi caso nuevo dejaba una fila así en la base de prueba.
  - (a) Dejarlo así.
  - (b) Pieza aparte y chica: ignorar en esa comparación las descripciones que normalizadas quedan vacías, con su caso.
  - **Recomiendo (b).** Es un defecto de sugerir, no de esta devolución: no lo toqué.

Estas D no me frenan: sigo con CATALOGO-LARGO-1.

### SHAs

| SHA | Qué |
|---|---|
| `576dc8d` | test: en Postgres, la fila que cambia de clave o se borra mientras se espera, por las cuatro vías (rojo en `03296d4`) |
| `aeae73b` | fix: el upsert vuelve a insertar si la fila se fue; confirmar un NCM devuelve `historial_guardado` |
| `b39d746` | fix: confirmar un NCM avisa también cuando el producto no entra (code-review, hallazgo 2) |
| `57c46f0` | test: `historial_guardado` con la base caída y con el producto que no entra; sabotajes de Postgres; sin `PG_DSN` el script de sabotajes no da verde |
| `b5fb03a` | test: el caso `[crece al normalizar]` retira la fila del historial que crea (abajo, «Una prueba que ensuciaba la base») |
| este | docs: informe |

**Archivos de producto:** `services/client_memory.py` (`upsert_client_product_history`) y `main.py` (`guardar_uso_ncm`). `producto +19/−11`, más 4 de CHANGELOG. Grep de historia de §6: vacío.

### Por qué un reintento y no `ON CONFLICT DO UPDATE`

Con READ COMMITTED, `INSERT … ON CONFLICT DO NOTHING` no espera la fila trabada, y el `SELECT … FOR UPDATE` que sigue vuelve vacío si la fila cambió de clave o se borró mientras esperaba. El arreglo deja el par INSERT y SELECT y lo repite hasta 3 veces. `DO UPDATE` serviría, pero no hay una forma portable (Postgres y SQLite) de saber si la fila se insertó o se actualizó, y el código lo necesita para sumar bien el uso. Tres intentos alcanzan salvo que otro pedido cambie la misma fila tres veces seguidas en el medio; ese caso da 500, no un éxito falso. Lo razoné por código: **no lo corrí**.

### Rojos antes del arreglo

`despacho1b_postgres.py` con el producto de `03296d4` y los casos de `576dc8d`:

```
FALLA | operacion, la fila cambia de clave mientras espera: el uso queda en una fila nueva: en cola True, 200 200 {"success":true,"operation_id":"be621347-98f1-4988-a7ed-badbed20ae67","op_code":"OP-000001","historial_guardado":false} []
FALLA | operacion, la fila se borra mientras espera: el uso queda en una fila nueva: en cola True, 200 200 {"success":true,"operation_id":"7136632d-597c-44f8-a782-bfb9bdf8ebe0","op_code":"OP-000002","historial_guardado":false} []
FALLA | aprender, la fila cambia de clave mientras espera: el uso queda en una fila nueva: en cola True, 200 200 {"success":true,"cliente_id":"008e07c6-c457-4995-b686-3f9ea5a3b2d2","aprendidos":0} []
FALLA | aprender, la fila se borra mientras espera: el uso queda en una fila nueva: en cola True, 200 200 {"success":true,"cliente_id":"008e07c6-c457-4995-b686-3f9ea5a3b2d2","aprendidos":0} []
FALLA | guardar, la fila cambia de clave mientras espera: el uso queda en una fila nueva: en cola True, 200 500 {"detail":"No pudimos procesar tu solicitud. Probá de nuevo en unos segundos. Si vuelve a pasar, escribinos a hola@ynera.com.ar y te ayudamos.","code":"internal []
FALLA | guardar, la fila se borra mientras espera: el uso queda en una fila nueva: en cola True, 200 500 {"detail":"No pudimos procesar tu solicitud. Probá de nuevo en unos segundos. Si vuelve a pasar, escribinos a hola@ynera.com.ar y te ayudamos.","code":"internal []
FALLA | guardar-uso, la fila cambia de clave mientras espera: el uso queda en una fila nueva: en cola True, 200 200 {"success":true} []
FALLA | guardar-uso, la fila se borra mientras espera: el uso queda en una fila nueva: en cola True, 200 200 {"success":true} []
fallas: 8
```

El mismo script con el producto de `aeae73b` da los 8 en OK y «fallas: 0». Por ejemplo:

```
OK    | guardar-uso, la fila se borra mientras espera: el uso queda en una fila nueva: en cola True, 200 200 {"success":true,"historial_guardado":true} [(1,)]
```

Hallazgo 2 del code-review (`historial_guardado` en `true` aunque el producto no entre), con el caso de `57c46f0` sobre el producto de `aeae73b`, `[crece al normalizar]`:

```
E   AssertionError: {"success":true,"historial_guardado":true}
```

### Una prueba que ensuciaba la base

El caso `[crece al normalizar]` de `57c46f0` dejaba en `test.db` una fila del historial con 2000 «क़». Por la D52, `test_ncm_sugerir_catalog.py`, corrido después, la recibía como sugerencia para cualquier consulta. Con los tests afectados sobre `57c46f0`: «11 failed, 371 passed». `b5fb03a` borra esa fila en un `finally`, también si el caso falla. Sobre `b5fb03a`, los mismos archivos dan «382 passed». El producto no cambió.

### Sabotajes nuevos

En `despacho1b.sh`:

| Sabotaje | Qué rompe | Qué tiene que dar rojo |
|---|---|---|
| el upsert no espera la fila | saca `.with_for_update()` | «dos procesos guardan y aprenden el mismo producto a la vez: una fila con 16 usos» (Postgres) |
| el upsert no reintenta si la fila se fue | `range(3)` → `range(1)` | las 8 combinaciones (4 vías × cambio de clave o borrado), en Postgres |
| confirmar un NCM no avisa que la base falló | saca `historial_guardado = False` del `except` | `test_confirmar_un_ncm_dice_si_no_guardo_el_historial[la base falla]` |
| confirmar un NCM no avisa que el producto no entró | `historial_guardado` deja de seguir a `entry` | `…[crece al normalizar]` |

Los dos de Postgres corren sólo con `PG_DSN`. Sin `PG_DSN` imprimen «NO CORRIDO» y el script sale con error, para que no parezca verde.

Las cuatro líneas de los sabotajes nuevos, de `despacho1b.sh b5fb03a` con `PG_DSN` (136 ROJO en total):

```
ROJO  | confirmar un NCM no avisa que la base falló: «FAILED tests/test_despacho1b.py::test_confirmar_un_ncm_dice_si_no_guardo_el_historial[la base falla]» 
ROJO  | confirmar un NCM no avisa que el producto no entró: «FAILED tests/test_despacho1b.py::test_confirmar_un_ncm_dice_si_no_guardo_el_historial[crece al normalizar]» 
ROJO  | el upsert no espera la fila: «FALLA | dos procesos guardan y aprenden el mismo producto a la vez: una fila con 16 usos» 
ROJO  | el upsert no reintenta si la fila se fue: «FALLA | operacion, la fila cambia de clave mientras espera» «FALLA | operacion, la fila se borra mientras espera» «FALLA | aprender, la fila cambia de clave mientras espera» «FALLA | aprender, la fila se borra mientras espera» «FALLA | guardar, la fila cambia de clave mientras espera» «FALLA | guardar, la fila se borra mientras espera» «FALLA | guardar-uso, la fila cambia de clave mientras espera» «FALLA | guardar-uso, la fila se borra mientras espera» 
```

### La suite: los dos comandos

Las dos corren sobre `b5fb03a`, en un worktree limpio:

- **El comando de `ci.yml`** (sus variables y sus 10 `--deselect`, con `-rs`): «4278 passed, 336 skipped, 10 deselected, 2 xfailed, 94 warnings in 501.79s», sale con 0.
- **Mi comando** (`--timeout=300`, SQLite nueva, con `-rs`): «4288 passed, 336 skipped, 2 xfailed, 92 warnings in 506.64s», sale con 0. Son los mismos tests: 4278 + 10 deseleccionados = 4288.

**Los 336 saltos, contra los 102 de la base de `/entregar`:** comparé los motivos de `-rs` y son los mismos en las dos corridas. 234 son de `tests/test_excel3.py`: «could not import 'xlwt'». `xlwt` no está en `requirements.txt`, así que la CI, que instala de ahí, también los saltea. Los otros 102 son los motivos viejos de la base (python-magic, routers que no están montados, tests marcados «needs update»…). No toqué nada de eso: está fuera de la pieza.

La primera corrida del comando de `ci.yml` quedó cortada al 52 % porque la tarea de fondo llegó a su tope de 2 h (iba en cadena detrás de los sabotajes). No la cuento: la puerta es la corrida completa de arriba.

### Autorrevisión

**Adversario (Sonnet, esfuerzo alto),** sobre `aeae73b`. Cada hallazgo lo reproduje antes de decidir. Confirmó que no hay doble suma ni pérdida en las 8 combinaciones.

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | Un sabotaje buscaba un patrón que aparecía dos veces | Arreglado en `57c46f0` |
| 2 | La UI no lee `historial_guardado` | D51 |
| 3 | Agotar los 3 intentos | Razonado por código, no corrido. Da 500 |
| 4 | Sin `PG_DSN`, el script de sabotajes salía con 0 | Arreglado en `57c46f0` (sale con error si `NO_CORRIDOS` > 0) |
| 5 | `catalog_service.save_products` también hace un SELECT y después un INSERT, y puede chocar igual | Riesgo. Propuesta: va a CATALOGO-LARGO-1, que toca ese catálogo |

**`/code-review high`** sobre `4931eb2..b39d746`:

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | La UI no lee el flag | D51 |
| 2 | `historial_guardado` en `true` con `entry` en `None` (el producto no entra) | Arreglado en `b39d746`, con rojo antes (arriba) |
| 3 | Da `false` si falla sólo el catálogo del proveedor | No es defecto: los dos se confirman en el mismo `commit` (`save_products`, `catalog_service.py:399`). Si falla el del proveedor, el `rollback` deshace también el del cliente, así que `false` es cierto |
| 4 | El reintento vuelve a insertar la clave vieja, no la nueva | Es lo pedido: el uso es del producto que se confirmó |
| 5 | Agotar los intentos da `RuntimeError`, o sea 500 | Se acepta: es un error a la vista, no un éxito falso |
| 6 | `DO UPDATE` sería más simple | No, por lo explicado arriba |
| 7 | `esperan_un_bloqueo` (en el script de Postgres) no filtra por la tabla | Riesgo menor de la prueba: en la base descartable no hay otros bloqueos |
| 8 | Sin Postgres, el script salía con 0 | Arreglado en `57c46f0` |
| 9 | El SELECT se repite aunque el INSERT haya insertado | Menor: es una lectura por intento, y la fila hace falta igual |

**`/security-review`:** el comando falló (`fatal: ambiguous argument 'origin/HEAD...'`, el clon no tiene `origin/HEAD`). Lo hice a mano sobre `4931eb2..b5fb03a`. No encontré nada. Los valores salen de la sesión y del cuerpo ya validado. Las consultas van por SQLAlchemy con parámetros. El flag nuevo no expone datos. No cambia quién puede escribir qué.

### `CLAUDE.md` §6: `chequeo-6.py 4931eb2 b5fb03a`

```
chequeo-6 4931eb2..b5fb03a: avisos para mirar, no un veredicto
producto +19/−11
arnés +145/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11332 → 11334
  proyecto_maria/services/client_memory.py: 298 → 304
avisos: 0
```

### Para la cola de limpieza (propuestas)

- `despacho_lector.py`: el despacho se abre dos veces (una para validar y otra para leer, en dos procesos). Es el hallazgo 7 de RENDIMIENTO-1c.
- `catalog_service.save_products`: el SELECT y después el INSERT pueden chocar con otro pedido igual que el upsert del cliente (adversario, hallazgo 5), si CATALOGO-LARGO-1 no lo cubre.

### Riesgos

- Agotar los 3 intentos: no lo corrí.
- `historial_guardado` no se ve en la pantalla (D51).

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| `despacho1b_postgres.py`, Postgres 16 descartable | `03296d4` (producto) | «fallas: 8» |
| `despacho1b_postgres.py` | `b5fb03a` | «fallas: 0» |
| `despacho1b.sh` con `PG_DSN` | `b5fb03a` | 136 ROJO, «sabotajes sin rojo: 0», «sin Postgres, no corridos: 0» |
| tests afectados (`test_despacho1b`, `test_guardar1`, `test_disco1`, `test_pa1_textos`, `test_ncm_sugerir_catalog`) | `57c46f0` | «11 failed, 371 passed» (la fila de arriba) |
| tests afectados | `b5fb03a` | «382 passed, 5 warnings in 59.24s» |
| `compileall` | `b5fb03a` | «SALIDA compile 0», sin otras líneas |
| suite, comando de `ci.yml` | `b5fb03a` | «4278 passed, 336 skipped, 10 deselected, 2 xfailed», sale con 0 |
| suite, mi comando | `b5fb03a` | «4288 passed, 336 skipped, 2 xfailed», sale con 0 |

**Lo que no corrí:** agotar los 3 intentos, el smoke y el ataque de aislamiento. Este cambio no toca sesión ni permisos.

### Comandos para reproducir

```bash
git checkout b5fb03a
# Postgres 16 descartable; DSN de ejemplo
python scripts/testing/despacho1b_postgres.py postgresql://cdi@127.0.0.1:55432/postgres     # «fallas: 0»
git checkout 03296d4 -- proyecto_maria && python scripts/testing/despacho1b_postgres.py postgresql://cdi@127.0.0.1:55432/postgres; git checkout b5fb03a -- proyecto_maria   # «fallas: 8»
PG_DSN=postgresql://cdi@127.0.0.1:55432/postgres bash scripts/testing/sabotajes/despacho1b.sh b5fb03a   # «sabotajes sin rojo: 0», «sin Postgres, no corridos: 0»
bash scripts/testing/sabotajes/despacho1b.sh b5fb03a                     # sin PG_DSN: «NO CORRIDO» ×2, sale con error
```

## RENDIMIENTO-1c (D48 a): **entregada** en `3f0ed57` (2026-11-05)

**Resultado:** validar un PDF corre en el proceso aparte del lector, con un tope de 256 MB y 30 s de tiempo, al subir una factura y al leer un despacho. El PDF de 200 repeticiones hacía crecer la app 1029 MB (medido en su proceso); ahora la hace crecer 0 MB y devuelve 400 «El PDF es demasiado pesado para abrirlo. Probá con otro archivo.». Si un usuario sube diez PDFs pesados a la vez, la factura de otro usuario termina en 0,17 s, con las diez todavía en fila. Si no hay lugar para validar dentro del tiempo máximo, la respuesta es 503 «Hay muchos PDFs en revisión. Probá de nuevo en un rato.» y no un 400 que culpa al archivo. `rendimiento1c.sh`: 13 ROJO, «sabotajes con falla: 0», sobre `3f0ed57`. Suite completa sobre `3f0ed57`: «4286 passed, 336 skipped, 2 xfailed».

Esta entrega no toca DESPACHO-1b (arriba), salvo el texto del error en modo validar (ver «Qué cambió después de `03296d4`»).

### Decisiones

- **D49. El vendedor de la factura y `process_pdf` siguen abriendo el PDF dentro de la app.** `extraer_texto_pdf_seguro` (vendedor heurístico) y `process_pdf` leen el texto en el proceso de la app. Eso pasa después de validar, así que el PDF de 200 repeticiones no llega ahí. Lo que sí podría llegar es un PDF que pasa la validación y se infla al extraer el texto: no lo medí.
  - (a) Dejarlo así.
  - (b) Pieza aparte: extraer el texto también en el proceso aparte, con el mismo tope.
  - **Recomiendo (b), después de CATALOGO-LARGO-1.** El mecanismo ya existe. Lo que falta es la prueba con un PDF que se infle al extraer, no al contar hojas.
- **D50. Los cupos de validación se pueden ocupar con dos cuentas.** Hay dos lugares para toda la app y cada validación puede durar hasta 30 s. En modo validar no hay tope de CPU. Dos cuentas que suben, una y otra vez, PDFs que tardan sin inflarse frenan las validaciones de todos hasta 30 s cada vez.
  - (a) Dejarlo así: el limitador por cuenta ya acota cuántas subidas hace cada una.
  - (b) Tope de CPU de 10 s también en validar, el mismo que ya tiene el lector. Un PDF normal valida en unos 125 ms.
  - (c) Más lugares (4, uno por CPU).
  - **Recomiendo (b).** Reduce el bloqueo de 30 s a ~10 s, reusa lo que ya existe y no suma memoria. Con (c), el peor caso pasa a ser 4 × 256 MB.
  - Lo que midió el adversario, para dimensionar: con PDFs que se inflan (cortan rápido por memoria), cada cuenta atacante suma unos 0,4 s de espera a los demás; para llegar a 30 s harían falta unas 75 cuentas. El caso caro es el de PDFs lentos que no se inflan, que es el de arriba. Desde `5819029`, el que se queda sin lugar recibe 503 y no un 400.

Ninguna de las dos me frena: sigo con CATALOGO-LARGO-1.

### SHAs

| SHA | Qué |
|---|---|
| `ccf5d8c` | fix: validar un PDF corre en un proceso aparte con tope de memoria |
| `033cb11` | test: el PDF que se infla no hace crecer la app y diez de uno no frenan a otro; RENDIMIENTO-1 y DESPACHO-1b simulan la validación lenta en el proceso aparte |
| `843cc08` → `7dd008f` | fix → test: si el validador se cae, 500 y no «PDF inválido»; las diez se miden por orden, no por reloj |
| `9fd6bd0` | refactor: el comentario de la validación no nombra piezas (chequeo-6) |
| `a341966` → `a4d2310` | fix → test: el registro dice «el validador de PDF» cuando falla la validación (code-review, hallazgo 10) |
| `5819029` → `3f0ed57` | fix → test: esperar lugar da 503 y no culpa al archivo; quedarse sin memoria dentro de pypdf (SystemError) es «demasiado pesado»; la prueba de diez también con despachos; 8 sabotajes nuevos (adversario) |
| este | docs: informe |

**Archivos de producto:** `core/despacho_lector.py`, `security/file_security.py` y `main.py`. En `main.py`, sólo las dos llamadas que pasan `clave=user["username"]`.

### Qué cambió después de `03296d4`

`9fd6bd0` cambia sólo un comentario. `5819029` suma `SinLugar` (subclase de `TimeoutError`) en `validar_pdf_aparte` y `_leer_aparte`: en modo leer el despacho sigue cayendo en el mismo `except TimeoutError` de `main.py` (504), así que esa respuesta no cambia; en `validar_pdf`, un `SystemError` pasa a ser `MemoryError`. `a341966` cambia el texto de los tres `RuntimeError` de `_leer_aparte`: dicen «el validador de PDF» en modo validar y siguen diciendo «el lector de despachos» en modo leer. `tests/test_despacho1b.py:902` exige ese texto en modo leer y pasa (`301 passed, 3 warnings in 82.37s (0:01:22)`, `test_rendimiento1c.py` + `test_rendimiento1.py` + `test_despacho1b.py`, sobre `3f0ed57`). `despacho1b.sh` entero corre sobre `b5fb03a`, que contiene `3f0ed57` (DESPACHO-1b, arriba). Antes había corrido a mano, sobre `3f0ed57`, los dos sabotajes que caen en `_leer_aparte` (verde sin sabotaje, rojo con él):

```
un resultado que no es objeto pasa      → FAILED tests/test_despacho1b.py::test_un_lector_que_no_devuelve_un_objeto_es_un_error
el caño roto tapa el código de salida   → FAILED tests/test_despacho1b.py::test_un_lector_que_sale_sin_leer_todo_dice_con_que_salio
```

### `CLAUDE.md` §6: `chequeo-6.py ccf5d8c^ 3f0ed57`

La base `ccf5d8c^` incluye DESPACHO-1b vuelta 4, que se commiteó en el medio. Por eso el chequeo cuenta las dos piezas juntas. **Sólo RENDIMIENTO-1c: `producto +126/−53`** (suma de `ccf5d8c`, `843cc08`, `9fd6bd0`, `a341966` y `5819029`, sacada de `git show --numstat`; CHANGELOG incluido). Son 73 líneas netas, más de 20. El porqué: hacen falta el modo validar del proceso aparte, `validar_pdf_aparte` con cupos y la fila por usuario, y separar en `validate_file_upload` los casos tiempo, pesado, caído y sin lugar. Lo que salió de `file_security.py` (el pypdf en la app) es lo que resta.

```
chequeo-6 ccf5d8c^..3f0ed57: avisos para mirar, no un veredicto
producto +520/−246
  AVISO producto suma 274 líneas netas: el informe dice por qué (§6: más de 20)
arnés +1868/−69
historia (grep de §6, sin líneas movidas):
  AVISO historia en proyecto_maria/main.py:1331: """Una fila por producto en client_product_history (DESPACHO-1b): agrega
  AVISO historia en proyecto_maria/services/client_memory.py:12: escriben usan esa regla y la base no deja dos filas iguales (DESPACHO-1b).
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 766 → 867
  AVISO comentario nuevo de 3 líneas: proyecto_maria/core/despacho_lector.py:65 (§6: una o dos)
  AVISO comentario nuevo de 5 líneas: proyecto_maria/core/despacho_lector.py:683 (§6: una o dos)
  AVISO comentario nuevo de 3 líneas: proyecto_maria/core/despacho_lector.py:764 (§6: una o dos)
  proyecto_maria/database/models.py: 574 → 578
  proyecto_maria/main.py: 11177 → 11332
  AVISO función nueva de 87 líneas: proyecto_maria/main.py:1330 _migrate_product_history_clave (§6: ~60)
  AVISO comentario nuevo de 3 líneas: proyecto_maria/main.py:1401 (§6: una o dos)
  AVISO comentario nuevo de 4 líneas: proyecto_maria/main.py:1331 (§6: una o dos)
  proyecto_maria/security/file_security.py: 581 → 582
  proyecto_maria/services/client_memory.py: 285 → 298
avisos: 9
```

Cada AVISO:
- **Historia en `main.py:1331` y `client_memory.py:12`; función de 87 líneas en `main.py:1330`; comentarios en `main.py:1331` y `main.py:1401`; comentario en `despacho_lector.py:65`:** son de DESPACHO-1b vuelta 4 y se explicaron en su informe (`git show 03296d4:docs/pm/PARA-PM-2.md`).
- **Comentarios de 5 y 3 líneas en `despacho_lector.py:683` y `:764`:** son los docstrings de `validar_pdf_aparte` y `_main`, de `ccf5d8c` (28/10), escritos antes del 04/11. Quedan como están y van a la cola de limpieza.
- **Producto 274 netas:** el porqué de esta pieza está arriba (73 netas). El resto es DESPACHO-1b.

### Comandos para reproducir

```bash
git checkout 3f0ed57
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares ENVIRONMENT=test DATABASE_URL=sqlite+aiosqlite:///./test.db
python -m pytest -q --no-cov tests/test_rendimiento1c.py            # 6 passed
bash scripts/testing/sabotajes/rendimiento1c.sh 3f0ed57             # 13 ROJO; «sabotajes con falla: 0»
bash scripts/testing/sabotajes/rendimiento1.sh 3f0ed57              # 11 ROJO; «sabotajes con falla: 0»
python -c "import sys; sys.path.insert(0,'tests'); import test_rendimiento1c as t; print(t._correr('memoria'))"   # 'crecio_mb': 0
git checkout ccf5d8c^ -- proyecto_maria && python -m pytest -q --no-cov tests/test_rendimiento1c.py -k infla; git checkout 3f0ed57 -- proyecto_maria   # rojo: «la app creció 1029 MB»
```

### Rojo antes del arreglo

Sobre el producto de `ccf5d8c^`, con los casos de `033cb11`, el PDF de 200 repeticiones dio `la app creció 1029 MB`. Los dos hallazgos del adversario que arreglé dieron rojo antes del arreglo, con los casos de `3f0ed57` sobre el producto de `a4d2310`: `AssertionError: (['b', 'c'], (400, 'No pudimos abrir el PDF: tardó demasiado. Probá con otro archivo.'))` y `Failed: DID NOT RAISE MemoryError` (`2 failed, 4 passed, 3 warnings in 26.85s`). Las salidas de los dos scripts de sabotaje sobre `3f0ed57`:

```
ROJO  | validar el PDF vuelve al proceso de la app: dice «FAILED tests/test_rendimiento1c.py::test_un_pdf_que_se_infla_no_hace_crecer_la_app»
ROJO  | sin fila por usuario: todas las validaciones comparten los dos lugares: dice «B esperó detrás de las bombas de A»
ROJO  | la subida de facturas no pasa el usuario: dice «B esperó detrás de las bombas de A»
ROJO  | vuelve a contar páginas antes de mirar si está encriptado: dice «FAILED tests/test_rendimiento1c.py::test_validar_aparte_devuelve_lo_mismo_que_antes»
ROJO  | un validador que se cae vuelve a ser un PDF inválido: dice «FAILED tests/test_rendimiento1c.py::test_un_validador_que_se_cae_es_un_error_nuestro»
ROJO  | la lectura de despachos no pasa el usuario: dice «despacho: B esperó detrás de las bombas de A»
ROJO  | esperar el turno del usuario no tiene tiempo máximo: dice «FAILED tests/test_rendimiento1c.py::test_esperar_un_lugar_no_culpa_al_archivo»
ROJO  | sin tope de validaciones a la vez: dice «(['b', 'c'], 'pasó')»
ROJO  | la fila del usuario no se borra: dice «(['b', 'c'], {'»
ROJO  | esperar un lugar libre vuelve a culpar al archivo: dice «(['b', 'c'], (400, 'No pudimos abrir el PDF: tardó demasiado»
ROJO  | esperar el turno del usuario vuelve a culpar al archivo: dice «(['a'], (400, 'No pudimos abrir el PDF: tardó demasiado»
ROJO  | sin lugar vuelve a ser un 400: dice «(['b', 'c'], (400, 'No pudimos abrir el PDF: tardó demasiado»
ROJO  | quedarse sin memoria en C vuelve a ser un PDF inválido: dice «DID NOT RAISE»
sabotajes con falla: 0
SALIDA r1c 0
ROJO  | el PDF se vuelve a leer en el hilo del servidor: dice «FAILED tests/test_rendimiento1.py::test_health_responde_mientras_se_lee_un_pdf»
ROJO  | el texto del PDF se vuelve a leer en el hilo del servidor: dice «FAILED tests/test_rendimiento1.py::test_health_responde_mientras_se_lee_el_texto_del_pdf»
ROJO  | Gemini vuelve a correr en el hilo del servidor: dice «FAILED tests/test_rendimiento1.py::test_health_responde_mientras_gemini_sugiere_ncm»
ROJO  | la lectura pierde el tiempo máximo: dice «FAILED tests/test_rendimiento1.py::test_lectura_con_tiempo_maximo_y_error_claro»
ROJO  | validar el PDF vuelve al hilo del servidor: dice «FAILED tests/test_rendimiento1.py::test_health_responde_mientras_se_valida_el_pdf»
ROJO  | validar el PDF pierde el tiempo máximo: dice «FAILED tests/test_rendimiento1.py::test_validar_el_pdf_tiene_tiempo_maximo»
ROJO  | vuelve a contar páginas antes de mirar si está encriptado: dice «FAILED tests/test_rendimiento1.py::test_pdf_encriptado_dice_que_esta_encriptado»
ROJO  | el texto del vendedor sin tiempo máximo: dice «FAILED tests/test_rendimiento1.py::test_texto_del_vendedor_tiene_tiempo_maximo»
ROJO  | las lecturas de PDF vuelven al grupo de hilos compartido: dice «FAILED tests/test_rendimiento1.py::test_pdfs_lentos_no_traban_a_ncm_ni_a_la_validacion»
ROJO  | un error de tiempo del lector pasa por lectura lenta: dice «FAILED tests/test_rendimiento1.py::test_error_de_tiempo_adentro_del_lector_no_es_lectura_lenta»
ROJO  | Gemini sin tiempo máximo: dice «FAILED tests/test_rendimiento1.py::test_gemini_sin_respuesta_no_cuelga_la_sugerencia»
sabotajes con falla: 0
SALIDA r1 0
```

### Autorrevisión

**`/code-review high` sobre `ccf5d8c^..9fd6bd0`.**

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | En modo validar no hay tope de CPU | Riesgo; D50 (b) |
| 2 | Dos cuentas ocupan los dos lugares y frenan todas las validaciones hasta 30 s | D50 |
| 3 | La fila por usuario no tiene largo máximo y guarda los cuerpos en memoria | Riesgo: era igual antes, y lo acotan el limitador y el tope de tamaño de subida |
| 4 | Un despacho con un árbol de hojas pesado da 400 «demasiado pesado» en vez de 200 con AVISO_SIN_MEMORIA | Riesgo de UX. Si lo pesado es el texto, el despacho sigue pasando por la rama vieja |
| 5, 6 | El validador que se cae daba 400 «Invalid PDF file»; las diez se medían por reloj | Arreglado en `843cc08` y `7dd008f` |
| 7 | El despacho se abre dos veces (validar y leer, en dos procesos) | Riesgo: unos 125 ms más por despacho. A la cola de limpieza |
| 8 | Dos esquemas de concurrencia: la validación espera en fila y el lector da 429 | A propósito: subir una factura no debería rebotar. Leer un despacho ya daba 429 |
| 9 | Dos mensajes de «demasiado pesado» | A propósito: uno es de factura y otro de despacho |
| 10 | El registro decía «lector de despachos» también en modo validar | Arreglado en `a341966`, con rojo en `a4d2310` antes (`assert 'el validador de PDF salió con 7' in '...el lector de despachos salió con 7'`) |

**Adversario (Opus, esfuerzo alto):**

Revisó `9fd6bd0`. Cada hallazgo lo reproduje antes de decidir.

| # | Hallazgo | Qué hice |
|---|---|---|
| A1 | Esperar un lugar libre (o el turno del usuario) más que el tiempo máximo daba 400 «tardó demasiado. Probá con otro archivo», que culpa a un archivo que ni se abrió | Arreglado en `5819029`: 503 «Hay muchos PDFs en revisión». Rojo antes, arriba |
| A1b | Los dos lugares son para toda la app: las cuentas atacantes hacen esperar a las demás | D50, con su medición |
| A2a | Un PDF válido de 9,1 MB (2500 hojas × 70 enlaces) ahora se rechaza por el tope de 256 MB | Riesgo: es el tope pedido. Una factura real no tiene esa forma |
| A2b | Sin memoria dentro de una función en C de pypdf sale `SystemError`, y su texto interno llegaba al usuario como PDF inválido | Arreglado en `5819029`: pasa a «demasiado pesado». Rojo antes, arriba |
| A3a–d | Sabotajes que daban verde: la lectura de despachos sin usuario, el turno del usuario sin tiempo máximo, sin tope de lugares, la fila que no se borra | Casos y sabotajes en `3f0ed57` |
| A4 | Sin tope de CPU al validar; si matan al worker con SIGKILL, el hijo queda huérfano hasta su tiempo máximo; memoria del contenedor hasta 4 workers × 2 × 256 MB; el camino nunca corrió en la imagen Docker de producción | Riesgos, abajo |

### Riesgos, sin arreglo en esta pieza

- **Costo por subida:** validar aparte suma unos 125 ms por PDF chico (medí 126, 120 y 132 ms); importar pypdf se lleva 53. Es para toda factura y todo despacho.
- **D49 y D50**, arriba.
- **Hallazgos 3, 4 y 7** de la tabla del code-review.
- **A2a:** un PDF legítimo muy grande en estructura se rechaza.
- **A4:** huérfanos con SIGKILL al worker (viven hasta 30 s); el peor caso de memoria del contenedor, según cuántos workers corran en Railway; **no lo probé en la imagen Docker de producción**: si `RLIMIT_AS` o el `exec` del hijo se comportan distinto ahí, se ve al publicar.

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| `test_rendimiento1c.py` + `test_rendimiento1.py` + `test_despacho1b.py` | `3f0ed57` | `301 passed, 3 warnings in 82.37s (0:01:22)` |
| `rendimiento1c.sh` | `3f0ed57` | 13 ROJO, `sabotajes con falla: 0`, salida 0 |
| `rendimiento1.sh` | `3f0ed57` | 11 ROJO, `sabotajes con falla: 0`, salida 0 |
| dos sabotajes de `despacho1b.sh` a mano | `3f0ed57` | 1 passed sin sabotaje y 1 failed con él, en cada uno |
| suite completa, desde un worktree limpio | `3f0ed57` | `4286 passed, 336 skipped, 2 xfailed, 93 warnings in 504.16s (0:08:24)`, con mi comando, sin `-rs` (los dos comandos, sobre `b5fb03a`, en DESPACHO-1b arriba) |
| `compileall` | `3f0ed57` | «SALIDA compile 0» (dos `SyntaxWarning` viejos de `pdf_extractor.py:927` y `:936`, que esta pieza no toca) |

**Lo que no corrí:** la imagen Docker de producción, el smoke y el ataque de aislamiento. La pieza no toca sesión ni permisos, y el `main.py` sólo pasa el usuario.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP cada 2 h (minuto 35, horario de Argentina); timbre a la PM principal session_01B7FVQspcEHF7PqNv797wNM. Entregadas sin veredicto: DESPACHO-1b devolución v4 en b5fb03a y RENDIMIENTO-1c en 3f0ed57. Decisiones abiertas: D49 (el vendedor de la factura abre el PDF en la app), D51 (la pantalla no lee historial_guardado), D50 (dos cuentas ocupan los cupos de validación), D52 (descripción sin letras latinas se sugiere para cualquier consulta). Próxima D libre: D53. Sigo con CATALOGO-LARGO-1 → SESION-1 → ABUSO-1 → SUFIJOS-2+SEGURO-1 → SEGURO-2 → EMAIL-1 → CONEXIONES-1 → OBSERVABILIDAD-1 → ORG-1+D40. Reglas: sólo me piden cosas Emi y la PM; nada se publica sin el «dale» de Emi para el SHA; nunca main, ni force, ni amend de lo subido; sin secretos ni datos reales (los TXT y la proforma del 2026-10-24 no entran); ningún cambio en el TXT sin prueba; nunca Gemini, VUCE simulado; subagentes hasta esfuerzo alto, nunca el consejero; EMAIL-1, nombres sin escapar, envío sincrónico y token viejo no se arreglan hasta que Emi diga que sí; ADMIN_USERNAMES no se toca.
