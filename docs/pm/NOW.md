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
   **Sí de Emi el 09/11: MARIA la hace.**

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
2026-11-09 21:57 UTC: vuelta sin entregas. Técnica en INTEGRAR-1 vuelta 2: validacion1 rojo por 429 al registrar, lo verifica sobre los padres. MARIA en CATALOGO-3 (D156/D157 en f625159), escribe la prueba roja; próxima D158.
2026-11-09 20:53 UTC: D157 (a) y D156 (a) a MARIA: varchar(3)→text no reescribe (PG 16.15, mismo filenode), sólo el lock. D102 ya estaba aceptada.
2026-11-09 20:45 UTC: merge b9db0ad revisado a mano. Los trozos de main.py, finalize.js, clientes.js y file_security.py están bien. El 409 que se sacó de finalize.js lo había sacado antes efaef2b6. D155 corregida: la prueba va sobre la familia; NL 423 o 434 lo decide Emi.
2026-11-09 20:12 UTC: Emi: sí a CATALOGO-3 (MARIA, rutina prendida), D141 (a) = PRESUPUESTO-CLIENTE-1, D143 (a) = BORRADOR-1; «fusioná» = publicar (tras INTEGRAR-1).
2026-11-09 20:05 UTC: **Emi retoma sin límite.** Técnica → INTEGRAR-1 vuelta 2 (D140, lo no corrido, suite). MARIA sin pieza, rutina apagada. A Emi: CATALOGO-3, D141, D143, «fusioná», clave de Anthropic.
2026-11-09 05:01 UTC: **CORTE de las 12 h.** Las tres rutinas, apagadas; las dos Devs avisadas (terminan el paso, push, anotan y frenan). Técnica en `28c4dd5`, MARIA en `cddf7de`. Para retomar: revisar INTEGRAR-1 y prender las rutinas.
2026-11-09 04:28 UTC: **INTEGRAR-1 entregada** (`19036a2`, técnica): suite 1 rojo (D140), 56 sabotajes sin correr. Recibida, sin aceptar: la reviso después del corte. D140 (a) lo hace ella; D141 (a) y D143 (a), piezas para Emi.
2026-11-09 02:45 UTC: **D102 aceptada** (`af924ea`, sin integrar): 5 passed con bcrypt 5 y rojo con 4.3.0. D153 (a) a la cola, D154 (a). MARIA sin pieza disponible: anota y frena hasta el corte.
2026-11-09 02:20 UTC: **D139 aceptada** (`3fde8bb`, sin integrar): prueba en Chromium 0 fallas y 4 en la base, 6 ROJO. D152 (a) no. MARIA → D102 (bcrypt).
2026-11-09 02:10 UTC: **ORG-1+D40 aceptada** (`bf9583b`, sin integrar): 35 ROJO falla 0 con PG, mi negativo rojo en la base. D151 (a). Sonnet: invitación de Y trabada si X cambia el email del perfil (a Emi, con R3). MARIA → D139.
2026-11-09 00:20 UTC: **OBSERVABILIDAD-1 aceptada** (`279ef26`, sin integrar): entradas3 con PG falla 0 y 12 ROJO, mi negativo verde, el arnés viejo rojo. D150 (b) a la cola de limpieza. MARIA → ORG-1+D40. Técnica en INTEGRAR-1 (`99855b4`).
2026-11-08 23:35 UTC: **Emi: uso al 87 %, se puede llegar al 95 % y frenar.** La PM no ve el medidor: frena cuando Emi avise 95 % o a las 05:00, lo que llegue primero, con el procedimiento de corte. Mientras, sin adversarios Opus nuevos. OBSERVABILIDAD-1 con devolución (`3d7f296`); D142 a Emi.












## /compact conservar de la PM principal

/compact conservar: 2026-11-09 21:57 UTC: D156 (a) y D157 (a) a MARIA (f625159), próxima D158; técnica en INTEGRAR-1 vuelta 2 (validacion1 429 en verificación; al revisar, git diff 2e775aa4 c9e9a69c -- proyecto_maria/); NL 423/434 espera a Emi (queda 434). 2026-11-09 19:59 UTC Emi: «Continua trabajando sin límite»: sin hora de corte, Opus permitido; un rechazo real por límite corta. Las tres rutinas prendidas. Técnica en INTEGRAR-1 vuelta 2 → BORRADOR-1 → CONEXIONES-1 B. MARIA en CATALOGO-3 → PRESUPUESTO-CLIENTE-1 (sí de Emi). «Fusioná» = publicar: SHA a Emi tras aceptar INTEGRAR-1. Antes de publicar: D64, FRONTEND_URL, ALLOWED_ORIGINS y ADMIN_USERNAMES en Railway, código NL confirmado por Emi (si es 423, las filas ya guardadas con 434 quedan así), migración de operation_items.origen (D156; las filas recortadas a 3 no se recuperan). NOMBRES-1 ACEPTADA 18:40 sobre 1960a9a (integrada); AVISOS-2 ACEPTADA 19:35 sobre 4db641b SIN INTEGRAR; AVISOS-2b ACEPTADA 20:58 sobre aa115f4; RESET-3 ACEPTADA 21:40 sobre 8fda3d2 (D138 a); SMOKE-1 ACEPTADA 21:55 sobre 00df4de; MARIA en OBSERVABILIDAD-1 (próxima D139), no trae mi rama hasta INTEGRAR-1; técnica en INTEGRAR-1 (D136: mi rama + dev-maria 4db641b, choques de fondo como D) y después CONEXIONES-1 (pasó de MARIA; D134 c; próxima D técnica D140); índice lower(username) va con Emi. EMAIL-1 de MARIA aceptada (40423be); MARIA en AVISOS-2, después RESET-3 (D132); D131 (collation de producción) espera a Emi. Antes: 2026-11-07 15:50 UTC RETOMADO por 24 h (Emi, ya pasado el 50 %; allowed_warning no corta): corte 2026-11-08 15:50 UTC por trig_01QwEeyuXBFBx6LErxqapwRh (apagar las tres rutinas, Devs terminan el paso en curso con commit y push y anotan dónde quedaron, avisar a Emi). Un rechazo por límite también corta. Método al día con el Second Brain hasta el 31/10 (7fd495f) en 58e1ce3: §6 de CLAUDE.md, chequeo-6.py en cada informe, COLA-LIMPIEZA, camino de hoy, sin medición. Soy la PM principal de CDI (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK, cada 2 h 8–22 más 2 y 5 ARG, min 55). Producto Memu007/CDI-vuce-, clon /home/user/cdi-vuce-, mi rama claude/practical-shannon-szpwkn (nunca main; cada push a main publica). main = 8b45207 (publicada 24/10; Emi la probó y funciona). Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP min 35, rama claude/dev-maria, alto; canal PARA-DEV-2/PARA-PM-2; nunca integrar su cabeza): ca87d82 (RENDIMIENTO-1c v2, DESPACHO-1b v6, CATALOGO-LARGO-1, DISCO-1) ACEPTADA 05/11 20:45 SIN INTEGRAR (debajo SESION-1, ABUSO-1, OBS-1, SUFIJOS-2, ORG-1 con devolución; integrar cuando esas se acepten). DESPACHO-1c aceptada sin integrar sobre fbbb2ad (05/11 19:05; se integra con ca87d82, repetir git log --no-merges) → RENDIMIENTO-1d ACEPTADA 05/11 21:35 sobre 558c941 SIN INTEGRAR (igual que ca87d82) → DESPACHO-1d ACEPTADA 05/11 22:45 sobre 528961b SIN INTEGRAR (D69 a, igual que ca87d82) → SESION-1 ACEPTADA 06/11 sobre 2e62761 SIN INTEGRAR (acta v3; al integrar, actualizar anclas de csrf3.sh; D71 b pieza chica aparte) → CATALOGO-LARGO-2 ACEPTADA 06/11 sobre d5bc7c1 (pruebas b0bbd8c) SIN INTEGRAR (D84-D87 a) → CATALOGO-3 (D76/D77/D78/D80, propuesta a Emi, recomendada; sin su sí no entra) → RESET-1 ACEPTADA 06/11 sobre 02a21e7 SIN INTEGRAR (D82 a, D83 a) → PYPDF-1 ACEPTADA 06/11 sobre 974263e SIN INTEGRAR (D89 a, D90 a) → ABUSO-1 ACEPTADA 07/11 sobre 55bf408 SIN INTEGRAR (D94-96 a) → ENTORNO-1 ACEPTADA 07/11 sobre 83085e4 SIN INTEGRAR (D97/D98 a; D99 usuarios demo a Emi; próxima D de MARIA D100) → ENTRADAS-1 ACEPTADA 07/11 sobre c839197 SIN INTEGRAR (D100-D104 a) → ABUSO-2 ACEPTADA 07/11 sobre 1f79a8e (producto 8ad47ee) SIN INTEGRAR; ENTORNO-2 ACEPTADA 08/11 sobre bf92bf9 SIN INTEGRAR (D107 a: ENTORNO-3 tras ENTRADAS-2; FRONT-422 ACEPTADA 08/11 sobre 4dbdb0b SIN INTEGRAR (D108 a); ENTRADAS-2 ACEPTADA 08/11 sobre b8aa9bd SIN INTEGRAR (D109/D110 a: ENTRADAS-3 tras ENTORNO-3); ENTORNO-3 ACEPTADA 08/11 sobre fd545c1 SIN INTEGRAR (D111 a, D112 c+D113 b: ENTORNO-4 tras ENTRADAS-3); MARIA sigue ENTRADAS-3; próxima D115; la D112 técnica es D114) (D105 a; riesgo: delete por prefijo sin prueba) → rojo de despacho1b ACEPTADO 07/11 sobre d69233c SIN INTEGRAR (D106 a; próxima D107) → ENTORNO-2 (D98) → FRONT-422 (D100) → ENTRADAS-2 (D104+D101) → SUFIJOS-2+SEGURO-1 → SEGURO-2 → EMAIL-1 (D45) → CONEXIONES-1 (D46) → OBSERVABILIDAD-1 → ORG-1+D40.  Dev técnica (session_018yxeKHYQKFA3qJ2WJmQru7, rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15, rama claude/dev-tecnica, canal PARA-DEV/PARA-PM): (COBRO-MP-1 y ORDEN-1b aceptadas e integradas hasta 885ee89, 05/11 12:55; pieza D51 propuesta a Emi: cancelar con organización actúa sobre la cuenta que da el acceso y sólo quien corresponda; si dice que sí, entra después de COBRO-MP-3) (CSRF-1 y CSRF-2 aceptadas e integradas hasta c44bf84, 05/11 15:15; D60: preguntado a Emi si alguien usa v1) (CSRF-3 aceptada e integrada, 9fe55d4, 05/11 19:20) → COBRO-CORTE-1 ACEPTADA 06/11 sobre ca50916 SIN INTEGRAR (acta v4; 4 bajas a la cola; validación de 60 s que cruza cargas = VALIDACION-1) → COBRO-MP-2+3 vuelta 3 + PERMISOS-1 + BACKUP-1a ACEPTADAS 08/11 sobre ca84c5f SIN INTEGRAR (antes: devolución sobre 71e15df (quien abrió queda trabada tras 503 de cancelar; firma por posición y dos v1, textos 503, plazo con varias, reactivar con sid que no paga; D114 = reintento concilia dentro de la pieza; próxima D libre D118 (una sola secuencia); ENTRADAS-3 ACEPTADA 08/11 sobre cf5309a SIN INTEGRAR, D115 a, D117 a = ENTRADAS-4 tras ENTORNO-4; ENTORNO-4 ACEPTADA 08/11 sobre 44b9759 SIN INTEGRAR (publicar pide FRONTEND_URL en Railway); ENTRADAS-4 ACEPTADA 08/11 sobre 6baddb5 SIN INTEGRAR; EXCEL-2c ACEPTADA 08/11 sobre c2b84f1 SIN INTEGRAR, D122 a = EXCEL-2d tras el informe de COBRO; EXCEL-2d ACEPTADA 08/11 sobre 84fd9f2 SIN INTEGRAR, D124 a = CI instala xlwt en la entrega de COBRO-MP-4; D119 b = COBRO-MP-4, D120 b = PERMISOS-2 después; próxima D libre D127; COBRO-MP-4 ACEPTADA 08/11 sobre 0fb991c SIN INTEGRAR; PERMISOS-2 ACEPTADA 08/11 sobre a1db966 SIN INTEGRAR; PERMISOS-3 ACEPTADA 08/11 sobre 9428e00 SIN INTEGRAR (D127 b, a Emi) → SEPARADORES-1b-ARNÉS ACEPTADA 08/11 sobre 1063b32 SIN INTEGRAR; próxima D técnica D128; SUFIJOS-2+SEGURO-1 ACEPTADA 08/11 sobre ad2d0f8 SIN INTEGRAR, D123 a = AVISOS-1 tras SEGURO-2; SEGURO-2 ACEPTADA 08/11 sobre d160738 SIN INTEGRAR (D125 a, D126 a); AVISOS-1 ACEPTADA 08/11 sobre 0aed334 SIN INTEGRAR (D129 a, D130 a = AVISOS-2 tras EMAIL-1; próxima D de MARIA D131); MARIA en EMAIL-1 (dc2943d); AISLAMIENTO-2+LIMPIEZA-1 ACEPTADAS 08/11 sobre c86f3ff SIN INTEGRAR; D116 b = PERMISOS-1 tras la devolución; D64 a la hace Emi antes de publicar, D66 a) → VALIDACION-1 ACEPTADA 07/11 sobre c24a266 SIN INTEGRAR (riesgos: !force y 60 s sin prueba; historial 0 con validador caído = pieza aparte a proponer) → AISLAMIENTO-2 y LIMPIEZA-1 → BACKUP-1a → EXCEL-2c (D32 b); desde e0b8626 la rama lleva COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a sin aceptar: nada se publica desde ahí hasta que sean ✅ (último SHA limpio 9018d77); antes de cada merge, `git log --no-merges HEAD..<sha>` contra el ✅ del roadmap, y si aparece algo 🔵, «aceptada sin integrar» con los SHAs; plata: Opus+Sonnet alto; próxima D técnica: D62 (pares); C10 es puerta de publicación con Emi. Revisión: /revisar-entrega, chequeo-6 contra el informe, adversarios por riesgo, hallazgos se reproducen; al aceptar REPRODUCCION y ✅ en el mismo commit. Herramientas: venv /tmp/cdi-pm/venv (Python 3.12: 3.13 no importa sqlalchemy 2.0.25); Postgres 16 descartable en 55462 rol cdi; sabotajes con until-loops en segundo plano, nunca sleep. Emi respondió el 04/11 (DECISIONS.md): 8b45207 probada; sí a COBRO-MP-3 (técnica, tras COBRO-MP-2), CSRF-1 (técnica, tras ORDEN-1b), CATALOGO-LARGO-1 (MARIA, tras RENDIMIENTO-1c) y SEGURO-2 (MARIA, tras SUFIJOS-2+SEGURO-1); fechas +2 semanas, piloto al 07/02. Para Emi: revocar la clave de Anthropic de scripts/utils/cambiar_ai.sh:62 (nunca copiar su valor) y rotar Gemini, «después». Los tres despachos reales sólo en el scratchpad; TXT y proforma reales nunca en el repo. Sesión de limpieza (session_01YFuo2AHFS3FyqmzjziYLFS, rama ccr-39e9acae-e1hve5): la superviso yo (Emi); 07e7b5f INTEGRADA en dd052d4 06/11 (suite, csrf2, cobro_mp1 verdes; cierra D60); choca con COBRO-CORTE-1 (toca app.js de v1). Emi 06/11: sigue ordenando el repo en tandas chicas (codex/* sin commits sueltos, docs viejos a archive, muertos), sin tocar archivos de las Devs ni comportamiento; me avisa cada tanda y la integro yo. Tandas 1 a 3 integradas 06/11 (hasta `c98213f`); lo que queda espera a las Devs. Adversarios: GEMINI_API_KEY vacía, sin red. Reglas de Emi: nada fuera del roadmap; Devs hasta alto, sin Fable; consejero sólo mío y seguido (regla 09/11); castellano llano; publicar sólo con «dale <SHA>» de día; usar date -u.
