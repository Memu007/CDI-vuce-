# Dev 2 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

Hay **dos entregas pendientes**: MARIA-2b (arriba) y MARIA-1a (abajo, tal
como la entregué). MARIA-2b va encima de MARIA-1a.

## MARIA-2b — entregada: Gemini caído o con clave inválida ofrece la carga manual

| Qué | SHA |
|---|---|
| Base (MARIA-1a entregada) | `0a1775f` |
| Producto | `339eeb1`, `d4216df` |
| Pruebas y sabotajes | `c3bef51`, `9c2a156`, `c3acf44`, `6f31cfc`, `3df0d30` |
| **SHA que se entrega** | **`c3bef51`** |

**Resultado: terminada.** Con clave, si la llamada a Gemini falla, en las
**dos** copias del lector, el lector levanta el error propio de MARIA-2. El
endpoint responde 503 con `code: lectura_automatica_no_disponible` y la
pantalla muestra el botón «Cargar los productos a mano». Ya no aparece el
engañoso «No se encontró tabla de items». Cuenta como falla:
- la clave inválida o Gemini caído (la llamada lanza un error);
- la respuesta ilegible (no es JSON);
- la respuesta vacía o bloqueada;
- la configuración de Gemini rota.

Si Gemini responde bien pero sin productos, sigue el 400 de siempre. El texto
interno del error nunca llega a la pantalla, porque el mensaje es fijo. La
pantalla no cambió: ya manejaba ese `code` desde MARIA-2.

**De paso, en las pruebas de MARIA-2:** con MARIA-2b, una llamada a Gemini que
falla también termina en el 503. Por eso tres pruebas de MARIA-2 ya no
distinguían si faltaba el control de la clave; el sabotaje «clave en blanco»
quedaba verde. Ahora además verifican que no se intente llamar a Gemini, y el
sabotaje vuelve a dar rojo.

**D8. ¿Se descuenta el límite diario de PDFs cuando Gemini falla?** Hoy sí:
se descuenta antes de llamar a Gemini. Sin clave (MARIA-2) no se descuenta.
- (a) Dejarlo así: hubo una llamada a Gemini, que puede costar. **Recomiendo
  (a).**
- (b) Devolver el cupo cuando sale este 503. Hace falta una función nueva en
  `core/ai_quota.py`.

**Riesgo anotado:** un error de nuestro propio código al leer una respuesta
de Gemini que llegó bien también termina en este 503, con el error impreso en
el registro. Antes daba 400. Los dos revisores lo consideran defendible.

| Puerta (sobre `c3bef51`, worktree limpio) | Resultado |
|---|---|
| Suite completa | `791 passed, 102 skipped, 24 warnings in 61.22s`, 0 failed |
| `tests/test_maria2b_gemini_falla.py` (14 casos) + MARIA-2 + MARIA-1a | `84 passed` |
| `compileall` | ok |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `scripts/testing/sabotaje_maria2b.sh` | `OK: los 6 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria2.sh` / `sabotaje_maria1a.sh` (tocan el mismo archivo) | `OK: los 8 …` / `OK: los 10 …` |

**Rojo antes:** `assert 400 == 503` en las dos copias, para clave inválida,
Gemini caído, respuesta ilegible y respuesta vacía; en la copia PyMuPDF,
también para la configuración rota.

**Autorrevisión** (adversario Sonnet medio, más `/code-review high`):
arreglados con su rojo antes:
- la respuesta vacía o `None` daba 400;
- en la copia PyMuPDF, la configuración rota daba 400;
- si un modelo fallaba y otro respondía «sin productos», daba 503;
- las pruebas de MARIA-2 ya no distinguían el control de la clave;
- faltaban sabotajes de la copia de producción.

Quedan como riesgo, fuera de alcance:
- D8 (el cupo diario);
- `robust_extract_pdf_items`, que no tiene llamadores vivos y convierte el
  error en «sin productos»;
- la duplicación del Gemini falso entre los archivos de prueba.

Contexto: ~52 %. Sigo con MARIA-4 si no hay devolución.

---

## MARIA-1a — entregada: la factura bien leída

| Qué | SHA |
|---|---|
| Base (rama de la PM al arrancar) | `321f34b` |
| Producto | `e0b119b`, `14fca41`, `c411128` |
| Pruebas y sabotajes | `adb002f`, `4b8fc49`, `0f7b20f`, `509bdaa`, `0a1775f` |
| **SHA que se entrega (puertas corridas acá)** | **`0a1775f`** |
| Informe | el commit que trae este archivo (encima, sólo docs de la PM integrados) |

**Resultado: terminada.** Cambié las **dos** copias del lector con Gemini
(`pdf_extractor.py`): la de PyMuPDF y la de «PDF directo», que es la que corre
en producción.
- **País:** reconoce dos letras, tres letras y el nombre, contra la tabla
  oficial VUCE. `CHN`, `China` y `P.R. China` dan `CN`, código MARIA 310.
  `MEX` da `MX`, código 218. Lo que no se reconoce queda vacío. Antes `CHN`
  salía `CH`, Suiza; `MEX`, `ME`, Montenegro; y «Narnia», `NA`, Namibia.
- **Números:** cantidad, precio, peso, flete y seguro con coma salen bien.
  `1,500` es mil quinientos sólo si la misma factura usa el punto como
  decimal, y uno coma cinco si usa la coma. Si no hay pista, queda vacío.
  Todo lo que no es un número limpio también queda vacío: `12x3`, `1/2`,
  `500 g`, `2.5e3`, negativos, infinitos.
- **Lo que falta:** queda vacío (0 o `""`) y lo marca el semáforo. Se fueron
  el peso de 0,5 kg, la cantidad 1, el origen copiado del vendedor (D4) y la
  descripción «Producto».
- **Instrucciones a Gemini:** ya no dicen «estimar 0.5» para el peso. La
  copia PyMuPDF pide los números tal como aparecen en la factura.
- **Tabla tres letras → dos letras:** `proyecto_maria/core/paises_iso3.py`,
  194 países. Salió una sola vez de ISO 3166-1 con pycountry 26.2.16, que no
  es dependencia. El script es `scripts/datos/generar_paises_iso3.py`. Una
  prueba verifica que cada destino existe en la tabla oficial. El revisor la
  cruzó además con `iso-codes` del sistema: 0 pares erróneos.

## Decisiones

**D5. Un flete o seguro ilegible queda en 0 y nadie avisa.** Pasa con un
`"1,500"` sin pista, o un `"350 USD/kg"`. Antes, eso hacía descartar la
factura entera: un error visible. Ahora el valor CIF puede quedar más bajo sin
que nadie lo note, porque el semáforo sólo mira los ítems.
- (a) Pieza chica: el lector marca los campos ilegibles y la pantalla de
  subida los nombra en un aviso, por ejemplo «No pudimos leer el flete:
  completalo». **Recomiendo (a).** Si querés, va dentro de MARIA-2b, que toca
  la misma pantalla.
- (b) Dejarlo así hasta MARIA-1b, que es de la Dev 1.

**D6. Al guardar la operación vuelven el 1 y el 0,5.** `main.py`, alrededor
de la línea 5508, `save_client_operation`, usa `cantidad … or 1` y
`peso_unitario … or 0.5`. Lo leyó el revisor y no lo corrí. Si alguien guarda
sin completar, el dato inventado llega a la base. Está fuera de MARIA-1a: no
toqué `main.py` y lo tiene abierto la Dev 1.
- (a) Asignarlo a la Dev 1 junto con MARIA-1b (controles antes de generar).
  **Recomiendo (a).**
- (b) Lo hago yo después de MARIA-2b, si la Dev 1 libera ese archivo.

**D7. La copia que corre en producción sigue pidiendo números** («JSON
estricto» con ejemplos numéricos). Puede que Gemini convierta solo un
`1.500` brasileño en 1,5, y así nuestra regla nunca ve el texto original. No
se puede comprobar sin Gemini real.
- (a) Dejarlo así y medirlo con facturas reales cuando haya ensayo con clave.
  **Recomiendo (a).**
- (b) Pedirle los números como texto en las dos copias. Cambia lo que se le
  pide a Gemini en producción sin poder probarlo.

## Archivos de producto tocados (para «archivos abiertos»)

- `proyecto_maria/pdf_extractor.py`: funciones nuevas cerca de la línea 1950
  y las dos copias del lector (~2130-2500). No toqué la zona de la línea 800,
  que es de la Dev 1.
- `proyecto_maria/core/paises_iso3.py` (nuevo) y
  `scripts/datos/generar_paises_iso3.py` (nuevo).
- `CHANGELOG.md`.
- El generador del TXT (`core/maria_generator.py`) **no** se tocó.

## Evidencia

**Rojo antes** (pruebas nuevas contra el producto de la base, salida copiada):

```
E   AssertionError: assert ['CH', 'ME', ...', 'NA', 'CH'] == ['CN', 'MX', ... 'CN', '', '']
E   assert 1.0 == 0                      (cantidad que falta: antes 1)
E   AssertionError: el lector no devolvió datos: []   (números en castellano: la copia de producción tiraba la factura)
```

El revisor también corrió las pruebas contra la base: 13 failed y 1 passed.
La que pasa es la de la tabla, que no depende del producto viejo.

| Puerta (sobre `0a1775f`, worktree limpio) | Resultado |
|---|---|
| Suite completa `pytest -q --no-cov --timeout=120` | `777 passed, 102 skipped, 24 warnings in 56.72s`, 0 failed |
| `tests/test_maria1a_lectura_factura.py` + `test_maria2_sin_clave_gemini.py` | `70 passed` |
| Archivos reales (`test_generar_maria_txt.py`, `test_maria_subitems.py`) | `68 passed, 3 warnings in 4.97s` |
| `python -m compileall -q proyecto_maria` | sin salida (ok) |
| `smoke_friccion.sh` contra la API local | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `scripts/testing/sabotaje_maria1a.sh` | `OK: los 10 sabotajes dan rojo por la razón esperada` |
| `scripts/testing/sabotaje_maria2.sh` (también toca este archivo) | `OK: los 8 sabotajes dan rojo por la razón esperada` |

Los sabotajes de MARIA-1a son:
1. el país se corta a dos letras;
2. falta la tabla de tres letras;
3. se arregla una sola copia;
4. se adivina 1500 sin pista;
5. la coma decimal se toma como separador de miles;
6. vuelve el peso de 0,5;
7. vuelve la cantidad 1;
8. el pedido a Gemini vuelve a decir «estimar»;
9. se pegan los dígitos de un número sucio;
10. `NA` vuelve a ser Namibia.

**Autorrevisión:**

| Revisor | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| adversario | Sonnet alto | Alta: `12x3`, `1/2`, `500 g`, `2.5e3` daban un número equivocado | arreglado con rojo antes |
| adversario | Sonnet alto | Alta/media: pista decimal falsa porque la copia PyMuPDF le pedía a Gemini «arreglar» los números | arreglado: pide los números tal cual |
| adversario | Sonnet alto | Media: `NA` daba Namibia | arreglado: vacío |
| adversario | Sonnet alto | Media: negativos distintos en cada copia; `(1,500.00)` salía positivo | arreglado: vacío |
| adversario | Sonnet alto | Baja: un ítem raro descartaba la factura entera; `NaN` pasaba | arreglados |
| adversario | Sonnet alto | Media: `main.py` repone 1 y 0,5 al guardar | D6 |
| adversario | Sonnet alto | Media: el ejemplo de las instrucciones trae `peso_kg: 0.5` | riesgo (sin Gemini real no se reproduce) |
| adversario | Sonnet alto | Baja: «Países Bajos» y «República de Sudáfrica» quedan vacíos (la tabla oficial no les da dos letras) | aceptable: vacío, no equivocado |
| `/code-review high` | — | Flete o seguro ilegibles quedan en 0 sin aviso | D5 |
| `/code-review high` | — | La regla estricta rechazaba `12 PCS`, `100 USD`, `U$S 1.234,56`; y aceptaba `lb 5` | arreglado: moneda y unidades de cuenta sólo de una lista; `g` y `lb` no |
| `/code-review high` | — | `1.2,3` y `1,5.00` se leían; `9`×400 daba infinito; un entero gigante cortaba el lector | arreglados con rojo antes |
| `/code-review high` | — | La copia PyMuPDF sólo atrapaba `ValueError` | arreglado |
| `/code-review high` | — | La copia de producción sigue pidiendo números | D7 |
| `/code-review high` | — | `static/app.js` (pantalla vieja) completa el país del vendedor con `CN` | fuera de alcance, pantalla vieja |
| `/code-review high` | — | Las dos copias duplican el código | fuera de alcance: unificarlas es un refactor |

`/security-review`: no se corrió. La pieza no toca dinero, sesión, permisos ni
datos guardados.

## Para reproducir

```bash
git fetch origin claude/dev2-maria && PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 0a1775f 8080
# verde → «70 passed»
<venv>/bin/python -m pytest -q --no-cov tests/test_maria1a_lectura_factura.py tests/test_maria2_sin_clave_gemini.py
# rojo antes → muchos failed, con ['CH', 'ME', …]
git checkout 321f34b -- proyecto_maria && <venv>/bin/python -m pytest -q --no-cov tests/test_maria1a_lectura_factura.py; git checkout 0a1775f -- proyecto_maria
# sabotajes → «OK: los 10 …» y «OK: los 8 …»
VENV=<venv> scripts/testing/sabotaje_maria1a.sh 0a1775f; VENV=<venv> scripts/testing/sabotaje_maria2.sh 0a1775f
```

(Con el producto de la base, la prueba de la tabla de tres letras falla por
`ModuleNotFoundError`. Es lo esperable.)

## No corrido

- Facturas reales con Gemini real: está prohibido desde las pruebas. Las dos
  copias se prueban con un Gemini falso; la de PyMuPDF, además, con un
  PyMuPDF falso.
- `ataque_aislamiento.sh`: la pieza no toca sesión ni permisos.
- `e2e_maria.sh`: no corre en la nube.

MARIA-2b entregada encima (arriba).

Última vuelta: 2026-10-07 04:40 UTC
Contexto: ~45 % (pasado el umbral; compactar cuando Emi pueda)
