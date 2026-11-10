# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-3 entregada en f4ade80 (base 07504e0)

| SHA | Qué |
|---|---|
| 6cbd192 | fix: vendor_id y clave con el hash de las letras no latinas; el proveedor de más de 60 caracteres con el hash del nombre entero; memoria y NCM recordado con la misma clave; migración que recalcula sin borrar; origen a text con candado; origen válido = `pais_reconocido`, guardado tal cual; nada recorta; agrupar, métricas y TXT tratan 313, TAIWAN y TW igual; tarifar ya no supone dos letras; el 400 nombra el producto |
| 910e1d7 | fix: NFC en el origen; un código son 1 a 4 cifras; el resumen no latino deja afuera Latin-1 y Latin extendido (ª, º, µ) |
| e53aa5e | test: pruebas, arnés PG y sabotajes |
| 54a450c | test: paso 5 del arnés (un worker arranca aunque otro tenga el candado) — rojo |
| 08cc02c | fix: el candado ya no aborta el arranque |
| 43e825e | fix: un origen de miles de cifras no rompe los avisos (+ CHANGELOG) |
| d401b72 | test: el caso de miles de cifras |
| 208d814 | test: sabotaje 25 (`get_pais_codigo` con cualquier tira de cifras) |
| f4ade80 | test: los datos que distinguen los sabotajes 7, 13 y 15 («螺丝 3mm» en la migración, «ＣＨＩＮＡ», «ESPAN\u0303A» guardado como «ESPAÑA»); id del 24 corregido |
| (siguiente) | docs: este informe |

**Resultado:** D76, D77, D78/D86, D80 y D84 hechos con D155 (a), D156 (a) y D157 (a). Golden sin cambios. Puertas abajo. Hay una D nueva (D159) y queda abierta D158.

## Decisiones

- **D158 (abierta, sigue de antes): «123» es LIBIA.** D155 pedía rechazar «123», pero `pais_reconocido` lo reconoce como código de Libia.
  - (a) aceptarlo como código válido. **Recomiendo (a)**: es lo que dice la tabla de países y rechazarlo obliga a un caso especial contra el criterio único de D80. Ya está implementado así como supuesto reversible; la prueba de rechazo usa «99999».
  - (b) rechazarlo igual, con una excepción explícita.
- **D159: lo que el criterio nuevo deja afuera en otras puertas de entrada.** Con D155 el origen válido es nombre o código de país; quedan lugares que todavía piensan en dos o tres letras:
  - `pdf_extractor.py:575` pasa CHN, TWN, DEU, KOR y «Hong Kong» a XX;
  - `maxlength` 3 en `catalogo.js:270` y `clientes.js:1427`, y 2 en `clientes.js:1692`;
  - `clients.default_origin` VARCHAR(3) y los `[:3]` de main.py:7479/7557/9721.
  - (a) pieza aparte que los alinee con `pais_reconocido`. **Recomiendo (a)**: son otras pantallas y otra columna; meterlos acá agranda una pieza de revisión fuerte.
  - (b) dejarlos como están.
- **Entradas dobles de la tabla de países** (sin cambio; las nombro para que no se pierdan): NL (PAISES BAJOS→423, HOLANDA→434, NL→434), CHIPRE 311/435, TURQUIA 336/436, ALEMANIA 402/438. La prueba con ast acepta sólo NL repetida.

## Supuestos reversibles

- «123» se acepta (D158).
- `get_pais_codigo` toma como código sólo 1 a 4 cifras (`re.fullmatch(r"[0-9]{1,4}")`). Antes hacía `int()` de cualquier tira: con 5000 cifras, `/avisos` daba 500 (`ValueError: Exceeds the limit (4300 digits) for integer string conversion`). Era preexistente; lo arreglé porque D80 pasa por esa función. Efecto: «99999» en el TXT pasa al default (310), como ya pasaba con «XX».
- En la operación manual (main.py:3777) quedan el `.upper()` y el «XX» por defecto: es lo que ya hacía, y sacarlos cambia lo que guarda una operación manual, fuera de la tarea. En main.py:8184 no hay ninguno de los dos.

## Lo que cambió para quien usa

- «china», «China» y «CHINA» ahora valen como origen (antes sólo «CN»), y se guardan tal cual. «0310» vale y da 310; «0000310» no (más de 4 cifras).
- Casos de `test_despacho1b` que cambiaron:
  - `test_guardar_es_todo_o_nada`: se sacó `{"origen":"CHINA"}` (ahora es válido); «origen numero» dice «El origen tiene que ser el nombre o el código del país.».
  - `test_cambiar_el_origen_valida_igual_que_guardar`: «usá el código de dos letras.» → «usá el nombre o el código del país.»; «123» → «99999» (id «numeros», D158); se sacó «china» (id «nombre»); se sumaron «acento aparte» (ÉS) y «cifras de mas» ("1"*5000). Siguen rechazados ＢＲ, ÉS, XYZ, ZZ, ıt, ﬁ, ß, la lista y 12.
- D157: el mismo nombre CJK con y sin «Co., Ltd» queda como dos proveedores; las filas que ya estaban unidas por «co_ltd» no se separan.
- D156: «TAI» se rechaza al guardar, pero las filas viejas con «TAI» (o «CHI») en el TXT salen con 310 (China), porque `get_pais_codigo` cae al default. Va como riesgo.

## Archivos de producto

proyecto_maria/core/catalog_service.py, core/despacho_lector.py, core/maria_generator.py, core/tarifar_connector.py, database/models.py, main.py, pdf_extractor.py, services/client_memory.py, static/v2/screens/finalize.js. Más CHANGELOG.md.

## Comandos copiables

```bash
git fetch origin claude/dev-maria && git checkout f4ade80
source <venv>; export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_catalogo3.py tests/test_despacho1b.py tests/test_despacho1c.py   # todo passed
timeout 500 python -m pytest -q --no-cov -p no:warnings tests/test_generar_maria_txt.py tests/test_excel1_txt.py tests/test_punta_a_punta1.py tests/test_maria_subitems.py tests/test_maria1b_controles.py   # 115 passed, 2 xfailed
PY=$(which python) scripts/testing/sabotajes/catalogo3.sh   # «fallas: 0», 25 sabotajes
unset DATABASE_URL; python scripts/testing/catalogo3_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/postgres   # «todo OK»
python scripts/testing/catalogo3_postgres.py <URL> 07504e0 <worktree en 07504e0>   # la base: 5 fallas
```

## Rojos copiados

- C8, sobre 08cc02c, `test_un_origen_de_miles_de_cifras_no_rompe_los_avisos_ni_el_txt`:
  ```
  E   ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit
  1 failed, 33 deselected
  ```
- Paso 5 del arnés, sobre 54a450c: «FALLA | un worker arranca mientras otro tiene tomada la migración de claves»; en el log de PG: «canceling statement due to lock timeout / STATEMENT: SELECT pg_advisory_xact_lock(7302551)».
- Arnés sobre la base 07504e0 («5 fallas»):
  - «FALLA | dos workers esperan juntos la migración y arrancan los dos»
  - «FALLA | operation_items.origen pasa a text y la fila vieja queda igual»
  - «FALLA | la migración da el proveedor y la clave de hoy sin perder filas»
  - «FALLA | la operación manual y la del historial guardan «TAIWAN» entero»
  - «FALLA | «电线 2mm» y «钢管 2mm» del proveedor CJK quedan en dos filas»
- Los datos de f4ade80, con el arreglo revertido por el script de sabotajes (sabotajes 7, 13 y 15):
  - la migración no le da la clave de hoy al producto: dice «FAILED tests/test_catalogo3.py::test_la_migracion_separa_los_proveedores_y_los_productos_mezclados»
  - el ancho completo vuelve a pasar: dice «FAILED tests/test_despacho1b.py::test_cambiar_el_origen_valida_igual_que_guardar[nombre ancho completo]»
  - «É» con el acento aparte vuelve a pasar: dice «FAILED tests/test_despacho1b.py::test_cambiar_el_origen_guarda_el_codigo_en_mayusculas[acento aparte]» (el caso es «ESPAN» con la tilde aparte, que guarda «ESPAÑA»: el título del sabotaje dice «É» y debería decir «Ñ»; lo corrijo en el próximo commit de pruebas)

## Puertas

| Puerta | SHA | Salida |
|---|---|---|
| suite completa | f4ade80 | «5490 passed, 335 skipped, 3 xfailed in 1165.73s (0:19:25)», rc=0 (los 2 casos más que en 208d814 son los parámetros que suma f4ade80) |
| golden | f4ade80 | «115 passed, 2 xfailed in 18.42s» |
| compileall | f4ade80 | rc=0 |
| sabotajes catalogo3.sh | f4ade80 | 25 ROJO, «fallas: 0» |
| arnés PG 16 | f4ade80 | 7 pasos OK, «todo OK» |
| smoke_friccion | f4ade80 | «OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido», rc=0 |
| ataque_aislamiento | f4ade80 | «Bloqueado: 47 · Fugas: 0 · Sin probar: 0», «PUERTA G3 PASADA» |
| revisión de seguridad (acotada: adversario-sonnet-alto sobre `git diff 07504e0..f4ade80 -- proyecto_maria/`, sólo lectura, no el /security-review de la rama entera) | 07504e0..f4ade80 | sin hallazgos de confianza ≥8 |

Producto igual desde 43e825e: 208d814 y f4ade80 sólo tocan pruebas y el script de sabotajes. La suite, el golden y compileall corrieron sobre f4ade80.

## chequeo-6

```
chequeo-6 07504e0..f4ade80: avisos para mirar, no un veredicto
producto +166/−66
  AVISO producto suma 100 líneas netas: el informe dice por qué (§6: más de 20)
arnés +715/−26
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 636 → 702
  proyecto_maria/core/despacho_lector.py: 902 → 900
  proyecto_maria/core/maria_generator.py: 2347 → 2368
  proyecto_maria/core/tarifar_connector.py: 525 → 526
  proyecto_maria/database/models.py: 614 → 614
  proyecto_maria/main.py: 12111 → 12124
  proyecto_maria/pdf_extractor.py: 2893 → 2893
  proyecto_maria/services/client_memory.py: 305 → 305
  proyecto_maria/static/v2/screens/finalize.js: 1444 → 1445
avisos: 1
```

Por qué suma 100 líneas netas: el criterio único de origen (`origen_para_catalogo`, `origen_para_guardar`, `clave_de_origen`), el sufijo hash para CJK y para proveedores de más de 60 caracteres, la migración de vendor_id y product_key y el ALTER con candado. Lo que se pudo restar se restó: los `[:3]`, la validación de dos letras de despacho_lector y la normalización propia de tarifar.

## Hallazgos

| Quién | # | Sev. | Hallazgo | Qué hice |
|---|---|---|---|---|
| A, adversario-sonnet-alto, «origen y pantalla» | — | — | export CSV, `esArgentino`, validations.py:62, `_detect_default_origin`, slug del JS, filas TAI, emoji con Co., Ltd, filas co_ltd, latinos de más de 60, fuzzy CJK, `default_origin` VARCHAR(3), ancho completo, `.toUpperCase()`, «0310»/«00310», Ω, maxlength | Riesgos o D159 (abajo) |
| B, adversario-sonnet-alto, «claves y migración» | 1 | Media | ª, º y µ cambiaban el id latino | Arreglado en 910e1d7. Ω todavía lo cambia: riesgo |
| B | 2 | Media | Un worker abortaba por lock_timeout | Arreglado en 08cc02c, con el rojo del paso 5 |
| B | 3 | Media | `lookup_client_memory` (client_memory.py:286) unas 5 veces más lento | Riesgo |
| B | 4 | Media/baja | Un origen no reconocido rechaza todo el pedido en guardar_uso_ncm | Riesgo, por D155 |
| B | 5 | Baja | «Nº 5»/«No 5» y «10µF»/«10uF» ya no se parecen | Riesgo |
| B | 6 | Baja | Con un choque en la migración queda una fila huérfana | Riesgo (el log lo cuenta) |
| B | 7 | Baja | La clave puede pasar 2000 caracteres y el PUT/DELETE da 400 | Riesgo |
| B | 8 | Baja | La clave pierde la posición de las letras no latinas, marcas combinantes y emoji | Riesgo |
| B | 9 | — | Origen sin tope de largo en main.py:3780/8184 | Riesgo |
| C, /code-review high | 5 | Baja | Preexistente: «Køle»/«Kæle» dan 'k le 2mm'; «m²»/«m³» dan 'panel 3 m'; «Straße»/«Strasse» distintas | Riesgo |
| C | 6 | — | Comentarios del candado engañosos | Arreglado en 08cc02c |
| C | 8 | Media | Origen de miles de cifras: 500 en /avisos | Arreglado en 43e825e, rojo arriba |
| C | resto | — | guardar_uso_ncm da 400 con CHN, TWN, «Hong Kong» o «-»; save_products rechaza el lote entero; update_product no deja editar filas CHI/TAI; pdf_extractor.py:575; maxlength; client_memory.py:286; migración O(filas) en cada arranque | Riesgos o D159 |

## Riesgos y lo no corrido

- **«TAI» y «CHI» en el TXT salen como 310 (China).** Filas viejas con «TAI» (Taiwán) se generan con el código de China. No es nuevo (`get_pais_codigo` ya caía al default), pero ahora no se pueden corregir editando: «TAI» no es un país y update_product lo rechaza.
- Un origen no reconocido (CHN, TWN, «Hong Kong», «-») rechaza el pedido entero en guardar_uso_ncm y el lote entero en save_products.
- La migración de claves recorre en cada arranque las filas con letras no latinas, vendor vacío o de 60+ caracteres: con decenas de miles puede demorar el arranque; con el candado, el segundo worker la saltea después de 5 s.
- Un choque en la migración deja la fila vieja sin mover; el log dice cuántas.
- `lookup_client_memory` más lento (unas 5 veces, medido por B).
- Ω y otras letras griegas cambian el id de un proveedor latino.
- Similitud: «Nº 5»/«No 5», «10µF»/«10uF»; preexistente: «Køle»/«Kæle», «m²»/«m³».
- Clave de más de 2000 caracteres: PUT/DELETE dan 400.
- Origen sin tope de largo ni validación en la operación manual (main.py:3780) y en la del historial (main.py:8184): se guarda lo que llegue, igual que la descripción. Antes se recortaba a 3. En el TXT un origen no reconocido sale con el default 310 (caso de miles de cifras, C8).
- No corrido: el /security-review de la rama entera (corrió sólo la revisión acotada al producto de esta pieza) y la CI de GitHub (no la puedo disparar; además deselecciona los tests de presupuestos compartidos).

## Sigue

PRESUPUESTO-CLIENTE-1 (D141 a).

## /compact conservar

«Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. CATALOGO-3 entregada en f4ade80, esperando veredicto. Sigue PRESUPUESTO-CLIENTE-1. D158 y D159 abiertas; próxima D libre: D160. D151 sigue. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos.»
