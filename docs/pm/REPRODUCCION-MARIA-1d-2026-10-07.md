# Reproducción de MARIA-1d — 2026-10-07

**Veredicto: aceptada sobre `9679e21`** (informe en `e28be2f`, que sólo suma
el informe). Producto: `1ad7929` y `470b6eb` (base `8770925`) y `5512ad6`, el
punto sumado (base `0d6cb3e`). Se integra junto con MARIA-3, después del
ensayo.

## Lo que corrió la PM

Worktrees limpios, venv de siempre, Gemini falso, terceros simulados.

| Qué | Salida |
|---|---|
| Rojo antes: `test_maria1d_campos_vacios.py` con el producto de `8770925` | `44 failed, 4 passed`: `assert 'None' == ''`, `assert 'NON' == ''`, `«None» en el TXT`, `assert 200 == 400` |
| Rojo antes del punto sumado (`-k procedencia_rara_de_un_producto`, producto de `0d6cb3e`) | `8 failed`: el texto «Item 1: Procedencia no reconocida …» no está en `/generate_maria/avisos` |
| Focal (MARIA-1d, archivos reales, MARIA-3, IEXT y gastos) | `264 passed, 5 warnings in 8.57s` |
| Suite | `1029 passed, 102 skipped, 24 warnings in 76.03s` |

Coincide con el informe (1029).

## Subagente de la PM (Sonnet medio)

**Se sostiene:**
- La regla es por campo entero: `NA-123`, `None Ltd`, `N/A Corp`, `0` y
  `12345` se conservan.
- El lector ya no inventa DOL ni FOB.
- `/avisos` y `/generate_maria` coinciden en 26 variantes de procedencia en
  producto (`cn`, `China`, `0310` pasan; `²`, `ARG`, `XX`, `１０` frenan con
  el mismo texto).
- Los dos archivos reales salen idénticos.

| # | Hallazgo (todos ya pasaban en `8770925`) | Cómo quedó |
|---|---|---|
| 1 | Por la API, `moneda` = `USD`, `US$` o `u$s` e incoterm `FRE`, `NAN` o `Ex Works` llegan al TXT sin aviso (la pantalla v2 los traduce o los frena) | Lo cubre MARIA-1b (Dev 1): moneda de 3 letras sin «USD» e incoterm válido. Se comprueba al integrar las dos |
| 2 | `MariaRequest` trae `moneda="DOL"` e `incoterm="FOB"` por defecto, y `finalize.js` rellena DOL y FOB: el aviso de moneda o incoterm vacíos no se ve desde la pantalla | Lo cubre MARIA-1b (en `21a7a7e` el pedido trae `""` por defecto). Ídem |
| 3 | «None», «null» o «N/A» escritos (a mano, o en una operación guardada con el lector viejo) llegan al TXT y al nombre del archivo (`MARIA_None.TXT`, `IDSO=None`), sin aviso de carátula | A MARIA-5: en el servidor, esos valores enteros cuentan como vacío |
| 4 | Un ítem con cantidad, valor o peso `NaN` da 200 y `MDDTFOB=nan`, `QARTKGRNET=nan` | Es de los controles de MARIA-1b: se comprueba en esa revisión |
| 5 | La copia de PDF directo (la que usa producción) no trata la descripción como la de PyMuPDF: «None» o «N/A» quedan escritos, y `0` queda vacío. Termina en el 400 «Descripción muy corta», no en el TXT | A MARIA-5: las dos copias, iguales |
| 6 | Bajo: `moneda="NaN"` queda `NAN` | Lo frena o lo avisa MARIA-1b (moneda rara) |

## No corrido por la PM

- Los sabotajes de la Dev (`sabotaje_maria1d.sh` y los de MARIA-3, 4, 1c, 2b,
  2 y 1a) y `pantalla_maria3.js`.
- Gemini real: el prompt sin «Ante duda, DOL» se comprobó leyendo el código.

Contexto de la Dev 2: ~60 % al entregar; compactó después (94 mil tokens a
las 12:35 UTC).
