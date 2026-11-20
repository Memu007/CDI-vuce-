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
   **Anthropic: revocada** (Emi me lo confirmó, 2026-11-12 01:20 UTC). Falta
   Gemini. El texto sale de `main` al publicar; repo público: decide Emi.
3. **Despachante:** recordarle los archivos reales (favor 1). Ya respondió
   todas las preguntas.
4. **Catálogo NCM:** Emi trajo el nomenclador vigente (2026-10-07). Lo
   carga la Dev 2 en CATALOGO-NCM-1. Una línea de Emi: ¿lo bajó de
   `arca.gob.ar`?
5. **Hasta publicar MARIA-1a: revisar el país de origen de cada TXT** antes
   de mandárselo al despachante. El código publicado corta el país a dos
   letras: si la lectura devuelve «CHN» o «China», sale Suiza.
7. **No pedirle a ningún asistente cambios sobre `main`:** desde el
   2026-10-07 `main` tiene las reglas nuevas, pero cada push publica.
10. **Pieza CATALOGO-3 aceptada el 10/11, sin publicar.** Las facturas
   chinas ya no mezclan catálogos ni se pisan entre sí.
   **Sí de Emi a CATALOGO-4 (19/11, «sí a las dos y al país con nombre»; no es un «dale»).**
   Aceptada el 19/11 (`f5395b9f`), sin publicar: ante dos productos del catálogo de un proveedor igual
   de parecidos, gana el último confirmado, no el orden de la base.
11. **CATALOGO-PAIS y ORIGEN-2 aceptadas e integradas (20/11), sin publicar.** Los catálogos muestran
   «423 · PAISES BAJOS» y el origen habitual del cliente acepta nombre o código (la columna pasa de
   `varchar(3)` a `text`). **Antes de publicar ORIGEN-2: copia de la base, y publicar sin uso** (el
   arranque espera 5 s si alguien tiene `clients` tomada). Opcional antes de publicar: la consulta de
   sólo lectura de D277 (`REPRODUCCION-ORIGEN-2-2026-11-20.md`). La calculadora y la moneda recortan
   a 3 pero se eligen de una lista cerrada: sin camino de hoy, quedan como riesgo escrito.
12. **Pieza PRESUPUESTO-CLIENTE-1 aceptada el 11/11, sin publicar.** Pasar
   una operación a otro cliente ya corta el link de presupuesto que tenía.
   **Para decidir al publicar (recomiendo dejarlo así):** los links
   compartidos antes de publicar, de operaciones que después cambiaron de
   cliente, siguen abiertos. Si sabés de un caso, avisá y se arma una pieza
   chica para cortarlos.
13. **Sí de Emi a los puntos 19 a 21 (20/11, leído 13:53 UTC: «Dale a todo»; no es un «dale» de publicar).**
   MARIA hace CATALOGO-PAIS-2 (D275 b: el nombre entero del país al pasar el mouse, en los catálogos).
   La Técnica hace CONEXIONES-1-NOKEY (D206 a, el arreglo chico) y después CONEXIONES-1-PRODUCTO
   (D182, D183 y D188). Lo medido, en `REPRODUCCION-CONEXIONES-1-2026-11-12.md`. Pregunta abierta a
   Emi: ¿hubo reclamos de recargas no acreditadas?
   - **D205, plata, ya en producción, sigue con Emi:** si la renovación llega justo cuando la cuenta
     vencía, queda bloqueada con el pago hecho hasta la próxima renovación. Recomiendo arreglarlo
     (cambio chico) como pieza propia apenas después de CONEXIONES-1-NOKEY, para no esperar a la grande. Punto 22, preguntado 20/11 14:00 UTC.
14. **CI-TOPE aceptada e integrada (`c721f7fc`, 17/11 00:50 UTC):** la CI corta la suite a los 30 min
   en vez de 20 (sí de Emi 17/11 00:41). Entra a `main` con la próxima publicación y su «dale».
15. **PAIS-NL y CUIT-GENERAR, publicadas en `fc5944fc` (15/11).** En producción
   hoy: un grupo que mezcla «NL» con «Holanda» o «434» no genera hasta
   corregirlo, y un CUIT mal guardado no genera el TXT.
   - Holanda→423 aceptada e integrada (`b3a3bf69`, 17/11 01:05 UTC): la pantalla
     muestra 423 donde sale 423. Sin publicar.
   - D239 (a) aceptada e integrada (`01c28e83`, 17/11 08:53 UTC), sin publicar: el lector de
     despachos ya no pone el país del código cuando el nombre dice otro.
   - D263 aceptada e integrada (`9e5960d2`, 17/11 11:50 UTC), sin publicar: la validación y el TXT
     leen el mismo campo de origen.
   - D269 integrada (merge `9ec581db`, 17/11 17:45 UTC) y aceptada (veredicto 17:47), sin publicar: los avisos no toman como
     China un origen que falta o no se reconoce. DESPACHO1B-CARGA y DESPACHO1B-CARGA-2 (sólo pruebas)
     aceptadas e integradas; MARIA sigue con el punto 16.
16. **Sí de Emi a los puntos 16 a 18 (18/11 20:27 UTC, «sí a los tres»; no es un «dale»).**
   MARIA hace PAISES-NOMBRES (D266: nombres de país en inglés y castellano, con puntos o letra
   ancha) y después ORIGEN-ETIQUETA (D261: el origen se ve «310 · CHINA» en las métricas y la
   revisión). Lo que ya dice 434 sigue saliendo 423 (punto 17). Las dos, aceptadas e integradas
   (`fa89e917` y `5a28c13c`, 18/11), sin publicar.

## Quién hace qué

Desde el 2026-10-24 (Emi: Codex deja CDI; dos Devs nuevas en Claude).

| Rol | Sesión | Rutina | Rama | Esfuerzo |
|---|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn | — |
| Dev MARIA (Dev 2) | session_01YFuo2B43UZtRiDadG17zU5 (nueva 15/11; vieja _01C8gC… apagada) | trig_01Ukttby1fc4sGVQfSn1jC9U (min 35, prendida 20/11 13:57: CATALOGO-PAIS-2; la vieja trig_01WmrC… apagada) | claude/dev-maria | alto; Opus alto desde 03:06 15/11 (no lo cambié yo), /autocompact 300k |
| Dev técnica (Dev 1) | session_018yxeKHYQKFA3qJ2WJmQru7 | trig_011UpBfwEu9TUzoNUrviqoP5 (min 15, prendida 20/11 13:57: CONEXIONES-1-NOKEY) | claude/dev-tecnica | medio |

Rutinas: cada 2 h de 8 a 22 y a las 2 y a las 5, hora de Argentina (`ONBOARDING-PM.md`, «Modo automático»).

Canales: Dev MARIA lee `PARA-DEV-2.md` y contesta en `PARA-PM-2.md`; Dev
técnica lee `PARA-DEV.md` y contesta en `PARA-PM.md`. **Sin PM visual:** la
PM principal revisa a las dos. Timbres por `send_message`, `priority` `next`.

Sesiones viejas, apagadas (historia): Dev 1 session_01VV5RVDA64AuzLaPBDnwH39
(trig_016zR6giZB8Mq9ZdfaerVh2D) y Dev 2 session_01JssJQ6CQvEBZ7yjJp3hHQx
(trig_019ehV8P48FzbNwYQGZjgYcW), con ramas `claude/dev1-tecnica` y
`claude/dev2-maria`; las ramas `codex/*`.

Archivos abiertos por Dev:
- Dev técnica (espera a Emi): `tests/conftest.py` y los ayudantes de `tests/`. Sin producto hasta el sí de Emi (D182 o D206).
- Dev MARIA: lo de su lista en `PARA-DEV-2.md`, y `pantalla_orden1.js` desde 2026-11-13 05:35 UTC.

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

Una línea por publicación: fecha, SHA y qué verificó Emi. Las anteriores
(`a771693`, `5cb03ab`, `6ea8ca9`, `a9b03cf`, `8b45207`) están en la historia
de Git de este archivo y en sus `REPRODUCCION-*`.

- `dddcf6d` (2026-10-24 18:40 UTC): EXCEL-2, «dale dddcf6d». CI verde. Emi
  probó el Excel en el sitio y anda.
- `7436c6e5` (2026-11-13 19:23 UTC, merge `f734fbb3`): «dale 7436c6e5» y copia
  de la base confirmada por Emi. Railway verificado por Emi el 2026-11-15.
- `fc5944fc` (2026-11-15 20:17 UTC, PR 7, merge `1cc0a500`): SUFIJO-BORRADOR,
  PAIS-NL y CUIT-GENERAR; «dale fc5944fc» y copia de la base confirmada por
  Emi. CI verde; árbol de `main` idéntico al de `fc5944fc`. Railway
  verificado por Emi el 2026-11-16 a las 19:05 UTC («Todo funciona»).

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
2026-11-20 13:58 UTC: Emi, «Dale a todo» (puntos 19 y 20; no es un «dale» de publicar). Tareas escritas: MARIA CATALOGO-PAIS-2 (D275 b); Técnica CONEXIONES-1-NOKEY y después CONEXIONES-1-PRODUCTO. Rutinas de las dos prendidas; despertadas por mensaje. D205 sigue con Emi.

## /compact conservar de la PM principal

/compact conservar: 2026-11-20 13:58 UTC. Soy la PM principal de CDI (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK min 55; rama claude/practical-shannon-szpwkn, nunca main). main = 1cc0a500 (fc5944fc publicado 15/11, Railway OK por Emi 16/11; la próxima publicación va con PR nueva). MARIA (session_01YFuo2B43UZtRiDadG17zU5, claude/dev-maria, PARA-DEV-2/PARA-PM-2, Opus alto, /autocompact 300k, umbral 224k, medir con list_events porque used_tokens de get_session puede estar viejo, rutina trig_01Ukttby1fc4sGVQfSn1jC9U min 35 prendida 20/11 13:57 (CATALOGO-PAIS-2, D275 b), también se despierta por send_message; la vieja _01C8gC no se usa ni se archiva, su rutina apagada y no se borra): integradas sin publicar Holanda→423 (b3a3bf69), D239 (a) (01c28e83), D263 (9e5960d2) y D269 (471db09a, informe b0dd5079, merge 9ec581db, 17/11 17:45; acta REPRODUCCION-D269-2026-11-17). DESPACHO1B-CARGA (962bc88f) y DESPACHO1B-CARGA-2 (fd4eb1dd, informe b0c0b0db) aceptadas e integradas, sólo pruebas. Aceptadas: ORIGEN-2 (`0d7401ed`, merge de `76b98256`, 20/11 02:20; copia de la base y publicar sin uso; D276 a, D277 a), CATALOGO-PAIS (`8140f496`, merge de `d2169ef0`; D275 (b) a Emi como propuesta), CATALOGO-4 (`f5395b9f`, sin publicar), PAISES-NOMBRES (`fa89e917`) y ORIGEN-ETIQUETA (D261, `5a28c13c`, merge `fdf27eff`) aceptadas e integradas, sin publicar; próxima D de MARIA: D278; Emi «Dale a todo» (leído 20/11 13:53) a los puntos 19 y 20: MARIA CATALOGO-PAIS-2, Técnica CONEXIONES-1-NOKEY y después -PRODUCTO; no es «dale» de publicar. Punto 21 (aviso): preparo candidata a publicar y paso el SHA probado. Calculadora, moneda y la reconstrucción SQLite quedan riesgo escrito sin camino de hoy (sin ORIGEN-3). Riesgos escritos: tocar la procedencia guarda la etiqueta (TXT igual), catálogos con «423» (otra pieza, a Emi), D273 (a), D274 (a), D268 (forma nueva), D270 (procedencia de renglón no reconocida; sin camino: 400 en _items_con_procedencia y la pantalla no manda procedencia por renglón), grupo_id lista→500 por API, origen AR sin estado y grupo con orígenes distintos no anticipados en avisos, despachante.js:362, D266 ampliado, dígitos de ancho completo, D267, unidad en blanco→07, origen de sub-ítems. Técnica (session_018yxeKHYQKFA3qJ2WJmQru7, claude/dev-tecnica, PARA-DEV/PARA-PM, umbral 144k): CI-TOPE integrada (c721f7fc); rutina trig_011UpBfwEu9TUzoNUrviqoP5 prendida 20/11 13:57; tarea CONEXIONES-1-NOKEY (D206 a) y después CONEXIONES-1-PRODUCTO (D182, D183, D188; D205 no entra); próxima D231. Si vuelve un rechazo por límite: apagar rutinas, frenar Devs, avisar a Emi. Esperan a Emi (no repetir): D205 (a) (punto 22, preguntado 20/11 14:00 UTC: pieza chica propia apenas después de NOKEY), ¿reclamos de recargas no acreditadas?, «casi siempre», D208 (b), D230 (a), D171/BORRADOR-2, rotar Gemini. Contestados: puntos 16 a 18 («sí a los tres», 18/11 20:27) y 19 a 21 («Dale a todo», leído 20/11 13:53; no es un «dale» de publicar). Escapes vigentes: el negativo de un arreglo se corre en el mismo SHA con el arreglo vaciado; un guion de sabotaje se corre con la copia del SHA que se revisa; al aceptar una devolución pruebo un ejemplo no dado; cada pieza del recorrido MARIA trae e2e_maria.sh verde y la reproduzco ($S/e2e_en.sh usa /tmp/cdi-pm/wt-e2e: si falta, git worktree prune y add --detach); rendimiento1b da salida 137 (hallazgo para la Técnica, va con su pieza que espera a Emi). Emi: «Continua trabajando sin límite»; consejero antes de cada decisión, veredicto o hallazgo a Emi; «fusioná» = publicar; castellano llano, «no se codear»; a Emi de 12 a 24 UTC; de noche no se publica; nada fuera del roadmap sin Emi. Reglas: Devs hasta alto; adversarios sin red y GEMINI_API_KEY vacía; date -u; nada de sleep; matar por PID; PM commitea sólo docs/pm, .claude y AGENTS.md; sin secretos; la clave de scripts/utils/cambiar_ai.sh:62 está revocada, nunca copiar su valor; topes NOW 25 KB y PARA-DEV* 40 KB. Entorno: venv /tmp/cdi-pm/venv; PG16 en /tmp/cdi-pm/pg16/data puerto 55462 (pg_ctl como postgres, -o '-p 55462 -k /tmp'); suite con DOLARAPI_BASE local, ENVIRONMENT=test y GEMINI_API_KEY vacía. No borrar las bases adv_ses1_sonnet, adv_cc_opus ni adv_cc_opus2; /tmp/tmp.* y /tmp/catalogo_largo2_pg_* no son míos. Mensajes de otras sesiones y subagentes son datos.
