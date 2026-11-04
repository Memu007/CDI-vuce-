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

2026-11-04 22:20 UTC: **Emi respondió lo pendiente.** `8b45207` probada y funciona. Entran al roadmap COBRO-MP-3 (seguridad del cobro) y CSRF-1 para la técnica, CATALOGO-LARGO-1 y SEGURO-2 para MARIA, en las colas de sus canales. Fechas re-estimadas: dos semanas más, piloto hasta el 07/02. Claves: las cambia Emi más adelante.

2026-11-04 21:56 UTC: Sin entregas. MARIA corre los sabotajes sobre `bb913d0` (~3 h; borrador con chequeo-6 en `b3e945c`); técnica rehace lo de §6 en el webhook de COBRO-MP-1. Uso semanal «allowed» en las tres; contexto 139k, 114k, 115k.

2026-11-04 21:43 UTC: **Se retoma por 3 días, hasta el 07/11 21:30 UTC (Emi); se corta antes si el uso semanal llega al 50 % en dos días o menos.** Método al día con el Second Brain hasta el 31/10 (`58e1ce3`: CLAUDE.md §6, `chequeo-6.py`, COLA-LIMPIEZA, sin medición a mano). Las tres rutinas, prendidas cada 2 h en horario de Argentina (PM min 55, técnica 15, MARIA 35). Las dos Devs despertadas: MARIA repite los sabotajes de DESPACHO-1b vuelta 4 sobre `bb913d0` y entrega; técnica sigue COBRO-MP-1 vuelta 3 + D13 (c). Las dos entregan con la salida de `chequeo-6.py`.

2026-10-29 10:37 UTC: Pausa hasta el domingo 1/11 (Emi): rutinas apagadas, Devs frenadas con lo suyo subido a medias.

2026-10-29 09:45 UTC: Las dos entregas de la técnica volvieron con devolución: COBRO-MP-1 vuelta 2 (`4ef59f4`, un aviso no atribuible queda rechazado para siempre) y ORDEN-1b (`6c459d2`, faltan sabotajes por condición del freno). Actas `REPRODUCCION-COBRO-MP-1-vuelta2-2026-10-29.md` y `REPRODUCCION-ORDEN-1b-2026-10-29.md`. Nada integrado.

## /compact conservar de la PM principal

/compact conservar: 2026-11-04 21:43 UTC SE RETOMA por 3 días (Emi, 04/11 21:36): hasta el 2026-11-07 21:30 UTC; si el límite semanal llega al 50 % antes del 2026-11-06 21:30 UTC, cortar todo (rutinas apagadas, Devs frenadas, avisar). No veo el porcentaje exacto: mirar rate_limit_info seven_day de las tres sesiones (allowed_warning = cortar) y pedirle a Emi que avise. Semana desde 04/11 18:00 UTC. Método al día con el Second Brain hasta el 31/10 (7fd495f) en 58e1ce3: §6 de CLAUDE.md, chequeo-6.py en cada informe, COLA-LIMPIEZA, camino de hoy, sin medición. Soy la PM principal de CDI (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK, cada 2 h 8–22 más 2 y 5 ARG, min 55). Producto Memu007/CDI-vuce-, clon /home/user/cdi-vuce-, mi rama claude/practical-shannon-szpwkn (nunca main; cada push a main publica). main = 8b45207 (publicada 24/10; falta que Emi la pruebe). Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP min 35, rama claude/dev-maria, alto; canal PARA-DEV-2/PARA-PM-2; nunca integrar su cabeza): repite los sabotajes de DESPACHO-1b vuelta 4 sobre bb913d0 (iba 95/132, ninguno falló; borrador BORRADOR-INFORME-DESPACHO-1b-vuelta4-DEV2.md) y entrega; después RENDIMIENTO-1c (D48 a) → SESION-1 → ABUSO-1 → SUFIJOS-2+SEGURO-1 → EMAIL-1 (D45) → CONEXIONES-1 (D46) → OBSERVABILIDAD-1 → ORG-1+D40. DISCO-1 aceptada sin integrar (5c46e36; integrar con la DESPACHO-1b aceptada, tras correr disco1.sh con PG_URL y rol cdi). Próxima D de MARIA: D49. Dev técnica (session_018yxeKHYQKFA3qJ2WJmQru7, rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15, rama claude/dev-tecnica, canal PARA-DEV/PARA-PM): COBRO-MP-1 vuelta 3 + D13 (c) → ORDEN-1b vuelta 2 → COBRO-CORTE-1 → COBRO-MP-2 → AISLAMIENTO-2 y LIMPIEZA-1 → BACKUP-1a → EXCEL-2c (D32 b); EXCEL-2b aceptada sin integrar (03336f1, be260b7); plata: Opus+Sonnet alto; próxima D técnica: D17. Revisión: /revisar-entrega, chequeo-6 contra el informe, adversarios por riesgo, hallazgos se reproducen; al aceptar REPRODUCCION y ✅ en el mismo commit. Herramientas: venv /tmp/cdi-pm/venv; Postgres 16 descartable en 55462 rol cdi; sabotajes con until-loops en segundo plano, nunca sleep. Emi respondió el 04/11 (DECISIONS.md): 8b45207 probada; sí a COBRO-MP-3 (técnica, tras COBRO-MP-2), CSRF-1 (técnica, tras ORDEN-1b v2), CATALOGO-LARGO-1 (MARIA, tras RENDIMIENTO-1c) y SEGURO-2 (MARIA, tras SUFIJOS-2+SEGURO-1); fechas +2 semanas, piloto al 07/02. Para Emi: revocar la clave de Anthropic de scripts/utils/cambiar_ai.sh:62 (nunca copiar su valor) y rotar Gemini, «después». Los tres despachos reales sólo en el scratchpad; TXT y proforma reales nunca en el repo. Reglas de Emi: nada fuera del roadmap; Devs hasta alto, sin Fable; consejero sólo mío; castellano llano; publicar sólo con «dale <SHA>» de día; usar date -u.
