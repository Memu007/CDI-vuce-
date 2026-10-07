# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## RENDIMIENTO-1 — entregada, con un pendiente serio en D10

| | SHA |
|---|---|
| Base (mi rama con la tuya, código = `0ff38db`) | `0ff38db` |
| Producto | `989c175`, `0c2900e`, `eafb0dc`, `49113a0` |
| Pruebas y sabotajes | `ca01ad8`, `8249346`, `450f2d5`, `bfe49d5`, `ae0d826`, `8fd801d` |
| **Entrego (código)** | **`8fd801d`** |

Resultado:
1. **Leer un PDF ya no frena el sitio.** Leer el PDF, sacarle el texto,
   abrirlo para validarlo y pedirle un NCM a Gemini corren en otro hilo.
   `/health` responde mientras tanto.
2. **Tiempos máximos.**

   | Qué | Variable | Valor | Al vencerse |
   |---|---|---|---|
   | Lectura del PDF | `PDF_READ_TIMEOUT_S` | 120 s | 504 `{"detail": texto, "code": "lectura_pdf_demasiado_larga"}`; la pantalla ofrece la carga a mano, igual que MARIA-2 |
   | Validación | `PDF_VALIDATE_TIMEOUT_S` | 30 s | 400 «tardó demasiado» |
   | Adivinar el vendedor | `PDF_VENDOR_TIMEOUT_S` | 15 s | se sigue sin el vendedor (es opcional) |
   | Gemini en NCM | `NCM_GEMINI_TIMEOUT_S` | 30 s | se sigue sin sus sugerencias |

   Los valores mal escritos caen al valor por defecto.
3. **Grupo de hilos propio para leer PDF** (`PDF_READ_WORKERS`, 4). Un hilo
   que pasa del tiempo sigue corriendo hasta terminar. Con su propio grupo,
   las lecturas lentas no le quitan hilos a la validación ni a NCM.
4. **`PyPDF2` 3.0.1 → `pypdf` 6.19.** Reproduje X3: con un PDF armado, PyPDF2
   seguía colgado a los 10 s (lo corté); pypdf lo lee en 0,00 s.
   **`python-jose` afuera**: nadie la importaba, el token usa PyJWT. `ecdsa`
   venía con ella y también se va. La suite corre en un entorno nuevo armado
   sólo con `requirements.txt`, sin PyPDF2, jose ni ecdsa: `pip check` limpio.
5. Un PDF encriptado vuelve a decir «Encrypted PDFs are not allowed». Con
   pypdf decía «File has not been decrypted».

**Archivos de la Dev 2:** toqué `pdf_extractor.py` sólo en
`_extract_pdf_text` (líneas ~780-810, el respaldo PyPDF2 → pypdf), no en su
zona. Cambié una línea de su prueba `tests/test_maria2_sin_clave_gemini.py`
(`from PyPDF2 import PdfWriter` → `from pypdf import PdfWriter`) porque
PyPDF2 ya no se instala. Sus 8 sabotajes siguen en ROJO.

## Decisiones

- **D10 — Un PDF armado puede colgar la lectura para siempre (alta).** Lo
  encontró el revisor Sonnet. Un PDF de 460 bytes con un `/Length` que se
  apunta a sí mismo hace que pdfminer (el primer lector de
  `_extract_pdf_text`, y también pdfplumber) no termine nunca. Hay otro de
  1,5 MB que se descomprime a 1,5 GB y le hace pedir 3 GB de memoria.
  Un hilo no se puede cortar desde afuera, así que el 504 llega a tiempo
  pero el hilo sigue gastando CPU (y memoria, con el segundo).
  - **Antes de esta pieza** ese PDF colgaba el servidor entero.
  - **Ahora** cuelga sólo el grupo de lectura de PDF. Con 4 de esos
    archivos, nadie más puede leer un PDF hasta reiniciar; el resto del
    sitio sigue andando.

  Hoy ese texto lo lee sólo la adivinanza del vendedor: `process_pdf` va
  directo a Gemini Vision (según el revisor).
  Opciones:
  (a) RENDIMIENTO-2: leer el PDF en un proceso aparte, con tiempo y memoria
  máximos, que sí se puede matar. Es lo único que lo cierra; cambia cómo
  corre la lectura.
  (b) Para la adivinanza del vendedor, usar sólo pypdf, que aguantó los 10
  PDFs armados del revisor: el que más tardó, menos de 4 s, y el que más
  memoria usó, 152 MB. Es chico, pero deja a pdfminer en los otros
  caminos que lo usen.
  (c) Dejarlo.
  **Recomiendo (b) ya, como agregado de esta pieza, y (a) en la Fase 3**
  (seguridad). Con (b), el único camino que hoy le llega a pdfminer con un
  PDF del usuario queda cerrado.
- **D11 — La cuota diaria se cobra aunque la lectura dé 504.** Se descuenta
  antes de leer, como antes de esta pieza. Con Gemini real, el hilo sigue y
  gasta igual, así que devolverla dejaría gastar sin tope repitiendo
  lecturas lentas. **Recomiendo dejarla así** y anotarlo. Si D10 (a) entra,
  ahí se puede devolver la cuota, porque el proceso se mata.
- **D12 — Excel también frena el sitio (fuera de alcance).** Lo encontró el
  revisor Opus: `pd.read_excel` y `openpyxl.load_workbook` corren en el hilo
  del servidor. Un .xlsx de 3 MB congeló `/health` 21 s. **Recomiendo
  sumarlo a EXCEL-1**, que es mi próxima pieza y toca esas mismas rutas.

## Comandos copiables

```bash
git fetch origin claude/dev1-tecnica && git checkout 8fd801d
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 8fd801d 8080
# desde el worktree:
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_rendimiento1.py         # 14 passed
PY=$(which python) scripts/testing/sabotajes/rendimiento1.sh 8fd801d   # 11 «ROJO», «sabotajes con falla: 0»
# ojo: un venv viejo conserva PyPDF2 y jose aunque ya no estén en requirements.txt;
# para ver que no hacen falta, usá un venv nuevo (python3.12 -m venv) con sólo requirements.txt
```

## Evidencia (salida exacta)

**Rojo antes**, con las pruebas nuevas sobre el código de la base:

```
E   AssertionError: /health tardó 1.51 s mientras se leía un PDF
E   AssertionError: /health tardó 1.51 s mientras se leía el texto
E   AssertionError: 200 {"message":"PDF procesado exitosamente",...}   (sin tiempo máximo)
E   AssertionError: /health tardó 1.51 s mientras Gemini sugería
=================== 4 failed, 4 warnings in 6.28s ===================
```

Mi primera versión de esas pruebas daba verde sobre la base sin distinguir
nada: `/health` terminaba antes de que la lectura lenta empezara. Ahora la
demora se mide desde que empieza la lectura.

Segunda tanda, por los revisores, rojo antes del arreglo:

```
E   AssertionError: {"detail":"Invalid PDF file: could not convert string to float: '30s'"}
E   AssertionError: {"detail":"Leer el PDF tardó demasiado. ...","code":"PDF_READ_TIMEOUT"}   (un TimeoutError interno contado como lectura lenta)
E   AssertionError: assert 'Encrypted PDFs are not allowed' in 'Invalid PDF file: File has not been decrypted'
E   AssertionError: /api/ncm/sugerir esperó 2.70 s detrás de los PDFs lentos
```

**El cuelgue X3**, con un script aparte (PDF de una página cuyo contenido
termina en `%` sin fin de línea):

```
viejo salida=124                                # PyPDF2 3.0.1, cortado a los 10 s
nuevo páginas 1 texto '' 0.00s                   # pypdf 6.19
```

La prueba `test_pdf_armado_se_lee_sin_colgarse` obliga a pasar por pypdf
(pdfminer y OCR simulados vacíos) y comprueba que pypdf se usó. El
revisor Opus mostró que mi primera versión nunca llegaba a pypdf.

El único PDF del repositorio (`tests/test_factura.pdf`) da lo mismo con los
dos lectores: encriptado, páginas y palabras por página
(`iguales=1 distintos=0 errores=0`).

**Sabotajes** sobre `8fd801d`: los 11 de `rendimiento1.sh` en ROJO,
`sabotajes con falla: 0`. Los vigentes que tocan los mismos archivos siguen
en rojo: `admin1.sh` y `admin2.sh` (`sabotajes con falla: 0`) y
`sabotaje_maria2.sh` de la Dev 2 (`OK: los 8 sabotajes dan rojo por la
razón esperada`).

## Puertas sobre `8fd801d`

| Puerta | Resultado |
|---|---|
| Suite completa, worktree limpio, entorno nuevo sólo desde `requirements.txt` | `730 passed, 102 skipped, 24 warnings in 77.57s` |
| `compileall` y `pip check` | sin errores; `No broken requirements found.` |
| `smoke_friccion.sh` contra :8811 | `OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` | 22 BLOQUEADO, 0 FUGA |

## Autorrevisión

Los dos revisores se cortaron la primera vez por el límite de uso de la
cuenta. Los relancé a las 04:20 sobre `450f2d5`.

| Revisor | Hallazgo | Qué hice |
|---|---|---|
| Opus alto | las lecturas vencidas llenan el grupo de hilos compartido y traban la validación y NCM | grupo propio para leer PDF (`eafb0dc`) + prueba y sabotaje |
| Opus alto | Gemini en NCM sin tiempo máximo | 30 s y se sigue sin sus sugerencias |
| Opus alto | la prueba del PDF armado no pasaba por pypdf; tres sabotajes que la suite no veía | pruebas nuevas; los tres sabotajes ahora dan ROJO |
| Opus alto | encriptado con otro mensaje; tiempo de validación mal escrito rechaza todo; un TimeoutError interno contado como lectura lenta | arreglados, con prueba cada uno |
| Opus alto | cuota cobrada en el 504 | D11 |
| Opus alto | Excel frena el sitio | D12 |
| Opus alto | `scripts/security/*.sh` todavía nombran `python-jose` | fuera de alcance; no entran al build |
| Sonnet alto | PDF armado que cuelga pdfminer y bomba de memoria | D10 |
| Sonnet alto | la adivinanza del vendedor podía sumar 120 s más | tiempo propio de 15 s (`49113a0`) |
| Sonnet alto | el 504 no ofrecía la carga a mano y su código no seguía el estilo del resto | `lectura_pdf_demasiado_larga`, y la pantalla lo trata como MARIA-2 |
| Sonnet alto | el 400 de validación muestra el texto interno de la excepción | ya pasaba antes; sin cambio |
| Sonnet alto | `proyecto_maria/tests/test_pdf_router.py` parchea un PyPDF2 que ya no existe | carpeta vieja que la suite no corre; sin cambio |
| Sonnet alto | pypdf contra 10 PDFs armados | aguantó todos (menos de 4 s, 152 MB) |

## Qué no corrí

- Nada contra producción ni terceros. Gemini real tampoco: está simulado en
  todo.
- La pantalla con el error de lectura lenta no la vi en el navegador. El
  cambio es una condición en `upload.js` que reusa el camino de MARIA-2.
- No hice `/code-review` ni `/security-review` aparte: los dos revisores ya
  tuvieron ese foco y el tiempo de la cuenta es limitado. Si querés, los
  corro en la próxima vuelta.

## Archivos de producto que toqué

`proyecto_maria/main.py` (subida de PDF, `/api/ncm/sugerir`, helpers de
lectura), `proyecto_maria/security/file_security.py`,
`proyecto_maria/pdf_extractor.py` (sólo `_extract_pdf_text`),
`proyecto_maria/static/v2/screens/upload.js` (una condición),
`requirements.txt`, `CHANGELOG.md`.

## Sigo con

Lo que contestes de D10. Si no hay nada nuevo, EXCEL-1 (con D12 adentro, si
la aceptás).

Última vuelta: 2026-10-07 05:00 UTC
Contexto: ~42 %

`/compact conservar: Dev 1 de CDI en la rama claude/dev1-tecnica. ADMIN-1 y
ADMIN-2 aceptadas. RENDIMIENTO-1 entregada (código 8fd801d), informe en
PARA-PM.md con D10 (PDF armado cuelga pdfminer: recomendé usar sólo pypdf en
la adivinanza del vendedor ya y leer en un proceso aparte en la Fase 3), D11
(cuota en 504: dejarla) y D12 (Excel frena el sitio: a EXCEL-1). Después
siguen EXCEL-1, MARIA-1b y PUNTA-A-PUNTA-1. COBRO-CORTE-1 en pausa (D4=(b)
N=10, D5=(a), D6=(a)); COBRO-MP-1 es la primera pieza de la Fase 2. Entorno:
PM_DIR=/tmp/cdi-dev1, levantar.sh <SHA> 8811, venv /tmp/cdi-dev1/venv y
venv-limpio; sabotajes en scripts/testing/sabotajes/ (admin1, admin2,
rendimiento1) y scripts/testing/sabotaje_maria2.sh. Rutina de la PM:
trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
