# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.


## DESPACHO-1b, devolución sobre `1f5480e`: **entregada** en `{SHA}` (2026-10-29)

**Resultado:** los 8 puntos están arreglados. Cada uno tiene su rojo antes del arreglo, sobre el producto viejo, y su sabotaje. `despacho1b.sh` da {SAB}. La suite completa da `4284 passed, 336 skipped, 2 xfailed, 96 warnings in 677.94s (0:11:17)`, salida 0. En Postgres 16, dos procesos que guardan y aprenden el mismo producto a la vez dejan una fila con los 16 usos.

**Nada para decidir.** No abro ninguna D; la próxima libre sigue siendo la D49. Los supuestos reversibles están abajo.

**Qué trae el diff contra `1f5480e`, además de esta pieza:**
- tus docs (`docs/pm/`, `CLAUDE.md`);
- DISCO-1 (`5c46e36`), aceptada y sin integrar;
- RENDIMIENTO-1c (`ccf5d8c`, `033cb11`, `843cc08` y `7dd008f`), **sin entregar**. Toca `file_security.py`. Viene después de esta pieza, como dice tu canal.

**Archivos de producto de esta pieza:** `services/client_memory.py`, `main.py`, `core/despacho_lector.py` y `database/models.py`.

| SHA | Qué |
|---|---|
| `c66f7e7` | test: rojos antes del arreglo |
| `eb4e615` | fix: una regla de identidad y la base la sostiene |
| `dc1c610`, `ba9e42a`, `789815c` | test: guardar-uso como quinta vía, NFC, sabotajes por punto, arnés de Postgres 16 |
| `697ffb6` → `669bac0` → `daefd4b` | rojo → fix → sabotajes: el corte por CPU conserva lo leído, el largo se mide en NFC y la operación avisa lo que no guardó (autorrevisión) |
| `7b1f4bd`, `178e5fe` → `9dca44f` → `bdf8eac` | rojo → fix → sabotajes: la migración escribe las claves después de unir (code-review, hallazgo 1) |
| `9d67853` → `ae2ab9a` → `7e96b32` | rojo → fix → sabotajes: learn y la operación pasan los números crudos (code-review, hallazgo 2) |
| `7a34520` | test: sabotajes de la divisa con espacios y en minúscula (punto 7) |
| `91726ad` | docs: CHANGELOG de la vuelta |
| `c55bd32` → `e035fc9` | rojo → fix: la operación con productos que no son objetos, confirmar NCM y el PUT validan como guardar (adversario, hallazgos 1, 2, 3 y 5) |
| `4ea1cb4` | test: DISCO-1, el tope de confirmar entra con el NCM válido más largo (`8471.49.00.100D`) |
| `0c3a059` | test: el origen vacío del cambio deja «XX» en la fila; sabotajes de la operación, confirmar y el PUT |
| `b11809f` → `fca1878` → `4081221` | rojo → fix → sabotajes: el origen es ASCII, la operación rechaza un resumen o ítems de otro tipo, constante del aviso del NCM (code-review 2) |
| `f86005f` → `f5b8a93` → `17386a1`, `e9173de` | rojo → fix → sabotajes: el origen se valida como se escribió («ıt» entraba como IT), el origen «ﬁ», la operación vacía guarda ceros (code-review 3) |
| `bd14302` | refactor: `pais_reconocido` ya pasa a mayúsculas (code-review 4, hallazgo 7) |
| `4034cdd` | test: `guardar1.sh`, los sabotajes de editar y de aprender buscan el código de ahora |
| `bb913d0` | test: `despacho1b.sh` al día con el código de la vuelta (cuatro sabotajes no distinguían) y uno nuevo para `_DECIMAL`; el caso del PUT manda el NCM con espacios |
| `03296d4` | test: las hojas leídas antes del corte se miden con un entender que cuesta 50 ms (el sabotaje del tope de entender salía VERDE) |
| este | docs: informe y CHANGELOG |

## `CLAUDE.md` §6: `chequeo-6.py 1f5480e 03296d4`

Todo el código de esta vuelta es de antes del 04/11; no lo reescribí, como pide tu canal. De `bb913d0` a `03296d4` sólo cambia `tests/test_despacho1b.py` (+14/−3, la diferencia del arnés); de ahí a la cabeza, documentos. Ese cambio es del 05/11: le rige §6 y el chequeo no le marca avisos.

```
chequeo-6 1f5480e..03296d4: avisos para mirar, no un veredicto
producto +496/−242
  AVISO producto suma 254 líneas netas: el informe dice por qué (§6: más de 20)
arnés +1888/−71
historia (grep de §6, sin líneas movidas):
  AVISO historia en proyecto_maria/main.py:1331: """Una fila por producto en client_product_history (DESPACHO-1b): agrega
  AVISO historia en proyecto_maria/security/file_security.py:490: # con la memoria topeada y tiempo máximo (RENDIMIENTO-1 y 1c).
  AVISO historia en proyecto_maria/services/client_memory.py:12: escriben usan esa regla y la base no deja dos filas iguales (DESPACHO-1b).
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 766 → 850
  AVISO comentario nuevo de 3 líneas: proyecto_maria/core/despacho_lector.py:65 (§6: una o dos)
  AVISO comentario nuevo de 5 líneas: proyecto_maria/core/despacho_lector.py:678 (§6: una o dos)
  AVISO comentario nuevo de 3 líneas: proyecto_maria/core/despacho_lector.py:747 (§6: una o dos)
  proyecto_maria/database/models.py: 574 → 578
  proyecto_maria/main.py: 11177 → 11332
  AVISO función nueva de 87 líneas: proyecto_maria/main.py:1330 _migrate_product_history_clave (§6: ~60)
  AVISO comentario nuevo de 3 líneas: proyecto_maria/main.py:1401 (§6: una o dos)
  AVISO comentario nuevo de 4 líneas: proyecto_maria/main.py:1331 (§6: una o dos)
  proyecto_maria/security/file_security.py: 581 → 579
  proyecto_maria/services/client_memory.py: 285 → 298
avisos: 10
```

El rango trae también RENDIMIENTO-1c (`ccf5d8c`, `843cc08`), que no está en `1f5480e`: es todo `file_security.py` y +97/−44 por commit. Lo de esta pieza suma +430/−229 por commit (`eb4e615` +312/−159 y siete arreglos de revisión).

Cada aviso:
- **254 netas.** Unas 200 son de esta pieza. Las cinco vías pasaban por cuatro reglas distintas. Para unirlas restaron −229, pero hubo que sumar tres cosas que no estaban: la migración que une los duplicados ya guardados (87 líneas), la escritura con `ON CONFLICT` y `FOR UPDATE` contra el índice, y la validación del PUT y de la operación. Las 53 netas de RENDIMIENTO-1c se explican en su entrega.
- **Historia, tres:** ya escrito, va a la cola de limpieza. La de `file_security.py:490` es de RENDIMIENTO-1c.
- **Comentarios de 3 a 5 líneas, seis:** ya escrito, va a la cola de limpieza.
- **`_migrate_product_history_clave`, 87 líneas:** ya escrito, va a la cola de limpieza. Se parte en leer las filas, unir y escribir las claves.

Líneas que propongo para `COLA-LIMPIEZA.md`:
- `proyecto_maria/main.py:1330` `_migrate_product_history_clave` (87 líneas): partir en leer, unir y escribir claves; su docstring nombra la pieza.
- `proyecto_maria/core/despacho_lector.py:65`, `:678`, `:747` y `main.py:1401`: comentarios de 3 a 5 líneas, a una o dos con el porqué.
- `proyecto_maria/services/client_memory.py:12`: el docstring del módulo nombra la pieza.

Lo que el chequeo no mide, mirado a ojo:
- **Un chequeo en un solo lugar:** falla. La validación del producto se llama desde guardar y desde el PUT (riesgo 8 del code-review). Va a la cola: «`main.py`, guardar el despacho y el PUT del catálogo validan el producto por separado; una función que valide un renglón».
- **Un caso por causa:** las familias van como datos de un caso (`dos_vias`, `otros_digitos`, `medio_par`). Los dos casos de la forma Unicode miran causas distintas. Uno mira qué forma se guarda; el otro, que la NFC vaya después de pasar a minúsculas.

## Comandos para reproducir

```bash
git checkout {SHA}
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares ENVIRONMENT=test DATABASE_URL=sqlite+aiosqlite:///./test.db
python -m pytest -q --no-cov tests/test_despacho1b.py      # `281 passed, 3 warnings in 47.30s`
bash scripts/testing/sabotajes/despacho1b.sh {SHA}           # al final: «sabotajes sin rojo: 0»
DATABASE_URL=postgresql+asyncpg://…/descartable python scripts/testing/despacho1b_postgres.py   # al final: «fallas: 0»
```

## Punto por punto

1. **Una identidad en todas las vías.**
   - `identidad_del_producto` (client_memory.py) es la única regla: NCM llevado a 8 dígitos (sin puntos, guiones, espacios ni letra SIM) y descripción en NFC, sin mayúsculas (`casefold`) y con los espacios juntados. La clave es el sha256 de las dos.
   - La usan las cinco vías que escriben el catálogo: aprender, la operación, guardar el despacho, guardar-uso y el cambio (PUT). Sumé guardar-uso, que la devolución no nombraba y también escribe.
   - **Caso por cada par de vías:** `test_el_mismo_producto_por_dos_vias_queda_en_una_fila` está parametrizado por los 20 pares ordenados de vías. La primera escribe y la segunda escribe el mismo producto con otro formato. Exige una fila.
   - **Los cuatro reproducidos por la PM:**
     - los 275 caracteres: `test_dos_descripciones_que_comparten_275_caracteres_son_dos_productos`;
     - 10 dígitos y después guardar: `test_aprender_con_10_digitos_y_guardar_el_despacho_da_una_fila`;
     - compuesta y descompuesta: `test_la_n_compuesta_y_la_descompuesta_son_el_mismo_producto` y `test_las_minusculas_de_dos_formas_de_lo_mismo_son_el_mismo_producto`;
     - guiones: `test_cada_forma_del_mismo_producto_suma_a_la_misma_fila[guiones]`.
   - **Supuesto aceptado:** otra tilde u otra puntuación es otro producto (`test_otra_tilde_u_otra_puntuacion_es_otro_producto`).
2. **Lo que no es un NCM no entra.**
   - Dígitos arábigos, de ancho completo o mezclados dan 400 en las cinco vías (`test_un_ncm_con_otros_digitos_da_400_por_cada_via`, 15 casos). Al guardar un despacho, ese renglón vuelve marcado con el motivo (`test_guardar_un_despacho_con_otros_digitos_marca_el_renglon`).
   - Un ítem de learn que no es objeto da 400 y no 500: `test_aprender_un_item_que_no_es_un_objeto_da_400` (texto, lista, número y null).
   - Un `\ud800` en cualquier texto da 400 y nada queda guardado: `test_aprender_con_medio_par_da_400`, `test_una_operacion_con_medio_par_da_400_y_no_queda` y `test_cambiar_con_medio_par_da_400` (NCM, origen y descripción).
   - **La operación** da 400 «Cada producto tiene que ser un objeto.» si `items` no es una lista de objetos (número, texto, null, lista, `"x"`, `{"a": 1}`, `{}`, `0`, `""`, `false`) o si el cuerpo es una lista. Antes: 500 con el texto de la excepción (`test_una_operacion_con_productos_que_no_son_objetos_da_400`). Un `resumen` que no es objeto también da 400 (`test_una_operacion_con_un_resumen_que_no_es_un_objeto_da_400`). Sin productos ni resumen se guarda vacía, con los totales en cero (`test_una_operacion_sin_productos_ni_resumen_se_guarda_vacia`).
   - **Confirmar un NCM** (`/api/ncm/guardar-uso`) pasa por `ncm_para_historial`, como guardar: «pedido 20240115 nro», «39269090X» y «1234» dan 400 y no guardan nada (`test_confirmar_algo_que_no_es_un_ncm_da_400_y_no_guarda_nada`). Antes, el primero quedaba en el catálogo como 20240115. Un medio par en el origen o el proveedor da 400 (`test_confirmar_un_ncm_con_medio_par_da_400_y_no_guarda_nada`) y el NUL se saca (`test_confirmar_un_ncm_saca_el_nul_del_origen_y_del_proveedor`).
3. **La base sostiene la identidad.**
   - Columna `clave` con el índice único `ux_cph_owner_client_clave`. Se escribe con `INSERT … ON CONFLICT DO NOTHING` y después `SELECT … FOR UPDATE`: el que llega segundo suma a la fila del primero.
   - **SQLite:** seis guardados a la vez dejan una fila con seis usos (`test_seis_guardados_a_la_vez_dejan_una_fila`). En el rojo eran `[1, 1, 1, 1, 1, 1]`.
   - **Postgres 16, dos procesos** (`scripts/testing/despacho1b_postgres.py`), salida sobre `bd14302` (`4034cdd` sólo cambia `guardar1.sh`):
     ```
     OK    | la base de 1f5480e no tiene clave
     OK    | la versión anterior aprendió una fila: [('b2434a54-…',)]
     OK    | la migración une el producto en la fila más reciente, suma 4 usos y pondera el peso (0,1×1 + 0,4×3)/4: [('3926.90.90', 'CAÑO INVENTADO VERDE', '04069ff7…', 4, 0.32500000000000007, 4, 2.0, 1), ('SIN-CLASIF', 'ALGO SIN NCM', None, 1, None, None, None, None)]
     OK    | crea el índice único: [('CREATE UNIQUE INDEX ux_cph_owner_client_clave ON public.client_product_history USING btree (owner_username, client_id, clave)',)]
     OK    | arrancar otra vez no cambia nada: […la misma fila…]
     OK    | dos procesos guardan y aprenden el mismo producto a la vez: una fila con 16 usos: ['200'] [(16,)]
     OK    | dos aprendizajes en orden contrario, vuelta 0: [200, 200] []
     OK    | dos aprendizajes en orden contrario, vuelta 1: [200, 200] []
     OK    | dos aprendizajes en orden contrario, vuelta 2: [200, 200] []
     OK    | cada válvula, una fila con 6 usos: [(40, 6, 6)]
     fallas: 0
     salida 0
     ```
     La base de partida es una de `1f5480e` con el mismo producto en NFC y en NFD.
   - **La migración** (`_migrate_product_history_clave`) une los duplicados en la fila más reciente. Suma los usos y pondera cada promedio por sus usos. Escribe las claves recién después de unir y vacía antes las que cambian; dos claves cruzadas no chocan con el índice.
   - **Idempotente:** `test_la_migracion_une_los_duplicados_y_es_idempotente`. Casos de borde: `test_la_migracion_une_la_fila_sin_clave_que_dejo_la_version_anterior` y `test_la_migracion_reescribe_claves_cruzadas`.
   - **Si falla, se nota:** el arranque se corta con el error. Ya no imprime y sigue (`test_la_migracion_que_falla_no_sigue_callada`).
4. **El tope de CPU cubre el hijo entero.**
   - Extraer las hojas y entender el texto comparten los 10 s: extraer se lleva una parte y entender, lo que queda.
   - El corte llega con `setitimer(ITIMER_PROF)`. Se repite cada 0,05 s por si un `finally` de pypdf se traga el primero.
   - **Medido en `7e96b32`** con el PDF de la forma del tuyo (200 hojas × 500 renglones, `tests/pdf_bombas.py`, `parseo_caro`), CPU propia del hijo:
     ```
     lector_cpu_s 10.134  lector_mb 48  pared 10.37 s
     avisos: «El texto del PDF es demasiado largo: leí hasta la hoja 33.», «El PDF da demasiado trabajo: no pude leer sus productos.»
     ```
     Vos mediste 19,6 s antes. En el rojo, el caso daba `assert 8.500733 < 3.5` con un tope de prueba de 3 s: entender el texto no tenía tope.
   - **Casos:**
     - `test_el_tope_de_cpu_cubre_entender_el_texto`;
     - `test_las_hojas_leidas_antes_del_corte_dan_sus_productos`;
     - `test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado`;
     - `test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar`.
5. **El PUT valida igual que guardar.**
   - Pasa por las mismas funciones que guardar.
   - **Lo que rechaza con 400** (`test_cambiar_un_producto_valida_igual_que_guardar`, 7 casos): descripción vacía, NUL, más de 200 caracteres después de normalizar, NCM arábigo y peso «1_000».
   - **El origen** pasa por `origen_para_catalogo` (despacho_lector.py:789), la misma regla de guardar un despacho: dos letras ASCII de un país de la tabla, miradas como se escribieron y recién después pasadas a mayúsculas. «XYZ», «123», «ZZ», «china», una lista, un número, «ÉS», «ＢＲ», «ıt», «ſe» y «ﬁ» dan 400 (`test_cambiar_el_origen_valida_igual_que_guardar`, y los mismos en `test_guardar_es_todo_o_nada`). «ıt» importa porque `"ıt".upper()` es «IT»: el control viejo miraba después de pasar a mayúsculas. « br » y «B\x00R» guardan «BR»; vacío o null dejan «XX» en la fila (`test_cambiar_el_origen_guarda_el_codigo_en_mayusculas`).
   - **Lo que guarda:** la forma de la regla (`test_cambiar_un_producto_guarda_la_forma_de_la_regla`), con su clave recalculada.
   - **Choques:** si queda igual a otra fila, 409 (`test_el_mismo_producto_por_dos_vias_queda_en_una_fila[cambio-*]`). Cambiarse a sí mismo no es un choque (`test_cambiar_un_producto_a_si_mismo_no_es_un_choque`).
   - **Tope de learn:** 500 ítems, el mismo que guardar. Con 500 da 200 y con 501, 400 (`test_aprender_tiene_tope_de_500_productos`).
6. **Un solo borde.**
   - `valor_para_promedio` acepta lo que es menor que 1e12 y es la única regla para peso, valor y cantidad en todas las vías.
   - Al guardar un despacho, un peso o valor de 1e12 o más marca el renglón con el motivo y da 422 todo o nada (`test_un_peso_por_unidad_justo_en_el_tope_marca_el_renglon`). En el rojo, 1e12 justo daba 200 sin aviso.
   - Learn y la operación aprenden el producto sin ese valor. Si la operación no guarda un producto, lo dice (`test_una_operacion_con_un_producto_que_no_se_guarda_lo_dice`).
7. **Mutantes**, cada uno con su caso y su sabotaje en `despacho1b.sh`:

   | Mutante | Sabotaje | Caso que se pone rojo |
   |---|---|---|
   | `valor_para_promedio` quitado en la fila nueva | «un producto nuevo guarda el peso sin tope» | `test_un_producto_nuevo_no_guarda_valores_fuera_del_tope` |
   | `\ud800` en NCM y origen del PUT | «el cambio no mira el medio par» | `test_cambiar_con_medio_par_da_400[ncm]`, `[origen]` |
   | `casefold` | «la clave distingue mayúsculas» | `test_cada_forma_del_mismo_producto_suma_a_la_misma_fila[minusculas]` |
   | colapso de espacios | «la descripción no junta los espacios» | `…[espacios]` |
   | espacios del NCM | «el NCM no acepta espacios», «el NCM sin recortar las puntas» | `…[espacios en el ncm]`, `…[puntas del ncm]` |
   | divisa con espacios | «la divisa no recorta los espacios» | `test_guardar_un_despacho_en_dolares_guarda_el_valor[ usd ]` (y no `[dol]`) |
   | divisa en minúscula | «la divisa distingue minúsculas» | `…[dol]` (y no `[USD]`) |
   | `salteadas = True` tras el corte | «un corte por CPU parece escaneado» | `test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado` |
   | migración que no une | «la migración no une», «… cuenta filas, no usos», «… deja la fila más vieja», «… promedia sin pesar los usos» | `test_la_migracion_une_los_duplicados_y_es_idempotente` |
   | migración que choca | «la migración escribe la clave antes de unir», «… no vacía las claves que cambian» | `…une_la_fila_sin_clave…`, `…reescribe_claves_cruzadas` |
   | migración callada | «la migración que falla se calla» | `test_la_migracion_que_falla_no_sigue_callada` |

   La divisa: el supuesto, la prueba y el código dicen lo mismo. Se compara sin espacios en las puntas y sin mayúsculas (main.py:8412). `USD`, `DOL`, « usd » y `dol` guardan el valor; `EUR` y sin divisa, no.
8. **Cada afirmación lleva su medida.** La CPU, la concurrencia en Postgres y el rojo están copiados de su salida; los casos están nombrados.

## Rojo antes del arreglo

Corrido en un worktree limpio en `c66f7e7`: los casos nuevos sobre el producto de `1f5480e`, guardado en `rojo_repetido.txt`.

```
62 failed, 160 passed, 5 warnings in 96.93s
```

Las 62 fallas son de casos nuevos, y cada una es una aserción sobre el defecto:
- 26× `assert 200 == 400`;
- 6× `assert ([] == [('39269090', 2)]`;
- 4× `assert 500 == 400`;
- 4× `assert 200 == 409`;
- `assert [1, 1, 1, 1, 1, 1] == [6]` (seis guardados);
- `assert [(2, 250.5)] == [(1, 1.0), (1, 500.0)]` (los 275 caracteres);
- `assert 8.500733 < 3.5` (el tope de CPU sobre el texto);
- `ImportError: cannot import name '_migrate_product_history_clave'` (la migración no existía);
- `AttributeError: 'str' object has no attribute 'get'` y sus variantes (ítems de learn que no son objeto).

Una corrida anterior (`rojo_v4`, 92 fallas) no la cito: no salió de un árbol limpio y tenía 30 fallas de tests viejos.

**Rojos de las vueltas de revisión**, cada uno con los casos nuevos sobre el producto de antes de su arreglo:

| Rojo | Sobre | Salida | Ejemplos |
|---|---|---|---|
| `c55bd32` (adversario) | `7e96b32` | `21 failed, 1 passed, 240 deselected, 3 warnings in 3.10s` | `assert 500 == 400` en la operación, con «'str' object has no attribute 'get'»; confirmar «pedido 20240115 nro» daba 200 |
| `b11809f` (code-review 2) | `0c3a059` | `12 failed, 28 passed, 235 deselected, 3 warnings in 9.11s` | el PUT guardaba «ÉS» y «ＢＲ»; `{"items": {}}` daba 200; un resumen lista daba 500 |
| `f86005f` (code-review 3) | `4081221` | `4 failed, 27 passed, 248 deselected, 3 warnings in 8.84s` | «ſe», «ıt» y «china» en el PUT, y `test_guardar_es_todo_o_nada[i sin punto]` |

Verdes después de cada arreglo, sobre `tests/test_despacho1b.py` y los archivos que toca: `340 passed, 3 warnings in 73.63s` (`e035fc9`), `296 passed, 3 warnings in 72.42s` (`fca1878`) y `300 passed, 3 warnings in 72.27s` (`f5b8a93`).

## Autorrevisión

| Quién | Modelo y esfuerzo | Sobre | Hallazgos | Qué pasó |
|---|---|---|---|---|
| Yo, el diff entero | — | `daefd4b` | el corte por CPU tiraba lo leído; el largo se medía antes de NFC; la operación callaba lo que no guardaba | rojo `697ffb6`, fix `669bac0`, sabotajes `daefd4b` |
| Adversario | Sonnet alto | `ba9e42a` | ninguno: lo cortó un reinicio del contenedor antes de escribir | relanzado abajo |
| `/code-review high` | — | `daefd4b` | 10 (abajo) | 1 y 2 arreglados con su rojo; el resto, riesgos |
| `/security-review` | — | `9dca44f` | ninguna vulnerabilidad | — |
| Adversario | Sonnet alto | `7e96b32` | 5 (abajo) | 1, 2, 3 y 5 arreglados con su rojo (`c55bd32` → `e035fc9`); 4, a riesgos |
| `/code-review high` (2) | — | `7e96b32..0c3a059` | 10 | 2, 4, 5, 8 y 9 arreglados (`b11809f` → `fca1878`); 10 en este commit; el resto, riesgos |
| `/code-review high` (3) | — | `0c3a059..4081221` | 10 | 4, 7, 8 y 9 arreglados (`f86005f` → `f5b8a93`, `17386a1`, `e9173de`); 10 en este commit; el resto, riesgos |
| `/code-review high` (4) | — | `4081221..17386a1` | 8 | 3, 5 y 7 arreglados (`e9173de`, `bd14302`); 8 en este commit; el resto, riesgos |
| `/security-review` (2) | Opus, esfuerzo por defecto (subagente general) | `9db0002..bd14302`, `proyecto_maria/` | ninguna vulnerabilidad sobre el umbral | revisó SQL parametrizado en la migración, el upsert, el dueño en cada endpoint, el 409 sin fuga entre dueños, XSS y el proceso hijo sin shell |

**Hallazgos del code-review:**
1. La migración escribía la clave antes de unir y chocaba con el índice. **Arreglado** (`9dca44f`).
2. Learn y la operación convertían con `float()` y aprendían «1_000» y «٣». Rojo: `assert (1000.0, 3.0, 10.0) == (0.0, None, None)`. **Arreglado** (`ae2ab9a`): pasan el número crudo y `valor_para_promedio` lo rechaza.
3. a 10. Van a riesgos.

**Hallazgos del adversario sobre `7e96b32`** (Sonnet alto, en un worktree propio): aguantaron la identidad en las 16 combinaciones de vías, la migración, Postgres, el tope de CPU (10,15 s como máximo) y los bordes en 1e12.
1. La operación con un ítem que no es objeto daba 500 con el texto de la excepción. **Arreglado.**
2. Confirmar NCM con medio par o NUL en `origen` o `vendor_name` daba 200 y no guardaba nada. **Arreglado.**
3. El PUT guardaba el origen con NUL (500 en Postgres) y aceptaba orígenes que guardar rechaza («Non», «['a»). **Arreglado.**
4. Un cuerpo que es una lista con medio par da 500 en las cinco vías. **Riesgo**, abajo.
5. Confirmar NCM aceptaba cualquier texto con 8 dígitos. **Arreglado** con `ncm_para_historial`.

**Code-review 2, 3 y 4, lo arreglado:**
- El PUT guardaba «ＢＲ» o «ÉS» tal cual: `pais_reconocido` normaliza con NFKD (2-2). Ahora sólo ASCII.
- El control ASCII miraba después de pasar a mayúsculas: «ıt» entraba como IT (3-4). Ahora mira lo escrito; «ﬁ» (que crece a «FI») también tiene caso (4-3).
- Un `resumen` que no es objeto daba 500 (2-4); `{"items": {}}`, `0`, `""` y `false` pasaban (2-5).
- El mensaje del origen repetía la representación de Python de una lista (2-8): ahora dice «El origen tiene que ser el código de dos letras.».
- El aviso del NCM inválido estaba copiado en dos lugares (2-9): es una constante.
- Ningún sabotaje probaba los totales de la operación vacía (4-5), los ids de los sabotajes eran posicionales (3-8) y el origen que no es texto no se probaba en guardar (3-7).
- `upper` doble (4-7).

## Supuestos reversibles

- **Confirmar un NCM inválido da 400 y no aprende nada.** Antes, un NCM sin 8 dígitos igual sumaba en el historial del dueño; sólo se salteaban las memorias del cliente y del proveedor (code-review 2, hallazgo 7). Lo leí como el punto 2, «por ninguna vía». Si querés que el historial del dueño lo siga contando, es volver a separar ese paso.
- Una operación sin productos ni resumen se guarda vacía, con totales en cero.

- «1_000» y «٣» como peso en learn o en la operación: el producto se aprende sin ese valor, igual que con un infinito. Al guardar un despacho, el renglón vuelve marcado.
- El type hint de `upsert` sigue diciendo `Optional[float]`, pero ahora recibe el valor crudo (texto o número) y lo valida `valor_para_promedio`. No lo cambié para no ensanchar el diff.

## Riesgos, sin arreglo en esta pieza

- **Tuyos, quedan así:**
  - las filas viejas pesan por `veces_usado`;
  - learn de 100 ítems contra 5000 filas tarda 19 s;
  - la consulta de la migración no filtra por esquema;
  - el candado de lectura es por proceso.
- **`update_product_history` sobra.** Nada del producto lo llama: sólo `tests/test_despacho1b.py:1262` y `tests/old/`. Si alguien lo llamara hoy, escribiría filas sin `clave` ni dueño, fuera de la regla y del índice (un NULL no choca). Propuesta para otra pieza: borrarlo junto con sus pruebas.
- **Del code-review:**
  - 3: el semáforo de 2 lugares es global; va a RENDIMIENTO-1c.
  - 4: `process_pdf` parsea dentro del proceso; va a RENDIMIENTO-1c.
  - 5: un DELETE a la vez que un guardado. Va en un savepoint, todo o nada: no queda nada a medias. Bajo.
  - 6: un SIGPROF justo en el `finally` del tope. Rarísimo, y el temporizador se apaga igual.
  - 7: la migración recorre la tabla en cada arranque. Es lineal, y una tabla sin duplicados no escribe nada.
  - 8: la validación está repetida entre guardar y el PUT. Llaman a las mismas funciones, pero desde dos lugares.
  - 9: un NCM con otros dígitos rechaza el pedido entero. Es lo que pide el punto 2.
  - 10: leer un despacho levanta dos procesos.
- **Del adversario:**
  - Hallazgo 4: un cuerpo que es una lista con un medio par da 500 en las cinco vías. Lo agarra el manejador global del 422 al armar el mensaje, antes de llegar al endpoint. Baja: nada se guarda.
  - La operación no tiene tope de ítems: 5000 tardan 24 s. Learn y guardar sí lo tienen (500).
  - Learn y la operación con un valor de 1e12 aprenden el producto sin ese valor y no lo dicen por renglón. Es el supuesto aceptado.
  - Confirmar con un `ncm` o una `descripcion` que no son texto da 500. Ya pasaba en `1f5480e` (también code-review 2, hallazgo 6).
  - Un PUT que cambia la clave entre el INSERT y el FOR UPDATE de otra vía dejaría un `NoResultFound`. No lo reproduje.
  - Un posible deadlock entre borrar un cliente y aprender a la vez. No lo probé.
- **De los code-review 2, 3 y 4:**
  - **La pantalla del catálogo** (clientes.js:1427) acepta tres letras y precarga «XX». El PUT ahora da 400 a «CHN» o «XX», como pide el punto 5, y la pantalla muestra «No se pudo guardar» sin el motivo y deja escrito lo rechazado (2-1). Media para el uso; es del frontend. Propuesta para otra pieza: `maxlength="2"` y mostrar el detalle del 400.
  - **El origen en aprender, la operación y confirmar NCM** se guarda sin validar, cortado a tres letras: «China» queda «CHI» y «br» queda en minúsculas (2-3, 3-1, 4-1). El arreglo natural es llamar a `origen_para_catalogo` en `upsert_client_product_history`, pero cambia qué aprenden tres vías que el punto 5 no nombra. Lo propongo como pieza aparte.
  - `int()` y `float()` del resumen y de los campos de un ítem de la operación dan 500 con un valor que no es número; con una operación vacía, también un `null` en el resumen (3-2, 3-3, 4-4). `save_client_operation` devuelve `str(e)[:200]` en ese 500, que el security-review anotó fuera de alcance.
  - `pais_reconocido` es difuso; un conjunto ISO2 sería más claro (3-5).
  - El 400 de un cuerpo que no es objeto habla de «productos» (3-6).
  - `_origen_desde_factura` (pdf_extractor.py:2081) pasa a mayúsculas sin mirar ASCII. Es de las facturas, fuera de la pieza (4-2).
  - El 400 del origen repite lo escrito sin tope de largo ni filtro de caracteres de control (4-6). Baja: es la respuesta al mismo que lo mandó.

## Puertas

Sobre `bd14302`, salvo `guardar1.sh` (sobre `4034cdd`, que sólo cambia ese script). `tests/test_despacho1b.py`, `despacho1b.sh` y la suite, sobre `03296d4`. De `bd14302` a `{SHA}` sólo cambian `guardar1.sh`, `despacho1b.sh`, un valor de un caso del PUT, el CHANGELOG y este informe: ningún archivo de producto.

| Puerta | Salida |
|---|---|
| `tests/test_despacho1b.py` | `281 passed, 3 warnings in 47.30s`, salida 0 (sobre `03296d4`) |
| `despacho1b.sh` (copia congelada) | {SAB} |
| `disco1.sh` (copia congelada, sobre `bd14302`; toqué `tests/test_disco1.py`) | 39 ROJO, «sabotajes sin rojo: 0», salida 0. **No corrí** los 7 de Postgres («falta PG_URL»): son del bloqueo por dueño de DISCO-1, que esta vuelta no toca |
| `guardar1.sh` | 12 ROJO, «sabotajes con falla: 0», salida 0 (sobre `4034cdd`) |
| suite completa, base limpia | `4284 passed, 336 skipped, 2 xfailed, 96 warnings in 677.94s (0:11:17)`, salida 0 |
| `compileall -q proyecto_maria` | salida 0, sin texto |
| Postgres 16, `despacho1b_postgres.py` | «fallas: 0», salida 0 (sobre `bd14302`, arriba) |
| No corrido | smoke y ataque de aislamiento: la pieza no toca sesión ni permisos |

## Incidentes

- Un reinicio del contenedor mató al primer adversario antes de que escribiera hallazgos.
- Un script de sabotajes editado mientras corría. Desde entonces corro una copia congelada.
- **Postgres sobre `bd14302`, dos intentos fallidos antes del bueno**, los dos míos y de entorno:
  - el primero, porque corrí la copia del arnés desde mi carpeta temporal, donde un `bisect.py` mío tapaba al de la biblioteca;
  - el segundo, porque esa copia estaba fuera del repositorio y no encontraba el paquete.
  El tercero corrió desde el árbol de `bd14302`: «fallas: 0».
- **`guardar1.sh` sobre `bd14302`** dio «sabotajes con falla: 2»: dos patrones ROTO, que no encontraban el código. El de aprender estaba roto desde `669bac0`, dentro de esta vuelta, y no lo vi. El de editar lo rompí en `e035fc9`. Los dos se arreglaron en `4034cdd`, y sobre ese SHA da «sabotajes con falla: 0».
- **Un reinicio del contenedor cortó `despacho1b.sh` en el sabotaje 45 de 131**, con los 45 en ROJO y ninguna falla. Lo retomé con otra copia congelada, idéntica salvo un contador que saltea los primeros 45 sin correrlos. La copia vuelve a comprobar el verde de base. Las dos salidas van juntas en la tabla de puertas.

- **`despacho1b.sh` sobre `bd14302` dio cuatro sabotajes sin rojo, y el defecto es mío:** el script no siguió el código de `fca1878`, `f5b8a93` y `eb4e615`.
  - «el lector guarda el NCM con puntos» (ROJO?): el código ya no guardaba con puntos, el sabotaje caía por otro motivo (422 «Falta la posición SIM…» en 5 casos `dos_vias[*-guardar]`). Ahora se llama «el lector no acepta el NCM de 10 dígitos» y espera esos casos.
  - «el promedio acepta infinitos» (ROJO?): el caso esperado lo frena antes `_DECIMAL`. Ahora espera los tres que sí lo ven (`un_infinito_guardado_antes…`, `…no_es_un_peso_da_400[1e400]`, `un_producto_nuevo_no_guarda_valores_fuera_del_tope`).
  - «el origen con mitad de par se repite» (ROTO): buscaba el patrón viejo.
  - «el NCM sin recortar las puntas» (VERDE): ningún caso mandaba espacios al PUT. El caso `test_cambiar_un_producto_guarda_la_forma_de_la_regla` ahora manda `" 3926.90.90.000A "`. Con el sabotaje cae con `400` «El NCM no es válido: tiene que tener sus 8 dígitos.»; sin él, pasa.
  - `_DECIMAL` no tenía sabotaje: sumé «el promedio acepta números con otros dígitos», que hace caer `aprender_ignora_los_numeros_con_otros_digitos[learn|operacion]` y `cambiar_un_producto_valida_igual_que_guardar[guion bajo|peso arabigo]`.
  - Dos casos quedan sin un sabotaje propio que los tire solos: `test_el_mismo_ncm_con_o_sin_puntos_es_el_mismo_producto` (lo sostiene también la normalización de `identidad_del_producto`) y `test_aprender_un_peso_infinito_no_lo_guarda_y_el_catalogo_anda` (dos capas: `_DECIMAL` e `isfinite`). Sacar una sola capa no los distingue.
- **`despacho1b.sh` sobre `bb913d0` dio un VERDE, y el defecto es de la prueba:** «extraer se lleva el tope entero: la prueba no lo vio». El sabotaje deja a entender el texto con 1 ms de tope, pero el temporizador de CPU corta recién al tick siguiente (4 ms o más) y el texto de prueba se entiende en unos 3,1 ms (medido). `test_las_hojas_leidas_antes_del_corte_dan_sus_productos` pasaba igual. En `03296d4` la prueba hace que entender cueste 50 ms de CPU. Repetida 5 veces: 5 verdes sin sabotaje y 5 rojos con él. El producto no cambia.
- **Las dos corridas sobre `bb913d0` se cortaron en el sabotaje 96**, con los 95 anteriores en ROJO. A la primera la cortó el tope de 2 h de las tareas de fondo; desde ahí corro desacoplado. A la segunda, un reinicio del contenedor. El 96 solo dio ROJO, «4 failed, 277 passed, 3 warnings in 46.30s»: los cortes vinieron del entorno. Retomé desde el 96 con una copia congelada que saltea los anteriores sin correrlos. Ahí salió el VERDE de arriba. La puerta es la corrida completa sobre `03296d4`.
- **La corrida vieja sobre `bd14302` se cortó por el tope de tiempo de las tareas de fondo**, en el sabotaje 74 de los 86 que le quedaban, sin otra falla que esas cuatro. No la repetí: la puerta es la corrida completa del script corregido sobre `bb913d0`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP cada 2 h (minuto 35, horario de Argentina). Entregada sin veredicto: DESPACHO-1b vuelta 4 en {SHA}. Apenas entregada: RENDIMIENTO-1c (ccf5d8c, 033cb11, 843cc08, 7dd008f) con sabotajes rendimiento1c.sh, rendimiento1.sh y despacho1b.sh, suite, adversario Opus alto e informe con la D49 (el vendedor de la factura abre el PDF en la app). Después SESION-1 → ABUSO-1 → SUFIJOS-2 → EMAIL-1 (D45) → CONEXIONES-1 (D46) → OBSERVABILIDAD-1 → ORG-1+D40. Nunca main; nada se publica sin el «dale» de Emi para el SHA; sin secretos ni datos reales; Devs hasta esfuerzo alto, sin Fable; sin advisor.
