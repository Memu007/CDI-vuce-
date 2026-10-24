# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MARIA-7 — entregada a revisión (2026-10-24)

**Resultado:** los 9 puntos están hechos, con su rojo antes. La suite completa da
`1882 passed, 102 skipped, 2 xfailed`, sin rojos.
La e2e de la CI, la pantalla y el smoke dan verde sobre `f0b73f7`. Los 25
sabotajes dan rojo por la razón esperada. Las D1 a D8 de abajo son para vos,
o para preguntarle al despachante. Ninguna frena la entrega.

| Pieza | SHA |
|---|---|
| Base (tu rama al asignar) | `3dbfb4e` |
| Producto: lo que el MARIA rechazó el 24/10 (puntos 1 a 7) | `67d5688` |
| Casos del 24/10 y pruebas viejas con el CUIT del despachante | `39eef6c` |
| Producto: la tabla del despachante se desplaza en el teléfono | `c03bb1d` |
| Producto: punto 8, la fecha de la factura en su orden | `e3c68dc` |
| Casos de fechas, pantalla y sabotajes | `525c91b`, `7248141` |
| Producto: lo que encontró la autorrevisión | `449b157` |
| Casos de la autorrevisión, pantalla y sabotajes | `f08613f` |
| Merge de tu rama (`3fd8826`: EXCEL-3 y CLIENTE-1) | `3938330` |
| Producto: punto 9, fecha de inicio de actividad | `11d4ac1`, `e4e0336` |
| Casos y sabotajes del punto 9 | `35ba42d`, `f0b73f7` |
| **SHA probado** | **`f0b73f7`** |

## Decisiones

**D1. El largo y la unicidad de IDSO, IDDT e IARTESPAPU.**
- El largo máximo no está escrito ni en el código ni en `docs/`. Usé 8, que es
  lo que el MARIA aceptó: son los últimos 8 caracteres alfanuméricos del
  identificador de la operación.
- Dos facturas con el mismo final comparten IDSO. Por ejemplo, `FAC_ABC-00012345`
  y `FAC_XYZ-00012345` dan las dos `00012345`.
- `NDDTIMMTRN` y el `IEXT` de `[SBT]` siguen saliendo de `operation_id[:5]`.
  Para la v2 eso da «FAC_x», con guion bajo. Esto ya pasaba antes de la pieza.
- Opciones:
  - (a) Dejarlo así y preguntarle al despachante dos cosas: el largo máximo, y
    si el MARIA rechaza un IDSO repetido o el «_» en `NDDTIMMTRN`.
  - (b) Además, sacar `NDDTIMMTRN` e `IEXT` del mismo identificador corto. Eso
    cambia dos campos más del TXT, que la tarea no pidió.
- Recomiendo (a). (b) cambia lo que sale sin un rechazo que lo pida.

**D2. QARTKGRNET con milésimos y QARTUNTEST al centésimo (error 2122).**
- Con 465,125 kg salen `QARTKGRNET=465.125` y `QARTUNTEST=465.13`.
- La tarea dice «redondeado igual». Lo leí como «la cantidad estadística es el
  kilo neto al centésimo».
- Opciones:
  - (a) Dejarlo así.
  - (b) Con la estadística en kilos, escribir también QARTKGRNET al centésimo
    (`465.130`).
- Recomiendo preguntarle al despachante si el TXT aceptado el 24/10 tenía
  tres decimales distintos en esas dos líneas. Mientras tanto, (a).

**D3. Textos libres con «S.A.», paréntesis y comas.**
- El punto 6 pide limpiar sufijos y textos libres. Limpié sólo los sufijos.
- El archivo real que el MARIA aceptó trae «S.A.», paréntesis y comas en la
  razón social y el domicilio. Limpiarlos daba 13 rojos en los golden. El
  rechazo del 24/10 sólo nombra los valores de los sufijos.
- Opciones:
  - (a) Limpiar sólo los sufijos, como está.
  - (b) Limpiar también los textos libres y cambiar los golden.
- Recomiendo (a). (b) cambia lo que el MARIA ya aceptó.

**D4. Una identificación tributaria que parece cuenta bancaria.**
- Lo que tiene 16 dígitos o más y no es un código chino de crédito social que
  cierra su verificador, o es un IBAN que cierra el suyo, se toma por cuenta.
  Entonces el IDTRIB no sale y se avisa.
- El BR de Hong Kong completo, de 16 dígitos, cae en esa regla. Si el usuario
  lo vuelve a cargar, se vuelve a descartar.
- Además, un número cualquiera de 18 dígitos tiene 1 en 31 de cerrar el
  verificador chino y salir como tributaria.
- Opciones:
  - (a) Dejarlo así, con el aviso.
  - (b) Agregar en la revisión un «es la tributaria, mandala igual». Es
    funcionalidad nueva.
- Recomiendo (a) ahora y (b) como propuesta si aparece un proveedor de Hong
  Kong.

**D5. Otras formas de la fecha de inicio de actividad (punto 9).**
- Se aceptan `AAAA-MM-DD` y `DD/MM/AAAA`. Todo lo demás frena el TXT con un
  error que dice dónde corregir la fecha: `1/3/2015`, `01-03-2015`, una fecha
  con hora y `01/03/15`.
- `POST /api/clientes` guarda `[:10]` sin validar (`main.py:6304` y `:6382`).
  Por eso un dato así recién aparece al generar.
- `/generate_maria/avisos` no lo anticipa.
- El campo de fecha del navegador esconde un valor que no es ISO. Con tu D3
  (a) de CLIENTE-1 queda guardado y no se ve.
- Opciones:
  - (a) Dejarlo así: no se adivina y el error es claro.
  - (b) Aceptar `D/M/AAAA` y `DD-MM-AAAA`.
  - (c) Validar en el alta. Eso es de CLIENTE, no de esta pieza.
- Recomiendo (a) más (c) como tarea aparte. (b) no es adivinar, pero la tarea
  pidió sólo dos formas.

**D6. Una unidad que no se reconoce sale 07 sin aviso.**
- Ya pasaba antes de la pieza. Sumé formas de m²: `㎡`, `m^2`, `MTK`, `m2.`,
  `sq.m`, `Sq M` y `square meters`.
- Algo como «Kg.» o «Rollos» sigue cayendo en 07 en silencio.
- Opciones:
  - (a) Dejarlo para SUFIJOS-1 o UNIDADES.
  - (b) Sumar un aviso en los supuestos, en esta pieza.
- Recomiendo (b) como pieza chica aparte. No la hice: está fuera del punto 5.

**D7. Lo que pierde un sufijo al limpiarlo.**
- Un valor con caracteres que no son latinos queda en blanco:
  `AA(红色)-` sale `AA(  )-`.
- Un decimal cambia de sentido: `AI(1.5)` sale `AI(1 5)`.
- En los dos casos hay aviso, pero el TXT se genera igual.
- Opciones:
  - (a) Dejarlo así, con el aviso.
  - (b) No generar si un valor queda en blanco.
- Recomiendo preguntarle al despachante si el MARIA acepta un valor vacío y
  cómo se escribe un decimal en un sufijo. Mientras tanto, (a).

**D8. La v1 (`/dashboard?v=1`) no manda el número de factura.**
- El TXT de la v1 sale con `LDVDREFDOC` en blanco y un aviso.
- Opciones:
  - (a) Dejarlo así, si la v1 ya no se usa.
  - (b) Frenar el TXT sin número de factura, en las dos versiones.
- Recomiendo (a) si confirmás que la v1 no se usa. Si se usa, (b).

## Qué cambia en el TXT (los dos golden)

- `IDSO`, `IDDT` y la raíz de `IARTESPAPU`: de 9 a 8 caracteres (punto 2).
  - `000999001` → `00999001`.
  - `002720126` → `02720126`.
  - El número completo sigue en `NRO.REF.INTERNA`.
- `CSBTSVL`: `MODELO-A 001` → `MODELO A 001` (punto 6, el guion dentro del
  valor).
- Nada más cambia en los golden. `FECHA INIC.ACTIV` ya estaba `DD/MM/AAAA` en
  los dos, así que el punto 9 no los toca.
- Fuera de los golden también cambian:
  - `CDDTAGR` ahora es obligatorio (punto 3).
  - `LDVDREFDOC` lleva el número real (punto 4).
  - Las unidades (punto 5).
  - `IDTRIB-PROVEEDOR` (punto 7).
  - La fecha (punto 8).
  - `FECHA INIC.ACTIV` desde `AAAA-MM-DD` (punto 9).
  - Cada uno con su caso en `tests/test_maria7_*.py`.

## Comandos para reproducir

Desde un worktree de `f0b73f7`, con el entorno de las pruebas
(`DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key
ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake
DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares`):

```bash
python -m pytest -q --no-cov -p no:cacheprovider tests/test_maria7_rechazos_24_10.py tests/test_maria7_fechas.py tests/test_maria7_revision.py tests/test_maria7_inicio_actividad.py
# → 125 passed
scripts/testing/sabotaje_maria7.sh f0b73f7 <venv>
# → «OK: los 25 sabotajes dan rojo por la razón esperada»
git diff 3dbfb4e f0b73f7 -- tests/fixtures/maria_golden_anon.TXT tests/fixtures/maria_golden_subitems_anon.TXT
# → sólo IDSO/IDDT/IARTESPAPU de 9 a 8 y el guion de CSBTSVL
PM_DIR=<dir> docs/pm/herramientas/levantar.sh f0b73f7 <puerto>
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_maria7.js
# → «PANTALLA MARIA-7 OK»
```

## Puertas sobre `f0b73f7`

| Puerta | Salida exacta |
|---|---|
| Rojo antes, casos del 24/10 sobre la base | 51 casos `FAILED` en `test_maria7_rechazos_24_10.py` |
| Rojo antes, fechas (punto 8) | `26 failed, 4 passed, 3 warnings in 0.73s` |
| Rojo antes, punto 9 | se vio en rojo cada caso; sabotajes 23 a 25 abajo |
| Focales maria7 (4 archivos) | `125 passed, 5 warnings in 9.61s` |
| Sabotajes `sabotaje_maria7.sh f0b73f7` | `OK: los 25 sabotajes dan rojo por la razón esperada` |
| Suite completa (`--timeout=120`) | `1882 passed, 102 skipped, 2 xfailed, 23 warnings in 238.54s (0:03:58)` |
| `compileall -q proyecto_maria` | `rc=0` |
| e2e de la CI (`e2e_maria.sh`, con navegador) | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| Pantalla (`pantalla_maria7.js`, 390 px) | `PANTALLA MARIA-7 OK` (sale `ancho de la página a 390 px: 582`; ver riesgos) |
| `smoke_friccion.sh` | `OK · telemetría + alias session/state + by-cuit protegido` |

- La e2e necesitó lo que dice `ONBOARDING-DEV.md`: `PATH=<venv>/bin:$PATH` y
  `PUPPETEER_EXECUTABLE_PATH=/opt/pw-browsers/chromium`.
- La primera corrida falló sin eso, con `ModuleNotFoundError: No module named
  'fastapi'` y después con Chromium no encontrado. Es del entorno, no del
  producto.
- No corrí `ataque_aislamiento.sh`. La pieza no toca sesión, permisos ni de
  quién son los datos.
- Tampoco corrí `/security-review`, por la misma razón.

- El rojo conocido de EXCEL-2 (`test_excel2::test_ocho_libros…`, la subida
  normal daba 400 a los 30.1 s) esta vez pasó. Depende del tiempo de la
  máquina y falla igual en tu `3fd8826`; no es de esta pieza.

## Autorrevisión

| Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| Sonnet alto + Opus alto + `/code-review high` | La revisión daba vuelta la fecha del lector (`20/10/2026` → `26/20/2010`) | Arreglado (`449b157`), con su caso |
| Sonnet alto + Opus alto + `/code-review high` | Un año de dos cifras se adivinaba (`26/08/07` → 2007) | Ahora se pregunta |
| Sonnet alto + `/code-review high` | m² escrito de otras formas caía en 07 | Sumadas 7 formas; el resto es D6 |
| Opus alto + `/code-review high` | El código chino de crédito social, todo en números, se tomaba por cuenta | Verificador del código chino y del IBAN; lo que queda es D4 |
| Sonnet alto + Opus alto | La factura de más de 28 caracteres frenaba sin aviso previo | Ahora se avisa en `/generate_maria/avisos` |
| Sonnet alto + Opus alto | El mensaje de kilos con subítems no decía cómo salir | Ahora dice «con la cantidad igual al kilo neto al centésimo (465.13)» |
| Sonnet alto | La pregunta por la fecha salía con el título «Revisá el peso» | Ahora sale con «Revisá la factura» |
| Opus alto | La unidad del producto iba sin escapar al HTML | Escapada |
| `/code-review high` | La prueba de pantalla esperaba con un bucle fijo | `waitForRequest` |
| `/code-review high` | Textos libres sin limpiar | D3 |
| Opus alto + `/code-review high` | Colisión de IDSO; `NDDTIMMTRN`/`IEXT` de `operation_id[:5]` | D1 |
| Sonnet alto + Opus alto | QARTKGRNET 465.125 contra QARTUNTEST 465.13 | D2 |
| Opus alto | El valor del sufijo con caracteres que no son latinos queda en blanco; `1.5` → `1 5` | D7 |
| `/code-review high` | La v1 no manda el número de factura | D8 |
| Sonnet alto (punto 9) | `strftime("%Y")` no rellena: `0099-03-01` salía `01/03/99` | Arreglado (`e4e0336`), visto en rojo antes |
| Sonnet alto (punto 9) | El error no nombraba el campo de la revisión | Ahora nombra «Fecha inicio de actividades» |
| Sonnet alto (punto 9) | Otras formas, el alta sin validar y los avisos que no lo anticipan | D5 |

## Riesgos y lo que no se cubrió

- **Desborde a 390 px.** La pantalla mide el ancho de la página en 582 px. La
  tabla del despachante se desplaza sola (`c03bb1d`), pero la página entera
  todavía es más ancha que el teléfono. No comparé contra la base. Lo mido y
  te lo informo en la próxima vuelta, si no lo pedís antes.
- **Pruebas débiles, sólo `grep`:** el título del aviso en `upload.js` y el
  escape en `despachante.js` (sabotajes 21 y 22). El título sí se ve en el
  navegador en `pantalla_maria7.js`; el escape no.
- 0,004 kg con la estadística en kilos da `QARTUNTEST=0.00`. `peso_valido`
  acepta desde 0,001.
- `/generate_maria/avisos` no anticipa dos cosas:
  - un CUIT del despachante con sólo espacios, que llega llamando a la API
    directo porque el front los borra;
  - una unidad estadística inválida.
  Las dos frenan recién al generar, con un 400 claro.
- El ancho fijo cuenta caracteres, no bytes de UTF-8. Esto no cambió con la
  pieza.
- El punto 8 depende de que Gemini copie la fecha tal cual. Una fecha con el
  mes en letras y el año de 2 cifras sale vacía y se pregunta.
- La unidad que trae el producto (por ejemplo un Excel con «PCS») pisa la que
  elegís para la operación. Se ve en la lista de cada producto.
- Gemini no se llamó: la lectura de fechas se probó con lo que devolvería, no
  con el modelo real.
- No se usó ningún dato real del cliente del 24/10. Todo es sintético.

## Archivos de producto que toqué

`proyecto_maria/core/maria_generator.py`, `proyecto_maria/main.py`,
`proyecto_maria/core/controles_maria.py`, `proyecto_maria/pdf_extractor.py`,
`proyecto_maria/static/v2/screens/despachante.js`, `finalize.js`, `review.js`,
`upload.js`, `proyecto_maria/templates/dashboard_v2.html` y `CHANGELOG.md`.

## Siguiente

Sigo con MARIA-8, subítems por posición, sin esperar el veredicto. Si el
veredicto trae una devolución, esa va primero.

Última vuelta: 2026-10-24 20:19 UTC.

/compact conservar: Dev MARIA (Dev 2), rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. MARIA-7 entregada, SHA probado f0b73f7, D1–D8 abiertas en PARA-PM-2.md. Sigue MARIA-8 (subítems por posición), después VALOR-1 y SEPARADORES-1. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
