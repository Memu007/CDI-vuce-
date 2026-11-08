# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## AVISOS-1: **entregada**, producto y pruebas en `0aed334` (2026-11-08)

Base `e6adea1`. Son tres cosas, y no cambia lo que sale en un TXT que se
genera: cambia cuándo no se genera y lo que la persona lee.

1. **Exportación con algo adelante (D123).** `EC01` con un invisible
   (`​`, `﻿`, `⁠`), un nulo, un relleno Hangul (`ㅤ`,
   `ﾠ`), un espacio, un guion o escrito en ancho completo (`ＥＣ01`)
   generaba 200 con un TXT de importación (`ISTA=​EC0`). Ahora generar,
   los avisos y el generador usan un solo predicado (`es_exportacion`:
   NFKC, mayúsculas, se saltea lo que no es letra o número ASCII adelante) y
   dan el 400 de siempre. **No lo puse donde dijo D123: va D129.**
2. **El seguro borrado al pasar a CIF.** Calcular el 1 % con FOB y pasar a
   un incoterm con el seguro en el precio lo borra (el freno sigue). Antes el
   400, los avisos, la nota y el semáforo decían «no pudimos leerlo de la
   factura». Ahora el pedido manda `seguro_borrado` y todos dicen: «Seguro:
   el que calculó el sistema se borró al pasar a un incoterm que ya lo lleva
   en el precio. Cargá el de la factura en la revisión; si la factura no trae
   seguro, escribí 0.» La marca se va al recalcularlo o escribir un valor;
   vaciar el campo no la saca. De vuelta a FOB la nota sigue diciendo que se
   borró.
3. **El motivo donde cae la persona.** Ante el 400 del seguro la pantalla
   vuelve a la revisión y el motivo queda debajo del campo, marcado en rojo y
   llevado a la vista (`marcarEnLaRevision`). La pista dice «Si la factura no
   trae seguro, escribí 0.» en vez de «Dejar en 0 si no aplica». Caso de la
   familia, cada 400 que cambia de pantalla: sub-ítem (NCM), sufijo (generar),
   seguro en el precio, seguro sin leer, seguro borrado.

| SHA | qué |
|---|---|
| `7a2961f` | fix: EC con un invisible adelante (primera versión) |
| `8df6d91` | test: lo que va delante de EC, caso y arnés `avisos1.sh` |
| `a94ed02` | test: el arnés compara el id de pytest con la barra escrita |
| `e2864dc` | merge de tu rama (SEGURO-2 aceptada) |
| `d7345fa` | fix: un solo predicado de exportación (generar, avisos, generador) |
| `2ebf5b0` | test: rellenos, ancho completo, generador directo |
| `efb9c07` | fix: el seguro borrado dice lo que pasó; el motivo en la revisión; la pista + CHANGELOG |
| `491f2a3` | test: sus casos y sabotajes |
| `cec3564` | fix: el semáforo y la nota de FOB; vaciar el campo no saca la marca; el campo a la vista + CHANGELOG |
| `0aed334` | test: esos casos y sabotajes; un patrón de `seguro2.sh` sigue al código |
| `3af69c0` | merge de tu rama (sólo `docs/pm/`; producto y pruebas iguales a `0aed334`) |
| `dc2943d` | test: EMAIL-1 empezada (un email vacío no encuentra la cuenta sin email); fuera de esta entrega |
| este commit | docs: este informe |

`producto +54/−16`. Suma 38 netas: el predicado único con su constante (y
el import en `main.py`), el texto del borrado y su campo en el pedido, la
marca que se pone y se saca en la pantalla y en el semáforo, y
`marcarEnLaRevision`, que va aparte.

## Decisiones

**D129.** D123 (a) dice que el rechazo de exportación va después de limpiar
los textos. No lo moví. Evidencia: `limpiar_texto` sólo saca el nulo; no
saca `​`, `ㅤ` ni el espacio, así que moverlo no arregla la
familia. Y después de `_textos_como_van_al_txt` el chequeo queda detrás del
400 `SIN_PRODUCTOS` cuando `items: []`, y esa exportación recibía otro
motivo. Lo que sí resuelve la familia es el predicado (NFKC + saltear lo que
no es letra o número adelante), que es el mismo en los dos endpoints y en el
generador.

- (a) dejarlo antes, con el predicado único (lo entregado; recomiendo);
- (b) además moverlo después de limpiar, como dijo D123, aceptando que el
  pedido sin ítems diga `SIN_PRODUCTOS`.

**D130.** Una lista blanca para `tipo_destinacion`: `^[A-Z]{2}\d{2}$` después
de NFKC, o 400. Hoy `​IC04` (importación, no se frena) sale con un ISTA
corrupto, y `0EC01` o `XEC01` pasan cortados a 4 (`0EC0`). Entraría también
`pdf_extractor.py:2035`, que sigue con `strip`. Hay precedente en
`_sanitize_op_default` (`main.py:2415`).

- (a) pieza chica aparte con la lista blanca (recomiendo: es lo que cierra
  los homoglifos de abajo);
- (b) no hacerlo.

Supuesto reversible: `-EC01` frena a propósito (es una exportación mal
escrita, no una importación).

Próxima D libre: D131 (la Dev técnica ya usó D127 y su próxima es D128; por eso las mías son D129 y D130).

## Comandos

```bash
git checkout 0aed334
# los casos de la pieza: tiene que dar «199 passed»
GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. ENVIRONMENT=test \
DATABASE_URL=sqlite+aiosqlite:///./test.db python -m pytest -q --no-cov -p no:randomly \
  tests/test_doc1_documentos.py tests/test_generar_maria_txt.py tests/test_avisos1_seguro.py \
  tests/test_seguro2.py tests/test_seguro1.py tests/test_valor1c.py
# negativos: cada uno «sabotajes sin rojo: 0»
PY=python scripts/testing/sabotajes/avisos1.sh 0aed334
PY=python scripts/testing/sabotajes/seguro2.sh 0aed334
python docs/pm/herramientas/chequeo-6.py e6adea1 0aed334
```

## Puertas sobre `0aed334`

| puerta | resultado |
|---|---|
| rojo antes del arreglo, EC (sobre la base) | `20 failed, 23 passed, 29 deselected` (`﻿EC01`, `​ EC01`, `ㅤEC01`, `ﾠEC01`, `-EC01`, `ＥＣ01`, generador directo) |
| rojo antes del arreglo, seguro y motivo | `12 failed, 1 passed` |
| rojo antes del segundo arreglo (semáforo, FOB, vaciar, a la vista) | `4 failed, 13 passed` |
| casos de la pieza | `199 passed, 3 warnings in 50.22s` |
| `avisos1.sh` (22 sabotajes) | `BASE 149 passed, 18 warnings in 11.30s`, 22 `ROJO`, «sabotajes sin rojo: 0», rc=0 |
| `seguro2.sh` (19 sabotajes) | `BASE 78 passed, 5 warnings in 20.72s`, 19 `ROJO`, «sabotajes sin rojo: 0», rc=0 |
| `node --check` de los tres JS | sin error |
| compileall | salida 0 (sólo los `SyntaxWarning` de `pdf_extractor.py:927` y `:936`, de antes) |
| suite completa (SQLite, `--timeout=300`) | `5345 passed, 335 skipped, 3 xfailed, 97 warnings in 1017.67s (0:16:57)`, salida 0 |
| suite como la CI (`ENVIRONMENT=testing`, sin `DATABASE_URL`; sin deseleccionar los presupuestos compartidos) | `5345 passed, 335 skipped, 3 xfailed, 94 warnings in 998.54s (0:16:38)`, salida 0 |
| smoke_friccion, ataque_aislamiento | **no corridos** (no toca sesión, datos ni permisos) |

Cambio en un arnés viejo: en `seguro2.sh`, «escribirlo a mano deja la marca»
ahora busca `delete op.seguro_calculado; delete op.seguro_dejado;` (la línea
sumó la marca de borrado detrás). El rojo que pide es el mismo.

`separadores1b.sh` está roto de antes: va a la cola de limpieza (te paso la
línea, `COLA-LIMPIEZA.md` no lo toco).

## chequeo-6

```
chequeo-6 e6adea1..0aed334: avisos para mirar, no un veredicto
producto +54/−16
  AVISO producto suma 38 líneas netas: el informe dice por qué (§6: más de 20)
arnés +331/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/maria_generator.py: 2321 → 2331
  proyecto_maria/main.py: 12072 → 12075
  proyecto_maria/static/v2/screens/finalize.js: 1436 → 1444
  AVISO comentario nuevo de 3 líneas: proyecto_maria/static/v2/screens/finalize.js:410 (§6: una o dos)
  proyecto_maria/static/v2/screens/review.js: 1181 → 1195
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/review.js:7 <anónima> 1175 → 1189, 3 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/semaforo.js: 407 → 410
avisos: 3
```

- **38 netas:** arriba, junto a `producto +54/−16`.
- **Comentario de 3 líneas en `finalize.js:410`:** reescribe en el lugar uno
  de 4 que ya estaba (el de `borrarSeguroCalculado`), para que diga la marca.
- **Función de más de 150 en `review.js:7`:** es la IIFE del módulo, no una
  función. Lo nuevo (`marcarEnLaRevision`) va aparte; lo que creció adentro
  son las tres líneas de la marca en `onFieldChange`.

## Hallazgos de la autorrevisión

`/code-review high` y `adversario-sonnet-alto` (Sonnet, alto). Todos
reproducidos con su rojo y arreglados en `d7345fa` y `cec3564`:

| hallazgo | arreglo |
|---|---|
| el patrón con `\W` dejaba pasar rellenos Hangul y ancho completo | NFKC + saltear lo no ASCII alnum |
| el generador directo seguía con `strip` | el mismo predicado |
| el semáforo decía «no pudimos leer» para el borrado | dice que se borró |
| de vuelta a FOB la nota decía «no pudimos leer» | dice que se borró |
| vaciar el campo sacaba la marca y el servidor volvía a «no pudimos leerlo» | sólo un valor escrito la saca |
| el motivo quedaba debajo de un campo fuera de la vista | se lleva a la vista |

## Riesgos

- Pasan como importación: homoglifos cirílicos o griegos de E y C,
  `E​C01`, `ÉC01`. Lo cierra D130.
- `pdf_extractor.py:2035` sigue con `strip` (D130).
- Al volver a la revisión, `populate`/`validateAll` y el `validateField` de
  continuar pueden limpiar el motivo marcado (`review.js` 241, 352, 988,
  1014, 1057, 1079, 1108, 1184). El caso cubre la entrada a la revisión, no
  cada uno de esos caminos.
- Qué pantalla toma el 400 se decide por regex sobre el texto del servidor:
  si cambia el texto, cambia el destino.
- `marcarEnLaRevision` repite el código de mostrar de `validateField`
  (va a la cola si querés unificarlos).
- Los casos de la exportación en el HTML y de la pista son búsquedas de
  texto; la fila «seguro en el precio» de la familia sólo mira la pantalla
  (el texto lo pintan los avisos).
- Con FOB y la marca de borrado, el 400 del servidor sigue diciendo «al
  pasar a un incoterm que ya lo lleva»: es verdad, pero ya no es el
  incoterm de ahora.
- Siguen sin tocar `31/02/2026` y `٥`.

## Archivos de producto

`proyecto_maria/main.py`, `proyecto_maria/core/maria_generator.py`,
`proyecto_maria/static/v2/screens/finalize.js`, `review.js`, `semaforo.js`,
`proyecto_maria/templates/dashboard_v2.html`, `CHANGELOG.md`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797WNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. AVISOS-1 entregada en 0aed334 (informe en este archivo), D129 y D130 abiertas, próxima D libre D131. Sigue EMAIL-1, después CONEXIONES-1, OBSERVABILIDAD-1, ORG-1+D40 y D102. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
