# Reproducción de VALOR-1 — 2026-10-25

Sobre `3352a01` (informe `23ba183`, base `f71eaa9`). La PM corrió las
pruebas y los sabotajes. Dos revisores adversariales con contexto nuevo:
Opus alto (dinero y API) y Sonnet alto (pantalla). Todo local y con
sintéticos.

**Veredicto: devolución (VALOR-1b).** No se integra.

## Lo que se corrió

| Qué | Resultado |
|---|---|
| `tests/test_valor1.py` sobre `3352a01` (PM) | `49 passed` |
| `git diff 3352a01 23ba183 -- proyecto_maria tests scripts` y lo mismo contra `d234fe2` | 0 líneas |
| `scripts/testing/sabotaje_valor1.sh` (PM) | «OK: los 31 sabotajes dan rojo por la razón esperada», `fin rc=0` |
| TXT con ajustes contra TXT sin ajustes, 36 variantes (Opus) | idéntico byte a byte |
| FOB de la tarjeta contra `MDDTFOB` (Opus), 290 operaciones sintéticas | iguales en 290 de 290 |
| Basura por API (texto, listas, NaN, `inf`, enteros enormes) | ningún 500 |
| TXT descargado con el botón real (Sonnet) | con ajustes, idéntico; con «Calcular seguro» cambian sólo `MDDTASS`, `MARTASS` y `MARTBASIMP` |
| Respuestas fuera de orden, 25 rondas al azar con demoras de 0 a 900 ms (Sonnet) | la última gana |
| Cambio de operación con un pedido en vuelo (Sonnet) | no arrastra nada |
| HTML inyectado en descripción, moneda, filas, `valor.error` y avisos | no ejecuta nada |

## Hallazgos

| # | Qué | Gravedad |
|---|---|---|
| V1 | **Cuentas viejas después de «Usarlo».** `usarDescuento()` (`finalize.js`) cambia `op.ajustes_deducir` y llama a `refrescarAvisos()`, pero no a `cuentasViejas()`. Los manejadores del campo sí lo hacen. Si se aprieta «Calcular seguro» antes de que vuelvan las cuentas, el seguro sale con el FOB de antes del descuento. La PM lo reprodujo con `_pantalla({"descuento": 87.5}, "usarDescuento(); calcularSeguro();", VALOR)` de `tests/test_valor1.py`: 93,13 en vez de 92,25. El revisor de pantalla vio lo mismo (4,01 en vez de 3,01). El aviso «se calculó con otros importes» llega recién después. Contradice el punto 3 del informe y la línea del CHANGELOG «no usa cuentas de antes de cambiar un ajuste». | media-baja: dinero en el TXT, depende del orden de los clics |
| V2 | **El aviso del seguro no se va.** `calcularSeguro` no suma `seguro` a `campos_completados`. «No pudimos leer el seguro de la factura: completalo.» sigue después de calcularlo (`review.js:692`, `semaforo.js:53`). Con `seguro` en `campos_sin_leer`, el botón ofrece el 1 % sin decir que la factura probablemente traía un seguro. | baja |
| V3 | **D13 confirmada.** Con 1000 a deducir, `MDDTFOB=1387.50` y `MDDTASS=83.13`. El TXT lleva un FOB sin ajustes y un seguro calculado con ajustes. | media: TXT incoherente |
| V4 | **Ajustes que no son número, por API.** `MariaRequest` (`main.py:4110`) tipa `ajustes_incluir` y `ajustes_deducir` como `float \| None`. Con texto, `/generate_maria` da 422 (antes, 200) y `/generate_maria/avisos` da 422 y se pierden todos los avisos. | baja: sólo por API |
| V5 | El texto crudo de una excepción de Python llega a `valor.error`. | baja |
| V6 | Al restaurar una operación con un ajuste mal escrito, el error se ve sobre un campo vacío. | baja |
| V7 | `type=number` toma «1.000,50» como 1,0005 y «3.480» como 3,48, sin aviso. Los campos de flete y seguro ya hacen lo mismo: no es regresión. No se probó en Chrome real con es-AR. | riesgo |
| V8 | Cosméticos: textos cortados a 20 caracteres, «otro» importe con «0», un ajuste mal escrito se cuenta como 0, desborde con 13 cifras a 390 px. | baja |

## Lo que no se corrió

- La suite completa (la Dev sí, sobre `3352a01`).
- El smoke y la e2e (la Dev sí).
- El recorrido real desde la subida hasta la pantalla final.
- Chrome real con locale es-AR, otros navegadores y un móvil real.
- `/security-review`.
