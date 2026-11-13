# Reproducción de SEPARADORES-1b-LIMPIEZA (2026-11-12)

Entrega de la Dev técnica: tests `bb0d3347`, informe `28236cc1`, base `d8383df2`.
Sólo arnés (`tests/test_separadores1b.py` y dos anclas de
`scripts/testing/sabotaje_separadores1b.sh`). Revisado por la PM principal en un
worktree aparte, sobre `bb0d3347`, con el guion de esa versión.

## Lo reproducido

| qué | salida |
|---|---|
| `tests/test_separadores1b.py` | `105 passed` (igual al informe) |
| `chequeo-6.py d8383df2 bb0d3347` | producto +0/−0, arnés +11/−18, historia vacía, avisos: 0 (igual) |
| `anclas_perdidas.py bb0d3347 \| grep -c separadores1b` | `0` |
| `sabotaje_separadores1b.sh bb0d3347` | BASE `265 passed`; 12 ROJO; `factura_multiplica` y `factura_grupo_con_espacio` 5 failed cada uno; «OK: los 12 sabotajes dan rojo por la razón esperada»; salida 0 (igual) |

## Mi mutación, distinta de las del guion

Saqué sólo ` ` (espacio fino) de la clase que limpia los grupos en
`_monto_factura` (`pdf_extractor.py:2202`). Da 1 failed, 104 passed, y el rojo
es exactamente
`test_en_la_factura_con_la_pista_en_contra_queda_sin_leer[4 500.000-,]`:
cada separador de la familia tiene su entrada que lo distingue.

## Lo que no corrí

La suite completa: la pieza es sólo de tests y la tarea no la pedía.
