# Reproducción de DESPACHO-1c — 2026-11-05

Entrega: rama `claude/dev-maria`, producto hasta `1e8ee4d`, cabeza `5199709`
(trae CSRF-1 y CSRF-2 de la PM). Base `d25c263`. Worktree de PM `/tmp/cdi-pm/wd1c`.

**Veredicto: devolución.** Una causa: una falla de guardado puede quedar tapada
por un éxito en la pantalla.

## Lo que corrí yo (salida exacta)

```
== test_despacho1c
======================== 14 passed, 5 warnings in 2.99s ========================
== chequeo6
chequeo-6 d25c263..1e8ee4d: avisos para mirar, no un veredicto
producto +27/−10
arnés +279/−0
historia (grep de §6, sin líneas movidas): vacío
avisos: 0
== despacho1c
salida 0
7
fallas: 0
```

Coincide con el informe: 14 casos, 7 ROJO, 0 avisos.

## Lo que encontró el adversario (Sonnet alto), por lectura

- D57, de la Dev: cuando el guardado entero falla, `reSaveOperationAndClosePanel`
  muestra «Cliente guardado» encima del error.
- Lo mismo con un 402 (cuenta vencida, la nueva respuesta de COBRO-CORTE-1):
  el panel dice «Cliente asignado» aunque no se guardó nada.
- D53, de la Dev: `saveNcmUsage` (`ncm.js`) y aprender el catálogo
  (`finalize.js`) se tragan un 400.
- Una descripción sólo CJK o emoji normaliza a vacío. La pieza ya no la cruza
  con todo, pero dos de esas tampoco se distinguen entre sí. Se pesa en la
  devolución.

## No corrido por mí

- La suite sobre `5199709`: no corrida, porque la pieza vuelve.
- Playwright sobre las tres pantallas: no corrido, porque el arnés de la Dev ya
  da rojo con sus sabotajes.
