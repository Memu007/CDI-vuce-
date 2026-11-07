# Reproducción PYPDF-1 (Dev MARIA) — 2026-11-06

Entregado: `974263e` (producto `f3bd528`, pruebas `2471da2`, `9204e26`,
`db384f1`, `974263e`; informe `7417fe8`). Base de la pieza: `3e6320a`.
Entorno de la PM: venv con pypdf 6.21.4, sin red, `GEMINI_API_KEY` vacía.

## Puertas

| Puerta | Informe | PM |
|---|---|---|
| producto | `+4/−2`, un `except` y `requirements.txt` | igual (`git show f3bd528`) |
| chequeo-6 `3e6320a 974263e` | sin avisos propios | 1 aviso, de la limpieza de la PM (`fecha_inic_activ.py:1`), no de la pieza |
| `test_rendimiento1c` + `test_despacho1b` + `test_rendimiento1d` + `test_rendimiento1` | — | `324 passed in 123.74s`, salida 0 |
| `rendimiento1c.sh` | 18 ROJO, 0 falla | 18 ROJO, `sabotajes con falla: 0`, salida 0 |
| D87 (sin el tope de RunLength) | 2 failed | 2 failed: `test_una_hoja_que_se_infla_con_run_length_se_saltea`, `test_los_topes_de_pypdf_cubren_todos_los_filtros` |
| suite completa sobre `974263e` | `4989 passed, 335 skipped, 3 xfailed` | salida 0 con `-x`: ninguna falla. La línea con el conteo se perdió al recortar la salida, así que el número no está medido |

`despacho1b.sh` entero (133 sabotajes) no se corrió: queda como puerta de la
PM antes de publicar, como dice el informe.

## Negativos de la PM (por `validar_pdf_aparte`, en el proceso aparte)

| PDF | Resultado |
|---|---|
| válido de una hoja | `{'encriptado': False, 'paginas': 1}` |
| válido cortado al final | `{'error': 'Stream has ended unexpectedly'}` |
| `%PDF-1.4` + basura | `{'error': 'Stream has ended unexpectedly'}` |
| `/Pages` que se tiene de hijo | `{'error': 'Detected cyclic page references.'}`, no se cuelga |
| arreglo de 150 000 números en un objeto que no se lee | abre, 1 hoja |
| ~600 bytes con `xref 0 999999` | `PdfDemasiadoPesado` |

El último es el caso de D90: un PDF chico y roto recibe «demasiado pesado».
Es un 400 seguro; el mensaje es impreciso, no peligroso.

No se lanzó adversario propio: el producto cambia dos líneas y la Dev ya corrió
Sonnet alto y `/code-review high`. Los negativos de arriba atacan otros bordes.
