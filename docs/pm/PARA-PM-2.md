# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CUIT-GENERAR (D235 a): entregada en `29327d2`. Con un CUIT del despachante que no cierra con su verificador no se genera el TXT, venga del perfil, de `cuit_agr` o del estudio elegido, y el error dice dónde corregirlo. Dos decisiones: D243 y D244

| qué | SHA |
|---|---|
| base (informe de D238) | `3dc9908` |
| producto: `main.py` y `CHANGELOG.md` | `84e0f5e` |
| pruebas de esa primera versión | `6f0199f` |
| producto, arreglo del texto del error (lo encontraron los adversarios) | `6943d3b` |
| pruebas. **Lo que se entrega** | `29327d2` |
| integración de tu rama (sólo `docs/pm/`), después de las puertas | `13633e9` |
| informe | el commit siguiente |

`producto +25/−24` (más 5 líneas de `CHANGELOG.md`). Una función nueva,
`_cuit_del_despachante` (21 líneas, `main.py:4740-4760`), que reemplaza el
bloque que estaba dentro de `generate_maria_endpoint`.

**Lo que tenés que saber antes de publicar:** quien tenga hoy guardado en el
perfil un CUIT de 11 dígitos con el verificador mal deja de poder generar
hasta corregirlo en «Mi perfil». El error se lo dice con el nombre del campo.
Lo mismo con un estudio guardado con un CUIT que no cierra, si existe alguno
(el alta no los guarda desde `8bbfbe6`): el error manda a «Mis estudios». El
conteo de producción lo llevás vos (lo escribiste en D235); sumale la tabla
de estudios.

## Decisiones

**D243. Cuatro sabotajes de la Técnica quedaron sin ancla.** Saqué de
`generate_maria_endpoint` las líneas a las que apuntaban (`effective_cuit_agr
= estudio.cuit if …`, `con_el_perfil = estudio is None and …` y el `if not
_re_cuit.fullmatch…`): ahora esa lógica vive en `_cuit_del_despachante`.
`anclas_perdidas.py` da 6 perdidas de una línea en la base y 10 con la
pieza; las 4 nuevas son
`sabotajes/estudio1.sh:77`, `sabotajes/estudio1b.sh:70` y `:74` y
`sabotajes/excel2.sh:167`. Esos cuatro sabotajes ya no encuentran su patrón
en `main.py` (lo dice `anclas_perdidas.py`; no corrí sus guiones enteros):
los comportamientos siguen cubiertos por sus pruebas
(`test_estudio1` 26, `test_estudio1b` 47 y `test_excel2` 119 passed sobre
`29327d2`), lo que se perdió es el negativo. Hasta que se decida, ningún
guion mide una mutación de la marca «uso del perfil» ni del orden
estudio → `cuit_agr` → perfil. Los tres guiones son de ella y no los toqué.

Dejé medidas las líneas de reemplazo: cada una, aplicada sobre `29327d2`, da
exactamente el rojo que su guion espera.

| guion | ancla nueva (en `main.py`) | sabotaje | rojo medido |
|---|---|---|---|
| `estudio1.sh:77` | `crudo = (estudio.cuit if estudio is not None else cuit_agr) or del_perfil` | `crudo = cuit_agr or (estudio.cuit if estudio is not None else "") or del_perfil` | `1 failed, 25 passed`: `test_el_estudio_elegido_va_al_cddtagr_aunque_haya_perfil_y_cuit_agr` |
| `estudio1b.sh:70` | `es_el_del_perfil = estudio is None and bool(cuit) and cuit == del_perfil` | `es_el_del_perfil = estudio is None and not cuit_agr and bool(cuit)` | `1 failed, 46 passed`: `test_el_cuit_del_perfil_en_cuit_agr_cuenta_como_uso_del_perfil` |
| `estudio1b.sh:74` | la misma | `es_el_del_perfil = estudio is None and bool(cuit)` | `1 failed, 46 passed`: `test_un_cuit_agr_propio_no_cuenta_como_uso_del_perfil` |
| `excel2.sh:167` | `if crudo and not cuit_valido(cuit):` | `if False:` | `6 failed, 113 passed`: los 4 de `test_el_cuit_del_despachante_va_solo_con_11_digitos` y 2 de `test_cuit_del_despachante_o_id_del_vendedor_con_digitos_raros_no_deja_generar` |

- (a) la Técnica cambia esas cuatro anclas con las líneas de la tabla.
- (b) me autorizás a mí a cambiarlas en sus tres guiones, en una pieza chica
  aparte, y corro los tres enteros.
- (c) vuelvo el producto a la forma anterior (el bloque dentro del endpoint)
  para que las anclas viejas sigan valiendo. No lo recomiendo: es darle forma
  al producto por un guion de prueba, y el bloque viejo tenía un `try/except`
  que tapaba cualquier error.
- **Recomiendo (b)** si ella está con otra cosa, (a) si no: son cuatro líneas
  ya medidas. Hasta entonces `anclas_perdidas.py` va a marcar esas cuatro.

**D244. Los avisos de antes de generar no anuncian el CUIT que no cierra, y
tratan distinto un `cuit_agr` en blanco.** Dos cosas del mismo lugar
(`/generate_maria/avisos`, `main.py:~4990`), que no toqué porque tu
definición de la pieza habla de `/generate_maria`:

1. Con un CUIT del despachante que no cierra, los avisos no dicen nada del
   CUIT (sólo avisan cuando falta) y la persona se entera recién al tocar
   «Generar». Medido por el adversario Opus contra una API local: `avisos
   200`, 9 avisos, ninguno del CUIT; `generar 400`. Es el mismo patrón que ya
   tenían los demás rechazos de antes de generar; la pieza suma uno.
2. `/avisos` tiene su propia copia del orden estudio → `cuit_agr` → perfil.
   Para generar, un `cuit_agr` de puros espacios o de puros guiones no cae al
   perfil y da un 400 que nombra «» (ya era así en la base, lo comprobé en el
   diff); para los avisos cuenta como que no vino. Sólo se alcanza por la
   API: la pantalla nunca manda eso. Mi caso «en cuit_agr de puros espacios»
   fija hoy ese 400; con (a) cambia a «Falta el CUIT…» o a generar con el
   del perfil.

- (a) pieza chica aparte: `/avisos` usa `_cuit_del_despachante` (su 400 pasa
  a ser un aviso con el mismo texto) y un `cuit_agr` en blanco cuenta como
  ausente en los dos. Queda una sola copia del orden.
- (b) queda así: el 400 al generar ya dice qué pasa y dónde se corrige.
- **Recomiendo (a)**, sin apuro: saca una copia y evita que alguien revise
  los avisos, no vea nada y se choque con el 400. No la metí acá porque es
  funcionalidad que la tarea no pide (§3).

## Lo que hice distinto de lo que me escribiste (supuestos reversibles)

Me escribiste: «`/generate_maria` saltea esa regla para el CUIT del perfil y
para `cuit_agr` … primero los dos rojos … y el mensaje dice dónde
corregirlo».

1. **El CUIT del estudio elegido también pasa por el verificador.** La base
   ya le pedía 11 dígitos en el mismo `if`; dejarlo afuera era darle al
   estudio una regla más floja que al perfil. Sólo alcanza a un estudio
   guardado antes de que el alta mirara el verificador.
2. **Tres textos de «dónde», no uno.** Según de dónde sale el CUIT malo:
   - del perfil: «Corregilo en «Mi perfil», campo «Mi CUIT (despachante)».»
   - del estudio elegido: «Es el del estudio elegido: en «Mi perfil», «Mis
     estudios», borralo y agregalo de nuevo.» (no hay cómo editar un
     estudio: sólo alta y baja).
   - de `cuit_agr` y distinto del perfil: «No es el de tu perfil: lo mandó
     la operación. Si ya lo corregiste en «Mi perfil», recargá la página.»
     La operación no tiene campo de CUIT; la pantalla manda en `cuit_agr` el
     del perfil que tenía al cargar. El único camino que encontré para
     llegar acá desde la pantalla es una pestaña vieja.
3. **El texto del rechazo que ya existía cambió.** «… tiene que tener 11
   dígitos (0-9). Corregilo en la operación o en tu perfil.» pasó a «… no es
   válido: son 11 dígitos (0-9) y el último es el verificador. …» con el
   «dónde» de arriba. Ninguna prueba anterior fijaba el texto viejo entero
   (la suite completa da verde sin tocar ninguna).
4. **Saqué un `try/except` que tapaba cualquier error** al leer el CUIT del
   perfil (`except Exception: pass`). Con el `user` que entrega la sesión no
   puede fallar; si un día falla, se ve.
5. **Arnés de sabotajes compartido.** `sabotajes/_casos_y_pantalla.sh`
   (nuevo, 95 líneas) lleva lo que `cuit_perfil.sh` y `cuit_generar.sh`
   tenían igual; `cuit_perfil.sh` quedó en sus datos (+3/−93) y sigue
   dando sus 11 rojos. Lo hice para no copiar 90 líneas (§6: lo repetido va
   una vez). No lo monté sobre `_entorno_comun.sh`: ese corre
   `test_entorno1` como base y lo usan cuatro guiones que no son míos.

Lo que no toqué: `cuit_valido` (el `00000000000` sigue pasando, como
dijiste), `/generate_maria/avisos`, `finalize.js`, `profile.js`,
`estudios.js` y los guiones de la Técnica.

## Lo que salió mal

1. **La primera versión mandaba a corregir al lugar equivocado en dos
   casos**, y no lo vi yo: lo encontraron los dos adversarios. Con un
   estudio elegido de CUIT malo, y con una pestaña vieja que manda el CUIT
   anterior del perfil, el error decía «Es el que manda la operación, no el
   de tu perfil: corregilo ahí», y en la operación no hay dónde. Como
   `84e0f5e` y `6f0199f` ya estaban subidos, el arreglo va en commits nuevos
   (`6943d3b`, `29327d2`), con su rojo antes. Además un mutante que no
   miraba el CUIT del estudio pasaba toda la batería: ahora hay un dato y un
   sabotaje para eso.
2. Antes de subir `6f0199f`, mi guion de sabotajes tenía una frase esperada
   que ya no coincidía con el texto final; lo vi al correrlo entero y lo
   corregí antes del commit.
3. El contenedor se reinició en la primera ronda de adversarios y la mató;
   la relancé entera.
4. Una marca de fin vieja en mi scratch hizo que dos esperas volvieran antes
   de tiempo y estuve por leer un registro sin terminar. Lo vi con `ps`,
   borré la marca y esperé de nuevo. Ahora borro la marca antes de lanzar.

## Resultado

**Rojo antes del arreglo** (textos copiados de la salida):

| qué | resultado | lo que dice |
|---|---|---|
| los 12 casos de `29327d2` con `main.py` de `3dc9908`, en un worktree descartable | `7 failed, 5 passed` | los siete de los malos. Seis: `<origen>: 200 {"success":true,…` y `assert 200 == 400` (se generaba el TXT). El de puros espacios ya daba 400 y cae por el texto: `assert {'errors': ['... tu perfil.']} == {'errors': ['... la página.']}` |
| los mismos con `main.py` de `84e0f5e` (la primera versión) | `4 failed, 8 passed` | los tres de `cuit_agr`: `assert {'errors': ['...regilo ahí.']} == {'errors': ['... la página.']}`; el del estudio: `… == {'errors': ['...o de nuevo.']}` |
| la pantalla, con el servidor que sólo cuenta dígitos (el sabotaje 17, igual a la base) | ROJO | `FALLA: con 20999999998 guardado en el perfil se generó el TXT: CDDTAGR=20999999998` |
| los 12 casos, entrega | `12 passed` | |
| `pantalla_cuit_generar1.js`, entrega | `rc=0` | `PANTALLA CUIT-GENERAR-1 OK` |

Los casos (`tests/test_cuit_generar.py`, 94 líneas, dos pruebas con sus
datos):

- **Malos, 7** — de dónde sale el CUIT malo: guardado en el perfil; guardado
  y mandado por la pantalla; guardado con guiones y un espacio; en
  `cuit_agr` con uno bueno en el perfil; en `cuit_agr` con guiones y sin
  perfil; `cuit_agr` de puros espacios; en el estudio elegido con uno bueno
  en el perfil y en `cuit_agr`. Cada uno afirma el 400, el texto entero
  (cuál CUIT y dónde se corrige) y que no quedó ninguna operación contada.
- **Buenos, 5** — qué se usa: el del perfil; `cuit_agr` aunque el del
  perfil sea malo; el estudio aunque los otros dos sean malos; los dos
  verificadores que no salen de «11 − resto» (0 y 9). Cada uno afirma el
  200, el `CDDTAGR` exacto y una operación contada.

Los malos se ponen directo en la base de la prueba: la API ya no guarda uno.

La pantalla (`pantalla_cuit_generar1.js`, 70 líneas, sin esperas fijas): con
el CUIT malo en el perfil, «Generar» termina en el error con el CUIT y el
nombre del campo tal como está en el DOM de «Mi perfil»; se corrige ahí,
«Reintentar» genera y el `CDDTAGR` sale con el bueno.

**La pestaña vieja, corrida aparte sobre `29327d2`** (guion del adversario
con un paso más, en mi scratch; no entra al repositorio, así que no la
podés repetir: lo del servidor lo fija el caso «en cuit_agr, con uno bueno en
el perfil»):

```
perfil en el servidor tras B: "20111111112"
cuit_agr enviado por A: 20999999998 status 400
A ve: error: El CUIT del despachante «20999999998» no es válido: son 11 dígitos (0-9) y el último es el verificador. No es el de tu perfil: lo mandó la operación. Si ya lo corregiste en «Mi perfil», recargá la página.
campos CUIT visibles en A: []
Reintentar: cuit_agr 20999999998 status 400 {"detail":{"errors":["El CUIT del despachante «20999999998» no es válido: son 11 dígitos (0-9) y el último es el verificador. No es el de tu perfil: lo mandó la operación. Si ya lo corregiste en «Mi perfil», recargá la p
tras recargar: cuit_agr 20111111112 status 200 CDDTAGR 20111111112
```

## Negativos

`scripts/testing/sabotajes/cuit_generar.sh 29327d2`: 21 sabotajes, uno por
motivo; 16 contra los casos y 5 contra la pantalla. Salida de las puertas:

```
BASE  | casos: ======================== 12 passed, 5 warnings in 9.70s ========================
BASE  | pantalla: PANTALLA CUIT-GENERAR-1 OK
ROJO  | sólo se cuentan los dígitos: «guardado en el perfil: 200», 6 casos
ROJO  | el del perfil no se mira: «guardado con guiones y un espacio: 200», 3 casos
ROJO  | el que manda la operación no se mira: «sin CUIT en el perfil: 200», 3 casos
ROJO  | el del estudio elegido no se mira: «en el estudio elegido, con uno bueno en el perfil y en cuit_agr: 200», 1 casos
ROJO  | uno de puros espacios cuenta como que falta: «assert 'Falta el CUIT del despachante (CDDTAGR)», 1 casos
ROJO  | se rechaza después de contar la operación: «lo que no se genera no queda contado ni guardado», 7 casos
ROJO  | dónde se corrige, al revés: «recargá la página.']} != {'errors': ['El CUIT del despachante «20999999998»», 6 casos
ROJO  | el del estudio elegido manda a corregir como si lo mandara la operación: «recargá la página.']} != {'errors': ['El CUIT del despachante «20999999998»», 1 casos
ROJO  | uno vacío cuenta como el del perfil: «campo «Mi CUIT (despachante)».']} != {'errors': ['El CUIT del despachante «»», 1 casos
ROJO  | el del perfil guardado con guiones no se reconoce como el del perfil: «recargá la página.']} != {'errors': ['El CUIT del despachante «20999999998»», 1 casos
ROJO  | el del perfil guardado con un espacio en el medio no se reconoce como el del perfil: «recargá la página.']} != {'errors': ['El CUIT del despachante «20999999998»», 1 casos
ROJO  | se nombra como llegó: «assert ['20-11111118 9'] == ['20111111189']», 3 casos
ROJO  | un espacio en el medio queda en el CDDTAGR: «assert ['2011111118 9'] == ['20111111189']», 1 casos
ROJO  | el del perfil manda sobre cuit_agr: «cuit_agr, aunque el del perfil sea malo: 400», 2 casos
ROJO  | el estudio elegido no manda: «el estudio, aunque los otros dos sean malos: 400», 2 casos
ROJO  | el verificador sale siempre de «11 − resto»: «cuit_agr con verificador 0: 400», 2 casos
ROJO  | el servidor sólo cuenta los dígitos: «FALLA: con 20999999998 guardado en el perfil se generó el TXT: CDDTAGR=20999999998»
ROJO  | el error manda a corregirlo en la operación: «la pantalla no dice cuál es ni «Corregilo en «Mi perfil», campo «Mi CUIT (despachante)».»: error: El CUIT»
ROJO  | la pantalla no muestra los errores del servidor: «campo «Mi CUIT (despachante)».»: error: [object Object]»
ROJO  | el campo del perfil se llama de otra manera: «la pantalla no dice cuál es ni «Corregilo en «Mi perfil», campo «CUIT».»»
ROJO  | el CUIT corregido no llega a la operación sin recargar: «FALLA: corregido en «Mi perfil», «Reintentar» terminó en «error: El CUIT del despachante «20999999998»»
sabotajes sin rojo: 0
```

`scripts/testing/sabotajes/cuit_perfil.sh 29327d2` (sobre el arnés
compartido, sin cambios en sus datos):

```
BASE  | casos: ======================== 14 passed, 5 warnings in 9.35s ========================
BASE  | pantalla: PANTALLA CUIT-PERFIL-1 OK
ROJO  | sólo se cuentan los dígitos: «verificador equivocado: 200», 5 casos
ROJO  | no se mira nada: «diez dígitos: 200», 7 casos
ROJO  | el rechazo deja guardado el resto del pedido: «el pedido rechazado no deja nada guardado», 7 casos
ROJO  | uno malo ya guardado pasa si llega igual: «Con el malo», 1 casos
ROJO  | se guarda como llegó: «'20-11111111-2' == '20111111112'», 4 casos
ROJO  | el vacío no lo borra: «'20111111112' == ''», 1 casos
ROJO  | el verificador sale siempre de «11 − resto»: «assert 400 == 200», 2 casos
ROJO  | el servidor sólo cuenta los dígitos: «FALLA: «Mi perfil» guardó 20-99999999-8, que tiene el verificador equivocado»
ROJO  | la pantalla no dice lo que contestó el servidor: «FALLA: con 20-99999999-8 escrito terminó en «error: No se pudo guardar» y no en el error del CUIT»
ROJO  | el campo no queda marcado: «FALLA: el campo del CUIT no queda marcado»
ROJO  | el que ya estaba guardado no se muestra: «FALLA: con 20-99999999-8 ya guardado, el campo muestra «»»
sabotajes sin rojo: 0
```

## Revisión adversarial

Pieza de §3 (datos y validación de lo que sale en el TXT): dos adversarios,
según la tabla. Los dos leyeron y corrieron la primera versión
(`84e0f5e` + `6f0199f`); la versión final la leyeron `/code-review` y la
revisión de seguridad, abajo.

| quién | hallazgo | qué hice |
|---|---|---|
| `adversario-opus-alto` (Opus, alto), corrió | **ningún camino de un CUIT inválido al `CDDTAGR`**: 148 combinaciones estudio × `cuit_agr` × perfil contra la base y contra la pieza; espacios raros, guiones raros, dígitos de ancho completo y arábigos, tipos que no son texto. Un 400 no deja operación, uso del perfil, uso del estudio ni archivo (foto de todas las tablas antes y después) | |
| | media: pestaña vieja → el error mandaba a corregir «en la operación», donde no hay campo | arreglado en `6943d3b`, casos y sabotaje en `29327d2` |
| | baja: estudio con CUIT malo → el mismo texto equivocado | arreglado, ídem |
| | baja: un mutante que no mira el CUIT del estudio pasaba 337 pruebas | dato nuevo en los malos y sabotaje «el del estudio elegido no se mira» |
| | baja: `/avisos` no dice nada del CUIT inválido | D244 |
| | baja: cortar el arnés con TERM al padre durante un sabotaje de casos dejó un directorio en `/tmp` (una vez; no midió frecuencia) | riesgo, abajo |
| `adversario-sonnet-alto` (Sonnet, alto), corrió | media: el estudio elegido sin prueba y con el texto equivocado (lo mismo, por otro camino) | arreglado, ídem |
| | baja: los casos no miran el segundo valor de la función (la marca «uso del perfil»); lo cubre sólo `tests/test_estudio1b.py` | queda: es de ESTUDIO-1b y ahí están sus casos. Ver D243 |
| | baja: `/avisos` | D244 |
| | baja, dato de prueba: `20-11111118-9` (prefijo 20 con resto 1) no es un CUIT que ARCA emita; `cuit_valido` lo acepta | riesgo, abajo. No cambié el dato: prueba la rama `resto == 1 → 9` de la función tal como está |
| | baja: dos arneses comunes (`_casos_y_pantalla.sh` y `_entorno_comun.sh`) | línea propuesta para la cola, abajo |
| | la pantalla y el arnés: no encontró cómo dar verde sin que el producto haga lo que dice; corrió los dos guiones enteros (19 y 11 rojos en esa versión) | |

## `/code-review high` sobre `3dc9908..29327d2`

Los revisores heredan Fable. Seis hallazgos; ninguno pide cambiar el
producto dentro de la pieza.

| # | hallazgo | qué hice |
|---|---|---|
| 1 | cuatro anclas perdidas en guiones de la Técnica | D243 |
| 2 | un `cuit_agr` en blanco o de puros guiones frena el paso al perfil y da 400 con «», mientras `/avisos` lo toma como ausente | D244. Ya era así en la base |
| 3 | `/avisos` no anuncia el rechazo nuevo y tiene su copia del orden | D244 |
| 4 | el tercer texto supone una pestaña vieja; a un cliente de la API, o a un estado que traiga `op.cuit_agr`, recargar no le sirve | queda, riesgo bajo: la primera frase es cierta siempre y la segunda es condicional («Si ya lo corregiste…»). Nada en las pantallas v2 escribe `op.cuit_agr` |
| 5 | `_casos_y_pantalla.sh` repite el preámbulo y `aplicar` de `_entorno_comun.sh` | línea propuesta para la cola |
| 6 | la limpieza de guiones y espacios aparece dos veces en la función | queda: son las dos que ya estaban en el endpoint, movidas, no sumadas. La línea de la cola «una sola limpieza» la cubre |

Sus corridas: los 12 casos; los archivos que tocan `generate_maria`,
`2476 passed, 2 xfailed`; `chequeo-6`, 0 avisos.

## `/security-review` sobre `3dc9908..29327d2`

Un `adversario-opus-alto` (Opus, alto), sólo lectura, con las reglas del
comando (se informa sólo lo de confianza 8 o más). **Ningún hallazgo.** Lo
que miró: el CUIT dentro del texto del error en la pantalla (sale con
`textContent`, `finalize.js:1426-1432`: lo comprobé); el CUIT de un estudio
ajeno (`_estudio_elegido` filtra por dueño antes de la función nueva); qué
deja un 400 (nada: corre antes de contar la operación y de escribir el
archivo); si al mover la lógica se perdió un control (el orden y la limpieza
son los mismos y la regla quedó más estricta); tipos raros; inyección y
secretos. Como no hubo hallazgos, no hubo nada que filtrar.

Una cosa que descartó y dejo anotada: el texto del error va a la telemetría
propia (`CDI.track('maria_generate_error')`, al mismo servidor). El texto
viejo ya llevaba el CUIT (lo comprobé en la base); ahora también va cuando
el CUIT tiene 11 dígitos y no cierra. Es el CUIT del propio usuario.

## Comandos

```bash
# desde la raíz del repo, con esta rama; PY es tu python con las dependencias
export PY=/ruta/al/venv/bin/python
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake
# 1. los casos: «12 passed»
env -u DATABASE_URL -u ENVIRONMENT $PY -m pytest -q --no-cov -p no:cacheprovider tests/test_cuit_generar.py
# 2. el arreglo revertido: «7 failed, 5 passed», seis con «assert 200 == 400»
git worktree add -q --detach /tmp/cg-wt 29327d2
git -C /tmp/cg-wt checkout -q 3dc9908 -- proyecto_maria/main.py
(cd /tmp/cg-wt && env -u DATABASE_URL -u ENVIRONMENT $PY -m pytest -q --no-cov -p no:cacheprovider tests/test_cuit_generar.py)
git worktree remove --force /tmp/cg-wt
# 3. los 21 negativos: «BASE» verde dos veces, 21 líneas «ROJO» y «sabotajes sin rojo: 0» (unos 5 minutos)
env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/sabotajes/cuit_generar.sh 29327d2
# 4. la pantalla sola: «PANTALLA CUIT-GENERAR-1 OK»
SOLO=cuit_generar1 env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/correr_pantallas.sh 29327d2 /tmp/cg-pantalla
# 5. D243: 10 anclas perdidas (6 en la base); las 4 nuevas, de estudio1.sh, estudio1b.sh y excel2.sh
$PY scripts/testing/anclas_perdidas.py 29327d2
# 6. producto y avisos
python docs/pm/herramientas/chequeo-6.py 3dc9908 29327d2
```

## Puertas

Todas sobre `29327d2`, de a una.

| puerta | salida |
|---|---|
| suite completa de pytest | `6143 passed, 110 skipped, 3 xfailed` en 0:19:46, `rc=0`. Son los 6131 de `80cd954` más los 12 casos nuevos |
| `compileall -q proyecto_maria` | `rc=0`, sin salida |
| las pantallas (`correr_pantallas.sh 29327d2`) | `rc=0`, `resumen: 35 verdes, 0 rojas` (las 34 de antes y `cuit_generar1`) |
| `e2e_maria.sh` | `rc=0`, `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `smoke_friccion.sh` contra una API local | `rc=0`, `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido` |
| `ataque_aislamiento.sh` (Postgres 16 local y descartable) | `rc=0`, `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, `PUERTA G3 PASADA. Ningún despachante ve datos de otro.` |
| `sabotajes/cuit_generar.sh 29327d2` | `rc=0`, base verde (`12 passed` y `PANTALLA CUIT-GENERAR-1 OK`), 21 `ROJO`, `sabotajes sin rojo: 0` |
| `sabotajes/cuit_perfil.sh 29327d2` | `rc=0`, base verde (`14 passed` y `PANTALLA CUIT-PERFIL-1 OK`), 11 `ROJO`, `sabotajes sin rojo: 0` |
| `anclas_perdidas.py` | `29327d2`: `perdida, una línea 10 guiones: 8`; base `3dc9908`: `perdida, una línea 6 guiones: 5`. Las de varias líneas, 3 en los dos. Las 4 nuevas son las de D243 |
| `chequeo-6.py 3dc9908 29327d2` | abajo, entera |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |

**No corrí:** los guiones de sabotaje de piezas anteriores (los de la
Técnica de D243 incluidos: sólo medí sus cuatro líneas de reemplazo);
Postgres fuera de `ataque_aislamiento.sh`; nada contra producción. Las
puertas corrieron sobre `29327d2`; la integración de tu rama vino después y
sólo trae `docs/pm/`.

## `chequeo-6`

```
chequeo-6 3dc9908..29327d2: avisos para mirar, no un veredicto
producto +25/−24
arnés +386/−93
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12271 → 12272
avisos: 0
```

## Riesgos

- **Publicar frena a quien tenga un CUIT guardado que no cierra** (perfil o
  estudio). Es lo que pide la pieza; el conteo es tuyo.
- `00000000000` pasa `cuit_valido` (lo dejaste como riesgo). También pasa un
  prefijo 20 con resto 1 y verificador 9, que ARCA no emite. No sé si ARCA
  rechaza alguno de los dos en el `CDDTAGR`: no probado.
- D244: los avisos no anuncian el rechazo y un `cuit_agr` en blanco se trata
  distinto en los dos lugares.
- Una pestaña vieja con un CUIT anterior **bueno** sigue generando con ese,
  aunque el perfil ya tenga otro: `cuit_agr` manda sobre el perfil. Ya era
  así; la pieza no lo cambia.
- El tercer texto («recargá la página») no le sirve a un cliente de la API
  que mande un `cuit_agr` propio y malo: le dice que no es el del perfil, y
  nada más útil.
- `generate_maria_txt` no controla el CUIT por sí sola: el control está en
  el endpoint, que es su único llamador. Otro llamador futuro lo saltea.
- Si la ventana del 25/10 de 02:14 a 02:26 (alta de estudios con 11 dígitos
  y sin verificador, entre `609ec52` y `8bbfbe6`) llegó a desplegarse, puede
  haber estudios guardados con un CUIT que no cierra. No lo sé.
- El arnés de sabotajes, cortado con TERM sólo al proceso padre durante un
  sabotaje de casos, dejó una vez un directorio en `/tmp`. Con Ctrl-C (INT
  al grupo) no deja nada.
- D243: hasta que se decida, cuatro negativos de la Técnica no corren.
- No lo probé con una persona ni en otro navegador que el Chromium de las
  pruebas.

De paso, para vos: `CLAUDE.md` §5 dice que la CI deselecciona tests de
presupuestos compartidos; `.github/workflows/ci.yml:40-49` dice que desde
LIMPIEZA-1 corre la suite entera (`python -m pytest --no-cov`). No lo
corrí en la CI.

## Líneas que propongo para `COLA-LIMPIEZA.md` (no la toco)

- En lugar de «`sabotajes/cuit_perfil.sh` sobre `_entorno_comun.sh`»:
  «`sabotajes/_casos_y_pantalla.sh` y `_entorno_comun.sh` repiten worktree,
  trampa y `aplicar`: un solo arnés común (MARIA, CUIT-GENERAR)».
- «`tests/test_cuit_generar.py`: sumar a los buenos la familia que ARCA sí
  emite con resto 1 (prefijo 23 y verificador 9 o 4). Baja (MARIA,
  CUIT-GENERAR)».

## Archivos de producto que toqué

`proyecto_maria/main.py` (`_cuit_del_despachante`, nueva, y su llamada en
`generate_maria_endpoint`) y `CHANGELOG.md`. De pruebas:
`tests/test_cuit_generar.py`, `scripts/testing/pantalla_cuit_generar1.js`,
`scripts/testing/sabotajes/cuit_generar.sh`, `_casos_y_pantalla.sh` y
`cuit_perfil.sh`.

## Sigo con

Los guiones vencidos de `sabotajes-conocidos.txt`, uno por pieza: primero
`sabotaje_subitems1.sh`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `40de701`). D238 (a) aceptada, D242 (a). D239 y «Holanda» esperan a Emi: no se tocan. CUIT-GENERAR (D235 a) entregada sobre `29327d2` (base `3dc9908`; producto `84e0f5e` y `6943d3b`: `main.py`, `_cuit_del_despachante`; pruebas `6f0199f` y `29327d2`; suite `6143 passed`), con D243 (cuatro anclas de la Técnica perdidas en `estudio1.sh`, `estudio1b.sh` y `excel2.sh`; recomiendo (b)) y D244 (`/generate_maria/avisos` no anuncia el CUIT que no cierra y trata distinto un `cuit_agr` en blanco; recomiendo (a), pieza aparte) sin contestar. Si vuelve con devolución, va primero. Pieza activa: los vencidos de `sabotajes-conocidos.txt`, uno por pieza: primero `sabotaje_subitems1.sh`; después `sabotaje_sufijos1.sh`, que lleva lo que sumó la PM (a `sufijo_otra1`, como dato del mismo caso, la siguiente operación con su propio sufijo guardado: entra sin el aviso de la anterior y con su sufijo en el campo; su rojo: `pintarSufijo` que esconde el aviso sólo cuando el campo entra vacío). Después, los demás vencidos míos. Próxima D: D245. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato, no sólo por el que nombra la tarea. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto y sin consejero.
