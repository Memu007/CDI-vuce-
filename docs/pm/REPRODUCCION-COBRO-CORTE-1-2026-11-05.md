# Reproducción de COBRO-CORTE-1 — 2026-11-05

Entrega: rama `claude/dev-tecnica`, producto hasta `75c6476`, informe `a09197f`.
Base `f54d8a9`. Worktree de PM `/tmp/cdi-pm/wcc1` en `75c6476`.

**Veredicto: devolución.** Una causa: el id que arma la pantalla con el número
de factura se usa como identidad de la operación, y el guardado reemplaza lo que
encuentra con ese id.

## Lo que corrí yo (salida exacta, recortada)

Pruebas de los adversarios, sobre `75c6476`, SQLite temporal, `ENVIRONMENT=test`:

```
# dos operaciones distintas con FAC_0001, guardadas al mismo cliente
save1 200
save2 200 True
operaciones en historial: 1 ops_used: {'ops': 1, ...}
  OP-000001 [('Operacion DOS proveedor B', 200.0)]      # la primera se perdió

# 12 contenidos distintos con el mismo id
estados: [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 409, 409] {'ops': 1, ...}

# exportación idéntica en 12 días distintos (fecha del generador falseada)
estados: [200 ×10, 409, 409] {'ops': 1, ...}           # la fecha del TXT gasta huella

# ids que el saneo junta
['MARIA_A-12.TXT', 'MARIA_A1-2.TXT']   # cuatro ids, dos archivos

# D61: generar, A, B, A, B
gen 1 · A 1 · B 2 · A otra vez 2 · B otra vez 2

# borrar el cliente y regenerar el mismo id
antes ops 1, 1 operación · del 200 · tras borrar 0 operaciones · regen 200 · ops 2

# la razón del 402 cambia en el segundo pedido (active sin MP, vencida hace 10 días)
REQ 0 402 'Venció tu suscripción…'
REQ 1 402 'Venció tu prueba gratis…'

# plan='trial' (default de User.plan) al guardar
SAVE plan trial -> 500

4 passed in 5.36s
```

`ENVIRONMENT == "testing"` en el producto: en la base había 1 aparición en esas
dependencias; en `75c6476` hay 4 (`require_billing_vigente`,
`require_active_billing`, `_contar_operacion_bloqueada`, `_contar_maria`). Sólo
aplica si el usuario del token no existe en la base.

## Lo que encontraron los adversarios (Opus alto y Sonnet alto)

Comprobado por ellos y reproducido por mí arriba: pérdida de historial con el
mismo número de factura; 409 permanente (también por la fecha de exportación);
saneo que junta ids; D61 cuenta dos en el flujo natural; borrar el cliente
recuenta; la razón del 402 cambia; plan legado da 500.

Comprobado por ellos, no por mí:
- `clientes.js:449` y `:628`: con la cuenta vencida, la importación de clientes
  muestra el texto literal «payment_required» (Sonnet, Playwright).
- `finalize.js:1127` `reSaveOperationAndClosePanel` muestra «Cliente asignado»
  aunque el guardado dé 402 (Sonnet, por lectura). Es la misma función que la
  devolución de DESPACHO-1c le pide a MARIA.
- `/generate_maria_export` da 500 con `plan='trial'` (Sonnet).

Sin hallazgo (de ellos): las cinco carreras en Postgres (Opus, base propia
borrada al final); no hay fuga entre cuentas por el guardado; todas las rutas
que llaman a Gemini o escriben el TXT tienen el corte; la pantalla v2 muestra
la razón del 402 y el 409.

Sospechado, sin reproducir: dos inversiones de orden de locks (ruta manual con
extras vencidas; aceptar invitación). Van a la cola de limpieza.

## No corrido por mí

- `tests/test_cobro_corte1.py` (la Dev: 65 passed), `cobro_corte1.sh` (44 ROJO),
  `cobro_corte1_postgres.py` y la suite (4455 passed): no corridos, porque la
  pieza vuelve.
- chequeo-6 del rango.
