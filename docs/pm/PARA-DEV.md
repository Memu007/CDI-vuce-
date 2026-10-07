# PM → Dev 1

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev1-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM con
`merge`. Nunca `main`. La rama vieja `claude/project-deploy-review-4nct96`
queda como historia: todo lo suyo ya está en la de la PM.

Tus piezas están en `ROADMAP.md` (Dev 1): en la Fase 1, que la lectura de
PDF no se trabe, el Excel y los controles; después, cobro y seguridad. La
Dev 2 trabaja en `claude/dev2-maria`; no tocás su canal ni su rama.

Herramientas: todas menos el consejero; tu sesión y tus subagentes hasta
esfuerzo alto, nunca Fable (`ONBOARDING-DEV.md`, «Rol»).

Tu PM principal te despierta con `fire_trigger` de tu rutina; vos la
despertás a ella con el de la suya al entregar o al dejar una D que te frena
(`/entregar` §5). Los ids están en `NOW.md`, «Quién hace qué».

## Último veredicto

**PUNTA-A-PUNTA-1 aceptada sobre `3b52bc9`** (2026-10-07) e integrada. La PM
corrió la prueba (`7 passed, 3 xfailed`), tus 9 sabotajes (todos en rojo,
«con falla: 0») y la suite (`1226 passed, 102 skipped, 3 xfailed`). Detalle
en `REPRODUCCION-PUNTA-A-PUNTA-1-2026-10-07.md`. El caso del peso con más de
una unidad lo suma la Dev 2 con MARIA-5. Antes: MARIA-1b aceptada sobre
`beea9eb` (en Git).

## Respuestas a D28 a D31, COBRO-MP-1 (2026-10-07, 18:35 UTC)

- **D28: (a)**, seguir aceptando el aviso IPN sin firma. En tus riesgos
  queda escrito lo que sigue abierto: cualquiera, sin firma, hace que el
  servidor le pregunte a Mercado Pago por ids al azar con nuestro token. La
  tabla frena las repeticiones, no las consultas.
- **D29: (b)**, el precio del link cuando se armó, con tres condiciones:
  1. **Links viejos sin ese dato:** se compara contra el precio de hoy. Que
     quede escrito y probado.
  2. **Suscripción (preapproval):** `create_checkout`
     (`billing_service.py:161-190`) usa la suscripción cuando hay
     `MP_PREAPPROVAL_PLAN_ID_*`. Ahí el precio está en el panel de Mercado
     Pago, no en `PLANS`. Para esos pagos y sus renovaciones, el monto
     esperado sale de la suscripción leída en Mercado Pago. Si no, una
     diferencia entre el panel y el código rechaza todas las renovaciones.
  3. **Un pago rechazado es un cliente que pagó y no recibió nada.** No
     alcanza con el log: Emi tiene que poder verlo (en el admin que ya
     existe, o proponé dónde). Es criterio, no nota.
- **D30: (a)**, con el paso 4 en commits aparte.
  - Criterio: **si la respuesta de `/authorized_payments/{id}` no tiene la
    forma esperada, no se aplica nada** y se loguea.
  - La prueba en el sandbox es de la puerta G7, no una condición para
    publicar esta pieza: hoy no se le cobra a ningún estudio.
  - Le pregunto a Emi si `MP_PREAPPROVAL_PLAN_ID_*` está en Railway. Si no
    está, el paso 4 no corre en producción.
- **D31: visto bueno**, con condiciones:
  - Que no se aplique dos veces depende del índice único de la base, no de
    mirar antes de insertar.
  - Si el insert choca (`IntegrityError`), se responde `skipped` sin tocar
    la cuenta.
  - Una prueba con nombre manda dos avisos del mismo `payment_id` a la vez
    (`asyncio.gather`) y muestra que se aplica uno solo.
  - El `create_all` de la tabla, contra un Postgres de verdad si podés
    levantar uno local. Si no podés, lo declarás «no corrido»: SQLite no lo
    cubre.

## Respuestas a tus D (2026-10-07, 15:20 UTC)

- **D26: (a)**, en EXCEL-2 (abajo). El subagente lo confirmó: con 8 libros
  armados sin `<dimension>`, la subida normal da 400 a los 30 s.
- **D23 y D25** (el número de operación «FAC_…» y la referencia de la
  factura): son identificadores del TXT y van a **MARIA-6** (Dev 2). Mientras
  tanto, en PUNTA-A-PUNTA-1 marcalos como diferencias conocidas
  (`xfail` con la D en el motivo), no los arregles.
- **D24** (la pantalla no tiene dónde cargar subítems): se la pregunto a
  Emi. Por ahora, igual que D23.
- **`cuit_agr` y `vendedor_id` con dígitos de ancho completo:** la línea que
  ofreciste va en EXCEL-2, como «de paso».
- Anteriores (D13 a D22): en Git.

**Ya decididas para COBRO-CORTE-1** (2026-10-07; tus opciones están en tu `PARA-PM.md`
del commit `62b1d14`):
- **D4 (cuándo se cuenta): (b), con N = 10.**
- **D5: (a).** Sólo por estado en las rutas que gastan Gemini o generan valor;
  el tope, donde se cuenta una operación.
- **D6: (a)** ahora. El índice único (b), pieza aparte más adelante, después
  de mirar si producción ya tiene códigos repetidos.

## Tarea activa — EXCEL-2

Del `ROADMAP.md`: lo que el Excel todavía no lee (encabezado fuera de la fila
1, sin columna de origen, celdas combinadas: D18), CSV con `;`, latin-1 o BOM
en el historial de NCM, y que el aviso de mapeo nombre la columna usada.
Además:
1. **D26 (a):** las hojas se cuentan desde `xl/workbook.xml`, sin abrir el
   libro; se rechaza antes de abrirlo un libro cuyos textos compartidos o
   cuya primera hoja pasen de un tamaño. Criterio: con 8 libros armados sin
   `<dimension>` delante, la subida normal da 200, y un `sharedStrings` de
   19 millones de entradas vacías no pasa de 1 GB de memoria.
2. **De paso:** un monto que es un entero JSON gigante (`10**400`) o una lista
   da 400, no 500 (`OverflowError`), en `/generate_maria`, los subítems y la
   exportación; y `cuit_agr` y `vendedor_id`, sólo con dígitos 0-9.

## Siguiente, apenas entregues EXCEL-2

Escrito el 2026-10-07, 18:00 UTC, mientras la PM revisa EXCEL-2. Si el
veredicto trae devolución, va primero.

1. **GUARDAR-1, sólo si Emi dice que sí** (lo encontró el ataque a la
   segunda publicación, `REPRODUCCION-PUBLICACION-2-2026-10-07.md`, #1).
   En producción, guardar una operación cuyo producto lleva la SIM completa
   (`84714900100D`) da 500 y no guarda nada, porque
   `client_product_history.ncm` es `String(10)` y el error salta en el
   `commit` de `save_client_operation`. En SQLite no se ve.
   - **Alcance:** la operación se guarda siempre, aunque falle el historial
     (el historial no puede tirar abajo el guardado), y el historial guarda la
     posición completa o una forma que entre, sin perder la que usa la
     sugerencia.
   - **Sin migraciones a ciegas:** si hace falta cambiar la columna, D con
     el plan para Postgres y cómo se vuelve atrás.
   - **Criterios:** rojo antes y verde después contra Postgres (no
     alcanza SQLite), y suite completa.
2. **Si no, COBRO-MP-1** (Fase 2, `ROADMAP.md`): el aviso de pago de
   Mercado Pago verificado y aplicado una sola vez aunque se reenvíe, con el
   monto controlado (C3 de `AUDITORIA-2026-10-06.md`, tu D8). Además, que una
   renovación de la suscripción extienda el período (hoy sólo se procesa
   `type == "payment"`). Es plata: revisión fuerte (Opus y Sonnet, alto), y
   nada contra Mercado Pago real.

