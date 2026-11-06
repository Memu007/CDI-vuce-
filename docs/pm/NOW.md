# NOW — CDI

Actualizado: 2026-11-04. Estado vigente; la historia está en Git.

Método al día con CAMBIOS.md del secondbrain hasta 2026-10-31 (aplicado 2026-11-04).

**Publicado 2026-10-24 20:33 UTC:** `main` = `8b45207` (EXCEL-3 + CLIENTE-1),
con «dale 8b45207» de Emi; avance limpio sobre `dddcf6d`. Evidencia: CI
40128443771 verde (tests y e2e) sobre ese SHA; producto idéntico a `3fd8826`,
donde la suite local de la PM dio verde; sabotajes sobre `8b45207`: excel3
27/27 en rojo; cliente1 14 rojos y 1 «sin rojo» por una carrera de la prueba
(el foco a `#cfNombre` a los 80 ms parte el `fill` del CUIT; reproducida 2
de 82), sólo de prueba, va como PRUEBAS-1. La cadena de los scripts de piezas
viejas sigue corriendo y se anota al terminar. Falta: que Emi lo pruebe en el
sitio (proforma real y alta de cliente).

**EXCEL-3 aceptada 2026-10-24 19:30 UTC** (Dev técnica; producto `f3f9eb8` +
`b76be2f`): integrada por SHA (`a173af2`) a la rama de la PM, merge `a0c15ac`.
**Publicada** en `8b45207` (arriba); falta que Emi pruebe la proforma real en el sitio.
Detalle en `REPRODUCCION-EXCEL-3-2026-10-24.md`. D1 (descuento positivo,
sólo leído) y D2 (CLIENTE-1, a la vista con aviso) decididas por la PM;
Emi puede cambiarlas. Lo menor del adversario queda como EXCEL-3b, después
de PA-1.

**CLIENTE-1 aceptada 2026-10-24 19:41 UTC** (Dev técnica; producto `fbc006a` +
`12ff9b6`): el alta de cliente muestra CUIT, razón social, domicilio e inicio
de actividad y avisa cuáles faltan. Integrada por SHA (`c402bcb`) a la rama
de la PM, merge `23d7d5d`. **Publicada** en `8b45207`. Detalle en
`REPRODUCCION-CLIENTE-1-2026-10-24.md`. D3 (a) decidida por la PM: editar no
borra una fecha guardada en otro formato; va con PA-1. Hallazgo: la fecha de
inicio va al TXT como `AAAA-MM-DD` y el MARIA usa `DD/MM/AAAA`; sumado a
MARIA-7 como punto 9.

**PA-1 + D3 aceptada 2026-10-24 21:10 UTC** (Dev técnica; producto
`489daf4`, `c7e4c3a`, `26797f8`, `d8e084c`): «PA SIM» en las pantallas y
editar un cliente no borra una fecha de inicio que el campo no muestra.
Integrada con `merge` (`fe41228`), **sin publicar**. Detalle en
`REPRODUCCION-PA-1-2026-10-24.md`. D4–D7 decididas por la PM: la demo de la
landing va como PA-1b; la fecha validada en la API (con «None» y años de 5
cifras) va a CLIENTE-1b, y limpiar lo guardado en producción lo decide Emi.

**PRUEBAS-1 + PA-1b aceptadas con nota 2026-10-25 00:47 UTC** (Dev técnica,
sobre `e924b29`): sólo pruebas y la demo de la landing. Integrado `e924b29`
exactamente (merge `4f00636`), sin los commits de EXCEL-3b que vienen
después en su rama; **sin publicar**. `foco_cliente1.sh` dio rc=1 sobre
código sano: la nota va a CLIENTE-1b. Detalle en
`REPRODUCCION-PRUEBAS-1-2026-10-25.md`.
**Cola técnica, aceptada e integrada, sin publicar (2026-10-25 09:30 UTC):**
EXCEL-3d, CLIENTE-1b, ESTUDIO-1 y **EXCEL-3e** (`6f798d8`, informe
`e1acb64`), juntas con `merge` de `claude/dev-tecnica` (`5eb6ae4`). Un cargo
con medidas «/», «-» o 0 bajo una combinada ya no entra como producto sin
aviso. D24 (a). **CLIENTE-1c y ESTUDIO-1b aceptadas 2026-10-27** sobre `3aba9c2` (merge de `418ada3`): con eso ESTUDIO-1 ya se puede publicar. H1-bis (la clave de `--base` como la escribe SQLAlchemy) va primero en EXCEL-3f; hasta entonces el script de fechas no se corre contra producción. Detalle en `REPRODUCCION-ESTUDIO-1b-2026-10-27.md` y en la «Vuelta» de `REPRODUCCION-CLIENTE-1c-2026-10-27.md`.
Detalle en `REPRODUCCION-EXCEL-3e-2026-10-25.md`.
**Cola MARIA, aceptada e integrada, sin publicar:** MARIA-7/8
(`1fa0b6e`), VALOR-1b y MARIA-9 (`9f787f6`), SEPARADORES-1 y VALOR-1c
(`a099655`: el flete «3.480» ya no sale 3,48, lo ambiguo se pregunta) y
**SEPARADORES-1b 2026-10-25 08:30 UTC** sobre `db39de0`: un monto ilegible
ya no va como 0 y «1234.567» se pregunta. D20 (a), D21 (b), D22 (a, ARCA).
**SUFIJOS-1 (vuelta) y SEPARADORES-1c aceptadas 2026-10-27** sobre `45a3ea1`
(merge `e9981e5`, suite 3393 passed, 0 rojos). **SEPARADORES-1d aceptada 2026-10-27** sobre `140c122`
(avance rápido, suite 3478 passed, 0 rojos). Activa: **ORG-1** (invitaciones del estudio, permisos; lista en `ddfc798`, se entrega con el cupo del 28/10 18:00 UTC) y **ORG-1b** (email invitado completado en el registro, D27). Detalle en
`REPRODUCCION-SEPARADORES-1b-2026-10-25.md`.

**Rojos de la CI de mi rama (desde `bcab8b5`):** los 12 conocidos (11 de presupuesto y `test_guardar1`) los cierra `2ff3262`, que entró con el merge del 27/10; la suite local sobre `3aba9c2` da 0 rojos. Falta ver la CI verde en ese push antes de dar por cerrado.

**Rojo conocido de EXCEL-2, ya publicado:** `test_excel2.py::test_ocho_libros…`
falla siempre en la máquina de la PM (4 núcleos), también en la base: una
subida normal detrás de ocho libros de ~10 MiB espera en la fila de 2 hilos y
pasa el tope de 30 s. Pendiente de Emi: si se prioriza.

**Desde el 2026-10-24, tarde:** Codex deja CDI (Emi). Dos Devs nuevas en
Claude («Quién hace qué»). Ese día Emi y el despachante cargaron en el MARIA
el TXT de una factura real después de doce correcciones a mano: son la
Fase 1b del roadmap nuevo a tres meses (`ROADMAP.md`, aprobado por Emi el 2026-10-24). Pendiente de Emi: el esfuerzo en los dos chats
nuevos (el `/autocompact 200k` ya está: los dos marcan 200k), el packing list y los códigos de destino que manda el despachante.

**Publicación del 2026-10-24 10:00 ARG (`648cd2f`):** completada; cierre en `CIERRE-RETOMA-2026-10-24.md`.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06). Railway
(`cdi-production.up.railway.app`) publica cada push a `main` sin esperar los
tests. **En producción:** la usa sólo Emi, con facturas reales.
**Plan:** `ROADMAP.md`, con el orden de Emi del 2026-10-07: primero el TXT,
después el cobro, la seguridad al final y exhaustiva. Ningún estudio entra
antes de cerrar la Fase 3.

## Para Emi

1. **Segunda publicación, hecha:** `6ea8ca9`, 2026-10-07 19:58 UTC («dale
   6ea8ca9» de Emi). Emi genera un TXT con una factura real, lo descarga
   enseguida y mira: fecha DD/MM/AAAA, CUIT sin guiones, IVA adicional
   `NO_VALIDA`, `CARTUSO` 2, banco y empresa de digitalización. Ahora pide
   fecha de emisión, moneda, incoterm, CUIT válido y estado si el origen es
   argentino: un error que pide eso no es una falla. Guardar con la SIM
   completa sigue dando error hasta GUARDAR-1.
1a. **Sin volumen** (Emi, 2026-10-07): cada publicación o reinicio borra los
   TXT generados y el historial de NCM aprendido; las operaciones quedan en
   la base. Descargar el TXT apenas se genera. Lo arregla DISCO-1 (Fase 3).
2. **Rotar las claves de Gemini y revocar la de Anthropic** (G0). Gemini: en
   Google AI Studio borrar las que aparecieron, crear una nueva y ponerla sólo
   en Railway; mirar la facturación. Anthropic (2026-10-24): hay una clave
   real en `scripts/utils/cambiar_ai.sh:62` de `main` y en el historial desde
   `32e4282`; revocarla en la consola de Anthropic. Después, pieza chica para
   sacar el archivo (el historial queda; lo que protege es revocar).
3. **Despachante:** recordarle los archivos reales (favor 1). Ya respondió
   todas las preguntas.
4. **Catálogo NCM:** Emi trajo el nomenclador vigente (2026-10-07). Lo
   carga la Dev 2 en CATALOGO-NCM-1. Una línea de Emi: ¿lo bajó de
   `arca.gob.ar`?
5. **Hasta publicar MARIA-1a: revisar el país de origen de cada TXT** antes
   de mandárselo al despachante. El código publicado corta el país a dos
   letras: si la lectura devuelve «CHN» o «China», sale Suiza.
6. **Límite de uso de la cuenta:** lo tocó dos veces el 2026-10-07: entre
   las ~02:05 y las 03:40 UTC, y entre las ~18:34 y las 18:50 UTC (las dos
   Devs quedaron paradas; la PM las despertó a las 18:56). Por la regla de
   Emi (`DECISIONS.md`), **hoy se compacta desde el 30 % las Devs y el 40 %
   las PMs**; mañana vuelve a 60 y 50.
7. **No pedirle a ningún asistente cambios sobre `main`:** desde el
   2026-10-07 `main` tiene las reglas nuevas, pero cada push publica.
8. **Decidido por la PM (2026-10-29), D de COBRO-MP-1:** D8 (a), las
   consultas a Mercado Pago a un hilo con tope van en una tarea aparte
   después de esta tanda; D9 (b), una renovación sin pago identificado
   responde 503 para que Mercado Pago reintente; D10 (a), el botón que
   queda en «Abriendo…» se arregla recargando (riesgo aceptado).
9. **Emi respondió lo pendiente (04/11, `DECISIONS.md`):** `8b45207`
   probada y funciona; sí a COBRO-MP-3, CSRF-1 (con D16 b),
   CATALOGO-LARGO-1 y SEGURO-2; fechas re-estimadas, el piloto cierra el
   07/02. Las claves las cambia ella más adelante.

10. **Para decidir (recomiendo sí): pieza CATALOGO-3** (MARIA). Las
   facturas chinas mezclan datos: todos los proveedores con nombre sólo en
   chino caen en un mismo catálogo, y «电线 2mm» pisa el NCM de «钢管 2mm».
   Viene de antes; no se pierde plata, pero se sugiere un NCM equivocado.
   Sumaría que, si un producto de la factura no se puede aprender, la
   pantalla diga cuál (hoy dice «algunos» y no queda ninguno).

## Quién hace qué

Desde el 2026-10-24 (Emi: Codex deja CDI; dos Devs nuevas en Claude).

| Rol | Sesión | Rutina | Rama | Esfuerzo |
|---|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn | — |
| Dev MARIA (Dev 2) | session_01C8gCBjvn36wnYC6qG2Sixi | trig_01WmrC3ALqBXkD9UBv6dFGbP (min 35) | claude/dev-maria | alto |
| Dev técnica (Dev 1) | session_018yxeKHYQKFA3qJ2WJmQru7 | trig_011UpBfwEu9TUzoNUrviqoP5 (min 15) | claude/dev-tecnica | medio |

Rutinas: cada 2 h de 8 a 22 y a las 2 y a las 5, hora de Argentina (`ONBOARDING-PM.md`, «Modo automático»).

Canales: Dev MARIA lee `PARA-DEV-2.md` y contesta en `PARA-PM-2.md`; Dev
técnica lee `PARA-DEV.md` y contesta en `PARA-PM.md`. **Sin PM visual:** la
PM principal revisa a las dos. Timbres por `send_message`, `priority` `next`.

Sesiones viejas, apagadas (historia): Dev 1 session_01VV5RVDA64AuzLaPBDnwH39
(trig_016zR6giZB8Mq9ZdfaerVh2D) y Dev 2 session_01JssJQ6CQvEBZ7yjJp3hHQx
(trig_019ehV8P48FzbNwYQGZjgYcW), con ramas `claude/dev1-tecnica` y
`claude/dev2-maria`; las ramas `codex/*`.

Archivos abiertos por Dev:
- Dev técnica (EXCEL-3f): las cargas por Excel (`main.py` y sus pantallas).
- Dev MARIA (ORG-1 y ORG-1b): invitaciones y registro en `proyecto_maria/main.py`,
  `database/models.py`, `templates/landing.html`. Las dos tocan `main.py` en zonas distintas.

## En curso

Ver «Última vuelta» y la línea `/compact conservar` de abajo.

## Puertas para cobrarle a un estudio

| Puerta | Estado | Qué falta | Se cierra en |
|---|---|---|---|
| G0 · Secretos | 🔴 | Rotar las claves de Gemini | Emi, esta semana |
| G1 · Configuración | 🟢 | G1.1 a G1.5 cortan. G1.6 y G1.7 sin medir | — |
| G2 · Imagen real | 🟢 | Cerrada el 2026-09-17 | — |
| G3 · Aislamiento | 🟡 | La fuga de MARIA.TXT, cerrada en producción con el ensayo (sin cuentas ajenas: nadie vio facturas de Emi). Admin cerrado en la rama (ADMIN-1 y ADMIN-2). Abiertos: sesiones que reviven, límite de intentos burlable, prueba de aislamiento parcial | Fase 3 |
| G4 · Producto (MARIA) | 🔴 | Origen mal leído, estado e IVA adicional fijos, peso por unidad, avisos tarde, gastos FOB sin cablear, banco, identificadores. Sin productos inventados (MARIA-2) | Fase 1 y la prueba en el Kit |
| G5 · Pruebas | 🟢 | `1526 passed, 102 skipped, 2 xfailed, 0 failed` y e2e OK en la rama integrada (`df4de22` = `0e57f70` sin documentos, 2026-10-07) | — |
| G6 · Volver atrás | 🟡 | Esquema probado en local; falta la copia de la base | Fase 3 (y el ensayo lo ensaya) |
| G7 · Cobro | 🔴 | El corte por impago cubre 2 funciones; cancelar no cancela en Mercado Pago; aviso de pago sin firma; doble suscripción; invitaciones | Fase 2 |
| G8 · Piloto | ⚪ | Tres estudios presentan de verdad un MARIA de CDI | Fase 4 |

## Publicado

Una línea por publicación: fecha, SHA y qué verificó Emi. Las anteriores al
2026-10-24 (`a771693`, `5cb03ab`, `6ea8ca9`, `a9b03cf`) están en la historia
de Git de este archivo y en sus `REPRODUCCION-*`.

- `dddcf6d` (2026-10-24 18:40 UTC): EXCEL-2, «dale dddcf6d». CI verde. Emi
  probó el Excel en el sitio y anda.
- `8b45207` (2026-10-24 20:33 UTC): EXCEL-3 + CLIENTE-1, «dale 8b45207».
  Avance directo de `dddcf6d`. Falta lo que verifica Emi.

## Reglas

Congeladas desde el 2026-10-06 hasta el **2026-10-27** (`DECISIONS.md`,
«Reglas en un solo lugar»), salvo que algo se rompa. Ese día la PM revisa con
`medir.py` y las mediciones si alguna regla molesta.

## Método

Al día con `CAMBIOS.md` del Second Brain (`Memu007/ynerasecondbrain`) hasta
**2026-10-31**, commit `7fd495f`.

## Sumar una Dev

Cuando haya dos colas que no toquen los mismos archivos (por ejemplo, cobro y
sesión por un lado; pantallas y archivo MARIA por el otro):

1. Medir antes con `medir.py`: una sesión más agrega traspasos.
2. Copiar del Second Brain `plantilla/docs/pm/PARA-DEV-2.md` y `PARA-PM-2.md`.
   Si hay mucha cola visual, también `ARRANQUE-PM-VISUAL.md`, `VISUAL.md` y
   `ENTRE-PMS.md`, con su PM visual.
3. En `medir.py`, agregar `"dev2": "<su rama>"` a `RAMAS`.
4. Abrir la sesión, crearle su rutina, anotar todo en «Quién hace qué» y
   pasarle los ids de la rutina de su PM.

## Última vuelta
2026-11-06 11:40 UTC: **COBRO-MP-2 vuelve con devolución** (`4f1822f`): una sola cuenta aguanta (55 passed, Postgres sin fallas, Opus y Sonnet sin cobro doble ni días perdidos). Vuelve por el estudio: reactivar sin permiso, checkout que cancela la pausada que paga, no se puede sacar a quien dejó una pendiente, «Próximo cobro» según quién mira, espera sin tope con MP caído. D62 (a).

2026-11-06 11:20 UTC: **COBRO-CORTE-1 aceptada** (`ca50916`, técnica, sin integrar por `e0b8626`): 98 passed, 88 sabotajes en rojo sin falla, suite `4284 passed` rc=0, chequeo-6 con sus 3 avisos explicados; Opus y Sonnet alto sin doble cobro. Cuatro bajas a la cola. Para Emi: la validación de 60 s cruza cargas (de antes), pieza nueva. Técnica entregó COBRO-MP-2 (`4f1822f`, D62): reviso con Opus y Sonnet alto.

2026-11-06 08:55 UTC: vuelta. Límite `allowed` en las tres; contexto 139k/121k/114k. Sin entregas nuevas ni D abiertas: MARIA sigue la devolución de CATALOGO-LARGO-2 (`04e0e70`, corriendo sabotajes), técnica corre los sabotajes de COBRO-CORTE-1 sobre `ca50916` (sin subir). CI verde sobre `d26c404`.

2026-11-06 07:10 UTC: **RESET-1 aceptada** (`02a21e7`, MARIA, sin integrar como `ca87d82`): 6 passed (4 rojos en la base), Postgres sin fallas (3 en la base), 8 sabotajes en rojo, suite con sólo las 5 de pypdf (D73), dos negativos míos y dos adversarios sin hallazgos. D82 (a), D83 (a). Nueva RESET-2: el link en la respuesta sólo en prueba. **La limpieza entró** en `dd052d4` (suite, csrf2 y cobro_mp1 verdes): se va la v1 y se cierra D60. Vuelta 05:55: límite `allowed` en las cuatro.

2026-11-06 05:00 UTC: **CATALOGO-LARGO-2 vuelve con devolución** (`ccfe640`, MARIA). TAIWAN y CHILE ya llegan bien al TXT. Pero en Postgres un NUL o medio par rompe el lote entero (500; en la base, 200 con lo bueno guardado; reproducido por mí). Una fila vieja queda duplicada y sin editar, y la migración puede trabarse con `guardar-uso`, con un log que miente. D76, D77, D78 y D80 van a Emi como CATALOGO-3. La limpieza (`07e7b5f`, mergeada a prueba en `27b19d9`) corre suite, csrf2 y cobro_mp1.

2026-11-06 03:40 UTC: **COBRO-CORTE-1 vuelve con devolución corta** (`8295bb5`). El servidor aguanta: 126 passed, 9 rojos en la base, Postgres sin fallas, Opus sin doble cobro. La causa 2 sigue en el catálogo: la carga A le enseña su NCM al proveedor de B, reproducido en Chromium. Además, B queda trabada con «Generar» apagado cuando vuelve A, y si `os.link` falla, regenerar da 500. El commit ambiguo y el posible deadlock van a la cola.

2026-11-06 03:28 UTC: **SESION-1 aceptada** (`2e62761`, MARIA): 42 passed (13 rojos en la base), 38 sabotajes en rojo, suite `4933 passed` con sólo las 5 de pypdf (D73), mi ejemplo del pool sin 500. Sin integrar, por lo mismo que `ca87d82` (ahora también CATALOGO-LARGO-2 debajo). D73 → PYPDF-1, D74 (a) a CONEXIONES-1, D75 (a) a la cola; pieza nueva RESET-1 (un link de reset viejo o usado sigue sirviendo; de antes). Técnica entregó COBRO-CORTE-1 en `8295bb5`: reproduciendo, con Opus y Sonnet alto.

2026-11-06 01:55 UTC: vuelta. Límite `allowed` en todas; contexto 135k/137k. MARIA sigue SESION-1 (`25a2718`), técnica esperando sus sabotajes de `555cd98` (33/67) antes de subir. Emi me pidió responderle a la sesión de limpieza: la superviso. Su LIMPIEZA-1 (`0a410ac`) choca con la de técnica que mi rama ya trae (`8747c4c`, `tests/test_limpieza1.py`); le pedí mergear mi rama en la suya y volver con suite. La v1 (`085ec1d`) entra después de aceptar SESION-1; D60 se cierra con eso.

2026-11-05 23:55 UTC: vuelta. Límite semanal `allowed` en las tres; contexto 120k/135k/137k de 200k. Técnica rehace COBRO-CORTE-1 (corre sabotajes sobre `fbea636`), MARIA rehace SESION-1; ninguna entrega nueva ni D abierta. Una sesión del chat suelto de Emi armó LIMPIEZA-1 y el retiro de la UI v1 en `ccr-39e9acae-e1hve5` (`085ec1d`); no integrado: espera que Emi me lo confirme a mí y que cierre SESION-1. Si se va la v1, D60 se cierra.

2026-11-05 23:30 UTC: **SESION-1 vuelve con devolución** (`c429307`, MARIA). Lo prometido aguanta: 29 passed, 29 sabotajes en rojo, mi negativo de once tokens ajenos da 401 y distingue. Dos causas reproducidas: un reset del dueño no gana contra un cambio de clave o de email ya validado (el atacante sale con token vigente), y el tope de la clave actual abre una segunda conexión: 40 pedidos a la vez dan `{400: 3, 500: 37}` y otro usuario espera 29 s (base: 0,6 s). D71 (b) pieza aparte. Suite `5 failed` también en la base: `pypdf 6.21.4` sin tope cambió el error de los PDF bomba; no es de la pieza, va en una D de MARIA.

2026-11-05 22:45 UTC: **DESPACHO-1d aceptada** (`528961b`, MARIA): 83 casos, 24 sabotajes sin falla, mi ejemplo de siete nombres de proveedor raros bien; D69 (a). Sin integrar, por lo mismo que `ca87d82`. El acta de COBRO-CORTE-1 suma sus 60 sabotajes, sin falla. MARIA entregó SESION-1 (`c429307`): la reviso.

2026-11-05 21:57 UTC, rutina: límite semanal `allowed` en las tres sesiones. Técnica rehace COBRO-CORTE-1; MARIA sigue con SESION-1; DESPACHO-1d (`528961b`) en reproducción, sin D abiertas fuera de D69.

2026-11-05 22:00 UTC: **COBRO-CORTE-1 vuelve otra vez** (`0b9ccde`): lo de la vuelta anterior está, pero se cobra antes de entregar (falla al escribir el TXT: 500 y el reintento cuenta otra, reproducido) y una respuesta tardía le pasa el id a la carga siguiente (Opus y Sonnet por separado). Más, a cero: NUL/surrogate en el id da 500, aviso de borrar cliente, candado en `delete_cliente`. CATALOGO-LARGO-2: sí de Emi (21:41).

2026-11-05 21:35 UTC: **RENDIMIENTO-1d aceptada** (`558c941`, MARIA): la salida del hijo ya no pierde texto (surrogate suelto o locale que no es UTF-8); tope de 64 K y fila por usuario con caso y sabotaje (12 ROJO). Mi ejemplo distinto, rojo en la base. Sin integrar, por lo mismo que `ca87d82`. Sigue DESPACHO-1d.

2026-11-05 20:45 UTC: **`ca87d82` aceptada** (RENDIMIENTO-1c v2, DESPACHO-1b v6, CATALOGO-LARGO-1 y DISCO-1): sabotajes 138/46/12 en rojo, suite con Postgres `4537 passed`. ✅ CATALOGO-LARGO-1 y DISCO-1. **Sin integrar:** debajo vienen commits de SESION-1, ABUSO-1, OBSERVABILIDAD-1, SUFIJOS-2 y ORG-1, con devolución abierta. DESPACHO-1c (`fbbb2ad`) espera lo mismo.

## /compact conservar de la PM principal

/compact conservar: 2026-11-04 21:43 UTC SE RETOMA por 3 días (Emi, 04/11 21:36): hasta el 2026-11-07 21:30 UTC; si el límite semanal llega al 50 % antes del 2026-11-06 21:30 UTC, cortar todo (rutinas apagadas, Devs frenadas, avisar). No veo el porcentaje exacto: mirar rate_limit_info seven_day de las tres sesiones (allowed_warning = cortar) y pedirle a Emi que avise. Semana desde 04/11 18:00 UTC. Método al día con el Second Brain hasta el 31/10 (7fd495f) en 58e1ce3: §6 de CLAUDE.md, chequeo-6.py en cada informe, COLA-LIMPIEZA, camino de hoy, sin medición. Soy la PM principal de CDI (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK, cada 2 h 8–22 más 2 y 5 ARG, min 55). Producto Memu007/CDI-vuce-, clon /home/user/cdi-vuce-, mi rama claude/practical-shannon-szpwkn (nunca main; cada push a main publica). main = 8b45207 (publicada 24/10; Emi la probó y funciona). Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP min 35, rama claude/dev-maria, alto; canal PARA-DEV-2/PARA-PM-2; nunca integrar su cabeza): ca87d82 (RENDIMIENTO-1c v2, DESPACHO-1b v6, CATALOGO-LARGO-1, DISCO-1) ACEPTADA 05/11 20:45 SIN INTEGRAR (debajo SESION-1, ABUSO-1, OBS-1, SUFIJOS-2, ORG-1 con devolución; integrar cuando esas se acepten). DESPACHO-1c aceptada sin integrar sobre fbbb2ad (05/11 19:05; se integra con ca87d82, repetir git log --no-merges) → RENDIMIENTO-1d ACEPTADA 05/11 21:35 sobre 558c941 SIN INTEGRAR (igual que ca87d82) → DESPACHO-1d ACEPTADA 05/11 22:45 sobre 528961b SIN INTEGRAR (D69 a, igual que ca87d82) → SESION-1 ACEPTADA 06/11 sobre 2e62761 SIN INTEGRAR (acta v3; al integrar, actualizar anclas de csrf3.sh; D71 b pieza chica aparte) → CATALOGO-LARGO-2 DEVOLUCIÓN 06/11 sobre ccfe640 (NUL en PG rompe el lote, fila vieja duplicada, deadlock y log de migración; D82 en adelante) → CATALOGO-3 (D76/D77/D78/D80, propuesta a Emi, recomendada; sin su sí no entra) → RESET-1 ACEPTADA 06/11 sobre 02a21e7 SIN INTEGRAR (D82 a, D83 a) → PYPDF-1 (D73) → RESET-2 (nueva PM 06/11: dev_token_hint sólo con ENVIRONMENT=test) → ABUSO-1 → SUFIJOS-2+SEGURO-1 → SEGURO-2 → EMAIL-1 (D45) → CONEXIONES-1 (D46) → OBSERVABILIDAD-1 → ORG-1+D40.  Dev técnica (session_018yxeKHYQKFA3qJ2WJmQru7, rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15, rama claude/dev-tecnica, canal PARA-DEV/PARA-PM): (COBRO-MP-1 y ORDEN-1b aceptadas e integradas hasta 885ee89, 05/11 12:55; pieza D51 propuesta a Emi: cancelar con organización actúa sobre la cuenta que da el acceso y sólo quien corresponda; si dice que sí, entra después de COBRO-MP-3) (CSRF-1 y CSRF-2 aceptadas e integradas hasta c44bf84, 05/11 15:15; D60: preguntado a Emi si alguien usa v1) (CSRF-3 aceptada e integrada, 9fe55d4, 05/11 19:20) → COBRO-CORTE-1 ACEPTADA 06/11 sobre ca50916 SIN INTEGRAR (acta v4; 4 bajas a la cola; validación de 60 s que cruza cargas = VALIDACION-1) → COBRO-MP-2 DEVOLUCIÓN 06/11 sobre 4f1822f (una regla de quién toca la que paga; billing_me desde la que paga; tope con MP caído; D62 a) → VALIDACION-1 (sí de Emi 06/11 12:06) → COBRO-MP-3 → AISLAMIENTO-2 y LIMPIEZA-1 → BACKUP-1a → EXCEL-2c (D32 b); desde e0b8626 la rama lleva COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a sin aceptar: nada se publica desde ahí hasta que sean ✅ (último SHA limpio 9018d77); antes de cada merge, `git log --no-merges HEAD..<sha>` contra el ✅ del roadmap, y si aparece algo 🔵, «aceptada sin integrar» con los SHAs; plata: Opus+Sonnet alto; próxima D técnica: D62 (pares); C10 es puerta de publicación con Emi. Revisión: /revisar-entrega, chequeo-6 contra el informe, adversarios por riesgo, hallazgos se reproducen; al aceptar REPRODUCCION y ✅ en el mismo commit. Herramientas: venv /tmp/cdi-pm/venv (Python 3.12: 3.13 no importa sqlalchemy 2.0.25); Postgres 16 descartable en 55462 rol cdi; sabotajes con until-loops en segundo plano, nunca sleep. Emi respondió el 04/11 (DECISIONS.md): 8b45207 probada; sí a COBRO-MP-3 (técnica, tras COBRO-MP-2), CSRF-1 (técnica, tras ORDEN-1b), CATALOGO-LARGO-1 (MARIA, tras RENDIMIENTO-1c) y SEGURO-2 (MARIA, tras SUFIJOS-2+SEGURO-1); fechas +2 semanas, piloto al 07/02. Para Emi: revocar la clave de Anthropic de scripts/utils/cambiar_ai.sh:62 (nunca copiar su valor) y rotar Gemini, «después». Los tres despachos reales sólo en el scratchpad; TXT y proforma reales nunca en el repo. Sesión de limpieza (session_01YFuo2AHFS3FyqmzjziYLFS, rama ccr-39e9acae-e1hve5): la superviso yo (Emi); 07e7b5f INTEGRADA en dd052d4 06/11 (suite, csrf2, cobro_mp1 verdes; cierra D60); choca con COBRO-CORTE-1 (toca app.js de v1). Adversarios: GEMINI_API_KEY vacía, sin red. Reglas de Emi: nada fuera del roadmap; Devs hasta alto, sin Fable; consejero sólo mío; castellano llano; publicar sólo con «dale <SHA>» de día; usar date -u.
