# COBRO-CORTE-1, vuelta: reproducción de la PM (2026-11-05)

Veredicto: **devolución por dos causas** sobre `0b9ccde` (base `375edbc`).

## Lo corrido por la PM

| Qué | Resultado |
|---|---|
| `pytest tests/test_cobro_corte1.py` en `0b9ccde` | `82 passed, 5 warnings in 64.20s` |
| `chequeo-6.py 375edbc 0b9ccde` | `producto +131/−149`, `arnés +575/−260`, historia vacío, `avisos: 0` |
| `cobro_corte1.sh` con Postgres | corriendo al escribir esto (18 ROJO hasta ahora, de 60); el resultado va abajo |
| Reintento tras falla de escritura, Postgres local | `1.er pedido (falla al escribir): 500 ops 1` / `reintento sin operacion_id: 200 ops 2` / `filas: MARIA_FAC_W1_2e78fb6c.TXT, MARIA_FAC_W1_2d601b03.TXT` |

El script del reintento es de la adversaria Sonnet; lo corrí yo contra mi
Postgres (puerto 55462, base nueva `pm_wf`). Parchea `_user_downloads_dir`
a una ruta inexistente en el primer pedido. En `375edbc`, según la misma
adversaria, el reintento daba `ops 1` (no lo corrí yo en la base).

## Adversarias (Opus alto y Sonnet alto, contexto nuevo)

- **Respuesta tardía hereda el id** (las dos, por separado, Playwright con
  `page.route` demorando la respuesta): Opus `h2 … mandada=la de C true …
  ops antes 3 despues 3`; Sonnet `usadas desde el inicio: 1 (esperado 2)`,
  una fila para dos facturas, la de A apuntando al archivo de B. Ventana
  natural sin demora: 0,08 s (20 ítems) a 0,95 s (400 ítems) en Postgres
  local. `finalize.js` asignación tras generar y tras guardar.
- **Se cobra antes de entregar** (Sonnet): arriba, reproducido por la PM.
- **NUL / surrogate en `operacion_id` da 500 en Postgres** (las dos):
  `/generate_maria` 500 con `\x00` y `\ud800`; exportación 500 con
  `\ud800`; guardado 500 con `\ud800`. `ops` no sube. Lo había dejado la Dev
  como plausible.
- **Aviso de borrar cliente** promete borrar el historial; queda «Sin
  cliente» (Sonnet, reproducido).
- **`delete_cliente` sin candado** al reescribir `extra` (Opus, plausible).
- Previos o dentro de riesgos declarados: mensaje «actualizá a Premium»,
  dos relojes en el inicio de período, pestañas viejas al publicar, una
  operación sirve para 10 facturas desde la consola.
- Limpio: vaciado de `operacionId` en todos los caminos de carga de v2;
  nombre de archivo sin escape ni choque práctico; id ajeno da operación
  nueva; huella de exportación con otro día igual; sin `REGENERACIONES_AGOTADAS`;
  planes legados 200; sin sesión 401.

## No corrido

- Suite completa (la Dev informa `4476 passed, 121 skipped, 3 xfailed` en `da8effc`).
- El patrón de v1 (`app.js:3390`, `:3751`).
- El reintento contra `375edbc` por mi cuenta.
