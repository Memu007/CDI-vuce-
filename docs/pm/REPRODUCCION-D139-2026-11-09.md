# Reproducción D139 (a): escapar el panel de dev — 2026-11-09 02:20 UTC

Base `827df3e`, entrega `3fde8bb` (informe `d39c1f6`), rama `claude/dev-maria`.
Worktree desprendido en el scratchpad de la PM, borrado al terminar.

| Qué | Resultado |
|---|---|
| Diff de producto | sólo `dev_dashboard.html`: la tabla de pedidos con `textContent`; `fila` sube de pagos rechazados y se reusa |
| `grep innerHTML\|insertAdjacentHTML\|outerHTML\|document.write` en la plantilla | vacío |
| `node scripts/testing/pantalla_panel_dev.js` sobre `3fde8bb` | 7 OK, `fallas: 0`, salida 0 |
| La misma prueba con la plantilla de `827df3e` | `fallas: 4`: elementos creados 10, imágenes pedidas 1, fila 1 y fila 2 como texto; salida 1 |
| `scripts/testing/sabotajes/panel_dev.sh 3fde8bb` | BASE verde, 6 ROJO con su motivo, `sabotajes sin rojo: 0`, salida 0 |

No corrido por la PM: la suite pytest y el smoke (los corrió la Dev; la pieza
cambia sólo una plantilla del panel admin, sin datos, sesión ni permisos) y
adversarios nuevos (la Dev corrió Sonnet alto; su hallazgo de ejecución fuera
de la tabla quedó cubierto por la prueba).

Veredicto: aceptada, sin integrar.
