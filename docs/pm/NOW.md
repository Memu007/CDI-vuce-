# NOW — CDI

Actualizado: 2026-10-07. Estado vigente; la historia está en Git.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**Publicado:** `main` = `a771693` (2026-07-18) en Railway,
`cdi-production.up.railway.app`. Railway publica cada push a `main` sin
esperar los tests.
**En producción:** la usa sólo Emi, con facturas reales (Emi, 2026-10-07).
**Rama de PM:** `claude/practical-shannon-szpwkn`: lo aceptado y sin publicar
(incluye los 25 commits de `e8344d0`, ADMIN-1 y MARIA-2). **Ramas de las
Devs:** `claude/dev1-tecnica` y `claude/dev2-maria`.
**Plan:** `ROADMAP.md`, con el orden de Emi del 2026-10-07: primero el TXT,
después el cobro, la seguridad al final y exhaustiva. Ningún estudio entra
antes de cerrar la Fase 3.

## Para Emi

1. **Mañana, de día: publicación de ensayo** (aprobada el 2026-10-07; falta
   el «dale» para el SHA exacto, que le pasa la PM con la suite corrida sobre
   él). Antes, en Railway:
   - **lo primero, en la tabla de usuarios de la base: ¿existen `demo`,
     `premium` o `basico`?** El código publicado los crea con contraseñas
     escritas en el código (`demo` además es admin) cuando `ENVIRONMENT` no es
     `production`, y no los borra después. Si existen, cualquiera puede entrar
     con ellos y, con la fuga de MARIA.TXT, ver las facturas reales: borrarlos
     o cambiarles la contraseña antes que nada;
   - **si hay cuentas que no sean de Emi:** la fuga pedía sesión iniciada; sin
     cuentas ajenas, nadie pudo ver las facturas;
   - en las variables del servicio: `ENVIRONMENT` = `production`, que exista
     `DATABASE_URL` (la versión nueva no arranca sin ella; si faltara, Railway
     deja andando la vieja) y que `ADMIN_USERNAMES` tenga el usuario de Emi y
     sólo usuarios que ya existen (con ADMIN-1, sólo ellos entran al admin);
   - toda cuenta activa con el período vencido hace más de 7 días pasa a
     impaga al arrancar;
   - en la base: una copia (pestaña de copias de seguridad), si el plan lo
     permite;
   - al publicar se borran los TXT generados y el historial de NCM que viven
     en el disco del servidor (las operaciones en la base quedan);
   - recomendado: prender «Wait for CI» y apagar la red pública de la base.
2. **Rotar las claves de Gemini** (G0). En Google AI Studio: borrar las que
   aparecieron, crear una nueva y ponerla sólo en Railway. Mirar la
   facturación de Google.
3. **Despachante:** recordarle los archivos reales (favor 1). Las dos
   preguntas cortas ya se las mandó Emi el 2026-10-07.
4. **Hasta la primera publicación:** en `main` sigue la regla vieja que manda
   «push a `main`» a otros asistentes. No pedirle a ningún asistente cambios
   sobre `main`.

## Quién hace qué

| Rol | Sesión | Rutina | Rama |
|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn |
| Dev 1 | session_01VV5RVDA64AuzLaPBDnwH39 | trig_016zR6giZB8Mq9ZdfaerVh2D (min 15) | claude/dev1-tecnica |
| Dev 2 | session_01JssJQ6CQvEBZ7yjJp3hHQx | trig_019ehV8P48FzbNwYQGZjgYcW (min 35) | claude/dev2-maria |

**Sin PM visual:** la PM principal revisa a las dos Devs, y las dos la
despiertan con su rutina (donde los comandos dicen «PM visual», acá es la
principal).

La sesión vieja «CDI — Dev 1» (session_01F66wsdGqhMMEiCLTopVVXe, rutina
trig_01XijDAiEX4aBm8dfv9ZD6C1) se abrió sobre la copia vieja (`Memu007/CDI`):
pausada, no trabaja acá.

Esfuerzo (Emi, 2026-10-07): PM principal extra; las Devs, como máximo alto,
también sus subagentes (Emi confirmó las dos sesiones en alto). Ningún subagente usa Fable. El consejero es sólo de
la PM principal.

Archivos abiertos por Dev:
- Dev 1 (ADMIN-2): `proyecto_maria/main.py` (`/api/system/connectors`,
  `/api/payments/simulate-webhook`), `routers/admin_router.py`,
  `static/v2/topbar_financials.js`, `tests/test_admin_solo_admin.py`.
- Dev 2 (MARIA-1a): `proyecto_maria/pdf_extractor.py` (las dos copias del
  lector) y, si hace falta, la tabla de países de `core/maria_generator.py`.

## En curso

- **Dev 1:** ADMIN-2. Sigue la Fase 1: RENDIMIENTO-1 (incluye cambiar el
  lector de PDF viejo), EXCEL-1, MARIA-1b y PUNTA-A-PUNTA-1.
- **Dev 2:** MARIA-1a. Sigue: MARIA-2b, MARIA-4 (estado, IVA adicional,
  banco y empresa de digitalización), MARIA-3 y MARIA-5; MARIA-6 cuando
  llegue lo del despachante.
- **Aceptadas el 2026-10-07 e integradas:** ADMIN-1 (`ac25dbc`) y MARIA-2
  (`65ea6f3`). Suite sobre la rama integrada (`78b60c8`):
  `703 passed, 102 skipped`.
- **Publicación de ensayo:** dos candidatos. (a) `cb8f509`, el código de
  `e8344d0` tal cual; (b) la cabeza de la rama de PM, que además cierra el
  admin y saca los productos inventados, pero pide `ADMIN_USERNAMES`. La PM
  recomienda (b) si la variable está; si no, (a). La suite se corre otra vez
  sobre el SHA exacto.
- **Despachante:** respondió las seis preguntas el 2026-10-06
  (`PREGUNTAS-DESPACHANTE.md`). Faltan las dos cortas, los archivos reales y,
  al cerrar la Fase 1, la prueba en su Kit.

## Puertas para cobrarle a un estudio

| Puerta | Estado | Qué falta | Se cierra en |
|---|---|---|---|
| G0 · Secretos | 🔴 | Rotar las claves de Gemini | Emi, esta semana |
| G1 · Configuración | 🟢 | G1.1 a G1.5 cortan. G1.6 y G1.7 sin medir | — |
| G2 · Imagen real | 🟢 | Cerrada el 2026-09-17 | — |
| G3 · Aislamiento | 🟡 | En producción, la fuga de MARIA.TXT (se arregla con el ensayo). Admin cerrado en la rama (ADMIN-1). Abiertos: sesiones que reviven, límite de intentos burlable, prueba de aislamiento parcial | Fase 3 |
| G4 · Producto (MARIA) | 🔴 | Origen mal leído, estado e IVA adicional fijos, peso por unidad, avisos tarde, gastos FOB sin cablear, banco, identificadores. Sin productos inventados (MARIA-2) | Fase 1 y la prueba en el Kit |
| G5 · Pruebas | 🟢 | `703 passed, 102 skipped, 0 failed` en la rama integrada | — |
| G6 · Volver atrás | 🟡 | Esquema probado en local; falta la copia de la base | Fase 3 (y el ensayo lo ensaya) |
| G7 · Cobro | 🔴 | El corte por impago cubre 2 funciones; cancelar no cancela en Mercado Pago; aviso de pago sin firma; doble suscripción; invitaciones | Fase 2 |
| G8 · Piloto | ⚪ | Tres estudios presentan de verdad un MARIA de CDI | Fase 4 |

## Publicado

- `a771693` (2026-07-18), anterior a este método. Cada publicación nueva: una
  línea con fecha, SHA y qué verificó Emi.

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

2026-10-07 02:15 UTC: roadmap simplificado a pedido de Emi (una pantalla
para Emi con «está lista cuando…», el detalle abajo; tres fusiones de
piezas). PM al ~40 % de contexto: compacta en este corte.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.
