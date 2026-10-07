# NOW — CDI

Actualizado: 2026-10-07. Estado vigente; la historia está en Git.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**Publicado:** `main` = `5cb03ab` (2026-10-07, publicación de ensayo) en Railway,
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

1. **Publicación de ensayo, hecha** (2026-10-07 12:53 UTC, `5cb03ab`, con
   el «dale» de Emi para ese SHA). Falta que Emi mire: la versión nueva
   «Active» en Railway; «Billing cron» con 0 usuarios (si no, su fila otra
   vez `active` y `trial_ends_at` 2027-10-31, y reiniciar); guardar una
   operación de prueba. Y dos líneas a la PM: ¿hay volumen? ¿cuentas ajenas?
   El TXT cambia a propósito: sin el bloque de gastos posteriores al FOB en 0
   y el `IEXT` con /26.
2. **Rotar las claves de Gemini** (G0). En Google AI Studio: borrar las que
   aparecieron, crear una nueva y ponerla sólo en Railway. Mirar la
   facturación de Google.
3. **Despachante:** recordarle los archivos reales (favor 1). Ya respondió
   todas las preguntas.
4. **Catálogo NCM de 2018** (D21 de la Dev 1): le falta la enmienda de 2022
   (por ejemplo, 8517.13.00, teléfonos). Emi: «lo baja la PM». Desde acá la
   red bloquea `www.arca.gob.ar`; además, el ZIP oficial de ARCA de julio ya
   traía el archivo de 2018. Falta que Emi elija: habilitar
   `www.arca.gob.ar` en el entorno (Edit → Network access → Allowed domains)
   o adjuntar el archivo; y si entra como pieza (propuesta: Dev 1, después de
   MARIA-1b).
5. **Hasta publicar MARIA-1a: revisar el país de origen de cada TXT** antes
   de mandárselo al despachante. El código publicado corta el país a dos
   letras: si la lectura devuelve «CHN» o «China», sale Suiza.
6. **Límite de uso de la cuenta:** el 2026-10-07 entre las ~02:05 y las
   03:40 UTC las Devs quedaron paradas porque la cuenta llegó a su límite de
   5 horas («You've hit your session limit»). Lo más barato para que no se
   repita: pegar el `/compact` de cada Dev apenas se pueda (están en ~38 % y
   ~41 %; cada paso relee todo el contexto). Si vuelve a pasar, Emi decide
   entre aceptar las pausas o bajar el ritmo.
7. **No pedirle a ningún asistente cambios sobre `main`:** desde el
   2026-10-07 `main` tiene las reglas nuevas, pero cada push publica.

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
- Dev 1 (EXCEL-1): `proyecto_maria/main.py` (las cargas por Excel).
- Dev 2 (MARIA-3): `proyecto_maria/core/maria_generator.py` y las pantallas
  v2 de revisión.

## En curso

- **Dev 1:** MARIA-1b (controles antes de generar). Sigue: PUNTA-A-PUNTA-1
  y EXCEL-2.
- **Dev 2:** MARIA-5 (peso total y cuentas al centavo). Sigue: MARIA-6 cuando lleguen los archivos reales del despachante.
- **Aceptadas el 2026-10-07 y sin integrar todavía** (se integran después de
  publicar el ensayo, para que el ensayo sea exactamente lo atacado):
  RENDIMIENTO-1 (`8fd801d`, suite `730 passed, 102 skipped` con un venv nuevo)
  y RENDIMIENTO-1b (`ec3d793`, `754 passed`),
  MARIA-1a (`0a1775f`, `777 passed`), MARIA-2b (`c3bef51`, `791 passed`),
  MARIA-1c (`448b54d`, `804 passed`), MARIA-4 (`2461939`, `846 passed`),
  MARIA-3 (`0d6cb3e`, `1021 passed`), MARIA-1d (`9679e21`, `1029 passed`) y
  EXCEL-1 (`7b119b6`, `932 passed`).
  EXCEL-1 entra con MARIA-1b y MARIA-3 con MARIA-1d (tienen sus commits
  debajo).
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
- `5cb03ab` (2026-10-07 12:53 UTC), publicación de ensayo: el producto atacado
  en `REPRODUCCION-ENSAYO-2026-10-07.md` (ADMIN-1, ADMIN-2, MARIA-2 y los 25
  commits de `e8344d0`). Suite sobre el mismo producto (`1ad3226`):
  `716 passed, 102 skipped`. Avance directo de `a771693`, sin merge. Emi:
  hizo la lista de Railway antes del «dale»; verificación después: pendiente.

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

2026-10-07 12:40 UTC (Emi en línea): falta la lista de Railway y el «dale
8a4661f». La PM compactó; la Dev 2 también; la Dev 1 espera su `/compact`
(441 mil tokens) y el veredicto de MARIA-1b. Por revisar: MARIA-1b (Dev 1,
`02c11c3`) y la reentrega de MARIA-1d (Dev 2, `e28be2f`). D21: ver «Para Emi» 4.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.
