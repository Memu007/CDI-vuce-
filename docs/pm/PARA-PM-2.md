# Dev 2 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MARIA-2 — entregada: sin clave de Gemini no se inventan productos

| Qué | SHA |
|---|---|
| Base (cabeza de `claude/practical-shannon-szpwkn`) | `cb8f509` |
| Producto | `19e8a39`, `821f842`, `3184c10` |
| Pruebas y sabotajes | `7dcef8a`, `d275389`, `65ea6f3` |
| **SHA que se entrega (puertas corridas acá)** | **`65ea6f3`** |
| Informe | el commit que trae este archivo |

**Resultado: terminada.** Sin clave de Gemini, con la clave en blanco o con
el lector con IA apagado (`ENABLE_PDF_LLM_FALLBACK=false`), subir un PDF ya no
devuelve los dos «ITEM DEMOSTRACION». Responde **503** con
`{"detail": "No se pudo leer la factura automáticamente; cargá los productos a mano.", "code": "lectura_automatica_no_disponible"}`
y cero productos. No descuenta la cuota diaria de PDFs. La pantalla muestra el
mensaje con un botón «Cargar los productos a mano», que abre la carga manual.
Con clave, todo sigue como antes.

## Decisiones

**D1. Sin clave, ¿leer igual los PDF que traen texto?** Ya existe un lector
sin IA (`robust_extract_pdf_items`, tablas y líneas de texto), pero el camino
vivo no lo usa, ni antes ni ahora. Sin clave, hoy toda subida pide carga
manual.
- (a) Dejarlo así: nada inventado y nada nuevo que probar. **Recomiendo (a).**
  Ese lector viejo nunca se probó contra facturas reales, y con él vuelven las
  dudas de MARIA-1a (país, cantidades y peso adivinados).
- (b) Tarea aparte: usarlo sin clave sólo para PDF con texto y dejar el 503
  para los escaneados.

**D2. Con clave, pero Gemini caído o con clave inválida**, el lector devuelve
cero productos y el endpoint responde el 400 de siempre: «No se encontró tabla
de items en el PDF…». No inventa nada, pero el mensaje engaña y no ofrece la
carga manual. La tarea habla de la clave que falta, no de Gemini caído.
- (a) Lo dejo así (no está en el alcance).
- (b) Lo sumo a esta pieza: el mismo 503 con su código cuando Gemini falla.
  Es chico, pero hay que simular la falla.
**Recomiendo (b) como pieza aparte y chica.** Si preferís que vaya acá, lo hago
antes de MARIA-1a.

## Qué cambió (archivos de producto, para «archivos abiertos»)

- `proyecto_maria/pdf_extractor.py`: el «modo DEMO» ahora es el error propio
  `LecturaAutomaticaNoDisponible`. Hay una sola regla para saber si hay
  lector, `lectura_automatica_disponible()`, y una clave hecha sólo de
  espacios cuenta como que falta. Si `robust_extract_pdf_items` (que hoy usan
  sólo las pruebas) recibe ese error, devuelve `[]`.
- `proyecto_maria/main.py` (`upload_pdf_public`): valida el archivo, después
  pregunta si hay lector (503 si no lo hay) y recién ahí descuenta la cuota.
- `proyecto_maria/static/v2/screens/upload.js`: con ese `code`, muestra el
  mensaje y el botón de carga manual.
- `CHANGELOG.md`: una entrada.

**Supuestos que podés rechazar:**
1. **La validación del archivo pasó antes de la cuota.** Antes se descontaba
   la cuota y después se validaba. Ahora un archivo inválido no gasta cuota,
   también con clave. Sin ese cambio, el control de lector quedaba antes de la
   validación y tapaba sus errores (lo marcó `/code-review`).
2. **Elegí 503 y la clave `code`**, que es la que ya usan los otros errores de
   `main.py` (`internal_error`, `csrf_failed`).

## Otros caminos que inventan datos si falla Gemini (punto 3 de la tarea)

| Camino | ¿Vivo? | ¿Inventa? | Qué hice |
|---|---|---|---|
| `_extract_with_gemini_vision`, «modo DEMO» sin clave | sí, es el único que usa `/upload_pdf/public` | sí, 2 productos | **arreglado** |
| `robust_extract_pdf_items` (PDF sin texto → IA) | no, sólo lo usan pruebas | heredaba la demo | arreglado (devuelve `[]`) |
| `_llm_extract_pdf_items` sin clave | no | no, devuelve `[]` | nada |
| `_fallback_image_extraction` | sí | no, devuelve `[]` | nada |
| Con respuesta de Gemini, los campos que faltan se completan: descripción «Producto», cantidad 1, peso 0,5, origen `BR`/`CN` | sí | sí, **dato por dato** | **nada: es MARIA-1a** (un dato que falta queda vacío y con aviso) |
| `detect_vendor_from_text` | sí | no, lee el texto del PDF | queda |
| `simulateOperation()` en `upload.js` (5 productos de ejemplo) | no, el botón ya no está en `dashboard_v2.html` | sólo si alguien lo llama | nada, código muerto |
| `pdf_extractor_wrapper.py` | no, nadie lo importa (además está roto) | no | nada |
| Pantalla vieja `static/app.js` (`dashboard.html`) | sí | no: muestra el mensaje con el prefijo «Error procesando PDF:», sin botón | nada, fuera de alcance |

La D del canal («si quitar el modo demostración rompe una pantalla de
bienvenida o una demo comercial») **no aplica**. Ninguna pantalla depende del
modo DEMO del servidor. El «simular operación» del frontend es independiente y
ya no tiene botón.

## Evidencia

**Rojo antes** (prueba nueva sobre el producto de la base, salida copiada):

```
E   AssertionError: {"message":"PDF procesado exitosamente","filename":"factura.pdf","operacion":{},"items":[{"pieza":"","descripcion":"ITEM DEMOSTRACION (Falta API Key)","cantidad":10.0,"valor_unitario":150.0,"origen":"CN","peso_unitario":1.0},{"pieza":"","descripcion":"Configura GEMINI_API_KEY para usar IA real","cantidad":5.0,"valor_unitario":200.0,"origen":"US","peso_unitario":2.5}],"items_count":2}
E   assert 200 == 503
=================== 5 failed, 1 passed, 5 warnings in 0.41s ====================
```

**Verde después:** `tests/test_maria2_sin_clave_gemini.py`, 9 passed. Todas las
pruebas de ese archivo corren con un Gemini falso que falla si alguien lo
llama: ni Gemini real ni internet.

| Puerta (sobre `65ea6f3`, worktree limpio) | Resultado |
|---|---|
| Suite completa `pytest -q --no-cov --timeout=120` | `689 passed, 102 skipped, 9 warnings in 60.62s` (base: 680 passed; +9 nuevas; 0 failed) |
| Archivos reales y TXT (`test_generar_maria_txt`, `test_maria_subitems`, `test_maria_iext_anio`, `test_maria_gastos_fob`) | `82 passed, 3 warnings in 5.64s`. El generador del TXT no se tocó. |
| `python -m compileall -q proyecto_maria` | sin salida (ok) |
| `smoke_friccion.sh` contra la API local | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `scripts/testing/sabotaje_maria2.sh 65ea6f3` | `OK: los 8 sabotajes dan rojo por la razón esperada` |
| Captura (Chromium local, API sin clave) | `docs/pm/capturas/maria2-sin-lector.png`. Después del clic en el botón, se ve la pantalla de revisión. |

Sabotajes (cada uno, rojo y con su motivo): vuelve la demo; la demo llega a la
pantalla si se saca el control; se gasta la cuota; el endpoint no atrapa el
error (500); el lector corta también con clave; el camino viejo deja escapar el
error; falta el `code`; una clave en blanco cuenta como clave. Ningún sabotaje
anterior toca estos archivos: no había otros scripts.

**Autorrevisión:**

| Revisor | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| adversario | Sonnet alto | Media: sin lector, igual se gastaba la cuota diaria | arreglado, con rojo antes (`assert 5 == 4`) |
| adversario | Sonnet alto | Baja: con clave y Gemini caído, 400 engañoso | D2 |
| adversario | Sonnet alto | Baja: `pdf_extractor_wrapper.py` muerto, `app.js` viejo sin botón | listados arriba |
| `/code-review high` | — | El control de lector tapaba la validación del archivo | arreglado, con rojo antes (`assert 503 == 400`) |
| `/code-review high` | — | Una clave con espacios contaba como clave | arreglado, con rojo antes. Primero intentó llamar a Gemini de verdad y la corté: por eso ahora el archivo prohíbe Gemini. |
| `/code-review high` | — | `codigo` contra la convención `code` | arreglado |
| `/code-review high` | — | Sin clave se podría leer el PDF de texto | D1 |
| `/code-review high` | — | Con clave, un PDF ilegible por Gemini gasta cuota | riesgo bajo, comportamiento previo, fuera de alcance |
| `/code-review high` | — | El 503 parece una caída para un monitor | riesgo bajo. Railway no reinicia por un 503 de una ruta. |
| `/code-review high` | — | Hay tres copias de la regla «hay lector» (las otras dos, en caminos no vivos) | fuera de alcance: no las toqué |
| `/code-review high` | — | El script de sabotajes dejaba una carpeta en /tmp; la demo no se probaba en pantalla | arreglados |

`/security-review`: no se corrió. La pieza no toca dinero, sesión, permisos
ni datos. Sólo mueve de lugar la cuota, que gasta menos.

## Para reproducir

```bash
git fetch origin claude/dev2-maria && git checkout 65ea6f3
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 65ea6f3 8080
# rojo antes: la prueba nueva contra el producto de la base → «5 failed», con ITEM DEMOSTRACION
git checkout cb8f509 -- proyecto_maria && <venv>/bin/python -m pytest -q --no-cov tests/test_maria2_sin_clave_gemini.py; git checkout 65ea6f3 -- proyecto_maria
# verde → «9 passed»
<venv>/bin/python -m pytest -q --no-cov tests/test_maria2_sin_clave_gemini.py
# sabotajes → «OK: los 8 sabotajes dan rojo por la razón esperada»
VENV=<venv> scripts/testing/sabotaje_maria2.sh 65ea6f3
```

(Con el producto de la base, la prueba de la clave en blanco intenta llamar a
Gemini. El Gemini falso de la prueba la corta y no sale a internet.)

## No corrido

- `ataque_aislamiento.sh`: la pieza no toca datos, sesión ni permisos.
- `e2e_maria.sh`: no corre en la nube.
- Una factura real con clave real: prohibido desde pruebas. El camino con
  clave lo cubre un modelo falso.

Sigo con MARIA-1a.

Última vuelta: 2026-10-07
Contexto: ~20 %
