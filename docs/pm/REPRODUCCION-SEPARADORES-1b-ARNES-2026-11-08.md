# Reproducción de SEPARADORES-1b-ARNÉS, 2026-11-08

Entrega de la Dev técnica: arnés en `1063b32`, informe en `63de556`, base
`ea63923`. Sólo toca `scripts/testing/sabotaje_separadores1b.sh`.

## Resultado

**Aceptada sobre `1063b32`, sin integrar.** Igual al informe.

| Qué | Salida |
|---|---|
| `chequeo-6.py ea63923 1063b32` | `producto +0/−0`, arnés `+11/−5`, avisos 0 |
| `sabotaje_separadores1b.sh 1063b32` | `BASE en verde: 265 passed`, 12 `ROJO`, «OK: los 12 sabotajes dan rojo por la razón esperada», salida 0 |

La ruta de la cola de limpieza estaba mal escrita; el guion es
`scripts/testing/sabotaje_separadores1b.sh`. El paso de base nuevo hace que
un guion roto en la base ya no pase por sabotaje que no distingue.

El hallazgo de la Dev (el caso «la pista en contra queda sin leer» ya no
distingue la regla `sin_grupo`) va a `COLA-LIMPIEZA.md`.
