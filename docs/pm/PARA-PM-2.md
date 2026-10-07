# Dev 2 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MARIA-5 — en curso: una D sobre el peso que cargan el lector y el Excel

**D22. ¿El peso que traen el lector de PDF y el Excel es de una unidad o de
la línea?** Revisé cada camino antes de cambiar nada:

| Camino | Qué llega hoy | Claro |
|---|---|---|
| Carga a mano (v2, `ncm.js:688`) | «Peso unitario»; `buildMariaRequest` manda `peso_unitario` | sí, una unidad |
| Validación (v2) | muestra unitario × cantidad | sí, total |
| v1 (`app.js:3300`) | manda `peso_kg = peso_unitario × cantidad` | sí, total |
| Archivos reales en las pruebas | `peso_kg = 33` para 6 unidades | sí, total |
| Operación guardada (`main.py:5600`) | guarda `peso_unitario`; **si viene 0, inventa 0,5** | unidad |
| **Lector PDF, las dos copias** | el prompt pide `peso_kg: Peso en kg` sin decir de qué; se guarda como `peso_unitario`. Ejemplo de PyMuPDF con cantidad 1; el de PDF directo, 10 unidades con 0,5 kg | **ambiguo** |
| **Excel** (`main.py:4594`) | las columnas «peso», «weight», pero también «peso total», «peso neto» y «peso bruto», van a `peso_unitario` sin dividir | **ambiguo** |

Lo que hago sin esperar, porque no depende de la D: en el generador,
`peso_kg`, si viene, es el total de la línea (como lo mandan la v1 y los
archivos reales); si no viene, se usa `peso_unitario` × cantidad (lo que
mandan la v2 y la pantalla de validación). Los grupos suman esos totales
(hoy suman unitarios). Así ningún camino se multiplica dos veces y los dos
archivos reales no se mueven.

Lo que espera la D es qué escriben en `peso_unitario` el lector y el Excel:
si hoy Gemini o el Excel ponen el total de la línea, después del cambio el
TXT saldría multiplicado otra vez (como ya sale hoy en la pantalla de
validación).

- **(a) Recomendada.** El lector le pide a Gemini las dos cosas,
  `peso_unitario` y `peso_total_linea`, y usa la que venga (si viene sólo el
  total, lo divide por la cantidad). En el Excel, las columnas «peso total»,
  «peso neto» y «peso bruto» se dividen por la cantidad, y «peso» o «weight»
  quedan como peso de una unidad, como dice la plantilla.
- (b) El lector y el Excel quedan como están; se avisa en la revisión que el
  peso es por unidad. Más barato, pero el error queda en manos del despachante.

Sin la D, entrego el generador y dejo el lector y el Excel como están, con
el riesgo escrito.

Encontrados de paso, fuera del alcance (los propongo, no los toco): al
guardar, un peso 0 se guarda como 0,5 (`main.py:5600`); en `ncm.js`, editar
la cantidad o el valor de un grupo copia el total del grupo a cada producto
(`setGroupField`) y el TXT suma de más; «peso bruto» del Excel entra como neto.

## MARIA-1d — reentrega con el punto sumado: **`9679e21`**

**Resultado: terminada. No hay nada para decidir.** La entrega de MARIA-1d
(más abajo, sobre `c60dc3a`) sigue valiendo, y la rama incluye MARIA-3
aceptada.

| Punto sumado | Qué hice | Rojo antes → verde |
|---|---|---|
| Procedencia rara en un producto (`²`, `99999`, `٢٢٢`, «Narnia», en `pais_procedencia` o `procedencia`) | Una sola función, `errores_de_procedencia`, arma el texto. Al generar es el error 400 de siempre; en `/generate_maria/avisos` aparece el mismo texto, primero en la lista | `test_procedencia_rara_de_un_producto_avisa_igual_antes_y_al_generar`: `8 failed` → `8 passed` |

| Puerta (sobre `8a036bf`, mismo producto y pruebas que `9679e21`; el último commit sólo arregla el patrón de un sabotaje) | Resultado |
|---|---|
| Suite completa, worktree limpio | `1029 passed, 102 skipped, 25 warnings in 64.36s`, 0 failed |
| `sabotaje_maria1d.sh` | `OK: los 8 sabotajes dan rojo por la razón esperada` (el 8 es el punto sumado) |
| `sabotaje_maria3` / `4` / `1c` / `2b` / `2` / `1a` | `OK: los 30 …` (sobre `9679e21`) / `9` / `4` / `6` / `8` / `10` |
| `pantalla_maria3.js` | `OK: pantalla MARIA-3` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

Última vuelta: 2026-10-07 11:30 UTC
Contexto: ~63 % (pasado el umbral: compactar en este corte)

---

## MARIA-3 — reentrega con la devolución: **`0d6cb3e`**

**Resultado: los cinco puntos, cada uno con su rojo antes y verde después. No
hay nada para decidir.** Producto: `0144d4e` y `0e41311` (este último, de la
revisión de la devolución). El resto son pruebas, sabotajes y la captura.
MARIA-1d (abajo) sigue entregada sobre `c60dc3a` y está incluida en esta rama.

| Punto | Qué hice | Rojo antes → verde |
|---|---|---|
| 1. Una sola tabla | La tabla oficial es **`proyecto_maria/static/v2/paises_maria.js`**: los 309 países de `TABLA PAISES V.0 25082010.xlsx` (tabla oficial VUCE, según `HANDOFF.md` y la nota del archivo). El servidor lee ese mismo archivo (`codigos_tabla_oficial()`), así que no hay copia. La regla está en la raíz (`pais_reconocido` y `get_pais_codigo`): sólo cifras 0-9 y un código de la tabla. Vale para la procedencia de la operación, la de cada producto y el origen | `test_la_procedencia_acepta_todos_los_paises_de_la_pantalla`: failed → los 309 pasan; 668, 436, 435, 223, 150, 242, 254 y 358 salen en `CARTPAYPRC` |
| 2. Año del `IEXT` | Sin una fecha de emisión válida no se genera: 400 «Falta la fecha de emisión de la factura (DD/MM/AAAA)…». El año del IEXT sale de esa fecha. La revisión marca la fecha como requerida y no deja seguir sin ella. Los avisos previos dicen «sin una fecha válida no se genera el TXT» | `test_sin_fecha_valida_no_se_genera` (12 casos, incluidos `Fecha 18/07/2025` y `18/07/٢٥`); pantalla contra `088577f`: `FALLA: la fecha de emisión no figura como requerida en la revisión` |
| 3. Fechas equivocadas | DD/MM/AA es 20AA (`01/01/69` → `01/01/2069`). Una fecha futura o de hace más de dos años se avisa antes de generar. La revisión valida fechas reales (rechaza `31/02/2026`) con las mismas reglas que el servidor | `test_la_fecha_de_la_factura_sale_en_el_txt[01/01/69-01/01/2069]`, `test_fecha_futura_o_vieja_se_avisa`; pantalla: `OK la revisión pide la fecha y rechaza el 31/02/2026` |
| 4. Procedencia rara | `²`, `٢٢٢` o `2²2`: 400 «Procedencia «²» no reconocida: elegí un país de la lista.» en `/generate_maria` y en `/avisos`, nunca el texto de Python. En un producto da «Item N: Procedencia no reconocida». Una procedencia de producto en blanco no pisa la de la operación ni tapa la otra clave | `test_procedencia_no_reconocida_se_rechaza` (12), `test_codigo_raro_en_el_producto…` (6), `…en_blanco…` (2) |
| 5. Gastos | Un importe no finito, negativo o de más de un billón da 400 «Gastos (…): … no es un importe válido», por `gastos_anteriores_fob`, por `gastos_fob` y en el generador. **También el flete y el seguro**: con C y D los gastos salen de flete + seguro, y un `flete=inf` llegaba a `GTOS-POS-FOB=inf` | `test_gastos_que_no_son_un_importe_dan_400` (20), `test_el_generador_tampoco…` (5), `test_flete_o_seguro…` (8) |

Contra `088577f`, las pruebas nuevas dan `75 failed, 59 passed`.

**Pruebas viejas que cambié**, porque fijaban lo que la devolución pide quitar:
- `test_maria_iext_anio.py`: «sin fecha usa el año actual» y «fecha rara cae
  al año actual» pasan a «no se genera».
- `test_generar_maria_txt.py`, `test_prelaunch_block1.py` y MARIA-1d generaban
  sin fecha: ahora la llevan.

| Puerta (sobre `0d6cb3e`, worktree limpio) | Resultado |
|---|---|
| Suite completa | `1021 passed, 102 skipped, 25 warnings in 61.34s`, 0 failed |
| `sabotaje_maria3.sh` | `OK: los 30 sabotajes dan rojo por la razón esperada` (27 a 30 son los de la devolución) |
| `sabotaje_maria1d` / `4` / `1c` / `2b` / `2` / `1a` | `OK: los 7 …` / `9` / `4` / `6` / `8` / `10` |
| `pantalla_maria3.js` | 7 líneas `OK` y `OK: pantalla MARIA-3` |
| `pantalla_maria4.js` / `pantalla_maria1c.js` | `OK: pantalla MARIA-4` / `OK: pantalla MARIA-1c` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| Captura | `docs/pm/capturas/maria3-avisos.png` |

**Autorrevisión** con `/code-review high` sobre la devolución. Lo que arreglé
de ahí:
- el flete y el seguro;
- la regla de los códigos en la raíz (un producto con `99999` o `²` también
  pasaba);
- una procedencia en blanco que tapaba la otra clave;
- la fecha real en la revisión;
- el tope de gastos, que subí a un billón por las monedas de poco valor;
- el aviso de fecha aunque no haya productos;
- comentarios viejos.

**Riesgos que quedan:**
- La fecha d/m contra m/d ambigua (`03/04/2026`): queda anotada, como pediste.
- El servidor lee la tabla de países de un archivo de la pantalla. Si alguien
  le cambia el formato, el error dice cuál archivo es, y una prueba verifica
  los 309 códigos.
- Con la fecha obligatoria, la pantalla vieja (v1) recibe el 400 si no la
  carga. La v1 tiene la fecha como texto libre.

Última vuelta: 2026-10-07 12:10 UTC
Contexto: ~60 % (pasado el umbral: compactar en este corte)

---

## MARIA-1d — entregada: **`c60dc3a`**

**Resultado: terminada. No hay nada para decidir.** Base `8770925`
(MARIA-3 entregada más tu rama). Producto: `5faecad`, `83a0860`. El resto son
pruebas y sabotajes.

| Qué | Ahora | Rojo antes → verde |
|---|---|---|
| Campos nulos | En las dos copias del lector, el número de factura, el vendedor (nombre, identificador y dirección), el comprador, el domicilio, la fecha, la moneda y el incoterm quedan `""`, sin «None» ni «NON» | contra `8770925`: `26 failed, 3 passed` (por ejemplo `numero_factura = 'None'` y `moneda = 'NON'`) |
| Moneda e incoterm ausentes | El lector no inventa `DOL` ni `FOB`. La revisión ya los exige | `assert 'DOL' == ''` → passed |
| El vacío escrito como texto | «None», «null» o «N/A» (sin importar mayúsculas ni espacios) cuentan como vacío | 10 failed → passed (casos de la revisión) |
| Una descripción que no es texto | En la copia PyMuPDF el producto se descartaba en silencio (`'int' object is not subscriptable`); ahora llega | failed → passed |
| Prompt | Ya no dice «Ante duda, DOL»: si no hay palabra ni símbolo de moneda, `null` | prueba sobre el código; **no corrido con el Gemini real** |
| Avisos de la carátula | Antes de generar (y al generar) se avisa qué falta: vendedor, nombre o CUIT del importador, moneda o incoterm, con la línea del TXT que queda vacía o no sale | failed → passed |
| «None» en todo el TXT | Una factura con todos los campos nulos pasa por el lector (las dos copias) y por `/generate_maria`, con el pedido armado como la pantalla y los productos leídos: ni «None», ni «NON», ni «null» en el TXT ni en el nombre del archivo | antes: `«None» en el TXT` |

| Puerta | Resultado |
|---|---|
| Suite completa sobre `83a0860` (mismo producto y pruebas que `c60dc3a`; el último commit sólo toca un sabotaje) | `951 passed, 102 skipped, 25 warnings in 60.93s`, 0 failed |
| `tests/test_maria1d_campos_vacios.py` | `40 passed` |
| `sabotaje_maria1d.sh` | `OK: los 7 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria3` / `4` / `1c` / `2b` / `2` / `1a` | `OK: los 20 …` (el patrón de la fecha, al día) / `9` / `4` / `6` / `8` / `10` |
| Archivos reales | `test_golden_reproduce_estructura_real` y el de 2025 por el endpoint, dentro de la suite: idénticos |
| `pantalla_maria3.js` / `pantalla_maria4.js` | `OK: pantalla MARIA-3` / `OK: pantalla MARIA-4` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

**Autorrevisión** con `/code-review high`. Los cuatro arreglos de la tabla
(vacío escrito como texto, descripción no textual, prompt y prueba con los
productos leídos) salieron de ahí.

**Riesgos que quedan** (fuera de la pieza):
- La pantalla vieja (v1) sigue poniendo `DOL` y `FOB` cuando están vacíos,
  sin avisar. Es el mismo caso que D11.
- La v2 también tiene ese relleno en `finalize.js`, pero la revisión no deja
  seguir sin moneda ni incoterm, así que en la práctica no se usa. Por eso el
  aviso de moneda o incoterm vacíos sólo salta si alguien llama a la API sin
  ellos.
- Un CUIT presente pero mal formado no se avisa: sólo se avisa el vacío.
- Las dos copias del lector siguen duplicadas: cada arreglo se hace dos veces.

## No corrido

- El prompt nuevo con el Gemini real.

Última vuelta: 2026-10-07 10:40 UTC
Contexto: ~48 %

---

## MARIA-3 — entregada: **`088577f`**

**Resultado: terminada, con una D (D12) que no frena.** Base `06e4ac3`
(MARIA-4 aceptada). Producto: `341a429`, `1b1a95a`, `1e915f2`. El resto son
pruebas, sabotajes y la captura.

Lo que cambia en el TXT, punto por punto:

| Punto | Ahora | Prueba | Rojo antes → verde |
|---|---|---|---|
| Avisos antes de generar (M6) | `POST /generate_maria/avisos` devuelve los mismos avisos que `/generate_maria`, sin generar ni guardar. En validación, el panel «Revisá antes de generar» va arriba del botón y se actualiza al cambiar la tarjeta del despachante | pantalla | `pantalla_maria3.js` contra `06e4ac3`: `FALLA: no aparece el campo de procedencia`; con la pieza: `OK: pantalla MARIA-3` |
| Gastos anteriores al FOB (M8) | El campo de la pantalla va a `GTOS-ANT-FOB` con EXW, FCA o FAS, y sólo si es más de 0. Con otra condición no va y se avisa. Vacío o 0 con EXW, FCA o FAS: no sale y se avisa. FAS entra en `INCOTERMS_VALIDOS`. El `gastos_fob` explícito sigue mandando, como antes | respuesta 6; nota del SIM; el archivo real de 2026: los 150 cargados en la pantalla salen igual que en el real, y los bloques de productos también | antes: `assert [] == ['150.00']` |
| Procedencia | Campo por operación en la revisión, con la lista de países. Va a cada producto que no trae la suya. Si no se reconoce, o es un número que no está en la tabla, da 400. Vacía: igual al origen, con aviso, como antes | art. 15 del CA; el archivo real de 2025 sale **entero idéntico** por `/generate_maria` cargando la procedencia «PE» por operación | antes: 404 en el endpoint y procedencia sin aplicar |
| Fecha de emisión | La de la factura en DD/MM/AAAA. Se aceptan también d/m/AAAA, DD/MM/AA y AAAA-MM-DD, y se normalizan al formato de los archivos reales. Si no hay fecha o no se puede leer, `FECHAEMISIONFACT` sale **vacía** y se avisa. El año del IEXT se sigue leyendo de lo escrito | D15 | antes: `assert ['07/10/2026'] == ['']`: salía la fecha de hoy |
| Sin avisos de más | Flete o seguro «N/A», «NA», «-», «FREE», «included», «Prepaid» (con o sin punto, sin importar mayúsculas), y país «Unknown», «?», «N/A»: no se marcan como sin leer. «N/A 30» o «Unknown land» sí se marcan. Una fecha que no vino queda `""` (antes `"None"`) | — | 16 failed → passed, en las dos copias del lector |

Contra `06e4ac3`, las pruebas nuevas dan `44 failed, 9 passed`. Los 9 que
pasan son resguardos de lo que ya andaba.

| Puerta (worktree limpio) | Resultado |
|---|---|
| Suite completa sobre `fa4b096` (mismo producto y pruebas que `088577f`; el último commit sólo toca scripts y la captura) | `911 passed, 102 skipped, 25 warnings in 62.36s`, 0 failed |
| `tests/test_maria3_antes_de_generar.py` | `65 passed` |
| `sabotaje_maria3.sh` | `OK: los 20 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria4` / `1c` / `2b` / `2` / `1a` | `OK: los 9 …` / `OK: los 4 …` (patrón puesto al día) / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| `pantalla_maria3.js` | 5 líneas `OK` y `OK: pantalla MARIA-3`. Incluye la respuesta de avisos demorada: contra `a3f2df9` daba `FALLA: mientras llega la respuesta se ven los avisos de la operación anterior` |
| `pantalla_maria4.js` / `pantalla_maria1c.js` | `OK: pantalla MARIA-4` / `OK: pantalla MARIA-1c` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| Captura | `docs/pm/capturas/maria3-avisos.png` |

**Autorrevisión** (`/code-review high` y un adversario Sonnet alto, que
comparó los avisos previos con los de generar en 1512 combinaciones: 0
diferencias). Arreglado, cada uno con su prueba y su sabotaje:
- con una fecha no aceptada, el año del IEXT pasaba al de hoy;
- «1/7/2025» quedaba vacía;
- una procedencia numérica fuera de la tabla («99999») llegaba al TXT;
- gastos infinitos o de menos de un centavo se declaraban (`MCPL=inf`, `0.00`);
- un año 0026 salía como `05/03/26`;
- al entrar a validar con otra operación, el panel mostraba un momento los
  avisos de la anterior.

**Supuestos que podés rechazar:**
- Sin fecha, la línea `FECHAEMISIONFACT` sale con el valor vacío; no se
  omite. Así leí «vacía».
- Un 0 en gastos anteriores no se declara: el campo de la pantalla vale 0
  cuando está vacío.
- Una fecha DD/MM/AA se escribe con cuatro cifras, como en los archivos reales.

**Riesgos que quedan:**
- «included» o «Prepaid» en un CIF deja el flete en 0 sin aviso. Lo pediste
  así, pero en ese caso el flete viene dentro del precio.
- El campo de gastos es numérico: en Chromium, «1,5» queda 15. Es lo que se
  ve en el campo, pero no lo probé con un Chrome real en es-AR.
- La lista de países de la pantalla trae alias que no son países, por ejemplo
  «Islas» → 150 Cabo Verde o «Córdoba» → 256 ZF Córdoba. Es la tabla de
  MARIA-4, y la procedencia los acepta.
- Los avisos previos no incluyen los errores que bloquean (SBT, NCM). Esos
  siguen saliendo al generar o en la tarjeta del despachante.
- Sin fecha, el año del IEXT es el de hoy. Los identificadores son MARIA-6.
- La pantalla vieja (v1) recibe los avisos nuevos (gastos, procedencia), pero
  no tiene esos campos.

## Decisiones

**D12. El lector escribe «None» en los demás campos que Gemini devuelve
vacíos.** Lo encontró el revisor: número de factura, vendedor, comprador,
domicilio, y «NON» en moneda e incoterm. Llegan al TXT, por ejemplo
`IDSO=FAC_None` y `CDDTINCOTE=NON`. Es el mismo defecto que arreglé sólo en la
fecha, que era la que pedía MARIA-3.
- (a) Pieza chica aparte: `str(x or "")` en las dos copias, con la moneda y el
  incoterm vacíos en vez de «NON». **Recomiendo (a), antes de MARIA-5.**
- (b) Sumarlo a MARIA-5.

No me frena: sigo con MARIA-5 cuando la escribas.

## Para reproducir

```bash
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 088577f 8080
<venv>/bin/python -m pytest -q --no-cov tests/test_maria3_antes_de_generar.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py tests/test_maria4_despachante.py   # 174 passed
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria3.js     # «OK: pantalla MARIA-3»
VENV=<venv> scripts/testing/sabotaje_maria3.sh 088577f                      # «OK: los 20 …»
```

## No corrido

- La procedencia y la fecha en el Kit real.
- El campo de gastos con un Chrome real en español.

Última vuelta: 2026-10-07 09:30 UTC
Contexto: ~40 %

---

## MARIA-4 — reentrega con la devolución: **`2461939`**

Producto `dbf8848`; pruebas y sabotajes `dbf8848`…`2461939`. La entrega
anterior (`6149ef3`, abajo) sigue valiendo para todo lo demás.

| Punto devuelto | Qué hice | Rojo antes → verde |
|---|---|---|
| 1. Estado contra origen | El generador rechaza un estado argentino (1, 3, 5) con origen extranjero y uno importado (2, 4, 6) con origen argentino: 400 «Ítem N (descripción): el estado «…» no corresponde al origen (…); elegí otro.». Los nombres y la regla están en un solo lugar, `ESTADOS_ARGENTINOS` / `ESTADOS_IMPORTADOS`. En la pantalla, cada producto ofrece sólo los estados de su origen, y el estado elegido queda atado a la clase de origen: si el origen cambia, se borra y se vuelve a pedir | `test_estado_que_no_corresponde_al_origen_se_rechaza`: 7 failed → passed. Pantalla contra `6149ef3`: `FALLA: al pasar a origen extranjero queda el estado argentino elegido antes`; con `2461939`: `OK al cambiar el origen el estado elegido se vuelve a pedir y sólo se ofrecen los que corresponden` |
| 2. La pantalla vieja muestra los avisos | Después de generar, `static/app.js` muestra los `warnings` y los `supuestos` de `/generate_maria` en un `alert` («Revisá antes de pegar el TXT en el Kit»), antes de bajar el archivo | `test_la_pantalla_vieja_muestra_los_avisos_de_generate_maria`: failed → passed. Es una prueba sobre el código: no corrí la v1 en el navegador |
| 3. `origen` y `pais_origen` | Los supuestos leen `pais_origen` primero, como el generador, en sus dos lugares | `test_supuestos_leen_el_origen_como_el_generador`: failed → passed |

Tuve que corregir dos pruebas que usaban combinaciones que ahora no valen.
Una pedía estado 5 con origen chino: la pasé a 6. La otra probaba un grupo
con estados distintos usando 2 y 6: la pasé a 2 y 4.

| Puerta (sobre `2461939`) | Resultado |
|---|---|
| Suite completa | `846 passed, 102 skipped, 25 warnings in 60.34s`, 0 failed |
| MARIA-4 + archivos reales + sub-ítems + supuestos | `122 passed` |
| `pantalla_maria4.js` | 7 líneas `OK`, `OK: pantalla MARIA-4` |
| `sabotaje_maria4.sh` (6 de antes + estado contra origen, orden del origen, pantalla vieja sin avisos) | `OK: los 9 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria1c` / `2b` / `2` / `1a` | `OK: los 4 …` / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

No hubo autorrevisión con subagentes en esta vuelta: los tres puntos son
chicos y tienen cada uno su rojo antes y su sabotaje. Nada para decidir.

Contexto: ~88 %. Hace falta el `/compact` antes de MARIA-3.

---

## MARIA-4 — entregada: lo que decide el despachante sale en el TXT

| Qué | SHA |
|---|---|
| Base (MARIA-1c aceptada) | `448b54d` |
| Producto | `893f6bd` (generador y `/generate_maria`), `30aa414` (pantalla y listados), `8b6edb9` (arreglos de la revisión), `9cf109e` (CHANGELOG) |
| Pruebas, sabotajes, pantalla y captura | `5500f6e`, `e3b7b84`, `9cf109e`, `41a623e`, `b3ec171`, `6149ef3` |
| **SHA que se entrega** | **`6149ef3`** |

**Resultado: terminada.** Cambia lo que sale en el TXT, campo por campo y con
la prueba que fijaste:

| Campo | Ahora | Por defecto |
|---|---|---|
| `CARTUSO`, por producto | Se elige entre los seis estados, con los nombres del despachante (1 a 6). La tabla está en un solo lugar, `ESTADOS_MERCADERIA`, con tu nota | Origen extranjero: 2. Origen argentino: no hay. Si falta, el servidor responde 400 «Ítem N (descripción): el origen es argentino; elegí el estado…» y la pantalla no deja generar |
| `IVAADICIONAL1` | Por operación, con cambio por producto: reventa (`NO_VALIDA`) o uso particular (`IVAAD1`) | Reventa |
| `BANCOSARGENTINA` | Código BCRA de 3 dígitos, por operación. Va antes de `ARDIG-SETI-OPC`, como en el archivo de 2026 | El último banco del cliente. Si no hay, la línea no sale y hay aviso |
| `ARDIG-CUIT-PSAD` | Modoc (`PSAD06`) o Lakaut (`PSAD01`) | La última empresa del usuario. Si no hay, Modoc |

- **Supuestos:** lo que se usó por defecto entra en `supuestos_declarados`:
  el estado de cada producto, el IVA, el banco ausente y la empresa. Se suma
  el aviso de que la reducción o exclusión del IVA se elige en «Ventajas» del
  Kit. El aviso fijo «se declaró 3, siempre» se fue.
- **Pantalla v2:** en validación, antes de generar, aparece la tarjeta «Lo
  que decide el despachante»:
  - banco, empresa e IVA de la operación;
  - una tabla por producto con el estado y el cambio de IVA.

  Solo se guarda lo que la persona elige. El valor por defecto sigue al
  origen: si al volver a NCM el origen pasa a argentino, el estado se vuelve
  a pedir. La propuesta de banco y empresa es del cliente activo.
- **Dónde se guarda, sin columnas nuevas:** en la operación, dentro de
  `extra.resumen.maria`. Incluye el estado y el IVA de cada producto. Los
  listados `GET /api/clientes/{id}/operaciones` y `GET /api/operations`
  devuelven `maria`, recortado a 12 caracteres, y de ahí sale la propuesta.
  Respetan el dueño de las operaciones: el revisor lo probó con dos usuarios.

**Los dos archivos reales:**
- **2025:** sale idéntico entero, cargando estado 3, uso particular, sin banco
  y `PSAD06`.
- **2026:** salen igual que el real los cuatro campos (`2`, `NO_VALIDA`,
  `191`, `PSAD01`) y el orden banco → `ARDIG-SETI-OPC` → `ARDIG-CUIT-PSAD`.
  Los bloques de productos también salen idénticos. El resto del archivo de
  2026 nunca se comparó entero: el real viene sin el relleno de espacios.

## Decisiones

**D11. En la pantalla vieja (v1), un producto de origen argentino ya no se
puede generar.** Esa pantalla no tiene dónde elegir el estado. Recibe el 400
con el mensaje claro y no se rompe, pero no genera. Con otros orígenes genera
con los valores por defecto (2 y reventa). Tampoco muestra los supuestos.
- (a) Aceptarlo: la v1 está de salida, y el criterio 3 prohíbe inventar el
  estado. **Recomiendo (a).**
- (b) Agregar un selector de estado en la v1: una pieza aparte.

Supuesto que podés rechazar: si el banco viene propuesto (el último del
cliente) y la persona no lo toca, va al TXT y la pantalla lo dice («Banco
191: el último que usó este cliente»).

## Evidencia

**Rojo antes:** las pruebas nuevas contra el producto de `448b54d` dan
`30 failed, 2 passed`. Por ejemplo, `TypeError: generate_maria_txt() got an
unexpected keyword argument 'banco_bcra'` y `assert 200 == 400` (origen
argentino sin estado). La comprobación de pantalla contra la primera versión
(`9cf109e`) falla con `FALLA: estados: ["2","3"]`: el 2 por defecto quedaba
guardado como elegido.

| Puerta (sobre `6149ef3`, worktree limpio) | Resultado |
|---|---|
| Suite completa | `837 passed, 102 skipped, 24 warnings in 60.13s`, 0 failed |
| MARIA-4 + archivos reales + supuestos + sub-ítems | `113 passed` |
| `compileall` | ok |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `scripts/testing/pantalla_maria4.js` | `OK estado 2 por defecto en el importado; el argentino sin estado; banco 191 propuesto` / `OK sin estado en el argentino no se genera` / `OK el pedido lleva banco 191, Lakaut, uso particular, el estado 3 elegido y el importado sin elegir` / `OK al volver y pasar a origen argentino se vuelve a pedir el estado` / `OK otro cliente: se propone su banco (014)` / `OK: pantalla MARIA-4` |
| `pantalla_maria1c.js` | `OK: pantalla MARIA-1c` |
| `sabotaje_maria4.sh` (CARTUSO 3 fijo, IVAAD1 fijo, PSAD06 fijo, sin banco, estado argentino inventado, listados sin `maria`) | `OK: los 6 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria1c` / `2b` / `2` / `1a` | `OK: los 4 …` / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| Captura | `docs/pm/capturas/maria4-despachante.png` |

**Autorrevisión** (adversario Sonnet alto, que probó la pantalla en una API
propia, más `/code-review high`). Arreglados, cada uno con su prueba o su
paso en la comprobación de pantalla:
- el estado por defecto quedaba guardado como elegido, y al pasar el origen a
  argentino salía `CARTUSO=2`. Es el defecto que esta pieza tenía que evitar;
- el banco o la empresa propuestos de un cliente quedaban pegados al cambiar
  de cliente;
- lo elegido se perdía al volver a NCM;
- se guardaba el valor por defecto como elegido, y por eso los supuestos no
  lo avisaban;
- la propuesta se pedía de a una consulta y podía pisar lo que se escribía
  mientras tanto;
- el estado y el IVA por producto no se guardaban con la operación;
- un grupo con el mismo valor escrito de dos maneras se rechazaba;
- el mensaje de error apuntaba a la fila equivocada en los grupos; ahora
  nombra el producto;
- un banco con dígitos no latinos pasaba;
- el listado crecía sin tope con un valor sembrado;
- la pantalla trataba «ARG» como Argentina y el servidor no.

Quedan como riesgos o fuera de alcance:
- la v1 (D11);
- la tabla de estados está copiada en `despachante.js`, con una nota en el
  archivo. Unificarla pide un endpoint;
- la v2 todavía no muestra los supuestos antes de generar: eso es MARIA-3.

## Para reproducir

```bash
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 6149ef3 8080
<venv>/bin/python -m pytest -q --no-cov tests/test_maria4_despachante.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py tests/test_maria_supuestos.py   # 113 passed
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria4.js          # «OK: pantalla MARIA-4»
VENV=<venv> scripts/testing/sabotaje_maria4.sh 6149ef3                           # «OK: los 6 …»
```

## No corrido

- La prueba en el Kit del orden de los estados: la tabla tiene la nota.
- La pantalla v1 en el navegador: el revisor la probó por HTTP.
- `ataque_aislamiento.sh`: los listados nuevos filtran por dueño. El revisor
  probó con dos usuarios: el que no es dueño recibe 404 y la lista vacía.

Sigo con MARIA-3.

Última vuelta: 2026-10-07 06:50 UTC
Contexto: ~82 % (muy pasado el umbral; compactar)
