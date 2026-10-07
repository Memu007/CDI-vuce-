# Reproducción de GUARDAR-1 — 2026-10-07

**Veredicto: aceptada** sobre `d6fe25f` más `aec4f15` (la línea de la e2e).
D32: (b), que va como GUARDAR-2.

**Aislada:** la rama de la Dev en `d6fe25f` traía, sobre `6ea8ca9`, también
EXCEL-2 (devuelta) y COBRO-MP-1 (sin revisar). La PM pasó sólo los ocho
commits de GUARDAR-1 con `cherry-pick` sobre su rama:

```
01d5723 191db69 3135802 6d918d8 e08c920 d6fe25f cabf090 aec4f15
```

Entraron limpios, salvo el CHANGELOG, que quedó sólo con la entrada de
GUARDAR-1. El resultado es `2621c3b`, integrado en `a9b03cf`.

`git diff 2621c3b a9b03cf` sin `docs/pm` da vacío. Contra `main` (`6ea8ca9`),
el producto cambia sólo en `main.py` y `client_memory.py`; además entran las
pruebas, los scripts, `config/e2e_maria.js` y las pruebas de
PUNTA-A-PUNTA-1, ya aceptadas.

## Lo que corrió la PM, sobre `2621c3b`

| Qué | Salida |
|---|---|
| Rojo antes: `test_guardar1.py` con el producto de `4c6f2d4` | `ImportError: cannot import name 'NCM_HISTORIAL_MAX'` (no distingue caso por caso; el rojo lo da Postgres, abajo) |
| Suite | `1247 passed, 102 skipped, 3 xfailed, 25 warnings in 130.74s` |
| e2e de la CI | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |

## Subagente de la PM (Sonnet alto, Postgres 16 local)

| Qué | Salida |
|---|---|
| `guardar1_postgres.py` en `2621c3b` | `fallas: 0`, 13 OK; `guardar con la SIM completa responde 200 (… "historial_guardado":true)` |
| Lo mismo en `4c6f2d4` | 7 `FALLA` (la Dev dijo 6); después revienta porque falta `ncm_para_historial` |

**Se sostiene:**
- **Operación atómica:** con un trigger diferido que falla en el COMMIT,
  todo en 0.
- **El contador:** nunca cuenta dos veces. Un 500 por cuerpo malo no cuenta.
- **50 productos con uno que falla:** `historial_guardado:false`, 50 ítems,
  49 en el historial.
- **Conexión que se cae después del commit:** la operación queda y el
  guardado siguiente anda.
- **Historial viejo de 10 caracteres:** `lookup` y `sugerir` dan lo mismo
  que en la base.
- **Listar y exportar:** andan.
- **Tiempo:** 120 ítems en 1,04 s, contra 0,67 s en la base.

| # | Hallazgo | ¿Antes? | Cómo quedó |
|---|---|---|---|
| 1 | Ocho guardados a la vez: el contador queda en 1 o 2, y los `op_code` se repiten | Sí, idéntico | A COBRO-CORTE-1 |
| 2 | Con 14 de 15 usadas, ocho guardados a la vez entran los ocho | Sí | A COBRO-CORTE-1 |
| 3 | Un `grupo_id` que no es entero se descarta sin aviso (antes, 500) | Nuevo; la pantalla no lo manda | Se deja |
| 4 | «DOLARES» se guarda como `DOL`; «CHINA» como `CHI` (esto ya pasaba) | La moneda es nueva (antes, 500) | Se deja |
| 5 | NUL al editar un producto, o un `\ud800` suelto al guardar: 500 | Sí | Se deja |
| D32 | Con la pieza, la sugerencia del cliente (`84714900`) tapa la SIM del proveedor (`84714900100D`). La pantalla exige `^\d{11}[A-Z]$`, así que lo que antes llegaba listo ahora llega incompleto | Nuevo (antes no se guardaba nada) | (b) en GUARDAR-2 |

**La D32 medida:**
- **Opción (a), agrandar la columna:** en Postgres no reescribe la tabla (3
  millones de filas en 3,6 ms, mismo `relfilenode`), y el código publicado
  anda con la columna ancha.
- **Pero (a) tiene tres problemas:**
  - El `ALTER` que espera una transacción abierta frena a todos los que
    vienen detrás; hace falta `lock_timeout`.
  - En el solapamiento del despliegue, las conexiones abiertas dan
    `InvalidCachedStatementError`: un guardado perdió el historial sin
    avisar.
  - Además no alcanza sola: `upsert_client_product_history` no actualiza el
    `ncm` de una fila que ya existe.
- **Opción (b):** arregla lo que ve la persona, sin migración. Por eso se
  eligió.

## No corrido

- Los sabotajes de la Dev (`sabotajes/guardar1.sh`).
- La facturación por organización.
- Un corte en medio del primer commit.
- Producción.

Contexto de la Dev 1 en la pieza: de ~18 % a ~45 % (`get_session`).
