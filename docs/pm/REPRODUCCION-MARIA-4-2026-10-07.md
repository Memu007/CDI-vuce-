# Reproducción de MARIA-4 — 2026-10-07

**Veredicto: devuelta** (sobre `6149ef3`, base `448b54d`), por tres puntos: un
estado que contradice el origen sale sin aviso, la pantalla vieja no muestra
los supuestos, y `origen` y `pais_origen` se leen en distinto orden.

## Lo que corrió la PM

Worktree limpio, Python 3.12, Gemini falso, terceros simulados.

| Qué | Salida |
|---|---|
| Rojo antes: `test_maria4_despachante.py` con el producto de `448b54d` | `30 failed, 2 passed` (`generate_maria_txt() got an unexpected keyword argument 'banco_bcra'`, `assert 200 == 400` con origen argentino sin estado, …) |
| Focal con los archivos reales, supuestos, sub-ítems, `IEXT` y gastos FOB | `127 passed, 3 warnings in 6.73s` |
| Suite completa | `837 passed, 102 skipped, 24 warnings in 71.58s` |

Coincide con el informe (837/102/0).

## Subagente de la PM (Sonnet alto)

**Lo central se sostiene.** Los valores raros dan 400 o se normalizan bien
(estado `0`, `7`, `"2.0"`, `True` → 400; `" 3 "`, `"03"` → 3; `ivaad1` →
`IVAAD1`; banco `19`, `1911`, `abc` → 400; `psad01` → `PSAD01`). Un producto
argentino sin estado da 400, también en grupo. El estado sigue al producto
al reordenar. **Archivos reales:** 2025 idéntico byte a byte; 2026, con
espacios normalizados, difiere sólo en `LDVDREFDOC` (MARIA-6) y una línea en
blanco al final: nada de los cuatro campos ni de su orden. **Propuesta de
banco y empresa:** ningún usuario ve operaciones ni clientes ajenos (404).

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | Un estado «argentino» (1, 3, 5) con origen extranjero, o «importado» (2, 4, 6) con origen argentino, sale al TXT sin aviso. En pantalla: estado 3 elegido con origen AR, después origen CN → el pedido lleva `['CN','3']` | **Devolución** |
| 2 | La pantalla vieja (`static/app.js:3360-3440`) no muestra `warnings` ni `supuestos`: genera con los valores por defecto sin que nadie los vea. La tarea pedía «su aviso» | **Devolución** |
| 3 | Sólo por API: el generador usa `pais_origen or origen` y los supuestos `origen or pais_origen`; con `pais_origen=CN` y `origen=AR` sale `CARTUSO=2` sin aviso | **Devolución** |
| 4 | Un grupo con estados distintos da 400 (toast en pantalla); la tabla no muestra qué filas son grupo; un `estado` dentro de un sub-ítem se ignora (sólo por API) | Se deja |
| 5 | El banco no se valida contra una tabla: `000` y `999` pasan | Se deja: no hay tabla de fuente oficial; lo verá la prueba en el Kit |

## No corrido por la PM

- Los sabotajes de la Dev (`sabotaje_maria4.sh`) y su comprobación de
  pantalla (la corrió el subagente: `OK: pantalla MARIA-4`).
- El orden de los códigos 1 a 6 en el Kit real (lo confirma la prueba del
  despachante).

Contexto de la Dev 2 a las 06:10 UTC: ~58 % (576 mil tokens).
