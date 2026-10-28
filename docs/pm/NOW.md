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

## Quién hace qué

Desde el 2026-10-24 (Emi: Codex deja CDI; dos Devs nuevas en Claude).

| Rol | Sesión | Rutina | Rama | Esfuerzo |
|---|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn | — |
| Dev MARIA (Dev 2) | session_01C8gCBjvn36wnYC6qG2Sixi | trig_01WmrC3ALqBXkD9UBv6dFGbP (min 35) | claude/dev-maria | alto |
| Dev técnica (Dev 1) | session_018yxeKHYQKFA3qJ2WJmQru7 | trig_011UpBfwEu9TUzoNUrviqoP5 (min 15) | claude/dev-tecnica | medio |

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

2026-10-28 16:20 UTC: Emi: «hay que gastar cupo, tenés 2 horas antes de que se reinicie». Las dos Devs despertadas para correr /entregar ya, en su orden; la PM revisa GUARDAR-2 y ORDEN-1 con adversario Sonnet alto y suite sobre 0d89c20. Emi: sí o no a la medición chica de la D39.

2026-10-28 14:00 UTC: sesiones bajo 170k (técnica 137k, MARIA 118k), las dos esperan el cupo de las 18:00. MARIA terminó EMAIL-1 (2b93071, suite 3954 passed) y CONEXIONES-1 (30c0e97: sin conexiones colgadas, sin cambio de producto), sin entregar. D38 (1) y D39 (1) por ahora, decididas por la PM; la medición chica de la D39 se le propone a Emi. La técnica, BACKUP-1a subida en 70f6d3d.

2026-10-28 13:00 UTC: sesiones bajo 170k (técnica 137k, MARIA 139k). Sin D abiertas. MARIA tiene EMAIL-1 en su clon (sin subir) y mide CONEXIONES-1: sin conexiones colgadas en la primera corrida, arma los sabotajes del medidor. La técnica, BACKUP-1a en la rama hasta `9d2d4bb`: sabotajes y suites corriendo; entrega con el cupo de las 18:00. Emi: contar los pares de email, destino de la copia, textos legales.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.

## /compact conservar de la PM principal

/compact conservar: Soy la PM principal de CDI (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK min 55). Producto Memu007/CDI-vuce-, clon /home/user/cdi-vuce-, mi rama claude/practical-shannon-szpwkn (nunca main; cada push a main publica). main = 8b45207 (EXCEL-3 + CLIENTE-1, publicada 24/10 con «dale 8b45207»; falta que Emi la pruebe; volver a dddcf6d sólo con su ok). Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, alto): MARIA-7/8, VALOR-1b, MARIA-9, SEPARADORES-1, VALOR-1c y SEPARADORES-1b aceptadas e integradas (la última sobre db39de0, merge 49361ca, sin publicar); SUFIJOS-1 (vuelta, 45a3ea1) y SEPARADORES-1c (91be665) aceptadas e integradas (merge e9981e5, suite 3393 passed 0 rojos), sin publicar. Anotado: arancel 200 con {} deja celdas sin aviso. SEPARADORES-1d aceptada sobre 140c122 (avance rápido; suite 3478 passed 0 rojos). Activa: ORG-1 (permisos: revisión fuerte con adversario; Postgres 16 local en /usr/lib/postgresql/16; cupo de subagentes en uso desde 28/10 16:20 UTC (Emi: gastarlo antes del reinicio de las 18:00); se pausa si Emi pone antes 8.1/9.2/8.2 de Argon). Próxima D: D28 (D26 a, propuesta a Emi; D27 b = ORG-1b). ORG-1 lista en ddfc798 sin entregar; ORG-1b hecha (f8616cf, probada en 5d42909), se entrega en el mismo /entregar. Después de ORG-1, LEGAL-1 espera el texto de Emi (pedido el 27/10). DESPACHO-1a (bajar el catálogo del cliente en Excel) dada a MARIA el 28/10, entrega con ORG-1/ORG-1b, apartado propio. DESPACHO-1 (despacho oficializado → catálogo del cliente, editable y descargable en Excel; nunca TXT) sumada al roadmap por Emi el 28/10 (para que despachantes que vienen de otro sistema armen rápido el catálogo y después hagan el predespacho en CDI), Fase 1c de MARIA (ubicada por la PM: detrás de las piezas del TXT; se hace la primera que tenga lo suyo; lista antes del piloto 28/12); Emi manda la pregunta 6 el 28/10; espera la pregunta 6 al despachante (despachos de ejemplo y formato del catálogo; Excel si no hay otro). El despachante contestó el 28/10 (PREGUNTAS-DESPACHANTE.md; despachos reales sólo en el scratchpad, forma en DESPACHOS-FORMA.md): DESTINO-1 de MARIA hecha sin entregar (producto 7526be9, pruebas f887b4a, informe 4905cd8; entrega propia después de ORG-1); SUFIJOS-2 adelantada a «empezala ya» el 28/10 03:00 UTC, encima de 4905cd8 (D28 a: el golden no se toca, la línea GANANCIASOP3 dice USOPAR; commits aparte encima de ORG-1/ORG-1b/DESPACHO-1a, que se entregan con su propio SHA y suite sobre ese SHA; entrega propia), después SUFIJOS-2 y SEGURO-1; PESO-NETO-1 y PRORRATEO-1 siguen esperando; preguntas 5 a 10 para Emi de día. D29 (a) decidida el 28/10 04:00 (PIDE_NUMERO=("Z",); pregunta 10 al despachante). SUFIJOS-2 hecha sin entregar (probada 4ca6829). SEGURO-1 dada a MARIA el 28/10 04:00, «empezala ya», encima de 4ca6829, entrega propia después de SUFIJOS-2 (regla en el servidor; el seguro calculado se borra al pasar a CIF/CIP/DPU/DAP/DDP; si no se puede, D30). D30 (a) por ahora (28/10 05:00; (b), frenar en el servidor el seguro «para completar», va a Emi de día como SEGURO-2, recomendada). SEGURO-1 hecha sin entregar (probada 371cde2, informe de9cb24; entrega después de SUFIJOS-2; /security-review). DESPACHO-1b (lectura y pantalla del despacho, sin Gemini, nunca TXT) hecha sin entregar (producto 0591722, probada e59e1a8, informe 5ed8e89; entrega después de SEGURO-1; revisión fuerte: datos de clientes). D31 (a) decidida por la PM 28/10 06:00 (el catálogo guarda sólo lo que tiene columna; sin migración). DATOS-1 de MARIA hecha sin entregar (dada 28/10 06:00 encima de e59e1a8; probada c996ad4, informe b19582c; entrega después de DESPACHO-1b; D5 borrar cliente con presupuesto en Postgres, D32 (a) decidida por la PM 28/10 06:05: borrar el cliente borra sus presupuestos compartidos en la misma transacción; D2 /health 503 sin texto; D6 sin dev_detail en los dos manejadores de 500; /security-review). DISCO-1 de MARIA hecha sin entregar (dada 28/10 07:00 encima de c996ad4; probada 88b22c8, informe ae5c69b; D33 (a) decidida por la PM 08:00: el código no cambia, rescatar los historiales de producción lo decide Emi al publicar; historial de NCM de ncm_historial_<usuario>.json a una tabla nueva por dueño, mismo comportamiento, sin perder cuentas a la vez, carga única de los .json viejos, Postgres 16; lista de lo demás en DATA_DIR a riesgos; revisión fuerte). OBSERVABILIDAD-1 de MARIA hecha sin entregar (dada 28/10 08:00 encima de 88b22c8; probada 39be45e, código 7ae35ab, informe 15a95e0; entrega después de DISCO-1; D34 (a) decidida por la PM 09:00: sólo la columna, el dueño por token es otra pieza a riesgos; migración: revisión fuerte). SESION-1 de MARIA hecha sin entregar (pasada de la técnica 28/10 09:00 encima de 39be45e; probada 895ee73, diff f5160d7..895ee73, informe 5105838; suite 3872 passed 0 rojos y 19 sabotajes ROJO según ella; entrega después de OBSERVABILIDAD-1; S3: revocar nunca escribe NULL en active_jti, logout revoca, cambiar email pide la clave; autenticación: revisión fuerte). Activa de MARIA: ABUSO-1 (🔵, pasada de la técnica por la PM 28/10 10:00, encima de 895ee73: S4 IP detrás del proxy, S5 /api/ui/event sin sesión ni tope, S6 enumeración y recuperar usuario sin límite, C9 pruebas gratis infinitas; D35 (1) en las cinco, decidida por la PM 28/10 10:15 sobre e25e87c: última IP del XFF con log en el 429, sus números, mensajes quedan, tres acciones sin sesión, contadores de login en tabla con commit propio; D36 (2) por ahora 10:30: el email se sigue comparando igual, su (1) va a Emi; Argon 14 y X1 fuera; revisión fuerte). ABUSO-1 hecha sin entregar (probada 43916a7, informe 76def65). D37 (2) por ahora 12:00 (session.close() cancelado tras la respuesta, preexistente: a riesgos, sin filtrar el aviso; medirlo es pieza nueva, a Emi). Emi dijo sí el 28/10 12:15 a EMAIL-1 (D36: el email sin distinguir mayúsculas al buscar y al crear o cambiar; pares existentes no se tocan hasta que Emi los cuente; qué hacer con dos cuentas va a la D38) y CONEXIONES-1 (D37: medir con gunicorn como el Dockerfile y Postgres 16 si quedan conexiones tomadas; arreglar sólo si quedan): activa EMAIL-1 encima de e1b3129, después CONEXIONES-1, cada una con su /entregar después del de ABUSO-1; revisión fuerte. MARIA dejó las diez entregas preparadas para el cupo (e1b3129). EMAIL-1 hecha sin entregar (probada 2b93071, base e22a5cf; suite 3954 passed 0 rojos; sabotajes 13/13). CONEXIONES-1 hecha sin entregar (30c0e97, sólo scripts y pruebas: sin conexiones colgadas con gunicorn y Postgres 16; sin cambio de producto). D38 (1) decidida por la PM 14:00 (exacto gana; varias sin exacta, ninguna; (3) unificar e índice sobre lower(email) espera el conteo de Emi). D39 (1) por ahora 14:00 (40 logins malos a la vez llenan el pool 50/50: a riesgos); su (2), medición chica con 60-100 a la vez, propuesta a Emi como pieza nueva. Doce entregas en orden (2b324e9), a /entregar ya desde 16:20 UTC por pedido de Emi. Próxima D de MARIA: D40. Dev técnica (session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, medio): EXCEL-3f aceptada sobre 8c63c37 e integrada hasta 8e744a0 (28/10 01:45 UTC; EXCEL-3 ✅); EXCEL-3d, CLIENTE-1b/1c, ESTUDIO-1/1b y EXCEL-3e integradas, sin publicar. GUARDAR-2 entregada en cef45ce (informe cb42e8f; sólo main.py +50 −5; suite 3863 passed 0 rojos según ella; 9 sabotajes; Postgres 16 OK; sin code-review ni adversario): revisión con adversario en curso desde 16:20 UTC, NO integrar cb42e8f hasta aceptarla. ORDEN-1 entregada en 0d89c20 (informe cdc9c57; D1-D3 (a) contestadas en 3b60e3d; sabotajes 14/14 rojos reproducidos por la PM; para el adversario: logout no borra los borradores, preexistente): adversario y suite en curso desde 16:20 UTC, NO integrar hasta aceptarla. Diagnóstico de test_excel2 recibido (b5a50d1: cola detrás de las pesadas); D4 (a) carril liviano y D5 (a) dt < 5 s, decididos por la PM el 28/10 02:40. EXCEL-2b hecha sin entregar (cf2012b, 116d9f2, b3ac325; entrega con el cupo; revisión fuerte con adversario). COBRO-MP-1 hecha sin entregar en f54d8a9 (subida a claude/dev-tecnica; suite 3948 passed; 32 sabotajes en rojo; entrega después de EXCEL-2b; revisión Opus+Sonnet alto; dos riesgos para Emi de día: dos pagos a la vez de una cuenta dan una sola extensión; un aviso de renovación sin suscripción queda rechazado para siempre). COBRO-CORTE-1 hecha sin entregar en 27e4594 (dada 28/10 05:00 encima de f54d8a9; D4 b N=10, D5 a, D6 a de efef997; análisis 62b1d14; plata: Opus+Sonnet alto; al revisarla, ver que aislar test_user en las pruebas no tape un bloqueo real a quien regenera mucho). COBRO-MP-2 hecha sin entregar en dda9f5b, subida a claude/dev-tecnica el 28/10 10:00 (73a570e; verificado con ls-remote); se entrega después de COBRO-CORTE-1. AISLAMIENTO-2 (rama 7d3a7f8) y LIMPIEZA-1 hechas sin entregar, después de COBRO-MP-2. Activa de la técnica: BACKUP-1a (hecha, subida en 70f6d3d, entrega con el cupo; pasada de MARIA por la PM 28/10 12:00, encima de LIMPIEZA-1: pg_dump, restauración en base descartable y comparación; destino fuera de Railway y programación esperan a Emi; datos: revisión fuerte). Detalle de COBRO-MP-2 (dada 28/10 08:00 encima de 27e4594: C2 cancelar también en MP y activa hasta fin de período, C4 una sola suscripción sin perder días, C8/D9 reactivar pagando y sin token no dice «activada»; MP simulado; plata: Opus+Sonnet alto; D7 (a) en las cuatro, decidida por la PM 28/10 08:20, Emi la confirma de día; próxima D de la técnica: D8).  PRUEBAS-1 + PA-1b integradas. Pendiente de la PM: revisar GUARDAR-2; revisión fuerte de ORG-1/ORG-1b/DESPACHO-1a de MARIA cuando entregue; limpiar /tmp/cdi-pm/wt-*, rev1d, rev1d-b y base1d; contarle a Emi de día que ESTUDIO-1 se puede publicar y que DESTINO-1 y PESO-NETO-1 esperan la lista de códigos y el packing list del despachante. Para Emi: decir sí o no a la medición chica de la D39 (recomendé sí); contar en producción, con una consulta de sólo lectura, los pares de email que sólo difieren en mayúsculas (para EMAIL-1); BACKUP-1: adónde va la copia; confirmar la D35 de ABUSO-1 (números de límite y supuesto del proxy de Railway; al publicarla, mirar el log del 429); confirmar la D7 de COBRO-MP-2 (cuatro comportamientos del cobro, (a) decidida por la PM); el límite de gasto (frenó a las tres sesiones el 25/10 de ~03:30 a 04:50 UTC y a MARIA el 27/10 17:35 UTC; el semanal vuelve el 28/10 18:00 UTC); D26: endpoint para cancelar una invitación pendiente (fuera del roadmap; recomendé sí); orden de prioridad de Argon (REPRODUCCION-ARGON-2026-10-24.md; nada al roadmap sin su «dale»; preguntado el 27/10 si 8.1/9.2/8.2 van antes de ORG-1, recomendé sí); Emi manda el pedido al despachante (27/10) y la pregunta 5; probar 8b45207; preguntas al despachante (PREGUNTAS-DESPACHANTE.md); packing list; revocar la clave de Anthropic de cambiar_ai.sh y rotar Gemini; 4.1 y 6.1 de producción; el script de fechas con --base deja la clave en el historial (pasarla por variable). Roadmap en ROADMAP.md, con marca por pieza (✅ al aceptar la pieza entera) y avance con docs/pm/herramientas/avance.py (28/10 01:45: 29 %, 10 de 34); TXT y proforma reales sólo en el scratchpad. Reglas de Emi: nada fuera del roadmap; Devs hasta alto, sin Fable; consejero sólo mío; castellano llano; consultas de 9 a 21 ARG; publicar sólo con «dale <SHA>» de día; usar date -u.

