# Reproducción de MARIA-2 — 2026-10-07

**Veredicto: aceptada sobre `65ea6f3`** (base `cb8f509`).

## Lo que corrió la PM

Worktree limpio en `65ea6f3`, Python 3.12, con `GEMINI_API_KEY=test-key`,
`ENVIRONMENT=test`, VUCE, Tarifar y AFIP simulados, y el dólar contra un
puerto local cerrado.

| Qué | Salida |
|---|---|
| Rojo antes: la prueba nueva con el producto de `cb8f509` | `AssertionError: {"message":"PDF procesado exitosamente",…"descripcion":"ITEM DEMOSTRACION (Falta API Key)"…` |
| Focales: `test_maria2_sin_clave_gemini.py` y las del TXT (`test_generar_maria_txt`, `test_maria_subitems`, `test_maria_iext_anio`, `test_maria_gastos_fob`) | `91 passed, 4 warnings in 5.90s` |
| `python -m compileall -q proyecto_maria` | ok |
| Suite completa | `689 passed, 102 skipped, 9 warnings in 64.39s` |

Coincide con el informe (689/102/0). El generador del TXT no cambió.

## Subagente de la PM

Sonnet medio, sin Gemini real ni internet.

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | Con clave, un archivo inválido ya no gasta cuota (antes sí) | Es el supuesto 1 de la Dev. Aceptado: gasta menos. El límite de pedidos sigue |
| 2 | Un archivo enorme se lee entero antes del 413 | De antes (el servidor recibe el archivo completo antes de la función). Bajo; no es de esta pieza |
| 3 | Sin clave: extensión mala o PDF roto dan 400; PDF válido da 503; cero productos; cuota sin tocar | Confirma la entrega |
| 4 | La pantalla v2 muestra el 503 con el botón; la pantalla vieja v1, sólo texto | Ya lo dijo la Dev |
| 5 | Otros dos caminos no vivos usan la clave sin quitar espacios | Informativo; sólo los usan las pruebas |

Buscó `DEMOSTRACION`, «Falta API Key» y modos demo fuera de las pruebas: no
quedan en el producto.

## No corrido por la PM

- Los 8 sabotajes de la Dev (`scripts/testing/sabotaje_maria2.sh`).
- La pantalla en el navegador (la captura de la Dev está en
  `docs/pm/capturas/maria2-sin-lector.png`).
- Una factura real con Gemini real: no se puede desde acá.

Contexto de la Dev 2 al entregar: ~24 % (237 mil tokens).
