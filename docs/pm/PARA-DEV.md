# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev1-tecnica` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev técnica: lectura de Excel y PDF, clientes y estudio, cobro y
seguridad. La Dev MARIA trabaja en `claude/dev-maria` (el TXT); no tocás su
canal ni su rama, ni `maria_generator.py`.

Esfuerzo medio (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev técnica:». Ella te despierta igual.

**Datos reales:** la proforma de la reunión del 2026-10-24 tiene datos de
un cliente: no entra al repositorio. Las pruebas usan sintéticos.

## Veredicto de EXCEL-3f (con H1-bis) (2026-10-28): aceptada

Sobre `8c63c37` (informe `0557f03`). El detalle está en
`REPRODUCCION-EXCEL-3f-2026-10-28.md`. Corrí la suite desde base limpia,
`cliente1c.sh` entero (44 ROJO), los 39 sabotajes de 3f y los que
reapuntaste de `excel3.sh` (todos en rojo) y trece negativos míos en
`.xlsx` y `.xls`, en la base y en la entrega. Mi adversario no corrió
(presupuesto). Integro tu rama hasta `8e744a0`, sin GUARDAR-2, que sigue en
revisión. **Con esto EXCEL-3 queda cerrada.**

- **Bien:** H1-bis tapa la clave en todas las formas que probé; D21 (b),
  D22 (b), H5, la descripción repetida a mano y el texto de contenedor, con
  sus sabotajes. Lo único que cambia el FOB es el plural, y se comporta como
  su singular en la base. Tus supuestos y tus riesgos quedan aceptados.
- **Riesgos que anoto, no los arregles:** «Seguros para puerta» sin origen
  sale del FOB con su fila nombrada (ya pasaba con el singular); «Transporte
  interno» con origen y «DHL» solo no llevan aviso (no cambian el FOB).
- **Un rojo que no es tuyo, para después de ORDEN-1:**
  `test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`.
  En mi contenedor (4 núcleos) da rojo siempre: en la suite y 6 de 6 corrido
  solo, 3 en la base `89a0fde` y 3 en `8c63c37`. La subida normal tarda
  30,7 a 32,7 s y da 400 («tardó demasiado»). Vos lo viste 1 de 5. Lo que
  importa es que en producción una subida normal puede esperar ~30 s detrás
  de ocho pesadas. Pedido: diagnosticá dónde se van los 30 s (cola,
  hilos, CPU) y proponé el arreglo con una D. Sin subir el corte de 30 s ni
  aflojar la prueba.

## Tu diagnóstico de `test_excel2` y D4-D5 (2026-10-28): EXCEL-2b, ahora

Recibido en `b5a50d1` (medición `ff03efe`). Diagnóstico aceptado: los 30 s
son cola detrás de las pesadas, no trabajo de la subida normal. Es el
criterio de EXCEL-2 ya aceptado (D26 a: ocho libros armados y la normal da
200), así que arreglarlo está dentro del roadmap y no va a ABUSO-1.

- **D4: (a), carril liviano.** Pieza **EXCEL-2b**, ahora. Condiciones:
  - el umbral se mide una vez, sobre las partes XML descomprimidas (no las
    imágenes), con valor por defecto en el código y variable de entorno;
  - el tope de 10 MiB y el resto de los cortes de EXCEL-2 no se tocan;
  - sin límite de frecuencia: eso es ABUSO-1;
  - un caso que muestre que un libro que dice ser chico y no lo es no
    entra al carril liviano (el umbral no se puede burlar desde el libro);
  - sabotajes que manden la normal al carril pesado y que salteen la
    medida del umbral;
  - (b) y (c) no entran ahora.
  Toca `file_security.py` y `main.py`: revisión fuerte con adversario
  (cupo, hoy después de las 18:00 UTC).
- **D5: (a).** La prueba afirma también `dt` < 5 s, en la misma pieza.

Decidido por la PM.

## ORDEN-1 (en revisión) y tus D (2026-10-28)

Recibida en `cdc9c57` (código `0d89c20`). Es de pantalla y del borrador
del navegador: la reproduzco ahora y sumo un adversario sobre los
borradores (computadora compartida, pérdida de productos) cuando haya
presupuesto, hoy después de las 18:00 UTC. Mientras, no la integro.

- **D1: (a).** El orden vive en el borrador de cada pestaña. Una columna
  que nadie lee es una migración sin uso; si algún día una pantalla
  reabre operaciones del servidor, la posición entra en esa pieza.
- **D2: (a). Tenías razón:** «el Excel» lo puse yo sin comprobar que v2
  lo tuviera. Se cumple con la tabla y el TXT. Un Excel de la operación
  en v2 no entra al roadmap salvo que Emi lo pida.
- **D3: (a).** El centavo puede cambiar de ítem, el total no. Queda el
  xfail con su motivo.

Decidido por la PM.

## GUARDAR-2 (en revisión)

Recibida en `cef45ce` (informe `cb42e8f`). Toca lectura por dueño: la
reviso con adversario cuando haya presupuesto (hoy, después de las 18:00
UTC). Si vuelve con devolución, va antes que lo que estés haciendo.

## Orden

1. EXCEL-2b (D4 a y D5 a), ahora.
2. Si GUARDAR-2 u ORDEN-1 vuelven con devolución, esa va primero.
3. Después, COBRO-MP-1.
