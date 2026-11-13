# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## AJUSTE-BORRADOR: entregada en `d094c24`. Reprodujo en rojo y está arreglada. `pytest` entero da 1 rojo que no es de esta pieza: lo trae EXCEL2D-RELOJ. Dos decisiones: D227 y D234

Integré tu rama dos veces: hasta `e3b169e` (merge `6152e9e`), donde leí
valor1 aceptada y la línea que le sumaste a esta pieza («cubre también
D222»), y hasta `23967c9` (merge `d094c24`), que no cambia mi canal. Tus
commits propios tocan sólo `docs/pm/`; lo de `tests/` y `scripts/` viene de la
Técnica, ya aceptado por vos. Sigo con el lugar 2, **CUIT-PERFIL (D225)**.

**Antes que nada: `pytest` entero sobre `a7511e0` no dio verde.**
`1 failed, 6110 passed, 110 skipped, 3 xfailed`. El rojo es
`tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas]`
y no sale de esta pieza: lo trae EXCEL2D-RELOJ (`f75cb48`, de la Técnica), que
llegó con tu rama. En este contenedor dio rojo las 2 veces que corrí la
suite entera; tu `NOW.md` dice que la CI dio verde. Está diagnosticado, con la
causa reproducida, en **D234**. Todas las demás puertas dieron verde.

| qué | SHA |
|---|---|
| base (mi informe anterior) | `a647bee` |
| el caso de pantalla, rojo sobre el código de hoy | `a57b584` |
| el arreglo (producto + `CHANGELOG.md`) | `c4620ca` |
| una aserción en pytest y el mensaje del caso | `1323fdc` |
| tu rama integrada | `6152e9e` |
| el caso de pytest con los dos campos; sobre éste corrieron las puertas | `a7511e0` |
| tu rama otra vez, hasta `23967c9`: **el que se entrega** | `d094c24` |
| informe | el commit siguiente |

**Resultado.**

- **Tu lectura era correcta y reproduce en un navegador.** Sobre `a57b584`
  (producto igual a `a647bee`), `pantalla_ajuste1.js` escribe «abc» en Ajustes
  a incluir y «1,500» en Ajustes a deducir, recarga, la operación se recupera
  y vuelve a la validación:

  ```
  FALLA: el aviso dice «Ajustes a incluir: no es un número. Ajustes a deducir: ¿1.500 o 1,5? Escribilo con punto de miles (1.500) o como 1,5. Ajustes a incluir: «abc» no es un importe.» y el campo de Ajustes a incluir: muestra «», no «abc»
  FALLA: el aviso dice «Ajustes a incluir: no es un número. Ajustes a deducir: ¿1.500 o 1,5? Escribilo con punto de miles (1.500) o como 1,5. Ajustes a incluir: «abc» no es un importe.» y el campo de Ajustes a deducir: muestra «», no «1,500»
  ```

- **El arreglo es tu sugerencia: salieron las dos guardas** de `pintarValor`
  (`finalize.js:451` y `:454`). Con la página viva no hacían nada: el campo le
  escribe a la operación en cada tecla (`:341–346`), así que siempre coinciden.
  Sólo cambiaban algo con el campo recién creado, que es el defecto.
  Producto **+4/−4** (dos condiciones más cortas y el comentario que las
  explicaba, reescrito).
- Sobre `a7511e0` el caso da verde:
  `OK Ajustes a incluir: el campo muestra «abc» después de recargar`,
  `OK Ajustes a deducir: el campo muestra «1,500» después de recargar`,
  `PANTALLA AJUSTE-1 OK`.
- **D222, lo que quedaba.** Las guardas sin sabotaje ya no existen. El «a la
  vista» ahora tiene negativo, en pytest, que es lo que corre la CI:
  - caso nuevo `test_un_ajuste_mal_escrito_se_ve_en_el_campo_que_llega_vacio`
    (los dos campos como datos). Con el `finalize.js` de `a647bee`:
    `1 failed, 75 passed`, `{'valorIncluir': ''} != {'valorIncluir': '1-2'}` y
    `{'valorDeducir': ''} != {'valorDeducir': '1-2'}`.
  - la mitad «y a la vista» de
    `test_un_numero_que_el_campo_no_entiende_queda_marcado_y_a_la_vista`: con
    el arreglo puesto y una mutación a mano (lo mal escrito se pinta vacío en
    Ajustes a incluir) da `2 failed, 74 passed`: esa prueba
    (`assert '' == '1-2'`) y el caso nuevo. Con la guarda puesta, `pintarValor`
    no tocaba ese campo cuando el texto estaba mal escrito, así que ninguna
    mutación de esa línea podía ponerla roja.

  Las dos corridas son a mano, en una copia fuera del repo; no sumé casos a
  `sabotaje_valor1.sh` (la pieza no es de revisión fuerte).

## Decisiones

**D227. El sufijo de valor de la operación (`#sbtSufijoValor`) tiene el mismo
dibujo que este defecto, y no lo toqué.** Lo leí, no lo corrí en un navegador
(lo encontró `/code-review`). `op.sbt_sufijo_valor` se escribe sólo al generar
(`finalize.js:671`) y ninguna línea de `static/v2` le asigna valor al campo.
Después de generar una vez, volver y recargar: la operación recuperada trae el
sufijo, el campo arranca vacío; los avisos se piden con el sufijo guardado
(`:927`) y la tarjeta del despachante lee el campo vacío
(`despachante.js:256`). El «Generar» siguiente pisa el guardado con el campo
vacío (`:671`) y frena pidiendo el sufijo (`:678`).

- (a) Pieza aparte, con el rojo primero (un caso de pantalla; si no reproduce,
  se informa con la salida).
- (b) A la cola de limpieza.
- (c) Nada.

Recomiendo **(a)**: es el mismo defecto que me pediste acá (lo que se manda y
lo que se ve no coinciden) y hoy sólo está leído. No frena lo que sigue.

**D234. `pytest` entero está en rojo desde EXCEL2D-RELOJ (`f75cb48`), que
llegó con tu rama: `test_la_subida_cara_no_frena_a_nadie` recorre todos los
hilos del proceso en cada marca, y en la corrida entera hay unos 1080.** (Uso
D234 porque D228–D233 son de la Técnica; si ese número no es mío, renumerala.)

```
FAILED tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas]
tests/test_excel2d.py:213: in test_la_subida_cara_no_frena_a_nadie
    assert frenado < 1, f"el otro hilo no avanzó mientras el proceso gastó {frenado:.2f} s de CPU"
E   AssertionError: el otro hilo no avanzó mientras el proceso gastó 1.01 s de CPU
E   assert 1.0095503170000484 < 1
= 1 failed, 6110 passed, 110 skipped, 3 xfailed, 106 warnings in 1279.19s (0:21:19) =
```

No lo relancé hasta verlo verde. Lo que corrí después es diagnóstico. Sobre
el repo, sin tocarlo: la prueba sola (`7 passed`, 3,12 s) y el comando 4 de
«Para reproducir», que la pone roja en 4 s (`1 failed, 6 passed`, 1,25 s). El
resto, en una copia fuera del repo (`git archive a7511e0`) con una línea
agregada que anota la medida antes del `assert`:

| qué | ese caso (tope 1 s) | marcas del hilo testigo | resultado |
|---|---|---|---|
| la prueba sola (`-k no_frena`), 5 veces | 0,389 · 0,565 · 0,410 · 0,578 · 0,406 s | 7 u 8 | `7 passed` las 5 |
| `pytest` entero otra vez, en la copia | 1,263 s, con 1076 hilos vivos | 4 | rojo otra vez, el mismo caso |
| sola, con 1075 hilos dormidos puestos adrede, 2 veces | 1,320 y 1,325 s | 3 | `1 failed, 6 passed` las 2 |
| lo mismo, con `_otro_hilo_listo` devolviendo `True` sin recorrer nada, 2 veces | 0,253 y 0,131 s | 38 y 40 | `7 passed` las 2 |

- **La causa.** Desde `f75cb48` el hilo testigo llama a `_otro_hilo_listo()`
  en cada marca: lista `/proc/self/task` y abre el `stat` de cada hilo. Cuando
  la corrida entera llega a `test_excel2d.py` (40 %) el proceso arrastra unos
  1080 hilos, casi todos dormidos (`/proc/<pid>/task`: 1081, 1078 en `S`). El
  testigo se queda recorriéndolos mientras la subida gasta CPU y casi no marca
  (3 o 4 marcas contra 38 o 40): `frenado` deja de medir a la subida y mide al
  propio testigo.
- **En este contenedor (4 núcleos) no es de vez en cuando:** 2 corridas
  enteras, 2 rojas (1,01 y 1,26 s). Antes de integrar tu rama, `pytest` entero
  sobre `c4620ca` dio verde. Tu acta de EXCEL2D-RELOJ dice «No corrido: pytest
  entero, …».
- **En la CI no salió:** tu `NOW.md` (`23967c9`) dice «CI de la PR verde sobre
  `e3b169e8` y `fa6df9bc`», y la CI corre la suite entera (`ci.yml:49`). No
  miré la CI ni sé por qué allá pasa: una máquina más rápida alcanza (acá
  pasó el tope por 0,01 s la primera vez), o menos hilos. El margen allá no
  lo conozco.
- **No sale de mi diff.** El producto que cambia es `finalize.js` (pantalla);
  la prueba sube un Excel al backend. `tests/test_valor1.py` corre después en
  el mismo proceso (96 % contra 40 %).
- **Lo que no miré:** qué pruebas dejan esos 1080 hilos. Línea que propongo
  para la cola: «la suite llega a `test_excel2d.py` con ~1080 hilos dormidos
  que dejó alguna prueba anterior; ver cuáles y cerrarlos».
- La segunda corrida entera, por ser en una copia sin `.git`, dio además
  `test_limpieza1::test_no_queda_un_camino_de_publicacion_a_google_cloud`
  (`git ls-files` sale 128). Es de la copia, no del repo.

Opciones:

- (a) Vuelve a la Técnica como devolución de EXCEL2D-RELOJ: la prueba es suya.
- (b) La tomo yo (me abrís `tests/test_excel2d.py` para esa pieza).
- (c) Se revierte `f75cb48` hasta que esté arreglada.

Recomiendo **(a)**. Mientras tanto, en un contenedor como éste ninguna
entrega que integre tu rama puede mostrar `pytest` entero en verde; cuándo va,
lo decidís vos. No frena CUIT-PERFIL: su `pytest` entero va a traer este
mismo rojo hasta que se arregle, y lo voy a informar así.

## Supuestos (reversibles)

1. **El caso nuevo en `tests/test_valor1.py`** (+7). Pediste un caso de
   pantalla; lo sumé porque la CI no corre las pantallas y sin él volver a
   poner la guarda la deja en verde. Además es lo que cierra D222.
2. **El caso de pantalla prueba los dos campos en una sola recarga**, como
   datos del mismo caso (una causa).
3. **`sabotaje_valor1.sh` no cambió.** Corrió entero porque cambiaron su
   producto y su prueba.

## Para reproducir

```bash
# raíz del repo; VENV = carpeta de un venv con requirements.txt; hace falta node y Playwright.
# 1. El rojo sobre el código de antes y el verde sobre el entregado (cada uno ~1 min)
SOLO="ajuste1" env -u DATABASE_URL -u ENVIRONMENT PY=$VENV/bin/python bash scripts/testing/correr_pantallas.sh a57b584 /tmp/aj-rojo
#   ROJA  ajuste1  rc=1 …  resumen: 0 verdes, 1 rojas: ajuste1
SOLO="ajuste1" env -u DATABASE_URL -u ENVIRONMENT PY=$VENV/bin/python bash scripts/testing/correr_pantallas.sh a7511e0 /tmp/aj-verde
#   verde ajuste1  rc=0 … PANTALLA AJUSTE-1 OK   resumen: 1 verdes, 0 rojas

# 2. La prueba corta (~20 s), y su rojo con las guardas de antes (la tercera línea deja el árbol como estaba)
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
P="env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider tests/test_valor1.py"
$P
#   76 passed
git show a647bee:proyecto_maria/static/v2/screens/finalize.js > proyecto_maria/static/v2/screens/finalize.js; $P; git checkout -- proyecto_maria/static/v2/screens/finalize.js
#   FAILED tests/test_valor1.py::test_un_ajuste_mal_escrito_se_ve_en_el_campo_que_llega_vacio   1 failed, 75 passed

# 3. Los sabotajes de valor1, enteros (~11 min)
bash scripts/testing/sabotaje_valor1.sh a7511e0 $VENV
#   29 líneas ROJO, ninguna FALLA; «OK: los 29 sabotajes dan rojo por la razón esperada»; sale 0

# 4. D234 sin correr la suite entera (~4 s): la prueba sola, con 1075 hilos dormidos en el proceso
mkdir -p /tmp/d234 && printf 'import threading\n_fin = threading.Event()\ndef pytest_sessionstart(session):\n    for _ in range(1075):\n        threading.Thread(target=_fin.wait, daemon=True).start()\ndef pytest_sessionfinish(session):\n    _fin.set()\n' > /tmp/d234/hilos_plugin.py
PYTHONPATH=/tmp/d234 env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider -p hilos_plugin tests/test_excel2d.py -k no_frena
#   FAILED …test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas]   1 failed, 6 passed, 19 deselected
#   sin «-p hilos_plugin»: 7 passed, 19 deselected
```

## Puertas

Todas sobre `a7511e0`, salvo donde dice otra cosa.

| puerta | salida |
|---|---|
| `pantalla_ajuste1.js` sobre `a57b584` (antes del arreglo) | `ROJA ajuste1 rc=1`, `resumen: 0 verdes, 1 rojas: ajuste1` |
| `pantalla_ajuste1.js` | `verde ajuste1 rc=0`, `PANTALLA AJUSTE-1 OK`, `resumen: 1 verdes, 0 rojas` |
| `tests/test_valor1.py` | `76 passed` |
| `tests/test_valor1.py` sobre `d094c24` | `76 passed` |
| `pantalla_ajuste1.js` sobre `d094c24` | `verde ajuste1 rc=0`, `PANTALLA AJUSTE-1 OK`, `resumen: 1 verdes, 0 rojas` |
| la misma con el `finalize.js` de `a647bee`, copia fuera del repo | `1 failed, 75 passed` (el caso nuevo, los dos campos) |
| la misma con la mutación a mano, copia fuera del repo | `2 failed, 74 passed` («a la vista» y el caso nuevo) |
| `test_valor1`, `test_separadores1`, `test_separadores1b`, `test_valor1c` | `296 passed` (57 s) |
| `sabotaje_valor1.sh` entero | 29 `ROJO`, 0 `FALLA`; `OK: los 29 sabotajes dan rojo por la razón esperada`; sale 0 (693 s) |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `pytest` entero | **`1 failed, 6110 passed, 110 skipped, 3 xfailed`** (1279 s). El rojo es D234. Son 6224 casos: los 6223 de `c4620ca` y el caso nuevo |
| `compileall -q proyecto_maria` | sin salida, sale 0 |
| las 31 pantallas (`correr_pantallas.sh`) sobre `c4620ca` | `resumen: 31 verdes, 0 rojas` (910 s) |
| `tests/test_excel2d.py -k no_frena`, sola, una vez | `7 passed, 19 deselected` (3,12 s) |
| la misma con 1075 hilos dormidos (comando 4), una vez | `1 failed, 6 passed, 19 deselected`; `el otro hilo no avanzó mientras el proceso gastó 1.25 s de CPU` |
| `anclas_perdidas.py` | 2452 anclas (una más: la trajo tu rama en `sabotajes/excel2d.sh`); los mismos hallazgos, línea por línea, que sobre `0334800` |
| historia en el producto (grep de §6), `a647bee..d094c24` | vacío |

**Sobre `d094c24` repetí sólo `tests/test_valor1.py` y el caso de pantalla.**
De `a7511e0` a `d094c24` cambian `docs/pm/` y `scripts/testing/forzar_orden1.js`
(DOS-RELOJES, de la Técnica), que no usan `pytest`, la e2e ni mi caso.

**Las 31 pantallas no se repitieron sobre `a7511e0`.** De `c4620ca` a
`a7511e0` no cambia el producto ni nada que una pantalla use: mío,
`tests/test_valor1.py` y el mensaje de `pantalla_ajuste1.js`; de tu rama,
`tests/conftest.py`, `tests/test_excel2d.py` y `sabotajes/excel2d.sh`. Sí
repetí sobre `a7511e0` el caso de esta pieza y todo lo que corre `pytest`.
Antes de integrar tu rama, sobre `c4620ca`, había corrido además: `pytest`
entero (`6110 passed, 110 skipped, 3 xfailed`), la e2e, `compileall` y
`sabotaje_valor1.sh` (29 `ROJO`); y sobre `1323fdc`, el caso y el guion otra
vez (29 `ROJO`).

**`pytest` entero no se repitió sobre el repo después del rojo.** Lo que corrí
después es diagnóstico y está en D234: sobre el repo, la prueba sola, una vez;
el resto, en una copia fuera del repo.

Archivos de producto tocados: `proyecto_maria/static/v2/screens/finalize.js`
y `CHANGELOG.md`.

## chequeo-6

```
chequeo-6 a647bee..d094c24: avisos para mirar, no un veredicto
producto +4/−4
arnés +116/−11
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/screens/finalize.js: 1484 → 1484
avisos: 0
```

El `arnés +116/−11` incluye lo que trajo tu rama: `tests/conftest.py`,
`tests/test_excel2d.py` y `sabotajes/excel2d.sh` (+39/−5) y
`forzar_orden1.js` (+9/−6). Lo mío es `pantalla_ajuste1.js` +61 y
`tests/test_valor1.py` +7.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-medio` | Sonnet, medio | Sin hallazgos. Leyó; no corrió el caso ni levantó servidor. | — |
| `/code-review high` | Fable (heredado), alto | El arreglo sólo lo cuida un caso de pantalla que la CI no corre. | Arreglado: el caso de pytest (`1323fdc`, y los dos campos en `a7511e0`), con su rojo. |
| `/code-review high` | Fable (heredado), alto | En el caso, `(… \|\| {}).dataset.screen` rompe si no hay pantalla activa, y el `.catch` tapaba la causa con un mensaje fijo. | Arreglado en `1323fdc`: `?.dataset.screen`, y el mensaje trae el error de la espera. |
| `/code-review high` | Fable (heredado), alto | `#sbtSufijoValor` no se repinta desde la operación recuperada. Fuera de este diff; leído, no corrido. | D227. |
| yo, al leer tu línea sobre D222 | — | Mi aserción de `1323fdc` miraba sólo Ajustes a deducir: volver a poner la guarda sólo en Ajustes a incluir dejaba `pytest` en verde. | Arreglado en `a7511e0`. |

Las dos revisiones miraron `a647bee..c4620ca`. Lo que vino después
(`1323fdc`, `a7511e0`: sólo pruebas) no pasó por subagentes; lo revisé yo.
`/code-review` no corrió pruebas: sus tres notas son de lectura. Las dos
primeras las comprobé corriendo; la tercera no.

## Qué no corrí y riesgos

- **`pytest` entero quedó con 1 rojo** (D234), sobre `a7511e0`. Sobre
  `d094c24`, el que entrego, no lo corrí: `tests/test_excel2d.py` es el mismo
  en los dos, así que espero el mismo rojo. El último verde entero es de
  `c4620ca`, antes de integrar tu rama. Los otros 6110 casos pasaron.
- Sobre `d094c24` tampoco corrí la e2e, `sabotaje_valor1.sh` ni
  `compileall`: desde `a7511e0` no cambia nada que usen.
- El diagnóstico de D234 usa 1075 hilos dormidos puestos por mí, no los de la
  suite: reproduce el número (1,32 s contra 1,26 s) pero no dice quién los
  deja ni si alguno hace algo más que dormir.
- **D227 no está reproducida**: es lectura de código.
- **El contenedor se reinició** en medio del primer `pytest` entero sobre
  `c4620ca` (iba por el 81 %, sin rojos hasta ahí). No lo diagnostiqué más
  allá de eso: murió el entorno, no una prueba. Lo relancé entero desde cero.
- Las 31 pantallas, sólo sobre `c4620ca` (arriba dice por qué).
- No corrí Postgres ni `smoke_friccion.sh` ni `ataque_aislamiento.sh`: la
  pieza no toca backend, datos, sesión ni permisos.
- Riesgo que queda: el caso de pantalla sigue fuera de la CI, como todas las
  pantallas. Lo que la CI cuida es el caso de pytest, que usa un DOM simulado,
  no un navegador.
- El adversario apuntó, leyendo, que la guarda además dejaba el campo con el
  texto de la operación anterior si otra cargada en la misma pestaña traía un
  ajuste mal escrito. No lo corrí; sin la guarda ese camino no existe.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 23967c9, ya integrada en d094c24), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Aceptadas e integradas por la PM: D218, D219, PANTALLAS-MARIA, D223 + D224, D226 y valor1 (actas del 13/11). Entregada y esperando veredicto: AJUSTE-BORRADOR en d094c24 (puertas sobre a7511e0; caso a57b584, arreglo c4620ca: salieron las dos guardas de pintarValor, producto +4/−4; pantalla_ajuste1.js y un caso en test_valor1.py con los dos campos; cierra lo que quedaba de D222). Abiertas para decidir: D227 (el sufijo #sbtSufijoValor no se repinta desde la operación recuperada; leído, no corrido; recomendé pieza aparte con rojo primero) y D234 (pytest entero da 1 rojo desde EXCEL2D-RELOJ, f75cb48, de la Técnica: test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas] recorre los ~1080 hilos que arrastra la corrida entera; en mi contenedor 2 de 2 rojas, la CI de la PM dio verde; causa reproducida; recomendé que vuelva a la Técnica; no toco tests/test_excel2d.py). Hasta que D234 se arregle, mi pytest entero trae ese rojo: se informa, no se repite hasta verde. Ya decididas: D221 (b), D222 (a), D223 (a), D224 (a), D225 (a), D226 (a). Orden de la PM, una pieza a la vez: la que arranco ahora es CUIT-PERFIL (D225: producto con datos, revisión fuerte —adversarios y sabotaje propio—; primero el rojo de hoy: el perfil guarda un CUIT con dígito verificador malo; PUT /api/user/profile rechaza un CUIT inválido y la pantalla muestra el error, sugerencia cuit_valido en controles_maria.py:52; decir qué pasa con los perfiles ya guardados sin cambiar datos; orden1, validacion1, cobro_corte1 y cobro_mp1_v2 pasan a _cuit_perfil.js; pantalla_orden1.js ya es mía). Después: los vencidos de sabotajes-conocidos.txt, uno por pieza. No son míos: maria7, maria1c, correr_pantallas.sh, forzar_arranque.js, forzar_orden1.js, pantalla_borrador1.js. Próxima D: la que diga PARA-DEV-2.md (usé D227 y D234; D228–D233 son de la Técnica). Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
