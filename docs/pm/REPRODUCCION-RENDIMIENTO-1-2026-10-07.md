# Reproducción de RENDIMIENTO-1 — 2026-10-07

**Veredicto: aceptada sobre `8fd801d`** (base `0ff38db`), con un agregado
obligatorio antes de publicarla: RENDIMIENTO-1b (D10 b).

## Lo que corrió la PM

Worktree limpio en `8fd801d` y un **venv nuevo armado sólo con su
`requirements.txt`** (Python 3.12): `pypdf 6.19.0`, sin PyPDF2, `python-jose`
ni `ecdsa`; `pip check`: `No broken requirements found.` Variables de prueba de
siempre (Gemini falso, terceros simulados, dólar contra un puerto cerrado).

| Qué | Salida |
|---|---|
| Rojo antes: `tests/test_rendimiento1.py` con el producto de `0ff38db` | `14 failed` (`/health` tarda `1.506 > 1.5` s durante una lectura, sin tiempo máximo, PDF armado colgado, PyPDF2 y jose presentes, …) |
| Focal | `14 passed, 4 warnings in 10.44s` |
| Suite completa | `730 passed, 102 skipped, 23 warnings in 81.78s` |

Coincide con el informe (730/102/0).

## Subagente de la PM (Sonnet alto)

**Se sostiene:** las lecturas y NCM corren aparte con tiempos máximos; `pypdf`
no se cuelga con PDFs armados; nada vivo importa PyPDF2, `jose` ni `ecdsa`; el
504 llega bien a la pantalla v2 (ofrece la carga a mano); con `pypdf` el texto
de los PDF de prueba es el mismo y un PDF encriptado AES da el mensaje limpio
(antes filtraba un error interno).

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | **D10 de la Dev, confirmado:** con una cuenta de prueba gratis, 4 subidas en paralelo de un PDF armado de 442 bytes dejan colgados los 4 hilos de lectura (CPU sostenido); después, un PDF bueno da 504 para cualquier usuario hasta reiniciar. `/health` sigue respondiendo (0,6 a 1 s) | Antes de la pieza ese PDF colgaba el servidor entero: es una mejora, pero no se publica sin cerrar D10. **RENDIMIENTO-1b** (D10 b): el único camino vivo hacia pdfminer es la adivinanza del vendedor (`main.py` → `_extract_pdf_text`); pasa a usar sólo `pypdf`. El proceso aparte que se puede matar (D10 a) va a ABUSO-1, Fase 3 |
| 2 | Leído: un tiempo máximo en `0` o negativo no cae al valor por defecto (corta todo al instante) | En RENDIMIENTO-1b |
| 3 | `process_pdf` usa sólo PyMuPDF; `robust_extract_pdf_items` y `_extract_items_per_page` (pdfplumber) no tienen llamadores vivos | Confirma el alcance de D10 b |

## No corrido por la PM

- Los 11 sabotajes de la Dev (`scripts/testing/sabotajes/rendimiento1.sh`):
  crean worktrees.
- Gemini real: la sugerencia de NCM con tiempo máximo se probó con uno falso.

Contexto de la Dev 1 al entregar: ~41 % (407 mil tokens a las 03:15 UTC).
