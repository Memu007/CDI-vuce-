# Reproducción de MARIA-1a y MARIA-2b — 2026-10-07

**Veredicto: MARIA-1a aceptada sobre `0a1775f`** (base `321f34b`) **y
MARIA-2b aceptada sobre `c3bef51`** (encima de MARIA-1a). MARIA-1a no se
publica sin MARIA-1c (D5).

## Lo que corrió la PM

Worktrees limpios, Python 3.12, Gemini falso, terceros simulados, dólar contra
un puerto cerrado.

| Qué | Salida |
|---|---|
| MARIA-1a, rojo antes (`test_maria1a_lectura_factura.py` con el producto de `321f34b`) | `59 failed, 2 passed` |
| MARIA-1a, focal con los archivos reales (`test_generar_maria_txt`, `test_maria_subitems`, `test_maria_iext_anio`, `test_maria_gastos_fob`) | `143 passed, 5 warnings in 6.23s` |
| MARIA-1a, suite | `777 passed, 102 skipped, 24 warnings in 77.51s` |
| MARIA-2b, rojo antes (`test_maria2b_gemini_falla.py` con el producto de `0a1775f`) | `12 failed, 2 passed`: `assert 400 == 503` |
| MARIA-2b, focal (con MARIA-2 y MARIA-1a) | `84 passed, 5 warnings in 1.20s` |
| MARIA-2b, suite | `791 passed, 102 skipped, 24 warnings in 69.00s` |

Coinciden con los informes (777 y 791). El generador del TXT no cambió.

## Subagente de la PM (Sonnet alto)

**MARIA-1a se sostiene:** unos 300 casos de país, ningún código equivocado
(los 194 de tres letras coinciden con `iso-codes`); `1.234,56`, `1,234.56`,
`1 234,56`, `$1,234.56`, `U$S` bien; `1.500` y `1,500` según la pista, vacío
sin pista. **MARIA-2b se sostiene:** clave inválida, caída, respuesta
ilegible, vacía y configuración rota dan 503 con el mensaje fijo, sin
productos inventados.

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | D5, reproducido hasta el TXT: flete `"1,500"` sin pista y seguro `"350 USD/kg"` salen `MDDTFLE=0.00` y `MDDTASS=0.00`; el único aviso es «se declaró 0.00». Antes la factura daba 400 | MARIA-1c, antes de publicar MARIA-1a |
| 2 | Leído: la pantalla vieja (`static/app.js:3289`, `/dashboard?v=1`) repone `cantidad \|\| 1` y `origen \|\| 'CN'` antes de generar. En la v2, `/generate_maria` da 400 con origen vacío, cantidad 0 o peso 0 | MARIA-1c |
| 3 | Leído: al guardar, `main.py:5509-5511` repone 1 y 0,5 (D6 de la Dev) | MARIA-1b (Dev 1) |
| 4 | Una falla de Gemini gasta cuota (`[503, 503, 429]` con límite 2) | D8: se deja, como la D11 de la Dev 1 |
| 5 | Bajo: `{"items": null}`, `[]` o prosa dan 503 en vez de 400 | Se deja: los dos ofrecen la carga a mano |
| 6 | Nombres que quedan vacíos (no equivocados): «United States», «Viet Nam», «Republic of Korea», «Made in PRC», «Países Bajos», UAE, Hong Kong, Macao | Se deja: vacío más el semáforo |
| 7 | Sin verificar: Países Bajos sale 434 (HOLANDA); la tabla VUCE también tiene 423 (PAISES BAJOS) | Lo dirá un archivo real o la prueba en el Kit |

## Producción hoy

El código publicado (`a771693`) corta el país a dos letras
(`pdf_extractor.py:2194` y `:2361`): si Gemini devuelve `CHN` o `China`, el
TXT sale con Suiza. Hasta publicar MARIA-1a, Emi revisa el país de origen
antes de mandarle un TXT al despachante.

## No corrido por la PM

- Los sabotajes de la Dev (`sabotaje_maria1a.sh`, `sabotaje_maria2b.sh`).
- La copia del lector con PyMuPDF real (`fitz` no está en `requirements.txt`:
  producción usa la de PDF directo).
- Gemini real.

Contexto de la Dev 2 al entregar: ~52 % (MARIA-2b); ~38 % al entregar MARIA-1a.
