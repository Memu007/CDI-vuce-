# NOW — CDI

Actualizado: 2026-10-07. Estado vigente; la historia está en Git.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**Publicado:** `main` = `a771693` (2026-07-18) en Railway,
`cdi-production.up.railway.app`. Railway publica cada push a `main` sin
esperar los tests.
**En producción:** la usa sólo Emi, con facturas reales (Emi, 2026-10-07).
**Rama de PM:** `claude/practical-shannon-szpwkn`: lo aceptado y sin publicar
(incluye los 25 commits de `e8344d0`, ADMIN-1, ADMIN-2 y MARIA-2). **Ramas de las
Devs:** `claude/dev1-tecnica` y `claude/dev2-maria`.
**Plan:** `ROADMAP.md`, con el orden de Emi del 2026-10-07: primero el TXT,
después el cobro, la seguridad al final y exhaustiva. Ningún estudio entra
antes de cerrar la Fase 3.

## Para Emi

1. **Mañana, de día: publicación de ensayo** (aprobada el 2026-10-07; falta
   el «dale» para el SHA exacto, que le pasa la PM con la suite corrida sobre
   él). Antes, en Railway, en este orden (probado en local con Postgres y una
   base armada con el código de julio: `REPRODUCCION-ENSAYO-2026-10-07.md`):
   1. **Copia de la base** (pestaña de copias de seguridad), antes de tocar
      nada.
   2. **Tabla `users`:**
      - **¿Existen `demo`, `premium` o `basico`?** Borrar esas filas. El
        código publicado los crea con contraseñas escritas en el código, y
        `demo` tiene guardado el rol de admin: entra al panel aunque no esté
        en `ADMIN_USERNAMES`. Si Railway no deja borrarlos (tienen datos), no
        seguir y avisar a la PM.
      - **Tu fila:** `billing_status` = `active` y `trial_ends_at` = una fecha
        del año que viene (por ejemplo, 2027-10-31). Si no, al arrancar la
        versión nueva tu cuenta pasa a impaga: seguís generando el TXT, pero
        no guardás operaciones nuevas, y volver a la versión vieja no lo
        deshace. Hacen falta las dos cosas: con la fecha sola no alcanza.
      - **Cuentas que no sean tuyas,** o filas en la tabla `organizations`:
        avisar a la PM. Sin cuentas ajenas, nadie pudo ver tus facturas con
        la fuga de MARIA.TXT.
   3. **Variables del servicio:**
      - que existan `ALLOWED_ORIGINS`, `JWT_SECRET_KEY` y `DATABASE_URL` (sin
        ellas la versión nueva no arranca y Railway deja andando la vieja);
      - `ADMIN_USERNAMES` = tu usuario, escrito exactamente igual (si nombra un
        usuario que no existe, el primero que se registre con ese nombre es
        admin);
      - **`ENVIRONMENT` = `production`, exactamente así, en minúsculas.** Con
        «Production» la versión nueva crea los tres usuarios de prueba en la
        base real y `demo` entra como admin.
   4. ¿El servicio tiene un volumen conectado? Una línea a la PM (sin
      volumen, al publicar se borran los TXT generados y el historial de NCM;
      las operaciones en la base quedan).
   5. Recomendado: prender «Wait for CI» y apagar la red pública de la base.
   6. **Después de publicar:** en los registros del arranque, la línea
      «Billing cron» tiene que decir 0 usuarios pasados a `past_due`; y
      guardar una operación de prueba.

   El TXT cambia a propósito en dos cosas: desaparece el bloque de gastos
   posteriores al FOB en 0 y el año del `IEXT` pasa a 26.
2. **Rotar las claves de Gemini** (G0). En Google AI Studio: borrar las que
   aparecieron, crear una nueva y ponerla sólo en Railway. Mirar la
   facturación de Google.
3. **Despachante:** recordarle los archivos reales (favor 1). Ya respondió
   todas las preguntas.
4. **Hasta publicar MARIA-1a: revisar el país de origen de cada TXT** antes
   de mandárselo al despachante. El código publicado corta el país a dos
   letras: si la lectura devuelve «CHN» o «China», sale Suiza.
5. **Límite de uso de la cuenta:** el 2026-10-07 entre las ~02:05 y las
   03:40 UTC las Devs quedaron paradas porque la cuenta llegó a su límite de
   5 horas («You've hit your session limit»). Lo más barato para que no se
   repita: pegar el `/compact` de cada Dev apenas se pueda (están en ~38 % y
   ~41 %; cada paso relee todo el contexto). Si vuelve a pasar, Emi decide
   entre aceptar las pausas o bajar el ritmo.
6. **Hasta la primera publicación:** en `main` sigue la regla vieja que manda
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
- Dev 1 (RENDIMIENTO-1b): `proyecto_maria/main.py` (la adivinanza del
  vendedor y los tiempos máximos), `security/file_security.py`.
- Dev 2 (MARIA-1c): `proyecto_maria/pdf_extractor.py` (las dos copias del
  lector), `static/v2/screens/upload.js` y `static/app.js`.

## En curso

- **Dev 1:** RENDIMIENTO-1b (un PDF armado no deja a nadie sin lectura).
  Sigue: EXCEL-1, MARIA-1b y PUNTA-A-PUNTA-1.
- **Dev 2:** MARIA-1c (lo que no se pudo leer se avisa). Sigue: MARIA-4
  (estado, IVA adicional, banco y empresa de digitalización), MARIA-3 y
  MARIA-5; MARIA-6 cuando lleguen los archivos reales del despachante.
- **Aceptadas el 2026-10-07 y sin integrar todavía** (se integran después de
  publicar el ensayo, para que el ensayo sea exactamente lo atacado):
  RENDIMIENTO-1 (`8fd801d`, suite `730 passed, 102 skipped` con un venv nuevo),
  MARIA-1a (`0a1775f`, `777 passed`) y MARIA-2b (`c3bef51`, `791 passed`).
  RENDIMIENTO-1 sale con RENDIMIENTO-1b y MARIA-1a con MARIA-1c.
- **Aceptadas el 2026-10-07 e integradas:** ADMIN-1 (`ac25dbc`), MARIA-2
  (`65ea6f3`) y ADMIN-2 (`f9f8393`). Suite sobre `f9f8393`, que tiene el
  mismo producto y las mismas pruebas que la rama de PM:
  `716 passed, 102 skipped`.
- **Publicación de ensayo:** dos candidatos. (a) `cb8f509`, el código de
  `e8344d0` tal cual; (b) la cabeza de la rama de PM, que además cierra el
  admin, borra el atajo que activaba una suscripción sin pagar y saca los
  productos inventados, pero pide `ADMIN_USERNAMES`. La PM
  recomienda (b) si la variable está; si no, (a). Un subagente Opus alto
  atacó `81bcaba` y repitió sobre `7f1dd2c` (con ADMIN-2): se puede publicar
  si Emi hace antes la lista de arriba. Suite sobre `321f34b` (04:05 UTC):
  `716 passed, 102 skipped`; de ahí a la cabeza sólo cambian documentos. Si
  entra producto antes del «dale», se corre otra vez sobre el SHA exacto.
- **Despachante:** respondió las seis preguntas y las dos cortas el
  2026-10-06 (`PREGUNTAS-DESPACHANTE.md`): la empresa de digitalización se
  elige por operación (Modoc = `PSAD06`, Lakaut = `PSAD01`) y la reducción del
  IVA adicional es una «ventaja» que elige él en el Kit, no va en el TXT.
  Faltan los archivos reales y, al cerrar la Fase 1, la prueba en su Kit.

## Puertas para cobrarle a un estudio

| Puerta | Estado | Qué falta | Se cierra en |
|---|---|---|---|
| G0 · Secretos | 🔴 | Rotar las claves de Gemini | Emi, esta semana |
| G1 · Configuración | 🟢 | G1.1 a G1.5 cortan. G1.6 y G1.7 sin medir | — |
| G2 · Imagen real | 🟢 | Cerrada el 2026-09-17 | — |
| G3 · Aislamiento | 🟡 | En producción, la fuga de MARIA.TXT (se arregla con el ensayo). Admin cerrado en la rama (ADMIN-1 y ADMIN-2). Abiertos: sesiones que reviven, límite de intentos burlable, prueba de aislamiento parcial | Fase 3 |
| G4 · Producto (MARIA) | 🔴 | Origen mal leído, estado e IVA adicional fijos, peso por unidad, avisos tarde, gastos FOB sin cablear, banco, identificadores. Sin productos inventados (MARIA-2) | Fase 1 y la prueba en el Kit |
| G5 · Pruebas | 🟢 | `716 passed, 102 skipped, 0 failed` en la rama integrada | — |
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

2026-10-07 05:35 UTC (rutina): tres entregas revisadas y aceptadas
(RENDIMIENTO-1, MARIA-1a, MARIA-2b), con su subagente Sonnet alto cada una;
quedan en las ramas de las Devs hasta después del ensayo. Activas:
RENDIMIENTO-1b (Dev 1) y MARIA-1c (Dev 2). Contexto: Dev 1 ~41 %, Dev 2 ~52 %
(Emi pega sus `/compact` a la mañana); PM ~30 %.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.
