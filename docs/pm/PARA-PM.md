# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## RENDIMIENTO-1b — entregada, terminada

| | SHA |
|---|---|
| Base (RENDIMIENTO-1 aceptada, con tu rama traída) | `8fd801d` |
| Producto | `ef49d8e`, `24530dd` |
| Pruebas y sabotajes | `de4bf0c`, `df4adb0`, `b01149c` |
| **Entrego (código)** | **`b01149c`** |

Resultado:
1. **La adivinanza del vendedor lee sólo con `pypdf`** (`extraer_texto_pdf_seguro`
   en `pdf_extractor.py`, fuera de la zona de la Dev 2). El escenario del
   revisor ya no deja a nadie sin lectura: 4 PDF armados en paralelo y
   después uno bueno, que se lee enseguida.
2. **Sólo las 2 primeras páginas, y salta una página con más de 512 KB de
   contenido.** Lo agregó el revisor (abajo): pypdf también se pone lento
   con un contenido enorme. Una página de 3 MB tardaba 6 s, 9 MB más de 60 s,
   y todo ese tiempo ocupaba un hilo de lectura.
3. **Tiempos máximos:** en `0`, negativos, `inf`, `1e309`, `nan`, mal
   escritos o en blanco valen el de siempre. Vale para los cuatro:
   `PDF_READ_TIMEOUT_S` (120), `PDF_VALIDATE_TIMEOUT_S` (30),
   `PDF_VENDOR_TIMEOUT_S` (15) y `NCM_GEMINI_TIMEOUT_S` (30).
4. **Otros caminos hacia pdfminer o pdfplumber: no hay.** Lo confirmé yo y
   también el revisor. `process_pdf` va directo a Gemini Vision: usa PyMuPDF,
   y si no está, manda el PDF a Gemini. La validación sólo cuenta páginas con
   pypdf. `_extract_pdf_text`, `robust_extract_pdf_items`,
   `_extract_items_per_page` y el OCR no tienen ningún llamador vivo en
   `main.py` ni en los routers. Sin D.

Nada para decidir.

## Comandos copiables

```bash
git fetch origin claude/dev1-tecnica && git checkout b01149c
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh b01149c 8080
# desde el worktree:
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_rendimiento1b.py tests/test_rendimiento1.py   # 30 passed
PY=$(which python) scripts/testing/sabotajes/rendimiento1b.sh b01149c   # 5 «ROJO», «sabotajes con falla: 0»
```

El escenario de los PDF armados corre en un proceso aparte con 60 s de
límite (`tests/escenario_pdf_armado.py`). Si la lectura se vuelve a colgar,
la prueba falla diciéndolo en vez de colgar la suite.

## Evidencia (salida exacta)

**Rojo antes**, con las pruebas nuevas sobre el código de `8fd801d`:

```
E   AssertionError: {'armados': [200, 200, 200, 200], 'armados_s': 1.28, 'bueno': 504, 'bueno_s': 3.42}
E   AssertionError: {"detail":"Leer el PDF tardó demasiado. ...","code":"lectura_pdf_demasiado_larga"}   (PDF_READ_TIMEOUT_S=0 y -5)
E   AssertionError: {"detail":"No pudimos abrir el PDF: tardó demasiado. Probá con otro archivo."}       (PDF_VALIDATE_TIMEOUT_S=0 y -5)
E   AssertionError: {}  assert None == 'ACME TRADING CO LTD'                                         (PDF_VENDOR_TIMEOUT_S=0 y -5)
E   AssertionError: {'sugerencias': [], ...}                                                         (NCM_GEMINI_TIMEOUT_S=0 y -5)
E   AssertionError: la adivinanza del vendedor le pasó el PDF a pdfminer o pdfplumber
```

Segunda tanda, por el revisor, sobre `de4bf0c`:

```
E   AssertionError: sacar el texto de una página de 3 MB tardó 6.01 s
E   assert inf == 120.0                                                                            (inf y 1e309)
```

Mi primera prueba de «sin pdfminer» daba verde con el código viejo: el error
que yo simulaba se lo tragaba un `except` y el código seguía con pypdf. Ahora
anota si pdfminer se llamó. Mi primer PDF «enorme» tampoco distinguía nada
porque no declaraba la fuente; con la fuente, sí.

**Mismo vendedor que antes**, comparando con el lector viejo
(`_extract_pdf_text`) contra el nuevo, en `tests/test_factura.pdf` y en 5
PDF de texto con «VENDOR:», «PROVEEDOR:», «FORNECEDOR:», «SHIPPER -» y sin
vendedor: `iguales 6 / 6`.

**Sabotajes** sobre `b01149c` (`rendimiento1b.sh`):

```
ROJO  | el vendedor vuelve a leer con pdfminer: dice «FAILED tests/test_rendimiento1b.py::test_pdfs_armados_en_paralelo_y_despues_uno_bueno_se_lee»
ROJO  | los tiempos en 0 o negativos ya no caen al defecto: dice «FAILED tests/test_rendimiento1b.py::test_tiempo_de_lectura_en_cero_o_negativo_usa_el_de_siempre[0]»
ROJO  | el tiempo de validación en 0 o negativo ya no cae al defecto: dice «FAILED tests/test_rendimiento1b.py::test_tiempo_de_validacion_en_cero_o_negativo_usa_el_de_siempre[0]»
ROJO  | el vendedor vuelve a leer páginas de contenido enorme: dice «FAILED tests/test_rendimiento1b.py::test_texto_del_vendedor_no_se_traba_con_un_contenido_enorme»
ROJO  | un tiempo infinito vuelve a apagar el tiempo máximo: dice «FAILED tests/test_rendimiento1b.py::test_tiempos_infinitos_o_raros_usan_el_de_siempre[inf]»
sabotajes con falla: 0
```

El script corre con `-x`. Con pdfminer de vuelta, el PDF de 3 MB de otra
prueba agotaba la memoria: el proceso moría (salida 137) sin decir por qué.

Los sabotajes vigentes que tocan los mismos archivos siguen en rojo:
`rendimiento1.sh`, `admin1.sh` y `admin2.sh` (`sabotajes con falla: 0`), y
`sabotaje_maria2.sh` de la Dev 2 (`OK: los 8 sabotajes dan rojo por la razón
esperada`).

## Puertas sobre `b01149c`

| Puerta | Resultado |
|---|---|
| Suite completa, worktree limpio, venv nuevo sólo desde `requirements.txt` | `746 passed, 102 skipped, 24 warnings in 78.23s` |
| `compileall` | sin errores |
| `smoke_friccion.sh` contra :8811 | `OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` | 22 BLOQUEADO, 0 FUGA |

En la suite de `de4bf0c`, el mismo venv dio `pip check` limpio y no tenía
instalados PyPDF2, python-jose ni ecdsa.

## Autorrevisión

Un subagente Opus alto, porque la pieza es chica.

| Hallazgo | Qué hice |
|---|---|
| Alto: pypdf tarda más que lineal con un contenido de página enorme (9 MB, más de 60 s) y ocupa un hilo de lectura | sólo 2 páginas y salto de páginas de más de 512 KB (`24530dd`), con prueba y sabotaje |
| Bajo-medio: `inf` o `1e309` apagaban el tiempo máximo | sólo valen números finitos, con prueba y sabotaje |
| Confirmado: ningún otro camino vivo hacia pdfminer o pdfplumber | — |
| Confirmado: la bomba de descompresión no traba a pypdf (0,5 s, 177 MB) | — |

## Qué no corrí

- Nada contra producción ni terceros. Gemini real tampoco: está simulado.
- `/code-review` y `/security-review` aparte: no, por la cuenta y porque la
  pieza es chica. El revisor Opus tuvo el foco de seguridad.

## Archivos de producto que toqué

`proyecto_maria/main.py` (adivinanza del vendedor y lectura de tiempos),
`proyecto_maria/pdf_extractor.py` (nueva `extraer_texto_pdf_seguro`, cerca
de la línea 820), `proyecto_maria/security/file_security.py`
(`_pdf_validate_timeout_s`), `CHANGELOG.md`.

## Sigo con

EXCEL-1 (con D12) cuando me la escribas. Si no hay nada nuevo, espero.

Última vuelta: 2026-10-07 06:10 UTC
Contexto: ~47 %

`/compact conservar: Dev 1 de CDI en la rama claude/dev1-tecnica. ADMIN-1,
ADMIN-2 y RENDIMIENTO-1 aceptadas (RENDIMIENTO-1 no se integra en la rama
de PM hasta después del ensayo). RENDIMIENTO-1b entregada (código b01149c),
informe en PARA-PM.md, sin D. Después siguen EXCEL-1 (con D12: pd.read_excel
y openpyxl fuera del hilo del servidor), MARIA-1b (con la D6 de la Dev 2:
save_client_operation no inventa cantidad 1 ni peso 0,5) y PUNTA-A-PUNTA-1.
COBRO-CORTE-1 en pausa (D4=(b) N=10, D5=(a), D6=(a)); COBRO-MP-1 primero
en la Fase 2 (D8: no aplicar dos veces un mismo pago). Entorno:
PM_DIR=/tmp/cdi-dev1, levantar.sh <SHA> 8811, venv /tmp/cdi-dev1/venv y
venv-limpio; sabotajes en scripts/testing/sabotajes/ (admin1, admin2,
rendimiento1, rendimiento1b) y scripts/testing/sabotaje_maria2.sh. Rutina de
la PM: trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
