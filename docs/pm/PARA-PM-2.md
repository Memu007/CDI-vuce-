# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D149 (a) + CR8 + ids de pytest: entregado en `48195cf` (sólo pruebas)

| qué | SHA |
|---|---|
| base | `b558b66` |
| cuatro guiones cortos (el adelantado, ya integrado sin aceptar) | `f2709a2` |
| patrones al día en `despacho1b`, `cobro_mp2`, `sesion1`, `datos1` (CR8) y `catalogolargo1` | `2e7c880` |
| tu rama traída con `merge` (`a3dae6a`) | `684da1f` |
| la causa que sumaste: ningún patrón depende del id de un texto largo | `ab5b08c` |
| lo que encontró la revisión (largo, NUL, conexiones) | `0f39738` |
| tu rama traída con `merge` (`4e1e618`) | `e248d8a` |
| nota de estado, no era la entrega (este informe la reemplaza) | `862198a` |
| tu rama traída con `merge` (`e4cc761`) | `832bf74` |
| el arnés del perfil espera el foco; `despacho1b` no busca un caso que ya no existe | `bcd1f07` |
| el arnés dice qué pasó si el perfil no se cierra (lo marcó la revisión) | `54ba001` |
| los dos casos de la hoja cara comparan la lista entera de avisos | `4292e0f` |
| tu rama traída con `merge` (`35c19be`) | `c4a1ecb` |
| tu rama traída con `merge` (`a7240cd`) | `393d8aa` |
| `no_debe` de `despacho1b.sh` mira sólo las líneas de resultado — **el que se entrega** | `48195cf` |
| tu rama traída con `merge` (`73b868a`), después de la corrida: sólo `docs/pm` y guiones de CONEXIONES-1 | `f198f4c` |
| informe | el commit siguiente |

**Resultado.** Mis patrones viejos quedan al día y ninguno depende del id
que pytest arma para un texto largo. `despacho1b.sh` entero sobre `48195cf`:
136 `ROJO`, `sabotajes sin rojo: 0`, sale 0. Es la primera corrida entera
limpia de ese guion en esta pieza, y es una sola. Los otros guiones corrieron
sobre SHAs anteriores; por qué valen igual está en «Puertas».

Correr los guiones enteros sacó cuatro rojos que no eran del producto. Los
dos primeros quedan arreglados en `bcd1f07`, el tercero en `4292e0f` y el
cuarto en `48195cf`:

- `sesion1.sh` dio un `ROJO?` por una carrera de foco en mi arnés de pantalla
  (abajo, con la prueba que pediste).
- `despacho1b.sh` dio dos `ROJO?`: dos sabotajes esperaban el caso `[nombre]`,
  que CATALOGO-3 sacó de la prueba. **Se me pasó en `2e7c880`:** mis corridas
  anteriores se cortaron antes de llegar a esos dos sabotajes.
- `despacho1b.sh` entero sobre `54ba001` dio 135 `ROJO` y un `ROJO?` en un
  sabotaje viejo que esta pieza no tocaba («el corte de CPU es una
  Exception»). Es intermitente y la causa es una aserción floja de la prueba
  (abajo, con la prueba del arreglo).
- `despacho1b.sh` entero sobre `c4a1ecb` dio 136 `ROJO` y un `ANCHO` en otro
  sabotaje viejo («aprender no mira los dígitos»). El caso que el guion
  acusaba no falla: el guion buscaba su nombre en toda la salida y pytest lo
  nombra en una advertencia ajena. Es intermitente; lo reproduje con una
  salida guardada (abajo).

Los tres sabotajes de `datos1.sh` que anclaban en un comentario ahora anclan
en código. Producto: **+0/−0**.

## Decisiones

**D168. Quedan anclas de sabotaje que incluyen un comentario.** `/code-review`
marcó siete en líneas que esta pieza no cambió: `sesion1.sh:197`,
`despacho1b.sh:370`, `:422`, `:426`, `:716`, `cobro_mp2.sh:152` y `:256`.
No son un caso suelto. Este grep, que es aproximado y no ve los patrones
partidos en varias líneas, da 35 líneas en 16 guiones, míos y de la Técnica:

```bash
grep -nE "^ +[\$'\"].*( #|//) +[[:alnum:]ÁÉÍÓÚáéíóú]" scripts/testing/sabotajes/*.sh scripts/testing/sabotaje_*.sh | wc -l
```

- (a) Una pieza corta aparte, después de D145, sólo con mis guiones.
- (b) A la cola de limpieza, como una sola entrada para la familia; cada Dev
  la paga cuando vuelve a tocar el guion.
- (c) Dentro de D149: lo reabro y vuelvo a correr los guiones tocados.

**Recomiendo (b).** El riesgo es bajo y ruidoso: si alguien cambia el
comentario, el sabotaje sale `ROTO`, no verde. Reanclar obliga a volver a
correr cada guion (`despacho1b` solo son dos horas), y CR8 como lo escribiste
eran los tres de `datos1`. No toqué `COLA-LIMPIEZA.md`: es tuyo.

**D169. El caso de `sesion1` en `foco_perfil.sh`.** El guion de la Técnica
prueba hoy dos campos de `pantalla_estudio1.js`. Con una línea más en `CASOS`
(`"scripts/testing/pantalla_sesion1.js·#pfEmail"`) también cuida mi arnés.

- (a) La suma la Técnica: el guion es de ella.
- (b) La sumo yo.
- (c) No se suma.

**Recomiendo (a).** No lo toqué. La prueba de abajo la corrí con una copia
fuera del repositorio.

**Supuestos reversibles:**

1. La causa de los ids fue en un commit aparte (`ab5b08c`) y no «en el mismo
   commit» que los patrones: `2e7c880` ya estaba subido cuando llegó tu
   veredicto.
2. Sólo las dos filas largas de `test_disco1.py` llevan `id=` explícito. Mis
   otros cuatro casos cuyo id cambia no tienen ningún patrón que los nombre
   (abajo).
3. `sesion1.sh`: «limpiar abre su propia conexión» esperaba `[login]`, que ya
   no pasa por ahí. Quedó partido en dos sabotajes («limpiar pide otra
   conexión con la del pedido tomada» y «descontar abre su propia conexión»).
4. `sesion1.sh`: sumé el motivo («2 conexiones a la vez») a tres sabotajes
   de conexiones que no eran de esta pieza. Antes esperaban sólo el nombre
   del caso.
5. `despacho1b.sh`: los dos sabotajes del NUL quedaron en uno, anclado en la
   línea que saca el NUL dentro de `_cuerpo_guardable`. Los dos casos que lo
   ven son los mismos.
6. `catalogolargo1.sh`: el sabotaje viejo del historial ya no espera
   guardar-uso, y sumé uno («ninguna memoria controla el largo») que sí lo
   deja en rojo.
7. `pantalla_sesion1.js`: `abrirPerfil` espera que el foco esté en «Mi CUIT»
   antes de escribir. Si el producto deja de poner el foco ahí, el arnés
   falla con «el perfil no terminó de abrir con el foco en «Mi CUIT»» y hay
   que cambiar esa espera.
8. Arreglé el `ROJO?` del corte de CPU dentro de esta pieza, como pediste
   con el de `sesion1`: dos aserciones de `test_despacho1b.py`. La otra
   salida era que el sabotaje pidiera sólo el caso «aparte»; no la tomé
   porque ese caso tiene la misma aserción. Se revierte con `4292e0f`.

## Para reproducir

Con pytest 9.2.0 (`requirements.txt`) y un Postgres 16 local descartable:

```bash
ADMIN=postgresql://cdi@127.0.0.1:55432/postgres
PY=<venv>/bin/python PG_URL=$ADMIN bash scripts/testing/sabotajes/catalogolargo1.sh 48195cf  # 11 ROJO, «fallas: 0», 1,5 min (lo corrí en e248d8a)
PY=<venv>/bin/python PG_URL=$ADMIN bash scripts/testing/sabotajes/disco1.sh 48195cf          # 46 ROJO, «sabotajes sin rojo: 0», 6,5 min (lo corrí en ab5b08c)
PY=<venv>/bin/python bash scripts/testing/sabotajes/datos1.sh 48195cf                        # 20 ROJO, «sabotajes sin rojo: 0», 4 min (lo corrí en ab5b08c)
PY=<venv>/bin/python PG_DSN=$ADMIN bash scripts/testing/sabotajes/sesion1.sh 48195cf         # 39 ROJO, «sabotajes sin rojo: 0», 30 min (lo corrí en 54ba001)
PY=<venv>/bin/python PG_DSN=$ADMIN bash scripts/testing/sabotajes/despacho1b.sh 48195cf      # 136 ROJO, «sabotajes sin rojo: 0», sale 0, 2 h 17 min
python docs/pm/herramientas/chequeo-6.py b558b66 0f39738                                     # producto +0/−0, avisos: 0
python docs/pm/herramientas/chequeo-6.py 832bf74 54ba001                                     # producto +0/−0, arnés +9/−3, avisos: 0
python docs/pm/herramientas/chequeo-6.py 54ba001 4292e0f                                     # producto +0/−0, arnés +2/−2, avisos: 0
python docs/pm/herramientas/chequeo-6.py 393d8aa 48195cf                                     # producto +0/−0, arnés +3/−2, avisos: 0
```

Sobre `48195cf` corrió sólo `despacho1b.sh`. Por qué los otros valen igual
está abajo, en «Puertas».

El rojo de tu causa, con el guion de antes:

```bash
git show 2e7c880:scripts/testing/sabotajes/disco1.sh > /tmp/disco1_viejo.sh
PY=<venv>/bin/python PG_URL=$ADMIN bash /tmp/disco1_viejo.sh 2e7c880   # 44 ROJO y 2 «ROJO?» que piden «…[BBBB», 6 min
```

La prueba del arreglo del foco, con el reloj de la Técnica (su guion no se
toca: se copia y se le cambia la lista de casos):

```bash
sed '/pantalla_estudio1.js·#pfEstudioNombre/d; s|pantalla_estudio1.js·#pfEstudioCuit|pantalla_sesion1.js·#pfEmail|' \
  scripts/testing/foco_perfil.sh > /tmp/foco_sesion1.sh
PY=<venv>/bin/python bash /tmp/foco_sesion1.sh 832bf74   # PIERDE … lo escrito cayó en «Mi CUIT», sale 1
PY=<venv>/bin/python bash /tmp/foco_sesion1.sh 54ba001   # NO PIERDE, sale 0
```

## Puertas (todas con pytest 9.2.0)

| guion | sobre | salida |
|---|---|---|
| `catalogolargo1.sh` | `e248d8a` | 11 `ROJO`, `fallas: 0`, 87 s |
| `sesion1.sh` | `54ba001` | 39 `ROJO`, `sabotajes sin rojo: 0`, sale 0, 1805 s |
| `despacho1b.sh` | `54ba001` | 135 `ROJO`, 1 `ROJO?` (el del corte de CPU), `sabotajes sin rojo: 1`, sale 1, 8271 s |
| `despacho1b.sh` | `c4a1ecb` | 136 `ROJO`, 1 `ANCHO` (abajo), `sabotajes sin rojo: 1`, sale 1, 8307 s |
| `despacho1b.sh` | `48195cf` | 136 `ROJO`, `sin Postgres, no corridos: 0`, `sabotajes sin rojo: 0`, sale 0, 8202 s |
| `foco_perfil.sh` con mi caso (copia) | `832bf74` | `PIERDE`, sale 1 |
| ídem | `bcd1f07` y `54ba001` | `NO PIERDE`, sale 0 |
| `disco1.sh` | `ab5b08c` | 46 `ROJO`, `sabotajes sin rojo: 0`, 388 s |
| `datos1.sh` | `ab5b08c` | 20 `ROJO`, `sabotajes sin rojo: 0`, 237 s |
| `cobro_mp2.sh`, **reducido** (abajo) | `ab5b08c` | `BASE  \| en verde`, 1 `ROJO`, `sabotajes con falla: 0`, 214 s |
| `maria1b.sh` | `ab5b08c` | 34 `ROJO`, `sabotajes con falla: 0`, 523 s |
| `entradas1.sh` | `ab5b08c` | 32 `ROJO`, `sabotajes con falla: 0`, 822 s |
| `abuso1.sh` | `ab5b08c` | 34 `ROJO`, `sabotajes sin rojo: 0`, 886 s |
| `disco1.sh` de `2e7c880` (el rojo de la causa) | `2e7c880` | 44 `ROJO`, 2 `ROJO?` sin «…[BBBB», 372 s |
| chequeo-6 `b558b66 0f39738`, `832bf74 54ba001`, `54ba001 4292e0f` y `393d8aa 48195cf` | | abajo |

**Lo que no corrió sobre el SHA entregado.** Los seis guiones que corrieron
sobre `ab5b08c` y `catalogolargo1.sh` (sobre `e248d8a`) no cambiaron después,
ni sus pruebas. Entre `ab5b08c` y `48195cf` el producto cambia sólo en
`app_v2.js` (16 líneas, de tu merge); lo demás que cambia son pruebas y
arneses de otras piezas. Ninguno de esos siete guiones nombra un archivo de
esa lista:

```bash
git diff ab5b08c 48195cf --stat -- proyecto_maria tests scripts/testing
```

`sesion1.sh` y la prueba del foco corrieron sobre `54ba001`. Entre `54ba001`
y `48195cf` cambian las dos líneas de `tests/test_despacho1b.py`, las tres de
`no_debe` en `despacho1b.sh` y, por tus merges, los guiones de CONEXIONES-1
de la Técnica; el producto no cambia:

```bash
git diff 54ba001 48195cf --stat -- proyecto_maria tests scripts/testing
```

Después de la corrida traje tu rama (`73b868a`) en `f198f4c`. Fuera de
`docs/pm` suma ocho archivos `scripts/testing/conexiones1_*` de la Técnica y
nada más:

```bash
git diff 48195cf f198f4c --stat -- . ':!docs/pm'
```

```
chequeo-6 b558b66..0f39738: avisos para mirar, no un veredicto
producto +0/−0
arnés +65/−62
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

```
chequeo-6 832bf74..54ba001: avisos para mirar, no un veredicto
producto +0/−0
arnés +9/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

```
chequeo-6 54ba001..4292e0f: avisos para mirar, no un veredicto
producto +0/−0
arnés +2/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

```
chequeo-6 393d8aa..48195cf: avisos para mirar, no un veredicto
producto +0/−0
arnés +3/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Sobre la base entera el chequeo incluye tus merges:

```
chequeo-6 b558b66..48195cf: avisos para mirar, no un veredicto
producto +7/−9
arnés +1268/−174
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/app_v2.js: 1201 → 1199
  AVISO creció una función de más de 150: scripts/testing/pantalla_cliente1.js:27 <anónima> 296 → 297, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

El `producto +7/−9` y el `AVISO` vienen de tus merges (BORRADOR-1 y los
arneses de la Técnica), no de esta pieza: ningún commit mío toca `app_v2.js`
ni `pantalla_cliente1.js`.

**Los rojos de lo que encontró la revisión**, una vez, en un worktree aparte
sobre `ab5b08c`:

| cambio en el producto | salida |
|---|---|
| `validar_largo` sin pasar a NFC | `6 failed, 7 passed`: entre ellos `guardar_uso…[nfd-que-achica]` y `[nfc-que-crece]` |
| `validar_largo` con `if False:` | `7 failed, 6 passed`: entre ellos `guardar_uso…[2001]` y `[nfc-que-crece]` |
| `_cuerpo_guardable` sin `data = _sin_nul(data)` | `2 failed, 283 passed`: `test_guardar_saca_el_nul_de_los_textos` y `…en_mayusculas[nul]`; `[minusculas]` sigue verde |
| los cuatro sabotajes de conexiones de `sesion1.sh` | cada uno falla con «2 conexiones a la vez», no con un 500 |

## El `ROJO?` de `sesion1`

**Lo que salió**, sobre `e248d8a` (38 `ROJO`, 1 `ROJO?`):

```
ROJO? | la pantalla manda el PUT sin clave: rojo (salida 1), pero sin «FALLA: sin clave»
FALLA: cambiar el email no muestra el campo de la clave
```

**Cuál de las dos causas.** Esa corrida no registró el estado de la pantalla:
no puedo probar cuál fue. Lo que medí después apunta al foco (la tuya), y las
dos existen en el arnés de antes:

| arnés | qué le hice a la página | resultado |
|---|---|---|
| el de `832bf74` | nada, 3 corridas | verde las 3; el foco demorado de la primera apertura cae 37, 19 y 23 ms antes de que el arnés entre a `#pfEmail` |
| el de `832bf74` | ese foco se dispara cuando el arnés entra a `#pfEmail`, 2 corridas | las 2 con el texto del `ROJO?` (estado abajo) |
| el de `832bf74` | la página atiende 60 ms tarde la respuesta del guardado | falla por el cierre tardío: modal escondido, `TimeoutError: page.click` |
| sólo con la espera del foco | ídem | falla igual: modal escondido, `TimeoutError: page.fill` |
| el entregado | las tres cosas | verde |

```
ESTADO: {"foco":"pfCuit","pfCuit":"otro-ses1_1794456514471@ejemplo.test","pfEmail":"ses1_1794456514471@ejemplo.test","modalVisible":true,"isOpen":true}
FALLA: cambiar el email no muestra el campo de la clave
```

- **Foco.** `fill` enfoca el campo y después escribe en lo que tenga el foco.
  El perfil pone el foco en «Mi CUIT» 150 ms después de cargar; si cae en el
  medio, el email nuevo queda en «Mi CUIT». Da el texto exacto del `ROJO?` y
  alcanza con que el arnés se atrase unos 20 a 40 ms.
- **Cierre tardío** (mi hipótesis). Al guardar, el modal se esconde 130 ms
  después del cierre. En limpio el cierre corre entre 4 y 10 ms antes de que
  el arnés reabra y no molesta. Si corre después, esconde el modal reabierto.
  Con la demora puesta a mano dio `TimeoutError`, no el texto del `ROJO?`;
  para dar ese texto el arnés tendría que atrasarse además unos 85 ms.

En una corrida anterior de la tercera fila, que no guardé en un log, perdió
por el foco y no por el cierre: con esa demora puede salir cualquiera de las
dos.

**El arreglo** (`pantalla_sesion1.js`, `abrirPerfil`): antes de abrir espera
que el modal anterior esté escondido; antes de escribir espera el email
cargado y el foco en «Mi CUIT». Son condiciones observables, sin espera
fija. `profile.js` no se tocó.

**La prueba que pediste** (rojo siempre con el arnés de antes, verde con el
arreglado), con el reloj de `foco_perfil.sh`:

```
832bf74: PIERDE      | scripts/testing/pantalla_sesion1.js·#pfEmail: lo escrito cayó en «Mi CUIT» (robado=%23pfEmail&valor=++SES1_1794455795227%40EJEMPLO.TEST+) · focos: foco=campo&ms=50
         FALLA: TimeoutError: page.waitForResponse: Timeout 30000ms exceeded while waiting for event "response"
54ba001: NO PIERDE   | scripts/testing/pantalla_sesion1.js·#pfEmail · focos: foco=reloj&ms=3001 foco=reloj&ms=3000 foco=reloj&ms=3000
```

En `54ba001` los tres focos los dispara el reloj a los 3 s: el arnés espera
el foco en las tres aperturas y recién después escribe.

Las mediciones de la tabla salen de un armado mío fuera del repositorio
(sirve el producto, cambia los tiempos de la página y registra el estado al
fallar). Lo que podés repetir vos es la prueba con el reloj.

## El `ROJO?` de `despacho1b`

**Lo que salió**, sobre `54ba001`:

```
ROJO? | el corte de CPU es una Exception: rojo (salida 1), pero sin «FAILED tests/test_despacho1b.py::test_una_sola_hoja_cara_se_corta_en_el_tope_de_cpu»
FAILED tests/test_despacho1b.py::test_el_lector_aparte_corta_una_sola_hoja_cara
```

Sobre `e248d8a` ese mismo sabotaje había dado `ROJO`.

**La causa.** No es del producto: el caso pedía el aviso del corte con `in`.
Con el sabotaje, el corte es una `Exception` y el `except Exception` de la
hoja se lo traga: queda «No pude leer la hoja 1.». El temporizador repite. Si
otro disparo se atiende después de ese `except` y antes del desarme, sale por
afuera de la hoja y suma «El PDF da demasiado trabajo: leí hasta la hoja 0.».
Con los dos avisos, el `in` se cumple y el caso pasa.

**Medido**, con un plugin de pytest mío fuera del repositorio que anota dónde
cae cada corte, sobre `tests/test_despacho1b.py` entero:

| sabotaje | aserción | temporizador | avisos | caso |
|---|---|---|---|---|
| no | la de antes | normal | sólo el del corte | pasa (`285 passed`) |
| sí | la de antes | normal, 27 lecturas | 25 veces sólo «No pude leer la hoja 1.»; 2 veces los dos | las 25 con resumen de pytest: falla (`4 failed, 281 passed`) |
| sí | la de antes | repetición forzada a 4 ms, 2 corridas | los dos, las 2 | **pasa** (`3 failed, 282 passed`) |
| sí | la nueva | repetición forzada a 4 ms, 3 corridas | los dos, las 3 | **falla** (`4 failed, 281 passed`) |
| sí | la nueva | normal, 1 corrida | sólo «No pude leer la hoja 1.» | falla |
| no | la nueva | normal | sólo el del corte | pasa (`285 passed`) |

En las dos lecturas naturales con los dos avisos, el primer corte se atendió
a los 0,451 s dentro de pypdf y el segundo a los 0,459 s en
`despacho_lector.py:377`, ya fuera del `try` de la hoja.

Lo que no tengo:

- De esas dos lecturas no quedó el resumen de pytest: una la corté yo y de
  la otra no sé por qué falta. Que el caso pasa con esos avisos lo muestran
  las corridas forzadas y el `ROJO?` del guion.
- El temporizador repite cada 50 ms y los dos cortes quedaron a 8 ms. No
  medí por qué el primero se atendió tarde.
- Una primera ronda de 16 corridas no vale como frecuencia: el plugin
  tenía un defecto que cambiaba dónde caía el corte. No la uso.

El mensaje de `4292e0f` dice «1 de 26 corridas naturales»: lo conté antes
de que terminara la tanda. La cuenta final es la de la tabla, 2 de 27. El
commit ya estaba subido y no se reescribe.

**El arreglo** (`4292e0f`, dos líneas de prueba, producto +0/−0): los dos
casos de la hoja cara comparan la lista entera de avisos. El caso «aparte»
tenía la misma aserción y lee con el mismo código en el proceso hijo; ahí no
forcé el segundo corte, porque el plugin no entra al hijo.

**La prueba que pediste para el otro `ROJO?`**, acá: con el sabotaje y la
forma que antes pasaba (los dos avisos), la aserción de antes pasa 2 de 2 y
la nueva falla 3 de 3; sin sabotaje, verde. No es repetible con los guiones
del repositorio: el segundo corte se fuerza con mi plugin. Lo que podés
repetir es `despacho1b.sh` entero.

**Lo que esto no prueba:** que no quede otro sabotaje intermitente en
`despacho1b.sh`. Una corrida entera sin `ROJO?` no lo demuestra.

## El `ANCHO` de `despacho1b`

**Lo que salió**, sobre `c4a1ecb` (136 `ROJO`, 1 `ANCHO`, sale 1):

```
ANCHO | aprender no mira los dígitos: también «test_un_ncm_con_otros_digitos_da_400_por_cada_via[operacion-arabigo]»
```

El mismo sabotaje dio su `ROJO` en esa corrida, y en las enteras sobre
`e248d8a` y `54ba001` no dio `ANCHO`.

**La causa.** No es del producto ni del caso: es de `no_debe`, que buscaba el
nombre del caso prohibido en toda la salida de pytest. Pytest también nombra,
en su resumen de advertencias, al caso que estaba corriendo cuando un hilo de
aiosqlite de un caso anterior termina con «Event loop is closed»
(`PytestUnhandledThreadExceptionWarning`). El caso pasa y el guion lo acusaba.

**Medido.** El guion tira la salida de pytest después de juzgarla, así que la
de esa corrida no quedó. Puse el mismo sabotaje a mano en un worktree aparte
sobre `c4a1ecb` y guardé cada salida:

| corridas | `FAILED` | lo que nombran las advertencias |
|---|---|---|
| 13 del archivo entero | siempre los mismos 3 (`[aprender-arabigo]`, `[aprender-ancho completo]`, `[aprender-mezclado]`); ningún `ERROR` | en las 13, algún caso que pasó; en 1, `[operacion-arabigo]`; en otra, `[operacion-ancho completo]` |
| 68 sólo de ese caso (`-k`) | los mismos 3 en las 68 | en 6, algún caso de la familia que pasó (2 veces `[operacion-mezclado]`) |

**El arreglo** (`48195cf`, tres líneas del guion, producto +0/−0): `no_debe`
busca `FAILED <archivo>::<caso>` o `ERROR <archivo>::<caso>`, como ya hacía
`juzgar` con los que tienen que fallar. Las 27 llamadas pasan nombres de
caso; ninguna quedó sin poder coincidir.

**La prueba que pediste para el otro `ROJO?`**, acá: sobre la salida guardada
donde la advertencia nombra a `[operacion-arabigo]` (`3 failed, 282 passed`),
la llamada de `no_debe` de ese sabotaje, tal cual está en el guion:

| guion | salida |
|---|---|
| el de `c4a1ecb` | `ANCHO \| aprender no mira los dígitos: también «…[operacion-arabigo]»` |
| el de `48195cf` | nada |
| el de `48195cf`, prohibiendo `[aprender-arabigo]`, que sí falló | `ANCHO` |
| el de `48195cf`, con una línea `ERROR …[operacion-arabigo]` agregada a mano a la salida | `ANCHO` |

Para repetirlo con una salida tuya (el sabotaje puesto a mano, y `<caso>` uno
que pasó y que el «warnings summary» nombra; en mis 13 corridas siempre hubo
alguno):

```bash
T=tests/test_despacho1b.py; FALLAS=0
eval "$(git show c4a1ecb:scripts/testing/sabotajes/despacho1b.sh | sed -n '/^no_debe() {/,/^}/p')"; no_debe antes "$(cat <salida>)" '<caso>'   # ANCHO
eval "$(git show 48195cf:scripts/testing/sabotajes/despacho1b.sh | sed -n '/^no_debe() {/,/^}/p')"; no_debe ahora "$(cat <salida>)" '<caso>'   # nada
```

**Lo que esto no prueba:**

- Que la salida de la corrida sobre `c4a1ecb` tuviera esa advertencia: no
  quedó guardada. Lo que hay es que el caso no falló en ninguna de 81
  corridas con el sabotaje y que la advertencia lo nombró en 1 de 13 enteras.
- Que no quede otro intermitente en el guion. Las dos corridas enteras
  anteriores dieron uno distinto cada una; la de `48195cf` salió limpia, y
  es una sola.

El guion sigue tirando la salida de pytest. Con el arreglo ya no hace falta
para un `ANCHO`: sólo sale si hay una línea de resultado.

## Los ids de pytest

Con 9.2.0 cambian 8 ids de 6155 respecto de 9.1.1 (comparé las dos listas
de `--collect-only`). Son de `test_disco1.py` (2), `test_estudio1.py`,
`test_maria1a_lectura_factura.py`, `test_maria8_subitems_por_posicion.py`,
`test_org1.py`, `test_subitems1.py` y `test_valor1c.py`.

De todos los guiones de sabotaje, sólo dos nombran uno de esos ids:

- `disco1.sh` líneas 200 y 227 (mío): arreglado. Las dos filas llevan
  `id="descripcion-de-2001"` y el guion busca ese id.
- `estudio1.sh:134` (de la Técnica): no lo toqué. Ella lo arregló y llegó
  con tu merge: en `bcd1f07` busca `[largo]`.

## Qué cambió en cada guion

- `despacho1b.sh`: once patrones al día (medio par, NUL, resumen, origen) y
  la expresión regular del sufijo. En `bcd1f07`, «el PUT no valida el
  origen» y «el origen se mira en mayúsculas» ya no esperan `[nombre]`.
- `pantalla_sesion1.js`: la espera de `abrirPerfil` (arriba).
- `sesion1.sh`: revocar, email y los sabotajes de conexiones (supuestos 3 y 4).
- `cobro_mp2.sh`: un sabotaje apuntaba a `main.py` y la línea está en
  `config.py`.
- `datos1.sh`: CR8, tres anclas pasan de comentario a código.
- `catalogolargo1.sh`: supuesto 6, y el ancla del arranque al día.
- `disco1.sh` y `test_disco1.py`: los ids.
- `maria1b.sh`, `entradas1.sh`, `abuso1.sh`: en `f2709a2`.

**Para la cola de limpieza, si te sirve:** guardar-uso controla el largo de
la descripción dos veces (`main.py:10487` con `texto_para_guardar` y
`main.py:10498` con `_problema_historial`). Por eso el sabotaje del
historial solo no lo ponía en rojo.

## Revisión

| quién | hallazgo | qué hice |
|---|---|---|
| adversario Sonnet, esfuerzo medio | medio: `catalogolargo1.sh` perdió la expectativa de guardar-uso | arreglado en `0f39738` |
| ídem | bajo-medio: en `sesion1.sh`, «limpiar…» podría fallar por un 500 y no por la conexión | lo corrí: falla por «2 conexiones a la vez». Igual fijé el motivo en el guion |
| ídem | bajo: se fue `test_resetear_clave_revoca_todas_las_sesiones` de un sabotaje | queda: el reseteo ya no pasa por `revocar_sesiones` |
| `/code-review high` (hereda el modelo de la sesión) | 1 y 2: los mismos dos de arriba | arreglados |
| ídem | 3: los dos sabotajes del NUL de `despacho1b.sh` sacaban tres reglas juntas | arreglado: uno solo, sobre la línea del NUL |
| ídem | 4: siete anclas con comentario en líneas que no cambié | D168 |
| adversario Sonnet, esfuerzo medio, sobre `0f39738` y `bcd1f07`, sólo leyendo | medio: la espera de que el modal se esconda fallaba con un `TimeoutError` sin mensaje | arreglado en `54ba001`. Rojo con una copia donde el modal no se puede esconder: `FALLA: el perfil no terminó de cerrarse` |
| ídem | medio: el arnés ya no tropieza con el foco que le roba el texto a quien escribe rápido | queda: es el defecto de `profile.js` que ya está en la cola; el arnés lo encontraba sólo por azar |
| ídem | bajo: un solo sabotaje del NUL para las cuatro rutas que pasan por `_cuerpo_guardable` | queda: el control está una vez, en esa línea (supuesto 5) |
| ídem | bajo: «2 conexiones a la vez» fija el número | queda: si fueran 3 saldría `ROJO?`, no verde |
| adversario Sonnet, esfuerzo medio, sobre `4292e0f`, sólo leyendo | nada contra la aserción nueva: en base no encontró otro aviso posible ni un `except` de pypdf que se trague el corte; con el sabotaje, no encontró camino por el que el caso pase | — |
| ídem | bajo, hipótesis, del producto y sin cambio en esta pieza: en `_tope_de_cpu`, un disparo entre la entrada al `finally` y `leyendo = False` saltearía el desarme | no lo toqué ni lo probé: riesgo abajo |
| adversario Sonnet, esfuerzo medio, sobre `48195cf`, sólo leyendo el guion y las salidas guardadas | nada contra el `no_debe` nuevo: no encontró un caso prohibido que falle y no dé `ANCHO` (error de preparación o de cierre sale como `ERROR`; si pytest corta antes del resumen, `juzgar` da `ROJO?`), ni una de las 27 llamadas que deje de coincidir, ni el mismo defecto en otro lugar del guion | — |
| ídem | bajo, texto: el comentario nuevo es cierto pero genérico (no dice que la advertencia es la del resumen de pytest) | queda: cambiarlo movía el SHA y la corrida entera es sobre este |
| ídem | bajo, hipótesis: `no_debe` y `juzgar` dependen de que `T` sea la ruta que imprime pytest | queda: hoy coincide (136 `ROJO`); si dejara de coincidir, `juzgar` daría `ROJO?` en todos, no verde |

`/code-review` y el primer adversario miraron `b558b66..ab5b08c`; el segundo,
`0f39738` y `bcd1f07`; el tercero, `4292e0f`; el cuarto, `48195cf`.
`54ba001` (una línea) lo revisé sólo yo. `/code-review` no volvió a correr
sobre las dos líneas de `4292e0f` ni sobre las tres de `48195cf`.

## Cortes y demoras

- A las 03:43 UTC el contenedor se reinició y cortó `despacho1b.sh` sobre
  `e248d8a` en el sabotaje 129 de 136 (127 `ROJO`, los 2 `ROJO?` de
  `[nombre]`, 7 sin correr). Lo volví a correr entero sobre `54ba001`.
- Corté a mano la tanda sobre `bcd1f07` a los 9 minutos (8 `ROJO`, ninguno
  sin rojo) para sumar el arreglo de `54ba001` y correr todo sobre el SHA
  que se entrega.
- Mi estimación de entrega anterior quedó corta por eso y por los cuatro
  rojos. El tercero y el cuarto sumaron cada uno su diagnóstico y otra
  corrida entera de `despacho1b.sh` (8307 s sobre `c4a1ecb` y 8202 s
  sobre `48195cf`).

## No corrido

- **`cobro_mp2.sh` entero** (unas 3 h 15 min). Corrí una copia reducida: la
  base y el único sabotaje que cambió.
- **La suite completa.** La pieza toca guiones de sabotaje, el arnés
  `pantalla_sesion1.js`, `test_disco1.py` (+3/−2) y dos líneas de
  `test_despacho1b.py`; cada archivo corre
  entero dentro de su guion.
  La última suite completa es la de `f36cc83`, con pytest 9.1.1.
- `/security-review`, smoke y ataque de aislamiento: no hay producto tocado.

## Tu aviso sobre la subida pública de PDF

No tengo nada abierto en esa ruta ni en `require_billing_vigente`.

## Riesgos

- Bajo: los ids de mis otros cuatro casos largos siguen dependiendo de la
  versión de pytest. Hoy ningún guion los nombra.
- Bajo: D168.
- Bajo: el arnés del perfil depende de que el foco caiga en «Mi CUIT»
  (supuesto 7).
- Bajo: `foco_perfil.sh` no cuida todavía mi arnés (D169).
- Bajo: si una lectura cortada por CPU suma algún día otro aviso legítimo,
  los dos casos de la hoja cara fallan en base. Es un rojo ruidoso, no un
  verde falso.
- Bajo: la advertencia de aiosqlite («Event loop is closed») sale en cada
  corrida entera de `tests/test_despacho1b.py`, con y sin sabotaje. Es ruido
  de las pruebas, no un fallo; no busqué de qué caso viene. Si querés, a la
  cola de limpieza.
- Bajo, del producto y sin probar: la hipótesis del revisor sobre el
  `finally` de `_tope_de_cpu` (tabla de revisión). Si te interesa, es una
  pieza aparte: no entra en una de sólo pruebas.

## D167

Volví a compactar desde el informe anterior. El resumen cita logs por
ruta; este informe no copia las salidas largas.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 73b868a), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. D149 (a) + CR8 + ids de pytest entregado en 48195cf (informe en el commit siguiente), esperando veredicto; abiertas D168 (anclas con comentario) y D169 (sumar mi arnés a foco_perfil.sh). Sigue D145 (a): cada sabotaje de mis arneses registra con su propio X-Forwarded-For; abuso1 queda con una sola IP; cliente1, foco_cliente1, destino1 y despacho1a son de la Técnica. Próxima D libre: D190. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
