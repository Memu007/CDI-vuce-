# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega PAISES-NOMBRES (D266): sobre `fa89e917` (2026-11-18 22:22 UTC)

**Resultado.** Base `e5476182`. Los seis criterios están; los números salen de los logs de abajo. Lo
que decidís vos: **D273** y **D274**, al final.

- **1. Toda la tabla.** `const NOMBRES` (en `paises_maria.js`) trae 225 países con su nombre en inglés y
  en castellano, con puntos y sin ellos. Sale de la norma ISO 3166-1 (pycountry 26.2.16) con
  `scripts/datos/generar_nombres_paises.py`, más los nombres corrientes que la norma no trae
  («Holland», «EE.UU.», «Samoa Americana»). La leen el servidor (`_nombres_de_pais`, la misma que usan
  los dos lectores y el TXT) y la pantalla. Los alias que ya existían mandan sobre los nombres nuevos.
  El caso recorre NOMBRES: cada nombre solo, con su código y con el de otro país, en el despacho, la
  factura y `codigo_de_pais`; otro caso hace lo mismo en la pantalla con node.
- **2. Países Bajos.** «Netherlands», «The Netherlands», «Holland», «Holanda» y «Países Bajos» dan NL
  (423) solos, con 423 y con 434. Al lado de 310, 406 o 241 no dan ninguno.
- **3. Letra ancha.** U+FF01 a U+FF5E se leen como ASCII en los dos lectores. «３１０ ＢＲ» daba BR en
  la base; ahora da ninguno, igual que «310 BR».
- **4. Sin países nuevos equivocados.** Medí la base contra `fa89e917`: **0 orígenes cambian de un país
  a otro** en 1609 textos, cada uno solo, con cada código de la tabla y con 434. Las facturas de prueba
  del repositorio no cambian. Los nombres difíciles van como datos en un solo caso (`DIFICILES`).
- **5. Lo que queda afuera.** Un nombre que no está en la lista sigue dejando ganar al código: D264 (a)
  no cambia. D267 sigue como riesgo.
- **6. Negativo en el mismo SHA.** Con todo el arreglo vaciado (los nombres en el servidor y en la
  pantalla, y la letra ancha) fallan los casos 1, 2 y 3. Con sólo la letra ancha vaciada fallan sólo
  los seis de la letra ancha. Las otras partes, una por una, también dan rojo.

## Criterio 4: la medición

`corpus.txt` tiene 1609 textos: los nombres de la norma, los alias, la tabla, INDEC, NOMBRES,
`DIFICILES` y 22 entradas que trajo el adversario («MOROCCO LEATHER», «GREENLAND (DENMARK)»…). Cada texto
va solo, como «c texto» y como «c · texto», para cada código de la tabla y 434. Todo pasa por el despacho,
la factura y `codigo_de_pais`, y se guarda sólo lo que da país (como nombre de la tabla).
```
antes  (e5476182): 1609 textos, 226650 reconocidos
después (fa89e917): 1609 textos, 40477 reconocidos
antes 226650 después 40477 | ganados 3019 | país→otro país 0 | país→ninguno 189192
ganados por lector: Counter({'factura': 1160, 'codigo': 1160, 'despacho': 699})
código con el nombre de otro país: {'despacho': 184248} | otras pérdidas: 4944
```
- **184 248 pérdidas son lo que pide la tarea:** un código con el nombre de otro país.
- **Las 4944 restantes salen de 15 textos.** Todos nombran otro país adentro:

  | texto | veces | por qué |
  |---|---|---|
  | GREENLAND (DENMARK), COOK ISLANDS (NEW ZEALAND) | 618 c/u | territorio y su país; también con su propio código. En castellano («666 GROENLANDIA (DINAMARCA)») ya daba ninguno |
  | United States Minor Outlying Islands | 616 | excluido a propósito (UM); nombra UNITED STATES |
  | Republic of South Africa (dos formas) | 616 c/u | nombra SOUTH AFRICA; con 143 es D273 |
  | MOROCCO LEATHER, JORDAN SHOES | 616 c/u | palabra de producto que es un país |
  | TURKEY BREAST | 614 | ídem |
  | 223 PUERTO RICO (UNITED STATES), 242 ARUBA (NETHERLANDS) | 2 c/u | territorio y su país, con su código |
  | 310 CHINA MACAU / GIBRALTAR / HOLLAND COTTON / BERMUDA SHORTS | 2 c/u | otro país al lado de China |
  | 315 MADE IN U.S.A. | 2 | **daba India**: ahora ninguno |

  Todas quedan sin origen, con aviso: ninguna da otro país.
- **Antes y después de las facturas de prueba del repositorio.** Corrí los 16 archivos de pruebas de
  facturas y despachos (1983 casos) con un plugin de pytest que anota cada texto que pasa por los dos
  lectores y lo que devuelven. Base y `fa89e917` son iguales, entrada por entrada (17 entradas):
  ```
  despacho '203 BRASIL' → 'BR' | despacho '310 BRASIL' → None | despacho '310 CHINA' → 'CN'
  despacho '900 ATLANTIDA' → None | despacho 'ATLANTIDA' → None
  factura 'AR' → 'AR' | 'ATLANTIDA' → '' | 'CHN' → 'CN' | 'CN' → 'CN' | 'China' → 'CN' | 'MEX' → 'MX'
  factura 'N/A' → '' | 'NA' → '' | 'Narnia' → '' | 'P.R. China' → 'CN' | None → '' | nan → ''
  diff registro_base.json registro2_nuevo.json → IGUALES_A_BASE
  ```
  Las facturas de prueba traen pocos orígenes distintos. La medición de arriba es la que distingue.

## Supuestos

1. **La letra ancha se lee sólo en los dos lectores.** `codigo_de_pais` y la pantalla siguen rechazando
   «３１０» escrito a mano, como pide el caso de Holanda (`NO_SON_HOLANDA`). Las cifras de otro
   alfabeto («٤٣٤») tampoco cuentan. Usé una tabla de ancho completo y no NFKC, que el repositorio
   usa en otros lados, porque NFKC también cambia «№» por «No», y «No» es Noruega: lo probé y
   `_origen_desde_factura` da `'NO'`.
2. **Los territorios** sin sigla de dos letras entran por la lista `TERRITORIOS` del generador.
   Quedan afuera Jersey y Guernsey («212 NEW JERSEY»), Bonaire, Curazao y San Martín, y las islas
   menores de Estados Unidos (UM).
3. **«UK»** sigue como antes: la factura y el despacho devuelven «UK», no «GB». Ya estaba así en la
   base; por eso «UK» no está entre los nombres nuevos.
4. **El índice es uno solo:** el TXT y la validación también reconocen los nombres nuevos. Un producto
   con origen «United States» antes frenaba la generación por origen no reconocido; ahora sale 212.
   En el caso de la tabla no cambia ninguna salida del TXT que antes saliera; lo que cambia es que
   ahora sale algo donde antes frenaba.
5. **«999 + nombre»:** 999 es «OTROS PAISES». Con un nombre de la lista al lado, ahora da ninguno.

## Decisiones para vos

- **D273.** La tabla tiene países con dos códigos y nombres distintos: 143/159 Sudáfrica, 402/438,
  341/668, 242/653 Aruba y 241/659 Antillas. Con el código de uno y el nombre del otro dan ninguno, con
  aviso. Por ejemplo, «143 SUDAFRICA», «659 NETHERLANDS ANTILLES» y «653 ARUBA».
  - (a) Seguir así: pérdida con aviso. **Es el defecto que dejé.**
  - (b) Tratarlos como el mismo país, como Chipre y Turquía (311/435, 336/436).
- **D274.** «212 MADE IN U.S.A.» y «212 MADE IN E.E.U.U.» dan ninguno, en la base y ahora: con los
  puntos, la palabra que sigue a «IN» tiene una letra y la regla de «MADE IN» la cuenta como India.
  «212 MADE IN USA» da US. No lo toqué porque la regla de «MADE IN» queda igual (criterio 4).
  - (a) Dejarlo: pérdida con aviso.
  - (b) Una pieza chica que lea «MADE IN» con los puntos.

## Commits

| commit | qué |
|---|---|
| `75d37027` fix | NOMBRES generado, el servidor y la pantalla lo leen; letra ancha en los dos lectores; CHANGELOG |
| `3bf8c78c` test | los casos de la tarea; catalogo3 y maria1a siguen a la línea nueva («４３４» es NL) |
| `d808c026` test | «310 · CHINA» en lugar de «310 - CHINA»: el arnés corta el nombre del caso en « - » |
| `9bd853e2` test | `scripts/testing/sabotajes/paises_nombres.sh` |
| `a12c9c03` fix | lo que encontró el adversario: Samoa Americana, las Islas Vírgenes y las Antillas por su nombre; «Republic of South Africa» afuera; la búsqueda de NOMBRES no depende de la sangría |
| `fa89e917` test | esos nombres en `DIFICILES`; el caso no lee una tabla vacía en silencio. **Lo que se entrega** |
| informe | el commit siguiente |

## Pruebas

| qué | SHA | resultado |
|---|---|---|
| `test_paises_nombres.py` y `test_catalogo3.py` | `fa89e917` | «133 passed, 3 warnings in 26.63s» |
| suite completa, desde un worktree limpio | `fa89e917` | «6224 passed, 110 skipped, 3 xfailed, 110 warnings in 1142.03s» |
| `paises_nombres.sh` | `fa89e917` | nueve «ROJO», «OK: todos los sabotajes en rojo» (abajo) |
| `catalogo3.sh` | `fa89e917` | 65 «ROJO», «fallas: 0» |
| `sin_sigla.sh` | `fa89e917` | 16 «ROJO», «sabotajes sin rojo: 0» |
| `holanda423.sh` | `fa89e917` | 17 «ROJO», «sabotajes sin rojo: 0» |
| `origen_txt.sh` | `fa89e917` | 13 «ROJO», «sabotajes sin rojo: 0» |
| `excel1.sh` | `fa89e917` | 36 «ROJO», «sabotajes con falla: 0» |
| `sabotaje_maria1a.sh` | `fa89e917` | «OK: los 10 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria3.sh` | `fa89e917` | «OK: los 32 sabotajes dan rojo por la razón esperada» |
| `e2e_maria.sh` | `fa89e917` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| medición del criterio 4 | `e5476182` y `fa89e917` | arriba |
| chequeo-6 | `e5476182..fa89e917` | abajo, entero |

Rojo antes del arreglo: los casos de `3bf8c78c` sobre el producto de `e5476182` dan «13 failed, 9 passed». Fallaban por
la tarea: «310 UNITED STATES» daba CN, el nombre no se reconocía y la letra ancha no se leía.

Los sabotajes de `paises_nombres.sh`:
```
BASE  | casos: ======================== 22 passed, 5 warnings in 0.57s ========================
ROJO  | todo vaciado: test_cada_pais_se_reconoce_por_su_nombre_en_ingles_y_en_castellano
ROJO  | todo vaciado: test_paises_bajos_es_423_solo_con_423_o_con_434[Netherlands]
ROJO  | todo vaciado: test_la_letra_ancha_se_lee_como_la_comun[310 BR]
ROJO  | sin letra ancha: «AssertionError», 6 casos
ROJO  | el servidor no lee los nombres: «AssertionError», 7 casos
ROJO  | la pantalla no lee los nombres: «AssertionError», 1 casos
ROJO  | el despacho no lee la letra ancha: «AssertionError», 3 casos
ROJO  | la factura no lee la letra ancha: «AssertionError», 5 casos
ROJO  | un nombre de la norma choca con el de otro país: «AssertionError», 2 casos
OK: todos los sabotajes en rojo
```

chequeo-6, entero:
```
chequeo-6 e5476182..fa89e917: avisos para mirar, no un veredicto
producto +248/−7
  AVISO producto suma 241 líneas netas: el informe dice por qué (§6: más de 20)
arnés +178/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 942 → 942
  proyecto_maria/core/maria_generator.py: 2400 → 2404
  proyecto_maria/pdf_extractor.py: 2890 → 2894
  proyecto_maria/static/v2/paises_maria.js: 56 → 289
  AVISO creció una función de más de 150: proyecto_maria/static/v2/paises_maria.js:2 <anónima> 54 → 287, 233 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 2
```
- **AVISO «producto suma 241 líneas netas».** 233 son el bloque de datos generado: un renglón por país,
  como ALIASES, que ya está en el mismo archivo. El código suma 12: el bucle de la pantalla, la lectura
  del servidor y la letra ancha.
- **AVISO «creció una función de más de 150».** La «función» es el envoltorio del módulo
  (`(function () {…})()`), que ya guarda COUNTRIES y ALIASES. Lo nuevo es una constante de datos, no
  una rama. Sacarla a otro archivo suma un `<script>`, un orden de carga y un segundo archivo que leer
  en el servidor y en el caso de la pantalla. Si preferís el archivo aparte, es una pieza chica.

## Revisiones

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` (datos) | `9bd853e2` | 0 países cambiados en 2 409 156 entradas; 3 tipos de pérdida | arreglé el primero; abajo |
| `/code-review high` | `e5476182..9bd853e2` | 10 | arreglé 3; abajo |
| `/security-review` | — | no corrió | el comando falla: el repositorio no tiene `origin/HEAD`. La revisé a mano: abajo |

El adversario:
1. **El nombre compuesto del propio país, con su código, quedaba sin origen.** «695 SAMOA AMERICANA»,
   «683 UNITED STATES VIRGIN ISLANDS» y «241 NETHERLANDS ANTILLES» daban su código; con la pieza, SAMOA,
   UNITED STATES o NETHERLANDS nombraban otro país. **Arreglado** en `a12c9c03`, con datos: las tres
   formas en NOMBRES y en `DIFICILES`. Con el producto de `9bd853e2`, el archivo de casos de `fa89e917` da «1 failed, 21 passed»: falla sólo `DIFICILES`.
   El territorio con su país entre paréntesis en inglés («666 GREENLAND (DENMARK)») ahora da ninguno,
   como ya daba en castellano: queda en la tabla de pérdidas.
2. **Palabras de producto que son un país** («310 CHINA BERMUDA SHORTS», «310 MOROCCO LEATHER», «212
   NEW ENGLAND»): pérdida con aviso, en la tabla de pérdidas. «NEW ENGLAND» es como «NEW JERSEY». Lo
   dejé porque «ENGLAND» es como se escribe Inglaterra en una factura.
3. **La normalización de la pantalla y la del servidor difieren en marcas combinantes raras**
   (U+20D0…): «CHINA⃐» es China en el servidor y nada en la pantalla. Ya estaba así en la base. Va a
   riesgos.

El `/code-review`:
1. «212 MADE IN U.S.A.» da ninguno: igual que en la base (lo corrí en los dos). Es **D274**.
2. «Republic of South Africa» daba 159 y «República de Sudáfrica», 143: **arreglado**, los dos afuera.
3. La búsqueda de NOMBRES en el servidor dependía de la sangría: **arreglado**, la misma expresión que
   el caso.
4. El caso tomaba una tabla vacía si no encontraba NOMBRES: **arreglado**, ahora falla.
5. «Republic of China» con 313 (Taiwán) da ninguno: igual que en la base. No lo sumé a Taiwán porque
   hay facturas chinas que escriben así su país, y entonces un origen pasaría de China a Taiwán.
   Queda en D264 (a).
6. La letra ancha sólo en los lectores: es el supuesto 1.
7. El AVISO de la función: arriba.
8. NFKC en lugar de la tabla: no, por «№» (supuesto 1).
9. Si dos nombres chocaran, el servidor se quedaría con el último y la pantalla con el primero. Hoy no
   chocan, y el caso de choques lo frena (el sabotaje del 159 da rojo). Sin cambio.
10. El caso de choques arma la tabla vieja a mano en lugar de usar `_nombres_de_pais()`: tiene que
    ser así, porque compara lo viejo con lo nuevo y esa función ya los trae juntos. Sin cambio.

La revisión de seguridad a mano:
- NOMBRES es un dato fijo del repositorio, no algo que escriba un usuario. Lo que escribe el usuario
  sólo pasa por `translate` y por los lectores de siempre.
- Las claves nuevas de ALIASES salen en mayúsculas de `normalize`, así que no hay `__proto__`.
- Ningún nombre nuevo llega a la pantalla como HTML.

## Comandos

```bash
VENV=/ruta/al/venv
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider --timeout=300"
# 1. los casos, en fa89e917                                           → «133 passed»
$PT tests/test_paises_nombres.py tests/test_catalogo3.py | tail -1
# 2. los negativos (1 min)                → «ROJO  | todo vaciado» ×3, seis «ROJO» más, «OK: todos los sabotajes en rojo»
PY=$VENV/bin/python scripts/testing/sabotajes/paises_nombres.sh fa89e917 | grep -E "^(ROJO|VERDE|ROTO|OK|FALLAS)"
# 3. antes y después de los dos ejemplos de la tarea, la letra ancha y Netherlands
for r in e5476182 fa89e917; do R=/tmp/pn-$r; git worktree add -f -q --detach $R $r && (cd $R && env -u DATABASE_URL ENVIRONMENT=development GEMINI_API_KEY=x PYTHONPATH=. $VENV/bin/python -B -W ignore -c "
from proyecto_maria.core.despacho_lector import origen_iso2 as o
print('$r', [o(t) for t in ('310 UNITED STATES', '435 República Dominicana', '212 U.S.A.', 'NETHERLANDS', '３１０ ＢＲ', '310 MADE IN USA')])" 2>&1 | tail -1); git worktree remove -f $R; done
#    → e5476182 ['CN', '435', 'US', None, 'BR', None]
#    → fa89e917 [None, None, 'US', 'NL', None, None]
# 4. §6                                    → «producto +248/−7», «avisos: 2» (los dos de arriba)
python3 docs/pm/herramientas/chequeo-6.py e5476182 fa89e917
```
Los tres ya los corrí con esa salida. La medición del criterio 4 tarda unos 4 minutos por árbol y
necesita los guiones de mi scratchpad: no te la pido, el resultado está arriba.

## Riesgos

- **D273 y D274** (arriba).
- **Pérdidas con aviso nuevas** (la tabla del criterio 4): la palabra de producto que es un país
  («TURKEY BREAST», «MOROCCO LEATHER») y el territorio con su país entre paréntesis.
- **Las marcas combinantes raras** (punto 3 del adversario), de antes.
- **NOMBRES se regenera a mano:** si cambia pycountry, hay que volver a correr el generador, y el
  caso de choques tiene que seguir en verde.
- **Lo que no corrí:** nada de lo que pide la tarea. Hubo una primera medición sobre un corpus con renglones crudos de mi volcado (1805 textos): también dio «país→otro país 0»; la de arriba es la del corpus limpio.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio cada 2 h). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `e5476182`. Aceptadas: las de antes (… DESPACHO1B-CARGA-2 sobre `fd4eb1dd`). Entregada, en revisión: PAISES-NOMBRES (D266) sobre `fa89e917`, con D273 y D274 abiertas. Sigue, apenas entregué: ORIGEN-ETIQUETA (D261), datos (§3), adversario Sonnet alto y `e2e_maria.sh` sobre el SHA. Próxima D: D275. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; una tasa «después» sin ese negativo no distingue; cada número del informe sale de un log, y el que no está, se mide o se saca; lo que marca un adversario se reproduce antes de proponerlo; un congelado del recolector sin `gc.collect()` antes mueve los finalizadores al caso siguiente; una tarea en segundo plano muere a las 2 h: puertas con `setsid nohup` y un vigía de timeout largo; horas, sólo de `date -u` en el momento de escribirlas, también la del encabezado; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
