# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-3 (vuelta) entregada en ec0092a (base 1345ca7)

Para ver sólo la vuelta: `git diff 1345ca7..ec0092a`. Debajo de 1345ca7 quedan
de176b1, f9d4c76, db0f25a y 1345ca7, que son de PRESUPUESTO-CLIENTE-1 (sin
entregar, no son de esta pieza), y 2fbfea9 (el informe anterior).

| SHA | Qué |
|---|---|
| 7624e4e | fix: el catálogo no pierde el NCM por un origen que no reconoce |
| a4181a6 · 506991a · 97e3f4f | test: origen no reconocido, NFKC, Bolt™, sabotajes |
| 210a53f · bc046ae | refactor: docstrings en dos líneas |
| 2e411b6 | fix: el lote no se pierde por un origen; el país se lee con un solo criterio |
| df84ad0 · 6638f5a · 3747e47 · 2c36f62 | test: lote, una lectura del país, sabotajes apuntados |
| 466f8ab | fix: la pantalla recorta los mismos espacios que el servidor |
| e1ae1fd · a54e182 | test: pantalla y servidor leen igual el país con espacios raros |
| 4e85706 | fix: ㎜ o ℃ dan la misma clave que mm o °C |
| 8ccd004 · a92bddd | test: ㎜, ℃, ㎖ y su sabotaje |
| 8924ebe | perf: la clave de producto se calcula una vez por descripción |
| ce155dc · 389a366 | test: una clave por fila por pedido y su sabotaje |
| bb855e0 | fix: el aviso no dice «sin origen» si el producto conserva el suyo |
| 9dcee73 | test: ese aviso |
| ec0092a | test: el bench del lookup (`scripts/testing/bench_catalogo3_lookup.py`) |
| (siguiente) | docs: este informe |

**Resultado.** Las tres causas de la devolución quedan resueltas; D158 (a) y
D159 (a) aplicadas; el golden no cambia (115 passed, 2 xfailed).

- **Causa 1:** un origen no reconocido no hace perder NCM, historial, memoria
  ni catálogo, y la persona se entera. Un solo criterio (`origen_para_guardar`,
  catalog_service.py:84) en el extractor, guardar-uso, el PUT, el lote y
  catalogo.js. Guardar-uso responde `aviso` «No se guardó el origen. …» y la
  pantalla lo muestra; al finalizar, el producto se aprende sin ese origen,
  conserva el que tenía y la pantalla lo nombra.
- **Causa 2:** NFKC con µ/μ, ｶﾞｽ/ガス, ², ﬁ, ㎜, ℃, ㎖ dan `exact`. Screw M8
  contra «Screw M8 螺丝» queda **fuzzy en los dos sentidos** (lo decido yo,
  como pediste). «电线 2mm» y «钢管 2mm» siguen sin encontrarse (`none`).
- **Causa 3:** el lookup tarda menos que la base en las 6 combinaciones
  (tabla abajo), con 65 y con 430 caracteres. `test_acelerar_no_cambia_ninguna_clave`
  prueba que las claves no cambian.
- **Corrijo el informe anterior:** `/generate_maria` con «TAI» frena con
  «Origen no reconocido»; no lo saca como 310.

## Decisiones

- **D160. Formas de país que no están en la tabla** (U.S.A., Viet Nam, PRC,
  Turkey, TAI): hoy quedan sin origen y con aviso. (a) dejarlas así;
  (b) agregarlas como alias. Recomiendo (a): cada alias nuevo es un código que
  sale en el TXT, y el aviso ya evita la pérdida silenciosa.
- **D161. Excepción a NFKC para «ºª№™℠»** (catalog_service.py:136-141): NFKC
  literal convierte º en «o», № en «No» y ™ en «TM», que cambia claves ya
  guardadas («Nº 5» dejaría de encontrar lo de antes). (a) mantener la
  excepción; (b) NFKC literal. Recomiendo (a).
- **D162. 22 alias que no son países** (AFRICA, OCEANIA, provincias
  argentinas y otros) quedaron fuera de la lectura del país: con ellos, un
  origen «AFRICA» salía con un código que no es de un país. (a) dejarlos
  fuera, que da «origen no reconocido» y aviso; (b) restaurarlos. Recomiendo (a).
- Próxima D libre: **D163**.

Para tener en cuenta, sin D: el proveedor también pasa por NFKC (sus ids no
cambian, lo prueba `test_acelerar_no_cambia_ninguna_clave`); el parecido se mide
de un solo lado; el tope de parecido coincide con el umbral (por eso Screw M8
cae en fuzzy y no en exact).

## Supuestos reversibles

- Sumé 193 alias ISO3 (de la tabla oficial). Dos chocan con otra lectura
  posible: SUR=232 (Sudáfrica) y CAN=204 (Canadá).
- ＣＨＩＮＡ (ancho completo) y ÉSP se reconocen, pero el texto se guarda
  tal cual vino.

## Lo que cambió para quien usa

- Guardar un uso o cambiar el NCM de una fila con un origen viejo o raro
  guarda el NCM y avisa que el origen quedó sin cambiar.
- Productos que se escriben distinto pero se leen igual se encuentran.
- Buscar en el catálogo con descripciones largas o en kana es más rápido.

## Archivos de producto

`proyecto_maria/core/catalog_service.py`, `core/maria_generator.py`,
`core/maria_generator_export.py`, `main.py`, `pdf_extractor.py`,
`static/v2/paises_maria.js`, `static/v2/screens/catalogo.js`,
`static/v2/screens/finalize.js`, `static/v2/screens/ncm.js`, y `CHANGELOG.md`.

## Comandos copiables

Desde un worktree en ec0092a, con su venv y las variables de las pruebas
(`DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares`):

```bash
PY=$(which python) scripts/testing/sabotajes/catalogo3.sh          # 45 ROJO, «fallas: 0»
python -m pytest -q --no-cov tests/test_catalogo3.py tests/test_despacho1b.py tests/test_despacho1c.py   # 0 failed
timeout 500 python -m pytest -q --no-cov -p no:warnings tests/test_generar_maria_txt.py tests/test_excel1_txt.py tests/test_punta_a_punta1.py tests/test_maria_subitems.py tests/test_maria1b_controles.py   # 115 passed, 2 xfailed
(unset DATABASE_URL; python scripts/testing/catalogo3_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/postgres)   # 7 OK, «todo OK»
KANA=1 python scripts/testing/bench_catalogo3_lookup.py 430      # y 65, y ACENTOS=1; repetir en 07504e0 y comparar «total=»
```

## Bench del lookup

`bench_catalogo3_lookup.py`: 2000 productos del proveedor, 2000 filas de
memoria del cliente, 20 ítems (10 existentes, 10 nuevos), mejor de 3. Total en
segundos (misma máquina, uno tras otro):

| Combinación | Base cddf7de | ec0092a (producto = 9dcee73) |
|---|---|---|
| kana, 65 | 1,39 | 0,75 |
| kana, 430 | 3,97 | 2,01 |
| sin acentos, 65 | 2,06 | 1,31 |
| sin acentos, 430 | 5,04 | 3,76 |
| con acentos, 65 | 2,17 | 1,53 |
| con acentos, 430 | 5,23 | 4,13 |

- cddf7de tiene el mismo producto que 07504e0 (`git diff --stat 07504e0 cddf7de -- proyecto_maria` vacío).
- Sin el caché (a92bddd) kana 430 daba 21,48 s. El perfil: `_normalize` con 49 M
  de llamadas y `_sufijo` con 27 s acumulados, porque la clave de cada fila se
  recalculaba para cada ítem. Por eso `lru_cache(maxsize=4096)` sobre
  `clave_de_producto` (catalog_service.py:147) y no reescribir la normalización:
  la clave es pura y se calcula una vez por descripción.
- La prueba de equivalencia de la entrega anterior pasaba por casualidad; ahora
  `test_un_pedido_calcula_la_clave_de_cada_fila_una_sola_vez` cuenta llamadas, y
  el sabotaje con `maxsize=0` da rojo («assert 141 <= ((12 + 10) + 1)»).
- matches_cli a 430 (sin y con acentos): la base da 13 y la vuelta 20. Viene de
  6cbd192 (primera vuelta), que puso la memoria con el mismo criterio que el
  proveedor; el vocabulario del bench es de 18 palabras, y a 430 caracteres las
  descripciones se parecen y dan fuzzy. matches_prov da 20 en las dos.

## Rojos copiados (con el arreglo revertido)

- e1ae1fd: «Left contains 7 more items, first extra item: ('𝐁𝐑', '203', '') 1 failed»
- 8ccd004: «assert ('none', False) == ('exact', True)» (Tubo 10㎜, Frasco 500㎖), «('fuzzy', True) == ('exact', True)» (Sensor 120℃), «3 failed, 11 passed»
- ce155dc: «E   assert 141 <= ((12 + 10) + 1)  1 failed, 88 deselected» (maxsize=0)
- 9dcee73: «E   AssertionError: {"success":true,"historial_guardado":true,"aviso":"Se guardó sin origen. No reconozco el origen «TAI»: usá el nombre o el código del país."}  1 failed, 89 deselected»
- 3747e47: «FAILED …test_cada_forma_del_pais_da_el_mismo_codigo_al_importar_y_exportar[HONG KONG]  7 failed, 11 passed»
- 2c36f62: «FAILED tests/test_despacho1b.py::test_cambiar_el_origen_valida_igual_que_guardar[acento aparte] assert 200 == 400»

## Puertas

Corridas sobre 9dcee73; ec0092a sólo suma el script del bench (el producto es
idéntico), así que no las repetí sobre ec0092a.

| Puerta | SHA | Salida |
|---|---|---|
| Suite completa | 9dcee73 | «5548 passed, 335 skipped, 3 xfailed in 1136.18s (0:18:56)» |
| Golden | 9dcee73 | «115 passed, 2 xfailed in 17.68s» |
| compileall | 9dcee73 | rc 0 |
| sabotaje_maria1a.sh | 9dcee73 | «OK: los 10 sabotajes dan rojo por la razón esperada» |
| sabotajes/catalogo3.sh | 9dcee73 | 45 ROJO, «fallas: 0» |
| catalogo3_postgres.py (PG 16) | 9dcee73 | 7 OK, «todo OK» |
| smoke_friccion.sh | 9dcee73 | «OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido» |
| ataque_aislamiento.sh | 9dcee73 | «Bloqueado: 47 · Fugas: 0 · Sin probar: 0», «PUERTA G3 PASADA» |

### chequeo-6

```
chequeo-6 1345ca7..ec0092a: avisos para mirar, no un veredicto
producto +152/−99
  AVISO producto suma 53 líneas netas: el informe dice por qué (§6: más de 20)
arnés +414/−44
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 702 → 732
  proyecto_maria/core/maria_generator.py: 2368 → 2391
  proyecto_maria/core/maria_generator_export.py: 320 → 298
  proyecto_maria/main.py: 12134 → 12137
  proyecto_maria/pdf_extractor.py: 2893 → 2890
  proyecto_maria/static/v2/paises_maria.js: 33 → 47
  proyecto_maria/static/v2/screens/catalogo.js: 402 → 403
  proyecto_maria/static/v2/screens/finalize.js: 1445 → 1451
  proyecto_maria/static/v2/screens/ncm.js: 2350 → 2351
avisos: 1
```

**Por qué suma 53 netas:** los alias son datos (ISO3 y formas del país en
maria_generator.py y paises_maria.js), NFKC con su excepción, el `lru_cache` y
el criterio único `origen_para_guardar`. Se restaron 22 líneas en la
exportación (que ahora usa la misma lectura) y 3 en el extractor.

## Hallazgos

| Quién | # | Sev. | Hallazgo | Qué hice |
|---|---|---|---|---|
| /code-review high | 1 | baja | El tope de parecido igual al umbral deja Screw M8 en fuzzy | Queda así; nota arriba |
| /code-review high | 2 | baja | ISO3 SUR y CAN ambiguos | Supuesto reversible |
| /code-review high | 3 | baja | `_origen_desde_factura` (pdf_extractor.py:2084) devuelve el nombre entero si el país está en la tabla y no tiene ISO2 («Alemania Federal», 402); llega a vendedor_pais, al origen del ítem y al origen del Excel (main.py:5898) | Deliberado: antes ese origen se perdía; ahora el TXT lo lee como 402 (test_catalogo3, `LECTURA_PAIS`). Queda como riesgo: la pantalla muestra el nombre donde espera dos letras |
| /code-review high | 4 | media | El aviso decía «sin origen» aunque el producto conservaba el suyo | Arreglado en bb855e0, rojo en 9dcee73 |
| /code-review high | 5 | baja | finalize.js: el texto del hallazgo no lo recuperé tras compactar | Riesgo bajo, sin verificar |
| /code-review high | 6 | baja | ＣＨＩＮＡ y ÉSP se guardan tal cual | Supuesto reversible |
| /code-review high | 7 | — | La exportación lee distinto | No es defecto: usa la misma lectura |
| /code-review high | 8 | — | Cambio de cliente de una operación compartida | Es de PRESUPUESTO-CLIENTE-1, va con esa pieza |
| /code-review high | 9 | — | `codigos_tabla_oficial` sin caché | 5 µs por llamada: no vale el código |
| /code-review high | 10 | baja | La migración de claves corre en cada arranque | Riesgo (abajo); el tercer arranque no cambia nada (arnés PG) |
| adversario-opus-alto, alto (seguridad) | — | — | Sin hallazgos de confianza ≥ 8 sobre 1345ca7..9dcee73 | No ejecutó catalog_service ni la migración (le faltaba sqlalchemy) |

## Riesgos y lo no corrido

- El caché es global pero la función es pura; ocupa de 16 a 32 MB. Con más de
  4096 filas distintas por pedido el LRU deja de acertar y vuelve a la
  velocidad sin caché.
- Riesgos que no pediste: una clave de más de 2000 caracteres, una transacción
  abierta en el primer arranque, la migración que parte en dos al proveedor
  (D157), simplificado contra tradicional y Ø contra φ: no los cubrí.
- La pantalla quita sólo las marcas U+0300 a U+036F; el servidor, todas las
  combinantes.
- Descripciones largas con vocabulario compartido dan fuzzy (ver bench).
- Sin diagnosticar: «Task was destroyed but it is pending» al final de la suite
  (no falla nada), la línea «DATABASE_URL not set, using SQLite» en el arnés de
  PG y el WARNING de DISCO-1 en su paso 7.
- No corrido: `/security-review` completo de la rama (corrí el adversario de
  seguridad sobre la vuelta), la CI de GitHub, y las puertas sobre ec0092a.

## Sigue

PRESUPUESTO-CLIENTE-1 (D141 a): faltan sus puertas, sabotajes, informe y el
hallazgo 8.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. CATALOGO-3 (vuelta) entregada en ec0092a (informe en el commit siguiente), esperando veredicto. Sigue PRESUPUESTO-CLIENTE-1. D160, D161 y D162 abiertas; próxima D libre: D163. D151 sigue. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos.
