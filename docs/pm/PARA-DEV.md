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

**GUARDAR-1 aceptada sobre `d6fe25f` más `aec4f15`** (2026-10-07, 21:20 UTC).
- **Aislada:** `d6fe25f` traía también EXCEL-2 y COBRO-MP-1. La PM pasó sólo
  tus ocho commits con `cherry-pick` (`2621c3b`); entraron limpios, salvo el
  CHANGELOG. Está integrada en `a9b03cf`, que es el candidato a publicar.
- **Lo que corrió la PM sobre `2621c3b`:**
  - Suite: `1247 passed, 102 skipped, 3 xfailed`.
  - e2e de la CI: «E2E MARIA OK».
  - `tests/test_guardar1.py` no corre con el producto viejo: importa
    `NCM_HISTORIAL_MAX`. El rojo antes lo da `guardar1_postgres.py`.
- **El subagente (Sonnet alto, contra Postgres 16):**
  - Base: 7 fallas. Con la pieza: `fallas: 0`.
  - Nunca queda una operación sin ítems, y el contador nunca cuenta dos
    veces.
  - Con 50 productos y uno que falla, se pierde sólo ese en el historial.
  - Si se cae la conexión después del commit, la operación queda.
  - El historial viejo de 10 caracteres y el listado y la exportación andan
    igual.
- Detalle en `REPRODUCCION-GUARDAR-1-2026-10-07.md`.

**D32: (b)**, sin migración. Si el historial del cliente tiene 8 dígitos y
el catálogo del proveedor tiene una SIM completa que empieza con esos 8, gana
la del proveedor.
- (a) no alcanza sola: `upsert_client_product_history` no actualiza el `ncm`
  de una fila que ya existe.
- Además, el `ALTER` necesita `lock_timeout`, y en el despliegue las
  conexiones abiertas dieron `InvalidCachedStatementError` (un guardado
  perdió el historial sin avisar).
- Va como **GUARDAR-2**, apenas entregues la devolución de EXCEL-2 (abajo).

**Se deja, anotado:**
- Ocho guardados a la vez cuentan de menos y repiten el `op_code`, y con 14
  usadas entran 8. Ya pasaba: va a COBRO-CORTE-1, que es «sin pasarse del
  tope».
- Un `grupo_id` que no es entero se descarta sin aviso (la pantalla no lo
  manda).
- La moneda «DOLARES» se guarda como `DOL`.
- Un NUL al editar un producto da 500.

---

**Devolución de EXCEL-2 (en curso)**, sobre `3e6e63e` (2026-10-07, 19:45 UTC) por seis puntos.

**Lo que corrió la PM:**
- Rojo antes, `test_excel2.py` con el producto de `3b52bc9`:
  `43 failed, 8 passed`.
- Suite: `1277 passed, 102 skipped, 3 xfailed`. Coincide con tu informe
  (1267 más los 10 que deselecciona la CI).

**Lo que se sostiene:**
- Las hojas con nombre repetido y una relación normal.
- Los 19 millones de textos vacíos: 400 en 0,1 s y 153 MB.
- Las entidades XML: expat 2.6.1 corta.
- El orden de los topes.
- Las combinadas con filas vacías de verdad arriba, y los números puros.
- El cuerpo del 400 nunca sale vacío.
- Coma, punto y coma, tab, comillas y BOM en el CSV.
- Nueve libros normales dan lo mismo que en `3b52bc9`, y los archivos
  reales salen idénticos.
- El CUIT del despachante.

Detalle en `REPRODUCCION-EXCEL-2-2026-10-07.md`. Los archivos de ataque no
están en tu contenedor: abajo dice cómo armarlos.

**Orden:** primero termina **GUARDAR-1**, porque es un error que ya está en
producción y EXCEL-2 no está publicada. Después, esta devolución. Después,
COBRO-MP-1.

1. **Una combinada gigante no traba la lectura (rompe).**
   - `_rellenar_combinadas` recorre cada combinada hasta su última fila, y
     el corte de 10.000 combinadas no acota nada.
   - Ejemplo: un libro de pocos KB con `<mergeCell ref="C2:C1048576"/>`
     repetido 2000 veces ocupa un hilo unos 1000 s, y con dos así la subida
     normal da 504. Con 10 combinadas, 5,6 s contra 0,1 s en `3b52bc9`.
   - Criterio: el trabajo es proporcional a las filas de la tabla, no al
     tamaño de las combinadas. El caso de 2000 tarda menos de 1 s.
2. **Una combinada en cantidad, precio o peso nunca se copia (rompe:
   plata).**
   - La guarda sólo frena números puros. Con «5 UN» y «USD 100» combinados
     en `D2:D3` y `E2:E3`, la fila de abajo pasa de 0/0 a 5/100: el FOB se
     duplica. Con «$ 1.500,00» en el precio, copia 1500.
   - Que la regla sea por columna, no por el valor: en las columnas de
     cantidad, valor y peso, no se copia nada.
3. **Los estilos con un tope que proteja de verdad (rompe).**
   - Un `styles.xml` de 10 MB de `<xf/>` (el archivo pesa 17 KB) pasa la
     validación, sube a 1,4 GB de memoria y tarda 52 s. Con dos así, la
     subida normal da 504 y el proceso llega a 1,9 GB.
   - Con `<font/>`, 884 MB; con `<dxf/>`, 870 MB.
   - El tope de cada parte que openpyxl lee entera se elige midiendo la
     memoria. Criterio: ningún libro que pasa la validación pasa de 1 GB.
4. **Las hojas como las ve openpyxl, y el criterio de la D26 con otros
   libros.**
   - **La hoja escondida:** `hojas_del_xlsx` sólo cuenta relaciones con un
     `Type` que termina en `/worksheet`. openpyxl abre como hoja cualquier
     relación que no sea de gráfico. Una segunda hoja con el mismo nombre que
     la primera y un `Type` raro no se mide ni se saca del zip: con 8 así
     delante, la normal da 504.
   - **La primera hoja grande:** una de 27 MB sin `<dimension>` queda bajo
     el tope de 30 MB, y con 8 así delante la normal da 504.
   - Criterio: con 8 libros de cada tipo delante, la normal da 200. Si para
     eso el tope de la primera hoja tiene que bajar a un tamaño que una
     factura real podría pasar, D con lo medido.
5. **El CSV nunca pierde las tildes en silencio.**
   - Un solo par de bytes cp1252 que parece UTF-8 manda todo el archivo a
     UTF-8 con reemplazo: «Acci�n», «Beb�», «Ni�o».
   - Los pares: «é» seguido de «®», «ñ» seguido de un espacio duro (0xA0),
     «ó» seguido de «¿».
   - En `3b52bc9` el archivo se rechazaba, y se veía.
   - Criterio: esos cp1252 se leen bien. Si no se puede decidir la
     codificación, sale un aviso.
6. **Una fila vacía dentro de una combinada no es una «fila sin leer».**
   - Con `C2:C4` sobre una fila vacía, la fila 3 sale en
     `filas_excel_sin_leer`. Es por rellenar antes del `dropna`.

**De paso:** con `cantidad: 10**400`, el 400 de `/generate_maria` trae
también «Valor inválido» y «Peso inválido». Que nombre sólo el campo malo.

**Se deja, anotado:**
- Un perfil con un CUIT que no tiene 11 dígitos ahora da 400 con un mensaje
  claro. Antes salía `CDDTAGR=123`.
- 92 MB de medios en un libro de 2 hojas: 359 MB y 1,4 s, dentro del tope de
  100 MB.

**D27: (a)**, se dejan 10 MB. El subagente confirmó que el mensaje llega a
la pantalla (`upload.js` muestra `detail`).

**Criterios:** rojo antes y verde después en cada punto. Los archivos reales
y los nueve libros normales dan lo mismo. Suite completa en verde.

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

## Siguiente, apenas entregues la devolución de EXCEL-2 — GUARDAR-2 (D32 b)

Escrito el 2026-10-07, 21:20 UTC.
- **Qué arregla:** en la sugerencia de NCM (`/api/catalog/lookup`,
  `/api/ncm/sugerir` y el autorrelleno), si el historial del cliente tiene 8
  dígitos y el catálogo del proveedor tiene una SIM completa que empieza con
  esos 8, gana la del proveedor.
- **Cómo se prueba:** hoy, con GUARDAR-1, la pantalla recibe `84714900` y
  marca incompleto lo que antes llegaba listo (`84714900100D`).
- **Sin migración.** Vale también para lo que ya escribía `guardar-uso`.
- **Criterios:** rojo antes y verde después, contra Postgres. La e2e da «E2E
  MARIA OK». Suite completa.

Después, COBRO-MP-1 (en pausa).

## Antes: GUARDAR-1 (Emi dijo que sí) — aceptada

Escrito el 2026-10-07, 18:40 UTC. **Emi dijo que sí a GUARDAR-1**: es un error
que ya está en producción, así que va antes que COBRO-MP-1.
- **COBRO-MP-1 queda en pausa en `83b4ec1`** (pasos 1 y 3 hechos, sin
  entregar). Anotá en tu `PARA-PM.md` dónde quedó; nada de `/entregar`.
  La retomás después de GUARDAR-1, con D28 a D31 como están.
- **Dato nuevo para COBRO-MP-1:** Emi confirmó que las variables
  `MP_PREAPPROVAL_PLAN_ID_*` están en Railway. El paso 4 y la rama de la
  suscripción de la D29 corren en producción: que no se aplique nada si la
  respuesta no tiene la forma esperada es lo que protege la plata.
- La devolución de EXCEL-2 va después de GUARDAR-1 (arriba).
- **Sumá a GUARDAR-1 la e2e de la CI.** `main` (`6ea8ca9`, publicado hoy)
  tiene la CI en rojo en `e2e-maria`: `config/e2e_maria.js` no completa la
  fecha de emisión que pide MARIA-3, y `confirmReview` espera para siempre.
  - La PM lo reprodujo, y con una línea pasa entero («E2E MARIA OK»): en
    `confirmReview`, después del incoterm,
    `await replaceInput(page, '#f_fecha_emision', '01/10/2026');`. Usá una
    fecha que no avise (ni futura ni de hace más de dos años).
  - Corré la e2e sobre tu SHA. Cómo se corre en la nube está en
    `ONBOARDING-DEV.md`.

1. **GUARDAR-1** (lo encontró el ataque a la
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
2. **Después, COBRO-MP-1** (Fase 2, `ROADMAP.md`): el aviso de pago de
   Mercado Pago verificado y aplicado una sola vez aunque se reenvíe, con el
   monto controlado (C3 de `AUDITORIA-2026-10-06.md`, tu D8). Además, que una
   renovación de la suscripción extienda el período (hoy sólo se procesa
   `type == "payment"`). Es plata: revisión fuerte (Opus y Sonnet, alto), y
   nada contra Mercado Pago real.

