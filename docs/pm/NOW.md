# NOW — CDI

Actualizado: 2026-10-25. Estado vigente; la historia está en Git.

Método al día con CAMBIOS.md del secondbrain hasta 2026-10-21 (aplicado 2026-10-24).

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
9. **Para decidir de día (D16 de ORDEN-1b):** el servidor no pide el
   token CSRF al cerrar sesión. Lo peor que pasa es que alguien quede
   afuera y tenga que volver a entrar: no hay datos ni plata en juego.
   Recomiendo sumar una pieza chica al final de la cola de la técnica.

## Quién hace qué

Desde el 2026-10-24 (Emi: Codex deja CDI; dos Devs nuevas en Claude).

| Rol | Sesión | Rutina | Rama | Esfuerzo |
|---|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn | — |
| Dev MARIA (Dev 2) | session_01C8gCBjvn36wnYC6qG2Sixi | trig_01WmrC3ALqBXkD9UBv6dFGbP (cada 3 h, min 35) | claude/dev-maria | alto |
| Dev técnica (Dev 1) | session_018yxeKHYQKFA3qJ2WJmQru7 | trig_011UpBfwEu9TUzoNUrviqoP5 (cada 3 h, min 15) | claude/dev-tecnica | medio |

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
**2026-10-06 (noche)**, commit `faa8a3a`.

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

2026-10-29 09:56 UTC: Sin entregas nuevas. Técnica arrancó la h de COBRO vuelta 3 (rojos primero); MARIA va 67 de 132 sabotajes sobre `bb913d0`, sin fallas. Contexto 134k y 130k.

2026-10-29 09:45 UTC: **Las dos entregas de la técnica vuelven con devolución.** COBRO-MP-1 vuelta 2 (`4ef59f4`): aguantan los arreglos, pero un aviso de pago que no se puede atribuir queda «rechazado» para siempre y traba el aviso que lo acompaña (sale en parte de la regla b de la PM, ya corregida). ORDEN-1b (`6c459d2`): el producto aguanta; faltan sabotajes que pongan rojo cada condición del freno. Actas en `REPRODUCCION-COBRO-MP-1-vuelta2-2026-10-29.md` y `REPRODUCCION-ORDEN-1b-2026-10-29.md`. Técnica: COBRO vuelta 3 con D13 (c), después las pruebas de ORDEN-1b. Nada se integra. La vuelta de las 08:55 no tuvo novedades.

2026-10-29 08:30 UTC: La técnica entregó ORDEN-1b (`6c459d2`) y D14 (`4ef59f4`). Contestadas D15 (c) y D16 (a), con la pieza aparte propuesta a Emi; arranca D13 (c). Reviso ORDEN-1b y COBRO-MP-1 vuelta 2.

2026-10-29 07:56 UTC: Sin entregas nuevas. MARIA corre 132 sabotajes sobre `bb913d0`; técnica sigue con D14 y los sabotajes de ORDEN-1b, sin push todavía. Contexto bajo 125k.

2026-10-29 06:57 UTC: Sin entregas nuevas. MARIA cierra DESPACHO-1b vuelta 4 (sabotajes al día en `bb913d0`, corre la suite); técnica corre el arreglo de D14 y orden1b.sh. Contexto bajo 118k. Recortadas las vueltas sin novedad.

2026-10-29 06:40 UTC: La técnica entregó la vuelta 2 de COBRO-MP-1 (`999b27a`, informe `069b190`). D14 (a): arregla dos pruebas antes de ORDEN-1b. D13 (c), decidido por la PM: una suscripción vieja todavía activa en Mercado Pago da 409 con la salida a la vista. La reviso entera con el arreglo de D14.

2026-10-29 05:25 UTC: La técnica avisó que la vuelta 2 de COBRO-MP-1 ya tiene el código en `999b27a` y sus puertas corriendo. Decidido por la PM: entrega el informe, sin código nuevo, y sigue con ORDEN-1b en commits aparte. Se revisan en paralelo.

2026-10-29 03:31 UTC: ORDEN-1 vuelta 3 aceptada sobre `f7fbb72` (76 sabotajes rojos; dos adversarios sin altas). Integración diferida: la rama técnica intercala COBRO-MP-1 sin aceptar. La D12 resultó media (Generar desde la pestaña ajena cobra y guarda en la cuenta de B): ORDEN-1b encargada a la técnica, ya.

2026-10-29 01:41 UTC: **COBRO-MP-1 de la técnica vuelve con devolución sobre `784e793`.** Lo grave: dos pagos distintos de la misma cuenta a la vez se cobran los dos y se acredita uno; si Mercado Pago contesta con error al consultar un pago, el pago se pierde sin rastro; y volver al checkout antes del aviso cancela la suscripción recién cobrada (la PM afinó D7.2: con un cobro aprobado sin aplicar, 409 y no se cancela). También la prueba en Postgres del pago repetido estaba muerta. La cancelación en organizaciones (preexistente) va en COBRO-MP-2. Acta en `REPRODUCCION-COBRO-MP-1-2026-10-29.md`; técnica despertada (sigue ORDEN-1 vuelta 3 y después esta).

2026-10-29 01:06 UTC: **Revisadas las tres entregas que dejaron las Devs.** MARIA: DISCO-1 aceptada sobre `5c46e36`, sin integrar (está encima de DESPACHO-1b; se integra con la vuelta que se acepte, después de correr `disco1.sh` de nuevo); DESPACHO-1b devolución sobre `1f5480e` (la identidad del producto vale en una sola vía, guardados simultáneos duplican, el tope de CPU no cubre el parseo). Técnica: ORDEN-1 devolución sobre `86c9d84` (la recuperación escribe con el usuario de después de esperar el candado: la operación de A se pierde y B la ve). Actas en `REPRODUCCION-*-2026-10-29.md`; las dos Devs despertadas. A las 00:56 llegó COBRO-MP-1 de la técnica (`784e793`): D8–D10 decididas por la PM («Para Emi», 8); la revisión sigue: las puertas de la PM corren y Opus y Sonnet alto atacan; un negativo de la PM ya da rojo (dos pagos distintos de la misma cuenta a la vez: se registran los dos y se acredita uno).

2026-10-28 23:33 UTC: **Emi: el plan sigue en tres meses, sin apurar; la prioridad es calidad de senior y no saltear pasos («si se estira un poquito más, no hay problema»).** Anotado arriba de los dos canales de Dev («Ritmo y calidad») y en `DECISIONS.md`; avisado a las dos Devs. La técnica corre `/code-review high` y `/security-review` de COBRO-MP-1 antes de entregarla.

2026-10-28 23:18 UTC: **Pausa levantada (Emi: «volver a trabajar tranqui», su otra entrega pasó al martes).** Las tres rutinas prendidas de nuevo (PM min 55 cada hora; Devs cada 3 h, min 35 y 15). Sigue: revisar lo que las Devs dejaron y seguir las colas.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.

## /compact conservar de la PM principal

/compact conservar: 09:56 sin novedad. 09:45 UTC: COBRO-MP-1 vuelta 2 devolución sobre 4ef59f4 (h alta: aviso no atribuible queda rechazado para siempre y traba el par; arreglo de la regla b; i pruebas; j suma a D13 c) y ORDEN-1b devolución de pruebas sobre 6c459d2 (un sabotaje por condición del freno: cookie, sesionAjena, verbos no POST, salida del diálogo, limpieza de Comprobando). Actas REPRODUCCION-COBRO-MP-1-vuelta2 y REPRODUCCION-ORDEN-1b. Nada integrado. Técnica: COBRO vuelta 3 + D13 (c) ya, ORDEN-1b vuelta 2 apenas entregue; próxima D técnica D17. Para Emi de día: telemetría v2 403 por CSRF; línea de seguridad en el roadmap (lecturas síncronas a MP, límite de pedidos, IPN sin firma); D16 (b) CSRF en el logout. Antes, 01:41: COBRO-MP-1 devolución sobre 784e793 (commit 2e1a855; causas a–g en PARA-DEV.md: candado de cuenta en el webhook, regla 503/rechazado para lecturas de MP, D7.2 afinada con 409 si hay cobro aprobado sin aplicar, D31 Postgres muerta, mutantes vivos, recarga con tope, ids de B); cancelar en org va en COBRO-MP-2; técnica despertada. Worktrees /tmp/cdi-pm/* por borrar con git worktree remove. Antes: DISCO-1 aceptada sin integrar (5c46e36; integrar con la próxima DESPACHO-1b aceptada, tras correr disco1.sh con PG_URL y rol cdi); DESPACHO-1b devolución sobre 1f5480e; Emi 28/10: sin apurar, calidad de senior, no saltear pasos; el plan se puede estirar (re-estimar fechas después de la primera sesión con el despachante). Soy la PM principal de CDI (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK min 55). Producto Memu007/CDI-vuce-, clon /home/user/cdi-vuce-, mi rama claude/practical-shannon-szpwkn (nunca main; cada push a main publica). main = 8b45207 (publicada 24/10; falta que Emi la pruebe). Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi, rutina cada 3 h min 35, rama claude/dev-maria, alto; canal PARA-DEV-2/PARA-PM-2; su cabeza lleva RENDIMIENTO-1c a medias: nunca integrar su cabeza). Orden de MARIA: DESPACHO-1b vuelta 4 → RENDIMIENTO-1c (D48 (a)) → SESION-1 → ABUSO-1 → SUFIJOS-2+SEGURO-1 → EMAIL-1 (D45) → CONEXIONES-1 (D46) → OBSERVABILIDAD-1 → ORG-1+D40. Aceptadas de MARIA: ORG-1 ✅, DESTINO-1 ✅, SEGURO-1, DATOS-1, EMAIL-1, DISCO-1 (sin integrar las de encima de lo no aceptado). Próxima D de MARIA: D49. Dev técnica (session_018yxeKHYQKFA3qJ2WJmQru7, rutina cada 3 h min 15, rama claude/dev-tecnica, canal PARA-DEV/PARA-PM): EXCEL-3 ✅, GUARDAR-2 integradas; EXCEL-2b ✅ aceptada sin integrar (03336f1, be260b7); orden: COBRO-MP-1 vuelta 3 + D13 c → ORDEN-1b vuelta 2 → COBRO-CORTE-1 → COBRO-MP-2 → AISLAMIENTO-2 y LIMPIEZA-1 → BACKUP-1a → EXCEL-2c (D32 b); plata: Opus+Sonnet alto; próxima D técnica: D17. Revisión: adversarios por riesgo, hallazgos se reproducen; al aceptar REPRODUCCION y ✅ en el mismo commit. Herramientas: venv /tmp/cdi-pm/venv; Postgres 16 descartable en 55462 rol cdi; sabotajes con until-loops en segundo plano, nunca sleep. Para Emi (12 a 00 UTC): pieza de seguridad; propuesta de pieza por la pérdida muda de memoria del cliente y catálogo (product_key String(300)); SEGURO-2; probar 8b45207; revocar la clave de Anthropic de scripts/utils/cambiar_ai.sh:62 (nunca copiar su valor) y rotar Gemini; re-estimar fechas. Los tres despachos reales sólo en el scratchpad; TXT y proforma reales nunca en el repo. Reglas de Emi: nada fuera del roadmap; Devs hasta alto, sin Fable; consejero sólo mío; castellano llano; publicar sólo con «dale <SHA>» de día; usar date -u.
