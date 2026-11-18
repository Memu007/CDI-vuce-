# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega ORIGEN-ETIQUETA (D261): sobre `5a28c13c` (2026-11-18 23:13 UTC)

**Resultado.** Base `bf787b2d`. Están los cuatro criterios. Incluye `dfa1b08d`, el merge de tu rama, que sólo
trae `docs/pm/`. Los números salen de los logs de abajo. No hay D nuevas: lo que
decidís vos es el supuesto 1 y si aceptás el riesgo 1.

- **1. Código y nombre.** El «Origen frecuente» del cliente y la procedencia de la revisión usan una
  función nueva, `etiqueta` (en `paises_maria.js`). Muestra `label` («310 · CHINA») si el valor es un
  país y, si no, lo escrito. «CN», «CHINA», «CHN», «310» y «Hong Kong» se ven con código y nombre.
  «434», «0434», 434 como número, «434 · HOLANDA», «HOLANDA» y «NL» se ven «423 · PAISES BAJOS».
- **2. Lo que no se reconoce** se ve como se escribió, sin los blancos de los bordes. El KPI lo pone
  con `textContent` y la revisión con `input.value`. La pantalla prueba un `<img onerror>`: no se
  ejecuta y no crea elementos.
- **3. TXT igual byte a byte.** Generé el TXT de la misma operación en la base y en `7a02d2ca`, desde
  la pantalla de revisión. Fueron 14 formas de procedencia, cada una dejada como venía del borrador y
  escrita a mano:
  ```
  28 operaciones; 28 TXT iguales byte a byte; 22 se ven distinto
  ```
  Las 6 que se ven igual en la base y ahora son «222 · PERU», «423 · PAISES BAJOS» y la vacía, en sus
  dos modos. Lo guardado no se reescribe: la operación conserva lo escrito. La pantalla lo comprueba
  con cada forma, en el borrador y escrita. Hay un sabotaje que guarda lo que se ve y da rojo.
- **4. Reemplaza «se ve el código «423»» en esos dos lugares.** Los catálogos del proveedor y del
  cliente siguen con `mostrar` y «423» (supuesto 1).

## Supuestos

1. «La revisión» es el campo de procedencia de la pantalla de revisión, el único de esa pantalla que
   tiene país. El origen de cada ítem se edita en la grilla del NCM, que ya mostraba código y nombre con
   su propia copia de la regla. Esa copia ahora llama a `etiqueta` (§6: un chequeo, un lugar). Para el
   NCM no cambia nada, porque la regla era la misma. Los catálogos no entran: si los querés con
   etiqueta, es otra pieza. Tienen `maxlength="3"` y la grilla del cliente es angosta.
2. Lo que no es un país se ve sin los blancos de los bordes (« ATLANTIDA » se ve «ATLANTIDA»). Lo tomé
   de la regla del NCM, para que las tres pantallas se vean igual. Un origen frecuente de sólo
   espacios ahora se ve «—»; antes quedaba en blanco.

## Commits

| commit | qué |
|---|---|
| `30f5786a` fix | `etiqueta`; el KPI y la procedencia la usan; CHANGELOG |
| `9288fc56` test | el caso de la etiqueta; la pantalla recorre 16 formas en el KPI y en la revisión |
| `9b51ab54` test | `holanda423.sh`: los sabotajes siguen a la línea nueva; siete nuevos |
| `876bc666` fix | lo que marcó `/code-review`: una sola etiqueta para el NCM, el KPI y la revisión; el nombre largo no ensancha el KPI |
| `1fb6804f` test | el recorte en el caso; vaciar antes de escribir, para que dispare «change»; el chequeo de HTML en el KPI; un ayudante para la tabla |
| `7a02d2ca` test | los sabotajes siguen al recorte |
| `dfa1b08d` merge | tu rama (sólo `docs/pm/`) |
| `5a28c13c` test | el sabotaje de «cada tecla» espera el rojo que ahora da antes (abajo). **Lo que se entrega** |
| informe | el commit siguiente |

## Pruebas

| qué | SHA | resultado |
|---|---|---|
| `test_catalogo3.py` y `test_paises_nombres.py` | `7a02d2ca` (los mismos en `5a28c13c`) | «134 passed, 3 warnings in 26.25s» |
| suite completa, desde un worktree limpio | `5a28c13c` | «6225 passed, 110 skipped, 3 xfailed, 105 warnings in 1098.28s (0:18:18)» |
| `holanda423.sh` | `5a28c13c` | 24 «ROJO», «sabotajes sin rojo: 0» (abajo) |
| `pantalla_holanda423.js` | `5a28c13c` | «OK: pantalla Holanda→423» (la base de `holanda423.sh`) |
| `e2e_maria.sh`, desde un worktree limpio | `5a28c13c` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| TXT antes y después | `bf787b2d` y `7a02d2ca` | arriba |
| KPI a 390 px con nombres largos | `9b51ab54` y `7a02d2ca` | abajo |
| chequeo-6 | `bf787b2d..5a28c13c` | abajo, entero |

**Rojo antes del arreglo.**
- La pantalla de `7a02d2ca` sobre el producto de `bf787b2d` da «FALLA: el origen frecuente «434» se ve
  «423»».
- El caso nuevo en la base no tiene `etiqueta`. Medido con `mostrar`, que es lo que se veía, da «353
  distintos de 693». Por ejemplo: «('CHN', 'CHN', '310 · CHINA'), ('ITA', 'ITA', '417 · ITALIA'),
  ('Hong Kong', 'Hong Kong', '341 · HONG KONG')».

`holanda423.sh`:
```
BASE  | casos: ======================= 112 passed, 5 warnings in 25.78s =======================
BASE  | pantalla: OK: pantalla Holanda→423
ROJO  | la etiqueta es lo que muestra el catálogo: «AssertionError», 1 casos
ROJO  | la etiqueta es lo que muestra el catálogo: «FALLA: el origen frecuente «434» se ve «423»»
ROJO  | la etiqueta es sólo el código: «AssertionError», 1 casos
ROJO  | la etiqueta escribe «null» por lo que falta: «AssertionError», 1 casos
ROJO  | la etiqueta deja los blancos de los bordes: «AssertionError», 1 casos
ROJO  | el origen frecuente se ve como HTML: «FALLA: el origen frecuente «<img»
ROJO  | mostrar devuelve lo que vino: «At index 0 diff: '434' != '423'», 1 casos
ROJO  | mostrar escribe «null» por lo que falta: «'null' != ''», 1 casos
ROJO  | mostrar recorta lo que no es el 434: «'Holanda' != ' Holanda '», 1 casos
ROJO  | mostrar devuelve lo que vino: «FALLA: catálogo del proveedor: «434» guardado se ve «434»»
ROJO  | el catálogo del proveedor muestra lo guardado: «FALLA: catálogo del proveedor: «434» guardado se ve «434»»
ROJO  | el catálogo del cliente muestra lo guardado: «FALLA: catálogo del cliente: «434» guardado se ve «434»»
ROJO  | el catálogo del cliente deja lo escrito: «FALLA: «434» escrito en el catálogo del cliente se ve «434»»
ROJO  | la procedencia del borrador se ve como vino: «FALLA: procedencia «434» del borrador se ve «434»»
ROJO  | la procedencia escrita queda como se escribió: «FALLA: procedencia «434» escrita se ve «434»»
ROJO  | la procedencia del borrador cambia en la operación: «FALLA: procedencia «434» del borrador queda «423 · PAISES BAJOS» en la operación»
ROJO  | la procedencia escrita se guarda como se ve: «FALLA: procedencia «434» escrita queda «423 · PAISES BAJOS» en la operación»
ROJO  | el catálogo del proveedor manda el origen sin tocar: «FALLA: cambiar sólo el NCM reescribe el origen guardado»
ROJO  | el catálogo del cliente pisa lo que se sigue escribiendo: «FALLA: lo escrito mientras se guardaba «434» quedó «423»»
ROJO  | el borrador muestra cada campo con su etiqueta: «FALLA: la factura «434» del borrador se ve «423 · PAISES BAJOS»»
ROJO  | lo escrito en cualquier campo pasa por la etiqueta: «FALLA: la factura «0434» escrita se ve «423 · PAISES BAJOS»»
ROJO  | el catálogo del cliente muestra el código de lo escrito: «FALLA: «nl» escrito en origen del catálogo del cliente se ve «423»»
ROJO  | la procedencia cambia en cada tecla: «FALLA: procedencia «434» escrita queda «423 · PAISES BAJOS» en la operación»
ROJO  | el origen frecuente se ve como vino: «FALLA: el origen frecuente «434» se ve «434»»
sabotajes sin rojo: 0
```
«La procedencia cambia en cada tecla» daba rojo en `7a02d2ca`, pero con otra frase: «procedencia «434»
escrita queda «423 · PAISES BAJOS» en la operación». Es la misma causa. Ahora la ve antes el bucle, que
vacía y escribe cada forma; `5a28c13c` espera esa frase. El chequeo de «4340» tecla por tecla sigue en la
pantalla.

El KPI a 390 px de ancho, con los nombres más largos de la tabla. Los números son el ancho de la grilla
(`scrollWidth`/`clientWidth`) y el alto de la tarjeta:
```
antes del CSS (9b51ab54)  109 · REP.DEMOCRAT.DEL CONGO EX ZAIRE   grilla [311, 308]  alto 66
ahora (7a02d2ca)          109 · REP.DEMOCRAT.DEL CONGO EX ZAIRE   grilla [308, 308]  alto 88
ahora (7a02d2ca)          682 · ISLAS VIRGENES BRITANICAS (TERRITORIO NO AUTONOMO DEL REINO UNIDO)  alto 176
```
La página entera ya mide 523 px de ancho a 390 px de vista, con cualquier origen (también con «310 ·
CHINA»). Eso no es de esta pieza: va a riesgos.

chequeo-6, entero:
```
chequeo-6 bf787b2d..5a28c13c: avisos para mirar, no un veredicto
producto +12/−5
arnés +89/−30
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/paises_maria.js: 289 → 294
  AVISO creció una función de más de 150: proyecto_maria/static/v2/paises_maria.js:2 <anónima> 287 → 292, 2 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/clientes.js: 2213 → 2213
  proyecto_maria/static/v2/screens/ncm.js: 2351 → 2351
  proyecto_maria/static/v2/screens/review.js: 1198 → 1198
avisos: 1
```
- **AVISO «creció una función de más de 150».** La «función» es el envoltorio del módulo
  (`(function () {…})()`). `etiqueta` es una función aparte de tres líneas, como `mostrar` y `label`,
  que están en el mismo envoltorio.

## Revisiones

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` (datos) | `9b51ab54` | 0 que rompan un criterio; 3 menores | abajo |
| `/code-review high` | `bf787b2d..9b51ab54` | 7 | arreglé 5; abajo |
| `/security-review` | — | no corrió | el comando falla porque el repositorio no tiene `origin/HEAD`. La hice a mano: abajo |

El adversario:
- Comparó `etiqueta` con `codigo_de_pais` del servidor en 30 000 cadenas al azar (separadores raros,
  saltos, combinantes, mayúsculas): **0 diferencias**.
- Comprobó en el navegador que enfocar y salir no cambia el estado, que lo escrito queda en la
  operación y que el HTML se ve como texto.
- Comprobó que nada más lee `#f_procedencia` y que `finalize.js` arma el TXT desde la operación.
- Los tres menores:
  1. Un arreglo `['CN']` se vería «310 · CHINA». No llega: el valor viene de JSON como texto.
  2. Un origen frecuente de sólo espacios se veía en blanco. Queda arreglado por el supuesto 2.
  3. Los catálogos siguen con `mostrar`. Es el supuesto 1.

El `/code-review`:
1. **ncm.js tenía la misma regla duplicada.** Arreglado en `876bc666`: ahora llama a `etiqueta`.
2. **Escribir lo mismo que se ve no dispara «change»**, así que ATLANTIDA, el HTML y «-» no probaban
   lo escrito. Arreglado en `1fb6804f`: se vacía antes de escribir.
3. **Un nombre largo ensanchaba el KPI.** Arreglado con `min-width: 0` y `overflow-wrap: anywhere`;
   las medidas están arriba.
4. **El campo muestra la etiqueta y la operación guarda lo escrito.** Eso es lo que pide el criterio
   3. Nada compara el campo con la operación (lo verificó el adversario), y el campo no tiene la pista
   «Detectado del PDF». Sin cambio.
5. **El caso leía la tabla con su propia expresión.** Ahora hay un ayudante, `_paises_de_la_pantalla`,
   que también usa el caso que ya la leía igual. No usa `_tabla_oficial` porque esa normaliza los
   nombres y la etiqueta lleva el nombre como está escrito.
6. **El chequeo de HTML ejecutado estaba en la revisión, donde no puede pasar.** Pasó al KPI.
7. **El nombre del caso era largo.** Ahora es `test_la_etiqueta_es_la_del_txt`.

La revisión de seguridad a mano:
- Lo nuevo llega a la pantalla sólo por `textContent` (el KPI) y por `input.value` (la procedencia).
  Hay un sabotaje que pasa el KPI a `innerHTML` y la pantalla da rojo.
- En el NCM, `getOriginLabel` devuelve lo mismo que antes y sigue pasando por `CDI.escapeHtml` donde
  arma HTML.
- No cambia nada del servidor, de lo guardado ni del TXT.

## Comandos

```bash
VENV=/ruta/al/venv
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider --timeout=300"
# 1. los casos, en 5a28c13c                                         → «134 passed»
$PT tests/test_catalogo3.py tests/test_paises_nombres.py | tail -1
# 2. los negativos y la pantalla (unos 25 min)          → 24 «ROJO», «sabotajes sin rojo: 0»
PY=$VENV/bin/python scripts/testing/sabotajes/holanda423.sh 5a28c13c | grep -E "^(BASE|ROJO|VERDE|ROTO)|sin rojo"
# 3. §6                                                 → «producto +12/−5», «avisos: 1» (el de arriba)
python3 docs/pm/herramientas/chequeo-6.py bf787b2d 5a28c13c
```
Ya corrí los tres y dieron esa salida. El TXT antes y después y el KPI a 390 px salen de guiones de mi
scratchpad: no te los pido, los resultados están arriba.

## Riesgos

1. **El 682 ocupa 176 px de alto en el KPI** a 390 px de ancho. Es un país raro y no rompe la grilla.
   Si preferís cortarlo con «…», es una línea de CSS.
2. **La página de clientes ya era más ancha que un celular** (523 px a 390 px de vista), con cualquier
   origen. Viene de antes; no lo toqué.
3. **Un mismo país se ve distinto según la pantalla:** con código y nombre en el KPI, la revisión y el
   NCM, y como se escribió en los catálogos (supuesto 1).
4. **Lo que no corrí:** nada de lo que pide la tarea.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio cada 2 h). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `04cdc9c0`. Aceptadas: las de antes (… PAISES-NOMBRES (D266) sobre `fa89e917`, D273 (a) y D274 (a)). Entregada, en revisión: ORIGEN-ETIQUETA (D261) sobre `5a28c13c`, sin D nuevas; supuestos 1 (la revisión es la procedencia; los catálogos siguen con «423») y 2 (recorte de bordes). No hay pieza marcada «apenas entregues»: espero el veredicto. Próxima D: D275. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; una tasa «después» sin ese negativo no distingue; cada número del informe sale de un log, y el que no está, se mide o se saca; lo que marca un adversario se reproduce antes de proponerlo; un congelado del recolector sin `gc.collect()` antes mueve los finalizadores al caso siguiente; una tarea en segundo plano muere a las 2 h: puertas con `setsid nohup` y un vigía de timeout largo; horas, sólo de `date -u` en el momento de escribirlas, también la del encabezado; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
