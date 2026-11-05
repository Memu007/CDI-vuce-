# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## RENDIMIENTO-1d: **entregada** en `aaed661` (2026-11-05), D49 (b) y D55 (b)

| Pieza | Resultado | Qué decidís |
|---|---|---|
| RENDIMIENTO-1d (D49 b) | Sacar el texto de la factura para adivinar el vendedor (`/upload_pdf/public`) ya no corre en un hilo de la app. Corre en el proceso aparte del lector, con sus topes: 256 MB de memoria, 8 MB por flujo y tope de CPU. Tiene dos lugares propios, separados de los de validar, y el texto que vuelve tiene tope de 64 K caracteres. Un PDF de 1104 bytes cuyo texto se infla a 28 millones de caracteres hacía crecer la app 296 MB; ahora 0 MB. | D63 |
| D55 (b) | Esperar un lugar para leer un despacho ya no le quita tiempo al PDF: espera hasta el tope (si no hay lugar, `SinLugar`) y después el proceso tiene el tope entero, como validar. | D67 |

**Ojo para publicar, sigue igual:** esta rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío, `aaed661` incluido, sirve para publicar hasta que esas cinco estén ✅.

**Archivos de producto que toqué:** `proyecto_maria/core/despacho_lector.py` y `proyecto_maria/main.py` (sólo `upload_pdf_public`, ~4592).

**DESPACHO-1c (`fbbb2ad`):** su informe era el que estaba acá. DESPACHO-1d, la que me pediste después, la estoy haciendo ahora y va en el próximo informe.

### Decisiones

- **D63. El tope de 8 MB por flujo también vale para el texto del vendedor.** Una factura real con un flujo de contenido que descomprimido pase 8 MB ahora no da vendedor; antes sí. La subida sigue andando y el vendedor queda vacío, como cuando no se reconoce. Lo marcó `/code-review`.
  - (a) Dejarlo.
  - (b) Sacar el tope por flujo sólo para el texto y quedarse con los 256 MB, el CPU y los 64 K.
  - **Recomiendo (a).** El vendedor es opcional y se completa a mano. Un flujo de texto de más de 8 MB en una factura no lo vi nunca. Con (b), el caso `test_el_texto_corta_cada_flujo_que_se_infla` y su sabotaje se van.

- **D67. Sin lugar para leer un despacho da 504, y en validar da 503.** Al leer, `SinLugar` es un `TimeoutError` y `main.py` lo contesta 504 `lectura_pdf_demasiado_larga` («Leer el despacho tardó demasiado…»). Validar contesta 503 «muchos PDFs». No lo cambié: D55 pedía el patrón de la espera, no la respuesta.
  - (a) Dejar 504.
  - (b) 503 con un texto de «sin lugar», como validar.
  - **Recomiendo (b)**, en una pieza aparte. La persona que esperó un lugar no tiene un PDF largo: el texto le dice algo falso. Es una rama en `main.py` y un caso.

### SHAs (base `f5d227c`)

| SHA | Qué |
|---|---|
| `01d8dea` | test: rojo, el texto del vendedor infla la app. Sobre ese SHA: `AssertionError: la app creció 1494 MB: {'normal': [200, 'ACME TRADING CO LTD'], 'bomba': [200, None], 'crecio_mb': 1494}` |
| `0897f28` | fix: el texto se saca en el proceso aparte (`modo="texto"`, tabla `_MODOS`) |
| `9890b26` | test: topes por flujo y de CPU del texto, y sabotajes |
| `f2a7cd4` | docs: CHANGELOG |
| `11051b0` | test: rojo, el texto ocupa los lugares de validar (con 6 subidas de un atacante, la víctima esperaba 20 s) |
| `945e883` | fix: lugares propios para el texto (`_SACANDO_TEXTO`) |
| `cd55d7e` | test: sabotaje de los lugares compartidos |
| `6ff9f41` | test: rojo, PDF de 1 KB cuyo texto se infla. Sobre ese SHA: `texto: la app creció 296 MB: {'normal': [200, 'ACME TRADING CO LTD'], 'fuentes': [200, None, 2], 'texto': [200, None, 296]}` |
| `528ff2b` | fix: el texto que vuelve tiene tope de 64 K caracteres (`_MAX_TEXTO_VENDEDOR`) |
| `fd7334e` | test: sabotaje del tope del texto |
| `d307a3f` | docs: CHANGELOG |

Vuelta con D55 (b), sobre `fbbb2ad` (DESPACHO-1c):

| SHA | Qué |
|---|---|
| `e9f06a3` | test: rojo, esperar lugar para leer un despacho se cobra al PDF. Sobre ese SHA sólo falla `[menos-que-un-pdf]`: `AssertionError: venció leyendo` |
| `db9fbf9` | fix: `_leer_aparte` espera hasta `hasta` y después corre con `limite_s` entero (producto +8/−10) |
| `cf4177d` | test: sabotaje nuevo en `rendimiento1d.sh` y dos anclas al día en `rendimiento1c.sh` y `rendimiento1.sh` |
| `83eb7c8` | docs: CHANGELOG |
| `ad38d87` | test: la espera de validar y la de leer quedan en un solo caso, con la vía como dato; un ancla rota de `rendimiento1c.sh` al día |
| `cf039b2` | test: el sabotaje de leer busca el motivo en la línea `E` del error, no en cualquier parte de la salida |
| `489ec67` | merge de tu rama (CSRF-3 aceptada y docs) |
| `aaed661` | test: el ancla del sabotaje «el proceso aparte no le pasa el tope a validar» apunta a `_MODOS[modo][0](data, limite_cpu_s)`, donde el hijo elige el modo |

El caso es `test_esperar_casi_todo_el_tope_no_culpa_al_archivo` (`tests/test_rendimiento1c.py`), uno para las dos vías: `validar` y `leer` son un dato del caso. En `e9f06a3` era un caso aparte casi igual al de validar; `/code-review` lo marcó contra «un caso por causa» y en `ad38d87` quedaron unidos. Ocupa los dos lugares, los libera a distintas distancias del tope y pide un PDF normal con ese tope. Las cuatro filas por vía: a 0.5 s y a 0.08 s del tope tiene que pasar; justo en el tope, pasar o «sin lugar»; pasado el tope, «sin lugar». Antes de medir comprueba que el PDF tarda más de 0.08 s, si no la fila del medio no distingue nada.

**Un ancla rota que no era de esta vuelta.** El sabotaje «sin fila por usuario» de `rendimiento1c.sh` buscaba `"validar", hasta)`, que dejó de existir en `0897f28` (la primera vuelta de esta pieza). `git log -S` lo confirma: falta en `03bdc9f`, `d307a3f` y `fbbb2ad`. En la primera vuelta no corrí `rendimiento1c.sh`, por eso no lo vi. Ahora busca `modo, hasta)`.

El PDF del caso es sintético (`tests/pdf_bombas.py`, `texto_que_se_infla`): 1104 bytes, 28 M caracteres, 8.46 s de CPU para sacarlos.

### Comandos

```bash
git checkout aaed661
# «4 passed»
<entorno de la suite> python -m pytest -q --no-cov tests/test_rendimiento1d.py
# 7 ROJO y «fallas: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/rendimiento1d.sh aaed661
# 17 ROJO y «sabotajes con falla: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/rendimiento1c.sh aaed661
# 11 ROJO y «sabotajes con falla: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/rendimiento1.sh aaed661
```

### Puertas

Todas sobre `aaed661`, en worktrees limpios en ese SHA, una después de la otra:

| Puerta | Salida exacta |
|---|---|
| `pytest -q --no-cov --timeout=300` (suite completa) | `4851 passed, 355 skipped, 3 xfailed, 101 warnings in 683.63s (0:11:23)`, salida 0 |
| suite con el entorno de la CI (`ENVIRONMENT=testing`, `JWT_SECRET_KEY`, `EMAIL_VERIFICATION_REQUIRED=false`) | `4851 passed, 355 skipped, 3 xfailed, 100 warnings in 682.59s (0:11:22)`, salida 0 |
| `compileall -q proyecto_maria tests` | sin salida, salida 0 |
| `rendimiento1d.sh` | 7 ROJO, «fallas: 0», salida 0 |
| `rendimiento1c.sh` | 17 ROJO, «sabotajes con falla: 0», salida 0 |
| `rendimiento1.sh` | 11 ROJO, «sabotajes con falla: 0», salida 0 |

Los siete rojos de `rendimiento1d.sh`, copiados de la salida:

```
ROJO  | el texto del vendedor vuelve a sacarse en un hilo de la app: dice «la app creció»
ROJO  | el texto sin topes por flujo: dice «sacar el texto llegó a»
ROJO  | el texto sin tope de CPU: dice «DID NOT RAISE»
ROJO  | el proceso aparte no sabe sacar el texto: dice «'normal': [200, None]»
ROJO  | el texto ocupa los lugares de validar: dice «assert 503 == »
ROJO  | el texto vuelve a la app sin tope: dice «texto: la app creció»
ROJO  | esperar lugar para leer un despacho se descuenta del tope: dice «AssertionError: venció leyendo»
fallas: 0
```

**La CI no deselecciona nada.** `CLAUDE.md` §5 dice que `ci.yml` deselecciona tests de presupuestos compartidos, pero hoy `.github/workflows/ci.yml:45` corre `python -m pytest --no-cov` sin `--deselect`. Por eso la puerta de la CI de esta vuelta es la suite entera con su entorno. **Propuesta:** corregir esa línea de §5.

**Un rojo de entorno, mío, en una corrida anterior (`cd55d7e`).** La suite dio `1 failed` en `test_maria1b_devolucion.py`. La causa: corrí dos suites a la vez, y ese caso y `test_excel2.py:512` usan una ruta fija en `/tmp`. Solo pasa; desde entonces las suites corren una después de la otra. **Propuesta para `COLA-LIMPIEZA.md`:** que esos dos casos usen `tmp_path`.

### Revisiones

Adversario `adversario-sonnet-alto` (Sonnet, alto) sobre `f2a7cd4` (primera vuelta):

| # | Severidad | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | Alta | Un PDF chico cuyo texto se infla hacía crecer la app ~295 MB al volver el texto (en la base, +279: no lo empeoré, pero estaba en la pieza) | Arreglado en `528ff2b`, rojo en `6ff9f41` |
| 2 | Media | El texto compartía los lugares de validar: con 6 subidas de un atacante, la víctima esperó 20 s | Arreglado en `945e883`, rojo en `11051b0` |
| 3 | Media-baja | Sacar `clave=user["username"]` en `main.py` no lo ve ningún caso (5 passed) | Riesgo, abajo |
| 4 | Baja | `test_rendimiento1d` no distingue el tope de memoria del hijo | Lo cubre el sabotaje `_MAX_MEMORIA_HIJO` de `despacho1b.sh`, porque el lanzador es el mismo. No lo corrí en esta pieza |
| 5 | Baja | Las fallas sólo van a `logging.debug` | Riesgo |
| 6 | Baja | Hasta 2×15 s más de espera en una subida | Riesgo |

El adversario confirmó además que no hay otro camino que lea el PDF dentro de la app. `fitz` no está instalado; si se instalara, renderiza cada hoja a 3x. Los errores se atrapan y no llegan al cliente.

Adversario `adversario-sonnet-alto` (Sonnet, alto) sobre `fbbb2ad..cf039b2` y `aaed661` (vuelta D55). No encontró nada alto ni medio; leyó y razonó, no corrió pruebas:

| # | Severidad | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | Baja | El peor caso de `/despacho/leer` sube de 180 s a 300 s con los valores por defecto: validar ya podía tardar 2×30 s, y leer pasa de 120 s a 240 s (espera hasta 120 y corre 120 entero) | Riesgo, abajo. Es lo que pide D55 (b) |
| 2 | Baja | El caso no comprueba que la fila de leer del usuario se libere después de un `SinLugar` o de cancelar. El código la libera en un `finally` | Riesgo: hueco de cobertura, no defecto |
| 3 | Baja | La fila de leer «casi todo el tope» deja al hijo exactamente 2 s, sin margen: en una máquina muy cargada podría dar «venció leyendo» con el código bien | Riesgo. Pasó en las dos suites sobre `aaed661` y en `rendimiento1c.sh`; no lo medí bajo carga |

Confirmó también que ni el lugar ni la clave quedan tomados para siempre (no hay `await` entre tomar y el `try`, y en Python 3.12 `Semaphore.acquire` devuelve el permiso si lo cancelan), y que `SinLugar` y el vencimiento del hijo salen por caminos separados.

`/code-review high` (primera vuelta):

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | Lugares compartidos con validar | Arreglado (el 2 del adversario) |
| 2 | Hasta dos veces el tiempo del vendedor | Riesgo (el 6 del adversario) |
| 3 | `fitz` latente | Riesgo |
| 5 | `modo` no se valida | Es una constante interna: la pasa `main.py` y no llega del cliente |
| 6 | El tope de 8 MB por flujo puede perder el vendedor | D63 |
| 7 | El nombre y el docstring de `validar_pdf_aparte` ya no dicen lo que hace | Nota de mantenimiento: lo anoto para la cola |
| 8 | `extraer_texto_pdf_seguro` repite a `_leer_hojas` y se traga `MemoryError` | Propuesta para `COLA-LIMPIEZA.md` |
| 9 | Cada subida levanta un intérprete más | Propuesta |

`/code-review` de la vuelta D55 marcó el caso duplicado contra «un caso por causa»: arreglado en `ad38d87`.

Revisión de seguridad, mía y no independiente: `modo` es una constante que va como argumento en una lista, sin shell. El entorno del hijo va limpio. El nombre de usuario sólo es clave de un diccionario. No encontré nada de confianza alta.

### Chequeo §6, entero

`docs/pm/herramientas/chequeo-6.py f5d227c d307a3f` (primera vuelta):

```
chequeo-6 f5d227c..d307a3f: avisos para mirar, no un veredicto
producto +53/−31
  AVISO producto suma 22 líneas netas: el informe dice por qué (§6: más de 20)
arnés +268/−21
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 875 → 899
  proyecto_maria/main.py: 12041 → 12039
avisos: 1
```

**Por qué suma 22:** es un modo nuevo del proceso aparte. Suma la función, una tabla que reemplaza dos `if/else`, los lugares propios y el tope del texto. Dos docstrings crecieron una línea.

`chequeo-6.py fbbb2ad cf039b2` (vuelta D55):

```
chequeo-6 fbbb2ad..cf039b2: avisos para mirar, no un veredicto
producto +8/−10
arnés +59/−28
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 899 → 897
avisos: 0
```

`chequeo-6.py 489ec67 aaed661` (después de tu merge):

```
chequeo-6 489ec67..aaed661: avisos para mirar, no un veredicto
producto +0/−0
arnés +1/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Riesgos

- Sacar `clave=` en la llamada de `main.py` dejaría el texto sin fila por usuario, y ningún caso lo ve (hallazgo 3 de la primera vuelta).
- Una subida puede esperar hasta 15 s para validar y otros 15 s para el texto (`PDF_VENDOR_TIMEOUT_S`).
- El peor caso de `/despacho/leer` sube de 180 s a 300 s. No sé cuánto aguanta el proxy de Railway: si corta antes, la persona ve un corte en vez del 504.
- La fila «casi todo el tope» de leer no tiene margen bajo una carga muy alta.
- Si el texto falla, sólo queda en `logging.debug`.
- `fitz` (PyMuPDF) no está, pero si alguien lo agrega, lee el PDF en la app sin topes.

### Lo que no corrí

- El sabotaje `_MAX_MEMORIA_HIJO` de `despacho1b.sh`.
- `smoke_friccion.sh` y `ataque_aislamiento.sh`: la pieza no toca sesión, permisos ni datos.
- Postgres: la pieza no toca la base.
