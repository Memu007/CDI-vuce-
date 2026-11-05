# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DESPACHO-1c: **entregada** en `5199709` (2026-11-05), con tus CSRF-1 y CSRF-2 integradas

| Pieza | Resultado | Qué decidís |
|---|---|---|
| DESPACHO-1c (D51 b + D52 b) | Las tres pantallas que guardan en la memoria de productos avisan cuando el servidor contesta `historial_guardado: false`; «Cliente guardado» ya no tapa ese aviso. Una consulta o una fila del historial que normalizan a vacío ya no se cruzan con todo. | D57 |
| RENDIMIENTO-1c v2, DESPACHO-1b v6, CATALOGO-LARGO-1 | Sin cambios desde `ca87d82` (abajo). Este es el timbre que no te mandé en su momento. | D53–D56, abajo |

**Ojo para publicar, sigue igual:** desde `96052c8` esta rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío desde `96052c8`, `5199709` incluido, sirve para publicar hasta que esas cinco estén ✅. El último sin ese código es `ca87d82`, que no tiene DESPACHO-1c.

**Numeración:** mis D llegan a D57. En `640036a` usaste «D59» para la otra Dev; si las D son una sola serie, D58 quedó sin usar. No cambia nada mío.

### Decisiones

- **D57. Si guardar la operación falla, «Cliente guardado» tapa el error.** En el panel de cliente sin asignar, `reSaveOperationAndClosePanel` (`finalize.js:1171`) muestra «Cliente guardado» salvo que llegue `historial_guardado: false`. Cuando el guardado entero falla, `saveOperationToHistory` muestra su error y devuelve `{ok: false}` sin ese campo, así que el éxito sale después y reemplaza el error (un toast reemplaza al anterior). Antes de esta pieza pasaba lo mismo, porque el éxito salía siempre: no lo empeoré, pero queda al lado de lo que toqué. Lo encontraron por separado `/code-review` y el adversario.
  - (a) Dejarlo.
  - (b) La guarda pasa a `guardado.ok && guardado.historial_guardado !== false`, con un escenario más en el arnés (`/operaciones` con 500) y su sabotaje.
  - **Recomiendo (b), como devolución chica de esta pieza.** Es una condición en la línea que ya cambié; la dejé afuera porque D51 pide el aviso de `false`, no el del error.

D53 y D54 siguen sin decidir y no las hice. El hallazgo 4 de abajo (un 400 de guardar-uso no se avisa) es la D53.

### SHAs (base `d25c263`)

| SHA | Qué |
|---|---|
| `58f2aed` | test: rojos del aviso de memoria sin guardar y de la descripción que normaliza a vacío |
| `98d6222` | fix: avisar lo que no quedó en la memoria y no cruzar descripciones vacías (+ `CHANGELOG.md`) |
| `336e5fb` | test: `despacho1c.sh`, sabotajes de las dos guardas de sugerir y de los tres avisos |
| `3095033` | refactor: una consulta que normaliza a vacío no lee el historial (hallazgo 7) |
| `71598bd` | test: el aviso se reconoce por su título, lo guardado sigue diciendo «Cliente guardado» y el arnés sin vueltas fijas (hallazgos 5 y 6) |
| `1e8ee4d` | test: la respuesta sin `historial_guardado` no avisa |
| `04d88a5` | merge de tu rama: CSRF-1 (ver «Merge», abajo) |
| `a7ed7b6` | test: cada caso arranca con el limitador apagado |
| `5199709` | merge de tu rama: CSRF-2 hasta `72f92ba` |
| este | docs: informe |

**Archivos de producto de esta pieza:** `proyecto_maria/main.py` (`sugerir_ncm`, paso 3), `proyecto_maria/static/v2/screens/finalize.js` (`reSaveOperationAndClosePanel`, `saveOperationToHistory`), `proyecto_maria/static/v2/screens/ncm.js` (`saveNcmUsage`) y `CHANGELOG.md`.

**Cómo queda:**
- `sugerir_ncm`: si la consulta normaliza a vacío no lee el historial; una fila guardada que normaliza a vacío no se compara. Lo idéntico no latino («日本語の製品» contra «日本語の製品») tampoco se sugiere: es lo literal de D52 (b), lo marca el hallazgo 2.
- Operación con cliente activo: con `false`, aviso «Algunos productos no quedaron en la memoria».
- Panel de cliente sin asignar: con `false`, ese aviso queda a la vista y no sale «Cliente guardado»; con `true` o sin el campo, «Cliente guardado» como antes.
- Confirmar una posición: con `false`, aviso «No se guardó en la memoria de productos».
- Sin el campo en la respuesta, ninguna pantalla avisa.

**Pruebas:** `tests/test_despacho1c.py` tiene dos casos. Uno es para sugerir, con la familia como datos: fila guardada japonesa o sólo de signos, consulta japonesa o devanagari, y una que sí coincide y se sigue sugiriendo. El otro corre las tres pantallas reales con un DOM falso (`tests/despacho1c_pantalla.js`): tres escenarios por `true`/`false`/sin dato. El arnés espera a ver la llamada a la red, como condición, sin vueltas fijas.

### Comandos

```bash
git checkout 5199709
# «14 passed»
<entorno de la suite> python -m pytest -q --no-cov tests/test_despacho1c.py
# 7 ROJO y «fallas: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1c.sh 5199709
```

### Puertas

Sobre `5199709` (en un worktree limpio en ese SHA), salvo donde dice otro:

| Puerta | SHA | Salida exacta |
|---|---|---|
| `pytest -q --no-cov --timeout=300` (suite completa) | `5199709` | `4806 passed, 355 skipped, 3 xfailed, 103 warnings in 652.79s`, salida 0 |
| suite con el entorno de la CI (`ENVIRONMENT=testing`, `EMAIL_VERIFICATION_REQUIRED=false`) | `5199709` | `4806 passed, 355 skipped, 3 xfailed, 100 warnings in 645.92s`, salida 0 |
| `compileall -q proyecto_maria tests` | `5199709` | salida 0. Avisa `SyntaxWarning: invalid escape sequence '\-'` en `pdf_extractor.py:927` y `:936`; eso viene de antes y no lo toqué |
| `tests/test_despacho1c.py` | `5199709` | `14 passed, 3 warnings in 2.02s` |
| `despacho1c.sh` | `1e8ee4d` | 7 ROJO, «fallas: 0», salida 0. Después de ese SHA cambiaron `tests/conftest.py` y los merges de CSRF; ninguno toca `sugerir_ncm`, `finalize.js`, `ncm.js` ni el arnés (`git diff 1e8ee4d 5199709` sobre esos archivos da vacío) |
| `despacho1b.sh` con `PG_DSN` | `515821a` | 138 ROJO, «sin Postgres, no corridos: 0», «sabotajes sin rojo: 0», salida 0 |
| tus `csrf1.sh` y `csrf2.sh`, en copias adaptadas (ver «Merge») | `5199709` | csrf1 da 8 ROJO y csrf2 da 10 ROJO, con «sabotajes con falla: 0» y salida 0 en los dos. Los scripts originales dan 7 ROJO + 1 ROTO y 9 ROJO + 1 ROTO |

### Revisiones

`/code-review high` sobre `d25c263..336e5fb`, 8 hallazgos:

| # | Hallazgo | Estado |
|---|---|---|
| 1 | `finalize.js:1171`: si guardar falla, «Cliente guardado» tapa el error | D57 (anterior, al lado) |
| 2 | `main.py`: una descripción sólo no latina no se sugiere ni para el mismo texto | riesgo bajo; es lo literal de D52 (b) |
| 3 | `main.py`, guardar-uso: con una descripción que normaliza a vacío contesta `historial_guardado: true`, aunque esa fila nunca se va a sugerir (el catálogo salta la clave vacía y la memoria del cliente da similitud 0) | riesgo bajo, nuevo: el aviso no sale en un caso donde la memoria no va a servir |
| 4 | `ncm.js:1842`: con un 400 de guardar-uso no se guarda nada y no se avisa | es la D53, sin decidir |
| 5 | el test no comprobaba «Cliente guardado» ni el título del aviso | arreglado en `71598bd` |
| 6 | espera fija de 20 vueltas en el arnés | arreglado en `71598bd` |
| 7 | la consulta vacía leía todo el historial | arreglado en `3095033` |
| 8 | el chequeo de `historial_guardado === false` queda en `finalize.js` y en `ncm.js`, con textos distintos | riesgo de §6: son dos pantallas sin código común (`saveNcmUsage` no pasa por `saveOperationToHistory`) y los textos dicen cosas distintas. Unirlas sería un helper en `app_v2.js` para dos líneas; lo dejo para `COLA-LIMPIEZA.md` si te parece |

Adversario Sonnet, esfuerzo alto (`adversario-sonnet-alto`), sobre `336e5fb`:

| | Hallazgo | Estado |
|---|---|---|
| A (media) | = hallazgo 1 | D57 |
| B (baja) | el dashboard v1 (`app.js:3741`, `3924`) no lee el flag | riesgo: no lo toqué. D51 nombra «la pantalla» y lo leí como la v2, que es la que guarda con cliente activo; si el v1 todavía se usa, es otra pieza chica |
| C (baja) | = hallazgo 2 | riesgo |
| D (baja) | una fila corta («a», «1») coincide por `in` con casi cualquier consulta | existía antes de D52; riesgo, no lo toqué |
| huecos | el arnés no cubre las rutas `create` del panel (`orphanCreateClick`) ni «Usar cliente existente» | riesgo: pasan por la misma `reSaveOperationAndClosePanel` que `asignar-cliente` |

### Chequeo §6 (`docs/pm/herramientas/chequeo-6.py`), entero

```
chequeo-6 d25c263..1e8ee4d: avisos para mirar, no un veredicto
producto +27/−10
arnés +279/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12043 → 12045
  proyecto_maria/static/v2/screens/finalize.js: 1390 → 1400
  proyecto_maria/static/v2/screens/ncm.js: 2336 → 2341
avisos: 0
---
chequeo-6 1e8ee4d..04d88a5: avisos para mirar, no un veredicto
producto +16/−14
arnés +207/−13
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12045 → 12044
  proyecto_maria/static/v2/app_v2.js: 1199 → 1202
avisos: 0
---
chequeo-6 04d88a5..a7ed7b6: avisos para mirar, no un veredicto
producto +0/−0
arnés +8/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
---
chequeo-6 a7ed7b6..5199709: avisos para mirar, no un veredicto
producto +37/−11
  AVISO producto suma 26 líneas netas: el informe dice por qué (§6: más de 20)
arnés +218/−74
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12044 → 12041
  proyecto_maria/static/csrf.js: nuevo, 27
avisos: 1
---
```

El AVISO de `a7ed7b6..5199709` es tu CSRF-2: el producto de ese merge es línea por línea el de `6e71766..72f92ba` (lo comparé con `diff` sobre las líneas `+`/`−`), sin nada mío.

### Lo que no corrí

La imagen Docker de producción, el smoke y el ataque de aislamiento: DESPACHO-1c no toca sesión, permisos ni datos de otros. Los sabotajes de CSRF tal cual vienen dan un ROTO cada uno; los conté en las copias adaptadas: ver «Merge».

---

## Merge con tu rama, después de `ca87d82` (2026-11-05)

Traje tu rama dos veces: `96052c8` (hasta `885ee89`, con COBRO-MP-1, ORDEN-1b y EXCEL-2b) y `a8c235d` (sólo `NOW.md` y `PARA-DEV.md`). El primero rompió cuatro cosas; las cuatro tienen arreglo y las puertas de abajo corren sobre `515821a`, que tiene el mismo código que `a8c235d`.

**Ojo para publicar:** desde `96052c8` esta rama tiene `e0b8626`, o sea el código sin aceptar que nombra tu `NOW.md` de las 13:05: COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a. Ningún SHA mío a partir de `96052c8` sirve para publicar hasta que esas cinco piezas estén ✅. Si querés mis tres piezas sin ese código, el último SHA mío anterior al merge es `ca87d82`.

| SHA | Qué |
|---|---|
| `96052c8` | merge de tu rama. Conflictos: los imports de `main.py` (se unieron las dos listas) y `CHANGELOG.md` (se unieron las entradas) |
| `6c8159a` | fix: `validar_con_carril` vuelve a recibir y pasar `clave`. La resolución automática del merge dejó `clave` sin definir en `file_security.py`, lo que daba `NameError` (500) en cada subida de PDF. Producto +3/−2 |
| `e90a978` | test: los usuarios de `test_disco1.py` se crean con `plan="premium", billing_status="active"`, porque COBRO-CORTE-1 (`require_billing_vigente`) daba 402 en `/upload_pdf/public`. **Para que lo mires:** `test_guardar2.py:205` pasa a `{DESC: "84713012"}`, porque la regla de identidad de DESPACHO-1b guarda el NCM en 8 dígitos y el caso esperaba la forma con puntos |
| `515821a` | test: el caso de las diez subidas espera a que las diez bombas de A entren a validar (ver abajo) |
| `a8c235d` | merge de tu rama, sólo docs |

**El caso de las diez tenía una carrera.** Lanzaba la subida de B sin comprobar que las diez bombas de A estuvieran ya en la fila, y B podía llegar antes que ellas. Lo vi con `rendimiento1c.sh`: el sabotaje de la fila por usuario daba VERDE. Ahora el caso cuenta las entradas a `validar_pdf_aparte` y espera la condición observable «10 de 10». Tiene un tope de tiempo y no usa espera fija. El assert es el mismo de antes.

| Arnés | Sabotaje de la fila | Ruta | Bombas sin terminar cuando B responde | demora de B | Resultado |
|---|---|---|---|---|---|
| viejo | puesto | factura | 6 | 1.94 s | VERDE (no lo veía) |
| nuevo | puesto | factura | 0 | 5.06 s | rojo «factura: B esperó detrás de las bombas de A» |
| nuevo | sin sabotaje | factura | 10 | 0.14 s | pasa |
| nuevo | sin sabotaje | despacho | 10 | 0.28 s | pasa |

**Riesgo fuera de alcance (propuesta):** `main.py:8048` llama a `logger.warning("[fill-if-empty] …")`, pero `logger` no está definido en `main.py` (pyflakes: «undefined name 'logger'»). Viene de `b88da9c`, que ya estaba antes del merge. Si esa rama se ejecuta, da `NameError` en lugar del aviso. No lo toqué; propongo una línea en `COLA-LIMPIEZA.md` o una pieza chica.

**Chequeo §6 del arreglo del merge** (`docs/pm/herramientas/chequeo-6.py 96052c8 515821a`), entero:

```
chequeo-6 96052c8..515821a: avisos para mirar, no un veredicto
producto +3/−2
arnés +9/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/security/file_security.py: 692 → 693
avisos: 0
```


### Merge con CSRF-1 y CSRF-2 (después de DESPACHO-1c)

| SHA | Qué |
|---|---|
| `04d88a5` | merge de tu rama hasta `6e71766` (CSRF-1). Conflicto en `main.py`, `logout_root`: quedó tu alias (`"""Alias de /auth/logout"""`, delega en `logout`) con la firma de SESION-1, o sea `return await logout(request, response, db)`. `logout` sigue revocando la sesión, así que borrar mi `revocar_sesion_de_la_request` del alias no pierde nada |
| `a7ed7b6` | test: una fixture `autouse` en `tests/conftest.py` apaga el limitador al empezar cada caso (`monkeypatch`, que lo deja como estaba al terminar). Con el tope de registros por IP, `test_csrf.py` y `test_prelaunch_block1.py` daban 429 corridos solos: dependían de que un caso anterior dejara el limitador apagado. Los casos que miden un tope lo prenden ellos. Producto +0/−0 |
| `5199709` | merge de tu rama hasta `72f92ba` (CSRF-2). Sólo conflicto en `CHANGELOG.md` (se unieron las entradas). El producto del merge es exactamente el tuyo |

**Tus sabotajes de CSRF no corren sobre una rama con SESION-1.** `csrf1.sh` y `csrf2.sh` buscan `    return await logout(request, response)`, y acá la línea termina en `, db)`. Sobre `5199709` cada uno dio un ROTO: «patrón no encontrado una sola vez (0)», en «el alias borra la cookie por su cuenta» (csrf1) y en «el alias responde sin cerrar la sesión» (csrf2). Todos los demás dieron ROJO. No es un defecto de producto. Corrí copias en mi scratchpad con ese único cambio en el patrón; el diff contra tus scripts es una línea en cada uno. Cuando integres SESION-1, esos dos patrones tienen que cambiar igual: no los toqué en el repo porque los scripts son tuyos.

---

## Tres entregas en `ca87d82` (2026-11-05): RENDIMIENTO-1c vuelta 2, DESPACHO-1b vuelta 6 y CATALOGO-LARGO-1

| Pieza | Resultado | Qué decidís |
|---|---|---|
| RENDIMIENTO-1c v2 | Un PDF normal que esperó lugar o se valida o recibe 503; ya no recibe 400. Validar tiene tope de 10 s de CPU (D50 b): pasarlo da 400 «demasiado pesado». | D55, D56 |
| DESPACHO-1b v6 | Un caso en Postgres agota los 3 intentos por las cuatro vías y fija qué contesta cada una; dos sabotajes, sobre el 3 y sobre el `else`. Sin cambios de producto. | nada |
| CATALOGO-LARGO-1 | Una descripción de hasta 2000 caracteres se guarda entera en la memoria del cliente y en el catálogo; con más, 400 y no guarda nada. | D53, D54 |

### Decisiones

- **D55. Leer un despacho todavía cobra la espera.** `leer_despacho_aparte` llama a `_leer_aparte` sin `hasta`: la espera por un lugar se descuenta de `PDF_READ_TIMEOUT_S` (120 s). Si la espera se come casi todo, el lector arranca con poco tiempo, vence con `TimeoutError` y `main.py` responde 504 «Leer el despacho tardó demasiado…». Es el mismo defecto que esta vuelta arregla en validar, pero en el otro camino, y la tarea pedía validar. No lo reproduje con un caso.
  - (a) Dejarlo: 120 s es mucho margen y el lector tiene un lugar por usuario (429 si ya está leyendo).
  - (b) Que leer siga el mismo patrón que validar: pasar `hasta`, un caso con la familia como datos y su sabotaje, dentro de RENDIMIENTO-1d.
  - **Recomiendo (b) dentro de RENDIMIENTO-1d.** Toca el mismo archivo y es una línea de producto; así `_leer_aparte` queda con un solo modo y desaparece la rama sin `hasta` (ver Riesgos).

- **D56. El peor caso de validar es 2 × `limite_s`.** Ahora la espera (fila del usuario más lugar libre) tiene `limite_s` y después el proceso tiene `limite_s` entero. Con `PDF_VALIDATE_TIMEOUT_S=30`, una subida puede tardar hasta 60 s antes de responder.
  - (a) Dejarlo así: cada mitad tiene su respuesta (503 si no hubo lugar, 400 si el archivo tardó), que es lo que pide la tarea.
  - (b) Un tope total por encima (por ejemplo, 2 × `limite_s` documentado, o la espera con su propia variable de entorno).
  - **Recomiendo (a).** El 503 llega a los 30 s como mucho; los 60 s sólo pasan si el PDF, una vez lanzado, tarda los 30 s del tope, y ese ya es un PDF que da 400.

D53 y D54 son de CATALOGO-LARGO-1 (abajo, sin cambios). Ninguna me frena: sigo con DESPACHO-1c.

### SHAs (base `bd46b4e`)

| SHA | Qué |
|---|---|
| `41d0b51` | test: RENDIMIENTO-1c v2, rojos de la espera que se cobra y del tope de CPU al validar |
| `6baaf91` | fix: RENDIMIENTO-1c v2, la espera por un lugar no se le cobra al PDF y validar tiene tope de CPU |
| `abf760f` | test: RENDIMIENTO-1c v2, sabotajes de la espera cobrada y del tope de CPU |
| `c73bf92` | test: el sabotaje de memoria de `despacho1b.sh` sigue al nombre nuevo de la salida |
| `6af219f` | test: DESPACHO-1b v6, el producto que no queda en 3 intentos |
| `c7c0571` | test: dos sabotajes de `despacho1b.sh` siguen a la sangría nueva del lector |
| `7b39fd2` | test: `despacho1b.sh` no juzga con la salida de un sabotaje anterior |
| `1994cb4` | fix: el docstring de `PdfDemasiadoPesado` dice que también sale por el tope de CPU |
| `ca87d82` | test: el sabotaje del tope de descripción del historial vuelve a distinguir (CATALOGO-LARGO-1, «Sabotajes») |
| este | docs: informe |

**Archivos de producto de esta vuelta:** `proyecto_maria/core/despacho_lector.py` (`validar_pdf`, `validar_pdf_aparte`, `_leer_aparte`, `_main`, `PdfDemasiadoPesado`) y `CHANGELOG.md`.

### Comandos

```bash
git checkout ca87d82
# «2 failed» sobre 3f0ed57 ([menos-que-un-pdf] y test_validar_tiene_tope_de_cpu); «11 passed» sobre ca87d82
<entorno de la suite> python -m pytest -q --no-cov tests/test_rendimiento1c.py
# 17 ROJO y «sabotajes con falla: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/rendimiento1c.sh ca87d82
# 11 ROJO y «sabotajes con falla: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/rendimiento1.sh ca87d82
# las 4 líneas «<vía>, el producto no queda en 3 intentos» en OK y «fallas: 0»
<venv>/bin/python -I scripts/testing/despacho1b_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/postgres
# los dos sabotajes de v6 en ROJO y «sabotajes sin rojo: 0»
PY=<venv>/bin/python PG_DSN=postgresql://<usuario>@127.0.0.1:<puerto>/postgres scripts/testing/sabotajes/despacho1b.sh ca87d82
```

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| `rendimiento1c.sh` | `ca87d82` | 17 ROJO, «sabotajes con falla: 0», salida 0 |
| `rendimiento1.sh` | `ca87d82` | 11 ROJO, «sabotajes con falla: 0», salida 0 |
| `despacho1b_postgres.py` | `ca87d82` | 22 OK, «fallas: 0», salida 0 |
| `despacho1b.sh` con `PG_DSN` | `1994cb4` | 138 ROJO, «sin Postgres, no corridos: 0», «sabotajes sin rojo: 0», salida 0 |
| `disco1.sh` con `PG_URL` | `ca87d82` | 46 ROJO, «sabotajes sin rojo: 0», salida 0 |
| `catalogolargo1.sh` con `PG_URL` | `ca87d82` | 12 ROJO, «fallas: 0», salida 0 |
| suite completa, mi comando, worktree limpio | `1994cb4` | «4303 passed, 336 skipped, 2 xfailed, 94 warnings in 530.80s (0:08:50)», salida 0 |
| suite completa, comando de `ci.yml` (10 `--deselect`, `-rs`), worktree limpio | `1994cb4` | «4293 passed, 336 skipped, 10 deselected, 2 xfailed, 92 warnings in 518.04s (0:08:38)», salida 0 |
| `compileall -q proyecto_maria tests` | `1994cb4` | sin salida, salida 0 |

Entre `1994cb4` y `ca87d82` sólo cambian `scripts/testing/sabotajes/disco1.sh` y `catalogolargo1.sh`: ni producto ni casos. Por eso las suites, `compileall` y `despacho1b.sh` quedan sobre `1994cb4`; los dos scripts que cambiaron y los que corrían después, sobre `ca87d82`.

**Por qué hay un `ca87d82`.** Sobre `1994cb4`, `disco1.sh` dio «ROJO? | sin tope de descripción»: el caso de confirmar seguía en rojo, pero no por el historial. `f31c1d3` (CATALOGO-LARGO-1) sumó `catalog_svc.validar_largo` en guardar-uso, y 2001 letras ya las frena ese tope antes que el del historial. En `ca87d82` el sabotaje de `disco1.sh` se ancla en el caso de importar, y `catalogolargo1.sh` suma uno que se pone rojo en `[nfd-que-achica]` (2002 caracteres tal cual, 1001 en NFC: sólo lo frena el tope del historial). Además, una primera corrida de `disco1.sh` se cortó por el tiempo máximo de mi herramienta, no por un rojo; la de la tabla es entera.

`disco1.sh` lo corrí porque pediste correrlo con PG antes de integrar `5c46e36`.

**Lo que no corrí:** la imagen Docker de producción, el smoke y el ataque de aislamiento (nada de esto toca sesión ni permisos).

---

## RENDIMIENTO-1c, vuelta 2: **entregada**

**Resultado:** al subir un PDF, la espera tiene su propio tiempo y la corrida el suyo. `validar_pdf_aparte` fija `hasta = ahora + limite_s` antes de la fila; la fila del usuario y el lugar libre se esperan hasta `hasta`, y si vence, `SinLugar` → 503 «Hay muchos PDFs en revisión. Probá de nuevo en un rato.». Una vez lanzado, el proceso tiene `limite_s` entero; si vence ahí, `TimeoutError` → 400 «tardó demasiado». Así un PDF normal nunca recibe 400 por haber esperado. Validar corre además bajo `_tope_de_cpu(10 s)`; pasarlo sale por el mismo código de salida que la memoria y da 400 `PDF_DEMASIADO_PESADO` (D50 b). Leer un despacho no cambia de significado: `SinLugar` si no llegó a lanzarse, `TimeoutError` si sí, y sigue cobrando la espera (D55).

### Conteo, corregido

Tenías razón. Mi informe anterior decía `+126/−53` «CHANGELOG incluido», y era falso: `ccf5d8c`, `843cc08`, `9fd6bd0`, `a341966` y `5819029` suman `proyecto_maria/` +126/−53, y el CHANGELOG +11/−1; en total, +137/−54, tu número.

Esta vuelta: **producto +51/−43** (chequeo-6, sólo `despacho_lector.py`), +55/−43 con el CHANGELOG. Netas +8.

### Rojo

`tests/test_rendimiento1c.py`, sobre `3f0ed57`:

```
FAILED tests/test_rendimiento1c.py::test_esperar_casi_todo_el_tope_no_culpa_al_archivo[menos-que-un-pdf]
FAILED tests/test_rendimiento1c.py::test_validar_tiene_tope_de_cpu - Assertio...
=================== 2 failed, 9 passed, 5 warnings in 35.02s ===================
```

`test_esperar_casi_todo_el_tope_no_culpa_al_archivo` es un caso con la familia como datos (tope 2 s; B y C ocupan los dos lugares y los liberan X s antes del tope; A sube un PDF normal):

| id | libera antes del tope | acepta |
|---|---|---|
| `casi-todo` | 0,5 s | «pasó» |
| `menos-que-un-pdf` | 0,08 s | «pasó» |
| `justo` | 0 s | «pasó» o 503 |
| `pasado` | −0,2 s | 503 |

**Lo que distingue el defecto es sólo `menos-que-un-pdf`.** `casi-todo` pasa en la base porque 0,5 s alcanzan para un PDF normal (~0,125 s); `justo` y `pasado` aceptan 503, que la base también daba. El caso comprueba que el PDF normal tarda más de 0,08 s, así que `menos-que-un-pdf` no puede pasar en la base por casualidad. Las otras tres quedan para fijar el borde: que no se vuelva 400 en ninguno.

`test_validar_tiene_tope_de_cpu` pone el tope en 0,05 s: un PDF trabajoso (`pdf_que_se_infla(repeticiones=10, claves=50_000)`, 0,23 a 0,29 s de CPU medidos) da (400, PESADO) y uno normal (~0,0004 s) pasa.

### Sabotajes

`rendimiento1c.sh`, sobre `abf760f` (sobre `ca87d82`, en Puertas): 17 ROJO, «sabotajes con falla: 0». Los cuatro nuevos:

| Sabotaje | Rojo |
|---|---|
| la espera por un lugar se descuenta del tiempo para validar | `[menos-que-un-pdf]` |
| validar no corre bajo el tope de CPU | `test_validar_tiene_tope_de_cpu` |
| el proceso aparte no le pasa el tope a validar | `test_validar_tiene_tope_de_cpu` |
| pasar el tope de CPU no sale como demasiado pesado | `test_validar_tiene_tope_de_cpu` |

Salida entera sobre `ca87d82`:

```
ROJO  | validar el PDF vuelve al proceso de la app: dice «FAILED tests/test_rendimiento1c.py::test_un_pdf_que_se_infla_no_hace_crecer_la_app»
ROJO  | sin fila por usuario: todas las validaciones comparten los dos lugares: dice «B esperó detrás de las bombas de A»
ROJO  | la subida de facturas no pasa el usuario: dice «B esperó detrás de las bombas de A»
ROJO  | vuelve a contar páginas antes de mirar si está encriptado: dice «FAILED tests/test_rendimiento1c.py::test_validar_aparte_devuelve_lo_mismo_que_antes»
ROJO  | un validador que se cae vuelve a ser un PDF inválido: dice «FAILED tests/test_rendimiento1c.py::test_un_validador_que_se_cae_es_un_error_nuestro»
ROJO  | la lectura de despachos no pasa el usuario: dice «despacho: B esperó detrás de las bombas de A»
ROJO  | esperar el turno del usuario no tiene tiempo máximo: dice «FAILED tests/test_rendimiento1c.py::test_esperar_un_lugar_no_culpa_al_archivo»
ROJO  | sin tope de validaciones a la vez: dice «(['b', 'c'], 'pasó')»
ROJO  | la fila del usuario no se borra: dice «(['b', 'c'], {'»
ROJO  | esperar un lugar libre vuelve a culpar al archivo: dice «(['b', 'c'], (400, 'No pudimos abrir el PDF: tardó demasiado»
ROJO  | la espera por un lugar se descuenta del tiempo para validar: dice «FAILED tests/test_rendimiento1c.py::test_esperar_casi_todo_el_tope_no_culpa_al_archivo[menos-que-un-pdf]»
ROJO  | validar no corre bajo el tope de CPU: dice «FAILED tests/test_rendimiento1c.py::test_validar_tiene_tope_de_cpu»
ROJO  | el proceso aparte no le pasa el tope a validar: dice «FAILED tests/test_rendimiento1c.py::test_validar_tiene_tope_de_cpu»
ROJO  | pasar el tope de CPU no sale como demasiado pesado: dice «FAILED tests/test_rendimiento1c.py::test_validar_tiene_tope_de_cpu»
ROJO  | esperar el turno del usuario vuelve a culpar al archivo: dice «(['a'], (400, 'No pudimos abrir el PDF: tardó demasiado»
ROJO  | sin lugar vuelve a ser un 400: dice «(['b', 'c'], (400, 'No pudimos abrir el PDF: tardó demasiado»
ROJO  | quedarse sin memoria en C vuelve a ser un PDF inválido: dice «DID NOT RAISE»
sabotajes con falla: 0
```

`rendimiento1.sh`: 11 ROJO, «sabotajes con falla: 0». `despacho1b.sh` cambió dos veces por esta vuelta (`c73bf92`, `c7c0571`): el nombre de la salida y la sangría del lector movían sus patrones.

### Revisiones

`/code-review high` sobre `bd46b4e..7b39fd2`:

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | El peor caso de validar es 2 × `limite_s` | D56 |
| 2 | Leer despacho cobra la espera y da 504 | D55 |
| 3 | `_leer_aparte` tiene dos modos según `hasta` | Propuesta para `COLA-LIMPIEZA.md`; desaparece con D55 (b) |
| 4 | El docstring de `PdfDemasiadoPesado` decía sólo memoria | Arreglado en `1994cb4` |
| 5 | La espera de la fila usa `limite_s` y no `hasta - ahora` | Son lo mismo: `hasta` se fija justo antes. Riesgo bajo |
| 6 | `despacho1b.sh` juzgaba un sabotaje con la salida del anterior (`ULTIMA`) | Arreglado en `7b39fd2` |
| 7 | El margen de CPU del caso | Medido: normal ~0,0004 s contra 0,05; trabajoso 0,23 a 0,29 s. Sin cambio |

Adversario Opus, esfuerzo alto (`adversario-opus-alto`): F1 era el mismo docstring (arreglado); F2 a F5 van en Riesgos. `/security-review` del diff de producto: sin hallazgos.

### Riesgos

- D55 y D56.
- El tope de CPU se mide con la señal de CPU del proceso aparte: una función en C de pypdf que no suelta el control lo pasa por un rato; después corta el tiempo de pared de `limite_s`.
- Un PDF que pasa el tope de CPU da el mismo 400 que uno que pasa el de memoria («demasiado pesado»): para quien sube es lo mismo, pero el registro no dice cuál de los dos fue.
- `_leer_aparte` queda con dos modos según venga `hasta` (Revisiones, 3).

**Propuesta para `COLA-LIMPIEZA.md`:** `_leer_aparte` con un solo modo (siempre con `hasta`), si D55 no va por (b).

### Chequeo §6

```
chequeo-6 bd46b4e..ca87d82: avisos para mirar, no un veredicto
producto +51/−43
arnés +239/−34
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 867 → 875
avisos: 0
```

---

## DESPACHO-1b, vuelta 6: **entregada**

**Resultado:** `despacho1b_postgres.py` tiene `nunca_queda`: un trigger `BEFORE INSERT ... FOR EACH ROW` sobre `client_product_history` (sólo para descripciones `NUNCA QUEDA …`) suma uno a una secuencia y devuelve `null`, así que la fila no queda nunca. Por cada vía comprueba que hubo **3 intentos**, **ninguna fila** y esta respuesta:

| Vía | Respuesta |
|---|---|
| guardar | 500 |
| operación | 200 con `historial_guardado: false` |
| guardar-uso | 200 con `historial_guardado: false` |
| aprender | 200 con `aprendidos: 0` |

Al final borra el trigger, la función y la secuencia. Usé un solo trigger que descarta la fila en vez de tu *sugerencia* (crear y borrar en dos triggers): es más corto y llega al mismo `else` de `client_memory.py:228-234`.

**Frase corregida:** «si las 3 fallan, sale un error (500), nunca un 200 mudo» vale sólo para guardar. Operación y guardar-uso responden 200 con `historial_guardado: false`, y aprender responde 200 sin contarlo en `aprendidos`.

Salida, sobre `ca87d82`:

```
OK    | operacion, el producto no queda en 3 intentos: lo dice: 200 {"success":true,"operation_id":"297c3054-06a8-4ea7-bd82-8da55cc0225c","op_code":"OP-000003","historial_guardado":false}, intentos 3, filas 0
OK    | aprender, el producto no queda en 3 intentos: lo dice: 200 {"success":true,"cliente_id":"44729cff-9cfd-471a-980e-c3ed9aa48a7d","aprendidos":0}, intentos 3, filas 0
OK    | guardar, el producto no queda en 3 intentos: lo dice: 500 {"detail":"No pudimos procesar tu solicitud. Probá de nuevo en unos segundos. Si vuelve a pasar, escribinos a hola@ynera.com.ar y te ayudamos.","code":"internal, intentos 3, filas 0
OK    | guardar-uso, el producto no queda en 3 intentos: lo dice: 200 {"success":true,"historial_guardado":false}, intentos 3, filas 0
fallas: 0
```

### Sabotajes nuevos en `despacho1b.sh`

| Sabotaje | Rojo |
|---|---|
| el upsert intenta 2 veces (`range(3)` → `range(2)`) | las cuatro vías: «<vía>, el producto no queda en 3 intentos» |
| el upsert que no pudo guardar se calla (`raise RuntimeError(...)` → `return None`) | sólo «guardar, el producto no queda en 3 intentos»; además el script comprueba que operación, aprender y guardar-uso sigan en `OK`, y si no, marca `ANCHO` |

El segundo es el 200 mudo de guardar que no tenía rojo: con `return None`, guardar contesta 200; las otras tres vías ya contestan lo mismo con o sin el `raise`, por eso el rojo tiene que ser sólo el de guardar.

Salida, sobre `1994cb4`:

```
ROJO  | el upsert intenta 2 veces: «FALLA | operacion, el producto no queda en 3 intentos» «FALLA | aprender, el producto no queda en 3 intentos» «FALLA | guardar, el producto no queda en 3 intentos» «FALLA | guardar-uso, el producto no queda en 3 intentos»
ROJO  | el upsert que no pudo guardar se calla: «FALLA | guardar, el producto no queda en 3 intentos»
```

---

## CATALOGO-LARGO-1: **entregada** (el producto termina en `7bcb7b9`; las puertas, también sobre `ca87d82`)

**Resultado:** con cliente y proveedor, una descripción de 301 a 2000 caracteres se guarda entera en la memoria del cliente y en el catálogo; con 2001 o más, guardar-uso y el catálogo (guardar y cambiar) responden 400 «La descripción pasa de 2000 caracteres.» y no guardan nada. En Postgres 16, `catalogo_largo1_postgres.py` arranca `e099744` sobre una base descartable y después esta versión: con el producto viejo da «fallas: 6» (301, 501 y 2000 responden `200 {"success":true,"historial_guardado":false}` con 0 filas en las dos memorias); con el nuevo, «fallas: 0». La migración pasa `product_key` y `descripcion` del catálogo a `text`; si no puede (por ejemplo, otra conexión tiene tomada la tabla), **el arranque no sigue**: antes de este cambio el arranque seguía con las columnas cortas y guardar-uso volvía a responder 200 sin guardar. `catalogolargo1.sh` con `PG_URL`: 12 ROJO, «fallas: 0» (sobre `ca87d82`). La suite completa sobre `7bcb7b9`, desde un worktree limpio: «4298 passed», y con el comando de la CI «4288 passed, 10 deselected»; 0 failed en las dos.

### Decisiones

- **D53. La pantalla no muestra el 400.** El backend ya no responde 200 sin guardar, pero las dos pantallas que llaman tragan el error: `static/v2/screens/ncm.js:1822` (`saveNcmUsage`, `catch (_) { /* best effort */ }`) y `static/v2/screens/finalize.js:1307` (aprender el catálogo, ídem). Con 2001 caracteres el usuario no ve nada y el producto no queda guardado. Si «a la vista» en la tarea quiere decir en la pantalla, esto no lo cumple.
  - (a) Alcanza con el 400 en la respuesta: la pieza queda como está.
  - (b) Pieza aparte y chica, junto con la D51: las dos pantallas muestran el aviso cuando llega un 400 o `historial_guardado: false`.
  - **Recomiendo (b).** Es la misma pantalla y el mismo patrón que la D51; tocarla acá mezcla pantalla con datos.

- **D54. Si la migración no puede pasar las columnas a texto, la app no arranca.** Elegí esto porque la alternativa, seguir con el tope viejo, es exactamente el 200 sin guardar que la tarea prohíbe. Railway reintenta hasta 10 veces (`ON_FAILURE`) y cada intento espera la tabla 5 s como mucho (`lock_timeout`). Si algo la tiene tomada más que eso, el despliegue queda caído. Hay precedente: `_migrate_product_history_clave` (DESPACHO-1b) también corta el arranque.
  - (a) Dejarlo así.
  - (b) Que no corte el arranque y que guardar-uso y el catálogo respondan 503 mientras las columnas sigan cortas: más código y un chequeo por pedido.
  - **Recomiendo (a).** La tabla es chica, el `ALTER` a `text` desde `varchar` no reescribe la tabla en Postgres y sólo se hace una vez.

Ninguna me frena: sigo con DESPACHO-1c.

### SHAs

| SHA | Qué |
|---|---|
| `15929f5` | test: rojos de la descripción larga en guardar-uso y el catálogo |
| `300c125` | fix: una descripción de hasta 2000 caracteres se guarda entera en el catálogo y en la memoria del cliente |
| `613c71a` | refactor: el largo se valida dentro del bucle de `save_products` |
| `0fa45f7` | test: prueba en Postgres 16 y sabotajes |
| `5e81ef6` | test: el sabotaje de la migración con la sangría del código |
| `f31c1d3` | fix: el historial vuelve a medir el texto tal cual y guardar-uso suma el tope del catálogo (code-review 1, 2, 6 y 8); `lock_timeout` |
| `bd7b9cd` | test: casos en escapes, importar el historial y el NCM que no es producto |
| `dd805b8` | test: `disco1.sh` y `despacho1b.sh` vuelven a sus patrones; el sabotaje del NCM que no es producto queda en `despacho1b.sh` |
| `0223c28` | fix: comentario del tope en dos líneas y entrada del CHANGELOG |
| `38fbe01` | test: con la tabla tomada el arranque tiene que fallar (adversario Opus, hallazgo 1) |
| `7bfd3a8` | fix: si el arranque no puede pasar el catálogo a texto, no arranca |
| `7bcb7b9` | test: el arranque fallido libera su pool y sabotaje que vuelve a tragar el error |
| `ca87d82` | test: el sabotaje del tope de descripción del historial vuelve a distinguir (abajo, «Sabotajes») |
| este | docs: informe |

**Archivos de producto:** `core/catalog_service.py` (`MAX_DESCRIPCION`, `validar_largo`, `save_products`, `update_product`), `database/models.py` (`VendorCatalogProduct.product_key` y `descripcion` a `Text`), `services/client_memory.py` (el tope del historial usa la misma constante) y `main.py` (`_migrate_catalogo_sin_tope`, `lifespan`, `guardar_uso_ncm`, `catalog_save_products`, `catalog_update_product`, `_validate_product_key`).

### Cómo queda

- El tope es uno: `catalog_service.MAX_DESCRIPCION = 2000`. El catálogo y guardar-uso lo miden en NFC con `validar_largo`, porque la memoria del cliente guarda en NFC. El historial de NCM (`_problema_historial`) guarda el texto tal cual y lo mide así; por eso «e + acento» × 1001 (2002 tal cual, 1001 en NFC) entra al catálogo pero guardar-uso lo rechaza con 400, sin guardar en ninguna de las dos memorias.
- La clave de la URL (`PUT`/`DELETE`) acepta hasta 2000; antes, 500.
- Las columnas pasan a `text` sin tope en la base: el tope lo pone el código y responde 400, en vez de que Postgres corte con un error que terminaba en 200.

### Comandos

```bash
git checkout ca87d82
# 12 ROJO y «fallas: 0»; sin PG_URL tendría que dar 10 ROJO y «SALTO | sin PG_URL» (esa variante no la corrí sobre ca87d82)
PY=<venv>/bin/python PG_URL=postgresql://<usuario>@127.0.0.1:<puerto>/postgres scripts/testing/sabotajes/catalogolargo1.sh ca87d82
# 10 OK y «fallas: 0»; con el producto de e099744, «fallas: 6»
<venv>/bin/python scripts/testing/catalogo_largo1_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/postgres
# «12 passed»
<entorno de la suite> python -m pytest -q --no-cov tests/test_catalogo_largo1.py
```

### Rojos antes del arreglo

Los casos de `15929f5` sobre el producto de `e099744`:

```
FAILED tests/test_catalogo_largo1.py::test_guardar_uso_guarda_en_las_dos_memorias_o_da_400[nfd-que-achica]
FAILED tests/test_catalogo_largo1.py::test_guardar_uso_guarda_en_las_dos_memorias_o_da_400[nfc-que-crece]
FAILED tests/test_catalogo_largo1.py::test_guardar_en_el_catalogo_respeta_el_tope[2001]
FAILED tests/test_catalogo_largo1.py::test_guardar_en_el_catalogo_respeta_el_tope[nfc-que-crece]
FAILED tests/test_catalogo_largo1.py::test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas
=================== 5 failed, 4 passed, 3 warnings in 2.74s ====================
```

Los 4 que pasan en la base son los casos que SQLite no puede mostrar (no controla el largo de las columnas): esos los cubre la prueba en Postgres. La misma, con el producto de `e099744`:

```
FALLA | primer arranque: las columnas son text y el producto viejo queda igual: [('descripcion', 'character varying', 500), ('product_key', 'character varying', 300)]
FALLA | segundo arranque: las columnas son text y el producto viejo queda igual: [('descripcion', 'character varying', 500), ('product_key', 'character varying', 300)]
FALLA | guardar-uso con 301 caracteres se guarda entero en las dos memorias: 200 {"success":true,"historial_guardado":false} historial 0 catálogo 0
FALLA | guardar-uso con 501 caracteres se guarda entero en las dos memorias: 200 {"success":true,"historial_guardado":false} historial 0 catálogo 0
FALLA | guardar-uso con 2000 caracteres se guarda entero en las dos memorias: 200 {"success":true,"historial_guardado":false} historial 0 catálogo 0
FALLA | el catálogo guarda, cambia y borra un producto de 2000: 500 400 {"detail":"product_key inválido"} 400 {"detail":"product_key inválido"}
fallas: 6
```

Con la tabla tomada, sobre `38fbe01` (la migración todavía tragaba el error):

```
⚠️ Migracion catalogo_sin_tope (no critica): DBAPIError(... LockNotAvailableError: canceling statement due to lock timeout)
FALLA | con la tabla tomada el arranque falla en vez de seguir con las columnas cortas: [('descripcion', 'character varying', 500), ('product_key', 'character varying', 300)]
fallas: 1
```

Sobre `7bfd3a8`: los 10 en OK y «fallas: 0».

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| `catalogolargo1.sh` con `PG_URL` | `7bcb7b9` | 11 ROJO, «fallas: 0», salida 0 |
| `catalogolargo1.sh` y `disco1.sh` con `PG_URL` | `ca87d82` | en «Puertas», arriba |
| `despacho1b.sh` y las dos suites | `1994cb4` | en «Puertas», arriba |
| suite completa, mi comando, worktree limpio | `7bcb7b9` | «4298 passed, 336 skipped, 2 xfailed, 95 warnings in 511.89s», salida 0 |
| suite completa, comando de `ci.yml` (10 `--deselect`, `-rs`), worktree limpio | `7bcb7b9` | «4288 passed, 336 skipped, 10 deselected, 2 xfailed, 94 warnings in 502.35s», salida 0 |
| `compileall` | `7bcb7b9` | sin salida, salida 0 |

`despacho1b.sh` y `disco1.sh` los corrí porque `dd805b8` cambia sus patrones; van sobre `1994cb4` y `ca87d82`, que contienen `7bcb7b9`.

**Lo que no corrí:** la imagen Docker de producción, el smoke y el ataque de aislamiento (la pieza no toca sesión ni permisos). La migración no la probé contra una copia de la base de producción: sólo contra una base descartable creada por `e099744`.

### Sabotajes

En `catalogolargo1.sh`, uno por motivo:

| Sabotaje | Qué tiene que dar rojo |
|---|---|
| el catálogo mide el largo sin pasar a NFC | `test_guardar_en_el_catalogo_respeta_el_tope[nfc-que-crece]` |
| el tope no deja entrar el máximo (`>=`) | `test_guardar_en_el_catalogo_respeta_el_tope[2000]` |
| guardar en el catálogo no controla el largo | `test_guardar_en_el_catalogo_respeta_el_tope[2001]` |
| cambiar un producto no controla el largo | `test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas` |
| guardar-uso no controla el largo en NFC | `test_guardar_uso_guarda_en_las_dos_memorias_o_da_400[nfc-que-crece]` |
| el historial mide el largo en NFC | `test_importar_el_historial_mide_el_texto_como_lo_guarda` |
| guardar-uso no controla el largo como lo guarda el historial (`_HISTORIAL_MAX_DESCRIPCION` sin tope) | `test_guardar_uso_guarda_en_las_dos_memorias_o_da_400[nfd-que-achica]` |
| el catálogo da 500 en vez de 400 al guardar | `test_guardar_en_el_catalogo_respeta_el_tope[2001]` |
| el catálogo da 500 en vez de 400 al cambiar | `test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas` |
| la clave de la URL vuelve a tener tope de 500 | `test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas` |
| el arranque no pasa las columnas a text (Postgres) | «FALLA \| primer arranque: las columnas son text» |
| el arranque sigue si la migración falla (Postgres) | «FALLA \| con la tabla tomada el arranque falla» |

### Revisiones

`/code-review high` sobre `e099744..0223c28`, 10 hallazgos:

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | La migración tragaba todo error y no tenía `lock_timeout` | `f31c1d3` suma el timeout; `7bfd3a8` la hace fatal |
| 2 | `_problema_historial` medía en NFC para todas las vías | Arreglado en `f31c1d3`: el historial mide tal cual; caso `importar_el_historial` y sabotaje |
| 3 | `historial_guardado=False` con `entry is None` sin caso | Queda como riesgo (abajo) |
| 4 | Un comentario decía «en NFC como se guarda» del catálogo | Corregido: mide en NFC como la memoria del cliente |
| 5 | CRECE y ACHICA escritos con caracteres literales | Escapes `\u` |
| 6 | El chequeo del largo, repetido | Unificado en `catalog_svc.validar_largo`. Quedan `despacho_lector._MAX_DESCRIPCION` y `_HISTORIAL_MAX_DESCRIPCION` aparte: propuesta para `COLA-LIMPIEZA.md` (abajo) |
| 7 | Faltaba el CHANGELOG | Agregado |
| 8 | Import dentro de la función | Usa `catalog_svc` del módulo |
| 9 | Parametrize repetido | Una lista `CASOS` |
| 10 | `sql()` de la prueba dejaba conexiones abiertas | `contextlib.closing` |

Adversario Opus, esfuerzo alto (`adversario-opus-alto`), sobre `0223c28`:

| # | Sev | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | Alta | Si la migración falla, el arranque sigue y guardar-uso vuelve a dar 200 sin guardar | Reproducido (rojo arriba) y arreglado en `7bfd3a8`; D54 |
| 2 | Alta | Sin `lock_timeout`, el arranque se cuelga con la tabla tomada | Arreglado en `f31c1d3` |
| 3 | Media | La pantalla ignora el 400 | D53 |
| 4 | Media | `vendor_nombre` de más de 200 u `origen` de más de 5 dan 200 con `historial_guardado: false`; NCM de más de 20, NUL, `\ud800` o NCM numérico dan 500 | Existía antes: riesgo |
| 5 | Baja | Aprender con 2001 productos da 200 con uno menos y sin motivo | Existía antes: riesgo |
| 6 | Baja | En SQLite 4 casos pasan en la base; lo central está en la prueba de Postgres, que no corre en la CI; la rama `entry is not None` sin caso | Riesgo |
| 7 | Baja | `api_logs.endpoint` es `varchar(200)` y una URL con clave larga no entra | Riesgo |
| 8 | Baja | `despacho_lector._MAX_DESCRIPCION` aparte | `COLA-LIMPIEZA.md` |

Adversario Sonnet, esfuerzo alto (`adversario-sonnet-alto`), sobre `300c125`, 8 hallazgos: la pantalla ignora el error (D53); descripciones sin letras latinas dan 200 sin guardar (D52, existía); el costo de comparar contra el catálogo largo, 3 a 6 s con 2000 caracteres (riesgo); 500 con NUL, surrogates o NCM de más de 20 (existía); el rollback por `vendor`/`origen` de más da 200 con `historial_guardado: false` (existía); uno cosmético; `api_logs` `varchar(200)` (riesgo); la migración tragada (arreglada en `7bfd3a8`).

`/security-review`: sin hallazgos de confianza alta. Nota baja: el `except ValueError` del catálogo pasaría a 400 un error de programación que hoy sería 500.

### Riesgos

- La prueba en Postgres no corre en la CI: en SQLite los casos de 301 a 2000 pasan también en la base vieja.
- `save_products` hace `SELECT` y después `INSERT`: dos pedidos a la vez con el mismo producto nuevo pueden chocar. Existía antes.
- `guardar_uso_ncm` llama a `validar_largo` también sin `vendor_name`: una descripción que en NFC pasa de 2000 da 400 aunque no vaya al catálogo. Supuesto reversible: una sola regla para guardar-uso.
- El `except ValueError` de los dos endpoints del catálogo.
- Comparar contra el historial con descripciones de 2000 cuesta más (el adversario Sonnet midió 3 a 6 s); no lo medí yo.

**Propuesta para `COLA-LIMPIEZA.md`:** unificar `despacho_lector._MAX_DESCRIPCION` y `_HISTORIAL_MAX_DESCRIPCION` con `catalog_service.MAX_DESCRIPCION`.

### Chequeo §6

```
chequeo-6 e099744..HEAD: avisos para mirar, no un veredicto
producto +47/−8
  AVISO producto suma 39 líneas netas: el informe dice por qué (§6: más de 20)
arnés +463/−10
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 572 → 584
  proyecto_maria/database/models.py: 578 → 578
  proyecto_maria/main.py: 11334 → 11363
  proyecto_maria/services/client_memory.py: 304 → 302
avisos: 1
```

El `AVISO` queda: de las 39 líneas netas, unas 20 son la migración (Postgres la necesita, el modelo solo no cambia una columna que ya existe) y el resto `validar_largo` con sus tres respuestas 400.

