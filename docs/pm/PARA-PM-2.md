# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SEPARADORES-1c: entregada a revisión (2026-10-27)

**Antes:** la vuelta de SUFIJOS-1 sigue en tu revisión. Su informe es la
versión de este archivo en `76570de` (probada en `45a3ea1`, nada para
decidir).

**Resultado:** están hechos los tres puntos, cada uno con casos y
sabotajes.
- La factura deja sin leer los miles mal formados.
- El servidor toma como blanco sólo lo que la pantalla también toma como
  blanco.
- La pregunta escribe las dos lecturas con `escribir()` y conserva el
  signo.

Lo probado es `45a3ea1`, que tiene el mismo código de 1c que `9663ac6`.
`git diff 9663ac6 45a3ea1` sobre los cuatro archivos de producto y los tres
de prueba de 1c da vacío.

**Lo que decidís vos: D24 y D25**, abajo. Ninguna frena esta entrega. La
numeración sigue la de este canal (D22 y D23 fueron SUFIJOS-1). La D24 y
la D25 de `PARA-PM.md` y `PARA-DEV.md` son de la Dev técnica.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `90cc097`, `69a4593` |
| Producto y `CHANGELOG.md` | `4f2045f` |
| Casos de SEPARADORES-1b que cambian con 1c | `d5a3f58` |
| Caso del semáforo y sabotajes | `9663ac6` |
| **SHA probado:** suite, compileall, casos | **`45a3ea1`** |

Tu diff de revisión es `adfe707..9663ac6`, sólo sobre los archivos de 1c.
El resto de ese rango es SUFIJOS-1.

## Decisiones

**D24. La misma regla de miles para cantidades, precios y pesos de la
factura.** El punto 1 lo apliqué sólo a `_monto_factura`, que lee el flete y
el seguro. `_numero_factura` lee cantidad, valor unitario y pesos, y sigue
leyendo por mil lo mal formado. Corrido sobre `45a3ea1`:

```
0750.000 ,      monto None  numero 750000.0
7500.000.000 ,  monto None  numero 7500000000.0
02500.000 ,     monto None  numero 2500000.0
7500.000,50 ,   monto None  numero 7500000.5
```

Eso entra al FOB del TXT.
- **(a)** Una pieza chica aparte, con casos y sabotaje. Sería la misma
  regla en `_numero_factura`, y lo que no se lee queda vacío, como hoy con
  «12x3».
- **(b)** Dejarlo como está.

Recomiendo **(a)**. Es la misma familia y pega en el valor de la
mercadería, no sólo en el flete. No lo hice en esta pieza por dos razones:
la tarea habla de montos y tus ejemplos son flete y seguro, y cambiaría lo
que sale en el TXT por otro camino.

**D25. La forma decimal que propone la pregunta se acepta y el TXT
redondea sin aviso.** Seguí tu indicación: las dos lecturas con
`escribir()`. Para «2500.125» la pregunta propone «2500,1250».
- La pantalla lo lee como `2500.125`.
- El servidor lo lleva a `MDDTFLE=2500.13` sin avisar.
- Es lo que marcaste en el punto 3, ahora con otra forma escrita.

Corrido:

```
leer('2500,1250')                          → {"valor":2500.125,"error":null}
centavos(importe_valido(2500.125,'Flete')) → 2500.13
```

La causa es que `leer` acepta más de dos decimales. «No se toca» pide que
«1.234,567» se siga aceptando, así que no lo cambié.
- **(a)** Queda así. La forma propuesta se lee como dice la pregunta, y el
  redondeo es el mismo de cualquier importe con tres decimales.
- **(b)** Una pieza chica: la revisión avisa sin frenar cuando un importe
  tiene más de dos decimales («va al TXT como 2500,13»).
- **(c)** `leer` rechaza más de dos decimales. Contradice «No se toca».

Recomiendo **(b)**. Saca el «sin aviso», que era tu objeción, sin tocar lo
que se acepta.

## Qué cambió

Estos son los archivos que toqué:
- `proyecto_maria/pdf_extractor.py`
- `proyecto_maria/core/maria_generator.py`
- `proyecto_maria/core/controles_maria.py`
- `proyecto_maria/static/v2/montos_ar.js`
- `CHANGELOG.md`

- **1. Factura.** `_miles_mal_formados` corre antes de leer el flete o el
  seguro. Si la parte entera viene en grupos de miles con cero adelante, o
  con una cabeza de cuatro cifras o más, el monto queda en `None`.
  - Termina en flete 0 con el aviso de MARIA-1c, como pide «No se toca».
  - En la pantalla, `sonMiles` exige la cabeza sin cero: «01.500.000» no
    cierra.
  - La rama «cuatro cifras o más y tres decimales» también toma el cero
    adelante: «01234.500» pregunta.
- **2. Blanco.** Lo arreglé del lado del servidor.
  - `importe_valido` y los controles de la cabecera hacen
    `strip(ESPACIOS)`. `ESPACIOS` son sólo los blancos que `trim()` de JS
    también saca.
  - `\x85` y `\x1c`–`\x1f` ya no son blanco: llegan como texto y dan 400
    «no es un importe.». El semáforo dice lo mismo.
  - La pantalla no cambió. El campo vacío o con espacios comunes sigue
    siendo 0, también por API.
  - Un caso recorre todo el plano básico: lo que el servidor toma como
    blanco es un subconjunto de lo que saca `trim()`.
  - El BOM (`﻿`) lo saca `trim()` y el servidor no, así que por API da
    400 en vez de 0. Ya era así antes de 1c. Es más estricto, no un 0
    callado.
- **3. La pregunta.** Las dos lecturas se escriben con `escribir()` y
  conservan el signo, también en la rama de la coma:
  - «2500.125» → «¿2500125 o 2500,1250?»;
  - «-1234.500» → «¿-1234500 o -1234,5?»;
  - «-3,480» → «¿-3.480 o -3,48?».

  Un caso lee cada forma propuesta y comprueba que da lo que dice la
  pregunta. D25 es lo que pasa después, en el TXT.

## Supuestos reversibles

- **La forma «miles» va sin separador** («2500125»), no «2.500.125».
  `escribir()` no pone puntos de miles, y la tarea pide `escribir()` para
  las dos.
- **Más de quince cifras no pregunta: «Debe ser un numero.».** Pasado ese
  largo, `Number` ya no da las cifras exactas y la pregunta propondría otro
  número. Antes «1» repetido 199998 veces, con «.125», preguntaba
  «¿111.111.…».
- **Cambié dos casos de SEPARADORES-1b** (`d5a3f58`): la pregunta con el
  texto nuevo y la cifra larga con el error de arriba. Son consecuencia
  directa del punto 3. Si preferís otro texto, se revierte ahí.

## Puertas

Todo es sobre `45a3ea1`, salvo los sabotajes (`9663ac6`) y el smoke
(`252f04d`). Los tres tienen el mismo código de 1c.

| Puerta | Resultado |
|---|---|
| `test_separadores1c.py`, `1b` y `1` | `292 passed, 4 warnings in 57.17s` |
| `sabotaje_separadores1c.sh 9663ac6` | `OK: los 10 sabotajes dan rojo por la razón esperada`, salida 0 |
| Suite completa, worktree limpio, sola | `13 failed, 3077 passed, 302 skipped, 2 xfailed, 94 warnings in 452.55s (0:07:32)` |
| `compileall -q proyecto_maria` | rc 0 |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

Cada sabotaje vuelve a una lectura de antes:

| Sabotaje | Qué vuelve a como era |
|---|---|
| `factura_sin_regla` | la factura sin la regla de miles |
| `factura_cero_adelante` | la factura con cero adelante |
| `pantalla_miles_con_cero` | la pantalla acepta miles con cero adelante |
| `pantalla_no_pregunta_con_cero` | la pantalla no pregunta con cero adelante |
| `generador_strip_python` | `strip()` de Python en el generador |
| `controles_strip_python` | `strip()` de Python en los controles |
| `pregunta_sin_signo` | la pregunta sin el signo |
| `coma_sin_signo` | la rama de la coma sin el signo |
| `pregunta_tres_decimales` | la pregunta con tres decimales |
| `pregunta_sin_tope` | la pregunta sin el tope de quince cifras |

**Los 13 rojos** son los 12 conocidos más uno.
- **Los 12 conocidos:**
  - `test_guardar1`, que cierra CLIENTE-1c;
  - los 11 del tope de 15 operaciones (`clientes_plan02/04`,
    `maria4_despachante`, `op_code_and_fill_if_empty`, `operations_manual`
    y `prelaunch_block1`).
- **El otro es**
  `test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`,
  ya informado en SUFIJOS-1. Es de tiempo en este entorno, no de esta
  pieza:
  - corrido solo, da rojo también en tu `842d68a`: «normal: 400 en 30.2 s»;
  - `git diff 842d68a..45a3ea1 -- tests/test_excel2.py proyecto_maria/security`
    da vacío.

**Lo que no corrí:**
- Ni subagentes adversariales ni `/code-review`: no tengo cuota hasta el
  28/10 a las 18:00 UTC. La autorrevisión es sólo mía, sin independencia.
- `ataque_aislamiento.sh`: no toqué sesión, datos ni permisos.

## Comandos

Este muestra sólo lo de 1c:

```bash
git diff adfe707..9663ac6 -- proyecto_maria/pdf_extractor.py proyecto_maria/core/maria_generator.py \
  proyecto_maria/core/controles_maria.py proyecto_maria/static/v2/montos_ar.js
```

Este tiene que dar `292 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_separadores1c.py tests/test_separadores1b.py tests/test_separadores1.py
```

Este tiene que dar «OK: los 10 sabotajes dan rojo por la razón esperada» y
salida 0:

```bash
scripts/testing/sabotaje_separadores1c.sh 9663ac6 <venv>
```

## Riesgos

- **Con dos marcas distintas, `_separador_decimal` decide cuál es la
  decimal.** Si un PDF trae una forma rara («1.234.567,890,12»), la regla
  nueva la deja sin leer, que es el lado seguro.
- **Un solo grupo sin pista, como «02 750», queda sin leer. Antes daba
  2750** (corrido sobre `adfe707`).
  - Es lo que pide el punto 1: con espacio no puede ser decimal, y el cero
    adelante hace mal formado el grupo.
  - Si algún proveedor escribe así de verdad, ahora va con flete 0 y aviso.
- **D24 y D25**, arriba: el mismo defecto sigue por otros dos caminos.

Última vuelta: Tue Oct 27 19:30:30 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregadas a revisión la vuelta de SUFIJOS-1 (informe en 76570de, probada en 45a3ea1, nada para decidir) y SEPARADORES-1c (probada en 45a3ea1, 10 sabotajes; D24 miles en _numero_factura, recomiendo a; D25 aviso por más de 2 decimales, recomiendo b). Espero veredicto; no hay pieza marcada «apenas entregues». Sin cuota de subagentes ni /code-review hasta 28/10 18:00 UTC. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
