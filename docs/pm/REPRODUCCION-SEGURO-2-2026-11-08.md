# Reproducción de SEGURO-2, 2026-11-08

Entrega de la Dev MARIA: producto y pruebas en `d160738`, informe en
`e6adea1`, base `3366ca5`. Corrido por la PM desde un worktree de `d160738`,
venv Python 3.12, sin red y con `GEMINI_API_KEY` vacía.

## Resultado

**Aceptada sobre `d160738`, sin integrar.** Igual al informe.

| Qué | Salida |
|---|---|
| `chequeo-6.py 3366ca5 d160738` | `producto +46/−20`, 3 `AVISO` explicados en el informe (26 netas; dos IIFE de archivo entero) |
| suites de seguro, valor y MARIA de la entrega | `242 passed, 4 warnings in 46.30s`, salida 0 |
| `sabotajes/seguro2.sh d160738` | 19 `ROJO`, `sabotajes sin rojo: 0`, salida 0 |
| `sabotajes/seguro1.sh d160738` | 12 `ROJO`, `sabotajes sin rojo: 0`, salida 0 |
| `sabotajes/valor1c.sh d160738` | en curso al subir este commit (4 ROJO de 25 hasta ahí); se completa en el siguiente |

La suite completa no la repetí: la Dev la corrió dos veces (5294 passed) y
el diff no toca el servidor fuera de `_seguro_por_corregir` y el pedido.

## Adversario Sonnet alto (en pantalla real, Playwright)

Levantó la app de `d160738` en modo fake y manejó la pantalla. No encontró
ninguna secuencia que genere un TXT con un seguro sin leer, ni con el 1 %
calculado o dejado bajo CIF, ni una que deje a la persona sin salida. Probó
FOB y CIF con seguro sin leer, `0`, ` 0 `, `0,00`, vaciar, `abc`, calcular →
CIF, dejar → recargar → CIF, firma con respuestas viejas, y que dos bloqueos
no consuman operación. Dos bajas:

1. Calcular el 1 % con FOB y después pasar a CIF deja el aviso «no pudimos
   leerlo de la factura», que es falso: lo calculó el sistema. El freno es
   el correcto (con CIF hay que escribir el seguro). Ya en los riesgos del
   informe; el texto va a AVISOS-1.
2. Después del 400 «no pudimos leerlo», la pantalla vuelve a la revisión
   pero el texto queda en la pantalla de generar, oculta: en la revisión sólo
   se ve el chip del semáforo. La pista fija del campo sigue diciendo «Dejar
   en 0 si no aplica» con el campo vacío. Nuevo; va a AVISOS-1.

## Decisiones

- D125 (a): el freno mira cómo llegó el seguro, no cuánto vale.
- D126 (a): la nota igual para los cinco incoterms.

## Riesgos que quedan

- El servidor confía en las marcas que manda la pantalla (D125).
- `separadores1b.sh` da salida 1 igual en la base (patrón 3 roto desde
  `4f2045f`): arnés roto de antes, a `COLA-LIMPIEZA.md`.
- No se probó un PDF real (Gemini apagado); `campos_sin_leer` se armó con la
  forma de `pdf_extractor`.
