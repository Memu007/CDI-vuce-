# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega D239 (a), vuelta tras la devolución sobre `196ef370`: sobre `01c28e83` (08:06 UTC)

**Resultado.** Los cinco criterios de la vuelta se cumplen en `01c28e83` (base `2e69a0b1`). Un código
con otro país nombrado al lado da ninguno y el aviso: entre paréntesis, pegado, después de números o
con la sigla de dos letras («143 CHINA (MAINLAND)», «310 HONG KONG (TERRITORIO DE CHINA)», «410 MADEIRA
(TERRITORIO DE PORTUGAL)», tu no dado «212 ARUBA (TERRITORIO DE PAISES BAJOS)», «310 CHINA (VN)», «143 US
12»). «143,00», «143.5» y «143 310» no empiezan con un código. Lo que andaba sigue: los 114, «143», «143
REPUBLICA DE SUDAFRICA» → 143, «310 CHINA» → CN; el volcado del criterio 4 de la pieza da 0 diferencias
con `196ef370`. Cruzando cada código de la tabla con cada nombre de la tabla (284592 formas), ninguna
da el código con otro país: la base tenía 154106 y `196ef370`, 26709. `producto +57/−14`.

**Lo que decidís vos:**
- **D266. Nombres de país que no conoce ninguna tabla.** «310 UNITED STATES», «310 U.S.A.», «310 SOUTH
  AFRICA», «310 RUSSIA», «310 MACAU» dan CN sin aviso: el resto no se reconoce como país y gana el código
  (D264 (a)). Con el nombre que la tabla sí tiene da ninguno («310 USA», «310 GERMANY», «310 ESTADOS
  UNIDOS»). Propongo una pieza aparte que sume los nombres en inglés y las grafías con puntos a los nombres
  reconocidos; cambia también el lector de facturas, que usa el mismo índice. Sin pieza, queda como riesgo.
- **D267. Siglas que en un despacho son una abreviatura.** Con un número fuera de la tabla, «900 SD» da
  Sudán, «900 SN» Senegal, «900 NO» Noruega, «900 SI» Eslovenia, «900 ROU» Rumania (en Argentina, Uruguay).
  Es previo: la base da lo mismo, y «SD» solo, sin número, también da Sudán (es el reconocedor de la
  factura). Sólo saqué «NA», que el lector de facturas ya trataba como «no aplica». Propongo decidirlo con
  D266: o una lista de abreviaturas que no son país, o que una sigla sola no alcance fuera de la tabla.

**Una causa, tres arreglos de producto:**
- `eeaca5c8`: el resto se recorre palabra a palabra con el nombre más largo desde cada una
  (`_paises_nombrados`), en vez de recortarle la puntuación y descartar lo que no se reconoce. Alcanza
  con un país distinto (por nombre de tabla) para no dar ninguno. El código tiene que ser tres cifras
  sueltas: `(\d{3})\b(?!\W*\d)`.
- `0d835e0b`: una sigla de dos letras cuenta salvo entre dos palabras de tres letras o más (el «IN» de
  «MADE IN USA», que es India): «310 CHINA (VN)», «143 US 12», «143 (CN) 5» daban el código. Con un
  número fuera de la tabla, sólo un nombre entero da país: «900 MAR DEL PLATA» daba Marruecos en un
  paso intermedio mío (no en la base).
- `6f5b98a0`: fuera de la tabla, el nombre entero se busca en el mismo índice, con sus signos: el paso
  intermedio perdía «900 CHINA (MAINLAND)» y «900 VATICANO(SANTA SEDE)». Fuera de la tabla da lo mismo
  que la base en lo que medí, salvo «999 CHINA» (999 es de la tabla, ya informado).

**Por qué +43 netas (el AVISO de chequeo-6):** `_paises_nombrados` y su índice (`_paises_por_palabras`)
son el criterio 1: reconocer un país en cualquier lugar del resto, no sólo el resto entero. No hay otro
reconocedor que lo haga; el de la factura reconoce el texto entero como un país, no un país dentro de un
texto. Sumarlo sin sacar nada era lo mínimo: los dos que ya había (`codigo_de_pais` con nombre y
`_origen_desde_factura`) siguen usándose en otros lados. Que haya tres reconocedores va a la cola de
limpieza (abajo).

### Criterio 3: el caso

`test_un_codigo_con_otro_pais_al_lado_no_da_ninguno` (`test_catalogo3.py`). Los nombres de la tabla con
paréntesis o punto salen de `COUNTRIES` (`> 40`, hoy 56):
- cada uno con su propio código da su país (o su código, si no tiene sigla);
- con «900», un número fuera de la tabla, da el país de ese nombre (D265 (a));
- con 143 y con 310, cuando son otro país, da ninguno;
- las formas de número de la devolución y «143 MADE IN USA», «143 PRODUCTO USA ORIGINAL»;
- cada sigla de dos letras de la tabla que no es CN, en «310 CHINA (XX)», «310 CHINA XX 125» y «310 · XX · 2»;
- fuera de la tabla, una palabra suelta no es un nombre («900 MAR DEL PLATA», «900 CAROLINA DEL SUR»,
  «900 NA»);
- y lo que tiene que seguir: «143», «143 ORIGEN», «143 REPUBLICA DE SUDAFRICA» → 143; «310 CHINA», «310
  (CN)», «310 MADE IN CHINA», «310 PAIS DE ORIGEN» → CN; «999 ATLANTIDA» → 999; «900 · CHINA», «900 (P.R.
  CHINA)» → CN; «900 TIMOR ORIENTAL» → 358.

El caso de los 114 (`test_un_codigo_sin_sigla_entra_por_el_despacho`) sigue igual y verde.

### Criterio 4: el rojo con el arreglo revertido

Producto de `196ef370`, pruebas de `01c28e83`:
```
E     At index 7 diff: None != 'RESTO (AFRICA)'
=========== 1 failed, 1 passed, 109 deselected, 5 warnings in 0.39s ============
```
El primer assert ya cae: en `196ef370` el `\W*$` le sacaba la «)» a un nombre propio. Las formas de tu
devolución, con el mismo producto:
`{'143 CHINA (MAINLAND)': '143', '310 HONG KONG (TERRITORIO DE CHINA)': 'CN', '212 ARUBA (TERRITORIO DE
PAISES BAJOS)': 'US', '143,00 310 CHINA': '143', '143.5 CHINA': '143', '310 CHINA (VN)': 'CN', '143 US 12':
'143', '143 MADE IN USA': '143'}`; en `01c28e83`, todas None.

## Sabotajes (§3)

`sin_sigla.sh` pasa de 6 a 16: catorce del lector y los dos de pantalla. Los que deshacen el código sin
sigla o la comparación rompen también el caso nuevo y esperan los dos casos.

| sabotaje | frase |
|---|---|
| el código sin sigla no da origen | «At index 0 diff: '310' != '143'» |
| código y nombre de dos países dan el código | «At index 0 diff: '143' != None» |
| se compara el código y no el país | «diff: '310' != '435'» |
| la puntuación tapa el nombre de otro país | «At index 147 diff: '310' != '271'» |
| lo que no es un nombre entero se descarta | «{'143 CHINA POPULAR': '143'}» |
| gana el nombre más corto | «At index 125 diff: '310' != '229'» |
| un número pegado al código es código | «{'143 310': '143', '143,00': '143', '143.5': '143'}» |
| dos letras cuentan entre dos palabras | «{'310 MADE IN CHINA': None, '310 PAIS DE ORIGEN': None}» |
| dos letras junto a una palabra no cuentan | «{'310 CHINA (AD)': 'CN'}» |
| un número cuenta como palabra | «{'310 CHINA AD 125': 'CN'}» |
| tres letras no cuentan entre dos palabras | «{'143 PRODUCTO USA ORIGINAL': '143'}» |
| fuera de la tabla, una palabra suelta da el país | «'900 CAROLINA DEL SUR': 'SR'» |
| fuera de la tabla, el nombre no da el país | «At index 0 diff: None != 'REP CENTROAFRICANA'» |
| fuera de la tabla, «NA» es Namibia | «{'900 NA': 'NA'}» |

`catalogo3.sh`: el sabotaje del «４３４» de ancho completo ancla en la línea nueva del lector.

## Revisión

- **`/code-review high`, dos veces.** La primera, sobre `5539cc7a`: la sigla de otro país junto a un
  nombre o un número daba el código («310 CHINA (VN)», «143 US 12»): arreglado (`0d835e0b`); «900 MAR DEL
  PLATA» y «900 NA» con el respaldo por palabra suelta: arreglado. La segunda, sobre `993c8efa`: mi
  arreglo de «MAR DEL PLATA» perdía los alias con paréntesis fuera de la tabla («900 CHINA (MAINLAND)» →
  None): arreglado (`6f5b98a0`), con la familia `900 {nombre}` en el caso.
- **Adversario Sonnet alto** sobre `01c28e83`, sólo el respaldo fuera de la tabla: siglas que son
  abreviaturas (D267, previo); nombres en inglés con un código de la tabla (D266); una sigla entre dos
  palabras no cuenta, «310 SHENZHEN HK PORT» da CN (la regla de «MADE IN USA», a riesgos). Sin país
  equivocado con nombres enteros; probó provincias, Chipre, 20000 palabras (0,04 s).
- **`/security-review`** sobre `2e69a0b1..01c28e83`, a mano y no con subtareas (el producto es una
  función de texto a texto y tres líneas de pantalla): sin hallazgos. El aviso que repite el texto leído
  sale con `CDI.escapeHtml`; el guardado sigue pasando por `origen_valido`.
- **Tu sugerencia del tiempo:** sin el `\W*$`, 30000 caracteres tardan 17 ms («143 » + «CHINA » × 5000);
  «143 » + «- » × 5000, menos de 1 ms. Es lineal: cada palabra mira hasta el nombre más largo del índice.

## Puertas

| puerta | SHA | resultado |
|---|---|---|
| suite completa, worktree limpio | `01c28e83` | «6199 passed, 110 skipped, 3 xfailed, 107 warnings in 1116.59s (0:18:36)», salida 0 (05:47–06:06) |
| `e2e_maria.sh` | `01c28e83` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.», salida 0 |
| `despacho1b.sh` | `01c28e83` | 132 ROJO y «sabotajes sin rojo: 0» (06:06–08:03); salida 1 sólo por los 4 de Postgres «NO CORRIDO | falta PG_DSN», que corrí aparte: abajo |
| `sin_sigla.sh` | `01c28e83` | base «111 passed» y pantalla OK; 16 de 16 ROJO, «sabotajes sin rojo: 0», salida 0 (03:47–03:54) |
| `holanda423.sh` | `01c28e83` | base «111 passed» y «OK: pantalla Holanda→423»; 17 de 17 ROJO, salida 0 (03:54–03:57) |
| `catalogo3.sh` | `01c28e83` | 65 de 65 ROJO, «fallas: 0», salida 0 (hasta 05:29) |
| `anclas_perdidas.py` | `01c28e83` | 2586 anclas, perdida 1, la de la base (`limpieza1.sh:135`) |
| `chequeo-6.py 2e69a0b1` | `01c28e83` | producto +57/−14, un AVISO (las netas, arriba) |
| cruce código × nombre de la tabla | `01c28e83` | 284592 formas, 0 mal (base 154106, `196ef370` 26709) |
| volcado del criterio 4 de la pieza | `01c28e83` | 11348 formas, 0 diferencias con `196ef370` |

Una primera tanda de puertas se cortó por mi tope de tiempo (`despacho1b.sh` a los 60 min, 68 sabotajes en
ROJO y ninguno sin rojo hasta ahí; la suite en 91 %, sin fallas hasta ahí): las relancé enteras, en serie.

Los 4 de Postgres de `despacho1b.sh` (el upsert de `client_memory.py`, que esta pieza no toca) los corrí
con un Postgres 16 descartable y local, con el mismo cambio y las mismas frases que `sabotaje_pg`, contra
`despacho1b_postgres.py` en un worktree de `01c28e83`:
```
BASE  | rc=0 fallas=0 ok=22
ROJO  | el upsert no espera la fila: rc=1 faltan=[]
ROJO  | el upsert no reintenta si la fila se fue: rc=1 faltan=[]
ROJO  | el upsert intenta 2 veces: rc=1 faltan=[]
ROJO  | el upsert que no pudo guardar se calla: rc=1 faltan=[] otras vías OK: True
```
Con tu Postgres, `PG_DSN=postgresql://…` delante de `despacho1b.sh` los corre dentro del guion.

## Comandos

```bash
VENV=/ruta/al/venv   # el tuyo
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider"
# 1. el rojo: producto de 196ef370, pruebas de 01c28e83
R=/tmp/rojo239b; git worktree add -f -q --detach $R 01c28e83 && cd $R && git checkout 196ef370 -- proyecto_maria
$PT tests/test_catalogo3.py -k "otro_pais or sin_sigla" | grep -E "At index|failed"   # «At index 7 diff: None != 'RESTO (AFRICA)'», «1 failed, 1 passed»
cd - >/dev/null; git worktree remove -f $R
# 2. lo de tu devolución y un no dado, sobre 01c28e83: todo None
PYTHONPATH=. $VENV/bin/python -W ignore -c "from proyecto_maria.core.despacho_lector import origen_iso2 as o; print([o(f) for f in ['143 CHINA (MAINLAND)','310 HONG KONG (TERRITORIO DE CHINA)','410 MADEIRA (TERRITORIO DE PORTUGAL)','143,00 310 CHINA','143.5 CHINA','212 ARUBA (TERRITORIO DE PAISES BAJOS)']])"
# 3. sabotajes y §6
PATH=$VENV/bin:$PATH PY=$VENV/bin/python bash scripts/testing/sabotajes/sin_sigla.sh 01c28e83 | tail -1    # «sabotajes sin rojo: 0»
PATH=$VENV/bin:$PATH PY=$VENV/bin/python bash scripts/testing/sabotajes/despacho1b.sh 01c28e83 | tail -1   # «sabotajes sin rojo: 0»; sin PG_DSN sale 1 por los 4 «NO CORRIDO»
python3.12 docs/pm/herramientas/chequeo-6.py 2e69a0b1 01c28e83     # «producto +57/−14», un AVISO (arriba, el porqué)
```

chequeo-6, entero:
```
chequeo-6 2e69a0b1..01c28e83: avisos para mirar, no un veredicto
producto +57/−14
  AVISO producto suma 43 líneas netas: el informe dice por qué (§6: más de 20)
arnés +148/−5
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 899 → 942
  proyecto_maria/static/v2/screens/clientes.js: 2213 → 2213
avisos: 1
```

| commit | qué |
|---|---|
| `eeaca5c8` fix | el país nombrado en cualquier lugar del resto; el código, tres cifras sueltas |
| `fb5a6a69` test | el caso: nombres con signos de la tabla y números que no son código |
| `5539cc7a` test | seis sabotajes nuevos; los del lector siguen a la línea de hoy |
| `0d835e0b` fix | la sigla junto a un nombre o un número; fuera de la tabla, nombre entero; CHANGELOG |
| `c0e0395f`, `00111e37` test | las siglas como familia, «XX 125», tres letras entre palabras |
| `993c8efa` test | sabotajes de la sigla y del nombre entero |
| `6f5b98a0` fix | fuera de la tabla, el nombre con sus signos |
| `ff54a185` test | la familia `900 {nombre}` |
| `01c28e83` test | los sabotajes siguen al índice; «NA». **Lo que se entrega** |
| informe | el commit siguiente |

## Riesgos

- **D266 y D267** (arriba): hasta decidir, un nombre en inglés al lado de un código de la tabla da el
  código sin aviso, y una abreviatura de dos letras fuera de la tabla da un país (como en la base).
- **Una sigla entre dos palabras no cuenta**: «310 SHENZHEN HK PORT» da CN. Es el precio de que «MADE IN
  CHINA» no dé India.
- **None de más, con aviso** (lo aceptado, ahora más ancho): un ISO3 que es palabra («310 POR MAR», «309
  COREA (SUR)», «310 CHINA AND HONG KONG»), «341 HONG KONG (CHINA)», «313 TAIWAN, PROVINCIA DE CHINA»,
  «200 ARGENTINA TIERRA DEL FUEGO», «143 143», dos letras al borde («310 CHINA NO»), «143 ZA» y «143 REP
  SUDAFRICA» (143 y 159 son entradas distintas), «900 CHINA - ORIGEN».
- **Un código al final se ignora**: «143 ORIGEN 310» da 143; puede ser la procedencia pegada.
- **Tres reconocedores de país** (`codigo_de_pais` con nombre, `_origen_desde_factura` y
  `_paises_nombrados`): lo propongo para la cola de limpieza.
- **`test_despacho1b::test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado`** falló una vez
  con dos adversarios corriendo en paralelo y pasó solo (396 passed): es el tope de 0,05 s de CPU que ya
  tenés anotado.
- Lo guardado no se migra; lo de producción no se midió; la CI deselecciona y Railway no la espera.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `d621c6d6`). Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D257 (b) `3c7eb14`), D244 (a) y Holanda→423 sobre `b3a3bf69`. En revisión: D239 (a), vuelta tras la devolución sobre `196ef370`, entregada sobre `01c28e83` (base `2e69a0b1`), informe en el commit siguiente; puertas en «Puertas» de este archivo. Decididos por la PM: D264 (a), D265 (a), supuestos 1 y 2, pérdidas con aviso. Abiertas para la PM: D266 (nombres que ninguna tabla conoce, «310 UNITED STATES» da CN) y D267 (siglas que son abreviaturas fuera de la tabla, «900 SD» da Sudán; previo). Después: D263 (validación mira `origen`, el generador usa `pais_origen`), sin pieza marcada «apenas entregues»: si al despertar no hay nada nuevo, termino la vuelta. D262 (a) está en la cola de limpieza; D261 la lleva la PM. Próxima D: D268. Lecciones (además de las de antes, que siguen en el historial de este archivo): una tarea en segundo plano muere a las 2 h: puertas largas con `setsid nohup` y un vigía que espera una línea en un archivo; `despacho1b.sh` tarda unas 2 h y sin PG_DSN sale 1: Postgres 16 está en /usr/lib/postgresql/16 (initdb y pg_ctl como postgres, en /tmp/cdi-dev2/pg16, puerto 55472); no editar un guion de sabotaje mientras corre; medir `anclas_perdidas.py` y correr el guion del ancla antes de entregar; `/security-review` necesita `origin/HEAD`: ref local temporal y borrarlo; horas, sólo de `date -u`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe.
